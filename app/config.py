"""Application configuration management"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Auth records storage
AUTH_RECORDS_DIR = BASE_DIR / "auth_records"
AUTH_RECORDS_DIR.mkdir(exist_ok=True)
AUTH_RECORD_PATH = AUTH_RECORDS_DIR / "auth_record.json"

# Microsoft Azure AD / Entra ID credentials
CLIENT_ID = os.getenv("CLIENT_ID")
TENANT_ID = os.getenv("TENANT_ID")

# Application settings
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
DEBUG = os.getenv("DEBUG", "true").lower() in ("true", "1", "yes")

# Microsoft Graph API scopes
GRAPH_SCOPES = [
    "Calendars.Read",
    "Calendars.ReadWrite",
    "Mail.Read",
    "Mail.Send",
]

def validate_config() -> None:
    """Validate required configuration values"""
    if not CLIENT_ID:
        raise ValueError("CLIENT_ID is required in .env file")
    if not TENANT_ID:
        raise ValueError("TENANT_ID is required in .env file")


