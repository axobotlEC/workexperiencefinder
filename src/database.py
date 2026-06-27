# src/database.py
from pathlib import Path
import sqlite3
"""Note: import pandas lazily inside `load_opportunities` to avoid
requiring pandas for scripts that only write to the DB.
"""

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "opportunities.db"
TABLE_NAME = "opportunities"
COLUMNS = (
    "title",
    "company",
    "location",
    "deadline",
    "sector",
    "description",
    "link",
    "source",
    "is_student_opportunity",
    "scrape_validation_passed",
)

def _connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)

def init_db():
    with _connect() as conn:
        conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                company TEXT NOT NULL,
                location TEXT,
                deadline TEXT,
                sector TEXT,
                description TEXT,
                link TEXT NOT NULL UNIQUE,
                source TEXT,
                is_student_opportunity INTEGER DEFAULT 0,
                scrape_validation_passed INTEGER DEFAULT 1
            )
            """
        )
        existing = conn.execute(f"PRAGMA table_info({TABLE_NAME})").fetchall()
        existing_columns = {row[1] for row in existing}
        if "is_student_opportunity" not in existing_columns:
            conn.execute(
                f"ALTER TABLE {TABLE_NAME} ADD COLUMN is_student_opportunity INTEGER DEFAULT 0"
            )
        if "scrape_validation_passed" not in existing_columns:
            conn.execute(
                f"ALTER TABLE {TABLE_NAME} ADD COLUMN scrape_validation_passed INTEGER DEFAULT 1"
            )
        conn.commit()

def _normalise_opportunity(item):
    if hasattr(item, "to_dict"):
        data = item.to_dict()
    elif isinstance(item, dict):
        data = item
    else:
        raise TypeError("Opportunity items must be dictionaries or objects with to_dict().")

    normalized = {column: data.get(column, "") for column in COLUMNS}
    for required in ("title", "company", "link"):
        if not normalized.get(required):
            print("Warning: opportunity missing required canonical field", required, "for item", {
                "title": normalized.get("title"),
                "company": normalized.get("company"),
                "link": normalized.get("link"),
            })

    if normalized.get("is_student_opportunity") in (None, ""):
        normalized["is_student_opportunity"] = 0
    else:
        normalized["is_student_opportunity"] = int(bool(normalized["is_student_opportunity"]))

    if normalized.get("scrape_validation_passed") in (None, ""):
        normalized["scrape_validation_passed"] = 1
    else:
        normalized["scrape_validation_passed"] = int(bool(normalized["scrape_validation_passed"]))

    return normalized

def save_opportunities(items):
    init_db()
    rows = [_normalise_opportunity(item) for item in items]

    if not rows:
        return

    with _connect() as conn:
        conn.executemany(
            f"""
            INSERT INTO {TABLE_NAME} ({", ".join(COLUMNS)})
            VALUES ({", ".join(["?" for _ in COLUMNS])})
            ON CONFLICT(link) DO UPDATE SET
                title = excluded.title,
                company = excluded.company,
                location = excluded.location,
                deadline = excluded.deadline,
                sector = excluded.sector,
                description = excluded.description,
                source = excluded.source,
                is_student_opportunity = excluded.is_student_opportunity,
                scrape_validation_passed = excluded.scrape_validation_passed
            """,
            [tuple(row[column] for column in COLUMNS) for row in rows],
        )
        conn.commit()

def load_opportunities():
    init_db()

    # Import pandas only when loading data for display/analysis
    import pandas as pd

    with _connect() as conn:
        rows = conn.execute(
            f"""
            SELECT title, company, location, deadline, sector, description, link, source, is_student_opportunity, scrape_validation_passed
            FROM {TABLE_NAME}
            ORDER BY company, title
            """
        ).fetchall()

    return pd.DataFrame(rows, columns=COLUMNS)

def clear_opportunities():
    init_db()

    with _connect() as conn:
        conn.execute(f"DELETE FROM {TABLE_NAME}")
        conn.commit()
