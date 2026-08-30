"""Test ComfyUI headless API execution."""
import os, sys, json, time, subprocess, urllib.request, urllib.error, signal

COMFYUI_DIR = os.path.expanduser("~/ComfyUI")
COMFYUI_PY = os.path.join(COMFYUI_DIR, "main.py")
PORT = 8188

def start_comfyui():
    """Start ComfyUI in headless mode."""
    print("Starting ComfyUI...")
    proc = subprocess.Popen(
        [sys.executable, COMFYUI_PY, "--listen", "127.0.0.1", "--port", str(PORT), "--dont-print-server"],
        cwd=COMFYUI_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    # Wait for server to be ready
    for i in range(60):
        time.sleep(2)
        try:
            resp = urllib.request.urlopen(f"http://127.0.0.1:{PORT}/system_stats", timeout=3)
            if resp.status == 200:
                data = json.loads(resp.read().decode())
                print(f"ComfyUI ready! System: {json.dumps(data.get('system', {}), indent=2)}")
                return proc
        except:
            pass
        # Check if process died
        if proc.poll() is not None:
            out = proc.stderr.read().decode(errors='replace')
            print(f"ComfyUI crashed: {out[-500:]}")
            return None
    print("ComfyUI failed to start within 120s")
    proc.kill()
    return None

def queue_prompt(workflow):
    """Submit a workflow to ComfyUI and return prompt_id."""
    data = json.dumps({"prompt": workflow}).encode()
    req = urllib.request.Request(
        f"http://127.0.0.1:{PORT}/prompt",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    resp = urllib.request.urlopen(req, timeout=10)
    result = json.loads(resp.read().decode())
    return result.get("prompt_id")

def wait_result(prompt_id, timeout=120):
    """Wait for a prompt to complete and return output info."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            resp = urllib.request.urlopen(f"http://127.0.0.1:{PORT}/history/{prompt_id}", timeout=5)
            history = json.loads(resp.read().decode())
            if prompt_id in history:
                outputs = history[prompt_id].get("outputs", {})
                return outputs
        except:
            pass
        time.sleep(1)
    return None

def get_image(filename, subfolder="", folder_type="output"):
    """Download a generated image."""
    url = f"http://127.0.0.1:{PORT}/view?filename={filename}&subfolder={subfolder}&type={folder_type}"
    resp = urllib.request.urlopen(url, timeout=10)
    return resp.read()

# Minimal SD1.5 txt2img workflow for DreamShaper 8
DREAMSHAPER_8_WORKFLOW = {
    "3": {
        "class_type": "KSampler",
        "inputs": {
            "seed": 42,
            "steps": 20,
            "cfg": 7.0,
            "sampler_name": "euler_ancestral",
            "scheduler": "normal",
            "denoise": 1.0,
            "model": ["4", 0],
            "positive": ["6", 0],
            "negative": ["7", 0],
            "latent_image": ["5", 0]
        }
    },
    "4": {
        "class_type": "CheckpointLoaderSimple",
        "inputs": {
            "ckpt_name": "dreamshaper_8.safetensors"
        }
    },
    "5": {
        "class_type": "EmptyLatentImage",
        "inputs": {
            "width": 512,
            "height": 768,
            "batch_size": 1
        }
    },
    "6": {
        "class_type": "CLIPTextEncode",
        "inputs": {
            "text": "cinematic portrait of a mysterious performer on a dark stage, dramatic lighting, professional photography, shallow depth of field, rich colors, 8k",
            "clip": ["4", 1]
        }
    },
    "7": {
        "class_type": "CLIPTextEncode",
        "inputs": {
            "text": "blurry, low quality, deformed, ugly, watermark, text, logo",
            "clip": ["4", 1]
        }
    },
    "8": {
        "class_type": "VAEDecode",
        "inputs": {
            "samples": ["3", 0],
            "vae": ["4", 2]
        }
    },
    "9": {
        "class_type": "SaveImage",
        "inputs": {
            "filename_prefix": "vpi_test_dreamshaper8",
            "images": ["8", 0]
        }
    }
}

# SDXL workflow for DreamShaper XL
DREAMSHAPER_XL_WORKFLOW = {
    "3": {
        "class_type": "KSampler",
        "inputs": {
            "seed": 42,
            "steps": 25,
            "cfg": 7.0,
            "sampler_name": "euler_ancestral",
            "scheduler": "normal",
            "denoise": 1.0,
            "model": ["4", 0],
            "positive": ["6", 0],
            "negative": ["7", 0],
            "latent_image": ["5", 0]
        }
    },
    "4": {
        "class_type": "CheckpointLoaderSimple",
        "inputs": {
            "ckpt_name": "dreamshaper_xl_turbo_v21.safetensors"
        }
    },
    "5": {
        "class_type": "EmptyLatentImage",
        "inputs": {
            "width": 1024,
            "height": 1024,
            "batch_size": 1
        }
    },
    "6": {
        "class_type": "CLIPTextEncode",
        "inputs": {
            "text": "cinematic portrait of a mysterious performer on a dark stage, dramatic lighting, professional photography, shallow depth of field, rich colors",
            "clip": ["4", 1]
        }
    },
    "7": {
        "class_type": "CLIPTextEncode",
        "inputs": {
            "text": "blurry, low quality, deformed, ugly, watermark, text, logo",
            "clip": ["4", 1]
        }
    },
    "8": {
        "class_type": "VAEDecode",
        "inputs": {
            "samples": ["3", 0],
            "vae": ["4", 2]
        }
    },
    "9": {
        "class_type": "SaveImage",
        "inputs": {
            "filename_prefix": "vpi_test_dreamshaper_xl",
            "images": ["8", 0]
        }
    }
}

if __name__ == "__main__":
    proc = start_comfyui()
    if not proc:
        print("FAILED: Could not start ComfyUI")
        sys.exit(1)

    try:
        # Test DreamShaper 8
        print("\n=== Test: DreamShaper 8 (SD1.5) ===")
        pid = queue_prompt(DREAMSHAPER_8_WORKFLOW)
        if pid:
            print(f"  Queued: {pid}")
            outputs = wait_result(pid, timeout=120)
            if outputs:
                for node_id, node_out in outputs.items():
                    if "images" in node_out:
                        for img in node_out["images"]:
                            data = get_image(img["filename"], img.get("subfolder", ""))
                            out_path = os.path.join("artifacts", "visual", f"ds8_test.png")
                            os.makedirs(os.path.dirname(out_path), exist_ok=True)
                            with open(out_path, "wb") as f:
                                f.write(data)
                            print(f"  Saved: {out_path} ({len(data)//1024}KB)")
            else:
                print("  TIMEOUT: Generation did not complete in 120s")
        else:
            print("  FAILED: Could not queue prompt")

        # Test DreamShaper XL
        print("\n=== Test: DreamShaper XL Turbo ===")
        pid = queue_prompt(DREAMSHAPER_XL_WORKFLOW)
        if pid:
            print(f"  Queued: {pid}")
            outputs = wait_result(pid, timeout=180)
            if outputs:
                for node_id, node_out in outputs.items():
                    if "images" in node_out:
                        for img in node_out["images"]:
                            data = get_image(img["filename"], img.get("subfolder", ""))
                            out_path = os.path.join("artifacts", "visual", f"dsxl_test.png")
                            with open(out_path, "wb") as f:
                                f.write(data)
                            print(f"  Saved: {out_path} ({len(data)//1024}KB)")
            else:
                print("  TIMEOUT: XL generation did not complete in 180s")

        print("\n=== All tests complete ===")

    finally:
        print("Shutting down ComfyUI...")
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except:
            proc.kill()
        print("Done.")
