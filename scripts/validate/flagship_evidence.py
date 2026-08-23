#!/usr/bin/env python3
"""Validate the real flagship evidence without claiming artistic perfection."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FLAGSHIP = ROOT / "artifacts" / "flagship"
CANONICAL = FLAGSHIP / "emberveil-canonical"
QA = FLAGSHIP / "qa"


def run(argv: list[str]) -> tuple[int, str]:
    p = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True, timeout=180)
    return p.returncode, (p.stdout + p.stderr)[-1200:]


def main() -> int:
    required = [
        CANONICAL / "canonical-build-report.json",
        CANONICAL / "emberveil-canonical.glb",
        CANONICAL / "emberveil-canonical-turntable.mp4",
        CANONICAL / "emberveil-canonical-cinematic.mp4",
        QA / "runtime-canonical-final2" / "state.json",
        QA / "runtime-canonical-final2" / "console.json",
    ]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        print("FLAGSHIP_EVIDENCE FAIL missing", missing)
        return 1
    report = json.loads((CANONICAL / "canonical-build-report.json").read_text(encoding="utf-8"))
    export = report.get("results", {}).get("export", {}).get("glb_validation", {})
    checks = {
        "canonical_build": report.get("ok") is True,
        "glb_structural_valid": export.get("valid") is True,
        "material_count": export.get("material_count", 0) >= 4,
        "animation_count": export.get("animation_count", 0) >= 3,
    }
    images = [
        CANONICAL / "preview" / "preview-frame-0048.png",
        CANONICAL / "turntable" / "turntable-000.png",
        CANONICAL / "turntable" / "turntable-012.png",
        CANONICAL / "cinematic-frames" / "seq-0001.png",
        CANONICAL / "cinematic-frames" / "seq-0036.png",
        CANONICAL / "cinematic-frames" / "seq-0072.png",
    ]
    code, output = run([sys.executable, str(ROOT / "scripts/validate/perceptual_visual_qa.py"), *map(str, images), "--strict"])
    checks["perceptual_readability"] = code == 0
    print(output)
    code, output = run([sys.executable, str(ROOT / "scripts/validate/asset_variant_diff.py"), str(CANONICAL / "emberveil-canonical.glb"), str(CANONICAL / "emberveil-canonical.glb"), "--strict"])
    checks["variant_gate_baseline"] = code == 0
    print(output)
    state = json.loads((QA / "runtime-canonical-final2" / "state.json").read_text(encoding="utf-8"))
    observed = [f.get("state", {}).get("foundryState") for f in state.get("frames", [])]
    observed = [s for s in observed if s]
    checks["runtime_loaded"] = bool(observed) and all(s.get("heroLoaded") for s in observed)
    checks["runtime_complete_animation_set"] = bool(observed) and max(s.get("activeAnimationCount", 0) for s in observed) >= 3
    console = json.loads((QA / "runtime-canonical-final2" / "console.json").read_text(encoding="utf-8"))
    checks["runtime_console_network_clean"] = not console.get("messages") and not console.get("failedRequests")
    result = {"schema_version": 1, "checks": checks, "ok": all(checks.values()),
              "limitations": ["metrics and structural gates do not prove professional artistic quality", "runtime fps=0 is headless SwiftShader throttling"]}
    (QA / "flagship-evidence.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print("FLAGSHIP_EVIDENCE", "PASS" if result["ok"] else "FAIL", checks)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
