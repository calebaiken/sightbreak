"""Cycles review renders of the shipped rifle and rigged arms with their baked textures.

python render_arms.py <out_dir> [--samples 32] [--size 960x540]

Imports game/assets/weapons/relay_ar/relay_ar.glb and relay_ar_arms.glb as shipped,
binds the shipped 1024 texture sets (albedo, ORM, normal) and renders the hold from
several sides, the in-game eye at the viewmodel's 54 degree field of view, and two
frames of the reload clip with the magazine moved along the same curve the game uses.
Offline path tracing with a studio rig: it shows forms and textures, not game lighting.
"""
import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
from mathutils import Euler, Matrix, Vector  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, '../../game/assets/weapons/relay_ar')
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
OUT = os.path.abspath(argv[0])
SAMPLES = int(argv[argv.index('--samples') + 1]) if '--samples' in argv else 32
W, H = (int(v) for v in (argv[argv.index('--size') + 1] if '--size' in argv else '960x540').split('x'))
os.makedirs(OUT, exist_ok=True)


def textured(name, prefix):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    bsdf = nodes['Principled BSDF']

    def image(label, colour):
        node = nodes.new('ShaderNodeTexImage')
        node.image = bpy.data.images.load(os.path.join(ASSETS, f'{prefix}_{label}.png'))
        node.image.colorspace_settings.name = colour
        return node
    albedo, orm, normal = image('albedo', 'sRGB'), image('orm', 'Non-Color'), image('normal', 'Non-Color')
    split = nodes.new('ShaderNodeSeparateColor')
    links.new(orm.outputs['Color'], split.inputs['Color'])
    shade = nodes.new('ShaderNodeMix')
    shade.data_type = 'RGBA'
    shade.blend_type = 'MULTIPLY'
    shade.inputs['Factor'].default_value = 1.0
    links.new(albedo.outputs['Color'], shade.inputs['A'])
    links.new(split.outputs['Red'], shade.inputs['B'])
    links.new(shade.outputs['Result'], bsdf.inputs['Base Color'])
    links.new(split.outputs['Green'], bsdf.inputs['Roughness'])
    links.new(split.outputs['Blue'], bsdf.inputs['Metallic'])
    nmap = nodes.new('ShaderNodeNormalMap')
    links.new(normal.outputs['Color'], nmap.inputs['Color'])
    links.new(nmap.outputs['Normal'], bsdf.inputs['Normal'])
    return mat


bpy.ops.wm.read_factory_settings(use_empty=True)
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=os.path.join(ASSETS, 'relay_ar.glb'))
rifle = [o for o in bpy.data.objects if o not in before and o.type == 'MESH']
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=os.path.join(ASSETS, 'relay_ar_arms.glb'))
arms = [o for o in bpy.data.objects if o not in before]
rifle_mat, arms_mat = textured('rifle', 'relay_ar'), textured('arms', 'relay_ar_arms')
for o in rifle:
    o.data.materials.clear()
    o.data.materials.append(rifle_mat)
    o.hide_render = o.name == 'stock'
rig = next(o for o in arms if o.type == 'ARMATURE')
for o in arms:
    if o.type == 'MESH':
        o.data.materials.clear()
        o.data.materials.append(arms_mat)
magazine = next(o for o in rifle if o.name == 'magazine')
mag_rest = magazine.location.copy()

scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = SAMPLES
scene.render.resolution_x, scene.render.resolution_y = W, H
scene.render.fps = 30
world = bpy.data.worlds.new('studio')
scene.world = world
world.use_nodes = True
world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.20, 0.22, 0.25, 1)
world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.35
# Standard view transform, so baked albedos read at their true value (AgX lifts them).
scene.view_settings.view_transform = 'Standard'
scene.view_settings.exposure = -1.6


def light(name, loc, energy, size, target=(0, 0.2, 0)):
    data = bpy.data.lights.new(name, 'AREA')
    data.energy, data.size = energy, size
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    obj.location = loc
    obj.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()


light('key', (0.6, -0.2, 0.7), 70, 0.8)
light('fill', (-0.7, 0.3, 0.2), 22, 0.8)
light('rim', (0.0, 0.9, 0.4), 40, 0.5)
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
scene.collection.objects.link(cam)
scene.camera = cam
cam.data.clip_start = 0.005


def clip_frame(p):
    scene.frame_set(round(p * 30))
    drop = 0.23 * math.sin(min(1.0, max(0.0, (p - 0.12) / 0.72)) * math.pi)
    magazine.location = mag_rest + Vector((0, 0, -drop))


def shot(name, loc, target, lens=50):
    cam.data.sensor_fit, cam.data.lens = 'AUTO', lens
    cam.location = loc
    cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = os.path.join(OUT, name + '.png')
    bpy.ops.render.render(write_still=True)
    print('RENDER', scene.render.filepath)


def eye(name):
    """The in-game camera at the viewmodel projection, from weapon_model.gd's placement."""
    source = open(os.path.join(HERE, '../../game/scripts/gameplay/weapon_model.gd')).read()
    vector = lambda n: Vector(float(v) for v in re.search(r'static var %s := Vector3\(([^)]*)\)' % n, source).group(1).split(','))
    fov = float(re.search(r'const FOV := ([0-9.]+)', open(os.path.join(HERE, '../../game/scripts/gameplay/viewmodel_shading.gd')).read()).group(1))
    rot = Euler(vector('relay_ar_rotation'), 'ZXY').to_matrix()
    g2b = lambda g: Vector((g.x, -g.z, g.y))
    eye_at = g2b(rot.inverted() @ (Vector((0, 0, 0)) - Vector((0.235, -0.235, -0.42)) - vector('relay_ar_offset')))
    forward, up = g2b(rot.inverted() @ Vector((0, 0, -1))), g2b(rot.inverted() @ Vector((0, 1, 0)))
    cam.data.sensor_fit = 'VERTICAL'
    cam.data.angle = math.radians(fov)
    cam.matrix_world = Matrix((forward.cross(up), up, -forward)).transposed().to_4x4()
    cam.location = eye_at
    scene.render.filepath = os.path.join(OUT, name + '.png')
    bpy.ops.render.render(write_still=True)
    print('RENDER', scene.render.filepath)


clip_frame(0.0)
eye('eye_54')
shot('right_34', (0.42, -0.22, 0.16), (0.01, 0.12, -0.03))
shot('left_34', (-0.48, 0.10, 0.10), (0.0, 0.26, -0.02))
shot('firing_hand', (0.20, -0.02, -0.03), (0.01, 0.0, -0.05), 60)
shot('firing_hand_left', (-0.20, 0.03, -0.03), (0.0, 0.01, -0.05), 60)
shot('support_hand', (-0.14, 0.62, -0.12), (0.0, 0.43, 0.0), 50)
shot('support_hand_right', (0.17, 0.46, 0.05), (0.0, 0.43, 0.015), 50)
clip_frame(0.14)
shot('reload_grab', (-0.36, 0.0, -0.06), (0.0, 0.14, -0.08))
clip_frame(0.45)
shot('reload_down', (-0.40, -0.05, -0.16), (0.0, 0.12, -0.22))
