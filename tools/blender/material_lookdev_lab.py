"""
Material LookDev Lab — Apprenticeship Wave 001
================================================

Creates a professional lookdev scene with:
  - Neutral curved hero objects (sphere + rounded cube + cylinder)
  - Ground contact plane
  - Controlled 3-point studio rig
  - 5 material identities via Principled BSDF
  - 4 lighting conditions per material
  - 5 adversarial diagnostic failures

Author: 11vatedTech Foundry
Blender: 5.2.0 LTS
"""
import bpy
import os
import sys
import json
import math
from pathlib import Path
from mathutils import Vector, Euler

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
OUTPUT_DIR = Path(__file__).parent.parent.parent / "artifacts" / "material-lab" / "renders"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
RENDER_WIDTH = 1024
RENDER_HEIGHT = 576
RENDER_SAMPLES = 128  # Enough for material evaluation, not final production

# ---------------------------------------------------------------------------
# Scene setup
# ---------------------------------------------------------------------------
def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    # Remove all materials
    for mat in bpy.data.materials:
        bpy.data.materials.remove(mat)

def setup_render():
    """Configure Cycles renderer for consistent lookdev."""
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.render.resolution_x = RENDER_WIDTH
    scene.render.resolution_y = RENDER_HEIGHT
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'
    scene.render.image_settings.color_depth = '16'
    scene.cycles.samples = RENDER_SAMPLES
    scene.cycles.use_denoising = True
    scene.cycles.denoiser = 'OPENIMAGEDENOISE'
    scene.view_settings.view_transform = 'Standard'
    scene.view_settings.look = 'None'
    # ACES-like for professional lookdev
    scene.view_settings.view_transform = 'AgX'

def setup_camera():
    """Place camera for standard lookdev view."""
    bpy.ops.object.camera_add(location=(4.5, -2.5, 2.8))
    cam = bpy.context.object
    cam.name = "LookdevCamera"
    # Look at origin
    cam.rotation_euler = Euler((math.radians(72), 0, math.radians(60)), 'XYZ')
    bpy.context.scene.camera = cam
    cam.data.dof.use_dof = False
    return cam

def setup_hero_objects():
    """Create neutral lookdev geometry."""
    objects = []
    
    # Ground plane
    bpy.ops.mesh.primitive_plane_add(size=8, location=(0, 0, -1.1))
    ground = bpy.context.object
    ground.name = "GroundPlane"
    objects.append(ground)
    
    # Hero sphere — curved, reveals specular response
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.8, location=(-0.9, 0, -0.2))
    sphere = bpy.context.object
    sphere.name = "HeroSphere"
    objects.append(sphere)
    
    # Rounded cube — planar faces + curved edges for edge-behavior study
    bpy.ops.mesh.primitive_cube_add(size=1.2, location=(0.9, 0, -0.2))
    cube = bpy.context.object
    cube.name = "HeroCube"
    # Add bevel modifier for rounded edges
    bevel = cube.modifiers.new(name="RoundEdges", type='BEVEL')
    bevel.width = 0.08
    bevel.segments = 3
    bevel.limit_method = 'ANGLE'
    bpy.ops.object.modifier_apply(modifier="RoundEdges")
    objects.append(cube)
    
    # Cylinder — directional roughness reveals anisotropy
    bpy.ops.mesh.primitive_cylinder_add(radius=0.5, depth=1.4, location=(0, -1.6, -0.2))
    cylinder = bpy.context.object
    cylinder.name = "HeroCylinder"
    objects.append(cylinder)
    
    return objects

# ---------------------------------------------------------------------------
# Lighting rigs
# ---------------------------------------------------------------------------
def lighting_neutral_studio():
    """Standard 3-point lookdev: key + fill + rim, neutral 6500K."""
    bpy.ops.object.light_add(type='AREA', location=(4, -1, 3.5))
    key = bpy.context.object
    key.name = "KeyLight"
    key.data.energy = 200
    key.data.size = 1.5
    key.data.color = (1.0, 0.98, 0.95)  # Slightly warm 5500K
    
    bpy.ops.object.light_add(type='AREA', location=(-2, -0.5, 2))
    fill = bpy.context.object
    fill.name = "FillLight"
    fill.data.energy = 80
    fill.data.size = 2
    fill.data.color = (0.85, 0.88, 1.0)  # Cool fill
    
    bpy.ops.object.light_add(type='AREA', location=(-1, 3, 2.5))
    rim = bpy.context.object
    rim.name = "RimLight"
    rim.data.energy = 120
    rim.data.size = 1
    rim.data.color = (1.0, 1.0, 1.0)

def clear_lights():
    for obj in bpy.data.objects:
        if obj.type == 'LIGHT':
            bpy.data.objects.remove(obj, do_unlink=True)

def lighting_grazing():
    """Single hard light at grazing angle — reveals surface microstructure."""
    bpy.ops.object.light_add(type='AREA', location=(6, 0.1, 0.0))
    key = bpy.context.object
    key.name = "GrazingLight"
    key.data.energy = 500
    key.data.size = 0.3
    key.data.color = (1.0, 1.0, 1.0)
    key.rotation_euler = Euler((math.radians(-90), 0, 0), 'XYZ')

def lighting_lowkey():
    """Single motivated source, strong falloff — tests shadow-side readability."""
    bpy.ops.object.light_add(type='SPOT', location=(3, -2, 4))
    key = bpy.context.object
    key.name = "LowKeySpot"
    key.data.energy = 800
    key.data.spot_size = math.radians(40)
    key.data.spot_blend = 0.3
    key.data.color = (1.0, 0.95, 0.85)  # Warm tungsten

def lighting_highkey():
    """Large soft fills, minimal shadow — tests material response without contrast help."""
    bpy.ops.object.light_add(type='AREA', location=(0, -3, 4))
    top = bpy.context.object
    top.name = "HighKeyTop"
    top.data.energy = 300
    top.data.size = 4
    top.data.color = (1.0, 1.0, 1.0)
    
    bpy.ops.object.light_add(type='AREA', location=(0, 3, 1))
    front = bpy.context.object
    front.name = "HighKeyFront"
    front.data.energy = 200
    front.data.size = 3
    front.data.color = (1.0, 1.0, 1.0)

# ---------------------------------------------------------------------------
# Material definitions — Principled BSDF
# ---------------------------------------------------------------------------
def mat_aged_steel():
    """Dielectric with metallic base. Weathered steel: dark F0, moderate roughness,
    subtle surface variation, light edge oxidation."""
    mat = bpy.data.materials.new("AgedSteel")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    bsdf.inputs['Base Color'].default_value = (0.18, 0.17, 0.16, 1.0)
    bsdf.inputs['Metallic'].default_value = 0.95
    bsdf.inputs['Roughness'].default_value = 0.28
    bsdf.inputs['IOR'].default_value = 1.45  # Standard dielectric IOR
    bsdf.inputs['Anisotropic'].default_value = 0.15
    bsdf.inputs['Anisotropic Rotation'].default_value = 0.3
    # Subtle surface oxidation — slight diffuse orange tint in crevices
    bsdf.inputs['Coat Weight'].default_value = 0.0
    
    out = nodes.new('ShaderNodeOutputMaterial')
    out.location = (200, 0)
    links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    return mat

def mat_ceramic():
    """Dielectric. Glazed ceramic: diffuse base with glossy coat, low roughness,
    subtle warm undertone. No metallic."""
    mat = bpy.data.materials.new("CeramicGlaze")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    bsdf.inputs['Base Color'].default_value = (0.92, 0.89, 0.84, 1.0)  # Warm cream
    bsdf.inputs['Metallic'].default_value = 0.0  # Non-metallic dielectric
    bsdf.inputs['Roughness'].default_value = 0.08  # Glossy glaze
    bsdf.inputs['Specular IOR Level'].default_value = 0.5
    bsdf.inputs['Subsurface Weight'].default_value = 0.05  # Slight SSS for ceramic
    bsdf.inputs['Subsurface Radius'].default_value = (1.0, 0.8, 0.6)
    bsdf.inputs['Coat Weight'].default_value = 0.15  # Clear glaze layer
    bsdf.inputs['Coat Roughness'].default_value = 0.03
    
    out = nodes.new('ShaderNodeOutputMaterial')
    out.location = (200, 0)
    links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    return mat

def mat_painted_wood():
    """Dielectric. Aged painted wood: moderate roughness, subtle bump for grain,
    diffuse base with some specular from paint layer."""
    mat = bpy.data.materials.new("PaintedWood")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    bsdf.inputs['Base Color'].default_value = (0.35, 0.30, 0.24, 1.0)  # Weathered dark brown paint
    bsdf.inputs['Metallic'].default_value = 0.0
    bsdf.inputs['Roughness'].default_value = 0.55  # Painted but worn
    bsdf.inputs['Specular IOR Level'].default_value = 0.35
    
    # Add subtle bump for wood grain under paint
    noise = nodes.new('ShaderNodeTexNoise')
    noise.location = (-300, -100)
    noise.inputs['Scale'].default_value = 15.0
    noise.inputs['Detail'].default_value = 4.0
    noise.inputs['Roughness'].default_value = 0.5
    
    bump = nodes.new('ShaderNodeBump')
    bump.location = (-100, -100)
    bump.inputs['Strength'].default_value = 0.08
    links.new(noise.outputs['Fac'], bump.inputs['Height'])
    links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    
    out = nodes.new('ShaderNodeOutputMaterial')
    out.location = (200, 0)
    links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    return mat

def mat_dirty_glass():
    """Transmissive dielectric. Dirty glass: transmission with absorption,
    roughness variation, some surface grime."""
    mat = bpy.data.materials.new("DirtyGlass")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    bsdf.inputs['Base Color'].default_value = (1.0, 1.0, 1.0, 1.0)
    bsdf.inputs['Metallic'].default_value = 0.0
    bsdf.inputs['Roughness'].default_value = 0.12  # Slightly dirty, not perfectly clean
    bsdf.inputs['Transmission Weight'].default_value = 0.9
    bsdf.inputs['Alpha'].default_value = 0.85
    # Slight absorption — greenish tint from iron content
    
    # Volume absorption for glass thickness
    abs_node = nodes.new('ShaderNodeBsdfPrincipled')  # Not ideal — use volume
    
    # Simpler: slight green tint from absorption via Base Color bleed
    bsdf.inputs['Base Color'].default_value = (0.88, 0.94, 0.86, 1.0)
    
    out = nodes.new('ShaderNodeOutputMaterial')
    out.location = (200, 0)
    links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    return mat

def mat_rubber_polymer():
    """Dielectric. Hard rubber/polymer: very diffuse, almost no specular,
    slight roughness variation, dark matte surface."""
    mat = bpy.data.materials.new("RubberPolymer")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    bsdf.inputs['Base Color'].default_value = (0.08, 0.07, 0.08, 1.0)  # Near-black
    bsdf.inputs['Metallic'].default_value = 0.0
    bsdf.inputs['Roughness'].default_value = 0.72  # Very diffuse
    bsdf.inputs['Specular IOR Level'].default_value = 0.15  # Minimal specular
    
    # Subtle surface micro-texture
    noise = nodes.new('ShaderNodeTexNoise')
    noise.location = (-300, -100)
    noise.inputs['Scale'].default_value = 40.0
    noise.inputs['Detail'].default_value = 6.0
    
    bump = nodes.new('ShaderNodeBump')
    bump.location = (-100, -100)
    bump.inputs['Strength'].default_value = 0.04
    links.new(noise.outputs['Fac'], bump.inputs['Height'])
    links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    
    out = nodes.new('ShaderNodeOutputMaterial')
    out.location = (200, 0)
    links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    return mat

# ---------------------------------------------------------------------------
# Adversarial diagnostic materials
# ---------------------------------------------------------------------------
def mat_adversarial_ceramic_too_metallic():
    """DIAGNOSTIC: Ceramic with metallic set too high — should read as wrong."""
    mat = bpy.data.materials.new("DIAG_CeramicTooMetallic")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    bsdf.inputs['Base Color'].default_value = (0.92, 0.89, 0.84, 1.0)  # Same cream
    bsdf.inputs['Metallic'].default_value = 0.6  # WRONG — ceramic is dielectric
    bsdf.inputs['Roughness'].default_value = 0.08
    bsdf.inputs['Coat Weight'].default_value = 0.15
    
    out = nodes.new('ShaderNodeOutputMaterial')
    out.location = (200, 0)
    links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    return mat

def mat_adversarial_metal_too_diffuse():
    """DIAGNOSTIC: Steel with metallic too low — loses metallic response."""
    mat = bpy.data.materials.new("DIAG_MetalTooDiffuse")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    bsdf.inputs['Base Color'].default_value = (0.18, 0.17, 0.16, 1.0)
    bsdf.inputs['Metallic'].default_value = 0.0  # WRONG — should be ~0.95
    bsdf.inputs['Roughness'].default_value = 0.28
    
    out = nodes.new('ShaderNodeOutputMaterial')
    out.location = (200, 0)
    links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    return mat

def mat_adversarial_rubber_too_glossy():
    """DIAGNOSTIC: Rubber with roughness too low — reads as plastic, not rubber."""
    mat = bpy.data.materials.new("DIAG_RubberTooGlossy")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    bsdf.inputs['Base Color'].default_value = (0.08, 0.07, 0.08, 1.0)
    bsdf.inputs['Metallic'].default_value = 0.0
    bsdf.inputs['Roughness'].default_value = 0.15  # WRONG — rubber should be ~0.7
    
    out = nodes.new('ShaderNodeOutputMaterial')
    out.location = (200, 0)
    links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    return mat

def mat_adversarial_glass_no_transmission():
    """DIAGNOSTIC: Glass material with transmission=0 — just a glossy sphere."""
    mat = bpy.data.materials.new("DIAG_GlassNoTransmission")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    bsdf.inputs['Base Color'].default_value = (1.0, 1.0, 1.0, 1.0)
    bsdf.inputs['Metallic'].default_value = 0.0
    bsdf.inputs['Roughness'].default_value = 0.05
    bsdf.inputs['Transmission Weight'].default_value = 0.0  # WRONG — glass needs transmission
    
    out = nodes.new('ShaderNodeOutputMaterial')
    out.location = (200, 0)
    links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    return mat

def mat_adversarial_wrong_scale():
    """DIAGNOSTIC: Noise bump scale way too large — surface detail reads at wrong physical size."""
    mat = bpy.data.materials.new("DIAG_WrongScale")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    bsdf.inputs['Base Color'].default_value = (0.6, 0.55, 0.45, 1.0)
    bsdf.inputs['Metallic'].default_value = 0.0
    bsdf.inputs['Roughness'].default_value = 0.45
    
    noise = nodes.new('ShaderNodeTexNoise')
    noise.location = (-300, -100)
    noise.inputs['Scale'].default_value = 0.5  # WRONG — enormous bumps, object reads as pebble-sized
    noise.inputs['Detail'].default_value = 2.0
    
    bump = nodes.new('ShaderNodeBump')
    bump.location = (-100, -100)
    bump.inputs['Strength'].default_value = 0.4
    links.new(noise.outputs['Fac'], bump.inputs['Height'])
    links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    
    out = nodes.new('ShaderNodeOutputMaterial')
    out.location = (200, 0)
    links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    return mat

# ---------------------------------------------------------------------------
# Assign material to objects
# ---------------------------------------------------------------------------
def assign_material(mat, objects):
    for obj in objects:
        if obj.type == 'MESH' and obj.name != 'GroundPlane':
            if obj.data.materials:
                obj.data.materials[0] = mat
            else:
                obj.data.materials.append(mat)

def assign_ground_material():
    """Neutral grey photogrammetry-style ground with slight texture."""
    mat = bpy.data.materials.new("NeutralGround")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    bsdf.inputs['Base Color'].default_value = (0.45, 0.45, 0.45, 1.0)
    bsdf.inputs['Metallic'].default_value = 0.0
    bsdf.inputs['Roughness'].default_value = 0.6
    
    out = nodes.new('ShaderNodeOutputMaterial')
    out.location = (200, 0)
    links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    
    ground = bpy.data.objects.get('GroundPlane')
    if ground and ground.data.materials:
        ground.data.materials[0] = mat
    elif ground:
        ground.data.materials.append(mat)
    return mat

# ---------------------------------------------------------------------------
# Render function
# ---------------------------------------------------------------------------
def render_to_file(filepath):
    bpy.context.scene.render.filepath = str(filepath)
    bpy.ops.render.render(write_still=True)

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print("=" * 60)
    print("MATERIAL LOOKDEV LAB — Wave 001")
    print(f"Blender: {bpy.app.version_string}")
    print(f"Output: {OUTPUT_DIR}")
    print("=" * 60)
    
    # Materials and their metadata
    materials = [
        ("aged_steel", mat_aged_steel, "Aged Steel", "Conductor"),
        ("ceramic", mat_ceramic, "Ceramic Glaze", "Dielectric"),
        ("painted_wood", mat_painted_wood, "Painted Wood", "Dielectric"),
        ("dirty_glass", mat_dirty_glass, "Dirty Glass", "Transmissive"),
        ("rubber_polymer", mat_rubber_polymer, "Rubber/Polymer", "Dielectric"),
    ]
    
    adversarial = [
        ("diag_ceramic_too_metallic", mat_adversarial_ceramic_too_metallic, "Ceramic → Too Metallic", "Metallic set on dielectric"),
        ("diag_metal_too_diffuse", mat_adversarial_metal_too_diffuse, "Metal → Too Diffuse", "Metallic=0 on conductor"),
        ("diag_rubber_too_glossy", mat_adversarial_rubber_too_glossy, "Rubber → Too Glossy", "Roughness too low"),
        ("diag_glass_no_transmission", mat_adversarial_glass_no_transmission, "Glass → No Transmission", "Transmission weight=0"),
        ("diag_wrong_scale", mat_adversarial_wrong_scale, "Bump → Wrong Scale", "Noise scale 0.5 (10x too large)"),
    ]
    
    lighting_configs = [
        ("neutral_studio", lighting_neutral_studio, "Neutral Studio (3-point)"),
        ("grazing", lighting_grazing, "Grazing Light"),
        ("lowkey", lighting_lowkey, "Low Key (single spot)"),
        ("highkey", lighting_highkey, "High Key (soft fills)"),
    ]
    
    results = []
    
    # Render each material under each lighting condition
    for mat_id, mat_fn, mat_name, mat_class in materials:
        for light_id, light_fn, light_name in lighting_configs:
            clear_scene()
            setup_render()
            setup_camera()
            objects = setup_hero_objects()
            
            mat = mat_fn() if callable(mat_fn) else mat_fn
            assign_material(mat, objects)
            assign_ground_material()
            
            light_fn()
            
            filename = f"mat_{mat_id}__light_{light_id}.png"
            filepath = OUTPUT_DIR / filename
            render_to_file(filepath)
            
            results.append({
                "material": mat_id,
                "material_name": mat_name,
                "material_class": mat_class,
                "lighting": light_id,
                "lighting_name": light_name,
                "file": str(filepath),
                "filename": filename,
            })
            print(f"  Rendered: {filename}")
    
    # Render adversarial materials under neutral studio only (for diagnosis)
    for diag_id, diag_fn, diag_name, diag_desc in adversarial:
        clear_scene()
        setup_render()
        setup_camera()
        objects = setup_hero_objects()
        
        mat = diag_fn() if callable(diag_fn) else diag_fn
        assign_material(mat, objects)
        assign_ground_material()
        
        lighting_neutral_studio()
        
        filename = f"adversarial_{diag_id}.png"
        filepath = OUTPUT_DIR / filename
        render_to_file(filepath)
        
        results.append({
            "material": diag_id,
            "material_name": diag_name,
            "material_class": "ADVERSARIAL",
            "lighting": "neutral_studio",
            "lighting_name": "Neutral Studio",
            "adversarial": True,
            "failure_description": diag_desc,
            "file": str(filepath),
            "filename": filename,
        })
        print(f"  Rendered adversarial: {filename}")
    
    # Write manifest
    manifest_path = OUTPUT_DIR / "manifest.json"
    manifest = {
        "lab": "Apprenticeship Wave 001 — Material LookDev",
        "blender_version": bpy.app.version_string,
        "render_count": len(results),
        "render_width": RENDER_WIDTH,
        "render_height": RENDER_HEIGHT,
        "render_samples": RENDER_SAMPLES,
        "color_transform": "AgX",
        "materials": [
            {"id": m[0], "name": m[2], "class": m[3]} for m in materials
        ],
        "adversarial_diagnostics": [
            {"id": a[0], "name": a[2], "failure": a[3]} for a in adversarial
        ],
        "lighting_conditions": [
            {"id": l[0], "name": l[2]} for l in lighting_configs
        ],
        "results": results,
    }
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    print(f"\nManifest: {manifest_path}")
    print(f"Total renders: {len(results)}")
    print("MATERIAL LOOKDEV LAB COMPLETE")

if __name__ == "__main__":
    main()