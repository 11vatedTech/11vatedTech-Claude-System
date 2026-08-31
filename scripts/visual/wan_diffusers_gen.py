"""BLOCKER 1: Wan2.1 T2V 1.3B video generation via diffusers (native SDPA, no flash-attn needed).
Hardware: RTX 5070 Ti Laptop ~12GB VRAM. Uses Wan2.1-T2V-1.3B-Diffusers from HF cache.
Settings chosen for 12GB: 480x832, ~49 frames, CPU offload, bf16.
Writes MP4 + extracted frames + a JSON benchmark report.
"""
import os, sys, json, time, gc, traceback

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "..", "artifacts", "visual", "video")
OUT = os.path.abspath(OUT)
os.makedirs(OUT, exist_ok=True)

MODEL_ID = "Wan-AI/Wan2.1-T2V-1.3B-Diffusers"
PROMPT = ("A luminous purple crystal floating in a dark obsidian cavern, violet energy "
          "pulses radiating from within the crystal, slow cinematic rotation, volumetric "
          "god rays, dark fantasy atmosphere, deep shadows, bioluminescent glow, "
          "cinematic camera slowly orbiting, high detail.")
NEG = ("blurry, low quality, distorted, watermark, text, jpeg artifacts, extra fingers, "
       "mutated hands, poorly drawn, static, dull colors")
H, W, NFRAMES = 480, 832, 49  # ~3s @ 16fps, fits 12GB
STEPS, GUIDANCE, SEED = 25, 5.0, 42

report = {"model": MODEL_ID, "prompt": PROMPT, "resolution": f"{W}x{H}",
          "frames": NFRAMES, "steps": STEPS, "guidance": GUIDANCE, "seed": SEED,
          "vram_gb": 12}

def log(msg):
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    with open(os.path.join(OUT, "wan_run.log"), "a", encoding="utf-8") as f:
        f.write(line + "\n")

try:
    import torch
    from diffusers import WanPipeline
    from diffusers.utils import export_to_video
    log(f"torch {torch.__version__}, CUDA avail={torch.cuda.is_available()}")
    log(f"GPU: {torch.cuda.get_device_name(0)}")
    log(f"Loading pipeline {MODEL_ID} ...")
    t0 = time.time()
    pipe = WanPipeline.from_pretrained(MODEL_ID, torch_dtype=torch.bfloat16)
    # CPU offload text encoder to save VRAM
    pipe.enable_model_cpu_offload()
    pipe.vae.enable_tiling()
    t_load = time.time() - t0
    report["load_time_s"] = round(t_load, 1)
    log(f"Pipeline loaded in {t_load:.1f}s. Generating...")
    torch.cuda.reset_peak_memory_stats()
    t1 = time.time()
    out = pipe(prompt=PROMPT, negative_prompt=NEG, height=H, width=W,
               num_frames=NFRAMES, num_inference_steps=STEPS,
               guidance_scale=GUIDANCE, generator=torch.Generator().manual_seed(SEED))
    t_gen = time.time() - t1
    peak = torch.cuda.max_memory_allocated() / 1e9
    report["gen_time_s"] = round(t_gen, 1)
    report["vram_peak_gb"] = round(peak, 2)
    log(f"Generated in {t_gen:.1f}s, peak VRAM {peak:.2f}GB")
    frames = out.frames[0]
    mp4 = os.path.join(OUT, "wan_crystal_obsidian.mp4")
    export_to_video(frames, mp4, fps=16)
    report["artifact"] = mp4
    # Extract 6 representative frames
    from PIL import Image
    step = max(1, len(frames) // 6)
    for i, idx in enumerate(range(0, len(frames), step)):
        if i >= 6: break
        fp = os.path.join(OUT, f"wan_frame_{i:02d}.png")
        Image.fromarray(frames[idx]).save(fp)
    report["frame_count"] = len(frames)
    report["fps"] = 16
    report["status"] = "SUCCESS"
    log(f"DONE. Video: {mp4}")
except Exception as e:
    report["status"] = "FAILED"
    report["error"] = str(e)
    log("FAILED: " + str(e))
    log(traceback.format_exc()[-1500:])
finally:
    with open(os.path.join(OUT, "wan_report.json"), "w") as f:
        json.dump(report, f, indent=2)
    log("Report written. Exit.")
