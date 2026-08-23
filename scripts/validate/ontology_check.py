#!/usr/bin/env python3
"""Validate the capability ontology: every declared provider must resolve to a
real skill, agent, script, template, tool, or 9Router endpoint, and every
evidence pointer must exist. Also prints the L0-L5 maturity baseline.

This is the "evidence, not claims" gate for the Foundry ontology. A maturity
claim with no resolvable provider or missing evidence fails the check.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ONTOLOGY = ROOT / "config" / "capability-ontology.json"

# tools whose absence is a documented degraded state, not an error
DEGRADED_OK = {"whisper", "piper", "comfyui", "krita", "gimp", "kdenlive", "audacity"}


def tool_resolvable(name: str) -> bool:
    sys.path.insert(0, str(ROOT / "scripts" / "media"))
    from vtmedia.common import resolve_tool  # type: ignore

    return resolve_tool(name) is not None


def endpoint_resolvable(name: str) -> bool:
    """9Router endpoints: resolvable if the gateway answers (count may be 0)."""
    import urllib.request

    try:
        with urllib.request.urlopen("http://127.0.0.1:20128" + name, timeout=5) as r:
            data = json.loads(r.read().decode("utf-8", "replace"))
        return isinstance(data, dict) and "data" in data
    except Exception:
        return False


def resolve(kind: str, name: str) -> tuple[bool, str]:
    if kind == "skill":
        return (ROOT / "plugin" / "skills" / name / "SKILL.md").exists(), f"plugin/skills/{name}/SKILL.md"
    if kind == "agent":
        return (ROOT / "plugin" / "agents" / f"{name}.md").exists(), f"plugin/agents/{name}.md"
    if kind == "script":
        p = ROOT / name
        return p.exists(), name
    if kind == "template":
        return (ROOT / name).exists(), name
    if kind == "config":
        return (ROOT / name).exists(), name
    if kind == "tool":
        if name in DEGRADED_OK:
            return True, f"tool {name} (degraded-ok)"
        return tool_resolvable(name), f"tool {name}"
    if kind == "tool-degraded":
        return True, f"tool {name} (documented degraded)"
    if kind == "9router-endpoint":
        return endpoint_resolvable(name), f"9router {name}"
    return False, f"unknown kind {kind}"


def main() -> int:
    data = json.loads(ONTOLOGY.read_text(encoding="utf-8"))
    failures: list[str] = []
    stats: dict[str, int] = {}
    resolved = 0
    total = 0
    for domain in data["domains"]:
        for cap in domain["capabilities"]:
            total += 1
            stats[cap["maturity"]] = stats.get(cap["maturity"], 0) + 1
            for ev in cap.get("evidence", []):
                if not (ROOT / ev).exists():
                    failures.append(f"missing_evidence {domain['id']}/{cap['id']}: {ev}")
            for prov in cap["providers"]:
                ok, where = resolve(prov["kind"], prov["name"])
                resolved += ok
                if not ok:
                    failures.append(f"unresolved_provider {domain['id']}/{cap['id']}: {where}")

    print(f"ontology_domains={len(data['domains'])}")
    print(f"ontology_capabilities={total}")
    print(f"providers_resolved={resolved}")
    print("maturity_baseline=" + json.dumps(dict(sorted(stats.items())), separators=(",", ":")))
    print(f"ontology_failures={len(failures)}")
    for f in failures:
        print("FAIL", f)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
