"""Regroup a baked .blend (bake.py) into game meshes and export a GLB for Godot.

python export.py <generator.py> <bake_dir> <out.glb>

Groups follow the generator's GROUPS (one draw each, everything else joins 'body').
The magazine's second material becomes the child 'magazine_rounds' so the reload
animation moves both. Marker empties (muzzle, ejection, reticle) and the generator's
ANCHORS are exported as nodes. UVs and normals are kept exactly as baked.
"""
import importlib.util
import pathlib
import sys
import bpy

args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
gen_path, bake_dir, out = pathlib.Path(args[0]).resolve(), pathlib.Path(args[1]).resolve(), pathlib.Path(args[2]).resolve()
name = gen_path.stem
sys.path.insert(0, str(gen_path.parent))
spec = importlib.util.spec_from_file_location('gen', gen_path)
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)
bpy.ops.wm.open_mainfile(filepath=str(bake_dir / f'{name}.blend'))


def select(objects):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objects:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]


def join(objects, group):
    if len(objects) > 1:
        select(objects)
        bpy.ops.object.join()
    joined = bpy.context.view_layer.objects.active if len(objects) > 1 else objects[0]
    joined.name = joined.data.name = group
    return joined


atlas = bpy.data.materials.new(f'{name}_atlas')
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
assigned = {}
for group, parts in gen.GROUPS.items():
    for o in meshes:
        if o.name.split('.')[0] in parts:
            assigned.setdefault(group, []).append(o)
body = [o for o in meshes if not any(o in v for v in assigned.values())]
groups = {g: join(objs, g) for g, objs in assigned.items()}
if body:
    groups['body'] = join(body, 'body')

# Split the magazine's cartridge (second material) into a child that follows it.
mag = groups.get('magazine')
if mag is not None and len(mag.data.materials) > 1:
    select([mag])
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    mag.active_material_index = 1
    bpy.ops.object.material_slot_select()
    bpy.ops.mesh.separate(type='SELECTED')
    bpy.ops.object.mode_set(mode='OBJECT')
    rounds = next(o for o in bpy.context.selected_objects if o != mag)
    rounds.name = rounds.data.name = 'magazine_rounds'
    rounds.parent = mag
    rounds.matrix_parent_inverse = mag.matrix_world.inverted()
    groups['magazine_rounds'] = rounds

for o in groups.values():
    o.data.materials.clear()
    o.data.materials.append(atlas)
for anchor, at in gen.ANCHORS.items():
    empty = bpy.data.objects.new(anchor, None)
    bpy.context.collection.objects.link(empty)
    empty.location = at
for o in bpy.data.objects:
    if o.type not in ('MESH', 'EMPTY'):
        bpy.data.objects.remove(o, do_unlink=True)
tris = {g: sum(len(p.vertices) - 2 for p in o.data.polygons) for g, o in groups.items()}
out.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.export_scene.gltf(filepath=str(out), export_format='GLB', export_apply=True, export_extras=True,
                          export_materials='PLACEHOLDER', export_texcoords=True, export_normals=True,
                          export_tangents=False, export_yup=True)
print('EXPORTED', out, tris, 'total', sum(tris.values()),
      'nodes', sorted(o.name for o in bpy.data.objects))
