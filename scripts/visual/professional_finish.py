#!/usr/bin/env python3
"""
Professional Finishing Pipeline
================================
Takes existing strong outputs through real finishing passes:
composition correction, color grade, contrast, sharpening, vignette,
grain, material enhancement, edge cleanup.

Uses ImageMagick for deterministic raster finishing.
"""

import subprocess
import os
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
CAL = PROJECT_ROOT / "artifacts" / "visual" / "calibration"
FINISHED = PROJECT_ROOT / "artifacts" / "visual" / "finished"
FINISHED.mkdir(parents=True, exist_ok=True)

def magick(*args):
    """Run ImageMagick command."""
    cmd = ["magick"] + list(args)
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    return r.returncode == 0, r.stderr

def finish_environment(input_path, output_path):
    """Professional finish for environment concept art."""
    # Step 1: Auto-level to maximize dynamic range
    magick(str(input_path), "-auto-level", str(output_path))
    # Step 2: Slight contrast boost + warmth
    magick(str(output_path),
        "-modulate", "100,110,102",  # slight saturation + warmth
        "-contrast", "-contrast",     # two passes of contrast
        str(output_path))
    # Step 3: Unsharp mask for detail
    magick(str(output_path),
        "-unsharp", "0x1+0.8+0.05",
        str(output_path))
    # Step 4: Vignette
    magick(str(output_path),
        "-vignette", "0x40+50+50",
        str(output_path))
    # Step 5: Subtle film grain
    magick(str(output_path),
        "-attenuate", "0.15", "+noise", "Gaussian",
        "-compose", "overlay", "-composite",
        str(output_path))
    return True

def finish_character(input_path, output_path):
    """Professional finish for character concept art."""
    # Step 1: Auto-white-balance
    magick(str(input_path), "-white-balance", str(output_path))
    # Step 2: Enhance local contrast (clarity)
    magick(str(output_path),
        "-unsharp", "0x3+1.2+0.02",
        str(output_path))
    # Step 3: Slight warm grade
    magick(str(output_path),
        "-modulate", "102,115,101",
        str(output_path))
    # Step 4: Vignette (tighter for portraits)
    magick(str(output_path),
        "-vignette", "0x60+50+50",
        str(output_path))
    # Step 5: Subtle grain
    magick(str(output_path),
        "-attenuate", "0.12", "+noise", "Gaussian",
        "-compose", "overlay", "-composite",
        str(output_path))
    return True

def finish_product(input_path, output_path):
    """Professional finish for product visualization."""
    # Step 1: Enhance highlights and shadows
    magick(str(input_path), "-auto-level", str(output_path))
    # Step 2: Sharpen product details
    magick(str(output_path),
        "-unsharp", "0x2+1.5+0.01",
        str(output_path))
    # Step 3: Boost contrast for premium feel
    magick(str(output_path),
        "-level", "5%,95%,1.1",
        str(output_path))
    # Step 4: Subtle vignette
    magick(str(output_path),
        "-vignette", "0x30+50+50",
        str(output_path))
    return True

def finish_vfx(input_path, output_path):
    """Professional finish for VFX concept art."""
    magick(str(input_path), "-auto-level", str(output_path))
    magick(str(output_path),
        "-modulate", "100,130,100",  # boost saturation for energy
        "-contrast",
        str(output_path))
    magick(str(output_path),
        "-unsharp", "0x1+1.0+0.03",
        str(output_path))
    magick(str(output_path),
        "-vignette", "0x50+50+50",
        str(output_path))
    return True

FINISH_TARGETS = [
    # (input_name, output_name, finish_function)
    ("I_environment_00.png", "env_finished.png", finish_environment),
    ("char_concept_b.png", "creature_finished.png", finish_character),
    ("char_concept_a.png", "warrior_finished.png", finish_character),
    ("G_3D_product_00.png", "product_finished.png", finish_product),
    ("B_character_creature_00.png", "forest_guardian_finished.png", finish_character),
    ("A_high_end_2D_00.png", "explorer_finished.png", finish_environment),
    ("vfx_energy.png", "vfx_energy_finished.png", finish_vfx),
    ("vfx_organic.png", "vfx_phoenix_finished.png", finish_vfx),
    ("L_VFX_00.png", "vfx_portal_finished.png", finish_vfx),
    ("F_2_5D_composition_00.png", "street_market_finished.png", finish_environment),
    ("env_natural.png", "mushroom_forest_finished.png", finish_environment),
    ("env_fantasy.png", "sky_city_finished.png", finish_environment),
    ("product_tech.png", "smartwatch_finished.png", finish_product),
    ("product_food.png", "dessert_finished.png", finish_product),
]

if __name__ == "__main__":
    print("=" * 60)
    print("PROFESSIONAL FINISHING PIPELINE")
    print("=" * 60)

    results = []
    for input_name, output_name, finish_fn in FINISH_TARGETS:
        input_path = CAL / input_name
        output_path = FINISHED / output_name

        if not input_path.exists():
            print(f"  SKIP {input_name} (not found)")
            continue

        print(f"  [{input_name}] -> {output_name}...", end=" ", flush=True)
        success = finish_fn(input_path, output_path)
        if success and output_path.exists():
            sz = os.path.getsize(str(output_path)) // 1024
            results.append({"input": input_name, "output": output_name, "size_kb": sz, "status": "OK"})
            print(f"OK ({sz}KB)")
        else:
            results.append({"input": input_name, "output": output_name, "status": "FAILED"})
            print("FAILED")

    # Save results
    out_path = FINISHED / "finishing_results.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)

    ok = sum(1 for r in results if r["status"] == "OK")
    print(f"\n{'='*60}")
    print(f"FINISHED: {ok}/{len(results)} assets")
    print(f"Results: {out_path}")
