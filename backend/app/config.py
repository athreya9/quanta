import os
from pathlib import Path
from dotenv import load_dotenv

# Search for .env in project root, backend folder, or working directory
base_dir = Path(__file__).resolve().parent.parent.parent
env_files = [
    base_dir / ".env",
    base_dir / "backend" / ".env",
    Path(".env")
]

for env_path in env_files:
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
        break
else:
    load_dotenv()

SLACK_WEBHOOK_URL: str = os.getenv("SLACK_WEBHOOK_URL", "")
PORT: int = int(os.getenv("PORT", 3002))
ENV: str = os.getenv("ENV", "production")

# INTENT_MODE can be 'production' (default) or 'demo'
INTENT_MODE: str = os.getenv("INTENT_MODE", "production").lower().strip()
