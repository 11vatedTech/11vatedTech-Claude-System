#!/usr/bin/env python3
"""Build the Emberveil flagship hero through the structured Blender op API.

Composes reusable high-level ops (mesh.lathe, mesh.radial_array,
material.subsurface, animation.float, camera.path, render.*, asset.export_glb)
into the hero: a glass bell vessel, a living ember core, brass filigree, a
float animation, motivated lighting, a turntable, and a cinematic camera move.
All evidence and artifacts land under artifacts/flagship/emberveil/.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "media"))

from vtmedia.blender_ops import run_op  # type: ignore
from vtmedia import ffmpeg_tools  # type: ignore

OUT = ROOT / "artifacts" / "flagship" / "emberveil"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    chain = OUT / "session.blend"
    results: dict = {}

    def rec(name, fn):
        try:
            r = fn()
            if "ok" not in r:  # raw tool results (ffmpeg) carry returncode
                r["ok"] = r.get("returncode") == 0
                r["health"] = "PASS" if r["ok"] else "FAILED"
            results[name] = r
        except Exception as exc:
            results[name] = {"ok": False, "health": "FAILED",
                             "error": f"{type(exc).__name__}: {exc}"}
        status = results[name].get("health") or results[name].get("error", "")
        print(f"  {name:26} {status}")
        return results[name]

    # --- scene foundation -------------------------------------------------
    rec("scene.create", lambda: run_op("scene.create", {
        "world_color": [0.02, 0.015, 0.01],
        "objects": [{"type": "empty", "name": "Emberveil_root", "location": [0, 0, 0]}],
        "camera": {"name": "Cam", "lens_mm": 55, "x": 6.0, "y": -7.0, "z": 3.0, "look_at": [0, 0, 1.2]},
        "lights": [{"type": "sun", "name": "CoolRim", "x": -6, "y": -4, "z": 8, "energy": 0.6}],
    }, OUT, chain_blend=chain))

    # --- hero geometry (authored profiles, not primitives) ----------------
    # glass bell: capsule/bell silhouette
    rec("mesh.lathe.bell", lambda: run_op("mesh.lathe", {
        "name": "glass_bell", "segments": 96,
        "profile": [[0.0, 0.0], [0.55, 0.05], [0.92, 0.4], [1.12, 1.0],
                    [0.98, 1.7], [0.62, 2.1], [0.4, 2.32], [0.2, 2.42], [0.0, 2.48]],
        "location": [0, 0, 0.55],
    }, OUT, chain_blend=chain))
    # ember core: flame teardrop
    rec("mesh.lathe.core", lambda: run_op("mesh.lathe", {
        "name": "ember_core", "segments": 64,
        "profile": [[0.0, 0.0], [0.28, 0.08], [0.46, 0.4], [0.4, 0.85],
                    [0.22, 1.3], [0.08, 1.55], [0.0, 1.66]],
        "location": [0, 0, 0.95],
    }, OUT, chain_blend=chain))
    # brass band around the bell's waist
    rec("mesh.lathe.band", lambda: run_op("mesh.lathe", {
        "name": "brass_band", "segments": 96,
        "profile": [[1.0, 1.5], [1.12, 1.5], [1.12, 1.68], [1.0, 1.68]],
        "location": [0, 0, 0.55],
    }, OUT, chain_blend=chain))
    # filigree guard arc (one, then radial array)
    rec("mesh.lathe.filigree", lambda: run_op("mesh.lathe", {
        "name": "filigree_arc", "segments": 48,
        "profile": [[0.94, 1.05], [1.3, 1.15], [1.42, 1.7], [1.3, 2.15], [0.94, 2.2]],
        "location": [0, 0, 0.55],
    }, OUT, chain_blend=chain))
    rec("mesh.radial_array", lambda: run_op("mesh.radial_array", {
        "name": "filigree_arc", "count": 3,
    }, OUT, chain_blend=chain))
    # presentation plinth: low polished disc via lathe
    rec("mesh.lathe.plinth", lambda: run_op("mesh.lathe", {
        "name": "plinth", "segments": 96,
        "profile": [[3.4, 0.0], [3.6, 0.0], [3.6, 0.12], [3.4, 0.12]],
        "location": [0, 0, 0.0],
    }, OUT, chain_blend=chain))

    # --- materials ---------------------------------------------------------
    rec("mat.glass", lambda: run_op("material.subsurface", {
        "name": "Emberveil_Glass", "base_color": [1.0, 0.82, 0.55], "roughness": 0.12,
        "transmission": 0.9, "ior": 1.45, "subsurface": 0.35, "subsurface_color": [0.95, 0.5, 0.2],
        "clearcoat": 1.0, "assign_to": ["glass_bell"],
    }, OUT, chain_blend=chain))
    rec("mat.ember", lambda: run_op("material.subsurface", {
        "name": "Emberveil_Core", "base_color": [1.0, 0.55, 0.15], "roughness": 0.3,
        "emission": [1.0, 0.45, 0.08], "emission_strength": 6.0, "subsurface": 0.5,
        "subsurface_color": [1.0, 0.3, 0.05], "assign_to": ["ember_core"],
    }, OUT, chain_blend=chain))
    rec("mat.brass", lambda: run_op("material.construct", {
        "name": "Emberveil_Brass", "base_color": [0.42, 0.28, 0.14], "metallic": 1.0,
        "roughness": 0.32, "assign_to": ["brass_band", "filigree_arc", "filigree_arc_01", "filigree_arc_02"],
    }, OUT, chain_blend=chain))
    rec("mat.plinth", lambda: run_op("material.construct", {
        "name": "Emberveil_Plinth", "base_color": [0.12, 0.1, 0.09], "metallic": 0.4,
        "roughness": 0.55, "assign_to": ["plinth"],
    }, OUT, chain_blend=chain))

    # --- rig + animation ----------------------------------------------------
    # purposeful rig: parent the parts to the root (morphology-appropriate)
    rec("rig.parent", lambda: run_op("scene.parent", {
        "root": "Emberveil_root",
        "children": ["glass_bell", "ember_core", "brass_band", "filigree_arc",
                     "filigree_arc_01", "filigree_arc_02"],
    }, OUT, chain_blend=chain))
    # float animation on the root (weightless bob + sway, loop-safe)
    rec("anim.float", lambda: run_op("animation.float", {
        "name": "Emberveil_root", "frame_start": 1, "frame_end": 96,
        "amplitude": 0.18, "cycles": 2, "sway_degrees": 2.5,
    }, OUT, chain_blend=chain))
    rec("rig.inspect", lambda: run_op("rig.inspect", {}, OUT, chain_blend=chain))
    rec("anim.inspect", lambda: run_op("animation.inspect", {}, OUT, chain_blend=chain))

    # --- renders -------------------------------------------------------------
    rec("render.turntable", lambda: run_op("render.turntable", {
        "target": [0, 0, 1.2], "radius": 5.5, "height": 1.8, "frames": 24,
        "resolution": [640, 360], "engine": "CYCLES", "samples": 24,
    }, OUT / "turntable", chain_blend=chain))
    rec("render.preview", lambda: run_op("render.preview", {
        "frame": 24, "resolution": [960, 540], "engine": "CYCLES", "samples": 48,
    }, OUT / "preview", chain_blend=chain))
    # cinematic camera move
    rec("camera.path", lambda: run_op("camera.path", {
        "name": "CinematicCam", "frame_start": 1, "frame_end": 72,
        "radius": 6.2, "height": 2.0, "target": [0, 0, 1.2],
        "sweep_degrees": 80, "start_angle": -40, "lens_mm": 45,
    }, OUT, chain_blend=chain))
    rec("render.sequence", lambda: run_op("render.sequence", {
        "frame_start": 1, "frame_end": 72, "resolution": [640, 360],
        "engine": "CYCLES", "samples": 24,
    }, OUT / "cinematic-frames", chain_blend=chain))

    # --- export ---------------------------------------------------------------
    rec("asset.export_glb", lambda: run_op("asset.export_glb", {
        "out_path": str(OUT / "emberveil.glb"),
    }, OUT, chain_blend=chain))

    # --- video assembly (ffmpeg in the real pipeline) -------------------------
    if (OUT / "turntable" / "turntable-000.png").exists():
        rec("video.turntable", lambda: ffmpeg_tools.image_sequence_to_video(
            str(OUT / "turntable" / "turntable-%03d.png"), OUT / "emberveil-turntable.mp4", fps=12))
    if (OUT / "cinematic-frames" / "seq-0001.png").exists():
        rec("video.cinematic", lambda: ffmpeg_tools.image_sequence_to_video(
            str(OUT / "cinematic-frames" / "seq-%04d.png"), OUT / "emberveil-cinematic.mp4", fps=12))

    failed = [n for n, r in results.items() if not r.get("ok")]
    report = {"ok": not failed, "failed": failed, "results": results}
    (OUT / "build-report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"EMBERVEIL BUILD: {'PASS' if not failed else 'FAILED'} failed={failed}")
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
