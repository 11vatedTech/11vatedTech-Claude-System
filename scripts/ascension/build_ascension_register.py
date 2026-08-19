#!/usr/bin/env python3
"""Build the machine-readable Capability Ascension Register.

Merges the capability ontology (config/capability-ontology.json) with curated
assessments (config/ascension-assessments.json) into a single register
(config/capability-ascension-register.json) that answers, for every
capability:

  WHAT CAN IT ACTUALLY DO TODAY?
  - current maturity, providers, evidence
  - missing executable capability
  - missing observation capability
  - missing evaluation
  - missing verification
  - dependencies
  - target maturity, priority, next implementation action

Maturity is never inflated: the register only reports what the evidence
supports, and the ontology gate (ontology_check.py) still enforces provider
and evidence existence.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ONTOLOGY = ROOT / "config" / "capability-ontology.json"
ASSESSMENTS = ROOT / "config" / "ascension-assessments.json"
OUT = ROOT / "config" / "capability-ascension-register.json"

DEFAULT_ASSESSMENT = {
    "missing_executable": "none identified; capability is definition/document only",
    "missing_observation": "no runtime observation layer",
    "missing_evaluation": "no production evaluation with real artifacts",
    "missing_verification": "no independent verification step",
    "dependencies": [],
    "target_maturity": "L3",
    "priority": "P3",
    "next_action": "audit and define evidence requirements before elevation",
}


def main() -> int:
    ontology = json.loads(ONTOLOGY.read_text(encoding="utf-8"))
    assessments = json.loads(ASSESSMENTS.read_text(encoding="utf-8"))
    scale = ontology["maturity_scale"]

    register: dict = {
        "schema_version": 1,
        "register_id": "11vt-capability-ascension-register",
        "generated": "2026-08-18",
        "baseline_version": ontology["baseline_version"],
        "maturity_scale": scale,
        "principle": "maturity is never inflated; L5 requires real implementation + real use + failure test + regression test + independent review + documented limitations",
        "capabilities": [],
    }

    seen = 0
    for domain in ontology["domains"]:
        for cap in domain["capabilities"]:
            seen += 1
            a = assessments.get(cap["id"], DEFAULT_ASSESSMENT)
            entry = {
                "id": cap["id"],
                "domain": domain["id"],
                "current_maturity": cap["maturity"],
                "providers": cap["providers"],
                "evidence": cap.get("evidence", []),
                "missing_executable": a.get("missing_executable"),
                "missing_observation": a.get("missing_observation"),
                "missing_evaluation": a.get("missing_evaluation"),
                "missing_verification": a.get("missing_verification"),
                "dependencies": a.get("dependencies", []),
                "target_maturity": a.get("target_maturity", "L3"),
                "priority": a.get("priority", "P3"),
                "next_action": a.get("next_action"),
            }
            register["capabilities"].append(entry)

    register["totals"] = {
        "capabilities": seen,
        "assessed_explicitly": len(assessments),
        "l0": sum(1 for c in register["capabilities"] if c["current_maturity"] == "L0"),
        "l2": sum(1 for c in register["capabilities"] if c["current_maturity"] == "L2"),
        "l3": sum(1 for c in register["capabilities"] if c["current_maturity"] == "L3"),
        "l4": sum(1 for c in register["capabilities"] if c["current_maturity"] == "L4"),
        "l5": sum(1 for c in register["capabilities"] if c["current_maturity"] == "L5"),
        "priority_p0": sum(1 for c in register["capabilities"] if c["priority"] == "P0"),
        "priority_p1": sum(1 for c in register["capabilities"] if c["priority"] == "P1"),
    }
    OUT.write_text(json.dumps(register, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"register_capabilities={seen}")
    print(f"assessed_explicitly={len(assessments)}")
    print(f"output={OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
