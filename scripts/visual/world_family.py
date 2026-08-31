"""ORIGINAL WORLD FAMILY + CREATIVE RANGE GALLERY."""
import os, json, math
from PIL import Image, ImageDraw, ImageFilter
import numpy as np

OUT = "artifacts/visual/creative-cognition"
os.makedirs(OUT, exist_ok=True)

# ============================================================
# ORIGINAL WORLD: VERIDIAN DEPTHS
# Concept: An underwater civilization where bioluminescence is language
# ============================================================
VERIDIAN_WORLD = {
    "name": "Veridian Depths",
    "concept": "An underwater civilization where bioluminescent organisms serve as writing, architecture, and social hierarchy.",
    "culture": "Communal, slow-paced, deeply interconnected. Communication is visual/emotional through light patterns.",
    "environment": "Deep ocean trenches, bioluminescent coral cities, thermal vent power sources.",
    "materials": "Living coral, chitin, bioluminescent fluid, pressure-adapted glass, deep-sea minerals.",
    "shape_language": "Organic curves, branching structures, radial symmetry, flowing forms.",
    "color": "Deep blues, teals, bioluminescent greens, occasional warm bioluminescent orange.",
    "light": "Internal bioluminescence, thermal vent glow, filtered surface light.",
    "technology": "Bio-integrated, grown rather than built, symbiotic machinery.",
}

def create_world_bible():
    """Create the mini art bible for Veridian Depths."""
    print("--- Veridian Depths: Art Bible ---")
    
    bible = {
        "world": VERIDIAN_WORLD,
        "visual_principles": {
            "architecture": "Organic branching structures, no straight lines, bioluminescent navigation markers",
            "characters": "Flowing forms, bioluminescent patterns as identity, webbed extremities, large light-sensitive eyes",
            "objects": "Grown from living material, no sharp edges, functional beauty, symbiotic design",
            "typography": "Light patterns, not written symbols. Communication through bioluminescent sequences.",
            "motion": "Fluid, weighted by water pressure, graceful but deliberate.",
        },
        "palette": {
            "deep_ocean": (10, 25, 45),
            "biolum_green": (40, 200, 120),
            "biolum_teal": (30, 180, 180),
            "coral_warm": (180, 100, 60),
            "thermal_orange": (220, 140, 40),
            "surface_blue": (40, 80, 140),
        },
    }
    
    with open(os.path.join(OUT, "veridian_bible.json"), "w") as f:
        json.dump(bible, f, indent=2)
    
    print(f"  Art bible created")
    return bible

def create_veridian_character():
    """Create a character from the Veridian Depths world."""
    print("\n--- Veridian Depths: Character ---")
    
    W, H = 800, 1000
    img = Image.new("RGB", (W, H), (10, 25, 45))
    draw = ImageDraw.Draw(img)
    
    cx, cy = W // 2, H // 2
    
    # Character: "Light Speaker" — a bioluminescent being
    # Body: flowing organic form
    body_points = []
    for i in range(30):
        angle = i * math.pi / 15
        r = 80 + 20 * math.sin(angle * 3)
        x = cx + int(r * math.cos(angle))
        y = cy - 100 + int(r * math.sin(angle) * 1.5)
        body_points.append((x, y))
    
    if len(body_points) > 2:
        draw.polygon(body_points, fill=(20, 60, 80))
    
    # Head: larger, light-sensitive
    head_cx, head_cy = cx, cy - 180
    draw.ellipse([head_cx - 50, head_cy - 60, head_cx + 50, head_cy + 40], fill=(25, 70, 90))
    
    # Large eyes
    draw.ellipse([head_cx - 30, head_cy - 20, head_cx - 5, head_cy + 10], fill=(40, 200, 120))
    draw.ellipse([head_cx + 5, head_cy - 20, head_cx + 30, head_cy + 10], fill=(40, 200, 120))
    
    # Bioluminescent patterns
    for i in range(15):
        x = cx + int(60 * math.cos(i * 0.5))
        y = cy - 50 + int(100 * math.sin(i * 0.3))
        r = 5 + int(3 * math.sin(i))
        draw.ellipse([x - r, y - r, x + r, y + r], fill=(40, 200, 120))
    
    # Arms: flowing, webbed
    for side in [-1, 1]:
        for i in range(20):
            x = cx + side * (60 + i * 5)
            y = cy - 80 + i * 8
            wave = int(8 * math.sin(i * 0.5))
            r = max(1, 6 - i // 4)
            draw.ellipse([x + wave - r, y - r, x + wave + r, y + r], fill=(30, 150, 100))
    
    # Bioluminescent glow
    glow = Image.new("RGB", (W, H), (0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    for x, y in [(cx, cy - 180), (cx - 80, cy - 50), (cx + 80, cy - 50)]:
        for r in range(40, 0, -1):
            v = int(30 * (r / 40))
            glow_draw.ellipse([x - r, y - r, x + r, y + r], fill=(v // 3, v, v // 2))
    glow = glow.filter(ImageFilter.GaussianBlur(radius=15))
    
    arr = np.array(img, dtype=np.float32)
    glow_arr = np.array(glow, dtype=np.float32)
    result = np.clip(arr + glow_arr * 0.6, 0, 255).astype(np.uint8)
    img = Image.fromarray(result)
    
    fp = os.path.join(OUT, "veridian_character.png")
    img.save(fp)
    print(f"  Character: Light Speaker — {W}x{H}")
    return fp

def create_veridian_environment():
    """Create an environment from the Veridian Depths world."""
    print("\n--- Veridian Depths: Environment ---")
    
    W, H = 1200, 800
    img = Image.new("RGB", (W, H), (10, 20, 40))
    draw = ImageDraw.Draw(img)
    
    # Deep ocean gradient
    for y in range(H):
        t = y / H
        r = int(10 + 15 * t)
        g = int(20 + 30 * t)
        b = int(40 + 40 * t)
        draw.line([(0, y), (W, y)], fill=(r, g, b))
    
    # Bioluminescent coral city
    for i in range(8):
        cx = 100 + i * 140
        cy = H - 100 - np.random.randint(0, 100)
        
        # Coral branches
        for j in range(5):
            angle = -0.3 + j * 0.15
            length = 60 + np.random.randint(0, 40)
            x2 = cx + int(length * math.cos(angle))
            y2 = cy + int(length * math.sin(angle))
            
            # Branch with bioluminescent tip
            draw.line([(cx, cy), (x2, y2)], fill=(30, 120, 80), width=3)
            draw.ellipse([x2 - 5, y2 - 5, x2 + 5, y2 + 5], fill=(40, 200, 120))
    
    # Floating bioluminescent particles
    np.random.seed(42)
    for _ in range(100):
        x = np.random.randint(0, W)
        y = np.random.randint(0, H)
        r = np.random.randint(2, 6)
        draw.ellipse([x - r, y - r, x + r, y + r], fill=(40, 200, 120))
    
    # Thermal vent glow at bottom
    for x in range(0, W, 30):
        for r in range(20, 0, -1):
            v = int(40 * (r / 20))
            draw.ellipse([x - r, H - 50 - r, x + r, H - 50 + r], fill=(v, v // 2, 0))
    
    fp = os.path.join(OUT, "veridian_environment.png")
    img.save(fp)
    print(f"  Environment: Bioluminescent City — {W}x{H}")
    return fp

def create_creative_range_gallery():
    """Create a gallery of meaningfully different visual languages."""
    print("\n--- Creative Range Gallery ---")
    
    W, H = 1200, 800
    img = Image.new("RGB", (W, H), (20, 20, 25))
    draw = ImageDraw.Draw(img)
    
    # Gallery: 6 different visual languages in one image
    languages = [
        {"name": "LITHIC DREAMS", "color": (65, 75, 90), "shape": "crystalline"},
        {"name": "AETHERWEAVE", "color": (40, 60, 80), "shape": "wave"},
        {"name": "GRAPHITE DUSK", "color": (80, 75, 70), "shape": "gestural"},
        {"name": "VERIDIAN", "color": (30, 120, 80), "shape": "organic"},
        {"name": "NEON DRIFT", "color": (180, 40, 120), "shape": "geometric"},
        {"name": "OBSIDIAN", "color": (40, 40, 45), "shape": "brutalist"},
    ]
    
    cell_w = W // 3
    cell_h = H // 2
    
    for i, lang in enumerate(languages):
        col = i % 3
        row = i // 3
        x0 = col * cell_w
        y0 = row * cell_h
        
        # Background
        draw.rectangle([x0, y0, x0 + cell_w, y0 + cell_h], fill=lang["color"])
        
        # Shape based on language type
        cx = x0 + cell_w // 2
        cy = y0 + cell_h // 2
        
        if lang["shape"] == "crystalline":
            # Angular crystal
            draw.polygon([
                (cx, cy - 80),
                (cx + 50, cy - 20),
                (cx + 40, cy + 60),
                (cx - 40, cy + 60),
                (cx - 50, cy - 20),
            ], fill=tuple(min(255, c + 40) for c in lang["color"]))
        
        elif lang["shape"] == "wave":
            # Wave form
            for x in range(x0 + 50, x0 + cell_w - 50, 3):
                y = cy + int(30 * math.sin((x - x0) * 0.05))
                draw.ellipse([x - 2, y - 2, x + 2, y + 2], fill=(100, 180, 200))
        
        elif lang["shape"] == "gestural":
            # Hand-drawn circles
            for r in range(40, 0, -5):
                v = int(150 * (r / 40))
                draw.ellipse([cx - r + np.random.randint(-3, 3), cy - r + np.random.randint(-3, 3),
                             cx + r + np.random.randint(-3, 3), cy + r + np.random.randint(-3, 3)],
                            fill=(v, v, v))
        
        elif lang["shape"] == "organic":
            # Organic blob
            points = []
            for a in range(0, 360, 10):
                angle = a * math.pi / 180
                r = 50 + 15 * math.sin(a * 0.1)
                points.append((cx + int(r * math.cos(angle)), cy + int(r * math.sin(angle))))
            draw.polygon(points, fill=(60, 180, 120))
        
        elif lang["shape"] == "geometric":
            # Neon geometric
            for i in range(6):
                angle = i * math.pi / 3
                x1 = cx + int(40 * math.cos(angle))
                y1 = cy + int(40 * math.sin(angle))
                x2 = cx + int(40 * math.cos(angle + math.pi / 3))
                y2 = cy + int(40 * math.sin(angle + math.pi / 3))
                draw.line([(x1, y1), (x2, y2)], fill=(180, 40, 120), width=3)
        
        elif lang["shape"] == "brutalist":
            # Brutalist blocks
            draw.rectangle([cx - 60, cy - 40, cx + 60, cy + 40], fill=(80, 80, 85))
            draw.rectangle([cx - 40, cy - 25, cx + 40, cy + 25], fill=(60, 60, 65))
            draw.rectangle([cx - 20, cy - 10, cx + 20, cy + 10], fill=(100, 100, 105))
        
        # Label
        draw.text((x0 + 10, y0 + cell_h - 25), lang["name"], fill=(200, 200, 210))
    
    fp = os.path.join(OUT, "creative_range_gallery.png")
    img.save(fp)
    print(f"  Gallery: 6 Visual Languages — {W}x{H}")
    return fp

# ============================================================
# MAIN
# ============================================================
def main():
    print("=== ORIGINAL WORLD + CREATIVE RANGE ===\n")
    
    create_world_bible()
    create_veridian_character()
    create_veridian_environment()
    create_creative_range_gallery()
    
    report = {
        "original_world": {
            "name": VERIDIAN_WORLD["name"],
            "concept": VERIDIAN_WORLD["concept"],
            "assets_created": ["character", "environment", "art_bible"],
            "coherence": "Bioluminescent palette, organic forms, underwater atmosphere, light-as-language",
        },
        "creative_range": {
            "languages_demonstrated": 6,
            "mediums": ["procedural", "generative", "composited"],
            "coherence_test": "Each language has distinct shape, color, material, and mood",
        },
    }
    
    with open(os.path.join(OUT, "world_report.json"), "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\n=== COMPLETE ===")

if __name__ == "__main__":
    main()
