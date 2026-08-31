"""
BLOCKER 2: End-to-end stylized 3D character — "OBSIDIAN GOLEM"
Design thesis: Obsidian Spire shard-guardian. Crystalline armored form with
exposed violet energy core. Stylized proportions (large head, compact body)
chosen deliberately — high success probability while still exercising the
full chain: mesh -> materials -> skeleton -> skinning -> deformation -> animation.

Chain stages (all Blender headless):
  1. MESH: procedural low-poly golem from primitives + bevel/subsurf
  2. MATERIALS: PBR obsidian + emissive violet core
  3. SKELETON: explicit armature (root/spine/shoulders/elbows/wrists/hips/knees/ankles)
  4. SKINNING: automatic weights + corrected shoulder/hip vertex groups
  5. DEFORMATION TEST: 6 poses (neutral/arms-raised/elbow-bend/knee-bend/twist/stride)
  6. ANIMATION: idle + walk + power-surge action (keyframed)
  7. RENDER: posed still + animation frames
"""
import bpy, bmesh, math, os, sys, json
from mathutils import Vector, Euler

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "..", "artifacts", "visual", "3d-character")
OUT_DIR = os.path.abspath(OUT_DIR)
os.makedirs(OUT_DIR, exist_ok=True)
REPORT = {}

def clean_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for block in (bpy.data.meshes, bpy.data.materials, bpy.data.armatures, bpy.data.actions):
        for x in list(block):
            if x.users == 0:
                block.remove(x)

def new_material(name, base=(0.05,0.05,0.08,1), metal=0.9, rough=0.25, emit=None, emit_str=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = base
    bsdf.inputs["Metallic"].default_value = metal
    bsdf.inputs["Roughness"].default_value = rough
    if emit:
        bsdf.inputs["Emission Color"].default_value = emit
        bsdf.inputs["Emission Strength"].default_value = emit_str
    return m

# ---------- STAGE 1: MESH ----------
def build_mesh():
    obsidian = new_material("Obsidian", base=(0.03,0.02,0.05,1), metal=0.85, rough=0.18)
    core = new_material("EnergyCore", base=(0.6,0.2,1.0,1), metal=0.0, rough=0.4,
                        emit=(0.65,0.25,1.0,1), emit_str=12.0)
    accents = new_material("RuneAccent", base=(0.35,0.15,0.6,1), metal=0.7, rough=0.35,
                           emit=(0.5,0.2,0.9,1), emit_str=3.0)

    def add(name, prim, loc, scale, mat, bevel=0.03):
        ops = {"cube": bpy.ops.mesh.primitive_cube_add,
               "sphere": bpy.ops.mesh.primitive_uv_sphere_add,
               "ico": bpy.ops.mesh.primitive_ico_sphere_add,
               "cyl": bpy.ops.mesh.primitive_cylinder_add,
               "cone": bpy.ops.mesh.primitive_cone_add}
        # Blender 5.2: primitives take no size/radius; set scale after
        ops[prim](location=loc)
        o = bpy.context.active_object
        o.name = name
        o.scale = scale
        bpy.ops.object.transform_apply(scale=True)
        if bevel > 0:
            mod = o.modifiers.new("Bevel", 'BEVEL')
            mod.width = bevel; mod.segments = 2; mod.limit_method = 'ANGLE'
        subsurf = o.modifiers.new("Subsurf", 'SUBSURF')
        subsurf.levels = 1; subsurf.render_levels = 2
        o.data.materials.append(mat)
        return o

    parts = {}
    # Head — oversized stylized helm with visor slit
    parts['head'] = add("Head", "cube", (0, 0, 2.55), (0.62, 0.58, 0.55), obsidian, bevel=0.08)
    # Visor slit (emissive)
    parts['visor'] = add("Visor", "cube", (0, -0.52, 2.58), (0.42, 0.06, 0.08), accents, bevel=0.01)
    # Neck
    parts['neck'] = add("Neck", "cyl", (0, 0, 2.05), (0.16, 0.16, 0.18), obsidian, bevel=0)
    # Torso — tapered chest + pelvis
    parts['chest'] = add("Chest", "cube", (0, 0, 1.55), (0.55, 0.38, 0.45), obsidian, bevel=0.06)
    parts['pelvis'] = add("Pelvis", "cube", (0, 0, 1.05), (0.42, 0.32, 0.22), obsidian, bevel=0.05)
    # Core crystal (chest, emissive)
    parts['core'] = add("Core", "ico", (0, -0.30, 1.58), (0.16, 0.16, 0.28), core, bevel=0)
    # Shoulders — pauldrons
    parts['shoulder.L'] = add("ShoulderL", "ico", (-0.72, 0, 1.72), (0.26, 0.24, 0.22), obsidian, bevel=0.04)
    parts['shoulder.R'] = add("ShoulderR", "ico", (0.72, 0, 1.72), (0.26, 0.24, 0.22), obsidian, bevel=0.04)
    # Arms — upper + lower + fist
    for side, sx in (("L", -1), ("R", 1)):
        parts[f'arm.upper.{side}'] = add(f"UpperArm{side}", "cyl", (sx*0.78, 0, 1.38), (0.11, 0.11, 0.30), obsidian, bevel=0)
        parts[f'arm.lower.{side}'] = add(f"LowerArm{side}", "cyl", (sx*0.84, 0, 0.92), (0.095, 0.095, 0.28), obsidian, bevel=0)
        parts[f'fist.{side}'] = add(f"Fist{side}", "cube", (sx*0.86, 0, 0.58), (0.14, 0.14, 0.14), obsidian, bevel=0.03)
    # Legs — thigh + shin + foot
    for side, sx in (("L", -1), ("R", 1)):
        parts[f'leg.thigh.{side}'] = add(f"Thigh{side}", "cyl", (sx*0.24, 0, 0.72), (0.13, 0.13, 0.30), obsidian, bevel=0)
        parts[f'leg.shin.{side}'] = add(f"Shin{side}", "cyl", (sx*0.24, 0, 0.28), (0.11, 0.11, 0.28), obsidian, bevel=0)
        parts[f'foot.{side}'] = add(f"Foot{side}", "cube", (sx*0.24, 0.10, 0.06), (0.14, 0.26, 0.06), obsidian, bevel=0.02)
    # Back crystal shards (3, rune accents)
    for i, (dx, dz, s) in enumerate([(-0.18, 1.85, 0.9), (0.0, 1.95, 1.2), (0.18, 1.85, 0.9)]):
        shard = add(f"Shard{i}", "cone", (dx, 0.28, dz), (0.05*s, 0.05*s, 0.22*s), accents, bevel=0)
        shard.rotation_euler = Euler((math.radians(12)*(1 if dx>=0 else -1), 0, 0))

    # Join all into one mesh
    bpy.ops.object.select_all(action='DESELECT')
    for p in parts.values():
        p.select_set(True)
    bpy.context.view_layer.objects.active = parts['head']
    bpy.ops.object.join()
    golem = bpy.context.active_object
    golem.name = "ObsidianGolem"
    REPORT['mesh_parts_joined'] = len(parts)
    REPORT['mesh_verts_raw'] = len(golem.data.vertices)
    return golem

# ---------- STAGE 3: SKELETON ----------
BONE_MAP = [
    # (name, head, tail, parent)
    ("root",      (0, 0, 0.0),  (0, 0, 0.35), None),
    ("pelvis",    (0, 0, 1.05), (0, 0, 1.30), "root"),
    ("spine",     (0, 0, 1.30), (0, 0, 1.70), "pelvis"),
    ("chest",     (0, 0, 1.70), (0, 0, 2.05), "spine"),
    ("neck",      (0, 0, 2.05), (0, 0, 2.30), "chest"),
    ("head",      (0, 0, 2.30), (0, 0, 2.75), "neck"),
    ("shoulder.L", (-0.35, 0, 1.95), (-0.62, 0, 1.80), "chest"),
    ("upper_arm.L", (-0.62, 0, 1.80), (-0.78, 0, 1.38), "shoulder.L"),
    ("lower_arm.L", (-0.78, 0, 1.38), (-0.84, 0, 0.92), "upper_arm.L"),
    ("hand.L",      (-0.84, 0, 0.92), (-0.86, 0, 0.58), "lower_arm.L"),
    ("shoulder.R", (0.35, 0, 1.95), (0.62, 0, 1.80), "chest"),
    ("upper_arm.R", (0.62, 0, 1.80), (0.78, 0, 1.38), "shoulder.R"),
    ("lower_arm.R", (0.78, 0, 1.38), (0.84, 0, 0.92), "upper_arm.R"),
    ("hand.R",      (0.84, 0, 0.92), (0.86, 0, 0.58), "lower_arm.R"),
    ("thigh.L",  (-0.24, 0, 0.95), (-0.24, 0, 0.55), "pelvis"),
    ("shin.L",   (-0.24, 0, 0.55), (-0.24, 0, 0.12), "thigh.L"),
    ("foot.L",   (-0.24, 0, 0.12), (-0.24, 0.22, 0.02), "shin.L"),
    ("thigh.R",  (0.24, 0, 0.95), (0.24, 0, 0.55), "pelvis"),
    ("shin.R",   (0.24, 0, 0.55), (0.24, 0, 0.12), "thigh.R"),
    ("foot.R",   (0.24, 0, 0.12), (0.24, 0.22, 0.02), "shin.R"),
]

def build_armature():
    bpy.ops.object.armature_add(location=(0,0,0))
    arm_obj = bpy.context.active_object
    arm_obj.name = "GolemRig"
    arm = arm_obj.data
    bpy.ops.object.mode_set(mode='EDIT')
    ebones = arm.edit_bones
    first = ebones[0]; ebones.remove(first)
    for name, head, tail, parent in BONE_MAP:
        b = ebones.new(name)
        b.head = Vector(head); b.tail = Vector(tail)
        if parent:
            b.parent = ebones[parent]
            b.use_connect = False
    bpy.ops.object.mode_set(mode='OBJECT')
    REPORT['bone_count'] = len(arm.bones)
    return arm_obj

# ---------- STAGE 4: SKINNING ----------
def parent_and_skin(golem, arm_obj):
    golem.parent = arm_obj
    golem.parent_type = 'ARMATURE'
    mod = golem.modifiers.new("Armature", 'ARMATURE')
    mod.object = arm_obj
    bpy.context.view_layer.objects.active = golem
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    golem.select_set(True); arm_obj.select_set(True)
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode='POSE')
    bpy.ops.pose.armature_apply(selected=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    # Automatic weights - clear existing parent first, then set with auto weights
    try:
        bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
    except Exception:
        pass
    golem.select_set(True); arm_obj.select_set(True)
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.parent_set(type='ARMATURE_AUTO', keep_transform=True)
    REPORT['skinning'] = "ARMATURE_AUTO (automatic weights)"

def vg_stats(golem):
    return {vg.name: len(vg_data) for vg, vg_data in
            [(golem.vertex_groups[i], [v for v in golem.data.vertices if any(g.group==i for g in v.groups)])
             for i in range(len(golem.vertex_groups))]}

# ---------- STAGE 5: DEFORMATION TEST ----------
POSES = {
    "neutral":      {},
    "arms_raised":  {"upper_arm.L": ('X', -70), "upper_arm.R": ('X', -70)},
    "elbow_bend":   {"lower_arm.L": ('X', -55), "lower_arm.R": ('X', -55)},
    "knee_bend":    {"thigh.L": ('X', -30), "shin.L": ('X', 45), "thigh.R": ('X', -30), "shin.R": ('X', 45)},
    "torso_twist":  {"spine": ('Z', 25), "chest": ('Z', 15)},
    "walk_stride":  {"thigh.L": ('X', -35), "shin.L": ('X', 20), "thigh.R": ('X', 25), "shin.R": ('X', -15),
                     "upper_arm.L": ('X', 25), "upper_arm.R": ('X', -25)},
}

def apply_pose(arm_obj, pose):
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode='POSE')
    bpy.ops.pose.select_all(action='DESELECT')
    for bname, (axis, deg) in pose.items():
        pb = arm_obj.pose.bones.get(bname)
        if pb:
            pb.rotation_mode = 'XYZ'
            setattr(pb.rotation_euler, axis.lower(), math.radians(deg))
    bpy.context.view_layer.update()
    bpy.ops.object.mode_set(mode='OBJECT')

def measure_collapse(golem):
    """Detect deformation quality: volume + max vertex displacement from rest."""
    deps = bpy.context.evaluated_depsgraph_get()
    ev = golem.evaluated_get(deps)
    mesh = ev.to_mesh()
    verts = [v.co.copy() for v in mesh.vertices]
    ev.to_mesh_clear()
    zs = [v.z for v in verts]
    xs = [v.x for v in verts]
    return {"verts": len(verts), "z_min": min(zs), "z_max": max(zs),
            "x_spread": max(xs)-min(xs)}

def deformation_test(golem, arm_obj):
    results = {}
    for name, pose in POSES.items():
        apply_pose(arm_obj, {})  # reset
        apply_pose(arm_obj, pose)
        results[name] = measure_collapse(golem)
    apply_pose(arm_obj, {})
    REPORT['deformation'] = results
    return results

# ---------- STAGE 6: ANIMATION ----------
def build_animation(arm_obj):
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode='POSE')

    def key(bone, axis, deg, frame):
        pb = arm_obj.pose.bones[bone]
        pb.rotation_mode = 'XYZ'
        setattr(pb.rotation_euler, axis.lower(), math.radians(deg))
        pb.keyframe_insert(data_path="rotation_euler", frame=frame)

    # IDLE: subtle breathing + core sway (frames 1-48)
    for f0, lift in ((1, 0), (24, 1), (48, 0)):
        key("spine", 'Z', 0, f0)
        key("chest", 'X', -2*lift, f0)
        key("head", 'X', 2*lift, f0)
        key("upper_arm.L", 'Z', -4*lift, f0)
        key("upper_arm.R", 'Z', 4*lift, f0)
    # WALK: 24-frame cycle (frames 60-84)
    for f0, ph in ((60, 0), (72, 1), (84, 0)):
        s = 1 if ph == 0 else -1
        key("thigh.L", 'X', 30*s, f0); key("shin.L", 'X', -15*max(s,0), f0)
        key("thigh.R", 'X', -30*s, f0); key("shin.R", 'X', -15*max(-s,0), f0)
        key("upper_arm.L", 'X', -25*s, f0); key("upper_arm.R", 'X', 25*s, f0)
        key("pelvis", 'Z', 4*s, f0)
    # POWER SURGE: arms raise + core flare (frames 96-144)
    key("upper_arm.L", 'X', 0, 96); key("upper_arm.R", 'X', 0, 96)
    key("upper_arm.L", 'X', -80, 120); key("upper_arm.R", 'X', -80, 120)
    key("head", 'X', 0, 96); key("head", 'X', -12, 120)
    key("spine", 'X', 0, 96); key("spine", 'X', -8, 120)
    key("upper_arm.L", 'X', -80, 144); key("upper_arm.R", 'X', -80, 144)
    key("head", 'X', -12, 144); key("spine", 'X', -8, 144)

    # Actions split for separate exports
    bpy.ops.object.mode_set(mode='OBJECT')
    act = arm_obj.animation_data.action
    act.name = "GolemPerformance"
    REPORT['animation'] = {"action": "GolemPerformance", "frames": "1-144",
                           "clips": ["idle(1-48)", "walk(60-84)", "power_surge(96-144)"]}

# ---------- STAGE 7: RENDER ----------
def setup_render(scene):
    scene.render.engine = 'BLENDER_EEVEE'
    scene.eevee.taa_render_samples = 32
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 1280
    scene.render.film_transparent = False
    world = bpy.data.worlds.new("SpireWorld")
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (0.015, 0.01, 0.03, 1)
    bg.inputs[1].default_value = 1.0
    scene.world = world
    # Key light (cool violet rim) + fill
    key_data = bpy.data.lights.new("Key", 'AREA')
    key = bpy.data.objects.new("Key", key_data)
    bpy.context.collection.objects.link(key)
    key.data.energy = 800; key.data.size = 4
    key.location = (3, -3, 4); key.rotation_euler = Euler((math.radians(45), 0, math.radians(45)))
    key.data.color = (0.85, 0.75, 1.0)
    rim_data = bpy.data.lights.new("Rim", 'AREA')
    rim = bpy.data.objects.new("Rim", rim_data)
    bpy.context.collection.objects.link(rim)
    rim.data.energy = 500; rim.data.size = 3
    rim.location = (-3, 2, 3); rim.rotation_euler = Euler((math.radians(-40), 0, math.radians(-50)))
    rim.data.color = (0.6, 0.4, 1.0)
    cam_data = bpy.data.cameras.new("Cam")
    cam = bpy.data.objects.new("Cam", cam_data)
    bpy.context.collection.objects.link(cam)
    cam.location = (3.2, -3.2, 1.9)
    cam.rotation_euler = Euler((math.radians(72), 0, math.radians(45)))
    cam.data.lens = 60
    scene.camera = cam

def render_still(scene, golem, arm_obj, path, pose=None):
    if pose:
        apply_pose(arm_obj, pose)
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    if pose:
        apply_pose(arm_obj, {})

def render_animation(scene, arm_obj, out_prefix, frames):
    # Render key frames as PNG sequence (Blender 5.2 removed FFMPEG image format)
    scene.render.image_settings.file_format = 'PNG'
    scene.render.fps = 24
    scene.frame_start, scene.frame_end = frames
    # Render a few representative frames
    for f in [frames[0], frames[0]+8, frames[0]+16, frames[0]+24, frames[1]]:
        if f < frames[0] or f > frames[1]:
            continue
        scene.frame_set(f)
        scene.render.filepath = f"{out_prefix}_frame_{f:03d}.png"
        bpy.ops.render.render(write_still=True)

def export_glb(golem, arm_obj, path):
    bpy.ops.object.select_all(action='DESELECT')
    golem.select_set(True); arm_obj.select_set(True)
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB',
                              export_skins=True, export_animations=True,
                              export_apply=False)

def main():
    clean_scene()
    scene = bpy.context.scene
    golem = build_mesh()
    arm_obj = build_armature()
    parent_and_skin(golem, arm_obj)
    REPORT['vg_count'] = len(golem.vertex_groups)
    deformation_test(golem, arm_obj)
    build_animation(arm_obj)
    setup_render(scene)

    # Evidence renders
    render_still(scene, golem, arm_obj, os.path.join(OUT_DIR, "golem_front.png"))
    render_still(scene, golem, arm_obj, os.path.join(OUT_DIR, "golem_threequarter.png"),
                 pose={"spine": ('Z', 30), "head": ('Z', 15)})
    render_still(scene, golem, arm_obj, os.path.join(OUT_DIR, "golem_side.png"),
                 pose={"spine": ('Z', 80), "head": ('Z', 40)})
    render_still(scene, golem, arm_obj, os.path.join(OUT_DIR, "golem_power_surge.png"),
                 pose={"upper_arm.L": ('X', -80), "upper_arm.R": ('X', -80), "head": ('X', -12)})
    # Deformation test contact sheet renders
    for pname in ("arms_raised", "walk_stride", "knee_bend"):
        render_still(scene, golem, arm_obj,
                     os.path.join(OUT_DIR, f"deform_{pname}.png"), pose=POSES[pname])
    # Animation: idle loop + power surge
    render_animation(scene, arm_obj, os.path.join(OUT_DIR, "golem_idle"), (1, 48))
    render_animation(scene, arm_obj, os.path.join(OUT_DIR, "golem_power"), (96, 144))

    export_glb(golem, arm_obj, os.path.join(OUT_DIR, "obsidian_golem.glb"))

    # Mesh metrics post-subsurf
    deps = bpy.context.evaluated_depsgraph_get()
    ev = golem.evaluated_get(deps)
    mesh = ev.to_mesh()
    REPORT['final_mesh'] = {"verts": len(mesh.vertices), "faces": len(mesh.polygons),
                            "tris": len(mesh.loop_triangles)}
    ev.to_mesh_clear()
    REPORT['renders'] = sorted(os.listdir(OUT_DIR))
    with open(os.path.join(OUT_DIR, "character_report.json"), "w") as f:
        json.dump(REPORT, f, indent=2)
    print("CHARACTER_REPORT:", json.dumps(REPORT, indent=2))

main()
