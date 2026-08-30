#!/usr/bin/env python3
"""
11VatedTech Creative Intelligence + Fidelity Atlas
====================================================
Core engine for benchmarking, classifying, and routing creative capabilities.
"""

import json
import os
import time
import urllib.request
from dataclasses import dataclass, field, asdict
from typing import Optional
from pathlib import Path

COMFYUI_URL = "http://127.0.0.1:8188"
PROJECT_ROOT = Path(__file__).parent.parent.parent
ARTIFACTS = PROJECT_ROOT / "artifacts" / "visual" / "atlas"
ARTIFACTS.mkdir(parents=True, exist_ok=True)

# ============================================================
# CREATIVE CAPABILITY ONTOLOGY
# ============================================================

ARTIFACT_CLASSES = [
    "character", "creature", "human", "portrait", "environment",
    "architecture", "vehicle", "prop", "product", "fashion",
    "logo", "symbol", "illustration", "poster", "editorial",
    "UI", "HUD", "icon", "sprite", "tile", "texture", "material",
    "shader", "VFX", "motion_graphic", "cinematic", "animation",
    "3D_model", "sculpture", "procedural_form", "data_visualization",
    "interactive_art", "typography", "brand_system"
]

REPRESENTATIONS = [
    "raster", "vector", "pixel", "sprite", "2D_layered",
    "2.5D", "3D_mesh", "procedural_geometry", "SDF", "shader",
    "generative", "hybrid"
]

STYLE_FAMILIES = {
    "photoreal": {"desc": "Photorealistic rendering", "risk_human": "HIGH", "strength_product": "HIGH"},
    "cinematic_realism": {"desc": "Film-quality realism", "risk_human": "MEDIUM", "strength_product": "HIGH"},
    "concept_art": {"desc": "Professional concept art", "risk_human": "LOW", "strength_creature": "HIGH"},
    "anime": {"desc": "Japanese animation style", "risk_human": "LOW", "strength_character": "VERY_HIGH"},
    "cel_shaded": {"desc": "Cel/toon shading", "risk_human": "LOW", "strength_character": "HIGH"},
    "digital_painting": {"desc": "Painterly digital art", "risk_human": "MEDIUM", "strength_environment": "HIGH"},
    "pixel_art": {"desc": "Pixel-level precision art", "risk_human": "LOW", "strength_sprite": "VERY_HIGH"},
    "vector": {"desc": "Clean vector illustration", "risk_human": "LOW", "strength_identity": "VERY_HIGH"},
    "flat_graphic": {"desc": "Modern flat graphic design", "risk_human": "LOW", "strength_UI": "HIGH"},
    "low_poly": {"desc": "Low polygon 3D", "risk_human": "LOW", "strength_3D": "HIGH"},
    "procedural": {"desc": "Mathematically generated", "risk_human": "LOW", "strength_shader": "VERY_HIGH"},
    "abstract": {"desc": "Non-representational art", "risk_human": "LOW", "strength_shader": "HIGH"},
    "surreal": {"desc": "Dreamlike imagery", "risk_human": "MEDIUM", "strength_illustration": "HIGH"},
    "fantasy": {"desc": "Fantasy illustration", "risk_human": "LOW", "strength_creature": "VERY_HIGH"},
    "sci_fi": {"desc": "Science fiction", "risk_human": "MEDIUM", "strength_environment": "HIGH"},
    "luxury": {"desc": "Premium commercial aesthetic", "risk_human": "MEDIUM", "strength_product": "VERY_HIGH"},
    "minimalist": {"desc": "Reduced essential elements", "risk_human": "LOW", "strength_identity": "HIGH"},
    "maximalist": {"desc": "Rich detailed composition", "risk_human": "MEDIUM", "strength_illustration": "HIGH"},
    "organic": {"desc": "Natural flowing forms", "risk_human": "MEDIUM", "strength_creature": "HIGH"},
    "brutalist": {"desc": "Raw powerful design", "risk_human": "LOW", "strength_UI": "MEDIUM"},
}

CONFIDENCE_LEVELS = [
    "EXCEPTIONAL", "STRONG", "PRODUCTION_CAPABLE",
    "GUARDED", "EXPERIMENTAL", "WEAK", "UNPROVEN"
]

# ============================================================
# FAILURE TAXONOMY
# ============================================================

FAILURE_CATEGORIES = {
    "human_anatomy": {
        "hands": {"risk": "HIGH", "recovery": ["reference_pose", "controlnet_pose", "hand_crop", "inpainting", "stylization", "3D_hand"]},
        "fingers": {"risk": "HIGH", "recovery": ["pose_control", "regional_inpaint", "stylize", "partial_occlusion"]},
        "feet": {"risk": "MEDIUM", "recovery": ["framing", "shoes", "stylization"]},
        "ears": {"risk": "MEDIUM", "recovery": ["hair_coverage", "angle", "stylization"]},
        "teeth": {"risk": "HIGH", "recovery": ["mouth_closed", "stylization", "cropping"]},
        "eyes": {"risk": "MEDIUM", "recovery": ["reference", "symmetry_control", "model_selection"]},
        "facial_symmetry": {"risk": "MEDIUM", "recovery": ["reference_conditioning", "ControlNet", "face_crop"]},
        "profile_views": {"risk": "HIGH", "recovery": ["3D_rotation", "reference", "stylization"]},
        "foreshortening": {"risk": "HIGH", "recovery": ["pose_reference", "3D_blockout", "compositional_framing"]},
        "body_contact": {"risk": "HIGH", "recovery": ["3D_scene", "compositing", "stylization"]},
        "crossed_limbs": {"risk": "HIGH", "recovery": ["pose_reference", "inpainting"]},
    },
    "identity_consistency": {
        "same_character_cross_image": {"risk": "HIGH", "recovery": ["IP-Adapter", "reference_package", "3D_canon", "LoRA"]},
        "costume_continuity": {"risk": "MEDIUM", "recovery": ["reference_conditioning", "canon_documentation"]},
        "age_stability": {"risk": "MEDIUM", "recovery": ["reference", "canon_assets"]},
    },
    "objects": {
        "symmetry": {"risk": "MEDIUM", "recovery": ["mirror_copy", "SVG", "Blender", "procedural"]},
        "mechanical_coherence": {"risk": "HIGH", "recovery": ["Blender", "technical_reference", "3D_model"]},
        "text_generation": {"risk": "VERY_HIGH", "recovery": ["deterministic_type", "SVG_type", "HTML_type"]},
        "logos": {"risk": "HIGH", "recovery": ["SVG", "vector", "deterministic"]},
        "transparent_parts": {"risk": "HIGH", "recovery": ["Blender", "shader", "compositing"]},
        "repeated_patterns": {"risk": "MEDIUM", "recovery": ["procedural", "SVG_pattern", "tiling"]},
    },
    "environments": {
        "perspective": {"risk": "MEDIUM", "recovery": ["3D_scene", "vanishing_point", "grid"]},
        "architectural_logic": {"risk": "HIGH", "recovery": ["Blender", "Unreal", "arch_reference"]},
        "scale_continuity": {"risk": "MEDIUM", "recovery": ["depth_control", "compositing"]},
    },
    "motion": {
        "temporal_flicker": {"risk": "HIGH", "recovery": ["keyframe_control", "temporal_consistency", "post_processing"]},
        "identity_drift": {"risk": "HIGH", "recovery": ["IP-Adapter_per_frame", "reference_identity", "3D_model"]},
        "limb_deformation": {"risk": "HIGH", "recovery": ["skeletal_control", "3D_rig", "keyframe"]},
    },
}

# ============================================================
# BENCHMARK CATEGORIES (from Section 56)
# ============================================================

BENCHMARK_BRIEFS = {
    "A_high_end_2D": {
        "artifact_class": "illustration",
        "style": "concept_art",
        "representation": "generative",
        "brief": "A weathered explorer standing at the edge of a luminous underground cavern, bioluminescent crystals casting prismatic light across carved ancient walls, concept art quality with dramatic rim lighting and atmospheric depth",
        "dimensions": "768x1024",
        "positive": "concept art, masterpiece, cinematic lighting, atmospheric, detailed, rim light, volumetric fog, dramatic composition, professional illustration",
        "negative": "low quality, blurry, deformed, ugly, text, watermark, logo",
        "model": "dreamshaper_8",
    },
    "B_character_creature": {
        "artifact_class": "creature",
        "style": "fantasy",
        "representation": "generative",
        "brief": "A majestic forest guardian creature with antler-like branches growing crystalline flowers, mossy fur textures, wise ancient eyes, standing in a misty ancient forest, full body concept art with silhouette clarity",
        "dimensions": "768x1024",
        "positive": "fantasy creature concept art, detailed creature design, mossy organic textures, crystal growth, ancient wise eyes, forest environment, misty atmosphere, full body, strong silhouette, professional concept art",
        "negative": "low quality, blurry, deformed, ugly, text, watermark, generic, amorphous blob",
        "model": "dreamshaper_8",
    },
    "C_difficult_anatomy": {
        "artifact_class": "portrait",
        "style": "digital_painting",
        "representation": "generative",
        "brief": "Close-up of two hands gently holding a fragile glass orb containing a miniature galaxy, detailed finger anatomy, soft directional lighting, painterly digital art quality with visible brushwork",
        "dimensions": "768x768",
        "positive": "two hands holding glass orb, detailed finger anatomy, galaxy inside glass sphere, soft studio lighting, painterly brushwork, digital painting, close-up hands, masterful anatomy, professional quality",
        "negative": "low quality, blurry, deformed hands, extra fingers, fused fingers, ugly, missing fingers, bad anatomy, text, watermark",
        "model": "dreamshaper_8",
    },
    "D_pixel_sprite": {
        "artifact_class": "sprite",
        "style": "pixel_art",
        "representation": "pixel",
        "brief": "A set of 4 pixel art character poses for a fantasy mage character: idle, casting spell, walking, and jumping. 64x64 each, limited 16-color palette, clear silhouette, distinct frames on transparent background",
        "dimensions": "512x512",
        "positive": "pixel art, 16-color palette, fantasy mage character, 64x64 sprite sheet, idle pose, casting spell, walking, jumping, transparent background, clean pixels, retro game art, crisp edges, no anti-aliasing",
        "negative": "blurry, smooth, anti-aliased, photographic, realistic, text, watermark, high resolution detail",
        "model": "dreamshaper_8",
    },
    "E_vector_identity": {
        "artifact_class": "logo",
        "style": "vector",
        "representation": "vector",
        "brief": "Premium brand identity mark for a luxury organic skincare company called 'Terra Botanica' — abstract botanical form, geometric precision meets organic curves, gold and deep forest green on dark background",
        "dimensions": "1024x1024",
        "positive": "premium brand identity, luxury logo, botanical abstract mark, geometric organic, gold accent, forest green, clean vector style, professional brand design, minimalist luxury, high-end cosmetics brand",
        "negative": "low quality, blurry, text, watermark, clip art, generic, amateur, stock illustration, messy",
        "model": "dreamshaper_xl_turbo",
    },
    "F_2_5D_composition": {
        "artifact_class": "environment",
        "style": "digital_painting",
        "representation": "2.5D",
        "brief": "A layered scene of a futuristic Japanese street market at dusk, multiple depth layers: foreground lanterns, mid-ground stalls with characters, background neon-lit skyscrapers, atmospheric perspective, warm and cool color contrast",
        "dimensions": "1024x768",
        "positive": "layered depth scene, Japanese street market, futuristic, dusk lighting, neon glow, atmospheric perspective, warm lanterns, cool neon background, detailed environment, cinematic composition, professional concept art",
        "negative": "low quality, blurry, flat, no depth, text, watermark, generic, amateur",
        "model": "dreamshaper_xl_turbo",
    },
    "G_3D_product": {
        "artifact_class": "product",
        "style": "luxury",
        "representation": "generative",
        "brief": "A premium wireless headphone product shot on dark reflective surface, dramatic studio lighting with warm key and cool fill, metallic and leather materials, floating slightly above surface, hero product photography quality",
        "dimensions": "1024x1024",
        "positive": "premium headphone product photography, studio lighting, dark reflective surface, metallic materials, leather texture, hero product shot, commercial photography, dramatic lighting, professional product render",
        "negative": "low quality, blurry, text, watermark, amateur, stock photo, generic background",
        "model": "dreamshaper_xl_turbo",
    },
    "H_stylized_3D": {
        "artifact_class": "3D_model",
        "style": "low_poly",
        "representation": "3D_mesh",
        "brief": "A stylized low-poly dragon perched on a treasure hoard, isometric view, warm firelight, jewel-toned palette, clean polygonal forms with deliberate facet visibility, playful yet majestic design",
        "dimensions": "1024x1024",
        "positive": "low poly dragon, stylized 3D, isometric view, treasure hoard, warm firelight, jewel tones, clean polygonal facets, playful design, fantasy game art, professional stylized 3D",
        "negative": "photorealistic, blurry, text, watermark, messy topology, ugly, generic",
        "model": "dreamshaper_xl_turbo",
    },
    "I_environment": {
        "artifact_class": "environment",
        "style": "concept_art",
        "representation": "generative",
        "brief": "An expansive alien marketplace built into the interior of a massive geode cave, crystalline walls refracting light from floating bioluminescent vendors, alien architecture with organic curves, deep atmospheric depth",
        "dimensions": "1024x768",
        "positive": "alien marketplace, geode cave interior, crystalline walls, bioluminescent, floating vendors, organic architecture, deep atmosphere, concept art, professional environment design, cinematic depth, epic scale",
        "negative": "low quality, blurry, flat, text, watermark, generic, amateur, small scale",
        "model": "dreamshaper_xl_turbo",
    },
    "J_material_shader": {
        "artifact_class": "shader",
        "style": "procedural",
        "representation": "shader",
        "brief": "WebGL shader art: iridescent soap bubble surface with thin-film interference colors, realistic fluid distortion, Fresnel edge highlights, environmental reflections, mouse-reactive surface tension",
        "dimensions": "html_shader",
        "model": "code_native",
    },
    "K_motion_animation": {
        "artifact_class": "motion_graphic",
        "style": "minimalist",
        "representation": "hybrid",
        "brief": "Motion graphics: geometric shapes assembling into a premium logo mark through choreographed entrance, staggered timing, anticipation-settle motion, professional easing, dark background",
        "dimensions": "html_motion",
        "model": "code_native",
    },
    "L_VFX": {
        "artifact_class": "VFX",
        "style": "sci_fi",
        "representation": "generative",
        "brief": "A sci-fi energy portal vortex, swirling plasma rings with electrical arcs, deep purple and electric blue energy streams, particle spray, volumetric glow, dramatic composition",
        "dimensions": "768x1024",
        "positive": "sci-fi energy portal, plasma vortex, electrical arcs, purple blue energy, particles, volumetric glow, dramatic, VFX concept art, professional visual effects",
        "negative": "low quality, blurry, text, watermark, amateur, simple",
        "model": "dreamshaper_xl_turbo",
    },
    "M_typography": {
        "artifact_class": "typography",
        "style": "editorial",
        "representation": "vector",
        "brief": "Experimental typography poster: the word RESONANCE deconstructed into geometric fragments that vibrate and echo across the composition, kinetic energy captured in static form, high contrast black white and electric accent",
        "dimensions": "html_typo",
        "model": "code_native",
    },
    "N_hybrid_masterpiece": {
        "artifact_class": "illustration",
        "style": "luxury",
        "representation": "hybrid",
        "brief": "Hybrid masterpiece: a luminous deep-sea creature emerging from dark water, rendered through WebGL shader for the creature body (bioluminescent material), SVG tentacle details, generative atmospheric background, HTML typography overlay",
        "dimensions": "html_hybrid",
        "model": "hybrid",
    },
    "O_multi_asset_world": {
        "artifact_class": "brand_system",
        "style": "sci_fi",
        "representation": "hybrid",
        "brief": "Multi-asset world family for a sci-fi game called VOID WANDERER: one character portrait, one environment scene, one prop/weapon, one UI element, one promotional poster — all sharing the same visual identity",
        "dimensions": "multi",
        "model": "hybrid",
    },
}

# ============================================================
# COMFYUI API RUNNER
# ============================================================

def check_comfyui():
    try:
        r = urllib.request.urlopen(f"{COMFYUI_URL}/system_stats", timeout=3)
        return json.loads(r.read())
    except:
        return None

def queue_workflow(workflow, timeout=120):
    """Submit workflow to ComfyUI and return output images."""
    data = json.dumps({"prompt": workflow}).encode()
    req = urllib.request.Request(
        f"{COMFYUI_URL}/prompt",
        data=data,
        headers={"Content-Type": "application/json"}
    )
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        result = json.loads(resp.read())
        prompt_id = result.get("prompt_id")
        if not prompt_id:
            return None, "No prompt_id returned"

        # Poll for completion
        start = time.time()
        while time.time() - start < timeout:
            try:
                hist = urllib.request.urlopen(f"{COMFYUI_URL}/history/{prompt_id}", timeout=5)
                history = json.loads(hist.read())
                if prompt_id in history:
                    outputs = history[prompt_id].get("outputs", {})
                    images = []
                    for node_out in outputs.values():
                        if "images" in node_out:
                            for img in node_out["images"]:
                                images.append({
                                    "filename": img["filename"],
                                    "subfolder": img.get("subfolder", ""),
                                    "type": img.get("type", "output")
                                })
                    return images, None
            except:
                pass
            time.sleep(2)
        return None, f"Timeout after {timeout}s"
    except Exception as e:
        return None, str(e)

def download_image(filename, subfolder="", save_path=None):
    """Download generated image from ComfyUI."""
    url = f"{COMFYUI_URL}/view?filename={filename}&subfolder={subfolder}&type=output"
    try:
        data = urllib.request.urlopen(url, timeout=15).read()
        if save_path:
            with open(save_path, "wb") as f:
                f.write(data)
            return save_path
        return data
    except Exception as e:
        return None

# ============================================================
# DREAMSHAPER 8 WORKFLOW (SD1.5)
# ============================================================

def make_ds8_workflow(positive, negative, w=768, h=768, steps=25, cfg=7.0, seed=None):
    if seed is None:
        seed = int(time.time() * 1000) % (2**32)
    return {
        "3": {
            "class_type": "KSampler",
            "inputs": {
                "model": ["4", 0],
                "positive": ["6", 0],
                "negative": ["7", 0],
                "latent_image": ["5", 0],
                "seed": seed,
                "steps": steps,
                "cfg": cfg,
                "sampler_name": "euler_ancestral",
                "scheduler": "normal",
                "denoise": 1.0
            }
        },
        "4": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": "dreamshaper_8.safetensors"}
        },
        "5": {
            "class_type": "EmptyLatentImage",
            "inputs": {"width": w, "height": h, "batch_size": 1}
        },
        "6": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": positive, "clip": ["4", 1]}
        },
        "7": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": negative, "clip": ["4", 1]}
        },
        "8": {
            "class_type": "VAEDecode",
            "inputs": {"samples": ["3", 0], "vae": ["4", 2]}
        },
        "9": {
            "class_type": "SaveImage",
            "inputs": {"images": ["8", 0], "filename_prefix": "atlas"}
        }
    }

# ============================================================
# DREAMSHAPER XL WORKFLOW (SDXL)
# ============================================================

def make_dsxl_workflow(positive, negative, w=1024, h=1024, steps=15, cfg=2.0, seed=None):
    if seed is None:
        seed = int(time.time() * 1000) % (2**32)
    return {
        "3": {
            "class_type": "KSampler",
            "inputs": {
                "model": ["4", 0],
                "positive": ["6", 0],
                "negative": ["7", 0],
                "latent_image": ["5", 0],
                "seed": seed,
                "steps": steps,
                "cfg": cfg,
                "sampler_name": "euler",
                "scheduler": "sgm_uniform",
                "denoise": 1.0
            }
        },
        "4": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": "dreamshaper_xl_turbo_v21.safetensors"}
        },
        "5": {
            "class_type": "EmptyLatentImage",
            "inputs": {"width": w, "height": h, "batch_size": 1}
        },
        "6": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": positive, "clip": ["4", 1]}
        },
        "7": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": negative, "clip": ["4", 1]}
        },
        "8": {
            "class_type": "VAEDecode",
            "inputs": {"samples": ["3", 0], "vae": ["4", 2]}
        },
        "9": {
            "class_type": "SaveImage",
            "inputs": {"images": ["8", 0], "filename_prefix": "atlas"}
        }
    }

# ============================================================
# IP-ADAPTER WORKFLOW (reference-conditioned)
# ============================================================

def make_ipadapter_workflow(positive, negative, reference_image_path, w=768, h=768, seed=None):
    if seed is None:
        seed = int(time.time() * 1000) % (2**32)
    # We need the reference in ComfyUI/input
    ref_name = os.path.basename(reference_image_path)
    return {
        "1": {
            "class_type": "LoadImage",
            "inputs": {"image": ref_name}
        },
        "4": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": "dreamshaper_8.safetensors"}
        },
        "10": {
            "class_type": "IPAdapterModelLoader",
            "inputs": {"ipadapter_file": "ip-adapter-plus_sd15.safetensors"}
        },
        "11": {
            "class_type": "CLIPVisionLoader",
            "inputs": {"clip_name": "model.safetensors"}
        },
        "12": {
            "class_type": "IPAdapterApply",
            "inputs": {
                "ipadapter": ["10", 0],
                "clip_vision": ["11", 0],
                "image": ["1", 0],
                "model": ["4", 0],
                "weight": 0.7,
                "noise": 0.0,
                "weight_type": "original"
            }
        },
        "5": {
            "class_type": "EmptyLatentImage",
            "inputs": {"width": w, "height": h, "batch_size": 1}
        },
        "6": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": positive, "clip": ["4", 1]}
        },
        "7": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": negative, "clip": ["4", 1]}
        },
        "3": {
            "class_type": "KSampler",
            "inputs": {
                "model": ["12", 0],
                "positive": ["6", 0],
                "negative": ["7", 0],
                "latent_image": ["5", 0],
                "seed": seed,
                "steps": 25,
                "cfg": 7.0,
                "sampler_name": "euler_ancestral",
                "scheduler": "normal",
                "denoise": 1.0
            }
        },
        "8": {
            "class_type": "VAEDecode",
            "inputs": {"samples": ["3", 0], "vae": ["4", 2]}
        },
        "9": {
            "class_type": "SaveImage",
            "inputs": {"images": ["8", 0], "filename_prefix": "atlas_ipa"}
        }
    }

# ============================================================
# UPSCALE WORKFLOW
# ============================================================

def make_upscale_workflow(input_filename):
    return {
        "1": {
            "class_type": "LoadImage",
            "inputs": {"image": input_filename}
        },
        "2": {
            "class_type": "UpscaleModelLoader",
            "inputs": {"model_name": "RealESRGAN_x4plus.pth"}
        },
        "3": {
            "class_type": "ImageUpscaleWithModel",
            "inputs": {"upscale_model": ["2", 0], "image": ["1", 0]}
        },
        "4": {
            "class_type": "SaveImage",
            "inputs": {"images": ["3", 0], "filename_prefix": "atlas_up"}
        }
    }

# ============================================================
# BENCHMARK EXECUTOR
# ============================================================

def run_benchmark(key, brief_data, output_dir):
    """Run a single benchmark and save result."""
    model = brief_data.get("model", "dreamshaper_8")
    dims = brief_data.get("dimensions", "768x768")

    # Parse dimensions
    if dims == "html_shader" or dims == "html_motion" or dims == "html_typo" or dims == "html_hybrid" or dims == "multi":
        return {"key": key, "status": "code_native", "note": "Handled by code-native engine"}

    w, h = [int(x) for x in dims.split("x")]

    # Select workflow
    if "xl" in model:
        workflow = make_dsxl_workflow(
            brief_data["positive"], brief_data.get("negative", ""),
            w=w, h=h, steps=15, cfg=2.0
        )
    else:
        workflow = make_ds8_workflow(
            brief_data["positive"], brief_data.get("negative", ""),
            w=w, h=h, steps=25, cfg=7.0
        )

    # Queue and wait
    images, error = queue_workflow(workflow, timeout=120)
    if error:
        return {"key": key, "status": "FAILED", "error": error}

    # Download
    results = []
    for i, img in enumerate(images):
        save_path = str(output_dir / f"{key}_{i:02d}.png")
        downloaded = download_image(img["filename"], img.get("subfolder", ""), save_path)
        if downloaded:
            sz = os.path.getsize(save_path)
            results.append({"path": save_path, "size_bytes": sz})

    return {"key": key, "status": "OK", "results": results}

# ============================================================
# FIDELITY CLASSIFIER
# ============================================================

@dataclass
class CategoryResult:
    category: str
    artifact_class: str
    style: str
    representation: str
    pipeline: str
    confidence: str
    quality_score: float  # 0-10
    sample_count: int = 1
    strengths: list = field(default_factory=list)
    weaknesses: list = field(default_factory=list)
    failure_modes: list = field(default_factory=list)
    recovery_strategies: list = field(default_factory=list)
    commercial_state: str = "EXPERIMENTAL"
    last_tested: str = ""
    evidence: list = field(default_factory=list)

    def to_dict(self):
        return asdict(self)

# ============================================================
# CREATIVE FRONTIER MAP GENERATOR
# ============================================================

def generate_frontier_map(results):
    """Classify the full creative frontier from benchmark results."""
    frontier = {
        "EXCEPTIONAL": [],
        "STRONG": [],
        "PRODUCTION_CAPABLE": [],
        "GUARDED": [],
        "EXPERIMENTAL": [],
        "WEAK": [],
        "UNPROVEN": [],
    }

    for r in results:
        cr = r if isinstance(r, CategoryResult) else CategoryResult(**r) if isinstance(r, dict) else None
        if cr:
            level = cr.confidence
            if level in frontier:
                frontier[level].append({
                    "category": cr.category,
                    "artifact_class": cr.artifact_class,
                    "style": cr.style,
                    "pipeline": cr.pipeline,
                    "quality": cr.quality_score,
                    "commercial": cr.commercial_state,
                })

    return frontier

# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("11VatedTech Creative Intelligence Atlas")
    print("=" * 60)

    # Check ComfyUI
    stats = check_comfyui()
    if stats:
        print(f"ComfyUI: RUNNING")
        dev = stats.get("devices", [{}])[0]
        print(f"VRAM: {dev.get('vram_total', 0) // (1024**3)} GB")
    else:
        print("ComfyUI: NOT RUNNING — cannot run generative benchmarks")
        exit(1)

    # Run generative benchmarks
    gen_benchmarks = {k: v for k, v in BENCHMARK_BRIEFS.items()
                      if v.get("model", "") in ("dreamshaper_8", "dreamshaper_xl_turbo")}

    print(f"\nRunning {len(gen_benchmarks)} generative benchmarks...")
    all_results = []

    for key, brief in gen_benchmarks.items():
        print(f"  [{key}] ...", end=" ", flush=True)
        result = run_benchmark(key, brief, ARTIFACTS)
        all_results.append(result)
        status = result.get("status", "UNKNOWN")
        print(status)
        if status == "OK":
            for r in result.get("results", []):
                sz = r.get("size_bytes", 0) // 1024
                print(f"    -> {r['path']} ({sz}KB)")

    # Save raw results
    results_path = ARTIFACTS / "benchmark_raw.json"
    with open(results_path, "w") as f:
        json.dump(all_results, f, indent=2)

    # Code-native benchmarks are handled by code_native_engine
    code_native_keys = [k for k, v in BENCHMARK_BRIEFS.items()
                        if v.get("model") in ("code_native", "hybrid")]
    print(f"\n{len(code_native_keys)} code-native/hybrid benchmarks (handled by code_native_engine)")
    for k in code_native_keys:
        all_results.append({"key": k, "status": "code_native"})

    print(f"\nRaw results saved to {results_path}")
    print(f"Total benchmarks: {len(all_results)}")
    print(f"Generative results: {len([r for r in all_results if r.get('status') == 'OK'])}")
    print(f"Code-native: {len([r for r in all_results if r.get('status') == 'code_native'])}")
    print(f"Failed: {len([r for r in all_results if r.get('status') == 'FAILED'])}")

    print("\nAtlas engine ready. Run benchmarks or inspect results.")
