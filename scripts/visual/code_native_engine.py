"""
11vatedTech Code-Native Visual Intelligence Engine

Extends the existing VPI with code-native and hybrid visual synthesis.

Capabilities:
- Visual Representation Router (intent -> medium selection)
- Code-Native Brief Compiler
- Procedural Gradient Director
- CSS Material Synthesis
- SVG Illustration Intelligence
- Shape Language Engine
- Shader Director (GLSL/WGSL)
- Procedural Material Director
- Motion Choreography Intelligence
- Typography Art Director
- Reference-to-Procedure Translator
- Visual Decomposition Engine
- Hybrid Visual Compositor
- Code-Native Perceptual QA
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict, List, Any


# ============================================================
# VISUAL REPRESENTATION ROUTER
# ============================================================

REPRESENTATION_MEDIA = {
    "css": {
        "strengths": ["responsive", "gradients", "layout", "animation", "transparency"],
        "weaknesses": ["complex geometry", "3D", "photorealism"],
        "best_for": ["UI chrome", "layout", "simple materials", "responsive design"],
        "performance": "excellent",
        "editability": "high",
        "determinism": "high",
    },
    "svg": {
        "strengths": ["vector precision", "scalability", "animation", "filters", "identity"],
        "weaknesses": ["complex scenes", "raster effects", "performance with many nodes"],
        "best_for": ["logos", "icons", "illustrations", "brand identity", "technical graphics"],
        "performance": "good",
        "editability": "high",
        "determinism": "high",
    },
    "canvas2d": {
        "strengths": ["procedural drawing", "particles", "brush simulation", "image processing"],
        "weaknesses": ["resolution dependent", "no DOM integration"],
        "best_for": ["generative art", "data visualization", "interactive illustrations"],
        "performance": "good",
        "editability": "medium",
        "determinism": "low",
    },
    "webgl": {
        "strengths": ["GPU acceleration", "shaders", "3D", "postprocessing", "particles"],
        "weaknesses": ["complexity", "fallback required", "mobile limits"],
        "best_for": ["shader art", "3D scenes", "GPU particles", "material simulation"],
        "performance": "excellent (GPU)",
        "editability": "low",
        "determinism": "low",
    },
    "webgpu": {
        "strengths": ["compute shaders", "large datasets", "simulation", "custom rendering"],
        "weaknesses": ["browser support", "complexity", "learning curve"],
        "best_for": ["compute-heavy", "large procedural fields", "simulation"],
        "performance": "excellent (when supported)",
        "editability": "very low",
        "determinism": "low",
    },
    "three_js": {
        "strengths": ["3D scenes", "materials", "lighting", "postprocessing", "instancing"],
        "weaknesses": ["bundle size", "complexity", "mobile performance"],
        "best_for": ["3D product visualization", "environments", "complex scenes"],
        "performance": "good",
        "editability": "medium",
        "determinism": "medium",
    },
    "blender": {
        "strengths": ["physically accurate", "materials", "lighting", "animation", "rendering"],
        "weaknesses": ["not real-time", "render time", "integration"],
        "best_for": ["product renders", "characters", "environments", "VFX"],
        "performance": "slow (offline)",
        "editability": "high",
        "determinism": "high",
    },
    "generative_image": {
        "strengths": ["photorealism", "creative exploration", "atmosphere", "characters"],
        "weaknesses": ["non-deterministic", "artifact prone", "identity instability"],
        "best_for": ["hero visuals", "concepts", "atmosphere", "characters"],
        "performance": "slow (generation)",
        "editability": "low",
        "determinism": "very low",
    },
    "hybrid": {
        "strengths": ["combines all", "highest potential fidelity"],
        "weaknesses": ["complexity", "coherence challenges", "integration"],
        "best_for": ["hero compositions", "premium experiences"],
        "performance": "varies",
        "editability": "medium",
        "determinism": "medium",
    },
}


def route_representation(
    visual_intent: str,
    asset_type: str = "general",
    fidelity: str = "production",
    interaction: bool = False,
    motion: bool = False,
    responsive: bool = True,
    identity_sensitive: bool = False,
    runtime_target: str = "browser",
    performance_budget: str = "normal",
    determinism_required: bool = False,
) -> Dict:
    """
    Route a visual requirement to the optimal representation medium.
    
    Returns medium selection with reasoning.
    """
    # Intent keyword analysis for stronger signal
    intent_lower = visual_intent.lower()
    wants_gpu = any(w in intent_lower for w in ["shader", "gpu", "webgl", "webgpu", "real-time", "fluid", "compute"])
    wants_3d = any(w in intent_lower for w in ["3d", "three.js", "scene", "volumetric", "raymarch"])
    wants_generative = any(w in intent_lower for w in ["generative", "procedural", "particle", "simulation"])
    wants_vector = any(w in intent_lower for w in ["vector", "svg", "logo", "brand", "identity", "emblem"])
    wants_css = any(w in intent_lower for w in ["layout", "responsive", "ui", "interface", "typography"])
    
    scores = {}
    
    for medium, props in REPRESENTATION_MEDIA.items():
        score = 30  # base — low enough for intent to matter
        
        # Boost for relevant strengths
        if responsive and "responsive" in props["strengths"]:
            score += 12
        if interaction and "animation" in props["strengths"]:
            score += 8
        if identity_sensitive and "identity" in props["strengths"]:
            score += 12
        if determinism_required and props["determinism"] == "high":
            score += 18
        
        # Intent-based boosts (strong signal)
        if wants_gpu and medium in ["webgl", "webgpu"]:
            score += 30
        if wants_3d and medium in ["three_js", "webgl"]:
            score += 25
        if wants_generative and medium in ["canvas2d", "webgl"]:
            score += 20
        if wants_vector and medium == "svg":
            score += 30
        if wants_css and medium == "css":
            score += 20
        
        # Boost for best-for match
        for bf in props["best_for"]:
            if asset_type.lower() in bf.lower() or bf.lower() in intent_lower:
                score += 12
        
        # Penalty for weaknesses (stronger)
        if runtime_target == "browser" and medium in ["blender", "generative_image"]:
            score -= 25
        if performance_budget == "tight" and props["performance"] in ["slow (offline)", "slow (generation)"]:
            score -= 20
        if wants_gpu and medium not in ["webgl", "webgpu", "three_js"]:
            score -= 10
        if wants_vector and medium != "svg":
            score -= 5
        
        scores[medium] = score
    
    # Select top medium
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    primary = ranked[0][0]
    
    # Build pipeline (primary + potential secondary)
    pipeline = [primary]
    if fidelity in ["production", "hero"] and primary not in ["hybrid"]:
        # Consider hybrid for high fidelity
        if ranked[1][1] > 60:
            pipeline.append(ranked[1][0])
    
    return {
        "primary_medium": primary,
        "pipeline": pipeline,
        "scores": {k: v for k, v in ranked},
        "reasoning": f"Selected {primary} for {asset_type} at {fidelity} fidelity",
    }


# ============================================================
# PROCEDURAL GRADIENT DIRECTOR
# ============================================================

GRADIENT_SEMANTICS = {
    "key_light": {
        "type": "radial",
        "position": "top-center",
        "colors": ["transparent", "rgba(255,220,180,0.15)"],
        "description": "Primary illumination source",
    },
    "fill_light": {
        "type": "radial",
        "position": "side",
        "colors": ["transparent", "rgba(200,210,230,0.08)"],
        "description": "Shadow-side illumination",
    },
    "rim_light": {
        "type": "linear",
        "angle": "0deg",
        "colors": ["rgba(201,169,110,0.12)", "transparent"],
        "description": "Edge separation light",
    },
    "atmospheric_depth": {
        "type": "linear",
        "angle": "180deg",
        "colors": ["transparent", "rgba(8,8,12,0.4)"],
        "description": "Distance fog / depth cue",
    },
    "vignette": {
        "type": "radial",
        "position": "center",
        "colors": ["transparent", "rgba(0,0,0,0.3)"],
        "description": "Focus draw / edge darkening",
    },
    "specular_highlight": {
        "type": "radial",
        "position": "off-center",
        "colors": ["rgba(255,255,255,0.1)", "transparent"],
        "description": "Material specular response",
    },
}

MATERIAL_GRADIENTS = {
    "chrome": {
        "layers": [
            {"type": "linear", "angle": "135deg", "colors": ["#2a2a30", "#8a8a92", "#d4d4dc", "#8a8a92", "#2a2a30"]},
            {"type": "radial", "position": "30% 20%", "colors": ["rgba(255,255,255,0.1)", "transparent"]},
        ],
        "filters": ["contrast(1.1)"],
    },
    "gold": {
        "layers": [
            {"type": "linear", "angle": "135deg", "colors": ["#7a6340", "#c9a96e", "#e8d5a3", "#c9a96e", "#7a6340"]},
            {"type": "radial", "position": "40% 30%", "colors": ["rgba(232,213,163,0.15)", "transparent"]},
        ],
        "filters": [],
    },
    "pearl": {
        "layers": [
            {"type": "linear", "angle": "160deg", "colors": ["#e8e4dc", "#f5f0e8", "#e8e4dc", "#d4cfc6"]},
            {"type": "radial", "position": "50% 40%", "colors": ["rgba(255,255,255,0.2)", "transparent"]},
        ],
        "filters": ["brightness(1.05)"],
    },
    "glass": {
        "layers": [
            {"type": "linear", "angle": "180deg", "colors": ["rgba(255,255,255,0.08)", "rgba(255,255,255,0.02)"]},
            {"type": "radial", "position": "50% 0%", "colors": ["rgba(255,255,255,0.12)", "transparent"]},
        ],
        "filters": ["backdrop-filter: blur(10px)"],
    },
    "velvet": {
        "layers": [
            {"type": "linear", "angle": "180deg", "colors": ["#1a0a2e", "#2d1b4e", "#1a0a2e"]},
            {"type": "radial", "position": "50% 60%", "colors": ["rgba(45,27,78,0.3)", "transparent"]},
        ],
        "filters": ["contrast(1.2)"],
    },
}


def generate_gradient_css(
    semantic: str,
    material: Optional[str] = None,
    custom_colors: Optional[List[str]] = None,
) -> str:
    """Generate CSS gradient code for a semantic lighting/material intent."""
    if material and material in MATERIAL_GRADIENTS:
        mat = MATERIAL_GRADIENTS[material]
        layers = []
        for layer in mat["layers"]:
            if layer["type"] == "linear":
                layers.append(f"linear-gradient({layer['angle']}, {', '.join(layer['colors'])})")
            elif layer["type"] == "radial":
                layers.append(f"radial-gradient(circle at {layer['position']}, {', '.join(layer['colors'])})")
        return ", ".join(layers)
    
    if semantic in GRADIENT_SEMANTICS:
        g = GRADIENT_SEMANTICS[semantic]
        if custom_colors:
            colors = custom_colors
        else:
            colors = g["colors"]
        if g["type"] == "radial":
            return f"radial-gradient(circle at {g.get('position', 'center')}, {', '.join(colors)})"
        else:
            return f"linear-gradient({g.get('angle', '180deg')}, {', '.join(colors)})"
    
    return "transparent"


# ============================================================
# SHAPE LANGUAGE ENGINE
# ============================================================

SHAPE_PRIMITIVES = {
    "superellipse": "M x0 y0 C ... Z",  # parametric
    "blob": "smooth organic closed curve",
    "arch": "curved structural element",
    "wedge": "tapered directional form",
    "ribbon": "flowing linear element",
    "ring": "concentric circular element",
    "lens": "convex/concave optical form",
}


def shape_language_analysis(visual_intent: str) -> Dict:
    """Analyze visual intent and recommend shape language."""
    shapes = []
    
    # Intent-based shape recommendations
    if any(w in visual_intent.lower() for w in ["organic", "natural", "fluid", "living"]):
        shapes.extend(["blob", "ribbon", "lens"])
    if any(w in visual_intent.lower() for w in ["precision", "technical", "exact", "geometric"]):
        shapes.extend(["superellipse", "arch", "wedge"])
    if any(w in visual_intent.lower() for w in ["luxury", "premium", "elegant"]):
        shapes.extend(["superellipse", "ribbon", "ring"])
    if any(w in visual_intent.lower() for w in ["dynamic", "energy", "motion"]):
        shapes.extend(["wedge", "ribbon", "blob"])
    
    if not shapes:
        shapes = ["superellipse", "ribbon"]
    
    return {
        "recommended_shapes": shapes,
        "shape_rhythm": "varied" if len(shapes) > 2 else "restrained",
        "negative_space": "generous" if "luxury" in visual_intent.lower() else "balanced",
    }


# ============================================================
# CODE-NATIVE BRIEF COMPILER
# ============================================================

def compile_code_native_brief(
    founder_instruction: str,
    product_context: Optional[Dict] = None,
    quality_mode: str = "production",
) -> Dict:
    """
    Compile founder instruction into a code-native visual brief.
    
    Reasons from aesthetic properties to rendering mechanisms.
    """
    brief = {
        "raw_instruction": founder_instruction,
        "quality_mode": quality_mode,
        "form": "",
        "material": "",
        "light": "",
        "motion": "",
        "color": "",
        "interaction": "",
        "forbidden": [],
        "implementation_hints": [],
    }
    
    # Form analysis
    if any(w in founder_instruction.lower() for w in ["organic", "living", "grown", "fluid"]):
        brief["form"] = "organic continuous curvature, non-geometric"
        brief["implementation_hints"].extend(["domain warping", "FBM noise", "smooth SDF"])
    elif any(w in founder_instruction.lower() for w in ["precise", "geometric", "architectural"]):
        brief["form"] = "precise geometric, controlled proportions"
        brief["implementation_hints"].extend(["superellipses", "Bezierr splines", "grid systems"])
    else:
        brief["form"] = "intentional form with clear shape language"
    
    # Material analysis
    if any(w in founder_instruction.lower() for w in ["chrome", "metallic", "reflective"]):
        brief["material"] = "reflective but imperfect metallic surface"
        brief["implementation_hints"].extend(["Fresnel", "anisotropic highlights", "environment mapping"])
    elif any(w in founder_instruction.lower() for w in ["glass", "translucent", "crystal"]):
        brief["material"] = "translucent with refraction and internal light"
        brief["implementation_hints"].extend(["IOR", "chromatic aberration", "subsurface"])
    elif any(w in founder_instruction.lower() for w in ["velvet", "soft", "fabric"]):
        brief["material"] = "soft surface with subtle sheen"
        brief["implementation_hints"].extend(["sheen gradient", "microfiber texture"])
    
    # Light analysis
    if any(w in founder_instruction.lower() for w in ["dramatic", "cinematic", "theatrical"]):
        brief["light"] = "dramatic key light with controlled shadows"
    elif any(w in founder_instruction.lower() for w in ["soft", "ambient", "gentle"]):
        brief["light"] = "soft ambient with gentle falloff"
    
    # Forbidden patterns
    brief["forbidden"] = [
        "GRADIENT_AS_ART_DIRECTION",
        "GLASSMORPHISM_AS_FIDELITY_PROXY",
        "PARTICLE_SYSTEM_AS_VISUAL_CONCEPT",
        "NEON_AS_PREMIUM_PROXY",
        "BLOOM_AS_QUALITY_PROXY",
        "THREEJS_PRIMITIVE_AS_HERO_ASSET",
        "BIG_TYPOGRAPHY_AS_VISUAL_IDENTITY",
    ]
    
    return brief


# ============================================================
# VISUAL DECOMPOSITION ENGINE
# ============================================================

def decompose_composition(
    brief: Dict,
    representation: Dict,
) -> List[Dict]:
    """
    Decompose a visual composition into independent production layers.
    
    Each layer is assigned to the strongest production medium.
    """
    layers = []
    
    # Layer 0: Background atmosphere
    layers.append({
        "layer": "L0_background",
        "description": "ambient atmosphere, gradient field, depth",
        "medium": "css" if representation["primary_medium"] in ["css", "svg"] else "canvas2d",
        "priority": "foundation",
    })
    
    # Layer 1: Structural elements
    layers.append({
        "layer": "L1_structure",
        "description": "architecture, frames, structural geometry",
        "medium": "svg" if "svg" in representation["pipeline"] else "css",
        "priority": "structural",
    })
    
    # Layer 2: Hero element
    layers.append({
        "layer": "L2_hero",
        "description": "primary focal element",
        "medium": representation["primary_medium"],
        "priority": "primary",
    })
    
    # Layer 3: Typography
    layers.append({
        "layer": "L3_typography",
        "description": "text hierarchy, type-as-form",
        "medium": "html/svg",
        "priority": "information",
    })
    
    # Layer 4: Material effects
    if representation["primary_medium"] in ["webgl", "three_js", "hybrid"]:
        layers.append({
            "layer": "L4_material_fx",
            "description": "shader effects, material simulation",
            "medium": "webgl",
            "priority": "enhancement",
        })
    
    # Layer 5: Grain / texture
    layers.append({
        "layer": "L5_texture",
        "description": "grain, noise, tactile quality",
        "medium": "css/svg",
        "priority": "finish",
    })
    
    # Layer 6: Motion
    layers.append({
        "layer": "L6_motion",
        "description": "animation, choreography, timing",
        "medium": "css/waapi",
        "priority": "temporal",
    })
    
    return layers


# ============================================================
# HYBRID VISUAL COMPOSITOR
# ============================================================

def compose_hybrid(
    layers: List[Dict],
    coherence_checks: Optional[List[str]] = None,
) -> Dict:
    """
    Compose multiple production layers into one coherent visual.
    
    Returns composition instructions and coherence requirements.
    """
    if coherence_checks is None:
        coherence_checks = [
            "palette_consistency",
            "lighting_direction",
            "perspective",
            "depth_consistency",
            "material_language",
            "grain_consistency",
            "scale_relationships",
            "motion_character",
        ]
    
    return {
        "layers": layers,
        "coherence_checks": coherence_checks,
        "medium_count": len(set(l["medium"] for l in layers)),
        "integration_notes": "Ensure all layers share one visual world",
    }


# ============================================================
# CODE-NATIVE PERCEPTUAL QA
# ============================================================

CODE_NATIVE_QA_DIMENSIONS = [
    ("composition", "Is the composition intentional and not default?"),
    ("visual_hierarchy", "Is there clear focal direction?"),
    ("material_quality", "Do materials look deliberate, not default?"),
    ("shape_sophistication", "Are shapes designed, not default primitives?"),
    ("lighting", "Is lighting art-directed, not just present?"),
    ("typography", "Is type professional and intentional?"),
    ("motion", "Does animation serve purpose, not just exists?"),
    ("originality", "Could this come from a template?"),
    ("depth", "Is there atmospheric depth and layering?"),
    ("interaction_feedback", "Does interaction feel designed?"),
    ("coherence", "Do all elements feel like one visual world?"),
    ("commercial_finish", "Would this survive commercial scrutiny?"),
]


def code_native_perceptual_qa(asset_type: str = "general") -> List[Dict]:
    """Generate perceptual QA checklist for code-native visuals."""
    checklist = []
    for dim, question in CODE_NATIVE_QA_DIMENSIONS:
        checklist.append({
            "dimension": dim,
            "question": question,
            "status": "pending",
            "notes": "",
        })
    return checklist


# ============================================================
# FAILURE PATTERNS
# ============================================================

CODE_NATIVE_FAILURE_PATTERNS = {
    "GRADIENT_AS_ART_DIRECTION": "Using a gradient as the entire visual concept",
    "GLASSMORPHISM_AS_FIDELITY_PROXY": "Defaulting to glassmorphism for 'premium' feel",
    "PARTICLE_SYSTEM_AS_VISUAL_CONCEPT": "Particles = visual design",
    "NEON_AS_PREMIUM_PROXY": "Neon glow = premium",
    "BLOOM_AS_QUALITY_PROXY": "Bloom = quality",
    "THREEJS_PRIMITIVE_AS_HERO_ASSET": "Default Three.js geometry as hero",
    "BIG_TYPOGRAPHY_AS_VISUAL_IDENTITY": "Large type = visual identity",
    "ANIMATION_QUANTITY_AS_MOTION_QUALITY": "More animation = better motion",
    "SHADER_COMPLEXITY_AS_ARTISTIC_QUALITY": "Complex shader = good art",
    "DEFAULT_CIRCLE_AS_ORGANIC": "Default circle = organic form",
    "UNMODIFIED_STOCK_PRIMITIVE": "Unmodified stock Three.js/CSS primitive",
}


def detect_code_native_failure_patterns(code: str) -> List[Dict]:
    """Scan code for known failure patterns."""
    detected = []
    
    patterns_to_check = {
        "linear-gradient(.*#111.*#222)": "GRADIENT_AS_ART_DIRECTION",
        "backdrop-filter.*blur": "GLASSMORPHISM_AS_FIDELITY_PROXY",
        "THREE\\.SphereGeometry": "THREEJS_PRIMITIVE_AS_HERO_ASSET",
        "THREE\\.BoxGeometry": "THREEJS_PRIMITIVE_AS_HERO_ASSET",
        "THREE\\.PlaneGeometry": "THREEJS_PRIMITIVE_AS_HERO_ASSET",
        "font-size.*clamp.*8vw": "BIG_TYPOGRAPHY_AS_VISUAL_IDENTITY",
    }
    
    import re
    for pattern, failure_id in patterns_to_check.items():
        if re.search(pattern, code):
            detected.append({
                "pattern": failure_id,
                "description": CODE_NATIVE_FAILURE_PATTERNS.get(failure_id, ""),
                "severity": "warning",
            })
    
    return detected


# Export
__all__ = [
    "route_representation",
    "generate_gradient_css",
    "shape_language_analysis",
    "compile_code_native_brief",
    "decompose_composition",
    "compose_hybrid",
    "code_native_perceptual_qa",
    "detect_code_native_failure_patterns",
    "REPRESENTATION_MEDIA",
    "GRADIENT_SEMANTICS",
    "MATERIAL_GRADIENTS",
    "CODE_NATIVE_FAILURE_PATTERNS",
]
