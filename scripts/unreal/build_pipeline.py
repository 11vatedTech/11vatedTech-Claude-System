#!/usr/bin/env python3
"""Bounded Unreal build/package wrapper; never exposes giant ad-hoc UAT commands."""
from __future__ import annotations
import argparse, hashlib, json, os, re, subprocess, time
from pathlib import Path
from typing import Any

try:
    from unreal_intelligence import toolchain_health
except ImportError:
    toolchain_health = None

from windows_env import foundry_subprocess_env, unreal_arg_path, path_report

ROOT = Path(__file__).resolve().parents[2]

def engine_root(explicit: Path | None) -> Path:
    if explicit: return explicit
    env = os.environ.get("UNREAL_ENGINE_ROOT")
    if env: return Path(env)
    candidates = sorted(Path("C:/Program Files/Epic Games").glob("UE_*") if Path("C:/Program Files/Epic Games").exists() else [])
    if not candidates: raise FileNotFoundError("no Unreal engine root")
    return candidates[-1]

def execute(args: list[str], cwd: Path, timeout: int) -> dict[str, Any]:
    started = time.monotonic()
    try:
        p = subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=timeout, env=foundry_subprocess_env())
        return {"status": "PASS" if p.returncode == 0 else "FAIL", "exit_code": p.returncode, "duration_seconds": round(time.monotonic() - started, 3), "stdout_tail": p.stdout[-12000:], "stderr_tail": p.stderr[-12000:]}
    except subprocess.TimeoutExpired as exc:
        return {"status": "TIMEOUT", "exit_code": None, "duration_seconds": round(time.monotonic() - started, 3), "stdout_tail": str(exc.stdout or "")[-12000:], "stderr_tail": str(exc.stderr or "")[-12000:]}

def compile_target(project: Path, target: str, config: str, explicit_engine: Path | None, timeout: int) -> dict[str, Any]:
    if not re.fullmatch(r"[A-Za-z0-9_]+", target) or config not in {"DebugGame", "Development", "Shipping", "Test"}:
        return {"schema_version": 1, "kind": "unreal-compile", "status": "REJECTED", "error": "invalid_target_or_configuration"}
    project = project.resolve(); root = engine_root(explicit_engine); bat = root / "Engine/Build/BatchFiles/Build.bat"
    if not project.exists() or not bat.exists(): return {"schema_version": 1, "kind": "unreal-compile", "status": "UNAVAILABLE", "error": "project_or_build_bat_missing"}
    result = execute([str(bat), target, "Win64", config, unreal_arg_path(project), "-WaitMutex", "-NoHotReloadFromIDE"], project.parent, timeout)
    result.update({"schema_version": 1, "kind": "unreal-compile", "project": str(project), "target": target, "configuration": config, "engine_root": str(root), "path_resolution": {"project": path_report(project), "engine_root": path_report(root)}})
    return result

def package(project: Path, archive: Path, explicit_engine: Path | None, config: str, timeout: int, staging_dir: Path | None = None) -> dict[str, Any]:
    if config not in {"Development", "Shipping", "Test"}: return {"schema_version": 1, "kind": "unreal-package", "status": "REJECTED", "error": "invalid_configuration"}
    project = project.resolve(); archive = archive.resolve(); staging_dir = staging_dir.resolve() if staging_dir else None; root = engine_root(explicit_engine); uat = root / "Engine/Build/BatchFiles/RunUAT.bat"
    if not project.exists() or not uat.exists(): return {"schema_version": 1, "kind": "unreal-package", "status": "UNAVAILABLE", "error": "project_or_uat_missing"}
    # BuildCookRun with a C++ project first builds the Editor target. Keep the
    # missing prerequisite explicit instead of spending time on a guaranteed
    # UAT failure or misreporting a game-target compile as package readiness.
    netfx_roots = [Path("C:/Program Files (x86)/Windows Kits/NETFXSDK"), Path("C:/Program Files/Windows Kits/NETFXSDK"), Path("C:/Program Files (x86)/Microsoft SDKs/NETFXSDK"), Path("C:/Program Files/Microsoft SDKs/NETFXSDK")]
    if toolchain_health is not None:
        netfx_ready = bool(toolchain_health().get("netfx_sdk", {}).get("available"))
    else:
        netfx_ready = any((version / "Include/um").exists() and (version / "Lib/um").exists() for base in netfx_roots if base.exists() for version in base.iterdir() if version.is_dir())
    if (project.parent / "Source").exists() and not netfx_ready:
        return {"schema_version": 1, "kind": "unreal-package", "status": "BLOCKED", "error": "editor_target_prerequisite_missing", "missing_component": "Microsoft.Net.Component.4.8.SDK", "reason": "UnrealBuildTool SwarmInterface requires a .NET Framework SDK (4.6+); install the component in the existing Visual Studio Build Tools instance", "project": str(project), "archive": str(archive), "configuration": config, "engine_root": str(root)}
    archive.parent.mkdir(parents=True, exist_ok=True)
    run_id = f"package-{int(time.time() * 1000)}"
    args = [str(uat), "BuildCookRun", f"-project={unreal_arg_path(project)}", "-noP4", "-build", "-cook", "-stage", "-pak", "-archive", f"-archivedirectory={unreal_arg_path(archive)}", "-platform=Win64", f"-clientconfig={config}", "-utf8output"]
    if staging_dir:
        staging_dir.mkdir(parents=True, exist_ok=True)
        args.append(f"-stagingdirectory={unreal_arg_path(staging_dir)}")
    result = execute(args, project.parent, timeout)
    manifest_candidates = []
    for root_dir in [archive, staging_dir / "Windows" if staging_dir else None, project.parent / "Saved" / (staging_dir.name if staging_dir else "") / "Windows" if staging_dir else None]:
        if root_dir and root_dir.exists():
            manifest_candidates.extend(str(p.resolve()) for p in root_dir.glob("Manifest_*Win64.txt"))
    result.update({"schema_version": 1, "kind": "unreal-package", "run_id": run_id, "project": str(project), "archive": str(archive), "configuration": config, "engine_root": str(root), "staging_dir": str(staging_dir) if staging_dir else None, "manifest_candidates": sorted(set(manifest_candidates)), "path_resolution": {"project": path_report(project), "archive": path_report(archive), "staging_dir": path_report(staging_dir) if staging_dir else None, "engine_root": path_report(root)}})
    return result

def verify(archive: Path) -> dict[str, Any]:
    files = sorted(p for p in archive.rglob("*") if p.is_file()) if archive.exists() else []
    executables = [p for p in files if p.suffix.lower() == ".exe"]
    return {"schema_version": 1, "kind": "unreal-package-verification", "status": "PASS" if executables else "FAIL", "archive": str(archive), "file_count": len(files), "executables": [{"path": str(p), "sha256": hashlib.sha256(p.read_bytes()).hexdigest(), "bytes": p.stat().st_size} for p in executables]}

def main() -> int:
    p = argparse.ArgumentParser(); p.add_argument("--engine-root", type=Path); sub = p.add_subparsers(dest="command", required=True)
    c = sub.add_parser("compile"); c.add_argument("project", type=Path); c.add_argument("--target", required=True); c.add_argument("--config", default="Development"); c.add_argument("--timeout", type=int, default=600)
    b = sub.add_parser("package"); b.add_argument("project", type=Path); b.add_argument("--archive", type=Path, required=True); b.add_argument("--config", default="Development"); b.add_argument("--timeout", type=int, default=1200); b.add_argument("--staging-dir", type=Path)
    v = sub.add_parser("verify"); v.add_argument("archive", type=Path)
    args = p.parse_args()
    if args.command == "compile": result = compile_target(args.project, args.target, args.config, args.engine_root, args.timeout)
    elif args.command == "package": result = package(args.project, args.archive, args.engine_root, args.config, args.timeout, args.staging_dir)
    else: result = verify(args.archive)
    print(json.dumps(result, indent=2, ensure_ascii=False)); return 0 if result.get("status") == "PASS" else 1

if __name__ == "__main__": raise SystemExit(main())
