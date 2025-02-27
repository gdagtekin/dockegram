# Dockegram

Dockegram is a Telegram bot that allows you to manage Docker containers directly through Telegram messages. With Dockegram, you can start, stop, restart containers, view logs, and monitor container status, all from your Telegram app.

## Features

- Start, stop, and restart Docker containers
- View container logs
- List all containers with their current status
- Check if specific containers exist
- Automatic monitoring of container status with alerts for unexpected stops
- User authentication to restrict access to authorized users only

## Prerequisites

- Docker installed on your host machine
- Telegram Bot Token (obtained from BotFather)
- Telegram User ID of authorized users

### Creating a Telegram Bot

1. Open Telegram and search for `@BotFather`
2. Start a chat with BotFather and send the command `/newbot`
3. Follow the instructions to create your bot
4. Once created, BotFather will provide you with a token. Save this token for later use.

### Getting Your Telegram User ID


1. Send a message to `@userinfobot` on Telegram
2. The bot will reply with your User ID and other information

## Installation and Usage

### Method 1: Using Docker Compose

1. Create a `docker-compose.yml` file with the following content:

```yaml
version: '3.9'

services:
  dockergram:
    image: gdagtekin/dockegram:latest
    container_name: dockegram
    restart: unless-stopped
    environment:
      - TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN
      - ALLOWED_USER_IDS=YOUR_USER_ID
      - ENABLE_MONITORING=True
      - MONITORING_INTERVAL=300
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
```

2. Replace `YOUR_BOT_TOKEN` and `YOUR_USER_ID` with your actual values
3. Run the following command in the same directory as your `docker-compose.yml` file:

```bash
docker compose up -d
```

### Method 2: Using Docker Run

```bash
docker run -d \
  --name dockegram \
  --restart unless-stopped \
  -e TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN \
  -e ALLOWED_USER_IDS=YOUR_USER_ID \
  -e ENABLE_MONITORING=True \
  -e MONITORING_INTERVAL=300 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  gdagtekin/dockegram:latest
```

Replace `YOUR_BOT_TOKEN` with the token provided by BotFather and `YOUR_USER_ID` with your Telegram User ID. If you want to allow multiple users, separate their IDs with commas (e.g., `123456789,987654321`).

### Method 3: Building from Source

1. Clone the repository:

```bash
git clone https://github.com/gdagtekin/dockegram.git
cd dockegram
```

2. Build the Docker image:

```bash
docker build -t dockegram .
```

3. Run the container:

```bash
docker run -d \
  --name dockegram \
  --restart unless-stopped \
  -e TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN \
  -e ALLOWED_USER_IDS=YOUR_USER_ID \
  -e ENABLE_MONITORING=True \
  -e MONITORING_INTERVAL=300 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  dockegram
```

## Configuration Options

You can configure Dockegram using the following environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `TELEGRAM_BOT_TOKEN` | Your Telegram Bot token | Required |
| `ALLOWED_USER_IDS` | Comma-separated list of authorized Telegram User IDs | Required |
| `ENABLE_MONITORING` | Enable automatic container monitoring | False |
| `MONITORING_INTERVAL` | Monitoring check interval in seconds | 300 |

## Bot Commands

Dockegram supports two command formats:

### Direct Command Format (Recommended)

- `/start_container_name` - Start a container
- `/stop_container_name` - Stop a container
- `/restart_container_name` - Restart a container
- `/logs_container_name` - Show last 10 logs from a container

### Traditional Format (Also Supported)

- `/start container_name` - Start a container
- `/stop container_name` - Stop a container
- `/restart container_name` - Restart a container
- `/logs container_name` - Show last 10 logs from a container
- `/check container_name` - Check if a container exists

### Other Commands

- `/list` - List all containers with clickable command links
- `/help` - Show help message
- `/info` - Show information about the bot environment

## Usage Examples

- To start a container named "nginx": `/start_nginx` or `/start nginx`
- To stop a container: `/stop_nginx` or `/stop nginx`
- To view container logs: `/logs_nginx` or `/logs nginx`
- To list all containers: `/list`

## Monitoring Feature

When `ENABLE_MONITORING` is set to `True`, Dockegram will periodically check the status of all containers. If a container stops unexpectedly (not manually stopped through the bot), Dockegram will send an alert message to all authorized users.

## Security Considerations

- The bot only allows commands from users listed in `ALLOWED_USER_IDS`
- The Docker socket is mounted into the container, which gives the bot full control over your Docker environment
- Only give access to users you trust with full Docker control

## License

Distributed under the AGPLv3 License. See [`LICENSE.md`](https://github.com/gdagtekin/dockegram/blob/main/LICENSE) for more information.

## Credits

Developed by Gökhan Dağtekin
