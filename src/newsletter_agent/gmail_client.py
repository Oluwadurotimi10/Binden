from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from newsletter_agent.config import (
    CREDENTIALS_PATH,
    GMAIL_SCOPES,
    GMAIL_QUERY,
    MAX_EMAILS_PER_RUN,
    TOKEN_PATH,
)


def authenticate():
    """Authenticate using the local desktop OAuth flow."""
    credentials = None

    if TOKEN_PATH.exists():
        credentials = Credentials.from_authorized_user_file(
            str(TOKEN_PATH),
            GMAIL_SCOPES,
        )

    if not credentials or not credentials.valid:
        if (
            credentials
            and credentials.expired
            and credentials.refresh_token
        ):
            credentials.refresh(Request())
        else:
            if not CREDENTIALS_PATH.exists():
                raise FileNotFoundError(
                    f"Missing OAuth file: {CREDENTIALS_PATH}"
                )

            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_PATH),
                GMAIL_SCOPES,
            )
            credentials = flow.run_local_server(port=0)

        TOKEN_PATH.write_text(credentials.to_json())
        TOKEN_PATH.chmod(0o600)

    return build(
        "gmail",
        "v1",
        credentials=credentials,
        cache_discovery=False,
    )


def list_message_ids(service) -> list[str]:
    """Search Gmail and return matching message IDs."""
    message_ids: list[str] = []
    page_token = None

    while len(message_ids) < MAX_EMAILS_PER_RUN:
        remaining = MAX_EMAILS_PER_RUN - len(message_ids)

        response = (
            service.users()
            .messages()
            .list(
                userId="me",
                q=GMAIL_QUERY,
                maxResults=min(remaining, 100),
                pageToken=page_token,
            )
            .execute()
        )

        message_ids.extend(
            message["id"]
            for message in response.get("messages", [])
        )

        page_token = response.get("nextPageToken")

        if not page_token:
            break

    return message_ids[:MAX_EMAILS_PER_RUN]


def fetch_message(service, message_id: str) -> dict:
    """Fetch the full parsed MIME payload of one message."""
    return (
        service.users()
        .messages()
        .get(
            userId="me",
            id=message_id,
            format="full",
        )
        .execute()
    )


def fetch_newsletters() -> list[dict]:
    """
    Fetch matching emails from Gmail.

    Returns raw Gmail message dictionaries. Parsing and storage
    are handled by separate modules.
    """
    try:
        service = authenticate()
        ids = list_message_ids(service)

        messages = []
        for message_id in ids:
            messages.append(fetch_message(service, message_id))

        return messages

    except HttpError as error:
        raise RuntimeError(
            f"Gmail API request failed: {error}"
        ) from error