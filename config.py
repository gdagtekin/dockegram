import os

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN")
ALLOWED_USER_IDS = list(map(int, os.environ.get("ALLOWED_USER_IDS", "YOUR_ALLOWED_USERS").split(",")))
ENABLE_MONITORING = os.environ.get("ENABLE_MONITORING", "False").lower() == "true"
MONITORING_INTERVAL = int(os.environ.get("MONITORING_INTERVAL", "300"))