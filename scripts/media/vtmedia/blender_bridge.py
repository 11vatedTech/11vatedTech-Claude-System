from __future__ import annotations

from pathlib import Path
from shutil import which
from typing import Any
from .common import ensure_dir, run, write_json

ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = Path(__file__).resolve().parent / "blender_scripts"


def available() -> bool:
    return which("blender") is not None


def doctor() -> dict[str, Any]:
    if not available():
        return {"availability": "missing", "health": "MISSING"}
    version = run(["blender", "--version"], timeout=30)
    py = run(["blender", "--background", "--python-expr", "import bpy, json; print('BLENDER_PY_OK', bpy.app.version_string)"], timeout=60)
    gpu = run(["blender", "--background", "--python", str(SCRIPT_DIR / "gpu_report.py")], timeout=90)
    return {"availability": "available", "health": "PASS" if py.get("returncode") == 0 else "FAILED", "version": version, "python": py, "gpu_report": gpu}


def render_test(out_dir: Path, quality: str = "preview") -> dict[str, Any]:
    ensure_dir(out_dir)
    if not available():
        return {"availability": "missing", "health": "MISSING", "message": "Blender executable not found"}
    scene_json = out_dir / "scene.json"
    scene = {
        "schema_version": 1,
        "scene_id": "11vt-crystal-atelier",
        "quality": quality,
        "resolution": [1280, 720] if quality == "preview" else [3840, 2160],
        "render": {"engine": "CYCLES", "device": "AUTO", "samples": 64 if quality == "preview" else 256},
        "camera": {"lens_mm": 55, "position": [4.5, -6.5, 3.4], "look_at": [0, 0, 0.7]},
        "lighting": {"strategy": "warm_key_cyan_rim", "color_management": "Filmic"},
        "art_direction": "Faceted glass monolith with physical material response, not primitive placeholder cube.",
    }
    write_json(scene_json, scene)
    blend = out_dir / "test-scene.blend"
    png = out_dir / "render.png"
    stats = out_dir / "render-stats.json"
    r = run(["blender", "--background", "--python", str(SCRIPT_DIR / "render_scene.py"), "--", str(scene_json), str(blend), str(png), str(stats)], timeout=600)
    return {"command": r, "scene": str(scene_json), "blend": str(blend), "render": str(png), "stats": str(stats), "health": "PASS" if Path(png).exists() else "FAILED"}


def export_glb(blend: Path, out_glb: Path) -> dict[str, Any]:
    ensure_dir(out_glb.parent)
    if not available():
        return {"availability": "missing", "health": "MISSING"}
    return run(["blender", "--background", str(blend), "--python", str(SCRIPT_DIR / "export_gltf.py"), "--", str(out_glb)], timeout=180)
