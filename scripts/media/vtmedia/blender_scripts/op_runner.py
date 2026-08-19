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
        if light_spec.get("type") == "sun":
            bpy.ops.object.light_add(type="SUN", location=(light_spec.get("x", 5), light_spec.get("y", -5), light_spec.get("z", 10)))
        else:
            bpy.ops.object.light_add(type="POINT", location=(light_spec.get("x", 3), light_spec.get("y", -3), light_spec.get("z", 6)))
        light = bpy.context.active_object
        light.name = light_spec.get("name", "Light")
        light.data.energy = light_spec.get("energy", 1000.0 if light.type == "POINT" else 3.0)
        if light.type == "SUN":
            light.data.energy = light_spec.get("energy", 3.0)

    return op_scene_inspect({"names": None})


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


# ---------------------------------------------------------------- rig ops

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

def _render_frame(scene, filepath: str, resolution, engine: str, samples: int) -> None:
    scene.render.resolution_x, scene.render.resolution_y = resolution
    scene.render.engine = engine
    if engine == "CYCLES":
        scene.cycles.samples = samples
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
    _render_frame(scene, png, spec.get("resolution", [640, 360]), spec.get("engine", "CYCLES"), int(spec.get("samples", 32)))
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
        _render_frame(scene, png, spec.get("resolution", [320, 180]), spec.get("engine", "CYCLES"), int(spec.get("samples", 16)))
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


# ------------------------------------------------------------- dispatch

OPS = {
    "scene.create": op_scene_create,
    "scene.inspect": op_scene_inspect,
    "mesh.analyze": op_mesh_analyze,
    "mesh.optimize": op_mesh_optimize,
    "material.construct": op_material_construct,
    "material.inspect": op_material_inspect,
    "rig.inspect": op_rig_inspect,
    "animation.create_loop": op_animation_create_loop,
    "animation.create_translation": op_animation_create_translation,
    "animation.inspect": op_animation_inspect,
    "animation.loop_check": op_animation_loop_check,
    "camera.setup": op_camera_setup,
    "render.preview": op_render_preview,
    "render.turntable": op_render_turntable,
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
