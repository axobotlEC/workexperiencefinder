from pathlib import Path
import sqlite3

import pandas as pd

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
                source TEXT
            )
            """
        )
        conn.commit()

def _normalise_opportunity(item):
    if hasattr(item, "to_dict"):
        data = item.to_dict()
    elif isinstance(item, dict):
        data = item
    else:
        raise TypeError("Opportunity items must be dictionaries or objects with to_dict().")

    return {column: data.get(column, "") for column in COLUMNS}

def save_opportunities(items):
    init_db()
    rows = [_normalise_opportunity(item) for item in items]

    if not rows:
        return

    with _connect() as conn:
        conn.executemany(
            f"""
            INSERT INTO {TABLE_NAME} ({", ".join(COLUMNS)})
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(link) DO UPDATE SET
                title = excluded.title,
                company = excluded.company,
                location = excluded.location,
                deadline = excluded.deadline,
                sector = excluded.sector,
                description = excluded.description,
                source = excluded.source
            """,
            [tuple(row[column] for column in COLUMNS) for row in rows],
        )
        conn.commit()

def load_opportunities():
    init_db()

    with _connect() as conn:
        rows = conn.execute(
            f"""
            SELECT title, company, location, deadline, sector, description, link, source
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