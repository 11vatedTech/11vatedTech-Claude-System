"""Commercial and sales-operations entities.

Money is stored as ``NUMERIC`` and computed deterministically in SQL/Python —
never by an LLM. Opportunities derive from real evidence and every pipeline
transition is validated against the state machine and recorded in history.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from growthos.domain.base import Record, jsonb
from growthos.domain.enums import (
    CampaignStatus,
    OpportunityClassification,
    PipelineStage,
)
from growthos.domain.models_comms import Conversation
from growthos.domain.models_identity import Company, Person
from growthos.domain.models_product import Product

Money = Numeric(14, 2)


class Prospect(Record):
    __tablename__ = "prospect"

    person_id: Mapped[str | None] = mapped_column(
        ForeignKey("person.id", ondelete="SET NULL"), nullable=True, index=True
    )
    company_id: Mapped[str | None] = mapped_column(
        ForeignKey("company.id", ondelete="SET NULL"), nullable=True, index=True
    )
    status: Mapped[str] = mapped_column(String(40), default="discovered", nullable=False)
    source: Mapped[str] = mapped_column(String(120), default="manual", nullable=False)
    source_evidence_id: Mapped[str | None] = mapped_column(
        ForeignKey("source_evidence.id", ondelete="SET NULL"), nullable=True
    )
    qualification: Mapped[dict[str, Any]] = mapped_column(jsonb, default=dict, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    person: Mapped[Person] = relationship()
    company: Mapped[Company] = relationship()

    __table_args__ = (
        UniqueConstraint(
            "person_id", "company_id", "source", name="uq_prospect_identity"
        ),
    )


class Campaign(Record):
    __tablename__ = "campaign"

    name: Mapped[str] = mapped_column(String(300), nullable=False, index=True)
    product_id: Mapped[str] = mapped_column(
        ForeignKey("product.id", ondelete="CASCADE"), nullable=False, index=True
    )
    objective: Mapped[str | None] = mapped_column(Text, nullable=True)
    revenue_objective: Mapped[Decimal | None] = mapped_column(Money, nullable=True)
    market_id: Mapped[str | None] = mapped_column(
        ForeignKey("market.id", ondelete="SET NULL"), nullable=True
    )
    icp_id: Mapped[str | None] = mapped_column(
        ForeignKey("ideal_customer_profile.id", ondelete="SET NULL"), nullable=True
    )
    buyer: Mapped[str | None] = mapped_column(String(300), nullable=True)
    offer: Mapped[str | None] = mapped_column(Text, nullable=True)
    pricing_hypothesis: Mapped[str | None] = mapped_column(Text, nullable=True)
    channels: Mapped[list[str]] = mapped_column(jsonb, default=list, nullable=False)
    prospect_criteria: Mapped[dict[str, Any]] = mapped_column(
        jsonb, default=dict, nullable=False
    )
    messaging_strategy: Mapped[str | None] = mapped_column(Text, nullable=True)
    proof_assets: Mapped[list[str]] = mapped_column(jsonb, default=list, nullable=False)
    validation_goals: Mapped[list[str]] = mapped_column(jsonb, default=list, nullable=False)
    success_metrics: Mapped[list[str]] = mapped_column(jsonb, default=list, nullable=False)
    stop_conditions: Mapped[list[str]] = mapped_column(jsonb, default=list, nullable=False)
    status: Mapped[CampaignStatus] = mapped_column(
        default=CampaignStatus.DRAFT, nullable=False
    )

    product: Mapped[Product] = relationship()

    __table_args__ = (
        UniqueConstraint("name", name="uq_campaign_name"),
    )


class CampaignProspect(Record):
    __tablename__ = "campaign_prospect"

    campaign_id: Mapped[str] = mapped_column(
        ForeignKey("campaign.id", ondelete="CASCADE"), nullable=False, index=True
    )
    prospect_id: Mapped[str] = mapped_column(
        ForeignKey("prospect.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(40), default="discovered", nullable=False)

    __table_args__ = (
        UniqueConstraint("campaign_id", "prospect_id", name="uq_campaign_prospect"),
    )


class ProductProspectMatch(Record):
    __tablename__ = "product_prospect_match"

    product_id: Mapped[str] = mapped_column(
        ForeignKey("product.id", ondelete="CASCADE"), nullable=False, index=True
    )
    prospect_id: Mapped[str] = mapped_column(
        ForeignKey("prospect.id", ondelete="CASCADE"), nullable=False, index=True
    )
    evidence_id: Mapped[str | None] = mapped_column(
        ForeignKey("source_evidence.id", ondelete="SET NULL"), nullable=True
    )
    fit: Mapped[str | None] = mapped_column(Text, nullable=True)
    use_case: Mapped[str | None] = mapped_column(Text, nullable=True)
    buyer: Mapped[str | None] = mapped_column(String(300), nullable=True)
    value_hypothesis: Mapped[str | None] = mapped_column(Text, nullable=True)
    approach_strategy: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    risk: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(40), default="hypothesis", nullable=False)

    __table_args__ = (
        UniqueConstraint("product_id", "prospect_id", name="uq_product_prospect_match"),
    )


class Opportunity(Record):
    __tablename__ = "opportunity"

    title: Mapped[str] = mapped_column(String(300), nullable=False, index=True)
    company_id: Mapped[str | None] = mapped_column(
        ForeignKey("company.id", ondelete="SET NULL"), nullable=True, index=True
    )
    person_id: Mapped[str | None] = mapped_column(
        ForeignKey("person.id", ondelete="SET NULL"), nullable=True, index=True
    )
    campaign_id: Mapped[str | None] = mapped_column(
        ForeignKey("campaign.id", ondelete="SET NULL"), nullable=True
    )
    source_evidence_id: Mapped[str | None] = mapped_column(
        ForeignKey("source_evidence.id", ondelete="SET NULL"), nullable=True
    )
    stage: Mapped[PipelineStage] = mapped_column(
        default=PipelineStage.DISCOVERED, nullable=False, index=True
    )
    estimated_value: Mapped[Decimal | None] = mapped_column(Money, nullable=True)
    probability: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    classification: Mapped[OpportunityClassification | None] = mapped_column(nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    next_action: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    closed_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    company: Mapped[Company] = relationship()
    person: Mapped[Person] = relationship()
    transitions: Mapped[list[OpportunityTransition]] = relationship(
        back_populates="opportunity", cascade="all, delete-orphan"
    )
    scores: Mapped[list[OpportunityScore]] = relationship(
        back_populates="opportunity", cascade="all, delete-orphan"
    )


class OpportunityTransition(Record):
    __tablename__ = "opportunity_transition"

    opportunity_id: Mapped[str] = mapped_column(
        ForeignKey("opportunity.id", ondelete="CASCADE"), nullable=False, index=True
    )
    from_stage: Mapped[PipelineStage] = mapped_column(nullable=False)
    to_stage: Mapped[PipelineStage] = mapped_column(nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    actor: Mapped[str] = mapped_column(String(200), default="founder", nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    opportunity: Mapped[Opportunity] = relationship(back_populates="transitions")


class OpportunityScore(Record):
    __tablename__ = "opportunity_score"

    opportunity_id: Mapped[str] = mapped_column(
        ForeignKey("opportunity.id", ondelete="CASCADE"), nullable=False, index=True
    )
    need_severity: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    customer_fit: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    buyer_authority: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    ability_to_pay: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    urgency: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    reachability: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    delivery_confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    potential_margin: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    strategic_value: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    repeat_potential: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    referral_potential: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    relationship_leverage: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    scope_risk: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    payment_risk: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    competitive_pressure: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    overall_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    classification: Mapped[OpportunityClassification | None] = mapped_column(nullable=True)
    reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommended_next_action: Mapped[str | None] = mapped_column(Text, nullable=True)

    opportunity: Mapped[Opportunity] = relationship(back_populates="scores")


class Offer(Record):
    __tablename__ = "offer"

    opportunity_id: Mapped[str] = mapped_column(
        ForeignKey("opportunity.id", ondelete="CASCADE"), nullable=False, index=True
    )
    commercial_form: Mapped[str] = mapped_column(String(120), nullable=False)
    price: Mapped[Decimal | None] = mapped_column(Money, nullable=True)
    scope_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    price_reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(40), default="draft", nullable=False)

    opportunity: Mapped[Opportunity] = relationship()


class Proposal(Record):
    __tablename__ = "proposal"

    opportunity_id: Mapped[str] = mapped_column(
        ForeignKey("opportunity.id", ondelete="CASCADE"), nullable=False, index=True
    )
    offer_id: Mapped[str | None] = mapped_column(
        ForeignKey("offer.id", ondelete="SET NULL"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(40), default="draft", nullable=False)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    opportunity: Mapped[Opportunity] = relationship()


class Project(Record):
    __tablename__ = "project"

    opportunity_id: Mapped[str] = mapped_column(
        ForeignKey("opportunity.id", ondelete="SET NULL"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="setup", nullable=False)
    client_company_id: Mapped[str | None] = mapped_column(
        ForeignKey("company.id", ondelete="SET NULL"), nullable=True
    )
    scope: Mapped[dict[str, Any]] = mapped_column(jsonb, default=dict, nullable=False)
    budget: Mapped[Decimal | None] = mapped_column(Money, nullable=True)
    deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    start_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    promises: Mapped[list[str]] = mapped_column(jsonb, default=list, nullable=False)
    risks: Mapped[list[str]] = mapped_column(jsonb, default=list, nullable=False)

    opportunity: Mapped[Opportunity] = relationship()


class RevenueEvent(Record):
    __tablename__ = "revenue_event"

    opportunity_id: Mapped[str | None] = mapped_column(
        ForeignKey("opportunity.id", ondelete="SET NULL"), nullable=True, index=True
    )
    project_id: Mapped[str | None] = mapped_column(
        ForeignKey("project.id", ondelete="SET NULL"), nullable=True, index=True
    )
    event_type: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    amount: Mapped[Decimal] = mapped_column(Money, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source: Mapped[str | None] = mapped_column(String(120), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class Commitment(Record):
    __tablename__ = "commitment"

    conversation_id: Mapped[str] = mapped_column(
        ForeignKey("conversation.id", ondelete="CASCADE"), nullable=False, index=True
    )
    person_id: Mapped[str | None] = mapped_column(
        ForeignKey("person.id", ondelete="SET NULL"), nullable=True, index=True
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(40), default="open", nullable=False)
    extracted_by: Mapped[str] = mapped_column(String(40), default="agent", nullable=False)

    conversation: Mapped[Conversation] = relationship()


class Objection(Record):
    __tablename__ = "objection"

    conversation_id: Mapped[str | None] = mapped_column(
        ForeignKey("conversation.id", ondelete="CASCADE"), nullable=True, index=True
    )
    opportunity_id: Mapped[str | None] = mapped_column(
        ForeignKey("opportunity.id", ondelete="SET NULL"), nullable=True, index=True
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str | None] = mapped_column(String(120), nullable=True)
    status: Mapped[str] = mapped_column(String(40), default="open", nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    conversation: Mapped[Conversation] = relationship()


class Referral(Record):
    __tablename__ = "referral"

    referrer_person_id: Mapped[str] = mapped_column(
        ForeignKey("person.id", ondelete="SET NULL"), nullable=True, index=True
    )
    referred_person_id: Mapped[str | None] = mapped_column(
        ForeignKey("person.id", ondelete="SET NULL"), nullable=True, index=True
    )
    opportunity_id: Mapped[str | None] = mapped_column(
        ForeignKey("opportunity.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(40), default="new", nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    occurred_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
