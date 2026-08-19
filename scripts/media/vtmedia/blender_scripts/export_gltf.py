import sys
from pathlib import Path
import bpy
args = sys.argv[sys.argv.index('--') + 1:]
out = Path(args[0])
out.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.export_scene.gltf(filepath=str(out), export_format='GLB')
print('11VT_GLTF_EXPORTED ' + str(out))
