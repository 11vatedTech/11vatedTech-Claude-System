#!/usr/bin/env python3
"""Asset Resolver — asset requirement/resolution engine.

For every asset a product needs, decide among the resolution modes and score
the decision across the factors that matter to 11vatedTech products (identity,
canon, quality, editability, licensing, provenance, runtime, cost, originality).

The resolver never silently passes a random download: every resolution emits a
provenance plan, and resolutions that would introduce unknown-license assets
are flagged as blocking until the license is resolved.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]

RESOLUTION_MODES = [
    "REUSE_INTERNAL", "SOURCE_EXTERNAL", "TRANSFORM_INTERNAL",
    "TRANSFORM_LICENSED_EXTERNAL", "PROCEDURAL_GENERATION",
    "LOCAL_GENERATIVE_SYNTHESIS", "PROGRAMMATIC_CREATION",
    "DIRECTED_ORIGINAL_CREATION", "CAPTURE", "MOTION_CAPTURE",
    "PHOTOGRAMMETRY_RECONSTRUCTION", "SIMULATION", "INVENT_NEW_PRODUCTION_METHOD",
]

FACTORS = ["identity", "canon", "quality", "editability", "licensing",
           "provenance", "runtime", "cost_time", "originality"]

# factor -> how each mode scores (0..3; 3 = excellent fit)
MODE_SCORES: dict[str, dict[str, int]] = {
    "REUSE_INTERNAL":            {"identity": 2, "canon": 2, "quality": 1, "editability": 2, "licensing": 3, "provenance": 3, "runtime": 2, "cost_time": 3, "originality": 1},
    "SOURCE_EXTERNAL":           {"identity": 0, "canon": 1, "quality": 2, "editability": 1, "licensing": 1, "provenance": 0, "runtime": 2, "cost_time": 3, "originality": 0},
    "TRANSFORM_INTERNAL":        {"identity": 2, "canon": 2, "quality": 2, "editability": 2, "licensing": 3, "provenance": 3, "runtime": 2, "cost_time": 2, "originality": 2},
    "TRANSFORM_LICENSED_EXTERNAL": {"identity": 1, "canon": 1, "quality": 2, "editability": 2, "licensing": 2, "provenance": 2, "runtime": 2, "cost_time": 2, "originality": 1},
    "PROCEDURAL_GENERATION":     {"identity": 2, "canon": 2, "quality": 2, "editability": 3, "licensing": 3, "provenance": 3, "runtime": 2, "cost_time": 2, "originality": 3},
    "LOCAL_GENERATIVE_SYNTHESIS": {"identity": 1, "canon": 1, "quality": 1, "editability": 1, "licensing": 2, "provenance": 2, "runtime": 2, "cost_time": 2, "originality": 2},
    "PROGRAMMATIC_CREATION":     {"identity": 2, "canon": 2, "quality": 2, "editability": 3, "licensing": 3, "provenance": 3, "runtime": 3, "cost_time": 2, "originality": 2},
    "DIRECTED_ORIGINAL_CREATION": {"identity": 3, "canon": 3, "quality": 3, "editability": 3, "licensing": 3, "provenance": 3, "runtime": 1, "cost_time": 0, "originality": 3},
    "CAPTURE":                   {"identity": 3, "canon": 2, "quality": 3, "editability": 1, "licensing": 2, "provenance": 2, "runtime": 2, "cost_time": 1, "originality": 2},
    "MOTION_CAPTURE":            {"identity": 2, "canon": 2, "quality": 3, "editability": 1, "licensing": 2, "provenance": 2, "runtime": 2, "cost_time": 0, "originality": 2},
    "PHOTOGRAMMETRY_RECONSTRUCTION": {"identity": 3, "canon": 2, "quality": 3, "editability": 1, "licensing": 2, "provenance": 2, "runtime": 1, "cost_time": 0, "originality": 2},
    "SIMULATION":                {"identity": 2, "canon": 2, "quality": 2, "editability": 2, "licensing": 3, "provenance": 3, "runtime": 1, "cost_time": 1, "originality": 2},
    "INVENT_NEW_PRODUCTION_METHOD": {"identity": 3, "canon": 3, "quality": 2, "editability": 3, "licensing": 3, "provenance": 3, "runtime": 1, "cost_time": 0, "originality": 3},
}

# factor weights; can be overridden per requirement
DEFAULT_WEIGHTS: dict[str, int] = {
    "identity": 3, "canon": 3, "quality": 3, "editability": 2, "licensing": 3,
    "provenance": 3, "runtime": 2, "cost_time": 1, "originality": 3,
}

def resolve(requirement: dict[str, Any]) -> dict[str, Any]:
    """Resolve one asset requirement. `requirement` fields:
    name, category (optional), quality_target (optional), weights (optional),
    flags: needs_originality (bool), license_known (bool), runtime_critical (bool),
    can_create (bool), time_budget (optional)."""
    name = requirement["name"]
    weights = dict(DEFAULT_WEIGHTS)
    weights.update(requirement.get("weights", {}))
    flags = {
        "needs_originality": True, "license_known": False, "runtime_critical": False,
        "can_create": True, "time_budget": None, "generative_available": False,
        "capture_available": False,
    }
    flags.update(requirement.get("flags", {}))
    # flag-driven weight modulation: the same factor set must discriminate
    # between a hero asset (originality-critical) and a utility asset (cheap)
    if not flags["needs_originality"]:
        weights["originality"] = max(1, weights["originality"] // 3)
        weights["identity"] = max(1, weights["identity"] // 2)
    if flags["runtime_critical"]:
        weights["runtime"] = weights["runtime"] * 2
    if flags.get("time_budget") == "tight":
        weights["cost_time"] = weights["cost_time"] * 3
        weights["quality"] = max(1, weights["quality"] - 1)

    # flag-driven mode boosts (interpretable policy, not hidden tuning)
    boosts: dict[str, float] = {}
    if flags.get("capture_available"):
        for m in ("CAPTURE", "MOTION_CAPTURE", "PHOTOGRAMMETRY_RECONSTRUCTION"):
            boosts[m] = boosts.get(m, 0.0) + 0.6
    if flags["license_known"]:
        for m in ("SOURCE_EXTERNAL", "TRANSFORM_LICENSED_EXTERNAL"):
            boosts[m] = boosts.get(m, 0.0) + 0.5
    if flags.get("time_budget") == "tight":
        for m in ("REUSE_INTERNAL", "SOURCE_EXTERNAL", "PROCEDURAL_GENERATION", "PROGRAMMATIC_CREATION"):
            boosts[m] = boosts.get(m, 0.0) + 0.4
    if not flags["needs_originality"]:
        boosts["SOURCE_EXTERNAL"] = boosts.get("SOURCE_EXTERNAL", 0.0) + 0.3
        boosts["REUSE_INTERNAL"] = boosts.get("REUSE_INTERNAL", 0.0) + 0.3

    scored = []
    blocked: list[str] = []
    for mode in RESOLUTION_MODES:
        scores = MODE_SCORES[mode]
        total = sum(scores[f] * weights[f] for f in FACTORS) / sum(weights.values())
        total += boosts.get(mode, 0.0)
        reason = None
        if mode in ("SOURCE_EXTERNAL", "TRANSFORM_LICENSED_EXTERNAL") and not flags["license_known"]:
            reason = "license_unknown"
        if mode == "LOCAL_GENERATIVE_SYNTHESIS" and not flags.get("generative_available"):
            reason = "provider_missing"
        if mode in ("MOTION_CAPTURE", "CAPTURE", "PHOTOGRAMMETRY_RECONSTRUCTION") and not flags.get("capture_available"):
            reason = "equipment_missing"
        if mode in ("DIRECTED_ORIGINAL_CREATION", "INVENT_NEW_PRODUCTION_METHOD") and not flags["can_create"]:
            reason = "creation_not_available"
        entry = {"mode": mode, "score": round(total, 3), "blocked": bool(reason), "reason": reason}
        scored.append(entry)
        if reason:
            blocked.append(mode)

    ranked = [s for s in scored if not s["blocked"]]
    ranked.sort(key=lambda s: s["score"], reverse=True)
    decision = ranked[0] if ranked else {"mode": None, "score": 0.0, "blocked": True, "reason": "all_modes_blocked"}

    provenance_plan = {
        "license_required": None,
        "provenance_record_required": True,
        "vault_required": True,
    }
    if decision["mode"] in ("SOURCE_EXTERNAL", "TRANSFORM_LICENSED_EXTERNAL"):
        provenance_plan["license_required"] = "resolve license + record in vault before use"

    return {
        "requirement": name,
        "category": requirement.get("category"),
        "quality_target": requirement.get("quality_target", "PRODUCTION"),
        "decision": decision,
        "ranked_alternatives": ranked[:3],
        "blocked_modes": blocked,
        "provenance_plan": provenance_plan,
        "note": "resolution is a decision record; execution must produce a vault record with license and provenance",
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="asset_resolver")
    p.add_argument("requirement", help="JSON file with one or more requirements")
    args = p.parse_args(argv)
    reqs = json.loads(Path(args.requirement).read_text(encoding="utf-8"))
    if isinstance(reqs, dict):
        reqs = [reqs]
    for req in reqs:
        print(json.dumps(resolve(req), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
