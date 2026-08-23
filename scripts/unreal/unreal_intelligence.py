#!/usr/bin/env python3
"""Structured Unreal Game Studio intelligence.

This first slice is deliberately useful without an Unreal process: it discovers
installed engines, inspects .uproject metadata and project content, and emits
stable JSON diagnostics. It does not pretend that static inspection proves
runtime gameplay quality; runtime/editor operations are separate capabilities.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
SKIP_DIRS = {"Binaries", "DerivedDataCache", "Intermediate", "Saved", ".git", "Build", "node_modules"}
PROJECT_EXTENSIONS = {".uasset", ".umap", ".ubulk", ".uexp", ".usmap", ".ini", ".cpp", ".h", ".cs", ".uplugin"}


def existing(path: Path) -> str | None:
    return str(path) if path.exists() else None


def read_json(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except Exception as exc:
        return None, f"{type(exc).__name__}: {exc}"


def engine_candidates() -> list[Path]:
    candidates: list[Path] = []
    env = os.environ.get("UNREAL_ENGINE_ROOT")
    if env:
        candidates.append(Path(env))
    for base in (Path("C:/Program Files/Epic Games"), Path("C:/Program Files (x86)/Epic Games")):
        if base.exists():
            candidates.extend(sorted(p for p in base.glob("UE_*") if p.is_dir()))
    return candidates


def engine_version(root: Path) -> dict[str, Any]:
    version_file = root / "Engine/Build/Build.version"
    data, error = read_json(version_file)
    if data is None:
        return {"version_file": str(version_file), "error": error}
    return {
        "version_file": str(version_file),
        "major": data.get("MajorVersion"),
        "minor": data.get("MinorVersion"),
        "patch": data.get("PatchVersion"),
        "changelist": data.get("Changelist"),
        "branch": data.get("BranchName"),
        "version": ".".join(str(data.get(k, 0)) for k in ("MajorVersion", "MinorVersion", "PatchVersion")),
    }


def plugin_inventory(root: Path) -> dict[str, Any]:
    plugin_root = root / "Engine/Plugins"
    plugins: list[dict[str, Any]] = []
    if not plugin_root.exists():
        return {"count": 0, "plugins": plugins}
    for descriptor in sorted(plugin_root.rglob("*.uplugin")):
        try:
            data, error = read_json(descriptor)
            if data is None:
                continue
            name = data.get("FriendlyName") or data.get("Name") or descriptor.stem
            plugins.append({"name": name, "path": str(descriptor), "enabled_by_default": data.get("EnabledByDefault", False), "experimental": data.get("ExperimentalVersion", False), "modules": [m.get("Name") for m in data.get("Modules", []) if isinstance(m, dict)]})
        except OSError:
            continue
    names = {str(p["name"]).lower() for p in plugins}
    wanted = {"python editor script plugin", "remote control", "data validation", "niagara", "pcg", "control rig", "gameplay abilities", "enhanced input"}
    return {"count": len(plugins), "plugins": plugins, "relevant_present": sorted(n for n in wanted if n in names)}


def command_available(command: str) -> str | None:
    return shutil.which(command)


def toolchain_health() -> dict[str, Any]:
    """Discover VS Build Tools even when cl/msbuild are absent from PATH."""
    vs_roots = [Path("C:/Program Files/Microsoft Visual Studio/2022/BuildTools"), Path("C:/Program Files/Microsoft Visual Studio/2022/Community"), Path("C:/Program Files/Microsoft Visual Studio/2022/Professional"), Path("C:/Program Files/Microsoft Visual Studio/2022/Enterprise")]
    installations = []
    for root in vs_roots:
        if not root.exists():
            continue
        msvc_roots = sorted((root / "VC/Tools/MSVC").glob("*")) if (root / "VC/Tools/MSVC").exists() else []
        msvc = msvc_roots[-1] if msvc_roots else None
        candidates = {"root": str(root), "cl": existing(msvc / "bin/Hostx64/x64/cl.exe") if msvc else None, "link": existing(msvc / "bin/Hostx64/x64/link.exe") if msvc else None, "msbuild": existing(root / "MSBuild/Current/Bin/amd64/MSBuild.exe"), "msvc_toolset": msvc.name if msvc else None}
        candidates["compile_ready"] = all(candidates.get(k) for k in ("cl", "link", "msbuild"))
        installations.append(candidates)
    sdk_candidates = [Path("C:/Program Files (x86)/Windows Kits/10"), Path("C:/Program Files (x86)/Windows Kits/11")]
    sdks = []
    for sdk in sdk_candidates:
        versions = sorted((p for p in (sdk / "bin").glob("*") if p.is_dir() and re.fullmatch(r"\\d+\\.\\d+\\.\\d+\\.\\d+", p.name))) if (sdk / "bin").exists() else []
        rc = versions[-1] / "x64/rc.exe" if versions else None
        if sdk.exists(): sdks.append({"root": str(sdk), "versions": [v.name for v in versions], "rc": existing(rc) if rc else None})
    netfx_roots = [Path("C:/Program Files (x86)/Windows Kits/NETFXSDK"), Path("C:/Program Files/Windows Kits/NETFXSDK"), Path("C:/Program Files (x86)/Microsoft SDKs/NETFXSDK"), Path("C:/Program Files/Microsoft SDKs/NETFXSDK")]
    netfx_registry = []
    try:
        import winreg
        for hive, hive_name in ((winreg.HKEY_LOCAL_MACHINE, "HKLM"), (winreg.HKEY_CURRENT_USER, "HKCU")):
            for base in (r"SOFTWARE\\WOW6432Node\\Microsoft\\Microsoft SDKs\\NETFXSDK", r"SOFTWARE\\Microsoft\\Microsoft SDKs\\NETFXSDK"):
                try:
                    with winreg.OpenKey(hive, base) as key:
                        for index in range(winreg.QueryInfoKey(key)[0]):
                            version = winreg.EnumKey(key, index)
                            if version not in {"4.8", "4.7.2", "4.7.1", "4.7", "4.6.2", "4.6.1", "4.6"}:
                                continue
                            with winreg.OpenKey(key, version) as version_key:
                                try: install = winreg.QueryValueEx(version_key, "KitsInstallationFolder")[0]
                                except OSError: install = None
                            netfx_registry.append({"hive": hive_name, "key": f"{base}\\{version}", "version": version, "kits_installation_folder": install})
                except OSError:
                    continue
    except ImportError:
        netfx_registry = []
    netfx_versions = []
    for netfx_root in netfx_roots:
        if netfx_root.exists():
            for version_dir in sorted(p for p in netfx_root.iterdir() if p.is_dir()):
                include = version_dir / "Include/um"
                libraries = version_dir / "Lib/um"
                netfx_versions.append({"version": version_dir.name, "root": str(version_dir), "include": existing(include), "lib": existing(libraries), "usable": include.exists() and libraries.exists()})
    netfx_sdk = {"versions": netfx_versions, "registry": netfx_registry, "registry_key_present": bool(netfx_registry), "required_for_unreal_editor_target": True, "available": any(v["usable"] for v in netfx_versions), "missing_component": None if any(v["usable"] for v in netfx_versions) else "Microsoft.Net.Component.4.8.SDK"}
    return {"path_commands": {name: command_available(name) for name in ("dotnet", "cl", "link", "msbuild")}, "visual_studio": installations, "windows_sdks": sdks, "netfx_sdk": netfx_sdk, "compile_ready": any(i["compile_ready"] and sdks for i in installations), "editor_target_ready": any(i["compile_ready"] and sdks for i in installations) and netfx_sdk["available"]}


def health(engine_root: Path | None = None) -> dict[str, Any]:
    roots = [engine_root] if engine_root else engine_candidates()
    engines = []
    for root in roots:
        if not root or not root.exists():
            continue
        binaries = root / "Engine/Binaries/Win64"
        batch = root / "Engine/Build/BatchFiles"
        engines.append({
            "root": str(root),
            "version": engine_version(root),
            "executables": {name: existing(binaries / name) for name in ("UnrealEditor.exe", "UnrealEditor-Cmd.exe")},
            "automation": {name: existing(batch / name) for name in ("RunUAT.bat", "Build.bat")},
            "plugins": plugin_inventory(root),
        })
    toolchain = toolchain_health()
    return {
        "schema_version": SCHEMA_VERSION,
        "kind": "unreal-installation-health",
        "engines": engines,
        "toolchain": toolchain,
        "windows_sdk": [s["root"] for s in toolchain["windows_sdks"]],
        "usable_engine_count": sum(1 for e in engines if e["executables"].get("UnrealEditor-Cmd.exe") and e["automation"].get("RunUAT.bat")),
        "editor_target_ready": toolchain["editor_target_ready"],
        "limitations": ["Editor startup and runtime play are not implied by static health; use unreal.editor.health and runtime QA when implemented."] + (["Unreal Editor target is blocked: install Microsoft.Net.Component.4.8.SDK in the existing Visual Studio Build Tools instance."] if not toolchain["editor_target_ready"] else []),
    }


def iter_project_files(root: Path):
    if not root.exists():
        return
    for path in root.rglob("*"):
        if not path.is_file() or any(part in SKIP_DIRS for part in path.relative_to(root).parts):
            continue
        if path.suffix.lower() in PROJECT_EXTENSIONS:
            yield path


def ini_value(config_root: Path, key: str) -> list[str]:
    values: list[str] = []
    for path in sorted(config_root.glob("*.ini")) if config_root.exists() else []:
        text = path.read_text(encoding="utf-8", errors="replace")
        values.extend(re.findall(rf"^\s*{re.escape(key)}\s*=\s*(.+?)\s*$", text, flags=re.MULTILINE))
    return values


def inspect_project(project_file: Path, engine_root: Path | None = None) -> dict[str, Any]:
    project_file = project_file.resolve()
    root = project_file.parent
    data, parse_error = read_json(project_file)
    data = data or {}
    files = list(iter_project_files(root))
    by_ext: dict[str, int] = {}
    for path in files:
        by_ext[path.suffix.lower()] = by_ext.get(path.suffix.lower(), 0) + 1
    source_files = [p for p in files if "Source" in p.relative_to(root).parts]
    classes: list[dict[str, Any]] = []
    for path in source_files:
        if path.suffix.lower() not in {".cpp", ".h"}:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for macro, kind, name in re.findall(r"\b(UCLASS|USTRUCT|UENUM|UINTERFACE)\b[^\n]*\n?[^\n]*?\b(class|struct|enum)\s+(?:\w+\s+)?(\w+)", text):
            classes.append({"macro": macro, "kind": kind, "name": name, "file": str(path.relative_to(root)).replace("\\", "/")})
    enabled_plugins = [p.get("Name") for p in data.get("Plugins", []) if isinstance(p, dict) and p.get("Enabled")]
    startup_maps = ini_value(root / "Config", "GameDefaultMap") + ini_value(root / "Config", "ServerDefaultMap")
    maps = [str(p.relative_to(root)).replace("\\", "/") for p in files if p.suffix.lower() == ".umap"]
    project_version = data.get("EngineAssociation")
    installed_version = engine_version(engine_root).get("version") if engine_root else None
    warnings: list[str] = []
    if parse_error: warnings.append(f"uproject_parse_error: {parse_error}")
    if not data: warnings.append("uproject_metadata_empty")
    if not startup_maps: warnings.append("no_configured_startup_map")
    if not maps: warnings.append("no_project_maps_found")
    if installed_version and project_version and project_version not in {installed_version, f"{installed_version.split('.')[0]}.{installed_version.split('.')[1]}"} and project_version != "5.8":
        warnings.append(f"engine_association_differs: project={project_version} installed={installed_version}")
    return {
        "schema_version": SCHEMA_VERSION,
        "kind": "unreal-project-inspection",
        "project": str(project_file),
        "root": str(root),
        "metadata": {k: data.get(k) for k in ("FileVersion", "EngineAssociation", "Category", "Description")},
        "modules": data.get("Modules", []),
        "enabled_plugins": enabled_plugins,
        "content": {"files_by_extension": dict(sorted(by_ext.items())), "maps": maps, "source_files": len(source_files), "classes": classes},
        "startup_maps": startup_maps,
        "warnings": warnings,
        "static_inspection_only": True,
    }


def run_commandlet(project_file: Path, commandlet: str, engine_root: Path | None = None, timeout: int = 120, disable_plugins: list[str] | None = None) -> dict[str, Any]:
    """Run one allowlisted commandlet with bounded lifecycle and JSON evidence."""
    allowed = {"DataValidation", "AssetAudit"}
    if commandlet not in allowed:
        return {"schema_version": SCHEMA_VERSION, "kind": "unreal-commandlet", "status": "REJECTED", "error": f"commandlet_not_allowlisted: {commandlet}"}
    root = engine_root or (engine_candidates()[-1] if engine_candidates() else None)
    if root is None:
        return {"schema_version": SCHEMA_VERSION, "kind": "unreal-commandlet", "status": "UNAVAILABLE", "error": "no_engine_root"}
    executable = root / "Engine/Binaries/Win64/UnrealEditor-Cmd.exe"
    project_file = project_file.resolve()
    if not executable.exists():
        return {"schema_version": SCHEMA_VERSION, "kind": "unreal-commandlet", "status": "UNAVAILABLE", "error": "UnrealEditor-Cmd.exe_missing", "engine_root": str(root)}
    if not project_file.exists():
        return {"schema_version": SCHEMA_VERSION, "kind": "unreal-commandlet", "status": "REJECTED", "error": "project_missing", "project": str(project_file)}
    args = [str(executable), str(project_file), f"-run={commandlet}", "-unattended", "-nop4", "-nosplash", "-nullrhi", "-NoSound", "-stdout", "-FullStdOutLogOutput", "-NoLogTimes"]
    for plugin in disable_plugins or []:
        if not re.fullmatch(r"[A-Za-z0-9_]+", plugin):
            return {"schema_version": SCHEMA_VERSION, "kind": "unreal-commandlet", "status": "REJECTED", "error": f"invalid_plugin_name: {plugin}"}
        args.append(f"-DisablePlugin={plugin}")
    started = time.monotonic()
    try:
        completed = subprocess.run(args, capture_output=True, text=True, timeout=timeout, cwd=project_file.parent)
        status = "PASS" if completed.returncode == 0 else "FAIL"
        return {"schema_version": SCHEMA_VERSION, "kind": "unreal-commandlet", "status": status, "commandlet": commandlet, "project": str(project_file), "engine_root": str(root), "exit_code": completed.returncode, "duration_seconds": round(time.monotonic() - started, 3), "stdout_tail": completed.stdout[-12000:], "stderr_tail": completed.stderr[-12000:]}
    except subprocess.TimeoutExpired as exc:
        return {"schema_version": SCHEMA_VERSION, "kind": "unreal-commandlet", "status": "TIMEOUT", "commandlet": commandlet, "project": str(project_file), "engine_root": str(root), "duration_seconds": round(time.monotonic() - started, 3), "stdout_tail": str(exc.stdout or "")[-12000:], "stderr_tail": str(exc.stderr or "")[-12000:]}


def import_glb(project_file: Path, asset: Path, destination: str, report_path: Path, engine_root: Path | None = None, timeout: int = 180) -> dict[str, Any]:
    """Import a GLB through Unreal's Editor Python/AssetTools boundary."""
    project_file = project_file.resolve(); asset = asset.resolve(); report_path = report_path.resolve()
    if not asset.exists() or asset.suffix.lower() != ".glb":
        return {"schema_version": SCHEMA_VERSION, "kind": "unreal-asset-import", "status": "REJECTED", "error": "asset_must_be_existing_glb"}
    if not project_file.exists():
        return {"schema_version": SCHEMA_VERSION, "kind": "unreal-asset-import", "status": "REJECTED", "error": "project_missing"}
    if not re.fullmatch(r"/Game(?:/[A-Za-z0-9_.-]+)+", destination):
        return {"schema_version": SCHEMA_VERSION, "kind": "unreal-asset-import", "status": "REJECTED", "error": "invalid_unreal_content_path"}
    root = engine_root or (engine_candidates()[-1] if engine_candidates() else None)
    executable = root / "Engine/Binaries/Win64/UnrealEditor-Cmd.exe" if root else None
    probe = Path(__file__).with_name("editor_import_probe.py")
    if not executable or not executable.exists() or not probe.exists():
        return {"schema_version": SCHEMA_VERSION, "kind": "unreal-asset-import", "status": "UNAVAILABLE", "error": "editor_import_surface_missing"}
    report_path.parent.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy(); env.update({"FOUNDRY_IMPORT_SOURCE": str(asset), "FOUNDRY_IMPORT_REPORT": str(report_path), "FOUNDRY_IMPORT_DEST": destination})
    args = [str(executable), str(project_file), "-run=PythonScript", f"-script={probe}", "-unattended", "-nop4", "-nosplash", "-nullrhi", "-NoSound", "-stdout", "-FullStdOutLogOutput", "-NoLogTimes"]
    started = time.monotonic()
    try:
        completed = subprocess.run(args, capture_output=True, text=True, timeout=timeout, cwd=project_file.parent, env=env)
        probe_result = json.loads(report_path.read_text(encoding="utf-8")) if report_path.exists() else {"status": "MISSING"}
        status = "PASS" if completed.returncode == 0 and probe_result.get("status") == "PASS" else "FAIL"
        return {"schema_version": SCHEMA_VERSION, "kind": "unreal-asset-import", "status": status, "project": str(project_file), "source": str(asset), "destination": destination, "editor_exit_code": completed.returncode, "duration_seconds": round(time.monotonic() - started, 3), "probe": probe_result, "stdout_tail": completed.stdout[-8000:], "stderr_tail": completed.stderr[-8000:]}
    except subprocess.TimeoutExpired as exc:
        return {"schema_version": SCHEMA_VERSION, "kind": "unreal-asset-import", "status": "TIMEOUT", "project": str(project_file), "source": str(asset), "duration_seconds": round(time.monotonic() - started, 3), "stdout_tail": str(exc.stdout or "")[-8000:], "stderr_tail": str(exc.stderr or "")[-8000:]}


def runtime_observe(executable: Path, project: Path | None, log_path: Path, timeout: int = 45, trace: bool = False, extra_args: list[str] | None = None) -> dict[str, Any]:
    """Launch a game target with bounded lifecycle and classify actual evidence."""
    executable = executable.resolve(); log_path = log_path.resolve()
    if not executable.exists():
        return {"schema_version": SCHEMA_VERSION, "kind": "unreal-runtime-observation", "status": "UNAVAILABLE", "error": "game_executable_missing", "executable": str(executable)}
    log_path.parent.mkdir(parents=True, exist_ok=True)
    args = [str(executable)] + ([str(project.resolve())] if project else []) + ["-game", "-unattended", "-nop4", "-nosplash", "-stdout", "-FullStdOutLogOutput", "-NoSound", f"-log={log_path}"]
    if trace:
        args.append("-trace=default,frame,bookmark,loadtime")
    args += extra_args or []
    started = time.monotonic()
    try:
        completed = subprocess.run(args, cwd=executable.parent, capture_output=True, text=True, timeout=timeout)
        stdout, stderr = completed.stdout or "", completed.stderr or ""
        text = log_path.read_text(encoding="utf-8", errors="replace") if log_path.exists() else stdout + "\\n" + stderr
        errors = [line.strip() for line in text.splitlines() if re.search(r"\b(Error|Critical error|Assertion failed|crashed)\b", line, re.I)]
        markers = {"project_loaded": "Failed to open descriptor file" not in text, "asset_registry_loaded": "Failed to load premade asset registry" not in text, "game_module_loaded": "The game module 'FoundryCalibration' could not be found" not in text, "map_loaded": bool(re.search(r"LoadMap|World.*BeginPlay|GameMode", text, re.I)), "gameplay_markers": "ASHWAKE" in text or "RELIQUARY" in text or "LogFoundry" in text, "crashed": bool(re.search(r"Critical error|crashed|Assertion failed", text, re.I)), "asset_registry_premade_failure": "Failed to load premade asset registry" in text, "loose_content_runtime": "Running without a pakfile/IoStore" in text or "Failed to initialize ShaderCodeLibrary" in text}
        if markers["asset_registry_premade_failure"] and markers["crashed"]:
            status = "LOOSE_CONTENT_ASSET_REGISTRY_FAILURE"
        else:
            status = "RUNTIME_CRASH" if markers["crashed"] else "RUNTIME_FAIL" if completed.returncode else "GAMEPLAY_OBSERVED" if markers["gameplay_markers"] and markers["map_loaded"] else "MAP_LOADED_NO_GAMEPLAY" if markers["map_loaded"] else "STARTUP_ONLY"
        return {"schema_version": SCHEMA_VERSION, "kind": "unreal-runtime-observation", "status": status, "exit_code": completed.returncode, "executable": str(executable), "project": str(project.resolve()) if project else None, "log": str(log_path), "duration_seconds": round(time.monotonic() - started, 3), "markers": markers, "error_count": len(errors), "errors": errors[-20:], "stdout_tail": stdout[-4000:], "stderr_tail": stderr[-4000:], "trace_requested": trace, "command": args, "diagnosis": "development game target requires cooked asset registry/shader data; use Editor -game for loose-content play or BuildCookRun for packaged play" if status == "LOOSE_CONTENT_ASSET_REGISTRY_FAILURE" else None}
    except subprocess.TimeoutExpired as exc:
        text = log_path.read_text(encoding="utf-8", errors="replace") if log_path.exists() else str(exc.stdout or "")
        return {"schema_version": SCHEMA_VERSION, "kind": "unreal-runtime-observation", "status": "RUNTIME_TIMEOUT", "exit_code": None, "executable": str(executable), "project": str(project.resolve()) if project else None, "log": str(log_path), "duration_seconds": round(time.monotonic() - started, 3), "errors": [line.strip() for line in text.splitlines() if "Error" in line][-20:], "trace_requested": trace, "command": args}


def run_automation_tests(project_file: Path, test_name: str, engine_root: Path | None = None, timeout: int = 180, nullrhi: bool = True) -> dict[str, Any]:
    """Execute a named Unreal automation test through the Editor command line.

    Discovery is intentionally separate from execution: a source macro or a
    compiled symbol is not evidence of a test result. This operation records
    the actual process result and a bounded diagnostic when the C++ Editor
    target/module is unavailable.
    """
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", test_name):
        return {"schema_version": SCHEMA_VERSION, "kind": "unreal-native-test-execution", "status": "REJECTED", "error": "invalid_test_name"}
    project_file = project_file.resolve()
    root = engine_root or (engine_candidates()[-1] if engine_candidates() else None)
    executable = root / "Engine/Binaries/Win64/UnrealEditor-Cmd.exe" if root else None
    if not executable or not executable.exists():
        return {"schema_version": SCHEMA_VERSION, "kind": "unreal-native-test-execution", "status": "UNAVAILABLE", "error": "UnrealEditor-Cmd.exe_missing", "project": str(project_file)}
    args = [str(executable), str(project_file), "-unattended", "-nop4", "-nosplash", "-stdout", "-FullStdOutLogOutput", "-NoSound"]
    if nullrhi:
        args.append("-nullrhi")
    args.append(f"-ExecCmds=Automation RunTests {test_name};Quit")
    started = time.monotonic()
    try:
        completed = subprocess.run(args, cwd=project_file.parent, capture_output=True, text=True, timeout=timeout)
        text = (completed.stdout or "") + "\\n" + (completed.stderr or "")
        test_pattern = re.escape(test_name)
        passed = bool(re.search(rf"(?:Test Completed|Test Passed|Passed).*{test_pattern}", text, re.I) or re.search(rf"{test_pattern}.*(?:Passed|Success)", text, re.I))
        failed = bool(re.search(rf"(?:Test Failed|Failed).*{test_pattern}", text, re.I) or re.search(rf"{test_pattern}.*(?:Failed|Error)", text, re.I))
        module_missing = "The game module 'FoundryCalibration' could not be found" in text
        status = "PASS" if completed.returncode == 0 and passed and not failed else "BLOCKED_MODULE" if module_missing else "FAIL"
        return {"schema_version": SCHEMA_VERSION, "kind": "unreal-native-test-execution", "status": status, "test": test_name, "project": str(project_file), "exit_code": completed.returncode, "duration_seconds": round(time.monotonic() - started, 3), "evidence": {"passed_marker": passed, "failed_marker": failed, "module_missing": module_missing}, "stdout_tail": text[-12000:], "command": args}
    except subprocess.TimeoutExpired as exc:
        return {"schema_version": SCHEMA_VERSION, "kind": "unreal-native-test-execution", "status": "TIMEOUT", "test": test_name, "project": str(project_file), "duration_seconds": round(time.monotonic() - started, 3), "stdout_tail": str(exc.stdout or "")[-12000:], "command": args}


def discover_native_tests(source_root: Path) -> dict[str, Any]:
    repo_root = Path(__file__).resolve().parents[2]
    source_root = source_root.resolve()
    tests = []
    for path in sorted(source_root.rglob("*.cpp")) if source_root.exists() else []:
        text = path.read_text(encoding="utf-8", errors="replace")
        for match in re.finditer(r'IMPLEMENT_SIMPLE_AUTOMATION_TEST\(\s*(\w+)\s*,\s*"([^"]+)"', text):
            tests.append({"symbol": match.group(1), "name": match.group(2), "source": str(path.relative_to(repo_root)).replace("\\", "/"), "execution": "not_proven_until_editor_or_game_automation_target_runs"})
    return {"schema_version": SCHEMA_VERSION, "kind": "unreal-native-test-discovery", "count": len(tests), "tests": tests, "status": "DISCOVERED_NOT_EXECUTED" if tests else "NONE_FOUND"}


def validate_project(project_file: Path, engine_root: Path | None = None) -> dict[str, Any]:
    report = inspect_project(project_file, engine_root)
    issues = [{"severity": "warning", "code": w} for w in report["warnings"]]
    for module in report["modules"]:
        if not isinstance(module, dict) or not module.get("Name"):
            issues.append({"severity": "error", "code": "module_missing_name"})
    report["validation"] = {"ok": not any(i["severity"] == "error" for i in issues), "issues": issues}
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="unreal_intelligence")
    parser.add_argument("--engine-root", type=Path, help="explicit Unreal engine root")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("health")
    for name in ("inspect", "validate"):
        p = sub.add_parser(name); p.add_argument("project", type=Path)
    p = sub.add_parser("commandlet"); p.add_argument("project", type=Path); p.add_argument("--name", choices=("DataValidation", "AssetAudit"), default="DataValidation"); p.add_argument("--timeout", type=int, default=120); p.add_argument("--disable-plugin", action="append", default=[])
    p = sub.add_parser("import-glb"); p.add_argument("project", type=Path); p.add_argument("asset", type=Path); p.add_argument("--destination", required=True); p.add_argument("--report", type=Path, required=True); p.add_argument("--timeout", type=int, default=180)
    p = sub.add_parser("runtime"); p.add_argument("executable", type=Path); p.add_argument("--project", type=Path); p.add_argument("--log", type=Path, required=True); p.add_argument("--timeout", type=int, default=45); p.add_argument("--trace", action="store_true"); p.add_argument("--game-arg", action="append", default=[])
    p = sub.add_parser("automation"); p.add_argument("project", type=Path); p.add_argument("test"); p.add_argument("--timeout", type=int, default=180); p.add_argument("--no-nullrhi", action="store_true")
    p = sub.add_parser("discover-tests"); p.add_argument("source", type=Path)
    args = parser.parse_args(argv)
    if args.command == "health": result = health(args.engine_root)
    elif args.command == "inspect": result = inspect_project(args.project, args.engine_root)
    elif args.command == "validate": result = validate_project(args.project, args.engine_root)
    elif args.command == "commandlet": result = run_commandlet(args.project, args.name, args.engine_root, args.timeout, args.disable_plugin)
    elif args.command == "runtime": result = runtime_observe(args.executable, args.project, args.log, args.timeout, args.trace, args.game_arg)
    elif args.command == "automation": result = run_automation_tests(args.project, args.test, args.engine_root, args.timeout, not args.no_nullrhi)
    elif args.command == "discover-tests": result = discover_native_tests(args.source)
    else: result = import_glb(args.project, args.asset, args.destination, args.report, args.engine_root, args.timeout)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if args.command == "health" and result["usable_engine_count"] == 0: return 2
    if args.command == "validate" and not result["validation"]["ok"]: return 1
    if args.command in {"commandlet", "import-glb"} and result.get("status") != "PASS": return 1
    if args.command == "runtime" and result.get("status") not in {"GAMEPLAY_OBSERVED", "MAP_LOADED_NO_GAMEPLAY", "STARTUP_ONLY"}: return 1
    if args.command == "automation" and result.get("status") != "PASS": return 1
    if args.command == "discover-tests" and result.get("status") == "NONE_FOUND": return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
