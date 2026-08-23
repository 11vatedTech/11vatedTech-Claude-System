"""GitHub portfolio evidence census (read-only, explicitly authorized).

Enumerates public repositories visible under founder-authorized GitHub profiles
and performs a lightweight first-pass evidence census: metadata presence,
source/test/build/runtime signals, and deterministic evidence-strength
classification. Repository existence is NOT capability proof; README claims are
NOT implementation proof; several repos describing the same system must not
multiply company capability breadth.

No repository is modified, cloned for mutation, or deep-analyzed here.
"""

from __future__ import annotations

import os
import re
from datetime import datetime
from typing import Any

import httpx

GITHUB_API = "https://api.github.com"

# The two explicitly founder-authorized read-only evidence scopes.
AUTHORIZED_PROFILES = ["11vatedTech", "11vated"]

_SOURCE_EXT = {
    ".py", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".rs", ".go", ".cs",
    ".cpp", ".cc", ".c", ".h", ".hpp", ".java", ".rb", ".php", ".swift", ".kt",
    ".gd", ".sh", ".sql", ".vue", ".svelte", ".dart", ".lua", ".ex", ".exs",
}
_LANG_BY_EXT = {
    ".py": "Python", ".ts": "TypeScript", ".tsx": "TypeScript/React",
    ".js": "JavaScript", ".jsx": "JavaScript/React", ".mjs": "JavaScript",
    ".cjs": "JavaScript", ".rs": "Rust", ".go": "Go", ".cs": "C#",
    ".cpp": "C++", ".cc": "C++", ".c": "C", ".h": "C/C++", ".hpp": "C++",
    ".java": "Java", ".rb": "Ruby", ".php": "PHP", ".swift": "Swift",
    ".kt": "Kotlin", ".gd": "GDScript", ".sh": "Shell", ".sql": "SQL",
    ".vue": "Vue", ".svelte": "Svelte", ".dart": "Dart", ".lua": "Lua",
    ".ex": "Elixir", ".exs": "Elixir",
}
_MANIFESTS = {
    "package.json", "pyproject.toml", "Cargo.toml", "go.mod", "pom.xml",
    "CMakeLists.txt", "Makefile", "build.gradle", "requirements.txt",
    "tsconfig.json", "vite.config.ts", "Dockerfile",
}
_README_NAMES = {"readme.md", "readme.rst", "readme.txt", "readme"}
# Files worth fetching for deep evidence (patterns, not exhaustive).
_DEEP_FILE_PATTERNS = [
    "readme.md", "readme.rst", "readme",
    "pyproject.toml", "package.json", "cargo.toml", "go.mod",
    "tsconfig.json", "vite.config.ts",
    "dockerfile", "docker-compose.yml", "docker-compose.yaml",
]
# Source directories to examine for deep evidence.
_DEEP_SOURCE_DIRS = ["src", "lib", "app", "core", "pkg", "cmd", "internal"]
# Test directories to examine.
_DEEP_TEST_DIRS = ["tests", "test", "spec", "__tests__"]
# Max file size to fetch (bytes) — skip giant vendored files.
_MAX_FILE_FETCH = 50_000
# Max files to fetch per repo for deep analysis.
_MAX_DEEP_FILES = 25


def _redact_token(text: str, token: str | None) -> str:
    """Remove any accidental token appearance from a string."""
    if not token:
        return text
    return text.replace(token, "***REDACTED***")


class GitHubHealthState:
    """Tracks GitHub API access health without leaking credentials."""
    AUTHENTICATED = "AUTHENTICATED"
    PUBLIC_ONLY = "PUBLIC_ONLY"
    RATE_LIMITED = "RATE_LIMITED"
    AUTH_ERROR = "AUTH_ERROR"
    UNKNOWN = "UNKNOWN"


class GitHubProfileClient:
    """Read-only official GitHub REST API client with graceful rate limiting.

    Supports authenticated (higher rate limit) and unauthenticated access.
    Credentials are never stored in PostgreSQL, evidence records, or logs.
    """

    def __init__(self, token: str | None = None) -> None:
        self.token = token or os.environ.get("GITHUB_TOKEN")
        self.rate_limited = False
        self.auth_error = False
        self.rate_remaining: int | None = None
        self.rate_reset: datetime | None = None
        self.health_state = GitHubHealthState.UNKNOWN
        self._request_count = 0
        self.headers: dict[str, str] = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "GrowthOS-CapabilityIntelligence/0.2 (public research)",
        }
        if self.token:
            self.headers["Authorization"] = f"Bearer {self.token}"

    def _update_health_from_response(self, resp: httpx.Response) -> None:
        """Derive health state from response headers. Never exposes the token."""
        remaining = resp.headers.get("x-ratelimit-remaining")
        reset_ts = resp.headers.get("x-ratelimit-reset")
        if remaining is not None:
            import contextlib
            with contextlib.suppress(ValueError):
                self.rate_remaining = int(remaining)
        if reset_ts is not None:
            import contextlib
            with contextlib.suppress(ValueError, OSError):
                self.rate_reset = datetime.fromtimestamp(int(reset_ts))
        if resp.status_code in (403, 429):
            self.rate_limited = True
            self.health_state = GitHubHealthState.RATE_LIMITED
        elif resp.status_code == 401:
            self.auth_error = True
            self.health_state = GitHubHealthState.AUTH_ERROR
        elif self.token and not self.auth_error and not self.rate_limited:
            self.health_state = GitHubHealthState.AUTHENTICATED
        elif not self.token and not self.rate_limited:
            self.health_state = GitHubHealthState.PUBLIC_ONLY

    async def _get(self, url: str) -> tuple[int, Any]:
        self._request_count += 1
        try:
            async with httpx.AsyncClient(timeout=30, headers=self.headers) as client:
                resp = await client.get(url)
        except httpx.HTTPError:
            return -1, None
        self._update_health_from_response(resp)
        if resp.status_code in {403, 429}:
            self.rate_limited = True
            return resp.status_code, None
        # 404 = not found; 409/422 = empty repo or missing branch (no tree yet).
        if resp.status_code in {404, 409, 422}:
            return resp.status_code, None
        if resp.status_code >= 400:
            return resp.status_code, None
        try:
            return resp.status_code, resp.json()
        except ValueError:
            return resp.status_code, None

    async def list_repos(self, login: str) -> tuple[str, list[dict[str, Any]]]:
        """List public repos for a user (or org) profile."""
        for base in ("users", "orgs"):
            status, data = await self._get(
                f"{GITHUB_API}/{base}/{login}/repos?per_page=100&sort=updated"
            )
            if status == 200 and isinstance(data, list):
                return base, data
            if status == 404:
                continue
            # rate limit or other error
            return base, []
        return "unknown", []

    async def get_tree(self, full_name: str, default_branch: str | None) -> list[str]:
        branch = default_branch or "main"
        status, data = await self._get(
            f"{GITHUB_API}/repos/{full_name}/git/trees/{branch}?recursive=1"
        )
        if status != 200 or not isinstance(data, dict):
            return []
        tree = data.get("tree") or []
        return [str(item.get("path") or "") for item in tree if item.get("path")]

    async def get_releases(self, full_name: str) -> bool:
        status, data = await self._get(
            f"{GITHUB_API}/repos/{full_name}/releases?per_page=1"
        )
        if status != 200:
            return False
        return isinstance(data, list) and len(data) > 0

    async def get_file_content(
        self, full_name: str, path: str, ref: str | None = None
    ) -> str | None:
        """Fetch a single file's decoded content from a repository.

        Returns None on failure or if the file is too large. Content is
        decoded from base64 by the GitHub API. Token is never logged.
        """
        params = f"?ref={ref}" if ref else ""
        status, data = await self._get(
            f"{GITHUB_API}/repos/{full_name}/contents/{path}{params}"
        )
        if status != 200 or not isinstance(data, dict):
            return None
        # The API returns decoded content for single-file fetches.
        content = data.get("content")
        if not content:
            return None
        # Respect size limits
        size = data.get("size", 0)
        if isinstance(size, int) and size > _MAX_FILE_FETCH:
            return None
        return content

    async def get_readme(self, full_name: str) -> str | None:
        """Fetch the README content for a repository."""
        status, data = await self._get(
            f"{GITHUB_API}/repos/{full_name}/readme"
        )
        if status != 200 or not isinstance(data, dict):
            return None
        content = data.get("content")
        size = data.get("size", 0)
        if not content:
            return None
        if isinstance(size, int) and size > _MAX_FILE_FETCH:
            return None
        return content

    def health_report(self) -> dict[str, Any]:
        """Return access health without exposing credentials."""
        return {
            "mode": self.health_state,
            "rate_remaining": self.rate_remaining,
            "rate_limited": self.rate_limited,
            "auth_error": self.auth_error,
            "request_count": self._request_count,
            "has_token": bool(self.token),
            # Never include: token, authorization header, token value
        }


# ---------------------------------------------------------------------------
# Pure census logic (no network)
# ---------------------------------------------------------------------------


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def classify_repository(
    meta: dict[str, Any],
    tree_paths: list[str],
    *,
    releases_present: bool = False,
) -> dict[str, Any]:
    """Lightweight first-pass evidence census from metadata + file tree."""
    name = str(meta.get("name") or "unknown")
    description = (meta.get("description") or "").strip()
    size_kb = int(meta.get("size") or 0)

    paths = [p.lower() for p in tree_paths]
    readme_present = any(p.rsplit("/", 1)[-1].startswith("readme") for p in paths)

    source_paths = [p for p in tree_paths if _is_source(p)]
    source_present = bool(source_paths)
    tests_present = any(
        ("test" in p or "spec" in p) and _is_source(p) for p in tree_paths
    )
    ci_build_present = any(
        ".github/workflows" in p
        or ".gitlab-ci" in p
        or "azure-pipelines" in p
        or p.endswith("jenkinsfile")
        or p.split("/")[-1] in _MANIFESTS
        for p in paths
    )
    architecture_docs_present = any(
        "docs" in p.split("/") or "architecture" in p or "openspec" in p or "adr" in p
        for p in paths
    )
    languages = sorted({_LANG_BY_EXT[ext] for p in tree_paths if (ext := _ext(p)) in _LANG_BY_EXT})

    # A repo with no meaningful content (only license/readme/gitignore).
    meaningful = [
        p for p in tree_paths
        if _is_source(p)
        or p.split("/")[-1] in _MANIFESTS
        or p.split("/")[-1].startswith("readme")
        or "docs" in p.split("/")
        or ".github/workflows" in p
    ]
    empty_or_minimal = len(meaningful) == 0 or (size_kb < 20 and not source_present)

    strength = _classify_strength(
        readme_present=readme_present,
        source_present=source_present,
        tests_present=tests_present,
        ci_build_present=ci_build_present,
        releases_present=releases_present,
        architecture_docs_present=architecture_docs_present,
        empty_or_minimal=empty_or_minimal,
    )

    return {
        "name": name,
        "full_name": str(meta.get("full_name") or name),
        "html_url": meta.get("html_url"),
        "description": description,
        "topics": list(meta.get("topics") or []),
        "visibility": str(meta.get("visibility") or "public"),
        "archived": bool(meta.get("archived")),
        "fork": bool(meta.get("fork")),
        "default_branch": meta.get("default_branch"),
        "primary_language": meta.get("language"),
        "languages": languages or ([str(meta["language"])] if meta.get("language") else []),
        "size_kb": size_kb,
        "stargazers": int(meta.get("stargazers_count") or 0),
        "readme_present": readme_present,
        "source_present": source_present,
        "tests_present": tests_present,
        "ci_build_present": ci_build_present,
        "releases_present": releases_present,
        "architecture_docs_present": architecture_docs_present,
        "empty_or_minimal": empty_or_minimal,
        "evidence_strength": strength,
        "pushed_at": meta.get("pushed_at"),
        "source_file_count": len(source_paths),
        "test_file_count": sum(1 for p in tree_paths if ("test" in p or "spec" in p) and _is_source(p)),
    }


def _ext(path: str) -> str:
    idx = path.rfind(".")
    return path[idx:] if idx > path.rfind("/") else ""


def _is_source(path: str) -> bool:
    return _ext(path).lower() in _SOURCE_EXT


def _classify_strength(
    *,
    readme_present: bool,
    source_present: bool,
    tests_present: bool,
    ci_build_present: bool,
    releases_present: bool,
    architecture_docs_present: bool,
    empty_or_minimal: bool,
) -> str:
    if empty_or_minimal or not source_present:
        return "DOCUMENTATION_ONLY" if readme_present or architecture_docs_present else "EMPTY_OR_MINIMAL"
    if tests_present and ci_build_present and releases_present:
        return "STRONG_CAPABILITY_EVIDENCE"
    if releases_present and (tests_present or ci_build_present):
        return "RUNTIME_EVIDENCE_PRESENT"
    if ci_build_present:
        return "BUILD_EVIDENCE_PRESENT"
    if tests_present:
        return "TEST_EVIDENCE_PRESENT"
    if source_present:
        return "IMPLEMENTATION_PRESENT" if readme_present else "EXPERIMENTAL"
    return "EMPTY_OR_MINIMAL"


def score_repository(classified: dict[str, Any]) -> tuple[float, dict[str, float]]:
    """Capability Evidence Value score (0..1) across independent dimensions."""
    src_count = int(classified.get("source_file_count") or 0)
    implementation_depth = min(1.0, 0.2 + 0.1 * min(src_count, 8)) if src_count else 0.0
    test_evidence = 1.0 if classified.get("tests_present") else 0.3 if classified.get("source_present") else 0.0
    build_runtime = (
        1.0 if classified.get("releases_present")
        else 0.7 if classified.get("ci_build_present")
        else 0.0
    )
    maturity = 0.0
    if not classified.get("archived"):
        maturity += 0.3
    if classified.get("readme_present"):
        maturity += 0.3
    if int(classified.get("stargazers") or 0) > 0:
        maturity += 0.2
    if classified.get("description"):
        maturity += 0.2
    commercial_distinctiveness = min(1.0, 0.3 + 0.1 * len(classified.get("topics") or []))
    reproducibility = 0.8 if (classified.get("tests_present") and classified.get("ci_build_present")) else 0.4 if classified.get("tests_present") else 0.15
    completeness = sum([
        bool(classified.get("readme_present")),
        bool(classified.get("source_present")),
        bool(classified.get("tests_present")),
        bool(classified.get("ci_build_present")),
        bool(classified.get("releases_present")),
        bool(classified.get("architecture_docs_present")),
    ]) / 6.0

    breakdown = {
        "implementation_depth": round(implementation_depth, 3),
        "test_evidence": round(test_evidence, 3),
        "build_runtime_evidence": round(build_runtime, 3),
        "project_maturity": round(min(1.0, maturity), 3),
        "commercial_distinctiveness": round(commercial_distinctiveness, 3),
        "reproducibility_potential": round(reproducibility, 3),
        "evidence_completeness": round(completeness, 3),
    }
    score = (
        0.25 * implementation_depth
        + 0.20 * test_evidence
        + 0.20 * build_runtime
        + 0.10 * min(1.0, maturity)
        + 0.10 * commercial_distinctiveness
        + 0.10 * reproducibility
        + 0.05 * completeness
    )
    return round(min(1.0, score), 3), breakdown


def repo_stem(name: str) -> str:
    """Return a repository's family root: its first non-version token.

    Variants of one technology (``GSPL``, ``GSPL_AI``, ``GSPL-Sprites``;
    ``Paradigm``, ``paradigm-sprites``) share the same leading token and
    therefore cluster into one family. Version tokens (``v2``, ``1.0``) are
    skipped so ``my-app`` and ``my-app-v2`` collapse together.
    """
    tokens = re.findall(r"[a-z0-9]+", name.lower())
    for token in tokens:
        if not re.match(r"^v?\d+(\.\d+)*$", token):
            return token
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or name.lower()


def cluster_families(repos: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Cluster repos into project families by name stem + shared topics.

    Deterministic and data-driven: families emerge from names/topics, not from
    a hardcoded list.
    """
    families: dict[str, dict[str, Any]] = {}
    for repo in repos:
        stem = repo_stem(str(repo.get("name") or ""))
        topics = {t.lower() for t in (repo.get("topics") or [])}
        matched_key: str | None = None
        for key, fam in families.items():
            fam_topics = fam["_topics"]
            if key == stem:
                matched_key = key
                break
            if topics and fam_topics and len(topics & fam_topics) >= 2:
                matched_key = key
                break
        if matched_key is None:
            matched_key = stem
            families[matched_key] = {
                "stem": stem,
                "members": [],
                "_topics": set(topics),
                "languages": set(),
            }
        families[matched_key]["members"].append(repo)
        families[matched_key]["_topics"] |= topics
        families[matched_key]["languages"] |= set(repo.get("languages") or [])
    return families


def _strength_rank(strength: str) -> int:
    order = [
        "EMPTY_OR_MINIMAL", "DOCUMENTATION_ONLY", "EXPERIMENTAL",
        "IMPLEMENTATION_PRESENT", "TEST_EVIDENCE_PRESENT",
        "BUILD_EVIDENCE_PRESENT", "RUNTIME_EVIDENCE_PRESENT",
        "STRONG_CAPABILITY_EVIDENCE",
    ]
    return order.index(strength) if strength in order else -1


def select_deep_analysis(
    repos: list[dict[str, Any]],
    families: dict[str, dict[str, Any]],
    *,
    max_count: int = 8,
) -> list[str]:
    """Select up to ``max_count`` repos maximizing evidence quality + diversity.

    Picks the best-scored repo per family first (to avoid picking many siblings
    of one system), then fills remaining slots with the highest-scored
    unselected repos.
    """
    selected: list[str] = []
    chosen: set[str] = set()

    family_ranked = sorted(
        families.values(),
        key=lambda f: -max((r["score"] for r in f["members"]), default=0.0),
    )
    for fam in family_ranked:
        if len(selected) >= max_count:
            break
        best = max(fam["members"], key=lambda r: r["score"])
        if best["full_name"] not in chosen:
            selected.append(best["full_name"])
            chosen.add(best["full_name"])

    remaining = sorted(
        (r for r in repos if r["full_name"] not in chosen),
        key=lambda r: -r["score"],
    )
    for repo in remaining:
        if len(selected) >= max_count:
            break
        selected.append(repo["full_name"])
        chosen.add(repo["full_name"])

    return selected


def family_overlap_note(members: list[dict[str, Any]]) -> str | None:
    if len(members) > 1:
        names = ", ".join(str(m.get("name")) for m in members)
        return (
            f"{len(members)} repositories appear to be the same technology "
            f"family ({names}); they count as ONE evidence family, not "
            f"{len(members)} independent capabilities."
        )
    return None


# ---------------------------------------------------------------------------
# Deep evidence file selection
# ---------------------------------------------------------------------------

def select_deep_files(tree_paths: list[str], *, max_files: int = _MAX_DEEP_FILES) -> list[str]:
    """Select files worth fetching for deep evidence analysis.

    Prioritizes README, config/manifest files, then source files in key
    directories, then test files. Skips vendored/generated/nodes_modules.
    """
    candidates: list[tuple[int, str]] = []
    seen: set[str] = set()

    def _add(priority: int, path: str) -> None:
        if path not in seen and path in tree_paths:
            candidates.append((priority, path))
            seen.add(path)

    # Priority 0: README
    for p in tree_paths:
        if p.split("/")[-1].lower() in _README_NAMES:
            _add(0, p)
            break

    # Priority 1: manifest/config files
    for p in tree_paths:
        basename = p.split("/")[-1].lower()
        if basename in {m.lower() for m in _MANIFESTS} or basename in {
            "dockerfile", "docker-compose.yml", "docker-compose.yaml",
            ".gitignore", "license", "license.md",
        }:
            _add(1, p)

    # Priority 2: source files in key directories
    for p in tree_paths:
        parts = p.split("/")
        if any(part.lower() in _DEEP_SOURCE_DIRS for part in parts[:-1]) and _is_source(p):
            _add(2, p)

    # Priority 3: test files
    for p in tree_paths:
        parts = p.split("/")
        if any(part.lower() in _DEEP_TEST_DIRS for part in parts[:-1]) and _is_source(p):
            _add(3, p)

    # Priority 4: other source files
    for p in tree_paths:
        if _is_source(p) and p not in seen:
            _add(4, p)

    candidates.sort(key=lambda x: (x[0], x[1]))
    return [path for _, path in candidates[:max_files]]
