"""Unit tests for commercial entity resolution (pure, deterministic logic).

These cover the classification heuristics without any database or network:
GitHub account type is never commercial identity; activity/need/commercial
status are independent; discovery priority is separate from revenue scoring.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from growthos.domain.enums import (
    ActivityStatus,
    CommercialEntityStatus,
    NeedEvidenceClass,
    OrganizationType,
)
from growthos.domain.models_scout import DiscoveryCandidate
from growthos.services.entity_resolution import (
    _resolve_activity,
    _resolve_commercial_status,
    _resolve_entity_type,
    _resolve_need,
    _topic_market_fit,
    candidate_identity_key,
    compute_discovery_priority,
)
from growthos.shared.ids import new_id


def _profile(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "name": "",
        "company": "",
        "blog": "",
        "email": "",
        "bio": "",
        "location": "",
        "public_repos": 0,
        "followers": 0,
        "updated_at": None,
    }
    base.update(overrides)
    return base


def test_github_org_alone_is_not_commercial_company() -> None:
    entity_type, _confidence = _resolve_entity_type("Organization", _profile(), 3)
    assert entity_type == OrganizationType.OPEN_SOURCE_ORGANIZATION


def test_org_with_website_and_company_resolves_commercial() -> None:
    entity_type, confidence = _resolve_entity_type(
        "Organization", _profile(blog="https://studio.example", company="Studio Inc"), 5
    )
    assert entity_type == OrganizationType.COMMERCIAL_COMPANY
    assert 0.0 < confidence <= 0.6  # capped; GitHub is self-reported


def test_user_with_company_resolves_independent_developer() -> None:
    entity_type, _ = _resolve_entity_type(
        "User", _profile(company="Indie Studio", blog="https://dev.example"), 4
    )
    assert entity_type == OrganizationType.INDEPENDENT_DEVELOPER


def test_bare_user_with_few_repos_is_hobby_project() -> None:
    entity_type, _ = _resolve_entity_type("User", _profile(), 1)
    assert entity_type == OrganizationType.HOBBY_PROJECT


def test_individual_is_non_commercial() -> None:
    status, confidence = _resolve_commercial_status(OrganizationType.HOBBY_PROJECT, _profile())
    assert status == CommercialEntityStatus.NON_COMMERCIAL
    assert confidence >= 0.5


def test_commercial_entity_is_unverified_not_verified() -> None:
    # GitHub self-reported signals are NOT independent corroboration.
    status, _ = _resolve_commercial_status(OrganizationType.COMMERCIAL_COMPANY, _profile())
    assert status == CommercialEntityStatus.COMMERCIAL_UNVERIFIED


def test_activity_from_updated_at() -> None:
    recent = (datetime.now(UTC) - timedelta(days=10)).isoformat()
    old = (datetime.now(UTC) - timedelta(days=700)).isoformat()
    assert _resolve_activity(_profile(updated_at=recent))[0] in {
        ActivityStatus.ACTIVE,
        ActivityStatus.LIKELY_ACTIVE,
    }
    assert _resolve_activity(_profile(updated_at=old))[0] in {
        ActivityStatus.STALE,
        ActivityStatus.LIKELY_INACTIVE,
    }
    assert _resolve_activity(_profile())[0] == ActivityStatus.UNKNOWN


def test_topic_relevance_is_not_need() -> None:
    need_class, _reason = _resolve_need(_profile(), ["2d", "sprite", "game"])
    assert need_class in {NeedEvidenceClass.NO_NEED_EVIDENCE, NeedEvidenceClass.GENERAL_RELEVANCE}


def test_explicit_need_signal_is_indirect_only() -> None:
    need_class, _ = _resolve_need(_profile(bio="We are hiring a gameplay programmer"), [])
    assert need_class == NeedEvidenceClass.INDIRECT_NEED_SIGNAL


def test_market_fit_scores_topic_overlap() -> None:
    assert _topic_market_fit([]) == 0.0
    assert _topic_market_fit(["2d", "sprite", "game"]) >= 0.6
    assert _topic_market_fit(["unrelated"]) <= 0.2


def test_identity_key_is_deterministic_per_source() -> None:
    a = candidate_identity_key("github", {"github_owner": "acme"})
    b = candidate_identity_key("github", {"github_owner": "acme"})
    c = candidate_identity_key("github", {"github_owner": "other"})
    assert a == b
    assert a != c


def test_discovery_priority_is_independent_of_revenue_score() -> None:
    candidate = DiscoveryCandidate(
        id=new_id(),
        source="github",
        source_identity_key="github:acme",
        canonical_name="acme",
        identity_confidence=0.95,
        market_fit_confidence=0.8,
        commercial_entity_confidence=0.2,
        buyer_potential_confidence=0.0,
    )
    # Discovery priority is a research-triage number, never a revenue number.
    priority = compute_discovery_priority(candidate)
    assert 0.0 <= priority <= 1.0
    assert candidate.discovery_priority_score is None  # pure function; not mutated
    # No revenue-scoring fields exist on a candidate by construction.
    assert not hasattr(candidate, "revenue_opportunity_score")
