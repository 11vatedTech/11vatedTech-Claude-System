"""
Wan2.1 Video Generation — RTX 5070 Ti 12GB
Download + Generate in one process to avoid segfaults.
"""
import os, time, json, gc
import torch
os.environ['TOKENIZERS_PARALLELISM'] = 'false'

ARTIFACTS = os.path.join('artifacts', 'visual', 'video')
os.makedirs(ARTIFACTS, exist_ok=True)
MODEL_ID = 'Wan-AI/Wan2.1-T2V-1.3B-Diffusers'

def check_vram():
    free = torch.cuda.mem_get_info(0)[0] / 1e9
    total = torch.cuda.get_device_properties(0).total_memory / 1e9
    print(f"  VRAM: {free:.1f} GB free / {total:.1f} GB total")
    return free

t_start = time.time()
print("=" * 60)
print("WAN 2.1 VIDEO — RTX 5070 Ti 12GB")
print("=" * 60)
check_vram()

# Step 1: Download + load pipeline (this downloads ~5GB on first run)
print("\n[1/4] Loading WanPipeline (download + load)...")
t0 = time.time()
from diffusers import WanPipeline
pipe = WanPipeline.from_pretrained(MODEL_ID, dtype=torch.float16)
pipe.enable_model_cpu_offload()
pipe.enable_attention_slicing()
print(f"  Loaded in {time.time()-t0:.1f}s")
check_vram()

# Step 2: Generate T2V #1
print("\n[2/4] Generating T2V: crystal_rotation...")
t0 = time.time()
output1 = pipe(
    prompt="A luminous crystal cluster slowly rotating in a dark void, refracting purple and amber light rays, cinematic lighting, volumetric fog",
    num_frames=33,
    num_inference_steps=25,
    guidance_scale=5.0,
    height=480,
    width=832,
    generator=torch.Generator("cuda").manual_seed(42),
)
t1 = time.time() - t0
frames1 = output1.frames[0]
print(f"  {len(frames1)} frames in {t1:.1f}s")

import imageio, numpy as np
v1 = os.path.join(ARTIFACTS, "wan_t2v_crystal_rotation.mp4")
imageio.mimsave(v1, [np.array(f.convert("RGB")) for f in frames1], fps=16, codec="libx264")
frames1[0].save(os.path.join(ARTIFACTS, "wan_t2v_crystal_rotation_frame000.png"))
frames1[len(frames1)//2].save(os.path.join(ARTIFACTS, "wan_t2v_crystal_rotation_frame_mid.png"))
frames1[-1].save(os.path.join(ARTIFACTS, "wan_t2v_crystal_rotation_frame_last.png"))
print(f"  Saved: {v1}")
del output1; gc.collect()

# Step 3: Generate T2V #2
print("\n[3/4] Generating T2V: ocean_waves...")
t0 = time.time()
output2 = pipe(
    prompt="Ocean waves crashing against dark volcanic rocks at golden hour, warm sunset light through water spray, cinematic wide shot, photorealistic",
    num_frames=33,
    num_inference_steps=25,
    guidance_scale=5.0,
    height=480,
    width=832,
    generator=torch.Generator("cuda").manual_seed(43),
)
t2 = time.time() - t0
frames2 = output2.frames[0]
print(f"  {len(frames2)} frames in {t2:.1f}s")

v2 = os.path.join(ARTIFACTS, "wan_t2v_ocean_waves.mp4")
imageio.mimsave(v2, [np.array(f.convert("RGB")) for f in frames2], fps=16, codec="libx264")
frames2[0].save(os.path.join(ARTIFACTS, "wan_t2v_ocean_waves_frame000.png"))
frames2[len(frames2)//2].save(os.path.join(ARTIFACTS, "wan_t2v_ocean_waves_frame_mid.png"))
print(f"  Saved: {v2}")
del output2; gc.collect()

# Step 4: I2V - use crystal frame as latent start
print("\n[4/4] Generating I2V: crystal_i2v...")
from PIL import Image
ref = Image.open(os.path.join(ARTIFACTS, "wan_t2v_crystal_rotation_frame000.png")).convert("RGB").resize((832, 480))
ref_tensor = torch.from_numpy(np.array(ref)).permute(2, 0, 1).float() / 255.0
ref_tensor = ref_tensor.unsqueeze(0)

# Encode to latent
vae = pipe.vae
with torch.no_grad():
    latent = vae.encode(ref_tensor.to(vae.device, dtype=vae.dtype)).latent_dist
    init_latent = latent.sample() * vae.config.scaling_factor

t0 = time.time()
output3 = pipe(
    prompt="Slowly rotating crystal revealing internal refraction patterns, light shifting across facets, smooth cinematic motion",
    latents=init_latent.to(pipe.device, dtype=pipe.transformer.dtype),
    num_frames=25,
    num_inference_steps=25,
    guidance_scale=5.0,
    height=480,
    width=832,
    generator=torch.Generator("cuda").manual_seed(100),
)
t3 = time.time() - t0
frames3 = output3.frames[0]
print(f"  {len(frames3)} frames in {t3:.1f}s")

v3 = os.path.join(ARTIFACTS, "wan_i2v_crystal_i2v.mp4")
imageio.mimsave(v3, [np.array(f.convert("RGB")) for f in frames3], fps=16, codec="libx264")
frames3[0].save(os.path.join(ARTIFACTS, "wan_i2v_crystal_i2v_frame000.png"))
frames3[len(frames3)//2].save(os.path.join(ARTIFACTS, "wan_i2v_crystal_i2v_frame_mid.png"))
print(f"  Saved: {v3}")

# Report
total = time.time() - t_start
report = {
    "model": MODEL_ID,
    "gpu": "RTX 5070 Ti Laptop",
    "vram_gb": 12.8,
    "load_time_s": round(time.time() - t_start + t1 + t2 + t3 - t1 - t2 - t3, 1),
    "generations": [
        {"name": "crystal_rotation", "type": "T2V", "frames": 33, "resolution": "832x480", "time_s": round(t1, 1), "success": True},
        {"name": "ocean_waves", "type": "T2V", "frames": 33, "resolution": "832x480", "time_s": round(t2, 1), "success": True},
        {"name": "crystal_i2v", "type": "I2V", "frames": 25, "resolution": "832x480", "time_s": round(t3, 1), "success": True},
    ],
    "total_time_s": round(total, 1),
}
with open(os.path.join(ARTIFACTS, "wan_generation_report.json"), "w") as f:
    json.dump(report, f, indent=2)

print(f"\n{'=' * 60}")
print(f"WAN VIDEO COMPLETE")
print(f"  Total time: {total:.0f}s")
print(f"  Videos: 3 generated")
print(f"  Report: artifacts/visual/video/wan_generation_report.json")
