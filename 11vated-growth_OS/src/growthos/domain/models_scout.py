"""Revenue Scout domain entities.

The Revenue Scout is the autonomous commercial agent. It discovers markets and
real organizations, scores them, qualifies/rejects them, and prepares
controlled outreach — all from attributable evidence. No fictional businesses
or contacts exist; every prospect carries provenance back to a real source.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from growthos.domain.base import Record, jsonb
from growthos.domain.enums import (
    ActivityStatus,
    CapabilityStatus,
    CommercialEntityStatus,
    CommercialOfferStatus,
    DiscoveryCandidateState,
    EntityTrack,
    MarketThesisStatus,
    NeedEvidenceClass,
    OrganizationType,
    PurchasingCapacity,
    ResearchTruth,
    ScoutMode,
    ScoutProspectState,
)
from growthos.domain.models_identity import Company

Money = Numeric(14, 2)


class CapabilityCanon(Record):
    """Authoritative, founder-reviewed delivery capability.

    Proposed capabilities are internal hypotheses only. ``external_claimable``
    can become true only for founder-confirmed or evidence-verified entries.
    """

    __tablename__ = "capability_canon"

    name: Mapped[str] = mapped_column(String(300), nullable=False, index=True)
    definition: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str | None] = mapped_column(String(120), nullable=True)
    delivery_form: Mapped[str | None] = mapped_column(String(200), nullable=True)
    proof_evidence: Mapped[list[dict[str, Any]]] = mapped_column(jsonb, default=list, nullable=False)
    maturity: Mapped[str | None] = mapped_column(String(80), nullable=True)
    typical_customer_problem: Mapped[str | None] = mapped_column(Text, nullable=True)
    deliverables: Mapped[list[str]] = mapped_column(jsonb, default=list, nullable=False)
    dependencies: Mapped[list[str]] = mapped_column(jsonb, default=list, nullable=False)
    delivery_complexity: Mapped[float | None] = mapped_column(Float, nullable=True)
    estimated_founder_effort: Mapped[str | None] = mapped_column(String(120), nullable=True)
    reusability: Mapped[float | None] = mapped_column(Float, nullable=True)
    price_range_hypothesis: Mapped[dict[str, Any]] = mapped_column(jsonb, default=dict, nullable=False)
    margin_hypothesis: Mapped[float | None] = mapped_column(Float, nullable=True)
    recurring_potential: Mapped[float | None] = mapped_column(Float, nullable=True)
    white_label_potential: Mapped[float | None] = mapped_column(Float, nullable=True)
    enterprise_potential: Mapped[float | None] = mapped_column(Float, nullable=True)
    related_product_ids: Mapped[list[str]] = mapped_column(jsonb, default=list, nullable=False)
    related_completed_work: Mapped[list[str]] = mapped_column(jsonb, default=list, nullable=False)
    limitations: Mapped[list[str]] = mapped_column(jsonb, default=list, nullable=False)
    status: Mapped[CapabilityStatus] = mapped_column(
        default=CapabilityStatus.PROPOSED, nullable=False
    )
    entered_from: Mapped[str] = mapped_column(String(120), default="founder_review", nullable=False)
    external_claimable: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    source_evidence_ids: Mapped[list[str]] = mapped_column(jsonb, default=list, nullable=False)
    founder_review_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Safe, customer-facing representation of the capability. Never contains
    # local paths, source code, credentials, or private internals.
    external_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Commercial-model fit assessment: [{model, fit, notes}] where fit is
    # FIT / POSSIBLE / WEAK / NOT_CURRENTLY_SUPPORTED.
    commercial_models: Mapped[list[dict[str, Any]]] = mapped_column(jsonb, default=list, nullable=False)
    # Machine recommendation (distinct from founder decision)
    recommended_decision: Mapped[str | None] = mapped_column(String(60), nullable=True)
    recommendation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommendation_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    # Evidence summary for founder review
    evidence_summary_for_review: Mapped[dict[str, Any]] = mapped_column(jsonb, default=dict, nullable=False)
    # Deep review completeness of supporting repos
    deep_review_completeness: Mapped[dict[str, Any]] = mapped_column(jsonb, default=dict, nullable=False)

    __table_args__ = (UniqueConstraint("name", name="uq_capability_canon_name"),)


class CommercialOffer(Record):
    """A buyer-facing package grounded in one or more approved capabilities."""

    __tablename__ = "commercial_offer"

    name: Mapped[str] = mapped_column(String(300), nullable=False, index=True)
    buyer: Mapped[str] = mapped_column(String(300), nullable=False)
    problem: Mapped[str] = mapped_column(Text, nullable=False)
    deliverable: Mapped[str] = mapped_column(Text, nullable=False)
    included_capability_ids: Mapped[list[str]] = mapped_column(jsonb, default=list, nullable=False)
    expected_outcome: Mapped[str | None] = mapped_column(Text, nullable=True)
    scope_boundaries: Mapped[list[str]] = mapped_column(jsonb, default=list, nullable=False)
    delivery_model: Mapped[str | None] = mapped_column(String(120), nullable=True)
    timeline_hypothesis: Mapped[str | None] = mapped_column(String(120), nullable=True)
    price_hypothesis: Mapped[dict[str, Any]] = mapped_column(jsonb, default=dict, nullable=False)
    entry_offer: Mapped[str | None] = mapped_column(Text, nullable=True)
    premium_offer: Mapped[str | None] = mapped_column(Text, nullable=True)
    recurring_component: Mapped[str | None] = mapped_column(Text, nullable=True)
    proof_required: Mapped[list[str]] = mapped_column(jsonb, default=list, nullable=False)
    exclusions: Mapped[list[str]] = mapped_column(jsonb, default=list, nullable=False)
    risks: Mapped[list[str]] = mapped_column(jsonb, default=list, nullable=False)
    status: Mapped[CommercialOfferStatus] = mapped_column(
        default=CommercialOfferStatus.HYPOTHESIS, nullable=False
    )
    source_evidence_ids: Mapped[list[str]] = mapped_column(jsonb, default=list, nullable=False)
    founder_review_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (UniqueConstraint("name", name="uq_commercial_offer_name"),)


class DiscoveryRequestCache(Record):
    """Persistent bounded cache/accounting for public discovery requests."""

    __tablename__ = "scout_discovery_cache"

    source: Mapped[str] = mapped_column(String(80), nullable=False)
    query_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    query: Mapped[dict[str, Any]] = mapped_column(jsonb, default=dict, nullable=False)
    results: Mapped[list[dict[str, Any]]] = mapped_column(jsonb, default=list, nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_status: Mapped[str] = mapped_column(String(40), default="success", nullable=False)
    retry_after_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    request_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    __table_args__ = (UniqueConstraint("source", "query_hash", name="uq_scout_discovery_cache"),)


class ScoutControl(Record):
    """Founder-configurable Revenue Scout control surface.

    A single control row per founder. The GLOBAL KILL SWITCH, when enabled,
    blocks every outbound marketing action while research may continue.
    """

    __tablename__ = "scout_control"

    founder_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    mode: Mapped[ScoutMode] = mapped_column(default=ScoutMode.ASSIST, nullable=False)
    kill_switch: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Budgets and targets.
    daily_research_budget: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    daily_prospect_target: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    daily_outreach_cap: Mapped[int] = mapped_column(Integer, default=10, nullable=False)

    # Discovery scope.
    geographies: Mapped[list[str]] = mapped_column(jsonb, default=list, nullable=False)
    excluded_industries: Mapped[list[str]] = mapped_column(jsonb, default=list, nullable=False)
    approved_offers: Mapped[list[str]] = mapped_column(jsonb, default=list, nullable=False)
    allowed_campaign_ids: Mapped[list[str]] = mapped_column(jsonb, default=list, nullable=False)
    research_depth: Mapped[str] = mapped_column(String(40), default="standard", nullable=False)
    quiet_hours: Mapped[dict[str, Any]] = mapped_column(jsonb, default=dict, nullable=False)

    # Quality gates. Discovery factors are deliberately conservative; 0.30 is
    # reachable by a listing with website/contact evidence but not by bare ones.
    min_revenue_score: Mapped[float] = mapped_column(Float, default=0.30, nullable=False)
    min_evidence_confidence: Mapped[float] = mapped_column(Float, default=0.3, nullable=False)

    # Exploration split (exploitation / adjacent / experimental).
    explore_exploit: Mapped[float] = mapped_column(Float, default=0.7, nullable=False)
    explore_adjacent: Mapped[float] = mapped_column(Float, default=0.2, nullable=False)
    explore_experimental: Mapped[float] = mapped_column(Float, default=0.1, nullable=False)

    # Compliance prerequisites for outbound marketing.
    business_postal_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    opt_out_email: Mapped[str | None] = mapped_column(String(320), nullable=True)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("founder_id", name="uq_scout_control_founder"),
    )


class MarketOpportunityThesis(Record):
    """A structured, evidence-backed hypothesis about a target market."""

    __tablename__ = "market_opportunity_thesis"

    market: Mapped[str] = mapped_column(String(300), nullable=False, index=True)
    buyer: Mapped[str | None] = mapped_column(String(300), nullable=True)
    problem: Mapped[str | None] = mapped_column(Text, nullable=True)
    solution: Mapped[str | None] = mapped_column(Text, nullable=True)
    commercial_model: Mapped[str | None] = mapped_column(String(120), nullable=True)
    expected_deal_min: Mapped[Decimal | None] = mapped_column(Money, nullable=True)
    expected_deal_max: Mapped[Decimal | None] = mapped_column(Money, nullable=True)
    sales_cycle_hypothesis: Mapped[str | None] = mapped_column(String(120), nullable=True)
    margin_hypothesis: Mapped[float | None] = mapped_column(nullable=True)
    competition: Mapped[str | None] = mapped_column(Text, nullable=True)
    proof_required: Mapped[list[str]] = mapped_column(jsonb, default=list, nullable=False)
    acquisition_difficulty: Mapped[float | None] = mapped_column(nullable=True)
    strategic_value: Mapped[float | None] = mapped_column(nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    status: Mapped[MarketThesisStatus] = mapped_column(
        default=MarketThesisStatus.HYPOTHESIS, nullable=False
    )
    evidence_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_evidence_id: Mapped[str | None] = mapped_column(
        ForeignKey("source_evidence.id", ondelete="SET NULL"), nullable=True
    )
    # Capability-driven theses link back to the confirmed capability that
    # grounded them, and record how the scout selected/ranked them.
    capability_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    selection_reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)
    discovery_source: Mapped[str | None] = mapped_column(String(80), nullable=True)
    short_term_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    strategic_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)


class ScoutProspectScore(Record):
    """Persisted Revenue Opportunity Score with component dimensions."""

    __tablename__ = "scout_prospect_score"

    prospect_id: Mapped[str] = mapped_column(
        ForeignKey("prospect.id", ondelete="CASCADE"), nullable=False, index=True
    )
    buyer_fit: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    problem_severity: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    ability_to_pay: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    authority_confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    urgency: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    reachability: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    expected_deal_size: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    expected_margin: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    delivery_confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    sales_cycle_efficiency: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    recurring_potential: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    repeat_potential: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    referral_potential: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    partnership_leverage: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    productization_potential: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    proof_strength: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    strategic_value: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    founder_capacity_cost: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    scope_risk: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    payment_risk: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    competitive_pressure: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    # Derived.
    revenue_opportunity_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    short_term_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    strategic_value_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    combined_priority: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    probability: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    # Independent qualification confidence dimensions.
    identity_confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    problem_confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    capability_fit_confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    buyer_confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    outreach_readiness_confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    confidence_reasoning: Mapped[dict[str, str]] = mapped_column(jsonb, default=dict, nullable=False)
    expected_value_min: Mapped[Decimal | None] = mapped_column(Money, nullable=True)
    expected_value_max: Mapped[Decimal | None] = mapped_column(Money, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    recommended_sales_motion: Mapped[str | None] = mapped_column(String(200), nullable=True)
    recommended_next_action: Mapped[str | None] = mapped_column(Text, nullable=True)
    reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)
    scored_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        UniqueConstraint("prospect_id", name="uq_scout_prospect_score"),
    )


class ProspectEvent(Record):
    """Every acquisition lifecycle transition, fully audited."""

    __tablename__ = "prospect_event"

    prospect_id: Mapped[str] = mapped_column(
        ForeignKey("prospect.id", ondelete="CASCADE"), nullable=False, index=True
    )
    from_state: Mapped[ScoutProspectState | None] = mapped_column(nullable=True)
    to_state: Mapped[ScoutProspectState] = mapped_column(nullable=False)
    actor: Mapped[str] = mapped_column(String(200), default="scout", nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source_evidence_id: Mapped[str | None] = mapped_column(
        ForeignKey("source_evidence.id", ondelete="SET NULL"), nullable=True
    )


class WebsiteAudit(Record):
    """Reproducible public-website reconnaissance observation."""

    __tablename__ = "website_audit"

    company_id: Mapped[str | None] = mapped_column(
        ForeignKey("company.id", ondelete="SET NULL"), nullable=True, index=True
    )
    prospect_id: Mapped[str | None] = mapped_column(
        ForeignKey("prospect.id", ondelete="SET NULL"), nullable=True, index=True
    )
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    method: Mapped[str] = mapped_column(String(80), default="http_fetch", nullable=False)
    truth_class: Mapped[ResearchTruth] = mapped_column(
        default=ResearchTruth.DIRECT_OBSERVATION, nullable=False
    )
    observations: Mapped[list[dict[str, Any]]] = mapped_column(jsonb, default=list, nullable=False)
    evidence: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    company: Mapped[Company] = relationship()


class ScoutRun(Record):
    """One execution of the scout loop (daily / manual / light)."""

    __tablename__ = "scout_run"

    run_type: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(40), default="running", nullable=False)
    summary: Mapped[dict[str, Any]] = mapped_column(jsonb, default=dict, nullable=False)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)


class MarketLearning(Record):
    """Real outcomes by market/industry/offer — the scout's memory."""

    __tablename__ = "market_learning"

    market: Mapped[str | None] = mapped_column(String(300), nullable=True, index=True)
    industry: Mapped[str | None] = mapped_column(String(200), nullable=True, index=True)
    offer: Mapped[str | None] = mapped_column(String(300), nullable=True)
    product_id: Mapped[str | None] = mapped_column(
        ForeignKey("product.id", ondelete="SET NULL"), nullable=True
    )
    campaign_id: Mapped[str | None] = mapped_column(
        ForeignKey("campaign.id", ondelete="SET NULL"), nullable=True
    )
    prospect_id: Mapped[str | None] = mapped_column(
        ForeignKey("prospect.id", ondelete="SET NULL"), nullable=True
    )
    outcome: Mapped[str] = mapped_column(String(60), nullable=False)  # reply/meeting/won/lost/...
    deal_size: Mapped[Decimal | None] = mapped_column(Money, nullable=True)
    sales_cycle_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    margin: Mapped[float | None] = mapped_column(nullable=True)
    loss_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    close_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class DiscoveryCandidate(Record):
    """A real externally observed entity that has NOT yet been commercially
    qualified. Discovery candidates are pre-prospect; they may become Prospects
    only after the promotion gate passes (verified entity + commercial actor +
    activity + market fit + problem evidence + capability fit).
    """

    __tablename__ = "discovery_candidate"

    source: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    # Deterministic string key (e.g. "github:{owner}") used for cross-run
    # deduplication. jsonb cannot carry a plain unique index in Postgres, so
    # the identity key is materialized as a string column.
    source_identity_key: Mapped[str] = mapped_column(String(320), nullable=False)
    source_evidence_id: Mapped[str | None] = mapped_column(
        ForeignKey("source_evidence.id", ondelete="SET NULL"), nullable=True, index=True
    )
    # Provenance back to a Prospect row that was reclassified into a candidate.
    legacy_prospect_id: Mapped[str | None] = mapped_column(
        ForeignKey("prospect.id", ondelete="SET NULL"), nullable=True, index=True
    )
    # Populated only when the candidate passes the promotion gate.
    prospect_id: Mapped[str | None] = mapped_column(
        ForeignKey("prospect.id", ondelete="SET NULL"), nullable=True, index=True
    )

    canonical_name: Mapped[str] = mapped_column(String(300), nullable=False, index=True)
    state: Mapped[DiscoveryCandidateState] = mapped_column(
        default=DiscoveryCandidateState.DISCOVERED_SIGNAL, nullable=False, index=True
    )
    entity_type: Mapped[OrganizationType] = mapped_column(
        default=OrganizationType.UNKNOWN, nullable=False
    )
    commercial_status: Mapped[CommercialEntityStatus] = mapped_column(
        default=CommercialEntityStatus.COMMERCIAL_UNVERIFIED, nullable=False
    )
    activity_status: Mapped[ActivityStatus] = mapped_column(
        default=ActivityStatus.UNKNOWN, nullable=False
    )
    need_evidence_class: Mapped[NeedEvidenceClass] = mapped_column(
        default=NeedEvidenceClass.NO_NEED_EVIDENCE, nullable=False
    )
    purchasing_capacity: Mapped[PurchasingCapacity] = mapped_column(
        default=PurchasingCapacity.UNKNOWN, nullable=False
    )
    track: Mapped[EntityTrack] = mapped_column(
        default=EntityTrack.NOT_COMMERCIAL, nullable=False
    )

    official_website: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    country_region: Mapped[str | None] = mapped_column(String(300), nullable=True)

    # Independent confidence dimensions (must not be collapsed into one number).
    identity_confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    commercial_entity_confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    market_fit_confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    buyer_potential_confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    discovery_priority_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    problem_evidence: Mapped[str | None] = mapped_column(Text, nullable=True)
    products_projects: Mapped[list[dict[str, Any]]] = mapped_column(jsonb, default=list, nullable=False)
    public_source_refs: Mapped[list[dict[str, Any]]] = mapped_column(jsonb, default=list, nullable=False)
    decision_maker_evidence: Mapped[list[dict[str, Any]]] = mapped_column(jsonb, default=list, nullable=False)
    contact_paths: Mapped[list[dict[str, Any]]] = mapped_column(jsonb, default=list, nullable=False)
    external_ids: Mapped[dict[str, Any]] = mapped_column(jsonb, default=dict, nullable=False)
    enrichment: Mapped[dict[str, Any]] = mapped_column(jsonb, default=dict, nullable=False)
    qualification_outcome: Mapped[str | None] = mapped_column(String(200), nullable=True)
    last_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("source", "source_identity_key", name="uq_discovery_candidate_source_identity"),
    )


class DiscoveryCandidateEvent(Record):
    """Audited lifecycle transition of a discovery candidate."""

    __tablename__ = "discovery_candidate_event"

    candidate_id: Mapped[str] = mapped_column(
        ForeignKey("discovery_candidate.id", ondelete="CASCADE"), nullable=False, index=True
    )
    from_state: Mapped[DiscoveryCandidateState | None] = mapped_column(nullable=True)
    to_state: Mapped[DiscoveryCandidateState] = mapped_column(nullable=False)
    actor: Mapped[str] = mapped_column(String(200), default="scout", nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source_evidence_id: Mapped[str | None] = mapped_column(
        ForeignKey("source_evidence.id", ondelete="SET NULL"), nullable=True
    )


class SourceEffectiveness(Record):
    """Learning metrics per discovery source, from real outcomes only.

    Separates discovery yield from commercial yield so the scout can learn
    "GitHub is useful for technical evidence but weak for commercial prospect
    discovery" without conflating poor source with poor market.
    """

    __tablename__ = "source_effectiveness"

    source: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    market: Mapped[str | None] = mapped_column(String(300), nullable=True, index=True)
    candidates_found: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    verified_commercial_entities: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    problem_signals: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    capability_matches: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    verified_contacts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sales_qualified: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    promoted_to_prospect: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    duplicate_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    false_positive_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    verified_entity_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    problem_signal_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    recommendation: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[dict[str, Any]] = mapped_column(jsonb, default=dict, nullable=False)
    assessed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        UniqueConstraint("source", "market", name="uq_source_effectiveness_source_market"),
    )
