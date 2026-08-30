#!/usr/bin/env python3
"""Capture all range test HTML files as PNG screenshots via Playwright."""
import os, time
from pathlib import Path
from playwright.sync_api import sync_playwright

PROJECT_ROOT = Path(__file__).parent.parent.parent
CAL = PROJECT_ROOT / "artifacts" / "visual" / "calibration"

HTML_FILES = [
    # Shader range
    "shader_metal", "shader_organic", "shader_volumetric", "shader_abstract", "shader_chromatic",
    # Typography range
    "typo_editorial", "typo_luxury", "typo_experimental", "typo_kinetic", "typo_ui",
    # Vector range
    "vec_brand_mark", "vec_organic_ornament", "vec_tech_graphic", "vec_abstract_composition",
    # Hybrid advantage
    "hybrid_gen_only", "hybrid_code_native", "hybrid_full",
]

if __name__ == "__main__":
    print(f"Capturing {len(HTML_FILES)} range test screenshots...")
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 720})

        for name in HTML_FILES:
            html_path = CAL / f"{name}.html"
            if not html_path.exists():
                print(f"  SKIP {name} (no HTML)")
                continue

            png_path = CAL / f"{name}.png"
            url = f"file:///{html_path.as_posix()}"
            page.goto(url)
            # Wait for fonts + shader warmup
            page.wait_for_timeout(2000 if "shader" in name else 1500)
            page.screenshot(path=str(png_path))
            sz = os.path.getsize(str(png_path)) // 1024
            print(f"  {name}: {sz}KB")

        browser.close()
    print("Done!")
