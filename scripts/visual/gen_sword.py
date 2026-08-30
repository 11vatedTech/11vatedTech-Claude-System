import bpy, math, os

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

output_path = r"C:/Users/11vat/OneDrive/Desktop/11vatedTech-Claude-System/artifacts/visual/mastery_3d"

# Blade
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 1.5))
blade = bpy.context.active_object
blade.name = "Blade"
blade.scale = (0.05, 0.02, 1.0)
bpy.ops.object.transform_apply(scale=True)
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
scene.render.engine = 'BLENDER_EEVEE'
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
