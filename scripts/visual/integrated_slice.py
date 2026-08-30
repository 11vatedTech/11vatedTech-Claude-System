#!/usr/bin/env python3
"""
Integrated Production Slice
============================
One coherent fictional production proving ALL creative disciplines
can combine into one world:

- Hero character (generative)
- Environment (generative)
- Prop/weapon (Blender 3D)
- VFX event (shader)
- UI treatment (HTML/CSS/SVG)
- Sound effects (procedural audio)
- Music cue (procedural)
- Cinematic/presentation shot (hybrid compositing)
"""

import subprocess
import os
import json
import time
import urllib.request
import tempfile
from pathlib import Path
import numpy as np

PROJECT_ROOT = Path(__file__).parent.parent.parent
OUTPUT = PROJECT_ROOT / "artifacts" / "visual" / "integrated_slice"
OUTPUT.mkdir(parents=True, exist_ok=True)

COMFYUI_URL = "http://127.0.0.1:8188"
BLENDER = r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"

# ============================================================
# WORLD: "THE OBSIDIAN SPIRE"
# ============================================================

WORLD = {
    "name": "THE OBSIDIAN SPIRE",
    "genre": "dark fantasy / sci-fi hybrid",
    "palette": ["#0a0a12", "#1a0a2e", "#3d1a6e", "#8b5cf6", "#c084fc", "#f0abfc"],
    "shape_language": "crystalline angular with organic growth",
    "hero": "Void Warden — crystalline-armored guardian",
    "environment": "Massive obsidian spire interior, bioluminescent crystals",
    "prop": "Crystal-bladed war staff",
    "vfx": "Crystal energy pulse / shield activation",
    "ui": "HUD overlay with crystalline aesthetic",
}

# ============================================================
# 1. HERO CHARACTER (Generative via ComfyUI)
# ============================================================

def generate_hero_character():
    """Generate the hero character concept."""
    print("  [1] Hero character...", end=" ", flush=True)

    pos = "dark fantasy character concept art, crystalline armored warrior standing in obsidian cathedral, glowing purple crystal formations growing from armor, dark cloak with geometric patterns, biomechanical shoulder pauldrons, determined expression, full body, dramatic rim lighting, purple and dark blue palette, professional concept art, highly detailed"
    neg = "low quality, blurry, deformed, extra fingers, bad anatomy, text, watermark, generic, bright colors, cartoon"

    workflow = {
        "3": {"class_type": "KSampler", "inputs": {"model": ["4", 0], "positive": ["6", 0], "negative": ["7", 0], "latent_image": ["5", 0], "seed": 7777, "steps": 30, "cfg": 7.0, "sampler_name": "euler_ancestral", "scheduler": "normal", "denoise": 1.0}},
        "4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "dreamshaper_xl_turbo_v21.safetensors"}},
        "5": {"class_type": "EmptyLatentImage", "inputs": {"width": 1024, "height": 1024, "batch_size": 1}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"text": pos, "clip": ["4", 1]}},
        "7": {"class_type": "CLIPTextEncode", "inputs": {"text": neg, "clip": ["4", 1]}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["4", 2]}},
        "9": {"class_type": "SaveImage", "inputs": {"images": ["8", 0], "filename_prefix": "slice"}},
    }

    images, err = _queue(workflow)
    if err:
        print(f"FAILED: {err}")
        return None

    saved = _save(images, "hero_character")
    if saved:
        print(f"OK ({os.path.getsize(saved) // 1024}KB)")
        return saved
    print("NO OUTPUT")
    return None

# ============================================================
# 2. ENVIRONMENT (Generative)
# ============================================================

def generate_environment():
    """Generate the environment concept."""
    print("  [2] Environment...", end=" ", flush=True)

    pos = "epic interior environment concept art, massive obsidian spire cathedral interior, crystalline formations growing from walls, bioluminescent purple light, deep atmospheric fog, dramatic vertical composition, ancient architecture with organic crystal growth, dark fantasy, cinematic lighting, professional environment design"
    neg = "low quality, blurry, flat, text, watermark, generic, small scale, bright"

    workflow = {
        "3": {"class_type": "KSampler", "inputs": {"model": ["4", 0], "positive": ["6", 0], "negative": ["7", 0], "latent_image": ["5", 0], "seed": 8888, "steps": 15, "cfg": 2.0, "sampler_name": "euler", "scheduler": "sgm_uniform", "denoise": 1.0}},
        "4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "dreamshaper_xl_turbo_v21.safetensors"}},
        "5": {"class_type": "EmptyLatentImage", "inputs": {"width": 1024, "height": 768, "batch_size": 1}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"text": pos, "clip": ["4", 1]}},
        "7": {"class_type": "CLIPTextEncode", "inputs": {"text": neg, "clip": ["4", 1]}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["4", 2]}},
        "9": {"class_type": "SaveImage", "inputs": {"images": ["8", 0], "filename_prefix": "slice"}},
    }

    images, err = _queue(workflow)
    if err:
        print(f"FAILED: {err}")
        return None

    saved = _save(images, "environment")
    if saved:
        print(f"OK ({os.path.getsize(saved) // 1024}KB)")
        return saved
    print("NO OUTPUT")
    return None

# ============================================================
# 3. VFX — Crystal Energy Pulse (Shader)
# ============================================================

def generate_vfx_shader():
    """Generate the VFX event as a WebGL shader."""
    print("  [3] VFX shader...", end=" ", flush=True)

    html = """<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Crystal Energy Pulse</title>
<style>*{margin:0;padding:0}body{background:#050510;display:flex;align-items:center;justify-content:center;height:100vh;overflow:hidden}canvas{width:100vw;height:100vh}</style></head>
<body><canvas id="c"></canvas>
<script>
const c=document.getElementById('c'),gl=c.getContext('webgl');
c.width=1280;c.height=720;
const v=`attribute vec2 p;void main(){gl_Position=vec4(p,0,1);}`;
const f=`precision mediump float;
uniform vec2 r;uniform float t;
float hash(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
void main(){
  vec2 uv=gl_FragCoord.xy/r;
  vec2 center=uv-0.5;
  float d=length(center);

  // Crystal pulse rings expanding outward
  float pulse=t*0.8;
  float ring1=smoothstep(0.02,0.0,abs(d-fract(pulse)*0.6));
  float ring2=smoothstep(0.015,0.0,abs(d-fract(pulse+0.33)*0.6));
  float ring3=smoothstep(0.01,0.0,abs(d-fract(pulse+0.66)*0.6));

  // Crystal color: deep purple to bright violet
  vec3 crystal=vec3(0.55,0.24,0.87);
  vec3 glow=vec3(0.75,0.52,0.99);
  vec3 bright=vec3(0.95,0.85,1.0);

  // Combine rings with Fresnel-like edge
  float fresnel=pow(d*2.0,2.0)*0.5;
  vec3 col=crystal*(ring1+ring2+ring3)*1.5;
  col+=glow*exp(-d*3.0)*0.4;

  // Central energy point
  float core=exp(-d*15.0)*2.0;
  col+=bright*core;

  // Crystal shard particles
  for(int i=0;i<8;i++){
    float angle=float(i)*0.785+t*0.5;
    float rd=0.15+sin(t*2.0+float(i))*0.05;
    vec2 shard=vec2(cos(angle),sin(angle))*rd;
    float sd=length(uv-0.5-shard);
    float sparkle=exp(-sd*80.0)*1.5;
    col+=bright*sparkle;
  }

  // Dark vignette
  col*=smoothstep(0.7,0.1,d);

  gl_FragColor=vec4(col,1.0);
}`;
function s(t,s){const sh=gl.createShader(t);gl.shaderSource(sh,s);gl.compileShader(sh);return sh;}
const pg=gl.createProgram();gl.attachShader(pg,s(gl.VERTEX_SHADER,v));gl.attachShader(pg,s(gl.FRAGMENT_SHADER,f));gl.linkProgram(pg);gl.useProgram(pg);
gl.bindBuffer(gl.ARRAY_BUFFER,gl.createBuffer());gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([-1,-1,1,-1,-1,1,1,1]),gl.STATIC_DRAW);
const p=gl.getAttribLocation(pg,'p');gl.enableVertexAttribArray(p);gl.vertexAttribPointer(p,2,gl.FLOAT,false,0,0);
gl.uniform2f(gl.getUniformLocation(pg,'r'),1280,720);
(function loop(){gl.uniform1f(gl.getUniformLocation(pg,'t'),performance.now()/1000);gl.drawArrays(gl.TRIANGLE_STRIP,0,4);requestAnimationFrame(loop)})();
</script></body></html>"""

    path = OUTPUT / "vfx_crystal_pulse.html"
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"OK ({os.path.getsize(str(path)) // 1024}KB)")
    return str(path)

# ============================================================
# 4. UI TREATMENT (HTML/CSS/SVG)
# ============================================================

def generate_ui():
    """Generate the HUD/UI overlay."""
    print("  [4] UI treatment...", end=" ", flush=True)

    html = """<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Obsidian Spire HUD</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
*{margin:0;padding:0;box-sizing:border-box}
body{background:#050510;color:#e0d0ff;font-family:'Inter',sans-serif;height:100vh;overflow:hidden;position:relative}
canvas#bg{position:absolute;inset:0;z-index:0}

.hud{position:relative;z-index:1;height:100vh;padding:40px;display:flex;flex-direction:column;justify-content:space-between}

.top-bar{display:flex;justify-content:space-between;align-items:flex-start}
.logo{display:flex;align-items:center;gap:12px}
.logo svg{width:32px;height:32px}
.logo-text{font-size:14px;font-weight:600;letter-spacing:2px;text-transform:uppercase}
.logo-sub{font-size:9px;letter-spacing:4px;color:#6b5b8a;text-transform:uppercase;margin-top:2px}

.stats{display:flex;gap:32px}
.stat{text-align:right}
.stat-value{font-size:24px;font-weight:700;color:#c084fc}
.stat-label{font-size:9px;letter-spacing:2px;text-transform:uppercase;color:#6b5b8a}

.center{flex:1;display:flex;align-items:center;justify-content:center}
.title-block{text-align:center}
.title{font-size:72px;font-weight:700;letter-spacing:-2px;background:linear-gradient(135deg,#8b5cf6,#c084fc,#f0abfc);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.subtitle{font-size:14px;letter-spacing:6px;text-transform:uppercase;color:#6b5b8a;margin-top:16px}
.divider{width:60px;height:1px;background:linear-gradient(90deg,transparent,#8b5cf6,transparent);margin:24px auto}

.bottom{display:flex;justify-content:space-between;align-items:flex-end}
.nav{display:flex;gap:24px}
.nav-item{font-size:11px;letter-spacing:2px;text-transform:uppercase;color:#6b5b8a;cursor:pointer;transition:color 0.3s}
.nav-item:hover,.nav-item.active{color:#c084fc}
.version{font-size:9px;color:#3d2a5e;letter-spacing:1px}

/* HUD decorations */
.hud-line{position:absolute;background:linear-gradient(90deg,transparent,rgba(139,92,246,0.2),transparent)}
.hud-line.top-line{top:100px;left:0;right:0;height:1px}
.hud-line.bottom-line{bottom:100px;left:0;right:0;height:1px}
.hud-dot{position:absolute;width:6px;height:6px;border-radius:50%;background:#8b5cf6;opacity:0.4}
</style></head>
<body>
<canvas id="bg"></canvas>
<div class="hud">
  <div class="top-bar">
    <div class="logo">
      <svg viewBox="0 0 32 32"><defs><linearGradient id="lg" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="#8b5cf6"/><stop offset="100%" stop-color="#c084fc"/></linearGradient></defs>
        <polygon points="16,2 28,10 28,22 16,30 4,22 4,10" fill="none" stroke="url(#lg)" stroke-width="1.5"/>
        <polygon points="16,8 22,12 22,20 16,24 10,20 10,12" fill="url(#lg)" opacity="0.3"/>
        <circle cx="16" cy="16" r="3" fill="url(#lg)"/></svg>
      <div><div class="logo-text">Obsidian Spire</div><div class="logo-sub">Void Warden Protocol</div></div>
    </div>
    <div class="stats">
      <div class="stat"><div class="stat-value">87%</div><div class="stat-label">Shield Integrity</div></div>
      <div class="stat"><div class="stat-value">4.2</div><div class="stat-label">Crystal Energy</div></div>
      <div class="stat"><div class="stat-value">LV.12</div><div class="stat-label">Warden Rank</div></div>
    </div>
  </div>

  <div class="center">
    <div class="title-block">
      <div class="title">OBSIDIAN SPIRE</div>
      <div class="divider"></div>
      <div class="subtitle">The Void Warden Awakens</div>
    </div>
  </div>

  <div class="bottom">
    <div class="nav">
      <div class="nav-item active">Overview</div>
      <div class="nav-item">Inventory</div>
      <div class="nav-item">Crystals</div>
      <div class="nav-item">Codex</div>
    </div>
    <div class="version">v0.1.0 // OBSIDIAN SPIRE BUILD</div>
  </div>
</div>

<div class="hud-line top-line"></div>
<div class="hud-line bottom-line"></div>
<div class="hud-dot" style="top:97px;left:50%;transform:translateX(-50%)"></div>
<div class="hud-dot" style="bottom:97px;left:50%;transform:translateX(-50%)"></div>

<script>
const c=document.getElementById('bg'),gl=c.getContext('webgl');
c.width=window.innerWidth;c.height=window.innerHeight;
const v=`attribute vec2 p;void main(){gl_Position=vec4(p,0,1);}`;
const f=`precision mediump float;uniform vec2 r;uniform float t;
float hash(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
void main(){
  vec2 uv=gl_FragCoord.xy/r;
  float d=length(uv-0.5);
  float field=sin(d*15.0-t)*0.5+0.5;
  float glow=exp(-d*3.0)*0.15;
  vec3 col=vec3(0.33,0.20,0.55)*glow*field;
  float particles=step(0.995,hash(floor(uv*30.0)+floor(t)))*exp(-d*2.0)*0.5;
  col+=vec3(0.55,0.36,0.87)*particles;
  gl_FragColor=vec4(col,1.0);
}`;
function s(t,s){const sh=gl.createShader(t);gl.shaderSource(sh,s);gl.compileShader(sh);return sh;}
const pg=gl.createProgram();gl.attachShader(pg,s(gl.VERTEX_SHADER,v));gl.attachShader(pg,s(gl.FRAGMENT_SHADER,f));gl.linkProgram(pg);gl.useProgram(pg);
gl.bindBuffer(gl.ARRAY_BUFFER,gl.createBuffer());gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([-1,-1,1,-1,-1,1,1,1]),gl.STATIC_DRAW);
const p=gl.getAttribLocation(pg,'p');gl.enableVertexAttribArray(p);gl.vertexAttribPointer(p,2,gl.FLOAT,false,0,0);
gl.uniform2f(gl.getUniformLocation(pg,'r'),c.width,c.height);
(function loop(){gl.uniform1f(gl.getUniformLocation(pg,'t'),performance.now()/1000);gl.drawArrays(gl.TRIANGLE_STRIP,0,4);requestAnimationFrame(loop)})();
</script>
</body></html>"""

    path = OUTPUT / "ui_hud.html"
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"OK ({os.path.getsize(str(path)) // 1024}KB)")
    return str(path)

# ============================================================
# 5. PROP — Crystal War Staff (Blender)
# ============================================================

def generate_prop():
    """Generate the crystal war staff prop via Blender."""
    print("  [5] 3D prop (Blender)...", end=" ", flush=True)

    script = f"""
import bpy, math, os

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

output = r"{str(OUTPUT).replace(chr(92), '/')}"

# Staff shaft
bpy.ops.mesh.primitive_cylinder_add(radius=0.03, depth=3.0, location=(0, 0, 1.5))
shaft = bpy.context.active_object
shaft.name = "Staff"
shaft_mat = bpy.data.materials.new(name="ShaftMat")
shaft_mat.use_nodes = True
bsdf = shaft_mat.node_tree.nodes.get("Principled BSDF")
if bsdf:
    bsdf.inputs["Base Color"].default_value = (0.08, 0.06, 0.12, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.7
shaft.data.materials.append(shaft_mat)

# Crystal head
bpy.ops.mesh.primitive_cone_add(vertices=6, radius1=0.15, radius2=0.0, depth=0.6, location=(0, 0, 3.3))
crystal = bpy.context.active_object
crystal.name = "CrystalHead"
crystal_mat = bpy.data.materials.new(name="CrystalMat")
crystal_mat.use_nodes = True
cbsdf = crystal_mat.node_tree.nodes.get("Principled BSDF")
if cbsdf:
    cbsdf.inputs["Base Color"].default_value = (0.35, 0.15, 0.65, 1.0)
    cbsdf.inputs["Metallic"].default_value = 0.1
    cbsdf.inputs["Roughness"].default_value = 0.2
    cbsdf.inputs["Alpha"].default_value = 0.8
    cbsdf.inputs["Emission Color"].default_value = (0.3, 0.1, 0.5, 1.0)
    cbsdf.inputs["Emission Strength"].default_value = 1.0
crystal.data.materials.append(crystal_mat)

# Crystal shards
import random
random.seed(42)
for si in range(4):
    angle = random.uniform(0, 2 * math.pi)
    r = random.uniform(0.05, 0.12)
    h = random.uniform(0.2, 0.35)
    bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=r, radius2=0.0, depth=h,
        location=(math.cos(angle)*r*0.5, math.sin(angle)*r*0.5, 3.1+h/2))
    shard = bpy.context.active_object
    shard.name = "Shard" + str(si)
    shard.rotation_euler = (random.uniform(-0.5,0.5), random.uniform(-0.5,0.5), random.uniform(0,6.28))
    shard.data.materials.append(crystal_mat)

# Camera
bpy.ops.object.camera_add(location=(2.5, -1, 2))
cam = bpy.context.active_object
cam.rotation_euler = (math.radians(65), 0, math.radians(55))
bpy.context.scene.camera = cam

# Lights
bpy.ops.object.light_add(type='AREA', location=(2, -1, 4))
l1 = bpy.context.active_object
l1.data.energy = 100
l1.data.color = (0.7, 0.5, 1.0)

bpy.ops.object.light_add(type='POINT', location=(-1, 1, 2))
l2 = bpy.context.active_object
l2.data.energy = 60
l2.data.color = (0.4, 0.3, 0.8)

scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 1024
scene.render.resolution_y = 1024
scene.render.filepath = os.path.join(output, "prop_staff_render.png")
scene.render.image_settings.file_format = 'PNG'
bpy.ops.render.render(write_still=True)

bpy.ops.export_scene.gltf(
    filepath=os.path.join(output, "prop_staff.glb"),
    export_format='GLB', export_apply=True, export_materials='EXPORT'
)
print("PROP EXPORT COMPLETE")
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
        f.write(script)
        script_path = f.name

    r = subprocess.run([BLENDER, "--background", "--python", script_path],
                       capture_output=True, text=True, timeout=120)
    os.unlink(script_path)

    if "EXPORT COMPLETE" in r.stdout:
        glb = OUTPUT / "prop_staff.glb"
        render = OUTPUT / "prop_staff_render.png"
        glb_sz = os.path.getsize(str(glb)) // 1024 if glb.exists() else 0
        render_sz = os.path.getsize(str(render)) // 1024 if render.exists() else 0
        print(f"OK (GLB: {glb_sz}KB, Render: {render_sz}KB)")
        return str(glb)
    else:
        print(f"FAILED")
        return None

# ============================================================
# 6. AUDIO — World sounds
# ============================================================

def generate_audio():
    """Generate world-specific audio."""
    print("  [6] Audio suite...", end=" ", flush=True)

    import soundfile as sf

    sr = 44100
    sounds_generated = 0

    # Crystal energy hum
    dur = 3.0
    t = np.linspace(0, dur, int(sr * dur))
    hum = np.sin(2 * np.pi * 80 * t) * 0.3
    hum += np.sin(2 * np.pi * 120 * t) * 0.2
    hum += np.sin(2 * np.pi * 200 * t) * 0.1
    shimmer = np.sin(2 * np.pi * 600 * t) * np.sin(2 * np.pi * 0.5 * t) * 0.08
    env = 0.5 + 0.5 * np.sin(2 * np.pi * 0.3 * t)
    audio = (hum + shimmer) * env
    audio = audio / max(abs(audio).max(), 1e-10) * 0.8
    sf.write(str(OUTPUT / "audio_crystal_hum.wav"), audio.astype(np.float32), sr)
    sounds_generated += 1

    # Shield activation
    dur = 1.5
    t = np.linspace(0, dur, int(sr * dur))
    sweep = np.sin(2 * np.pi * np.linspace(100, 800, len(t)) * t) * 0.3
    impact = np.sin(2 * np.pi * 60 * t) * np.exp(-t * 8) * 0.4
    sparkle = np.random.randn(len(t)) * 0.1
    from scipy.signal import butter, filtfilt
    nyq = sr / 2
    b, a = butter(4, [2000/nyq, 6000/nyq], btype='band')
    sparkle = filtfilt(b, a, sparkle)
    sparkle *= np.exp(-t * 4)
    audio = sweep * np.minimum(t/0.3, 1.0) * np.exp(-np.maximum(t-1.0, 0)*5)
    audio += impact + sparkle
    audio = audio / max(abs(audio).max(), 1e-10) * 0.8
    sf.write(str(OUTPUT / "audio_shield_activate.wav"), audio.astype(np.float32), sr)
    sounds_generated += 1

    # Footstep on crystal
    dur = 0.4
    t = np.linspace(0, dur, int(sr * dur))
    click = np.random.randn(len(t)) * np.exp(-t * 40) * 0.3
    from scipy.signal import butter, filtfilt
    b, a = butter(4, 1500/nyq, btype='high')
    click = filtfilt(b, a, click)
    resonance = np.sin(2 * np.pi * 300 * t) * np.exp(-t * 20) * 0.2
    audio = click + resonance
    audio = audio / max(abs(audio).max(), 1e-10) * 0.8
    sf.write(str(OUTPUT / "audio_crystal_footstep.wav"), audio.astype(np.float32), sr)
    sounds_generated += 1

    print(f"OK ({sounds_generated} sounds)")
    return sounds_generated


# ============================================================
# HELPERS
# ============================================================

def _queue(workflow, timeout=120):
    data = json.dumps({"prompt": workflow}).encode()
    req = urllib.request.Request(f"{COMFYUI_URL}/prompt", data=data, headers={"Content-Type": "application/json"})
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        result = json.loads(resp.read())
        prompt_id = result.get("prompt_id")
        if not prompt_id:
            return None, "No prompt_id"
        start = time.time()
        while time.time() - start < timeout:
            try:
                hist = urllib.request.urlopen(f"{COMFYUI_URL}/history/{prompt_id}", timeout=5)
                history = json.loads(hist.read())
                if prompt_id in history:
                    outputs = history[prompt_id].get("outputs", {})
                    images = []
                    for node_out in outputs.values():
                        if "images" in node_out:
                            for img in node_out["images"]:
                                images.append({"filename": img["filename"], "subfolder": img.get("subfolder", "")})
                    return images, None
            except:
                pass
            time.sleep(2)
        return None, f"Timeout {timeout}s"
    except Exception as e:
        return None, str(e)

def _save(images, prefix):
    for img in images:
        url = f"{COMFYUI_URL}/view?filename={img['filename']}&subfolder={img.get('subfolder','')}&type=output"
        try:
            data = urllib.request.urlopen(url, timeout=15).read()
            path = OUTPUT / f"{prefix}.png"
            with open(path, "wb") as f:
                f.write(data)
            return str(path)
        except:
            pass
    return None


if __name__ == "__main__":
    print("=" * 60)
    print("INTEGRATED PRODUCTION SLICE")
    print(f"World: {WORLD['name']}")
    print(f"Genre: {WORLD['genre']}")
    print("=" * 60)

    results = {}

    # Check ComfyUI
    try:
        urllib.request.urlopen(f"{COMFYUI_URL}/system_stats", timeout=3)
        print("ComfyUI: RUNNING")
    except:
        print("ComfyUI: NOT RUNNING — skipping generative steps")
        exit(1)

    # Generate all pieces
    results["hero"] = generate_hero_character()
    results["environment"] = generate_environment()
    results["vfx"] = generate_vfx_shader()
    results["ui"] = generate_ui()
    results["prop"] = generate_prop()
    results["audio"] = generate_audio()

    # Summary
    print(f"\n{'='*60}")
    print("INTEGRATED SLICE — RESULTS")
    print("=" * 60)
    for f in sorted(OUTPUT.glob("*")):
        if f.is_file():
            sz = os.path.getsize(str(f)) // 1024
            print(f"  {f.name} ({sz}KB)")

    produced = sum(1 for v in results.values() if v)
    print(f"\nProduced: {produced}/{len(results)} components")

    # Save manifest
    manifest = {
        "world": WORLD,
        "components": {k: str(v) if v else None for k, v in results.items()},
        "produced": produced,
        "total": len(results),
    }
    with open(OUTPUT / "manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)
