#!/usr/bin/env python3
"""Game-design intelligence: experience decisions must trace to implementation.

This is intentionally a schema/traceability tool, not a claim that a JSON
brief is a good game. Playtest evidence and independent design review remain
separate required evidence for higher maturity.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REQUIRED = ("player_fantasy", "player_verbs", "core_loop", "controls", "feedback", "challenge", "failure_recovery", "win_condition", "accessibility")


def validate(brief: dict[str, Any]) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    for key in REQUIRED:
        value = brief.get(key)
        if not value or (isinstance(value, list) and not all(value)):
            issues.append({"severity": "error", "code": f"missing_{key}"})
    mechanics = brief.get("mechanics", [])
    if not mechanics:
        issues.append({"severity": "error", "code": "no_mechanics"})
    for i, item in enumerate(mechanics):
        for key in ("id", "player_experience", "system", "implementation", "evidence"):
            if not item.get(key):
                issues.append({"severity": "error", "code": f"mechanics_{i}_missing_{key}"})
        if item.get("evidence") and not isinstance(item["evidence"], list):
            issues.append({"severity": "error", "code": f"mechanics_{i}_evidence_must_be_list"})
    if not brief.get("secondary_loops"):
        issues.append({"severity": "warning", "code": "no_secondary_loop"})
    if not brief.get("playtest_plan"):
        issues.append({"severity": "warning", "code": "no_playtest_plan"})
    return {"ok": not any(i["severity"] == "error" for i in issues), "issues": issues}


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(prog="game_design")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("validate"); p.add_argument("brief", type=Path)
    p = sub.add_parser("create"); p.add_argument("out", type=Path); p.add_argument("--title", default="Emberveil: The Last Reliquary")
    args = parser.parse_args()
    if args.command == "validate":
        brief = json.loads(args.brief.read_text(encoding="utf-8")); brief["validation"] = validate(brief); result = brief
    else:
        result = {
            "schema_version": 1, "kind": "game-design-brief", "title": args.title,
            "player_fantasy": "Protect a dying fire-reliquary by reading a hostile shrine and choosing when to awaken its guardian.",
            "player_verbs": ["move", "look", "attune", "ignite", "retreat"],
            "core_loop": ["read the space", "approach a signal", "attune the reliquary", "survive its response", "restore a coal or fail"],
            "secondary_loops": ["learn shrine patterns", "optimize risk/reward ember routes"],
            "controls": {"keyboard_mouse": ["WASD move", "mouse look", "E attune"], "controller": ["left stick move", "right stick look", "south face attune"]},
            "feedback": {"success": ["warm pulse", "rising hum", "gold ember motes"], "danger": ["cracked tone", "red heat bloom", "camera recoil"]},
            "challenge": "The shrine changes its safe route after each attunement; the player must observe before committing.",
            "failure_recovery": "A failed attunement returns the player to the last lit coal with reduced route certainty, never a dead-end state.",
            "win_condition": "Light three reliquaries and reach the central ember before the chamber cools.",
            "accessibility": ["remappable actions", "subtitle-ready events", "reduced camera motion", "high-contrast interaction cue", "audio-independent danger cue"],
            "mechanics": [
                {"id": "attunement", "player_experience": "risk a close reading of the shrine", "system": "timed interaction with stateful danger response", "implementation": "Enhanced Input action + gameplay state component + feedback event bus", "evidence": ["planned: unreal gameplay test", "planned: playtest capture"]},
                {"id": "ember-routing", "player_experience": "choose a safer or richer route", "system": "branching shrine nodes with resource consequence", "implementation": "data-driven route asset + level encounter markers", "evidence": ["planned: level-design review"]}
            ],
            "camera": {"mode": "close third-person", "principle": "keep the reliquary readable while preserving spatial threat cues"},
            "audio_language": "resonant metal, dry ash, localized ember hum; no unproven stock assets",
            "playtest_plan": {"first_session_questions": ["Can a new player explain the attunement goal?", "Does danger read without audio?", "Does retreat feel like a choice rather than punishment?"], "evidence": "required before COHERENT promotion"},
            "quality_ladder": "BLOCKOUT",
            "game_state": ["START", "PLAYING", "SUCCESS", "FAILURE", "RESTART"],
            "level_requirements": ["safe entry chamber", "pulse-reading lesson", "escalated hostile attunement", "three-coal climax", "recoverable failure return"],
            "ai_systemic_opposition": {"type": "deterministic shrine-response state machine", "states": ["DORMANT", "READING", "SAFE_WINDOW", "HOSTILE", "COOLED"], "player_counterplay": "observe pulse, retreat during HOSTILE, commit only during SAFE_WINDOW"},
            "animation_requirements": ["player locomotion", "attune action", "reliquary pulse", "hostile surge", "success ignition", "failure recoil"],
            "vfx_requirements": [{"event": "SAFE_WINDOW", "purpose": "communicate actionable timing", "shape": "converging gold motes", "budget": "one local emitter"}, {"event": "HOSTILE", "purpose": "signal danger", "shape": "red heat fracture and outward ash burst", "budget": "one burst plus emissive pulse"}],
            "audio_requirements": ["chamber ambience", "pulse tick", "attune confirmation", "hostile warning", "success ignition", "failure recoil"],
            "ui_requirements": ["state label", "coal progress", "interaction prompt", "failure/restart prompt", "reduced-motion and high-contrast modes"],
            "architecture_decisions": [{"subsystem": "movement", "mode": "C++", "rationale": "reusable tested input and movement behavior"}, {"subsystem": "reliquary state", "mode": "C++", "rationale": "deterministic state transitions and native tests"}, {"subsystem": "presentation", "mode": "HYBRID", "rationale": "C++ owns state; Blueprint/UMG/Niagara author presentation"}, {"subsystem": "encounter data", "mode": "DATA", "rationale": "tunable pulse windows without code edits"}],
            "failure_injection": ["missing imported mesh", "invalid input mapping", "illegal HOSTILE→SUCCESS transition", "missing VFX asset", "missing startup map"],
        }
        result["validation"] = validate(result); args.out.parent.mkdir(parents=True, exist_ok=True); args.out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("validation", {}).get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
