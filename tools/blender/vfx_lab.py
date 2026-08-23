"""
VFX Lab — Apprenticeship Wave 001
3 visual languages for ENERGY IMPACT: physical/magical/technological
Blender 5.2 EEVEE, 96 frames, frame sequences
"""
import bpy, math, json
from pathlib import Path
from mathutils import Vector, Euler

OUT = Path(__file__).parent.parent.parent / "artifacts" / "vfx-lab" / "renders"
OUT.mkdir(parents=True, exist_ok=True)

def clear_all():
    for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
    for m in list(bpy.data.materials): bpy.data.materials.remove(m)

def setup():
    s = bpy.context.scene
    s.render.engine = 'BLENDER_EEVEE'
    s.render.resolution_x = 1024; s.render.resolution_y = 576
    s.render.resolution_percentage = 100
    s.render.fps = 24; s.frame_end = 96
    s.render.image_settings.file_format = 'PNG'
    s.view_settings.view_transform = 'Standard'
    # Camera
    bpy.ops.object.camera_add(location=(0,-6,3))
    cam = bpy.context.object
    cam.rotation_euler = Euler((math.radians(80),0,0),'XYZ')
    bpy.context.scene.camera = cam
    # Ground reference
    bpy.ops.mesh.primitive_plane_add(size=10, location=(0,0,-0.5))
    gm = bpy.data.materials.new("Gnd"); gm.use_nodes = True
    n=gm.node_tree.nodes; l=gm.node_tree.links
    b=n.new('ShaderNodeBsdfPrincipled'); b.inputs['Base Color'].default_value=(0.2,0.2,0.25,1)
    o=n.new('ShaderNodeOutputMaterial'); l.new(b.outputs['BSDF'],o.inputs['Surface'])
    bpy.context.object.data.materials.append(gm)
    # Ambient light
    bpy.ops.object.light_add(type='AREA', location=(0,-3,4))
    bpy.context.object.data.energy = 50; bpy.context.object.data.size = 3

def create_impact_emitter():
    """Empty at origin that particles burst from."""
    bpy.ops.object.empty_add(type='SPHERE', location=(0,0,1.5))
    return bpy.context.object

def vfx_physical():
    """Physical/debris impact: fast burst, gravity, bounce, dissipation via fade."""
    emitter = create_impact_emitter()
    emitter.name = "Emitter_Physical"
    
    # Create debris particles using icosphere instancing
    particles = []
    for i in range(30):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.06, location=(0,0,1.5))
        p = bpy.context.object
        p.name = f"Debris_{i}"
        # Random velocity outward + upward
        angle = (i / 30) * math.pi * 2
        speed = 3.0 + (i % 5) * 0.8  # varied speed
        p.location = (0,0,1.5)
        # Animate
        p.keyframe_insert(data_path="location", frame=10)  # birth at frame 10
        p.location = (
            math.cos(angle) * speed * 2,
            math.sin(angle) * speed * 2,
            1.5 + speed * 1.5
        )
        p.keyframe_insert(data_path="location", frame=22)  # peak
        # Fall to ground
        p.location = (math.cos(angle) * speed * 3, math.sin(angle) * speed * 3, 0.0)
        p.keyframe_insert(data_path="location", frame=40)  # hit ground
        # Settle
        p.location = (math.cos(angle) * speed * 3.5, math.sin(angle) * speed * 3.5, 0.0)
        p.keyframe_insert(data_path="location", frame=60)
        # Hide after
        p.hide_render = True
        p.keyframe_insert(data_path="hide_render", frame=60)
        
        # Material with emission then fade
        m = bpy.data.materials.new(f"DebrisMat_{i}")
        m.use_nodes = True; n=m.node_tree.nodes; l=m.node_tree.links
        b=n.new('ShaderNodeBsdfPrincipled'); b.inputs['Base Color'].default_value=(0.7,0.5,0.3,1)
        b.inputs['Roughness'].default_value=0.5
        b.inputs['Emission Color'].default_value=(1.0,0.6,0.2,1)
        b.inputs['Emission Strength'].default_value=2.0
        # Animate emission fade
        b.inputs['Emission Strength'].default_value = 2.0
        b.inputs['Emission Strength'].keyframe_insert('default_value', frame=10)
        b.inputs['Emission Strength'].default_value = 0.5
        b.inputs['Emission Strength'].keyframe_insert('default_value', frame=40)
        b.inputs['Emission Strength'].default_value = 0.0
        b.inputs['Emission Strength'].keyframe_insert('default_value', frame=60)
        o=n.new('ShaderNodeOutputMaterial'); l.new(b.outputs['BSDF'],o.inputs['Surface'])
        p.data.materials.append(m)
        particles.append(p)
    
    # Impact flash at origin
    bpy.ops.object.light_add(type='POINT', location=(0,0,1.5))
    flash = bpy.context.object
    flash.data.energy = 5000
    flash.data.keyframe_insert('energy', frame=10)
    flash.data.energy = 5000
    flash.data.keyframe_insert('energy', frame=11)
    flash.data.energy = 0
    flash.data.keyframe_insert('energy', frame=18)
    
    return particles

def vfx_magical():
    """Magical/energy impact: upward swirl, glow, no gravity, slow dissipation."""
    emitter = create_impact_emitter()
    emitter.name = "Emitter_Magical"
    
    particles = []
    for i in range(40):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.04, location=(0,0,1.5))
        p = bpy.context.object
        p.name = f"Spark_{i}"
        angle = (i / 40) * math.pi * 2
        height = 1.5 + (i % 6) * 0.3
        
        p.location = (0,0,1.5)
        p.keyframe_insert(data_path="location", frame=15)  # birth
        # Float upward with spiral
        for frame, t in [(30, 0.3), (50, 0.6), (75, 1.0)]:
            radius = 2.5 * t
            spiral_angle = angle + t * math.pi * 3
            p.location = (math.cos(spiral_angle)*radius, math.sin(spiral_angle)*radius, 1.5 + t*4)
            p.keyframe_insert(data_path="location", frame=frame)
        
        p.hide_render = True
        p.keyframe_insert(data_path="hide_render", frame=80)
        
        m = bpy.data.materials.new(f"SparkMat_{i}")
        m.use_nodes = True; n=m.node_tree.nodes; l=m.node_tree.links
        b=n.new('ShaderNodeBsdfPrincipled'); b.inputs['Base Color'].default_value=(0.3,0.6,1.0,1)
        b.inputs['Roughness'].default_value=0.2
        b.inputs['Emission Color'].default_value=(0.4,0.7,1.0,1)
        b.inputs['Emission Strength'].default_value=3.0
        # Fade emission
        for f, val in [(15,3.0),(35,2.0),(55,0.8),(80,0.0)]:
            b.inputs['Emission Strength'].default_value = val
            b.inputs['Emission Strength'].keyframe_insert('default_value', frame=f)
        o=n.new('ShaderNodeOutputMaterial'); l.new(b.outputs['BSDF'],o.inputs['Surface'])
        p.data.materials.append(m)
        particles.append(p)
    
    return particles

def vfx_technological():
    """Technological/signal impact: geometric grid burst, precise timing, digital fade."""
    emitter = create_impact_emitter()
    emitter.name = "Emitter_Tech"
    
    particles = []
    for i in range(25):
        # Cube bursts (geometric, angular)
        bpy.ops.mesh.primitive_cube_add(size=0.08, location=(0,0,1.5))
        p = bpy.context.object
        p.name = f"Tech_{i}"
        angle = (i / 25) * math.pi * 2
        grid_step = 1.5 + (i % 5) * 0.7
        
        p.location = (0,0,1.5)
        p.keyframe_insert(data_path="location", frame=8)  # sharp birth
        
        # Grid-like expansion
        for frame, scale in [(16,0.5),(28,1.0)]:
            px = math.cos(angle) * grid_step * scale
            py = math.sin(angle) * grid_step * scale
            pz = 1.5 + scale * 1.5
            p.location = (px, py, pz)
            p.keyframe_insert(data_path="location", frame=frame)
        
        # Hold then vanish
        p.location = (p.location[0], p.location[1], p.location[2])
        p.keyframe_insert(data_path="location", frame=40)
        p.hide_render = True
        p.keyframe_insert(data_path="hide_render", frame=42)
        
        m = bpy.data.materials.new(f"TechMat_{i}")
        m.use_nodes = True; n=m.node_tree.nodes; l=m.node_tree.links
        b=n.new('ShaderNodeBsdfPrincipled'); b.inputs['Base Color'].default_value=(0.1,0.9,0.5,1)
        b.inputs['Roughness'].default_value=0.1
        b.inputs['Emission Color'].default_value=(0.1,0.9,0.5,1)
        b.inputs['Emission Strength'].default_value=2.5
        for f, val in [(8,2.5),(28,1.5),(40,0.0)]:
            b.inputs['Emission Strength'].default_value = val
            b.inputs['Emission Strength'].keyframe_insert('default_value', frame=f)
        o=n.new('ShaderNodeOutputMaterial'); l.new(b.outputs['BSDF'],o.inputs['Surface'])
        p.data.materials.append(m)
        particles.append(p)
    
    return particles

def render_frames(profile):
    seq_dir = OUT / f"frames_{profile}"
    seq_dir.mkdir(parents=True, exist_ok=True)
    for frame in range(1, 97, 2):
        bpy.context.scene.frame_set(frame)
        bpy.context.scene.render.filepath = str(seq_dir / f"frame_{frame:04d}.png")
        bpy.ops.render.render(write_still=True)
    return seq_dir

# Render all 3 variants
for profile, vfx_fn in [("physical", vfx_physical), ("magical", vfx_magical), ("technological", vfx_technological)]:
    clear_all()
    setup()
    vfx_fn()
    render_frames(profile)
    print(f"  {profile} rendered ({len(list((OUT/f'frames_{profile}').glob('*.png')))} frames)")

manifest = {"lab":"VFX Lab","blender":bpy.app.version_string,"variants":["physical","magical","technological"],"frames":96}
with open(OUT/"manifest.json",'w') as f: json.dump(manifest,f,indent=2)
print("VFX Lab complete")