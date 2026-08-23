"""Reclassification of existing real evidence.

Recomputes the structured classification for every stored message, then
rebuilds Founder Inbox items through the pipeline gate. Source evidence,
messages, conversations, and identities are preserved — only derived
intelligence (classifications + inbox items) is recomputed.

Returns a report suitable for the completion matrix.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from growthos.domain.enums import FounderInboxKind, FounderInboxStatus
from growthos.domain.models_comms import (
    FounderInboxItem,
    Message,
    MessageClassification,
)
from growthos.intelligence.pipeline_gate import evaluate_inbox_eligibility
from growthos.shared.ids import new_id

# Inbox kinds produced from Gmail messages by the sync engine.
_MESSAGE_INBOX_KINDS = {
    FounderInboxKind.EMAIL_NEEDS_RESPONSE,
    FounderInboxKind.DEADLINE_APPROACHING,
    FounderInboxKind.AGENT_NEEDS_JUDGMENT,
    FounderInboxKind.CLIENT_REQUIREMENT,
    FounderInboxKind.INTEGRATION_FAILED,
}


async def reclassify_all(session: AsyncSession) -> dict[str, Any]:
    """Reclassify every message and rebuild the Founder Inbox through the gate.

    Also removes any existing message-derived inbox items that fail the gate,
    while preserving non-message system items (approvals, jobs, etc.).
    """
    from growthos.intelligence.commercial import classify_message

    # --- Existing message-derived inbox items: remove for rebuild -----------
    message_kinds = list(_MESSAGE_INBOX_KINDS)
    existing_items = (
        await session.execute(
            select(FounderInboxItem.id).where(FounderInboxItem.kind.in_(message_kinds))
        )
    ).scalars().all()
    removed = len(existing_items)
    if existing_items:
        await session.execute(
            delete(FounderInboxItem).where(FounderInboxItem.id.in_(list(existing_items)))
        )

    messages = (await session.execute(select(Message))).scalars().all()
    total = len(messages)

    # Rebuild the parsed view from the stored message so classification is
    # deterministic and independent of the original Gmail resource.

    distribution: Counter[str] = Counter()
    counts: dict[str, int] = {
        "business_relevant": 0,
        "noncommercial": 0,
        "inbox_eligible_identities": 0,
        "items_created": 0,
    }
    eligible_person_ids: set[str] = set()

    for message in messages:
        parsed = {
            "gmail_message_id": message.external_message_id,
            "gmail_thread_id": message.external_thread_id,
            "sender_email": message.sender_ref,
            "sender_name": None,
            "subject": message.subject,
            "body": message.body,
            "headers": _labels_to_headers(message.labels),
            "labels": message.labels,
            "sent_at": message.timestamp,
        }
        # Classify deterministically.
        result = classify_message(parsed)
        distribution[result.primary.value] += 1

        # Persist classification row (idempotent per message).
        row = (
            await session.execute(
                select(MessageClassification).where(
                    MessageClassification.message_id == message.id
                )
            )
        ).scalar_one_or_none()
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

        # Count commercial relevance.
        business = result.primary.value.startswith("BUSINESS_")
        if business:
            counts["business_relevant"] += 1
        else:
            counts["noncommercial"] += 1

        # Pipeline gate.
        eligible, gate_reason, ctx = await evaluate_inbox_eligibility(
            session, sender_email=message.sender_ref
        )
        if not eligible:
            continue
        if ctx.get("person_id"):
            eligible_person_ids.add(ctx["person_id"])
        if result.primary.value in {
            "PROMOTIONAL", "NEWSLETTER", "SOCIAL_NOTIFICATION",
            "TRANSACTIONAL", "SPAM_OR_LOW_VALUE",
        }:
            continue
        if result.attention_score < 40.0:
            continue

        # Create the inbox item (deduped by kind+entity).
        kinds = result.attention_kinds or []
        if "security_issue" in kinds:
            kind = FounderInboxKind.EMAIL_NEEDS_RESPONSE
            title = f"Security matter from {message.sender_ref}: {message.subject or '(no subject)'}"
            summary = f"Security issue flagged ({gate_reason})."
        elif "system_failure" in kinds:
            kind = FounderInboxKind.INTEGRATION_FAILED
            title = f"System alert from {message.sender_ref}: {message.subject or '(no subject)'}"
            summary = f"System-failure language flagged ({gate_reason})."
        elif "payment_issue" in kinds:
            kind = FounderInboxKind.CLIENT_REQUIREMENT
            title = f"Payment matter from {message.sender_ref}: {message.subject or '(no subject)'}"
            summary = f"Payment/invoice language flagged ({gate_reason})."
        else:
            kind = FounderInboxKind.EMAIL_NEEDS_RESPONSE
            title = f"Actionable from {message.sender_ref}: {message.subject or '(no subject)'}"
            summary = f"Attention drivers: {', '.join(kinds)} ({gate_reason})."

        existing = (
            await session.execute(
                select(FounderInboxItem.id).where(
                    FounderInboxItem.kind == kind,
                    FounderInboxItem.entity_type == "person",
                    FounderInboxItem.entity_id == ctx.get("person_id"),
                )
            )
        ).scalar_one_or_none()
        if existing is not None:
            continue
        session.add(
            FounderInboxItem(
                id=new_id(),
                kind=kind,
                title=title,
                summary=summary,
                entity_type="person",
                entity_id=ctx.get("person_id"),
                source_evidence_id=message.source_evidence_id,
                status=FounderInboxStatus.UNREAD,
                priority=min(10, 2 + int(result.attention_score // 10)),
                payload={
                    "gmail_message_id": message.external_message_id,
                    "gate_reason": gate_reason,
                    "classification": result.primary.value,
                    "relevance_score": result.relevance_score,
                    "attention_score": result.attention_score,
                },
            )
        )
        counts["items_created"] += 1

    await session.flush()

    # Post-rebuild inbox count.
    after_count = (
        await session.execute(select(func.count()).select_from(FounderInboxItem))
    ).scalar() or 0

    return {
        "total_messages": total,
        "classification_distribution": dict(distribution),
        "commercially_relevant": counts["business_relevant"],
        "noncommercial": counts["noncommercial"],
        "inbox_eligible_identities": len(eligible_person_ids),
        "items_removed_by_gate": removed,
        "items_created": counts["items_created"],
        "founder_inbox_after": after_count,
    }


def _labels_to_headers(labels: list[str]) -> dict[str, str]:
    """No header reconstruction from labels — the classifier reads ``labels``
    directly as a deterministic bulk signal (PROMOTIONS/UPDATES/FORUMS/SOCIAL).
    New messages synced going forward carry real headers via
    ``parse_message_resource``; stored messages keep their Gmail labels.
    """
    return {}

