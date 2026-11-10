import sqlite3
from pathlib import Path


SCHEMA = """
CREATE TABLE IF NOT EXISTS newsletters (
    message_id TEXT PRIMARY KEY,
    thread_id TEXT,
    sender TEXT,
    subject TEXT,
    received_at TEXT,
    body TEXT NOT NULL,
    ingested_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""


def initialise_database(database_path: Path) -> None:
    database_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(database_path) as connection:
        connection.execute(SCHEMA)


def contains_message(
    database_path: Path,
    message_id: str,
) -> bool:
    with sqlite3.connect(database_path) as connection:
        row = connection.execute(
            """
            SELECT 1
            FROM newsletters
            WHERE message_id = ?
            """,
            (message_id,),
        ).fetchone()

    return row is not None


def save_newsletter(
    database_path: Path,
    newsletter: dict,
) -> bool:
    """
    Insert a newsletter once.

    Returns True if inserted; False if this message ID already exists.
    """
    with sqlite3.connect(database_path) as connection:
        cursor = connection.execute(
            """
            INSERT OR IGNORE INTO newsletters (
                message_id,
                thread_id,
                sender,
                subject,
                received_at,
                body
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                newsletter["message_id"],
                newsletter["thread_id"],
                newsletter["sender"],
                newsletter["subject"],
                newsletter["received_at"],
                newsletter["body"],
            ),
        )

    return cursor.rowcount == 1