"""Unit tests for Gmail message parsing and bounded-query building."""

from __future__ import annotations

import base64
from datetime import UTC, datetime

from growthos.integrations.gmail import GmailClient
from growthos.integrations.gmail_sync import (
    _markers,
    build_initial_query,
    normalize_email,
    parse_message_resource,
)


def _part(mime_type: str, data: str | None = None, *, filename: str = "") -> dict:
    part: dict = {"mimeType": mime_type}
    if filename:
        part["filename"] = filename
        part["body"] = {"attachmentId": "ATT001", "size": 10}
    elif data:
        part["body"] = {"data": base64.urlsafe_b64encode(data.encode()).decode()}
    return part


def _resource(**overrides) -> dict:
    resource = {
        "id": "msg-1",
        "threadId": "thread-1",
        "historyId": "12345",
        "internalDate": "1724100000000",
        "labelIds": ["INBOX", "IMPORTANT"],
        "payload": {
            "headers": [
                {"name": "From", "value": "Jane Doe <jane@example.com>"},
                {"name": "To", "value": "founder@11vatedtech.com"},
                {"name": "Subject", "value": "Quick question about pricing"},
                {"name": "Message-ID", "value": "<rfc123@example.com>"},
            ],
            "parts": [
                _part("text/plain", "Hi, could you send a proposal by Friday? Thanks."),
                _part("application/pdf", filename="spec.pdf"),
            ],
        },
    }
    resource.update(overrides)
    return resource


def test_parse_extracts_headers_body_and_attachments() -> None:
    parsed = parse_message_resource(_resource())
    assert parsed["gmail_message_id"] == "msg-1"
    assert parsed["gmail_thread_id"] == "thread-1"
    assert parsed["history_id"] == "12345"
    assert parsed["rfc_message_id"] == "<rfc123@example.com>"
    assert parsed["sender_name"] == "Jane Doe"
    assert parsed["sender_email"] == "jane@example.com"
    assert parsed["subject"] == "Quick question about pricing"
    assert "could you send a proposal by Friday" in parsed["body"]
    assert parsed["attachments"] == [
        {"filename": "spec.pdf", "mime_type": "application/pdf", "attachment_id": "ATT001", "size": 10}
    ]
    assert parsed["labels"] == ["INBOX", "IMPORTANT"]
    assert parsed["sent_at"].tzinfo is not None


def test_parse_handles_missing_headers() -> None:
    parsed = parse_message_resource({"id": "x", "internalDate": None})
    assert parsed["sender_email"] is None
    assert parsed["subject"] is None
    assert parsed["body"] == ""


def test_initial_query_is_bounded_and_excludes_junk() -> None:
    q = build_initial_query({"lookback_days": 14, "exclude_domains": ["competitor.com"]})
    assert "newer_than:14d" in q
    assert "-in:spam" in q
    assert "-in:trash" in q
    assert "-from:competitor.com" in q


def test_normalize_email() -> None:
    assert normalize_email("  Jane@Example.COM ") == "jane@example.com"
    assert normalize_email(None) is None


def test_signal_detection() -> None:
    hits = _markers("Please send the proposal by EOD. We are evaluating options.")
    assert "question" in hits
    assert "deadline" in hits
    assert "budget" in hits
    assert "buying_signal" in hits
    neutral = _markers("Thanks for the update.")
    assert neutral == {}


def test_get_message_requests_structured_full_format_by_default() -> None:
    """Regression: format=raw returns a MIME blob with no payload, which
    starves the parser (no sender/subject/body). The client must request
    format=full so the structured payload (headers, parts, attachment ids)
    is present, unless raw is explicitly requested."""
    import asyncio

    calls: list[tuple[str, dict]] = []

    async def fake_request(method: str, path: str, **kwargs):
        calls.append((path, kwargs))
        return {}

    client = GmailClient("tok")
    client._request = fake_request  # type: ignore[method-assign]

    async def run():
        await client.get_message("m1")
        await client.get_message("m2", raw=True)

    asyncio.run(run())
    assert calls[0] == ("/users/me/messages/m1", {"params": {"format": "full"}})
    assert calls[1] == ("/users/me/messages/m2", {"params": {"format": "raw"}})


def test_parse_uses_header_date_when_present() -> None:
    resource = _resource()
    resource["payload"]["headers"].append(
        {"name": "Date", "value": "Tue, 20 Aug 2024 10:00:00 +0000"}
    )
    parsed = parse_message_resource(resource)
    assert parsed["sent_at"] == datetime(2024, 8, 20, 10, 0, tzinfo=UTC)
