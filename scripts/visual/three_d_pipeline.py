#!/usr/bin/env python3
"""
3D Asset Pipeline — Blender + trimesh
======================================
Generate a 3D product/prop asset, validate mesh, export GLB.
Uses Blender headless for authoritative geometry.
"""

import subprocess
import os
import json
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
OUTPUT = PROJECT_ROOT / "artifacts" / "visual" / "mastery_3d"
OUTPUT.mkdir(parents=True, exist_ok=True)

BLENDER = r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"

# Blender Python script for generating a stylized low-poly crystal prop
CRYSTAL_SCRIPT = """
import bpy
import bmesh
import math
import os

# Clear scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Create crystal cluster
output_path = r"{output_path}"

# Create main crystal (elongated octahedron)
bpy.ops.mesh.primitive_cone_add(
    vertices=8, radius1=0.4, radius2=0.0, depth=2.0,
    location=(0, 0, 1.0)
)
main_crystal = bpy.context.active_object
main_crystal.name = "MainCrystal"

# Add material
mat = bpy.data.materials.new(name="CrystalMat")
mat.use_nodes = True
nodes = mat.node_tree.nodes
links = mat.node_tree.links

# Set up principled BSDF
bsdf = nodes.get("Principled BSDF")
if bsdf:
    bsdf.inputs["Base Color"].default_value = (0.1, 0.3, 0.6, 1.0)
    bsdf.inputs["Metallic"].default_value = 0.1
    bsdf.inputs["Roughness"].default_value = 0.2
    bsdf.inputs["Alpha"].default_value = 0.85
    bsdf.inputs["Emission Color"].default_value = (0.05, 0.15, 0.4, 1.0)
    bsdf.inputs["Emission Strength"].default_value = 0.3
mat.blend_method = 'BLEND' if hasattr(mat, 'blend_method') else None
main_crystal.data.materials.append(mat)

# Create smaller crystals
import random
random.seed(42)
for i in range(5):
    angle = random.uniform(0, 2 * math.pi)
    dist = random.uniform(0.3, 0.8)
    x = math.cos(angle) * dist
    y = math.sin(angle) * dist
    height = random.uniform(0.5, 1.2)
    radius = random.uniform(0.1, 0.25)

    bpy.ops.mesh.primitive_cone_add(
        vertices=6, radius1=radius, radius2=0.0, depth=height,
        location=(x, y, height/2)
    )
    crystal = bpy.context.active_object
    crystal.name = f"Crystal_{i}"
    crystal.rotation_euler = (
        random.uniform(-0.3, 0.3),
        random.uniform(-0.3, 0.3),
        random.uniform(0, math.pi * 2)
    )
    crystal.data.materials.append(mat)

# Add base rock
bpy.ops.mesh.primitive_uv_sphere_add(
    segments=12, ring_count=8, radius=1.2,
    location=(0, 0, -0.2)
)
base = bpy.context.active_object
base.name = "BaseRock"
base.scale = (1.0, 1.0, 0.3)

rock_mat = bpy.data.materials.new(name="RockMat")
rock_mat.use_nodes = True
rock_bsdf = rock_mat.node_tree.nodes.get("Principled BSDF")
if rock_bsdf:
    rock_bsdf.inputs["Base Color"].default_value = (0.15, 0.12, 0.1, 1.0)
    rock_bsdf.inputs["Roughness"].default_value = 0.9
    rock_bsdf.inputs["Metallic"].default_value = 0.0
base.data.materials.append(rock_mat)

# Add camera
bpy.ops.object.camera_add(location=(3, -3, 2.5))
cam = bpy.context.active_object
cam.rotation_euler = (math.radians(65), 0, math.radians(45))
bpy.context.scene.camera = cam

# Add light
bpy.ops.object.light_add(type='AREA', location=(2, -2, 4))
light = bpy.context.active_object
light.data.energy = 200
light.data.color = (0.8, 0.85, 1.0)

bpy.ops.object.light_add(type='POINT', location=(-1, 1, 2))
light2 = bpy.context.active_object
light2.data.energy = 100
light2.data.color = (0.4, 0.6, 1.0)

# Render settings
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE_NEXT' if hasattr(bpy.types, 'BLENDER_EEVEE_NEXT') else 'BLENDER_EEVEE'
scene.render.resolution_x = 1024
scene.render.resolution_y = 1024
scene.render.resolution_percentage = 100
scene.render.filepath = os.path.join(output_path, "crystal_render.png")
scene.render.image_settings.file_format = 'PNG'

# Render
bpy.ops.render.render(write_still=True)

# Export GLB
bpy.ops.export_scene.gltf(
    filepath=os.path.join(output_path, "crystal_cluster.glb"),
    export_format='GLB',
    use_selection=False,
    export_apply=True,
    export_materials='EXPORT'
)

# Also export OBJ
bpy.ops.wm.obj_export(
    filepath=os.path.join(output_path, "crystal_cluster.obj"),
    export_selected_objects=False,
    export_materials=True
)

print("EXPORT COMPLETE")
print(f"Render: {{output_path}}/crystal_render.png")
print(f"GLB: {{output_path}}/crystal_cluster.glb")
print(f"OBJ: {{output_path}}/crystal_cluster.obj")
"""

# Blender script for a stylized weapon (sword)
SWORD_SCRIPT = """
import bpy
import math
import os

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

output_path = r"{output_path}"

# Blade
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 1.5))
blade = bpy.context.active_object
blade.name = "Blade"
blade.scale = (0.05, 0.02, 1.0)
bpy.ops.object.transform_apply(scale=True)

# Taper the blade tip
bpy.ops.object.mode_set(mode='EDIT')
bm = bmesh.from_edit_mesh(blade.data)
for v in bm.verts:
    if v.co.z > 1.8:
        v.co.x *= 0.1
        v.co.y *= 0.1
bmesh.update_edit_mesh(blade.data)
bpy.ops.object.mode_set(mode='OBJECT')

blade_mat = bpy.data.materials.new(name="BladeMat")
blade_mat.use_nodes = True
bsdf = blade_mat.node_tree.nodes.get("Principled BSDF")
if bsdf:
    bsdf.inputs["Base Color"].default_value = (0.7, 0.72, 0.75, 1.0)
    bsdf.inputs["Metallic"].default_value = 0.95
    bsdf.inputs["Roughness"].default_value = 0.15
blade.data.materials.append(blade_mat)

# Handle
bpy.ops.mesh.primitive_cylinder_add(radius=0.04, depth=0.5, location=(0, 0, 0.25))
handle = bpy.context.active_object
handle.name = "Handle"
handle_mat = bpy.data.materials.new(name="HandleMat")
handle_mat.use_nodes = True
hbsdf = handle_mat.node_tree.nodes.get("Principled BSDF")
if hbsdf:
    hbsdf.inputs["Base Color"].default_value = (0.25, 0.15, 0.08, 1.0)
    hbsdf.inputs["Roughness"].default_value = 0.8
handle.data.materials.append(handle_mat)

# Guard
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.5))
guard = bpy.context.active_object
guard.name = "Guard"
guard.scale = (0.2, 0.04, 0.03)
bpy.ops.object.transform_apply(scale=True)
guard_mat = bpy.data.materials.new(name="GuardMat")
guard_mat.use_nodes = True
gbsdf = guard_mat.node_tree.nodes.get("Principled BSDF")
if gbsdf:
    gbsdf.inputs["Base Color"].default_value = (0.8, 0.65, 0.2, 1.0)
    gbsdf.inputs["Metallic"].default_value = 0.9
    gbsdf.inputs["Roughness"].default_value = 0.3
guard.data.materials.append(guard_mat)

# Pommel
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.06, location=(0, 0, 0.0))
pommel = bpy.context.active_object
pommel.name = "Pommel"
pommel.data.materials.append(guard_mat)

# Camera
bpy.ops.object.camera_add(location=(2, -1.5, 1.5))
cam = bpy.context.active_object
cam.rotation_euler = (math.radians(60), 0, math.radians(50))
bpy.context.scene.camera = cam

# Lights
bpy.ops.object.light_add(type='AREA', location=(2, -1, 3))
light = bpy.context.active_object
light.data.energy = 150
light.data.color = (1.0, 0.95, 0.9)

bpy.ops.object.light_add(type='POINT', location=(-1, 1, 2))
light2 = bpy.context.active_object
light2.data.energy = 80
light2.data.color = (0.7, 0.8, 1.0)

# Render
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE_NEXT' if hasattr(bpy.types, 'BLENDER_EEVEE_NEXT') else 'BLENDER_EEVEE'
scene.render.resolution_x = 1024
scene.render.resolution_y = 1024
scene.render.filepath = os.path.join(output_path, "sword_render.png")
scene.render.image_settings.file_format = 'PNG'
bpy.ops.render.render(write_still=True)

# Export GLB
bpy.ops.export_scene.gltf(
    filepath=os.path.join(output_path, "sword.glb"),
    export_format='GLB',
    export_apply=True,
    export_materials='EXPORT'
)

print("SWORD EXPORT COMPLETE")
"""


def run_blender(script_content, label):
    """Run a Blender script headlessly."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
        f.write(script_content)
        script_path = f.name

    print(f"  [{label}] Running Blender...", end=" ", flush=True)
    r = subprocess.run(
        [BLENDER, "--background", "--python", script_path],
        capture_output=True, text=True, timeout=120
    )
    os.unlink(script_path)

    if r.returncode == 0 and "EXPORT COMPLETE" in r.stdout:
        print("OK")
        return True
    else:
        # Check for render output even if export had issues
        if "Render" in r.stdout or "render" in r.stdout.lower():
            print("PARTIAL (render may exist)")
            return True
        print(f"FAILED (rc={r.returncode})")
        if r.stderr:
            # Look for key errors
            for line in r.stderr.split('\n')[-5:]:
                if line.strip():
                    print(f"    {line.strip()[:100]}")
        return False


def validate_mesh(glb_path):
    """Validate a GLB file with trimesh."""
    try:
        import trimesh
        scene = trimesh.load(str(glb_path))
        if isinstance(scene, trimesh.Scene):
            meshes = list(scene.geometry.values())
        else:
            meshes = [scene]

        results = []
        for m in meshes:
            if isinstance(m, trimesh.Trimesh):
                results.append({
                    "vertices": len(m.vertices),
                    "faces": len(m.faces),
                    "is_watertight": m.is_watertight,
                    "volume": float(m.volume) if m.is_watertight else None,
                    "bounds": m.bounds.tolist(),
                })
        return results
    except Exception as e:
        return [{"error": str(e)}]


if __name__ == "__main__":
    print("=" * 60)
    print("3D ASSET PIPELINE — Blender + trimesh")
    print("=" * 60)

    if not Path(BLENDER).exists():
        print(f"Blender not found at {BLENDER}")
        exit(1)

    # Generate crystal cluster
    crystal_script = CRYSTAL_SCRIPT.replace("{output_path}", str(OUTPUT).replace("\\", "/"))
    crystal_ok = run_blender(crystal_script, "Crystal Cluster")

    # Generate sword
    sword_script = SWORD_SCRIPT.replace("{output_path}", str(OUTPUT).replace("\\", "/"))
    sword_ok = run_blender(sword_script, "Sword")

    # Validate meshes
    print("\n--- MESH VALIDATION ---")
    for name in ["crystal_cluster.glb", "sword.glb"]:
        path = OUTPUT / name
        if path.exists():
            sz = os.path.getsize(str(path)) // 1024
            print(f"  {name} ({sz}KB):")
            validation = validate_mesh(path)
            for v in validation:
                if "error" in v:
                    print(f"    Error: {v['error']}")
                else:
                    print(f"    Vertices: {v['vertices']}, Faces: {v['faces']}, Watertight: {v['is_watertight']}")
        else:
            print(f"  {name}: NOT FOUND")

    # List outputs
    print("\n--- OUTPUTS ---")
    for f in sorted(OUTPUT.glob("*")):
        sz = os.path.getsize(str(f)) // 1024
        print(f"  {f.name} ({sz}KB)")
