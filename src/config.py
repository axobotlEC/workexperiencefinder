# src/config.py
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DB_PATH = DATA_DIR / "opportunities.db"

USER_AGENT = "WorkExpFinderBot/1.0 (+https://example.org)"
REQUEST_TIMEOUT = 10