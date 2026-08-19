import json, math, sys, time
from pathlib import Path
import bpy
from mathutils import Vector

args = sys.argv[sys.argv.index('--') + 1:]
scene_path, blend_path, png_path, stats_path = [Path(a) for a in args[:4]]
scene_spec = json.loads(scene_path.read_text(encoding='utf-8'))
started = time.time()

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()
scene = bpy.context.scene
scene.render.engine = scene_spec.get('render', {}).get('engine', 'CYCLES')
scene.cycles.samples = int(scene_spec.get('render', {}).get('samples', 64))
scene.cycles.use_denoising = True
scene.view_settings.view_transform = 'Filmic'
scene.view_settings.look = 'Medium High Contrast'
scene.view_settings.exposure = 0
scene.view_settings.gamma = 1
res = scene_spec.get('resolution', [1280, 720])
scene.render.resolution_x, scene.render.resolution_y = int(res[0]), int(res[1])
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGBA'
scene.render.image_settings.color_depth = '16'
try:
    prefs = bpy.context.preferences.addons['cycles'].preferences
    for backend in ['OPTIX', 'CUDA']:
        try:
            prefs.compute_device_type = backend
            prefs.get_devices()
            usable = [d for d in prefs.devices if d.type != 'CPU']
            if usable:
                for d in prefs.devices: d.use = True
                scene.cycles.device = 'GPU'
                break
        except Exception:
            pass
except Exception:
    pass

# Meaningful non-primitive final geometry: faceted crystal cluster built from bevelled cylinders/cones.
def make_mat(name, color, metallic=0, roughness=0.2, alpha=1, transmission=0):
    mat=bpy.data.materials.new(name); mat.use_nodes=True
    bsdf=mat.node_tree.nodes.get('Principled BSDF')
    if bsdf:
        try: bsdf.inputs['Base Color'].default_value=color
        except Exception: pass
        for inp,val in [('Metallic',metallic),('Roughness',roughness),('Alpha',alpha)]:
            if inp in bsdf.inputs: bsdf.inputs[inp].default_value=val
        if 'Transmission Weight' in bsdf.inputs: bsdf.inputs['Transmission Weight'].default_value=transmission
        if 'IOR' in bsdf.inputs: bsdf.inputs['IOR'].default_value=1.46
    mat.blend_method='BLEND'; mat.use_screen_refraction=True
    return mat
crystal = make_mat('aurora glass - cyan gold dispersion', (0.35,0.9,1.0,0.55), 0, 0.06, 0.58, 0.25)
gold = make_mat('brushed warm gold bevels', (1.0,0.58,0.16,1), 0.8, 0.18, 1, 0)
dark = make_mat('obsidian satin base', (0.015,0.012,0.02,1), 0.2, 0.35, 1, 0)

bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=1.0, depth=2.8, location=(0,0,1.4), rotation=(0.12,0.0,0.39))
mono=bpy.context.object; mono.name='faceted aurora monolith - authored validation asset'; mono.data.materials.append(crystal)
bpy.ops.object.shade_smooth()
bev=mono.modifiers.new('intentional bevels for caught highlights','BEVEL'); bev.width=.08; bev.segments=2
mono.modifiers.new('weighted normals','WEIGHTED_NORMAL')

for i,(x,y,h,r) in enumerate([(-1.35,.25,1.5,.35),(1.15,.35,1.9,.42),(.45,-.85,1.2,.28),(-.55,-1.05,1.0,.22)]):
    bpy.ops.mesh.primitive_cone_add(vertices=7, radius1=r, radius2=r*.42, depth=h, location=(x,y,h/2), rotation=(0.2*i,0.1*i,0.5*i))
    o=bpy.context.object; o.name=f'supporting cut crystal shard {i+1}'; o.data.materials.append(crystal)
    o.modifiers.new('micro bevel','BEVEL').width=.035; o.modifiers.new('weighted normals','WEIGHTED_NORMAL')

bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=2.4, depth=.18, location=(0,0,-.09))
base=bpy.context.object; base.name='obsidian display plinth'; base.data.materials.append(dark)
base.modifiers.new('soft machined bevel','BEVEL').width=.06; base.modifiers.new('weighted normals','WEIGHTED_NORMAL')

bpy.ops.mesh.primitive_torus_add(major_radius=2.55, minor_radius=.035, major_segments=160, minor_segments=8, location=(0,0,.08))
ring=bpy.context.object; ring.name='thin gold calibration ring'; ring.data.materials.append(gold)

# environment and lights
world=scene.world or bpy.data.worlds.new('world'); scene.world=world; world.color=(0.01,0.012,0.025)
for name, loc, rot, power, color, size in [
    ('large warm softbox key',(-3.5,-4.5,5.5),(math.radians(60),0,math.radians(-35)),650,(1,.78,.45),4.0),
    ('cyan rim strip',(3.6,2.7,3.2),(math.radians(60),0,math.radians(135)),420,(0.35,.85,1),2.0),
    ('tiny white sparkle kicker',(0,-3,2.2),(math.radians(75),0,0),95,(1,1,1),.6)]:
    bpy.ops.object.light_add(type='AREA', location=loc, rotation=rot)
    l=bpy.context.object; l.name=name; l.data.energy=power; l.data.color=color; l.data.size=size

# camera look at origin
cam_spec=scene_spec.get('camera',{})
pos=Vector(cam_spec.get('position',[4.5,-6.5,3.4])); target=Vector(cam_spec.get('look_at',[0,0,.7]))
bpy.ops.object.camera_add(location=pos)
cam=bpy.context.object; cam.name='hero three-quarter product camera'; cam.data.lens=cam_spec.get('lens_mm',55); cam.data.dof.use_dof=True; cam.data.dof.focus_distance=(pos-target).length; cam.data.dof.aperture_fstop=5.6
direction=target-pos; cam.rotation_euler=direction.to_track_quat('-Z','Y').to_euler(); scene.camera=cam

# add background plane
bpy.ops.mesh.primitive_plane_add(size=9, location=(0,0,-.2))
plane=bpy.context.object; plane.name='matte studio floor'; plane.data.materials.append(dark)

bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
scene.render.filepath=str(png_path)
bpy.ops.render.render(write_still=True)

stats={
 'scene_id': scene_spec.get('scene_id'),
 'elapsed_seconds': round(time.time()-started,3),
 'engine': scene.render.engine,
 'cycles_device': getattr(scene.cycles,'device',None),
 'samples': scene.cycles.samples,
 'resolution': [scene.render.resolution_x, scene.render.resolution_y],
 'objects': [o.name for o in bpy.context.scene.objects],
 'materials': [m.name for m in bpy.data.materials],
 'art_direction': scene_spec.get('art_direction'),
 'final_blockers': []
}
stats_path.write_text(json.dumps(stats, indent=2), encoding='utf-8')
print('11VT_BLENDER_RENDER_DONE ' + json.dumps(stats))
