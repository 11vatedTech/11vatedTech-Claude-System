#!/usr/bin/env python3
"""Machine-readable truth audit for the deployed Foundry capability surface.

Documentation and agent names are evidence of intent, not operational proof.
The audit classifies each ontology entry using provider presence, executable
provider types, evidence paths, and independent verification markers.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ONTOLOGY = ROOT / "config" / "capability-ontology.json"
DEFAULT_OUT = ROOT / "config" / "capability-truth-audit.json"

STATES = ("ABSENT", "THEORETICAL", "SCRIPTED", "OPERATIONAL", "VERIFIED", "PRODUCTION-PROVEN")
EXECUTABLE_KINDS = {"script", "tool", "9router-endpoint", "commandlet", "mcp", "library"}
REVIEW_TERMS = ("review", "independent", "human", "playtest", "golden", "verification")
PRODUCTION_TERMS = ("production", "packaged", "release", "real product", "shipping")


def exists(root: Path, value: str) -> bool:
    if value.startswith("/"):
        return False
    return (root / value).exists()


def _provider_location(provider: dict) -> str | None:
    kind = provider.get("kind")
    name = str(provider.get("name", ""))
    if kind == "tool":
        try:
            import sys
            sys.path.insert(0, str(ROOT / "scripts" / "media"))
            from vtmedia.common import resolve_tool  # type: ignore
            return str(resolve_tool(name)) if resolve_tool(name) else None
        except Exception:
            return None
    if kind in EXECUTABLE_KINDS and exists(ROOT, name):
        return name
    return None


def classify(cap: dict) -> tuple[str, dict]:
    providers = cap.get("providers", [])
    evidence = cap.get("evidence", [])
    executable_paths = [location for p in providers if (location := _provider_location(p))]
    provider_present = bool(executable_paths)
    evidence_paths = [e for e in evidence if exists(ROOT, str(e))]
    all_text = " ".join(str(x).lower() for x in evidence_paths + executable_paths)
    review_evidence = [e for e in evidence_paths if any(term in str(e).lower() for term in REVIEW_TERMS)]
    production_evidence = [e for e in evidence_paths if any(term in str(e).lower() for term in PRODUCTION_TERMS)]

    if not providers and not evidence_paths:
        state = "ABSENT"
    elif not provider_present:
        state = "THEORETICAL"
    elif not executable_paths:
        state = "THEORETICAL"
    elif not evidence_paths:
        state = "SCRIPTED"
    elif cap.get("maturity") == "L0":
        state = "THEORETICAL"
    elif review_evidence and production_evidence:
        state = "PRODUCTION-PROVEN"
    elif review_evidence:
        state = "VERIFIED"
    else:
        state = "OPERATIONAL" if cap.get("maturity") in {"L2", "L3", "L4", "L5"} else "SCRIPTED"

    return state, {
        "provider_count": len(providers),
        "executable_providers": executable_paths,
        "evidence_present": evidence_paths,
        "missing_evidence": [e for e in evidence if e not in evidence_paths],
        "review_evidence": review_evidence,
        "production_evidence": production_evidence,
        "ontology_maturity": cap.get("maturity"),
        "maturity_scope": cap.get("maturity_scope", "unspecified"),
        "limitations": [
            "path existence does not prove artifact quality",
            "agent/skill prose is not operational evidence",
            "PRODUCTION-PROVEN requires explicit artifact, evaluation, and independent review evidence"
        ]
    }


def main() -> int:
    global ROOT
    parser = argparse.ArgumentParser()
    parser.add_argument("--ontology", type=Path, default=ONTOLOGY)
    parser.add_argument("--root", type=Path, default=ROOT, help="canonical source root used to resolve evidence pointers")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    ROOT = args.root.resolve()
    ontology = json.loads(args.ontology.read_text(encoding="utf-8"))
    records = []
    for domain in ontology.get("domains", []):
        for cap in domain.get("capabilities", []):
            state, evidence = classify(cap)
            records.append({"id": cap["id"], "domain": domain["id"], "truth_state": state, "evidence": evidence})
    counts = {state: sum(1 for r in records if r["truth_state"] == state) for state in STATES}
    report = {
        "schema_version": 1,
        "kind": "capability-truth-audit",
        "ontology": str(args.ontology),
        "principle": "tool access and documentation do not imply mastery",
        "truth_states": list(STATES),
        "counts": counts,
        "capabilities": records,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"counts": counts, "output": str(args.out)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
