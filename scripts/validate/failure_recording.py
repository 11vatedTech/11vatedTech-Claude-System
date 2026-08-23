#!/usr/bin/env python3
"""Failure Recording System — captures, classifies, and persists production failures.

Every failure during flagship creation is recorded with:
- timestamp, phase, component, failure_type, description
- severity (critical/warning/info)
- evidence (file paths, error messages)
- resolution status

This enables the quality ladder: failures must be tracked, not silently fixed.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

RECORDS_FILE = Path(__file__).resolve().parents[2] / "artifacts" / "flagship" / "failure-records.json"


def load_records() -> list[dict]:
    if RECORDS_FILE.exists():
        return json.loads(RECORDS_FILE.read_text(encoding="utf-8"))
    return []


def save_records(records: list[dict]):
    RECORDS_FILE.parent.mkdir(parents=True, exist_ok=True)
    RECORDS_FILE.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")


def record_failure(
    phase: str,
    component: str,
    failure_type: str,
    description: str,
    severity: str = "warning",
    evidence: list[str] | None = None,
    resolution: str = "open",
) -> dict:
    """Record a failure and persist it."""
    records = load_records()
    entry = {
        "id": f"FR-{len(records) + 1:04d}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "phase": phase,
        "component": component,
        "failure_type": failure_type,
        "description": description,
        "severity": severity,
        "evidence": evidence or [],
        "resolution": resolution,
    }
    records.append(entry)
    save_records(records)
    return entry


def list_open() -> list[dict]:
    """List all unresolved failures."""
    return [r for r in load_records() if r.get("resolution") == "open"]


def resolve(failure_id: str, resolution: str = "fixed"):
    """Mark a failure as resolved."""
    records = load_records()
    for r in records:
        if r["id"] == failure_id:
            r["resolution"] = resolution
            r["resolved_at"] = datetime.now(timezone.utc).isoformat()
    save_records(records)


def summary() -> dict:
    """Summary statistics of all failures."""
    records = load_records()
    by_severity = {}
    by_phase = {}
    by_type = {}
    for r in records:
        by_severity[r["severity"]] = by_severity.get(r["severity"], 0) + 1
        by_phase[r["phase"]] = by_phase.get(r["phase"], 0) + 1
        by_type[r["failure_type"]] = by_type.get(r["failure_type"], 0) + 1
    return {
        "total": len(records),
        "open": len(list_open()),
        "by_severity": by_severity,
        "by_phase": by_phase,
        "by_type": by_type,
    }


# ── Pre-recorded failures from this session ──────────────────────
SESSION_FAILURES = [
    {
        "phase": "production",
        "component": "op_runner",
        "failure_type": "session_chaining_corruption",
        "description": "Individual material ops using open_mainfile in background mode destroy mesh objects. Scene loses all MESH-type objects, retaining only CAMERA and LIGHT. Root cause: Blender 5.2 background open_mainfile does not fully restore scene state.",
        "severity": "critical",
        "evidence": [
            "v2-glass-result.json: ok=True but scene lost meshes",
            "debug-inspect: 3 objects (Cam, EmberCoreLight, FillLight), 0 meshes",
            "emberveil.glb dropped from 231KB to 132 bytes",
        ],
        "resolution": "fixed",
    },
    {
        "phase": "production",
        "component": "op_runner",
        "failure_type": "function_ordering",
        "description": "v2-batch-upgrade.py called _lathe() before its def statement. Python requires function definitions before calls in the same scope.",
        "severity": "critical",
        "evidence": [
            "v2-upgrade.log: NameError: name '_lathe' is not defined (line 84)",
        ],
        "resolution": "fixed",
    },
    {
        "phase": "production",
        "component": "material_ops",
        "failure_type": "object_naming_mismatch",
        "description": "Brass material spec used filigree_arc.001/002 (Blender dotted names) but actual objects were named filigree_arc_01/002 (underscored). Radial array naming convention mismatch.",
        "severity": "warning",
        "evidence": [
            "v2-brass-result.json: ValueError: object_not_found filigree_arc.001",
            "build-report.rig.parent.children: filigree_arc_01, filigree_arc_02",
        ],
        "resolution": "fixed",
    },
    {
        "phase": "runtime",
        "component": "presentation",
        "failure_type": "launch_json_deleted",
        "description": "Three.js runtime agent deleted .claude/launch.json after validation, breaking preview server for subsequent sessions.",
        "severity": "warning",
        "evidence": [
            "preview_start failed: No .claude/launch.json found",
            "Agent removed temporary preview config during cleanup",
        ],
        "resolution": "fixed",
    },
]


def main() -> int:
    if len(sys.argv) > 1 and sys.argv[1] == "seed":
        # Seed the failure records with session findings
        for f in SESSION_FAILURES:
            entry = record_failure(**f)
            print(f"  Recorded {entry['id']}: {entry['description'][:60]}...")
        print(f"\nSeeded {len(SESSION_FAILURES)} failure records.")
    elif len(sys.argv) > 1 and sys.argv[1] == "summary":
        s = summary()
        print(json.dumps(s, indent=2))
    elif len(sys.argv) > 1 and sys.argv[1] == "open":
        open_f = list_open()
        print(f"Open failures: {len(open_f)}")
        for f in open_f:
            print(f"  {f['id']}: [{f['severity']}] {f['description'][:80]}")
    else:
        print("Usage: failure_recording.py [seed|summary|open]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
