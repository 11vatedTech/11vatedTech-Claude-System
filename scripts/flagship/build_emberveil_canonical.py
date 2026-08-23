#!/usr/bin/env python3
"""Canonical Emberveil build using only registered structured Blender ops.

The batch boundary is intentional: all operations execute in one Blender
process, preserving scene state while preventing the previously observed
open_mainfile corruption. The result is a calibration artifact, not a claim
that the Foundry can yet produce professional/signature art automatically.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "media"))
from vtmedia.blender_ops import run_batch  # type: ignore

OUT = ROOT / "artifacts" / "flagship" / "emberveil-canonical"


def step(step_name: str, operation: str, **params) -> dict:
    return {"name": step_name, "op": operation, "params": params}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    glb = OUT / "emberveil-canonical.glb"
    ops = [
        step("scene", "scene.create", world_color=[0.012, 0.008, 0.006], objects=[
            {"type": "empty", "name": "Emberveil_root", "location": [0, 0, 0]},
        ], camera={"name": "PresentationCam", "lens_mm": 58, "x": 5.3, "y": -7.0, "z": 3.2, "look_at": [0, 0, 1.35]}),
        # A small authored shrine environment: the hero is grounded in a space,
        # not floating in an uncontextualized black void.
        step("hero_bell", "mesh.lathe", name="glass_bell", segments=128, profile=[
            [0.0, 0.24], [0.42, 0.27], [0.68, 0.40], [0.94, 0.70],
            [1.08, 1.08], [1.13, 1.48], [1.07, 1.78], [0.90, 2.06],
            [0.68, 2.25], [0.42, 2.38], [0.16, 2.46], [0.0, 2.50]], location=[0, 0, 0.55]),
        step("ember_core", "mesh.lathe", name="ember_core", segments=96, profile=[
            [0.0, 0.34], [0.18, 0.40], [0.38, 0.65], [0.47, 0.98],
            [0.40, 1.30], [0.26, 1.58], [0.10, 1.78], [0.0, 1.88]], location=[0, 0, 0.82]),
        step("brass_band", "mesh.lathe", name="brass_band", segments=128, profile=[
            [1.03, 1.25], [1.16, 1.29], [1.16, 1.44], [1.03, 1.48]], location=[0, 0, 0.55]),
        step("filigree", "mesh.lathe", name="filigree_arc", segments=64, profile=[
            [1.02, 0.78], [1.22, 0.92], [1.35, 1.28], [1.38, 1.72], [1.22, 2.12], [1.02, 2.28]], location=[0, 0, 0.55]),
        step("filigree_array", "mesh.radial_array", name="filigree_arc", count=4),
        step("basalt_shrine", "mesh.lathe", name="basalt_shrine", segments=128, profile=[
            [3.0, 0.0], [3.45, 0.0], [4.10, 0.10], [4.55, 0.24],
            [4.45, 0.38], [3.70, 0.42], [3.0, 0.28]], location=[0, 0, 0.0]),
        step("ash_ring", "mesh.lathe", name="ash_ring", segments=128, profile=[
            [2.15, 0.0], [2.45, 0.03], [2.55, 0.08], [2.28, 0.12], [2.15, 0.08]], location=[0, 0, 0.42]),
        step("shrine_pillar", "mesh.lathe", name="shrine_pillar", segments=48, profile=[
            [0.18, 0.0], [0.30, 0.05], [0.34, 0.60], [0.22, 0.82], [0.16, 0.82]], location=[2.45, 0, 0.35]),
        step("shrine_pillars", "mesh.radial_array", name="shrine_pillar", count=4),
        step("finish_glass", "mesh.surface_finish", name="glass_bell", smooth=True, bevel_width=0.012, bevel_segments=2),
        step("finish_core", "mesh.surface_finish", name="ember_core", smooth=True, bevel_width=0.008, bevel_segments=2),
        step("finish_band", "mesh.surface_finish", name="brass_band", smooth=True, bevel_width=0.018, bevel_segments=2),
        step("finish_filigree", "mesh.surface_finish", name="filigree_arc", smooth=True, bevel_width=0.008, bevel_segments=2),
        step("finish_filigree_01", "mesh.surface_finish", name="filigree_arc_01", smooth=True, bevel_width=0.008, bevel_segments=2),
        step("finish_filigree_02", "mesh.surface_finish", name="filigree_arc_02", smooth=True, bevel_width=0.008, bevel_segments=2),
        step("finish_filigree_03", "mesh.surface_finish", name="filigree_arc_03", smooth=True, bevel_width=0.008, bevel_segments=2),
        step("finish_shrine", "mesh.surface_finish", name="basalt_shrine", smooth=True, bevel_width=0.03, bevel_segments=3),
        step("finish_ash", "mesh.surface_finish", name="ash_ring", smooth=True, bevel_width=0.02, bevel_segments=2),
        step("finish_pillar", "mesh.surface_finish", name="shrine_pillar", smooth=True, bevel_width=0.018, bevel_segments=2),
        step("finish_pillar_01", "mesh.surface_finish", name="shrine_pillar_01", smooth=True, bevel_width=0.018, bevel_segments=2),
        step("finish_pillar_02", "mesh.surface_finish", name="shrine_pillar_02", smooth=True, bevel_width=0.018, bevel_segments=2),
        step("finish_pillar_03", "mesh.surface_finish", name="shrine_pillar_03", smooth=True, bevel_width=0.018, bevel_segments=2),
        step("parent_hero", "scene.parent", root="Emberveil_root", children=[
            "glass_bell", "ember_core", "brass_band", "filigree_arc", "filigree_arc_01", "filigree_arc_02", "filigree_arc_03"],
        ),
        step("glass_material", "material.subsurface", name="Emberveil_Glass", base_color=[0.75, 0.30, 0.08], roughness=0.16, transmission=0.72, ior=1.45, subsurface=0.18, subsurface_color=[0.85, 0.38, 0.12], clearcoat=0.65, assign_to=["glass_bell"]),
        step("core_material", "material.subsurface", name="Emberveil_Core", base_color=[1.0, 0.22, 0.025], roughness=0.24, emission=[1.0, 0.13, 0.015], emission_strength=8.0, subsurface=0.38, subsurface_color=[1.0, 0.16, 0.02], assign_to=["ember_core"]),
        step("core_noise", "material.noise_emission", name="Emberveil_Core", scale=4.5, detail=4.0, strength_min=5.0, strength_max=12.0, assign_to=["ember_core"]),
        step("brass_material", "material.construct", name="Emberveil_Brass", base_color=[0.42, 0.20, 0.055], metallic=0.92, roughness=0.30, assign_to=["brass_band", "filigree_arc", "filigree_arc_01", "filigree_arc_02", "filigree_arc_03"]),
        step("brass_variation", "material.surface_variation", name="Emberveil_Brass", scale=7.0, detail=5.0, roughness_min=0.22, roughness_max=0.48, bump_strength=0.10, dark_color=[0.08, 0.025, 0.008], light_color=[0.58, 0.27, 0.055]),
        step("basalt_material", "material.construct", name="Emberveil_Basalt", base_color=[0.035, 0.025, 0.022], metallic=0.12, roughness=0.62, assign_to=["basalt_shrine", "ash_ring", "shrine_pillar", "shrine_pillar_01", "shrine_pillar_02", "shrine_pillar_03"]),
        step("basalt_variation", "material.surface_variation", name="Emberveil_Basalt", scale=3.2, detail=6.0, roughness_min=0.48, roughness_max=0.78, bump_strength=0.24, dark_color=[0.012, 0.009, 0.008], light_color=[0.09, 0.065, 0.045]),
        step("mechanical_rig", "rig.mechanical", name="Emberveil_ControlRig", bones=[
            {"name": "vessel_root", "head": [0, 0, 0.55], "tail": [0, 0, 1.0]},
            {"name": "core_suspension", "head": [0, 0, 0.82], "tail": [0, 0, 1.55], "parent": "vessel_root"},
            {"name": "filigree_guard", "head": [0, 0, 1.0], "tail": [0, 0, 2.0], "parent": "vessel_root"},
        ]),
        step("rig_parent", "scene.parent", root="Emberveil_root", children=["Emberveil_ControlRig"]),
        step("idle_float", "animation.float", name="Emberveil_root", frame_start=1, frame_end=96, amplitude=0.11, cycles=2, sway_degrees=1.8),
        step("core_pulse", "animation.pulse", name="ember_core", frame_start=1, frame_end=96, amplitude=0.075, cycles=4),
        step("ring_motion", "animation.rotate", name="brass_band", frame_start=1, frame_end=96, turns=0.20, axis="Z"),
        step("filigree_motion", "animation.rotate", name="filigree_arc", frame_start=1, frame_end=96, turns=-0.08, axis="Z"),
        step("lighting", "lighting.construct", world_strength=0.20, exposure=0.7, lights=[
            {"name": "EmberCoreLight", "type": "POINT", "location": [0, -0.2, 1.25], "energy": 260, "color": [1.0, 0.20, 0.035], "radius": 0.35},
            {"name": "WarmKey", "type": "AREA", "location": [3.8, -4.5, 4.5], "energy": 720, "color": [1.0, 0.42, 0.16], "size": 4.0, "look_at": [0, 0, 1.2]},
            {"name": "WarmBounce", "type": "AREA", "location": [0.5, -2.8, 0.8], "energy": 360, "color": [0.72, 0.22, 0.07], "size": 3.0, "look_at": [0, 0, 1.0]},
            {"name": "CoolSeparation", "type": "AREA", "location": [-4.0, 1.8, 4.0], "energy": 900, "color": [0.18, 0.48, 0.95], "size": 3.5, "look_at": [0, 0, 1.4]},
            {"name": "TopAtmosphere", "type": "AREA", "location": [0, 2.0, 6.0], "energy": 500, "color": [0.55, 0.32, 0.18], "size": 5.0, "look_at": [0, 0, 0.8]},
        ]),
        step("inspect", "scene.inspect"),
        step("rig_inspect", "rig.inspect"),
        step("material_inspect", "material.inspect"),
        step("preview", "render.preview", out_dir=str(OUT / "preview"), frame=48, resolution=[960, 540], engine="CYCLES", samples=48, denoising=True),
        step("turntable", "render.turntable", out_dir=str(OUT / "turntable"), target=[0, 0, 1.25], radius=5.8, height=1.7, frames=24, resolution=[640, 360], engine="CYCLES", samples=24, denoising=True),
        step("camera_path", "camera.path", name="CinematicCam", frame_start=1, frame_end=72, radius=6.8, height=2.0, target=[0, 0, 1.25], sweep_degrees=72, start_angle=-36, lens_mm=52),
        step("sequence", "render.sequence", out_dir=str(OUT / "cinematic-frames"), frame_start=1, frame_end=72, resolution=[640, 360], engine="CYCLES", samples=24, denoising=True),
        step("export", "asset.export_glb", out_path=str(glb)),
    ]
    report = run_batch(ops, OUT, timeout=1200, save_blend=OUT / "session.blend")
    (OUT / "canonical-build-report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"CANONICAL EMBERVEIL: {'PASS' if report.get('ok') else 'FAILED'} ops={report.get('op_count')} failed={report.get('failed')}")
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
