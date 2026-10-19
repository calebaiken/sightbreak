"""Review render of the box-modelled glove cage (hand_cage.py): the low-poly glove, flat shaded with its edges drawn, beside nothing
else, from four views; and the same silhouette over the high-poly glove. A shape and topology review, not a texture one.

python preview_cage.py <out_dir> [--size 1000x700] [--no-high]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Vector  # noqa: E402
import hand_cage  # noqa: E402
import relay_ar_arms as arms  # noqa: E402
import sdf  # noqa: E402

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
OUT = os.path.abspath(argv[0])
W, HT = (int(v) for v in (argv[argv.index('--size') + 1] if '--size' in argv else '1000x700').split('x'))
os.makedirs(OUT, exist_ok=True)
low = hand_cage.glove_low_object()
print('cage glove: %d vertices, %d faces, %d triangles' % (len(low.data.vertices), len(low.data.polygons), sum(len(p.vertices) - 2 for p in low.data.polygons)))
mat = bpy.data.materials.new('low')
mat.use_nodes = True
mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.55, 0.60, 0.68, 1)
mat.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.6
low.data.materials.append(mat)
wire = low.modifiers.new('wire', 'WIREFRAME')
wire.thickness = 0.00035
wire.use_replace = False
wmat = bpy.data.materials.new('wire')
wmat.use_nodes = True
wmat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.05, 0.05, 0.06, 1)
low.data.materials.append(wmat)
wire.material_offset = 1
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
    scene.collection.objects.link(light)
    light.rotation_euler = (Vector((0.0, 0.05, 0.0)) - light.location).to_track_quat('-Z', 'Y').to_euler()
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
cam.data.lens = 70
scene.collection.objects.link(cam)
scene.camera = cam
target = Vector((0.0, 0.05, 0.0))
VIEWS = {'back': (Vector((0.15, -0.25, 1.0)), 0.42), 'palm': (Vector((0.10, -0.20, -1.0)), 0.42),
         'side': (Vector((-1.0, -0.2, 0.25)), 0.42), 'three_quarter': (Vector((-0.6, -0.7, 0.7)), 0.44)}
for name, (direction, dist) in VIEWS.items():
    cam.location = target + direction.normalized() * dist
    cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = os.path.join(OUT, 'cage_%s.png' % name)
    bpy.ops.render.render(write_still=True)
