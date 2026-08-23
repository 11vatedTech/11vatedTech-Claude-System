#!/usr/bin/env python3
"""Deterministic mission compiler for cross-domain Foundry work.

It is a planning compiler, not a quality certifier. The output makes unknowns,
non-goals, evidence, and human approval points explicit before expensive work.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

RULES = [
    ("frontend", {"frontend", "website", "web app", "dashboard", "ui", "ux", "browser",
                  "interactive", "showcase", "checkout", "mobile", "responsive", "page",
                  "landing", "form", "navigation", "component"},
     ["frontend-design", "ui-ux", "accessibility", "responsive-design", "motion-design", "web-performance"],
     ["Playwright runtime harness", "browser DevTools", "axe-core", "Lighthouse"],
     ["browser states", "responsive screenshots", "keyboard path", "accessibility scan", "performance metrics"]),
    ("creative", {"visual", "art", "creative", "3d", "creature", "lighting", "material",
                  "animation", "vfx", "cinematic", "character", "premium", "look", "feel",
                  "typography", "identity", "motion", "color"},
     ["creative-direction", "art-direction", "visual-development", "lookdev", "perceptual-qa"],
     ["Blender", "Unreal Engine", "FFmpeg", "ImageMagick"],
     ["visual thesis", "concept directions", "controlled renders", "motion evidence", "independent critique"]),
    ("game", {"game", "playable", "gameplay", "level", "player", "mechanic", "ai", "combat"},
     ["game-design", "game-feel", "level-design", "runtime-qa", "performance"],
     ["Unreal Engine", "native automation", "Gauntlet", "Unreal Insights"],
     ["design trace", "playable runtime", "scenario test", "playtest", "profile", "packaged build"]),
    ("engineering", {"code", "software", "repository", "refactor", "debug", "architecture",
                     "api", "service", "pipeline", "testability", "performance", "rendering"},
     ["semantic-repository-intelligence", "architecture", "testing", "release-engineering"],
     ["LSP/compiler tooling", "test runner", "runtime logs"],
     ["change-impact report", "focused tests", "regression tests", "runtime evidence"]),
]


def compile_intent(intent: str, mission_id: str = "compiled-mission") -> dict:
    text = intent.lower()
    matched = [rule for rule in RULES if any(term in text for term in rule[1])]
    if not matched:
        matched = [RULES[-1]]
    disciplines = []
    tools = []
    evidence = []
    for _, _, rule_disciplines, rule_tools, rule_evidence in matched:
        disciplines.extend(rule_disciplines)
        tools.extend(rule_tools)
        evidence.extend(rule_evidence)
    disciplines = list(dict.fromkeys(disciplines))
    tools = list(dict.fromkeys(tools))
    evidence = list(dict.fromkeys(evidence))
    visual = any(name in disciplines for name in ("creative-direction", "art-direction", "frontend-design"))
    unknowns = [
        "which user/player outcome makes the work valuable?",
        "which requirements are version-specific and need current primary-source research?",
        "what evidence can falsify quality rather than merely prove execution?",
    ]
    if visual:
        unknowns.append("what visual thesis, anti-references, and signature qualities distinguish this from a generic template?")
    if "game-design" in disciplines:
        unknowns.append("what player fantasy, core loop, feedback, challenge, and failure/recovery model are being tested?")
    return {
        "schema_version": 1,
        "kind": "compiled-founder-mission",
        "mission_id": mission_id,
        "intent": intent,
        "success_condition": "Required evidence exists and the relevant independent or human review has no unresolved hard blocker.",
        "non_goals": ["polish a frozen calibration fixture", "claim mastery from tool access or passing structural tests"],
        "unknown_questions": unknowns,
        "required_disciplines": disciplines,
        "required_capabilities": [f"{name}:research->practice->review->repair->transfer" for name in disciplines],
        "knowledge_gaps": ["current model capability for this role", "version-specific tool behavior", "discipline-specific quality ceiling"],
        "research": ["official standards and tool documentation", "professional breakdowns", "independent critique criteria"],
        "tools": tools,
        "model_roles": ["builder", "specialist-reviewer", "independent-reviewer"],
        "production_stages": ["intent", "research", "visual or interaction development", "bounded implementation", "evidence", "review", "repair", "transfer"],
        "evidence": evidence,
        "human_approval_points": ["direction selection", "quality-floor acceptance", "final appeal/appealability or usability verdict"],
        "stop_condition": "Stop when the declared capability question is answered, the transfer test is recorded, or the value gate returns STOP_AND_REPLAN.",
        "routing_note": "Model selection must use the measured registry; multimodal roles require actual image/video/audio payload evidence.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("intent", nargs="?", help="Founder outcome request")
    parser.add_argument("--mission", type=Path, help="JSON file with mission_id and intent")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.mission:
        source = json.loads(args.mission.read_text(encoding="utf-8"))
        intent = source.get("intent") or source.get("primary_objective", "")
        mission_id = source.get("mission_id", "compiled-mission")
    elif args.intent:
        intent, mission_id = args.intent, "compiled-mission"
    else:
        parser.error("provide intent or --mission")
    result = compile_intent(intent, mission_id)
    text = json.dumps(result, indent=2, ensure_ascii=False)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
