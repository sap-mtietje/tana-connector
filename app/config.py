"""Configuration management"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


CLIENT_ID = os.getenv("CLIENT_ID")
TENANT_ID = os.getenv("TENANT_ID")


GRAPH_SCOPES = ["Calendars.Read", "Mail.Read", "Mail.ReadWrite"]


HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
DEBUG = os.getenv("DEBUG", "true").lower() in ("true", "1", "yes")

BASE_DIR = Path(__file__).resolve().parent.parent
AUTH_RECORD_PATH = BASE_DIR / "auth_records" / "auth_record.json"

# Delta token cache settings
DELTA_CACHE_DIR = BASE_DIR / "cache" / "delta_tokens"
DELTA_CACHE_DIR.mkdir(parents=True, exist_ok=True)


def validate_config() -> None:
    """Validate that required configuration is present"""
    if not CLIENT_ID:
        raise ValueError("CLIENT_ID is required in .env file")

    if not TENANT_ID:
        raise ValueError("TENANT_ID is required in .env file")
