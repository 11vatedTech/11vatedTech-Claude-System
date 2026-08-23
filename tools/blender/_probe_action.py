
import bpy
import math
bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0,0,2))
pivot = bpy.context.object
pivot.keyframe_insert(data_path='rotation_euler', frame=1)
pivot.rotation_euler = (0,0,math.radians(30))
pivot.keyframe_insert(data_path='rotation_euler', frame=10)
action = pivot.animation_data.action
print('Action attrs:', [a for a in dir(action) if not a.startswith('_')])
for attr in ['fcurves', 'fcurves', 'FCurves', 'FCurves']:
    if hasattr(action, attr):
        print(f'  {attr}: {getattr(action, attr)}')
        break
