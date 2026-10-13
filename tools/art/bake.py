"""Unwrap and texture-bake a generator module (relay_ar.py, relay_ar_hands.py).

python bake.py <generator.py> <out_dir> [--size 2048] [--samples 64]

Writes raw bake passes <name>_{albedo,roughness,normal,occlusion,metallic}_raw.png
(normal: tangent space, OpenGL +Y) and <name>.blend (unjoined, unwrapped parts with
their procedural materials) for hand editing and for export.py. Surface detail comes
from object-space procedural materials, so it is continuous across UV seams.
"""
import importlib.util
import math
import pathlib
import sys
import bpy
from mathutils import Vector

args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
size, samples = 2048, 64
if '--size' in args:
    i = args.index('--size'); size = int(args[i + 1]); del args[i:i + 2]
if '--samples' in args:
    i = args.index('--samples'); samples = int(args[i + 1]); del args[i:i + 2]
gen_path, out = pathlib.Path(args[0]).resolve(), pathlib.Path(args[1]).resolve()
out.mkdir(parents=True, exist_ok=True)
name = gen_path.stem
sys.path.insert(0, str(gen_path.parent))
spec = importlib.util.spec_from_file_location('gen', gen_path)
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)
gen.build()

scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
# Ambient occlusion is a contact term at weapon scale: 3.5 cm, not the default
# world distance, which darkens whole faces that merely face other parts.
if scene.world is None:
    scene.world = bpy.data.worlds.new('bake')
scene.world.light_settings.distance = 0.035
meshes = [o for o in bpy.data.objects if o.type == 'MESH']

# ------------------------------------------------------------------ UV atlas
bpy.ops.object.select_all(action='DESELECT')
for o in meshes:
    o.select_set(True)
bpy.context.view_layer.objects.active = meshes[0]
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=math.radians(55), island_margin=0.0015, area_weight=0.0, correct_aspect=True, scale_to_bounds=False)
bpy.ops.uv.pack_islands(rotate=True, margin=0.0025)
bpy.ops.object.mode_set(mode='OBJECT')

# ------------------------------------------------------------------ procedural surfaces
# name: (base linear rgb, metallic, roughness, edge rgb, edge metallic, edge roughness, micro bump, stipple)
SURFACES = {
    'anodized': ((0.040, 0.043, 0.047), 0.70, 0.42, (0.30, 0.31, 0.32), 1.0, 0.30, 0.15, 0.0),
    'steel': ((0.030, 0.031, 0.033), 0.95, 0.36, (0.22, 0.22, 0.23), 1.0, 0.26, 0.10, 0.0),
    'polymer': ((0.105, 0.088, 0.064), 0.0, 0.64, (0.15, 0.13, 0.10), 0.0, 0.48, 0.20, 0.0),
    'rubber': ((0.020, 0.020, 0.021), 0.0, 0.88, (0.035, 0.035, 0.036), 0.0, 0.80, 0.25, 0.6),
    'glass': ((0.012, 0.025, 0.022), 0.0, 0.05, (0.012, 0.025, 0.022), 0.0, 0.05, 0.0, 0.0),
    'brass': ((0.42, 0.27, 0.08), 1.0, 0.32, (0.55, 0.40, 0.16), 1.0, 0.22, 0.05, 0.0),
    'glove': ((0.022, 0.021, 0.020), 0.0, 0.88, (0.045, 0.043, 0.040), 0.0, 0.80, 0.30, 0.35),
    'sleeve': ((0.016, 0.022, 0.027), 0.0, 0.92, (0.030, 0.038, 0.044), 0.0, 0.86, 0.30, 0.0),
    'strap': ((0.20, 0.15, 0.06), 0.0, 0.72, (0.26, 0.20, 0.09), 0.0, 0.66, 0.35, 0.0),
}
# Grip and stock get a stippled texture that reads at first-person distance.
STIPPLED = {'grip', 'stock_body', 'hand_stop'}


def node(tree, kind, **inputs):
    n = tree.nodes.new(kind)
    for key, value in inputs.items():
        if key in n.inputs:
            n.inputs[key].default_value = value
        else:
            setattr(n, key, value)
    return n


def build_surface(mat_name, stippled):
    base, metal, rough, edge_col, edge_metal, edge_rough, micro, stip = SURFACES[mat_name]
    if stippled:
        stip = 1.0
    mat = bpy.data.materials.new(f'{mat_name}{"_stippled" if stippled else ""}_bake')
    mat.use_nodes = True
    t = mat.node_tree
    t.nodes.clear()
    out_node = node(t, 'ShaderNodeOutputMaterial')
    bsdf = node(t, 'ShaderNodeBsdfPrincipled')
    coords = node(t, 'ShaderNodeTexCoord')
    geo = node(t, 'ShaderNodeNewGeometry')
    # Edge mask: rounded (bevel) normal versus true normal.
    bevel = node(t, 'ShaderNodeBevel', samples=8)
    bevel.inputs['Radius'].default_value = 0.0012
    dot = node(t, 'ShaderNodeVectorMath', operation='DOT_PRODUCT')
    t.links.new(bevel.outputs['Normal'], dot.inputs[0])
    t.links.new(geo.outputs['Normal'], dot.inputs[1])
    edge_ramp = node(t, 'ShaderNodeMapRange', clamp=True)
    edge_ramp.inputs['From Min'].default_value = 0.985
    edge_ramp.inputs['From Max'].default_value = 0.90
    t.links.new(dot.outputs['Value'], edge_ramp.inputs['Value'])
    # Break the wear up so edges chip rather than outline.
    chip = node(t, 'ShaderNodeTexNoise', noise_dimensions='3D')
    chip.inputs['Scale'].default_value = 180.0
    chip.inputs['Detail'].default_value = 6.0
    chip.inputs['Roughness'].default_value = 0.65
    t.links.new(coords.outputs['Object'], chip.inputs['Vector'])
    chip_ramp = node(t, 'ShaderNodeMapRange', clamp=True)
    chip_ramp.inputs['From Min'].default_value = 0.42
    chip_ramp.inputs['From Max'].default_value = 0.62
    t.links.new(chip.outputs['Fac'], chip_ramp.inputs['Value'])
    wear = node(t, 'ShaderNodeMath', operation='MULTIPLY', use_clamp=True)
    t.links.new(edge_ramp.outputs['Result'], wear.inputs[0])
    t.links.new(chip_ramp.outputs['Result'], wear.inputs[1])
    # Cavity: short-range occlusion collects grime in recesses.
    ao = node(t, 'ShaderNodeAmbientOcclusion', samples=8, only_local=True)
    ao.inputs['Distance'].default_value = 0.006
    # Broad tonal variation and fine roughness grain.
    broad = node(t, 'ShaderNodeTexNoise')
    broad.inputs['Scale'].default_value = 14.0
    broad.inputs['Detail'].default_value = 3.0
    t.links.new(coords.outputs['Object'], broad.inputs['Vector'])
    grain = node(t, 'ShaderNodeTexNoise')
    grain.inputs['Scale'].default_value = 900.0
    grain.inputs['Detail'].default_value = 2.0
    t.links.new(coords.outputs['Object'], grain.inputs['Vector'])
    # Directional handling scratches: noise stretched along the barrel axis.
    stretch = node(t, 'ShaderNodeMapping')
    stretch.inputs['Scale'].default_value = (60.0, 2.0, 60.0)
    t.links.new(coords.outputs['Object'], stretch.inputs['Vector'])
    scratch = node(t, 'ShaderNodeTexNoise')
    scratch.inputs['Scale'].default_value = 40.0
    scratch.inputs['Detail'].default_value = 8.0
    t.links.new(stretch.outputs['Vector'], scratch.inputs['Vector'])
    scratch_ramp = node(t, 'ShaderNodeMapRange', clamp=True)
    scratch_ramp.inputs['From Min'].default_value = 0.66
    scratch_ramp.inputs['From Max'].default_value = 0.72
    t.links.new(scratch.outputs['Fac'], scratch_ramp.inputs['Value'])

    # Base colour = base * tonal variation, grime in cavities, worn edges.
    tone = node(t, 'ShaderNodeMapRange', clamp=True)
    tone.inputs['To Min'].default_value = 0.88
    tone.inputs['To Max'].default_value = 1.10
    t.links.new(broad.outputs['Fac'], tone.inputs['Value'])
    base_rgb = node(t, 'ShaderNodeMix', data_type='RGBA', blend_type='MULTIPLY')
    base_rgb.inputs['Factor'].default_value = 1.0
    base_rgb.inputs['A'].default_value = (*base, 1)
    t.links.new(tone.outputs['Result'], base_rgb.inputs['B'])
    grime = node(t, 'ShaderNodeMix', data_type='RGBA', blend_type='MULTIPLY')
    grime_amount = node(t, 'ShaderNodeMath', operation='SUBTRACT', use_clamp=True)
    grime_amount.inputs[0].default_value = 1.0
    t.links.new(ao.outputs['AO'], grime_amount.inputs[1])
    t.links.new(grime_amount.outputs['Value'], grime.inputs['Factor'])
    t.links.new(base_rgb.outputs['Result'], grime.inputs['A'])
    grime.inputs['B'].default_value = (0.55, 0.52, 0.48, 1)
    worn = node(t, 'ShaderNodeMix', data_type='RGBA')
    t.links.new(wear.outputs['Value'], worn.inputs['Factor'])
    t.links.new(grime.outputs['Result'], worn.inputs['A'])
    worn.inputs['B'].default_value = (*edge_col, 1)
    t.links.new(worn.outputs['Result'], bsdf.inputs['Base Color'])

    # Roughness = base + grain, smoother scratches and worn edges, rougher grime.
    rough_grain = node(t, 'ShaderNodeMapRange', clamp=True)
    rough_grain.inputs['To Min'].default_value = rough - 0.05
    rough_grain.inputs['To Max'].default_value = rough + 0.05
    t.links.new(grain.outputs['Fac'], rough_grain.inputs['Value'])
    rough_scratch = node(t, 'ShaderNodeMix', data_type='FLOAT')
    rough_scratch.inputs['B'].default_value = max(0.05, rough - 0.12)
    scratch_scaled = node(t, 'ShaderNodeMath', operation='MULTIPLY', use_clamp=True)
    scratch_scaled.inputs[1].default_value = 0.0 if mat_name in ('glass', 'rubber') else 0.7
    t.links.new(scratch_ramp.outputs['Result'], scratch_scaled.inputs[0])
    t.links.new(scratch_scaled.outputs['Value'], rough_scratch.inputs['Factor'])
    t.links.new(rough_grain.outputs['Result'], rough_scratch.inputs['A'])
    rough_edge = node(t, 'ShaderNodeMix', data_type='FLOAT')
    rough_edge.inputs['B'].default_value = edge_rough
    t.links.new(wear.outputs['Value'], rough_edge.inputs['Factor'])
    t.links.new(rough_scratch.outputs['Result'], rough_edge.inputs['A'])
    t.links.new(rough_edge.outputs['Result'], bsdf.inputs['Roughness'])

    metal_mix = node(t, 'ShaderNodeMix', data_type='FLOAT')
    metal_mix.inputs['A'].default_value = metal
    metal_mix.inputs['B'].default_value = edge_metal
    t.links.new(wear.outputs['Value'], metal_mix.inputs['Factor'])
    t.links.new(metal_mix.outputs['Result'], bsdf.inputs['Metallic'])

    # Height: fine grain plus optional stipple (Voronoi pits).
    height = node(t, 'ShaderNodeMath', operation='MULTIPLY')
    height.inputs[1].default_value = micro
    t.links.new(grain.outputs['Fac'], height.inputs[0])
    if stip > 0:
        vor = node(t, 'ShaderNodeTexVoronoi', feature='F1')
        vor.inputs['Scale'].default_value = 600.0
        t.links.new(coords.outputs['Object'], vor.inputs['Vector'])
        pits = node(t, 'ShaderNodeMath', operation='MULTIPLY_ADD')
        t.links.new(vor.outputs['Distance'], pits.inputs[0])
        pits.inputs[1].default_value = stip
        t.links.new(height.outputs['Value'], pits.inputs[2])
        height = pits
    bump = node(t, 'ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.6 if stip > 0 else 0.35
    bump.inputs['Distance'].default_value = 0.0006 if stip > 0 else 0.0002
    t.links.new(height.outputs[0], bump.inputs['Height'])
    t.links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    t.links.new(bsdf.outputs['BSDF'], out_node.inputs['Surface'])
    # Emission branch used to bake metallic (no direct metallic bake pass).
    emit = node(t, 'ShaderNodeEmission')
    t.links.new(metal_mix.outputs['Result'], emit.inputs['Color'])
    mat['bsdf'] = bsdf.name
    mat['emit'] = emit.name
    return mat


bake_mats = {}
for o in meshes:
    for slot in o.material_slots:
        source = slot.material.name.split('.')[0]
        stippled = o.name in STIPPLED and source in ('polymer', 'rubber')
        key = (source, stippled)
        if key not in bake_mats:
            bake_mats[key] = build_surface(source, stippled)
        slot.material = bake_mats[key]

# ------------------------------------------------------------------ bake passes
images = {}


def target(label, colour_space):
    img = bpy.data.images.new(f'{name}_{label}', size, size, alpha=False)
    img.colorspace_settings.name = colour_space
    for mat in bake_mats.values():
        tree = mat.node_tree
        tex = tree.nodes.get('bake_target') or tree.nodes.new('ShaderNodeTexImage')
        tex.name = 'bake_target'
        tex.image = img
        tree.nodes.active = tex
    images[label] = img
    return img


def surface_output(kind):
    for mat in bake_mats.values():
        tree = mat.node_tree
        out_node = next(n for n in tree.nodes if n.bl_idname == 'ShaderNodeOutputMaterial')
        source = tree.nodes[mat['emit'] if kind == 'emit' else mat['bsdf']]
        tree.links.new(source.outputs[0], out_node.inputs['Surface'])


bpy.ops.object.select_all(action='DESELECT')
for o in meshes:
    o.select_set(True)
bpy.context.view_layer.objects.active = meshes[0]
margin = max(4, size // 256)


def bake(kind, label, colour_space, sample_count, **kw):
    scene.cycles.samples = sample_count
    img = target(label, colour_space)
    bpy.ops.object.bake(type=kind, margin=margin, use_clear=True, target='IMAGE_TEXTURES', **kw)
    img.filepath_raw = str(out / f'{name}_{label}_raw.png')
    img.file_format = 'PNG'
    img.save()
    print('BAKED', label)


surface_output('bsdf')
bake('DIFFUSE', 'albedo', 'sRGB', 1, pass_filter={'COLOR'})
bake('ROUGHNESS', 'roughness', 'Non-Color', 1)
bake('NORMAL', 'normal', 'Non-Color', 4, normal_space='TANGENT')
bake('AO', 'occlusion', 'Non-Color', samples)
surface_output('emit')
bake('EMIT', 'metallic', 'Non-Color', 1)
surface_output('bsdf')

# The editable source keeps every part separate with its procedural materials;
# export.py regroups it into game meshes without touching the UVs baked above.
bpy.ops.wm.save_as_mainfile(filepath=str(out / f'{name}.blend'), compress=True)
print('SAVED', out / f'{name}.blend')
