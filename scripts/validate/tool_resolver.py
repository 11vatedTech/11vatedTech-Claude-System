#!/usr/bin/env python3
"""Canonical environment-aware tool discovery used by all Foundry operators."""
from __future__ import annotations
import glob, os, shutil, subprocess

WINDOWS_PATTERNS = {
    "inkscape": ["/c/Program Files/Inkscape/bin/inkscape.exe", "/c/Program Files/Inkscape/inkscape.exe", r"C:\Program Files\Inkscape\bin\inkscape.exe"],
    "blender": ["/c/Program Files/Blender Foundation/Blender */blender.exe", r"C:\Program Files\Blender Foundation\Blender *\blender.exe"],
    "unreal": ["/c/Program Files/Epic Games/UE_*/Engine/Binaries/Win64/UnrealEditor-Cmd.exe", r"C:\Program Files\Epic Games\UE_*\Engine\Binaries\Win64\UnrealEditor-Cmd.exe"],
    "krita": ["/c/Program Files/Krita*/bin/krita.exe", "/c/Program Files/Krita*/krita.exe", r"C:\Program Files\Krita*\bin\krita.exe"],
    "magick": ["/c/Program Files/ImageMagick-*/magick.exe", r"C:\Program Files\ImageMagick-*\magick.exe"],
}


def resolve_tool(name: str) -> str | None:
    path = shutil.which(name)
    if path:
        return path
    hits: list[str] = []
    for pattern in WINDOWS_PATTERNS.get(name, []):
        hits.extend(glob.glob(pattern))
    return sorted(set(hits))[-1] if hits else None


def tool_state(name: str, version_args: list[str] | None = None) -> dict:
    path = resolve_tool(name)
    result = {"name": name, "path": path, "state": "NOT_FOUND"}
    if not path:
        return result
    result["state"] = "INSTALLED"
    if version_args is not None:
        try:
            p = subprocess.run([path, *version_args], capture_output=True, text=True, timeout=15)
            result["execution"] = p.returncode == 0
            result["state"] = "EXECUTION_PROVEN" if p.returncode == 0 else "INSTALLED"
            result["version_output"] = (p.stdout + p.stderr).strip()[:300]
        except Exception as exc:
            result["execution_error"] = type(exc).__name__
    return result


def discover_all() -> dict:
    specs = {
        "git": ["--version"], "python": ["--version"], "node": ["--version"],
        "npm": ["--version"], "cmake": ["--version"], "ffmpeg": ["-version"],
        "magick": ["--version"], "inkscape": ["--version"], "krita": ["--version"],
        "blender": ["--version"], "unreal": ["-version"], "ollama": ["--version"],
    }
    return {name: tool_state(name, args) for name, args in specs.items()}
