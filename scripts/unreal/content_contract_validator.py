#!/usr/bin/env python3
"""Reusable multi-stage Unreal content contract validator.

Produces one durable record per required asset across independent AUTHORING,
EDITOR, COOK, STAGE/ARCHIVE, and RUNTIME stages. Later evidence never erases
or substitutes for earlier-stage failures.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

try:
    from windows_env import foundry_subprocess_env, resolve_known_path, unreal_arg_path
except ImportError:  # pragma: no cover
    from scripts.unreal.windows_env import foundry_subprocess_env, resolve_known_path, unreal_arg_path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ENGINE_ROOT = Path("C:/Program Files/Epic Games/UE_5.8")
DEFAULT_PROJECT = ROOT / "artifacts/unreal/calibration/FoundryCalibration.uproject"
DEFAULT_MANIFEST = ROOT / "artifacts/unreal/calibration/ashwake-required-assets.json"
DEFAULT_ARCHIVE = ROOT / "artifacts/unreal/calibration/Packaged/Ashwake/Windows"
DEFAULT_OUT = ROOT / "artifacts/unreal/health/ashwake-required-assets-content-contract.json"

STAGES = ["AUTHORING", "EDITOR", "COOK", "STAGE_ARCHIVE", "RUNTIME"]
LOG_WARNING_PATTERN = re.compile(r"(Failed to find object|SkipPackage|Can't find file|Failed to load|Missing package|LogStreaming: Warning|LogUObjectGlobals: Warning)", re.I)
RUNTIME_LOAD_PATTERNS = [
    re.compile(r"ASSET_RUNTIME_LOADED Id=(\S+) ObjectPath=(\S+) ExpectedClass=(\S+) ActualClass=(\S+) RuntimeLoadable=(\d+)"),
    re.compile(r"ASSET_LOADED id=(\S+) object=(\S+) expected_class=(\S+) actual_class=(\S+) loaded=(true|false)", re.I),
]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def package_to_source_file(project_root: Path, package_path: str) -> Path:
    rel = package_path.removeprefix("/Game/")
    return (project_root / "Content" / Path(*rel.split("/"))).with_suffix(".uasset")


def default_engine_root(explicit: Path | None) -> Path:
    if explicit:
        return explicit
    if DEFAULT_ENGINE_ROOT.exists():
        return DEFAULT_ENGINE_ROOT
    candidates = sorted(Path("C:/Program Files/Epic Games").glob("UE_*") if Path("C:/Program Files/Epic Games").exists() else [])
    return candidates[-1] if candidates else DEFAULT_ENGINE_ROOT


def automation_log_slug(engine_root: Path) -> str:
    text = str(engine_root.resolve()).replace("\\", "/").rstrip("/")
    if re.match(r"^[A-Za-z]:/", text):
        text = text[0] + text[2:]
    return text.replace("/", "+").replace(" ", "+")


def discover_manifests(project_root: Path, archive_root: Path | None, stage_root: Path | None, engine_root: Path, explicit: list[Path]) -> list[dict[str, Any]]:
    names = ["Manifest_UFSFiles_Win64.txt", "FinalCopyWin64_UFSFiles.txt", "Manifest_NonUFSFiles_Win64.txt", "Manifest_DebugFiles_Win64.txt"]
    found: list[dict[str, Any]] = []
    seen: set[Path] = set()

    def add(path: Path, source: str, strength: int) -> None:
        try:
            resolved = path.resolve()
        except OSError:
            resolved = path
        if resolved in seen or not resolved.exists():
            return
        seen.add(resolved)
        found.append({"path": str(resolved), "source": source, "strength": strength, "mtime": resolved.stat().st_mtime})

    for path in explicit:
        add(path, "explicit", 100)
    if archive_root:
        for name in names:
            add(archive_root / name, "archive_root", 90)
    if stage_root:
        for name in names:
            add(stage_root / "Windows" / name, "stage_root_windows", 85)
            add(stage_root / name, "stage_root", 84)
    saved = project_root / "Saved"
    for staged in sorted(saved.glob("StagedBuilds*"), key=lambda p: p.stat().st_mtime if p.exists() else 0, reverse=True):
        for name in names:
            add(staged / "Windows" / name, "project_saved_staged_build", 70)
    appdata = resolve_known_path("APPDATA").path
    if appdata:
        log_root = Path(appdata) / "Unreal Engine" / "AutomationTool" / "Logs"
        preferred = log_root / automation_log_slug(engine_root)
        for name in names:
            add(preferred / name, "automation_tool_preferred", 60)
        if log_root.exists():
            for name in names:
                for path in sorted(log_root.rglob(name), key=lambda p: p.stat().st_mtime, reverse=True)[:20]:
                    add(path, "automation_tool_recursive", 40)
    found.sort(key=lambda item: (-item["strength"], -item["mtime"], item["path"]))
    return found


def load_manifest_entries(manifests: list[dict[str, Any]]) -> dict[str, list[str]]:
    entries: dict[str, list[str]] = {}
    for item in manifests:
        path = Path(item["path"])
        try:
            lines = [line.replace("\\", "/") for line in path.read_text(encoding="utf-8", errors="replace").splitlines() if line.strip()]
        except OSError:
            lines = []
        entries[str(path)] = lines
    return entries


def container_files(archive_root: Path | None, stage_root: Path | None) -> list[dict[str, Any]]:
    roots = []
    if archive_root:
        roots.append((archive_root, "archive"))
    if stage_root:
        roots.append((stage_root / "Windows", "stage"))
        roots.append((stage_root, "stage"))
    out = []
    seen: set[Path] = set()
    for root, source in roots:
        if not root.exists():
            continue
        for path in sorted(root.rglob("*")):
            if path.suffix.lower() in {".pak", ".ucas", ".utoc"} and path.is_file() and path.resolve() not in seen:
                seen.add(path.resolve())
                out.append({"path": str(path.resolve()), "source": source, "bytes": path.stat().st_size})
    return out


def runtime_text(paths: list[Path]) -> str:
    chunks = []
    for path in paths:
        if path and path.exists():
            chunks.append(path.read_text(encoding="utf-8", errors="replace"))
    return "\n".join(chunks)


def runtime_asset_loads(text: str) -> dict[str, list[dict[str, Any]]]:
    loads: dict[str, list[dict[str, Any]]] = {}
    for pattern in RUNTIME_LOAD_PATTERNS:
        for match in pattern.finditer(text):
            loaded = match.group(5) in {"1", "true", "TRUE", "True"}
            entry = {
                "id": match.group(1),
                "object_path": match.group(2),
                "expected_class": match.group(3),
                "actual_class": match.group(4),
                "runtime_loadable": loaded,
                "status": "PASS" if loaded and match.group(3) == match.group(4) else "FAIL",
                "evidence_source": "runtime_log",
            }
            loads.setdefault(entry["id"], []).append(entry)
    return loads


def runtime_component_active(asset: dict[str, Any], text: str) -> dict[str, Any]:
    logical_id = str(asset.get("id", ""))
    base = Path(asset.get("package_path", "")).name
    kind = asset.get("kind") or asset.get("expected_class")
    if kind == "NiagaraSystem":
        matches = [line.strip() for line in text.splitlines() if "VFX_STATE" in line and base in line and "active=true" in line and "spawn_rate=" in line and "energy=" in line and "color=" in line]
    elif kind == "SoundWave":
        matches = [line.strip() for line in text.splitlines() if "AUDIO_PLAYING" in line and (base in line or logical_id in line) and "playing=true" in line]
    elif kind == "AnimSequence":
        matches = [line.strip() for line in text.splitlines() if "ANIMATION_PLAYING" in line and (base in line or logical_id in line) and "playing=true" in line]
    else:
        matches = []
    return {"active": bool(matches), "evidence": matches[-5:]}


def run_editor_load_check(project: Path, manifest: Path, engine_root: Path, timeout: int) -> dict[str, Any]:
    editor = engine_root / "Engine/Binaries/Win64/UnrealEditor-Cmd.exe"
    if not editor.exists():
        return {"status": "UNAVAILABLE", "error": "UnrealEditor-Cmd.exe_missing", "engine_root": str(engine_root)}
    with tempfile.TemporaryDirectory() as td:
        script = Path(td) / "foundry_content_contract_editor_check.py"
        output = Path(td) / "asset-load.json"
        script.write_text(f"""
import json
from pathlib import Path
import unreal
manifest = json.loads(Path(r'{manifest}').read_text(encoding='utf-8'))
checks = []
for asset in manifest.get('required_assets', []):
    obj = unreal.load_asset(asset['object_path'])
    checks.append({{'id': asset.get('id'), 'expected_class': asset.get('kind') or asset.get('expected_class'), 'object_path': asset.get('object_path'), 'loaded': obj is not None, 'loaded_class': obj.get_class().get_name() if obj else None}})
report = {{'schema_version': 1, 'kind': 'foundry-editor-asset-load', 'status': 'PASS' if all(c['loaded'] and c['loaded_class'] == c['expected_class'] for c in checks) else 'FAIL', 'checks': checks}}
Path(r'{output}').write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps(report))
""", encoding="utf-8")
        cmd = [str(editor), unreal_arg_path(project), "-run=PythonScript", f"-script={unreal_arg_path(script)}", "-unattended", "-nop4", "-nosplash", "-nullrhi", "-NoSound", "-stdout", "-FullStdOutLogOutput", "-NoLogTimes"]
        started = time.monotonic()
        try:
            done = subprocess.run(cmd, cwd=project.parent, capture_output=True, text=True, timeout=timeout, env=foundry_subprocess_env())
            report = json.loads(output.read_text(encoding="utf-8")) if output.exists() else {"status": "FAIL", "error": "editor_report_missing"}
            report.update({"editor_exit_code": done.returncode, "duration_seconds": round(time.monotonic() - started, 3), "stdout_tail": (done.stdout or "")[-8000:], "stderr_tail": (done.stderr or "")[-8000:]})
            if done.returncode != 0:
                report["status"] = "FAIL"
            return report
        except subprocess.TimeoutExpired as exc:
            return {"schema_version": 1, "kind": "foundry-editor-asset-load", "status": "TIMEOUT", "duration_seconds": round(time.monotonic() - started, 3), "stdout_tail": str(exc.stdout or "")[-8000:], "stderr_tail": str(exc.stderr or "")[-8000:]}


def build_records(manifest: dict[str, Any], project_root: Path, manifest_entries: dict[str, list[str]], manifests: list[dict[str, Any]], archive_root: Path | None, stage_root: Path | None, editor_report: dict[str, Any], runtime: dict[str, list[dict[str, Any]]], runtime_log_text: str, containers: list[dict[str, Any]], quality_evidence: list[str]) -> list[dict[str, Any]]:
    editor_by_id = {c.get("id"): c for c in editor_report.get("checks", [])}
    records = []
    for asset in manifest.get("required_assets", []):
        logical_id = asset.get("id")
        expected_class = asset.get("kind") or asset.get("expected_class")
        package_path = asset.get("package_path")
        object_path = asset.get("object_path")
        source_file = package_to_source_file(project_root, package_path)
        rel = package_path.removeprefix("/Game/")
        package_entry = f"FoundryCalibration/Content/{rel}.uasset".lower()
        manifest_matches = [
            {"manifest": mpath, "line": line, "evidence_source": next((m["source"] for m in manifests if m["path"] == mpath), "unknown")}
            for mpath, lines in manifest_entries.items()
            for line in lines
            if package_entry in line.lower()
        ]
        archive_candidates = []
        if archive_root:
            archive_candidates.append((archive_root / "FoundryCalibration" / "Content" / Path(*rel.split("/"))).with_suffix(".uasset"))
        if stage_root:
            archive_candidates.append((stage_root / "Windows" / "FoundryCalibration" / "Content" / Path(*rel.split("/"))).with_suffix(".uasset"))
        archive_present = any(p.exists() for p in archive_candidates) or any(m["evidence_source"] in {"archive_root", "stage_root", "stage_root_windows", "project_saved_staged_build"} for m in manifest_matches)
        editor_check = editor_by_id.get(logical_id, {})
        runtime_entries = runtime.get(logical_id, [])
        runtime_loaded = any(e.get("status") == "PASS" and e.get("object_path") == object_path for e in runtime_entries)
        active = runtime_component_active(asset, runtime_log_text)
        failures = []
        if not source_file.exists():
            failures.append("AUTHORING_SOURCE_MISSING")
        if editor_report and not (editor_check.get("loaded") and editor_check.get("loaded_class") == expected_class):
            failures.append("EDITOR_LOAD_FAILED")
        if not manifest_matches:
            failures.append("COOK_MANIFEST_ENTRY_MISSING")
        if not archive_present:
            failures.append("ARCHIVE_EVIDENCE_MISSING")
        if runtime_log_text and not runtime_loaded:
            failures.append("RUNTIME_LOAD_MISSING")
        if runtime_log_text and expected_class in {"NiagaraSystem", "SoundWave", "AnimSequence"} and not active["active"]:
            failures.append("RUNTIME_COMPONENT_INACTIVE")
        records.append({
            "logical_id": logical_id,
            "expected_class": expected_class,
            "source_path": str(source_file),
            "editor_object_path": object_path,
            "source_present": source_file.exists(),
            "editor_loadable": bool(editor_check.get("loaded") and editor_check.get("loaded_class") == expected_class) if editor_report else None,
            "cook_required": True,
            "cooked_manifest_present": bool(manifest_matches),
            "cooked_manifest_evidence": manifest_matches[-10:],
            "archive_present": archive_present,
            "archive_candidates": [str(p) for p in archive_candidates],
            "runtime_loaded": runtime_loaded if runtime_log_text else None,
            "runtime_load_evidence": runtime_entries[-10:],
            "runtime_component_active": active["active"] if runtime_log_text else None,
            "runtime_component_evidence": active["evidence"],
            "quality_evidence": quality_evidence,
            "container_evidence": containers,
            "failure_reason": failures,
            "stages": {
                "AUTHORING": {"status": "PASS" if source_file.exists() else "FAIL", "evidence": str(source_file)},
                "EDITOR": {"status": "PASS" if editor_check.get("loaded") and editor_check.get("loaded_class") == expected_class else ("SKIPPED" if not editor_report else "FAIL"), "evidence": editor_check},
                "COOK": {"status": "PASS" if manifest_matches else "FAIL", "evidence": manifest_matches[-10:]},
                "STAGE_ARCHIVE": {"status": "PASS" if archive_present else "FAIL", "evidence": [str(p) for p in archive_candidates if p.exists()]},
                "RUNTIME": {"status": "PASS" if runtime_loaded and (active["active"] or expected_class not in {"NiagaraSystem", "SoundWave", "AnimSequence"}) else ("SKIPPED" if not runtime_log_text else "FAIL"), "evidence": {"loads": runtime_entries[-10:], "active": active}},
            },
        })
    return records


def stage_summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    summary = {}
    for stage in STAGES:
        statuses = [r["stages"][stage]["status"] for r in records]
        required_statuses = [s for s in statuses if s != "SKIPPED"]
        summary[stage] = {"status": "PASS" if required_statuses and all(s == "PASS" for s in required_statuses) else ("SKIPPED" if not required_statuses else "FAIL"), "pass": statuses.count("PASS"), "fail": statuses.count("FAIL"), "skipped": statuses.count("SKIPPED")}
    return summary


def scan_warnings(text: str, manifest: dict[str, Any] | None = None) -> list[str]:
    tokens = {"/Game/Calibration", "FoundryCalibration/Content/Calibration"}
    if manifest:
        for asset in manifest.get("required_assets", []):
            for key in ("id", "package_path", "object_path"):
                value = asset.get(key)
                if value:
                    tokens.add(str(value))
            package_path = str(asset.get("package_path") or "")
            if package_path:
                tokens.add(Path(package_path).name)
    return [line.strip() for line in text.splitlines() if LOG_WARNING_PATTERN.search(line) and any(token in line for token in tokens)][-100:]


def validate(args: argparse.Namespace) -> dict[str, Any]:
    project = args.project.resolve()
    project_root = project.parent
    manifest_path = args.manifest.resolve()
    manifest = load_json(manifest_path)
    engine = default_engine_root(args.engine_root).resolve()
    archive_root = args.archive_root.resolve() if args.archive_root else None
    stage_root = args.stage_root.resolve() if args.stage_root else None
    runtime_logs = [p.resolve() for p in args.runtime_log]
    runtime_log_text = runtime_text(runtime_logs)
    quality_evidence = [str(p.resolve()) for p in args.quality_evidence if p.exists()]
    manifests = discover_manifests(project_root, archive_root, stage_root, engine, [p.resolve() for p in args.ufs_manifest]) if args.cooked else []
    entries = load_manifest_entries(manifests)
    containers = container_files(archive_root, stage_root) if args.cooked else []
    editor_report = run_editor_load_check(project, manifest_path, engine, args.timeout) if args.editor_load else {}
    runtime_load = runtime_asset_loads(runtime_log_text)
    records = build_records(manifest, project_root, entries, manifests, archive_root, stage_root, editor_report, runtime_load, runtime_log_text, containers, quality_evidence)
    stages = stage_summary(records)
    failures = [r for r in records if r["failure_reason"]]
    warnings = scan_warnings(runtime_log_text, manifest)
    report = {
        "schema_version": 2,
        "kind": "foundry-content-contract-validation",
        "project": str(project),
        "manifest": str(manifest_path),
        "engine_root": str(engine),
        "archive_root": str(archive_root) if archive_root else None,
        "stage_root": str(stage_root) if stage_root else None,
        "runtime_logs": [str(p) for p in runtime_logs],
        "discovered_manifests": manifests,
        "containers": containers,
        "editor_load": editor_report,
        "asset_records": records,
        "stage_summary": stages,
        "runtime_reference_warnings": warnings,
        "status": "PASS" if not failures and not warnings else "FAIL",
        "failures": failures,
    }
    # Backwards-compatible fields for Ashwake callers.
    report["source_checks"] = [{"id": r["logical_id"], "kind": r["expected_class"], "object_path": r["editor_object_path"], "source_file": r["source_path"], "source_exists": r["source_present"]} for r in records]
    report["cooked_checks"] = [{"id": r["logical_id"], "package_path": next(a.get("package_path") for a in manifest.get("required_assets", []) if a.get("id") == r["logical_id"]), "cooked_exists": r["cooked_manifest_present"] and r["archive_present"], "runtime_loaded": r["runtime_loaded"], "runtime_component_active": r["runtime_component_active"], "failure_reason": r["failure_reason"]} for r in records]
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path, nargs="?", default=DEFAULT_MANIFEST)
    parser.add_argument("--project", type=Path, default=DEFAULT_PROJECT)
    parser.add_argument("--engine-root", type=Path)
    parser.add_argument("--editor-load", action="store_true")
    parser.add_argument("--cooked", action="store_true")
    parser.add_argument("--archive-root", type=Path, default=DEFAULT_ARCHIVE)
    parser.add_argument("--stage-root", type=Path)
    parser.add_argument("--ufs-manifest", action="append", type=Path, default=[])
    parser.add_argument("--runtime-log", action="append", type=Path, default=[])
    parser.add_argument("--required-runtime-log", type=Path)
    parser.add_argument("--quality-evidence", action="append", type=Path, default=[])
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    if args.required_runtime_log:
        args.runtime_log.append(args.required_runtime_log)
    report = validate(args)
    text = json.dumps(report, indent=2, ensure_ascii=False)
    print(text)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
