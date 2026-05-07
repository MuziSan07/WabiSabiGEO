"""
config.py — Central configuration
Reads from .env locally, from Streamlit secrets on cloud.
"""
import os

# Try loading .env locally — safely ignore if it fails (Streamlit Cloud)
try:
    from dotenv import load_dotenv
    load_dotenv(encoding="utf-8", errors="ignore")
except Exception:
    pass

# Try Streamlit secrets (for cloud deployment)
try:
    import streamlit as st
    for key, value in st.secrets.items():
        if isinstance(value, str):
            os.environ.setdefault(key, value)
except Exception:
    pass

ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
FIRECRAWL_API_KEY: str = os.getenv("FIRECRAWL_API_KEY", "")
GOOGLE_CREDENTIALS_PATH: str = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
GOOGLE_SHEET_ID: str = os.getenv("GOOGLE_SHEET_ID", "")
INDEXNOW_KEY: str = os.getenv("INDEXNOW_KEY", "")
AGENCY_NAME: str = os.getenv("AGENCY_NAME", "Wabi Sabi Agency")
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
APP_HOST: str = os.getenv("APP_HOST", "0.0.0.0")
APP_PORT: int = int(os.getenv("APP_PORT", "8000"))

CLAUDE_MODEL = "claude-sonnet-4-6"
