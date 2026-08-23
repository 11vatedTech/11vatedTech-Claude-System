"""Communication entities.

Raw messages are preserved separately from analysis. Every outbound adapter
consults the suppression ledger before sending. The founder inbox is generated
only from real events.
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
from growthos.domain.enums import (
    ChannelType,
    FounderInboxKind,
    FounderInboxStatus,
    OutreachState,
    SuppressionScope,
)
from growthos.domain.enums import (
    MessageClassification as MessageClassificationEnum,
)


class Conversation(Record):
    __tablename__ = "conversation"

    subject_type: Mapped[str] = mapped_column(String(64), nullable=False)
    subject_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    channel: Mapped[ChannelType] = mapped_column(default=ChannelType.EMAIL, nullable=False)
    external_thread_id: Mapped[str | None] = mapped_column(String(300), nullable=True)
    title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    last_message_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    status: Mapped[str] = mapped_column(String(40), default="open", nullable=False)

    messages: Mapped[list[Message]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint(
            "subject_type", "subject_id", "external_thread_id",
            name="uq_conversation_thread",
        ),
    )


class Message(Record):
    __tablename__ = "message"

    conversation_id: Mapped[str] = mapped_column(
        ForeignKey("conversation.id", ondelete="CASCADE"), nullable=False, index=True
    )
    integration_account_id: Mapped[str | None] = mapped_column(
        ForeignKey("integration_account.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    direction: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    sender_ref: Mapped[str | None] = mapped_column(String(500), nullable=True)
    recipient_ref: Mapped[str | None] = mapped_column(String(500), nullable=True)
    subject: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    external_message_id: Mapped[str | None] = mapped_column(String(300), nullable=True)
    external_thread_id: Mapped[str | None] = mapped_column(String(300), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    attachments: Mapped[list[dict[str, Any]]] = mapped_column(
        jsonb, default=list, nullable=False
    )
    labels: Mapped[list[str]] = mapped_column(jsonb, default=list, nullable=False)
    raw_stored_ref: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source_evidence_id: Mapped[str | None] = mapped_column(
        ForeignKey("source_evidence.id", ondelete="SET NULL"), nullable=True
    )

    conversation: Mapped[Conversation] = relationship(back_populates="messages")

    __table_args__ = (
        UniqueConstraint(
            "external_message_id", name="uq_message_external_id"
        ),
        UniqueConstraint(
            "integration_account_id",
            "external_message_id",
            name="uq_message_account_external",
        ),
    )


class Outreach(Record):
    __tablename__ = "outreach"

    conversation_id: Mapped[str | None] = mapped_column(
        ForeignKey("conversation.id", ondelete="SET NULL"), nullable=True
    )
    prospect_id: Mapped[str | None] = mapped_column(
        ForeignKey("prospect.id", ondelete="SET NULL"), nullable=True, index=True
    )
    person_id: Mapped[str | None] = mapped_column(
        ForeignKey("person.id", ondelete="SET NULL"), nullable=True, index=True
    )
    campaign_id: Mapped[str | None] = mapped_column(
        ForeignKey("campaign.id", ondelete="SET NULL"), nullable=True
    )
    channel: Mapped[ChannelType] = mapped_column(default=ChannelType.EMAIL, nullable=False)
    state: Mapped[OutreachState] = mapped_column(
        default=OutreachState.DRAFT, nullable=False, index=True
    )
    subject: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    why_this_person: Mapped[str | None] = mapped_column(Text, nullable=True)
    why_now: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_relevance: Mapped[str | None] = mapped_column(Text, nullable=True)
    value_created: Mapped[str | None] = mapped_column(Text, nullable=True)
    relationship_context: Mapped[str | None] = mapped_column(Text, nullable=True)
    next_step: Mapped[str | None] = mapped_column(Text, nullable=True)
    send_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    replied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)


class SuppressionRecord(Record):
    __tablename__ = "suppression_record"

    scope: Mapped[SuppressionScope] = mapped_column(
        default=SuppressionScope.ALL_CHANNELS, nullable=False
    )
    subject_type: Mapped[str] = mapped_column(String(64), nullable=False)
    subject_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    channel: Mapped[ChannelType | None] = mapped_column(nullable=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="active", nullable=False)
    source: Mapped[str] = mapped_column(String(120), default="founder", nullable=False)
    created_by: Mapped[str] = mapped_column(String(200), default="founder", nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "scope", "subject_type", "subject_id", "channel",
            name="uq_suppression",
        ),
    )


class MessageClassification(Record):
    """Structured commercial classification of a message.

    One row per message (idempotent per message id). Stores the primary class,
    secondary tags, relevance and founder-attention scores, the evidence that
    drove the decision, a reasoning summary, and the classifier version so
    reclassification is traceable.
    """

    __tablename__ = "message_classification"

    message_id: Mapped[str] = mapped_column(
        ForeignKey("message.id", ondelete="CASCADE"), nullable=False, index=True
    )
    primary_class: Mapped[MessageClassificationEnum] = mapped_column(nullable=False, index=True)
    secondary_tags: Mapped[list[str]] = mapped_column(jsonb, default=list, nullable=False)
    relevance_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    attention_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    attention_kinds: Mapped[list[str]] = mapped_column(jsonb, default=list, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    evidence: Mapped[list[dict[str, Any]]] = mapped_column(jsonb, default=list, nullable=False)
    reasoning: Mapped[str] = mapped_column(Text, default="", nullable=False)
    classifier_version: Mapped[str] = mapped_column(String(80), nullable=False)

    message: Mapped[Message] = relationship()

    __table_args__ = (
        UniqueConstraint("message_id", name="uq_message_classification"),
    )


class FounderInboxItem(Record):
    __tablename__ = "founder_inbox_item"

    kind: Mapped[FounderInboxKind] = mapped_column(nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    entity_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    entity_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source_evidence_id: Mapped[str | None] = mapped_column(
        ForeignKey("source_evidence.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[FounderInboxStatus] = mapped_column(
        default=FounderInboxStatus.UNREAD, nullable=False, index=True
    )
    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    payload: Mapped[dict[str, Any]] = mapped_column(jsonb, default=dict, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "kind", "entity_type", "entity_id", name="uq_inbox_item_source"
        ),
    )
