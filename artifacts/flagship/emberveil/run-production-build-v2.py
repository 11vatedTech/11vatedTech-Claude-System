"""Emberveil Production Build v2 Runner.

Chains structured Blender ops from production-build-v2.json through
a single persistent session.blend. Each op is validated, executed via
the op_runner, and results are collected into a build report.

Usage:
    python run-production-build-v2.py
    python run-production-build-v2.py --dry-run
    python run-production-build-v2.py --skip-render
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

# Add the scripts dir to path so we can import blender_ops
SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "scripts" / "media"
sys.path.insert(0, str(SCRIPTS_DIR))

from vtmedia.blender_ops import run_op, validate  # noqa: E402

BUILD_DIR = Path(__file__).resolve().parent
SPEC_PATH = BUILD_DIR / "production-build-v2.json"
REPORT_PATH = BUILD_DIR / "production-build-v2-report.json"


def run_build(dry_run: bool = False, skip_render: bool = False) -> dict:
    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    ops = spec["ops"]
    chain_blend = BUILD_DIR / spec.get("session_blend", "session.blend")

    results: dict[str, dict] = {}
    skipped: list[str] = []
    failed: list[str] = []
    started = time.time()

    for op_def in ops:
        op_id = op_def["id"]
        op_name = op_def["op"]
        params = dict(op_def.get("params", {}))

        # Skip renders if requested
        if skip_render and op_name.startswith("render."):
            skipped.append(op_id)
            results[op_id] = {"ok": True, "health": "SKIPPED", "op": op_name,
                              "note": "skipped by --skip-render"}
            continue

        # Validate before running
        errors = validate(op_name, params)
        if errors:
            results[op_id] = {"ok": False, "health": "FAILED", "op": op_name,
                              "validation_errors": errors}
            failed.append(op_id)
            print(f"  FAIL  {op_id}: {errors}")
            continue

        if dry_run:
            results[op_id] = {"ok": True, "health": "DRY_RUN", "op": op_name}
            print(f"  DRY   {op_id} ({op_name})")
            continue

        print(f"  RUN   {op_id} ({op_name})...", end=" ", flush=True)
        t0 = time.time()

        out_dir = BUILD_DIR / "v2-ops"
        try:
            r = run_op(op_name, params, out_dir, timeout=600, chain_blend=chain_blend)
        except Exception as exc:
            r = {"ok": False, "health": "FAILED", "op": op_name,
                 "error": f"{type(exc).__name__}: {exc}"}

        elapsed = round(time.time() - t0, 1)
        r["elapsed_seconds"] = elapsed
        results[op_id] = r

        status = r.get("health", "?")
        error = r.get("error", "")
        print(f"{status} ({elapsed}s) {error}")

        if not r.get("ok"):
            failed.append(op_id)

    total_elapsed = round(time.time() - started, 1)
    report = {
        "build_id": spec["build_id"],
        "version": spec["version"],
        "total_ops": len(ops),
        "passed": len(ops) - len(failed) - len(skipped),
        "failed": failed,
        "skipped": skipped,
        "total_elapsed_seconds": total_elapsed,
        "results": results,
    }

    REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nBuild {'PASSED' if not failed else 'FAILED'}: "
          f"{report['passed']}/{len(ops)} ops in {total_elapsed}s")
    if failed:
        print(f"Failed: {', '.join(failed)}")
    if skipped:
        print(f"Skipped: {', '.join(skipped)}")
    print(f"Report: {REPORT_PATH}")
    return report


if __name__ == "__main__":
    dry = "--dry-run" in sys.argv
    skip = "--skip-render" in sys.argv
    report = run_build(dry_run=dry, skip_render=skip)
    raise SystemExit(0 if not report["failed"] else 1)
