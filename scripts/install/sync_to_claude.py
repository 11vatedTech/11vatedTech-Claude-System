#!/usr/bin/env python3
"""Deploy the canonical 11vatedTech-Claude-System Foundry into the global
~/.claude installation.

This is the strengthened deployment mechanism for the global architecture:

    11vatedTech-Claude-System  (develop / research / build / test)
            |  sync_to_claude.py  (validated Foundry intelligence)
            v
    C:/Users/11vat/.claude      (available in every project)

Safety properties:
- A timestamped backup of every touched target is written before any change.
- A deployment manifest (version, file inventory, sha256) is recorded under
  ~/.claude/11vatedtech/deployments/ so any deployment can be rolled back.
- --dry-run reports drift without writing.
- --rollback <deployment_id> restores a previous deployment from its backup.
- Stale 11vt-* skills/agents present globally but absent from the repo are
  reported (and only removed with --prune, never by default).

Targets synced:
- skills:            plugin/skills/*/      -> ~/.claude/skills/
- agents:            plugin/agents/*.md    -> ~/.claude/agents/
- capability-system: docs/* + validate     -> ~/.claude/11vatedtech/capability-system/
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
HOME = Path.home()
CLAUDE_DIR = HOME / ".claude"
SKILLS_DST = CLAUDE_DIR / "skills"
AGENTS_DST = CLAUDE_DIR / "agents"
CAPSYS_DST = CLAUDE_DIR / "11vatedtech" / "capability-system"
DEPLOYMENTS_DIR = CLAUDE_DIR / "11vatedtech" / "deployments"
BACKUPS_DIR = CLAUDE_DIR / "backups"

# repo docs -> capability-system destination names
CAPSYS_MAP: dict[str, str] = {
    "docs/capability-registry.md": "capability-registry.md",
    "docs/memory-architecture.md": "memory-architecture.md",
    "docs/source-ledger.md": "source-ledger.md",
    "docs/update-procedure.md": "update-procedure.md",
    "docs/rollback-procedure.md": "rollback-procedure.md",
    "docs/upgrade-record-2026-08-15.md": "upgrade-record-2026-08-15.md",
    "scripts/install/validate_capability_installation.py": "scripts/validate-capabilities.py",
    "scripts/validate/perceptual_visual_qa.py": "scripts/validate/perceptual_visual_qa.py",
    "scripts/validate/asset_variant_diff.py": "scripts/validate/asset_variant_diff.py",
    "scripts/validate/flagship_evidence.py": "scripts/validate/flagship_evidence.py",
    "scripts/validate/cohesion_audit.py": "scripts/validate/cohesion_audit.py",
    "scripts/repo/semantic_intelligence.py": "scripts/repo/semantic_intelligence.py",
    "scripts/repo/multilang_semantic_intelligence.py": "scripts/repo/multilang_semantic_intelligence.py",
    "scripts/validate/repo_semantic_golden_tasks.py": "scripts/validate/repo_semantic_golden_tasks.py",
    "scripts/validate/unreal_foundry_tests.py": "scripts/validate/unreal_foundry_tests.py",
    "scripts/validate/router_health.py": "scripts/validate/router_health.py",
    "scripts/validate/capability_truth_audit.py": "scripts/validate/capability_truth_audit.py",
    "scripts/validate/mission_value_gate.py": "scripts/validate/mission_value_gate.py",
    "scripts/validate/visual_evidence_evaluator.py": "scripts/validate/visual_evidence_evaluator.py",
    "scripts/validate/model_router.py": "scripts/validate/model_router.py",
    "scripts/validate/model_golden_tasks.py": "scripts/validate/model_golden_tasks.py",
    "scripts/validate/foundry_ascension_tests.py": "scripts/validate/foundry_ascension_tests.py",
    "scripts/validate/creative_micro_lab.py": "scripts/validate/creative_micro_lab.py",
    "scripts/validate/frontend_quality_contract.py": "scripts/validate/frontend_quality_contract.py",
    "scripts/ascension/build_capability_truth_audit.py": "scripts/ascension/build_capability_truth_audit.py",
    "scripts/ascension/mission_compiler.py": "scripts/ascension/mission_compiler.py",
    "config/capability-truth-audit.json": "config/capability-truth-audit.json",
    "config/capability-gap-register.json": "config/capability-gap-register.json",
    "config/creative-intelligence-institute.json": "config/creative-intelligence-institute.json",
    "config/experience-game-design-institute.json": "config/experience-game-design-institute.json",
    "config/frontend-ui-ux-institute.json": "config/frontend-ui-ux-institute.json",
    "config/maturity-and-knowledge-contract.json": "config/maturity-and-knowledge-contract.json",
    "config/resource-packs/frontend-ui-ux-core.json": "config/resource-packs/frontend-ui-ux-core.json",
    "config/resource-packs/art-direction-lookdev-core.json": "config/resource-packs/art-direction-lookdev-core.json",
    "config/resource-packs/semantic-engineering-core.json": "config/resource-packs/semantic-engineering-core.json",
    "config/missions/capability-ascension-20260822.json": "config/missions/capability-ascension-20260822.json",
    "config/model-capability-registry.json": "config/model-capability-registry.json",
    "artifacts/ascension/model-selection-matrix.json": "artifacts/ascension/model-selection-matrix.json",
    "artifacts/ascension/CREATIVE-INTELLIGENCE-CONTINUITY-20260822.json": "artifacts/ascension/CREATIVE-INTELLIGENCE-CONTINUITY-20260822.json",
    "artifacts/ascension/research/creative-intelligence-source-ledger-20260822.json": "artifacts/ascension/research/creative-intelligence-source-ledger-20260822.json",
    "artifacts/ascension/micro-labs/frontend-contract-fixture.json": "artifacts/ascension/micro-labs/frontend-contract-fixture.json",
    "artifacts/ascension/micro-labs/frontend-quality-contract.json": "artifacts/ascension/micro-labs/frontend-quality-contract.json",
    "artifacts/ascension/micro-labs/creative-lab-fixture.json": "artifacts/ascension/micro-labs/creative-lab-fixture.json",
    "scripts/unreal/unreal_intelligence.py": "scripts/unreal/unreal_intelligence.py",
    "scripts/unreal/editor_import_probe.py": "scripts/unreal/editor_import_probe.py",
    "scripts/unreal/game_design.py": "scripts/unreal/game_design.py",
    "scripts/unreal/agent_coverage.py": "scripts/unreal/agent_coverage.py",
    "scripts/unreal/concept_lab.py": "scripts/unreal/concept_lab.py",
    "scripts/unreal/vertical_slice_graph.py": "scripts/unreal/vertical_slice_graph.py",
    "scripts/unreal/build_pipeline.py": "scripts/unreal/build_pipeline.py",
    "scripts/unreal/blender_unreal_bridge.py": "scripts/unreal/blender_unreal_bridge.py",
    "scripts/assets/asset_vault.py": "scripts/assets/asset_vault.py",
    "scripts/assets/asset_resolver.py": "scripts/assets/asset_resolver.py",
    "scripts/assets/requirement_discovery.py": "scripts/assets/requirement_discovery.py",
    "scripts/media/vtmedia/blender_ops.py": "scripts/media/vtmedia/blender_ops.py",
    "scripts/media/vtmedia/blender_scripts/op_runner.py": "scripts/media/vtmedia/blender_scripts/op_runner.py",
    "scripts/media/vtmedia/common.py": "scripts/media/vtmedia/common.py",
    "scripts/media/vtmedia/image_tools.py": "scripts/media/vtmedia/image_tools.py",
    "scripts/media/vtmedia/ffmpeg_tools.py": "scripts/media/vtmedia/ffmpeg_tools.py",
    "scripts/media/vtmedia/blender_bridge.py": "scripts/media/vtmedia/blender_bridge.py",
    "scripts/media/vtmedia/__init__.py": "scripts/media/vtmedia/__init__.py",
    "config/capability-ontology.json": "config/capability-ontology.json",
    "config/quality-models.json": "config/quality-models.json",
    # ── Operationalization Sprint (2026-08-22) ──
    "scripts/repo/lsp_client.py": "scripts/repo/lsp_client.py",
    "scripts/repo/semantic_code_bus.py": "scripts/repo/semantic_code_bus.py",
    "scripts/frontend/runtime_harness.py": "scripts/frontend/runtime_harness.py",
    "scripts/validate/tiered_regression.py": "scripts/validate/tiered_regression.py",
    "scripts/validate/lexical_vs_semantic_benchmark.py": "scripts/validate/lexical_vs_semantic_benchmark.py",
    "artifacts/benchmarks/lexical-vs-semantic.json": "artifacts/benchmarks/lexical-vs-semantic.json",
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def manifest_for(sources: dict[str, Path]) -> dict[str, str]:
    return {name: "sha256:" + sha256_file(p) for name, p in sources.items()}


def collect_skills() -> dict[str, Path]:
    out: dict[str, Path] = {}
    for d in (ROOT / "plugin" / "skills").iterdir():
        if d.is_dir() and (d / "SKILL.md").exists():
            out[f"skills/{d.name}/SKILL.md"] = d / "SKILL.md"
    return out


def collect_agents() -> dict[str, Path]:
    out: dict[str, Path] = {}
    for f in (ROOT / "plugin" / "agents").glob("*.md"):
        out[f"agents/{f.name}"] = f
    return out


def collect_capsys() -> dict[str, Path]:
    out: dict[str, Path] = {}
    for rel, dst in CAPSYS_MAP.items():
        src = ROOT / rel
        if src.exists():
            out[f"capability-system/{dst}"] = src
    return out


def collect_all() -> dict[str, Path]:
    out: dict[str, Path] = {}
    out.update(collect_skills())
    out.update(collect_agents())
    out.update(collect_capsys())
    return out


def dst_for(name: str) -> Path:
    if name.startswith("skills/"):
        return SKILLS_DST / name[len("skills/") :]
    if name.startswith("agents/"):
        return AGENTS_DST / name[len("agents/") :]
    if name.startswith("capability-system/"):
        return CAPSYS_DST / name[len("capability-system/") :]
    raise ValueError(f"unknown target: {name}")


def current_state() -> dict[str, str]:
    out: dict[str, str] = {}
    for name in collect_all():
        p = dst_for(name)
        if p.exists():
            out[name] = "sha256:" + sha256_file(p)
    return out


def detect_stale() -> list[str]:
    """11vt-* skills/agents present globally but absent from the repo."""
    repo_skills = {d.name for d in (ROOT / "plugin" / "skills").iterdir() if d.is_dir()}
    repo_agents = {f.stem for f in (ROOT / "plugin" / "agents").glob("*.md")}
    stale: list[str] = []
    if SKILLS_DST.exists():
        for d in SKILLS_DST.iterdir():
            if d.is_dir() and d.name.startswith("11vt-") and d.name not in repo_skills:
                stale.append(f"skills/{d.name}")
    if AGENTS_DST.exists():
        for f in AGENTS_DST.glob("11vt-*.md"):
            if f.stem not in repo_agents:
                stale.append(f"agents/{f.name}")
    return sorted(stale)


def backup_targets(deployment_id: str) -> Path:
    backup_dir = BACKUPS_DIR / f"deploy-{deployment_id}"
    backup_dir.mkdir(parents=True, exist_ok=True)
    for name in collect_all():
        src = dst_for(name)
        if not src.exists():
            continue
        rel = Path(name)
        target = backup_dir / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if src.is_dir():
            shutil.copytree(src, target, dirs_exist_ok=True)
        else:
            shutil.copy2(src, target)
    return backup_dir


def write_file_safely(name: str, src: Path) -> None:
    dst = dst_for(name)
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.is_dir():
        shutil.copytree(src, dst, dirs_exist_ok=True)
    else:
        shutil.copy2(src, dst)


def sync(dry_run: bool = False, prune: bool = False, no_backup: bool = False) -> int:
    sources = collect_all()
    current = current_state()
    desired = manifest_for(sources)

    to_write = [n for n in desired if current.get(n) != desired[n]]
    stale = detect_stale() if prune else []
    stale = [s for s in stale if s not in desired]  # never prune a managed file

    print(f"version={read_version()}")
    print(f"managed_files={len(desired)}")
    print(f"to_update={len(to_write)}")
    for n in sorted(to_write):
        print(f"  update {n}")
    if stale:
        print(f"stale_11vt_removable={stale}")
    else:
        print("stale_11vt_removable=[]")

    if dry_run:
        print("dry_run=True no_changes_written")
        return 0

    deployment_id = time.strftime("%Y%m%d-%H%M%S")
    backup_dir = None if no_backup else backup_targets(deployment_id)

    for n in sorted(to_write):
        write_file_safely(n, sources[n])
    for s in stale:
        p = dst_for(s)
        if p.is_dir():
            shutil.rmtree(p)
        else:
            p.unlink(missing_ok=True)
        print(f"  pruned {s}")

    manifest = {
        "id": deployment_id,
        "created": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "version": read_version(),
        "backup_dir": str(backup_dir) if backup_dir else None,
        "updated": sorted(to_write),
        "pruned": stale,
        "files": desired,
    }
    DEPLOYMENTS_DIR.mkdir(parents=True, exist_ok=True)
    (DEPLOYMENTS_DIR / f"{deployment_id}.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"deployment_id={deployment_id}")
    if backup_dir:
        print(f"backup_dir={backup_dir}")
    print(f"manifest={DEPLOYMENTS_DIR / deployment_id}.json")
    return 0


def rollback(deployment_id: str) -> int:
    manifest_path = DEPLOYMENTS_DIR / f"{deployment_id}.json"
    if not manifest_path.exists():
        print(f"no_manifest {deployment_id}")
        return 1
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    backup_dir = Path(manifest["backup_dir"]) if manifest.get("backup_dir") else None
    if not backup_dir or not backup_dir.exists():
        print(f"no_backup {deployment_id} at {backup_dir}")
        return 1
    restored: list[str] = []
    for rel in manifest.get("files", {}):
        src = backup_dir / rel
        if src.exists():
            write_file_safely(rel, src)
            restored.append(rel)
    manifest["rolled_back"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    manifest["restored"] = restored
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"restored={len(restored)} from {backup_dir}")
    return 0


def list_deployments() -> int:
    if not DEPLOYMENTS_DIR.exists():
        print("deployments=[]")
        return 0
    for p in sorted(DEPLOYMENTS_DIR.glob("*.json")):
        m = json.loads(p.read_text(encoding="utf-8"))
        print(f"{m['id']} version={m.get('version')} updated={len(m.get('updated', []))} rolled_back={bool(m.get('rolled_back'))}")
    return 0


def read_version() -> str:
    return (ROOT / "VERSION").read_text(encoding="utf-8").strip()


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="sync_to_claude")
    p.add_argument("--dry-run", action="store_true", help="report drift without writing")
    p.add_argument("--prune", action="store_true", help="remove stale 11vt-* skills/agents absent from the repo")
    p.add_argument("--no-backup", action="store_true", help="skip the pre-sync backup (not recommended)")
    p.add_argument("--rollback", metavar="DEPLOYMENT_ID", help="restore a previous deployment from its backup")
    p.add_argument("--list", action="store_true", help="list recorded deployments")
    args = p.parse_args(argv)
    if args.list:
        return list_deployments()
    if args.rollback:
        return rollback(args.rollback)
    return sync(dry_run=args.dry_run, prune=args.prune, no_backup=args.no_backup)


if __name__ == "__main__":
    sys.exit(main())
