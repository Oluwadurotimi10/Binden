from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

from newsletter_agent.config import DATABASE_PATH
from newsletter_agent.database import (
    initialise_database,
    save_newsletter,
)
from newsletter_agent.gmail_client import fetch_newsletters
from newsletter_agent.parser import (
    decode_header_value,
    extract_email_content,
)


def get_headers(message: dict) -> dict[str, str]:
    """Convert Gmail headers to a simple dictionary."""
    headers = message.get("payload", {}).get("headers", [])

    return {
        header["name"].lower(): decode_header_value(
            header.get("value", "")
        )
        for header in headers
    }


def normalise_date(
    header_date: str,
    internal_date: str | None,
) -> str:
    """Parse the email date, falling back to Gmail's timestamp."""
    if header_date:
        try:
            dt = parsedate_to_datetime(header_date)

            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)

            return dt.astimezone(timezone.utc).isoformat()
        except (TypeError, ValueError, OverflowError):
            pass

    if internal_date:
        try:
            timestamp = int(internal_date) / 1000
            return datetime.fromtimestamp(
                timestamp,
                tz=timezone.utc,
            ).isoformat()
        except (TypeError, ValueError, OverflowError, OSError):
            pass

    return datetime.now(timezone.utc).isoformat()


def transform_message(message: dict) -> dict:
    """Transform a Gmail API response into our internal schema."""
    headers = get_headers(message)

    return {
        "message_id": message["id"],
        "thread_id": message.get("threadId", ""),
        "sender": headers.get("from", ""),
        "subject": headers.get("subject", "(No subject)"),
        "received_at": normalise_date(
            headers.get("date", ""),
            message.get("internalDate"),
        ),
        "body": extract_email_content(
            message.get("payload", {})
        ),
    }


def run_ingestion() -> dict[str, int]:
    """Fetch, transform and persist new newsletters."""
    initialise_database(DATABASE_PATH)

    messages = fetch_newsletters()

    inserted = 0
    skipped = 0
    empty = 0

    for message in messages:
        newsletter = transform_message(message)

        if not newsletter["body"]:
            empty += 1
            print(
                "No readable body:",
                newsletter["subject"],
            )
            continue

        was_inserted = save_newsletter(
            DATABASE_PATH,
            newsletter,
        )

        if was_inserted:
            inserted += 1
            print("Saved:", newsletter["subject"])
        else:
            skipped += 1
            print("Already processed:", newsletter["subject"])

    return {
        "fetched": len(messages),
        "inserted": inserted,
        "skipped": skipped,
        "empty": empty,
    }


if __name__ == "__main__":
    stats = run_ingestion()
    print("\nIngestion complete:", stats)