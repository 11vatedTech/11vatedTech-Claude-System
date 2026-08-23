
import bpy

# Create a temporary material to inspect inputs
mat = bpy.data.materials.new('ProbeMat')
mat.use_nodes = True  # Still works in 5.2, deprecated but functional
nodes = mat.node_tree.nodes
nodes.clear()

bsdf = nodes.new('ShaderNodeBsdfPrincipled')
print('=== Principled BSDF Inputs (Blender 5.2) ===')
for inp in bsdf.inputs:
    print(f'  {inp.name!r}: type={inp.type} identifier={inp.identifier!r}')

bpy.data.materials.remove(mat)
