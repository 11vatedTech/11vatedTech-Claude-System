#!/usr/bin/env python3
"""Visual Grounding V3 Dataset Generator.

Creates a balanced set of real controlled PNG images with explicit labels
for benchmarking visual grounding models. Each image is generated deterministically
with known properties - no filename-derived labels.

Classes:
- UI_PRESENT: YES / NO
- RENDER_TYPE: 2D / 3D(rendered)
- DOMINANT_VALUE: LOW_KEY / MID_KEY / HIGH_KEY
- MAJOR_CLIPPING: YES / NO
- MAJOR_OVERLAP: YES / NO
- ORIENTATION: LANDSCAPE / PORTRATURE / SQUARE (deterministic from dimensions)
- FOCAL_REGION: specific enum from actual pixel brightness center
- VISIBLE_TEXT: YES / NO
"""

import json
import hashlib
import os
import random
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("ERROR: PIL/Pillow not installed. Run: pip install Pillow")
    raise SystemExit(1)

OUTPUT_DIR = Path("artifacts/kapif/m002.1/visual-v3-dataset")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

random.seed(42)  # Deterministic

SAMPLES = []

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def compute_focal_region(img):
    """Compute focal region using 3x3 grid sampling for speed and accuracy."""
    w, h = img.size
    grid = [[0.0]*3 for _ in range(3)]
    # Sample every 8th pixel for speed
    step = max(1, min(w, h) // 50)
    for y in range(0, h, step):
        for x in range(0, w, step):
            try:
                p = img.getpixel((x, y))
            except Exception:
                continue
            if isinstance(p, tuple):
                b = sum(p[:3]) / 3
            else:
                b = float(p)
            gy = min(2, y * 3 // h)
            gx = min(2, x * 3 // w)
            grid[gy][gx] += b
    # Find brightest grid cell
    best = (0, 0, 0.0)
    for gy in range(3):
        for gx in range(3):
            if grid[gy][gx] > best[2]:
                best = (gy, gx, grid[gy][gx])
    names = [
        ["TOP_LEFT", "TOP_CENTER", "TOP_RIGHT"],
        ["CENTER_LEFT", "CENTER", "CENTER_RIGHT"],
        ["BOTTOM_LEFT", "BOTTOM_CENTER", "BOTTOM_RIGHT"],
    ]
    return names[best[0]][best[1]]

def compute_dominant_value(img):
    """Compute dominant value region using grid sampling."""
    w, h = img.size
    total_b = 0.0
    count = 0
    step = max(1, min(w, h) // 100)
    for y in range(0, h, step):
        for x in range(0, w, step):
            try:
                p = img.getpixel((x, y))
            except Exception:
                continue
            if isinstance(p, tuple):
                b = sum(p[:3]) / (3 * 255)
            else:
                b = p / 255 if isinstance(p, (int, float)) else 0.5
            total_b += b
            count += 1
    mean_b = total_b / max(1, count)
    if mean_b < 0.33:
        return "LOW_KEY"
    elif mean_b < 0.66:
        return "MID_KEY"
    else:
        return "HIGH_KEY"

def sample_id_from_index(i):
    return f"v3-{i:03d}"

# ======================================================================
# Category A: Frontend / UI
# ======================================================================

def gen_desktop_ui_with_nav(idx):
    """Desktop UI, navigation visible, multi-column, text visible."""
    w, h = 1920, 1080
    img = Image.new("RGB", (w, h), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    # Nav bar
    draw.rectangle([0, 0, w, 60], fill=(30, 30, 60))
    for x in [120, 240, 360, 480]:
        draw.rectangle([x, 15, x+80, 45], fill=(255, 255, 255))
    # 3 columns
    for col in range(3):
        x0 = 40 + col * 620
        draw.rectangle([x0, 90, x0+580, 1000], fill=(240, 240, 245))
        draw.rectangle([x0, 90, x0+580, 130], fill=(200, 200, 210))
    # Footer
    draw.rectangle([0, 1020, w, h], fill=(30, 30, 60))
    return img, {
        "ui_present": "YES", "render_type": "2D",
        "visible_text": "YES", "major_clipping": "NO",
        "major_overlap": "NO", "orientation": "LANDSCAPE",
        "label_provenance": "deterministic_pil_generation",
        "description": "Desktop UI with top nav bar, 3 columns, footer"
    }

def gen_mobile_ui_single_col(idx):
    """Mobile UI, single column, navigation visible."""
    w, h = 390, 844
    img = Image.new("RGB", (w, h), (245, 245, 250))
    draw = ImageDraw.Draw(img)
    # Status bar
    draw.rectangle([0, 0, w, 44], fill=(30, 30, 30))
    # Nav
    draw.rectangle([0, 44, w, 100], fill=(50, 50, 120))
    # Content blocks
    for y in range(120, 700, 100):
        draw.rectangle([16, y, w-16, y+80], fill=(255, 255, 255))
        draw.rectangle([16, y+10, 16+200, y+30], fill=(80, 80, 80))
    # Bottom nav
    draw.rectangle([0, h-60, w, h], fill=(50, 50, 120))
    return img, {
        "ui_present": "YES", "render_type": "2D",
        "visible_text": "YES", "major_clipping": "NO",
        "major_overlap": "NO", "orientation": "PORTRAIT",
        "label_provenance": "deterministic_pil_generation",
        "description": "Mobile UI single column with top/bottom nav"
    }

def gen_modal_overlay(idx):
    """Desktop UI with modal/overlay visible."""
    w, h = 1920, 1080
    img = Image.new("RGB", (w, h), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    # Background UI
    draw.rectangle([0, 0, w, 60], fill=(30, 30, 60))
    for col in range(3):
        x0 = 40 + col * 620
        draw.rectangle([x0, 90, x0+580, 1000], fill=(240, 240, 245))
    # Overlay (semi-transparent effect via darkened background)
    draw.rectangle([0, 0, w, h], fill=(0, 0, 0, 128))
    # Modal
    mx, my = w//2-250, h//2-200
    draw.rectangle([mx, my, mx+500, my+400], fill=(255, 255, 255))
    draw.rectangle([mx, my, mx+500, my+50], fill=(50, 50, 100))
    return img, {
        "ui_present": "YES", "render_type": "2D",
        "visible_text": "YES", "major_clipping": "NO",
        "major_overlap": "YES", "orientation": "LANDSCAPE",
        "label_provenance": "deterministic_pil_generation",
        "description": "Desktop UI with modal overlay overlapping content"
    }

def gen_selected_state(idx):
    """UI with selected/active state visible."""
    w, h = 1920, 1080
    img = Image.new("RGB", (w, h), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    # Sidebar with selected item
    draw.rectangle([0, 0, 280, h], fill=(240, 240, 245))
    items = ["Dashboard", "Settings", "Profile", "Reports", "Users"]
    for i, item in enumerate(items):
        y = 80 + i * 50
        if i == 1:
            draw.rectangle([0, y, 280, y+45], fill=(50, 80, 200))
        draw.rectangle([20, y+10, 160, y+30], fill=(100, 100, 100))
    # Main content
    draw.rectangle([310, 0, w, h], fill=(255, 255, 255))
    return img, {
        "ui_present": "YES", "render_type": "2D",
        "visible_text": "YES", "major_clipping": "NO",
        "major_overlap": "NO", "orientation": "LANDSCAPE",
        "label_provenance": "deterministic_pil_generation",
        "description": "UI with sidebar, one item selected (highlighted)"
    }

# ======================================================================
# Category B: Visual Failure / Clipping
# ======================================================================

def gen_clipped_mobile(idx):
    """Mobile UI with content clipped at edges."""
    w, h = 390, 200  # Intentionally short viewport to cause clipping
    img = Image.new("RGB", (w, h), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    # Content that overflows
    draw.rectangle([0, 0, w, 50], fill=(50, 50, 120))
    draw.rectangle([0, 45, w, 300], fill=(240, 240, 245))
    # Text extends beyond viewport bottom
    for y in range(60, 300, 25):
        draw.rectangle([20, y, 350, y+15], fill=(120, 120, 120))
    return img, {
        "ui_present": "YES", "render_type": "2D",
        "visible_text": "YES", "major_clipping": "YES",
        "major_overlap": "NO", "orientation": "LANDSCAPE",
        "label_provenance": "deterministic_pil_generation",
        "description": "Mobile UI with content clipped (viewport too short)"
    }

def gen_overlap_cards(idx):
    """UI with overlapping card elements."""
    w, h = 1280, 720
    img = Image.new("RGB", (w, h), (230, 230, 235))
    draw = ImageDraw.Draw(img)
    # Overlapping cards
    for i in range(4):
        x = 100 + i * 250
        y = 100 + (i % 2) * 150
        draw.rectangle([x, y, x+350, y+250], fill=(255, 255, 255))
        draw.rectangle([x+10, y+10, x+200, y+30], fill=(80, 80, 80))
        draw.rectangle([x+10, y+50, x+300, y+200], fill=(200, 210, 230))
    return img, {
        "ui_present": "YES", "render_type": "2D",
        "visible_text": "YES", "major_clipping": "NO",
        "major_overlap": "YES", "orientation": "LANDSCAPE",
        "label_provenance": "deterministic_pil_generation",
        "description": "UI with overlapping card elements"
    }

def gen_dark_ui_clipped(idx):
    """Dark UI with clipping - text extends past container."""
    w, h = 1920, 400  # Very short for wide content
    img = Image.new("RGB", (w, h), (20, 20, 30))
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, w, 60], fill=(40, 40, 60))
    for y in range(80, 800, 30):
        draw.rectangle([40, y, 1800, y+18], fill=(180, 180, 180))
    return img, {
        "ui_present": "YES", "render_type": "2D",
        "visible_text": "YES", "major_clipping": "YES",
        "major_overlap": "NO", "orientation": "LANDSCAPE",
        "label_provenance": "deterministic_pil_generation",
        "description": "Dark UI with text content clipped at bottom"
    }

# ======================================================================
# Category C: 3D / Art
# ======================================================================

def gen_3d_object_render(idx):
    """3D object rendered against gradient background."""
    w, h = 1024, 1024
    img = Image.new("RGB", (w, h), (0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Gradient background
    for y in range(h):
        v = int(30 + (y / h) * 40)
        draw.line([(0, y), (w, y)], fill=(v, v, v+10))
    # Simulated 3D sphere with shading using radial gradient
    cx, cy, r = w//2, h//2, 200
    # Draw concentric circles from outside in
    for ri in range(r, 0, -1):
        # Approximate lighting: brighter toward top-left
        nz_approx = (r*r - ri*ri*0.3)**0.5 / r if ri < r else 0.5
        light = max(0, 0.4 + 0.6 * nz_approx)
        c = int(40 + 200 * light)
        draw.ellipse([cx-ri, cy-ri, cx+ri, cy+ri],
                     outline=(c, int(c*0.9), int(c*0.7)))
    # Fill center
    draw.ellipse([cx-r//3, cy-r//3, cx+r//3, cy+r//3],
                 fill=(220, 198, 140))
    return img, {
        "ui_present": "NO", "render_type": "3D",
        "visible_text": "NO", "major_clipping": "NO",
        "major_overlap": "NO", "orientation": "SQUARE",
        "label_provenance": "deterministic_pil_generation",
        "description": "3D sphere render with gradient background"
    }

def gen_3d_scene_dark(idx):
    """3D scene, dark values, character-like silhouette."""
    w, h = 1920, 1080
    img = Image.new("RGB", (w, h), (10, 10, 15))
    draw = ImageDraw.Draw(img)
    # Ground plane
    for y in range(h//2, h):
        v = int(15 + (y - h//2) * 0.05)
        draw.line([(0, y), (w, y)], fill=(v, v-2, v-5))
    # Silhouette figure
    fx, fy = w//2, h//2 + 50
    # Body
    draw.rectangle([fx-30, fy, fx+30, fy+150], fill=(20, 20, 25))
    # Head
    draw.ellipse([fx-25, fy-60, fx+25, fy+10], fill=(25, 25, 30))
    # Glow eye
    draw.ellipse([fx-8, fy-40, fx-2, fy-34], fill=(200, 50, 30))
    draw.ellipse([fx+2, fy-40, fx+8, fy-34], fill=(200, 50, 30))
    # Ambient light on ground
    for r in range(100, 0, -1):
        alpha = int(15 * (1 - r/100))
        draw.ellipse([fx-r, h//2-r//2, fx+r, h//2+r//2],
                     fill=(alpha, alpha-5, alpha-10))
    return img, {
        "ui_present": "NO", "render_type": "3D",
        "visible_text": "NO", "major_clipping": "NO",
        "major_overlap": "NO", "orientation": "LANDSCAPE",
        "label_provenance": "deterministic_pil_generation",
        "description": "Dark 3D scene with character silhouette and glowing eyes"
    }

def gen_material_study(idx):
    """Material/lighting study - brass patina gradient."""
    w, h = 800, 600
    img = Image.new("RGB", (w, h), (0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Gradient using horizontal lines (much faster than putpixel)
    for y in range(h):
        yr = y / h
        r = int(140 + 80 * yr)
        g = int(100 + 60 * yr)
        b = int(40 + 30 * yr)
        draw.line([(0, y), (w, y)], fill=(min(255, r), min(255, g), min(255, b)))
    return img, {
        "ui_present": "NO", "render_type": "2D",
        "visible_text": "NO", "major_clipping": "NO",
        "major_overlap": "NO", "orientation": "LANDSCAPE",
        "label_provenance": "deterministic_pil_generation",
        "description": "Material study - brass/gold gradient"
    }

# ======================================================================
# Category D: Value / Composition
# ======================================================================

def gen_high_key_abstract(idx):
    """High-key abstract composition."""
    w, h = 1024, 1024
    img = Image.new("RGB", (w, h), (245, 245, 248))
    draw = ImageDraw.Draw(img)
    # Light colored shapes
    colors = [(220, 225, 235), (210, 215, 230), (230, 225, 220)]
    for i in range(5):
        x = random.randint(100, w-300)
        y = random.randint(100, h-300)
        s = random.randint(100, 250)
        draw.ellipse([x, y, x+s, y+s], fill=colors[i % 3])
    return img, {
        "ui_present": "NO", "render_type": "2D",
        "visible_text": "NO", "major_clipping": "NO",
        "major_overlap": "NO", "orientation": "SQUARE",
        "label_provenance": "deterministic_pil_generation",
        "description": "High-key abstract composition with light shapes"
    }

def gen_low_key_dramatic(idx):
    """Low-key dramatic composition with focal point off-center."""
    w, h = 1920, 1080
    img = Image.new("RGB", (w, h), (5, 5, 8))
    draw = ImageDraw.Draw(img)
    # Single spotlight off-center
    cx, cy = int(w * 0.65), int(h * 0.4)
    for r in range(200, 0, -1):
        v = int(180 * (1 - r/200) ** 2)
        draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill=(v, v-10, v-20))
    return img, {
        "ui_present": "NO", "render_type": "2D",
        "visible_text": "NO", "major_clipping": "NO",
        "major_overlap": "NO", "orientation": "LANDSCAPE",
        "label_provenance": "deterministic_pil_generation",
        "description": "Low-key dramatic composition with off-center focal point"
    }

def gen_multiple_focal(idx):
    """Composition with multiple competing focal regions."""
    w, h = 1280, 720
    img = Image.new("RGB", (w, h), (40, 40, 50))
    draw = ImageDraw.Draw(img)
    # Three equally bright focal points
    for cx, cy in [(300, 360), (640, 200), (980, 450)]:
        for r in range(80, 0, -1):
            v = int(200 * (1 - r/80))
            draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill=(v, v-5, v-10))
    return img, {
        "ui_present": "NO", "render_type": "2D",
        "visible_text": "NO", "major_clipping": "NO",
        "major_overlap": "NO", "orientation": "LANDSCAPE",
        "label_provenance": "deterministic_pil_generation",
        "description": "Composition with 3 competing focal points"
    }

# ======================================================================
# Category E: Mixed / Editorial
# ======================================================================

def gen_editorial_headline_top(idx):
    """Editorial layout with large headline at top."""
    w, h = 1200, 800
    img = Image.new("RGB", (w, h), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    # Large headline bar at top
    draw.rectangle([60, 60, w-60, 200], fill=(20, 20, 30))
    # Body text blocks
    draw.rectangle([60, 240, 560, 700], fill=(240, 240, 242))
    draw.rectangle([620, 240, w-60, 500], fill=(240, 240, 242))
    # Image placeholder
    draw.rectangle([620, 530, w-60, 700], fill=(180, 190, 200))
    return img, {
        "ui_present": "YES", "render_type": "2D",
        "visible_text": "YES", "major_clipping": "NO",
        "major_overlap": "NO", "orientation": "LANDSCAPE",
        "label_provenance": "deterministic_pil_generation",
        "description": "Editorial layout with large headline at top, body text, image"
    }

def gen_sparse_landing(idx):
    """Sparse landing page, center focal point."""
    w, h = 1920, 1080
    img = Image.new("RGB", (w, h), (250, 250, 252))
    draw = ImageDraw.Draw(img)
    # Center hero
    cx, cy = w//2, h//2
    draw.rectangle([cx-200, cy-80, cx+200, cy+80], fill=(30, 40, 80))
    draw.rectangle([cx-100, cy+120, cx+100, cy+160], fill=(200, 60, 40))
    return img, {
        "ui_present": "YES", "render_type": "2D",
        "visible_text": "YES", "major_clipping": "NO",
        "major_overlap": "NO", "orientation": "LANDSCAPE",
        "label_provenance": "deterministic_pil_generation",
        "description": "Sparse landing page with centered hero element"
    }

def gen_light_value_landscape(idx):
    """Light-value scene (nature-like, non-3D)."""
    w, h = 1920, 1080
    img = Image.new("RGB", (w, h), (0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Sky gradient (light)
    for y in range(h//2):
        v = int(180 + 75 * (y / (h/2)))
        draw.line([(0, y), (w, y)], fill=(v, v, min(255, v+10)))
    # Ground (light green)
    for y in range(h//2, h):
        v = int(120 + 40 * ((y - h/2) / (h/2)))
        draw.line([(0, y), (w, y)], fill=(v-30, v, v-50))
    return img, {
        "ui_present": "NO", "render_type": "2D",
        "visible_text": "NO", "major_clipping": "NO",
        "major_overlap": "NO", "orientation": "LANDSCAPE",
        "label_provenance": "deterministic_pil_generation",
        "description": "Light-value landscape scene (sky gradient + ground)"
    }

def gen_weak_hierarchy_ui(idx):
    """UI with intentionally weak visual hierarchy."""
    w, h = 1280, 720
    img = Image.new("RGB", (w, h), (240, 240, 240))
    draw = ImageDraw.Draw(img)
    # All elements same size/color - weak hierarchy
    for i in range(6):
        y = 40 + i * 110
        draw.rectangle([40, y, 1240, y+90], fill=(200, 200, 205))
        draw.rectangle([60, y+30, 400, y+60], fill=(160, 160, 165))
    return img, {
        "ui_present": "YES", "render_type": "2D",
        "visible_text": "YES", "major_clipping": "NO",
        "major_overlap": "NO", "orientation": "LANDSCAPE",
        "label_provenance": "deterministic_pil_generation",
        "description": "UI with intentionally weak visual hierarchy (uniform cards)"
    }

def gen_multiple_overlap_panels(idx):
    """UI panels with substantial overlap - 4 overlapping cards."""
    w, h = 1280, 720
    img = Image.new("RGB", (w, h), (245, 245, 248))
    draw = ImageDraw.Draw(img)
    for i in range(5):
        x = 80 + i * 180
        y = 60 + (i % 3) * 80
        draw.rectangle([x, y, x+350, y+300], fill=(255, 255, 255))
        draw.rectangle([x+10, y+10, x+200, y+30], fill=(100, 100, 100))
    return img, {
        "ui_present": "YES", "render_type": "2D",
        "visible_text": "YES", "major_clipping": "NO",
        "major_overlap": "YES", "orientation": "LANDSCAPE",
        "label_provenance": "deterministic_pil_generation",
        "description": "UI with 5 heavily overlapping card panels"
    }

def gen_clipped_editorial(idx):
    """Editorial layout with text clipped at bottom edge."""
    w, h = 800, 300  # Very short viewport
    img = Image.new("RGB", (w, h), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, w, 40], fill=(20, 20, 30))
    for y in range(60, 900, 20):
        draw.rectangle([30, y, 750, y+12], fill=(60, 60, 60))
    return img, {
        "ui_present": "YES", "render_type": "2D",
        "visible_text": "YES", "major_clipping": "YES",
        "major_overlap": "NO", "orientation": "LANDSCAPE",
        "label_provenance": "deterministic_pil_generation",
        "description": "Editorial layout with content clipped at bottom"
    }

def gen_focal_offcenter(idx):
    """Dark scene with focal point in top-right quadrant."""
    w, h = 1920, 1080
    img = Image.new("RGB", (w, h), (8, 8, 12))
    draw = ImageDraw.Draw(img)
    cx, cy = int(w * 0.8), int(h * 0.25)
    for r in range(150, 0, -1):
        v = int(220 * (1 - r/150) ** 1.5)
        draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill=(v, v-15, v-30))
    return img, {
        "ui_present": "NO", "render_type": "2D",
        "visible_text": "NO", "major_clipping": "NO",
        "major_overlap": "NO", "orientation": "LANDSCAPE",
        "label_provenance": "deterministic_pil_generation",
        "description": "Dark scene with off-center focal point (top-right)"
    }

def gen_character_silhouette(idx):
    """Character silhouette against colored background."""
    w, h = 800, 1200
    img = Image.new("RGB", (w, h), (80, 20, 40))
    draw = ImageDraw.Draw(img)
    # Character silhouette
    cx = w // 2
    # Head
    draw.ellipse([cx-50, 100, cx+50, 200], fill=(20, 10, 15))
    # Body
    draw.polygon([(cx-60, 200), (cx+60, 200), (cx+80, 700), (cx-80, 700)],
                 fill=(20, 10, 15))
    # Arms
    draw.polygon([(cx-60, 250), (cx-200, 450), (cx-180, 470), (cx-40, 280)],
                 fill=(20, 10, 15))
    draw.polygon([(cx+60, 250), (cx+200, 450), (cx+180, 470), (cx+40, 280)],
                 fill=(20, 10, 15))
    # Legs
    draw.polygon([(cx-40, 700), (cx-70, 1100), (cx-30, 1100), (cx, 700)],
                 fill=(20, 10, 15))
    draw.polygon([(cx+40, 700), (cx+70, 1100), (cx+30, 1100), (cx, 700)],
                 fill=(20, 10, 15))
    return img, {
        "ui_present": "NO", "render_type": "2D",
        "visible_text": "NO", "major_clipping": "NO",
        "major_overlap": "NO", "orientation": "PORTRAIT",
        "label_provenance": "deterministic_pil_generation",
        "description": "Character silhouette against dark red background"
    }

def gen_dense_text(idx):
    """Dense text layout - multiple columns of text blocks."""
    w, h = 1200, 1600
    img = Image.new("RGB", (w, h), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    # Two-column dense text
    for col in range(2):
        x0 = 60 + col * 580
        for y in range(80, 1500, 22):
            line_w = random.randint(300, 520)
            draw.rectangle([x0, y, x0+line_w, y+14], fill=(60, 60, 60))
    return img, {
        "ui_present": "YES", "render_type": "2D",
        "visible_text": "YES", "major_clipping": "NO",
        "major_overlap": "NO", "orientation": "PORTRAIT",
        "label_provenance": "deterministic_pil_generation",
        "description": "Dense two-column text layout"
    }

# ======================================================================
# Additional balanced samples to ensure class diversity
# ======================================================================

def gen_square_3d_torus(idx):
    """Square 3D torus-like object."""
    w, h = 800, 800
    img = Image.new("RGB", (w, h), (15, 15, 25))
    draw = ImageDraw.Draw(img)
    cx, cy = w//2, h//2
    # Concentric rings
    for r in range(180, 60, -5):
        brightness = int(100 + 80 * ((180-r)/120))
        draw.ellipse([cx-r, cy-r, cx+r, cy+r],
                     outline=(brightness, brightness-20, brightness-40), width=3)
    # Inner glow
    for r in range(60, 0, -1):
        v = int(150 * (r/60))
        draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill=(v, v//2, v//3))
    return img, {
        "ui_present": "NO", "render_type": "3D",
        "visible_text": "NO", "major_clipping": "NO",
        "major_overlap": "NO", "orientation": "SQUARE",
        "label_provenance": "deterministic_pil_generation",
        "description": "3D torus-like concentric ring object"
    }

def gen_mid_value_abstract(idx):
    """Mid-value abstract composition."""
    w, h = 1024, 768
    img = Image.new("RGB", (w, h), (128, 128, 135))
    draw = ImageDraw.Draw(img)
    random.seed(idx + 100)
    for _ in range(8):
        x = random.randint(0, w-200)
        y = random.randint(0, h-200)
        s = random.randint(80, 200)
        v = random.randint(90, 170)
        draw.rectangle([x, y, x+s, y+s], fill=(v, v-10, v+5))
    return img, {
        "ui_present": "NO", "render_type": "2D",
        "visible_text": "NO", "major_clipping": "NO",
        "major_overlap": "NO", "orientation": "LANDSCAPE",
        "label_provenance": "deterministic_pil_generation",
        "description": "Mid-value abstract composition with rectangles"
    }

def gen_dark_ui_no_overlap(idx):
    """Dark UI, no clipping, no overlap."""
    w, h = 1920, 1080
    img = Image.new("RGB", (w, h), (18, 18, 24))
    draw = ImageDraw.Draw(img)
    # Nav
    draw.rectangle([0, 0, w, 56], fill=(30, 30, 42))
    # Cards in grid
    for row in range(2):
        for col in range(3):
            x = 60 + col * 610
            y = 80 + row * 480
            draw.rectangle([x, y, x+560, y+440], fill=(35, 35, 48))
            draw.rectangle([x+20, y+20, x+300, y+50], fill=(120, 120, 140))
    return img, {
        "ui_present": "YES", "render_type": "2D",
        "visible_text": "YES", "major_clipping": "NO",
        "major_overlap": "NO", "orientation": "LANDSCAPE",
        "label_provenance": "deterministic_pil_generation",
        "description": "Dark UI grid with no clipping or overlap"
    }

def gen_3d_gradient_landscape(idx):
    """3D-like landscape gradient (procedural terrain)."""
    w, h = 1920, 1080
    img = Image.new("RGB", (w, h), (0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Sky
    for y in range(int(h*0.4)):
        v = int(40 + 80 * (y / (h*0.4)))
        draw.line([(0,y),(w,y)], fill=(v+20, v+30, v+60))
    # Mountains
    random.seed(200)
    points = [(0, int(h*0.4))]
    for x in range(0, w+40, 40):
        base_y = int(h*0.4) + random.randint(-80, 80)
        points.append((x, base_y))
    points.append((w, int(h*0.4)))
    points.append((w, h))
    points.append((0, h))
    draw.polygon(points, fill=(30, 45, 25))
    # Foreground
    for y in range(int(h*0.7), h):
        v = int(20 + 15 * ((y - h*0.7) / (h*0.3)))
        draw.line([(0,y),(w,y)], fill=(v, v+8, v))
    return img, {
        "ui_present": "NO", "render_type": "2D",
        "visible_text": "NO", "major_clipping": "NO",
        "major_overlap": "NO", "orientation": "LANDSCAPE",
        "label_provenance": "deterministic_pil_generation",
        "description": "Procedural landscape with mountains (3D-like terrain)"
    }

# ======================================================================
# GENERATE ALL SAMPLES
# ======================================================================

generators = [
    gen_desktop_ui_with_nav,
    gen_mobile_ui_single_col,
    gen_modal_overlay,
    gen_selected_state,
    gen_clipped_mobile,
    gen_overlap_cards,
    gen_dark_ui_clipped,
    gen_3d_object_render,
    gen_3d_scene_dark,
    gen_material_study,
    gen_high_key_abstract,
    gen_low_key_dramatic,
    gen_multiple_focal,
    gen_editorial_headline_top,
    gen_sparse_landing,
    gen_light_value_landscape,
    gen_weak_hierarchy_ui,
    gen_character_silhouette,
    gen_dense_text,
    gen_square_3d_torus,
    gen_mid_value_abstract,
    gen_dark_ui_no_overlap,
    gen_3d_gradient_landscape,
    gen_multiple_overlap_panels,
    gen_clipped_editorial,
    gen_focal_offcenter,
]

samples = []
for i, gen_fn in enumerate(generators):
    sid = sample_id_from_index(i)
    img, labels = gen_fn(i)
    
    # Deterministic orientation from dimensions
    w, h = img.size
    if w > h:
        labels["orientation"] = "LANDSCAPE"
    elif h > w:
        labels["orientation"] = "PORTRAIT"
    else:
        labels["orientation"] = "SQUARE"
    
    # Compute focal region from actual pixels
    labels["focal_region"] = compute_focal_region(img)
    
    # Compute dominant value from actual pixels
    labels["dominant_value"] = compute_dominant_value(img)
    
    # Save image
    img_path = OUTPUT_DIR / f"{sid}.png"
    img.save(str(img_path))
    
    # Compute hash
    img_hash = sha256_file(str(img_path))
    
    sample = {
        "sample_id": sid,
        "sha256": img_hash,
        "source_path": str(img_path),
        "width": w,
        "height": h,
        "ground_truth": {
            k: v for k, v in labels.items()
            if k not in ("label_provenance", "description")
        },
        "label_provenance": labels.get("label_provenance", "deterministic_pil_generation"),
        "description": labels.get("description", ""),
    }
    samples.append(sample)

# Compute dataset hash
dataset_bytes = json.dumps(samples, sort_keys=True, indent=2).encode()
dataset_hash = hashlib.sha256(dataset_bytes).hexdigest()

# Compute label distributions
prop_counts = {}
for s in samples:
    for prop, val in s["ground_truth"].items():
        if prop not in prop_counts:
            prop_counts[prop] = {}
        prop_counts[prop][val] = prop_counts[prop].get(val, 0) + 1

# Check class balance for binary properties
balance_ok = True
for prop in ["ui_present", "visible_text", "major_clipping", "major_overlap"]:
    counts = prop_counts.get(prop, {})
    yes_count = counts.get("YES", 0)
    no_count = counts.get("NO", 0)
    total = yes_count + no_count
    if total > 0:
        minority = min(yes_count, no_count)
        if minority < 3:
            print(f"WARN: {prop} imbalanced: YES={yes_count} NO={no_count}")
            balance_ok = False

# Write manifest
manifest = {
    "version": 3,
    "dataset_hash": dataset_hash,
    "total_samples": len(samples),
    "label_distributions": prop_counts,
    "class_balance_sufficient": balance_ok,
    "samples": samples,
}

manifest_path = OUTPUT_DIR / "dataset-manifest.json"
with open(str(manifest_path), "w") as f:
    json.dump(manifest, f, indent=2)

# Summary
print(f"V3 Dataset: {len(samples)} samples generated")
print(f"Dataset hash: {dataset_hash}")
print(f"Class balance: {'PASS' if balance_ok else 'FAIL'}")
print(f"Output: {OUTPUT_DIR}")
print()
print("Label distributions:")
for prop, counts in sorted(prop_counts.items()):
    print(f"  {prop}: {counts}")
