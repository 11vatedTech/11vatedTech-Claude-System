import bpy, json, math
from pathlib import Path
from mathutils import Euler

OUT = Path(__file__).parent.parent.parent / "artifacts" / "animation-lab" / "renders"
OUT.mkdir(parents=True, exist_ok=True)

def clear_all():
    for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
    for m in list(bpy.data.materials): bpy.data.materials.remove(m)
    for a in list(bpy.data.actions): bpy.data.actions.remove(a)

def setup():
    s = bpy.context.scene
    s.render.engine = 'BLENDER_EEVEE'
    s.render.resolution_x = 1024; s.render.resolution_y = 576
    s.render.resolution_percentage = 100
    s.render.image_settings.file_format = 'PNG'
    s.render.fps = 24
    s.frame_end = 96
    s.view_settings.view_transform = 'Standard'

def scene():
    # Ground
    bpy.ops.mesh.primitive_plane_add(size=8, location=(0,0,-1.5))
    bpy.context.object.name = "Ground"
    gm = bpy.data.materials.new("G")
    gm.use_nodes = True
    n = gm.node_tree.nodes; l = gm.node_tree.links
    b = n.new('ShaderNodeBsdfPrincipled')
    b.inputs['Base Color'].default_value = (0.4,0.4,0.4,1)
    o = n.new('ShaderNodeOutputMaterial')
    l.new(b.outputs['BSDF'], o.inputs['Surface'])
    bpy.context.object.data.materials.append(gm)
    
    # Pendulum: pivot + bob + arm
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.35, location=(0,0,0))
    bpy.context.object.name = "Bob"
    bob = bpy.context.object
    bm = bpy.data.materials.new("BobMat"); bm.use_nodes = True
    n = bm.node_tree.nodes; l = bm.node_tree.links
    bs = n.new('ShaderNodeBsdfPrincipled')
    bs.inputs['Base Color'].default_value = (0.85,0.85,0.8,1); bs.inputs['Roughness'].default_value = 0.3
    o = n.new('ShaderNodeOutputMaterial')
    l.new(bs.outputs['BSDF'], o.inputs['Surface'])
    bob.data.materials.append(bm)
    
    # Arm (cylinder)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.06, depth=2.2, location=(0,0,1.1))
    arm = bpy.context.object; arm.name = "Arm"
    am = bpy.data.materials.new("ArmMat"); am.use_nodes = True
    n = am.node_tree.nodes; l = am.node_tree.links
    ba = n.new('ShaderNodeBsdfPrincipled')
    ba.inputs['Base Color'].default_value = (0.3,0.3,0.35,1); ba.inputs['Metallic'].default_value = 0.7; ba.inputs['Roughness'].default_value = 0.4
    o = n.new('ShaderNodeOutputMaterial')
    l.new(ba.outputs['BSDF'], o.inputs['Surface'])
    arm.data.materials.append(am)
    
    # Pivot point (empty at top of arm)
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0,0,2.2))
    pivot = bpy.context.object; pivot.name = "Pivot"
    
    # Parent arm and bob to pivot
    arm.parent = pivot
    bob.parent = pivot
    # Bob should move with arm tip
    bob.location = (0,0,-2.2)
    
    # Camera
    bpy.ops.object.camera_add(location=(5,-3,2))
    cam = bpy.context.object
    cam.rotation_euler = Euler((math.radians(75),0,math.radians(55)),'XYZ')
    bpy.context.scene.camera = cam
    
    # Light
    bpy.ops.object.light_add(type='AREA', location=(3,-2,4))
    bpy.context.object.data.energy = 300; bpy.context.object.data.size = 2
    
    return pivot

def animate_weight(pivot, profile):
    """Animate pendulum swing with weight-specific timing/spacing."""
    # Clear existing animation
    pivot.animation_data_clear()
    
    # Keyframe rotation
    pivot.rotation_euler = Euler((0,0,0),'XYZ')
    pivot.keyframe_insert(data_path="rotation_euler", frame=1)
    
    if profile == "light":
        # Light: fast, bouncy, lots of overshoot, quick settle
        # Swing right fast
        pivot.rotation_euler = Euler((0,0,math.radians(35)),'XYZ')
        pivot.keyframe_insert(data_path="rotation_euler", frame=10)
        # Overshoot back
        pivot.rotation_euler = Euler((0,0,math.radians(-28)),'XYZ')
        pivot.keyframe_insert(data_path="rotation_euler", frame=18)
        # Second overshoot
        pivot.rotation_euler = Euler((0,0,math.radians(20)),'XYZ')
        pivot.keyframe_insert(data_path="rotation_euler", frame=25)
        # Settle
        pivot.rotation_euler = Euler((0,0,math.radians(-10)),'XYZ')
        pivot.keyframe_insert(data_path="rotation_euler", frame=32)
        pivot.rotation_euler = Euler((0,0,math.radians(5)),'XYZ')
        pivot.keyframe_insert(data_path="rotation_euler", frame=38)
        pivot.rotation_euler = Euler((0,0,0),'XYZ')
        pivot.keyframe_insert(data_path="rotation_euler", frame=45)
        
        # Add secondary bounce at tip (bob scale)
        bob = bpy.data.objects['Bob']
        bob.animation_data_clear()
        bob.scale = (1,1,1)
        bob.keyframe_insert(data_path="scale", frame=1)
        bob.scale = (0.9,0.9,1.1)  # slight squash on impact
        bob.keyframe_insert(data_path="scale", frame=18)
        bob.scale = (1.05,1.05,0.95)  # stretch on rebound
        bob.keyframe_insert(data_path="scale", frame=25)
        bob.scale = (1,1,1)
        bob.keyframe_insert(data_path="scale", frame=38)
        
    elif profile == "heavy":
        # Heavy: slow, massive, minimal overshoot, long settle
        pivot.rotation_euler = Euler((0,0,math.radians(30)),'XYZ')
        pivot.keyframe_insert(data_path="rotation_euler", frame=20)
        # Small overshoot (heavy doesn't bounce much)
        pivot.rotation_euler = Euler((0,0,math.radians(-15)),'XYZ')
        pivot.keyframe_insert(data_path="rotation_euler", frame=32)
        # Slow return
        pivot.rotation_euler = Euler((0,0,math.radians(8)),'XYZ')
        pivot.keyframe_insert(data_path="rotation_euler", frame=48)
        # Long slow settle
        pivot.rotation_euler = Euler((0,0,math.radians(-3)),'XYZ')
        pivot.keyframe_insert(data_path="rotation_euler", frame=64)
        pivot.rotation_euler = Euler((0,0,math.radians(1)),'XYZ')
        pivot.keyframe_insert(data_path="rotation_euler", frame=78)
        pivot.rotation_euler = Euler((0,0,0),'XYZ')
        pivot.keyframe_insert(data_path="rotation_euler", frame=90)
        
    elif profile == "mechanical":
        # Mechanical: precise, stepped, crisp stops, no organic overshoot
        # Fast move to position
        pivot.rotation_euler = Euler((0,0,math.radians(30)),'XYZ')
        pivot.keyframe_insert(data_path="rotation_euler", frame=12)
        # Hold
        pivot.rotation_euler = Euler((0,0,math.radians(30)),'XYZ')
        pivot.keyframe_insert(data_path="rotation_euler", frame=20)
        # Precise return (no overshoot)
        pivot.rotation_euler = Euler((0,0,0),'XYZ')
        pivot.keyframe_insert(data_path="rotation_euler", frame=30)
        # Hold
        pivot.rotation_euler = Euler((0,0,0),'XYZ')
        pivot.keyframe_insert(data_path="rotation_euler", frame=38)
        # Second cycle - mechanical repeat
        pivot.rotation_euler = Euler((0,0,math.radians(-25)),'XYZ')
        pivot.keyframe_insert(data_path="rotation_euler", frame=50)
        pivot.rotation_euler = Euler((0,0,0),'XYZ')
        pivot.keyframe_insert(data_path="rotation_euler", frame=62)
        
    # Blender 5.2 uses layered actions - interpolation customization
    # requires the new channelbag API. Default bezier handles are fine
    # for light/heavy; mechanical is distinguished by key timing alone.
    pass

def render_sequence(profile):
    """Render 48 frames + FFmpeg video (if available)."""
    seq_dir = OUT / f"frames_{profile}"
    seq_dir.mkdir(parents=True, exist_ok=True)
    bpy.context.scene.render.filepath = str(seq_dir / "frame_")
    
    # Render selected frames (every 2nd frame for video efficiency)
    for frame in range(1, 97, 2):
        bpy.context.scene.frame_set(frame)
        bpy.context.scene.render.filepath = str(seq_dir / f"frame_{frame:04d}.png")
        bpy.ops.render.render(write_still=True)
    
    # Use FFmpeg if available to make video
    import subprocess, shutil
    ffmpeg = shutil.which('ffmpeg') or r'C:\ffmpeg\bin\ffmpeg.exe'
    if Path(ffmpeg).exists() if isinstance(ffmpeg, str) else False:
        video = OUT / f"anim_{profile}.mp4"
        cmd = [ffmpeg, '-framerate', '24', '-i', str(seq_dir/'frame_%04d.png'), '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-y', str(video)]
        subprocess.run(cmd, capture_output=True)
        return video
    
    return None

for profile in ["light", "heavy", "mechanical"]:
    clear_all()
    setup()
    pivot = scene()
    animate_weight(pivot, profile)
    render_sequence(profile)
    print(f"  {profile} rendered")

manifest = {"lab":"Animation Lab","blender":bpy.app.version_string,"profiles":["light","heavy","mechanical"],"fps":24,"frames":96}
with open(OUT/"manifest.json",'w') as f: json.dump(manifest,f,indent=2)
print("Animation Lab complete")