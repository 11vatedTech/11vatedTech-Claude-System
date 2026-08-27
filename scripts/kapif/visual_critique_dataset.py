#!/usr/bin/env python3
"""Professional Visual Critique Dataset — Controlled before/after pairs.

Creates controlled image pairs where ONE design variable changed, so the model
must identify: OBSERVATION, CAUSE, IMPACT, REPAIR.

Disciplines covered:
- Typography (scale hierarchy)
- UI_Hierarchy (spacing/weight)
- Composition (focal point placement)
- Clipping/Layout (overflow repair)
- Value/Contrast (black crush)
"""

import json
import hashlib
import os
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    from PIL import Image, ImageDraw
    ImageFont = None

OUTPUT_DIR = Path("artifacts/kapif/m002.1/critique-v3-pairs")
DATASET_PATH = OUTPUT_DIR / "critique-manifest.json"


def _hash_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _get_font(size=24):
    """Try to load a real font, fallback to default."""
    font_paths = [
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/calibri.ttf",
        "C:/Windows/Fonts/verdana.ttf",
    ]
    for fp in font_paths:
        if os.path.exists(fp):
            try:
                return ImageFont.truetype(fp, size)
            except Exception:
                continue
    try:
        return ImageFont.truetype("arial", size)
    except Exception:
        return ImageFont.load_default()


def create_typography_pair():
    """BEFORE: all text same size (weak hierarchy).
       AFTER: headline large, body smaller (strong hierarchy)."""
    w, h = 800, 600
    bg = (245, 245, 240)

    # BEFORE: weak hierarchy
    img_b = Image.new("RGB", (w, h), bg)
    d = ImageDraw.Draw(img_b)
    font_mid = _get_font(20)
    d.rectangle([(40, 40), (760, 560)], outline=(200, 200, 200), width=2)
    y = 60
    for line in ["Article Title", "Subtitle goes here", "Body paragraph text that explains the main point of the article in detail.", "Another paragraph with more content and supporting evidence."]:
        d.text((60, y), line, fill=(40, 40, 40), font=font_mid)
        y += 50

    # AFTER: strong hierarchy
    img_a = Image.new("RGB", (w, h), bg)
    d = ImageDraw.Draw(img_a)
    d.rectangle([(40, 40), (760, 560)], outline=(200, 200, 200), width=2)
    font_title = _get_font(36)
    font_sub = _get_font(18)
    font_body = _get_font(14)
    d.text((60, 60), "Article Title", fill=(20, 20, 20), font=font_title)
    d.text((60, 110), "Subtitle goes here", fill=(100, 100, 100), font=font_sub)
    d.text((60, 160), "Body paragraph text that explains the main point of the article in detail.", fill=(50, 50, 50), font=font_body)
    d.text((60, 210), "Another paragraph with more content and supporting evidence.", fill=(50, 50, 50), font=font_body)

    return img_b, img_a, {
        "discipline": "TYPOGRAPHY",
        "intervention": "headline_scale_increase",
        "before_defect": "all_text_same_size_no_hierarchy",
        "after_repair": "distinct_title_subtitle_body_scale",
    }


def create_ui_hierarchy_pair():
    """BEFORE: cramped spacing, no visual separation.
       AFTER: proper whitespace and card separation."""
    w, h = 800, 600
    bg = (255, 255, 255)

    # BEFORE: cramped
    img_b = Image.new("RGB", (w, h), bg)
    d = ImageDraw.Draw(img_b)
    font = _get_font(14)
    y = 10
    for i in range(6):
        d.rectangle([(20, y), (780, y + 70)], fill=(240, 240, 245), outline=(200, 200, 200))
        d.text((30, y + 5), "Card %d Title" % (i + 1), fill=(30, 30, 30), font=_get_font(14))
        d.text((30, y + 30), "Description text for this card item.", fill=(100, 100, 100), font=font)
        y += 78

    # AFTER: proper spacing
    img_a = Image.new("RGB", (w, h), bg)
    d = ImageDraw.Draw(img_a)
    y = 20
    for i in range(4):
        d.rectangle([(30, y), (770, y + 90)], fill=(248, 248, 252), outline=(220, 220, 220), width=1)
        d.text((50, y + 12), "Card %d Title" % (i + 1), fill=(30, 30, 30), font=_get_font(18))
        d.text((50, y + 45), "Description text for this card item.", fill=(100, 100, 100), font=font)
        y += 120

    return img_b, img_a, {
        "discipline": "UI_HIERARCHY",
        "intervention": "whitespace_and_card_separation",
        "before_defect": "cramped_layout_no_separation",
        "after_repair": "proper_whitespace_card_padding",
    }


def create_composition_pair():
    """BEFORE: subject centered (generic).
       AFTER: subject off-center (rule of thirds)."""
    w, h = 800, 600
    bg = (30, 30, 50)

    # BEFORE: centered subject
    img_b = Image.new("RGB", (w, h), bg)
    d = ImageDraw.Draw(img_b)
    cx, cy = w // 2, h // 2
    d.ellipse([(cx - 80, cy - 80), (cx + 80, cy + 80)], fill=(200, 120, 60))
    d.ellipse([(cx - 30, cy - 40), (cx + 30, cy - 10)], fill=(40, 40, 60))
    # Generic horizon line
    d.line([(0, h // 2 + 100), (w, h // 2 + 100)], fill=(60, 60, 80), width=2)

    # AFTER: off-center subject (rule of thirds)
    img_a = Image.new("RGB", (w, h), bg)
    d = ImageDraw.Draw(img_a)
    ox, oy = w * 2 // 3, h // 3  # right-third intersection
    d.ellipse([(ox - 80, oy - 80), (ox + 80, oy + 80)], fill=(200, 120, 60))
    d.ellipse([(ox - 30, oy - 40), (ox + 30, oy - 10)], fill=(40, 40, 60))
    d.line([(0, h // 2 + 100), (w, h // 2 + 100)], fill=(60, 60, 80), width=2)

    return img_b, img_a, {
        "discipline": "COMPOSITION",
        "intervention": "rule_of_thirds_placement",
        "before_defect": "centered_subject_generic_composition",
        "after_repair": "off_center_subject_dynamic_composition",
    }


def create_clipping_pair():
    """BEFORE: content clipped at bottom (overflow).
       AFTER: content fully visible."""
    w, h = 400, 400
    bg = (255, 255, 255)

    # BEFORE: clipping
    img_b = Image.new("RGB", (w, h), bg)
    d = ImageDraw.Draw(img_b)
    font = _get_font(16)
    d.rectangle([(20, 20), (380, 380)], fill=(250, 250, 255), outline=(200, 200, 200))
    d.text((30, 30), "Mobile Card Title", fill=(30, 30, 30), font=_get_font(20))
    d.text((30, 70), "This is a paragraph of body text that should be fully visible within the card bounds but is currently being clipped at the bottom edge of the container which is a layout defect.", fill=(60, 60, 60), font=font)
    # Intentionally clip: draw text beyond card bottom

    # AFTER: no clipping
    img_a = Image.new("RGB", (w, 500), bg)
    d = ImageDraw.Draw(img_a)
    d.rectangle([(20, 20), (380, 480)], fill=(250, 250, 255), outline=(200, 200, 200))
    d.text((30, 30), "Mobile Card Title", fill=(30, 30, 30), font=_get_font(20))
    d.text((30, 70), "This is a paragraph of body text that should be fully visible within the card bounds and is now properly contained within the expanded card container.", fill=(60, 60, 60), font=font)

    return img_b, img_a, {
        "discipline": "LAYOUT",
        "intervention": "container_expansion_fix_clipping",
        "before_defect": "content_overflow_clipped",
        "after_repair": "expanded_container_full_visibility",
    }


def create_contrast_pair():
    """BEFORE: black crush (low contrast, dark details lost).
       AFTER: improved contrast (details visible)."""
    w, h = 600, 400

    # BEFORE: black crush
    img_b = Image.new("RGB", (w, h), (10, 10, 15))
    d = ImageDraw.Draw(img_b)
    # Very low contrast elements
    for y in range(50, 350, 60):
        for x in range(50, 550, 100):
            d.rectangle([(x, y), (x + 60, y + 30)], fill=(15, 15, 20), outline=(20, 20, 25))
    font = _get_font(14)
    d.text((50, 20), "Dark Interface Panel", fill=(30, 30, 35), font=font)

    # AFTER: readable contrast
    img_a = Image.new("RGB", (w, h), (25, 25, 35))
    d = ImageDraw.Draw(img_a)
    for y in range(50, 350, 60):
        for x in range(50, 550, 100):
            d.rectangle([(x, y), (x + 60, y + 30)], fill=(50, 50, 65), outline=(80, 80, 100))
    d.text((50, 20), "Dark Interface Panel", fill=(200, 200, 210), font=font)

    return img_b, img_a, {
        "discipline": "CONTRAST",
        "intervention": "black_crush_repair",
        "before_defect": "black_crush_low_contrast",
        "after_repair": "improved_contrast_readability",
    }


ALL_PAIRS = [
    create_typography_pair,
    create_ui_hierarchy_pair,
    create_composition_pair,
    create_clipping_pair,
    create_contrast_pair,
]


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    samples = []

    for gen_fn in ALL_PAIRS:
        img_b, img_a, meta = gen_fn()
        disc = meta["discipline"]

        path_before = OUTPUT_DIR / f"{disc.lower()}_before.png"
        path_after = OUTPUT_DIR / f"{disc.lower()}_after.png"

        img_b.save(str(path_before))
        img_a.save(str(path_after))

        samples.append({
            "pair_id": f"{disc.lower()}_pair",
            "discipline": disc,
            "before_path": str(path_before),
            "after_path": str(path_after),
            "before_hash": _hash_file(path_before),
            "after_hash": _hash_file(path_after),
            "before_size": [img_b.width, img_b.height],
            "after_size": [img_a.width, img_a.height],
            "intervention": meta["intervention"],
            "before_defect": meta["before_defect"],
            "after_repair": meta["after_repair"],
            "known_cause": meta["intervention"],
        })

    manifest = {
        "version": "v1",
        "pair_count": len(samples),
        "disciplines": list(set(s["discipline"] for s in samples)),
        "scoring_contract": {
            "required_sections": ["OBSERVATION", "CAUSE", "IMPACT", "REPAIR", "CONFIDENCE", "SPECULATION"],
            "scoring_dimensions": [
                "grounded_observation_accuracy",
                "known_cause_accuracy",
                "repair_relevance",
                "false_detail_rate",
                "discipline_correctness",
                "ab_vs_ba_position_stability",
            ],
        },
        "samples": samples,
    }

    with open(str(DATASET_PATH), "w") as f:
        json.dump(manifest, f, indent=2)

    print("Critique dataset created: %d pairs" % len(samples))
    print("Disciplines: %s" % ", ".join(manifest["disciplines"]))
    print("Manifest: %s" % DATASET_PATH)
    for s in samples:
        print("  %s: %s -> %s" % (s["pair_id"], s["before_defect"], s["after_repair"]))


if __name__ == "__main__":
    main()
