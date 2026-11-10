import base64

from newsletter_agent.parser import (
    decode_body,
    extract_body,
    extract_email_content,
)


def encode(text: str) -> str:
    return base64.urlsafe_b64encode(
        text.encode("utf-8")
    ).decode("ascii").rstrip("=")


def test_decode_body():
    assert decode_body(encode("Hello AI")) == "Hello AI"


def test_extract_plain_text():
    payload = {
        "mimeType": "text/plain",
        "body": {"data": encode("Today's AI news")},
    }

    assert extract_email_content(payload) == "Today's AI news"


def test_html_fallback():
    payload = {
        "mimeType": "text/html",
        "body": {
            "data": encode(
                "<html><head><title>Test</title></head>"
                "<body><p>New AI model released</p>"
                "<script>tracking_code()</script>"
                "</body></html>"
            )
        },
    }

    text = extract_email_content(payload)

    assert "New AI model released" in text
    assert "tracking_code" not in text


def test_multipart_plain_text_preferred():
    payload = {
        "mimeType": "multipart/alternative",
        "parts": [
            {
                "mimeType": "text/plain",
                "body": {"data": encode("Plain text version")},
            },
            {
                "mimeType": "text/html",
                "body": {
                    "data": encode("<p>HTML version</p>")
                },
            },
        ],
    }

    plain, html = extract_body(payload)

    assert plain == "Plain text version"
    assert "HTML version" in html