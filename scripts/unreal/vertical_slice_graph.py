#!/usr/bin/env python3
"""Derive a vertical-slice production graph from game-design requirements."""
from __future__ import annotations
import argparse, json
from pathlib import Path


def build(spec: dict) -> dict:
    nodes = []
    edges = []
    def add(node_id, kind, label, evidence=None):
        nodes.append({"id": node_id, "kind": kind, "label": label, "evidence": evidence or []})
    def edge(a, b, relation): edges.append({"from": a, "to": b, "relation": relation})
    add("design", "design", spec["title"], ["artifacts/unreal/calibration/emberveil-game-design.json"])
    add("input", "runtime", "Enhanced Input actions and mapping context", ["artifacts/unreal/calibration/Source/FoundryCalibration/FoundryPlayerCharacter.cpp"])
    add("player", "gameplay", "player character movement and camera", ["artifacts/unreal/calibration/Source/FoundryCalibration/FoundryPlayerCharacter.cpp", "artifacts/unreal/health/foundry-compile-evidence.json"])
    add("state", "gameplay", "explicit START/PLAYING/SUCCESS/FAILURE/RESTART state", ["artifacts/unreal/calibration/Source/FoundryCalibration/FoundryGameState.cpp", "artifacts/unreal/health/foundry-compile-evidence.json"])
    add("reliquary", "gameplay", "attunement mechanic and deterministic shrine response", ["artifacts/unreal/calibration/Source/FoundryCalibration/FoundryRelicActor.cpp"])
    add("level", "world", "designed shrine chamber and recoverable encounter path", ["artifacts/unreal/calibration/map-authoring-report.json"])
    add("challenge", "ai", spec["ai_systemic_opposition"]["type"], ["artifacts/unreal/calibration/Source/FoundryCalibration/FoundryRelicActor.cpp"])
    add("mesh", "asset", "Emberveil imported skeletal mesh and authored environment assets", ["artifacts/unreal/calibration/emberveil-game-design.json", "artifacts/unreal/health/foundry-calibration-datavalidation-vfx.json"])
    add("materials", "asset", "parameterized brass/glass/core material instances", ["artifacts/unreal/health/foundry-calibration-datavalidation-vfx.json"])
    add("animation", "animation", ", ".join(spec["animation_requirements"]), ["artifacts/unreal/health/foundry-calibration-datavalidation-vfx.json"])
    add("vfx", "vfx", ", ".join(v["event"] for v in spec["vfx_requirements"]), ["artifacts/unreal/calibration/niagara-calibration-report.json"])
    add("audio", "audio", ", ".join(spec["audio_requirements"]), ["artifacts/unreal/calibration/audio-import-report.json"])
    add("ui", "ui", ", ".join(spec["ui_requirements"]), ["artifacts/unreal/calibration/Source/FoundryCalibration/FoundryHUD.cpp"])
    add("tests", "verification", "native state tests, functional scenario, content validation", ["artifacts/unreal/calibration/Source/FoundryCalibration/FoundryGameStateTests.cpp", "artifacts/unreal/health/native-test-discovery.json", "artifacts/unreal/health/foundry-calibration-datavalidation-vfx.json"])
    add("runtime", "observation", "play capture, logs, state telemetry, visual QA", ["artifacts/unreal/health/foundry-runtime-observation-trace.json"])
    add("package", "release", "Windows packaged build and launch verification", ["artifacts/unreal/health/foundry-package-preflight.json"])
    for a, b, r in [("design", "input", "requires"), ("input", "player", "drives"), ("player", "reliquary", "enables"), ("reliquary", "state", "mutates"), ("state", "challenge", "controls"), ("challenge", "level", "occupies"), ("level", "mesh", "uses"), ("mesh", "materials", "assigns"), ("reliquary", "animation", "synchronizes"), ("reliquary", "vfx", "signals"), ("reliquary", "audio", "signals"), ("state", "ui", "drives"), ("state", "tests", "verified_by"), ("tests", "runtime", "observed_in"), ("runtime", "package", "qualifies")]: edge(a, b, r)
    for item in spec.get("mechanics", []):
        mid = "mechanic-" + item["id"]
        add(mid, "mechanic", item["id"], item["evidence"])
        edge("design", mid, "traces")
        edge(mid, "reliquary", "implemented_by")
        edge(mid, "tests", "tested_by")
    return {"schema_version": 1, "kind": "unreal-vertical-slice-production-graph", "title": spec["title"], "nodes": nodes, "edges": edges, "quality_ladder": spec.get("quality_ladder"), "evidence_semantics": "Evidence pointers prove implementation or inspection only; they do not promote quality without runtime/playtest evidence.", "limitations": ["Graph derivation does not prove the referenced runtime systems exist until Unreal project inspection and play evidence are attached.", "Runtime currently fails before map load because loose-content asset registry/cook evidence is unavailable."]}


def main() -> int:
    p = argparse.ArgumentParser(); p.add_argument("spec", type=Path); p.add_argument("out", type=Path)
    args = p.parse_args(); result = build(json.loads(args.spec.read_text(encoding="utf-8"))); args.out.parent.mkdir(parents=True, exist_ok=True); args.out.write_text(json.dumps(result, indent=2), encoding="utf-8"); print(json.dumps({"nodes": len(result["nodes"]), "edges": len(result["edges"]), "quality_ladder": result["quality_ladder"]})); return 0

if __name__ == "__main__": raise SystemExit(main())
