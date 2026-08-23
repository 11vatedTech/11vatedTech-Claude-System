"""Identity, network, and integration entities.

The network graph is built only from real, attributable sources (founder input,
integrations, discovery). No fictional people or companies exist.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
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
    IntegrationKind,
    IntegrationStatus,
    PipelineState,
    RelationshipStage,
)


class Company(Record):
    __tablename__ = "company"

    name: Mapped[str] = mapped_column(String(300), nullable=False, index=True)
    legal_name: Mapped[str | None] = mapped_column(String(300), nullable=True)
    domain: Mapped[str | None] = mapped_column(String(300), nullable=True)
    website: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    industry: Mapped[str | None] = mapped_column(String(200), nullable=True, index=True)
    size_hint: Mapped[str | None] = mapped_column(String(80), nullable=True)
    location: Mapped[str | None] = mapped_column(String(300), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    external_ids: Mapped[dict[str, Any]] = mapped_column(jsonb, default=dict, nullable=False)
    origin_source: Mapped[str] = mapped_column(String(120), default="manual", nullable=False)
    origin_evidence_id: Mapped[str | None] = mapped_column(
        ForeignKey("source_evidence.id", ondelete="SET NULL"), nullable=True
    )

    __table_args__ = (
        UniqueConstraint("name", "domain", name="uq_company_name_domain"),
    )


class Person(Record):
    __tablename__ = "person"

    full_name: Mapped[str] = mapped_column(String(300), nullable=False, index=True)
    title: Mapped[str | None] = mapped_column(String(300), nullable=True)
    email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(40), nullable=True)
    linkedin_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    linkedin_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    location: Mapped[str | None] = mapped_column(String(300), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    external_ids: Mapped[dict[str, Any]] = mapped_column(jsonb, default=dict, nullable=False)
    origin_source: Mapped[str] = mapped_column(String(120), default="manual", nullable=False)
    origin_evidence_id: Mapped[str | None] = mapped_column(
        ForeignKey("source_evidence.id", ondelete="SET NULL"), nullable=True
    )
    last_interaction_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    company_links: Mapped[list[PersonCompany]] = relationship(
        back_populates="person", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("full_name", "email", name="uq_person_name_email"),
        UniqueConstraint("linkedin_id", name="uq_person_linkedin_id"),
    )


class PersonCompany(Record):
    __tablename__ = "person_company"

    person_id: Mapped[str] = mapped_column(
        ForeignKey("person.id", ondelete="CASCADE"), nullable=False, index=True
    )
    company_id: Mapped[str] = mapped_column(
        ForeignKey("company.id", ondelete="CASCADE"), nullable=False, index=True
    )
    position: Mapped[str | None] = mapped_column(String(300), nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    start_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    end_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    person: Mapped[Person] = relationship(back_populates="company_links")
    company: Mapped[Company] = relationship()

    __table_args__ = (
        UniqueConstraint("person_id", "company_id", name="uq_person_company"),
    )


class Relationship(Record):
    """A directed relationship between any two graph entities.

    ``subject`` is typically the founder (or a GrowthOS principal); ``object``
    is the counterparty. Roles are many-to-many in concept; stored as a JSON
    list of canonical role values.
    """

    __tablename__ = "relationship"

    subject_type: Mapped[str] = mapped_column(String(64), nullable=False)
    subject_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    object_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    object_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    stage: Mapped[RelationshipStage] = mapped_column(
        default=RelationshipStage.STRANGER, nullable=False
    )
    pipeline_state: Mapped[PipelineState | None] = mapped_column(nullable=True)
    temperature: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    thesis: Mapped[str | None] = mapped_column(Text, nullable=True)
    roles: Mapped[list[str]] = mapped_column(jsonb, default=list, nullable=False)
    strategic_relevance: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_meaningful_interaction_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    recommended_next_move: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Derived from real events only; None means "insufficient evidence".
    event_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    events: Mapped[list[RelationshipEvent]] = relationship(
        back_populates="relationship", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint(
            "subject_type",
            "subject_id",
            "object_type",
            "object_id",
            name="uq_relationship_pair",
        ),
    )


class RelationshipEvent(Record):
    __tablename__ = "relationship_event"

    relationship_id: Mapped[str] = mapped_column(
        ForeignKey("relationship.id", ondelete="CASCADE"), nullable=False, index=True
    )
    event_type: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    channel: Mapped[str | None] = mapped_column(String(40), nullable=True)
    evidence_id: Mapped[str | None] = mapped_column(
        ForeignKey("source_evidence.id", ondelete="SET NULL"), nullable=True
    )

    relationship: Mapped[Relationship] = relationship(back_populates="events")


class IntegrationAccount(Record):
    __tablename__ = "integration_account"

    kind: Mapped[IntegrationKind] = mapped_column(nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(120), nullable=False)
    external_account_id: Mapped[str | None] = mapped_column(String(300), nullable=True)
    display: Mapped[str | None] = mapped_column(String(300), nullable=True)
    status: Mapped[IntegrationStatus] = mapped_column(
        default=IntegrationStatus.NOT_CONFIGURED, nullable=False
    )
    granted_scopes: Mapped[list[str]] = mapped_column(jsonb, default=list, nullable=False)
    credentials_ref: Mapped[str | None] = mapped_column(String(300), nullable=True)
    health: Mapped[dict[str, Any]] = mapped_column(jsonb, default=dict, nullable=False)
    last_checked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        UniqueConstraint("kind", "provider", name="uq_integration_kind_provider"),
    )


class IntegrationEvent(Record):
    __tablename__ = "integration_event"

    integration_account_id: Mapped[str] = mapped_column(
        ForeignKey("integration_account.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    external_id: Mapped[str | None] = mapped_column(String(300), nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(jsonb, default=dict, nullable=False)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "integration_account_id", "event_type", "external_id",
            name="uq_integration_event_dedup",
        ),
    )
