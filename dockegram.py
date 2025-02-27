import logging
import docker
import time
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, filters, MessageHandler
from config import *
from functools import wraps


# Logging settings
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)

# Dictionary to track manually stopped containers
manually_stopped_containers = {}
# Dictionary to track containers we've already alerted about
alerted_containers = {}
# Flag to skip first monitoring cycle
initial_scan_complete = False

docker_client = docker.from_env()

# Decorator for user permission check
def restricted(func):
    @wraps(func)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        if update.effective_user.id not in ALLOWED_USER_IDS:
            await update.message.reply_text("❌ You don't have permission to use this command.")
            return
        return await func(update, context, *args, **kwargs)
    return wrapped

# Decorator to check container name - keep for backward compatibility
def requires_container_name(command_name):
    def decorator(func):
        @wraps(func)
        async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            if not context.args or len(context.args) < 1:
                await update.message.reply_text(f"ℹ️ Please specify a container name: /{command_name} container_name")
                return
            return await func(update, context, *args, **kwargs)
        return wrapped
    return decorator

# Common function to perform container operations with error handling
async def perform_container_operation(update: Update, container_name: str, operation_func, success_message: str):
    try:
        return await operation_func(container_name)
    except docker.errors.NotFound:
        logger.error(f"Container not found: {container_name}")
        await update.message.reply_text(f"❌ Container '{container_name}' not found.")
    except Exception as e:
        operation_name = operation_func.__name__
        logger.error(f"Container {operation_name} error for {container_name}: {e}")
        await update.message.reply_text(f"❌ Error during container operation: {str(e)}")
    return None

# Container operations
async def start_container_op(container_name: str):
    container = docker_client.containers.get(container_name)
    logger.info(f"Found container '{container_name}' with status: {container.status}")
    
    if container.status == "running":
        return {"status": "already_running", "container": container}
    
    logger.info(f"Starting container '{container_name}'")
    container.start()
    
    # Remove from manually stopped list if it exists
    if container_name in manually_stopped_containers:
        del manually_stopped_containers[container_name]
        del alerted_containers[container.name]
        
    return {"status": "started", "container": container}

async def stop_container_op(container_name: str):
    container = docker_client.containers.get(container_name)
    if container.status == "exited":
        return {"status": "already_stopped", "container": container}
    
    container.stop()
    
    # Add to manually stopped containers with timestamp
    manually_stopped_containers[container_name] = time.time()
    
    return {"status": "stopped", "container": container}

async def restart_container_op(container_name: str):
    container = docker_client.containers.get(container_name)
    container.restart()
    
    # Remove from manually stopped list if it exists
    if container_name in manually_stopped_containers:
        del manually_stopped_containers[container_name]
        del alerted_containers[container.name]
        
    return {"status": "restarted", "container": container}

async def get_container_logs_op(container_name: str):
    container = docker_client.containers.get(container_name)
    logs = container.logs(tail=10).decode('utf-8')
    return {"logs": logs, "container": container}

# Handlers for the container operations
async def handle_start_command(update: Update, container_name: str) -> None:
    """Handle start container command"""
    logger.info(f"Handling start command for container: {container_name}")
    
    result = await perform_container_operation(
        update, 
        container_name, 
        lambda name: start_container_op(name),
        f"✅ '{container_name}' has been started!"
    )
    
    if result:
        if result["status"] == "already_running":
            await update.message.reply_text(f"ℹ️ '{container_name}' is already running.")
        elif result["status"] == "started":
            await update.message.reply_text(f"✅ '{container_name}' has been started!")

async def handle_stop_command(update: Update, container_name: str) -> None:
    """Handle stop container command"""
    logger.info(f"Handling stop command for container: {container_name}")
    
    result = await perform_container_operation(
        update, 
        container_name, 
        lambda name: stop_container_op(name),
        f"🛑 '{container_name}' has been stopped!"
    )
    
    if result:
        if result["status"] == "already_stopped":
            await update.message.reply_text(f"ℹ️ '{container_name}' is already stopped.")
        elif result["status"] == "stopped":
            await update.message.reply_text(f"🛑 '{container_name}' has been stopped!")

async def handle_restart_command(update: Update, container_name: str) -> None:
    """Handle restart container command"""
    logger.info(f"Handling restart command for container: {container_name}")
    
    result = await perform_container_operation(
        update, 
        container_name, 
        lambda name: restart_container_op(name),
        f"🔄 '{container_name}' has been restarted!"
    )
    
    if result and result["status"] == "restarted":
        await update.message.reply_text(f"🔄 '{container_name}' has been restarted!")

async def handle_logs_command(update: Update, container_name: str) -> None:
    """Handle logs container command"""
    logger.info(f"Handling logs command for container: {container_name}")
    
    result = await perform_container_operation(
        update,
        container_name,
        lambda name: get_container_logs_op(name),
        ""
    )
    
    if result:
        logs = result["logs"]
        if not logs:
            await update.message.reply_text(f"ℹ️ No logs found for '{container_name}'.")
            return
        
        log_message = f"📜 Last 10 logs for '{container_name}':\n\n```\n{logs}\n```"
        await update.message.reply_text(log_message)

# Universal command handler - use regex pattern to extract container name
@restricted
async def universal_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Universal command handler that extracts container name using regex"""
    command_text = update.message.text
    logger.info(f"Universal handler received: {command_text}")
    
    # Direct extraction of command parts
    parts = command_text.split('_', 1)
    if len(parts) < 2:
        logger.warning(f"Command doesn't contain underscore: {command_text}")
        return
    
    cmd_type = parts[0].lstrip('/')
    container_name = '_'.join(parts[1:]).replace('_', '-').strip()
    
    logger.info(f"Parsed command type: {cmd_type}, container: {container_name}")
    
    if cmd_type == "start":
        await handle_start_command(update, container_name)
    elif cmd_type == "stop":
        await handle_stop_command(update, container_name)
    elif cmd_type == "restart":
        await handle_restart_command(update, container_name)
    elif cmd_type == "logs":
        await handle_logs_command(update, container_name)
    else:
        logger.warning(f"Unknown command type: {cmd_type}")
        await update.message.reply_text(f"❌ Unknown command: {cmd_type}")

# Keep the original command handlers for backward compatibility
@restricted
@requires_container_name("start")
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Command to start a container"""
    container_name = context.args[0]
    logger.info(f"Traditional start command for container: {container_name}")
    await handle_start_command(update, container_name)

@restricted
@requires_container_name("stop")
async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Command to stop a container"""
    container_name = context.args[0]
    logger.info(f"Traditional stop command for container: {container_name}")
    await handle_stop_command(update, container_name)

@restricted
@requires_container_name("restart")
async def restart_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Command to restart a container"""
    container_name = context.args[0]
    logger.info(f"Traditional restart command for container: {container_name}")
    await handle_restart_command(update, container_name)

@restricted
@requires_container_name("logs")
async def logs_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Get the last 10 logs from a container"""
    container_name = context.args[0]
    logger.info(f"Traditional logs command for container: {container_name}")
    await handle_logs_command(update, container_name)

@restricted
async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List all containers with clickable command links"""
    try:
        containers = sorted(docker_client.containers.list(all=True), key=lambda c: c.name.lower())
        if not containers:
            await update.message.reply_text("ℹ️ No containers found.")
            return
        
        container_list = "📋 Container List:\n\n"
        for container in containers:
            # Add appropriate emoji based on status
            status_emoji = "🟢" if container.status == "running" else "🔴"
            container_list += f"{status_emoji} {container.name} - Status: {container.status}\n"
            
            # Add clickable command links
            container_name = container.name.replace('-', '_')
            container_list += (
                f"▶️ /start_{container_name}\n"
                f"⏹ /stop_{container_name}\n"
                f"🔄 /restart_{container_name}\n"
                f"📜 /logs_{container_name}\n"
                f"━━━━━━━━━━━━━━━━━━\n\n"
            )
        
        await update.message.reply_text(container_list)
    except Exception as e:
        logger.error(f"Container listing error: {e}")
        await update.message.reply_text(f"❌ Error listing containers: {str(e)}")

@restricted
async def check_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Command to check if a specific container exists"""
    if not context.args or len(context.args) < 1:
        await update.message.reply_text("ℹ️ Please specify a container name: /check container_name")
        return
    
    container_name = context.args[0]
    try:
        containers = docker_client.containers.list(all=True)
        container_found = False
        
        for container in containers:
            if container.name == container_name:
                container_found = True
                await update.message.reply_text(f"✅ Container '{container_name}' exists with status: {container.status}")
                break
        
        if not container_found:
            await update.message.reply_text(f"❌ Container '{container_name}' not found in Docker.")
    
    except Exception as e:
        logger.error(f"Container check error: {e}")
        await update.message.reply_text(f"❌ Error checking container: {str(e)}")

@restricted
async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Info command to show information about the environment"""
    try:
        # Get list of all containers for info
        containers = docker_client.containers.list(all=True)
        container_names = [container.name for container in containers]
        
        info = "🔍 Information:\n\n"
        info += f"Bot Version: 1.0.0\n"
        info += f"Number of containers: {len(containers)}\n"
        info += f"Container names: {', '.join(container_names)}\n"
        info += f"Monitoring enabled: {ENABLE_MONITORING}\n"
        info += f"Manually stopped containers: {list(manually_stopped_containers.keys())}\n"
        
        await update.message.reply_text(info)
    except Exception as e:
        logger.error(f"Info command error: {e}")
        await update.message.reply_text(f"❌ Error generating info: {str(e)}")

async def monitor_containers(application):
    """Monitor container status and send alerts if containers have stopped unexpectedly"""
    global initial_scan_complete
    
    if not ENABLE_MONITORING:
        logger.info("Container monitoring is disabled")
        return
        
    logger.info(f"Container monitoring started (interval: {MONITORING_INTERVAL} seconds)")
    
    while True:
        try:
            containers = docker_client.containers.list(all=True)
            
            # On first run, just record the state of containers without sending alerts
            if not initial_scan_complete:
                logger.info("Initial container scan - recording states without alerting")
                for container in containers:
                    if container.status == "exited" or container.status == "dead":
                        alerted_containers[container.name] = True
                initial_scan_complete = True
            else:
                # Regular monitoring run - check containers and alert if needed
                for container in containers:
                    # If container is stopped and was not manually stopped by us
                    if ((container.status == "exited" or container.status == "dead") 
                            and container.name not in manually_stopped_containers
                            and container.name not in alerted_containers):
                        
                        # Record that we've alerted about this container
                        alerted_containers[container.name] = True
                        
                        # Send alert to all allowed users
                        for user_id in ALLOWED_USER_IDS:
                            await application.bot.send_message(
                                chat_id=user_id,
                                text=f"⚠️ Alert: Container '{container.name}' has stopped unexpectedly! Current status: {container.status}"
                            )
                    
                    # If a container is running again, remove it from alerted list
                    elif container.status == "running" and container.name in alerted_containers:
                        del alerted_containers[container.name]
                
            # Clean up old entries (older than 24 hours) from manually_stopped_containers
            current_time = time.time()
            for name, timestamp in list(manually_stopped_containers.items()):
                if current_time - timestamp > 86400:  # 24 hours
                    del manually_stopped_containers[name]
        
        except Exception as e:
            logger.error(f"Error in container monitoring: {e}")
        
        # Wait for the next check
        await asyncio.sleep(MONITORING_INTERVAL)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Help command"""
    help_text = """
📚 DockeGram Bot Commands

Commands can be used in two formats:

1. Direct command format:
/start_container_name - Start a container
/stop_container_name - Stop a container
/restart_container_name - Restart a container
/logs_container_name - Show last 10 logs from a container

2. Traditional format (still supported):
/start container_name - Start a container
/stop container_name - Stop a container
/restart container_name - Restart a container
/logs container_name - Show last 10 logs from a container
/check container_name - Check if a container exists

Other commands:
/list - List all containers with clickable command links
/help - Show this help message

/info - Show information about the bot environment

Example: /start_my_container or /start my_container
"""
    await update.message.reply_text(help_text)

async def main() -> None:
    """Start the bot"""
    # Check if bot token exists
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_TOKEN environment variable not set!")
        return

    # Create bot
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Add command handlers (traditional format)
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("stop", stop_command))
    application.add_handler(CommandHandler("restart", restart_command))
    application.add_handler(CommandHandler("list", list_command))
    application.add_handler(CommandHandler("logs", logs_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("check", check_command))
    application.add_handler(CommandHandler("info", info_command))

    # Add universal handler for all other containers
    for cmd_type in ["start_", "stop_", "restart_", "logs_"]:
        application.add_handler(MessageHandler(
            filters.Regex(f"^/{cmd_type}[a-zA-Z0-9_-]+$"),
            universal_command_handler
        ))

    # Start the bot
    logger.info("Bot is starting...")
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    
    # Start monitoring after the bot is fully initialized
    if ENABLE_MONITORING:
        monitoring_task = asyncio.create_task(monitor_containers(application))
    
    # Keep the bot running until interrupted
    try:
        # This creates a never-ending task that keeps the event loop running
        await asyncio.Event().wait()
    except (KeyboardInterrupt, SystemExit):
        # When interrupted, stop the monitoring task
        if ENABLE_MONITORING:
            monitoring_task.cancel()
        
        # Stop the application
        await application.updater.stop()
        await application.stop()

if __name__ == "__main__":
    asyncio.run(main())