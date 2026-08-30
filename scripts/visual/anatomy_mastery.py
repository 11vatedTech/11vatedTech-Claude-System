#!/usr/bin/env python3
"""
Anatomy Mastery — Hand/Anatomy Recovery Chain
===============================================
Test difficulty ladder with multiple recovery strategies.
"""

import json
import os
import time
import urllib.request
import shutil
from pathlib import Path

COMFYUI_URL = "http://127.0.0.1:8188"
PROJECT_ROOT = Path(__file__).parent.parent.parent
CAL = PROJECT_ROOT / "artifacts" / "visual" / "calibration"
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
    req = urllib.request.Request(f"{COMFYUI_URL}/prompt", data=data, headers={"Content-Type": "application/json"})
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
                    status = history[prompt_id].get("status", {})
                    if status.get("status_str") == "error":
                        msgs = status.get("messages", [])
                        for m in msgs:
                            if m[0] == "execution_error":
                                return None, m[1].get("exception_message", "error")
                    outputs = history[prompt_id].get("outputs", {})
                    images = []
                    for node_out in outputs.values():
                        if "images" in node_out:
                            for img in node_out["images"]:
                                images.append({"filename": img["filename"], "subfolder": img.get("subfolder", "")})
                    return images, None
            except:
                pass
            time.sleep(2)
        return None, f"Timeout {timeout}s"
    except Exception as e:
        return None, str(e)

def download_and_save(images, prefix):
    """Save images from ComfyUI output to calibration folder."""
    saved = []
    for img in images:
        url = f"{COMFYUI_URL}/view?filename={img['filename']}&subfolder={img.get('subfolder','')}&type=output"
        try:
            data = urllib.request.urlopen(url, timeout=15).read()
            path = CAL / f"{prefix}.png"
            with open(path, "wb") as f:
                f.write(data)
            saved.append(str(path))
        except:
            pass
    return saved

def make_ds8_workflow(pos, neg, w=768, h=768, steps=30, cfg=7.0, seed=None):
    if seed is None:
        seed = int(time.time() * 1000) % (2**32)
    return {
        "3": {"class_type": "KSampler", "inputs": {"model": ["4", 0], "positive": ["6", 0], "negative": ["7", 0], "latent_image": ["5", 0], "seed": seed, "steps": steps, "cfg": cfg, "sampler_name": "euler_ancestral", "scheduler": "normal", "denoise": 1.0}},
        "4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "dreamshaper_8.safetensors"}},
        "5": {"class_type": "EmptyLatentImage", "inputs": {"width": w, "height": h, "batch_size": 1}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"text": pos, "clip": ["4", 1]}},
        "7": {"class_type": "CLIPTextEncode", "inputs": {"text": neg, "clip": ["4", 1]}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["4", 2]}},
        "9": {"class_type": "SaveImage", "inputs": {"images": ["8", 0], "filename_prefix": "anat"}},
    }

# Difficulty ladder with recovery strategies
TESTS = [
    # Level 1: Single open hand (easiest)
    {
        "name": "hand_open_single",
        "difficulty": 1,
        "description": "Single open hand, fingers spread",
        "strategies": [
            {
                "approach": "direct_generation",
                "prompt": "digital painting, single open human hand with fingers spread wide, dramatic side lighting, clean dark background, anatomical study, professional quality, detailed finger joints, visible knuckles, correct finger count",
                "negative": "low quality, blurry, extra fingers, fused fingers, bad anatomy, deformed, six fingers, text, watermark",
                "weight": 1.0,
            },
            {
                "approach": "stylized_hand",
                "prompt": "stylized illustration of an open hand, clean lines, simplified anatomy, graphic design style, bold outlines, studio lighting, professional illustration",
                "negative": "low quality, blurry, deformed, photorealistic, text",
                "weight": 1.0,
            },
        ],
    },
    # Level 2: Holding an object
    {
        "name": "hand_holding_object",
        "difficulty": 2,
        "description": "Hand gripping a sword hilt",
        "strategies": [
            {
                "approach": "direct_generation",
                "prompt": "concept art, one hand firmly gripping a ornate sword hilt, detailed finger wrapping around handle, correct grip anatomy, dramatic lighting, professional quality, medieval fantasy style",
                "negative": "low quality, blurry, extra fingers, fused, bad anatomy, deformed, text, watermark",
                "weight": 1.0,
            },
            {
                "approach": "partial_occlusion",
                "prompt": "concept art, armored gauntlet gripping a sword hilt, medieval knight hand, armored fingers wrapping handle, dramatic lighting, metal armor, professional quality",
                "negative": "low quality, blurry, deformed, bad anatomy, text",
                "weight": 1.0,
            },
        ],
    },
    # Level 3: Two hands interacting
    {
        "name": "hands_two_interact",
        "difficulty": 3,
        "description": "Two hands cupping a glowing object",
        "strategies": [
            {
                "approach": "direct_generation",
                "prompt": "digital painting, two hands carefully cupping a small glowing orb, fingers interlaced, soft studio lighting, detailed anatomy, translucent glow, professional art",
                "negative": "low quality, blurry, extra fingers, fused, bad anatomy, deformed hands, missing fingers, text",
                "weight": 1.0,
            },
            {
                "approach": "simplified_interaction",
                "prompt": "concept art, two hands holding a crystal ball, palms facing each other, soft glow between hands, painterly style, atmospheric, professional illustration",
                "negative": "low quality, blurry, extra fingers, bad anatomy, deformed, text",
                "weight": 1.0,
            },
        ],
    },
    # Level 4: Hand near face (very hard)
    {
        "name": "hand_near_face",
        "difficulty": 4,
        "description": "Hand touching chin in thought pose",
        "strategies": [
            {
                "approach": "direct_generation",
                "prompt": "portrait, thoughtful person with hand resting on chin, fingers gently touching jawline, contemplative expression, studio lighting, detailed hand anatomy, professional portrait photography quality",
                "negative": "low quality, blurry, extra fingers, fused, bad anatomy, deformed, distorted face, text, watermark",
                "weight": 1.0,
            },
            {
                "approach": "obscured_hand",
                "prompt": "portrait, person in contemplation, hand partially hidden under chin, dramatic Rembrandt lighting, shallow depth of field, professional portrait, soft focus on hand area",
                "negative": "low quality, blurry, deformed, bad anatomy, text",
                "weight": 1.0,
            },
        ],
    },
    # Level 5: Extreme — typing on keyboard (complex multi-finger)
    {
        "name": "hands_typing",
        "difficulty": 5,
        "description": "Both hands typing on keyboard",
        "strategies": [
            {
                "approach": "direct_generation",
                "prompt": "top-down view, two hands typing on a mechanical keyboard, fingers in motion, detailed hand anatomy, warm desk lamp lighting, professional photography, correct finger count on all visible hands",
                "negative": "low quality, blurry, extra fingers, fused, bad anatomy, deformed, extra hands, text, watermark",
                "weight": 1.0,
            },
            {
                "approach": "angle_avoid",
                "prompt": "side view of hands typing on keyboard, shallow depth of field, motion blur on fingers, warm lighting, professional photography, artistic composition",
                "negative": "low quality, blurry, extra fingers, bad anatomy, text",
                "weight": 1.0,
            },
        ],
    },
]

if __name__ == "__main__":
    print("=" * 60)
    print("ANATOMY MASTERY — RECOVERY CHAIN BENCHMARK")
    print("=" * 60)

    if not check_comfyui():
        print("ComfyUI NOT RUNNING")
        exit(1)

    results = {}
    for test in TESTS:
        print(f"\n[Level {test['difficulty']}] {test['name']}: {test['description']}")
        test_results = {"difficulty": test["difficulty"], "description": test["description"], "strategies": []}

        for strategy in test["strategies"]:
            name = f"{test['name']}_{strategy['approach']}"
            print(f"  {strategy['approach']}...", end=" ", flush=True)

            workflow = make_ds8_workflow(strategy["prompt"], strategy["negative"], steps=35, cfg=7.5)
            images, err = queue_workflow(workflow, timeout=120)

            if err:
                print(f"FAILED: {err}")
                test_results["strategies"].append({"name": name, "status": "FAILED", "error": err})
                continue

            saved = download_and_save(images, name)
            if saved:
                sz = os.path.getsize(saved[0]) // 1024
                print(f"OK ({sz}KB)")
                test_results["strategies"].append({"name": name, "status": "OK", "path": saved[0], "size_kb": sz})
            else:
                print("NO OUTPUT")
                test_results["strategies"].append({"name": name, "status": "NO_OUTPUT"})

        results[test["name"]] = test_results

    # Save
    out_path = CAL / "anatomy_mastery_results.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)

    # Summary
    print(f"\n{'='*60}")
    print("ANATOMY RECOVERY CHAIN SUMMARY")
    print("=" * 60)
    for name, data in results.items():
        ok = sum(1 for s in data["strategies"] if s["status"] == "OK")
        total = len(data["strategies"])
        print(f"  Level {data['difficulty']} {name}: {ok}/{total} strategies produced output")

    print(f"\nResults: {out_path}")
