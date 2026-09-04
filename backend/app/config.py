import os

# QUANTA Configuration Settings
SLACK_WEBHOOK_URL: str = os.getenv("SLACK_WEBHOOK_URL", "")
PORT: int = int(os.getenv("PORT", 3002))
ENV: str = os.getenv("ENV", "production")
