"""Gmail synchronization engine.

Flow per run:

    retrieve (initial bounded query OR history.list)
    -> persist evidence + message + conversation + identities transactionally
    -> commit
    -> advance sync cursor (stored in IntegrationAccount.health)

The cursor is only advanced inside the same transaction that persists the
messages, so it can never run ahead of what is actually stored. If Gmail
reports the stored history id as too old (HTTP 404), a bounded recovery sync
establishes a fresh cursor.

Raw source evidence (SourceEvidence) and derived intelligence (claims) are
stored separately and linked by id. No Opportunity is ever created from an
email alone — only an Opportunity Hypothesis claim.
"""

from __future__ import annotations

import base64
import re
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from growthos.audit import record_audit
from growthos.config import get_settings
from growthos.domain.enums import (
    ChannelType,
    ClaimTag,
    FounderAttentionKind,
    FounderInboxKind,
    FounderInboxStatus,
    IntegrationStatus,
    TruthClass,
)
from growthos.domain.enums import (
    MessageClassification as MessageClass,
)
from growthos.domain.models_comms import (
    Conversation,
    FounderInboxItem,
    Message,
    MessageClassification,
)
from growthos.domain.models_evidence import ClaimEvidence, IntelligenceClaim, SourceEvidence
from growthos.domain.models_identity import IntegrationAccount, IntegrationEvent, Person
from growthos.integrations.gmail import GmailApiError, GmailClient
from growthos.intelligence.commercial import classify_message
from growthos.intelligence.evidence import record_evidence
from growthos.intelligence.pipeline_gate import evaluate_inbox_eligibility
from growthos.shared.ids import new_id

# ---------------------------------------------------------------------------
# Parsing (pure)
# ---------------------------------------------------------------------------


def _email_tuple(value: str | None) -> tuple[str | None, str | None]:
    """Split an RFC header into (name, email)."""
    if not value:
        return None, None
    match = re.search(r"<([^>]+)>", value)
    if match:
        name = value[: match.start()].strip(" \"'") or None
        return name, match.group(1).strip().lower()
    stripped = value.strip()
    return None, stripped.lower() if "@" in stripped else None


def _collect_text(part: Any, texts: list[str], attachments: list[dict[str, Any]]) -> None:
    filename = part.get("filename") or ""
    if filename:
        body = part.get("body", {})
        attachments.append(
            {
                "filename": filename,
                "mime_type": part.get("mimeType"),
                "attachment_id": body.get("attachmentId"),
                "size": body.get("size"),
            }
        )
        return
    mime = part.get("mimeType", "")
    if mime == "text/plain":
        data = part.get("body", {}).get("data")
        if data:
            try:
                texts.append(base64.urlsafe_b64decode(data).decode("utf-8", "replace"))
            except Exception:  # noqa: BLE001 - best effort body decode
                texts.append("")
    for child in part.get("parts", []):
        _collect_text(child, texts, attachments)


def parse_message_resource(resource: dict[str, Any]) -> dict[str, Any]:
    """Parse a Gmail message resource into a flat, persistence-ready dict."""
    payload = resource.get("payload") or {}
    headers = {h["name"].lower(): h["value"] for h in payload.get("headers", [])}
    texts: list[str] = []
    attachments: list[dict[str, Any]] = []
    _collect_text(payload, texts, attachments)

    internal_date = resource.get("internalDate")
    sent_at = datetime.fromtimestamp(int(internal_date) / 1000, tz=UTC) if internal_date else datetime.now(UTC)
    header_date = headers.get("date")
    if header_date:
        try:
            parsed = parsedate_to_datetime(header_date)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=UTC)
            sent_at = parsed.astimezone(UTC)
        except Exception:  # noqa: BLE001 - fall back to internalDate
            pass

    sender_name, sender_email = _email_tuple(headers.get("from"))
    return {
        "gmail_message_id": resource["id"],
        "gmail_thread_id": resource.get("threadId"),
        "history_id": resource.get("historyId"),
        "rfc_message_id": headers.get("message-id"),
        "sender_name": sender_name,
        "sender_email": sender_email,
        "to": headers.get("to"),
        "cc": headers.get("cc"),
        "subject": headers.get("subject"),
        "body": "\n".join(texts).strip(),
        "sent_at": sent_at,
        "attachments": attachments,
        "labels": resource.get("labelIds", []),
        # Headers useful for deterministic bulk/automated detection. Keys are
        # lowercased; values are raw header strings.
        "headers": {
            k: headers[k]
            for k in (
                "list-unsubscribe",
                "list-id",
                "list-post",
                "precedence",
                "auto-submitted",
                "x-auto-response-suppress",
                "x-feedback-id",
                "x-campaign-id",
                "x-mailer",
                "return-path",
                "x-originating-ip",
                "x-mailing-list",
            )
            if k in headers
        },
    }


def build_initial_query(config: dict[str, Any] | None = None) -> str:
    """Build a bounded Gmail search query (never the whole mailbox by default)."""
    settings = get_settings()
    cfg = config or {}
    parts: list[str] = []
    lookback_days = int(cfg.get("lookback_days") or settings.gmail_initial_lookback_days)
    parts.append(f"newer_than:{lookback_days}d")
    # Spam and Trash are always excluded.
    parts.append("-in:spam")
    parts.append("-in:trash")
    for label in cfg.get("include_labels") or []:
        parts.append(f"in:{label}")
    for label in cfg.get("exclude_labels") or []:
        parts.append(f"-in:{label}")
    for sender in cfg.get("exclude_senders") or []:
        parts.append(f"-from:{sender}")
    for domain in cfg.get("exclude_domains") or []:
        parts.append(f"-from:{domain}")
    return " ".join(parts)


# ---------------------------------------------------------------------------
# Identity resolution
# ---------------------------------------------------------------------------


def normalize_email(email: str | None) -> str | None:
    if not email:
        return None
    return email.strip().lower()


async def resolve_person(
    session: AsyncSession,
    *,
    email: str | None,
    full_name: str | None,
    evidence: SourceEvidence,
) -> Person | None:
    """Match an existing Person by normalized email; create only from evidence.

    Unknown fields (title, company, phone, location, authority) stay unknown.
    """
    email = normalize_email(email)
    if not email:
        return None
    result = await session.execute(select(Person).where(Person.email == email))
    existing = result.scalar_one_or_none()
    if existing is not None:
        return existing
    person = Person(
        id=new_id(),
        full_name=full_name or email.split("@")[0] or "Unknown sender",
        email=email,
        origin_source="gmail",
        origin_evidence_id=evidence.id,
        external_ids={"gmail": []},
    )
    session.add(person)
    await session.flush()
    return person


# ---------------------------------------------------------------------------
# Rule-based conversation intelligence (deterministic; no invented facts)
# ---------------------------------------------------------------------------


QUESTION_MARKERS = re.compile(
    r"(please|could you|can you|would you|do you|are you|is it|any update|"
    r"following up|thoughts\?|when (can|will)|how (can|soon))",
    re.IGNORECASE,
)
DEADLINE_MARKERS = re.compile(
    r"(by (?:monday|tuesday|wednesday|thursday|friday|saturday|sunday|"
    r"tomorrow|eod|end of (?:the )?day|next week|\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?)|"
    r"deadline|due date|needed by|required by)",
    re.IGNORECASE,
)
BUDGET_MARKERS = re.compile(
    r"(budget|pricing|price|cost|quote|proposal|estimate|rate)",
    re.IGNORECASE,
)
COMMITMENT_MARKERS = re.compile(
    r"(i will|we will|i'll|we'll|promise|commit to|send you|get back to you)",
    re.IGNORECASE,
)
OBJECTION_MARKERS = re.compile(
    r"(too expensive|not interested|no budget|can't afford|not a priority|"
    r"too busy|happy with (current|existing))",
    re.IGNORECASE,
)
BUYING_MARKERS = re.compile(
    r"(interested in|looking for|need help with|considering|exploring|"
    r"evaluating|we need|we're looking)",
    re.IGNORECASE,
)


def _markers(text: str) -> dict[str, list[str]]:
    hits: dict[str, list[str]] = {}
    for label, pattern in (
        ("question", QUESTION_MARKERS),
        ("deadline", DEADLINE_MARKERS),
        ("budget", BUDGET_MARKERS),
        ("commitment", COMMITMENT_MARKERS),
        ("objection", OBJECTION_MARKERS),
        ("buying_signal", BUYING_MARKERS),
    ):
        found = pattern.findall(text)
        if found:
            hits[label] = [str(f) for f in found]
    return hits


async def extract_intelligence(
    session: AsyncSession,
    *,
    parsed: dict[str, Any],
    evidence: SourceEvidence,
    classification: MessageClassification | None = None,
) -> list[IntelligenceClaim]:
    """Derive INFERENCE/HYPOTHESIS claims from a real message, linked to it.

    Opportunity-style hypotheses are gated on the commercial classification:
    promotional/newsletter/social/transactional messages never produce them.
    """
    body = parsed.get("body") or ""
    subject = parsed.get("subject") or ""
    text = f"{subject}\n{body}"
    signals = _markers(text)
    claims: list[IntelligenceClaim] = []

    def add_claim(
        text: str,
        truth_class: TruthClass,
        *,
        tag: ClaimTag | None = None,
        reasoning: str | None = None,
        confidence: float = 0.5,
        entity_type: str | None = None,
        entity_id: str | None = None,
    ) -> None:
        claim = IntelligenceClaim(
            id=new_id(),
            claim_type=truth_class,
            text=text,
            reasoning=reasoning,
            confidence=confidence,
            tag=tag,
            entity_type=entity_type,
            entity_id=entity_id,
        )
        session.add(claim)
        session.add(
            ClaimEvidence(
                id=new_id(), claim_id=claim.id, evidence_id=evidence.id, role="supports"
            )
        )
        claims.append(claim)

    # Opportunity Hypothesis gating: generic promotional language must never
    # produce a commercial hypothesis. Only business classes qualify, and only
    # when a buying signal is present.
    business_classes = {
        MessageClass.BUSINESS_CLIENT,
        MessageClass.BUSINESS_PROSPECT,
        MessageClass.BUSINESS_PARTNER,
        MessageClass.BUSINESS_REFERRAL,
        MessageClass.BUSINESS_NETWORK,
        MessageClass.BUSINESS_SERVICE,
        MessageClass.BUSINESS_VENDOR,
    }
    if signals.get("buying_signal") and (
        classification is None or classification.primary_class in business_classes
    ):
        add_claim(
            "Possible commercial interest expressed in email",
            TruthClass.HYPOTHESIS,
            tag=ClaimTag.COMMERCIAL_HYPOTHESIS,
            reasoning=(
                "Buying-signal language detected in a business-classified message"
                if classification is not None
                else "Buying-signal language detected in a real message"
            ),
            confidence=0.4,
            entity_type="gmail_message",
            entity_id=parsed["gmail_message_id"],
        )
    if signals.get("objection"):
        add_claim(
            "Objection raised in email",
            TruthClass.INFERENCE,
            reasoning="Objection language detected",
            confidence=0.6,
            entity_type="gmail_message",
            entity_id=parsed["gmail_message_id"],
        )
    if signals.get("budget"):
        add_claim(
            "Budget/pricing topic present in email",
            TruthClass.INFERENCE,
            reasoning="Budget or pricing language detected",
            confidence=0.55,
            entity_type="gmail_message",
            entity_id=parsed["gmail_message_id"],
        )
    if signals.get("commitment"):
        add_claim(
            "Commitment statement present in email",
            TruthClass.INFERENCE,
            reasoning="Commitment language detected",
            confidence=0.6,
            entity_type="gmail_message",
            entity_id=parsed["gmail_message_id"],
        )
    if signals.get("deadline"):
        add_claim(
            "Deadline referenced in email",
            TruthClass.INFERENCE,
            reasoning="Deadline language detected",
            confidence=0.6,
            entity_type="gmail_message",
            entity_id=parsed["gmail_message_id"],
        )
    return claims


async def persist_classification(
    session: AsyncSession,
    *,
    message: Message,
    parsed: dict[str, Any],
    relationship_context: dict[str, Any] | None = None,
) -> MessageClassification:
    """Classify a message and persist the structured result (idempotent)."""
    result = classify_message(parsed, relationship_context=relationship_context)
    existing = await session.execute(
        select(MessageClassification).where(
            MessageClassification.message_id == message.id
        )
    )
    row = existing.scalar_one_or_none()
    if row is None:
        row = MessageClassification(
            id=new_id(),
            message_id=message.id,
            primary_class=result.primary,
            secondary_tags=result.secondary_tags,
            relevance_score=result.relevance_score,
            attention_score=result.attention_score,
            attention_kinds=result.attention_kinds,
            confidence=result.confidence,
            evidence=result.evidence,
            reasoning=result.reasoning,
            classifier_version=result.version,
        )
        session.add(row)
    else:
        row.primary_class = result.primary
        row.secondary_tags = result.secondary_tags
        row.relevance_score = result.relevance_score
        row.attention_score = result.attention_score
        row.attention_kinds = result.attention_kinds
        row.confidence = result.confidence
        row.evidence = result.evidence
        row.reasoning = result.reasoning
        row.classifier_version = result.version
    await session.flush()
    return row


# Founder Inbox is pipeline-scoped: a promotional/social/newsletter sender is
# never eligible, and a real business sender is eligible only when the gate
# verifies an active pipeline relationship (see intelligence.pipeline_gate).
ATTENTION_THRESHOLD = 40.0


async def create_inbox_items(
    session: AsyncSession,
    *,
    parsed: dict[str, Any],
    evidence: SourceEvidence,
    message: Message,
    classification: MessageClassification,
) -> list[FounderInboxItem]:
    """Create Founder Inbox items ONLY through the pipeline gate.

    A message enters Founder Inbox only if ALL of:
      1. the sender passes evaluate_inbox_eligibility (active pipeline
         relationship — outreach sent, client, partner, active opportunity), and
      2. the founder-attention score exceeds the threshold, and
      3. the classification is not a never-inbox class.
    Otherwise it stays in Communications only.
    """
    created: list[FounderInboxItem] = []
    message_id = parsed["gmail_message_id"]
    subject = parsed.get("subject") or "(no subject)"
    sender = parsed.get("sender_email")

    eligible, gate_reason, _ctx = await evaluate_inbox_eligibility(
        session, sender_email=sender
    )
    if not eligible:
        return created

    never_inbox = {
        MessageClass.PROMOTIONAL,
        MessageClass.NEWSLETTER,
        MessageClass.SOCIAL_NOTIFICATION,
        MessageClass.TRANSACTIONAL,
        MessageClass.SPAM_OR_LOW_VALUE,
    }
    if classification.primary_class in never_inbox:
        return created
    if classification.attention_score < ATTENTION_THRESHOLD:
        return created

    kinds = classification.attention_kinds or []
    priority = min(10, 2 + int(classification.attention_score // 10))

    async def add_item(
        kind: FounderInboxKind,
        title: str,
        summary: str,
        p: int,
    ) -> None:
        item = FounderInboxItem(
            id=new_id(),
            kind=kind,
            title=title,
            summary=summary,
            entity_type="person",
            entity_id=_ctx.get("person_id"),
            source_evidence_id=evidence.id,
            status=FounderInboxStatus.UNREAD,
            priority=p,
            payload={
                "gmail_message_id": message_id,
                "gate_reason": gate_reason,
                "classification": classification.primary_class.value,
                "relevance_score": classification.relevance_score,
                "attention_score": classification.attention_score,
            },
        )
        session.add(item)
        created.append(item)

    if FounderAttentionKind.SECURITY_ISSUE in kinds:
        await add_item(
            FounderInboxKind.EMAIL_NEEDS_RESPONSE,
            f"Security matter from {sender}: {subject}",
            f"From {sender}: security issue flagged ({gate_reason}).",
            priority + 2,
        )
    elif FounderAttentionKind.SYSTEM_FAILURE in kinds:
        await add_item(
            FounderInboxKind.INTEGRATION_FAILED,
            f"System alert from {sender}: {subject}",
            f"From {sender}: system-failure language flagged ({gate_reason}).",
            priority + 1,
        )
    elif FounderAttentionKind.PAYMENT_ISSUE in kinds:
        await add_item(
            FounderInboxKind.CLIENT_REQUIREMENT,
            f"Payment matter from {sender}: {subject}",
            f"From {sender}: payment/invoice language flagged ({gate_reason}).",
            priority,
        )
    elif kinds:
        await add_item(
            FounderInboxKind.EMAIL_NEEDS_RESPONSE,
            f"Actionable from {sender}: {subject}",
            f"From {sender}: attention drivers {', '.join(kinds)} ({gate_reason}).",
            priority,
        )
    return created


# ---------------------------------------------------------------------------
# Sync orchestration
# ---------------------------------------------------------------------------


async def _get_or_create_account(
    session: AsyncSession, *, profile: dict[str, Any], granted_scopes: list[str]
) -> IntegrationAccount:
    result = await session.execute(
        select(IntegrationAccount).where(
            IntegrationAccount.kind == "gmail", IntegrationAccount.provider == "gmail"
        )
    )
    account = result.scalar_one_or_none()
    if account is None:
        account = IntegrationAccount(
            id=new_id(),
            kind="gmail",
            provider="gmail",
            external_account_id=profile.get("emailAddress"),
            display=profile.get("emailAddress"),
            status=IntegrationStatus.HEALTHY,
            granted_scopes=granted_scopes,
            credentials_ref="keyring:gmail.refresh_token",
        )
        session.add(account)
    else:
        account.external_account_id = profile.get("emailAddress")
        account.display = profile.get("emailAddress")
        account.granted_scopes = granted_scopes
    await session.flush()
    return account


async def _persist_message(
    session: AsyncSession,
    *,
    account: IntegrationAccount,
    parsed: dict[str, Any],
    client: GmailClient,
) -> tuple[SourceEvidence, Message] | None:
    """Persist evidence + message + conversation. Returns None if duplicate."""
    sent_at = parsed["sent_at"]
    content = (
        f"From: {parsed.get('sender_email')}\n"
        f"To: {parsed.get('to')}\n"
        f"Subject: {parsed.get('subject')}\n"
        f"Date: {sent_at.isoformat()}\n\n"
        f"{parsed.get('body') or ''}"
    )
    evidence, created = await record_evidence(
        session,
        source_type="gmail",
        content=content,
        truth_class=TruthClass.FACT,
        source_ref=parsed["gmail_message_id"],
        provenance={
            "gmail_message_id": parsed["gmail_message_id"],
            "gmail_thread_id": parsed["gmail_thread_id"],
            "rfc_message_id": parsed.get("rfc_message_id"),
            "history_id": parsed.get("history_id"),
            "labels": parsed.get("labels"),
        },
    )
    if not created:
        return None

    person = await resolve_person(
        session,
        email=parsed.get("sender_email"),
        full_name=parsed.get("sender_name"),
        evidence=evidence,
    )

    conversation = None
    if parsed.get("gmail_thread_id"):
        result = await session.execute(
            select(Conversation).where(
                Conversation.external_thread_id == parsed["gmail_thread_id"]
            )
        )
        conversation = result.scalar_one_or_none()
    if conversation is None:
        conversation = Conversation(
            id=new_id(),
            subject_type="person",
            subject_id=person.id if person else "unknown",
            channel=ChannelType.EMAIL,
            external_thread_id=parsed.get("gmail_thread_id"),
            title=parsed.get("subject"),
            last_message_at=parsed["sent_at"],
        )
        session.add(conversation)
        await session.flush()

    message = Message(
        id=new_id(),
        conversation_id=conversation.id,
        integration_account_id=account.id,
        direction="inbound",
        sender_ref=parsed.get("sender_email"),
        recipient_ref=parsed.get("to"),
        subject=parsed.get("subject"),
        body=parsed.get("body"),
        external_message_id=parsed["gmail_message_id"],
        external_thread_id=parsed.get("gmail_thread_id"),
        timestamp=parsed["sent_at"],
        attachments=parsed.get("attachments", []),
        labels=parsed.get("labels", []),
        source_evidence_id=evidence.id,
    )
    session.add(message)

    # Domain hypothesis for an unknown sender's domain (company hypothesis, not fact).
    if person is not None and "@" in (parsed.get("sender_email") or ""):
        domain = parsed["sender_email"].split("@")[1]
        claim = IntelligenceClaim(
            id=new_id(),
            claim_type=TruthClass.HYPOTHESIS,
            text=f"Sender domain {domain} may correspond to a company",
            reasoning="Company Hypothesis from sender domain; not asserted without evidence",
            confidence=0.3,
            tag=ClaimTag.COMMERCIAL_HYPOTHESIS,
            entity_type="domain",
            entity_id=domain,
        )
        session.add(claim)
        session.add(
            ClaimEvidence(id=new_id(), claim_id=claim.id, evidence_id=evidence.id, role="supports")
        )

    return evidence, message


async def sync_once(
    session: AsyncSession,
    *,
    client: GmailClient,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run one sync pass. Returns summary counts."""
    settings = get_settings()
    profile = await client.profile()
    granted = profile.get("scopes", []) if isinstance(profile.get("scopes"), list) else []
    if not granted:
        # profile does not carry scopes; fall back to the account record's grant.
        granted = []
    account = await _get_or_create_account(session, profile=profile, granted_scopes=granted)

    health = dict(account.health or {})
    cursor = health.get("history_id")

    message_ids: list[str] = []
    mode = "initial"
    if cursor:
        mode = "incremental"
        try:
            history = await client.history_list(int(cursor))
            message_ids = [
                m["id"]
                for h in history.get("history", [])
                for m in h.get("messages", [])
            ]
        except GmailApiError as exc:
            if exc.status == 404:
                # Cursor too old: bounded recovery sync establishes a new cursor.
                mode = "recovery"
                cursor = None
            else:
                raise

    if not cursor:
        query = build_initial_query(config)
        page_token: str | None = None
        seen = 0
        max_results = min(settings.gmail_sync_batch_size, 500)
        while seen < settings.gmail_initial_max_messages:
            page = await client.list_messages(
                query=query, max_results=max_results, page_token=page_token
            )
            batch = page.get("messages", [])
            if not batch:
                break
            message_ids.extend(m["id"] for m in batch)
            seen += len(batch)
            page_token = page.get("nextPageToken")
            if not page_token:
                break

    ingested = 0
    skipped = 0
    max_history = health.get("history_id")
    for message_id in message_ids:
        try:
            resource = await client.get_message(message_id)
        except GmailApiError:
            continue  # message may have been deleted; skip, never crash the pass
        parsed = parse_message_resource(resource)
        persisted = await _persist_message(session, account=account, parsed=parsed, client=client)
        if persisted is None:
            skipped += 1
        else:
            ingested += 1
            evidence, message = persisted
            classification = await persist_classification(
                session, message=message, parsed=parsed
            )
            await extract_intelligence(
                session, parsed=parsed, evidence=evidence, classification=classification
            )
            await create_inbox_items(
                session,
                parsed=parsed,
                evidence=evidence,
                message=message,
                classification=classification,
            )
            pid = parsed.get("history_id")
            if pid:
                max_history = max(int(max_history) if max_history else 0, int(pid))

    # Commit everything (evidence, messages, claims, inbox items) BEFORE the
    # cursor is considered advanced — same transaction, so atomic.
    account.health = {
        **health,
        "history_id": max_history if max_history else health.get("history_id"),
        "last_sync_at": datetime.now(UTC).isoformat(),
        "messages_ingested": int(health.get("messages_ingested", 0)) + ingested,
        "last_mode": mode,
    }
    account.last_checked_at = datetime.now(UTC)
    account.status = IntegrationStatus.HEALTHY
    account.error_message = None
    session.add(
        IntegrationEvent(
            id=new_id(),
            integration_account_id=account.id,
            event_type="gmail.sync",
            external_id=None,
            occurred_at=datetime.now(UTC),
            payload={
                "mode": mode,
                "retrieved": len(message_ids),
                "ingested": ingested,
                "skipped": skipped,
                "cursor": account.health.get("history_id"),
            },
        )
    )
    await record_audit(
        session,
        actor="worker",
        action="gmail.sync",
        entity_type="integration_account",
        entity_id=account.id,
        reason=f"sync mode={mode} ingested={ingested} skipped={skipped}",
    )
    await session.flush()
    return {
        "mode": mode,
        "retrieved": len(message_ids),
        "ingested": ingested,
        "skipped": skipped,
        "cursor": account.health.get("history_id"),
        "last_sync_at": account.health["last_sync_at"],
    }
