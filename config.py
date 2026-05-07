"""
config.py — Central configuration via .env
"""
from dotenv import load_dotenv
import os

load_dotenv()

ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
FIRECRAWL_API_KEY: str = os.getenv("FIRECRAWL_API_KEY", "")
GOOGLE_CREDENTIALS_PATH: str = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
GOOGLE_SHEET_ID: str = os.getenv("GOOGLE_SHEET_ID", "")
INDEXNOW_KEY: str = os.getenv("INDEXNOW_KEY", "")
AGENCY_NAME: str = os.getenv("AGENCY_NAME", "Wabi Sabi Agency")
APP_HOST: str = os.getenv("APP_HOST", "0.0.0.0")
APP_PORT: int = int(os.getenv("APP_PORT", "8000"))

CLAUDE_MODEL = "claude-sonnet-4-20250514"
