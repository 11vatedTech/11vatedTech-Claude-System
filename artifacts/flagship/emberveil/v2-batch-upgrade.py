"""Emberveil v2 Production Upgrade — single-session batch.

Opens the v1 session.blend (before material ops corrupted it),
applies improved materials, motivated lighting, and re-exports.
"""
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

SESSION = Path(__file__).parent / "session.blend"
OUT_DIR = Path(__file__).parent


def log(msg):
    print(f"[v2-upgrade] {msg}")


# ── Helper: Lathe mesh (must be defined before main logic) ───────
def _lathe(name, profile, segments, location, inset=0.0):
    """Create a mesh by rotating a 2D profile around Z axis."""
    verts = []
    faces = []
    for i in range(segments):
        angle = 2 * math.pi * i / segments
        cos_a, sin_a = math.cos(angle), math.sin(angle)
        for r, z in profile:
            r_adj = r - inset
            verts.append((r_adj * cos_a, r_adj * sin_a, z))

    for i in range(segments):
        n = len(profile)
        next_i = (i + 1) % segments
        for j in range(n - 1):
            v0 = i * n + j
            v1 = i * n + j + 1
            v2 = next_i * n + j + 1
            v3 = next_i * n + j
            faces.append((v0, v1, v2, v3))

    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.location = location
    return obj


def _create_filigree(name, z_rotation_deg):
    """Create a curved filigree arc strip."""
    arc_profile = [(0.92, 0.15), (1.08, 0.25), (1.2, 0.5),
                   (1.2, 0.75), (1.08, 0.95)]
    verts = []
    faces = []
    arc_steps = 16
    strip_width = 0.025

    for i in range(arc_steps):
        t = i / (arc_steps - 1)
        angle_z = math.radians(100) + t * math.radians(160)
        height = 0.15 + t * 0.85
        surface_r = 0.0
        for r, z in arc_profile:
            if abs(z - height) < 0.2:
                surface_r = r
                break
        if surface_r == 0:
            surface_r = 0.92 + t * 0.28

        for sign in [-1, 1]:
            r = surface_r + sign * strip_width
            x = r * math.cos(angle_z)
            y = r * math.sin(angle_z)
            verts.append((x, y, height))

    for i in range(arc_steps - 1):
        v0 = i * 2
        v1 = i * 2 + 1
        v2 = (i + 1) * 2 + 1
        v3 = (i + 1) * 2
        faces.append((v0, v1, v2, v3))

    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.rotation_euler = (0, 0, math.radians(z_rotation_deg))
    return obj


# ── Materials ────────────────────────────────────────────────────

def assign_material(obj_name, mat):
    obj = bpy.data.objects.get(obj_name)
    if obj and obj.type == 'MESH':
        obj.data.materials.clear()
        obj.data.materials.append(mat)
        log(f"  Assigned '{mat.name}' to '{obj_name}'")

def make_glass_material():
    mat = bpy.data.materials.new("Emberveil_Glass_v2")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (1.0, 0.702, 0.278, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.05
    if "Transmission Weight" in bsdf.inputs:
        bsdf.inputs["Transmission Weight"].default_value = 0.95
    if "IOR" in bsdf.inputs:
        bsdf.inputs["IOR"].default_value = 1.5
    if "Subsurface Weight" in bsdf.inputs:
        bsdf.inputs["Subsurface Weight"].default_value = 0.3
    if "Subsurface Radius" in bsdf.inputs:
        bsdf.inputs["Subsurface Radius"].default_value = (1.0, 0.7, 0.3)
    return mat

def make_ember_material():
    mat = bpy.data.materials.new("Emberveil_Core_v2")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (1.0, 0.478, 0.102, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.3
    if "Emission Color" in bsdf.inputs:
        bsdf.inputs["Emission Color"].default_value = (1.0, 0.478, 0.102, 1.0)
        bsdf.inputs["Emission Strength"].default_value = 25.0
    if "Subsurface Weight" in bsdf.inputs:
        bsdf.inputs["Subsurface Weight"].default_value = 0.5
    if "Subsurface Radius" in bsdf.inputs:
        bsdf.inputs["Subsurface Radius"].default_value = (1.0, 0.3, 0.05)
    return mat

def make_brass_material():
    mat = bpy.data.materials.new("Emberveil_Brass_v2")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (0.722, 0.525, 0.043, 1.0)
    bsdf.inputs["Metallic"].default_value = 0.9
    bsdf.inputs["Roughness"].default_value = 0.25
    if "Emission Color" in bsdf.inputs:
        bsdf.inputs["Emission Color"].default_value = (0.3, 0.2, 0.02, 1.0)
        bsdf.inputs["Emission Strength"].default_value = 0.1
    return mat

def make_plinth_material():
    mat = bpy.data.materials.new("Emberveil_Plinth_v2")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (0.102, 0.102, 0.102, 1.0)
    bsdf.inputs["Metallic"].default_value = 0.0
    bsdf.inputs["Roughness"].default_value = 0.4
    return mat


# ── Main Logic ───────────────────────────────────────────────────
objects = {o.name: o for o in bpy.data.objects}
mesh_names = [n for n, o in objects.items() if o.type == 'MESH']
log(f"Scene: {len(objects)} objects, {len(mesh_names)} meshes: {mesh_names}")

if len(mesh_names) < 3:
    log("Rebuilding scene from v1 specs...")
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = 96

    world = scene.world or bpy.data.worlds.new("World")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs[0].default_value = (0.02, 0.02, 0.05, 1.0)

    bpy.ops.object.camera_add(location=(6.0, -7.0, 3.0))
    cam = bpy.context.active_object
    cam.name = "Cam"
    cam.rotation_euler = (math.radians(79), 0, math.radians(41))
    cam.data.lens = 50
    scene.camera = cam

    bpy.ops.object.light_add(type='SUN', location=(-4, -6, 10))
    cool = bpy.context.active_object
    cool.name = "CoolRim"
    cool.data.energy = 0.8

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0))
    root = bpy.context.active_object
    root.name = "Emberveil_root"

    bell_profile = [
        (0.6, 1.2), (0.72, 1.15), (0.84, 1.05), (0.96, 0.9),
        (1.05, 0.75), (1.11, 0.6), (1.14, 0.45), (1.14, 0.3),
        (1.11, 0.18), (1.05, 0.1), (0.96, 0.05), (0.84, 0.02),
        (0.72, 0.0), (0.6, 0.0)
    ]
    _lathe("glass_bell", bell_profile, 48, (0, 0, 0))

    core_profile = [
        (0.0, 0.0), (0.06, 0.02), (0.27, 0.2), (0.33, 0.4),
        (0.3, 0.6), (0.24, 0.72), (0.15, 0.78), (0.06, 0.8),
        (0.0, 0.8)
    ]
    _lathe("ember_core", core_profile, 24, (0, 0, 0))

    band_profile = list(bell_profile)
    _lathe("brass_band", band_profile, 48, (0, 0, 0.85), inset=0.015)

    _create_filigree("filigree_arc", 0)
    _create_filigree("filigree_arc_01", 120)
    _create_filigree("filigree_arc_02", 240)

    plinth_profile = [(3.4, 0.0), (3.6, 0.0), (3.6, 0.12), (3.4, 0.12)]
    _lathe("plinth", plinth_profile, 96, (0, 0, 0.0))

    for name in ["glass_bell", "ember_core", "brass_band",
                  "filigree_arc", "filigree_arc_01", "filigree_arc_02", "plinth"]:
        obj = bpy.data.objects.get(name)
        if obj:
            obj.parent = root

    log(f"Rebuilt: {len(bpy.data.objects)} objects")
else:
    log("Scene intact, upgrading materials only")

log("Creating materials...")
glass_mat = make_glass_material()
ember_mat = make_ember_material()
brass_mat = make_brass_material()
plinth_mat = make_plinth_material()

log("Assigning materials...")
assign_material("glass_bell", glass_mat)
assign_material("ember_core", ember_mat)
assign_material("brass_band", brass_mat)
for name in ["filigree_arc", "filigree_arc_01", "filigree_arc_02"]:
    assign_material(name, brass_mat)
assign_material("plinth", plinth_mat)

# ── Motivated Lighting ───────────────────────────────────────────
log("Adding motivated lighting...")

# EmberCoreLight — warm point light at ember position
bpy.ops.object.light_add(type='POINT', location=(0, 0, 0.85))
ember_light = bpy.context.active_object
ember_light.name = "EmberCoreLight"
ember_light.data.energy = 150
ember_light.data.color = (1.0, 0.48, 0.1)

# FillLight — soft warm fill
bpy.ops.object.light_add(type='POINT', location=(1.5, -2.0, -0.3))
fill_light = bpy.context.active_object
fill_light.name = "FillLight"
fill_light.data.energy = 30
fill_light.data.color = (0.4, 0.25, 0.1)

# ── Save ─────────────────────────────────────────────────────────
log("Saving session...")
bpy.ops.wm.save_as_mainfile(filepath=str(SESSION))

# ── Export GLB ───────────────────────────────────────────────────
glb_path = OUT_DIR / "emberveil.glb"
log(f"Exporting GLB to {glb_path}...")
bpy.ops.export_scene.gltf(
    filepath=str(glb_path),
    export_format="GLB",
    use_selection=False,
    export_apply=True,
)
glb_size = glb_path.stat().st_size if glb_path.exists() else 0
log(f"GLB exported: {glb_size} bytes")

# ── Render turntable ─────────────────────────────────────────────
log("Rendering turntable...")
scene = bpy.context.scene
target = Vector((0, 0, 0.8))
radius = 5.0
height = 1.8
frames = 24

bpy.ops.object.camera_add(location=(target.x + radius, target.y, target.z + height))
tt_cam = bpy.context.active_object
tt_cam.name = "TurntableCam"
tt_cam.data.lens = 50
scene.camera = tt_cam

scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.engine = "CYCLES"
scene.cycles.samples = 128
scene.render.image_settings.file_format = "PNG"

turntable_dir = OUT_DIR / "turntable"
turntable_dir.mkdir(exist_ok=True)

for i in range(frames):
    angle = 2 * math.pi * i / frames
    tt_cam.location = (
        target.x + radius * math.cos(angle),
        target.y + radius * math.sin(angle),
        target.z + height
    )
    direction = target - tt_cam.location
    tt_cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    scene.frame_set(0)
    png = turntable_dir / f"turntable-{i:03d}.png"
    scene.render.filepath = str(png)
    bpy.ops.render.render(write_still=True)
    log(f"  Frame {i+1}/{frames}")

# ── Render beauty shot ───────────────────────────────────────────
log("Rendering beauty shot...")
scene.cycles.samples = 256
bpy.ops.object.camera_add(location=(4.5, -4.5, 2.5))
beauty_cam = bpy.context.active_object
beauty_cam.name = "BeautyCam"
beauty_cam.data.lens = 85
beauty_dir = target - beauty_cam.location
beauty_cam.rotation_euler = beauty_dir.to_track_quat("-Z", "Y").to_euler()
scene.camera = beauty_cam

beauty_png = OUT_DIR / "preview-frame-0001.png"
scene.render.filepath = str(beauty_png)
scene.frame_set(1)
bpy.ops.render.render(write_still=True)
log(f"Beauty shot saved: {beauty_png}")

# ── Final save ───────────────────────────────────────────────────
bpy.ops.wm.save_as_mainfile(filepath=str(SESSION))
log("Done.")
