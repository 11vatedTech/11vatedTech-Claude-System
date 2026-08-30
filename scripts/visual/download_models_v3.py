"""Download models with corrected HuggingFace repo/file paths."""
import os, sys, json, time
from huggingface_hub import hf_hub_download

COMFYUI = os.path.expanduser("~/ComfyUI")
CKPT = os.path.join(COMFYUI, "models", "checkpoints")
UPSCALE = os.path.join(COMFYUI, "models", "upscale_models")

for d in [CKPT, UPSCALE]:
    os.makedirs(d, exist_ok=True)

def dl(repo, fn, dest, label):
    if os.path.exists(dest) and os.path.getsize(dest) > 10*1024*1024:
        print(f"  EXISTS: {label} ({os.path.getsize(dest)//1024**2}MB)")
        return True
    print(f"  DL: {label} ...")
    t0 = time.time()
    try:
        path = hf_hub_download(repo_id=repo, filename=fn, local_dir=os.path.dirname(dest))
        if path != dest:
            import shutil
            shutil.move(path, dest)
        mb = os.path.getsize(dest)/1024**2
        print(f"  OK: {label} ({mb:.0f}MB, {time.time()-t0:.0f}s)")
        return True
    except Exception as e:
        print(f"  FAIL: {label}: {str(e)[:120]}")
        return False

results = {}

# DreamShaper 8 - digiplay mirror (no auth needed)
print("=== DreamShaper 8 ===")
results['ds8'] = dl("digiplay/DreamShaper_8", "dreamshaper_8.safetensors",
                    os.path.join(CKPT, "dreamshaper_8.safetensors"), "DreamShaper 8")

# DreamShaper XL Turbo v2.1
print("\n=== DreamShaper XL ===")
results['dsxl'] = dl("Lykon/dreamshaper-xl-v2-turbo", "DreamShaperXL_Turbo_v2_1.safetensors",
                     os.path.join(CKPT, "dreamshaper_xl_turbo_v21.safetensors"), "DreamShaper XL Turbo v2.1")

# Real-ESRGAN x4plus from GitHub releases (no HF auth)
print("\n=== Real-ESRGAN ===")
import urllib.request
realesrgan_url = "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth"
realesrgan_dest = os.path.join(UPSCALE, "RealESRGAN_x4plus.pth")
if os.path.exists(realesrgan_dest) and os.path.getsize(realesrgan_dest) > 10*1024*1024:
    print(f"  EXISTS: Real-ESRGAN ({os.path.getsize(realesrgan_dest)//1024**2}MB)")
    results['realesrgan'] = True
else:
    print(f"  DL: Real-ESRGAN from GitHub...")
    t0 = time.time()
    try:
        urllib.request.urlretrieve(realesrgan_url, realesrgan_dest)
        mb = os.path.getsize(realesrgan_dest)/1024**2
        print(f"  OK: Real-ESRGAN ({mb:.0f}MB, {time.time()-t0:.0f}s)")
        results['realesrgan'] = True
    except Exception as e:
        print(f"  FAIL: {e}")
        results['realesrgan'] = False

# Real-ESRGAN anime variant
realesrgan_anime_url = "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.2.4/RealESRGAN_x4plus_anime_6B.pth"
realesrgan_anime_dest = os.path.join(UPSCALE, "RealESRGAN_x4plus_anime_6B.pth")
if not (os.path.exists(realesrgan_anime_dest) and os.path.getsize(realesrgan_anime_dest) > 10*1024*1024):
    print("  DL: Real-ESRGAN anime...")
    try:
        urllib.request.urlretrieve(realesrgan_anime_url, realesrgan_anime_dest)
        print(f"  OK: Real-ESRGAN anime ({os.path.getsize(realesrgan_anime_dest)//1024**2}MB)")
        results['realesrgan_anime'] = True
    except Exception as e:
        print(f"  FAIL: {e}")
        results['realesrgan_anime'] = False
else:
    print(f"  EXISTS: Real-ESRGAN anime ({os.path.getsize(realesrgan_anime_dest)//1024**2}MB)")
    results['realesrgan_anime'] = True

# SD3.5 Medium - gated, requires HF token
print("\n=== SD3.5 Medium ===")
hf_token = os.environ.get('HF_TOKEN')
if hf_token:
    results['sd35m'] = dl("stabilityai/stable-diffusion-3.5-medium", "sd3.5_medium.safetensors",
                          os.path.join(CKPT, "sd3.5_medium.safetensors"), "SD3.5 Medium")
else:
    print("  SKIP: SD3.5 Medium requires HF_TOKEN (gated repo)")
    results['sd35m'] = 'skipped_no_auth'

# FLUX Schnell - gated, requires HF token
print("\n=== FLUX Schnell ===")
if hf_token:
    results['flux'] = dl("black-forest-labs/FLUX.1-schnell", "flux1-schnell.safetensors",
                          os.path.join(CKPT, "flux1_schnell.safetensors"), "FLUX Schnell")
else:
    print("  SKIP: FLUX Schnell requires HF_TOKEN (gated repo)")
    results['flux'] = 'skipped_no_auth'

# Summary
print("\n=== DOWNLOAD STATUS ===")
for k, v in results.items():
    status = "OK" if v is True else f"FAILED({v})" if v is False else f"SKIP({v})"
    print(f"  {k}: {status}")

# List all checkpoints and upscale models
print("\n=== CHECKPOINTS ===")
for f in os.listdir(CKPT):
    fp = os.path.join(CKPT, f)
    if os.path.isfile(fp) and os.path.getsize(fp) > 10*1024*1024:
        print(f"  {f}: {os.path.getsize(fp)//1024**2}MB")

print("\n=== UPSCALE MODELS ===")
for f in os.listdir(UPSCALE):
    fp = os.path.join(UPSCALE, f)
    if os.path.isfile(fp):
        print(f"  {f}: {os.path.getsize(fp)//1024**2}MB")
