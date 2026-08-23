"""Revenue Scout — continuous autonomous commercial discovery.

The scout independently decides which markets to investigate, finds real public
organizations, researches them, scores and qualifies them, and prepares
controlled outreach. Every action is audited; every prospect is attributable.

Guarantees held here:

- no fictional businesses or contacts (only real sources)
- unknown stays unknown (no invented emails/phones/titles)
- no prospect is called a client before a real WON engagement
- suppression overrides autonomy; the kill switch blocks all outbound
- outbound marketing is blocked until compliance prerequisites are configured
- campaign autonomy is backend-enforced (policy gate, not a frontend flag)
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from growthos.domain.enums import (
    CapabilityStatus,
    CommercialOfferStatus,
    ContactRouteKind,
    OutreachBlockReason,
    OutreachState,
    ResearchTruth,
    ScoutMode,
    ScoutProspectState,
    ScoutReplyClass,
    TruthClass,
)
from growthos.domain.models_commercial import Campaign, Prospect
from growthos.domain.models_comms import Outreach, SuppressionRecord
from growthos.domain.models_evidence import ResearchObservation, SourceEvidence
from growthos.domain.models_identity import Company, Person, PersonCompany
from growthos.domain.models_scout import (
    CapabilityCanon,
    CommercialOffer,
    DiscoveryRequestCache,
    MarketLearning,
    MarketOpportunityThesis,
    ProspectEvent,
    ScoutControl,
    ScoutProspectScore,
    ScoutRun,
    WebsiteAudit,
)
from growthos.domain.models_system import AuditEvent
from growthos.intelligence.discovery import (
    DiscoveredOrganization,
    WebsiteAuditEngine,
    discovery_sources,
    evidence_hash,
)
from growthos.intelligence.revenue_scoring import score_revenue_prospect
from growthos.shared.ids import new_id

FOUNDER_ID = "founder"  # single-founder system

# Valid acquisition transitions (from -> {to}).
_COMMON_RESEARCH_EXIT = {
    ScoutProspectState.RESEARCHED,
    ScoutProspectState.REJECTED,
    ScoutProspectState.NURTURE,
    ScoutProspectState.ARCHIVED,
}

_VALID_TRANSITIONS: dict[ScoutProspectState | None, set[ScoutProspectState]] = {
    None: {ScoutProspectState.DISCOVERED, ScoutProspectState.REJECTED, ScoutProspectState.ARCHIVED},
    ScoutProspectState.DISCOVERED: {
        ScoutProspectState.ENRICHMENT_REQUIRED,
        ScoutProspectState.RESEARCHING,
        ScoutProspectState.RESEARCHED,
        ScoutProspectState.REJECTED,
        ScoutProspectState.ARCHIVED,
    },
    ScoutProspectState.ENRICHMENT_REQUIRED: {
        ScoutProspectState.RESEARCHING,
        ScoutProspectState.RESEARCHED,
        ScoutProspectState.REJECTED,
        ScoutProspectState.NURTURE,
        ScoutProspectState.ARCHIVED,
    },
    ScoutProspectState.RESEARCHING: _COMMON_RESEARCH_EXIT,
    ScoutProspectState.RESEARCHED: {
        ScoutProspectState.PROBLEM_EVIDENCE_FOUND,
        ScoutProspectState.QUALIFIED,
        ScoutProspectState.REJECTED,
        ScoutProspectState.NURTURE,
        ScoutProspectState.ARCHIVED,
    },
    ScoutProspectState.PROBLEM_EVIDENCE_FOUND: {
        ScoutProspectState.CAPABILITY_MATCHED,
        ScoutProspectState.REJECTED,
        ScoutProspectState.NURTURE,
        ScoutProspectState.ARCHIVED,
    },
    ScoutProspectState.CAPABILITY_MATCHED: {
        ScoutProspectState.OFFER_DEFINED,
        ScoutProspectState.REJECTED,
        ScoutProspectState.NURTURE,
    },
    ScoutProspectState.OFFER_DEFINED: {
        ScoutProspectState.CONTACT_PATH_VERIFIED,
        ScoutProspectState.REJECTED,
        ScoutProspectState.NURTURE,
    },
    ScoutProspectState.CONTACT_PATH_VERIFIED: {
        ScoutProspectState.SALES_QUALIFIED,
        ScoutProspectState.REJECTED,
        ScoutProspectState.NURTURE,
    },
    ScoutProspectState.SALES_QUALIFIED: {
        ScoutProspectState.READY_TO_CONTACT,
        ScoutProspectState.REJECTED,
        ScoutProspectState.NURTURE,
    },
    # Legacy QUALIFIED is retained for historical rows but is not funnel-ready.
    ScoutProspectState.QUALIFIED: {
        ScoutProspectState.PROBLEM_EVIDENCE_FOUND,
        ScoutProspectState.OUTREACH_DRAFTED,
        ScoutProspectState.REJECTED,
        ScoutProspectState.NURTURE,
        ScoutProspectState.ARCHIVED,
    },
    ScoutProspectState.READY_TO_CONTACT: {
        ScoutProspectState.OUTREACH_DRAFTED,
        ScoutProspectState.REJECTED,
        ScoutProspectState.NURTURE,
    },
    ScoutProspectState.OUTREACH_DRAFTED: {
        ScoutProspectState.AWAITING_APPROVAL,
        ScoutProspectState.ENGAGED,
        ScoutProspectState.REJECTED,
    },
    ScoutProspectState.AWAITING_APPROVAL: {
        ScoutProspectState.APPROVED,
        ScoutProspectState.ENGAGED,
        ScoutProspectState.REJECTED,
        ScoutProspectState.ARCHIVED,
    },
    ScoutProspectState.APPROVED: {
        ScoutProspectState.CONTACTED,
        ScoutProspectState.REJECTED,
        ScoutProspectState.ARCHIVED,
    },
    ScoutProspectState.CONTACTED: {
        ScoutProspectState.REPLIED,
        ScoutProspectState.NURTURE,
        ScoutProspectState.LOST,
        ScoutProspectState.ARCHIVED,
    },
    ScoutProspectState.REPLIED: {
        ScoutProspectState.ENGAGED,
        ScoutProspectState.DISCOVERY_ACTIVE,
        ScoutProspectState.NURTURE,
        ScoutProspectState.LOST,
        ScoutProspectState.REJECTED,
    },
    ScoutProspectState.ENGAGED: {
        ScoutProspectState.DISCOVERY_ACTIVE,
        ScoutProspectState.OPPORTUNITY_ACTIVE,
        ScoutProspectState.LOST,
    },
    ScoutProspectState.DISCOVERY_ACTIVE: {
        ScoutProspectState.OPPORTUNITY_ACTIVE,
        ScoutProspectState.PROPOSAL_ACTIVE,
        ScoutProspectState.LOST,
    },
    ScoutProspectState.OPPORTUNITY_ACTIVE: {
        ScoutProspectState.PROPOSAL_ACTIVE,
        ScoutProspectState.NEGOTIATION_ACTIVE,
        ScoutProspectState.LOST,
    },
    ScoutProspectState.PROPOSAL_ACTIVE: {
        ScoutProspectState.NEGOTIATION_ACTIVE,
        ScoutProspectState.WON,
        ScoutProspectState.LOST,
    },
    ScoutProspectState.NEGOTIATION_ACTIVE: {ScoutProspectState.WON, ScoutProspectState.LOST},
    ScoutProspectState.WON: {ScoutProspectState.ARCHIVED},
    ScoutProspectState.LOST: {ScoutProspectState.NURTURE, ScoutProspectState.ARCHIVED},
    ScoutProspectState.NURTURE: {
        ScoutProspectState.RESEARCHING,
        ScoutProspectState.PROBLEM_EVIDENCE_FOUND,
        ScoutProspectState.REJECTED,
        ScoutProspectState.ARCHIVED,
    },
    ScoutProspectState.PARTNER_TRACK: {
        ScoutProspectState.RESEARCHING,
        ScoutProspectState.REJECTED,
        ScoutProspectState.ARCHIVED,
    },
}

# Lifecycle states the founder funnel groups on.
FUNNEL_STATES = {
    "discovered": {
        ScoutProspectState.DISCOVERED,
        ScoutProspectState.ENRICHMENT_REQUIRED,
        ScoutProspectState.RESEARCHING,
    },
    "researched": {ScoutProspectState.RESEARCHED},
    "evidence_found": {ScoutProspectState.PROBLEM_EVIDENCE_FOUND},
    "offer_matched": {
        ScoutProspectState.CAPABILITY_MATCHED,
        ScoutProspectState.OFFER_DEFINED,
        ScoutProspectState.CONTACT_PATH_VERIFIED,
    },
    "sales_qualified": {
        ScoutProspectState.SALES_QUALIFIED,
        ScoutProspectState.ENGAGED,
        ScoutProspectState.DISCOVERY_ACTIVE,
        ScoutProspectState.OPPORTUNITY_ACTIVE,
    },
    "ready_to_contact": {ScoutProspectState.READY_TO_CONTACT},
    "contacted": {ScoutProspectState.CONTACTED},
    "replies": {ScoutProspectState.REPLIED},
    "proposal_ready": {
        ScoutProspectState.PROPOSAL_ACTIVE,
        ScoutProspectState.NEGOTIATION_ACTIVE,
    },
    "won_clients": {ScoutProspectState.WON},
    "partner_track": {ScoutProspectState.PARTNER_TRACK},
    "nurture": {ScoutProspectState.NURTURE},
}


# ---------------------------------------------------------------------------
# Controls
# ---------------------------------------------------------------------------


async def get_control(session: AsyncSession) -> ScoutControl:
    result = await session.execute(
        select(ScoutControl).where(ScoutControl.founder_id == FOUNDER_ID)
    )
    control = result.scalar_one_or_none()
    if control is None:
        control = ScoutControl(
            id=new_id(),
            founder_id=FOUNDER_ID,
            updated_at=datetime.now(UTC),
        )
        session.add(control)
        await session.flush()
    return control


async def update_control(session: AsyncSession, patch: dict[str, Any]) -> ScoutControl:
    control = await get_control(session)
    allowed = {
        "enabled",
        "mode",
        "kill_switch",
        "daily_research_budget",
        "daily_prospect_target",
        "daily_outreach_cap",
        "geographies",
        "excluded_industries",
        "approved_offers",
        "allowed_campaign_ids",
        "research_depth",
        "quiet_hours",
        "min_revenue_score",
        "min_evidence_confidence",
        "explore_exploit",
        "explore_adjacent",
        "explore_experimental",
        "business_postal_address",
        "opt_out_email",
    }
    for key, value in patch.items():
        if key not in allowed:
            raise ValueError(f"Unknown scout control field: {key}")
        if key == "mode":
            try:
                value = ScoutMode(value)
            except ValueError as exc:
                raise ValueError(f"Invalid scout mode: {value}") from exc
        setattr(control, key, value)
    control.updated_at = datetime.now(UTC)
    await session.flush()
    return control


# ---------------------------------------------------------------------------
# Market selection
# ---------------------------------------------------------------------------


_DEFAULT_MARKETS: list[dict[str, Any]] = [
    {
        "market": "local professional services",
        "buyer": "dentists, lawyers, accountants, real estate agencies",
        "problem": "weak web conversion, manual booking, outdated presence",
        "solution": "modern conversion-focused website / booking experience",
        "commercial_model": "project + optional retainer",
        "expected_deal_min": 3000,
        "expected_deal_max": 15000,
        "sales_cycle_hypothesis": "2-6 weeks",
        "margin_hypothesis": 0.6,
        "competition": "local web agencies, DIY builders",
        "proof_required": ["portfolio case study"],
        "acquisition_difficulty": 0.5,
        "strategic_value": 0.5,
        "confidence": 0.4,
        "evidence_summary": "Founder-supplied default market hypothesis; unvalidated.",
    },
    {
        "market": "local hospitality & retail",
        "buyer": "restaurants, cafes, hotels, boutiques",
        "problem": "poor mobile UX, weak booking/conversion path",
        "solution": "booking + menu/presence modernization",
        "commercial_model": "project",
        "expected_deal_min": 2000,
        "expected_deal_max": 8000,
        "sales_cycle_hypothesis": "1-4 weeks",
        "margin_hypothesis": 0.55,
        "competition": "POS vendors, DIY builders",
        "proof_required": ["portfolio case study"],
        "acquisition_difficulty": 0.6,
        "strategic_value": 0.4,
        "confidence": 0.3,
        "evidence_summary": "Founder-supplied default market hypothesis; unvalidated.",
    },
    {
        "market": "creative & interactive experiences",
        "buyer": "game studios, creators, agencies",
        "problem": "need prototypes/MVPs, interactive experiences",
        "solution": "web-based interactive experiences, game-tech prototypes",
        "commercial_model": "project / productized service",
        "expected_deal_min": 5000,
        "expected_deal_max": 30000,
        "sales_cycle_hypothesis": "3-8 weeks",
        "margin_hypothesis": 0.65,
        "competition": "specialist studios",
        "proof_required": ["portfolio", "playable demo"],
        "acquisition_difficulty": 0.5,
        "strategic_value": 0.7,
        "confidence": 0.3,
        "evidence_summary": "Founder-supplied default market hypothesis; unvalidated.",
    },
]


async def build_market_theses(session: AsyncSession) -> list[MarketOpportunityThesis]:
    """Create market opportunity theses from defaults, then learn from outcomes."""
    # Add evidence-informed adjustments from market learning.
    learning = (
        await session.execute(
            select(MarketLearning.market, func.count(), func.avg(MarketLearning.deal_size))
            .group_by(MarketLearning.market)
        )
    ).all()

    theses: list[MarketOpportunityThesis] = []
    for spec in _DEFAULT_MARKETS:
        thesis = (
            await session.execute(
                select(MarketOpportunityThesis).where(
                    MarketOpportunityThesis.market == spec["market"]
                )
            )
        ).scalar_one_or_none()
        if thesis is None:
            thesis = MarketOpportunityThesis(
                id=new_id(),
                market=spec["market"],
                buyer=spec["buyer"],
                problem=spec["problem"],
                solution=spec["solution"],
                commercial_model=spec["commercial_model"],
                expected_deal_min=Decimal(str(spec["expected_deal_min"])),
                expected_deal_max=Decimal(str(spec["expected_deal_max"])),
                sales_cycle_hypothesis=spec["sales_cycle_hypothesis"],
                margin_hypothesis=spec["margin_hypothesis"],
                competition=spec["competition"],
                proof_required=spec["proof_required"],
                acquisition_difficulty=spec["acquisition_difficulty"],
                strategic_value=spec["strategic_value"],
                confidence=spec["confidence"],
                score=0.0,
                status="hypothesis",
                evidence_summary=spec["evidence_summary"],
            )
            session.add(thesis)
        # Reassess score from real outcomes if any exist.
        score = 0.0
        for market, count, avg_deal in learning:
            if market != spec["market"]:
                continue
            if count >= 1:
                score += min(0.3, 0.05 * count)
            if avg_deal:
                score += min(0.3, float(avg_deal) / 10000)
        thesis.score = round(min(1.0, score), 4) if score else 0.0
        theses.append(thesis)
    await session.flush()
    return theses


# ---------------------------------------------------------------------------
# Dedup + prospect creation
# ---------------------------------------------------------------------------


def _normalize_email(email: str | None) -> str | None:
    if not email:
        return None
    return email.strip().lower()


def _domain_of(website: str | None) -> str | None:
    if not website:
        return None
    m = re.match(r"https?://(?:www\.)?([^/]+)", website.strip())
    return m.group(1).lower() if m else None


async def find_duplicate_prospect(
    session: AsyncSession,
    *,
    name: str | None = None,
    website: str | None = None,
    email: str | None = None,
) -> Prospect | None:
    """Resolve against existing Company/Person/Prospect records."""
    domain = _domain_of(website)
    norm_email = _normalize_email(email)

    if domain:
        company = (
            await session.execute(
                select(Company).where(func.lower(Company.domain) == domain)
            )
        ).scalar_one_or_none()
        if company is not None:
            prospect = (
                await session.execute(
                    select(Prospect).where(Prospect.company_id == company.id)
                )
            ).scalars().first()
            if prospect is not None:
                return prospect

    if norm_email:
        person = (
            await session.execute(
                select(Person).where(func.lower(Person.email) == norm_email)
            )
        ).scalar_one_or_none()
        if person is not None:
            prospect = (
                await session.execute(
                    select(Prospect).where(Prospect.person_id == person.id)
                )
            ).scalars().first()
            if prospect is not None:
                return prospect

    if name:
        company = (
            await session.execute(
                select(Company).where(func.lower(Company.name) == name.strip().lower())
            )
        ).scalar_one_or_none()
        if company is not None:
            prospect = (
                await session.execute(
                    select(Prospect).where(Prospect.company_id == company.id)
                )
            ).scalars().first()
            if prospect is not None:
                return prospect
    return None


async def _is_suppressed(session: AsyncSession, company: Company, person: Person | None) -> bool:
    for entity_type, entity_id in [
        ("company", company.id),
        ("person", person.id if person else None),
    ]:
        if not entity_id:
            continue
        result = await session.execute(
            select(SuppressionRecord.id).where(
                SuppressionRecord.subject_type == entity_type,
                SuppressionRecord.subject_id == entity_id,
                SuppressionRecord.status == "active",
            )
        )
        if result.scalar_one_or_none() is not None:
            return True
    return False


async def create_prospect(
    session: AsyncSession,
    org: DiscoveredOrganization,
    *,
    actor: str = "scout",
    source_evidence: SourceEvidence | None = None,
) -> tuple[Prospect, bool]:
    """Create a real prospect from a discovered organization (dedup first).

    Returns (prospect, is_new). ``is_new`` is False when the organization
    already exists in GrowthOS (same domain/email/name) — the scout must not
    rediscover and recontact the same company.
    """
    existing = await find_duplicate_prospect(
        session, name=org.name, website=org.website, email=org.email
    )
    if existing is not None:
        return existing, False

    company = Company(
        id=new_id(),
        name=org.name,
        domain=_domain_of(org.website),
        website=org.website,
        industry=org.industry,
        location=org.location,
        description=org.description,
        origin_source=org.source,
        origin_evidence_id=source_evidence.id if source_evidence else None,
        external_ids=org.external_ids,
    )
    session.add(company)
    await session.flush()

    person: Person | None = None
    if org.email and _EMAIL_RE_OK(org.email):
        person = Person(
            id=new_id(),
            full_name=org.name,  # company-level contact placeholder only
            email=org.email,
            phone=org.phone,
            location=org.location,
            origin_source=org.source,
            origin_evidence_id=source_evidence.id if source_evidence else None,
        )
        session.add(person)
        await session.flush()
        session.add(
            PersonCompany(
                id=new_id(),
                person_id=person.id,
                company_id=company.id,
                is_primary=True,
            )
        )

    prospect = Prospect(
        id=new_id(),
        person_id=person.id if person else None,
        company_id=company.id,
        status=ScoutProspectState.DISCOVERED.value,
        source=org.source,
        source_evidence_id=source_evidence.id if source_evidence else None,
        qualification={
            "evidence": org.evidence,
            "retrieval_method": org.retrieval_method,
            "source_url": org.source_url,
            "captured_at": org.captured_at.isoformat(),
            "confidence": org.confidence,
            "notes": org.description or "",
            "discovery_contact_hints": {
                "email": org.email,
                "phone": org.phone,
                "source": org.source_url,
                "truth_class": "FACT",
            },
        },
    )
    session.add(prospect)
    await session.flush()
    await _record_transition(
        session, prospect, ScoutProspectState.DISCOVERED, actor=actor,
        reason=f"Discovered via {org.source}: {org.evidence}",
        evidence_id=source_evidence.id if source_evidence else None,
    )
    return prospect, True


_EMAIL_RE_OK = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$").match


# ---------------------------------------------------------------------------
# State machine
# ---------------------------------------------------------------------------


async def _record_transition(
    session: AsyncSession,
    prospect: Prospect,
    to_state: ScoutProspectState,
    *,
    actor: str = "scout",
    reason: str | None = None,
    evidence_id: str | None = None,
) -> None:
    from_state = None
    if prospect.status:
        try:
            from_state = ScoutProspectState(prospect.status)
        except ValueError:
            from_state = None
    if from_state == to_state:
        return
    allowed = _VALID_TRANSITIONS.get(from_state, set())
    if to_state not in allowed:
        raise ValueError(
            f"Invalid prospect transition {from_state.value if from_state else None} -> {to_state.value}"
        )
    session.add(
        ProspectEvent(
            id=new_id(),
            prospect_id=prospect.id,
            from_state=from_state,
            to_state=to_state,
            actor=actor,
            reason=reason,
            occurred_at=datetime.now(UTC),
            source_evidence_id=evidence_id,
        )
    )
    session.add(
        AuditEvent(
            actor=actor,
            action=f"prospect:{to_state.value}",
            entity_type="prospect",
            entity_id=prospect.id,
            previous_state={"status": prospect.status},
            new_state={"status": to_state.value},
            reason=reason,
            context={"source": prospect.source},
        )
    )
    prospect.status = to_state.value


async def transition_prospect(
    session: AsyncSession,
    prospect: Prospect,
    to_state: ScoutProspectState,
    *,
    actor: str = "scout",
    reason: str | None = None,
    evidence_id: str | None = None,
) -> Prospect:
    await _record_transition(
        session, prospect, to_state, actor=actor, reason=reason, evidence_id=evidence_id
    )
    await session.flush()
    return prospect


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------


async def score_prospect(
    session: AsyncSession,
    prospect: Prospect,
    factors: dict[str, float | None],
    *,
    expected_min: Decimal | None = None,
    expected_max: Decimal | None = None,
    confidence_dimensions: dict[str, float] | None = None,
    confidence_reasoning: dict[str, str] | None = None,
) -> ScoutProspectScore:
    result = score_revenue_prospect(factors)
    score_row = (
        await session.execute(
            select(ScoutProspectScore).where(ScoutProspectScore.prospect_id == prospect.id)
        )
    ).scalar_one_or_none()
    if score_row is None:
        score_row = ScoutProspectScore(id=new_id(), prospect_id=prospect.id, scored_at=datetime.now(UTC))
        session.add(score_row)
    for name, value in result.component_scores.items():
        if hasattr(score_row, name):
            setattr(score_row, name, value)
    score_row.revenue_opportunity_score = result.revenue_opportunity_score
    score_row.short_term_score = result.short_term_score
    score_row.strategic_value_score = result.strategic_value_score
    score_row.combined_priority = result.combined_priority
    score_row.probability = result.probability
    score_row.confidence = result.confidence
    dimensions = confidence_dimensions or {}
    for field in (
        "identity_confidence",
        "problem_confidence",
        "capability_fit_confidence",
        "buyer_confidence",
        "outreach_readiness_confidence",
    ):
        setattr(score_row, field, max(0.0, min(1.0, float(dimensions.get(field, 0.0)))))
    score_row.confidence_reasoning = confidence_reasoning or {}
    score_row.expected_value_min = expected_min
    score_row.expected_value_max = expected_max
    score_row.recommended_sales_motion = result.recommended_sales_motion
    score_row.recommended_next_action = result.recommended_next_action
    score_row.reasoning = "\n".join(result.reasoning) or None
    score_row.scored_at = datetime.now(UTC)
    await session.flush()
    return score_row


# ---------------------------------------------------------------------------
# Capability canon, website reconnaissance, and evidence-gated qualification
# ---------------------------------------------------------------------------


def _enum_value(value: Any) -> str:
    return value.value if hasattr(value, "value") else str(value)


async def list_capabilities(session: AsyncSession) -> list[CapabilityCanon]:
    result = await session.execute(
        select(CapabilityCanon).order_by(CapabilityCanon.created_at.desc())
    )
    return list(result.scalars().all())


async def create_capability(
    session: AsyncSession,
    *,
    name: str,
    definition: str,
    actor: str = "founder",
    **fields: Any,
) -> CapabilityCanon:
    """Create a proposed capability; approval is an explicit founder action."""
    if not name.strip() or not definition.strip():
        raise ValueError("Capability name and definition are required")
    existing = (
        await session.execute(
            select(CapabilityCanon).where(func.lower(CapabilityCanon.name) == name.strip().lower())
        )
    ).scalar_one_or_none()
    if existing is not None:
        return existing
    allowed = {
        "category", "delivery_form", "proof_evidence", "maturity",
        "typical_customer_problem", "deliverables", "dependencies",
        "delivery_complexity", "estimated_founder_effort", "reusability",
        "price_range_hypothesis", "margin_hypothesis", "recurring_potential",
        "white_label_potential", "enterprise_potential", "related_product_ids",
        "related_completed_work", "limitations", "source_evidence_ids",
        "founder_review_note",
    }
    unknown = set(fields) - allowed
    if unknown:
        raise ValueError(f"Unknown capability field(s): {', '.join(sorted(unknown))}")
    capability = CapabilityCanon(
        id=new_id(), name=name.strip(), definition=definition.strip(), entered_from=actor,
        status=CapabilityStatus.PROPOSED,
        external_claimable=False,
        **fields,
    )
    session.add(capability)
    await session.flush()
    return capability


async def review_capability(
    session: AsyncSession,
    capability: CapabilityCanon,
    *,
    status: str,
    note: str | None = None,
    actor: str = "founder",
) -> CapabilityCanon:
    try:
        next_status = CapabilityStatus(status)
    except ValueError as exc:
        raise ValueError(f"Invalid capability status: {status}") from exc
    if next_status in {CapabilityStatus.FOUNDER_CONFIRMED, CapabilityStatus.EVIDENCE_VERIFIED}:
        if not note and not capability.proof_evidence and not capability.source_evidence_ids:
            raise ValueError("An approved capability requires founder review or proof evidence")
        capability.external_claimable = True
    else:
        capability.external_claimable = False
    capability.status = next_status
    capability.founder_review_note = note or capability.founder_review_note
    capability.entered_from = actor
    await session.flush()
    return capability


async def list_offers(session: AsyncSession) -> list[CommercialOffer]:
    result = await session.execute(select(CommercialOffer).order_by(CommercialOffer.created_at.desc()))
    return list(result.scalars().all())


async def _approved_capabilities(session: AsyncSession) -> list[CapabilityCanon]:
    result = await session.execute(
        select(CapabilityCanon).where(
            CapabilityCanon.status.in_([
                CapabilityStatus.FOUNDER_CONFIRMED,
                CapabilityStatus.EVIDENCE_VERIFIED,
            ]),
            CapabilityCanon.external_claimable.is_(True),
        )
    )
    return list(result.scalars().all())


async def _match_capabilities(
    session: AsyncSession, problem_text: str
) -> list[tuple[CapabilityCanon, float, str]]:
    """Match only externally claimable capabilities; unknown remains unmatched."""
    terms = set(re.findall(r"[a-z]{4,}", problem_text.lower()))
    matches: list[tuple[CapabilityCanon, float, str]] = []
    for capability in await _approved_capabilities(session):
        corpus = " ".join(
            [capability.name, capability.definition, capability.category or "",
             capability.typical_customer_problem or "", *capability.deliverables]
        ).lower()
        overlap = len(terms & set(re.findall(r"[a-z]{4,}", corpus)))
        confidence = min(0.9, 0.35 + overlap * 0.08) if overlap else 0.0
        if confidence >= 0.5:
            matches.append((capability, round(confidence, 3), f"Matched {overlap} problem terms to approved capability evidence."))
    return sorted(matches, key=lambda item: item[1], reverse=True)


async def _persist_research_evidence(
    session: AsyncSession,
    prospect: Prospect,
    audit: dict[str, Any],
) -> tuple[WebsiteAudit, list[str]]:
    url = str(audit.get("url") or "")
    observations = audit.get("observations") or []
    summary = "\n".join(str(o.get("observation", "")) for o in observations)
    content = f"{url}\n{audit.get('http_status', '')}\n{summary}"
    digest = evidence_hash("website_audit", content)
    source = (
        await session.execute(
            select(SourceEvidence).where(
                SourceEvidence.source_type == "website_audit",
                SourceEvidence.content_hash == digest,
            )
        )
    ).scalar_one_or_none()
    if source is None:
        source = SourceEvidence(
            id=new_id(), source_type="website_audit", source_ref=url, content=content,
            content_hash=digest, truth_class=TruthClass.OBSERVATION,
            captured_at=datetime.now(UTC),
            provenance={"method": "public_http_fetch", "reproduction_method": "GET with public User-Agent"},
        )
        session.add(source)
        await session.flush()
    audit_row = WebsiteAudit(
        id=new_id(), company_id=prospect.company_id, prospect_id=prospect.id, url=url,
        fetched_at=datetime.now(UTC), method="public_http_fetch",
        truth_class=ResearchTruth.DIRECT_OBSERVATION,
        observations=observations, evidence=summary, confidence=max(
            (float(o.get("confidence", 0.0)) for o in observations), default=0.0
        ),
    )
    session.add(audit_row)
    await session.flush()
    observation_ids: list[str] = []
    for item in observations:
        row = ResearchObservation(
            id=new_id(), source_evidence_id=source.id, target_url=url,
            observed=str(item.get("observation", "")),
            observation_type=str(item.get("truth_class", "direct_observation")),
            confidence=float(item.get("confidence", 0.0)),
            meta={"method": "public_http_fetch", "audit_id": audit_row.id},
        )
        session.add(row)
        observation_ids.append(row.id)
    await session.flush()
    return audit_row, observation_ids


def _problem_from_audit(audit: dict[str, Any]) -> tuple[str | None, float, str]:
    """Return only defensible technical signals, never business-loss claims."""
    observations = audit.get("observations") or []
    hard: list[str] = []
    soft: list[str] = []
    for item in observations:
        text = str(item.get("observation", ""))
        truth = str(item.get("truth_class", ""))
        confidence = float(item.get("confidence", 0.0))
        if confidence < 0.7:
            continue
        if "HTTP 4" in text or "HTTP 5" in text or "plain HTTP" in text:
            hard.append(text)
        elif truth in {"direct_observation", "inference"} and (
            "no HTML form" in text or "No mobile viewport" in text
        ):
            soft.append(text)
    if hard:
        return "Public website technical or access issue: " + "; ".join(hard), 0.82, "Direct public-web observation"
    if soft:
        return "Possible conversion-friction signal requiring founder review: " + "; ".join(soft), 0.55, "Public-web observation/inference; not proof of lost business"
    return None, 0.0, "No defensible problem signal found in the bounded audit"


async def requalify_prospect(
    session: AsyncSession,
    prospect: Prospect,
    *,
    audit_engine: WebsiteAuditEngine | None = None,
    actor: str = "scout",
    min_revenue_score: float | None = None,
    reuse_audit: bool = False,
) -> dict[str, Any]:
    """Reprocess one real prospect without deleting evidence or sending.

    ``reuse_audit`` reuses the most recent existing website audit for the
    prospect instead of performing a new external request. It is used by
    selective requalification after a Capability Canon change so the scout does
    not redo external research unnecessarily.
    """
    company = (
        await session.execute(select(Company).where(Company.id == prospect.company_id))
    ).scalar_one_or_none() if prospect.company_id else None
    if company is None:
        prospect.qualification["research_status"] = "incomplete"
        return {"state": prospect.status, "research_status": "incomplete", "reason": "company identity missing"}

    qualification = dict(prospect.qualification or {})
    if prospect.status in {
        ScoutProspectState.DISCOVERED.value,
        ScoutProspectState.ENRICHMENT_REQUIRED.value,
        ScoutProspectState.NURTURE.value,
    }:
        await _record_transition(session, prospect, ScoutProspectState.RESEARCHING, actor=actor, reason="Bounded public reconnaissance started")

    if not company.website:
        qualification["research_status"] = "incomplete"
        qualification["research_reason"] = "No official website in source evidence; no problem inferred."
        identity_confidence = min(1.0, max(0.0, float(qualification.get("confidence", 0.0)) + 0.2))
        qualification["confidence_dimensions"] = {
            "identity_confidence": round(identity_confidence, 3),
            "problem_confidence": 0.0,
            "capability_fit_confidence": 0.0,
            "buyer_confidence": 0.0,
            "outreach_readiness_confidence": 0.0,
        }
        qualification["problem_evidence"] = None
        qualification["contact_routes"] = []
        prospect.qualification = qualification
        await score_prospect(
            session,
            prospect,
            {"buyer_fit": 0.5 if company.industry else None, "proof_strength": identity_confidence},
            confidence_dimensions=qualification["confidence_dimensions"],
            confidence_reasoning={
                "identity": "Public discovery identity; no official website found",
                "problem": "Unknown; enrichment incomplete",
                "capability": "Not evaluated",
                "buyer": "No buyer evidence",
                "outreach": "Not ready",
            },
        )
        if prospect.status == ScoutProspectState.RESEARCHING.value:
            await _record_transition(session, prospect, ScoutProspectState.RESEARCHED, actor=actor, reason="Research completed without an official website")
        return {
            "id": prospect.id, "company": company.name, "state": prospect.status,
            "research_status": "incomplete", "problem_evidence": False,
            "capability_matches": 0, "offer_id": None, "contact_routes": 0,
            "confidence_dimensions": qualification["confidence_dimensions"],
            "reason": qualification["research_reason"],
        }

    audit: dict[str, Any] | None = None
    audit_row: WebsiteAudit | None = None
    if reuse_audit:
        audit_row = (
            await session.execute(
                select(WebsiteAudit)
                .where(WebsiteAudit.prospect_id == prospect.id)
                .order_by(WebsiteAudit.fetched_at.desc())
            )
        ).scalars().first()
        if audit_row is not None:
            audit = {
                "url": audit_row.url,
                "http_status": None,
                "observations": audit_row.observations,
                "evidence": audit_row.evidence,
                "error": None,
            }
    if audit is None:
        engine = audit_engine or WebsiteAuditEngine()
        audit = await engine.audit(company.website)
        audit_row, _ = await _persist_research_evidence(session, prospect, audit)
    problem, problem_confidence, problem_reason = _problem_from_audit(audit)
    qualification["research_status"] = "complete" if not audit.get("error") else "incomplete"
    qualification["website_audit_id"] = audit_row.id if audit_row is not None else None
    qualification["research_url"] = company.website
    qualification["problem_evidence"] = problem
    qualification["problem_reasoning"] = problem_reason
    qualification["problem_observations"] = audit.get("observations") or []

    if prospect.status == ScoutProspectState.RESEARCHING.value:
        await _record_transition(session, prospect, ScoutProspectState.RESEARCHED, actor=actor, reason="Bounded official website reconnaissance completed")

    identity_confidence = min(1.0, max(0.0, float(qualification.get("confidence", 0.0)) + 0.2))
    contact_routes: list[dict[str, Any]] = []
    if company.website and not audit.get("error"):
        contact_routes.append({"kind": ContactRouteKind.VERIFIED_GENERAL_CONTACT.value, "source": company.website, "evidence": "Official website fetched successfully"})
    contact_hints = qualification.get("discovery_contact_hints") or {}
    if contact_hints.get("phone"):
        contact_routes.append({"kind": ContactRouteKind.VERIFIED_PUBLIC_PHONE.value, "source": contact_hints.get("source") or company.origin_source, "evidence": "Publicly listed business phone from discovery source", "value": contact_hints["phone"]})
    person = (
        await session.execute(select(Person).where(Person.id == prospect.person_id))
    ).scalar_one_or_none() if prospect.person_id else None
    if person and person.email:
        contact_routes.append({"kind": ContactRouteKind.VERIFIED_BUSINESS_EMAIL.value, "source": person.origin_source or "GrowthOS", "evidence": "Publicly listed business email"})
    qualification["contact_routes"] = contact_routes

    capability_confidence = 0.0
    buyer_confidence = 0.0
    readiness_confidence = 0.0
    capability_matches: list[dict[str, Any]] = []
    offer_id: str | None = None
    if problem and problem_confidence >= 0.6:
        if prospect.status == ScoutProspectState.RESEARCHED.value:
            await _record_transition(session, prospect, ScoutProspectState.PROBLEM_EVIDENCE_FOUND, actor=actor, reason=problem_reason, evidence_id=prospect.source_evidence_id)
        matches = await _match_capabilities(session, problem)
        for capability, confidence, reasoning in matches[:3]:
            capability_matches.append({"capability_id": capability.id, "name": capability.name, "confidence": confidence, "reasoning": reasoning})
        if matches:
            capability, capability_confidence, match_reason = matches[0]
            qualification["capability_match"] = {"capability_id": capability.id, "name": capability.name, "reasoning": match_reason, "limitations": capability.limitations}
            if prospect.status == ScoutProspectState.PROBLEM_EVIDENCE_FOUND.value:
                await _record_transition(session, prospect, ScoutProspectState.CAPABILITY_MATCHED, actor=actor, reason=match_reason, evidence_id=prospect.source_evidence_id)
            existing_offer = (
                await session.execute(
                    select(CommercialOffer).where(CommercialOffer.included_capability_ids.contains([capability.id]))
                )
            ).scalars().first()
            offer = existing_offer
            if offer is None:
                offer = CommercialOffer(
                    id=new_id(), name=f"Evidence-led {capability.name} engagement",
                    buyer=company.industry or "business decision maker", problem=problem,
                    deliverable=capability.definition, included_capability_ids=[capability.id],
                    expected_outcome="To be validated with the founder and prospect",
                    scope_boundaries=["No unverified performance or revenue claim"],
                    delivery_model="project hypothesis", timeline_hypothesis="hypothesis",
                    price_hypothesis=capability.price_range_hypothesis,
                    proof_required=["founder-confirmed capability proof"],
                    exclusions=["No promise beyond observed evidence"], risks=list(capability.limitations),
                    status=CommercialOfferStatus.HYPOTHESIS,
                    source_evidence_ids=[prospect.source_evidence_id] if prospect.source_evidence_id else [],
                )
                session.add(offer)
                await session.flush()
            offer_id = offer.id
            qualification["offer_id"] = offer.id
            qualification["offer_status"] = _enum_value(offer.status)
            if prospect.status == ScoutProspectState.CAPABILITY_MATCHED.value:
                await _record_transition(session, prospect, ScoutProspectState.OFFER_DEFINED, actor=actor, reason="Offer hypothesis grounded in an approved capability", evidence_id=prospect.source_evidence_id)
        else:
            qualification["qualification_block"] = "NO_APPROVED_CAPABILITY_MATCH"

    if contact_routes and (problem_confidence >= 0.6) and capability_confidence >= 0.6 and offer_id:
        if prospect.status == ScoutProspectState.OFFER_DEFINED.value:
            await _record_transition(session, prospect, ScoutProspectState.CONTACT_PATH_VERIFIED, actor=actor, reason="Legitimate public contact route recorded", evidence_id=prospect.source_evidence_id)
        buyer_confidence = 0.35  # general route only; no decision-maker inferred
        readiness_confidence = min(problem_confidence, capability_confidence, buyer_confidence)
        if prospect.status == ScoutProspectState.CONTACT_PATH_VERIFIED.value and readiness_confidence >= 0.6:
            await _record_transition(session, prospect, ScoutProspectState.SALES_QUALIFIED, actor=actor, reason="All deterministic sales qualification gates passed", evidence_id=prospect.source_evidence_id)
            await _record_transition(session, prospect, ScoutProspectState.READY_TO_CONTACT, actor=actor, reason="Outreach readiness evidence passed threshold", evidence_id=prospect.source_evidence_id)
    elif not problem:
        if prospect.status == ScoutProspectState.RESEARCHED.value:
            await _record_transition(session, prospect, ScoutProspectState.NURTURE, actor=actor, reason=problem_reason)

    qualification["confidence_dimensions"] = {
        "identity_confidence": round(identity_confidence, 3),
        "problem_confidence": round(problem_confidence, 3),
        "capability_fit_confidence": round(capability_confidence, 3),
        "buyer_confidence": round(buyer_confidence, 3),
        "outreach_readiness_confidence": round(readiness_confidence, 3),
    }
    qualification["capability_matches"] = capability_matches
    prospect.qualification = qualification
    factors = {
        "buyer_fit": 0.5 if company.industry else None,
        "problem_severity": min(1.0, problem_confidence),
        "ability_to_pay": 0.5 if company.website else 0.3,
        "authority_confidence": buyer_confidence or None,
        "urgency": None,
        "reachability": 0.7 if contact_routes else 0.2,
        "expected_deal_size": 0.5 if offer_id else 0.2,
        "expected_margin": 0.6 if offer_id else 0.2,
        "delivery_confidence": capability_confidence,
        "sales_cycle_efficiency": 0.4,
        "recurring_potential": 0.3,
        "repeat_potential": 0.3,
        "referral_potential": 0.3,
        "partnership_leverage": 0.2,
        "productization_potential": 0.3,
        "proof_strength": identity_confidence,
        "strategic_value": 0.4,
        "founder_capacity_cost": 0.4,
        "scope_risk": 0.5 if not offer_id else 0.3,
        "payment_risk": 0.4,
        "competitive_pressure": 0.4,
    }
    score = await score_prospect(
        session, prospect, factors,
        confidence_dimensions=qualification["confidence_dimensions"],
        confidence_reasoning={
            "identity": "Public discovery record plus official website evidence" if identity_confidence else "Insufficient identity evidence",
            "problem": problem_reason,
            "capability": "Approved capability match only" if capability_confidence else "NO_APPROVED_CAPABILITY_MATCH",
            "buyer": "No decision-maker inferred; general route only" if buyer_confidence else "No buyer evidence",
            "outreach": "All gates passed" if readiness_confidence >= 0.6 else "Blocked until problem, approved capability, offer, and buyer evidence are sufficient",
        },
    )
    prospect.qualification["revenue_score"] = score.revenue_opportunity_score
    await session.flush()
    return {
        "id": prospect.id, "company": company.name, "state": prospect.status,
        "research_status": qualification["research_status"],
        "problem_evidence": bool(problem), "capability_matches": len(capability_matches),
        "offer_id": offer_id, "contact_routes": len(contact_routes),
        "confidence_dimensions": qualification["confidence_dimensions"],
        "reason": qualification.get("qualification_block") or problem_reason,
    }


async def requalify_cohort(
    session: AsyncSession, *, limit: int | None = None, actor: str = "scout"
) -> dict[str, Any]:
    """Requalify existing real prospects in place; never creates replacements."""
    query = select(Prospect).where(Prospect.source == "overpass").order_by(Prospect.created_at)
    if limit:
        query = query.limit(limit)
    prospects = (await session.execute(query)).scalars().all()
    report: dict[str, Any] = {
        "organizations_discovered": len(prospects), "official_websites_found": 0,
        "organizations_researched": 0, "problem_evidence_found": 0,
        "capability_matches": 0, "offers_created": 0, "verified_contact_paths": 0,
        "decision_makers_identified": 0, "sales_qualified": 0, "ready_to_contact": 0,
        "rejected": 0, "nurture": 0, "research_incomplete": 0, "prospects": [],
    }
    for prospect in prospects:
        company = (
            await session.execute(select(Company).where(Company.id == prospect.company_id))
        ).scalar_one_or_none()
        if company and company.website:
            report["official_websites_found"] += 1
        result = await requalify_prospect(session, prospect, actor=actor)
        report["organizations_researched"] += int(result["research_status"] == "complete")
        report["research_incomplete"] += int(result["research_status"] != "complete")
        report["problem_evidence_found"] += int(result.get("problem_evidence", False))
        report["capability_matches"] += int(result.get("capability_matches", 0) > 0)
        report["offers_created"] += int(bool(result.get("offer_id")))
        report["verified_contact_paths"] += int(result.get("contact_routes", 0) > 0)
        report["decision_makers_identified"] += int(result.get("confidence_dimensions", {}).get("buyer_confidence", 0) >= 0.7)
        report["sales_qualified"] += int(result.get("state") == ScoutProspectState.SALES_QUALIFIED.value)
        report["ready_to_contact"] += int(result.get("state") == ScoutProspectState.READY_TO_CONTACT.value)
        report["nurture"] += int(result.get("state") == ScoutProspectState.NURTURE.value)
        report["prospects"].append(result)
    await session.flush()
    return report


# ---------------------------------------------------------------------------
# Compliance + autonomy gates
# ---------------------------------------------------------------------------


async def compliance_status(session: AsyncSession) -> dict[str, Any]:
    control = await get_control(session)
    has_address = bool((control.business_postal_address or "").strip())
    has_opt_out = bool((control.opt_out_email or "").strip())
    ok = has_address and has_opt_out
    return {
        "outbound_marketing_allowed": ok,
        "business_postal_address_configured": has_address,
        "opt_out_mechanism_configured": has_opt_out,
        "block_reason": None if ok else OutreachBlockReason.COMPLIANCE_NOT_CONFIGURED.value,
    }


async def check_campaign_policy(
    session: AsyncSession,
    campaign: Campaign,
    prospect: Prospect,
) -> tuple[bool, str | None]:
    """Enforce campaign autonomy boundaries (backend, not frontend)."""
    control = await get_control(session)

    # Target criteria from the campaign's prospect_criteria.
    criteria = campaign.prospect_criteria or {}
    company = (
        await session.execute(select(Company).where(Company.id == prospect.company_id))
    ).scalar_one_or_none() if prospect.company_id else None

    industries_include = criteria.get("industries") or []
    if industries_include and company and company.industry and company.industry not in industries_include:
        return False, "industry not in campaign target criteria"
    industries_exclude = criteria.get("excluded_industries") or []
    if industries_exclude and company and company.industry and company.industry in industries_exclude:
        return False, "industry excluded by campaign policy"
    geos = criteria.get("geographies") or []
    if geos and company and company.location and not any(
        g.lower() in company.location.lower() for g in geos
    ):
        return False, "location outside campaign geography"

    if control.excluded_industries and company and company.industry and company.industry in control.excluded_industries:
        return False, "industry globally excluded by scout control"

    # Daily cap.
    if campaign.status != "active":
        return False, "campaign not active"
    today = datetime.now(UTC).date()
    sent_today = await session.scalar(
        select(func.count(Outreach.id)).where(
            Outreach.campaign_id == campaign.id,
            Outreach.state.in_([OutreachState.SENT.value, OutreachState.REPLIED.value]),
            func.date(Outreach.sent_at) == today,
        )
    )
    cap = campaign.prospect_criteria.get("daily_send_cap") or 10
    if (sent_today or 0) >= int(cap):
        return False, "campaign daily send cap reached"
    return True, None


async def outbound_gate(
    session: AsyncSession,
    *,
    prospect: Prospect,
    campaign: Campaign | None,
    actor: str = "scout",
) -> tuple[bool, str, str | None]:
    """Full outbound gate: compliance, mode, kill switch, suppression, policy."""
    control = await get_control(session)

    if control.kill_switch:
        return False, OutreachBlockReason.KILL_SWITCH.value, "global kill switch enabled"

    compliance = await compliance_status(session)
    if not compliance["outbound_marketing_allowed"]:
        return False, OutreachBlockReason.COMPLIANCE_NOT_CONFIGURED.value, (
            "business postal address and opt-out mechanism must be configured"
        )

    if control.mode == ScoutMode.OBSERVE:
        return False, OutreachBlockReason.MODE_OBSERVE.value, "scout in OBSERVE mode"
    if control.mode == ScoutMode.ASSIST:
        # Drafting allowed; sending requires founder approval later.
        pass

    if campaign is not None:
        ok, reason = await check_campaign_policy(session, campaign, prospect)
        if not ok:
            return False, OutreachBlockReason.CAMPAIGN_POLICY.value, reason

    company = (
        await session.execute(select(Company).where(Company.id == prospect.company_id))
    ).scalar_one_or_none() if prospect.company_id else None
    person = (
        await session.execute(select(Person).where(Person.id == prospect.person_id))
    ).scalar_one_or_none() if prospect.person_id else None
    if await _is_suppressed(session, company, person) if company else False:
        return False, OutreachBlockReason.SUPPRESSED.value, "contact is suppressed"

    # Contact path.
    has_contact = False
    if person and person.email:
        has_contact = True
    if not has_contact:
        return False, OutreachBlockReason.NO_CONTACT_PATH.value, "no verifiable contact path"

    return True, "allowed", None


# ---------------------------------------------------------------------------
# Outreach drafting
# ---------------------------------------------------------------------------


def _fingerprint(body: str) -> str:
    import hashlib

    tokens = re.findall(r"[a-z]{4,}", body.lower())
    return hashlib.sha256(" ".join(sorted(set(tokens))).encode()).hexdigest()[:16]


async def draft_outreach(
    session: AsyncSession,
    prospect: Prospect,
    campaign: Campaign,
    *,
    offer: str | None = None,
) -> Outreach:
    """Draft only after the deterministic qualification gate passes."""
    if prospect.status != ScoutProspectState.READY_TO_CONTACT.value:
        raise ValueError("Prospect is not READY_TO_CONTACT; complete evidence-gated qualification first")
    qualification = prospect.qualification or {}
    if not qualification.get("problem_evidence") or not qualification.get("capability_match") or not qualification.get("offer_id"):
        raise ValueError("Outreach requires problem evidence, approved capability match, and offer")
    company = (
        await session.execute(select(Company).where(Company.id == prospect.company_id))
    ).scalar_one_or_none() if prospect.company_id else None
    score_row = (
        await session.execute(
            select(ScoutProspectScore).where(ScoutProspectScore.prospect_id == prospect.id)
        )
    ).scalar_one_or_none()

    company_name = company.name if company else "your team"
    why_this = qualification.get("problem_evidence") or "a bounded public-web observation"
    offer_text = offer or campaign.offer or "an evidence-led commercial engagement"

    subject = f"Quick thought for {company_name}"
    body_lines = [
        f"Hi {company_name},",
        "",
        f"I came across {company_name} while researching {campaign.objective or 'local businesses'}.",
        f"What stood out: {why_this}.",
        "",
        f"I lead 11vatedTech — we build {offer_text} for teams like yours.",
        "No pitch deck, no pressure — happy to share a couple of specific ideas if useful.",
        "",
        "Best,",
        "11vatedTech",
    ]
    body = "\n".join(body_lines)
    outreach = Outreach(
        id=new_id(),
        prospect_id=prospect.id,
        person_id=prospect.person_id,
        campaign_id=campaign.id,
        channel="email",
        state=OutreachState.DRAFT.value,
        subject=subject,
        body=body,
        why_this_person=why_this,
        why_now=score_row.recommended_next_action if score_row else None,
        evidence_relevance=prospect.qualification.get("evidence"),
        value_created=offer_text,
        next_step="Reply if a quick call would be useful",
    )
    session.add(outreach)
    await session.flush()
    await _record_transition(
        session, prospect, ScoutProspectState.OUTREACH_DRAFTED,
        reason="Outreach drafted from real evidence",
    )
    return outreach


# ---------------------------------------------------------------------------
# Reply linking + learning
# ---------------------------------------------------------------------------


async def link_reply(
    session: AsyncSession,
    prospect: Prospect,
    *,
    reply_class: ScoutReplyClass,
    reason: str,
    evidence_id: str | None = None,
) -> Prospect:
    to_state = (
        ScoutProspectState.ENGAGED
        if reply_class
        in {
            ScoutReplyClass.POSITIVE_INTEREST,
            ScoutReplyClass.MEETING_REQUEST,
            ScoutReplyClass.PRICING_REQUEST,
            ScoutReplyClass.QUESTION,
        }
        else ScoutProspectState.NURTURE
    )
    if reply_class == ScoutReplyClass.OPT_OUT:
        session.add(
            SuppressionRecord(
                id=new_id(),
                scope="all_channels",
                subject_type="company" if prospect.company_id else "person",
                subject_id=prospect.company_id or prospect.person_id or "",
                reason="prospect opted out of outreach",
                status="active",
                source="scout",
                created_by="scout",
            )
        )
        to_state = ScoutProspectState.ARCHIVED
    await _record_transition(
        session, prospect, to_state, actor="scout",
        reason=f"Reply classified {reply_class.value}: {reason}",
        evidence_id=evidence_id,
    )
    session.add(
        MarketLearning(
            id=new_id(),
            market=None,
            industry=None,
            prospect_id=prospect.id,
            outcome=f"reply:{reply_class.value}",
            occurred_at=datetime.now(UTC),
        )
    )
    await session.flush()
    return prospect


# ---------------------------------------------------------------------------
# Discovery run + daily loop
# ---------------------------------------------------------------------------


def _cached_orgs(rows: list[dict[str, Any]]) -> list[DiscoveredOrganization]:
    return [
        DiscoveredOrganization(
            **{**row, "captured_at": datetime.fromisoformat(row["captured_at"])}
        )
        for row in rows
    ]


async def _discover_with_cache(
    session: AsyncSession,
    source: Any,
    query: dict[str, Any],
    *,
    limit: int,
) -> tuple[list[DiscoveredOrganization], bool]:
    """Use a persistent 30-minute cache and leave public-source failures isolated."""
    query_hash = hashlib.sha256(json.dumps(query, sort_keys=True).encode()).hexdigest()
    now = datetime.now(UTC)
    cached = (
        await session.execute(
            select(DiscoveryRequestCache).where(
                DiscoveryRequestCache.source == getattr(source, "kind", "unknown"),
                DiscoveryRequestCache.query_hash == query_hash,
            )
        )
    ).scalar_one_or_none()
    if cached and cached.expires_at > now:
        return _cached_orgs(cached.results)[:limit], True
    orgs = await source.search(query, limit=limit)
    serialized = []
    for org in orgs:
        row = asdict(org)
        row["captured_at"] = org.captured_at.isoformat()
        serialized.append(row)
    if cached is None:
        cached = DiscoveryRequestCache(
            id=new_id(), source=getattr(source, "kind", "unknown"), query_hash=query_hash,
            query=query, results=serialized, fetched_at=now,
            expires_at=now + timedelta(minutes=30), last_status="success", request_count=1,
        )
        session.add(cached)
    else:
        cached.query = query
        cached.results = serialized
        cached.fetched_at = now
        cached.expires_at = now + timedelta(minutes=30)
        cached.last_status = "success"
        cached.request_count += 1
    await session.flush()
    return orgs, False


async def run_discovery(
    session: AsyncSession,
    *,
    limit: int = 20,
    actor: str = "scout",
    run_type: str = "manual",
) -> dict[str, Any]:
    """Run one discovery pass: markets -> real orgs -> prospects -> score."""
    control = await get_control(session)
    run = ScoutRun(
        id=new_id(),
        run_type=run_type,
        started_at=datetime.now(UTC),
        status="running",
    )
    session.add(run)
    await session.flush()

    summary: dict[str, Any] = {
        "discovered": 0,
        "new_prospects": 0,
        "duplicates_skipped": 0,
        "scored": 0,
        "qualified": 0,
        "rejected": 0,
        "rejected_reasons": {},
        "errors": [],
    }
    try:
        if control.enabled is False:
            summary["skipped"] = "scout disabled"
            run.status = "completed"
            run.finished_at = datetime.now(UTC)
            run.summary = summary
            await session.flush()
            return summary

        sources = discovery_sources()
        overpass = sources["overpass"]
        default_keys = getattr(overpass, "DEFAULT_KEYS", []) or []

        # Market selection: prefer the highest-scoring thesis; fall back to a
        # rotating slice of default categories so discovery explores broadly.
        theses = await build_market_theses(session)
        thesis_tags: dict[str, list[str]] = {
            "local professional services": [
                "amenity=dentist",
                "amenity=lawyer",
                "amenity=accountant",
                "amenity=real_estate_agency",
                "amenity=insurance",
            ],
            "local hospitality & retail": [
                "amenity=restaurant",
                "amenity=cafe",
                "amenity=bar",
                "shop=clothes",
                "shop=beauty",
                "tourism=hotel",
            ],
            "creative & interactive experiences": [
                "amenity=internet_cafe",
                "shop=video_games",
                "leisure=escape_game",
            ],
        }
        def _status_str(t: MarketOpportunityThesis) -> str:
            return t.status.value if hasattr(t.status, "value") else str(t.status)

        ranked = sorted(
            (t for t in theses if _status_str(t) in {"hypothesis", "validating", "active"}),
            key=lambda t: (t.score, t.confidence),
            reverse=True,
        )
        chosen = ranked[0] if ranked else None
        tags = thesis_tags.get(chosen.market) if chosen else default_keys[:8]
        if not tags:
            tags = default_keys[:8]
        summary["market_selected"] = chosen.market if chosen else "default"
        query: dict[str, Any] = {"tags": tags}
        orgs, cache_hit = await _discover_with_cache(session, overpass, query, limit=limit)
        summary["cache_hit"] = cache_hit
        summary["discovered"] = len(orgs)
        for org in orgs:
            # Persist source evidence first (provenance), idempotently: the
            # unique (source_type, content_hash) constraint protects against
            # duplicate evidence rows on re-runs.
            content = f"{org.name} | {org.website or ''} | {org.location or ''} | {org.evidence}"
            content_hash = evidence_hash(org.source, content)
            source = (
                await session.execute(
                    select(SourceEvidence).where(
                        SourceEvidence.source_type == f"discovery:{org.source}",
                        SourceEvidence.content_hash == content_hash,
                    )
                )
            ).scalar_one_or_none()
            if source is None:
                source = SourceEvidence(
                    id=new_id(),
                    source_type=f"discovery:{org.source}",
                    source_ref=org.source_url,
                    content=content,
                    content_hash=content_hash,
                    truth_class="OBSERVATION",
                    captured_at=org.captured_at,
                    provenance={
                        "retrieval_method": org.retrieval_method,
                        "captured_at": org.captured_at.isoformat(),
                    },
                )
                session.add(source)
                await session.flush()

            prospect, is_new = await create_prospect(
                session, org, actor=actor, source_evidence=source
            )
            if not is_new:
                summary["duplicates_skipped"] += 1
                continue
            summary["new_prospects"] += 1

            # Score from the evidence we have (conservative where unknown).
            factors: dict[str, float | None] = {
                "buyer_fit": 0.5 if org.industry else None,
                "problem_severity": None,  # unknown until website reconnaissance
                "ability_to_pay": 0.5 if (org.website or org.phone or org.email) else 0.3,
                "authority_confidence": None,
                "urgency": None,
                "reachability": 0.6 if (org.email or org.website) else 0.3,
                "expected_deal_size": 0.4,
                "expected_margin": 0.6,
                "delivery_confidence": 0.5,
                "sales_cycle_efficiency": 0.4,
                "recurring_potential": 0.3,
                "repeat_potential": 0.3,
                "referral_potential": 0.4,
                "partnership_leverage": 0.2,
                "productization_potential": 0.3,
                "proof_strength": org.confidence,
                "strategic_value": 0.4,
                "founder_capacity_cost": 0.4,
                "scope_risk": 0.4,
                "payment_risk": 0.3,
                "competitive_pressure": 0.4,
            }
            await score_prospect(
                session,
                prospect,
                factors,
                confidence_dimensions={
                    "identity_confidence": org.confidence,
                    "problem_confidence": 0.0,
                    "capability_fit_confidence": 0.0,
                    "buyer_confidence": 0.0,
                    "outreach_readiness_confidence": 0.0,
                },
                confidence_reasoning={
                    "identity": "Public discovery source evidence",
                    "problem": "Unknown until official website reconnaissance",
                    "capability": "No capability evaluated at discovery stage",
                    "buyer": "No decision-maker evidence",
                    "outreach": "Not outreach-ready; discovery is not qualification",
                },
            )
            summary["scored"] += 1

            # Discovery is deliberately not qualification. A real listing is
            # retained for enrichment, but cannot enter the sales funnel until
            # reconnaissance, a problem, an approved capability, an offer, and
            # a verified contact route all pass separately.
            await _record_transition(
                session, prospect, ScoutProspectState.ENRICHMENT_REQUIRED,
                reason="Discovery identity recorded; evidence-backed qualification required",
                evidence_id=source.id,
            )
            summary["qualified"] += 0
            summary.setdefault("enrichment_required", 0)
            summary["enrichment_required"] += 1

        run.status = "completed"
        run.finished_at = datetime.now(UTC)
        run.summary = summary
        await session.flush()
        return summary
    except Exception as exc:  # noqa: BLE001
        run.status = "failed"
        run.error = str(exc)
        run.finished_at = datetime.now(UTC)
        summary["errors"].append(str(exc))
        run.summary = summary
        await session.flush()
        raise


async def build_founder_brief(session: AsyncSession) -> dict[str, Any]:
    """Morning brief: pipeline, funnel, gaps, and recommended founder actions."""
    control = await get_control(session)
    funnel = await funnel_counts(session)

    pipeline_value = await session.scalar(
        select(func.coalesce(func.sum(ScoutProspectScore.expected_value_max * ScoutProspectScore.probability), 0))
    )
    brief: dict[str, Any] = {
        "generated_at": datetime.now(UTC).isoformat(),
        "mode": control.mode.value,
        "kill_switch": control.kill_switch,
        "funnel": funnel,
        "pipeline_value": float(pipeline_value or 0),
        "recommended_actions": [],
    }
    approved_capabilities = await session.scalar(
        select(func.count(CapabilityCanon.id)).where(
            CapabilityCanon.status.in_([
                CapabilityStatus.FOUNDER_CONFIRMED,
                CapabilityStatus.EVIDENCE_VERIFIED,
            ]),
            CapabilityCanon.external_claimable.is_(True),
        )
    )
    if funnel["ready_to_contact"] > 0:
        brief["recommended_actions"].append(
            f"{funnel['ready_to_contact']} qualified prospects are ready — review and approve outreach."
        )
    if funnel["evidence_found"] > 0 and not approved_capabilities:
        brief["recommended_actions"].append(
            f"{funnel['evidence_found']} prospects have bounded problem evidence, but no approved Capability Canon entry exists; review capabilities before any offer or outreach."
        )
    if funnel["discovered"] > 0:
        brief["recommended_actions"].append(
            f"{funnel['discovered']} discovered organizations still require enrichment; they are not sales-ready."
        )
    if funnel["replies"] > 0:
        brief["recommended_actions"].append(
            f"{funnel['replies']} prospect replies need founder attention."
        )
    if funnel["won_clients"] > 0:
        brief["recommended_actions"].append(
            f"{funnel['won_clients']} won engagements — schedule delivery."
        )
    if not brief["recommended_actions"]:
        brief["recommended_actions"].append(
            "No pending commercial actions. Scout continues research in "
            f"{control.mode.value} mode."
        )
    return brief


async def funnel_counts(session: AsyncSession) -> dict[str, int]:
    rows = (
        await session.execute(
            select(Prospect.status, func.count()).group_by(Prospect.status)
        )
    ).all()
    by_status = {status: count for status, count in rows}
    # Reclassified GitHub discoveries live in the pre-prospect layer and are
    # NOT commercial prospects; they must not inflate any funnel bucket.
    by_status.pop(ScoutProspectState.RECLASSIFIED_AS_CANDIDATE.value, None)
    out: dict[str, int] = {}
    for label, states in FUNNEL_STATES.items():
        out[label] = sum(by_status.get(s.value, 0) for s in states)
    out["total"] = sum(by_status.values())
    out["rejected"] = by_status.get(ScoutProspectState.REJECTED.value, 0)
    out["archived"] = by_status.get(ScoutProspectState.ARCHIVED.value, 0)
    return out
