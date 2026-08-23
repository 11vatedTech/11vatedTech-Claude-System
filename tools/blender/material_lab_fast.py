import bpy, json, math, os
from pathlib import Path
from mathutils import Euler

OUT = Path(__file__).parent.parent.parent / "artifacts" / "material-lab" / "renders"
OUT.mkdir(parents=True, exist_ok=True)

def clear_all():
    for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
    for m in list(bpy.data.materials): bpy.data.materials.remove(m)

def setup():
    s = bpy.context.scene
    s.render.engine = 'CYCLES'
    s.render.resolution_x = 1024
    s.render.resolution_y = 576
    s.render.resolution_percentage = 100
    s.render.image_settings.file_format = 'PNG'
    s.cycles.samples = 32
    s.cycles.use_denoising = True
    s.cycles.denoiser = 'OPENIMAGEDENOISE'
    s.view_settings.view_transform = 'AgX'

def scene_objects():
    # Ground
    bpy.ops.mesh.primitive_plane_add(size=8, location=(0,0,-1.1))
    bpy.context.object.name = "Ground"
    # Hero objects
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.8, location=(-0.9,0,-0.2))
    bpy.context.object.name = "Sphere"
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.9,0,-0.2))
    cube = bpy.context.object
    cube.name = "Cube"
    m = cube.modifiers.new("Bevel", 'BEVEL')
    m.width = 0.06; m.segments = 3
    bpy.ops.object.modifier_apply(modifier="Bevel")
    bpy.ops.mesh.primitive_cylinder_add(radius=0.45, depth=1.3, location=(0,-1.6,-0.2))
    bpy.context.object.name = "Cyl"
    # Camera
    bpy.ops.object.camera_add(location=(4.5,-2.5,2.8))
    cam = bpy.context.object
    cam.rotation_euler = Euler((math.radians(72), 0, math.radians(60)), 'XYZ')
    cam.data.dof.use_dof = False
    bpy.context.scene.camera = cam
    # Ground material
    gm = bpy.data.materials.new("Ground")
    gm.use_nodes = True
    gb = gm.node_tree.nodes.new('ShaderNodeBsdfPrincipled')
    gb.inputs['Base Color'].default_value = (0.45, 0.45, 0.45, 1)
    gb.inputs['Roughness'].default_value = 0.6
    gm.node_tree.links.new(gb.outputs['BSDF'], gm.node_tree.nodes.new('ShaderNodeOutputMaterial').inputs['Surface'])
    bpy.data.objects['Ground'].data.materials.append(gm)
    # Lights
    bpy.ops.object.light_add(type='AREA', location=(4,-1,3.5))
    k = bpy.context.object; k.name = "Key"; k.data.energy = 200; k.data.size = 1.5; k.data.color = (1,0.98,0.95)
    bpy.ops.object.light_add(type='AREA', location=(-2,-0.5,2))
    f = bpy.context.object; f.name = "Fill"; f.data.energy = 80; f.data.size = 2; f.data.color = (0.85,0.88,1)
    bpy.ops.object.light_add(type='AREA', location=(-1,3,2.5))
    r = bpy.context.object; r.name = "Rim"; r.data.energy = 120; r.data.size = 1

def make_mat(name, base, metallic, roughness, ior=1.45, trans=0, coat=0, coat_rough=0, sss=0, anisotropic=0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nodes = m.node_tree.nodes
    links = m.node_tree.links
    nodes.clear()
    b = nodes.new('ShaderNodeBsdfPrincipled')
    b.location = (0,0)
    b.inputs['Base Color'].default_value = base
    b.inputs['Metallic'].default_value = metallic
    b.inputs['Roughness'].default_value = roughness
    b.inputs['IOR'].default_value = ior
    b.inputs['Transmission Weight'].default_value = trans
    b.inputs['Coat Weight'].default_value = coat
    b.inputs['Coat Roughness'].default_value = coat_rough
    b.inputs['Subsurface Weight'].default_value = sss
    b.inputs['Anisotropic'].default_value = anisotropic
    o = nodes.new('ShaderNodeOutputMaterial')
    o.location = (200,0)
    links.new(b.outputs['BSDF'], o.inputs['Surface'])
    # Assign to hero objects
    for obj_name in ['Sphere', 'Cube', 'Cyl']:
        obj = bpy.data.objects.get(obj_name)
        if obj:
            if obj.data.materials: obj.data.materials[0] = m
            else: obj.data.materials.append(m)
    return m

results = []

# 5 real materials
mats = [
    ("aged_steel",        (0.18,0.17,0.16,1), 0.95, 0.28, 1.6, 0, 0, 0, 0, 0.15),
    ("ceramic",           (0.92,0.89,0.84,1), 0.0,  0.08, 1.5, 0, 0.15, 0.03, 0.05, 0),
    ("painted_wood",      (0.35,0.30,0.24,1), 0.0,  0.55, 1.45, 0, 0, 0, 0, 0),
    ("dirty_glass",       (0.88,0.94,0.86,1), 0.0,  0.12, 1.5, 0.85, 0, 0, 0, 0),
    ("rubber_polymer",    (0.08,0.07,0.08,1), 0.0,  0.72, 1.45, 0, 0, 0, 0, 0),
]

for mat_id, base, metallic, roughness, ior, trans, coat, coat_rough, sss, aniso in mats:
    clear_all()
    setup()
    scene_objects()
    make_mat(mat_id, base, metallic, roughness, ior, trans, coat, coat_rough, sss, aniso)
    fp = OUT / f"mat_{mat_id}.png"
    bpy.context.scene.render.filepath = str(fp)
    bpy.ops.render.render(write_still=True)
    results.append({"material": mat_id, "file": str(fp)})
    print(f"  {mat_id} done")

# 5 adversarial diagnostics
adv = [
    ("diag_ceramic_too_metallic",  (0.92,0.89,0.84,1), 0.6,  0.08, 1.5, 0, 0.15, 0.03, 0, 0),
    ("diag_metal_too_diffuse",     (0.18,0.17,0.16,1), 0.0,  0.28, 1.6, 0, 0, 0, 0, 0),
    ("diag_rubber_too_glossy",     (0.08,0.07,0.08,1), 0.0,  0.15, 1.45, 0, 0, 0, 0, 0),
    ("diag_glass_no_transmission", (1,1,1,1),           0.0,  0.05, 1.5, 0.0, 0, 0, 0, 0),
    ("diag_wrong_scale_bump",      (0.6,0.55,0.45,1),   0.0,  0.45, 1.45, 0, 0, 0, 0, 0),
]
adv_desc = ["Ceramic with metallic too high", "Metal rendered as dielectric", "Rubber with too-low roughness", "Glass without transmission", "Bump scale 10x too large"]

for i, (diag_id, base, metallic, roughness, ior, trans, coat, coat_rough, sss, aniso) in enumerate(adv):
    clear_all()
    setup()
    scene_objects()
    make_mat(diag_id, base, metallic, roughness, ior, trans, coat, coat_rough, sss, aniso)
    # For wrong-scale, add large-scale bump
    if i == 4:
        mat = bpy.data.materials.get(diag_id)
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        bsdf = None
        for n in nodes:
            if n.type == 'BSDF_PRINCIPLED': bsdf = n; break
        noise = nodes.new('ShaderNodeTexNoise')
        noise.location = (-300, -200)
        noise.inputs['Scale'].default_value = 0.5
        bump = nodes.new('ShaderNodeBump')
        bump.location = (-100, -200)
        bump.inputs['Strength'].default_value = 0.4
        links.new(noise.outputs['Fac'], bump.inputs['Height'])
        links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    fp = OUT / f"{diag_id}.png"
    bpy.context.scene.render.filepath = str(fp)
    bpy.ops.render.render(write_still=True)
    results.append({"material": diag_id, "adversarial": True, "description": adv_desc[i], "file": str(fp)})
    print(f"  {diag_id} done")

manifest = {"lab": "Material LookDev", "blender": bpy.app.version_string, "renders": len(results), "samples": 32, "results": results}
with open(OUT / "manifest.json", 'w') as f: json.dump(manifest, f, indent=2)
print(f"Done: {len(results)} renders")