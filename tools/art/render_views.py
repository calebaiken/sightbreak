"""Cycles turntable-style review renders of a generator module.

python render_views.py <module.py> <out_dir> [view ...] [--samples N] [--res WxH]
Views frame themselves from object bounds, so geometry changes never crop a shot.
"""
import importlib.util
import math
import pathlib
import sys
import bpy
from mathutils import Vector

args = sys.argv[1:]
samples, res = 48, (1600, 900)
if '--samples' in args:
    i = args.index('--samples'); samples = int(args[i + 1]); del args[i:i + 2]
if '--res' in args:
    i = args.index('--res'); res = tuple(int(v) for v in args[i + 1].split('x')); del args[i:i + 2]
module_path, out_dir, wanted = args[0], pathlib.Path(args[1]), args[2:]
out_dir.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(pathlib.Path(module_path).parent))
spec = importlib.util.spec_from_file_location('gen', module_path)
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)
gen.build()


def bounds(names=None):
    lo, hi = Vector((1e9,) * 3), Vector((-1e9,) * 3)
    for o in bpy.data.objects:
        if o.type != 'MESH' or o.name == 'floor' or (names and not any(o.name.startswith(n) for n in names)):
            continue
        for c in o.bound_box:
            p = o.matrix_world @ Vector(c)
            lo = Vector(map(min, lo, p)); hi = Vector(map(max, hi, p))
    return lo, hi


# (direction from target to camera, parts to frame or None for all, fov deg, fill, ortho)
VIEWS = {
    'left_34': (Vector((-0.78, 0.42, 0.32)), None, 28, 0.92, False),
    'right_34': (Vector((0.78, 0.42, 0.30)), None, 28, 0.92, False),
    'side_profile': (Vector((1, 0, 0)), None, 0, 0.94, True),
    'top_perspective': (Vector((0.35, -0.55, 0.95)), None, 30, 0.92, False),
    # Added for the sidearm, SMG and marksman review loop: the angles a player sees (behind the weapon, down the
    # sights) and the ones a silhouette check needs (front, underside).
    'rear_34': (Vector((0.55, -0.80, 0.38)), None, 28, 0.92, False),
    'front_34': (Vector((0.55, 0.85, 0.25)), None, 28, 0.92, False),
    'under_34': (Vector((0.50, 0.25, -0.70)), None, 28, 0.92, False),
    'sight_picture': (Vector((0.0, -1.0, 0.16)), None, 22, 0.80, False),
    'receiver_closeup': (Vector((0.80, 0.25, 0.32)), ['paint_upper', 'paint_lower', 'bolt', 'dust', 'deflector', 'charging'], 24, 0.95, False),
    'grip_magazine_closeup': (Vector((0.75, 0.35, 0.18)), ['grip', 'magazine', 'trigger', 'mag_release', 'release_fence'], 26, 0.92, False),
    'materials_closeup': (Vector((0.70, 0.45, 0.40)), ['barrel_nut', 'screw', 'pin1'], 18, 0.55, False),
    'support_hand': (Vector((-0.85, -0.25, 0.35)), ['glove_left'], 30, 0.9, False),
    # The Kestrel 9 with both hands, from where the player's eye is (behind, a little left and above) and from the left.
    'k9_player_eye': (Vector((-0.35, -0.90, 0.40)), ['paint_slide', 'grip', 'magazine', 'glove_right', 'glove_left'], 24, 0.85, False),
    'k9_left': (Vector((-0.95, -0.10, 0.18)), ['paint_slide', 'grip', 'magazine', 'glove_right', 'glove_left'], 24, 0.85, False),
    'k9_right': (Vector((0.95, -0.15, 0.18)), ['paint_slide', 'grip', 'magazine', 'glove_right', 'glove_left'], 24, 0.85, False),
    'firing_hand': (Vector((-0.80, 0.30, 0.10)), ['glove_right'], 30, 0.9, False),
}

NO_FLOOR = ('under_34',)

scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = samples
scene.cycles.use_denoising = True
scene.render.resolution_x, scene.render.resolution_y = res
scene.render.film_transparent = False
scene.view_settings.look = 'AgX - Medium High Contrast' if 'AgX - Medium High Contrast' in [
    i.name for i in scene.view_settings.bl_rna.properties['look'].enum_items] else 'None'

world = bpy.data.worlds.new('studio')
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes['Background']
bg.inputs['Color'].default_value = (0.20, 0.22, 0.25, 1)
bg.inputs['Strength'].default_value = 0.35

lo, hi = bounds()
centre, size = (lo + hi) / 2, (hi - lo)
span = max(size)

floor_mat = bpy.data.materials.new('floor')
floor_mat.use_nodes = True
fb = floor_mat.node_tree.nodes['Principled BSDF']
fb.inputs['Base Color'].default_value = (0.11, 0.115, 0.12, 1)
fb.inputs['Roughness'].default_value = 0.7
bpy.ops.mesh.primitive_plane_add(size=span * 30, location=(centre.x, centre.y, lo.z - 0.004))
floor = bpy.context.active_object
floor.name = 'floor'
floor.data.materials.append(floor_mat)


def area(name, energy, size_m, colour, direction):
    light = bpy.data.lights.new(name, 'AREA')
    light.energy, light.size, light.color = energy, size_m, colour
    obj = bpy.data.objects.new(name, light)
    bpy.context.collection.objects.link(obj)
    obj.location = centre + direction.normalized() * span * 1.6
    obj.rotation_euler = (centre - obj.location).to_track_quat('-Z', 'Y').to_euler()
    return obj


# Key upper-front-right, cool fill left, warm rim behind: reads form and edge wear.
area('key', 30, span * 0.6, (1.0, 0.97, 0.92), Vector((0.9, 0.6, 1.1)))
area('fill', 9, span * 1.0, (0.85, 0.92, 1.0), Vector((-1.0, 0.2, 0.4)))
area('rim', 24, span * 0.4, (1.0, 0.93, 0.85), Vector((-0.2, -1.0, 0.8)))
area('top', 6, span * 1.2, (1.0, 1.0, 1.0), Vector((0.0, 0.0, 1.0)))

camera = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
bpy.context.collection.objects.link(camera)
scene.camera = camera
camera.data.clip_start = 0.002
aspect = res[0] / res[1]
# In-game first-person camera, expressed in model space: Godot's viewmodel node
# (0.235, -0.235, -0.42) and weapon_model.gd's placement (rotation YXZ, offset),
# 82 degree vertical field of view.
if 'eye' in wanted:
    import re
    from mathutils import Euler, Matrix
    # Placement constants come straight from the game so this view cannot drift from it.
    source = (pathlib.Path(__file__).resolve().parents[2] / 'game/scripts/gameplay/weapon_model.gd').read_text()
    vector = lambda name: Vector(float(v) for v in re.search(r'static var %s := Vector3\(([^)]*)\)' % name, source).group(1).split(','))
    scale = float(re.search(r'static var relay_ar_scale := ([0-9.]+)', source).group(1))
    # Godot's Basis.from_euler default (YXZ) is R = Ry * Rx * Rz, which is Blender's 'ZXY'.
    rot = Euler(vector('relay_ar_rotation'), 'ZXY').to_matrix()
    offset = vector('relay_ar_offset')
    to_godot_model = lambda cam: (rot.inverted() @ (Vector(cam) - Vector((0.235, -0.235, -0.42)) - offset)) / scale
    g2b = lambda g: Vector((g.x, -g.z, g.y))
    eye = g2b(to_godot_model((0, 0, 0)))
    forward = g2b(rot.inverted() @ Vector((0, 0, -1)))
    up = g2b(rot.inverted() @ Vector((0, 1, 0)))
    camera.data.type = 'PERSP'
    camera.data.sensor_fit = 'VERTICAL'
    camera.data.angle = math.radians(82)
    camera.location = eye
    right = forward.cross(up)
    camera.matrix_world = Matrix((right, up, -forward)).transposed().to_4x4()
    camera.location = eye
    # Level ground 1.55 m below the eye in camera space, as in the game.
    ground = bpy.data.objects['floor']
    ground.rotation_euler = up.to_track_quat('Z', 'Y').to_euler()
    ground.location = eye - up * 1.55
    scene.render.filepath = str(out_dir / 'eye.png')
    bpy.ops.render.render(write_still=True)
    print('VIEW eye', scene.render.filepath)
    camera.data.sensor_fit = 'AUTO'
for name, (direction, parts, fov, fill, ortho) in VIEWS.items():
    if wanted and name not in wanted:
        continue
    plo, phi = bounds(parts)
    target, radius = (plo + phi) / 2, (phi - plo).length / 2
    d = direction.normalized()
    if ortho:
        camera.data.type = 'ORTHO'
        camera.data.ortho_scale = max((phi - plo).y, (phi - plo).z * aspect) / fill
        camera.location = target + d * span * 2
    else:
        camera.data.type = 'PERSP'
        camera.data.angle = math.radians(fov)
        # Distance at which every bounds corner projects inside `fill` of the frame.
        rot = (-d).to_track_quat('-Z', 'Y').to_matrix()
        right, up = rot.col[0], rot.col[1]
        tx = math.tan(math.radians(fov) / 2) * fill
        ty = tx / aspect
        corners = [Vector((x, y, z)) for x in (plo.x, phi.x) for y in (plo.y, phi.y) for z in (plo.z, phi.z)]
        distance = max(max(abs((c - target).dot(right)) / tx, abs((c - target).dot(up)) / ty)
                       + (c - target).dot(d) for c in corners)
        camera.location = target + d * distance
    camera.rotation_euler = (target - camera.location).to_track_quat('-Z', 'Y').to_euler()
    # Views from below would look through the floor at nothing: hide it for those.
    floor.hide_render = name in NO_FLOOR
    scene.render.filepath = str(out_dir / f'{name}.png')
    bpy.ops.render.render(write_still=True)
    floor.hide_render = False
    print('VIEW', name, scene.render.filepath)
