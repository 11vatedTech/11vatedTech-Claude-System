#!/usr/bin/env python3
"""Generate and score materially different original vertical-slice concepts."""
from __future__ import annotations
import argparse, json
from pathlib import Path

CONCEPTS = [
    {
        "id": "emberveil-last-reliquary", "title": "Emberveil: The Last Reliquary",
        "player_fantasy": "Read a dying shrine's danger and become the guardian who keeps its last fire alive.",
        "core_mechanic": "Attune to a reliquary only when its pulse pattern is safe; retreat and observe when it turns hostile.",
        "shape": "Close third-person shrine chamber with a suspended bell-reliquary, ash paths, and warm/cold state lighting.",
        "loops": ["observe pulse", "move into risk", "attune", "survive response", "light next coal"],
        "coverage": ["movement", "input", "state machine", "AI/systemic response", "animation", "Niagara", "audio", "camera", "HUD", "packaging"],
        "risk": "medium", "calibration_value": 10,
        "score": {"player_fantasy": 5, "mechanical_depth": 5, "game_feel": 5, "visual_identity": 5, "coverage": 5, "risk": 4, "calibration": 5}
    },
    {
        "id": "glasswake-courier", "title": "Glasswake Courier",
        "player_fantasy": "Carry a fragile memory through a shifting industrial flood before the world forgets it.",
        "core_mechanic": "Route sound-sensitive bridges by choosing when to move silently and when to spend resonance to reveal safe geometry.",
        "shape": "Side-on 3D traversal slice across glass catwalks, signal pylons, and reactive water haze.",
        "loops": ["scan resonance", "choose route", "cross", "spend memory", "reach archive"],
        "coverage": ["movement", "input", "route state", "procedural environment", "VFX", "audio", "camera", "UI", "packaging"],
        "risk": "high", "calibration_value": 9,
        "score": {"player_fantasy": 5, "mechanical_depth": 5, "game_feel": 4, "visual_identity": 5, "coverage": 4, "risk": 2, "calibration": 5}
    },
    {
        "id": "mothlight-salvage", "title": "Mothlight Salvage",
        "player_fantasy": "Be the tiny keeper of a dead observatory and coax one useful constellation back into the sky.",
        "core_mechanic": "Redirect a living beam through rotating lenses while a curious shadow organism learns from each mistake.",
        "shape": "Top-down diorama of brass optics, star dust, and a responsive shadow creature.",
        "loops": ["inspect lens", "rotate", "redirect beam", "evade shadow", "restore star"],
        "coverage": ["movement", "input", "puzzle state", "AI pursuit", "mechanical animation", "VFX", "audio", "camera", "UI", "packaging"],
        "risk": "medium-high", "calibration_value": 10,
        "score": {"player_fantasy": 5, "mechanical_depth": 4, "game_feel": 4, "visual_identity": 5, "coverage": 5, "risk": 3, "calibration": 5}
    }
]


def main() -> int:
    p = argparse.ArgumentParser(); p.add_argument("out", type=Path)
    args = p.parse_args()
    ranked = []
    for concept in CONCEPTS:
        total = sum(concept["score"].values())
        ranked.append({"id": concept["id"], "title": concept["title"], "total": total, "score": concept["score"]})
    ranked.sort(key=lambda item: (-item["total"], item["id"]))
    selected = ranked[0]["id"]
    result = {"schema_version": 1, "kind": "vertical-slice-concept-study", "concepts": CONCEPTS, "ranking": ranked, "selected_id": selected, "selection_reason": "Highest combined player fantasy, mechanical depth, visual identity, coverage, and calibration value with lower implementation risk than Glasswake."}
    args.out.parent.mkdir(parents=True, exist_ok=True); args.out.write_text(json.dumps(result, indent=2), encoding="utf-8"); print(json.dumps(result, indent=2)); return 0

if __name__ == "__main__": raise SystemExit(main())
