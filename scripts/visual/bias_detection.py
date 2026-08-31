"""TOOL-AESTHETIC BIAS DETECTION + ART-DIRECTED GENERATIVE ARTWORK."""
import os, json, math
from PIL import Image, ImageDraw, ImageFilter
import numpy as np

OUT = "artifacts/visual/creative-cognition"
os.makedirs(OUT, exist_ok=True)

# ============================================================
# TOOL-AESTHETIC BIAS ANALYSIS
# ============================================================
TOOL_BIASES = {
    "DreamShaper_8": {
        "signature": "Fantasy倾向, soft glow, centered composition, dramatic lighting, generic beauty",
        "strengths": "Character concept, fantasy atmosphere, painterly quality",
        "weaknesses": "Generic faces, over-glow, center-weighted composition, lack of specificity",
        "detection": "Check for: centered subject, dramatic backlight, soft glow halo, generic fantasy elements",
        "counter_strategy": "Specify exact composition, reject center-weighting, demand specific而不是generic elements",
    },
    "DreamShaper_XL": {
        "signature": "Higher detail, more photographic tendency, stronger material rendering",
        "strengths": "Material quality, detail density, environment atmosphere",
        "weaknesses": "Can become over-detailed, photorealism bias, less stylized control",
        "detection": "Check for: over-rendering, photorealism creep, loss of intentional style",
        "counter_strategy": "Specify style DNA explicitly, reject photorealism when not intended",
    },
    "SVG": {
        "signature": "Flat construction, geometric shapes, clean edges, limited gradients",
        "strengths": "Precision, scalability, identity, technical graphics",
        "weaknesses": "Can look flat/childlike if not designed, limited material suggestion",
        "detection": "Check for: over-simplification, loss of depth, generic icon aesthetic",
        "counter_strategy": "Use layering, gradient economy, sophisticated shape language",
    },
    "CSS": {
        "signature": "Box model thinking, gradient-heavy, shadow-dependent, responsive grid",
        "strengths": "Layout precision, typography, interactive states",
        "weaknesses": "Generic SaaS aesthetic, gradient overuse, shadow dependency",
        "detection": "Check for: gradient backgrounds, box shadows, generic card layouts",
        "counter_strategy": "Subvert grid expectations, use unconventional layouts, limit gradients",
    },
    "WebGL_Shader": {
        "signature": "Mathematical patterns, noise-based, infinite detail, procedural aesthetic",
        "strengths": "Originality, material exploration, motion, infinite resolution",
        "weaknesses": "Can become demo-quality, lack of compositional intent, noise-as-fidelity",
        "detection": "Check for: random noise patterns, demo aesthetic, lack of focal hierarchy",
        "counter_strategy": "Apply compositional rules, create focal hierarchy, intentional color",
    },
    "Blender": {
        "signature": "Physical accuracy, realistic materials, studio lighting, product render aesthetic",
        "strengths": "Geometry accuracy, material quality, lighting control",
        "weaknesses": "Can become generic 3D render, lack of artistic voice, over-physical",
        "detection": "Check for: generic studio lighting, perfect materials, lack of stylization",
        "counter_strategy": "Stylize materials, use unconventional lighting, add artistic imperfection",
    },
}

def create_bias_report():
    """Create tool-aesthetic bias detection report."""
    print("--- Tool-Aesthetic Bias Detection ---")
    
    report = {
        "biases": TOOL_BIASES,
        "detection_method": "Compare output against known tool signatures. If output matches signature, tool is dictating aesthetic.",
        "counter_strategy": "Specify art direction BEFORE tool selection. Reject outputs that match tool signature without artistic intent.",
        "quality_gate": "If output could be produced by a generic prompt without art direction, reject.",
    }
    
    with open(os.path.join(OUT, "bias_detection.json"), "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"  Analyzed {len(TOOL_BIASES)} tools")
    return report

def create_art_directed_generation():
    """Create art-directed generative artwork — art direction designed first, then generator used as tool."""
    print("\n--- Art-Directed Generative Artwork ---")
    print("  Method: Design art direction → Execute with procedural methods (no diffusion)")
    
    W, H = 1200, 800
    img = Image.new("RGB", (W, H), (0, 0, 0))
    
    # Art Direction (designed before execution):
    # Composition: Asymmetric, focal at golden ratio intersection
    # Value: High contrast, deep shadows, bright accents
    # Color: Limited palette — deep teal + warm copper + cream
    # Shape: Organic curves with geometric accents
    # Material: Metallic + translucent
    # Light: Single directional, theatrical
    # Mood: Mysterious, contemplative
    
    arr = np.zeros((H, W, 3), dtype=np.float32)
    
    # Golden ratio focal point
    gx = int(W * 0.618)
    gy = int(H * 0.382)
    
    # Layer 1: Deep gradient background
    for y in range(H):
        t = y / H
        arr[y, :] = np.array([0.02 + 0.03 * t, 0.04 + 0.04 * t, 0.06 + 0.05 * t])
    
    # Layer 2: Compositional masses (value study)
    # Large dark mass (left third)
    for y in range(H):
        for x in range(0, W // 3):
            dist = math.sqrt((x - W // 6) ** 2 + (y - H // 2) ** 2)
            if dist < 200:
                fade = max(0, 1 - dist / 200)
                arr[y, x] = np.clip(arr[y, x] + np.array([0.1, 0.08, 0.06]) * fade, 0, 1)
    
    # Warm accent mass at focal
    for r in range(100, 0, -1):
        t = r / 100
        intensity = (1 - t) ** 2 * 0.5
        y_start = max(0, gy - r)
        y_end = min(H, gy + r)
        x_start = max(0, gx - r)
        x_end = min(W, gx + r)
        
        for y in range(y_start, y_end):
            for x in range(x_start, x_end):
                d = math.sqrt((x - gx) ** 2 + (y - gy) ** 2)
                if d < r:
                    fade = 1 - d / r
                    arr[y, x] = np.clip(arr[y, x] + np.array([0.7, 0.4, 0.2]) * intensity * fade, 0, 1)
    
    # Layer 3: Geometric accent lines
    arr_uint8 = (arr * 255).clip(0, 255).astype(np.uint8)
    img = Image.fromarray(arr_uint8)
    draw = ImageDraw.Draw(img)
    
    # Compositional lines from focal
    for i in range(8):
        angle = i * math.pi / 4 + 0.3
        x1 = gx + int(50 * math.cos(angle))
        y1 = gy + int(50 * math.sin(angle))
        x2 = gx + int(300 * math.cos(angle))
        y2 = gy + int(300 * math.sin(angle))
        draw.line([(x1, y1), (x2, y2)], fill=(60, 100, 120), width=1)
    
    # Central focal element
    for r in range(25, 0, -1):
        v = int(200 * (r / 25))
        draw.ellipse([gx - r, gy - r, gx + r, gy + r], fill=(v, int(v * 0.7), int(v * 0.4)))
    
    # Title
    draw.text((50, H - 40), "ART-DIRECTED: Focal Asymmetry Study", fill=(100, 100, 120))
    draw.text((50, H - 25), "Teal + Copper palette, golden ratio focal, theatrical light", fill=(60, 60, 80))
    
    fp = os.path.join(OUT, "art_directed_work.png")
    img.save(fp)
    print(f"  Artwork: Focal Asymmetry Study — {W}x{H}")
    return fp

# ============================================================
# MAIN
# ============================================================
def main():
    print("=== BIAS DETECTION + ART-DIRECTED WORK ===\n")
    
    create_bias_report()
    create_art_directed_generation()
    
    print(f"\n=== COMPLETE ===")

if __name__ == "__main__":
    main()
