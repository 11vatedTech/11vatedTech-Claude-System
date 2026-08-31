"""Build Obsidian Spire integrated showcase."""
import os, base64

OUT = 'artifacts/visual/obsidian-spire'
os.makedirs(OUT, exist_ok=True)

def b64(path):
    if not os.path.exists(path):
        return ''
    with open(path, 'rb') as f:
        return base64.b64encode(f.read()).decode()

imgs = {
    'cf': b64('artifacts/visual/3d-character/golem_front.png'),
    'cs': b64('artifacts/visual/3d-character/golem_side.png'),
    'c3': b64('artifacts/visual/3d-character/golem_threequarter.png'),
    'cp': b64('artifacts/visual/3d-character/golem_power_surge.png'),
    'da': b64('artifacts/visual/3d-character/deform_arms_raised.png'),
    'dk': b64('artifacts/visual/3d-character/deform_knee_bend.png'),
    'dw': b64('artifacts/visual/3d-character/deform_walk_stride.png'),
    'sh': b64('artifacts/visual/finished_v2/shader_volumetric_professional.png'),
    'h2': b64('artifacts/visual/finished_v2/hero_2d_professional.png'),
    'ty': b64('artifacts/visual/finished_v2/typo_editorial_professional.png'),
    've': b64('artifacts/visual/finished_v2/vec_brand_professional.png'),
    'wn': b64('artifacts/visual/video/wan_frame_mid.png'),
}

def img_tag(key, alt=''):
    b = imgs.get(key, '')
    if not b:
        return ''
    return '<img src="data:image/png;base64,' + b + '" alt="' + alt + '" style="width:100%;border-radius:8px;border:1px solid rgba(139,92,246,0.2)">'

char_grid = ''.join(img_tag(k, k) for k in ['cf', 'cs', 'c3', 'cp'])
deform_grid = ''.join(img_tag(k, k) for k in ['da', 'dk', 'dw'])

# Build HTML parts
parts = []
parts.append('<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Obsidian Spire</title>')
parts.append('<style>')
parts.append('*{margin:0;padding:0;box-sizing:border-box}')
parts.append('body{background:#06060a;color:#e8e4dc;font-family:sans-serif}')
parts.append('.hero{height:100vh;display:flex;align-items:center;justify-content:center;text-align:center}')
parts.append('.hero h1{font-size:clamp(3rem,8vw,7rem);font-weight:700;background:linear-gradient(135deg,#8b5cf6,#06b6d4,#f472b6);-webkit-background-clip:text;-webkit-text-fill-color:transparent}')
parts.append('.sub{font-size:1.2rem;color:#94a3b8;margin-top:1rem;letter-spacing:0.1em;text-transform:uppercase}')
parts.append('.sec{padding:4rem 2rem;max-width:1400px;margin:0 auto}')
parts.append('.st{font-size:2rem;font-weight:700;margin-bottom:1.5rem;background:linear-gradient(90deg,#8b5cf6,#06b6d4);-webkit-background-clip:text;-webkit-text-fill-color:transparent}')
parts.append('.g4{display:grid;grid-template-columns:repeat(4,1fr);gap:1rem;margin:1rem 0}')
parts.append('.g3{display:grid;grid-template-columns:repeat(3,1fr);gap:1rem;margin:1rem 0}')
parts.append('.g2{display:grid;grid-template-columns:repeat(2,1fr);gap:2rem;margin:1rem 0}')
parts.append('.c{background:rgba(139,92,246,0.05);border:1px solid rgba(139,92,246,0.15);border-radius:16px;padding:1.5rem}')
parts.append('.c h3{font-size:1.1rem;color:#8b5cf6;margin-bottom:0.5rem}')
parts.append('.c p{font-size:0.9rem;color:#94a3b8;line-height:1.5}')
parts.append('.sb{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:1rem;margin:2rem 0}')
parts.append('.si{background:rgba(139,92,246,0.08);border-radius:8px;padding:1rem;text-align:center}')
parts.append('.si .l{font-size:0.75rem;color:#64748b;text-transform:uppercase;letter-spacing:0.1em}')
parts.append('.si .v{font-size:1.4rem;font-weight:700;color:#22c55e;margin-top:0.25rem}')
parts.append('.pl{display:flex;align-items:center;gap:0.5rem;flex-wrap:wrap;margin:1rem 0;padding:1rem;background:rgba(139,92,246,0.05);border-radius:8px}')
parts.append('.ps{background:rgba(139,92,246,0.15);border:1px solid rgba(139,92,246,0.3);border-radius:6px;padding:0.5rem 1rem;font-size:0.8rem;color:#c4b5fd}')
parts.append('.pa{color:#64748b;font-size:1.2rem}')
parts.append('audio{width:100%;margin-top:0.5rem}')
parts.append('footer{text-align:center;padding:4rem 2rem;color:#475569;font-size:0.8rem;border-top:1px solid rgba(139,92,246,0.1)}')
parts.append('</style></head><body>')

# Hero
parts.append('<section class="hero"><div><h1>THE OBSIDIAN SPIRE</h1>')
parts.append('<p class="sub">Integrated Production Slice - All Disciplines Unified</p></div></section>')

# Scoreboard
parts.append('<section class="sec"><h2 class="st">Production Scoreboard</h2><div class="sb">')
for label, value in [('3D Character', 'COMPLETE'), ('Rigging', '20 Bones'), ('Animation', '3 Clips'),
                     ('Deformation', '6 Tests'), ('Video Gen', 'Wan2.1'), ('AI Music', 'ACE-Step'),
                     ('Shader VFX', 'WebGL'), ('Typography', 'CSS/SVG')]:
    parts.append('<div class="si"><div class="l">' + label + '</div><div class="v">' + value + '</div></div>')
parts.append('</div></section>')

# 3D Character
parts.append('<section class="sec"><h2 class="st">3D Character - Obsidian Golem</h2>')
parts.append('<p style="color:#94a3b8;margin-bottom:1rem">Mesh 9044v | Skeleton 20b | Auto-skin | 6 Deform Tests | 3 Anim Clips | GLB Export</p>')
parts.append('<div class="g4">' + char_grid + '</div>')
parts.append('<h3 style="color:#8b5cf6;margin:1.5rem 0 0.5rem">Deformation Tests</h3>')
parts.append('<div class="g3">' + deform_grid + '</div></section>')

# Pipeline
parts.append('<section class="sec"><h2 class="st">Production Pipeline</h2>')
parts.append('<div class="pl"><span class="ps">Concept</span><span class="pa">-></span><span class="ps">Blender Mesh</span><span class="pa">-></span><span class="ps">PBR Materials</span><span class="pa">-></span><span class="ps">Armature 20b</span><span class="pa">-></span><span class="ps">Auto-skin</span><span class="pa">-></span><span class="ps">Deform QA</span><span class="pa">-></span><span class="ps">Keyframe Anim</span><span class="pa">-></span><span class="ps">EEVEE Render</span><span class="pa">-></span><span class="ps">GLB Export</span></div>')
parts.append('<div class="pl"><span class="ps">Wan2.1 T2V 1.3B</span><span class="pa">-></span><span class="ps">Python 3.12</span><span class="pa">-></span><span class="ps">SDPA Attention</span><span class="pa">-></span><span class="ps">49 Frames</span><span class="pa">-></span><span class="ps">MP4 Export</span></div>')
parts.append('<div class="pl"><span class="ps">ACE-Step 1.5 MIT</span><span class="pa">-></span><span class="ps">2B Turbo+0.6B LM</span><span class="pa">-></span><span class="ps">REST API</span><span class="pa">-></span><span class="ps">3x30s Cues</span><span class="pa">-></span><span class="ps">MP3 Export</span></div>')
parts.append('</section>')

# Video
parts.append('<section class="sec"><h2 class="st">Video - Wan2.1</h2>')
parts.append('<p style="color:#94a3b8;margin-bottom:1rem">832x480 16fps 49frames RTX5070Ti</p>')
parts.append('<div class="g3">' + img_tag('wn', 'wan') + '</div></section>')

# Audio
parts.append('<section class="sec"><h2 class="st">AI Music - ACE-Step 1.5</h2><div class="g3">')
parts.append('<div class="c"><h3>A - Atmospheric</h3><p>D minor 60BPM</p><audio controls src="../audio/acestep_A_atmospheric_v1.mp3"></audio></div>')
parts.append('<div class="c"><h3>B - Action</h3><p>E minor 140BPM</p><audio controls src="../audio/acestep_B_action_v1.mp3"></audio></div>')
parts.append('<div class="c"><h3>C - Menu</h3><p>A minor 75BPM</p><audio controls src="../audio/acestep_C_menu_v1.mp3"></audio></div>')
parts.append('</div></section>')

# Shader + 2D + Typography + Vector
parts.append('<section class="sec"><h2 class="st">Shader + 2D + Typography + Vector</h2><div class="g2">')
parts.append('<div class="c"><h3>Shader VFX</h3>' + img_tag('sh', 'shader') + '</div>')
parts.append('<div class="c"><h3>2D Hero</h3>' + img_tag('h2', 'hero') + '</div></div>')
parts.append('<div class="g2"><div class="c"><h3>Typography</h3>' + img_tag('ty', 'typo') + '</div>')
parts.append('<div class="c"><h3>Vector Identity</h3>' + img_tag('ve', 'vec') + '</div></div></section>')

# Coherence
parts.append('<section class="sec"><h2 class="st">Coherence</h2><div class="g2">')
for title, desc in [('Visual Canon', 'Purple/violet palette + crystalline shape language unified'),
                     ('Material Language', 'Obsidian/crystal materials consistent across 3D and shader'),
                     ('Motion Language', '3D animation + Wan video + CSS shader coherent'),
                     ('Audio Character', 'ACE-Step atmospheric+action+menu dark fantasy mood')]:
    parts.append('<div class="c"><h3>' + title + '</h3><p>' + desc + '</p></div>')
parts.append('</div></section>')

parts.append('<footer>THE OBSIDIAN SPIRE - 11vatedTech Foundry<br>3D+Rigging+Animation+Video+Music+Shader+Typography+Vector+Finishing</footer>')
parts.append('</body></html>')

html = '\n'.join(parts)
with open(os.path.join(OUT, 'obsidian_spire.html'), 'w') as f:
    f.write(html)

print(f'Created obsidian_spire.html ({os.path.getsize(os.path.join(OUT, "obsidian_spire.html"))//1024} KB)')
