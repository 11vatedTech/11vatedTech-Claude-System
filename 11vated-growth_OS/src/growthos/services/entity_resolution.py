"""Commercial Entity Resolution + Buyer Qualification.

Separates the pre-prospect layer (``DiscoveryCandidate``) from the commercial
pipeline (``Prospect``). A public technical signal — for example a GitHub
owner/project — is NOT automatically a buyer, a studio, or a reachable
decision-maker. Candidates pass through explicit, evidence-gated stages before
(and only if) they are promoted into the prospect funnel.

Guarantees held here:

- GitHub is a TECHNICAL_DISCOVERY_SOURCE, not a COMMERCIAL_IDENTITY_AUTHORITY.
- ``Organization account`` never implies ``commercial company``.
- ``active repository`` never implies ``buyer``.
- ``uses sprites`` never implies ``needs us``.
- confidence dimensions are independent (identity vs commercial vs market fit
  vs buyer potential).
- Discovery Priority Score (who deserves research) is separate from Revenue
  Opportunity Score (only computed after commercial qualification).
- no outreach is ever sent from this module.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

import growthos.domain.models  # noqa: F401  (registers all tables incl. FK targets)
from growthos.domain.enums import (
    ActivityStatus,
    CapabilityStatus,
    CommercialEntityStatus,
    DiscoveryCandidateState,
    EntityTrack,
    NeedEvidenceClass,
    OrganizationType,
    PurchasingCapacity,
    ScoutProspectState,
)
from growthos.domain.models_commercial import Prospect
from growthos.domain.models_identity import Company
from growthos.domain.models_scout import (
    CapabilityCanon,
    DiscoveryCandidate,
    DiscoveryCandidateEvent,
    MarketOpportunityThesis,
    SourceEffectiveness,
)
from growthos.domain.models_system import AuditEvent
from growthos.shared.ids import new_id

GITHUB_USER_ENDPOINT = "https://api.github.com/users/{login}"
GITHUB_ORG_ENDPOINT = "https://api.github.com/orgs/{login}"

# Topics that indicate technical relevance to the confirmed sprite-runtime
# capability. Relevance is NOT need; it only informs market-fit confidence.
_SPRITE_RELEVANT_TOPICS = {
    "2d", "2d-game", "sprite", "sprites", "pixel-art", "pixelart", "game",
    "game-development", "gamedev", "godot", "unity", "unreal", "pygame",
    "love2d", "monogame", "cocos2d", "rpg", "character", "animation",
    "game-engine", "indie-game", "mobile-game",
}

# Explicit language signals in an owner bio/description that indicate a real
# need to be researched (never a need claim by themselves).
_NEED_SIGNAL_TERMS = {
    "hiring": "open_engineering_roles",
    "looking for": "request_for_collaborators",
    "seeking": "request_for_collaborators",
    "work in progress": "prototype_stage",
    "wip": "prototype_stage",
    "prototype": "prototype_stage",
    "roadmap": "public_roadmap",
    "collaborator": "request_for_collaborators",
    "contributors welcome": "request_for_collaborators",
}

_SIX_MONTHS = timedelta(days=180)


def _now() -> datetime:
    return datetime.now(UTC)


# ---------------------------------------------------------------------------
# Identity keys + helpers
# ---------------------------------------------------------------------------


def candidate_identity_key(source: str, external_ids: dict[str, Any]) -> str:
    """Deterministic cross-run identity key for a candidate."""
    if source == "github":
        owner = external_ids.get("github_owner") or external_ids.get("login")
        if owner:
            return f"github:{owner}"
    # Fallback: hash the stable identity fields.
    import hashlib

    canonical = json_dumps(external_ids, sort_keys=True)
    return f"{source}:{hashlib.sha256(canonical.encode()).hexdigest()[:24]}"


def json_dumps(value: Any, **kwargs: Any) -> str:
    import json

    return json.dumps(value, default=str, **kwargs)


def _clamp(value: float) -> float:
    return round(max(0.0, min(1.0, value)), 3)


# ---------------------------------------------------------------------------
# Reclassification: prospect -> discovery candidate
# ---------------------------------------------------------------------------


async def reclassify_github_prospects(session: AsyncSession) -> dict[str, Any]:
    """Reclassify the GitHub-derived Prospects into DiscoveryCandidate rows.

    Evidence and provenance are preserved. The Prospect row is NOT deleted; its
    status becomes ``RECLASSIFIED_AS_CANDIDATE`` so the commercial funnel stops
    counting it, and a ``legacy_prospect_id`` back-link remains for provenance.
    """
    rows = (
        await session.execute(
            select(Prospect)
            .where(
                Prospect.source == "github",
                Prospect.status != ScoutProspectState.RECLASSIFIED_AS_CANDIDATE.value,
            )
            .order_by(Prospect.created_at)
        )
    ).scalars().all()

    created = 0
    skipped = 0
    candidates: list[DiscoveryCandidate] = []
    for prospect in rows:
        company = (
            await session.execute(select(Company).where(Company.id == prospect.company_id))
        ).scalar_one_or_none() if prospect.company_id else None
        external_ids = (company.external_ids if company else None) or {}
        identity_key = candidate_identity_key("github", external_ids)

        existing = (
            await session.execute(
                select(DiscoveryCandidate).where(
                    DiscoveryCandidate.source == "github",
                    DiscoveryCandidate.source_identity_key == identity_key,
                )
            )
        ).scalar_one_or_none()
        if existing is not None:
            if existing.legacy_prospect_id is None:
                existing.legacy_prospect_id = prospect.id
            candidates.append(existing)
            skipped += 1
            _mark_reclassified(session, prospect)
            continue

        repos = external_ids.get("repos") or []
        topics = external_ids.get("topics") or []
        languages = external_ids.get("languages") or []
        source_url = external_ids.get("github_owner_url") or (
            prospect.qualification or {}
        ).get("source_url")

        candidate = DiscoveryCandidate(
            id=new_id(),
            source="github",
            source_identity_key=identity_key,
            source_evidence_id=prospect.source_evidence_id,
            legacy_prospect_id=prospect.id,
            canonical_name=(company.name if company else external_ids.get("github_owner") or "unknown"),
            state=DiscoveryCandidateState.IDENTITY_RESOLUTION,
            entity_type=OrganizationType.UNKNOWN,
            commercial_status=CommercialEntityStatus.COMMERCIAL_UNVERIFIED,
            activity_status=ActivityStatus.UNKNOWN,
            need_evidence_class=NeedEvidenceClass.NO_NEED_EVIDENCE,
            purchasing_capacity=PurchasingCapacity.UNKNOWN,
            track=EntityTrack.NOT_COMMERCIAL,
            identity_confidence=0.6,  # real public GitHub account from discovery
            commercial_entity_confidence=0.0,
            market_fit_confidence=_topic_market_fit(topics),
            buyer_potential_confidence=0.0,
            discovery_priority_score=0.0,
            products_projects=[
                {
                    "kind": "repository",
                    "name": r.get("full_name"),
                    "url": r.get("html_url"),
                    "description": r.get("description"),
                    "language": r.get("language"),
                    "topics": r.get("topics"),
                    "stars": r.get("stars"),
                }
                for r in repos
            ],
            public_source_refs=[
                {"kind": "github_owner", "url": source_url},
                *[
                    {"kind": "github_repository", "url": r.get("html_url")}
                    for r in repos
                ],
            ],
            external_ids=external_ids,
            enrichment={
                "topics": topics,
                "languages": languages,
                "owner_type": external_ids.get("github_owner_type"),
            },
            qualification_outcome="NOT_YET_A_PROSPECT",
        )
        session.add(candidate)
        candidates.append(candidate)
        created += 1
        _mark_reclassified(session, prospect)

    await session.flush()
    return {
        "reclassified": created,
        "already_candidates": skipped,
        "total_github_prospects": len(rows),
        "candidate_ids": [c.id for c in candidates],
    }


def _mark_reclassified(session: AsyncSession, prospect: Prospect) -> None:
    """Move a GitHub prospect out of the commercial funnel, preserving audit."""
    if prospect.status == ScoutProspectState.RECLASSIFIED_AS_CANDIDATE.value:
        return
    previous = prospect.status
    prospect.status = ScoutProspectState.RECLASSIFIED_AS_CANDIDATE.value
    session.add(
        AuditEvent(
            actor="scout",
            action="prospect:reclassified_as_candidate",
            entity_type="prospect",
            entity_id=prospect.id,
            previous_state={"status": previous},
            new_state={"status": prospect.status},
            reason=(
                "GitHub is a technical discovery source, not a commercial "
                "identity authority; reclassified into the pre-prospect layer."
            ),
            context={"source": prospect.source},
        )
    )


# ---------------------------------------------------------------------------
# Confidence helpers (independent dimensions)
# ---------------------------------------------------------------------------


def _topic_market_fit(topics: list[str]) -> float:
    if not topics:
        return 0.0
    hit = len(set(t.lower() for t in topics) & _SPRITE_RELEVANT_TOPICS)
    if hit >= 3:
        return 0.8
    if hit == 2:
        return 0.6
    if hit == 1:
        return 0.4
    return 0.2


def _resolve_entity_type(
    owner_type: str | None, profile: dict[str, Any], repo_count: int
) -> tuple[OrganizationType, float]:
    """Most-defensible entity type from GitHub metadata alone (conservative).

    GitHub account type never implies a commercial company. We only ever assert
    a commercial entity type when corroborating self-reported signals (website
    and/or company field) also exist — and even then confidence is capped.
    """
    website = (profile.get("blog") or "").strip()
    company_field = (profile.get("company") or "").strip()
    bio = (profile.get("bio") or "").strip()
    name = (profile.get("name") or "").strip()

    is_org = owner_type == "Organization"

    if is_org and website and (company_field or bio):
        return OrganizationType.COMMERCIAL_COMPANY, 0.6
    if is_org and website:
        return OrganizationType.OPEN_SOURCE_ORGANIZATION, 0.5
    if is_org and company_field:
        return OrganizationType.COMMERCIAL_COMPANY, 0.45
    if is_org:
        return OrganizationType.OPEN_SOURCE_ORGANIZATION, 0.35

    # Individual (User) account.
    if company_field and website:
        return OrganizationType.INDEPENDENT_DEVELOPER, 0.55
    if company_field:
        return OrganizationType.INDEPENDENT_DEVELOPER, 0.45
    if name and (website or bio) and repo_count >= 3:
        return OrganizationType.INDIVIDUAL, 0.5
    if repo_count <= 2:
        return OrganizationType.HOBBY_PROJECT, 0.5
    return OrganizationType.INDIVIDUAL, 0.4


def _resolve_commercial_status(
    entity_type: OrganizationType, profile: dict[str, Any]
) -> tuple[CommercialEntityStatus, float]:
    """Commercial-actor gate.

    GitHub self-reported fields are NOT independent corroboration, so a
    commercial entity type maps to COMMERCIAL_UNVERIFIED (not VERIFIED) until a
    separate public source confirms a real commercial operation.
    """
    if entity_type in {
        OrganizationType.COMMERCIAL_COMPANY,
        OrganizationType.GAME_STUDIO,
        OrganizationType.AGENCY,
    }:
        return CommercialEntityStatus.COMMERCIAL_UNVERIFIED, 0.5
    if entity_type in {
        OrganizationType.INDIVIDUAL,
        OrganizationType.HOBBY_PROJECT,
        OrganizationType.COMMUNITY_PROJECT,
        OrganizationType.EDUCATIONAL_PROJECT,
    }:
        return CommercialEntityStatus.NON_COMMERCIAL, 0.7
    if entity_type in {
        OrganizationType.INDEPENDENT_DEVELOPER,
        OrganizationType.OPEN_SOURCE_ORGANIZATION,
    }:
        return CommercialEntityStatus.COMMERCIAL_UNVERIFIED, 0.35
    return CommercialEntityStatus.COMMERCIAL_UNVERIFIED, 0.2


def _resolve_activity(profile: dict[str, Any]) -> tuple[ActivityStatus, float]:
    """Activity from the owner profile's ``updated_at`` (recent public change)."""
    updated = profile.get("updated_at")
    if not updated:
        return ActivityStatus.UNKNOWN, 0.0
    try:
        dt = datetime.fromisoformat(str(updated).replace("Z", "+00:00"))
    except ValueError:
        return ActivityStatus.UNKNOWN, 0.0
    age = _now() - dt.astimezone(UTC)
    if age <= timedelta(days=30):
        return ActivityStatus.ACTIVE, 0.7
    if age <= timedelta(days=180):
        return ActivityStatus.LIKELY_ACTIVE, 0.6
    if age <= timedelta(days=365):
        return ActivityStatus.STALE, 0.5
    return ActivityStatus.LIKELY_INACTIVE, 0.5


def _resolve_need(
    profile: dict[str, Any], topics: list[str]
) -> tuple[NeedEvidenceClass, str | None]:
    """Need evidence from explicit public signals only.

    Topic overlap is relevance, never need. Only explicit language (hiring,
    seeking collaborators, prototype/roadmap/WIP) is recorded — and even then
    only as INDIRECT_NEED_SIGNAL, which does not advance the capability gate.
    """
    bio = (profile.get("bio") or "") + " " + (profile.get("description") or "")
    lowered = bio.lower()
    hits = [term for term in _NEED_SIGNAL_TERMS if term in lowered]
    if hits:
        return NeedEvidenceClass.INDIRECT_NEED_SIGNAL, (
            "Explicit public signals: " + ", ".join(sorted(set(_NEED_SIGNAL_TERMS[t] for t in hits)))
        )
    # Technical relevance is NOT a need.
    if _topic_market_fit(topics) >= 0.4:
        return NeedEvidenceClass.GENERAL_RELEVANCE, (
            "Repositories are technically relevant to the sprite-runtime "
            "capability, but no public need signal exists."
        )
    return NeedEvidenceClass.NO_NEED_EVIDENCE, "No public need evidence."


def _resolve_capacity(
    entity_type: OrganizationType, profile: dict[str, Any]
) -> PurchasingCapacity:
    website = (profile.get("blog") or "").strip()
    company_field = (profile.get("company") or "").strip()
    if entity_type in {OrganizationType.COMMERCIAL_COMPANY, OrganizationType.GAME_STUDIO, OrganizationType.AGENCY}:
        if website and company_field:
            return PurchasingCapacity.LOW  # signals exist; scale unknown
        return PurchasingCapacity.UNKNOWN
    if entity_type == OrganizationType.INDEPENDENT_DEVELOPER and website:
        return PurchasingCapacity.LOW
    return PurchasingCapacity.UNKNOWN


def _resolve_track(entity_type: OrganizationType, commercial_status: CommercialEntityStatus) -> EntityTrack:
    if commercial_status == CommercialEntityStatus.NON_COMMERCIAL:
        if entity_type == OrganizationType.OPEN_SOURCE_ORGANIZATION:
            return EntityTrack.ECOSYSTEM_TRACK
        return EntityTrack.NOT_COMMERCIAL
    return EntityTrack.PARTNER_TRACK  # not a client until promotion


def compute_discovery_priority(candidate: DiscoveryCandidate) -> float:
    """Discovery Priority Score: who deserves further research.

    Deliberately independent from revenue scoring. It ranks candidates for
    enrichment effort, not as sales opportunities.
    """
    website_signal = 0.1 if candidate.official_website else 0.0
    score = (
        0.30 * float(candidate.identity_confidence or 0.0)
        + 0.25 * float(candidate.market_fit_confidence or 0.0)
        + 0.25 * float(candidate.commercial_entity_confidence or 0.0)
        + 0.10 * float(candidate.buyer_potential_confidence or 0.0)
        + website_signal
    )
    return _clamp(score)


# ---------------------------------------------------------------------------
# Enrichment
# ---------------------------------------------------------------------------


async def fetch_github_profile(
    login: str, owner_type: str | None, *, client: httpx.AsyncClient | None = None
) -> dict[str, Any]:
    """Fetch public GitHub owner metadata via the official REST API.

    Returns {} on any failure (rate limit, 404, network) — unknown stays
    unknown; we never fabricate missing attributes.
    """
    endpoint = (
        GITHUB_ORG_ENDPOINT if owner_type == "Organization" else GITHUB_USER_ENDPOINT
    )
    url = endpoint.format(login=login)
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "GrowthOS-RevenueScout/0.1 (public research)",
    }
    owned_client: httpx.AsyncClient | None = None
    active_client = client
    if active_client is None:
        owned_client = httpx.AsyncClient(timeout=20, headers=headers)
        active_client = owned_client
    try:
        resp = await active_client.get(url)
        if resp.status_code != 200:
            return {}
        return resp.json()
    except (httpx.HTTPError, ValueError):
        return {}
    finally:
        if owned_client is not None:
            await owned_client.aclose()


async def enrich_candidate(
    session: AsyncSession,
    candidate: DiscoveryCandidate,
    *,
    profile: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Resolve a candidate's commercial identity honestly from public metadata."""
    previous_state = candidate.state
    external_ids = candidate.external_ids or {}
    login = external_ids.get("github_owner") or candidate.canonical_name
    owner_type = external_ids.get("github_owner_type")

    if profile is None and candidate.source == "github":
        profile = await fetch_github_profile(login, owner_type)
    profile = profile or {}

    # Persist what we actually learned.
    blog = (profile.get("blog") or "").strip()
    if blog and not blog.startswith(("http://", "https://")):
        blog = f"https://{blog}"
    candidate.official_website = blog or None
    candidate.country_region = (profile.get("location") or "").strip() or None
    candidate.enrichment = {
        **(candidate.enrichment or {}),
        "github_name": profile.get("name"),
        "github_company": profile.get("company"),
        "github_bio": profile.get("bio"),
        "github_public_email": profile.get("email"),
        "github_public_repos": profile.get("public_repos"),
        "github_followers": profile.get("followers"),
        "github_updated_at": profile.get("updated_at"),
        "profile_retrieved": bool(profile),
    }

    topics = external_ids.get("topics") or []
    repo_count = len(external_ids.get("repos") or []) or int(profile.get("public_repos") or 0)

    # Independent confidence dimensions (never collapsed).
    if profile:
        candidate.identity_confidence = max(candidate.identity_confidence, 0.95)
    else:
        candidate.identity_confidence = max(candidate.identity_confidence, 0.6)

    entity_type, entity_confidence = _resolve_entity_type(owner_type, profile, repo_count)
    commercial_status, commercial_confidence = _resolve_commercial_status(entity_type, profile)
    activity_status, _activity_confidence = _resolve_activity(profile)
    need_class, need_reason = _resolve_need(profile, topics)

    candidate.entity_type = entity_type
    candidate.commercial_status = commercial_status
    candidate.activity_status = activity_status
    candidate.need_evidence_class = need_class
    candidate.purchasing_capacity = _resolve_capacity(entity_type, profile)
    candidate.track = _resolve_track(entity_type, commercial_status)
    candidate.market_fit_confidence = _topic_market_fit(topics)
    candidate.commercial_entity_confidence = _clamp(commercial_confidence)
    candidate.buyer_potential_confidence = 0.0  # no buyer evidence from GitHub
    candidate.problem_evidence = need_reason
    candidate.last_verified_at = _now()
    candidate.discovery_priority_score = compute_discovery_priority(candidate)

    # Decision-maker and contact evidence: none is inventable from GitHub.
    candidate.decision_maker_evidence = []
    contact_paths: list[dict[str, Any]] = []
    if blog:
        contact_paths.append(
            {
                "class": "VERIFIED_PUBLIC_BUSINESS_CHANNEL",
                "value": blog,
                "source": "github_owner_profile",
                "note": "Self-reported website; contact route requires further verification.",
            }
        )
    candidate.contact_paths = contact_paths

    # State + outcome.
    if commercial_status == CommercialEntityStatus.NON_COMMERCIAL:
        candidate.state = DiscoveryCandidateState.NOT_COMMERCIAL
        candidate.qualification_outcome = "NOT_COMMERCIAL"
    elif entity_type == OrganizationType.UNKNOWN:
        candidate.state = DiscoveryCandidateState.IDENTITY_RESOLUTION
        candidate.qualification_outcome = "IDENTITY_UNRESOLVED"
    else:
        candidate.state = DiscoveryCandidateState.COMMERCIAL_STATUS_CHECK
        candidate.qualification_outcome = "COMMERCIAL_UNVERIFIED"

    await _record_candidate_event(
        session, candidate,
        from_state=previous_state,
        to_state=candidate.state,
        reason=f"Entity resolved as {entity_type.value}; commercial status {commercial_status.value}; {need_reason or 'no need evidence'}",
    )
    await session.flush()
    return _candidate_dict(candidate)


async def _record_candidate_event(
    session: AsyncSession,
    candidate: DiscoveryCandidate,
    *,
    to_state: DiscoveryCandidateState,
    reason: str,
    from_state: DiscoveryCandidateState | None = None,
) -> None:
    from_state = from_state or candidate.state
    session.add(
        DiscoveryCandidateEvent(
            id=new_id(),
            candidate_id=candidate.id,
            from_state=from_state,
            to_state=to_state,
            actor="scout",
            reason=reason,
            occurred_at=_now(),
            source_evidence_id=candidate.source_evidence_id,
        )
    )


def _candidate_dict(candidate: DiscoveryCandidate) -> dict[str, Any]:
    return {
        "id": candidate.id,
        "canonical_name": candidate.canonical_name,
        "source": candidate.source,
        "state": candidate.state.value,
        "entity_type": candidate.entity_type.value,
        "commercial_status": candidate.commercial_status.value,
        "activity_status": candidate.activity_status.value,
        "need_evidence_class": candidate.need_evidence_class.value,
        "purchasing_capacity": candidate.purchasing_capacity.value,
        "track": candidate.track.value,
        "official_website": candidate.official_website,
        "country_region": candidate.country_region,
        "identity_confidence": candidate.identity_confidence,
        "commercial_entity_confidence": candidate.commercial_entity_confidence,
        "market_fit_confidence": candidate.market_fit_confidence,
        "buyer_potential_confidence": candidate.buyer_potential_confidence,
        "discovery_priority_score": candidate.discovery_priority_score,
        "problem_evidence": candidate.problem_evidence,
        "contact_paths": candidate.contact_paths,
        "decision_maker_evidence": candidate.decision_maker_evidence,
        "qualification_outcome": candidate.qualification_outcome,
        "legacy_prospect_id": candidate.legacy_prospect_id,
        "prospect_id": candidate.prospect_id,
    }


# ---------------------------------------------------------------------------
# Promotion gate
# ---------------------------------------------------------------------------


def _capability_fits(candidate: DiscoveryCandidate, capability: CapabilityCanon) -> bool:
    """Match only the confirmed capability and its actual limitations."""
    if candidate.need_evidence_class not in {
        NeedEvidenceClass.DIRECT_NEED_SIGNAL,
        NeedEvidenceClass.STRONG_TECHNICAL_SIGNAL,
        NeedEvidenceClass.INDIRECT_NEED_SIGNAL,
    }:
        return False
    topics = {t.lower() for t in (candidate.enrichment or {}).get("topics", [])}
    if not (topics & _SPRITE_RELEVANT_TOPICS):
        return False
    return capability.status in {
        CapabilityStatus.FOUNDER_CONFIRMED,
        CapabilityStatus.EVIDENCE_VERIFIED,
    } and capability.external_claimable


async def _confirmed_capability(session: AsyncSession) -> CapabilityCanon | None:
    return (
        await session.execute(
            select(CapabilityCanon)
            .where(
                CapabilityCanon.status.in_([
                    CapabilityStatus.FOUNDER_CONFIRMED,
                    CapabilityStatus.EVIDENCE_VERIFIED,
                ]),
                CapabilityCanon.external_claimable.is_(True),
            )
            .order_by(CapabilityCanon.created_at)
        )
    ).scalars().first()


async def _reject_candidate(
    session: AsyncSession, candidate: DiscoveryCandidate, reason: str
) -> dict[str, Any]:
    candidate.state = DiscoveryCandidateState.REJECTED
    candidate.qualification_outcome = "PROMOTION_BLOCKED: " + reason
    await _record_candidate_event(
        session, candidate, to_state=candidate.state,
        reason=candidate.qualification_outcome,
    )
    await session.flush()
    return {"promoted": False, "reason": reason, "candidate": _candidate_dict(candidate)}


async def promote_candidate(
    session: AsyncSession, candidate: DiscoveryCandidate
) -> dict[str, Any]:
    """Promote a candidate to Prospect ONLY when every gate passes.

    Gates: verified real entity + commercial actor + active enough + market fit
    + problem/need evidence + confirmed-capability fit.
    """
    if candidate.prospect_id:
        return {"promoted": False, "reason": "already promoted", "candidate": _candidate_dict(candidate)}

    capability = await _confirmed_capability(session)

    # Gate 1: verified real entity.
    if candidate.identity_confidence < 0.7:
        return await _reject_candidate(session, candidate, "entity not verified")

    # Gate 2: commercial actor. Non-commercial is a definitive rejection;
    # merely-unverified commercial status is NOT a rejection — it means the
    # candidate needs independent corroborating evidence first.
    if candidate.commercial_status == CommercialEntityStatus.NON_COMMERCIAL:
        return await _reject_candidate(session, candidate, "entity is not a commercial actor")
    if candidate.commercial_status != CommercialEntityStatus.COMMERCIAL_VERIFIED:
        candidate.state = DiscoveryCandidateState.COMMERCIAL_STATUS_CHECK
        candidate.qualification_outcome = "COMMERCIAL_UNVERIFIED"
        await _record_candidate_event(
            session, candidate,
            to_state=candidate.state,
            reason="Commercial actor not independently verified; more corroborating evidence required.",
        )
        await session.flush()
        return {
            "promoted": False,
            "reason": "commercial actor not independently verified",
            "candidate": _candidate_dict(candidate),
        }

    # Gate 3+ (only for independently-verified commercial actors):
    # activity, market fit, need evidence, capability fit.
    failures: list[str] = []
    if candidate.activity_status not in {ActivityStatus.ACTIVE, ActivityStatus.LIKELY_ACTIVE}:
        failures.append("not active enough")
    if candidate.market_fit_confidence < 0.5:
        failures.append("insufficient selected-market fit")
    if candidate.need_evidence_class not in {
        NeedEvidenceClass.DIRECT_NEED_SIGNAL,
        NeedEvidenceClass.STRONG_TECHNICAL_SIGNAL,
    }:
        failures.append("no strong need evidence")
    if capability is None or not _capability_fits(candidate, capability):
        failures.append("no confirmed-capability fit")
    if failures:
        return await _reject_candidate(session, candidate, "; ".join(failures))

    # Promotion is intentionally conservative; create a real Prospect only on
    # full gate pass (rare with GitHub-only evidence).
    company = Company(
        id=new_id(),
        name=candidate.canonical_name,
        website=candidate.official_website,
        origin_source=candidate.source,
        origin_evidence_id=candidate.source_evidence_id,
        external_ids=candidate.external_ids,
    )
    session.add(company)
    await session.flush()
    prospect = Prospect(
        id=new_id(),
        company_id=company.id,
        status=ScoutProspectState.RESEARCHED.value,
        source=candidate.source,
        source_evidence_id=candidate.source_evidence_id,
        qualification={
            "candidate_id": candidate.id,
            "evidence": candidate.problem_evidence,
            "promoted_reason": candidate.qualification_outcome,
        },
    )
    session.add(prospect)
    await session.flush()
    candidate.prospect_id = prospect.id
    candidate.state = DiscoveryCandidateState.PROSPECT_CREATED
    candidate.qualification_outcome = "PROMOTED_TO_PROSPECT"
    candidate.track = EntityTrack.DIRECT_CLIENT_TRACK
    await _record_candidate_event(
        session, candidate, to_state=candidate.state,
        reason="All promotion gates passed; prospect created.",
    )
    await session.flush()
    return {
        "promoted": True,
        "prospect_id": prospect.id,
        "candidate": _candidate_dict(candidate),
    }


# ---------------------------------------------------------------------------
# Funnel
# ---------------------------------------------------------------------------


async def candidate_funnel(session: AsyncSession) -> dict[str, int]:
    rows = (
        await session.execute(
            select(DiscoveryCandidate.state, func.count()).group_by(DiscoveryCandidate.state)
        )
    ).all()
    by_state = {state: count for state, count in rows}
    return {
        "candidates": sum(by_state.values()),
        "identity_resolved": sum(
            c for s, c in by_state.items()
            if s.value != DiscoveryCandidateState.DISCOVERED_SIGNAL.value
        ),
        # Only independently verified commercial actors count as "verified".
        "verified_commercial_entities": sum(
            c for s, c in by_state.items()
            if s.value
            in {
                DiscoveryCandidateState.MARKET_FIT_CHECK.value,
                DiscoveryCandidateState.PROBLEM_RESEARCH.value,
                DiscoveryCandidateState.PROSPECT_ELIGIBLE.value,
                DiscoveryCandidateState.PROSPECT_CREATED.value,
            }
        ),
        "commercial_unverified": by_state.get(DiscoveryCandidateState.COMMERCIAL_STATUS_CHECK.value, 0),
        "not_commercial": by_state.get(DiscoveryCandidateState.NOT_COMMERCIAL.value, 0),
        "rejected": by_state.get(DiscoveryCandidateState.REJECTED.value, 0),
        "promoted_to_prospect": by_state.get(DiscoveryCandidateState.PROSPECT_CREATED.value, 0),
    }


# ---------------------------------------------------------------------------
# Source effectiveness + market reassessment
# ---------------------------------------------------------------------------


async def assess_source_effectiveness(
    session: AsyncSession,
    source: str,
    market: str | None = None,
) -> SourceEffectiveness:
    query = select(DiscoveryCandidate).where(DiscoveryCandidate.source == source)
    candidates = (await session.execute(query)).scalars().all()
    total = len(candidates)
    verified_commercial = sum(
        1 for c in candidates if c.commercial_status == CommercialEntityStatus.COMMERCIAL_VERIFIED
    )
    # Only signals strong enough to advance the capability gate count as
    # problem signals. INDIRECT (e.g. "prototype" in a bio) is tracked
    # separately and never treated as a commercial need.
    problem_signals = sum(
        1 for c in candidates
        if c.need_evidence_class
        in {
            NeedEvidenceClass.DIRECT_NEED_SIGNAL,
            NeedEvidenceClass.STRONG_TECHNICAL_SIGNAL,
        }
    )
    indirect_signals = sum(
        1 for c in candidates
        if c.need_evidence_class == NeedEvidenceClass.INDIRECT_NEED_SIGNAL
    )
    capability_matches = sum(
        1 for c in candidates if c.qualification_outcome and "CAPABILITY" in (c.qualification_outcome or "")
    )
    verified_contacts = sum(1 for c in candidates if c.contact_paths)
    promoted = sum(1 for c in candidates if c.prospect_id)

    identity_resolved = sum(1 for c in candidates if c.identity_confidence >= 0.7)
    non_commercial = sum(
        1 for c in candidates if c.commercial_status == CommercialEntityStatus.NON_COMMERCIAL
    )

    row = (
        await session.execute(
            select(SourceEffectiveness).where(
                SourceEffectiveness.source == source,
                SourceEffectiveness.market == market,
            )
        )
    ).scalar_one_or_none()
    if row is None:
        row = SourceEffectiveness(id=new_id(), source=source, market=market, assessed_at=_now())
        session.add(row)

    row.candidates_found = total
    row.verified_commercial_entities = verified_commercial
    row.problem_signals = problem_signals
    row.capability_matches = capability_matches
    row.verified_contacts = verified_contacts
    row.sales_qualified = 0
    row.promoted_to_prospect = promoted
    row.duplicate_rate = 0.0
    row.verified_entity_rate = round(identity_resolved / total, 3) if total else 0.0
    row.problem_signal_rate = round(problem_signals / total, 3) if total else 0.0
    row.false_positive_rate = round(non_commercial / total, 3) if total else 0.0

    if source == "github":
        row.recommendation = (
            "GitHub is useful for TECHNICAL discovery (real public identity, "
            f"{row.verified_entity_rate:.0%} identity-verified) but weak for "
            "COMMERCIAL prospect discovery "
            f"({row.problem_signal_rate:.0%} strong-problem-signal rate, "
            f"{verified_commercial} independently-verified commercial entities). "
            "Continue GitHub for technical evidence; add official studio/company "
            "directory and website sources to resolve commercial buyers."
        )
    row.notes = {
        "total_candidates": total,
        "non_commercial": non_commercial,
        "verified_commercial": verified_commercial,
        "capability_matches": capability_matches,
        "indirect_need_signals": indirect_signals,
    }
    row.assessed_at = _now()
    await session.flush()
    return row


async def reassess_market(
    session: AsyncSession, market: str, *, source: str = "github"
) -> dict[str, Any]:
    """Reassess a market thesis using real enrichment evidence.

    Distinguishes POOR_MARKET_FIT (no real demand) from POOR_SOURCE_FIT
    (the source cannot answer the commercial question even if the market may
    be good).
    """
    effectiveness = await assess_source_effectiveness(session, source, market=market)
    thesis = (
        await session.execute(
            select(MarketOpportunityThesis).where(MarketOpportunityThesis.market == market)
        )
    ).scalar_one_or_none()

    candidates_found = effectiveness.candidates_found
    verified_commercial = effectiveness.verified_commercial_entities
    problem_signals = effectiveness.problem_signals

    # The market cannot be judged from a source that yields no commercial-entity
    # or strong need evidence: that is a SOURCE limitation, not proof the
    # market is bad.
    if candidates_found > 0 and verified_commercial == 0 and problem_signals == 0:
        conclusion = "POOR_SOURCE_FIT"
        explanation = (
            "GitHub yielded technically relevant entities but zero independently "
            "verified commercial entities and zero strong problem signals. This "
            "is a discovery-source limitation, not evidence against the market: "
            "GitHub cannot answer 'is this a real studio/company with a need?'."
        )
    elif verified_commercial > 0 and problem_signals > 0:
        conclusion = "VALIDATE_FURTHER"
        explanation = (
            f"{verified_commercial} verified commercial entities and "
            f"{problem_signals} problem signals warrant further validation."
        )
    elif verified_commercial > 0 and problem_signals == 0:
        conclusion = "PROMISING"
        explanation = "Commercial entities exist but no need evidence yet; continue research with better sources."
    else:
        conclusion = "WEAK"
        explanation = "Insufficient real evidence to assess the market."

    if thesis is not None:
        thesis.evidence_summary = (
            (thesis.evidence_summary or "")
            + f" Reassessment: {conclusion} — {explanation}"
        )

    await session.flush()
    return {
        "market": market,
        "conclusion": conclusion,
        "explanation": explanation,
        "candidates_found": candidates_found,
        "verified_commercial_entities": verified_commercial,
        "problem_signals": problem_signals,
        "source": source,
    }


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


async def run_enrichment_pass(
    session: AsyncSession, *, market: str | None = None
) -> dict[str, Any]:
    """Reclassify GitHub prospects, enrich every candidate honestly, then
    compute source effectiveness and reassess the market. No outbound."""
    reclassified = await reclassify_github_prospects(session)

    candidates = (
        await session.execute(
            select(DiscoveryCandidate).where(DiscoveryCandidate.source == "github")
        )
    ).scalars().all()

    enriched: list[dict[str, Any]] = []
    async with httpx.AsyncClient(
        timeout=20,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "GrowthOS-RevenueScout/0.1 (public research)",
        },
    ) as client:
        for candidate in candidates:
            profile = await fetch_github_profile(
                candidate.canonical_name,
                (candidate.external_ids or {}).get("github_owner_type"),
                client=client,
            )
            enriched.append(await enrich_candidate(session, candidate, profile=profile))

    # Attempt promotion only for candidates that cleared commercial resolution.
    promoted = 0
    for candidate in candidates:
        if candidate.state in {
            DiscoveryCandidateState.COMMERCIAL_STATUS_CHECK,
            DiscoveryCandidateState.MARKET_FIT_CHECK,
            DiscoveryCandidateState.PROBLEM_RESEARCH,
        }:
            result = await promote_candidate(session, candidate)
            promoted += int(result.get("promoted", False))

    selected_market = market or "2D indie & mobile game studios"
    effectiveness = await assess_source_effectiveness(session, "github", market=selected_market)
    reassessment = await reassess_market(session, selected_market, source="github")

    await session.flush()
    return {
        "reclassified": reclassified,
        "candidates_enriched": len(enriched),
        "candidates": enriched,
        "promoted_to_prospect": promoted,
        "outbound": "disabled",
        "source_effectiveness": {
            "candidates_found": effectiveness.candidates_found,
            "verified_commercial_entities": effectiveness.verified_commercial_entities,
            "problem_signals": effectiveness.problem_signals,
            "capability_matches": effectiveness.capability_matches,
            "verified_contacts": effectiveness.verified_contacts,
            "sales_qualified": effectiveness.sales_qualified,
            "promoted_to_prospect": effectiveness.promoted_to_prospect,
            "verified_entity_rate": effectiveness.verified_entity_rate,
            "false_positive_rate": effectiveness.false_positive_rate,
            "problem_signal_rate": effectiveness.problem_signal_rate,
            "recommendation": effectiveness.recommendation,
        },
        "market_reassessment": reassessment,
    }
