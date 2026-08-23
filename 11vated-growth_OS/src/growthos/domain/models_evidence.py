"""Provenance and evidence entities.

The provenance architecture separates raw source material (facts/observations)
from derived intelligence (inferences/hypotheses). Derived claims must link
back to the raw evidence that supports them via ``claim_evidence``.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from growthos.domain.base import Record, jsonb
from growthos.domain.enums import ClaimTag, TruthClass


class SourceEvidence(Record):
    """Raw source material — a FACT or an OBSERVATION.

    Raw evidence is never overwritten by interpretation. A content hash is
    unique per source type so re-ingestion is idempotent.
    """

    __tablename__ = "source_evidence"

    source_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    source_ref: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    truth_class: Mapped[TruthClass] = mapped_column(default=TruthClass.FACT, nullable=False)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    provenance: Mapped[dict[str, Any]] = mapped_column(jsonb, default=dict, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "source_type", "content_hash", name="uq_evidence_source_hash"
        ),
    )


class IntelligenceClaim(Record):
    """An INFERENCE or HYPOTHESIS derived from evidence."""

    __tablename__ = "intelligence_claim"

    claim_type: Mapped[TruthClass] = mapped_column(nullable=False, index=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    confidence_rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    tag: Mapped[ClaimTag | None] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column(String(40), default="proposed", nullable=False)
    entity_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    entity_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    evidence_links: Mapped[list[ClaimEvidence]] = relationship(
        back_populates="claim", cascade="all, delete-orphan"
    )


class ClaimEvidence(Record):
    """Junction linking a derived claim to its supporting evidence."""

    __tablename__ = "claim_evidence"

    claim_id: Mapped[str] = mapped_column(
        ForeignKey("intelligence_claim.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    evidence_id: Mapped[str] = mapped_column(
        ForeignKey("source_evidence.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(String(80), default="supports", nullable=False)
    weight: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)

    claim: Mapped[IntelligenceClaim] = relationship(back_populates="evidence_links")
    evidence: Mapped[SourceEvidence] = relationship()

    __table_args__ = (
        UniqueConstraint("claim_id", "evidence_id", name="uq_claim_evidence"),
    )


class ResearchObservation(Record):
    """A structured observation gathered during research, tied to evidence."""

    __tablename__ = "research_observation"

    source_evidence_id: Mapped[str] = mapped_column(
        ForeignKey("source_evidence.id", ondelete="CASCADE"), nullable=False, index=True
    )
    target_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    observed: Mapped[str] = mapped_column(Text, nullable=False)
    observation_type: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    confidence: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    meta: Mapped[dict[str, Any]] = mapped_column(jsonb, default=dict, nullable=False)

    evidence: Mapped[SourceEvidence] = relationship()


class Learning(Record):
    """A statistically-honest lesson derived from real outcomes.

    ``sample_size`` is mandatory. Small samples must not be dressed up as
    authoritative conclusions.
    """

    __tablename__ = "learning"

    insight: Mapped[str] = mapped_column(Text, nullable=False)
    sample_size: Mapped[int] = mapped_column(Integer, nullable=False)
    evidence_period_start: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    evidence_period_end: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    recommendation: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(40), default="baseline", nullable=False)
    evidence_ids: Mapped[list[str]] = mapped_column(jsonb, default=list, nullable=False)
