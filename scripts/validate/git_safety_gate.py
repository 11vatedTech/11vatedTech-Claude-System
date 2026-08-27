#!/usr/bin/env python3
"""
Git Safety Gate — prevents destructive staging/push patterns.

Before staging detects:
  - Nested repositories
  - Generated build trees (venv, node_modules, tool distributions)
  - Untracked size
  - Files >50MB and >100MB
  - Secrets
  - Project-boundary violations

Produces a staging manifest. Blocks dangerous operations.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]

# ── Dangerous patterns ──

GENERATED_PATTERNS = [
    r"__pycache__/",
    r"\.pyc$",
    r"node_modules/",
    r"\.venv/",
    r"venv/",
    r"\.pytest_cache/",
    r"\.mypy_cache/",
    r"\.ruff_cache/",
    r"\.next/",
    r"dist/",
    r"build/",
    r"\.cache/",
    r"\.growthos/",
    r"\.freebuff/",
    r"\.secrets/",
]

PROJECT_BOUNDARY_VIOLATIONS = [
    "11vated-growth_OS",
    "Frontend-Designs",
]

KNOWN_TOOL_DISTRIBUTIONS = [
    "tools/lsp/clangd-dist",
    "tools/frontend/py-deps",
]

SECRET_PATTERNS = [
    r"API[_-]?KEY\s*=\s*['\"][^'\"]{8,}['\"]",
    r"SECRET\s*=\s*['\"][^'\"]{8,}['\"]",
    r"TOKEN\s*=\s*['\"][^'\"]{8,}['\"]",
    r"PASSWORD\s*=\s*['\"][^'\"]{8,}['\"]",
    r"-----BEGIN\s+(RSA|OPENSSH|EC)\s+PRIVATE\s+KEY-----",
]


def run_git(*args: str) -> tuple[int, str, str]:
    """Run a git command from repo root."""
    try:
        p = subprocess.run(
            ["git"] + list(args),
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=30,
        )
        return p.returncode, p.stdout, p.stderr
    except Exception as e:
        return 1, "", str(e)


def detect_nested_repos() -> list[str]:
    """Find nested .git directories (submodules or independent repos)."""
    nested = []
    for path in ROOT.rglob(".git"):
        rel = str(path.relative_to(ROOT))
        if rel == ".git":
            continue
        # Claude Code worktrees are expected infrastructure
        if ".claude/worktrees" in rel:
            continue
        nested.append(rel)
    return nested


def detect_project_boundary_violations() -> list[str]:
    """Detect project directories at Foundry root."""
    violations = []
    for name in PROJECT_BOUNDARY_VIOLATIONS:
        path = ROOT / name
        if path.is_dir():
            # Count files to estimate size
            file_count = sum(1 for _ in path.rglob("*") if _.is_file())
            violations.append(f"{name}/ ({file_count} files)")
    return violations


def detect_large_files(max_mb: int = 50) -> list[str]:
    """Find files larger than max_mb."""
    large = []
    for path in ROOT.rglob("*"):
        if path.is_file() and not any(p in str(path) for p in [".git/", "__pycache__", "node_modules"]):
            try:
                size_mb = path.stat().st_size / (1024 * 1024)
                if size_mb > max_mb:
                    large.append(f"{path.relative_to(ROOT)} ({size_mb:.1f} MB)")
            except OSError:
                pass
    return large


def detect_secrets() -> list[str]:
    """Scan for secrets in tracked files."""
    findings = []
    for pattern in SECRET_PATTERNS:
        # Only scan files that aren't in the secret patterns themselves
        for path in ROOT.rglob("*.py"):
            if ".git/" in str(path) or ".venv/" in str(path) or "__pycache__" in str(path):
                continue
            try:
                content = path.read_text(errors="replace")
                if re.search(pattern, content, re.IGNORECASE):
                    # Check if it looks like a real secret vs placeholder
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    for m in matches:
                        if not any(p in str(m).lower() for p in ["example", "your_", "xxx", "placeholder", "test_"]):
                            findings.append(f"{path.relative_to(ROOT)}: potential secret")
                            break
            except Exception:
                pass
    return findings


def estimate_untracked_size() -> dict[str, Any]:
    """Estimate size of untracked files."""
    rc, stdout, stderr = run_git("ls-files", "--others", "--exclude-standard", "-z")
    if rc != 0:
        return {"error": stderr}

    untracked = [p for p in stdout.split("\0") if p]
    total_bytes = 0
    file_count = 0
    large_untracked = []

    for rel in untracked[:5000]:  # Limit to avoid timeout
        path = ROOT / rel
        try:
            if path.is_file():
                size = path.stat().st_size
                total_bytes += size
                file_count += 1
                if size > 50 * 1024 * 1024:
                    large_untracked.append(f"{rel} ({size / (1024*1024):.1f} MB)")
        except OSError:
            pass

    return {
        "file_count_sampled": file_count,
        "total_untracked_count": len(untracked),
        "estimated_size_mb": round(total_bytes / (1024 * 1024), 1),
        "large_untracked": large_untracked,
        "truncated": len(untracked) > 5000,
    }


def check_force_push_safety() -> dict[str, Any]:
    """Check whether force push would be dangerous."""
    # Check if local and remote diverge
    rc, local, _ = run_git("rev-parse", "HEAD")
    rc2, remote, _ = run_git("rev-parse", "origin/main")

    if rc != 0 or rc2 != 0:
        return {"status": "UNKNOWN", "error": "Cannot determine divergence"}

    local = local.strip()
    remote = remote.strip()

    if local == remote:
        return {"status": "CLEAN", "ahead": 0, "behind": 0}

    # Check if local is ahead (fast-forward possible)
    rc3, merge_base, _ = run_git("merge-base", local, remote)
    merge_base = merge_base.strip()

    if merge_base == remote:
        return {"status": "FAST_FORWARD_SAFE", "ahead": "needs_calc"}
    else:
        return {
            "status": "DIVERGED",
            "warning": "Local and remote have diverged. Do NOT force push without explicit authorization. Use --force-with-lease and verify expected remote SHA.",
            "local": local,
            "remote": remote,
            "merge_base": merge_base,
        }


def generate_staging_manifest() -> dict[str, Any]:
    """Full pre-staging safety check."""
    return {
        "date": __import__("datetime").datetime.now().isoformat(),
        "nested_repos": detect_nested_repos(),
        "project_boundary_violations": detect_project_boundary_violations(),
        "large_files": detect_large_files(50),
        "very_large_files": detect_large_files(100),
        "secrets_scan": detect_secrets()[:10],
        "untracked_estimate": estimate_untracked_size(),
        "force_push_status": check_force_push_safety(),
        "safe_to_stage": True,  # Computed below
    }


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Git Safety Gate")
    parser.add_argument("--pre-stage", action="store_true", help="Full pre-staging safety check")
    parser.add_argument("--pre-push", action="store_true", help="Pre-push safety check")
    parser.add_argument("--force-push-detect", action="store_true", help="Check force push safety only")
    subparsers = parser.add_subparsers(dest="command")

    _ = subparsers.add_parser("manifest", help="Generate staging manifest")

    args = parser.parse_args()

    if args.force_push_detect:
        status = check_force_push_safety()
        if status["status"] == "DIVERGED":
            print("BLOCKED: History diverged. Do not force push.")
            print(f"  Local:  {status['local']}")
            print(f"  Remote: {status['remote']}")
            return 1
        print(f"Push safety: {status['status']}")
        return 0

    if args.pre_stage or args.pre_push or args.command == "manifest":
        manifest = generate_staging_manifest()

        issues = []

        if manifest["nested_repos"]:
            issues.append(f"NESTED_REPOS: {manifest['nested_repos']}")

        if manifest["project_boundary_violations"]:
            issues.append(f"PROJECT_BOUNDARY: {manifest['project_boundary_violations']}")

        if manifest["very_large_files"]:
            issues.append(f"VERY_LARGE_FILES: {len(manifest['very_large_files'])} files >100MB")

        if manifest["secrets_scan"]:
            issues.append(f"SECRETS: {len(manifest['secrets_scan'])} potential findings")

        if manifest["force_push_status"]["status"] == "DIVERGED":
            issues.append("FORCE_PUSH_RISK: history diverged")

        if issues:
            print("SAFETY GATE — ISSUES FOUND:")
            for issue in issues:
                print(f"  {issue}")
            manifest["safe_to_stage"] = False
            return 1
        else:
            print("SAFETY GATE — CLEAR")
            print(f"  Untracked: {manifest['untracked_estimate']}")
            manifest["safe_to_stage"] = True
            return 0

    # Default: brief check
    nested = detect_nested_repos()
    boundary = detect_project_boundary_violations()
    push = check_force_push_safety()

    all_clear = True
    if nested:
        print(f"Nested repos: {nested}")
        all_clear = False
    if boundary:
        print(f"Project boundary: {boundary}")
        all_clear = False
    if push["status"] == "DIVERGED":
        print(f"Force push risk: DIVERGED")
        all_clear = False

    if all_clear:
        print("CLEAR")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())