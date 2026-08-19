#!/usr/bin/env python3
"""Routing behavior evaluation (replaces the shallow name-existence check).

The capability entrypoint is the routing behavior of the system: it maps
Founder intent to the minimum sufficient skills/agents. This evaluation
verifies three properties that the old check never looked at:

1. ROUTING COVERAGE  — every skill an intent-trigger case expects must be
   reachable through the entrypoint's declared routing (no oracle/routing
   drift). A trigger case expecting a skill the entrypoint never routes to is
   a routing regression.
2. NO OVERTRIGGER    — every skill an intent-trigger case says should NOT
   fire must be outside the declared route for that intent.
3. NO DANGLING ROUTE — every capability the entrypoint routes to must exist
   as a real skill or agent in the plugin.

The rubric below mirrors the entrypoint's "Default routing" and
"Creative-production routing ladder". Keep the two in agreement: changing
one without the other fails the evaluation.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENTRYPOINT = ROOT / "plugin" / "skills" / "11vt-capability-entrypoint" / "SKILL.md"
CASES_FILE = ROOT / "evaluations" / "trigger" / "core-skill-trigger-cases.json"
SKILLS_DIR = ROOT / "plugin" / "skills"
AGENTS_DIR = ROOT / "plugin" / "agents"

# intent category -> (keyword regexes, expected capabilities)
# Mirrors plugin/skills/11vt-capability-entrypoint/SKILL.md routing sections.
RUBRIC: list[tuple[str, list[str], list[str]]] = [
    (
        "repo_continuation",
        [r"continue", r"resume", r"determine next work"],
        ["11vt-status", "11vt-product-lifecycle", "11vt-project-bootstrap"],
    ),
    (
        "bootstrap",
        [r"bootstrap", r"retrofit"],
        ["11vt-project-bootstrap"],
    ),
    (
        "release",
        [r"release", r"release candidate", r"artifacts", r"ship"],
        ["11vt-release-engineering"],
    ),
    (
        "independent_review",
        [r"independently", r"before merge", r"independent review", r"review this diff", r"handoff"],
        ["11vt-independent-reviewer"],
    ),
    (
        "creative_visual",
        [r"premium", r"high-fidelity", r"cinematic", r"webgl", r"motion", r"assets", r"art direction", r"animation", r"vfx", r"visual polish", r"screenshot", r"look"],
        ["11vt-creative-production", "11vt-design-director"],
    ),
    (
        "game",
        [r"game"],
        ["11vt-game-development"],
    ),
]


def load_cases() -> list[dict]:
    data = json.loads(CASES_FILE.read_text(encoding="utf-8"))
    return data["cases"]


def entrypoint_text() -> str:
    return ENTRYPOINT.read_text(encoding="utf-8")


def route_for_prompt(prompt: str) -> set[str]:
    """Union of rubric skills for every intent category the prompt matches."""
    low = prompt.lower()
    out: set[str] = set()
    for _name, patterns, skills in RUBRIC:
        if any(re.search(p, low) for p in patterns):
            out.update(skills)
    return out


def referenced_capabilities(text: str) -> set[str]:
    """Backticked 11vt-*/9router names mentioned in the entrypoint."""
    names = set(re.findall(r"`((?:11vt|9router)[a-z0-9-]*)`", text))
    # also catch the independent reviewer referenced without backticks in prose
    names.update(re.findall(r"\b(11vt-independent-reviewer)\b", text))
    return names


def exists(cap: str) -> bool:
    if (SKILLS_DIR / cap / "SKILL.md").exists():
        return True
    if (AGENTS_DIR / f"{cap}.md").exists():
        return True
    return False


def main() -> int:
    failures: list[str] = []
    text = entrypoint_text()
    cases = load_cases()

    # 3. NO DANGLING ROUTE
    for cap in sorted(referenced_capabilities(text)):
        if not exists(cap):
            failures.append(f"dangling_route {cap} referenced in entrypoint but not a skill/agent")

    # 1 + 2. per-case coverage and overtrigger
    for case in cases:
        prompt = case["prompt"]
        expect = set(case.get("expect") or [])
        expect_not = set(case.get("expect_not") or [])
        routed = route_for_prompt(prompt)

        for e in expect:
            if not exists(e):
                failures.append(f"unknown_expected {e!r} in case {prompt[:40]!r}")
            if e not in routed:
                failures.append(f"coverage_gap expected={e} not routed for {prompt[:60]!r}")
        for e in expect_not:
            if e in routed:
                failures.append(f"overtrigger expected_not={e} routed for {prompt[:60]!r}")

        # every routed capability for a matched intent must be declared in the
        # entrypoint text (rubric/doc agreement)
        for e in routed:
            if e not in text:
                failures.append(f"rubric_doc_drift {e} in rubric but missing from entrypoint text")

    # report
    print(f"routing_cases={len(cases)}")
    print(f"rubric_categories={len(RUBRIC)}")
    print(f"routing_failures={len(failures)}")
    for f in failures:
        print("FAIL", f)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
