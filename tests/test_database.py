import sqlite3
from newsletter_agent.config import DATABASE_PATH
from newsletter_agent.database import (
    initialise_database,
    save_newsletter,
)

def test_duplicate_newsletter_is_not_inserted():
    initialise_database(DATABASE_PATH)

    newsletter = {
        "message_id": "message-123",
        "thread_id": "thread-123",
        "sender": "test@example.com",
        "subject": "AI Newsletter",
        "received_at": "2026-11-15T10:00:00+00:00",
        "body": "Newsletter content",
        "body_html": "<p>Newsletter content</p>",
    }

    assert save_newsletter(DATABASE_PATH, newsletter) is True
    assert save_newsletter(DATABASE_PATH, newsletter) is False

    with sqlite3.connect(DATABASE_PATH) as connection:
        count = connection.execute(
            "SELECT COUNT(*) FROM newsletters"
        ).fetchone()[0]

    assert count == 1