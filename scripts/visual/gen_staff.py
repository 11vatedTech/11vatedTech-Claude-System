import bpy, math, os, random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

output = r"C:/Users/11vat/OneDrive/Desktop/11vatedTech-Claude-System/artifacts/visual/integrated_slice"

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
    cbsdf.inputs["Roughness"].default_value = 0.2
    cbsdf.inputs["Emission Color"].default_value = (0.3, 0.1, 0.5, 1.0)
    cbsdf.inputs["Emission Strength"].default_value = 1.0
crystal.data.materials.append(crystal_mat)

# Crystal shards
random.seed(42)
for si in range(4):
    angle = random.uniform(0, 2 * math.pi)
    r = random.uniform(0.05, 0.12)
    h = random.uniform(0.2, 0.35)
    bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=r, radius2=0.0, depth=h,
        location=(math.cos(angle)*r*0.5, math.sin(angle)*r*0.5, 3.1+h/2))
    shard = bpy.context.active_object
    shard.name = "Shard" + str(si)
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

# Render
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 1024
scene.render.resolution_y = 1024
scene.render.filepath = os.path.join(output, "prop_staff_render.png")
scene.render.image_settings.file_format = 'PNG'
bpy.ops.render.render(write_still=True)

# Export GLB
bpy.ops.export_scene.gltf(
    filepath=os.path.join(output, "prop_staff.glb"),
    export_format='GLB', export_apply=True, export_materials='EXPORT'
)
print("PROP EXPORT COMPLETE")
