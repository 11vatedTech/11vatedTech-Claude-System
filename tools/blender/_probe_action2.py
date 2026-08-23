
import bpy, math
bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0,0,2))
pivot = bpy.context.object
pivot.keyframe_insert(data_path='rotation_euler', frame=1)
pivot.rotation_euler = (0,0,math.radians(30))
pivot.keyframe_insert(data_path='rotation_euler', frame=10)
action = pivot.animation_data.action
print('is_action_layered:', action.is_action_layered)
print('is_action_legacy:', action.is_action_legacy)
print('layers:', action.layers)
print('slots:', action.slots)
# Try accessing keyframes through layers/slots
for layer in action.layers:
    print(f'Layer: {layer.name}, strips: {len(layer.strips)}')
    for strip in layer.strips:
        print(f'  Strip: {strip.type}, channels: {dir(strip)}')
        for attr in ['channels', 'channelbags', 'keys', 'keyframes']:
            if hasattr(strip, attr):
                print(f'    has {attr}')
                val = getattr(strip, attr)
                print(f'    value: {val}')
