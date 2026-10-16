"""Fast shape review of the right glove: the SDF at a coarse voxel size, Workbench-rendered from the back, the palm, the side and a
three-quarter view, with each region in its own flat colour (so panels and caps can be read), in about a minute.

python preview_glove.py <out_dir> [--h 0.0010] [--size 900x600]

This is a review of silhouettes and panels in the rest pose, not of the shipped mesh or of textures (the shipped one is arms_build.py's).
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Vector  # noqa: E402
import relay_ar_arms as arms  # noqa: E402
import sdf  # noqa: E402

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
OUT = os.path.abspath(argv[0])
H = float(argv[argv.index('--h') + 1]) if '--h' in argv else 0.0010
W, HT = (int(v) for v in (argv[argv.index('--size') + 1] if '--size' in argv else '900x600').split('x'))
os.makedirs(OUT, exist_ok=True)

# flat review colours per region (sRGB-ish, brightened so the zones are legible)
COLOURS = {'fabric': (0.34, 0.37, 0.43), 'palm': (0.55, 0.50, 0.42), 'shell': (0.08, 0.08, 0.09), 'strap': (0.70, 0.55, 0.20),
           'cuff': (0.26, 0.30, 0.36), 'seam': (0.82, 0.82, 0.78), 'tip': (0.55, 0.50, 0.42), 'pad': (0.20, 0.22, 0.26)}

shapes = arms.glove_shapes()
v, q = sdf.mesh(lambda P: arms.glove_distance(P, shapes), *arms.glove_bounds(), H)
centres = (v[q[:, 0]] + v[q[:, 2]]) / 2
reg = sdf.nearest_region(centres, [s for s, k in shapes[0]], 'fabric')
reg = np.where(reg == None, 'fabric', reg)  # noqa: E711
names = list(COLOURS)
mats = []
for n in names:
    m = bpy.data.materials.new(n)
    m.use_nodes = True
    bsdf = m.node_tree.nodes['Principled BSDF']
    bsdf.inputs['Base Color'].default_value = (*COLOURS[n], 1)
    bsdf.inputs['Roughness'].default_value = 0.55
    mats.append(m)
me = bpy.data.meshes.new('glove')
me.from_pydata([tuple(map(float, p)) for p in v], [], [tuple(map(int, f)) for f in q])
me.update()
for m in mats:
    me.materials.append(m)
me.polygons.foreach_set('material_index', [names.index(r) if r in names else 0 for r in reg])
for p in me.polygons:
    p.use_smooth = True
obj = bpy.data.objects.new('glove', me)
bpy.context.scene.collection.objects.link(obj)

scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 24
scene.cycles.use_denoising = False
scene.render.resolution_x, scene.render.resolution_y = W, HT
scene.world = bpy.data.worlds.new('w')
scene.world.use_nodes = True
scene.world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.5, 0.55, 0.58, 1)
scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.30
for loc, energy in (((0.3, -0.3, 0.6), 9.0), ((-0.4, 0.2, 0.3), 3.5)):
    light = bpy.data.objects.new('l', bpy.data.lights.new('l', 'AREA'))
    light.data.energy = energy
    light.data.size = 0.4
    light.location = loc
    bpy.context.scene.collection.objects.link(light)
    light.rotation_euler = (Vector((0.0, 0.05, 0.0)) - light.location).to_track_quat('-Z', 'Y').to_euler()
cam_data = bpy.data.cameras.new('cam')
cam_data.lens = 70
cam = bpy.data.objects.new('cam', cam_data)
bpy.context.scene.collection.objects.link(cam)
scene.camera = cam
target = Vector((0.0, 0.05, 0.0))
VIEWS = {  # name: direction from the target (hand-local: +Y fingers, +Z back of the hand), distance
    'back': (Vector((0.15, -0.25, 1.0)), 0.42),
    'palm': (Vector((0.10, -0.20, -1.0)), 0.42),
    'side': (Vector((-1.0, -0.2, 0.25)), 0.42),
    'three_quarter': (Vector((-0.6, -0.7, 0.7)), 0.44),
}
for name, (direction, dist) in VIEWS.items():
    d = direction.normalized()
    cam.location = target + d * dist
    cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = os.path.join(OUT, f'glove_{name}.png')
    bpy.ops.render.render(write_still=True)
print('triangles (high, voxel %.4f):' % H, int(sum(len(p.vertices) - 2 for p in me.polygons)))
