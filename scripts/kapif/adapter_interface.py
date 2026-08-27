#!/usr/bin/env python3
"""
KAPIF Source Adapter Interface.

Normalized interface: discover(query), fetch(identifier), refresh(snapshot),
policy(identifier), normalize(raw), metadata(raw), citations(raw), license(raw),
change_token(raw).

Adapters return normalized data. The rest of KAPIF should not know
Crossref-specific response structure.
"""
from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlparse

from . import source_policy
from .content_normalizer import UntrustedContent, normalize_and_scan
from .data_layer import log_fetch, store_snapshot
from .db import close_conn


@dataclass
class FetchResult:
    """Normalized fetch result from any adapter."""
    url: str
    adapter: str
    http_status: int
    etag: str = ""
    last_modified: str = ""
    content_type: str = ""
    raw_bytes: bytes = b""
    normalized_text: str = ""
    content_hash: str = ""
    normalized_hash: str = ""
    policy_decision: str = ""
    robots_status: str = ""
    safe_for_privileged: bool = True
    injection_flagged: bool = False
    warnings: list[str] = field(default_factory=list)
    snapshot_id: int = -1
    metadata: dict[str, Any] = field(default_factory=dict)


class SourceAdapter:
    """Base adapter with fetch/policy/normalize lifecycle."""

    adapter_name: str = "generic"
    adapter_version: str = "0.1.0"

    def policy(self, url: str) -> source_policy.SourcePolicy:
        return source_policy.evaluate_source(url, self.adapter_name)

    def fetch(self, url: str, **kwargs) -> FetchResult:
        """Override in subclasses."""
        raise NotImplementedError

    def normalize(self, result: FetchResult) -> FetchResult:
        """Run content through normalizer + injection scan."""
        norm = normalize_and_scan(result.raw_bytes, result.content_type, result.url)
        result.normalized_text = norm["text"]
        result.normalized_hash = hashlib.sha256(
            result.normalized_text.encode("utf-8", errors="replace")).hexdigest()
        result.injection_flagged = norm.get("injection", {}).get("flagged", False)
        result.safe_for_privileged = norm["safe_for_privileged_plane"]
        result.warnings = norm.get("warnings", [])
        return result

    def acquire(self, url: str, **kwargs) -> FetchResult:
        """Full acquire lifecycle: policy check → fetch → normalize → store snapshot."""
        pol = self.policy(url)
        if pol.decision in ("BLOCKED", "RESTRICTED", "HUMAN_REVIEW_REQUIRED"):
            log_fetch(url, self.adapter_name, http_status=0,
                      policy_decision=pol.decision, robots_status=pol.robots_status)
            return FetchResult(
                url=url, adapter=self.adapter_name, http_status=0,
                policy_decision=pol.decision, robots_status=pol.robots_status,
            )

        # Rate limit
        domain = urlparse(url).netloc
        rl = source_policy.get_rate_limiter()
        rl.wait_if_needed(domain)

        try:
            result = self.fetch(url, **kwargs)
            result.adapter = self.adapter_name
            result.policy_decision = pol.decision
            result.robots_status = pol.robots_status

            if result.http_status == 429:
                retry_after = 5.0
                rl.handle_429(domain, retry_after)
                log_fetch(url, self.adapter_name, http_status=429,
                          policy_decision=pol.decision, robots_status=pol.robots_status,
                          retry_count=1)
                return result

            if result.http_status == 304:
                log_fetch(url, self.adapter_name, http_status=304,
                          cache_hit=True, policy_decision=pol.decision)
                return result

            rl.reset_429(domain)

            # Normalize
            result = self.normalize(result)

            # Store snapshot
            content = result.raw_bytes
            result.content_hash = hashlib.sha256(content).hexdigest()
            result.normalized_hash = hashlib.sha256(
                result.normalized_text.encode("utf-8", errors="replace")).hexdigest()

            sid = store_snapshot(
                url=result.url, content=content,
                normalized=result.normalized_text, adapter=self.adapter_name,
                http_status=result.http_status, etag=result.etag,
                last_modified=result.last_modified,
                policy_decision=pol.decision, robots_status=pol.robots_status,
                content_type=result.content_type,
            )
            result.snapshot_id = sid

            log_fetch(url, self.adapter_name, http_status=result.http_status,
                      bytes_fetched=len(content),
                      policy_decision=pol.decision, robots_status=pol.robots_status)

            return result

        except Exception as e:
            log_fetch(url, self.adapter_name, http_status=0, error=str(e)[:200],
                      policy_decision=pol.decision)
            return FetchResult(
                url=url, adapter=self.adapter_name, http_status=0,
                policy_decision=pol.decision, robots_status=pol.robots_status,
            )

    def change_token(self, last_snapshot: dict[str, Any]) -> str | None:
        """Return a token representing this source's current state for change detection."""
        return None