"""Evidence provenance service.

Raw evidence (FACT/OBSERVATION) is recorded once (deduplicated by content hash
per source type) and never overwritten. Derived claims (INFERENCE/HYPOTHESIS)
must link back to supporting evidence.
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from growthos.domain.enums import ClaimTag, TruthClass
from growthos.domain.models_evidence import (
    ClaimEvidence,
    IntelligenceClaim,
    SourceEvidence,
)
from growthos.shared.errors import ValidationError
from growthos.shared.ids import new_id


def _content_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _assert_raw_truth_class(truth_class: TruthClass) -> None:
    if truth_class not in {TruthClass.FACT, TruthClass.OBSERVATION}:
        raise ValidationError(
            f"Raw evidence truth_class must be FACT or OBSERVATION, got {truth_class.value}"
        )


async def record_evidence(
    session: AsyncSession,
    *,
    source_type: str,
    content: str,
    truth_class: TruthClass = TruthClass.FACT,
    source_ref: str | None = None,
    provenance: dict[str, Any] | None = None,
    captured_at: datetime | None = None,
) -> tuple[SourceEvidence, bool]:
    """Record raw evidence idempotently.

    Returns ``(evidence, created)``. If identical evidence already exists for
    the source type, the existing record is returned and ``created`` is False.
    """
    _assert_raw_truth_class(truth_class)
    digest = _content_hash(content)
    existing = await session.execute(
        select(SourceEvidence).where(
            SourceEvidence.source_type == source_type,
            SourceEvidence.content_hash == digest,
        )
    )
    found = existing.scalar_one_or_none()
    if found is not None:
        return found, False

    evidence = SourceEvidence(
        id=new_id(),
        source_type=source_type,
        source_ref=source_ref,
        content=content,
        content_hash=digest,
        truth_class=truth_class,
        captured_at=captured_at or datetime.now(UTC),
        provenance=provenance or {},
    )
    session.add(evidence)
    await session.flush()
    return evidence, True


async def record_claim(
    session: AsyncSession,
    *,
    claim_type: TruthClass,
    text: str,
    reasoning: str | None = None,
    confidence: float = 0.0,
    evidence_ids: list[str] | None = None,
    tag: ClaimTag | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
    confidence_rationale: str | None = None,
) -> IntelligenceClaim:
    """Record an INFERENCE or HYPOTHESIS linked to supporting evidence."""
    if claim_type not in {TruthClass.INFERENCE, TruthClass.HYPOTHESIS}:
        raise ValidationError(
            f"Claim type must be INFERENCE or HYPOTHESIS, got {claim_type.value}"
        )
    if not 0.0 <= confidence <= 1.0:
        raise ValidationError("confidence must be within [0, 1]")

    claim = IntelligenceClaim(
        id=new_id(),
        claim_type=claim_type,
        text=text,
        reasoning=reasoning,
        confidence=confidence,
        confidence_rationale=confidence_rationale,
        tag=tag,
        entity_type=entity_type,
        entity_id=entity_id,
    )
    session.add(claim)
    await session.flush()

    for evidence_id in evidence_ids or []:
        session.add(
            ClaimEvidence(
                id=new_id(),
                claim_id=claim.id,
                evidence_id=evidence_id,
            )
        )
    await session.flush()
    return claim
