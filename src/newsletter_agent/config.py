import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

CREDENTIALS_PATH = PROJECT_ROOT / "credentials.json"
TOKEN_PATH = PROJECT_ROOT / "token.json"

DATABASE_PATH = Path(
    os.getenv("DATABASE_PATH", "data/newsletters.db")
)

if not DATABASE_PATH.is_absolute():
    DATABASE_PATH = PROJECT_ROOT / DATABASE_PATH

GMAIL_QUERY = os.getenv(
    "GMAIL_QUERY",
    "label:AI-Newsletters newer_than:2d",
)

MAX_EMAILS_PER_RUN = int(
    os.getenv("MAX_EMAILS_PER_RUN", "50")
)

GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly"
]