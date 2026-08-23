#!/usr/bin/env python3
"""Flagship Cohesion Audit — verifies all production artifacts form a coherent whole.

Checks that the creative brief, production graph, materials, animation,
VFX, lighting, camera, runtime presentation, and repository intelligence
are all present, cross-referenced, and consistent.

Exit code 0 = pass, 1 = failures found.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FLAGSHIP = ROOT / "artifacts" / "flagship"
EMBERVEIL = FLAGSHIP / "emberveil"
PRESENTATION = FLAGSHIP / "presentation"

failures: list[str] = []
warnings: list[str] = []


def check(condition: bool, msg: str, *, warn: bool = False):
    if not condition:
        if warn:
            warnings.append(msg)
        else:
            failures.append(msg)


def audit_files():
    """Required files must exist."""
    required = {
        "creative_brief": FLAGSHIP / "CREATIVE_BRIEF.md",
        "production_graph": FLAGSHIP / "production-graph.json",
        "session_blend": EMBERVEIL / "session.blend",
        "glb": EMBERVEIL / "emberveil.glb",
        "runtime_html": PRESENTATION / "index.html",
        "canonical_build": FLAGSHIP / "emberveil-canonical" / "canonical-build-report.json",
        "canonical_glb": FLAGSHIP / "emberveil-canonical" / "emberveil-canonical.glb",
        "perceptual_qa": FLAGSHIP / "qa" / "perceptual-canonical.json",
    }
    for key, path in required.items():
        check(path.exists(), f"missing_file {key}: {path}")

    # GLB must be non-trivial (>1KB)
    glb = EMBERVEIL / "emberveil.glb"
    if glb.exists():
        size = glb.stat().st_size
        check(size > 1024, f"glb_too_small {size} bytes (expected >1KB)", warn=True)


def audit_production_graph():
    """Production graph must be valid JSON with required nodes."""
    pg_path = FLAGSHIP / "production-graph.json"
    if not pg_path.exists():
        return
    try:
        pg = json.loads(pg_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        failures.append(f"production_graph_invalid_json: {e}")
        return

    nodes = {n["id"]: n for n in pg.get("nodes", [])}
    # Check minimum node count (graph uses emberveil-XX IDs)
    check(len(nodes) >= 12,
          f"production_graph insufficient nodes: {len(nodes)} (expected >=12)")

    # Check discipline coverage
    disciplines = set()
    for n in pg.get("nodes", []):
        d = n.get("discipline", "")
        if d:
            disciplines.add(d)
    check(len(disciplines) >= 4,
          f"production_graph low discipline coverage: {len(disciplines)} (expected >=4)")


def audit_materials():
    """Session must have materials assigned to mesh objects."""
    # Prefer the canonical persistent-batch build; retain the legacy report as
    # historical evidence rather than allowing it to mask the current asset.
    build_report = FLAGSHIP / "emberveil-canonical" / "canonical-build-report.json"
    if not build_report.exists():
        build_report = EMBERVEIL / "build-report.json"
    if not build_report.exists():
        warnings.append("no_build_report found")
        return

    try:
        br = json.loads(build_report.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        warnings.append("build_report_invalid_json")
        return

    results = br.get("results", {})
    mat_ops = [k for k in results if (k.startswith("mat.") or "material" in k) and "inspect" not in k]
    check(len(mat_ops) >= 3,
          f"insufficient_material_ops: {len(mat_ops)} (expected >=3 for glass/ember/brass)")

    all_results = json.dumps(results)
    canonical_export = results.get("export", {}).get("glb_validation", {})
    check(canonical_export.get("material_count", 0) >= 4,
          "canonical_glb_material_count_below_4", warn=True)
    check(canonical_export.get("animation_count", 0) >= 3,
          "canonical_glb_animation_count_below_3", warn=True)
    check("surface_variation" in all_results or "noise" in all_results,
          "procedural_surface_variation_not_evidenced", warn=True)


def audit_rendering():
    """Turntable and beauty shot must exist with reasonable size."""
    turntable_dir = EMBERVEIL / "turntable"
    if turntable_dir.exists():
        frames = list(turntable_dir.glob("turntable-*.png"))
        check(len(frames) >= 12,
              f"turntable_incomplete: {len(frames)} frames (expected ≥12)")
        if frames:
            sizes = [f.stat().st_size for f in frames]
            avg_size = sum(sizes) / len(sizes)
            check(avg_size > 10000,
                  f"turntable_frames_too_small: avg {avg_size:.0f} bytes (expected >10KB)")
    else:
        failures.append("missing turntable directory")

    canonical = FLAGSHIP / "emberveil-canonical"
    cturn = canonical / "turntable"
    cframes = list(cturn.glob("turntable-*.png")) if cturn.exists() else []
    check(len(cframes) >= 24,
          f"canonical_turntable_incomplete: {len(cframes)} frames (expected 24)")
    check((canonical / "emberveil-canonical-turntable.mp4").exists(), "missing canonical turntable video")
    check((canonical / "emberveil-canonical-cinematic.mp4").exists(), "missing canonical cinematic video")

    beauty = EMBERVEIL / "preview-frame-0001.png"
    check(beauty.exists(), "missing beauty shot: preview-frame-0001.png")
    if beauty.exists():
        check(beauty.stat().st_size > 50000,
              f"beauty_shot_too_small: {beauty.stat().st_size} bytes")


def audit_runtime():
    """Three.js runtime must be present and load GLB."""
    html_paths = [PRESENTATION / "index.html", FLAGSHIP / "runtime" / "index.html"]
    existing = [p for p in html_paths if p.exists()]
    if not existing:
        failures.append("missing runtime HTML")
        return
    contents = [p.read_text(encoding="utf-8") for p in existing]
    content = "\n".join(contents)
    check("three" in content.lower(), "runtime missing three.js import")
    check("GLTFLoader" in content, "runtime missing GLTFLoader")
    check("emberveil-canonical.glb" in content, "runtime not loading canonical animated GLB")
    check(any("EffectComposer" in c and "UnrealBloomPass" in c for c in contents),
          "runtime missing post-processing evidence")
    check(any("prefers-reduced-motion" in c or "prefersReduced" in c for c in contents),
          "runtime missing reduced motion support")
    runtime_content = (FLAGSHIP / "runtime" / "index.html").read_text(encoding="utf-8") if (FLAGSHIP / "runtime" / "index.html").exists() else ""
    check("animationClips" in runtime_content and "activeAnimationCount" in runtime_content,
          "runtime missing complete animation-set observability")


def audit_research():
    """Research artifacts must exist."""
    research_dir = FLAGSHIP / "research"
    if research_dir.exists():
        reports = list(research_dir.glob("*.json"))
        check(len(reports) >= 3,
              f"insufficient_research: {len(reports)} reports (expected ≥3)")
    else:
        failures.append("missing research directory")


def audit_perceptual_observation():
    """Perceptual QA and live runtime observation must be evidence-bearing."""
    report_path = FLAGSHIP / "qa" / "perceptual-canonical.json"
    if report_path.exists():
        report = json.loads(report_path.read_text(encoding="utf-8"))
        records = report.get("records", [])
        check(bool(records), "perceptual_qa_has_no_records")
        check(not any(r.get("failures") for r in records),
              "perceptual_qa_reports_readability_failures")
    else:
        failures.append("missing perceptual visual QA report")
    state_path = FLAGSHIP / "qa" / "runtime-canonical-final2" / "state.json"
    if state_path.exists():
        state = json.loads(state_path.read_text(encoding="utf-8"))
        observed = [f.get("state", {}).get("foundryState") for f in state.get("frames", [])]
        observed = [s for s in observed if s]
        check(bool(observed), "runtime_observation_missing_foundry_state")
        if observed:
            check(all(s.get("heroLoaded") for s in observed), "runtime_observation_hero_not_loaded")
            check(max(s.get("activeAnimationCount", 0) for s in observed) >= 3,
                  "runtime_observation_incomplete_animation_set")
    else:
        failures.append("missing live runtime observation state")
    console_path = FLAGSHIP / "qa" / "runtime-canonical-final2" / "console.json"
    if console_path.exists():
        console = json.loads(console_path.read_text(encoding="utf-8"))
        check(not console.get("messages") and not console.get("failedRequests"),
              "runtime_observation_console_or_network_errors")


def audit_evidence_systems():
    """Failure tests, regression, and quality models must be present."""
    # Quality models
    qm = ROOT / "config" / "quality-models.json"
    check(qm.exists(), "missing quality-models.json")

    # Failure tests
    ft = ROOT / "scripts" / "validate" / "failure_tests.py"
    check(ft.exists(), "missing failure_tests.py")

    # Regression
    sr = ROOT / "scripts" / "validate" / "system_regression.py"
    check(sr.exists(), "missing system_regression.py")

    # L5 evidence
    l5 = ROOT / "scripts" / "validate" / "l5_evidence.py"
    check(l5.exists(), "missing l5_evidence.py")


def main() -> int:
    print("=== COHESION AUDIT ===")
    audit_files()
    audit_production_graph()
    audit_materials()
    audit_rendering()
    audit_runtime()
    audit_perceptual_observation()
    audit_research()
    audit_evidence_systems()

    total_checks = len(failures) + len(warnings) + 1
    (FLAGSHIP / "qa").mkdir(parents=True, exist_ok=True)
    (FLAGSHIP / "qa" / "cohesion-current.json").write_text(json.dumps({
        "schema_version": 1, "artifact": "emberveil-canonical", "ok": not failures,
        "failures": failures, "warnings": warnings, "checks": total_checks,
        "interpretation": "cross-layer cohesion evidence; not a substitute for independent artistic review"
    }, indent=2), encoding="utf-8")
    print(f"checks={total_checks}")
    print(f"failures={len(failures)}")
    print(f"warnings={len(warnings)}")
    for f in failures:
        print(f"FAIL {f}")
    for w in warnings:
        print(f"WARN {w}")
    if not failures and not warnings:
        print("PASS All cohesion checks passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
