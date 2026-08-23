#!/usr/bin/env python3
"""Automatic asset requirement discovery.

The Founder should not have to enumerate the asset bill of materials. Given a
product requirement, this expands it into a production graph: asset requirement
nodes with types, disciplines, and dependencies. The graph is the input to the
Asset Resolver (one resolution per node).

Knowledge base is organized by product kind (creature entity, character,
environment, UI surface, cinematic shot, VFX system, audio system, ...).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]

# product kind -> list of asset requirements
# each requirement: {name, category, depends_on, discipline, quality_sensitive}
KNOWLEDGE_BASE: dict[str, list[dict[str, Any]]] = {
    "creature_entity": [
        {"name": "concept", "category": "2d-concept", "depends_on": [], "discipline": "creative-direction"},
        {"name": "turnaround_reference", "category": "2d-reference", "depends_on": ["concept"], "discipline": "art-direction"},
        {"name": "model", "category": "3d-model", "depends_on": ["concept", "turnaround_reference"], "discipline": "modeling"},
        {"name": "uv_layout", "category": "3d-uv", "depends_on": ["model"], "discipline": "technical-art"},
        {"name": "textures", "category": "2d-texture", "depends_on": ["uv_layout"], "discipline": "texturing"},
        {"name": "materials", "category": "3d-material", "depends_on": ["textures"], "discipline": "technical-art"},
        {"name": "rig", "category": "3d-rig", "depends_on": ["model"], "discipline": "rigging"},
        {"name": "skinning", "category": "3d-skinning", "depends_on": ["rig", "model"], "discipline": "technical-art"},
        {"name": "idle_animation", "category": "animation", "depends_on": ["rig", "skinning"], "discipline": "animation"},
        {"name": "locomotion_set", "category": "animation", "depends_on": ["rig", "skinning"], "discipline": "animation"},
        {"name": "action_set", "category": "animation", "depends_on": ["rig", "skinning"], "discipline": "animation"},
        {"name": "reaction_set", "category": "animation", "depends_on": ["rig", "skinning"], "discipline": "animation"},
        {"name": "facial_system", "category": "animation", "depends_on": ["rig"], "discipline": "facial-animation"},
        {"name": "vfx_set", "category": "vfx", "depends_on": ["action_set"], "discipline": "vfx"},
        {"name": "audio_set", "category": "audio", "depends_on": ["action_set"], "discipline": "audio"},
        {"name": "ui_representation", "category": "2d-ui", "depends_on": ["concept"], "discipline": "ui-design"},
        {"name": "runtime_optimization", "category": "runtime", "depends_on": ["model", "materials"], "discipline": "technical-art"},
        {"name": "lod_set", "category": "3d-lod", "depends_on": ["model"], "discipline": "technical-art"},
        {"name": "marketing_render", "category": "render", "depends_on": ["model", "materials", "rig"], "discipline": "cinematics"},
    ],
    "character": [
        {"name": "concept", "category": "2d-concept", "depends_on": [], "discipline": "creative-direction"},
        {"name": "model", "category": "3d-model", "depends_on": ["concept"], "discipline": "modeling"},
        {"name": "textures", "category": "2d-texture", "depends_on": ["model"], "discipline": "texturing"},
        {"name": "materials", "category": "3d-material", "depends_on": ["textures"], "discipline": "technical-art"},
        {"name": "rig", "category": "3d-rig", "depends_on": ["model"], "discipline": "rigging"},
        {"name": "skinning", "category": "3d-skinning", "depends_on": ["rig", "model"], "discipline": "technical-art"},
        {"name": "idle", "category": "animation", "depends_on": ["rig"], "discipline": "animation"},
        {"name": "locomotion", "category": "animation", "depends_on": ["rig"], "discipline": "animation"},
        {"name": "combat_set", "category": "animation", "depends_on": ["rig"], "discipline": "animation"},
        {"name": "facial", "category": "animation", "depends_on": ["rig"], "discipline": "facial-animation"},
        {"name": "audio", "category": "audio", "depends_on": ["combat_set"], "discipline": "audio"},
    ],
    "environment": [
        {"name": "layout_blockout", "category": "3d-blockout", "depends_on": [], "discipline": "level-design"},
        {"name": "modular_assets", "category": "3d-model", "depends_on": ["layout_blockout"], "discipline": "modeling"},
        {"name": "texture_set", "category": "2d-texture", "depends_on": ["modular_assets"], "discipline": "texturing"},
        {"name": "material_set", "category": "3d-material", "depends_on": ["texture_set"], "discipline": "technical-art"},
        {"name": "lighting", "category": "lighting", "depends_on": ["material_set"], "discipline": "lighting"},
        {"name": "prop_set", "category": "3d-model", "depends_on": ["layout_blockout"], "discipline": "modeling"},
        {"name": "vfx_ambient", "category": "vfx", "depends_on": ["lighting"], "discipline": "vfx"},
        {"name": "audio_ambience", "category": "audio", "depends_on": [], "discipline": "audio"},
        {"name": "optimization", "category": "runtime", "depends_on": ["modular_assets", "material_set"], "discipline": "technical-art"},
    ],
    "ui_surface": [
        {"name": "design_system", "category": "ui-system", "depends_on": [], "discipline": "design-direction"},
        {"name": "visual_canon", "category": "ui-canon", "depends_on": ["design_system"], "discipline": "art-direction"},
        {"name": "component_set", "category": "ui-component", "depends_on": ["design_system"], "discipline": "ui-design"},
        {"name": "typography", "category": "ui-typography", "depends_on": ["design_system"], "discipline": "typography"},
        {"name": "icon_set", "category": "ui-icon", "depends_on": ["visual_canon"], "discipline": "ui-design"},
        {"name": "motion_grammar", "category": "ui-motion", "depends_on": ["design_system"], "discipline": "motion-design"},
        {"name": "illustration", "category": "2d-illustration", "depends_on": ["visual_canon"], "discipline": "illustration"},
        {"name": "runtime_assets", "category": "runtime", "depends_on": ["component_set", "icon_set"], "discipline": "frontend"},
    ],
    "cinematic_shot": [
        {"name": "story_beat", "category": "cinematic-story", "depends_on": [], "discipline": "cinematics"},
        {"name": "storyboard", "category": "cinematic-storyboard", "depends_on": ["story_beat"], "discipline": "cinematics"},
        {"name": "previs", "category": "cinematic-previs", "depends_on": ["storyboard"], "discipline": "layout"},
        {"name": "animatic", "category": "cinematic-animatic", "depends_on": ["previs"], "discipline": "editing"},
        {"name": "shot_layout", "category": "cinematic-layout", "depends_on": ["previs"], "discipline": "layout"},
        {"name": "camera_rig", "category": "camera", "depends_on": ["shot_layout"], "discipline": "camera"},
        {"name": "lighting", "category": "lighting", "depends_on": ["shot_layout"], "discipline": "lighting"},
        {"name": "vfx_layer", "category": "vfx", "depends_on": ["shot_layout"], "discipline": "vfx"},
        {"name": "composite", "category": "cinematic-composite", "depends_on": ["render", "vfx_layer"], "discipline": "compositing"},
        {"name": "sound_design", "category": "audio", "depends_on": ["animatic"], "discipline": "audio"},
        {"name": "grade", "category": "cinematic-grade", "depends_on": ["composite"], "discipline": "color"},
        {"name": "delivery", "category": "cinematic-delivery", "depends_on": ["grade", "sound_design"], "discipline": "delivery"},
    ],
    "vfx_system": [
        {"name": "reference", "category": "vfx-reference", "depends_on": [], "discipline": "vfx"},
        {"name": "particle_setup", "category": "vfx-particles", "depends_on": ["reference"], "discipline": "vfx"},
        {"name": "shader_set", "category": "shader", "depends_on": ["reference"], "discipline": "shader"},
        {"name": "simulation", "category": "vfx-sim", "depends_on": ["particle_setup"], "discipline": "vfx"},
        {"name": "flipbook", "category": "vfx-flipbook", "depends_on": ["simulation"], "discipline": "vfx"},
        {"name": "audio_impact", "category": "audio", "depends_on": [], "discipline": "audio"},
        {"name": "runtime_optimization", "category": "runtime", "depends_on": ["simulation", "shader_set"], "discipline": "technical-art"},
    ],
    "signature_entity": [
        {"name": "concept_thesis", "category": "2d-concept", "depends_on": [], "discipline": "creative-direction"},
        {"name": "hero_mesh", "category": "3d-model", "depends_on": ["concept_thesis"], "discipline": "modeling"},
        {"name": "uv_layout", "category": "3d-uv", "depends_on": ["hero_mesh"], "discipline": "technical-art"},
        {"name": "material_set", "category": "3d-material", "depends_on": ["hero_mesh"], "discipline": "technical-art"},
        {"name": "purposeful_rig", "category": "3d-rig", "depends_on": ["hero_mesh"], "discipline": "rigging"},
        {"name": "presence_animation", "category": "animation", "depends_on": ["purposeful_rig"], "discipline": "animation"},
        {"name": "signature_performance", "category": "animation", "depends_on": ["purposeful_rig"], "discipline": "animation"},
        {"name": "secondary_motion", "category": "animation", "depends_on": ["purposeful_rig"], "discipline": "animation"},
        {"name": "signature_vfx", "category": "vfx", "depends_on": ["signature_performance"], "discipline": "vfx"},
        {"name": "motivated_lighting", "category": "lighting", "depends_on": ["material_set"], "discipline": "lighting"},
        {"name": "presentation_environment", "category": "3d-environment", "depends_on": ["hero_mesh"], "discipline": "environment"},
        {"name": "camera_sequence", "category": "camera", "depends_on": ["presence_animation", "signature_performance"], "discipline": "cinematography"},
        {"name": "ui_identity", "category": "2d-ui", "depends_on": ["concept_thesis"], "discipline": "design-direction"},
        {"name": "runtime_export", "category": "runtime", "depends_on": ["hero_mesh", "material_set", "presence_animation", "signature_performance"], "discipline": "technical-art"},
        {"name": "audio_bed", "category": "audio", "depends_on": ["signature_performance"], "discipline": "audio"},
        {"name": "marketing_render", "category": "render", "depends_on": ["hero_mesh", "material_set", "motivated_lighting"], "discipline": "cinematics"},
    ],
    "audio_system": [
        {"name": "sfx_set", "category": "audio-sfx", "depends_on": [], "discipline": "audio"},
        {"name": "ambience", "category": "audio-ambience", "depends_on": [], "discipline": "audio"},
        {"name": "foley", "category": "audio-foley", "depends_on": [], "discipline": "audio"},
        {"name": "dialogue", "category": "audio-dialogue", "depends_on": [], "discipline": "audio"},
        {"name": "mix", "category": "audio-mix", "depends_on": ["sfx_set", "ambience", "foley", "dialogue"], "discipline": "audio"},
        {"name": "master", "category": "audio-master", "depends_on": ["mix"], "discipline": "audio"},
        {"name": "sync", "category": "audio-sync", "depends_on": ["mix"], "discipline": "audio"},
    ],
}


def discover(product_kind: str, product_name: str) -> dict[str, Any]:
    nodes = KNOWLEDGE_BASE.get(product_kind)
    if not nodes:
        return {"ok": False, "error": f"unknown_product_kind {product_kind}",
                "known_kinds": sorted(KNOWLEDGE_BASE)}
    by_name = {n["name"]: n for n in nodes}
    edges = []
    for n in nodes:
        for dep in n["depends_on"]:
            if dep in by_name:
                edges.append({"from": dep, "to": n["name"]})
    node_ids = {n["name"]: f"{product_name.replace(' ', '-').lower()}-{i:02d}"
                for i, n in enumerate(nodes)}
    return {
        "ok": True,
        "product": product_name,
        "product_kind": product_kind,
        "node_count": len(nodes),
        "edge_count": len(edges),
        "nodes": [{"id": node_ids[n["name"]], "name": n["name"], "category": n["category"],
                   "discipline": n["discipline"], "depends_on": n["depends_on"],
                   "quality_sensitive": n.get("quality_sensitive", n["category"] in ("animation", "vfx", "3d-model", "2d-concept"))}
                  for n in nodes],
        "edges": edges,
        "disciplines_required": sorted({n["discipline"] for n in nodes}),
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="requirement_discovery")
    p.add_argument("product_kind")
    p.add_argument("product_name")
    args = p.parse_args(argv)
    print(json.dumps(discover(args.product_kind, args.product_name), indent=2, ensure_ascii=False))
    return 0 if discover(args.product_kind, args.product_name).get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
