# db/database.py
# SQLite-backed feedback storage.
# Production: swap DATABASE_URL env var to postgres:// connection string.
# No schema migrations needed — single table, created on startup.

import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./feedback.db")
DB_PATH = Path("feedback.db")


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables if they don't exist. Called at app startup."""
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at   TEXT NOT NULL,
                text_hash    TEXT NOT NULL,
                text_preview TEXT NOT NULL,
                lang_code    TEXT NOT NULL,
                mode_used    TEXT NOT NULL,
                st1_predicted INTEGER,
                st1_correct   INTEGER,
                correction    TEXT,
                raw_response  TEXT
            )
        """)
        conn.commit()
    print("✅ Database initialized.")


def save_feedback(
    text: str,
    lang_code: str,
    mode_used: str,
    st1_predicted: int,
    st1_correct: int | None,
    correction: str | None,
    raw_response: str,
) -> int:
    """
    Store a user feedback record.

    st1_correct: 1 if user confirmed, 0 if user said wrong, None if no feedback yet.
    correction:  Free-text or JSON string of corrected labels.

    Returns inserted row id.
    """
    import hashlib, json

    text_hash = hashlib.sha256(text.encode()).hexdigest()[:16]
    preview = text[:80].replace("\n", " ")

    with _connect() as conn:
        cursor = conn.execute(
            """
            INSERT INTO feedback
                (created_at, text_hash, text_preview, lang_code, mode_used,
                 st1_predicted, st1_correct, correction, raw_response)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now(timezone.utc).isoformat(),
                text_hash,
                preview,
                lang_code,
                mode_used,
                st1_predicted,
                st1_correct,
                correction,
                raw_response,
            ),
        )
        conn.commit()
        return cursor.lastrowid
