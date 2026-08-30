#!/usr/bin/env python3
"""
Expanded Calibration Benchmarks — N=3 variants per critical category.
Each variant uses a DIFFERENT brief to test breadth, not just repeatability.
"""

import json
import os
import time
import urllib.request
from pathlib import Path

COMFYUI_URL = "http://127.0.0.1:8188"
PROJECT_ROOT = Path(__file__).parent.parent.parent
ARTIFACTS = PROJECT_ROOT / "artifacts" / "visual" / "calibration"
ARTIFACTS.mkdir(parents=True, exist_ok=True)

# ============================================================
# EXPANDED BRIEFS — N=3 per category, different briefs each
# ============================================================

EXPANDED_BRIEFS = {
    # === CHARACTER DESIGN (3 variants) ===
    "char_concept_a": {
        "model": "ds8", "w": 768, "h": 1024,
        "positive": "concept art, a weathered female warrior with cybernetic arm, standing on rain-slicked rooftop at night, dramatic rim lighting, detailed armor, strong silhouette, professional character design, anime-influenced style",
        "negative": "low quality, blurry, deformed, ugly, extra fingers, bad anatomy, text, watermark",
    },
    "char_concept_b": {
        "model": "ds8", "w": 768, "h": 1024,
        "positive": "fantasy creature concept art, a luminous jellyfish-like forest spirit with translucent bell and trailing bioluminescent tendrils, ancient woodland, misty atmosphere, cel-shaded style, distinctive silhouette",
        "negative": "low quality, blurry, deformed, generic blob, text, watermark, photorealistic",
    },
    "char_concept_c": {
        "model": "ds8", "w": 768, "h": 1024,
        "positive": "character design sheet, a stylized robot mascot with expressive optical sensors, rounded friendly shapes, warm orange and white color scheme, multiple angles, clean lines, Pixar-inspired appeal",
        "negative": "low quality, blurry, menacing, complex, dark, text, watermark",
    },

    # === HANDS / ANATOMY (3 difficulty levels) ===
    "anatomy_easy": {
        "model": "ds8", "w": 768, "h": 768,
        "positive": "digital painting, single open hand with fingers spread, dramatic side lighting, visible anatomy detail, clean background, study quality, professional art",
        "negative": "low quality, blurry, extra fingers, fused fingers, bad anatomy, deformed, text",
    },
    "anatomy_medium": {
        "model": "ds8", "w": 768, "h": 768,
        "positive": "digital painting, hands carefully cupping a glowing crystal, soft studio lighting, detailed finger joints and fingernails, painterly style, professional anatomy study",
        "negative": "low quality, blurry, extra fingers, fused fingers, bad anatomy, missing fingers, deformed hands",
    },
    "anatomy_hard": {
        "model": "ds8", "w": 768, "h": 768,
        "positive": "concept art, two hands typing on holographic keyboard, one hand holding a stylus, complex interaction, multiple fingers visible, studio lighting, detailed anatomy, professional quality",
        "negative": "low quality, blurry, extra fingers, fused, deformed, bad anatomy, missing digits, text",
    },

    # === ENVIRONMENT (3 variants) ===
    "env_natural": {
        "model": "dsxl", "w": 1024, "h": 768,
        "positive": "environment concept art, a vast bioluminescent mushroom forest at twilight, giant fungi casting blue-green light, misty atmosphere, ground-level perspective, epic scale, cinematic depth",
        "negative": "low quality, blurry, flat, small, text, watermark, generic",
    },
    "env_architectural": {
        "model": "dsxl", "w": 1024, "h": 768,
        "positive": "environment concept art, ancient Egyptian temple interior with massive columns, sunlight streaming through ceiling cracks, dust particles, golden hieroglyphs, architectural grandeur, cinematic composition",
        "negative": "low quality, blurry, flat, text, watermark, generic, small scale",
    },
    "env_fantasy": {
        "model": "dsxl", "w": 1024, "h": 768,
        "positive": "environment concept art, a floating sky city with waterfalls cascading into clouds, ornate bridges connecting towers, warm sunset backlight, atmospheric perspective, whimsical architecture, Studio Ghibli-inspired",
        "negative": "low quality, blurry, dark, text, watermark, generic",
    },

    # === PRODUCT (3 variants) ===
    "product_tech": {
        "model": "dsxl", "w": 1024, "h": 1024,
        "positive": "premium product photography, luxury smartwatch on dark marble surface, dramatic rim lighting, brushed titanium and sapphire glass, floating slightly, hero shot, commercial quality",
        "negative": "low quality, blurry, text, watermark, amateur, stock photo",
    },
    "product_organic": {
        "model": "dsxl", "w": 1024, "h": 1024,
        "positive": "product photography, artisanal perfume bottle with golden liquid, dried flowers arrangement, warm natural light from window, shallow depth of field, editorial luxury aesthetic, high-end commercial",
        "negative": "low quality, blurry, text, watermark, generic, cheap looking",
    },
    "product_food": {
        "model": "dsxl", "w": 1024, "h": 1024,
        "positive": "food photography, elegant dark chocolate dessert on slate plate, raspberry sauce, gold leaf garnish, dramatic overhead lighting, Michelin restaurant quality, professional food styling",
        "negative": "low quality, blurry, text, watermark, amateur, unappetizing",
    },

    # === VFX (3 variants) ===
    "vfx_energy": {
        "model": "dsxl", "w": 768, "h": 1024,
        "positive": "VFX concept art, crackling electricity between two Tesla coils, blue-white arcs, ionized air glow, dark lab environment, scientific drama, professional visual effects",
        "negative": "low quality, blurry, simple, text, watermark, cartoon",
    },
    "vfx_organic": {
        "model": "dsxl", "w": 768, "h": 1024,
        "positive": "VFX concept art, a magical transformation spell, golden particles coalescing into a phoenix form, warm embers, ethereal light trails, fantasy VFX, professional quality",
        "negative": "low quality, blurry, text, watermark, generic magic, boring",
    },
    "vfx_destruction": {
        "model": "dsxl", "w": 768, "h": 1024,
        "positive": "VFX concept art, massive stone pillar cracking and crumbling, dust and debris, dramatic lighting from cracks, dynamic composition, destruction physics, cinematic VFX quality",
        "negative": "low quality, blurry, text, watermark, simple, low effort",
    },

    # === SHADER RANGE (via code-native HTML) ===
    # These are handled separately in the capture script
}

# ============================================================
# COMFYUI API
# ============================================================

def check_comfyui():
    try:
        r = urllib.request.urlopen(f"{COMFYUI_URL}/system_stats", timeout=3)
        return json.loads(r.read())
    except:
        return None

def queue_workflow(workflow, timeout=120):
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
    url = f"{COMFYUI_URL}/view?filename={filename}&subfolder={subfolder}&type=output"
    try:
        data = urllib.request.urlopen(url, timeout=15).read()
        if save_path:
            with open(save_path, "wb") as f:
                f.write(data)
            return save_path
        return data
    except:
        return None

# ============================================================
# WORKFLOWS
# ============================================================

def make_ds8_workflow(positive, negative, w=768, h=768, steps=25, cfg=7.0, seed=None):
    if seed is None:
        seed = int(time.time() * 1000) % (2**32)
    return {
        "3": {"class_type": "KSampler", "inputs": {"model": ["4", 0], "positive": ["6", 0], "negative": ["7", 0], "latent_image": ["5", 0], "seed": seed, "steps": steps, "cfg": cfg, "sampler_name": "euler_ancestral", "scheduler": "normal", "denoise": 1.0}},
        "4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "dreamshaper_8.safetensors"}},
        "5": {"class_type": "EmptyLatentImage", "inputs": {"width": w, "height": h, "batch_size": 1}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"text": positive, "clip": ["4", 1]}},
        "7": {"class_type": "CLIPTextEncode", "inputs": {"text": negative, "clip": ["4", 1]}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["4", 2]}},
        "9": {"class_type": "SaveImage", "inputs": {"images": ["8", 0], "filename_prefix": "cal"}},
    }

def make_dsxl_workflow(positive, negative, w=1024, h=1024, steps=15, cfg=2.0, seed=None):
    if seed is None:
        seed = int(time.time() * 1000) % (2**32)
    return {
        "3": {"class_type": "KSampler", "inputs": {"model": ["4", 0], "positive": ["6", 0], "negative": ["7", 0], "latent_image": ["5", 0], "seed": seed, "steps": steps, "cfg": cfg, "sampler_name": "euler", "scheduler": "sgm_uniform", "denoise": 1.0}},
        "4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "dreamshaper_xl_turbo_v21.safetensors"}},
        "5": {"class_type": "EmptyLatentImage", "inputs": {"width": w, "height": h, "batch_size": 1}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"text": positive, "clip": ["4", 1]}},
        "7": {"class_type": "CLIPTextEncode", "inputs": {"text": negative, "clip": ["4", 1]}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["4", 2]}},
        "9": {"class_type": "SaveImage", "inputs": {"images": ["8", 0], "filename_prefix": "cal"}},
    }

# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("CALIBRATION BENCHMARKS — EXPANDED N=3")
    print("=" * 60)

    stats = check_comfyui()
    if not stats:
        print("ComfyUI NOT RUNNING — cannot run benchmarks")
        exit(1)
    print("ComfyUI: RUNNING")

    results = {}
    total = len(EXPANDED_BRIEFS)
    for i, (key, brief) in enumerate(EXPANDED_BRIEFS.items()):
        print(f"\n[{i+1}/{total}] {key}...", end=" ", flush=True)
        
        if brief["model"] == "ds8":
            workflow = make_ds8_workflow(brief["positive"], brief["negative"], w=brief["w"], h=brief["h"])
        else:
            workflow = make_dsxl_workflow(brief["positive"], brief["negative"], w=brief["w"], h=brief["h"])

        images, error = queue_workflow(workflow, timeout=120)
        if error:
            print(f"FAILED: {error}")
            results[key] = {"status": "FAILED", "error": error}
            continue

        saved = []
        for img in images:
            path = str(ARTIFACTS / f"{key}.png")
            dl = download_image(img["filename"], img.get("subfolder", ""), path)
            if dl:
                sz = os.path.getsize(path) // 1024
                saved.append({"path": path, "size_kb": sz})
        
        results[key] = {
            "status": "OK",
            "model": brief["model"],
            "dimensions": f"{brief['w']}x{brief['h']}",
            "results": saved,
        }
        print(f"OK ({saved[0]['size_kb']}KB)" if saved else "NO OUTPUT")

    # Save results
    out_path = ARTIFACTS / "calibration_results.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)

    ok = sum(1 for r in results.values() if r.get("status") == "OK")
    fail = sum(1 for r in results.values() if r.get("status") == "FAILED")
    print(f"\n{'=' * 60}")
    print(f"DONE: {ok} OK, {fail} FAILED, {total} total")
    print(f"Results: {out_path}")
