"""
services/sheets_service.py
Save and load client configs from Google Sheets.
"""
import gspread
from google.oauth2.service_account import Credentials
from config import GOOGLE_CREDENTIALS_PATH, GOOGLE_SHEET_ID

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

HEADERS = [
    "client_name", "client_url",
    "competitor_1", "competitor_2", "competitor_3",
    "audience", "wabisabi_attribution", "timestamp"
]


def _get_sheet():
    creds = Credentials.from_service_account_file(GOOGLE_CREDENTIALS_PATH, scopes=SCOPES)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(GOOGLE_SHEET_ID)
    try:
        ws = sh.worksheet("clients")
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title="clients", rows=100, cols=20)
        ws.append_row(HEADERS)
    return ws


def save_client(data: dict) -> bool:
    try:
        ws = _get_sheet()
        from datetime import datetime
        row = [
            data.get("client_name", ""),
            data.get("client_url", ""),
            data.get("competitor_1", ""),
            data.get("competitor_2", ""),
            data.get("competitor_3", ""),
            data.get("audience", ""),
            "Yes" if data.get("wabisabi_attribution") else "No",
            datetime.utcnow().isoformat(),
        ]
        ws.append_row(row)
        return True
    except Exception as e:
        print(f"[Sheets] Save error: {e}")
        return False


def load_clients() -> list[dict]:
    try:
        ws = _get_sheet()
        records = ws.get_all_records()
        return records
    except Exception as e:
        print(f"[Sheets] Load error: {e}")
        return []
