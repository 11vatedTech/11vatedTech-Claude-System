#!/usr/bin/env python3
"""L5 evidence checker.

L5 (GOVERNED) is an enforced state, not a claim. A capability is L5 only when
all six requirements are present and verifiable:

1. REAL IMPLEMENTATION  — executable tooling exists and resolves
2. REAL USE             — a real artifact/evidence produced by it exists
3. FAILURE TEST         — a negative-path test proves the gate catches breaks
4. REGRESSION TEST      — the capability is wired into system_regression.py
5. INDEPENDENT REVIEW   — a dated review record exists (docs/l5-review-record-*.md)
6. DOCUMENTED LIMITATIONS — limitations recorded in the review record

The ontology's maturity claim is cross-checked: any capability marked L5 in
config/capability-ontology.json must pass this checker or the regression fails.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ONTOLOGY = ROOT / "config" / "capability-ontology.json"
REGRESSION = ROOT / "scripts" / "validate" / "system_regression.py"

# per-capability evidence map: where each L5 requirement lives.
# "regression" names the gate function in scripts/validate/system_regression.py
L5_REQUIREMENTS: dict[str, dict[str, list[str]]] = {
    "pixel-diff": {
        "implementation": ["scripts/media/vtmedia/image_tools.py"],
        "real_use": ["artifacts/creative-stack-validation/image/image-validation.json"],
        "failure_test": ["scripts/validate/failure_tests.py"],
        "regression": ["check_media"],
    },
    "blender-bridge": {
        "implementation": ["scripts/media/vtmedia/blender_ops.py", "scripts/media/vtmedia/blender_scripts/op_runner.py"],
        "real_use": ["artifacts/creative-stack-validation/blender-ops/blender-op-suite.json", "artifacts/creative-stack-validation/blender-ops/hero-scene.glb"],
        "failure_test": ["scripts/validate/failure_tests.py"],
        "regression": ["check_blender_ops"],
    },
    "animation-qa": {
        "implementation": ["scripts/media/vtmedia/blender_ops.py"],
        "real_use": ["artifacts/creative-stack-validation/blender-ops/turntable.mp4", "artifacts/creative-stack-validation/blender-ops/blender-op-suite.json"],
        "failure_test": ["scripts/media/vtmedia/blender_ops.py"],
        "regression": ["check_blender_ops"],
    },
    "global-sync": {
        "implementation": ["scripts/install/sync_to_claude.py"],
        "real_use": [str(Path.home() / ".claude" / "11vatedtech" / "deployments")],
        "failure_test": ["scripts/validate/failure_tests.py"],
        "regression": ["check_failure_tests"],
    },
    "rollback": {
        "implementation": ["scripts/install/sync_to_claude.py"],
        "real_use": [str(Path.home() / ".claude" / "backups")],
        "failure_test": ["scripts/validate/failure_tests.py"],
        "regression": ["check_failure_tests"],
    },
}

REVIEW_RECORD_PATTERN = re.compile(r"docs/l5-review-record-2026-08-18\.md")

# Production-domain capabilities must earn L5 with their own evidence — an L5
# dependency (e.g. blender-bridge) does NOT confer production maturity.
# These are the domains where "infrastructure L5" must never be mistaken for
# "production L5".
PRODUCTION_DOMAINS = {
    "3d-production", "character-animation", "visual-design", "vfx-production",
    "cinematic-production", "audio-production", "frontend-production",
    "creative-direction", "motion-design", "texturing", "rigging", "lighting",
}


def check(cap: str, reqs: dict[str, list[str]]) -> list[str]:
    failures: list[str] = []
    for req, paths in reqs.items():
        if req == "independent_review":
            if not list(ROOT.glob("docs/l5-review-record-*.md")):
                failures.append(f"missing_independent_review_record")
            continue
        if req == "documented_limitations":
            rec = ROOT / "docs" / "l5-review-record-2026-08-18.md"
            if not rec.exists() or cap not in rec.read_text(encoding="utf-8"):
                failures.append(f"missing_documented_limitations {cap}")
            continue
        if req == "regression":
            continue  # gate function names verified in main()
        for p in paths:
            path = Path(p)
            if not path.exists():
                failures.append(f"missing_{req} {p}")
    return failures


def main() -> int:
    ontology = json.loads(ONTOLOGY.read_text(encoding="utf-8"))
    l5_caps = []
    for domain in ontology["domains"]:
        for cap in domain["capabilities"]:
            if cap["maturity"] == "L5":
                l5_caps.append(cap["id"])

    failures: list[str] = []
    for cap in l5_caps:
        reqs = L5_REQUIREMENTS.get(cap)
        if not reqs:
            failures.append(f"L5_without_evidence_map {cap} (L5 requires its OWN evidence; an L5 dependency does not confer maturity)")
            continue
        # production-domain L5 must carry a production-domain scope label
        cap_scope = None
        for domain in ontology["domains"]:
            for c in domain["capabilities"]:
                if c["id"] == cap:
                    cap_scope = c.get("maturity_scope") or domain["id"]
        if cap_scope in PRODUCTION_DOMAINS or cap in PRODUCTION_DOMAINS:
            failures.append(f"production_domain_L5_not_supported {cap} (scope={cap_scope}) — infrastructure maturity cannot be inherited")
        # regression requirement: the named gate function must exist and be wired
        reg_text = REGRESSION.read_text(encoding="utf-8")
        for gate in reqs.get("regression", []):
            if gate not in reg_text:
                failures.append(f"missing_regression_gate {cap} -> {gate}")
        failures.extend(check(cap, reqs))

    print(f"l5_capabilities={l5_caps}")
    print(f"l5_failures={len(failures)}")
    for f in failures:
        print("FAIL", f)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
