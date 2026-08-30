#!/usr/bin/env python3
"""
Capability Audit — 3D Generation, Video, Audio
================================================
Determine what's currently available and what needs installation.
"""

import subprocess
import os
import sys
from pathlib import Path

def check(cmd):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        return r.returncode == 0, r.stdout.strip()[:200]
    except:
        return False, ""

def check_python_import(mod):
    try:
        __import__(mod)
        return True
    except:
        return False

def check_gpu():
    ok, out = check("nvidia-smi --query-gpu=name,memory.total --format=csv,noheader")
    return out if ok else "NOT FOUND"

def main():
    print("=" * 60)
    print("CAPABILITY AUDIT — 3D / VIDEO / AUDIO")
    print("=" * 60)

    # GPU
    print(f"\nGPU: {check_gpu()}")

    # Python
    print(f"Python: {sys.version}")

    # 3D Generation
    print("\n--- 3D GENERATION ---")
    hunyuan3d = check("pip show hunyuan3d 2>nul")
    trellis = check("pip show trellis 2>nul")
    trimesh = check_python_import("trimesh")
    print(f"  Hunyuan3D: {'INSTALLED' if hunyuan3d[0] else 'NOT INSTALLED'}")
    print(f"  TRELLIS: {'INSTALLED' if trellis[0] else 'NOT INSTALLED'}")
    print(f"  trimesh: {'INSTALLED' if trimesh else 'NOT INSTALLED'}")

    # Check for any .glb/.obj in existing artifacts
    glb_files = list(Path("artifacts").rglob("*.glb")) if Path("artifacts").exists() else []
    obj_files = list(Path("artifacts").rglob("*.obj")) if Path("artifacts").exists() else []
    print(f"  Existing .glb files: {len(glb_files)}")
    print(f"  Existing .obj files: {len(obj_files)}")

    # Video Generation
    print("\n--- VIDEO GENERATION ---")
    wan = check("pip show wan 2>nul")
    diffusers = check_python_import("diffusers")
    cv2 = check_python_import("cv2")
    print(f"  Wan: {'INSTALLED' if wan[0] else 'NOT INSTALLED'}")
    print(f"  diffusers: {'INSTALLED' if diffusers else 'NOT INSTALLED'}")
    print(f"  opencv: {'INSTALLED' if cv2 else 'NOT INSTALLED'}")

    # Audio
    print("\n--- AUDIO PRODUCTION ---")
    audiocraft = check("pip show audiocraft 2>nul")
    torchaudio = check_python_import("torchaudio")
    soundfile = check_python_import("soundfile")
    print(f"  AudioCraft: {'INSTALLED' if audiocraft[0] else 'NOT INSTALLED'}")
    print(f"  torchaudio: {'INSTALLED' if torchaudio else 'NOT INSTALLED'}")
    print(f"  soundfile: {'INSTALLED' if soundfile else 'NOT INSTALLED'}")

    # Check for existing audio files
    audio_files = list(Path("artifacts").rglob("*.wav")) + list(Path("artifacts").rglob("*.mp3")) if Path("artifacts").exists() else []
    print(f"  Existing audio files: {len(audio_files)}")

    # Animation
    print("\n--- ANIMATION ---")
    mixamo = Path(os.path.expanduser("~/Mixamo")).exists()
    print(f"  Mixamo dir: {'EXISTS' if mixamo else 'NOT FOUND'}")

    # Existing Blender/Unreal
    print("\n--- EXISTING 3D TOOLS ---")
    blender = Path(r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe")
    print(f"  Blender 5.2: {'EXISTS' if blender.exists() else 'NOT FOUND'}")
    ue = Path(r"C:\Program Files\Epic Games\UE_5.8")
    print(f"  Unreal 5.8: {'EXISTS' if ue.exists() else 'NOT FOUND'}")

    # ComfyUI models available
    print("\n--- COMFYUI MODELS ---")
    comfyui = Path(os.path.expanduser("~/ComfyUI"))
    checkpoints = list((comfyui / "models" / "checkpoints").glob("*.safetensors")) if (comfyui / "models" / "checkpoints").exists() else []
    loras = list((comfyui / "models" / "loras").glob("*.safetensors")) if (comfyui / "models" / "loras").exists() else []
    controlnet = list((comfyui / "models" / "controlnet").glob("*")) if (comfyui / "models" / "controlnet").exists() else []
    upscale = list((comfyui / "models" / "upscale_models").glob("*")) if (comfyui / "models" / "upscale_models").exists() else []
    print(f"  Checkpoints: {len(checkpoints)}")
    for c in checkpoints:
        print(f"    - {c.name} ({c.stat().st_size // (1024*1024)}MB)")
    print(f"  LoRAs: {len(loras)}")
    print(f"  ControlNet: {len(controlnet)}")
    print(f"  Upscale models: {len(upscale)}")

    # Pip packages summary
    print("\n--- KEY PIP PACKAGES ---")
    for pkg in ["torch", "torchvision", "torchaudio", "diffusers", "transformers", "accelerate", "safetensors", "trimesh", "pygltflib", "soundfile", "librosa", "audiocraft", "playwright", "Pillow", "opencv-python", "numpy", "scipy"]:
        ok, ver = check(f"pip show {pkg} 2>nul | findstr Version")
        print(f"  {pkg}: {ver if ok else 'NOT INSTALLED'}")


if __name__ == "__main__":
    main()
