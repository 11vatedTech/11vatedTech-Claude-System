import bpy, json, math, os
from pathlib import Path
from mathutils import Euler

OUT = Path(__file__).parent.parent.parent / "artifacts" / "lighting-lab" / "renders"
OUT.mkdir(parents=True, exist_ok=True)

def clear_all():
    for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
    for m in list(bpy.data.materials): bpy.data.materials.remove(m)
    for l in list(bpy.data.lights): bpy.data.lights.remove(l)

def setup():
    s = bpy.context.scene
    s.render.engine = 'CYCLES'
    s.render.resolution_x = 1024; s.render.resolution_y = 576
    s.render.resolution_percentage = 100
    s.cycles.samples = 32
    s.cycles.use_denoising = True; s.cycles.denoiser = 'OPENIMAGEDENOISE'
    s.view_settings.view_transform = 'AgX'

def scene_and_materials():
    # Ground
    bpy.ops.mesh.primitive_plane_add(size=8, location=(0,0,-1.1))
    bpy.context.object.name = "Ground"
    gm = bpy.data.materials.new("GroundMat")
    gm.use_nodes = True
    nodes = gm.node_tree.nodes; links = gm.node_tree.links
    gb = nodes.new('ShaderNodeBsdfPrincipled')
    gb.inputs['Base Color'].default_value = (0.45,0.45,0.45,1); gb.inputs['Roughness'].default_value = 0.6
    o = nodes.new('ShaderNodeOutputMaterial')
    links.new(gb.outputs['BSDF'], o.inputs['Surface'])
    bpy.context.object.data.materials.append(gm)
    
    # Objects
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.8, location=(-0.9,0,-0.2))
    bpy.context.object.name = "Sphere"
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.9,0,-0.2))
    c = bpy.context.object; c.name = "Cube"
    m = c.modifiers.new("B", 'BEVEL'); m.width = 0.06; m.segments = 3
    bpy.ops.object.modifier_apply(modifier="B")
    bpy.ops.mesh.primitive_cylinder_add(radius=0.45, depth=1.3, location=(0,-1.6,-0.2))
    bpy.context.object.name = "Cyl"
    
    # Camera
    bpy.ops.object.camera_add(location=(4.5,-2.5,2.8))
    cam = bpy.context.object
    cam.rotation_euler = Euler((math.radians(72),0,math.radians(60)),'XYZ')
    bpy.context.scene.camera = cam
    
    # 3 materials for lighting study
    def mat(name, base, metallic, roughness):
        m = bpy.data.materials.new(name); m.use_nodes = True
        n=m.node_tree.nodes; l=m.node_tree.links; n.clear()
        b=n.new('ShaderNodeBsdfPrincipled'); b.location=(0,0)
        b.inputs['Base Color'].default_value=base; b.inputs['Metallic'].default_value=metallic
        b.inputs['Roughness'].default_value=roughness
        o=n.new('ShaderNodeOutputMaterial'); o.location=(200,0)
        l.new(b.outputs['BSDF'], o.inputs['Surface'])
        return m
    
    mat_sphere = mat("Steel", (0.18,0.17,0.16,1), 0.95, 0.25)
    mat_cube = mat("Ceramic", (0.92,0.89,0.84,1), 0.0, 0.1)
    mat_cyl = mat("Rubber", (0.08,0.07,0.08,1), 0.0, 0.7)
    
    bpy.data.objects['Sphere'].data.materials.append(mat_sphere)
    bpy.data.objects['Cube'].data.materials.append(mat_cube)
    bpy.data.objects['Cyl'].data.materials.append(mat_cyl)

def clear_lights():
    for o in list(bpy.data.objects):
        if o.type == 'LIGHT': bpy.data.objects.remove(o, do_unlink=True)

lighting_configs = {
    "A_flat": lambda: [
        (bpy.ops.object.light_add(type='AREA', location=(0,-3,4)), bpy.context.object, {"energy":300,"size":4}),
        setattr(bpy.context.object.data, 'energy', 300), setattr(bpy.context.object.data, 'size', 4)
    ][:0] or (v := []) or [bpy.ops.object.light_add(type='AREA', location=(0,-3,4)), setattr(bpy.context.object.data,'energy',300), setattr(bpy.context.object.data,'size',4)],
    "B_key_only": lambda: (bpy.ops.object.light_add(type='AREA', location=(4,-1,3.5)), setattr(bpy.context.object.data,'energy',350)),
    "C_key_fill": lambda: [
        (bpy.ops.object.light_add(type='AREA', location=(4,-1,3.5)), setattr(bpy.context.object.data,'energy',250)),
        (bpy.ops.object.light_add(type='AREA', location=(-2,-0.5,2)), setattr(bpy.context.object.data,'energy',100))
    ],
    "D_lowkey": lambda: [
        (bpy.ops.object.light_add(type='SPOT', location=(3,-2,4)), setattr(bpy.context.object.data,'energy',800),
         setattr(bpy.context.object.data, 'spot_size', math.radians(40)))
    ],
    "E_highkey": lambda: [
        (bpy.ops.object.light_add(type='AREA', location=(0,-3,4)), setattr(bpy.context.object.data,'energy',300), setattr(bpy.context.object.data,'size',5)),
        (bpy.ops.object.light_add(type='AREA', location=(0,3,1)), setattr(bpy.context.object.data,'energy',200))
    ],
    "F_silhouette": lambda: [
        (bpy.ops.object.light_add(type='AREA', location=(0,4,0.5)), setattr(bpy.context.object.data,'energy',400), setattr(bpy.context.object.data,'size',2))
    ],
}

# The above lambdas are messy. Let me write clean lighting functions inline.
def apply_lighting(name):
    clear_lights()
    if name == "A_flat":
        bpy.ops.object.light_add(type='AREA', location=(0,-3,4))
        bpy.context.object.data.energy = 300; bpy.context.object.data.size = 4
    elif name == "B_key_only":
        bpy.ops.object.light_add(type='AREA', location=(4,-1,3.5))
        bpy.context.object.data.energy = 350; bpy.context.object.data.size = 1.5
    elif name == "C_key_fill":
        bpy.ops.object.light_add(type='AREA', location=(4,-1,3.5))
        bpy.context.object.data.energy = 250; bpy.context.object.data.size = 1.5
        bpy.ops.object.light_add(type='AREA', location=(-2,-0.5,2))
        bpy.context.object.data.energy = 100; bpy.context.object.data.size = 2
    elif name == "D_lowkey":
        bpy.ops.object.light_add(type='SPOT', location=(3,-2,4))
        bpy.context.object.data.energy = 800; bpy.context.object.data.spot_size = math.radians(40)
    elif name == "E_highkey":
        bpy.ops.object.light_add(type='AREA', location=(0,-3,4))
        bpy.context.object.data.energy = 300; bpy.context.object.data.size = 5
        bpy.ops.object.light_add(type='AREA', location=(0,3,1))
        bpy.context.object.data.energy = 200; bpy.context.object.data.size = 3
    elif name == "F_silhouette":
        bpy.ops.object.light_add(type='AREA', location=(0,4,0.5))
        bpy.context.object.data.energy = 400; bpy.context.object.data.size = 2
    elif name == "G_material_vs_lighting":
        # Differential diagnosis: bad material + good lighting
        bpy.ops.object.light_add(type='AREA', location=(4,-1,3.5))
        bpy.context.object.data.energy = 250; bpy.context.object.data.size = 1.5
        bpy.ops.object.light_add(type='AREA', location=(-2,-0.5,2))
        bpy.context.object.data.energy = 100; bpy.context.object.data.size = 2

# Actually let me just inline the lighting

lighting_names = [
    "A_flat", "B_key_only", "C_key_fill",
    "D_lowkey", "E_highkey", "F_silhouette"
]

for lname in lighting_names:
    clear_all()
    setup()
    scene_and_materials()
    apply_lighting(lname)
    fp = OUT / f"lighting_{lname}.png"
    bpy.context.scene.render.filepath = str(fp)
    bpy.ops.render.render(write_still=True)
    print(f"  {lname} done")

# Material vs lighting differential diagnosis
# Pair A: Bad material + correct lighting
clear_all(); setup()
scene_and_materials()
# Set Cubes ceramic to metallic
mat = bpy.data.materials.get("Ceramic")
n = mat.node_tree.nodes
for nd in n:
    if nd.type == 'BSDF_PRINCIPLED':
        nd.inputs['Metallic'].default_value = 0.6; break
apply_lighting("C_key_fill")
fp = OUT / "diag_bad_material_good_light.png"
bpy.context.scene.render.filepath = str(fp)
bpy.ops.render.render(write_still=True)
print("  diag_bad_material done")

# Pair B: Correct material + bad lighting
clear_all(); setup()
scene_and_materials()
apply_lighting("A_flat")
fp = OUT / "diag_good_material_bad_light.png"
bpy.context.scene.render.filepath = str(fp)
bpy.ops.render.render(write_still=True)
print("  diag_bad_lighting done")

manifest = {"lab":"Lighting Lab","blender":bpy.app.version_string,"renders":8}
with open(OUT/"manifest.json",'w') as f: json.dump(manifest,f,indent=2)
print(f"Lighting Lab: {len(lighting_names)+2} renders")