"""Quick FLUX.2 model load test — just try loading, no generation."""
import json, sys, time
from datetime import datetime
from pathlib import Path
import torch
from diffusers import Flux2Pipeline

OUTPUT_DIR = Path(__file__).resolve().parents[2] / "artifacts" / "ascension" / "milestone1"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

results = {
    "date": datetime.now().isoformat(),
    "gpu": torch.cuda.get_device_name(0),
    "vram_gb": round(torch.cuda.get_device_properties(0).total_memory/1e9, 2),
    "torch": torch.__version__,
    "cuda": torch.version.cuda,
}

print(f"GPU: {results['gpu']} ({results['vram_gb']}GB)")
print(f"PyTorch {results['torch']}, CUDA {results['cuda']}")

try:
    print("Loading model (bfloat16)...")
    t0 = time.time()
    pipe = Flux2Pipeline.from_pretrained(
        "black-forest-labs/FLUX.2-klein-4B",
        torch_dtype=torch.bfloat16,
    )
    load_time = round(time.time() - t0, 1)
    print(f"Model loaded in {load_time}s")

    print("Moving to GPU...")
    t0 = time.time()
    pipe = pipe.to("cuda")
    gpu_time = round(time.time() - t0, 1)
    
    vram = round(torch.cuda.memory_allocated(0)/1e9, 2)
    print(f"GPU loaded in {gpu_time}s, VRAM: {vram}GB")

    # Quick generation test
    print("Generating test image...")
    torch.cuda.reset_peak_memory_stats()
    t0 = time.time()
    img = pipe("A simple test image", num_inference_steps=4, guidance_scale=3.5, height=256, width=256).images[0]
    gen_time = round(time.time() - t0, 1)
    peak = round(torch.cuda.max_memory_allocated(0)/1e9, 2)
    
    path = OUTPUT_DIR / "flux2-test-output.png"
    img.save(str(path))
    print(f"Generated in {gen_time}s, peak VRAM: {peak}GB, output: {path}")

    results["status"] = "FEASIBLE"
    results["load_time_s"] = load_time
    results["gpu_time_s"] = gpu_time
    results["gen_time_s"] = gen_time
    results["load_vram_gb"] = vram
    results["peak_vram_gb"] = peak
    
except torch.cuda.OutOfMemoryError:
    print("OOM — model too large for 12GB VRAM")
    results["status"] = "CONSTRAINED_OOM"
except Exception as e:
    print(f"FAIL: {type(e).__name__}: {str(e)[:300]}")
    results["status"] = "FAILED"
    results["error"] = f"{type(e).__name__}: {str(e)[:300]}"

with open(OUTPUT_DIR / "flux2-benchmark-results.json", "w") as f:
    json.dump(results, f, indent=2, default=str)
print(f"\nResults: flux2-benchmark-results.json")
print(f"Classification: {results.get('status', 'UNKNOWN')}")