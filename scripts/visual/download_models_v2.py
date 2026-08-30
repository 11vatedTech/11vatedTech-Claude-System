"""Download remaining models with corrected paths."""
import os, sys, json, time
from huggingface_hub import hf_hub_download

COMFYUI = os.path.expanduser("~/ComfyUI")
CHECKPOINTS = os.path.join(COMFYUI, "models", "checkpoints")
UPSCALE = os.path.join(COMFYUI, "models", "upscale_models")

def download(repo, filename, dest, label=""):
    if os.path.exists(dest) and os.path.getsize(dest) > 10*1024*1024:
        print(f"  EXISTS: {label} ({os.path.getsize(dest)//1024**2}MB)")
        return True
    print(f"  DL: {label} from {repo}/{filename}...")
    t0 = time.time()
    try:
        path = hf_hub_download(repo_id=repo, filename=filename, local_dir=os.path.dirname(dest))
        if path != dest:
            import shutil
            shutil.move(path, dest)
        mb = os.path.getsize(dest) / 1024**2
        print(f"  OK: {label} ({mb:.0f}MB, {time.time()-t0:.0f}s)")
        return True
    except Exception as e:
        print(f"  FAIL: {label} - {e}")
        return False

# DreamShaper 8 - correct path (filename with space needs URL encoding or use snapshot)
print("=== DreamShaper 8 ===")
download("Lykon/DreamShaper", "DreamShaper 8 pruned.safetensors",
         os.path.join(CHECKPOINTS, "dreamshaper_8_pruned.safetensors"), "DreamShaper 8")

# Try alternate filename
if not os.path.exists(os.path.join(CHECKPOINTS, "dreamshaper_8_pruned.safetensors")):
    download("Lykon/DreamShaper", "DreamShaper 8.safetensors",
             os.path.join(CHECKPOINTS, "dreamshaper_8.safetensors"), "DreamShaper 8 (full)")

# DreamShaper XL
print("\n=== DreamShaper XL ===")
# The repo is "Lykon/DreamShaper XL" - huggingface doesn't like spaces in repo id
# Try with the actual URL
try:
    from huggingface_hub import HfApi
    api = HfApi()
    files = api.list_repo_files(repo_id="Lykon/DreamShaper XL")
    print(f"  Files found: {[f for f in files if f.endswith('.safetensors')][:5]}")
    for f in files:
        if 'xl' in f.lower() and f.endswith('.safetensors') and 'refiner' not in f.lower():
            download("Lykon/DreamShaper XL", f,
                     os.path.join(CHECKPOINTS, "dreamshaper_xl.safetensors"), f"DreamShaper XL ({f})")
            break
    else:
        for f in files:
            if f.endswith('.safetensors'):
                download("Lykon/DreamShaper XL", f,
                         os.path.join(CHECKPOINTS, "dreamshaper_xl.safetensors"), f"DreamShaper XL ({f})")
                break
except Exception as e:
    print(f"  FAIL listing repo: {e}")
    # Try direct download with URL encoding
    try:
        download("Lykon/DreamShaper%20XL", "DreamShaper XL v2.1.safetensors",
                 os.path.join(CHECKPOINTS, "dreamshaper_xl.safetensors"), "DreamShaper XL (URL encoded)")
    except:
        pass

# SD3.5 Medium - needs gated access, try alternate source
print("\n=== SD3.5 Medium ===")
# Try stabilityai official (may need auth token)
download("stabilityai/stable-diffusion-3.5-medium", "sd3.5_medium.safetensors",
         os.path.join(CHECKPOINTS, "sd3.5_medium.safetensors"), "SD3.5 Medium")

# FLUX Schnell - needs auth, try alternate quantized version
print("\n=== FLUX Schnell ===")
# Try community quantized version that fits 12GB
download("city96/FLUX.1-schnell-gguf", "flux1-schnell-Q5_K_M.gguf",
         os.path.join(CHECKPOINTS, "flux1_schnell_q5km.gguf"), "FLUX Schnell Q5_K_M (GGUF)")

# Real-ESRGAN - correct repo
print("\n=== Real-ESRGAN ===")
download("ai-forever/Real-ESRGAN", "RealESRGAN_x4plus.pth",
         os.path.join(UPSCALE, "RealESRGAN_x4plus.pth"), "Real-ESRGAN x4+")

# Also try x2anime for faces
download("ai-forever/Real-ESRGAN", "RealESRGAN_x4plus_anime_6B.pth",
         os.path.join(UPSCALE, "RealESRGAN_x4plus_anime_6B.pth"), "Real-ESRGAN x4+ anime")

# Also download GFPGAN for face restoration
print("\n=== GFPGAN ===")
download("TencentARC/GFPGAN", "GFPGANv1.4.pth",
         os.path.join(UPSCALE, "GFPGANv1.4.pth"), "GFPGAN v1.4")

print("\n=== CURRENT STATE ===")
for d in [CHECKPOINTS, UPSCALE]:
    for f in os.listdir(d):
        fp = os.path.join(d, f)
        if os.path.isfile(fp):
            print(f"  {f}: {os.path.getsize(fp)//1024**2}MB")
