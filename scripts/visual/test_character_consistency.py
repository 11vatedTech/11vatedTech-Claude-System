#!/usr/bin/env python3
"""
Character Consistency Test — same reference through IP-Adapter.
Test: front, 3/4, side, close-up, different pose, different lighting.
"""

import json
import os
import time
import urllib.request
from pathlib import Path

COMFYUI_URL = "http://127.0.0.1:8188"
PROJECT_ROOT = Path(__file__).parent.parent.parent
ARTIFACTS = PROJECT_ROOT / "artifacts" / "visual" / "calibration"
COMFYUI_INPUT = Path(os.path.expanduser("~/ComfyUI/input"))
COMFYUI_OUTPUT = Path(os.path.expanduser("~/ComfyUI/output"))

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
            return None, "No prompt_id"
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
                                })
                    return images, None
            except:
                pass
            time.sleep(2)
        return None, f"Timeout {timeout}s"
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

def make_character_sheet(positive, negative, seed=None):
    """Generate a character concept first to use as reference."""
    if seed is None:
        seed = int(time.time() * 1000) % (2**32)
    return {
        "3": {"class_type": "KSampler", "inputs": {"model": ["4", 0], "positive": ["6", 0], "negative": ["7", 0], "latent_image": ["5", 0], "seed": seed, "steps": 30, "cfg": 7.0, "sampler_name": "euler_ancestral", "scheduler": "normal", "denoise": 1.0}},
        "4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "dreamshaper_8.safetensors"}},
        "5": {"class_type": "EmptyLatentImage", "inputs": {"width": 768, "height": 1024, "batch_size": 1}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"text": positive, "clip": ["4", 1]}},
        "7": {"class_type": "CLIPTextEncode", "inputs": {"text": negative, "clip": ["4", 1]}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["4", 2]}},
        "9": {"class_type": "SaveImage", "inputs": {"images": ["8", 0], "filename_prefix": "char_ref"}},
    }

def make_ipadapter_variant(ref_filename, positive, negative, weight=0.7, seed=None):
    """Generate a variant using IP-Adapter with a reference image."""
    if seed is None:
        seed = int(time.time() * 1000) % (2**32)
    return {
        "1": {"class_type": "LoadImage", "inputs": {"image": ref_filename}},
        "4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "dreamshaper_8.safetensors"}},
        "10": {"class_type": "IPAdapterUnifiedLoader", "inputs": {"model": ["4", 0], "preset": "PLUS (high strength)"}},
        "12": {"class_type": "IPAdapter", "inputs": {
            "model": ["10", 0], "ipadapter": ["10", 1], "image": ["1", 0],
            "weight": weight, "start_at": 0.0, "end_at": 1.0, "weight_type": "standard"
        }},
        "3": {"class_type": "KSampler", "inputs": {"model": ["12", 0], "positive": ["6", 0], "negative": ["7", 0], "latent_image": ["5", 0], "seed": seed, "steps": 25, "cfg": 7.0, "sampler_name": "euler_ancestral", "scheduler": "normal", "denoise": 1.0}},
        "5": {"class_type": "EmptyLatentImage", "inputs": {"width": 768, "height": 1024, "batch_size": 1}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"text": positive, "clip": ["4", 1]}},
        "7": {"class_type": "CLIPTextEncode", "inputs": {"text": negative, "clip": ["4", 1]}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["4", 2]}},
        "9": {"class_type": "SaveImage", "inputs": {"images": ["8", 0], "filename_prefix": "char_ipa"}},
    }

def save_comfyui_output(images, prefix):
    """Save from ComfyUI output dir to calibration artifacts."""
    for img in images:
        src = COMFYUI_OUTPUT / img["filename"]
        if src.exists():
            import shutil
            dst = ARTIFACTS / f"{prefix}.png"
            shutil.copy2(str(src), str(dst))
            return str(dst)
    return None

if __name__ == "__main__":
    print("=" * 60)
    print("CHARACTER CONSISTENCY TEST")
    print("=" * 60)

    if not check_comfyui():
        print("ComfyUI NOT RUNNING")
        exit(1)

    # Step 1: Generate a reference character
    print("\n[1] Generating reference character...")
    ref_pos = "concept art, a young female elven ranger with silver-white hair, pointed ears, emerald green cloak, leather armor with leaf motifs, determined expression, standing in dappled forest light, full body, professional character design, detailed, sharp"
    ref_neg = "low quality, blurry, deformed, ugly, extra fingers, text, watermark, generic"
    
    workflow = make_character_sheet(ref_pos, ref_neg, seed=42)
    images, err = queue_workflow(workflow, timeout=120)
    if err:
        print(f"FAILED: {err}")
        exit(1)
    
    # Copy reference to ComfyUI/input and calibration/
    ref_name = None
    for img in images:
        src = COMFYUI_OUTPUT / img["filename"]
        if src.exists():
            import shutil
            # Save to calibration
            dst_cal = ARTIFACTS / "char_consistency_ref.png"
            shutil.copy2(str(src), str(dst_cal))
            # Copy to ComfyUI/input for IP-Adapter
            dst_input = COMFYUI_INPUT / "char_ref.png"
            shutil.copy2(str(src), str(dst_input))
            ref_name = "char_ref.png"
            print(f"  Reference saved: {dst_cal} ({os.path.getsize(str(dst_cal))//1024}KB)")
            break
    
    if not ref_name:
        print("  No reference image produced")
        exit(1)

    # Step 2: Generate variants using IP-Adapter
    variants = [
        ("char_ipa_front", "front portrait of the same elven ranger, looking directly at camera, soft forest lighting, same silver hair, same emerald cloak, same leaf armor, professional portrait, detailed face", 0.6),
        ("char_ipa_side", "profile view of the same elven ranger from the side, looking to the right, same silver-white hair, same green cloak, same leather armor with leaf motifs, dramatic side lighting", 0.6),
        ("char_ipa_action", "the same elven ranger drawing a bow, action pose, dynamic stance, same silver hair flowing, same green cloak billowing, same leaf armor, forest background, dynamic lighting", 0.5),
        ("char_ipa_closeup", "extreme close-up of the same elven ranger's face, silver-white hair, pointed ears, emerald eyes, determined expression, soft bokeh forest background, portrait lighting", 0.65),
        ("char_ipa_night", "the same elven ranger sitting by a campfire at night, warm firelight on face, same silver hair glowing in firelight, same green cloak, same leather armor, nighttime forest, atmospheric", 0.55),
    ]

    print(f"\n[2] Generating {len(variants)} IP-Adapter variants...")
    results = {"reference": {"path": str(ARTIFACTS / "char_consistency_ref.png"), "seed": 42}}
    
    for name, prompt, weight in variants:
        print(f"  [{name}]...", end=" ", flush=True)
        workflow = make_ipadapter_variant(ref_name, prompt, ref_neg, weight=weight)
        images, err = queue_workflow(workflow, timeout=120)
        if err:
            print(f"FAILED: {err}")
            results[name] = {"status": "FAILED", "error": err}
            continue
        
        path = save_comfyui_output(images, name)
        if path:
            sz = os.path.getsize(path) // 1024
            print(f"OK ({sz}KB)")
            results[name] = {"status": "OK", "path": path, "size_kb": sz}
        else:
            print("NO OUTPUT")

    # Step 3: Generate WITHOUT IP-Adapter for comparison
    print(f"\n[3] Generating 2 non-IP-Adapter variants for comparison...")
    no_ipa_variants = [
        ("char_noipa_a", "concept art, a young female elven ranger with silver-white hair, pointed ears, emerald green cloak, leather armor with leaf motifs, standing in dappled forest light, full body, professional"),
        ("char_noipa_b", "concept art, a young female elven ranger with silver-white hair, pointed ears, emerald green cloak, leather armor, forest background, different pose, professional character design"),
    ]
    for name, prompt in no_ipa_variants:
        print(f"  [{name}]...", end=" ", flush=True)
        workflow = make_character_sheet(prompt, ref_neg, seed=int(time.time()*1000)%(2**32))
        images, err = queue_workflow(workflow, timeout=120)
        if err:
            print(f"FAILED: {err}")
            continue
        path = save_comfyui_output(images, name)
        if path:
            sz = os.path.getsize(path) // 1024
            print(f"OK ({sz}KB)")
            results[name] = {"status": "OK", "path": path, "size_kb": sz}
        else:
            print("NO OUTPUT")

    # Save
    out_path = ARTIFACTS / "character_consistency_results.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)

    ok = sum(1 for v in results.values() if isinstance(v, dict) and v.get("status") == "OK")
    fail = sum(1 for v in results.values() if isinstance(v, dict) and v.get("status") == "FAILED")
    print(f"\n{'='*60}")
    print(f"CHARACTER CONSISTENCY: {ok} OK, {fail} FAILED")
    print(f"Results: {out_path}")
