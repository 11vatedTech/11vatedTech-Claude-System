"""Revenue Scout API routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import select

from growthos.api.deps import FounderDep, SessionDep
from growthos.domain.models_capability import (
    CapabilityEvidenceRecord,
    ProjectEvidenceRecord,
    TrustedRepositoryRoot,
)
from growthos.domain.models_commercial import Prospect
from growthos.domain.models_identity import Company, Person
from growthos.domain.models_scout import (
    CapabilityCanon,
    CommercialOffer,
    DiscoveryCandidate,
    MarketOpportunityThesis,
    ScoutControl,
    ScoutProspectScore,
)
from growthos.intelligence.capability import (
    inspect_trusted_root,
    portfolio_snapshot,
    validate_trusted_root,
)
from growthos.intelligence.capability_deepening import deepen_capability
from growthos.intelligence.discovery import discovery_source_catalog
from growthos.services.capability_activation import (
    activate_capability,
    activation_state,
    confirm_capability,
    process_canon_events,
    reject_capability,
    run_capability_discovery,
)
from growthos.services.entity_resolution import (
    _candidate_dict,
    assess_source_effectiveness,
    candidate_funnel,
    enrich_candidate,
    reclassify_github_prospects,
    run_enrichment_pass,
)
from growthos.services.portfolio_census import census_report, run_full_census
from growthos.services.portfolio_deep_evidence import run_portfolio_deep_evidence_pass
from growthos.services.scout import (
    build_founder_brief,
    build_market_theses,
    compliance_status,
    create_capability,
    funnel_counts,
    get_control,
    list_capabilities,
    list_offers,
    requalify_cohort,
    requalify_prospect,
    review_capability,
    run_discovery,
    update_control,
)

router = APIRouter(prefix="/scout", tags=["scout"])


class CapabilityCreate(BaseModel):
    name: str
    definition: str
    category: str | None = None
    delivery_form: str | None = None
    typical_customer_problem: str | None = None
    deliverables: list[str] = []
    limitations: list[str] = []
    founder_review_note: str | None = None


class CapabilityReview(BaseModel):
    status: str
    note: str | None = None


class CapabilityConfirm(BaseModel):
    name: str
    definition: str
    maturity: str = "PROTOTYPE_PROVEN"
    limitations: list[str] = []
    external_summary: str = ""
    note: str | None = None


class CapabilityReject(BaseModel):
    reason: str


class RepositoryRootCreate(BaseModel):
    path: str
    label: str | None = None


class ScoutControlPatch(BaseModel):
    enabled: bool | None = None
    mode: str | None = None
    kill_switch: bool | None = None
    daily_research_budget: int | None = None
    daily_prospect_target: int | None = None
    daily_outreach_cap: int | None = None
    geographies: list[str] | None = None
    excluded_industries: list[str] | None = None
    approved_offers: list[str] | None = None
    allowed_campaign_ids: list[str] | None = None
    research_depth: str | None = None
    quiet_hours: dict[str, Any] | None = None
    min_revenue_score: float | None = None
    min_evidence_confidence: float | None = None
    explore_exploit: float | None = None
    explore_adjacent: float | None = None
    explore_experimental: float | None = None
    business_postal_address: str | None = None
    opt_out_email: str | None = None


def _serialize_control(c: ScoutControl) -> dict[str, Any]:
    return {
        "enabled": c.enabled,
        "mode": c.mode.value,
        "kill_switch": c.kill_switch,
        "daily_research_budget": c.daily_research_budget,
        "daily_prospect_target": c.daily_prospect_target,
        "daily_outreach_cap": c.daily_outreach_cap,
        "geographies": c.geographies,
        "excluded_industries": c.excluded_industries,
        "approved_offers": c.approved_offers,
        "allowed_campaign_ids": c.allowed_campaign_ids,
        "research_depth": c.research_depth,
        "quiet_hours": c.quiet_hours,
        "min_revenue_score": c.min_revenue_score,
        "min_evidence_confidence": c.min_evidence_confidence,
        "explore_exploit": c.explore_exploit,
        "explore_adjacent": c.explore_adjacent,
        "explore_experimental": c.explore_experimental,
        "business_postal_address": c.business_postal_address,
        "opt_out_email": c.opt_out_email,
    }


async def _prospect_with_score(
    session, prospect: Prospect
) -> dict[str, Any]:
    company = None
    person = None
    if prospect.company_id:
        company = (
            await session.execute(select(Company).where(Company.id == prospect.company_id))
        ).scalar_one_or_none()
    if prospect.person_id:
        person = (
            await session.execute(select(Person).where(Person.id == prospect.person_id))
        ).scalar_one_or_none()
    score = (
        await session.execute(
            select(ScoutProspectScore).where(ScoutProspectScore.prospect_id == prospect.id)
        )
    ).scalar_one_or_none()
    return {
        "id": prospect.id,
        "status": prospect.status,
        "source": prospect.source,
        "company": company.name if company else None,
        "company_id": prospect.company_id,
        "domain": company.domain if company else None,
        "website": company.website if company else None,
        "industry": company.industry if company else None,
        "location": company.location if company else None,
        "contact_email": person.email if person else None,
        "contact_name": person.full_name if person else None,
        "evidence": prospect.qualification.get("evidence"),
        "revenue_score": score.revenue_opportunity_score if score else None,
        "short_term_score": score.short_term_score if score else None,
        "strategic_score": score.strategic_value_score if score else None,
        "probability": score.probability if score else None,
        "confidence": score.confidence if score else None,
        "identity_confidence": score.identity_confidence if score else None,
        "problem_confidence": score.problem_confidence if score else None,
        "capability_fit_confidence": score.capability_fit_confidence if score else None,
        "buyer_confidence": score.buyer_confidence if score else None,
        "outreach_readiness_confidence": score.outreach_readiness_confidence if score else None,
        "confidence_reasoning": score.confidence_reasoning if score else {},
        "qualification": prospect.qualification,
        "expected_min": float(score.expected_value_min) if score and score.expected_value_min else None,
        "expected_max": float(score.expected_value_max) if score and score.expected_value_max else None,
        "recommended_motion": score.recommended_sales_motion if score else None,
        "recommended_next": score.recommended_next_action if score else None,
        "reasoning": score.reasoning if score else None,
        "created_at": prospect.created_at,
    }


def _serialize_capability(c: CapabilityCanon) -> dict[str, Any]:
    return {
        "id": c.id, "name": c.name, "definition": c.definition,
        "category": c.category, "delivery_form": c.delivery_form,
        "status": c.status.value if hasattr(c.status, "value") else str(c.status),
        "external_claimable": c.external_claimable,
        "proof_evidence": c.proof_evidence, "typical_customer_problem": c.typical_customer_problem,
        "deliverables": c.deliverables, "limitations": c.limitations,
        "price_range_hypothesis": c.price_range_hypothesis,
        "founder_review_note": c.founder_review_note,
        "maturity": c.maturity,
        "related_completed_work": c.related_completed_work,
        "source_evidence_ids": c.source_evidence_ids,
    }


def _serialize_offer(o: CommercialOffer) -> dict[str, Any]:
    return {
        "id": o.id, "name": o.name, "buyer": o.buyer, "problem": o.problem,
        "deliverable": o.deliverable, "included_capability_ids": o.included_capability_ids,
        "expected_outcome": o.expected_outcome, "delivery_model": o.delivery_model,
        "timeline_hypothesis": o.timeline_hypothesis, "price_hypothesis": o.price_hypothesis,
        "status": o.status.value if hasattr(o.status, "value") else str(o.status),
        "entry_offer": o.entry_offer, "premium_offer": o.premium_offer,
        "recurring_component": o.recurring_component, "scope_boundaries": o.scope_boundaries,
        "proof_required": o.proof_required, "exclusions": o.exclusions, "risks": o.risks,
    }


@router.get("/capability-intelligence/portfolio")
async def capability_portfolio(session: SessionDep, founder: FounderDep):
    return await portfolio_snapshot(session)


@router.get("/capability-intelligence/projects")
async def capability_projects(session: SessionDep, founder: FounderDep):
    rows = (await session.execute(select(ProjectEvidenceRecord).order_by(ProjectEvidenceRecord.inspected_at.desc()))).scalars().all()
    return {"projects": [{"id": p.id, "name": p.name, "path": p.path, "git_branch": p.git_branch, "git_status": p.git_status, "languages": p.languages, "manifests": p.manifests, "source_directories": p.source_directories, "test_summary": p.test_summary, "intelligence_profile": p.intelligence_profile} for p in rows]}


@router.get("/capability-intelligence/roots")
async def capability_roots(session: SessionDep, founder: FounderDep):
    rows = (await session.execute(select(TrustedRepositoryRoot).order_by(TrustedRepositoryRoot.created_at.desc()))).scalars().all()
    return {"roots": [{"id": r.id, "path": r.path, "label": r.label, "enabled": r.enabled} for r in rows]}


@router.post("/capability-intelligence/roots")
async def capability_root_create(session: SessionDep, founder: FounderDep, body: RepositoryRootCreate):
    from pathlib import Path
    path = Path(body.path)
    valid, detail = validate_trusted_root(path)
    if not valid:
        raise HTTPException(status_code=422, detail=detail)
    path = path.expanduser().resolve()
    row = (await session.execute(select(TrustedRepositoryRoot).where(TrustedRepositoryRoot.path == str(path)))).scalar_one_or_none()
    if row is None:
        row = TrustedRepositoryRoot(id=__import__('growthos.shared.ids', fromlist=['new_id']).new_id(), path=str(path), label=body.label)
        session.add(row)
        await session.flush()
    return {"root": {"id": row.id, "path": row.path, "label": row.label, "enabled": row.enabled}}


@router.post("/capability-intelligence/roots/{root_id}/inspect")
async def capability_root_inspect(root_id: str, session: SessionDep, founder: FounderDep):
    row = (await session.execute(select(TrustedRepositoryRoot).where(TrustedRepositoryRoot.id == root_id))).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Trusted repository root not found")
    report = await inspect_trusted_root(session, row)
    await session.commit()
    return {"report": report}


@router.get("/capabilities")
async def scout_capabilities(session: SessionDep, founder: FounderDep):
    return {"capabilities": [_serialize_capability(c) for c in await list_capabilities(session)]}


@router.post("/capabilities")
async def scout_capability_create(
    session: SessionDep, founder: FounderDep, body: CapabilityCreate
):
    try:
        capability = await create_capability(
            session, name=body.name, definition=body.definition,
            category=body.category, delivery_form=body.delivery_form,
            typical_customer_problem=body.typical_customer_problem,
            deliverables=body.deliverables, limitations=body.limitations,
            founder_review_note=body.founder_review_note,
        )
        await session.commit()
        return {"capability": _serialize_capability(capability)}
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/capabilities/{capability_id}/deepen")
async def scout_capability_deepen(capability_id: str, session: SessionDep, founder: FounderDep):
    capability = (await session.execute(select(CapabilityCanon).where(CapabilityCanon.id == capability_id))).scalar_one_or_none()
    if capability is None:
        raise HTTPException(status_code=404, detail="Capability not found")
    try:
        report = await deepen_capability(session, capability)
        await session.commit()
        return {"report": report}
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.patch("/capabilities/{capability_id}")
async def scout_capability_review(
    capability_id: str, session: SessionDep, founder: FounderDep, body: CapabilityReview
):
    capability = (await session.execute(select(CapabilityCanon).where(CapabilityCanon.id == capability_id))).scalar_one_or_none()
    if capability is None:
        raise HTTPException(status_code=404, detail="Capability not found")
    try:
        await review_capability(session, capability, status=body.status, note=body.note)
        await session.commit()
        return {"capability": _serialize_capability(capability)}
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/capabilities/{capability_id}/confirm")
async def scout_capability_confirm(
    capability_id: str, session: SessionDep, founder: FounderDep, body: CapabilityConfirm
):
    capability = (await session.execute(select(CapabilityCanon).where(CapabilityCanon.id == capability_id))).scalar_one_or_none()
    if capability is None:
        raise HTTPException(status_code=404, detail="Capability not found")
    try:
        await confirm_capability(
            session, capability,
            name=body.name, definition=body.definition, maturity=body.maturity,
            limitations=body.limitations, external_summary=body.external_summary,
            note=body.note, actor="founder",
        )
        await session.commit()
        return {"capability": _serialize_capability(capability)}
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/capabilities/{capability_id}/reject")
async def scout_capability_reject(
    capability_id: str, session: SessionDep, founder: FounderDep, body: CapabilityReject
):
    capability = (await session.execute(select(CapabilityCanon).where(CapabilityCanon.id == capability_id))).scalar_one_or_none()
    if capability is None:
        raise HTTPException(status_code=404, detail="Capability not found")
    try:
        await reject_capability(session, capability, reason=body.reason, actor="founder")
        await session.commit()
        return {"capability": _serialize_capability(capability)}
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/capabilities/{capability_id}/activate")
async def scout_capability_activate(capability_id: str, session: SessionDep, founder: FounderDep):
    capability = (await session.execute(select(CapabilityCanon).where(CapabilityCanon.id == capability_id))).scalar_one_or_none()
    if capability is None:
        raise HTTPException(status_code=404, detail="Capability not found")
    try:
        report = await activate_capability(session, capability, actor="founder")
        await session.commit()
        return {"report": report}
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/capabilities/{capability_id}/activation")
async def scout_capability_activation_state(capability_id: str, session: SessionDep, founder: FounderDep):
    capability = (await session.execute(select(CapabilityCanon).where(CapabilityCanon.id == capability_id))).scalar_one_or_none()
    if capability is None:
        raise HTTPException(status_code=404, detail="Capability not found")
    state = await activation_state(session, capability)
    await session.flush()
    return state


@router.post("/capabilities/{capability_id}/discover")
async def scout_capability_discover(
    capability_id: str, session: SessionDep, founder: FounderDep, limit: int = 15
):
    capability = (await session.execute(select(CapabilityCanon).where(CapabilityCanon.id == capability_id))).scalar_one_or_none()
    if capability is None:
        raise HTTPException(status_code=404, detail="Capability not found")
    try:
        report = await run_capability_discovery(session, capability, limit=limit, actor="scout")
        await session.commit()
        return {"report": report}
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/canon-events/process")
async def scout_canon_events_process(session: SessionDep, founder: FounderDep):
    report = await process_canon_events(session)
    await session.commit()
    return report


@router.get("/offers")
async def scout_offers(session: SessionDep, founder: FounderDep):
    return {"offers": [_serialize_offer(o) for o in await list_offers(session)]}


@router.post("/requalify")
async def scout_requalify(session: SessionDep, founder: FounderDep, limit: int | None = None):
    report = await requalify_cohort(session, limit=limit, actor="founder")
    await session.commit()
    return {"report": report}


@router.post("/prospects/{prospect_id}/requalify")
async def scout_requalify_one(prospect_id: str, session: SessionDep, founder: FounderDep):
    prospect = (await session.execute(select(Prospect).where(Prospect.id == prospect_id))).scalar_one_or_none()
    if prospect is None:
        raise HTTPException(status_code=404, detail="Prospect not found")
    report = await requalify_prospect(session, prospect, actor="founder")
    await session.commit()
    return {"report": report, "prospect": await _prospect_with_score(session, prospect)}


@router.get("/overview")
async def scout_overview(session: SessionDep, founder: FounderDep):
    control = await get_control(session)
    funnel = await funnel_counts(session)
    compliance = await compliance_status(session)
    brief = await build_founder_brief(session)
    return {
        "control": _serialize_control(control),
        "funnel": funnel,
        "compliance": compliance,
        "brief": brief,
    }


@router.get("/sources")
async def scout_sources(session: SessionDep, founder: FounderDep):
    return {"sources": discovery_source_catalog()}


@router.get("/markets")
async def scout_markets(session: SessionDep, founder: FounderDep):
    await build_market_theses(session)
    await session.flush()
    result = await session.execute(
        select(MarketOpportunityThesis).order_by(MarketOpportunityThesis.score.desc())
    )
    theses = result.scalars().all()
    return {
        "markets": [
            {
                "id": t.id,
                "market": t.market,
                "buyer": t.buyer,
                "problem": t.problem,
                "solution": t.solution,
                "commercial_model": t.commercial_model,
                "expected_deal_min": float(t.expected_deal_min) if t.expected_deal_min else None,
                "expected_deal_max": float(t.expected_deal_max) if t.expected_deal_max else None,
                "sales_cycle": t.sales_cycle_hypothesis,
                "margin": t.margin_hypothesis,
                "score": t.score,
                "confidence": t.confidence,
                "status": t.status.value,
                "evidence_summary": t.evidence_summary,
            }
            for t in theses
        ]
    }


@router.get("/prospects")
async def scout_prospects(session: SessionDep, founder: FounderDep, limit: int = 100):
    result = await session.execute(
        select(Prospect)
        .order_by(Prospect.created_at.desc())
        .limit(limit)
    )
    prospects = result.scalars().all()
    items = []
    for p in prospects:
        items.append(await _prospect_with_score(session, p))
    return {"prospects": items}


@router.get("/controls")
async def scout_controls(session: SessionDep, founder: FounderDep):
    control = await get_control(session)
    await session.flush()
    return {"control": _serialize_control(control)}


@router.patch("/controls")
async def scout_controls_update(
    session: SessionDep, founder: FounderDep, body: ScoutControlPatch
):
    patch = {k: v for k, v in body.model_dump().items() if v is not None}
    control = await update_control(session, patch)
    await session.commit()
    return {"control": _serialize_control(control)}


@router.post("/run")
async def scout_run(session: SessionDep, founder: FounderDep, limit: int = 20):
    report = await run_discovery(session, limit=limit, run_type="manual")
    await session.commit()
    return {"report": report}


@router.get("/brief")
async def scout_brief(session: SessionDep, founder: FounderDep):
    brief = await build_founder_brief(session)
    return {"brief": brief}


# ---------------------------------------------------------------------------
# Discovery Candidates (pre-prospect layer)
# ---------------------------------------------------------------------------


@router.post("/candidates/reclassify")
async def scout_candidates_reclassify(session: SessionDep, founder: FounderDep):
    report = await reclassify_github_prospects(session)
    await session.commit()
    return {"report": report}


@router.post("/candidates/enrich")
async def scout_candidates_enrich(session: SessionDep, founder: FounderDep, market: str | None = None):
    report = await run_enrichment_pass(session, market=market)
    await session.commit()
    return {"report": report}


@router.get("/candidates")
async def scout_candidates(session: SessionDep, founder: FounderDep):
    rows = (
        await session.execute(
            select(DiscoveryCandidate).order_by(DiscoveryCandidate.discovery_priority_score.desc())
        )
    ).scalars().all()
    return {
        "candidates": [_candidate_dict(c) for c in rows],
        "funnel": await candidate_funnel(session),
    }


@router.get("/candidates/{candidate_id}")
async def scout_candidate_detail(candidate_id: str, session: SessionDep, founder: FounderDep):
    candidate = (
        await session.execute(select(DiscoveryCandidate).where(DiscoveryCandidate.id == candidate_id))
    ).scalar_one_or_none()
    if candidate is None:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return {"candidate": _candidate_dict(candidate)}


@router.post("/candidates/{candidate_id}/enrich")
async def scout_candidate_enrich(candidate_id: str, session: SessionDep, founder: FounderDep):
    candidate = (
        await session.execute(select(DiscoveryCandidate).where(DiscoveryCandidate.id == candidate_id))
    ).scalar_one_or_none()
    if candidate is None:
        raise HTTPException(status_code=404, detail="Candidate not found")
    report = await enrich_candidate(session, candidate)
    await session.commit()
    return {"candidate": report}


@router.get("/source-effectiveness")
async def scout_source_effectiveness(
    session: SessionDep, founder: FounderDep, source: str = "github", market: str | None = None
):
    row = await assess_source_effectiveness(session, source, market=market)
    await session.flush()
    return {
        "source_effectiveness": {
            "source": row.source,
            "market": row.market,
            "candidates_found": row.candidates_found,
            "verified_commercial_entities": row.verified_commercial_entities,
            "problem_signals": row.problem_signals,
            "capability_matches": row.capability_matches,
            "verified_contacts": row.verified_contacts,
            "sales_qualified": row.sales_qualified,
            "promoted_to_prospect": row.promoted_to_prospect,
            "verified_entity_rate": row.verified_entity_rate,
            "false_positive_rate": row.false_positive_rate,
            "problem_signal_rate": row.problem_signal_rate,
            "recommendation": row.recommendation,
            "notes": row.notes,
        }
    }


# ---------------------------------------------------------------------------
# GitHub Portfolio Evidence Census
# ---------------------------------------------------------------------------


@router.get("/portfolio-census")
async def scout_portfolio_census(session: SessionDep, founder: FounderDep):
    return await census_report(session)


@router.post("/portfolio-census/run")
async def scout_portfolio_census_run(session: SessionDep, founder: FounderDep):
    report = await run_full_census(session)
    await session.commit()
    return {"report": report}


# ---------------------------------------------------------------------------
# Portfolio Deep Evidence
# ---------------------------------------------------------------------------


@router.post("/portfolio-deep-evidence/run")
async def scout_portfolio_deep_evidence_run(session: SessionDep, founder: FounderDep):
    """Run deep evidence analysis on the 8 selected repositories.

    Fetches actual file contents from GitHub, performs lightweight code
    analysis, reassesses proposals, and produces a founder review report.
    No capability is auto-confirmed.
    """
    report = await run_portfolio_deep_evidence_pass(session)
    await session.commit()
    return {"report": report}


@router.get("/portfolio-deep-evidence")
async def scout_portfolio_deep_evidence_report(session: SessionDep, founder: FounderDep):
    """Get the current deep evidence status and founder review report."""
    from sqlalchemy import func
    # Just return existing evidence counts (no re-run)
    evidence_count = (
        await session.execute(
            select(func.count()).select_from(CapabilityEvidenceRecord).where(
                CapabilityEvidenceRecord.source_type == "github_deep_evidence"
            )
        )
    ).scalar() or 0
    proposed = (
        await session.execute(
            select(CapabilityCanon).where(
                CapabilityCanon.entered_from == "portfolio_deep_evidence"
            )
        )
    ).scalars().all()
    return {
        "evidence_records": evidence_count,
        "proposals": [
            {
                "name": c.name,
                "status": str(c.status),
                "founder_review_note": c.founder_review_note,
                "maturity": c.maturity,
            }
            for c in proposed
        ],
    }


# Evidence Mirror — local deep analysis
# ---------------------------------------------------------------------------


@router.post("/mirror/run")
async def mirror_run(session: SessionDep, founder: FounderDep):
    """Run local deep analysis on all selected repositories via evidence mirrors."""
    from growthos.services.evidence_mirror_service import run_full_local_deep_pass
    report = await run_full_local_deep_pass(session)
    await session.commit()
    return {"report": report}


@router.get("/mirror/status")
async def mirror_status(session: SessionDep, founder: FounderDep):
    """Show mirror status for all repositories."""
    from growthos.domain.models_capability import EvidenceMirror
    mirrors = list((await session.execute(select(EvidenceMirror))).scalars().all())
    return {
        "mirrors": [
            {
                "full_name": m.full_name,
                "state": m.mirror_state,
                "branch": m.default_branch,
                "sha": m.remote_commit_sha,
                "files_discovered": m.files_discovered,
                "last_analysis": str(m.last_deep_analysis_at) if m.last_deep_analysis_at else None,
                "error": m.error,
            }
            for m in mirrors
        ]
    }


@router.post("/mirror/rebuild")
async def mirror_rebuild(session: SessionDep, founder: FounderDep):
    """Rebuild capability recommendations from local evidence."""
    from growthos.services.evidence_mirror_service import rebuild_capability_recommendations
    result = await rebuild_capability_recommendations(session)
    await session.commit()
    return result
