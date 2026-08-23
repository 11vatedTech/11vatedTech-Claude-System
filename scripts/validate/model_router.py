#!/usr/bin/env python3
"""Evidence-based role router over config/model-capability-registry.json.

This does not call a model. It makes the selection decision observable and
keeps fallback behavior explicit when evidence is missing or stale.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REGISTRY = ROOT / "config" / "model-capability-registry.json"
ROLES = {
    "builder": ("code", "debug", "repo"),
    "reviewer": ("debug", "repo", "visual-critique"),
    "researcher": ("research", "repo"),
    "visual-critic": ("visual-critique", "research"),
    "architect": ("repo", "research", "debug"),
    "fast": ("code",),
    "frontend-designer": ("frontend-design", "ux-critique", "research"),
    "game-design-critic": ("game-design", "ux-critique", "visual-critique"),
    "art-director": ("art-direction", "visual-critique", "research"),
}


def choose(registry: dict, role: str) -> dict:
    required = ROLES.get(role, (role,))
    candidates = []
    for model, tasks in registry.items():
        observed = [tasks.get(task) for task in required if isinstance(tasks, dict) and tasks.get(task)]
        if not observed:
            continue
        passed = sum(1 for task in observed if task.get("passed"))
        latency_values = [task["latency_s"] for task in observed if isinstance(task.get("latency_s"), (int, float))]
        coverage = len(observed) / len(required)
        score = (passed / len(required)) * 0.7 + coverage * 0.3
        candidates.append({
            "model": model,
            "score": round(score, 4),
            "passed_tasks": passed,
            "observed_tasks": len(observed),
            "required_tasks": list(required),
            "median_latency_s": round(sorted(latency_values)[len(latency_values) // 2], 2) if latency_values else None,
        })
    candidates.sort(key=lambda x: (-x["score"], x["median_latency_s"] is None, x["median_latency_s"] or 999999, x["model"]))
    return {
        "role": role,
        "selection": candidates[0] if candidates else None,
        "candidates": candidates,
        "fallback_policy": "no evidence-based selection; caller must use configured fallback or stop",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("role", choices=sorted(ROLES))
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = choose(json.loads(args.registry.read_text(encoding="utf-8")), args.role)
    text = json.dumps({"schema_version": 1, "kind": "evidence-based-model-selection", **result}, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    print(text)
    return 0 if result["selection"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
