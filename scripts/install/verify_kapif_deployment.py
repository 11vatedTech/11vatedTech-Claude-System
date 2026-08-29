#!/usr/bin/env python3
"""Verify physical global installation hashes for KAPIF and managed runtime files."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
GLOBAL = Path.home() / ".claude" / "11vatedtech" / "capability-system"
DEPLOYMENTS = Path.home() / ".claude" / "11vatedtech" / "deployments"

KAPIF_RELATIVE = [
    "scripts/kapif/__init__.py", "scripts/kapif/data_layer.py", "scripts/kapif/db.py",
    "scripts/kapif/fts_index.py", "scripts/kapif/embeddings.py", "scripts/kapif/hybrid_retrieval.py",
    "scripts/kapif/professional_extractor.py", "scripts/kapif/llm_extractor.py",
    "scripts/kapif/model_intelligence.py", "scripts/kapif/model_tournaments.py",
    "scripts/kapif/visual_intelligence.py", "scripts/kapif/canon_pipeline.py",
    "scripts/kapif/security.py", "scripts/kapif/content_normalizer.py",
    "scripts/kapif/mission_compiler.py", "scripts/kapif/knowledge_extractor.py",
    "scripts/kapif/closure_gates_pass06.py", "scripts/kapif/golden_tasks_m002.py",
    "scripts/kapif/behavioral_validation_m0021.py", "scripts/kapif/injection_e2e_validation.py",
    "config/foundry-failure-patterns.json", "config/M002-truth-correction.json",
]

RUNTIME_REQUIRED = sorted(set(KAPIF_RELATIVE + [
    "VERSION",
    "scripts/doctor/foundry_doctor.py",
    "scripts/validate/foundry_validate.py",
    "scripts/validate/canonical_truth_generator.py",
    "scripts/validate/capability_truth_audit.py",
    "scripts/validate/tool_resolver.py",
    "scripts/mission/foundry_mission.py",
    "scripts/install/foundry_sync.py",
    "scripts/install/sync_to_claude.py",
    "scripts/install/verify_kapif_deployment.py",
    "config/product-portfolio-registry.json",
    "config/capability-ontology.json",
    "config/capability-truth-audit.json",
    "config/model-role-registry-vision.json",
    "config/resource-packs/art-direction-lookdev-core.json",
    "config/resource-packs/frontend-ui-ux-core.json",
    "config/resource-packs/composition-value-color-core.json",
    "config/resource-packs/typography-information-design-core.json",
    "config/resource-packs/ui-ux-interaction-core.json",
    "config/resource-packs/motion-design-core.json",
    "config/kapif/cross-pack-graph.json",
    "config/kapif/source-scope.json",
    "docs/product-repository-boundary.md",
]))


def sha(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def latest_manifest() -> dict[str, Any] | None:
    if not DEPLOYMENTS.exists():
        return None
    manifests = sorted(DEPLOYMENTS.glob("*.json"))
    if not manifests:
        return None
    return json.loads(manifests[-1].read_text(encoding="utf-8"))


def load_sync_module() -> Any | None:
    path = ROOT / "scripts" / "install" / "sync_to_claude.py"
    if not path.exists():
        return None
    spec = importlib.util.spec_from_file_location("sync_to_claude", path)
    if not spec or not spec.loader:
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def source_desired_files() -> dict[str, str] | None:
    module = load_sync_module()
    if module is None or not module.source_mode():
        return None
    return module.manifest_for(module.collect_all())


def dry_run_to_update() -> int | None:
    script = ROOT / "scripts" / "install" / "sync_to_claude.py"
    if not script.exists():
        return None
    proc = subprocess.run([sys.executable, str(script), "--dry-run"], cwd=str(ROOT), capture_output=True, text=True, timeout=30)
    for line in proc.stdout.splitlines():
        if line.startswith("to_update="):
            return int(line.split("=", 1)[1])
    return None


def run() -> dict[str, Any]:
    desired = source_desired_files()
    manifest = latest_manifest()
    if desired is None and manifest:
        desired = manifest.get("files", {})
    desired = desired or {}

    kapif_rows = []
    for rel in KAPIF_RELATIVE:
        source = ROOT / rel
        installed = GLOBAL / rel
        source_hash = sha(source)
        installed_hash = sha(installed)
        kapif_rows.append({
            "relative": rel,
            "source": str(source),
            "installed": str(installed),
            "source_sha256": source_hash,
            "installed_sha256": installed_hash,
            "match": bool(source_hash and source_hash == installed_hash) if (ROOT / ".git").exists() else bool(installed_hash),
        })

    missing_runtime_modules = [rel for rel in RUNTIME_REQUIRED if not (GLOBAL / rel).exists()]
    hash_mismatches = []
    missing_managed = []
    for managed_name, expected in desired.items():
        if not managed_name.startswith("capability-system/"):
            installed = Path.home() / ".claude" / managed_name
        else:
            installed = GLOBAL / managed_name[len("capability-system/"):]
        actual_hash = sha(installed)
        if actual_hash is None:
            missing_managed.append(managed_name)
        elif expected != "sha256:" + actual_hash:
            hash_mismatches.append({"relative": managed_name, "expected": expected, "actual": "sha256:" + actual_hash})

    unexplained_managed_files = []
    if manifest and desired:
        manifest_files = set(manifest.get("files", {}))
        desired_files = set(desired)
        unexplained_managed_files = sorted(manifest_files - desired_files)

    to_update = dry_run_to_update()
    status = "PASS" if (
        not missing_runtime_modules and
        not missing_managed and
        not hash_mismatches and
        not unexplained_managed_files and
        to_update == 0 and
        all(r["match"] for r in kapif_rows)
    ) else "FAIL"

    result = {
        "schema_version": 2,
        "kind": "kapif-global-hash-proof",
        "global_root": str(GLOBAL),
        "deployment_id": manifest.get("id") if manifest else None,
        "deployment_source_sha": manifest.get("source_sha") if manifest else None,
        "managed_file_count": len(desired),
        "missing_runtime_modules": missing_runtime_modules,
        "missing_managed_files": missing_managed,
        "unexplained_managed_files": unexplained_managed_files,
        "hash_mismatches": hash_mismatches,
        "to_update": to_update,
        "status": status,
        "files": kapif_rows,
    }
    out = ROOT / "artifacts" / "kapif" / "m002.1" / "global-hash-proof.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--quiet", action="store_true", help="accepted for validator compatibility")
    parser.parse_args()
    return 0 if run()["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
