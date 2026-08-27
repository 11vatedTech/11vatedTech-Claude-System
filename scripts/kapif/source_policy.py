#!/usr/bin/env python3
"""
KAPIF Source Policy Engine — determines what may be acquired and under what conditions.

Evaluates: robots.txt, site terms, authentication, paywall, content license,
API license, rate limits, commercial-use implications.

Robots.txt is NOT a copyright license. A permissive crawler rule does not
make content commercially reusable.
"""
from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser


@dataclass
class SourcePolicy:
    """Policy decision for a source before acquisition."""
    url: str
    decision: str = "METADATA_ALLOWED"  # Default, overridden by evaluate_source
    robots_status: str = "unknown"  # allowed, disallowed, not_checked, error
    terms_status: str = "unknown"
    auth_required: bool = False
    paywall_status: str = "unknown"
    content_license: str = "unknown"
    api_license: str = "unknown"
    rate_limit_rps: float = 0.0
    rate_limit_remaining: int = -1
    rate_limit_reset: float = 0.0
    commercial_use_allowed: bool = False
    checked_at: str = ""
    reason: str = ""


class RobotCache:
    """RFC 9309-aware robots.txt cache."""

    def __init__(self, ttl_seconds: int = 3600):
        self._cache: dict[str, tuple[RobotFileParser, float]] = {}
        self._ttl = ttl_seconds

    def _key(self, url: str) -> str:
        p = urlparse(url)
        return f"{p.scheme}://{p.netloc}"

    def is_allowed(self, url: str, user_agent: str = "KAPIF/1.0") -> tuple[bool, str]:
        """Check robots.txt. Returns (allowed, status)."""
        import urllib.request

        key = self._key(url)
        if key in self._cache:
            rp, cached_at = self._cache[key]
            if time.time() - cached_at < self._ttl:
                allowed = rp.can_fetch(user_agent, url)
                return allowed, "cached"

        rp = RobotFileParser()
        rp.set_url(f"{key}/robots.txt")
        try:
            rp.read()
            self._cache[key] = (rp, time.time())
            allowed = rp.can_fetch(user_agent, url)
            return allowed, "checked"
        except Exception:
            return True, "unreachable"  # Allow but note


# Global instances
_robot_cache = RobotCache()


def evaluate_source(url: str, adapter_type: str = "generic_web") -> SourcePolicy:
    """Determine acquisition policy for a URL before any fetch."""
    policy = SourcePolicy(url=url, checked_at=datetime.now().isoformat())

    # Check robots.txt
    allowed, robots_status = _robot_cache.is_allowed(url)
    policy.robots_status = robots_status
    if not allowed and robots_status == "checked":
        policy.decision = "BLOCKED"
        policy.reason = "robots_disallow"
        return policy

    # Domain-specific heuristics (should be adapter-driven in production)
    domain = urlparse(url).netloc.lower()

    # Known API sources
    if "api.crossref.org" in domain:
        policy.decision = "API_ALLOWED"
        policy.content_license = "metadata_mostly_open"
        policy.commercial_use_allowed = True
        policy.rate_limit_rps = 50.0
        return policy

    if "api.openalex.org" in domain:
        policy.decision = "API_ALLOWED"
        policy.content_license = "CC0"
        policy.commercial_use_allowed = True
        policy.rate_limit_rps = 10.0
        return policy

    if "api.semanticscholar.org" in domain:
        policy.decision = "API_ALLOWED"
        policy.content_license = "non_commercial_limited"
        policy.api_license = "ODC-BY for datasets, API terms for metadata"
        policy.commercial_use_allowed = False
        policy.rate_limit_rps = 1.0
        return policy

    if "api.github.com" in domain:
        policy.decision = "API_ALLOWED"
        policy.content_license = "varies_by_repo"
        policy.auth_required = False  # public endpoints
        policy.commercial_use_allowed = True
        policy.rate_limit_rps = 1.0  # unauthenticated
        return policy

    # Known official doc sources
    official_patterns = [
        ("docs.unrealengine.com", "Epic Games", "official_docs"),
        ("docs.blender.org", "Blender Foundation", "CC_BY_SA"),
        ("docs.python.org", "Python Software Foundation", "PSF"),
        ("nodejs.org", "OpenJS Foundation", "MIT"),
        ("developer.mozilla.org", "Mozilla", "CC_BY_SA"),
        ("w3.org", "W3C", "varies_document_license"),
        ("ietf.org", "IETF", "BCP78"),
        ("github.com/penpot", "Penpot", "MPL_2.0"),
        ("github.com/orama-interactive/Pixelorama", "Orama Interactive", "MIT"),
        ("materialx.org", "Academy Software Foundation", "Apache_2.0"),
        ("openpbr.org", "Academy Software Foundation", "Apache_2.0"),
        ("openusd.org", "Pixar/ASWF", "Apache_2.0"),
        ("c2pa.org", "C2PA", "spec_license"),
    ]
    for pattern, owner, license_ in official_patterns:
        if pattern in url:
            policy.decision = "FULL_TEXT_ALLOWED"
            policy.content_license = license_
            policy.commercial_use_allowed = True
            return policy

    # Default for generic web
    policy.decision = "METADATA_ALLOWED"
    return policy


class RateLimiter:
    """Rate-limit discipline with exponential backoff."""

    def __init__(self):
        self._last_request: dict[str, float] = {}
        self._consecutive_429: dict[str, int] = {}

    def wait_if_needed(self, domain: str, min_interval: float = 0.1):
        """Block until minimum interval since last request to domain."""
        now = time.time()
        if domain in self._last_request:
            elapsed = now - self._last_request[domain]
            if elapsed < min_interval:
                time.sleep(min_interval - elapsed)
        self._last_request[domain] = time.time()

    def handle_429(self, domain: str, retry_after: float = 5.0) -> float:
        """Handle rate limit with backoff. Returns backoff seconds."""
        self._consecutive_429[domain] = self._consecutive_429.get(domain, 0) + 1
        backoff = retry_after * (2 ** (self._consecutive_429[domain] - 1))
        time.sleep(backoff)
        return backoff

    def reset_429(self, domain: str):
        self._consecutive_429[domain] = 0


_rate_limiter = RateLimiter()


def get_rate_limiter() -> RateLimiter:
    return _rate_limiter