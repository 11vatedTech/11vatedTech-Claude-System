"""STYLE DNA SYSTEM + ORIGINAL STYLE INVENTION #1: LITHIC DREAMS."""
import os, json, math, colorsys
from PIL import Image, ImageDraw, ImageFilter
import numpy as np

OUT = "artifacts/visual/style-dna"
os.makedirs(OUT, exist_ok=True)

# ============================================================
# STYLE DNA DEFINITION
# ============================================================
STYLE_DNA_SCHEMA = {
    "form": ["geometric", "organic", "mixed"],
    "curvature": ["angular", "flowing", "mixed"],
    "proportion": ["natural", "exaggerated_tall", "exaggerated_wide", "compact"],
    "line": ["absent", "uniform", "variable", "broken", "engraved", "gestural"],
    "value": ["compressed", "graphic", "naturalistic", "dramatic"],
    "color": ["limited", "muted", "saturated", "spectral", "complementary", "analogous"],
    "edge": ["hard", "soft", "lost_and_found", "pixel_defined"],
    "material": ["graphic", "painterly", "tactile", "physical", "synthetic"],
    "mark": ["brush", "hatch", "stipple", "vector", "pixel", "procedural"],
    "light": ["flat", "natural", "theatrical", "volumetric", "internal"],
    "space": ["flattened", "orthographic", "perspective", "layered", "impossible"],
    "detail": ["sparse", "focal", "distributed", "ornamental"],
    "abstraction": ["representational", "semi_abstract", "abstract"],
    "motion": ["snappy", "heavy", "elastic", "drifting", "mechanical", "organic"],
    "mood": ["serene", "tense", "mysterious", "joyful", "melancholic", "aggressive", "ethereal"],
    "era_influence": ["none", "ancient", "medieval", "industrial", "modern", "futuristic", "timeless"],
}

# ============================================================
# ORIGINAL STYLE #1: LITHIC DREAMS
# Concept: Memory as geological strata — forms emerge from layered stone
# ============================================================
LITHIC_DREAMS = {
    "name": "Lithic Dreams",
    "concept": "Memory is geological. Forms crystallize from compressed time. Thought has weight and erosion.",
    "thesis": "All visual elements suggest geological processes: stratification, crystallization, erosion, compression.",
    "dna": {
        "form": "mixed — organic masses with crystalline fractures",
        "curvature": "angular with eroded edges",
        "proportion": "exaggerated_tall — forms reach upward like stalagmites",
        "line": "variable — thick stratification lines, thin crack lines",
        "value": "dramatic — deep shadows in crevices, bright highlights on facets",
        "color": "limited — slate blues, warm ochres, crystalline whites, deep blacks",
        "edge": "lost_and_found — faces dissolve into shadow, edges catch light",
        "material": "tactile — rough stone, smooth crystal, powdery sediment",
        "mark": "hatch — parallel strata lines, cross-hatch in shadows",
        "light": "theatrical — single directional light creating deep shadow",
        "space": "layered — foreground/midground/background as geological layers",
        "detail": "focal — detail concentrated at crystal faces and erosion points",
        "abstraction": "semi_abstract — recognizable forms emerge from abstract strata",
        "motion": "heavy — slow, weighted, gravitational",
        "mood": "mysterious — ancient, contemplative, slightly unsettling",
        "era_influence": "ancient — geological time, pre-human landscapes",
    },
    "palette": {
        "dominant": (65, 75, 90),      # Slate blue
        "secondary": (160, 130, 80),   # Warm ochre
        "accent": (200, 210, 220),     # Crystalline white
        "deep": (25, 28, 35),          # Deep shadow
        "highlight": (230, 225, 215),  # Facet highlight
    },
    "shape_language": {
        "primary": "triangular/crystalline — upward-pointing forms",
        "secondary": "horizontal strata — layered masses",
        "tertiary": "fracture lines — angular subdivisions within masses",
    },
}

def create_style_dna_document():
    """Create the Style DNA reference document."""
    print("--- Creating Style DNA Document ---")
    
    doc = {
        "schema": STYLE_DNA_SCHEMA,
        "description": "Style DNA is a multi-dimensional representation for describing and generating visual languages without requiring named existing styles.",
        "dimensions": len(STYLE_DNA_SCHEMA),
        "example": LITHIC_DREAMS,
        "usage": "Select values for each dimension. The combination defines a unique visual language. Cross-medium transfer preserves DNA values while adapting execution to each medium.",
    }
    
    with open(os.path.join(OUT, "style_dna_schema.json"), "w") as f:
        json.dump(doc, f, indent=2)
    
    print(f"  Schema: {len(STYLE_DNA_SCHEMA)} dimensions")
    print(f"  Example: {LITHIC_DREAMS['name']}")
    return True

def create_lithic_dreams_character():
    """Create a character in the Lithic Dreams style using SVG/Canvas (no diffusion)."""
    print("\n--- Lithic Dreams: Character Design ---")
    
    W, H = 800, 1000
    img = Image.new("RGB", (W, H), (25, 28, 35))
    draw = ImageDraw.Draw(img)
    
    palette = LITHIC_DREAMS["palette"]
    
    # Character: "Stratum Keeper" — a being made of geological layers
    cx, cy = W // 2, H // 2
    
    # Base form: tall triangular silhouette (stalagmite-like)
    # Body mass — layered horizontal strata
    strata = [
        (0, 80, 160, (65, 75, 90)),      # Base: wide slate
        (20, 60, 140, (80, 90, 100)),     # Layer 2
        (30, 40, 120, (100, 105, 110)),   # Layer 3
        (35, 20, 100, (120, 115, 105)),   # Layer 4
        (40, 0, 80, (140, 130, 110)),     # Upper body
        (45, -20, 60, (160, 145, 115)),   # Shoulders
        (50, -50, 40, (180, 165, 130)),   # Neck area
    ]
    
    for x_off, y_off, width, color in strata:
        y_top = cy + y_off - 40
        y_bot = cy + y_off + 30
        draw.polygon([
            (cx - width, y_top),
            (cx + width, y_top),
            (cx + width - 10, y_bot),
            (cx - width + 10, y_bot),
        ], fill=color)
    
    # Head: crystalline formation
    head_cx, head_cy = cx, cy - 100
    # Main crystal
    draw.polygon([
        (head_cx, head_cy - 60),
        (head_cx + 35, head_cy - 10),
        (head_cx + 25, head_cy + 30),
        (head_cx - 25, head_cy + 30),
        (head_cx - 35, head_cy - 10),
    ], fill=palette["accent"])
    
    # Crystal facets (darker for depth)
    draw.polygon([
        (head_cx, head_cy - 60),
        (head_cx + 35, head_cy - 10),
        (head_cx + 5, head_cy - 5),
    ], fill=(180, 190, 200))
    
    # Eyes: glowing ochre
    draw.ellipse([head_cx - 12, head_cy - 5, head_cx - 4, head_cy + 3], fill=palette["secondary"])
    draw.ellipse([head_cx + 4, head_cy - 5, head_cx + 12, head_cy + 3], fill=palette["secondary"])
    
    # Arms: extending from strata
    # Left arm — angular crystal branch
    draw.polygon([
        (cx - 50, cy - 30),
        (cx - 120, cy - 60),
        (cx - 130, cy - 50),
        (cx - 60, cy - 20),
    ], fill=(100, 105, 110))
    
    # Right arm
    draw.polygon([
        (cx + 50, cy - 30),
        (cx + 120, cy - 60),
        (cx + 130, cy - 50),
        (cx + 60, cy - 20),
    ], fill=(100, 105, 110))
    
    # Fracture lines across body
    for i in range(5):
        y = cy - 40 + i * 25
        x_start = cx - 140 + i * 10
        x_end = cx + 140 - i * 10
        draw.line([(x_start, y), (x_end, y)], fill=(40, 45, 55), width=1)
    
    # Hatch marks in shadow areas
    for i in range(20):
        x = cx - 100 + i * 10
        y = cy + 40
        draw.line([(x, y), (x + 5, y + 15)], fill=(35, 38, 45), width=1)
    
    # Ground strata
    for y in range(cy + 120, H, 8):
        v = int(50 + (y - cy - 120) * 0.1)
        draw.line([(0, y), (W, y)], fill=(v, v + 5, v + 10), width=2)
    
    fp = os.path.join(OUT, "lithic_character.png")
    img.save(fp)
    print(f"  Character: Stratum Keeper — {W}x{H}")
    return fp

def create_lithic_dreams_environment():
    """Create an environment in the Lithic Dreams style."""
    print("\n--- Lithic Dreams: Environment ---")
    
    W, H = 1200, 800
    img = Image.new("RGB", (W, H), (20, 22, 30))
    draw = ImageDraw.Draw(img)
    
    palette = LITHIC_DREAMS["palette"]
    
    # Sky: deep gradient
    for y in range(H // 2):
        t = y / (H // 2)
        r = int(20 + 30 * t)
        g = int(22 + 25 * t)
        b = int(35 + 30 * t)
        draw.line([(0, y), (W, y)], fill=(r, g, b))
    
    # Geological layers (background mountains)
    layers = [
        (0.3, (50, 55, 65)),    # Far mountains
        (0.5, (60, 65, 75)),    # Mid mountains
        (0.7, (75, 80, 85)),    # Near hills
    ]
    
    for layer_y, color in layers:
        points = []
        for x in range(0, W + 20, 20):
            y = int(H * layer_y + 50 * math.sin(x * 0.008) + 30 * math.sin(x * 0.015 + 1))
            points.append((x, y))
        points.append((W, H))
        points.append((0, H))
        draw.polygon(points, fill=color)
    
    # Crystal formations in midground
    crystals = [(200, 450), (500, 400), (800, 430), (1000, 460)]
    for cx, cy in crystals:
        h = np.random.randint(80, 180)
        w = np.random.randint(20, 50)
        # Crystal body
        draw.polygon([
            (cx, cy - h),
            (cx + w, cy),
            (cx + w - 5, cy + 20),
            (cx - w + 5, cy + 20),
            (cx - w, cy),
        ], fill=palette["accent"])
        # Facet shadow
        draw.polygon([
            (cx, cy - h),
            (cx + w, cy),
            (cx + 5, cy - h // 2),
        ], fill=(160, 170, 180))
    
    # Foreground strata
    for y in range(600, H, 6):
        v = int(40 + (y - 600) * 0.15)
        offset = int(10 * math.sin(y * 0.05))
        draw.line([(0, y), (W, y)], fill=(v + offset, v + offset + 5, v + offset + 10), width=2)
    
    # Atmospheric particles (dust/crystal fragments)
    np.random.seed(42)
    for _ in range(100):
        x = np.random.randint(0, W)
        y = np.random.randint(100, 500)
        size = np.random.randint(1, 4)
        v = np.random.randint(150, 220)
        draw.ellipse([x-size, y-size, x+size, y+size], fill=(v, v, v+10))
    
    fp = os.path.join(OUT, "lithic_environment.png")
    img.save(fp)
    print(f"  Environment: Crystal Strata Landscape — {W}x{H}")
    return fp

def create_lithic_dreams_prop():
    """Create a prop in the Lithic Dreams style."""
    print("\n--- Lithic Dreams: Prop Design ---")
    
    W, H = 600, 600
    img = Image.new("RGB", (W, H), (30, 32, 40))
    draw = ImageDraw.Draw(img)
    
    palette = LITHIC_DREAMS["palette"]
    
    # Prop: "Memory Stone" — a crystalline artifact with layered inscriptions
    cx, cy = W // 2, H // 2
    
    # Outer form: irregular crystal
    points = [
        (cx, cy - 150),      # Top peak
        (cx + 80, cy - 100), # Right upper
        (cx + 100, cy - 20), # Right mid
        (cx + 70, cy + 60),  # Right lower
        (cx + 30, cy + 120), # Bottom right
        (cx - 30, cy + 120), # Bottom left
        (cx - 70, cy + 60),  # Left lower
        (cx - 100, cy - 20), # Left mid
        (cx - 80, cy - 100), # Left upper
    ]
    draw.polygon(points, fill=palette["dominant"])
    
    # Inner strata lines
    for i in range(8):
        y = cy - 80 + i * 25
        w = 60 - abs(i - 4) * 8
        draw.line([(cx - w, y), (cx + w, y)], fill=(40, 45, 55), width=2)
    
    # Crystal face highlights
    draw.polygon([
        (cx, cy - 150),
        (cx + 40, cy - 80),
        (cx + 10, cy - 70),
    ], fill=palette["highlight"])
    
    draw.polygon([
        (cx, cy - 150),
        (cx - 40, cy - 80),
        (cx - 10, cy - 70),
    ], fill=(190, 200, 210))
    
    # Central ochre vein
    draw.line([(cx - 5, cy - 120), (cx + 5, cy + 80)], fill=palette["secondary"], width=4)
    
    # Glow around crystal
    glow = Image.new("RGB", (W, H), (0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    for r in range(200, 0, -2):
        v = int(30 * (r / 200))
        glow_draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill=(v, v, v+5))
    glow = glow.filter(ImageFilter.GaussianBlur(radius=20))
    
    # Blend glow
    arr = np.array(img, dtype=np.float32)
    glow_arr = np.array(glow, dtype=np.float32)
    result = np.clip(arr + glow_arr * 0.5, 0, 255).astype(np.uint8)
    img = Image.fromarray(result)
    
    fp = os.path.join(OUT, "lithic_prop.png")
    img.save(fp)
    print(f"  Prop: Memory Stone — {W}x{H}")
    return fp

def create_lithic_dreams_ui():
    """Create a UI element in the Lithic Dreams style."""
    print("\n--- Lithic Dreams: UI Element ---")
    
    W, H = 800, 400
    img = Image.new("RGB", (W, H), (20, 22, 28))
    draw = ImageDraw.Draw(img)
    
    palette = LITHIC_DREAMS["palette"]
    
    # UI: Health/Mana bar styled as geological strata
    bar_x, bar_y = 100, 80
    bar_w, bar_h = 600, 40
    
    # Background strata
    for y in range(bar_y, bar_y + bar_h):
        t = (y - bar_y) / bar_h
        v = int(40 + 20 * t)
        draw.line([(bar_x, y), (bar_x + bar_w, y)], fill=(v, v + 5, v + 10))
    
    # Fill level (60%)
    fill_w = int(bar_w * 0.6)
    for y in range(bar_y, bar_y + bar_h):
        t = (y - bar_y) / bar_h
        v = int(80 + 40 * (1 - t))
        draw.line([(bar_x, y), (bar_x + fill_w, y)], fill=(v, int(v * 0.9), int(v * 0.7)))
    
    # Crystal markers at 25%, 50%, 75%
    for pct in [0.25, 0.5, 0.75]:
        x = bar_x + int(bar_w * pct)
        draw.polygon([
            (x, bar_y - 8),
            (x + 5, bar_y),
            (x - 5, bar_y),
        ], fill=palette["accent"])
    
    # Border: crystalline edges
    draw.line([(bar_x, bar_y), (bar_x + bar_w, bar_y)], fill=palette["accent"], width=2)
    draw.line([(bar_x, bar_y + bar_h), (bar_x + bar_w, bar_y + bar_h)], fill=palette["accent"], width=2)
    
    # Label
    draw.text((bar_x, bar_y + bar_h + 15), "MEMORY STRATA", fill=palette["accent"])
    draw.text((bar_x + bar_w - 50, bar_y + bar_h + 15), "60%", fill=palette["secondary"])
    
    fp = os.path.join(OUT, "lithic_ui.png")
    img.save(fp)
    print(f"  UI: Memory Strata Bar — {W}x{H}")
    return fp

def create_lithic_dreams_motion_frame():
    """Create a motion study frame in the Lithic Dreams style."""
    print("\n--- Lithic Dreams: Motion Study ---")
    
    W, H = 800, 600
    img = Image.new("RGB", (W, H), (20, 22, 30))
    draw = ImageDraw.Draw(img)
    
    palette = LITHIC_DREAMS["palette"]
    
    # Motion: "Crystallization" — forms emerging from strata
    # Multiple frames overlaid with transparency
    frames = 5
    for f in range(frames):
        alpha = int(60 + 40 * (f / frames))
        y_offset = f * 20
        
        # Crystal growing from ground
        cx = W // 2 + f * 15
        cy = H - 100 - y_offset
        
        h = 50 + f * 30
        w = 15 + f * 5
        
        color = tuple(int(palette["accent"][i] * (alpha / 255)) for i in range(3))
        bg = tuple(int(20 + (palette["dominant"][i] - 20) * (alpha / 255)) for i in range(3))
        
        # Merged color
        final = tuple(min(255, palette["dominant"][i] + int((palette["accent"][i] - palette["dominant"][i]) * f / frames)) for i in range(3))
        
        draw.polygon([
            (cx, cy - h),
            (cx + w, cy),
            (cx - w, cy),
        ], fill=final)
    
    # Strata lines (static background)
    for y in range(H - 80, H, 6):
        v = int(40 + (y - (H-80)) * 0.3)
        draw.line([(0, y), (W, y)], fill=(v, v + 5, v + 10), width=1)
    
    # Motion lines
    for i in range(8):
        x = W // 2 - 60 + i * 15
        y1 = H - 80
        y2 = H - 150 - i * 10
        draw.line([(x, y1), (x, y2)], fill=(50, 55, 65), width=1)
    
    fp = os.path.join(OUT, "lithic_motion.png")
    img.save(fp)
    print(f"  Motion: Crystallization — {W}x{H}")
    return fp

# ============================================================
# MAIN
# ============================================================
def main():
    print("=== STYLE DNA + ORIGINAL STYLE INVENTION ===\n")
    
    create_style_dna_document()
    create_lithic_dreams_character()
    create_lithic_dreams_environment()
    create_lithic_dreams_prop()
    create_lithic_dreams_ui()
    create_lithic_dreams_motion_frame()
    
    # Write report
    report = {
        "style_dna": {
            "dimensions": len(STYLE_DNA_SCHEMA),
            "schema_created": True,
        },
        "original_style_1": {
            "name": LITHIC_DREAMS["name"],
            "concept": LITHIC_DREAMS["concept"],
            "thesis": LITHIC_DREAMS["thesis"],
            "mediums_created": ["character", "environment", "prop", "UI", "motion"],
            "coherence": "All share slate blue/ochre/white palette, crystalline/strata shapes, geological texture, theatrical light",
        },
    }
    
    with open(os.path.join(OUT, "style_dna_report.json"), "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\n=== COMPLETE ===")

if __name__ == "__main__":
    main()
