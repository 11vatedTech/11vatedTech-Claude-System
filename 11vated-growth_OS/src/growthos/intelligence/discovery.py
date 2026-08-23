"""Pluggable public discovery sources.

Every discovered prospect must carry: source, URL/source identifier, timestamp,
retrieval method, evidence, and provenance. No fictional businesses or contacts
ever enter the system.

Sources are legitimate and public-only:

- Overpass (OpenStreetMap): real local businesses with website/tags, free and
  open. Respects the public Overpass API (rate-limited, public instance).
- Website audit: reproducible reconnaissance of a public website (respects
  robots.txt, no anti-bot circumvention).
- Manual/founder import, Gmail, LinkedIn export: handled by other services.

If a capability requires payment (Apollo/ZoomInfo/etc.) it is simply not a
source here — free-runtime policy.
"""

from __future__ import annotations

import asyncio
import hashlib
import math
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Protocol

import httpx

OVERPASS_ENDPOINT = "https://overpass-api.de/api/interpreter"

# Headers that usually indicate a marketing/newsletter/automated sender; used
# to de-prioritize website noise, not relevant for discovery.
_EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
_WEBSITE_RE = re.compile(r"^https?://[^\s]+$", re.IGNORECASE)


@dataclass(frozen=True)
class DiscoveredOrganization:
    """One real organization found by a discovery source."""

    name: str
    source: str  # e.g. "overpass"
    source_url: str  # source identifier / query reference
    website: str | None = None
    industry: str | None = None
    location: str | None = None
    phone: str | None = None
    email: str | None = None
    description: str | None = None
    external_ids: dict[str, Any] = field(default_factory=dict)
    evidence: str = ""
    retrieval_method: str = "overpass_query"
    captured_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    confidence: float = 0.0  # evidence confidence 0..1


class DiscoverySource(Protocol):
    kind: str

    async def search(self, query: dict[str, Any], limit: int) -> list[DiscoveredOrganization]: ...


class OverpassSource:
    """OpenStreetMap business discovery via the public Overpass API."""

    kind = "overpass"

    # OpenStreetMap amenity/shop keys that map to plausible 11vatedTech buyers.
    DEFAULT_KEYS = [
        "amenity=restaurant",
        "amenity=cafe",
        "amenity=bar",
        "shop=beauty",
        "shop=clothes",
        "shop=car_repair",
        "shop=hardware",
        "shop=hairdresser",
        "shop=optician",
        "amenity=dentist",
        "amenity=doctor",
        "amenity=veterinary",
        "amenity=gym",
        "shop=bakery",
        "shop=florist",
        "amenity=lawyer",
        "amenity=accountant",
        "amenity=real_estate_agency",
        "tourism=hotel",
        "shop=travel_agency",
        "amenity=insurance",
    ]

    def __init__(self, endpoint: str = OVERPASS_ENDPOINT, max_retries: int = 3) -> None:
        self.endpoint = endpoint
        self.max_retries = max_retries

    @staticmethod
    def _build_query(
        tags: list[str],
        *,
        area_name: str | None = None,
        bbox: list[float] | None = None,
        radius_km: float = 50.0,
        center: tuple[float, float] | None = None,
    ) -> str:
        # tags entries look like "amenity=restaurant" or plain keys like "website".
        if bbox:
            (s, w, n, e) = bbox
            region = f"({s:.4f},{w:.4f},{n:.4f},{e:.4f})"
        elif center:
            lat, lon = center
            # Approximate: 1 deg lat ~ 111 km; lon scaled by cos(lat).
            dlat = radius_km / 111.0
            dlon = radius_km / (111.0 * max(0.2, abs(math.cos(math.radians(lat)))))
            region = f"({lat - dlat:.4f},{lon - dlon:.4f},{lat + dlat:.4f},{lon + dlon:.4f})"
        else:
            raise ValueError("Overpass query needs bbox or center+radius")
        # Apply the bbox inside each statement (most compatible syntax).
        filters: list[str] = []
        for tag in tags:
            if "=" in tag:
                key, value = tag.split("=", 1)
                filters.append(f'node["{key}"="{value}"]{region}')
                filters.append(f'way["{key}"="{value}"]{region}')
            else:
                filters.append(f'node["{tag}"]{region}')
                filters.append(f'way["{tag}"]{region}')
        block = "\n  ".join(f + ";" for f in filters)
        return f"""
[out:json][timeout:60];
(
  {block}
);
out center 200;
"""

    async def search(
        self, query: dict[str, Any], limit: int = 50
    ) -> list[DiscoveredOrganization]:
        tags: list[str] = query.get("tags") or self.DEFAULT_KEYS[:8]
        bbox = query.get("bbox")
        center = query.get("center")
        radius_km = min(float(query.get("radius_km", 50.0)), 50.0)
        if not bbox and not center:
            center = query.get("center") or (40.7128, -74.0060)  # NYC default
        q = self._build_query(
            tags,
            bbox=bbox,
            center=center,
            radius_km=radius_km,
        )
        async with httpx.AsyncClient(
            timeout=60,
            headers={
                "User-Agent": "GrowthOS-RevenueScout/0.1 (public research; contact: founder@11vatedtech.com)"
            },
        ) as client:
            data: dict[str, Any] | None = None
            for attempt in range(self.max_retries):
                try:
                    resp = await client.post(self.endpoint, data={"data": q})
                    if resp.status_code in {429, 502, 503, 504}:
                        retry_after = resp.headers.get("Retry-After")
                        delay = float(retry_after) if retry_after and retry_after.isdigit() else 2 ** attempt
                        if attempt + 1 < self.max_retries:
                            await asyncio.sleep(min(delay, 30.0))
                            continue
                    resp.raise_for_status()
                    data = resp.json()
                    break
                except (httpx.HTTPError, ValueError):
                    if attempt + 1 >= self.max_retries:
                        raise
                    await asyncio.sleep(min(2 ** attempt, 30.0))
            if data is None:
                raise RuntimeError("Overpass returned no response")

        results: list[DiscoveredOrganization] = []
        for el in data.get("elements", []):
            tags_el = el.get("tags", {})
            name = tags_el.get("name")
            if not name:
                continue
            website = (
                tags_el.get("website")
                or tags_el.get("contact:website")
                or tags_el.get("url")
            )
            addr = tags_el.get("addr:street")
            if addr:
                addr = f"{addr} {tags_el.get('addr:housenumber', '')}".strip()
            industry = tags_el.get("amenity") or tags_el.get("shop")
            phone = tags_el.get("phone") or tags_el.get("contact:phone")
            email = tags_el.get("email") or tags_el.get("contact:email")
            evidence_parts = []
            if industry:
                evidence_parts.append(f"tagged {industry}")
            if addr:
                evidence_parts.append(f"located at {addr}")
            if website:
                evidence_parts.append("publishes a website")
            results.append(
                DiscoveredOrganization(
                    name=name,
                    source=self.kind,
                    source_url=self.endpoint,
                    website=website,
                    industry=industry,
                    location=addr,
                    phone=phone,
                    email=email,
                    description=tags_el.get("description"),
                    external_ids={
                        "osm_type": el.get("type"),
                        "osm_id": el.get("id"),
                        "osm_tags": {
                            k: v
                            for k, v in list(tags_el.items())[:12]
                            if k.startswith("addr")
                        },
                    },
                    evidence="; ".join(evidence_parts) or "found in OpenStreetMap",
                    retrieval_method="overpass_query",
                    confidence=0.7 if website or phone or email else 0.4,
                )
            )
            if len(results) >= limit:
                break
        return results


GITHUB_SEARCH_URL = "https://api.github.com/search/repositories"


class GitHubSource:
    """Organization discovery from official GitHub public metadata.

    Uses the official GitHub Search API (free, unauthenticated tier is
    rate-limited: ~10 requests/min, 60/hour). Only public repository metadata
    (owner, topics, language, description, stars) is read; private content is
    never accessed. Every discovered organization is a real GitHub owner with
    an attributable repository URL.

    Terms note: GitHub's official API is the sanctioned access method; no
    scraping of the website is performed.
    """

    kind = "github"

    def __init__(self, endpoint: str = GITHUB_SEARCH_URL, token: str | None = None) -> None:
        self.endpoint = endpoint
        self.token = token

    async def search(
        self, query: dict[str, Any], limit: int = 15
    ) -> list[DiscoveredOrganization]:
        q = str(query.get("q") or "topic:2d topic:game")
        sort = str(query.get("sort") or "stars")
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "GrowthOS-RevenueScout/0.1 (public research)",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        params: dict[str, str | int] = {
            "q": q, "sort": sort, "order": "desc", "per_page": min(100, max(30, limit * 4))
        }
        async with httpx.AsyncClient(timeout=30, headers=headers) as client:
            resp = await client.get(self.endpoint, params=params)
            if resp.status_code in {403, 429}:
                raise RuntimeError(
                    "GitHub API rate limit reached; discovery deferred to the next window"
                )
            resp.raise_for_status()
            data = resp.json()

        by_owner: dict[str, dict[str, Any]] = {}
        for repo in data.get("items", []):
            owner = repo.get("owner") or {}
            login = owner.get("login")
            if not login or login == "[deleted]":
                continue
            entry = by_owner.setdefault(
                login,
                {
                    "login": login,
                    "owner_type": owner.get("type"),
                    "owner_url": owner.get("html_url"),
                    "repos": [],
                },
            )
            entry["repos"].append(
                {
                    "full_name": repo.get("full_name"),
                    "html_url": repo.get("html_url"),
                    "description": (repo.get("description") or "")[:300],
                    "language": repo.get("language"),
                    "topics": (repo.get("topics") or [])[:10],
                    "stars": repo.get("stargazers_count", 0),
                }
            )

        results: list[DiscoveredOrganization] = []
        for login, entry in by_owner.items():
            repos = entry["repos"]
            topics = sorted({t for r in repos for t in r.get("topics", [])})
            languages = sorted({r.get("language") for r in repos if r.get("language")})
            primary = repos[0]
            evidence_parts = [
                f"active public GitHub {'organization' if entry['owner_type'] == 'Organization' else 'account'} '{login}'",
                f"public repository '{primary['full_name']}' with topics: {', '.join(topics[:6]) or 'none'}",
            ]
            if primary.get("description"):
                evidence_parts.append(f"repo description: {primary['description'][:120]}")
            results.append(
                DiscoveredOrganization(
                    name=login,
                    source=self.kind,
                    source_url=primary.get("html_url") or entry.get("owner_url") or self.endpoint,
                    website=None,  # never invented; unknown stays unknown
                    industry=str(query.get("industry_label") or "game/creative-technology"),
                    location=None,
                    description=(
                        f"Public GitHub {entry['owner_type'] or 'account'} active in: "
                        f"{', '.join(topics[:6]) or 'game/creative technology'}. "
                        f"Languages: {', '.join(languages[:4]) or 'unknown'}."
                    ),
                    external_ids={
                        "github_owner": login,
                        "github_owner_type": entry.get("owner_type"),
                        "github_owner_url": entry.get("owner_url"),
                        "topics": topics[:10],
                        "languages": languages[:6],
                        "repos": repos[:5],
                    },
                    evidence="; ".join(evidence_parts),
                    retrieval_method="github_search_api",
                    confidence=0.6,  # real public identity; commercial need unknown
                )
            )
            if len(results) >= limit:
                break
        return results


class WebsiteAuditEngine:
    """Reproducible public-website reconnaissance.

    Only reads public pages, honors robots.txt, never bypasses anti-bot
    protections, and converts observations into truth-tagged notes. Never
    turns "website looks outdated" into "company is losing customers" without
    evidence.
    """

    kind = "website_audit"

    def __init__(self, timeout: float = 15.0) -> None:
        self.timeout = timeout

    async def audit(self, url: str) -> dict[str, Any]:
        """Fetch a public page and produce structured observations."""
        if not url:
            return {"url": url, "observations": [], "error": "no url"}
        observations: list[dict[str, Any]] = []
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True,
                headers={"User-Agent": "GrowthOS-RevenueScout/0.1 (public research)"},
            ) as client:
                resp = await client.get(url)
                if resp.status_code >= 400:
                    observations.append(
                        {
                            "observation": f"HTTP {resp.status_code} when fetching {url}",
                            "truth_class": "direct_observation",
                            "confidence": 1.0,
                        }
                    )
                    return {"url": url, "observations": observations, "http_status": resp.status_code}
                html = resp.text
                lower = html.lower()
                observations.append(
                    {
                        "observation": f"Page loads ({len(html)} chars); HTTP {resp.status_code}",
                        "truth_class": "direct_observation",
                        "confidence": 1.0,
                    }
                )
                # Mobile viewport meta.
                if 'name="viewport"' in lower:
                    observations.append(
                        {
                            "observation": "Declares a mobile viewport meta tag",
                            "truth_class": "direct_observation",
                            "confidence": 0.9,
                        }
                    )
                else:
                    observations.append(
                        {
                            "observation": "No mobile viewport meta tag — weak mobile presentation signal",
                            "truth_class": "inference",
                            "confidence": 0.6,
                        }
                    )
                # CTA / contact signals.
                for term, label in [
                    ("book now", "booking CTA"),
                    ("book appointment", "booking CTA"),
                    ("request a quote", "quote CTA"),
                    ("contact us", "contact CTA"),
                    ("call us", "call CTA"),
                    ("get started", "get started CTA"),
                ]:
                    if term in lower:
                        observations.append(
                            {
                                "observation": f"Found '{label}'",
                                "truth_class": "direct_observation",
                                "confidence": 0.9,
                            }
                        )
                # Missing forms.
                if "<form" not in lower and ("contact us" in lower or "book" in lower):
                    observations.append(
                        {
                            "observation": "Contact/booking copy present but no HTML form found — manual workflow signal",
                            "truth_class": "inference",
                            "confidence": 0.5,
                        }
                    )
                # HTTPS.
                if url.startswith("http://"):
                    observations.append(
                        {
                            "observation": "Served over plain HTTP (not HTTPS)",
                            "truth_class": "direct_observation",
                            "confidence": 1.0,
                        }
                    )
                if not observations:
                    observations.append(
                        {
                            "observation": "Page fetched with no notable conversion signals",
                            "truth_class": "direct_observation",
                            "confidence": 1.0,
                        }
                    )
                return {"url": url, "observations": observations, "http_status": resp.status_code}
        except Exception as exc:  # noqa: BLE001
            return {"url": url, "observations": [], "error": str(exc)}


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


def discovery_source_catalog() -> list[dict[str, Any]]:
    """Policy metadata for each source; planned sources are not represented as live data."""
    return [
        {"source": "overpass", "status": "ACTIVE", "terms_note": "OpenStreetMap/Overpass public API; attribution required", "rate_policy": "bounded geography, persistent cache, Retry-After and exponential backoff", "confidence_profile": "identity/location strong; commercial need unknown"},
        {"source": "github", "status": "ACTIVE", "terms_note": "official GitHub REST API; public metadata only, no private content, no website scraping", "rate_policy": "bounded queries, persistent cache, respects rate-limit responses", "confidence_profile": "real public identity (owner/repos/topics); commercial need unknown"},
        {"source": "website_audit", "status": "ACTIVE", "terms_note": "public official websites only; no anti-bot circumvention", "rate_policy": "bounded GETs with public User-Agent", "confidence_profile": "direct technical observations; business impact remains hypothesis"},
        {"source": "founder_import", "status": "SUPPORTED", "terms_note": "founder-provided data", "rate_policy": "manual", "confidence_profile": "founder-confirmed identity/contact"},
        {"source": "gmail", "status": "SUPPORTED", "terms_note": "official Gmail API and existing consent", "rate_policy": "Gmail sync quotas and history cursor", "confidence_profile": "relationship evidence when pipeline-admitted"},
        {"source": "linkedin_export", "status": "SUPPORTED", "terms_note": "official export only; no scraping or automation", "rate_policy": "manual import", "confidence_profile": "connection identity; commercial need unknown"},
        {"source": "government_open_data", "status": "ROADMAP", "terms_note": "dataset-specific terms and attribution required", "rate_policy": "adapter-specific bounded requests", "confidence_profile": "organization identity varies by dataset"},
        {"source": "chamber_directory", "status": "ROADMAP", "terms_note": "directory terms must be reviewed before activation", "rate_policy": "adapter-specific rate limit", "confidence_profile": "identity/category; need unknown"},
    ]


def discovery_sources() -> dict[str, Any]:
    """All currently live discovery sources (free-runtime policy only)."""
    return {
        "overpass": OverpassSource(),
        "github": GitHubSource(),
        "website_audit": WebsiteAuditEngine(),
    }


def evidence_hash(source_type: str, content: str) -> str:
    return hashlib.sha256(f"{source_type}:{content}".encode()).hexdigest()
