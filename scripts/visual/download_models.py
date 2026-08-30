"""Download models for Visual Production Intelligence."""
import os, sys, json, time
from huggingface_hub import hf_hub_download, snapshot_download

COMFYUI = os.path.expanduser("~/ComfyUI")
CHECKPOINTS = os.path.join(COMFYUI, "models", "checkpoints")
CONTROLNET = os.path.join(COMFYUI, "models", "controlnet")
IPADAPTER = os.path.join(COMFYUI, "models", "ipadapter")
UPSCALE = os.path.join(COMFYUI, "models", "upscale_models")
INPAINT = os.path.join(COMFYUI, "models", "inpaint")
LORA = os.path.join(COMFYUI, "models", "loras")
VAE = os.path.join(COMFYUI, "models", "vae")

# Ensure dirs exist
for d in [CHECKPOINTS, CONTROLNET, IPADAPTER, UPSCALE, INPAINT, LORA, VAE]:
    os.makedirs(d, exist_ok=True)

# Model download plan
downloads = [
    # DreamShaper 8 (SD1.5) - Creative Exploration Specialist
    {
        "id": "ds8",
        "repo": "Lykon/DreamShaper",
        "file": "DreamShaper 8 pruned.safetensors",
        "dest": os.path.join(CHECKPOINTS, "dreamshaper_8_pruned.safetensors"),
        "role": "Creative Exploration Specialist",
        "family": "SD1.5",
    },
    # DreamShaper XL (SDXL)
    {
        "id": "dsxl",
        "repo": "Lykon/DreamShaper XL",
        "file": "DreamShaper XL v2.1 refiner.safetensors",
        "dest": os.path.join(CHECKPOINTS, "dreamshaper_xl_v21.safetensors"),
        "role": "High-quality character/environment generation",
        "family": "SDXL",
    },
    # SD3.5 Medium
    {
        "id": "sd35m",
        "repo": "stabilityai/stable-diffusion-3.5-medium",
        "file": "sd3.5_medium.safetensors",
        "dest": os.path.join(CHECKPOINTS, "sd3.5_medium.safetensors"),
        "role": "Production illustration / precision generation",
        "family": "SD3.5",
    },
    # FLUX.1 Schnell (attempt - may be too large)
    {
        "id": "flux_schnell",
        "repo": "black-forest-labs/FLUX.1-schnell",
        "file": "flux1-schnell.safetensors",
        "dest": os.path.join(CHECKPOINTS, "flux1_schnell.safetensors"),
        "role": "Fast general generation / prompt adherence",
        "family": "FLUX",
        "optional": True,  # May be too large for 12GB
    },
    # IP-Adapter (SDXL)
    {
        "id": "ip_adapter_sdxl",
        "repo": "h94/IP-Adapter",
        "file": "sdxl_models/ip-adapter-plus_sdxl_vit-h.safetensors",
        "dest": os.path.join(IPADAPTER, "ip-adapter-plus_sdxl_vit-h.safetensors"),
        "role": "Reference conditioning for SDXL",
        "family": "IP-Adapter",
    },
    # IP-Adapter (SD1.5)
    {
        "id": "ip_adapter_sdv15",
        "repo": "h94/IP-Adapter",
        "file": "models/ip-adapter-plus_sd15.safetensors",
        "dest": os.path.join(IPADAPTER, "ip-adapter-plus_sd15.safetensors"),
        "role": "Reference conditioning for SD1.5",
        "family": "IP-Adapter",
    },
    # IP-Adapter CLIP image encoder
    {
        "id": "ip_adapter_clip",
        "repo": "h94/IP-Adapter",
        "file": "models/image_encoder/model.safetensors",
        "dest": os.path.join(IPADAPTER, "CLIP-ViT-H-14-laion2B-s32B-b79K/model.safetensors"),
        "role": "CLIP image encoder for IP-Adapter",
        "family": "IP-Adapter",
    },
    # ControlNet Canny (SD1.5)
    {
        "id": "controlnet_canny_sdv15",
        "repo": "diffusers/controlnet-canny-sdxl-1.0",
        "file": None,  # Will use alternate source
        "dest": os.path.join(CONTROLNET, "control_v11p_sd15_canny.pth"),
        "role": "Canny edge control for SD1.5",
        "family": "ControlNet",
        "repo": "lllyasviel/ControlNet-v1-1",
        "file": "control_v11p_sd15_canny.pth",
    },
    # ControlNet Depth (SD1.5)
    {
        "id": "controlnet_depth_sdv15",
        "repo": "lllyasviel/ControlNet-v1-1",
        "file": "control_v11f1p_sd15_depth.pth",
        "dest": os.path.join(CONTROLNET, "control_v11f1p_sd15_depth.pth"),
        "role": "Depth control for SD1.5",
        "family": "ControlNet",
    },
    # ControlNet OpenPose (SD1.5)
    {
        "id": "controlnet_pose_sdv15",
        "repo": "lllyasviel/ControlNet-v1-1",
        "file": "control_v11p_sd15_openpose.pth",
        "dest": os.path.join(CONTROLNET, "control_v11p_sd15_openpose.pth"),
        "role": "Pose control for SD1.5",
        "family": "ControlNet",
    },
    # Real-ESRGAN upscale model
    {
        "id": "realesrgan",
        "repo": "ai-forever/Real-ESRGAN",
        "file": "RealESRGAN_x4plus.pth",
        "dest": os.path.join(UPSCALE, "RealESRGAN_x4plus.pth"),
        "role": "Image upscaling / restoration",
        "family": "Restoration",
    },
]

def download_model(model):
    """Download a single model."""
    if os.path.exists(model["dest"]):
        size_mb = os.path.getsize(model["dest"]) / (1024**2)
        if size_mb > 10:
            print(f"  SKIP (exists, {size_mb:.0f}MB): {model['id']}")
            return True
    
    print(f"  Downloading: {model['id']} from {model['repo']}...")
    start = time.time()
    try:
        path = hf_hub_download(
            repo_id=model["repo"],
            filename=model["file"],
            local_dir=os.path.dirname(model["dest"]),
            local_dir_use_symlinks=False,
        )
        # If downloaded to a different path, move it
        if path != model["dest"]:
            import shutil
            os.makedirs(os.path.dirname(model["dest"]), exist_ok=True)
            shutil.move(path, model["dest"])
        
        elapsed = time.time() - start
        size_mb = os.path.getsize(model["dest"]) / (1024**2)
        print(f"  DONE: {model['id']} ({size_mb:.0f}MB, {elapsed:.1f}s)")
        return True
    except Exception as e:
        print(f"  FAILED: {model['id']} - {str(e)[:100]}")
        return False

# Download all models
results = {}
for model in downloads:
    is_optional = model.get("optional", False)
    try:
        ok = download_model(model)
        results[model["id"]] = {"ok": ok, "role": model["role"], "family": model["family"]}
    except Exception as e:
        results[model["id"]] = {"ok": False, "error": str(e)[:100], "role": model["role"]}
        if not is_optional:
            print(f"  WARNING: Required model {model['id']} failed")

# Summary
print("\n=== DOWNLOAD SUMMARY ===")
for mid, r in results.items():
    status = "✅" if r["ok"] else "❌"
    print(f"  {status} {mid}: {r['role']} ({r['family']})")

print(json.dumps(results, indent=2))
