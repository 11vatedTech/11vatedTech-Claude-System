#!/usr/bin/env python3
"""Validate the global ~/.claude 11vatedTech installation without exposing secrets.

This is the canonical source for the installed
~/.claude/11vatedtech/capability-system/scripts/validate-capabilities.py
(synced by scripts/install/sync_to_claude.py).

Expectations are derived from the canonical repo when it is present, so the
check never drifts from the source of truth.
"""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SKILL_ROOT = Path.home() / ".claude" / "skills"
AGENT_ROOT = Path.home() / ".claude" / "agents"
SETTINGS = Path.home() / ".claude" / "settings.json"

SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_\-]{8,}"),
    re.compile(r"ghp_[A-Za-z0-9_]+"),
    re.compile(r"github_pat_[A-Za-z0-9_]+"),
    re.compile(r"ANTHROPIC_API_KEY\s*=\s*['\"][^'\"]+"),
]


def expected_skills() -> list[str]:
    p = REPO / "plugin" / "skills"
    if p.exists():
        return sorted(d.name for d in p.iterdir() if d.is_dir() and (d / "SKILL.md").exists())
    return [
        "11vt-core-operating-system", "11vt-research-intelligence",
        "11vt-architecture-engineering", "11vt-production-engineering",
        "11vt-language-workflows", "11vt-ai-ml-local-inference",
        "11vt-game-development", "11vt-design-director", "11vt-creative-production",
        "11vt-repository-auditor", "11vt-testing-verification",
        "11vt-performance-security", "11vt-documentation-canon",
        "11vt-9router-orchestrator", "11vt-skill-foundry", "11vt-capability-entrypoint",
        "11vt-status", "11vt-project-bootstrap", "11vt-product-lifecycle",
        "11vt-release-engineering", "9router", "9router-chat", "9router-image",
        "9router-tts", "9router-embeddings", "9router-web-search",
        "9router-web-fetch", "9router-stt", "9router-video",
    ]


def expected_agents() -> list[str]:
    p = REPO / "plugin" / "agents"
    if p.exists():
        return sorted(f.stem for f in p.glob("*.md"))
    return [
        "11vt-independent-reviewer", "11vt-creative-director", "11vt-art-director",
        "11vt-experience-designer", "11vt-motion-director", "11vt-technical-artist",
        "11vt-asset-director", "11vt-visual-qa-director",
    ]


def load_settings() -> dict:
    try:
        return json.loads(SETTINGS.read_text(encoding="utf-8"))
    except Exception:
        return {}


def check_skills() -> bool:
    ok = True
    expected = expected_skills()
    for name in expected:
        path = SKILL_ROOT / name / "SKILL.md"
        if not path.exists():
            print(f"missing_skill {name}")
            ok = False
            continue
        text = path.read_text(encoding="utf-8")
        fm = re.match(r"^---\n(.*?)\n---\n", text, re.S)
        if not fm:
            print(f"missing_frontmatter {name}")
            ok = False
            continue
        declared = None
        desc = None
        for line in fm.group(1).splitlines():
            if line.startswith("name:"):
                declared = line.split(":", 1)[1].strip()
            if line.startswith("description:"):
                desc = line.split(":", 1)[1].strip()
        if declared != name:
            print(f"name_mismatch {name} declared={declared}")
            ok = False
        if not desc or len(desc) < 40:
            print(f"weak_description {name}")
            ok = False
    print(f"skills_expected={len(expected)} ok={ok}")
    return ok


def check_agents() -> bool:
    ok = True
    expected = expected_agents()
    for name in expected:
        path = AGENT_ROOT / f"{name}.md"
        if not path.exists():
            print(f"missing_agent {name}")
            ok = False
            continue
        text = path.read_text(encoding="utf-8")
        fm = re.match(r"^---\n(.*?)\n---\n", text, re.S)
        if not fm:
            print(f"missing_agent_frontmatter {name}")
            ok = False
            continue
        if f"name: {name}" not in fm.group(1):
            print(f"agent_name_mismatch {name}")
            ok = False
        if "description:" not in fm.group(1):
            print(f"agent_weak_description {name}")
            ok = False
    print(f"agents_expected={len(expected)} ok={ok}")
    return ok


def check_entrypoint_pointer() -> bool:
    claude_md = Path.home() / ".claude" / "CLAUDE.md"
    if not claude_md.exists():
        print("claude_md_pointer MISSING")
        return False
    text = claude_md.read_text(encoding="utf-8")
    ok = "11vt-capability-entrypoint" in text
    print(f"claude_md_pointer ok={ok}")
    return ok


def scan_secrets() -> bool:
    ok = True
    for root in (SKILL_ROOT, AGENT_ROOT):
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            for pattern in SECRET_PATTERNS:
                if pattern.search(text):
                    print(f"possible_secret {path}")
                    ok = False
    print(f"secret_scan_ok={ok}")
    return ok


def get_base_and_token() -> tuple[str, str]:
    settings = load_settings()
    env = settings.get("env", {}) if isinstance(settings, dict) else {}
    base = os.environ.get("NINEROUTER_URL") or env.get("ANTHROPIC_BASE_URL", "http://127.0.0.1:20128/v1")
    base = base.removesuffix("/v1")
    token = os.environ.get("NINEROUTER_KEY") or env.get("ANTHROPIC_AUTH_TOKEN", "")
    return base, token


def fetch_json(url: str, token: str = "", data: dict | None = None, timeout: int = 15) -> dict:
    body = None if data is None else json.dumps(data).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    req = urllib.request.Request(url, data=body, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8", "replace"))


def check_9router(smoke_chat: bool = True) -> bool:
    base, token = get_base_and_token()
    ok = True
    try:
        health = fetch_json(base + "/api/health")
        print("9router_health=" + json.dumps(health, separators=(",", ":")))
    except Exception as exc:
        print(f"9router_health_error {type(exc).__name__}: {exc}")
        return False

    for path in ["/v1/models", "/v1/models/image", "/v1/models/tts", "/v1/models/embedding", "/v1/models/web", "/v1/models/stt", "/v1/models/image-to-text"]:
        try:
            data = fetch_json(base + path, token=token)
            print(f"9router_discovery {path} count={len(data.get('data', []))}")
        except Exception as exc:
            print(f"9router_discovery_error {path} {type(exc).__name__}: {exc}")
            ok = False

    if smoke_chat and token:
        try:
            data = fetch_json(base + "/v1/chat/completions", token=token, data={
                "model": "11",
                "messages": [{"role": "user", "content": "Reply with exactly: ok"}],
                "max_tokens": 5,
                "stream": False,
            }, timeout=30)
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            print(f"9router_chat_smoke len={len(content)} sample={content[:20]!r}")
        except Exception as exc:
            print(f"9router_chat_smoke_error {type(exc).__name__}: {exc}")
            ok = False
    else:
        print("9router_chat_smoke_skipped")
    return ok


def main() -> int:
    import argparse
    p = argparse.ArgumentParser(prog="validate_capability_installation")
    p.add_argument("--no-chat-smoke", action="store_true", help="skip the 9Router chat smoke test")
    args = p.parse_args()
    ok = True
    ok &= check_skills()
    ok &= check_agents()
    ok &= check_entrypoint_pointer()
    ok &= scan_secrets()
    ok &= check_9router(smoke_chat=not args.no_chat_smoke)
    print(f"overall_ok={ok}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
