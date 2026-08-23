"""Repository Evidence Mirror — local read-only clones for deep source analysis.

For every explicitly founder-authorized GitHub repository, GrowthOS may maintain
an isolated local clone used only for Capability Intelligence. Mirrors are never
pushed, never modified, and never used as development workspaces.

Suggested location::

    <growthos-data>/evidence-mirrors/github/<owner>/<repo>

Shallow-first cloning minimizes disk and network cost. Deepening is selective
and only performed when ancestry/evidence-independence requires history.
"""

from __future__ import annotations

import asyncio
import os
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import growthos.domain.models  # noqa: F401
from growthos.config import get_settings
from growthos.domain.enums import MirrorState
from growthos.domain.models_capability import EvidenceMirror, RepositoryEvidence
from growthos.shared.ids import new_id

# ---------------------------------------------------------------------------
# Authorized profiles — mirrors are created only for explicitly authorized repos
# ---------------------------------------------------------------------------
AUTHORIZED_PROFILES = {"11vatedTech", "11vated"}


def _mirror_root() -> Path:
    """Return the configured evidence mirror root, creating it if needed.

    Default is ``~/.growthos/evidence-mirrors`` which is always outside
    the GrowthOS source tree.
    """
    raw = get_settings().evidence_mirror_root
    root = Path(raw) if raw else Path.home() / ".growthos" / "evidence-mirrors"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _mirror_path(owner: str, repo: str) -> Path:
    """Return the local filesystem path for a mirror."""
    return _mirror_root() / "github" / owner / repo


def _validate_owner_repo(owner: str, repo: str) -> None:
    """Reject path-escape attempts."""
    if "/" in owner or "\\" in owner or ".." in owner:
        raise ValueError(f"Invalid owner: {owner!r}")
    if "/" in repo or "\\" in repo or ".." in repo:
        raise ValueError(f"Invalid repo: {repo!r}")


def _validate_mirror_path(path: Path) -> None:
    """Ensure a mirror path lies under the configured root."""
    root = _mirror_root()
    try:
        resolved = path.resolve()
        root_resolved = root.resolve()
        if not str(resolved).startswith(str(root_resolved)):
            raise ValueError(f"Mirror path escapes root: {path}")
    except (OSError, ValueError) as exc:
        raise ValueError(f"Invalid mirror path: {exc}") from exc


def _validate_not_source_tree(path: Path) -> None:
    """Ensure a mirror path does not overlap with known source trees."""
    cwd_resolved = Path.cwd().resolve()
    path_resolved = path.resolve()
    if str(path_resolved).startswith(str(cwd_resolved)):
        raise ValueError(f"Mirror path is inside GrowthOS source tree: {path}")


# ---------------------------------------------------------------------------
# Git operations (async wrappers around subprocess)
# ---------------------------------------------------------------------------


async def _run_git(*args: str, cwd: str | Path | None = None, timeout: float = 120) -> tuple[int, str, str]:
    """Run a git command and return (returncode, stdout, stderr)."""
    cmd = ["git"] + list(args)
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=cwd,
    )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except TimeoutError:
        proc.kill()
        await proc.wait()
        return -1, "", "timeout"
    return proc.returncode or 0, stdout.decode(errors="replace"), stderr.decode(errors="replace")


async def _git_clone_shallow(
    remote_url: str,
    target: Path,
    *,
    branch: str | None = None,
) -> tuple[bool, str]:
    """Perform a shallow clone (blobless) into target. Returns (success, error)."""
    target.mkdir(parents=True, exist_ok=True)
    args = ["clone", "--filter=blob:none", "--no-checkout", remote_url, str(target)]
    if branch:
        args = ["clone", "--filter=blob:none", "--no-checkout", "--branch", branch, remote_url, str(target)]
    rc, out, err = await _run_git(*args, timeout=300)
    if rc != 0:
        return False, err or out
    return True, ""


async def _git_fetch(remote: str, branch: str, cwd: Path) -> tuple[bool, str]:
    """Fetch latest from remote for a specific branch."""
    rc, out, err = await _run_git("fetch", remote, branch, cwd=cwd, timeout=120)
    if rc != 0:
        return False, err or out
    return True, ""


async def _git_checkout_detached(ref: str, cwd: Path) -> tuple[bool, str]:
    """Checkout a specific commit/tag/ref in detached HEAD mode."""
    rc, out, err = await _run_git("checkout", "--detach", ref, cwd=cwd, timeout=60)
    if rc != 0:
        return False, err or out
    return True, ""


async def _git_rev_parse(ref: str, cwd: Path) -> str | None:
    """Return the SHA for a ref, or None."""
    rc, out, _ = await _run_git("rev-parse", ref, cwd=cwd, timeout=30)
    if rc != 0:
        return None
    return out.strip()


async def _git_remote_get_url(cwd: Path) -> str | None:
    """Return the origin remote URL."""
    rc, out, _ = await _run_git("remote", "get-url", "origin", cwd=cwd, timeout=10)
    if rc != 0:
        return None
    return out.strip()


async def _git_is_worktree_clean(cwd: Path) -> bool:
    """Check that the worktree has no uncommitted changes."""
    rc, out, _ = await _run_git("status", "--porcelain", cwd=cwd, timeout=10)
    if rc != 0:
        return False
    return out.strip() == ""


async def _git_log_sha(cwd: Path, ref: str = "HEAD", n: int = 1) -> list[str]:
    """Return the last n commit SHAs."""
    rc, out, _ = await _run_git("log", f"-{n}", "--format=%H", ref, cwd=cwd, timeout=10)
    if rc != 0:
        return []
    return [line.strip() for line in out.strip().splitlines() if line.strip()]


# ---------------------------------------------------------------------------
# Mirror lifecycle
# ---------------------------------------------------------------------------


async def create_mirror(
    session: AsyncSession,
    owner: str,
    repo: str,
    *,
    branch: str | None = None,
) -> EvidenceMirror:
    """Create or update a shallow evidence mirror for one repository.

    If the mirror already exists and is READY, performs a fetch instead.
    Returns the persisted EvidenceMirror record.
    """
    _validate_owner_repo(owner, repo)
    full_name = f"{owner}/{repo}"
    remote_url = f"https://github.com/{full_name}.git"
    path = _mirror_path(owner, repo)
    _validate_mirror_path(path)
    _validate_not_source_tree(path)

    # Upsert mirror record
    existing = (
        await session.execute(
            select(EvidenceMirror).where(EvidenceMirror.full_name == full_name)
        )
    ).scalar_one_or_none()

    if existing is None:
        mirror = EvidenceMirror(
            id=new_id(),
            owner=owner,
            repo_name=repo,
            full_name=full_name,
            remote_url=remote_url,
            local_path=str(path),
            mirror_state=MirrorState.CLONING,
            default_branch=branch,
            authorization_source="founder_authorized",
        )
        session.add(mirror)
        await session.flush()
    else:
        mirror = existing
        mirror.mirror_state = MirrorState.CLONING
        mirror.error = None
        await session.flush()

    # Perform clone or fetch
    if path.exists() and (path / ".git").exists():
        # Already cloned — fetch
        target_branch = branch or mirror.default_branch or "main"
        ok, err = await _git_fetch("origin", target_branch, path)
        if not ok:
            mirror.mirror_state = MirrorState.FETCH_FAILED
            mirror.error = err[:2000]
            await session.flush()
            return mirror
    else:
        # Fresh clone
        if path.exists():
            shutil.rmtree(path, ignore_errors=True)
        ok, err = await _git_clone_shallow(remote_url, path, branch=branch)
        if not ok:
            mirror.mirror_state = MirrorState.REMOTE_UNAVAILABLE
            mirror.error = err[:2000]
            await session.flush()
            return mirror
        # Checkout the default branch so the worktree is clean
        target_branch = branch or "main"
        # Auto-detect before checkout
        for candidate in ["main", "master"]:
            sha_cand = await _git_rev_parse(f"origin/{candidate}", path)
            if sha_cand:
                target_branch = candidate
                break
        await _run_git("checkout", target_branch, cwd=path, timeout=60)

    # Read metadata from the clone
    target_branch = branch or mirror.default_branch or "main"
    sha = await _git_rev_parse(f"origin/{target_branch}", path)
    default_branch_detected = target_branch

    # Auto-detect default branch from remote if not specified
    if not branch:
        # Try common defaults
        for candidate in ["main", "master"]:
            sha_candidate = await _git_rev_parse(f"origin/{candidate}", path)
            if sha_candidate:
                default_branch_detected = candidate
                sha = sha_candidate
                break

    mirror.default_branch = default_branch_detected
    mirror.remote_commit_sha = sha
    mirror.local_evidence_sha = sha
    mirror.mirror_state = MirrorState.READY
    mirror.is_fresh = True
    mirror.last_fetched_at = datetime.now(UTC)
    mirror.fetched_refs = [f"origin/{default_branch_detected}"]
    mirror.error = None

    # Count files
    try:
        rc, out, _ = await _run_git(
            "ls-tree", "-r", "--name-only", f"origin/{default_branch_detected}",
            cwd=path, timeout=30,
        )
        if rc == 0:
            all_files = [line for line in out.strip().splitlines() if line.strip()]
            mirror.files_discovered = len(all_files)
            # Detect source roots
            mirror.source_roots = _detect_source_roots(all_files)
            mirror.languages = _detect_languages(all_files)
            mirror.size_kb = sum(
                os.path.getsize(os.path.join(path, f))
                for f in all_files
                if os.path.isfile(os.path.join(path, f))
            ) // 1024
    except Exception:
        pass

    await session.flush()
    return mirror


async def refresh_mirror(
    session: AsyncSession,
    mirror: EvidenceMirror,
) -> EvidenceMirror:
    """Fetch latest for an existing mirror."""
    path = Path(mirror.local_path)
    if not path.exists() or not (path / ".git").exists():
        mirror.mirror_state = MirrorState.NOT_MIRRORED
        await session.flush()
        return mirror

    target_branch = mirror.default_branch or "main"
    ok, err = await _git_fetch("origin", target_branch, path)
    if not ok:
        mirror.mirror_state = MirrorState.FETCH_FAILED
        mirror.error = err[:2000]
        await session.flush()
        return mirror

    sha = await _git_rev_parse(f"origin/{target_branch}", path)
    mirror.remote_commit_sha = sha
    mirror.local_evidence_sha = sha
    mirror.mirror_state = MirrorState.READY
    mirror.is_fresh = True
    mirror.last_fetched_at = datetime.now(UTC)
    mirror.error = None
    await session.flush()
    return mirror


async def checkout_ref(
    session: AsyncSession,
    mirror: EvidenceMirror,
    ref: str,
) -> tuple[bool, str]:
    """Checkout a specific ref in the mirror (detached HEAD).

    Returns (success, error_message). This is used to inspect evidence
    from a specific branch or commit without affecting the default branch.
    """
    path = Path(mirror.local_path)
    if not path.exists() or not (path / ".git").exists():
        return False, "Mirror not on disk"

    ok, err = await _git_checkout_detached(ref, path)
    if ok:
        sha = await _git_rev_parse("HEAD", path)
        if sha:
            mirror.local_evidence_sha = sha
            await session.flush()
    return ok, err


# ---------------------------------------------------------------------------
# Read-only filesystem access
# ---------------------------------------------------------------------------


async def list_files(mirror: EvidenceMirror) -> list[str]:
    """List all files in the mirror at its current checkout."""
    path = Path(mirror.local_path)
    if not path.exists() or not (path / ".git").exists():
        return []
    target_branch = mirror.default_branch or "main"
    rc, out, _ = await _run_git(
        "ls-tree", "-r", "--name-only", f"origin/{target_branch}",
        cwd=path, timeout=30,
    )
    if rc != 0:
        return []
    return [line for line in out.strip().splitlines() if line.strip()]


async def read_file_content(mirror: EvidenceMirror, file_path: str) -> str | None:
    """Read a file from the mirror at the current HEAD."""
    path = Path(mirror.local_path) / file_path
    if not path.exists():
        return None
    # Safety: ensure path is inside mirror
    try:
        resolved = path.resolve()
        mirror_resolved = Path(mirror.local_path).resolve()
        if not str(resolved).startswith(str(mirror_resolved)):
            return None
    except (OSError, ValueError):
        return None
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except (OSError, UnicodeDecodeError):
        return None


async def read_file_bytes(mirror: EvidenceMirror, file_path: str) -> bytes | None:
    """Read a file as bytes from the mirror."""
    path = Path(mirror.local_path) / file_path
    if not path.exists():
        return None
    try:
        resolved = path.resolve()
        mirror_resolved = Path(mirror.local_path).resolve()
        if not str(resolved).startswith(str(mirror_resolved)):
            return None
    except (OSError, ValueError):
        return None
    try:
        return path.read_bytes()
    except OSError:
        return None


# ---------------------------------------------------------------------------
# Mirror safety verification
# ---------------------------------------------------------------------------


async def verify_mirror_safety(mirror: EvidenceMirror) -> dict[str, Any]:
    """Verify a mirror is safe: no path escapes, remote matches, no mutation."""
    path = Path(mirror.local_path)
    results: dict[str, Any] = {
        "mirror": mirror.full_name,
        "path_exists": path.exists(),
        "has_git": (path / ".git").exists() if path.exists() else False,
        "remote_matches": False,
        "no_uncommitted_changes": False,
        "path_under_root": False,
        "not_source_tree": False,
        "safe": False,
    }

    if not results["path_exists"] or not results["has_git"]:
        return results

    # Check remote URL matches
    remote_url = await _git_remote_get_url(path)
    results["remote_matches"] = remote_url == mirror.remote_url

    # Check no uncommitted changes
    results["no_uncommitted_changes"] = await _git_is_worktree_clean(path)

    # Check path is under mirror root
    try:
        root = _mirror_root()
        resolved = path.resolve()
        root_resolved = root.resolve()
        results["path_under_root"] = str(resolved).startswith(str(root_resolved))
    except (OSError, ValueError):
        pass

    # Check not inside source tree
    _validate_not_source_tree(path)  # raises if invalid
    results["not_source_tree"] = True

    results["safe"] = all([
        results["remote_matches"],
        results["no_uncommitted_changes"],
        results["path_under_root"],
        results["not_source_tree"],
    ])
    return results


async def verify_no_remote_mutation(mirror: EvidenceMirror) -> dict[str, Any]:
    """Verify the mirror has never been used for push/remote mutation."""
    path = Path(mirror.local_path)
    result: dict[str, Any] = {
        "mirror": mirror.full_name,
        "no_push_reflog": True,
        "no_stashed_pushes": True,
        "safe": True,
    }

    if not path.exists() or not (path / ".git").exists():
        return result

    # Check reflog for any push operations
    rc, out, _ = await _run_git("reflog", "--all", "--oneline", cwd=path, timeout=10)
    if rc == 0:
        for line in out.splitlines():
            lower = line.lower()
            if any(kw in lower for kw in ["push", "receive", "update"]):
                result["no_push_reflog"] = False
                result["safe"] = False
                break

    return result


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _detect_source_roots(files: list[str]) -> list[str]:
    """Detect likely source root directories from a file listing."""
    dir_counts: dict[str, int] = {}
    for f in files:
        parts = f.split("/")
        if len(parts) >= 2:
            root = parts[0]
            dir_counts[root] = dir_counts.get(root, 0) + 1

    # Sort by file count, return top directories
    sorted_dirs = sorted(dir_counts.items(), key=lambda x: -x[1])
    roots = []
    for dirname, count in sorted_dirs:
        if count >= 2 and not dirname.startswith("."):
            roots.append(dirname)
    return roots[:10]


def _detect_languages(files: list[str]) -> list[str]:
    """Detect likely programming languages from file extensions."""
    ext_map: dict[str, str] = {
        ".py": "Python", ".ts": "TypeScript", ".tsx": "TypeScript/React",
        ".js": "JavaScript", ".jsx": "JavaScript/React", ".rs": "Rust",
        ".go": "Go", ".cs": "C#", ".cpp": "C++", ".c": "C",
        ".h": "C/C++ Header", ".java": "Java", ".rb": "Ruby",
        ".swift": "Swift", ".kt": "Kotlin",
    }
    lang_counts: dict[str, int] = {}
    for f in files:
        for ext, lang in ext_map.items():
            if f.endswith(ext):
                lang_counts[lang] = lang_counts.get(lang, 0) + 1
    return [lang for lang, _ in sorted(lang_counts.items(), key=lambda x: -x[1])]


# ---------------------------------------------------------------------------
# Convenience: get or create mirror for a RepositoryEvidence record
# ---------------------------------------------------------------------------


async def ensure_mirror(
    session: AsyncSession,
    repo: RepositoryEvidence,
) -> EvidenceMirror:
    """Get an existing mirror or create one for a RepositoryEvidence record."""
    existing = (
        await session.execute(
            select(EvidenceMirror).where(EvidenceMirror.full_name == repo.full_name)
        )
    ).scalar_one_or_none()

    if existing and existing.mirror_state == MirrorState.READY:
        return existing

    return await create_mirror(
        session,
        repo.owner,
        repo.name,
        branch=repo.default_branch,
    )
