"""Capability Activation — first founder-confirmed capability and the
capability-driven commercial pipeline it unlocks.

This module implements the founder decision boundary (Edit & Confirm / Reject),
the persistent ``CAPABILITY_CANON_CHANGED`` event, the Problem <-> Capability
graph, buyer-oriented Offer Hypotheses, commercial-model assessment, Product/IP
hypotheses, capability-driven market theses + ranking, and a bounded real
discovery experiment — all with outbound strictly disabled.

Guarantees:

- a capability becomes externally claimable ONLY through an explicit founder
  action (Edit & Confirm); the agent never self-approves
- a rejected proposal is never deleted — it is marked REJECTED with reason and
  its evidence chain is retained
- every market thesis and offer remains a HYPOTHESIS until real market evidence
- discovery is bounded, attributable, and never sends outreach
- no synthetic commercial data is ever created
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from growthos.domain.enums import (
    CapabilityStatus,
    CommercialOfferStatus,
    MarketThesisStatus,
    ScoutProspectState,
)
from growthos.domain.models_capability import (
    CapabilityCanonEvent,
    CapabilityProductHypothesis,
    ProblemCanon,
    ProblemCapabilityMatch,
)
from growthos.domain.models_scout import (
    CapabilityCanon,
    CommercialOffer,
    MarketOpportunityThesis,
)
from growthos.domain.models_system import AuditEvent
from growthos.intelligence.capability_deepening import sanitize_commercial_text
from growthos.shared.ids import new_id

FOUNDER_ID = "founder"

# Canonical founder decision for the first real repository (GSPL-Sprites).
SPRITE_PROPOSAL_NAME = "Interactive Sprite System Prototyping"
SPRITE_CANONICAL_NAME = "Interactive Sprite Runtime & Behavior Prototyping"
SPRITE_CANONICAL_DEFINITION = (
    "Design and prototype interactive 2D sprite/character runtime systems with "
    "stateful behavior, transformations, procedural responses, and runtime "
    "interaction, grounded in demonstrated 11vatedTech implementation evidence."
)
SPRITE_EXTERNAL_SUMMARY = (
    "11vatedTech can prototype advanced interactive 2D character and sprite "
    "runtime behaviors, including stateful interactions, transformations, and "
    "custom runtime responses for experimental game and interactive-media projects."
)
SPRITE_LIMITATIONS = [
    "Prototype-level commercial maturity; not CLIENT_READY or PRODUCTION_PROVEN",
    "No independent production-client delivery evidence",
    "No external production deployment evidence",
    "No broad middleware compatibility guarantee",
    "No full-game-development claim",
    "No AAA-production claim",
    "No production-scale SDK/licensing guarantee",
    "Runtime validation remains partial",
    "Reproducibility remains medium",
]
FRONTEND_PROPOSAL_NAME = "Interactive Frontend Development"
FRONTEND_REJECT_REASON = (
    "GSPL-Sprites contains supporting project UI, but this repository does not "
    "independently prove a general externally marketable frontend-development "
    "capability. Other 11vatedTech repositories may provide stronger evidence later."
)


# ---------------------------------------------------------------------------
# Founder decisions
# ---------------------------------------------------------------------------


async def _record_review_event(
    session: AsyncSession,
    capability: CapabilityCanon,
    *,
    previous_state: str,
    new_state: str,
    action: str,
    changed_fields: dict[str, Any],
    reason: str | None,
    actor: str,
) -> None:
    from growthos.domain.models_capability import CapabilityReviewEvent

    session.add(
        CapabilityReviewEvent(
            id=new_id(),
            capability_id=capability.id,
            previous_state=previous_state,
            new_state=new_state,
            changed_fields=changed_fields,
            action=action,
            reason=reason,
            evidence_context={
                "proof_evidence": capability.proof_evidence,
                "limitations": capability.limitations,
            },
            actor=actor,
            occurred_at=datetime.now(UTC),
        )
    )
    session.add(
        AuditEvent(
            actor=actor,
            action=f"capability:{action}",
            entity_type="capability_canon",
            entity_id=capability.id,
            previous_state={"status": previous_state, "name": capability.name},
            new_state={"status": new_state, "name": capability.name},
            reason=reason,
            context={"changed_fields": list(changed_fields.keys())},
        )
    )


async def confirm_capability(
    session: AsyncSession,
    capability: CapabilityCanon,
    *,
    name: str,
    definition: str,
    maturity: str,
    limitations: list[str],
    external_summary: str,
    note: str | None = None,
    actor: str = "founder",
) -> CapabilityCanon:
    """Edit & Confirm: founder canonizes a capability with corrected scope.

    This is the ONLY path that makes a capability externally claimable.
    """
    if not name.strip() or not definition.strip():
        raise ValueError("Capability name and definition are required")
    previous_state = getattr(capability.status, "value", None) or str(capability.status)
    previous_name = capability.name
    changed: dict[str, Any] = {}
    if capability.name != name.strip():
        changed["name"] = {"from": previous_name, "to": name.strip()}
    if capability.definition != definition.strip():
        changed["definition"] = {"from": capability.definition, "to": definition.strip()}
    if (capability.maturity or "") != maturity:
        changed["maturity"] = {"from": capability.maturity, "to": maturity}
    if list(capability.limitations) != list(limitations):
        changed["limitations"] = {"from": list(capability.limitations), "to": list(limitations)}
    if (capability.external_summary or "") != external_summary:
        changed["external_summary"] = {"from": capability.external_summary, "to": external_summary}

    await _record_review_event(
        session,
        capability,
        previous_state=previous_state,
        new_state=CapabilityStatus.FOUNDER_CONFIRMED.value,
        action="EDIT_AND_CONFIRM",
        changed_fields=changed,
        reason=note,
        actor=actor,
    )

    capability.name = name.strip()
    capability.definition = definition.strip()
    capability.maturity = maturity
    capability.limitations = list(limitations)
    capability.external_summary = sanitize_commercial_text(external_summary)
    capability.status = CapabilityStatus.FOUNDER_CONFIRMED
    capability.external_claimable = True
    capability.entered_from = actor
    capability.founder_review_note = note or capability.founder_review_note

    await session.flush()
    await emit_canon_event(
        session, capability,
        event_type="CAPABILITY_CANON_CHANGED",
        payload={
            "capability_id": capability.id,
            "name": capability.name,
            "changed_state": CapabilityStatus.FOUNDER_CONFIRMED.value,
            "changed_scope": "renamed and narrowed to " + capability.name,
            "new_limitations": list(capability.limitations),
            "affected_problem_categories": _problem_classes_for(capability),
        },
    )
    return capability


async def reject_capability(
    session: AsyncSession,
    capability: CapabilityCanon,
    *,
    reason: str,
    actor: str = "founder",
) -> CapabilityCanon:
    """Reject a proposal for its evidence chain.

    The proposal and its evidence are retained; only the status changes so
    Revenue Scout cannot market it. This is not a global verdict on the company.
    """
    if not reason.strip():
        raise ValueError("A rejection reason is required")
    previous_state = getattr(capability.status, "value", None) or str(capability.status)
    await _record_review_event(
        session,
        capability,
        previous_state=previous_state,
        new_state=CapabilityStatus.REJECTED.value,
        action="REJECT",
        changed_fields={"reason": reason},
        reason=reason,
        actor=actor,
    )
    capability.status = CapabilityStatus.REJECTED
    capability.external_claimable = False
    capability.founder_review_note = reason
    capability.entered_from = actor
    await session.flush()
    return capability


# ---------------------------------------------------------------------------
# Persistent canon events
# ---------------------------------------------------------------------------


async def emit_canon_event(
    session: AsyncSession,
    capability: CapabilityCanon,
    *,
    event_type: str = "CAPABILITY_CANON_CHANGED",
    payload: dict[str, Any],
) -> CapabilityCanonEvent:
    event = CapabilityCanonEvent(
        id=new_id(),
        capability_id=capability.id,
        event_type=event_type,
        payload=payload,
        status="pending",
        occurred_at=datetime.now(UTC),
    )
    session.add(event)
    await session.flush()
    return event


async def pending_canon_events(session: AsyncSession) -> list[CapabilityCanonEvent]:
    rows = (
        await session.execute(
            select(CapabilityCanonEvent)
            .where(CapabilityCanonEvent.status == "pending")
            .order_by(CapabilityCanonEvent.occurred_at)
        )
    ).scalars().all()
    return list(rows)


# ---------------------------------------------------------------------------
# Problem <-> Capability graph
# ---------------------------------------------------------------------------


def _problem_classes_for(capability: CapabilityCanon) -> list[str]:
    """Normalized problem classes a capability plausibly addresses.

    Derived from the capability definition and evidence; remains hypothesis
    until a prospect observation links to it.
    """
    corpus = f"{capability.name} {capability.definition}".lower()
    classes = [
        "interactive character behavior needs",
        "custom 2D runtime interaction",
        "prototype character-system development",
        "stateful sprite behavior",
        "runtime character state and transformation systems",
        "experimental 2D game mechanics",
        "interactive-media character systems",
    ]
    if "frontend" in corpus:
        classes += ["interactive web experience needs", "conversion-focused frontend development"]
    return classes


async def build_problem_graph(
    session: AsyncSession, capability: CapabilityCanon
) -> list[dict[str, Any]]:
    """Create Problem Canon entries + ProblemCapabilityMatch records."""
    created: list[dict[str, Any]] = []
    for problem_name in _problem_classes_for(capability):
        problem = (
            await session.execute(
                select(ProblemCanon).where(ProblemCanon.name == problem_name)
            )
        ).scalar_one_or_none()
        if problem is None:
            problem = ProblemCanon(
                id=new_id(),
                name=problem_name,
                definition=(
                    f"Observed or hypothesized buyer need addressed by {capability.name}: "
                    f"{problem_name}."
                ),
                status="hypothesis",
            )
            session.add(problem)
            await session.flush()
        match = (
            await session.execute(
                select(ProblemCapabilityMatch).where(
                    ProblemCapabilityMatch.problem_id == problem.id,
                    ProblemCapabilityMatch.capability_id == capability.id,
                )
            )
        ).scalar_one_or_none()
        if match is None:
            match = ProblemCapabilityMatch(
                id=new_id(),
                problem_id=problem.id,
                capability_id=capability.id,
                fit_confidence=0.7,
                reasoning=(
                    f"{capability.name} directly addresses {problem_name} through "
                    "stateful runtime behavior, transformations, and procedural "
                    "responses grounded in demonstrated implementation evidence."
                ),
                delivery_complexity=0.5,
                founder_effort="medium",
                reuse_potential=0.6,
                limitations=list(capability.limitations),
                commercial_suitability=0.5,
            )
            session.add(match)
            await session.flush()
        created.append({"problem": problem.name, "fit_confidence": match.fit_confidence})
    return created


# ---------------------------------------------------------------------------
# Commercial models
# ---------------------------------------------------------------------------


def assess_commercial_models(capability: CapabilityCanon) -> list[dict[str, str]]:
    """Evaluate which commercial models fit the confirmed capability.

    Licensing/SDK positioning must not outrun evidence: the codebase is a
    prototype, so licensing and middleware are NOT currently supported.
    """
    models = [
        {"model": "custom prototype engagement", "fit": "FIT", "notes": "Primary model; directly matches the demonstrated prototype capability."},
        {"model": "R&D engagement", "fit": "FIT", "notes": "Experimental character-runtime research aligns with the evidence."},
        {"model": "technical consulting", "fit": "POSSIBLE", "notes": "Advisory work is possible but secondary to hands-on prototyping."},
        {"model": "implementation sprint", "fit": "POSSIBLE", "notes": "Bounded sprints fit prototype-level maturity."},
        {"model": "white-label development", "fit": "POSSIBLE", "notes": "Agencies could resell bounded prototyping; delivery risk is medium."},
        {"model": "recurring support", "fit": "WEAK", "notes": "No recurring product or support contract exists yet."},
        {"model": "licensing", "fit": "NOT_CURRENTLY_SUPPORTED", "notes": "The codebase is not yet suitable for external licensing."},
        {"model": "SDK/tooling", "fit": "NOT_CURRENTLY_SUPPORTED", "notes": "No packaged SDK exists; prototype only."},
        {"model": "middleware", "fit": "NOT_CURRENTLY_SUPPORTED", "notes": "No middleware guarantee can be made at prototype maturity."},
    ]
    return models


# ---------------------------------------------------------------------------
# Offer hypotheses
# ---------------------------------------------------------------------------


async def build_offer_hypotheses(
    session: AsyncSession, capability: CapabilityCanon
) -> list[CommercialOffer]:
    """Generate buyer-oriented Offer Hypotheses (never market-validated)."""
    specs = [
        {
            "name": "Interactive Character Systems Prototype",
            "buyer": "2D indie & mobile game studios",
            "problem": "Need a working interactive character/sprite runtime prototype before committing to production.",
            "deliverable": "A bounded prototype of a stateful 2D character runtime with transformations and procedural responses.",
            "timeline": "2-4 weeks",
            "price": {"min": 5000, "max": 15000, "model": "fixed-scope prototype"},
            "margin": 0.65,
            "effort": "medium",
            "reuse": 0.6,
            "licensing": "low",
            "white_label": "medium",
        },
        {
            "name": "2D Runtime Behavior Prototype",
            "buyer": "interactive-media & creative technology studios",
            "problem": "Need a custom 2D runtime behavior system for an interactive experience or product.",
            "deliverable": "Prototype runtime behavior (state, transformation, interaction) for an interactive-media product.",
            "timeline": "2-4 weeks",
            "price": {"min": 5000, "max": 18000, "model": "fixed-scope prototype"},
            "margin": 0.65,
            "effort": "medium",
            "reuse": 0.55,
            "licensing": "low",
            "white_label": "medium",
        },
        {
            "name": "Character Transformation Systems Sprint",
            "buyer": "animation technology & tooling companies",
            "problem": "Need a prototype of character state/transformation behavior for tooling or pipeline R&D.",
            "deliverable": "A focused sprint delivering a character transformation/state system prototype.",
            "timeline": "1-3 weeks",
            "price": {"min": 4000, "max": 12000, "model": "sprint"},
            "margin": 0.7,
            "effort": "low-medium",
            "reuse": 0.7,
            "licensing": "low",
            "white_label": "medium",
        },
        {
            "name": "Playable Character Systems R&D Engagement",
            "buyer": "game studios & IP holders exploring interactive character products",
            "problem": "Need R&D de-risking for playable character systems before larger investment.",
            "deliverable": "R&D engagement producing a playable/stateful character system prototype with documented behavior.",
            "timeline": "3-6 weeks",
            "price": {"min": 8000, "max": 25000, "model": "R&D retainer"},
            "margin": 0.6,
            "effort": "high",
            "reuse": 0.5,
            "licensing": "low",
            "white_label": "medium",
        },
    ]
    created: list[CommercialOffer] = []
    for spec in specs:
        existing = (
            await session.execute(
                select(CommercialOffer).where(CommercialOffer.name == spec["name"])
            )
        ).scalar_one_or_none()
        if existing is not None:
            created.append(existing)
            continue
        offer = CommercialOffer(
            id=new_id(),
            name=spec["name"],
            buyer=spec["buyer"],
            problem=spec["problem"],
            deliverable=spec["deliverable"],
            included_capability_ids=[capability.id],
            expected_outcome="Prototype of the described character/runtime system for founder + prospect validation.",
            scope_boundaries=[
                "Prototype scope only; no production middleware or SDK guarantee",
                "No full-game-development or AAA-production claim",
            ],
            delivery_model="fixed-scope prototype",
            timeline_hypothesis=spec["timeline"],
            price_hypothesis=spec["price"],
            entry_offer="Interactive Character Systems Prototype",
            premium_offer="Playable Character Systems R&D Engagement",
            recurring_component=None,
            proof_required=["founder-confirmed capability proof", "prototype demonstration"],
            exclusions=[
                "No production delivery without additional evidence",
                "No production-scale licensing",
            ],
            risks=list(capability.limitations),
            status=CommercialOfferStatus.HYPOTHESIS,
            source_evidence_ids=capability.source_evidence_ids,
        )
        session.add(offer)
        await session.flush()
        created.append(offer)
    return created


# ---------------------------------------------------------------------------
# Product / IP hypotheses
# ---------------------------------------------------------------------------


async def build_product_hypotheses(
    session: AsyncSession, capability: CapabilityCanon
) -> list[CapabilityProductHypothesis]:
    """Product/IP/SDK/middleware hypotheses — separate from Capability Canon."""
    specs = [
        {
            "hypothesis_type": "PRODUCT_HYPOTHESIS",
            "name": "Sprite Runtime Prototyping Service",
            "rationale": "The confirmed capability is a repeatable prototyping service; a productized engagement could standardize scope, price, and delivery.",
        },
        {
            "hypothesis_type": "IP_HYPOTHESIS",
            "name": "Sprite Runtime Behavior Technology",
            "rationale": "The GSPL-Sprites implementation demonstrates stateful sprite runtime behavior that could become licensable IP if matured and productized.",
        },
        {
            "hypothesis_type": "SDK_HYPOTHESIS",
            "name": "Sprite Runtime SDK",
            "rationale": "An SDK would require packaging, documentation, and support the prototype does not yet provide; hypothesis only.",
        },
        {
            "hypothesis_type": "MIDDLEWARE_HYPOTHESIS",
            "name": "Sprite Runtime Middleware",
            "rationale": "Middleware positioning is out of reach at prototype maturity; recorded as a future hypothesis, not a claim.",
        },
    ]
    created: list[CapabilityProductHypothesis] = []
    for spec in specs:
        existing = (
            await session.execute(
                select(CapabilityProductHypothesis).where(
                    CapabilityProductHypothesis.capability_id == capability.id,
                    CapabilityProductHypothesis.hypothesis_type == spec["hypothesis_type"],
                    CapabilityProductHypothesis.name == spec["name"],
                )
            )
        ).scalar_one_or_none()
        if existing is not None:
            created.append(existing)
            continue
        row = CapabilityProductHypothesis(
            id=new_id(),
            capability_id=capability.id,
            hypothesis_type=spec["hypothesis_type"],
            name=spec["name"],
            rationale=spec["rationale"],
            status="HYPOTHESIS",
        )
        session.add(row)
        await session.flush()
        created.append(row)
    return created


# ---------------------------------------------------------------------------
# Capability-driven market theses + ranking
# ---------------------------------------------------------------------------


def _thesis_scores(spec: dict[str, Any]) -> tuple[float, float, float]:
    deal = (float(spec.get("expected_deal_min", 0)) + float(spec.get("expected_deal_max", 0))) / 2
    deal_norm = min(1.0, deal / 30000.0)
    short = (
        0.25 * deal_norm
        + 0.20 * (1.0 - float(spec.get("acquisition_difficulty", 0.5)))
        + 0.20 * (1.0 if "week" in (spec.get("sales_cycle_hypothesis") or "") else 0.5)
        + 0.15 * float(spec.get("margin_hypothesis", 0.5))
        + 0.20 * float(spec.get("confidence", 0.0))
    )
    strategic = (
        0.30 * float(spec.get("strategic_value", 0.5))
        + 0.20 * float(spec.get("repeat_potential", 0.4))
        + 0.20 * float(spec.get("partnership_potential", 0.4))
        + 0.15 * float(spec.get("licensing_potential", 0.2))
        + 0.15 * (1.0 - float(spec.get("founder_effort_cost", 0.5)))
    )
    combined = 0.6 * short + 0.4 * strategic
    return round(min(1.0, short), 4), round(min(1.0, strategic), 4), round(min(1.0, combined), 4)


async def build_capability_market_theses(
    session: AsyncSession, capability: CapabilityCanon
) -> list[MarketOpportunityThesis]:
    """Autonomously generate competing market hypotheses from the capability.

    These are HYPOTHESES: the scout does not claim demand exists without
    external evidence. The bounded discovery experiment validates one of them.
    """
    specs = [
        {
            "market": "2D indie & mobile game studios",
            "buyer": "indie and mobile studios building 2D character/sprite-driven games",
            "buyer_role": "studio founder / technical director / game director",
            "problem": "Need interactive character runtime prototypes and stateful behavior systems before production commitment",
            "solution": capability.external_summary or capability.definition,
            "commercial_model": "custom prototype engagement",
            "expected_deal_min": 5000, "expected_deal_max": 15000,
            "sales_cycle_hypothesis": "2-6 weeks",
            "margin_hypothesis": 0.65,
            "acquisition_difficulty": 0.45,
            "strategic_value": 0.8,
            "repeat_potential": 0.6, "partnership_potential": 0.6,
            "licensing_potential": 0.3, "founder_effort_cost": 0.4,
            "confidence": 0.4,
            "reachability": "GitHub public metadata; direct contact unverified",
            "evidence_availability": "Public repos/topics; need-driven evidence required",
            "discovery_source": "github",
        },
        {
            "market": "interactive-media & creative technology studios",
            "buyer": "studios delivering interactive digital experiences",
            "buyer_role": "creative director / technical lead / producer",
            "problem": "Need custom 2D runtime behavior and interactive character systems for products and campaigns",
            "solution": capability.external_summary or capability.definition,
            "commercial_model": "custom prototype engagement / R&D engagement",
            "expected_deal_min": 6000, "expected_deal_max": 20000,
            "sales_cycle_hypothesis": "3-8 weeks",
            "margin_hypothesis": 0.6,
            "acquisition_difficulty": 0.5,
            "strategic_value": 0.7,
            "repeat_potential": 0.5, "partnership_potential": 0.7,
            "licensing_potential": 0.3, "founder_effort_cost": 0.5,
            "confidence": 0.35,
            "reachability": "GitHub public metadata; direct contact unverified",
            "evidence_availability": "Public repos/topics; need-driven evidence required",
            "discovery_source": "github",
        },
        {
            "market": "animation technology & tooling companies",
            "buyer": "companies building animation/sprite tooling and pipelines",
            "buyer_role": "tools engineer / technical director / R&D lead",
            "problem": "Need prototype character state/transformation systems for tooling or pipeline R&D",
            "solution": capability.external_summary or capability.definition,
            "commercial_model": "implementation sprint / R&D engagement",
            "expected_deal_min": 4000, "expected_deal_max": 12000,
            "sales_cycle_hypothesis": "2-5 weeks",
            "margin_hypothesis": 0.7,
            "acquisition_difficulty": 0.4,
            "strategic_value": 0.6,
            "repeat_potential": 0.7, "partnership_potential": 0.5,
            "licensing_potential": 0.4, "founder_effort_cost": 0.4,
            "confidence": 0.35,
            "reachability": "GitHub public metadata; direct contact unverified",
            "evidence_availability": "Public repos/topics; need-driven evidence required",
            "discovery_source": "github",
        },
        {
            "market": "IP / character-driven digital experiences",
            "buyer": "IP holders and studios with character-driven products",
            "buyer_role": "producer / creative director / brand lead",
            "problem": "Need interactive character experiences for IP-driven digital products",
            "solution": capability.external_summary or capability.definition,
            "commercial_model": "R&D engagement / custom prototype",
            "expected_deal_min": 8000, "expected_deal_max": 25000,
            "sales_cycle_hypothesis": "4-10 weeks",
            "margin_hypothesis": 0.6,
            "acquisition_difficulty": 0.6,
            "strategic_value": 0.8,
            "repeat_potential": 0.5, "partnership_potential": 0.6,
            "licensing_potential": 0.5, "founder_effort_cost": 0.6,
            "confidence": 0.3,
            "reachability": "GitHub public metadata; direct contact unverified",
            "evidence_availability": "Public repos/topics; need-driven evidence required",
            "discovery_source": "github",
        },
        {
            "market": "independent game-tool & middleware developers",
            "buyer": "independent tool developers building game/creative tooling",
            "buyer_role": "tools engineer / technical lead",
            "problem": "Need prototype runtime behavior systems for game/creative tooling",
            "solution": capability.external_summary or capability.definition,
            "commercial_model": "technical consulting / implementation sprint",
            "expected_deal_min": 4000, "expected_deal_max": 10000,
            "sales_cycle_hypothesis": "2-4 weeks",
            "margin_hypothesis": 0.7,
            "acquisition_difficulty": 0.4,
            "strategic_value": 0.6,
            "repeat_potential": 0.6, "partnership_potential": 0.6,
            "licensing_potential": 0.4, "founder_effort_cost": 0.4,
            "confidence": 0.3,
            "reachability": "GitHub public metadata; direct contact unverified",
            "evidence_availability": "Public repos/topics; need-driven evidence required",
            "discovery_source": "github",
        },
    ]
    created: list[MarketOpportunityThesis] = []
    for spec in specs:
        short, strategic, combined = _thesis_scores(spec)
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
                expected_deal_min=spec["expected_deal_min"],
                expected_deal_max=spec["expected_deal_max"],
                sales_cycle_hypothesis=spec["sales_cycle_hypothesis"],
                margin_hypothesis=spec["margin_hypothesis"],
                competition="specialist game/creative technology studios",
                proof_required=["playable prototype", "case study"],
                acquisition_difficulty=spec["acquisition_difficulty"],
                strategic_value=spec["strategic_value"],
                confidence=spec["confidence"],
                score=combined,
                status=MarketThesisStatus.HYPOTHESIS,
                evidence_summary=(
                    f"Capability-driven hypothesis grounded in the founder-confirmed "
                    f"capability '{capability.name}'. Reachability: {spec['reachability']}. "
                    f"Evidence availability: {spec['evidence_availability']}. "
                    "No external demand is asserted until discovery evidence exists."
                ),
                capability_id=capability.id,
                selection_reasoning=(
                    f"Derived from the confirmed capability '{capability.name}': "
                    f"buyer role {spec['buyer_role']}; problem '{spec['problem']}'."
                ),
                discovery_source=spec["discovery_source"],
                short_term_score=short,
                strategic_score=strategic,
            )
            session.add(thesis)
            await session.flush()
        else:
            thesis.short_term_score = short
            thesis.strategic_score = strategic
            thesis.score = combined
            thesis.capability_id = capability.id  # type: ignore[assignment]
            thesis.discovery_source = str(spec["discovery_source"])
        created.append(thesis)
    return created


async def rank_markets(session: AsyncSession) -> list[MarketOpportunityThesis]:
    """Deterministically recompute ranking with separate short/strategic scores."""
    theses = (await session.execute(select(MarketOpportunityThesis))).scalars().all()
    for thesis in theses:
        spec = {
            "expected_deal_min": float(thesis.expected_deal_min or 0) if thesis.expected_deal_min else 0,
            "expected_deal_max": float(thesis.expected_deal_max or 0) if thesis.expected_deal_max else 0,
            "acquisition_difficulty": float(thesis.acquisition_difficulty or 0.5),
            "sales_cycle_hypothesis": thesis.sales_cycle_hypothesis,
            "margin_hypothesis": float(thesis.margin_hypothesis or 0.5),
            "confidence": float(thesis.confidence or 0.0),
            "strategic_value": float(thesis.strategic_value or 0.5),
            "repeat_potential": 0.6 if thesis.capability_id else 0.4,
            "partnership_potential": 0.6 if thesis.capability_id else 0.3,
            "licensing_potential": 0.3 if thesis.capability_id else 0.2,
            "founder_effort_cost": 0.4,
        }
        short, strategic, combined = _thesis_scores(spec)
        thesis.short_term_score = short
        thesis.strategic_score = strategic
        thesis.score = combined
    await session.flush()
    rows = (await session.execute(select(MarketOpportunityThesis))).scalars().all()
    return sorted(rows, key=lambda t: (t.score, t.short_term_score, t.confidence), reverse=True)


async def select_validation_market(
    session: AsyncSession, capability: CapabilityCanon
) -> MarketOpportunityThesis | None:
    """Pick the top-ranked capability-driven thesis (no founder category input)."""
    ranked = await rank_markets(session)
    for thesis in ranked:
        if thesis.capability_id == capability.id and thesis.status != MarketThesisStatus.REJECTED:
            return thesis
    return None


# ---------------------------------------------------------------------------
# Bounded capability-driven discovery experiment
# ---------------------------------------------------------------------------


async def run_capability_discovery(
    session: AsyncSession,
    capability: CapabilityCanon,
    *,
    limit: int = 15,
    actor: str = "scout",
) -> dict[str, Any]:
    """Run a bounded real discovery experiment for the confirmed capability.

    The scout selects its own validation market (no founder category input),
    then queries the applicable public source. Every discovered organization
    is a real public entity with provenance. No outreach is ever sent here.

    ``limit`` is clamped to a bounded validation cohort (10-20) — this is not
    a mass lead scrape.
    """
    from growthos.domain.models_evidence import SourceEvidence
    from growthos.intelligence.discovery import discovery_sources, evidence_hash
    from growthos.services.scout import _record_transition, create_prospect, score_prospect

    limit = max(10, min(20, limit))
    thesis = await select_validation_market(session, capability)
    if thesis is None:
        return {
            "selected_market": None,
            "reason": "No capability-driven validation market available",
            "discovered": 0,
            "outbound": "disabled",
        }

    source_kind = thesis.discovery_source or "github"
    sources = discovery_sources()
    source = sources.get(source_kind)
    if source is None:
        return {
            "selected_market": thesis.market,
            "reason": f"Discovery source '{source_kind}' is not live",
            "discovered": 0,
            "outbound": "disabled",
        }

    # Capability-grounded queries: public repo topics relevant to the
    # confirmed sprite-runtime capability.
    query: dict[str, Any] = {
        "q": "topic:2d topic:sprite topic:game",
        "sort": "stars",
        "industry_label": thesis.market,
    }
    if capability.name.lower().startswith("interactive frontend"):
        query["q"] = "topic:frontend topic:interactive"

    orgs: list[Any] = []
    source_error: str | None = None
    try:
        orgs = await source.search(query, limit=limit)
    except Exception as exc:  # noqa: BLE001
        source_error = f"{source_kind} discovery failed: {exc}"

    summary: dict[str, Any] = {
        "selected_market": thesis.market,
        "selection_reasoning": thesis.selection_reasoning,
        "discovery_source": source_kind,
        "source_error": source_error,
        "discovered": len(orgs),
        "new_prospects": 0,
        "duplicates_skipped": 0,
        "problem_evidence": 0,
        "capability_matches": 0,
        "ready_to_contact": 0,
        "prospects": [],
        "outbound": "disabled",
    }

    for org in orgs:
        content = f"{org.name} | {org.website or ''} | {org.location or ''} | {org.evidence}"
        content_hash = evidence_hash(org.source, content)
        source_evidence = (
            await session.execute(
                select(SourceEvidence).where(
                    SourceEvidence.source_type == f"discovery:{org.source}",
                    SourceEvidence.content_hash == content_hash,
                )
            )
        ).scalar_one_or_none()
        if source_evidence is None:
            source_evidence = SourceEvidence(
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
                    "market_thesis": thesis.market,
                    "capability": capability.name,
                },
            )
            session.add(source_evidence)
            await session.flush()

        prospect, is_new = await create_prospect(
            session, org, actor=actor, source_evidence=source_evidence
        )
        if not is_new:
            summary["duplicates_skipped"] += 1
            continue
        summary["new_prospects"] += 1

        # Discovery is not qualification: a real public entity is retained for
        # enrichment, never auto-promoted to sales-ready.
        await _record_transition(
            session, prospect, ScoutProspectState.ENRICHMENT_REQUIRED,
            reason=f"Discovered via {source_kind} for the confirmed capability '{capability.name}'; qualification requires evidence",
            evidence_id=source_evidence.id,
        )
        await score_prospect(
            session,
            prospect,
            {
                "buyer_fit": 0.5,
                "problem_severity": None,
                "ability_to_pay": 0.4,
                "authority_confidence": None,
                "urgency": None,
                "reachability": 0.3,
                "expected_deal_size": 0.4,
                "expected_margin": 0.6,
                "delivery_confidence": 0.5,
                "sales_cycle_efficiency": 0.4,
                "recurring_potential": 0.3,
                "repeat_potential": 0.3,
                "referral_potential": 0.3,
                "partnership_leverage": 0.4,
                "productization_potential": 0.3,
                "proof_strength": org.confidence,
                "strategic_value": 0.6,
                "founder_capacity_cost": 0.4,
                "scope_risk": 0.4,
                "payment_risk": 0.4,
                "competitive_pressure": 0.4,
            },
            confidence_dimensions={
                "identity_confidence": org.confidence,
                "problem_confidence": 0.0,
                "capability_fit_confidence": 0.0,
                "buyer_confidence": 0.0,
                "outreach_readiness_confidence": 0.0,
            },
            confidence_reasoning={
                "identity": "Public GitHub metadata (owner + repository evidence)",
                "problem": "Unknown until research; discovery is not qualification",
                "capability": "Not evaluated at discovery stage",
                "buyer": "No decision-maker evidence",
                "outreach": "Not outreach-ready",
            },
        )
        summary["prospects"].append(
            {
                "id": prospect.id,
                "company": org.name,
                "source": org.source,
                "source_url": org.source_url,
                "evidence": org.evidence,
                "state": prospect.status,
            }
        )
    await session.flush()
    return summary


# ---------------------------------------------------------------------------
# Selective requalification (event processing)
# ---------------------------------------------------------------------------


async def _requalify_affected_prospects(
    session: AsyncSession, capability: CapabilityCanon
) -> dict[str, Any]:
    """Requalify only prospects that already carry problem evidence, reusing
    existing website audits (no new external requests)."""
    from growthos.domain.models_commercial import Prospect
    from growthos.services.scout import requalify_prospect

    states = [
        ScoutProspectState.PROBLEM_EVIDENCE_FOUND.value,
        ScoutProspectState.CAPABILITY_MATCHED.value,
        ScoutProspectState.OFFER_DEFINED.value,
        ScoutProspectState.CONTACT_PATH_VERIFIED.value,
        ScoutProspectState.SALES_QUALIFIED.value,
        ScoutProspectState.READY_TO_CONTACT.value,
        ScoutProspectState.NURTURE.value,
    ]
    prospects = (
        await session.execute(
            select(Prospect).where(Prospect.status.in_(states))
        )
    ).scalars().all()
    report: dict[str, Any] = {
        "reconsidered": len(prospects),
        "capability_matches": 0,
        "no_match": 0,
        "nurture": 0,
        "problem_evidence": 0,
        "prospects": [],
    }
    for prospect in prospects:
        result = await requalify_prospect(session, prospect, actor="scout", reuse_audit=True)
        report["problem_evidence"] += int(result.get("problem_evidence", False))
        report["capability_matches"] += int(result.get("capability_matches", 0) > 0)
        report["no_match"] += int(result.get("capability_matches", 0) == 0)
        report["nurture"] += int(result.get("state") == ScoutProspectState.NURTURE.value)
        report["prospects"].append(
            {"id": prospect.id, "company": result.get("company"), "state": result.get("state"),
             "capability_matches": result.get("capability_matches", 0)}
        )
    return report


async def process_canon_events(session: AsyncSession) -> dict[str, Any]:
    """Process pending CAPABILITY_CANON_CHANGED events (restart-safe)."""
    events = await pending_canon_events(session)
    results: list[dict[str, Any]] = []
    for event in events:
        capability = (
            await session.execute(
                select(CapabilityCanon).where(CapabilityCanon.id == event.capability_id)
            )
        ).scalar_one_or_none()
        try:
            if capability is None:
                raise ValueError("capability no longer exists")
            requalification = await _requalify_affected_prospects(session, capability)
            event.status = "processed"
            event.processed_at = datetime.now(UTC)
            event.error = None
            results.append({"event_id": event.id, "capability": capability.name, "requalification": requalification})
        except Exception as exc:  # noqa: BLE001
            event.status = "failed"
            event.error = str(exc)
            results.append({"event_id": event.id, "capability_id": event.capability_id, "error": str(exc)})
    await session.flush()
    return {"processed": results}


# ---------------------------------------------------------------------------
# Activation pipeline
# ---------------------------------------------------------------------------


async def activate_capability(
    session: AsyncSession, capability: CapabilityCanon, *, actor: str = "founder"
) -> dict[str, Any]:
    """Run the full downstream pipeline for a founder-confirmed capability.

    This is invoked after the founder decision is persisted. It does not send
    outreach and does not fabricate commercial data.
    """
    if capability.status != CapabilityStatus.FOUNDER_CONFIRMED:
        raise ValueError(
            "Only a founder-confirmed capability can be activated; status is "
            f"{getattr(capability.status, 'value', capability.status)}"
        )
    problem_graph = await build_problem_graph(session, capability)
    capability.commercial_models = assess_commercial_models(capability)
    offers = await build_offer_hypotheses(session, capability)
    product_hypotheses = await build_product_hypotheses(session, capability)
    theses = await build_capability_market_theses(session, capability)
    ranked = await rank_markets(session)
    selected = await select_validation_market(session, capability)
    requalification = await _requalify_affected_prospects(session, capability)
    await session.flush()
    return {
        "capability_id": capability.id,
        "capability": capability.name,
        "problem_graph": problem_graph,
        "offer_hypotheses": [o.name for o in offers],
        "product_hypotheses": [p.name for p in product_hypotheses],
        "market_theses": [t.market for t in theses],
        "selected_validation_market": selected.market if selected else None,
        "market_ranking": [{"market": t.market, "score": t.score, "short_term": t.short_term_score, "strategic": t.strategic_score, "confidence": t.confidence} for t in ranked],
        "requalification": requalification,
        "outbound": "disabled",
    }


async def activation_state(session: AsyncSession, capability: CapabilityCanon) -> dict[str, Any]:
    """Serialize the full activation state for the founder workspace."""
    from growthos.domain.models_capability import CapabilityProductHypothesis as CPH
    from growthos.domain.models_scout import CommercialOffer as CO

    offers = (await session.execute(select(CO).where(CO.included_capability_ids.contains([capability.id])))).scalars().all()
    problems = (await session.execute(select(ProblemCanon))).scalars().all()
    matches = (
        await session.execute(
            select(ProblemCapabilityMatch).where(ProblemCapabilityMatch.capability_id == capability.id)
        )
    ).scalars().all()
    hypotheses = (await session.execute(select(CPH).where(CPH.capability_id == capability.id))).scalars().all()
    theses = (await session.execute(select(MarketOpportunityThesis).where(MarketOpportunityThesis.capability_id == capability.id))).scalars().all()
    events = (
        await session.execute(
            select(CapabilityCanonEvent).where(CapabilityCanonEvent.capability_id == capability.id)
        )
    ).scalars().all()
    return {
        "capability": {
            "id": capability.id,
            "name": capability.name,
            "definition": capability.definition,
            "status": getattr(capability.status, "value", str(capability.status)),
            "external_claimable": capability.external_claimable,
            "maturity": capability.maturity,
            "external_summary": capability.external_summary,
            "limitations": capability.limitations,
            "commercial_models": capability.commercial_models,
            "founder_review_note": capability.founder_review_note,
        },
        "problem_graph": [
            {"problem": m.problem_id, "capability": m.capability_id, "fit_confidence": m.fit_confidence, "reasoning": m.reasoning}
            for m in matches
        ],
        "problem_canon": [{"id": p.id, "name": p.name, "status": p.status} for p in problems],
        "offers": [
            {
                "id": o.id, "name": o.name, "buyer": o.buyer, "problem": o.problem,
                "deliverable": o.deliverable, "status": getattr(o.status, "value", str(o.status)),
                "timeline_hypothesis": o.timeline_hypothesis, "price_hypothesis": o.price_hypothesis,
                "delivery_model": o.delivery_model, "risks": o.risks, "exclusions": o.exclusions,
            }
            for o in offers
        ],
        "product_hypotheses": [
            {"id": h.id, "hypothesis_type": h.hypothesis_type, "name": h.name, "rationale": h.rationale, "status": h.status}
            for h in hypotheses
        ],
        "market_theses": [
            {
                "id": t.id, "market": t.market, "buyer": t.buyer, "problem": t.problem,
                "score": t.score, "short_term_score": t.short_term_score,
                "strategic_score": t.strategic_score, "confidence": t.confidence,
                "status": getattr(t.status, "value", str(t.status)),
                "selection_reasoning": t.selection_reasoning,
                "discovery_source": t.discovery_source,
            }
            for t in theses
        ],
        "events": [
            {"id": e.id, "event_type": e.event_type, "status": e.status, "occurred_at": e.occurred_at.isoformat(), "payload": e.payload}
            for e in events
        ],
        "outbound": "disabled",
    }
