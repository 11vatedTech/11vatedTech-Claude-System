"""ARTISTIC FUNDAMENTALS: Real visual studies for composition, value, color, shape, edge, material."""
import os, json, math, colorsys
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import numpy as np

OUT = "artifacts/visual/fundamentals"
os.makedirs(OUT, exist_ok=True)
REPORT = {"studies": []}

def save(img, name):
    fp = os.path.join(OUT, name)
    img.save(fp, quality=95)
    return fp

# ============================================================
# 1. COMPOSITION STUDIES
# ============================================================
def study_composition():
    """Create composition studies: rule of thirds, golden ratio, dynamic symmetry."""
    print("\n--- Composition Studies ---")
    W, H = 1200, 800
    
    # Study 1: Rule of Thirds with value masses
    img = Image.new("RGB", (W, H), (20, 20, 25))
    draw = ImageDraw.Draw(img)
    
    # Draw thirds grid
    for i in range(1, 3):
        draw.line([(W*i//3, 0), (W*i//3, H)], fill=(60, 60, 70), width=1)
        draw.line([(0, H*i//3), (W, H*i//3)], fill=(60, 60, 70), width=1)
    
    # Place focal mass at upper-right intersection
    cx, cy = W*2//3, H//3
    for r in range(120, 0, -2):
        v = int(180 * (r/120))
        draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill=(v, v//2, v//3))
    
    # Secondary mass at lower-left
    cx2, cy2 = W//3, H*2//3
    for r in range(80, 0, -2):
        v = int(120 * (r/80))
        draw.ellipse([cx2-r, cy2-r, cx2+r, cy2+r], fill=(v//2, v//3, v))
    
    # Small accent at upper-left
    cx3, cy3 = W//3, H//3
    for r in range(30, 0, -2):
        v = int(200 * (r/30))
        draw.ellipse([cx3-r, cy3-r, cx3+r, cy3+r], fill=(v, v, v//2))
    
    fp1 = save(img, "composition_thirds.png")
    REPORT["studies"].append({"name": "Rule of Thirds", "file": fp1, "principle": "Focal mass at intersection, secondary balance, accent hierarchy"})
    
    # Study 2: Dynamic diagonal composition
    img2 = Image.new("RGB", (W, H), (15, 18, 22))
    draw2 = ImageDraw.Draw(img2)
    
    # Strong diagonal energy
    for i in range(0, W+H, 8):
        x1, y1 = max(0, i-H), min(H, i)
        x2, y2 = min(W, i), max(0, i-H)
        alpha = int(40 + 30 * math.sin(i * 0.02))
        draw2.line([(x1, y1), (x2, y2)], fill=(alpha, alpha+10, alpha+20), width=2)
    
    # Masses along diagonal
    for pos in [0.25, 0.5, 0.75]:
        cx = int(pos * W)
        cy = int(pos * H)
        r = int(60 + 40 * pos)
        for rr in range(r, 0, -2):
            v = int(160 * (rr/r))
            draw2.ellipse([cx-rr, cy-rr, cx+rr, cy+rr], fill=(v, v//2, v//4))
    
    fp2 = save(img2, "composition_diagonal.png")
    REPORT["studies"].append({"name": "Dynamic Diagonal", "file": fp2, "principle": "Diagonal energy creates movement, masses build rhythm along the line"})
    
    # Study 3: Centered/symmetric vs asymmetric balance
    img3 = Image.new("RGB", (W, H), (25, 22, 20))
    draw3 = ImageDraw.Draw(img3)
    
    # Left half: heavy centered mass
    for r in range(150, 0, -2):
        v = int(140 * (r/150))
        draw3.ellipse([W//4-r, H//2-r, W//4+r, H//2+r], fill=(v, v, v))
    
    # Right half: multiple small masses balancing
    positions = [(W*3//4, H//3), (W*3//4-40, H*2//3), (W*3//4+50, H*2//3+30)]
    for px, py in positions:
        for r in range(40, 0, -2):
            v = int(160 * (r/40))
            draw3.ellipse([px-r, py-r, px+r, py+r], fill=(v, v//2, v//3))
    
    # Divider line
    draw3.line([(W//2, 0), (W//2, H)], fill=(50, 50, 55), width=2)
    draw3.text((W//4-30, H-40), "CENTERED", fill=(80, 80, 85))
    draw3.text((W*3//4-30, H-40), "ASYMMETRIC", fill=(80, 80, 85))
    
    fp3 = save(img3, "composition_balance.png")
    REPORT["studies"].append({"name": "Balance Study", "file": fp3, "principle": "One heavy mass can balance multiple lighter ones through visual weight distribution"})
    
    print(f"  3 composition studies created")
    return True

# ============================================================
# 2. VALUE STUDIES
# ============================================================
def study_value():
    """Create value structure studies: 5-value scale, notan, value hierarchy."""
    print("\n--- Value Studies ---")
    W, H = 1200, 800
    
    # Study 1: 5-value scale exercise
    img = Image.new("RGB", (W, H), (240, 240, 235))
    draw = ImageDraw.Draw(img)
    
    values = [20, 60, 120, 180, 230]
    labels = ["Dark", "Shadow", "Mid", "Light", "Highlight"]
    band_w = W // 5
    for i, (v, label) in enumerate(zip(values, labels)):
        x0 = i * band_w
        draw.rectangle([x0, 0, x0 + band_w, H - 60], fill=(v, v, v))
        draw.text((x0 + band_w//2 - 20, H - 40), label, fill=(40, 40, 40))
    
    fp1 = save(img, "value_scale.png")
    REPORT["studies"].append({"name": "5-Value Scale", "file": fp1, "principle": "All visual information compresses to 5 values. Master value before color."})
    
    # Study 2: Notan (light/dark design)
    img2 = Image.new("RGB", (W, H), (240, 235, 230))
    draw2 = ImageDraw.Draw(img2)
    
    # Create interlocking light/dark shapes
    # Dark shapes
    dark_shapes = [
        [(100, 100), (400, 80), (350, 350), (80, 300)],
        [(500, 200), (700, 150), (750, 400), (550, 450)],
        [(200, 500), (450, 480), (400, 700), (150, 680)],
    ]
    for shape in dark_shapes:
        draw2.polygon(shape, fill=(30, 30, 35))
    
    # Light shapes (white on the same background for contrast)
    light_shapes = [
        [(300, 150), (500, 100), (550, 350), (350, 400)],
        [(600, 300), (850, 250), (900, 550), (650, 500)],
        [(100, 600), (350, 550), (400, 750), (50, 780)],
    ]
    for shape in light_shapes:
        draw2.polygon(shape, fill=(250, 250, 245))
    
    fp2 = save(img2, "value_notan.png")
    REPORT["studies"].append({"name": "Notan Design", "file": fp2, "principle": "Strong compositions work as pure light/dark interlocking shapes"})
    
    # Study 3: Value hierarchy in a scene
    img3 = Image.new("RGB", (W, H), (180, 175, 165))
    draw3 = ImageDraw.Draw(img3)
    
    # Background: lightest value
    draw3.rectangle([0, 0, W, H], fill=(190, 185, 175))
    
    # Middle ground: mid values
    draw3.polygon([(0, H*2//3), (W, H*2//3), (W, H), (0, H)], fill=(100, 95, 85))
    
    # Foreground elements: dark values
    for x in range(0, W, 200):
        h_var = 150 + int(50 * math.sin(x * 0.01))
        draw3.rectangle([x, H-h_var, x+80, H], fill=(40, 38, 35))
    
    # Focal point: darkest value with highest contrast
    cx, cy = W*2//3, H//2
    for r in range(60, 0, -1):
        v = int(20 + 15 * (r/60))
        draw3.ellipse([cx-r, cy-r, cx+r, cy+r], fill=(v, v, v))
    
    # Lightest accent near focal
    draw3.ellipse([cx+50, cy-40, cx+70, cy-20], fill=(250, 245, 235))
    
    fp3 = save(img3, "value_hierarchy.png")
    REPORT["studies"].append({"name": "Value Hierarchy", "file": fp3, "principle": "Darkest darks and lightest lights near focal point. Background lighter, foreground darker."})
    
    print(f"  3 value studies created")
    return True

# ============================================================
# 3. COLOR STUDIES
# ============================================================
def study_color():
    """Create color studies: temperature, complementary, limited palette."""
    print("\n--- Color Studies ---")
    W, H = 1200, 800
    
    # Study 1: Color temperature contrast
    img = Image.new("RGB", (W, H), (180, 170, 160))
    draw = ImageDraw.Draw(img)
    
    # Warm side
    for x in range(W//2):
        t = x / (W//2)
        r = int(200 - 40 * t)
        g = int(140 - 60 * t)
        b = int(100 - 40 * t)
        draw.line([(x, 0), (x, H)], fill=(r, g, b))
    
    # Cool side
    for x in range(W//2, W):
        t = (x - W//2) / (W//2)
        r = int(100 - 40 * t)
        g = int(140 - 20 * t)
        b = int(200 + 20 * t)
        draw.line([(x, 0), (x, H)], fill=(r, g, b))
    
    # Warm focal
    for r_size in range(80, 0, -2):
        t = r_size / 80
        draw.ellipse([W//4-r_size, H//2-r_size, W//4+r_size, H//2+r_size],
                     fill=(int(220*t), int(120*t), int(60*t)))
    
    # Cool focal
    for r_size in range(80, 0, -2):
        t = r_size / 80
        draw.ellipse([W*3//4-r_size, H//2-r_size, W*3//4+r_size, H//2+r_size],
                     fill=(int(60*t), int(120*t), int(220*t)))
    
    fp1 = save(img, "color_temperature.png")
    REPORT["studies"].append({"name": "Color Temperature", "file": fp1, "principle": "Warm advances, cool recedes. Temperature contrast creates depth without value change."})
    
    # Study 2: Complementary color harmony
    img2 = Image.new("RGB", (W, H), (40, 35, 30))
    draw2 = ImageDraw.Draw(img2)
    
    # Orange-blue complementary
    colors = [
        ((200, 120, 50), (50, 100, 200)),  # orange-blue
        ((180, 80, 80), (80, 140, 180)),    # muted red-cyan
    ]
    
    for ci, (warm, cool) in enumerate(colors):
        y_off = ci * H // 2
        # Warm masses
        for pos in [(W//4, y_off + H//4), (W//2, y_off + H//4 + 30)]:
            for r in range(60, 0, -2):
                t = r / 60
                c = tuple(int(warm[i] * t) for i in range(3))
                draw2.ellipse([pos[0]-r, pos[1]-r, pos[0]+r, pos[1]+r], fill=c)
        # Cool masses
        for pos in [(W*3//4, y_off + H//4), (W*3//4 + 40, y_off + H//4 - 20)]:
            for r in range(60, 0, -2):
                t = r / 60
                c = tuple(int(cool[i] * t) for i in range(3))
                draw2.ellipse([pos[0]-r, pos[1]-r, pos[0]+r, pos[1]+r], fill=c)
    
    fp2 = save(img2, "color_complementary.png")
    REPORT["studies"].append({"name": "Complementary Harmony", "file": fp2, "principle": "Complementary pairs create maximum chromatic contrast. Use one as dominant, one as accent."})
    
    # Study 3: Limited palette (3-color study)
    img3 = Image.new("RGB", (W, H), (235, 225, 210))
    draw3 = ImageDraw.Draw(img3)
    
    # 3-color palette: burnt sienna, cerulean, cream
    palette = [(160, 80, 40), (60, 110, 150), (235, 225, 210)]
    
    # Compose with limited palette
    # Large warm mass
    draw3.polygon([(0, H//3), (W*2//3, 0), (W, H//2), (W//2, H)], fill=palette[0])
    # Cool accent
    draw3.ellipse([W//2-80, H//3-80, W//2+80, H//3+80], fill=palette[1])
    # Small highlights
    draw3.ellipse([W//3-20, H//2-20, W//3+20, H//2+20], fill=palette[2])
    
    fp3 = save(img3, "color_limited.png")
    REPORT["studies"].append({"name": "Limited Palette", "file": fp3, "principle": "3 colors force intentional choices. Limitation breeds coherence and sophistication."})
    
    print(f"  3 color studies created")
    return True

# ============================================================
# 4. SHAPE LANGUAGE STUDIES
# ============================================================
def study_shape():
    """Create shape language studies: geometric vs organic, shape personality."""
    print("\n--- Shape Language Studies ---")
    W, H = 1200, 800
    
    # Study 1: Geometric vs Organic character silhouettes
    img = Image.new("RGB", (W, H), (240, 235, 228))
    draw = ImageDraw.Draw(img)
    
    # Geometric character (angular, mechanical)
    geo_shapes = [
        # Head (angular)
        [(W//4-30, 100), (W//4+30, 80), (W//4+35, 150), (W//4-25, 155)],
        # Torso (rectangle)
        [(W//4-40, 155), (W//4+40, 155), (W//4+35, 350), (W//4-45, 350)],
        # Left arm
        [(W//4-40, 170), (W//4-80, 180), (W//4-85, 320), (W//4-45, 310)],
        # Right arm
        [(W//4+40, 170), (W//4+80, 180), (W//4+85, 320), (W//4+45, 310)],
        # Left leg
        [(W//4-35, 350), (W//4-10, 350), (W//4-5, 520), (W//4-40, 520)],
        # Right leg
        [(W//4+10, 350), (W//4+35, 350), (W//4+40, 520), (W//4+5, 520)],
    ]
    for shape in geo_shapes:
        draw.polygon(shape, fill=(40, 40, 45))
    
    # Organic character (rounded, flowing)
    org_parts = [
        (W*3//4, 120, 50),  # head
        (W*3//4, 250, 45),  # torso
        (W*3//4-60, 220, 20),  # left shoulder
        (W*3//4+60, 220, 20),  # right shoulder
        (W*3//4-70, 300, 18),  # left hand
        (W*3//4+70, 300, 18),  # right hand
        (W*3//4-20, 420, 22),  # left knee
        (W*3//4+20, 420, 22),  # right knee
    ]
    for px, py, r in org_parts:
        draw.ellipse([px-r, py-r, px+r, py+r], fill=(60, 55, 50))
    
    # Connection lines for organic (flowing)
    draw.line([(W*3//4-50, 170), (W*3//4-70, 300)], fill=(60, 55, 50), width=12)
    draw.line([(W*3//4+50, 170), (W*3//4+70, 300)], fill=(60, 55, 50), width=12)
    draw.line([(W*3//4-30, 350), (W*3//4-20, 420)], fill=(60, 55, 50), width=14)
    draw.line([(W*3//4+30, 350), (W*3//4+20, 420)], fill=(60, 55, 50), width=14)
    
    draw.text((W//4-20, 550), "GEOMETRIC", fill=(80, 80, 85))
    draw.text((W*3//4-25, 550), "ORGANIC", fill=(80, 80, 85))
    
    fp1 = save(img, "shape_geometric_vs_organic.png")
    REPORT["studies"].append({"name": "Geometric vs Organic", "file": fp1, "principle": "Shape language defines character personality before detail. Angular = mechanical/fierce. Rounded = natural/friendly."})
    
    # Study 2: Shape personality through silhouette
    img2 = Image.new("RGB", (W, H), (245, 240, 232))
    draw2 = ImageDraw.Draw(img2)
    
    # 4 silhouettes with different personalities
    silhouettes = [
        # Tall thin (elegant/mysterious)
        {"cx": W//6, "parts": [(0, -80, 25), (0, 0, 30), (0, 60, 22), (0, 130, 18), (0, 200, 16), (-15, 200, 10), (15, 200, 10)]},
        # Short wide (powerful/stable)
        {"cx": W*2//6, "parts": [(0, -50, 40), (0, 20, 50), (0, 100, 35), (0, 170, 30), (-30, 170, 15), (30, 170, 15)]},
        # Angular aggressive
        {"cx": W*3//6, "parts": [(0, -60, 30), (0, 10, 45), (-40, 30, 15), (40, 30, 15), (0, 100, 25), (-20, 170, 12), (20, 170, 12)]},
        # Small cute
        {"cx": W*4//6, "parts": [(0, -40, 35), (0, 20, 30), (0, 80, 20), (-25, 80, 10), (25, 80, 10), (-15, 130, 10), (15, 130, 10)]},
    ]
    
    base_y = H // 2
    for sil in silhouettes:
        cx = sil["cx"]
        for ox, oy, r in sil["parts"]:
            draw2.ellipse([cx+ox-r, base_y+oy-r, cx+ox+r, base_y+oy+r], fill=(30, 28, 25))
    
    labels = ["ELEGANT", "POWERFUL", "AGGRESSIVE", "CUTE"]
    for i, label in enumerate(labels):
        draw2.text((W*(i+1)//6 - 25, H - 40), label, fill=(80, 75, 70))
    
    fp2 = save(img2, "shape_personality.png")
    REPORT["studies"].append({"name": "Shape Personality", "file": fp2, "principle": "Silhouette alone communicates personality. Proportions carry emotional weight."})
    
    # Study 3: Shape rhythm and repetition
    img3 = Image.new("RGB", (W, H), (235, 230, 222))
    draw3 = ImageDraw.Draw(img3)
    
    # Rhythmic shape pattern
    for i in range(20):
        x = 60 + i * 55
        size = int(30 + 20 * math.sin(i * 0.5))
        y = H // 2 + int(40 * math.sin(i * 0.3))
        draw3.ellipse([x-size, y-size, x+size, y+size], fill=(60 + i*5, 55 + i*4, 50 + i*3))
    
    fp3 = save(img3, "shape_rhythm.png")
    REPORT["studies"].append({"name": "Shape Rhythm", "file": fp3, "principle": "Repetition with variation creates visual rhythm. Size, spacing, and position variation prevent monotony."})
    
    print(f"  3 shape studies created")
    return True

# ============================================================
# 5. EDGE STUDIES
# ============================================================
def study_edge():
    """Create edge hierarchy studies: hard/soft/lost edges, edge as design tool."""
    print("\n--- Edge Studies ---")
    W, H = 1200, 800
    
    # Study 1: Edge hierarchy in a portrait-like composition
    img = Image.new("RGB", (W, H), (200, 190, 175))
    draw = ImageDraw.Draw(img)
    
    # Background: soft/lost edges
    for x in range(W):
        for y in range(0, H//3):
            v = int(180 + 20 * math.sin(x*0.01 + y*0.02))
            draw.point((x, y), fill=(v, v-5, v-15))
    
    # Mid-ground: medium edges
    draw.polygon([(0, H//3), (W, H//3-20), (W, H*2//3), (0, H*2//3+10)], fill=(120, 110, 100))
    
    # Foreground: hard edges
    draw.rectangle([W//4, H*2//3, W*3//4, H], fill=(50, 45, 40))
    
    # Focal: sharpest edges
    cx, cy = W//2, H//2
    draw.ellipse([cx-50, cy-50, cx+50, cy+50], fill=(200, 100, 60))
    draw.ellipse([cx-48, cy-48, cx+48, cy+48], fill=(220, 120, 80))
    
    fp1 = save(img, "edge_hierarchy.png")
    REPORT["studies"].append({"name": "Edge Hierarchy", "file": fp1, "principle": "Hard edges attract attention. Soft edges recede. Lost edges merge. Control edge sharpness to direct the eye."})
    
    # Study 2: Edge as design element
    img2 = Image.new("RGB", (W, H), (240, 235, 225))
    draw2 = ImageDraw.Draw(img2)
    
    # Hard edge: precise rectangle
    draw2.rectangle([100, 100, 350, 350], fill=(40, 40, 45))
    draw2.text((150, 360), "HARD", fill=(80, 80, 85))
    
    # Soft edge: gaussian blurred circle
    soft = Image.new("RGB", (W, H), (240, 235, 225))
    soft_draw = ImageDraw.Draw(soft)
    soft_draw.ellipse([450, 100, 700, 350], fill=(40, 40, 45))
    soft = soft.filter(ImageFilter.GaussianBlur(radius=15))
    img2.paste(soft, (0, 0))
    draw2.text((525, 360), "SOFT", fill=(80, 80, 85))
    
    # Lost edge: gradient fade
    for x in range(800, 1100):
        t = (x - 800) / 300
        alpha = int(40 * (1 - t))
        draw2.line([(x, 100), (x, 350)], fill=(alpha, alpha, alpha))
    draw2.text((880, 360), "LOST", fill=(80, 80, 85))
    
    fp2 = save(img2, "edge_types.png")
    REPORT["studies"].append({"name": "Edge Types", "file": fp2, "principle": "Edge quality is a design choice. Hard = defined, Soft = atmospheric, Lost = mystery/depth."})
    
    # Study 3: Edge contrast for focal control
    img3 = Image.new("RGB", (W, H), (180, 170, 155))
    draw3 = ImageDraw.Draw(img3)
    
    # Everything soft except one hard edge
    for r in range(200, 0, -1):
        v = int(160 * (r/200))
        draw3.ellipse([W//2-r, H//2-r, W//2+r, H//2+r], fill=(v, v-5, v-10))
    
    # One hard-edged accent
    draw3.rectangle([W//2-20, H//2-20, W//2+20, H//2+20], fill=(200, 80, 40))
    
    fp3 = save(img3, "edge_focal.png")
    REPORT["studies"].append({"name": "Edge for Focal Control", "file": fp3, "principle": "One hard edge among soft edges instantly draws the eye. The sharpest edge wins attention."})
    
    print(f"  3 edge studies created")
    return True

# ============================================================
# 6. MATERIAL STUDIES
# ============================================================
def study_material():
    """Create material representation studies: how different media suggest material."""
    print("\n--- Material Studies ---")
    W, H = 1200, 800
    
    # Study 1: Material through value pattern
    img = Image.new("RGB", (W, H), (235, 230, 220))
    draw = ImageDraw.Draw(img)
    
    # Metal: high contrast, sharp transitions
    for x in range(100, 350):
        for y in range(100, 350):
            v = int(128 + 100 * math.sin((x + y) * 0.1) * math.exp(-abs(x - 225) * 0.02))
            draw.point((x, y), fill=(v, v, v))
    draw.text((150, 360), "METAL", fill=(80, 80, 85))
    
    # Fabric: soft gradients, low contrast
    for x in range(450, 700):
        for y in range(100, 350):
            v = int(140 + 30 * math.sin(x * 0.03) * math.cos(y * 0.02))
            draw.point((x, y), fill=(v, v-5, v-10))
    draw.text((520, 360), "FABRIC", fill=(80, 80, 85))
    
    # Wood: directional grain
    for x in range(800, 1050):
        for y in range(100, 350):
            grain = math.sin(y * 0.2 + math.sin(x * 0.05) * 3) * 0.3
            v = int(130 + 40 * grain)
            draw.point((x, y), fill=(v, int(v * 0.85), int(v * 0.7)))
    draw.text((860, 360), "WOOD", fill=(80, 80, 85))
    
    # Glass: transparency, refraction suggestion
    for x in range(100, 350):
        for y in range(450, 700):
            cx, cy = 225, 575
            dist = math.sqrt((x-cx)**2 + (y-cy)**2)
            if dist < 100:
                v = int(200 - 60 * (dist/100) + 20 * math.sin(dist * 0.1))
                alpha = max(0, min(255, v))
                draw.point((x, y), fill=(alpha, alpha+10, alpha+20))
    draw.text((150, 710), "GLASS", fill=(80, 80, 85))
    
    fp1 = save(img, "material_patterns.png")
    REPORT["studies"].append({"name": "Material Value Patterns", "file": fp1, "principle": "Each material has a characteristic value pattern: metal=high contrast, fabric=soft, wood=directional, glass=transparent"})
    
    # Study 2: Material through brush/mark-making
    img2 = Image.new("RGB", (W, H), (245, 240, 230))
    draw2 = ImageDraw.Draw(img2)
    
    # Simulate brush strokes for painterly material
    np.random.seed(42)
    for _ in range(500):
        x = np.random.randint(100, 350)
        y = np.random.randint(100, 350)
        w = np.random.randint(5, 25)
        h = np.random.randint(2, 8)
        angle = np.random.uniform(-0.3, 0.3)
        v = int(120 + np.random.randint(-30, 30))
        draw2.ellipse([x-w, y-h, x+w, y+h], fill=(v, v-10, v-20))
    draw2.text((150, 360), "PAINTERLY", fill=(80, 80, 85))
    
    # Geometric/vector material
    for i in range(8):
        for j in range(8):
            x = 450 + i * 30
            y = 100 + j * 30
            v = int(80 + (i + j) * 10)
            draw2.rectangle([x, y, x+25, y+25], fill=(v, v, v+10))
    draw2.text((520, 360), "VECTOR", fill=(80, 80, 85))
    
    # Procedural/noise material
    for x in range(800, 1050):
        for y in range(100, 350):
            n = (math.sin(x * 0.1) * math.cos(y * 0.1) * 0.5 + 0.5)
            v = int(100 + 80 * n)
            draw2.point((x, y), fill=(v, v-5, v-15))
    draw2.text((860, 360), "PROCEDURAL", fill=(80, 80, 85))
    
    fp2 = save(img2, "material_marks.png")
    REPORT["studies"].append({"name": "Material through Marks", "file": fp2, "principle": "Mark-making defines material: brush=painterly, geometric=vector, noise=procedural"})
    
    # Study 3: Light interaction with material
    img3 = Image.new("RGB", (W, H), (30, 28, 25))
    draw3 = ImageDraw.Draw(img3)
    
    # Chrome sphere (high contrast reflections)
    cx, cy = 200, 300
    for r in range(80, 0, -1):
        t = r / 80
        v = int(255 * (1 - t) * (0.5 + 0.5 * math.sin(r * 0.2)))
        draw3.ellipse([cx-r, cy-r, cx+r, cy+r], fill=(v, v, v))
    
    # Matte sphere (soft gradient)
    cx2, cy2 = 450, 300
    for r in range(80, 0, -1):
        t = r / 80
        v = int(180 * (1 - t * 0.7))
        draw3.ellipse([cx2-r, cy2-r, cx2+r, cy2+r], fill=(v, int(v*0.9), int(v*0.85)))
    
    # Emissive sphere (self-illuminated)
    cx3, cy3 = 700, 300
    for r in range(80, 0, -1):
        t = r / 80
        v = int(200 + 55 * (1 - t))
        draw3.ellipse([cx3-r, cy3-r, cx3+r, cy3+r], fill=(v, int(v*0.6), int(v*0.3)))
    
    # Transparent sphere
    cx4, cy4 = 950, 300
    for r in range(80, 0, -1):
        t = r / 80
        v = int(60 + 40 * (1 - t))
        draw3.ellipse([cx4-r, cy4-r, cx4+r, cy4+r], fill=(v, v+10, v+20))
    
    labels = ["CHROME", "MATTE", "EMISSIVE", "TRANSPARENT"]
    for i, label in enumerate(labels):
        draw3.text((100 + i * 250 - 25, 400), label, fill=(120, 115, 110))
    
    fp3 = save(img3, "material_light.png")
    REPORT["studies"].append({"name": "Material Light Response", "file": fp3, "principle": "Material is defined by how it responds to light: chrome=reflective, matte=diffuse, emissive=self-lit, transparent=transmissive"})
    
    print(f"  3 material studies created")
    return True

# ============================================================
# MAIN
# ============================================================
def main():
    print("=== ARTISTIC FUNDAMENTALS STUDIES ===\n")
    
    study_composition()
    study_value()
    study_color()
    study_shape()
    study_edge()
    study_material()
    
    # Write report
    with open(os.path.join(OUT, "fundamentals_report.json"), "w") as f:
        json.dump(REPORT, f, indent=2)
    
    print(f"\n=== COMPLETE: {len(REPORT['studies'])} studies ===")
    for s in REPORT["studies"]:
        print(f"  {s['name']}: {s['principle'][:80]}...")

if __name__ == "__main__":
    main()
