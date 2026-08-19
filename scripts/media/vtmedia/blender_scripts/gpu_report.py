import json
import bpy
prefs = bpy.context.preferences.addons['cycles'].preferences
report = {'blender': bpy.app.version_string, 'devices': {}}
for backend in ['OPTIX','CUDA','HIP','ONEAPI','METAL','NONE']:
    try:
        prefs.compute_device_type = backend
        prefs.get_devices()
        report['devices'][backend] = [{'name': d.name, 'type': d.type, 'use': d.use} for d in prefs.devices]
    except Exception as exc:
        report['devices'][backend] = {'error': type(exc).__name__ + ': ' + str(exc)}
print('11VT_BLENDER_GPU_REPORT ' + json.dumps(report))
