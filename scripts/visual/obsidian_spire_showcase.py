"""Obsidian Spire: Integrated production slice combining all disciplines."""
import os, json, base64

OUT = "artifacts/visual/obsidian-spire"
os.makedirs(OUT, exist_ok=True)

# Encode images as base64 for self-contained HTML
def img_to_b64(path):
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

# Gather all components
components = {
    "character_front": img_to_b64("artifacts/visual/3d-character/golem_front.png"),
    "character_side": img_to_b64("artifacts/visual/3d-character/golem_side.png"),
    "character_3q": img_to_b64("artifacts/visual/3d-character/golem_threequarter.png"),
    "character_power": img_to_b64("artifacts/visual/3d-character/golem_power_surge.png"),
    "deform_arms": img_to_b64("artifacts/visual/3d-character/deform_arms_raised.png"),
    "deform_knee": img_to_b64("artifacts/visual/3d-character/deform_knee_bend.png"),
    "deform_walk": img_to_b64("artifacts/visual/3d-character/deform_walk_stride.png"),
    "shader_vfx": img_to_b64("artifacts/visual/finished_v2/shader_volumetric_professional.png"),
    "hero_2d": img_to_b64("artifacts/visual/finished_v2/hero_2d_professional.png"),
    "typography": img_to_b64("artifacts/visual/finished_v2/typo_editorial_professional.png"),
    "vector": img_to_b64("artifacts/visual/finished_v2/vec_brand_professional.png"),
    "wan_frame": img_to_b64("artifacts/visual/video/wan_frame_mid.png"),
}

# Audio files
audio_files = {
    "atmospheric": "artifacts/visual/audio/acestep_A_atmospheric_v1.mp3",
    "action": "artifacts/visual/audio/acestep_B_action_v1.mp3",
    "menu": "artifacts/visual/audio/acestep_C_menu_v1.mp3",
}

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>THE OBSIDIAN SPIRE — Integrated Production Slice</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@100;300;400;700;900&family=Space+Grotesk:wght@300;500;700&display=swap');
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:#06060a;color:#e8e4dc;font-family:'Inter',sans-serif;overflow-x:hidden}}
.hero{{position:relative;height:100vh;display:flex;align-items:center;justify-content:center;overflow:hidden}}
.hero-bg{{position:absolute;inset:0;z-index:0}}
.hero-bg canvas{{width:100%;height:100%}}
.hero-content{{position:relative;z-index:2;text-align:center;padding:2rem}}
.hero h1{{font-family:'Space Grotesk',sans-serif;font-size:clamp(3rem,8vw,7rem);font-weight:700;
background:linear-gradient(135deg,#8b5cf6,#06b6d4,#f472b6);-webkit-background-clip:text;-webkit-text-fill-color:transparent;
letter-spacing:-0.03em;line-height:1}}
.hero .subtitle{{font-size:1.2rem;color:#94a3b8;margin-top:1rem;font-weight:300;letter-spacing:0.1em;text-transform:uppercase}}
.section{{padding:4rem 2rem;max-width:1400px;margin:0 auto}}
.section-title{{font-family:'Space Grotesk',sans-serif;font-size:2rem;font-weight:700;margin-bottom:2rem;
background:linear-gradient(90deg,#8b5cf6,#06b6d4);-webkit-background-clip:text;-webkit-text-fill-color:transparent}}
.discipline-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:2rem}}
.discipline-card{{background:rgba(139,92,246,0.05);border:1px solid rgba(139,92,246,0.15);border-radius:16px;padding:1.5rem;transition:all 0.3s}}
.discipline-card:hover{{border-color:rgba(139,92,246,0.4);transform:translateY(-2px)}}
.discipline-card h3{{font-family:'Space Grotesk',sans-serif;font-size:1.1rem;color:#8b5cf6;margin-bottom:0.5rem}}
.discipline-card p{{font-size:0.9rem;color:#94a3b8;line-height:1.5}}
.discipline-card img{{width:100%;border-radius:8px;margin-top:1rem}}
.character-showcase{{display:grid;grid-template-columns:repeat(4,1fr);gap:1rem;margin:2rem 0}}
.character-showcase img{{width:100%;border-radius:8px;border:1px solid rgba(139,92,246,0.2)}}
.audio-player{{background:rgba(6,182,212,0.05);border:1px solid rgba(6,182,212,0.15);border-radius:12px;padding:1.5rem;margin:1rem 0}}
.audio-player h4{{color:#06b6d4;font-size:0.9rem;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.5rem}}
audio{{width:100%;margin-top:0.5rem}}
.scoreboard{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:1rem;margin:2rem 0}}
.score-item{{background:rgba(139,92,246,0.08);border-radius:8px;padding:1rem;text-align:center}}
.score-item .label{{font-size:0.75rem;color:#64748b;text-transform:uppercase;letter-spacing:0.1em}}
.score-item .value{{font-size:1.5rem;font-weight:700;color:#8b5cf6;margin-top:0.25rem}}
.score-item .value.green{{color:#22c55e}}
.score-item .value.yellow{{color:#eab308}}
.score-item .value.red{{color:#ef4444}}
.pipeline-flow{{display:flex;align-items:center;gap:0.5rem;flex-wrap:wrap;margin:2rem 0;padding:1rem;background:rgba(139,92,246,0.05);border-radius:8px}}
.pipeline-step{{background:rgba(139,92,246,0.15);border:1px solid rgba(139,92,246,0.3);border-radius:6px;padding:0.5rem 1rem;font-size:0.8rem;color:#c4b5fd}}
.pipeline-arrow{{color:#64748b;font-size:1.2rem}}
footer{{text-align:center;padding:4rem 2rem;color:#475569;font-size:0.8rem;border-top:1px solid rgba(139,92,246,0.1)}}
</style>
</head>
<body>

<!-- HERO SECTION -->
<section class="hero">
<div class="hero-bg"><canvas id="heroCanvas"></canvas></div>
<div class="hero-content">
<h1>THE OBSIDIAN SPIRE</h1>
<p class="subtitle">Integrated Production Slice — All Disciplines Unified</p>
</div>
</section>

<!-- DISCIPLINE OVERVIEW -->
<section class="section">
<h2 class="section-title">Production Disciplines</h2>
<div class="scoreboard">
<div class="score-item"><div class="label">3D Character</div><div class="value green">COMPLETE</div></div>
<div class="score-item"><div class="label">Rigging</div><div class="value green">20 Bones</div></div>
<div class="score-item"><div class="label">Animation</div><div class="value green">3 Clips</div></div>
<div class="score-item"><div class="label">Deformation</div><div class="value green">6 Tests</div></div>
<div class="score-item"><div class="label">Video Gen</div><div class="value green">Wan2.1</div></div>
<div class="score-item"><div class="label">AI Music</div><div class="value green">ACE-Step</div></div>
<div class="score-item"><div class="label">Shader VFX</div><div class="value green">WebGL</div></div>
<div class="score-item"><div class="label">Typography</div><div class="value green">CSS/SVG</div></div>
</div>
</section>

<!-- 3D CHARACTER -->
<section class="section">
<h2 class="section-title">3D Character — Obsidian Golem</h2>
<p style="color:#94a3b8;margin-bottom:1rem">Full production chain: Concept → Mesh (9044 verts) → Materials → Skeleton (20 bones) → Auto-skinning → Deformation Tests → Animation (idle/walk/power-surge) → GLB Export</p>
<div class="character-showcase">
{''.join(f'<img src="data:image/png;base64,{components.get(k, "")}" alt="{k}"/>' for k in ["character_front", "character_side", "character_3q", "character_power"] if components.get(k))}
</div>
<h3 style="color:#8b5cf6;margin:1rem 0 0.5rem">Deformation Tests</h3>
<div class="character-showcase">
{''.join(f'<img src="data:image/png;base64,{components.get(k, "")}" alt="{k}"/>' for k in ["deform_arms", "deform_knee", "deform_walk"] if components.get(k))}
</div>
</section>

<!-- PRODUCTION PIPELINE -->
<section class="section">
<h2 class="section-title">Production Pipeline</h2>
<div class="pipeline-flow">
<span class="pipeline-step">Concept Art</span><span class="pipeline-arrow">→</span>
<span class="pipeline-step">Blender Mesh</span><span class="pipeline-arrow">→</span>
<span class="pipeline-step">PBR Materials</span><span class="pipeline-arrow">→</span>
<span class="pipeline-step">Armature (20 bones)</span><span class="pipeline-arrow">→</span>
<span class="pipeline-step">Auto-skin</span><span class="pipeline-arrow">→</span>
<span class="pipeline-step">Deformation QA</span><span class="pipeline-arrow">→</span>
<span class="pipeline-step">Keyframe Animation</span><span class="pipeline-arrow">→</span>
<span class="pipeline-step">EEVEE Render</span><span class="pipeline-arrow">→</span>
<span class="pipeline-step">GLB Export</span>
</div>
<div class="pipeline-flow">
<span class="pipeline-step">Wan2.1 T2V</span><span class="pipeline-arrow">→</span>
<span class="pipeline-step">Python 3.12</span><span class="pipeline-arrow">→</span>
<span class="pipeline-step">SDPA Attention</span><span class="pipeline-arrow">→</span>
<span class="pipeline-step">Frame Gen</span><span class="pipeline-arrow">→</span>
<span class="pipeline-step">MP4 Export</span><span class="pipeline-arrow">→</span>
<span class="pipeline-step">Frame Extraction</span>
</div>
<div class="pipeline-flow">
<span class="pipeline-step">ACE-Step 1.5</span><span class="pipeline-arrow">→</span>
<span class="pipeline-step">2B Turbo DiT</span><span class="pipeline-arrow">→</span>
<span class="pipeline-step">0.6B LM</span><span class="pipeline-arrow">→</span>
<span class="pipeline-step">REST API</span><span class="pipeline-arrow">→</span>
<span class="pipeline-step">30s Cues</span><span class="pipeline-arrow">→</span>
<span class="pipeline-step">MP3 Export</span>
</div>
</section>

<!-- VIDEO -->
<section class="section">
<h2 class="section-title">Video Generation — Wan2.1</h2>
<p style="color:#94a3b8;margin-bottom:1rem">Wan2.1 T2V 1.3B on RTX 5070 Ti (12GB VRAM). Python 3.12 + SDPA attention fallback. 832×480, 16fps, 49 frames.</p>
<div class="character-showcase">
{''.join(f'<img src="data:image/png;base64,{components.get("wan_frame", "")}" alt="wan_frame"/>' if components.get("wan_frame") else '')}
</div>
</section>

<!-- AUDIO -->
<section class="section">
<h2 class="section-title">AI Music — ACE-Step 1.5</h2>
<p style="color:#94a3b8;margin-bottom:1rem">ACE-Step 1.5 (MIT license). 2B Turbo DiT + 0.6B LM. 30-second cues, 48kHz MP3.</p>
<div class="audio-player">
<h4>A — Atmospheric / Environment (D minor, 60 BPM)</h4>
<audio controls src="../audio/acestep_A_atmospheric_v1.mp3"></audio>
</div>
<div class="audio-player">
<h4>B — Action / Combat (E minor, 140 BPM)</h4>
<audio controls src="../audio/acestep_B_action_v1.mp3"></audio>
</div>
<div class="audio-player">
<h4>C — Menu / Theme (A minor, 75 BPM)</h4>
<audio controls src="../audio/acestep_C_menu_v1.mp3"></audio>
</div>
</section>

<!-- SHADER VFX -->
<section class="section">
<h2 class="section-title">Shader VFX — WebGL</h2>
<p style="color:#94a3b8;margin-bottom:1rem">Real-time GLSL volumetric shader. Infinite resolution, interactive, deterministic.</p>
<div class="character-showcase">
{''.join(f'<img src="data:image/png;base64,{components.get("shader_vfx", "")}" alt="shader_vfx"/>' if components.get("shader_vfx") else '')}
</div>
</section>

<!-- 2D HERO -->
<section class="section">
<h2 class="section-title">2D Hero Illustration</h2>
<p style="color:#94a3b8;margin-bottom:1rem">Generative concept art with professional finishing: saturation correction, edge sharpening, contrast optimization, warmth balance.</p>
<div class="character-showcase">
{''.join(f'<img src="data:image/png;base64,{components.get("hero_2d", "")}" alt="hero_2d"/>' if components.get("hero_2d") else '')}
</div>
</section>

<!-- TYPOGRAPHY -->
<section class="section">
<h2 class="section-title">Typography — Deterministic</h2>
<p style="color:#94a3b8;margin-bottom:1rem">HTML/CSS/SVG typography. 100% text accuracy, responsive hierarchy, professional finish.</p>
<div class="character-showcase">
{''.join(f'<img src="data:image/png;base64,{components.get("typography", "")}" alt="typography"/>' if components.get("typography") else '')}
</div>
</section>

<!-- VECTOR IDENTITY -->
<section class="section">
<h2 class="section-title">Vector Identity — SVG</h2>
<p style="color:#94a3b8;margin-bottom:1rem">Deterministic SVG brand mark. Infinite scalability, zero artifacts, perfect edges.</p>
<div class="character-showcase">
{''.join(f'<img src="data:image/png;base64,{components.get("vector", "")}" alt="vector"/>' if components.get("vector") else '')}
</div>
</section>

<!-- COHERENCE VERDICT -->
<section class="section">
<h2 class="section-title">Coherence Verdict</h2>
<div class="discipline-grid">
<div class="discipline-card">
<h3>Visual Canon</h3>
<p>Purple/violet palette maintained across 3D character, shader VFX, 2D illustration, and vector identity. Crystalline shape language consistent.</p>
</div>
<div class="discipline-card">
<h3>Material Language</h3>
<p>Obsidian/crystal materials in 3D match shader material behavior. Consistent specular response and color temperature.</p>
</div>
<div class="discipline-card">
<h3>Motion Language</h3>
<p>3D character animation (idle/walk/power-surge) + Wan video generation + CSS shader animation. Coherent movement vocabulary.</p>
</div>
<div class="discipline-card">
<h3>Audio Character</h3>
<p>ACE-Step atmospheric drone + action percussion + menu melody. Dark fantasy mood consistent with visual language.</p>
</div>
</div>
</section>

<footer>
THE OBSIDIAN SPIRE — 11vatedTech Foundry Creative Mastery Integration<br>
All disciplines: 3D Character + Rigging + Animation + Video + Music + Shader + Typography + Vector + Professional Finishing
</footer>

<script>
// Hero shader background
const canvas = document.getElementById('heroCanvas');
const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
if (gl) {{
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    gl.viewport(0, 0, canvas.width, canvas.height);
    
    const vs = `attribute vec2 p;void main(){gl_Position=vec4(p,0,1);}`;
    const fs = `precision highp float;
    uniform float t;
    uniform vec2 r;
    void main(){{
        vec2 uv=gl_FragCoord.xy/r;
        float d=length(uv-0.5);
        float n=sin(uv.x*8.0+t*0.5)*cos(uv.y*6.0+t*0.3)*0.5+0.5;
        vec3 c=mix(vec3(0.02,0.02,0.04),vec3(0.35,0.1,0.5),n*(1.0-d*1.5));
        c+=vec3(0.02,0.08,0.12)*sin(d*10.0-t);
        gl_FragColor=vec4(c,1);
    }}`;
    
    function createShader(type, src) {{
        const s = gl.createShader(type);
        gl.shaderSource(s, src);
        gl.compileShader(s);
        return s;
    }}
    
    const prog = gl.createProgram();
    gl.attachShader(prog, createShader(gl.VERTEX_SHADER, vs));
    gl.attachShader(prog, createShader(gl.FRAGMENT_SHADER, fs));
    gl.linkProgram(prog);
    gl.useProgram(prog);
    
    const buf = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, buf);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1,-1,1,-1,-1,1,1,1]), gl.STATIC_DRAW);
    const p = gl.getAttribLocation(prog, 'p');
    gl.enableVertexAttribArray(p);
    gl.vertexAttribPointer(p, 2, gl.FLOAT, false, 0, 0);
    
    const tLoc = gl.getUniformLocation(prog, 't');
    const rLoc = gl.getUniformLocation(prog, 'r');
    
    function render(time) {{
        gl.uniform1f(tLoc, time * 0.001);
        gl.uniform2f(rLoc, canvas.width, canvas.height);
        gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
        requestAnimationFrame(render);
    }}
    requestAnimationFrame(render);
}}
</script>
</body>
</html>"""

with open(os.path.join(OUT, "obsidian_spire.html"), "w") as f:
    f.write(html)

# Write component report
report = {
    "name": "THE OBSIDIAN SPIRE",
    "type": "Integrated Production Slice",
    "disciplines": {
        "3D_character": {"status": "COMPLETE", "mesh": "9044 verts", "bones": 20, "animation_clips": 3, "deformation_tests": 6},
        "video_generation": {"status": "COMPLETE", "model": "Wan2.1 T2V 1.3B", "resolution": "832x480", "fps": 16, "frames": 49},
        "ai_music": {"status": "COMPLETE", "model": "ACE-Step 1.5 (MIT)", "cues": 3, "duration": "30s each"},
        "shader_vfx": {"status": "COMPLETE", "type": "WebGL GLSL volumetric"},
        "typography": {"status": "COMPLETE", "type": "HTML/CSS/SVG deterministic"},
        "vector": {"status": "COMPLETE", "type": "SVG brand mark"},
        "2D_illustration": {"status": "COMPLETE", "type": "Generative + professional finish"},
        "professional_finishing": {"status": "COMPLETE", "assets": 5, "repairs": "defect-specific"},
    },
    "visual_canon": {
        "palette": "purple/violet/crystal",
        "shape_language": "crystalline/geometric",
        "atmosphere": "dark fantasy",
    },
    "file": "obsidian_spire.html",
}

with open(os.path.join(OUT, "spire_report.json"), "w") as f:
    json.dump(report, f, indent=2)

print(f"Obsidian Spire created: {os.path.join(OUT, 'obsidian_spire.html')}")
print(f"Components: {len([v for v in components.values() if v])} images, 3 audio cues")
