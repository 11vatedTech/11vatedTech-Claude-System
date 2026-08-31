"""ORIGINAL STYLE #2: AETHERWEAVE + GENERATOR-RESTRICTED HIGH-FIDELITY ARTWORK."""
import os, json, math
from PIL import Image, ImageDraw, ImageFilter
import numpy as np

OUT = "artifacts/visual/style-dna"
os.makedirs(OUT, exist_ok=True)

# ============================================================
# ORIGINAL STYLE #2: AETHERWEAVE
# Concept: Sound as visible fabric — music creates physical woven structures
# ============================================================
AETHERWEAVE = {
    "name": "Aetherweave",
    "concept": "Sound is tangible. Music weaves physical structures. Resonance creates architecture.",
    "thesis": "All forms emerge from wave interference patterns. Material is frozen sound.",
    "dna": {
        "form": "organic — wave-derived curves, interference patterns",
        "curvature": "flowing — sinusoidal, harmonic",
        "proportion": "natural with rhythmic variation",
        "line": "variable — thickness follows amplitude",
        "value": "compressed — mid-tone dominant, subtle gradients",
        "color": "analogous — warm amber to cool teal spectrum",
        "edge": "soft — wave-like transitions, no hard breaks",
        "material": "synthetic — light-based, translucent, luminous",
        "mark": "procedural — wave functions, interference",
        "light": "internal — forms glow from within",
        "space": "layered — wave叠加 creating depth",
        "detail": "distributed — pattern emerges from repetition",
        "abstraction": "semi_abstract — wave forms suggest but don't depict",
        "motion": "elastic — spring-like, harmonic oscillation",
        "mood": "ethereal — dreamlike, contemplative, musical",
        "era_influence": "futuristic — beyond physical materials",
    },
    "palette": {
        "dominant": (40, 60, 80),       # Deep teal
        "secondary": (180, 140, 60),    # Warm amber
        "accent": (220, 200, 160),      # Soft gold
        "deep": (15, 20, 30),           # Deep space
        "glow": (100, 180, 200),        # Luminous cyan
    },
}

# ============================================================
# ORIGINAL STYLE #3: GRAPHITE DUSK
# Concept: Twilight rendered through traditional drawing media
# ============================================================
GRAPHITE_DUSK = {
    "name": "Graphite Dusk",
    "concept": "The moment between day and night, rendered as if drawn by hand with graphite and charcoal.",
    "thesis": "All forms emerge from hand-drawn mark-making. Digital meets traditional draftsmanship.",
    "dna": {
        "form": "organic — hand-drawn quality, slight imperfection",
        "curvature": "mixed — controlled but with natural variation",
        "proportion": "natural — observational accuracy",
        "line": "variable — weight follows pressure, gesture visible",
        "value": "naturalistic — full range from paper white to deep charcoal",
        "color": "muted — near-monochrome with warm undertones",
        "edge": "lost_and_found — edges emerge from value, not outline",
        "material": "tactile — graphite grain, paper texture, charcoal smudge",
        "mark": "hatch — visible hatching, cross-hatching, tonal rubbing",
        "light": "natural — twilight quality, soft directional",
        "space": "perspective — atmospheric depth through value",
        "detail": "focal — detailed at focus, suggestive elsewhere",
        "abstraction": "representational — recognizable but painterly",
        "motion": "organic — fluid, hand-drawn quality",
        "mood": "melancholic — quiet, contemplative, intimate",
        "era_influence": "timeless — classical drawing tradition",
    },
    "palette": {
        "dominant": (80, 75, 70),       # Warm graphite
        "secondary": (140, 130, 120),   # Light graphite
        "accent": (200, 190, 175),      # Paper tone
        "deep": (25, 22, 20),           # Deep charcoal
        "warm": (120, 100, 80),         # Warm undertone
    },
}

def create_aetherweave_character():
    """Create a character in the Aetherweave style."""
    print("--- Aetherweave: Character Design ---")
    
    W, H = 800, 1000
    img = Image.new("RGB", (W, H), (15, 20, 30))
    draw = ImageDraw.Draw(img)
    
    palette = AETHERWEAVE["palette"]
    cx, cy = W // 2, H // 2
    
    # Character: "Resonance Weaver" — a being made of sound waves
    # Body: wave-derived form
    for i in range(20):
        y = cy - 150 + i * 15
        amplitude = 60 + 30 * math.sin(i * 0.3)
        wavelength = 0.05 + 0.01 * math.sin(i * 0.2)
        
        points = []
        for x in range(cx - int(amplitude), cx + int(amplitude), 5):
            wave_y = y + int(10 * math.sin(x * wavelength + i * 0.5))
            points.append((x, wave_y))
        
        if len(points) > 1:
            t = i / 20
            r = int(palette["dominant"][0] + (palette["secondary"][0] - palette["dominant"][0]) * t)
            g = int(palette["dominant"][1] + (palette["secondary"][1] - palette["dominant"][1]) * t)
            b = int(palette["dominant"][2] + (palette["secondary"][2] - palette["dominant"][2]) * t)
            for j in range(len(points) - 1):
                draw.line([points[j], points[j + 1]], fill=(r, g, b), width=3)
    
    # Head: interference pattern sphere
    head_cx, head_cy = cx, cy - 180
    for r in range(50, 0, -1):
        t = r / 50
        wave = math.sin(r * 0.3) * 0.3 + 0.7
        v = int(palette["glow"][0] * wave * (1 - t * 0.5))
        g = int(palette["glow"][1] * wave * (1 - t * 0.5))
        b = int(palette["glow"][2] * wave * (1 - t * 0.5))
        draw.ellipse([head_cx - r, head_cy - r, head_cx + r, head_cy + r], fill=(v, g, b))
    
    # Arms: extending wave forms
    for side in [-1, 1]:
        for i in range(15):
            x = cx + side * (60 + i * 8)
            y = cy - 100 + i * 10
            wave_x = int(10 * math.sin(i * 0.5))
            r = max(1, 4 - i // 4)
            draw.ellipse([x + wave_x - r, y - r, x + wave_x + r, y + r], fill=palette["accent"])
    
    # Ground: wave interference pattern
    for y in range(cy + 100, H, 4):
        for x in range(0, W, 4):
            wave1 = math.sin(x * 0.02 + y * 0.01) * 0.5
            wave2 = math.sin(x * 0.015 - y * 0.008) * 0.5
            interference = (wave1 + wave2) * 0.5 + 0.5
            v = int(30 * interference)
            draw.rectangle([x, y, x + 3, y + 3], fill=(v, v + 5, v + 10))
    
    fp = os.path.join(OUT, "aetherweave_character.png")
    img.save(fp)
    print(f"  Character: Resonance Weaver — {W}x{H}")
    return fp

def create_graphite_dusk_character():
    """Create a character in the Graphite Dusk style."""
    print("\n--- Graphite Dusk: Character Design ---")
    
    W, H = 800, 1000
    # Paper tone background
    img = Image.new("RGB", (W, H), (200, 190, 175))
    draw = ImageDraw.Draw(img)
    
    palette = GRAPHITE_DUSK["palette"]
    cx, cy = W // 2, H // 2
    
    # Add paper texture
    np.random.seed(42)
    for _ in range(5000):
        x = np.random.randint(0, W)
        y = np.random.randint(0, H)
        v = np.random.randint(-10, 10)
        draw.point((x, y), fill=(200 + v, 190 + v, 175 + v))
    
    # Character: "Twilight Wanderer" — a figure in graphite
    # Head
    head_cx, head_cy = cx, cy - 180
    draw.ellipse([head_cx - 35, head_cy - 45, head_cx + 35, head_cy + 25], fill=(60, 55, 50))
    
    # Hair: gestural strokes
    for i in range(20):
        angle = -0.5 + i * 0.05
        x1 = head_cx + int(30 * math.cos(angle))
        y1 = head_cy - 40
        x2 = head_cx + int(50 * math.cos(angle))
        y2 = head_cy - 60 + int(20 * math.sin(angle))
        draw.line([(x1, y1), (x2, y2)], fill=(40, 35, 30), width=2)
    
    # Body: gestural form
    body_points = [
        (cx - 40, cy - 150),
        (cx + 40, cy - 150),
        (cx + 50, cy),
        (cx + 30, cy + 100),
        (cx - 30, cy + 100),
        (cx - 50, cy),
    ]
    draw.polygon(body_points, fill=(70, 65, 55))
    
    # Hatching in shadow areas
    for i in range(30):
        x = cx + 20 + i * 2
        y1 = cy - 100 + i * 5
        y2 = y1 + 20
        draw.line([(x, y1), (x + 3, y2)], fill=(50, 45, 40), width=1)
    
    # Cross-hatching in deeper shadow
    for i in range(15):
        x = cx + 30 + i * 3
        y1 = cy + 20 + i * 4
        y2 = y1 + 15
        draw.line([(x + 5, y1), (x, y2)], fill=(40, 35, 30), width=1)
    
    # Arms: gestural lines
    draw.line([(cx - 40, cy - 130), (cx - 100, cy - 80)], fill=(50, 45, 40), width=3)
    draw.line([(cx + 40, cy - 130), (cx + 100, cy - 80)], fill=(50, 45, 40), width=3)
    
    # Legs
    draw.line([(cx - 20, cy + 100), (cx - 30, cy + 200)], fill=(50, 45, 40), width=4)
    draw.line([(cx + 20, cy + 100), (cx + 30, cy + 200)], fill=(50, 45, 40), width=4)
    
    # Smudge effect (blurred charcoal)
    smudge = img.filter(ImageFilter.GaussianBlur(radius=2))
    arr = np.array(img, dtype=np.float32)
    smudge_arr = np.array(smudge, dtype=np.float32)
    # Blend 85% sharp + 15% smudge
    result = (arr * 0.85 + smudge_arr * 0.15).clip(0, 255).astype(np.uint8)
    img = Image.fromarray(result)
    
    fp = os.path.join(OUT, "graphite_dusk_character.png")
    img.save(fp)
    print(f"  Character: Twilight Wanderer — {W}x{H}")
    return fp

def create_generator_restricted_artwork():
    """Create high-fidelity artwork using ONLY deterministic methods (no diffusion)."""
    print("\n--- Generator-Restricted High-Fidelity Artwork ---")
    print("  Method: Canvas2D procedural + compositing (NO diffusion)")
    
    W, H = 1200, 800
    img = Image.new("RGB", (W, H), (0, 0, 0))
    
    # Title: "CONVERGENCE" — an original composition
    # Concept: Multiple wave systems converging at a focal point
    
    # Layer 1: Deep space background
    np.random.seed(42)
    arr = np.zeros((H, W, 3), dtype=np.float32)
    
    # Starfield
    for _ in range(200):
        x = np.random.randint(0, W)
        y = np.random.randint(0, H)
        brightness = np.random.uniform(0.3, 1.0)
        size = np.random.randint(1, 3)
        arr[max(0,y-size):min(H,y+size), max(0,x-size):min(W,x+size)] = brightness * np.array([0.8, 0.85, 1.0])
    
    # Layer 2: Wave systems
    for wave_i in range(3):
        frequency = 0.01 + wave_i * 0.005
        amplitude = 100 + wave_i * 50
        phase = wave_i * 2.0
        color = np.array([
            [0.2, 0.4, 0.8],   # Blue
            [0.8, 0.4, 0.2],   # Orange
            [0.2, 0.8, 0.4],   # Green
        ][wave_i])
        
        for x in range(W):
            for y in range(H):
                # Distance from convergence point
                dx = x - W * 0.6
                dy = y - H * 0.4
                dist = math.sqrt(dx**2 + dy**2)
                
                # Wave function
                wave = math.sin(dist * frequency + phase) * 0.5 + 0.5
                
                # Fade with distance
                fade = max(0, 1 - dist / (W * 0.5))
                
                # Add to image
                intensity = wave * fade * 0.3
                arr[y, x] = np.clip(arr[y, x] + color * intensity, 0, 1)
    
    # Layer 3: Central convergence glow
    cx, cy = int(W * 0.6), int(H * 0.4)
    for r in range(150, 0, -1):
        t = r / 150
        intensity = (1 - t) ** 2 * 0.8
        y_start = max(0, cy - r)
        y_end = min(H, cy + r)
        x_start = max(0, cx - r)
        x_end = min(W, cx + r)
        
        for y in range(y_start, y_end):
            for x in range(x_start, x_end):
                d = math.sqrt((x - cx)**2 + (y - cy)**2)
                if d < r:
                    fade = 1 - d / r
                    arr[y, x] = np.clip(arr[y, x] + np.array([0.9, 0.8, 0.6]) * intensity * fade, 0, 1)
    
    # Convert to uint8
    arr = (arr * 255).clip(0, 255).astype(np.uint8)
    img = Image.fromarray(arr)
    
    # Layer 4: Geometric overlay (deterministic SVG-like shapes)
    draw = ImageDraw.Draw(img)
    
    # Convergence lines
    for i in range(12):
        angle = i * math.pi / 6
        x1 = cx + int(200 * math.cos(angle))
        y1 = cy + int(200 * math.sin(angle))
        x2 = cx + int(400 * math.cos(angle))
        y2 = cy + int(400 * math.sin(angle))
        draw.line([(x1, y1), (x2, y2)], fill=(100, 120, 150), width=1)
    
    # Central symbol
    for r in range(30, 0, -1):
        v = int(200 * (r / 30))
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(v, v, v))
    
    # Title text
    draw.text((W // 2 - 80, H - 60), "CONVERGENCE", fill=(180, 180, 200))
    draw.text((W // 2 - 100, H - 40), "Procedural + Composited", fill=(100, 100, 120))
    
    fp = os.path.join(OUT, "generator_restricted_artwork.png")
    img.save(fp)
    print(f"  Artwork: CONVERGENCE — {W}x{H} (NO diffusion used)")
    return fp

# ============================================================
# MAIN
# ============================================================
def main():
    print("=== ORIGINAL STYLES + GENERATOR-RESTRICTED ART ===\n")
    
    create_aetherweave_character()
    create_graphite_dusk_character()
    create_generator_restricted_artwork()
    
    report = {
        "original_style_2": {
            "name": AETHERWEAVE["name"],
            "concept": AETHERWEAVE["concept"],
            "thesis": AETHERWEAVE["thesis"],
            "mediums_created": ["character"],
            "coherence": "Wave-derived forms, luminous materials, harmonic motion, warm amber + cool teal palette",
        },
        "original_style_3": {
            "name": GRAPHITE_DUSK["name"],
            "concept": GRAPHITE_DUSK["concept"],
            "thesis": GRAPHITE_DUSK["thesis"],
            "mediums_created": ["character"],
            "coherence": "Hand-drawn quality, visible hatching, lost-and-found edges, monochrome with warm undertones",
        },
        "generator_restricted": {
            "title": "CONVERGENCE",
            "method": "Canvas2D procedural + compositing",
            "diffusion_used": False,
            "components": ["starfield", "wave systems", "central glow", "geometric overlay"],
        },
    }
    
    with open(os.path.join(OUT, "styles_v2_report.json"), "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\n=== COMPLETE ===")

if __name__ == "__main__":
    main()
