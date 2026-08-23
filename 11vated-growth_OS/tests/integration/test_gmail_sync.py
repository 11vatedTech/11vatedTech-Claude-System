"""Integration tests for the Gmail sync engine against the isolated test DB.

Uses a fake Gmail client with in-memory messages; no network or real account.
"""

from __future__ import annotations

import pytest
from sqlalchemy import func, select

from growthos.domain.models_comms import Conversation, FounderInboxItem, Message
from growthos.domain.models_evidence import ClaimEvidence, IntelligenceClaim, SourceEvidence
from growthos.domain.models_identity import IntegrationAccount, Person
from growthos.integrations.gmail import GmailApiError
from growthos.integrations.gmail_sync import sync_once


class FakeGmailClient:
    """In-memory Gmail API stand-in."""

    def __init__(self, messages: list[dict], *, history: dict[int, list[str]] | None = None):
        self.messages = {m["id"]: m for m in messages}
        self.history = history or {}
        self.profile_calls = 0
        self.list_calls = 0
        self.history_404 = False

    async def profile(self):
        self.profile_calls += 1
        return {"emailAddress": "founder@11vatedtech.com"}

    async def list_messages(self, *, query="", max_results=50, page_token=None):
        self.list_calls += 1
        ids = list(self.messages.keys())
        return {"messages": [{"id": i} for i in ids], "nextPageToken": None}

    async def get_message(self, message_id, *, raw=True):
        if message_id not in self.messages:
            raise GmailApiError(404, "message not found")
        return self.messages[message_id]

    async def history_list(self, history_id, *, history_types="messageAdded"):
        if self.history_404:
            raise GmailApiError(404, "history id too old")
        return {
            "history": [
                {"id": hid, "messages": [{"id": mid} for mid in mids]}
                for hid, mids in self.history.items()
                if hid > history_id
            ]
        }


def _msg(
    message_id: str,
    *,
    thread: str = "thread-1",
    history_id: str = "100",
    sender: str = "jane@example.com",
    subject: str | None = None,
    body: str | None = None,
) -> dict:
    import base64

    def part(mime: str, data: str) -> dict:
        return {"mimeType": mime, "body": {"data": base64.urlsafe_b64encode(data.encode()).decode()}}

    subject = subject or f"Quick question {message_id}"
    body = body or f"Hi, could you send a proposal by Friday? (ref {message_id})"
    return {
        "id": message_id,
        "threadId": thread,
        "historyId": history_id,
        "internalDate": "1724100000000",
        "labelIds": ["INBOX"],
        "payload": {
            "headers": [
                {"name": "From", "value": f"Jane Doe <{sender}>"},
                {"name": "To", "value": "founder@11vatedtech.com"},
                {"name": "Subject", "value": subject},
            ],
            "parts": [part("text/plain", body)],
        },
    }


async def _counts(session) -> dict[str, int]:
    return {
        "messages": await session.scalar(select(func.count(Message.id))),
        "evidence": await session.scalar(select(func.count(SourceEvidence.id))),
        "conversations": await session.scalar(select(func.count(Conversation.id))),
        "persons": await session.scalar(select(func.count(Person.id))),
        "claims": await session.scalar(select(func.count(IntelligenceClaim.id))),
        "inbox": await session.scalar(select(func.count(FounderInboxItem.id))),
    }


async def test_initial_sync_ingests_and_is_idempotent(session) -> None:
    client = FakeGmailClient([_msg("m1"), _msg("m2", history_id="101", thread="thread-2")])
    first = await sync_once(session, client=client)
    await session.commit()
    assert first["mode"] == "initial"
    assert first["ingested"] == 2
    counts = await _counts(session)
    assert counts["messages"] == 2
    assert counts["evidence"] == 2
    assert counts["conversations"] == 2

    # Second run as a full rescan (cursor cleared): same mailbox -> zero
    # duplicates, enforced by database uniqueness, not app checks.
    account = await session.scalar(
        select(IntegrationAccount).where(IntegrationAccount.provider == "gmail")
    )
    account.health = {**account.health, "history_id": None}
    await session.flush()
    second = await sync_once(session, client=client)
    await session.commit()
    assert second["ingested"] == 0
    assert second["skipped"] == 2
    counts = await _counts(session)
    assert counts["messages"] == 2
    assert counts["evidence"] == 2


async def test_cursor_advances_and_incremental_sync_ingests_new(session) -> None:
    client = FakeGmailClient([_msg("m1", history_id="100")])
    await sync_once(session, client=client)
    await session.commit()
    account = await session.scalar(select(IntegrationAccount).where(IntegrationAccount.provider == "gmail"))
    assert int(account.health["history_id"]) >= 100
    assert account.health["last_mode"] == "initial"

    # New message at a later history id; history lists it.
    client.messages["m2"] = _msg("m2", history_id="200", thread="thread-2")
    client.history = {200: ["m2"]}
    second = await sync_once(session, client=client)
    await session.commit()
    assert second["mode"] == "incremental"
    assert second["ingested"] == 1
    counts = await _counts(session)
    assert counts["messages"] == 2


async def test_cursor_recovery_on_404(session) -> None:
    client = FakeGmailClient([_msg("m1", history_id="100"), _msg("m2", history_id="101")])
    await sync_once(session, client=client)
    await session.commit()

    client.history_404 = True
    third = await sync_once(session, client=client)
    await session.commit()
    assert third["mode"] == "recovery"
    assert third["ingested"] == 0  # already present; no duplicates
    counts = await _counts(session)
    assert counts["messages"] == 2


async def test_sender_identity_reuse_and_evidence_linkage(session) -> None:
    client = FakeGmailClient(
        [
            _msg("m1", sender="jane@example.com", thread="t1"),
            _msg("m2", sender="jane@example.com", thread="t2", subject="Second email"),
        ]
    )
    await sync_once(session, client=client)
    await session.commit()
    persons = (await session.execute(select(Person))).scalars().all()
    assert len(persons) == 1
    assert persons[0].email == "jane@example.com"
    assert persons[0].title is None  # never invented

    links = await session.scalar(select(func.count(ClaimEvidence.id)))
    assert links >= 2  # every claim is linked to its evidence

    # Pipeline gate: an arbitrary Gmail sender is NOT inbox-eligible.
    # Merely receiving email never promotes someone into the Founder Inbox.
    from growthos.domain.models_commercial import Opportunity
    from growthos.intelligence.pipeline_gate import evaluate_inbox_eligibility
    from growthos.intelligence.relationships import admit_existing_client
    from growthos.services.reclassify import reclassify_all

    inbox = await session.scalar(select(func.count(FounderInboxItem.id)))
    assert inbox == 0  # no pipeline relationship exists yet
    assert await session.scalar(select(func.count(Opportunity.id))) == 0

    eligible, reason, _ = await evaluate_inbox_eligibility(session, sender_email="jane@example.com")
    assert not eligible
    assert "pipeline" in reason.lower() or "relationship" in reason.lower()

    # Founder explicitly admits the sender as an existing client -> inbox-eligible.
    person = (await session.execute(select(Person))).scalars().one()
    await admit_existing_client(session, person_id=person.id)
    await session.commit()

    eligible, reason, _ = await evaluate_inbox_eligibility(session, sender_email="jane@example.com")
    assert eligible

    # Rebuild the inbox through the gate — the client's question now appears.
    report = await reclassify_all(session)
    await session.commit()
    assert report["items_created"] >= 1
    inbox = await session.scalar(select(func.count(FounderInboxItem.id)))
    assert inbox >= 1


async def test_rollback_leaves_no_partial_state(session, session_factory) -> None:
    class BoomClient(FakeGmailClient):
        async def get_message(self, message_id, *, raw=True):
            if message_id == "m2":
                raise RuntimeError("boom")
            return await super().get_message(message_id, raw=raw)

    with pytest.raises(RuntimeError):
        await sync_once(session, client=BoomClient([_msg("m1"), _msg("m2")]))
    await session.rollback()

    async with session_factory() as check:
        assert await check.scalar(select(func.count(Message.id))) == 0
        assert await check.scalar(select(func.count(SourceEvidence.id))) == 0
