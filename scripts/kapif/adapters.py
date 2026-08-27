#!/usr/bin/env python3
"""
KAPIF Source Adapters — Crossref, OpenAlex, Semantic Scholar, GitHub, Generic Web.

API-first, crawler-second. Never scrape HTML when an authoritative supported API exists.
"""
from __future__ import annotations

import json
import re
import time
from typing import Any

import requests

from .adapter_interface import FetchResult, SourceAdapter

USER_AGENT = "KAPIF/0.1 (mailto:dev@11vatedtech.com)"


def _http_get(url: str, headers: dict | None = None, timeout: int = 30) -> requests.Response:
    hdrs = {"User-Agent": USER_AGENT}
    if headers:
        hdrs.update(headers)
    return requests.get(url, headers=hdrs, timeout=timeout)


# ═══════════════════════════════════════════════════
# A. Crossref
# ═══════════════════════════════════════════════════

class CrossrefAdapter(SourceAdapter):
    adapter_name = "crossref"
    adapter_version = "0.1.0"

    def _build_url(self, endpoint: str, params: dict | None = None) -> str:
        base = f"https://api.crossref.org/{endpoint}"
        if params:
            qs = "&".join(f"{k}={v}" for k, v in params.items())
            return f"{base}?{qs}"
        return base

    def discover(self, query: str, rows: int = 5) -> list[dict]:
        """Discover works by query."""
        url = self._build_url("works", {"query": query, "rows": str(rows)})
        r = _http_get(url)
        if r.status_code != 200:
            return []
        data = r.json()
        items = data.get("message", {}).get("items", [])
        return [{
            "doi": item.get("DOI"),
            "title": item.get("title", [""])[0],
            "publisher": item.get("publisher"),
            "type": item.get("type"),
            "year": item.get("published-print", {}).get("date-parts", [[None]])[0][0],
            "url": item.get("URL"),
            "citation_count": item.get("is-referenced-by-count"),
        } for item in items]

    def fetch(self, url: str, **kwargs) -> FetchResult:
        r = _http_get(url)
        return FetchResult(
            url=url, adapter=self.adapter_name, http_status=r.status_code,
            content_type=r.headers.get("Content-Type", "application/json"),
            raw_bytes=r.content,
            metadata={"response_json": r.json() if r.status_code == 200 else {}},
        )

    def fetch_work(self, doi: str) -> FetchResult:
        url = self._build_url(f"works/{doi}")
        return self.acquire(url)

    def change_token(self, last_snapshot: dict[str, Any]) -> str | None:
        """Crossref works can be updated — check indexed timestamp."""
        return None  # Needs additional call


# ═══════════════════════════════════════════════════
# B. OpenAlex
# ═══════════════════════════════════════════════════

class OpenAlexAdapter(SourceAdapter):
    adapter_name = "openalex"
    adapter_version = "0.1.0"

    BASE = "https://api.openalex.org"

    def discover(self, query: str, entity: str = "works", per_page: int = 5) -> list[dict]:
        url = f"{self.BASE}/{entity}?search={query}&per_page={per_page}"
        r = _http_get(url)
        if r.status_code != 200:
            return []
        data = r.json()
        return [{
            "id": item.get("id"),
            "doi": item.get("doi"),
            "title": item.get("title"),
            "type": item.get("type"),
            "publication_year": item.get("publication_year"),
            "cited_by_count": item.get("cited_by_count"),
            "open_access": item.get("open_access", {}).get("is_oa", False),
        } for item in data.get("results", [])]

    def fetch(self, url: str, **kwargs) -> FetchResult:
        # Polite identification
        r = _http_get(url, headers={"mailto": "dev@11vatedtech.com"})
        return FetchResult(
            url=url, adapter=self.adapter_name, http_status=r.status_code,
            content_type="application/json", raw_bytes=r.content,
            metadata={"openalex_id": url.split("/")[-1]},
        )

    def fetch_work(self, openalex_id: str) -> FetchResult:
        url = f"{self.BASE}/works/{openalex_id}"
        return self.acquire(url)

    def fetch_author(self, orcid: str) -> FetchResult:
        url = f"{self.BASE}/authors/{orcid}"
        return self.acquire(url)


# ═══════════════════════════════════════════════════
# C. Semantic Scholar
# ═══════════════════════════════════════════════════

class SemanticScholarAdapter(SourceAdapter):
    adapter_name = "semantic_scholar"
    adapter_version = "0.1.0"

    BASE = "https://api.semanticscholar.org/graph/v1"

    def discover(self, query: str, limit: int = 5) -> list[dict]:
        url = f"{self.BASE}/paper/search?query={query}&limit={limit}&fields=title,authors,year,externalIds,citationCount,openAccessPdf"
        r = _http_get(url)
        if r.status_code != 200:
            return []
        data = r.json()
        return [{
            "paper_id": item.get("paperId"),
            "title": item.get("title"),
            "year": item.get("year"),
            "authors": [a.get("name") for a in item.get("authors", [])],
            "citation_count": item.get("citationCount"),
            "open_access_url": item.get("openAccessPdf", {}).get("url") if item.get("openAccessPdf") else None,
        } for item in data.get("data", [])]

    def fetch(self, url: str, **kwargs) -> FetchResult:
        r = _http_get(url)
        return FetchResult(
            url=url, adapter=self.adapter_name, http_status=r.status_code,
            content_type="application/json", raw_bytes=r.content,
        )

    def fetch_paper(self, paper_id: str, fields: str = "title,authors,year,abstract,citationCount,references,externalIds,tldr") -> FetchResult:
        url = f"{self.BASE}/paper/{paper_id}?fields={fields}"
        return self.acquire(url)

    def fetch_citations(self, paper_id: str, limit: int = 10) -> FetchResult:
        url = f"{self.BASE}/paper/{paper_id}/citations?limit={limit}&fields=title,year,citationCount"
        return self.acquire(url)

    def fetch_references(self, paper_id: str, limit: int = 10) -> FetchResult:
        url = f"{self.BASE}/paper/{paper_id}/references?limit={limit}&fields=title,year,citationCount"
        return self.acquire(url)


# ═══════════════════════════════════════════════════
# D. GitHub
# ═══════════════════════════════════════════════════

class GitHubAdapter(SourceAdapter):
    adapter_name = "github"
    adapter_version = "0.1.0"

    BASE = "https://api.github.com"

    def discover_repo(self, query: str, per_page: int = 5) -> list[dict]:
        url = f"{self.BASE}/search/repositories?q={query}&per_page={per_page}"
        r = _http_get(url, headers={"Accept": "application/vnd.github+json"})
        if r.status_code != 200:
            return []
        data = r.json()
        return [{
            "full_name": item.get("full_name"),
            "description": item.get("description"),
            "stars": item.get("stargazers_count"),
            "language": item.get("language"),
            "license": item.get("license", {}).get("spdx_id") if item.get("license") else None,
            "url": item.get("html_url"),
            "default_branch": item.get("default_branch"),
        } for item in data.get("items", [])]

    def fetch(self, url: str, **kwargs) -> FetchResult:
        r = _http_get(url, headers={"Accept": "application/vnd.github+json"})
        etag = r.headers.get("ETag", "")
        return FetchResult(
            url=url, adapter=self.adapter_name, http_status=r.status_code,
            content_type="application/json", raw_bytes=r.content, etag=etag,
        )

    def fetch_repo(self, owner: str, repo: str) -> FetchResult:
        url = f"{self.BASE}/repos/{owner}/{repo}"
        return self.acquire(url)

    def fetch_releases(self, owner: str, repo: str, per_page: int = 5) -> FetchResult:
        url = f"{self.BASE}/repos/{owner}/{repo}/releases?per_page={per_page}"
        return self.acquire(url)

    def fetch_readme(self, owner: str, repo: str) -> FetchResult:
        """Fetch README content as raw markdown from raw.githubusercontent.com."""
        url = f"https://raw.githubusercontent.com/{owner}/{repo}/main/README.md"
        # Try main, then master
        r = _http_get(url)
        if r.status_code != 200:
            url = f"https://raw.githubusercontent.com/{owner}/{repo}/master/README.md"
            r = _http_get(url)
        return FetchResult(
            url=url, adapter=self.adapter_name, http_status=r.status_code,
            content_type="text/markdown", raw_bytes=r.content,
        )

    def change_token(self, last_snapshot: dict[str, Any]) -> str | None:
        return last_snapshot.get("etag")


# ═══════════════════════════════════════════════════
# E. Generic Web / Docs
# ═══════════════════════════════════════════════════

class GenericWebAdapter(SourceAdapter):
    adapter_name = "generic_web"
    adapter_version = "0.1.0"

    def fetch(self, url: str, **kwargs) -> FetchResult:
        r = _http_get(url)
        return FetchResult(
            url=url, adapter=self.adapter_name, http_status=r.status_code,
            content_type=r.headers.get("Content-Type", "text/html"),
            raw_bytes=r.content,
            etag=r.headers.get("ETag", ""),
            last_modified=r.headers.get("Last-Modified", ""),
        )

    def change_token(self, last_snapshot: dict[str, Any]) -> str | None:
        return last_snapshot.get("etag") or last_snapshot.get("last_modified")


# ── Adapter factory ──

ADAPTERS: dict[str, SourceAdapter] = {
    "crossref": CrossrefAdapter(),
    "openalex": OpenAlexAdapter(),
    "semantic_scholar": SemanticScholarAdapter(),
    "github": GitHubAdapter(),
    "generic_web": GenericWebAdapter(),
}


def get_adapter(name: str) -> SourceAdapter:
    return ADAPTERS.get(name, GenericWebAdapter())