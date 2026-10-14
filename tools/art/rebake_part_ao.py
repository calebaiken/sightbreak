"""Re-bake the ambient occlusion of one part of an unwrapped bake, with the rest of the
model hidden, so only the part's own occlusion is left.

python rebake_part_ao.py <bake_dir/name.blend> <object> <out_dir> [--size 2048] [--samples 48]

Why: bake.py bakes occlusion with every part in place. A part that moves in game (the
magazine, which reload pulls out of the magwell) is baked while seated, so the faces that
were inside the well come out fully occluded and are black the moment the part is pulled
out. The occlusion of such a part should be its own.

Writes <out_dir>/<object>_ao_on_black.png and <object>_ao_on_white.png: the same bake onto
a black and onto a white canvas. A texel that belongs to the part's UV islands (and their
bleed margin) is identical in both; every other texel is black in one and white in the
other, so the islands are exactly the texels where the two agree, even where the occlusion
itself is 0. patch_part_ao.py merges them into a full bake. Run with Blender's Python (bpy).
"""
import pathlib
import sys
import bpy

args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
size, samples = 2048, 48
if '--size' in args:
    i = args.index('--size'); size = int(args[i + 1]); del args[i:i + 2]
if '--samples' in args:
    i = args.index('--samples'); samples = int(args[i + 1]); del args[i:i + 2]
blend, part, out = pathlib.Path(args[0]).resolve(), args[1], pathlib.Path(args[2]).resolve()
out.mkdir(parents=True, exist_ok=True)

bpy.ops.wm.open_mainfile(filepath=str(blend))
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = samples
# The same contact distance bake.py uses.
scene.world.light_settings.distance = 0.035
target = bpy.data.objects[part]
for obj in bpy.data.objects:
    if obj.type == 'MESH' and obj is not target:
        obj.hide_render = True
        obj.hide_viewport = True
target.hide_render = False
bpy.ops.object.select_all(action='DESELECT')
target.select_set(True)
bpy.context.view_layer.objects.active = target
margin = max(4, size // 256)


def bake_onto(fill, label):
    image = bpy.data.images.new(f'{part}_{label}', size, size, alpha=False)
    image.generated_color = (fill, fill, fill, 1.0)
    image.colorspace_settings.name = 'Non-Color'
    for material in target.data.materials:
        tree = material.node_tree
        node = tree.nodes.get('bake_target') or tree.nodes.new('ShaderNodeTexImage')
        node.name = 'bake_target'
        node.image = image
        tree.nodes.active = node
    bpy.ops.object.bake(type='AO', margin=margin, use_clear=False, target='IMAGE_TEXTURES')
    image.filepath_raw = str(out / f'{part}_{label}.png')
    image.file_format = 'PNG'
    image.save()
    print('BAKED', label, out / f'{part}_{label}.png')


bake_onto(0.0, 'ao_on_black')
bake_onto(1.0, 'ao_on_white')
