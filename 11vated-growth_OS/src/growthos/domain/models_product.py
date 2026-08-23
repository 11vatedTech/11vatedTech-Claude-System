"""Product intelligence entities.

Products are first-class. Every claim about a product is tagged with a truth
class via ``claims``; capability and market conclusions remain hypotheses until
validated. Product versions preserve history.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import Float, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from growthos.domain.base import Record, jsonb
from growthos.domain.enums import ProductMaturity


class Product(Record):
    __tablename__ = "product"

    name: Mapped[str] = mapped_column(String(300), nullable=False, index=True)
    codename: Mapped[str | None] = mapped_column(String(300), nullable=True)
    definition: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    core_problem: Mapped[str | None] = mapped_column(Text, nullable=True)
    core_insight: Mapped[str | None] = mapped_column(Text, nullable=True)
    maturity: Mapped[ProductMaturity] = mapped_column(
        default=ProductMaturity.IDEA, nullable=False
    )
    status: Mapped[str] = mapped_column(String(40), default="active", nullable=False)
    positioning: Mapped[str | None] = mapped_column(Text, nullable=True)
    founder_involvement: Mapped[str | None] = mapped_column(Text, nullable=True)
    roadmap: Mapped[list[str]] = mapped_column(jsonb, default=list, nullable=False)

    # Structured canon fields (list-valued).
    features: Mapped[list[str]] = mapped_column(jsonb, default=list, nullable=False)
    capabilities: Mapped[list[str]] = mapped_column(jsonb, default=list, nullable=False)
    technical_differentiators: Mapped[list[str]] = mapped_column(
        jsonb, default=list, nullable=False
    )
    creative_differentiators: Mapped[list[str]] = mapped_column(
        jsonb, default=list, nullable=False
    )
    value_propositions: Mapped[list[str]] = mapped_column(jsonb, default=list, nullable=False)
    customer_outcomes: Mapped[list[str]] = mapped_column(jsonb, default=list, nullable=False)
    use_cases: Mapped[list[str]] = mapped_column(jsonb, default=list, nullable=False)
    target_customers: Mapped[list[str]] = mapped_column(jsonb, default=list, nullable=False)
    buyers: Mapped[list[str]] = mapped_column(jsonb, default=list, nullable=False)
    partners: Mapped[list[str]] = mapped_column(jsonb, default=list, nullable=False)
    industries: Mapped[list[str]] = mapped_column(jsonb, default=list, nullable=False)
    commercial_models: Mapped[list[str]] = mapped_column(jsonb, default=list, nullable=False)
    pricing_hypotheses: Mapped[list[dict[str, Any]]] = mapped_column(
        jsonb, default=list, nullable=False
    )
    competitive_alternatives: Mapped[list[str]] = mapped_column(
        jsonb, default=list, nullable=False
    )
    delivery_requirements: Mapped[list[str]] = mapped_column(
        jsonb, default=list, nullable=False
    )
    marketing_assets: Mapped[list[str]] = mapped_column(jsonb, default=list, nullable=False)
    sales_assets: Mapped[list[str]] = mapped_column(jsonb, default=list, nullable=False)
    objections: Mapped[list[str]] = mapped_column(jsonb, default=list, nullable=False)
    faq: Mapped[list[dict[str, Any]]] = mapped_column(jsonb, default=list, nullable=False)
    revenue_opportunities: Mapped[list[str]] = mapped_column(
        jsonb, default=list, nullable=False
    )
    limitations: Mapped[list[str]] = mapped_column(jsonb, default=list, nullable=False)
    risks: Mapped[list[str]] = mapped_column(jsonb, default=list, nullable=False)

    # Tagged claims: [{text, tag, confidence}].
    claims: Mapped[list[dict[str, Any]]] = mapped_column(jsonb, default=list, nullable=False)

    versions: Mapped[list[ProductVersion]] = relationship(
        back_populates="product", cascade="all, delete-orphan"
    )
    capability_links: Mapped[list[Capability]] = relationship(
        back_populates="product", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("name", name="uq_product_name"),
    )


class ProductVersion(Record):
    __tablename__ = "product_version"

    product_id: Mapped[str] = mapped_column(
        ForeignKey("product.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version: Mapped[int] = mapped_column(nullable=False)
    change_summary: Mapped[str] = mapped_column(Text, nullable=False)
    snapshot: Mapped[dict[str, Any]] = mapped_column(jsonb, default=dict, nullable=False)
    created_by: Mapped[str] = mapped_column(String(200), default="founder", nullable=False)

    product: Mapped[Product] = relationship(back_populates="versions")

    __table_args__ = (
        UniqueConstraint("product_id", "version", name="uq_product_version"),
    )


class Capability(Record):
    __tablename__ = "capability"

    name: Mapped[str] = mapped_column(String(300), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    product_id: Mapped[str | None] = mapped_column(
        ForeignKey("product.id", ondelete="SET NULL"), nullable=True, index=True
    )
    status: Mapped[str] = mapped_column(String(40), default="hypothesis", nullable=False)
    entered_from: Mapped[str] = mapped_column(String(120), default="founder", nullable=False)
    external_claimable: Mapped[bool] = mapped_column(default=False, nullable=False)

    product: Mapped[Product] = relationship(back_populates="capability_links")

    __table_args__ = (
        UniqueConstraint("name", name="uq_capability_name"),
    )


class CapabilityEvidence(Record):
    __tablename__ = "capability_evidence"

    capability_id: Mapped[str] = mapped_column(
        ForeignKey("capability.id", ondelete="CASCADE"), nullable=False, index=True
    )
    evidence_id: Mapped[str] = mapped_column(
        ForeignKey("source_evidence.id", ondelete="CASCADE"), nullable=False, index=True
    )
    proof_type: Mapped[str] = mapped_column(String(120), default="portfolio", nullable=False)

    __table_args__ = (
        UniqueConstraint("capability_id", "evidence_id", name="uq_capability_evidence"),
    )


class Market(Record):
    __tablename__ = "market"

    name: Mapped[str] = mapped_column(String(300), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    industry: Mapped[str | None] = mapped_column(String(200), nullable=True)
    status: Mapped[str] = mapped_column(String(40), default="hypothesis", nullable=False)

    __table_args__ = (
        UniqueConstraint("name", name="uq_market_name"),
    )


class MarketHypothesis(Record):
    __tablename__ = "market_hypothesis"

    product_id: Mapped[str] = mapped_column(
        ForeignKey("product.id", ondelete="CASCADE"), nullable=False, index=True
    )
    market_id: Mapped[str] = mapped_column(
        ForeignKey("market.id", ondelete="CASCADE"), nullable=False, index=True
    )
    hypothesis: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="hypothesis", nullable=False)

    product: Mapped[Product] = relationship()
    market: Mapped[Market] = relationship()


class IdealCustomerProfile(Record):
    __tablename__ = "ideal_customer_profile"

    product_id: Mapped[str] = mapped_column(
        ForeignKey("product.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    buyer: Mapped[str | None] = mapped_column(String(300), nullable=True)
    user: Mapped[str | None] = mapped_column(String(300), nullable=True)
    pains: Mapped[list[str]] = mapped_column(jsonb, default=list, nullable=False)
    triggers: Mapped[list[str]] = mapped_column(jsonb, default=list, nullable=False)
    firmographics: Mapped[dict[str, Any]] = mapped_column(jsonb, default=dict, nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="hypothesis", nullable=False)

    product: Mapped[Product] = relationship()
