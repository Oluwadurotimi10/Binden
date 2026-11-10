import base64
from email.header import decode_header, make_header

from bs4 import BeautifulSoup


def decode_header_value(value: str | None) -> str:
    """Decode an email header, including encoded non-ASCII text."""
    if not value:
        return ""

    try:
        return str(make_header(decode_header(value)))
    except (ValueError, LookupError):
        return value


def decode_body(data: str | None) -> str:
    """Decode Gmail's URL-safe base64 body representation."""
    if not data:
        return ""

    padding = "=" * (-len(data) % 4)
    raw = base64.urlsafe_b64decode(data + padding)

    # Email content can contain imperfect character encodings.
    return raw.decode("utf-8", errors="replace")


def extract_body(payload: dict) -> tuple[str, str]:
    """
    Return (plain_text, html) from a Gmail message payload.

    Recursively visits MIME parts and skips attachment content.
    """
    plain_parts: list[str] = []
    html_parts: list[str] = []

    def visit(part: dict) -> None:
        mime_type = part.get("mimeType", "")
        filename = part.get("filename", "")
        body = part.get("body", {})

        # Do not accidentally ingest attachment contents.
        if filename:
            return

        if mime_type == "text/plain":
            data = body.get("data")
            if data:
                plain_parts.append(decode_body(data))

        elif mime_type == "text/html":
            data = body.get("data")
            if data:
                html_parts.append(decode_body(data))

        for child in part.get("parts", []):
            visit(child)

    visit(payload)

    plain_text = "\n\n".join(plain_parts).strip()
    html_text = "\n\n".join(html_parts).strip()

    return plain_text, html_text


def clean_html(html: str) -> str:
    """Convert HTML into readable text."""
    soup = BeautifulSoup(html, "html.parser")

    for element in soup(
        ["script", "style", "head", "noscript"]
    ):
        element.decompose()

    return soup.get_text(separator="\n", strip=True)


def extract_email_content(payload: dict) -> str:
    """
    Prefer the plain-text email body.
    Fall back to HTML when plain text is unavailable.
    """
    plain_text, html_text = extract_body(payload)

    content = plain_text or clean_html(html_text)

    # Normalise excessive blank lines without destroying paragraphs.
    lines = [line.strip() for line in content.splitlines()]
    cleaned_lines: list[str] = []
    previous_blank = False

    for line in lines:
        if not line:
            if not previous_blank:
                cleaned_lines.append("")
            previous_blank = True
        else:
            cleaned_lines.append(line)
            previous_blank = False

    return "\n".join(cleaned_lines).strip()