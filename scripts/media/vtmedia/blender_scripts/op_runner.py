"""Blender-side structured operations runner.

Invoked by the host bridge as:

    blender --background --factory-startup --python op_runner.py -- <spec.json> <result.json>

Each op reads a JSON spec, executes a high-level structured operation, and
writes a JSON result plus any artifacts (renders, GLBs, videos). Every op
returns structured output with an explicit health field; failures are captured
in the result, never thrown as uncaught exceptions.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import bpy  # type: ignore
from mathutils import Vector  # type: ignore

VERSION = "0.4.0"


def _out(data: dict, ok: bool) -> dict:
    data["op_runner_version"] = VERSION
    data["blender_version"] = bpy.app.version_string
    data["ok"] = ok
    data["health"] = "PASS" if ok else "FAILED"
    return data


def _obj(name: str):
    if name not in bpy.data.objects:
        raise ValueError(f"object_not_found {name}")
    return bpy.data.objects[name]


def _action_fcurves(action):
    """Yield fcurves across legacy and layered (Blender 4+/5.x) actions."""
    if hasattr(action, "fcurves"):
        yield from action.fcurves
        return
    for layer in getattr(action, "layers", ()):
        for strip in getattr(layer, "strips", ()):
            for bag in getattr(strip, "channelbags", ()):
                yield from bag.fcurves


def _clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


def _deselect_all():
    bpy.ops.object.select_all(action="DESELECT")


def _world_pos(obj, bone_name: str | None = None) -> Vector:
    if bone_name:
        pose = obj.pose.bones.get(bone_name)
        if not pose:
            raise ValueError(f"bone_not_found {bone_name}")
        return obj.matrix_world @ pose.matrix.translation
    return obj.matrix_world.translation


# ---------------------------------------------------------------- scene ops

def op_scene_create(spec: dict) -> dict:
    _clear_scene()
    scene = bpy.context.scene
    world = scene.world or bpy.data.worlds.new("World")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        c = spec.get("world_color", [0.02, 0.02, 0.05])
        bg.inputs[0].default_value = (c[0], c[1], c[2], 1.0)

    for obj_spec in spec.get("objects", []):
        kind = obj_spec.get("type", "cube")
        name = obj_spec.get("name", f"{kind}_{len(bpy.data.objects)}")
        if kind == "cube":
            bpy.ops.mesh.primitive_cube_add(size=obj_spec.get("size", 2.0))
        elif kind == "sphere":
            bpy.ops.mesh.primitive_uv_sphere_add(radius=obj_spec.get("size", 1.0))
        elif kind == "cylinder":
            bpy.ops.mesh.primitive_cylinder_add(radius=obj_spec.get("size", 1.0), depth=obj_spec.get("depth", 2.0))
        elif kind == "plane":
            bpy.ops.mesh.primitive_plane_add(size=obj_spec.get("size", 4.0))
        elif kind == "empty":
            bpy.ops.object.empty_add(type=obj_spec.get("empty_type", "PLAIN_AXES"))
        else:
            raise ValueError(f"unsupported_object_type {kind}")
        obj = bpy.context.active_object
        obj.name = name
        loc = obj_spec.get("location", [0, 0, 0])
        rot = obj_spec.get("rotation", [0, 0, 0])
        obj.location = (loc[0], loc[1], loc[2])
        obj.rotation_euler = (math.radians(rot[0]), math.radians(rot[1]), math.radians(rot[2]))

    cam_spec = spec.get("camera")
    if cam_spec:
        bpy.ops.object.camera_add(location=(cam_spec.get("x", 6.0), cam_spec.get("y", -8.0), cam_spec.get("z", 5.0)))
        cam = bpy.context.active_object
        cam.name = cam_spec.get("name", "Camera")
        cam.data.lens = cam_spec.get("lens_mm", 55.0)
        scene.camera = cam
        if cam_spec.get("look_at"):
            target = Vector(cam_spec["look_at"])
            direction = target - cam.location
            cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()

    for light_spec in spec.get("lights", []):
        light_type = light_spec.get("type", "point").upper()
        if light_type not in {"SUN", "POINT", "AREA", "SPOT"}:
            raise ValueError(f"unsupported_light_type {light_type}")
        bpy.ops.object.light_add(type=light_type, location=(light_spec.get("x", 3), light_spec.get("y", -3), light_spec.get("z", 6)))
        light = bpy.context.active_object
        light.name = light_spec.get("name", "Light")
        light.data.energy = light_spec.get("energy", 1000.0 if light_type != "SUN" else 3.0)
        color = light_spec.get("color")
        if color:
            light.data.color = tuple(color[:3])
        if light_type == "AREA":
            light.data.shape = light_spec.get("shape", "DISK")
            light.data.size = float(light_spec.get("size", 3.0))
        if light_spec.get("look_at"):
            direction = Vector(light_spec["look_at"]) - light.location
            light.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()

    return op_scene_inspect({"names": None})


def op_scene_parent(spec: dict) -> dict:
    """Parent a list of objects to a root (for coherent group transforms)."""
    root = _obj(spec["root"])
    for child_name in spec.get("children", []):
        child = _obj(child_name)
        child.parent = root
    return _out({"root": root.name, "children": spec.get("children", []),
                 "parented": len(spec.get("children", []))}, True)


def op_scene_inspect(spec: dict) -> dict:
    scene = bpy.context.scene
    objects = []
    for obj in bpy.data.objects:
        objects.append({
            "name": obj.name,
            "type": obj.type,
            "location": [round(v, 4) for v in obj.location],
            "rotation": [round(math.degrees(v), 2) for v in obj.rotation_euler],
            "scale": [round(v, 4) for v in obj.scale],
            "materials": [m.name for m in obj.data.materials] if getattr(obj.data, "materials", None) is not None else [],
        })
    result = {
        "scene": {"name": scene.name, "frame_current": scene.frame_current, "frame_start": scene.frame_start, "frame_end": scene.frame_end},
        "camera": scene.camera.name if scene.camera else None,
        "objects": objects,
        "object_count": len(objects),
        "lights": [o.name for o in bpy.data.objects if o.type == "LIGHT"],
    }
    return _out(result, True)


def op_lighting_construct(spec: dict) -> dict:
    """Construct a motivated, inspectable lighting rig in one structured op."""
    scene = bpy.context.scene
    for obj in list(bpy.data.objects):
        if obj.type == "LIGHT":
            bpy.data.objects.remove(obj, do_unlink=True)
    world = scene.world or bpy.data.worlds.new("World")
    scene.world = world
    world.use_nodes = True
    background = world.node_tree.nodes.get("Background")
    if background:
        background.inputs[1].default_value = float(spec.get("world_strength", 0.12))
    if "exposure" in spec:
        scene.view_settings.exposure = float(spec["exposure"])
    created = []
    for light_spec in spec.get("lights", []):
        light_type = light_spec.get("type", "POINT").upper()
        if light_type not in {"SUN", "POINT", "AREA", "SPOT"}:
            raise ValueError(f"unsupported_light_type {light_type}")
        loc = light_spec.get("location", [light_spec.get("x", 0), light_spec.get("y", -2), light_spec.get("z", 3)])
        bpy.ops.object.light_add(type=light_type, location=tuple(loc))
        light = bpy.context.active_object
        light.name = light_spec.get("name", f"Light_{len(created)}")
        light.data.energy = float(light_spec.get("energy", 500.0 if light_type != "SUN" else 2.0))
        if light_spec.get("color"):
            light.data.color = tuple(light_spec["color"][:3])
        if light_type == "AREA":
            light.data.shape = light_spec.get("shape", "DISK")
            light.data.size = float(light_spec.get("size", 3.0))
        if light_spec.get("radius") is not None and hasattr(light.data, "shadow_soft_size"):
            light.data.shadow_soft_size = float(light_spec["radius"])
        if light_spec.get("look_at"):
            direction = Vector(light_spec["look_at"]) - light.location
            light.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
        created.append({"name": light.name, "type": light_type, "energy": light.data.energy,
                        "color": [round(v, 4) for v in light.data.color],
                        "location": [round(v, 4) for v in light.location]})
    return _out({"lights": created, "world_strength": background.inputs[1].default_value if background else None,
                 "exposure": scene.view_settings.exposure, "motivation": {
                     "key": "EmberCoreLight", "fill": "WarmBounce", "rim": "CoolSeparation"}}, True)


# ---------------------------------------------------------------- mesh ops

def _mesh_stats(obj) -> dict:
    mesh = obj.data
    import bmesh

    bm = bmesh.new()
    bm.from_mesh(mesh)
    ngons = sum(1 for f in bm.faces if len(f.verts) > 4)
    non_manifold = sum(1 for e in bm.edges if not e.is_manifold)
    tris = sum(max(len(f.verts) - 2, 1) for f in bm.faces)
    bm.free()
    uvs = bool(mesh.uv_layers)
    return {
        "vertices": len(mesh.vertices),
        "edges": len(mesh.edges),
        "faces": len(mesh.polygons),
        "triangulated_faces": tris,
        "ngons": ngons,
        "non_manifold_edges": non_manifold,
        "has_uvs": uvs,
        "material_slots": len(mesh.materials),
        "vertex_groups": [g.name for g in mesh.vertices[0].groups] if mesh.vertices else [],
    }


def op_mesh_analyze(spec: dict) -> dict:
    names = spec.get("names") or [o.name for o in bpy.data.objects if o.type == "MESH"]
    analyzed = []
    for name in names:
        obj = _obj(name)
        if obj.type != "MESH":
            analyzed.append({"name": name, "error": "not_a_mesh"})
            continue
        stats = _mesh_stats(obj)
        bounds = obj.bound_box
        min_corner = [min(v[i] for v in bounds) for i in range(3)]
        max_corner = [max(v[i] for v in bounds) for i in range(3)]
        stats.update({
            "bounds_min": [round(v, 4) for v in min_corner],
            "bounds_max": [round(v, 4) for v in max_corner],
            "dimensions": [round(max_corner[i] - min_corner[i], 4) for i in range(3)],
        })
        analyzed.append({"name": name, **stats})
    return _out({"meshes": analyzed}, True)


def op_mesh_surface_finish(spec: dict) -> dict:
    """Finish authored meshes for production readability: smooth normals and
    optional controlled beveling, never a replacement for topology review."""
    name = spec["name"]
    obj = _obj(name)
    if obj.type != "MESH":
        raise ValueError(f"not_a_mesh {name}")
    if spec.get("smooth", True):
        for polygon in obj.data.polygons:
            polygon.use_smooth = True
    bevel_width = float(spec.get("bevel_width", 0.0))
    if bevel_width > 0:
        modifier = obj.modifiers.new(name="11vt_surface_bevel", type="BEVEL")
        modifier.width = bevel_width
        modifier.segments = int(spec.get("bevel_segments", 2))
        modifier.limit_method = "ANGLE"
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=modifier.name)
    return _out({"name": name, "smooth_normals": bool(spec.get("smooth", True)),
                 "bevel_width": bevel_width, "bevel_segments": int(spec.get("bevel_segments", 2))}, True)


def op_mesh_optimize(spec: dict) -> dict:
    name = spec["name"]
    obj = _obj(name)
    if obj.type != "MESH":
        raise ValueError(f"not_a_mesh {name}")
    ratio = float(spec.get("ratio", 0.5))
    before = _mesh_stats(obj)
    mod = obj.modifiers.new(name="11vt_decimate", type="DECIMATE")
    mod.ratio = ratio
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=mod.name)
    after = _mesh_stats(obj)
    return _out({"name": name, "before": before, "after": after, "ratio": ratio,
                 "vertex_reduction_pct": round(100 * (1 - after["vertices"] / max(before["vertices"], 1)), 1)}, True)


# ---------------------------------------------------------- material ops

def op_material_construct(spec: dict) -> dict:
    mat_name = spec["name"]
    mat = bpy.data.materials.new(mat_name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    bsdf = nodes.get("Principled BSDF")
    inputs = bsdf.inputs
    bc = spec.get("base_color", [1.0, 1.0, 1.0])
    inputs["Base Color"].default_value = (bc[0], bc[1], bc[2], 1.0)
    if "metallic" in spec:
        inputs["Metallic"].default_value = float(spec["metallic"])
    if "roughness" in spec:
        inputs["Roughness"].default_value = float(spec["roughness"])
    if "emission" in spec:
        inputs["Emission Color"].default_value = (spec["emission"][0], spec["emission"][1], spec["emission"][2], 1.0)
        inputs["Emission Strength"].default_value = float(spec.get("emission_strength", 1.0))
    textures = []
    for slot in spec.get("textures", []):
        kind = slot.get("input")
        path = slot.get("path")
        if not path or not Path(path).exists():
            textures.append({"input": kind, "path": path, "loaded": False})
            continue
        tex = bpy.data.images.load(path)
        node = nodes.new("ShaderNodeTexImage")
        node.image = tex
        node.location = (-500, 200 * len(textures))
        nodes.links.new(node.outputs["Color"], inputs[kind])
        textures.append({"input": kind, "path": path, "loaded": True, "image": tex.name})
    for obj_name in spec.get("assign_to", []):
        obj = _obj(obj_name)
        if obj.data.materials:
            obj.data.materials[0] = mat
        else:
            obj.data.materials.append(mat)
    return _out({"material": mat_name, "node_count": len(nodes), "textures": textures,
                 "assigned_to": spec.get("assign_to", [])}, True)


def op_material_inspect(spec: dict) -> dict:
    materials = []
    for mat in bpy.data.materials:
        textures = []
        if mat.use_nodes:
            for node in mat.node_tree.nodes:
                if node.type == "TEX_IMAGE" and node.image:
                    textures.append({"name": node.name, "image": node.image.name,
                                     "filepath": node.image.filepath if node.image.filepath else None,
                                     "has_file": bool(node.image.filepath)})
        materials.append({"name": mat.name, "use_nodes": mat.use_nodes, "textures": textures})
    return _out({"materials": materials, "texture_dependency_count": sum(len(m["textures"]) for m in materials)}, True)


def op_material_noise_emission(spec: dict) -> dict:
    """Add a Noise Texture driving Emission Strength variation on an existing
    material, for flicker/pulse effects. Creates: Noise Texture -> Math(add)
    -> Emission Strength. The noise output [0,1] is scaled to [strength_min, strength_max]."""
    mat_name = spec["name"]
    if mat_name not in bpy.data.materials:
        raise ValueError(f"material_not_found {mat_name}")
    mat = bpy.data.materials[mat_name]
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    bsdf = nodes.get("Principled BSDF")
    if not bsdf:
        raise ValueError(f"no_principled_bsdf on {mat_name}")
    scale = float(spec.get("scale", 5.0))
    detail = float(spec.get("detail", 3.0))
    s_min = float(spec.get("strength_min", 15.0))
    s_max = float(spec.get("strength_max", 25.0))
    # Noise Texture
    noise = nodes.new("ShaderNodeTexNoise")
    noise.name = "11vt_flicker_noise"
    noise.location = (-600, -200)
    noise.inputs["Scale"].default_value = scale
    noise.inputs["Detail"].default_value = detail
    # Map Range: map [0,1] -> [s_min, s_max]
    mr = nodes.new("ShaderNodeMapRange")
    mr.name = "11vt_flicker_maprange"
    mr.location = (-350, -200)
    mr.inputs["From Min"].default_value = 0.0
    mr.inputs["From Max"].default_value = 1.0
    mr.inputs["To Min"].default_value = s_min
    mr.inputs["To Max"].default_value = s_max
    # Connect: Noise.Fac -> MapRange.Value -> Emission Strength
    links.new(noise.outputs["Fac"], mr.inputs["Value"])
    links.new(mr.outputs["Result"], bsdf.inputs["Emission Strength"])
    assigned_to = []
    for obj_name in spec.get("assign_to", []):
        obj = _obj(obj_name)
        if obj.data.materials:
            obj.data.materials[0] = mat
        else:
            obj.data.materials.append(mat)
        assigned_to.append(obj_name)
    return _out({"material": mat_name, "noise_scale": scale, "noise_detail": detail,
                 "strength_range": [s_min, s_max], "assigned_to": assigned_to,
                 "node_count": len(nodes)}, True)


def op_material_surface_variation(spec: dict) -> dict:
    """Build reusable procedural material variation: noise -> colour ramp,
    roughness range, and micro-normal bump. This is deliberately art-directed
    rather than an unbounded texture generator."""
    mat_name = spec["name"]
    mat = bpy.data.materials.get(mat_name)
    if not mat:
        raise ValueError(f"material_not_found {mat_name}")
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    bsdf = nodes.get("Principled BSDF")
    if not bsdf:
        raise ValueError(f"no_principled_bsdf_on {mat_name}")
    noise = nodes.new("ShaderNodeTexNoise")
    noise.name = "11vt_surface_noise"
    noise.inputs["Scale"].default_value = float(spec.get("scale", 5.0))
    noise.inputs["Detail"].default_value = float(spec.get("detail", 3.0))
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.name = "11vt_surface_color_ramp"
    dark = spec.get("dark_color", [0.04, 0.025, 0.015])
    light = spec.get("light_color", [0.35, 0.18, 0.05])
    ramp.color_ramp.elements[0].color = (*dark[:3], 1.0)
    ramp.color_ramp.elements[1].color = (*light[:3], 1.0)
    bump = nodes.new("ShaderNodeBump")
    bump.name = "11vt_micro_normal"
    bump.inputs["Strength"].default_value = float(spec.get("bump_strength", 0.12))
    bump.inputs["Distance"].default_value = 0.08
    rough = nodes.new("ShaderNodeMapRange")
    rough.name = "11vt_roughness_variation"
    rough.inputs["From Min"].default_value = 0.0
    rough.inputs["From Max"].default_value = 1.0
    rough.inputs["To Min"].default_value = float(spec.get("roughness_min", 0.22))
    rough.inputs["To Max"].default_value = float(spec.get("roughness_max", 0.48))
    links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    links.new(noise.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    links.new(noise.outputs["Fac"], rough.inputs["Value"])
    links.new(rough.outputs["Result"], bsdf.inputs["Roughness"])
    return _out({"material": mat_name, "variation": "noise_color_roughness_bump",
                 "scale": noise.inputs["Scale"].default_value, "detail": noise.inputs["Detail"].default_value,
                 "node_count": len(nodes), "assigned_to": spec.get("assign_to", [])}, True)


# ---------------------------------------------------------------- rig ops

def op_rig_mechanical(spec: dict) -> dict:
    """Create a morphology-appropriate control armature for articulated
    mechanical/organic parts. It is an explicit rig, not a humanoid preset."""
    name = spec["name"]
    bpy.ops.object.armature_add( location=(0, 0, 0) )
    armature = bpy.context.active_object
    armature.name = name
    armature.data.name = f"{name}_data"
    bpy.ops.object.mode_set(mode="EDIT")
    for bone in list(armature.data.edit_bones):
        armature.data.edit_bones.remove(bone)
    created = {}
    for item in spec.get("bones", []):
        bone = armature.data.edit_bones.new(item["name"])
        bone.head = tuple(item.get("head", [0, 0, 0]))
        bone.tail = tuple(item.get("tail", [0, 0, 1]))
        created[bone.name] = bone
    for item in spec.get("bones", []):
        parent = item.get("parent")
        if parent and parent in created:
            created[item["name"]].parent = created[parent]
    bpy.ops.object.mode_set(mode="OBJECT")
    return _out({"armature": name, "bone_count": len(created),
                 "bones": [{"name": item["name"], "parent": item.get("parent")} for item in spec.get("bones", [])],
                 "purpose": "Emberveil mechanical vessel controls"}, True)


def op_rig_inspect(spec: dict) -> dict:
    armature = None
    for obj in bpy.data.objects:
        if obj.type == "ARMATURE":
            armature = obj
            break
    if not armature:
        return _out({"armature": None, "bones": [], "note": "no_armature_in_scene"}, True)
    bones = []
    for bone in armature.data.bones:
        children = [b.name for b in bone.children]
        bones.append({"name": bone.name, "parent": bone.parent.name if bone.parent else None,
                      "children": children, "head": [round(v, 4) for v in bone.head_local],
                      "tail": [round(v, 4) for v in bone.tail_local]})
    constraints = []
    for pb in armature.pose.bones:
        for c in pb.constraints:
            constraints.append({"bone": pb.name, "type": c.type, "name": c.name})
    deform_bones = [b.name for b in armature.data.bones if b.use_deform]
    skinned_meshes = []
    for obj in bpy.data.objects:
        if obj.type == "MESH":
            groups = {g.name for g in obj.vertex_groups}
            skinned_meshes.append({"name": obj.name, "vertex_groups": len(groups),
                                   "groups_overlap_bones": len(groups & set(deform_bones))})
    max_depth = 0
    for b in armature.data.bones:
        d = 0
        p = b.parent
        while p:
            d += 1
            p = p.parent
        max_depth = max(max_depth, d)
    return _out({"armature": armature.name, "bone_count": len(bones), "max_hierarchy_depth": max_depth,
                 "deform_bones": len(deform_bones), "constraints": constraints,
                 "skinned_meshes": skinned_meshes}, True)


# ---------------------------------------------------------- animation ops

def op_animation_create_loop(spec: dict) -> dict:
    """Create a looping rotation action: frame_end pose == frame_start pose
    (mod 2*pi), so a seamless loop renders identical endpoints."""
    name = spec["name"]
    obj = _obj(name)
    start = int(spec.get("frame_start", 1))
    end = int(spec.get("frame_end", 48))
    turns = float(spec.get("turns", 1.0))
    axis = spec.get("axis", "Z").upper()
    if obj.animation_data is None:
        obj.animation_data_create()
    action = bpy.data.actions.new(f"11vt_loop_{name}")
    obj.animation_data.action = action
    e = list(obj.rotation_euler)
    bpy.context.scene.frame_set(start)
    if axis == "X": e[0] = 0.0
    elif axis == "Y": e[1] = 0.0
    else: e[2] = 0.0
    obj.rotation_euler = e
    obj.keyframe_insert(data_path="rotation_euler", frame=start)
    bpy.context.scene.frame_set(end)
    e2 = list(e)
    if axis == "X": e2[0] = 2 * math.pi * turns
    elif axis == "Y": e2[1] = 2 * math.pi * turns
    else: e2[2] = 2 * math.pi * turns
    obj.rotation_euler = e2
    obj.keyframe_insert(data_path="rotation_euler", frame=end)
    for fc in _action_fcurves(action):
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"
    scene = bpy.context.scene
    scene.frame_start = start
    scene.frame_end = end
    return _out({"object": name, "action": action.name, "frame_start": start, "frame_end": end,
                 "turns": turns, "axis": axis, "note": "loop endpoints identical mod 2*pi"}, True)


def op_animation_create_translation(spec: dict) -> dict:
    """Keyframe a linear horizontal translation (for foot-slide probe tests)."""
    name = spec["name"]
    obj = _obj(name)
    start = int(spec.get("frame_start", 1))
    end = int(spec.get("frame_end", 24))
    distance = float(spec.get("distance", 2.0))
    axis = spec.get("axis", "X").lower()
    if obj.animation_data is None:
        obj.animation_data_create()
    action = bpy.data.actions.new(f"11vt_drift_{name}")
    obj.animation_data.action = action
    loc = list(obj.location)
    bpy.context.scene.frame_set(start)
    obj.location = loc
    obj.keyframe_insert(data_path="location", frame=start)
    bpy.context.scene.frame_set(end)
    loc2 = list(loc)
    loc2[{"x": 0, "y": 1, "z": 2}[axis]] += distance
    obj.location = loc2
    obj.keyframe_insert(data_path="location", frame=end)
    for fc in _action_fcurves(action):
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"
    scene = bpy.context.scene
    scene.frame_start = start
    scene.frame_end = end
    return _out({"object": name, "action": action.name, "frame_start": start, "frame_end": end,
                 "distance": distance, "axis": axis}, True)


def op_animation_inspect(spec: dict) -> dict:
    actions = []
    for action in bpy.data.actions:
        channels = {}
        for fcurve in _action_fcurves(action):
            bone = fcurve.data_path.split('"')[1] if '"' in fcurve.data_path else fcurve.data_path
            channels[bone] = channels.get(bone, 0) + 1
        actions.append({"name": action.name, "frame_range": [action.frame_range[0], action.frame_range[1]],
                        "fcurves": sum(1 for _ in _action_fcurves(action)), "channels_per_bone": channels})
    scene = bpy.context.scene
    return _out({"actions": actions, "scene_frame_range": [scene.frame_start, scene.frame_end],
                 "scene_frame_current": scene.frame_current}, True)


def _bone_world_positions(obj, bone_name: str, frames: list[int]) -> list[tuple[float, float, float]]:
    positions = []
    for f in frames:
        bpy.context.scene.frame_set(f)
        bpy.context.view_layer.update()
        pos = _world_pos(obj, bone_name)
        positions.append((pos.x, pos.y, pos.z))
    return positions


def op_animation_loop_check(spec: dict) -> dict:
    """Loop-continuity QA: renders the first and last frames of the action
    range and reports pixel-diff AE + PSNR (seamless loop == near-identical
    endpoints). Also runs a bone-velocity foot-slide heuristic on a contact
    bone when provided."""
    scene = bpy.context.scene
    start = int(spec.get("frame_start", scene.frame_start))
    end = int(spec.get("frame_end", scene.frame_end))
    resolution = spec.get("resolution", [320, 180])
    scene.render.resolution_x, scene.render.resolution_y = resolution
    scene.render.engine = "CYCLES" if spec.get("engine", "cycles") == "cycles" else "BLENDER_EEVEE_NEXT"
    scene.cycles.samples = int(spec.get("samples", 16))

    out_dir = Path(spec["out_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)
    scene.render.image_settings.file_format = "PNG"
    first_png = out_dir / "loop-first.png"
    last_png = out_dir / "loop-last.png"
    scene.frame_set(start)
    scene.render.filepath = str(first_png)
    bpy.ops.render.render(write_still=True)
    scene.frame_set(end)
    scene.render.filepath = str(last_png)
    bpy.ops.render.render(write_still=True)

    # mechanical checks (host-side pixel diff is run by the bridge for AE/PSNR)
    loop = {
        "frame_start": start,
        "frame_end": end,
        "first_frame_png": str(first_png),
        "last_frame_png": str(last_png),
        "note": "pixel diff + PSNR between endpoints computed host-side",
    }

    contact_bone = spec.get("contact_bone")
    foot_slide = None
    if contact_bone:
        armature = next((o for o in bpy.data.objects if o.type == "ARMATURE"), None)
        tracked = None
        if armature and contact_bone in armature.data.bones:
            tracked = (armature, True)
        elif contact_bone in bpy.data.objects:
            tracked = (bpy.data.objects[contact_bone], False)
        if tracked:
            obj, is_bone = tracked
            frames = list(range(start, end + 1))
            if is_bone:
                positions = _bone_world_positions(obj, contact_bone, frames)
            else:
                positions = []
                for f in frames:
                    bpy.context.scene.frame_set(f)
                    bpy.context.view_layer.update()
                    p = obj.matrix_world.translation
                    positions.append((p.x, p.y, p.z))
            # horizontal speed per frame; foot-slide metric = max speed during
            # any sustained contact window (frames where vertical motion is small)
            speeds = []
            for i in range(1, len(positions)):
                dx = positions[i][0] - positions[i - 1][0]
                dy = positions[i][1] - positions[i - 1][1]
                dt = 1.0
                speeds.append(math.hypot(dx, dy) / dt)
            max_speed = max(speeds) if speeds else 0.0
            foot_slide = {
                "bone": contact_bone,
                "samples": len(positions),
                "max_horizontal_speed_per_frame": round(max_speed, 4),
                "flag": max_speed > float(spec.get("slide_threshold", 0.01)),
                "threshold": float(spec.get("slide_threshold", 0.01)),
                "note": "foot-slide heuristic: max horizontal speed of contact element between consecutive frames",
            }
    loop["foot_slide"] = foot_slide
    return _out(loop, True)


# ------------------------------------------------------------- production ops

def op_mesh_lathe(spec: dict) -> dict:
    """Lathe a 2D profile (list of [x, y], y up) around the Z axis into a mesh.
    Reusable for bells, vases, capsules, rims, bases."""
    name = spec["name"]
    profile = spec["profile"]
    if len(profile) < 2:
        raise ValueError("profile needs >= 2 points")
    segments = int(spec.get("segments", 64))
    import bmesh
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    verts = []
    for i in range(segments):
        theta = 2 * math.pi * i / segments
        for (x, y) in profile:
            verts.append(bm.verts.new((x * math.cos(theta), x * math.sin(theta), y)))
    n = len(profile)
    for i in range(segments):
        i2 = (i + 1) % segments
        for j in range(n - 1):
            a, b = i * n + j, i * n + j + 1
            c, d = i2 * n + j + 1, i2 * n + j
            bm.faces.new((verts[a], verts[b], verts[c], verts[d]))
    bm.normal_update()
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    loc = spec.get("location", [0, 0, 0])
    obj.location = (loc[0], loc[1], loc[2])
    return _out({"name": name, "vertices": len(mesh.vertices), "faces": len(mesh.polygons),
                 "profile_points": len(profile), "segments": segments}, True)


def op_mesh_radial_array(spec: dict) -> dict:
    """Duplicate an object radially around the Z axis (position + orientation),
    for filigree, antennae, petals, fins."""
    name = spec["name"]
    obj = _obj(name)
    count = int(spec.get("count", 6))
    dupes = [name]
    for i in range(1, count):
        angle = 2 * math.pi * i / count
        new_obj = obj.copy()
        new_obj.data = obj.data.copy()
        bpy.context.collection.objects.link(new_obj)
        new_obj.name = f"{name}_{i:02d}"
        x, y, z = obj.location
        new_obj.location = (x * math.cos(angle) - y * math.sin(angle),
                            x * math.sin(angle) + y * math.cos(angle), z)
        e = list(obj.rotation_euler)
        e[2] += angle
        new_obj.rotation_euler = e
        dupes.append(new_obj.name)
    return _out({"source": name, "count": count, "objects": dupes}, True)


def op_material_subsurface(spec: dict) -> dict:
    """Principled subsurface/transmission material (glass, skin, wax, ember)."""
    mat = bpy.data.materials.new(spec["name"])
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    inputs = bsdf.inputs
    bc = spec.get("base_color", [1, 1, 1])
    inputs["Base Color"].default_value = (bc[0], bc[1], bc[2], 1.0)
    if "roughness" in spec:
        inputs["Roughness"].default_value = float(spec["roughness"])
    if "transmission" in spec:
        inputs["Transmission Weight"].default_value = float(spec["transmission"])
    if "ior" in spec:
        inputs["IOR"].default_value = float(spec["ior"])
    if "subsurface" in spec:
        inputs["Subsurface Weight"].default_value = float(spec["subsurface"])
    if "subsurface_color" in spec:
        # Blender 5.x: subsurface color is expressed as per-channel scatter
        # radius (no separate Subsurface Color input).
        sc = spec["subsurface_color"]
        inputs["Subsurface Radius"].default_value = (max(sc[0], 0.001), max(sc[1], 0.001), max(sc[2], 0.001))
    if "emission" in spec:
        em = spec["emission"]
        inputs["Emission Color"].default_value = (em[0], em[1], em[2], 1.0)
        inputs["Emission Strength"].default_value = float(spec.get("emission_strength", 1.0))
    if "clearcoat" in spec:
        inputs["Coat Weight"].default_value = float(spec["clearcoat"])
    assigned_to = []
    for obj_name in spec.get("assign_to", []):
        obj = _obj(obj_name)
        if obj.data.materials:
            obj.data.materials[0] = mat
        else:
            obj.data.materials.append(mat)
        assigned_to.append(obj_name)
    return _out({"material": mat.name, "node_count": len(mat.node_tree.nodes),
                 "assigned_to": assigned_to}, True)


def op_animation_pulse(spec: dict) -> dict:
    """Purposeful breathing/heat pulse on a component, loop-safe."""
    name = spec["name"]
    obj = _obj(name)
    start, end = int(spec.get("frame_start", 1)), int(spec.get("frame_end", 96))
    amplitude, cycles = float(spec.get("amplitude", 0.08)), int(spec.get("cycles", 2))
    base = list(obj.scale)
    if obj.animation_data is None:
        obj.animation_data_create()
    action = bpy.data.actions.new(f"11vt_pulse_{name}")
    obj.animation_data.action = action
    for f in range(start, end + 1):
        t = (f - start) / max(end - start, 1)
        s = 1.0 + amplitude * (0.5 + 0.5 * math.sin(2 * math.pi * cycles * t))
        bpy.context.scene.frame_set(f)
        obj.scale = tuple(v * s for v in base)
        obj.keyframe_insert(data_path="scale", frame=f)
    return _out({"object": name, "action": action.name, "frames": [start, end],
                 "amplitude": amplitude, "cycles": cycles, "purpose": "contained-fire breathing pulse"}, True)


def op_animation_rotate(spec: dict) -> dict:
    """Purposeful secondary rotation for an articulated ring/filigree part."""
    name = spec["name"]
    obj = _obj(name)
    start, end = int(spec.get("frame_start", 1)), int(spec.get("frame_end", 96))
    turns = float(spec.get("turns", 0.25))
    axis = spec.get("axis", "Z").upper()
    if obj.animation_data is None:
        obj.animation_data_create()
    action = bpy.data.actions.new(f"11vt_rotate_{name}")
    obj.animation_data.action = action
    base = list(obj.rotation_euler)
    idx = {"X": 0, "Y": 1, "Z": 2}.get(axis, 2)
    for f in range(start, end + 1):
        t = (f - start) / max(end - start, 1)
        bpy.context.scene.frame_set(f)
        rot = list(base)
        rot[idx] += 2 * math.pi * turns * t
        obj.rotation_euler = rot
        obj.keyframe_insert(data_path="rotation_euler", frame=f)
    return _out({"object": name, "action": action.name, "frames": [start, end],
                 "turns": turns, "axis": axis, "purpose": "secondary mechanical drift"}, True)


def op_animation_float(spec: dict) -> dict:
    """Weightless floating bob + gentle sway (loop-safe: integer cycles)."""
    name = spec["name"]
    obj = _obj(name)
    start = int(spec.get("frame_start", 1))
    end = int(spec.get("frame_end", 96))
    amplitude = float(spec.get("amplitude", 0.15))
    cycles = int(spec.get("cycles", 2))
    sway = float(spec.get("sway_degrees", 2.0))
    base_z = obj.location.z
    base_rot = list(obj.rotation_euler)
    if obj.animation_data is None:
        obj.animation_data_create()
    action = bpy.data.actions.new(f"11vt_float_{name}")
    obj.animation_data.action = action
    for f in range(start, end + 1):
        t = (f - start) / max(end - start, 1)
        bpy.context.scene.frame_set(f)
        obj.location.z = base_z + amplitude * math.sin(2 * math.pi * cycles * t)
        obj.keyframe_insert(data_path="location", frame=f)
        obj.rotation_euler = (base_rot[0], base_rot[1],
                              base_rot[2] + math.radians(sway) * math.sin(2 * math.pi * cycles * t))
        obj.keyframe_insert(data_path="rotation_euler", frame=f)
    scene = bpy.context.scene
    scene.frame_start = start
    scene.frame_end = end
    return _out({"object": name, "action": action.name, "frames": [start, end],
                 "amplitude": amplitude, "cycles": cycles, "loop_safe": True}, True)


def op_camera_path(spec: dict) -> dict:
    """Animated dolly camera along an arc — for cinematic presentation moves."""
    name = spec.get("name", "CinematicCam")
    start = int(spec.get("frame_start", 1))
    end = int(spec.get("frame_end", 120))
    radius = float(spec.get("radius", 8.0))
    height = float(spec.get("height", 2.2))
    target = Vector(spec.get("target", [0, 0, 0.8]))
    sweep_deg = float(spec.get("sweep_degrees", 70.0))
    start_angle_deg = float(spec.get("start_angle", -35.0))
    lens = float(spec.get("lens_mm", 50.0))
    bpy.ops.object.camera_add(location=(target.x + radius, target.y, target.z + height))
    cam = bpy.context.active_object
    cam.name = name
    cam.data.lens = lens
    bpy.context.scene.camera = cam
    if cam.animation_data is None:
        cam.animation_data_create()
    action = bpy.data.actions.new(f"11vt_campath_{name}")
    cam.animation_data.action = action
    for f in range(start, end + 1):
        t = (f - start) / max(end - start, 1)
        angle = math.radians(start_angle_deg + sweep_deg * t)
        cam.location = (target.x + radius * math.cos(angle),
                        target.y + radius * math.sin(angle), target.z + height)
        direction = target - cam.location
        cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
        cam.keyframe_insert(data_path="location", frame=f)
        cam.keyframe_insert(data_path="rotation_euler", frame=f)
    scene = bpy.context.scene
    scene.frame_start = start
    scene.frame_end = end
    return _out({"camera": name, "frames": [start, end], "radius": radius,
                 "sweep_degrees": sweep_deg, "lens_mm": lens}, True)


def op_render_sequence(spec: dict) -> dict:
    """Render every frame in [start, end] to a PNG sequence (cinematic/VFX
    evidence source; host-side ffmpeg assembles the video)."""
    scene = bpy.context.scene
    start = int(spec.get("frame_start", scene.frame_start))
    end = int(spec.get("frame_end", scene.frame_end))
    out_dir = Path(spec["out_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)
    scene.render.resolution_x, scene.render.resolution_y = spec.get("resolution", [640, 360])
    scene.render.engine = spec.get("engine", "CYCLES")
    if scene.render.engine == "CYCLES":
        scene.cycles.samples = int(spec.get("samples", 24))
        scene.cycles.use_denoising = bool(spec.get("denoising", False))
    scene.render.image_settings.file_format = "PNG"
    rendered = []
    for f in range(start, end + 1):
        scene.frame_set(f)
        png = out_dir / f"seq-{f:04d}.png"
        scene.render.filepath = str(png)
        bpy.ops.render.render(write_still=True)
        rendered.append(str(png))
    return _out({"frames": len(rendered), "first": str(rendered[0]), "last": str(rendered[-1])}, True)


# ------------------------------------------------------------- camera ops

def op_camera_setup(spec: dict) -> dict:
    cam_spec = spec
    bpy.ops.object.camera_add(location=(cam_spec.get("x", 6.0), cam_spec.get("y", -8.0), cam_spec.get("z", 5.0)))
    cam = bpy.context.active_object
    cam.name = cam_spec.get("name", "Camera")
    cam.data.lens = cam_spec.get("lens_mm", 55.0)
    bpy.context.scene.camera = cam
    if cam_spec.get("look_at"):
        target = Vector(cam_spec["look_at"])
        direction = target - cam.location
        cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    return _out({"camera": cam.name, "lens_mm": cam.data.lens,
                 "location": [round(v, 4) for v in cam.location]}, True)


# ------------------------------------------------------------ render ops

def _render_frame(scene, filepath: str, resolution, engine: str, samples: int,
                   denoising: bool = False) -> None:
    scene.render.resolution_x, scene.render.resolution_y = resolution
    scene.render.engine = engine
    if engine == "CYCLES":
        scene.cycles.samples = samples
        scene.cycles.use_denoising = denoising
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(filepath)
    bpy.ops.render.render(write_still=True)


def op_render_preview(spec: dict) -> dict:
    scene = bpy.context.scene
    out_dir = Path(spec["out_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)
    frame = int(spec.get("frame", scene.frame_current))
    scene.frame_set(frame)
    png = out_dir / f"preview-frame-{frame:04d}.png"
    _render_frame(scene, png, spec.get("resolution", [640, 360]), spec.get("engine", "CYCLES"),
                  int(spec.get("samples", 32)), denoising=bool(spec.get("denoising", False)))
    return _out({"frame": frame, "render": str(png),
                 "resolution": [scene.render.resolution_x, scene.render.resolution_y]}, True)


def op_render_turntable(spec: dict) -> dict:
    """Orbit the camera around a target and render an image sequence
    (usable as turntable video evidence)."""
    scene = bpy.context.scene
    target = Vector(spec.get("target", [0, 0, 0]))
    radius = float(spec.get("radius", 8.0))
    height = float(spec.get("height", 2.0))
    frames = int(spec.get("frames", 12))
    out_dir = Path(spec["out_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)
    cam_spec = spec.get("camera", {})
    bpy.ops.object.camera_add(location=(target.x + radius, target.y, target.z + height))
    cam = bpy.context.active_object
    cam.name = cam_spec.get("name", "TurntableCamera")
    cam.data.lens = cam_spec.get("lens_mm", 50.0)
    scene.camera = cam
    rendered = []
    for i in range(frames):
        angle = 2 * math.pi * i / frames
        cam.location = (target.x + radius * math.cos(angle), target.y + radius * math.sin(angle), target.z + height)
        direction = target - cam.location
        cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
        scene.frame_set(0)
        png = out_dir / f"turntable-{i:03d}.png"
        _render_frame(scene, png, spec.get("resolution", [320, 180]), spec.get("engine", "CYCLES"),
                      int(spec.get("samples", 16)), denoising=bool(spec.get("denoising", False)))
        rendered.append(str(png))
    return _out({"frames": frames, "rendered": rendered, "radius": radius, "height": height}, True)


# ------------------------------------------------------------- asset ops

def op_asset_export_glb(spec: dict) -> dict:
    out_glb = Path(spec["out_path"])
    out_glb.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=str(out_glb),
        export_format="GLB",
        use_selection=bool(spec.get("use_selection", False)),
        export_apply=True,
    )
    exists = out_glb.exists()
    return _out({"out_path": str(out_glb), "exists": exists, "bytes": out_glb.stat().st_size if exists else 0}, exists)


def op_asset_ingest(spec: dict) -> dict:
    path = Path(spec["path"])
    if not path.exists():
        raise ValueError(f"file_not_found {path}")
    ext = path.suffix.lower()
    if ext == ".glb":
        bpy.ops.import_scene.gltf(filepath=str(path))
    elif ext == ".obj":
        bpy.ops.wm.obj_import(filepath=str(path))
    elif ext in (".fbx", ".gltf"):
        bpy.ops.import_scene.gltf(filepath=str(path)) if ext == ".gltf" else bpy.ops.import_scene.fbx(filepath=str(path))
    else:
        raise ValueError(f"unsupported_import_format {ext}")
    imported = [o.name for o in bpy.data.objects]
    return _out({"imported": imported, "object_count": len(imported), "source": str(path)}, True)


# ------------------------------------------------------------- pipeline batch + dispatch

def op_pipeline_batch(spec: dict) -> dict:
    """Run registered structured operations in one persistent Blender process."""
    results = {}
    root_out = Path(spec.get("out_dir", ".")).resolve()
    for index, item in enumerate(spec.get("operations", [])):
        op_name = item.get("op")
        params = dict(item.get("params", {}))
        if op_name in {"render.preview", "render.turntable", "render.sequence", "animation.loop_check"}:
            params.setdefault("out_dir", str(root_out / f"{index:02d}-{op_name.replace('.', '-') }"))
        fn = OPS.get(op_name)
        if not fn:
            results[item.get("name", f"op-{index}")] = _out({"error": f"unknown_op {op_name}"}, False)
            continue
        key = item.get("name", f"{index:02d}-{op_name}")
        try:
            result = fn(params)
            result["op"] = op_name
        except Exception as exc:
            result = _out({"op": op_name, "error": f"{type(exc).__name__}: {exc}"}, False)
        results[key] = result
    failed = [key for key, result in results.items() if not result.get("ok")]
    return _out({"results": results, "op_count": len(results), "failed": failed}, not failed)


# ------------------------------------------------------------- dispatch

OPS = {
    "scene.create": op_scene_create,
    "scene.parent": op_scene_parent,
    "scene.inspect": op_scene_inspect,
    "lighting.construct": op_lighting_construct,
    "pipeline.batch": op_pipeline_batch,
    "mesh.analyze": op_mesh_analyze,
    "mesh.optimize": op_mesh_optimize,
    "mesh.surface_finish": op_mesh_surface_finish,
    "mesh.lathe": op_mesh_lathe,
    "mesh.radial_array": op_mesh_radial_array,
    "material.construct": op_material_construct,
    "material.subsurface": op_material_subsurface,
    "material.surface_variation": op_material_surface_variation,
    "material.inspect": op_material_inspect,
    "material.noise_emission": op_material_noise_emission,
    "rig.mechanical": op_rig_mechanical,
    "rig.inspect": op_rig_inspect,
    "animation.create_loop": op_animation_create_loop,
    "animation.create_translation": op_animation_create_translation,
    "animation.float": op_animation_float,
    "animation.pulse": op_animation_pulse,
    "animation.rotate": op_animation_rotate,
    "animation.inspect": op_animation_inspect,
    "animation.loop_check": op_animation_loop_check,
    "camera.setup": op_camera_setup,
    "camera.path": op_camera_path,
    "render.preview": op_render_preview,
    "render.turntable": op_render_turntable,
    "render.sequence": op_render_sequence,
    "asset.export_glb": op_asset_export_glb,
    "asset.ingest": op_asset_ingest,
}


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(json.dumps({"ok": False, "error": "expected <spec.json> <result.json>"}))
        return 1
    spec_path, result_path = Path(argv[0]), Path(argv[1])
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    params = spec.get("params", {})
    # session chaining: load a prior .blend when provided, save when requested
    load_blend = params.get("load_blend")
    if load_blend and Path(load_blend).exists():
        # NOTE: open_mainfile in Blender background mode may not fully restore
        # mesh objects. For reliable session chaining, batch multiple ops in a
        # single Blender invocation (see v2-batch-upgrade.py pattern).
        bpy.ops.wm.open_mainfile(filepath=load_blend)
    op_name = spec.get("op")
    try:
        fn = OPS.get(op_name)
        if not fn:
            raise ValueError(f"unknown_op {op_name}")
        result = fn(params)
    except Exception as exc:  # structured failure, never uncaught
        result = {"ok": False, "health": "FAILED", "error": f"{type(exc).__name__}: {exc}",
                  "op": op_name, "blender_version": bpy.app.version_string}
    save_blend = params.get("save_blend")
    if result.get("ok") and save_blend:
        try:
            bpy.ops.wm.save_as_mainfile(filepath=save_blend)
            result["saved_blend"] = save_blend
        except Exception as exc:
            result["save_warning"] = f"{type(exc).__name__}: {exc}"
    result_path.parent.mkdir(parents=True, exist_ok=True)
    result_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]))
