#!/usr/bin/env python3
"""Tiered regression runner — FAST (<30s), STANDARD (<2min), DEEP (unbounded)."""

import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

TIER_FAST = [
    ("python", "-m", "py_compile", "scripts/repo/lsp_client.py"),
    ("python", "-m", "py_compile", "scripts/repo/semantic_code_bus.py"),
    ("python", "-m", "py_compile", "scripts/frontend/runtime_harness.py"),
    ("python", "-m", "json.tool", "config/capability-ontology.json"),
    ("python", "scripts/validate/ontology_check.py"),
    ("python", "scripts/validate/foundry_ascension_tests.py"),
]

TIER_STANDARD = [
    ("python", "scripts/validate/lexical_vs_semantic_benchmark.py"),
    ("python", "scripts/validate/frontend_quality_contract.py", "artifacts/ascension/micro-labs/frontend-quality-contract.json"),
    ("python", "scripts/validate/creative_micro_lab.py", "artifacts/ascension/micro-labs/creative-lab-fixture.json"),
]

TIER_DEEP = [
    ("python", "scripts/validate/system_regression.py"),
]


def run_tier(name: str, commands: list, timeout: int) -> dict:
    results = []
    start = time.perf_counter()
    for cmd in commands:
        t0 = time.perf_counter()
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=str(ROOT))
            passed = r.returncode == 0
            results.append({"command": " ".join(cmd), "exit_code": r.returncode,
                           "verdict": "PASS" if passed else "FAIL",
                           "elapsed_s": round(time.perf_counter() - t0, 2),
                           "stderr_tail": r.stderr[-300:] if r.stderr else ""})
        except subprocess.TimeoutExpired:
            results.append({"command": " ".join(cmd), "verdict": "TIMEOUT", "elapsed_s": round(time.perf_counter() - t0, 2)})
        except Exception as exc:
            results.append({"command": " ".join(cmd), "verdict": "FAIL", "error": str(exc)})
    elapsed = round(time.perf_counter() - start, 1)
    passed = sum(1 for r in results if r["verdict"] == "PASS")
    return {"tier": name, "elapsed_s": elapsed, "total": len(results), "passed": passed,
            "verdict": "PASS" if passed == len(results) else "PARTIAL", "results": results}


def main() -> int:
    tiers = [
        run_tier("FAST", TIER_FAST, 30),
        run_tier("STANDARD", TIER_STANDARD, 120),
    ]

    # DEEP is optional - skip if --deep not passed
    if "--deep" in sys.argv:
        tiers.append(run_tier("DEEP", TIER_DEEP, 600))

    report = {"schema_version": 1, "kind": "tiered-regression", "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
              "tiers": tiers, "overall": "PASS" if all(t["verdict"] == "PASS" for t in tiers) else "PARTIAL"}

    out = ROOT / "artifacts" / "regression" / "tiered.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False))

    for tier in tiers:
        p = tier["passed"]
        t = tier["total"]
        print(f"{tier['tier']:8s}  {p}/{t}  {tier['verdict']}  ({tier['elapsed_s']}s)")

    print(f"Overall: {report['overall']}")
    return 0 if report["overall"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())