"""Builds the rigged first-person arms (relay_ar_arms.glb) from relay_ar_arms.py.

Stages, all headless Blender (bpy module):
1. Mesh the right arm's glove and sleeve as high-poly surfaces (bake sources) and a
   medium surface without seams that QuadriFlow retopologises into the game mesh.
2. Bones from the same landmarks; automatic (bone heat) weights on the right arm.
3. The left arm is the right arm mirrored, with mirrored weights.
4. Both arms are placed on the rifle (Blender rifle space: barrel +Y, Z up) and the
   fingers close on the grip, trigger and handguard: each joint flexes until its
   phalanx would touch the rifle's surface (a BVH of the rifle's own meshes).
5. The posed arms become the bind pose; the reload clip moves the support hand from
   the handguard to the magazine, follows the magazine down the well and back, slaps
   it home and returns.

python arms_build.py <out_dir> [--preview] [--h-high 0.0005] [--rifle relay_ar.glb]
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
import bmesh  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Matrix, Quaternion, Vector  # noqa: E402
from mathutils.bvhtree import BVHTree  # noqa: E402
import relay_ar_arms as arms  # noqa: E402
import sdf  # noqa: E402

GRIP_AXIS = Vector((0, 0.27, 0.96)).normalized()        # pistol grip, bottom to top
GRIP_NORMAL = Vector((0, 0.96, -0.27)).normalized()     # toward the muzzle


# ------------------------------------------------------------------ meshes

def mesh_object(name, verts, faces, materials=(), regions=None):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(map(float, v)) for v in verts], [], [tuple(map(int, f)) for f in faces])
    me.update()
    obj = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(obj)
    for m in materials:
        me.materials.append(m)
    if regions is not None:
        names = [m.name for m in materials]
        me.polygons.foreach_set('material_index', [names.index(r) for r in regions])
    for p in me.polygons:
        p.use_smooth = True
    return obj


def select(*objs, active=None):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = active or objs[0]


def retopo(obj, faces):
    """Voxel-remesh, decimate to about 12k triangles, then QuadriFlow to about `faces`
    quads. QuadriFlow in Blender 5.2 refuses inputs much above 20k triangles with a
    misleading "not manifold" message, hence the decimation."""
    select(obj)
    mod = obj.modifiers.new('relax', 'SMOOTH')
    mod.factor, mod.iterations = 0.5, 3
    bpy.ops.object.modifier_apply(modifier=mod.name)
    mod = obj.modifiers.new('clean', 'REMESH')
    mod.mode, mod.voxel_size = 'VOXEL', 0.0015
    bpy.ops.object.modifier_apply(modifier=mod.name)
    source = obj.data.copy()
    for budget, seed in ((12000, 7), (9000, 7), (12000, 3), (15000, 11)):
        obj.data = source.copy()
        tris = sum(len(p.vertices) - 2 for p in obj.data.polygons)
        mod = obj.modifiers.new('thin', 'DECIMATE')
        mod.ratio = min(1.0, budget / tris)
        bpy.ops.object.modifier_apply(modifier=mod.name)
        if bpy.ops.object.quadriflow_remesh(target_faces=faces, use_preserve_sharp=False, use_mesh_symmetry=False, seed=seed) == {'FINISHED'}:
            break
    else:
        raise RuntimeError('QuadriFlow failed on ' + obj.name)
    for p in obj.data.polygons:
        p.use_smooth = True
    return obj


def material(name, colour, rough):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes['Principled BSDF']
    bsdf.inputs['Base Color'].default_value = (*colour, 1)
    bsdf.inputs['Roughness'].default_value = rough
    return m


# Linear base colour and roughness. A dark brown-grey glove with black moulded parts
# and a lighter suede palm reads as a glove (a lighter coyote read as bare skin at game
# distance); the olive jacket separates from both and from the graphite rifle.
PALETTE = {
    'fabric': ((0.050, 0.044, 0.034), 0.86), 'palm': ((0.078, 0.066, 0.050), 0.93),
    'shell': ((0.017, 0.017, 0.018), 0.48), 'strap': ((0.026, 0.024, 0.021), 0.80),
    'cuff': ((0.044, 0.039, 0.030), 0.88),
    'sleeve': ((0.056, 0.064, 0.040), 0.90), 'hem': ((0.044, 0.050, 0.032), 0.88),
}


def right_arm_meshes(h_high, h_mid, glove_faces, sleeve_faces, high=True):
    """High-poly glove and sleeve (bake sources) and the low-poly arm, hand-local."""
    mats = {k: material(k, *v) for k, v in PALETTE.items()}
    shapes = arms.glove_shapes()
    parts = {}
    if high:
        v, q = sdf.mesh(lambda P: arms.glove_distance(P, shapes), *arms.glove_bounds(), h_high)
        centres = (v[q[:, 0]] + v[q[:, 2]]) / 2
        reg = sdf.nearest_region(centres, [s for s, k in shapes[0]], 'fabric')
        reg = np.where(reg == None, 'fabric', reg)  # noqa: E711
        glove_regions = ('fabric', 'palm', 'shell', 'strap', 'cuff')
        parts['glove_high'] = mesh_object('glove_high', v, q, [mats[r] for r in glove_regions], reg)
        v, q = sdf.mesh(arms.sleeve_distance, *arms.sleeve_bounds(), h_high * 1.4)
        centres = (v[q[:, 0]] + v[q[:, 2]]) / 2
        parts['sleeve_high'] = mesh_object('sleeve_high', v, q, [mats['sleeve'], mats['hem']], arms.sleeve_region(centres))
    plain = (shapes[0], [])
    v, q = sdf.mesh(lambda P: arms.glove_distance(P, plain), *arms.glove_bounds(), h_mid)
    glove = retopo(mesh_object('glove_low', v, q), glove_faces)
    v, f = arms.sleeve_low_mesh()
    sleeve = mesh_object('sleeve_low', v, f)
    select(sleeve)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    glove.data.materials.append(mats['fabric'])
    sleeve.data.materials.append(mats['sleeve'])
    select(glove, sleeve)
    bpy.ops.object.join()
    glove.name = 'arm_low'
    parts['arm_low'] = glove
    return parts


# ------------------------------------------------------------------ bones

def right_bones():
    """(name, head, tail, parent, z-axis hint) in the right hand's local frame."""
    j = arms.skeleton()
    bones = [('forearm', j['elbow'], j['wrist'], None, arms.Z),
             ('hand', j['wrist'], np.asarray(arms.MCP['middle']), 'forearm', arms.Z)]
    for name in arms.FINGERS:
        joints, ups = arms.finger_chain(name)
        for i in range(3):
            bones.append((f'{name}_{i + 1}', joints[i], joints[i + 1], 'hand' if i == 0 else f'{name}_{i}', ups[i]))
    joints, ups = arms.thumb_chain()
    for i in range(3):
        bones.append((f'thumb_{i + 1}', joints[i], joints[i + 1], 'hand' if i == 0 else f'thumb_{i}', ups[i]))
    return bones


MIRROR = Matrix.Diagonal((-1, 1, 1, 1))


def make_armature(placements):
    """One armature for both arms. `placements` maps a side prefix to a 4x4 matrix from
    that arm's hand-local frame to rifle space (the left one includes the mirror)."""
    data = bpy.data.armatures.new('arms')
    rig = bpy.data.objects.new('arms', data)
    bpy.context.scene.collection.objects.link(rig)
    select(rig)
    bpy.ops.object.mode_set(mode='EDIT')
    for side, M in placements.items():
        for name, head, tail, parent, up in right_bones():
            b = data.edit_bones.new(f'{side}_{name}')
            b.head = M @ Vector(head)
            b.tail = M @ Vector(tail)
            b.align_roll(M.to_3x3() @ Vector(up))
            if parent:
                b.parent = data.edit_bones[f'{side}_{parent}']
                b.use_connect = False
    bpy.ops.object.mode_set(mode='OBJECT')
    return rig


def auto_weights(mesh_obj):
    """Bone-heat weights for the right arm in its local frame."""
    rig = make_armature({'R': Matrix.Identity(4)})
    select(mesh_obj, rig, active=rig)
    bpy.ops.object.parent_set(type='ARMATURE_AUTO')
    mesh_obj.parent = None
    for mod in list(mesh_obj.modifiers):
        mesh_obj.modifiers.remove(mod)
    bpy.data.objects.remove(rig, do_unlink=True)
    missing = [v.index for v in mesh_obj.data.vertices if not v.groups]
    return missing


def place_arm(src, side, M):
    """Copy of `src` transformed by M (mirrored if det < 0), groups renamed to `side`."""
    obj = src.copy()
    obj.data = src.data.copy()
    obj.name = f'arm_{side}'
    bpy.context.scene.collection.objects.link(obj)
    obj.data.transform(M)
    if M.determinant() < 0:
        obj.data.flip_normals()
    for g in obj.vertex_groups:
        g.name = f'{side}_{g.name.split("_", 1)[1]}' if g.name.startswith('R_') else f'{side}_{g.name}'
    return obj


# ------------------------------------------------------------------ placement and pose

def frame(x, y, z, origin):
    M = Matrix.Identity(4)
    for i, axis in enumerate((x, y, z)):
        M.col[i][:3] = axis
    M.col[3][:3] = origin
    return M


def hand_frame(distal, dorsal, mcp_target, mirror=False, roll=0.0):
    """Matrix from the (right) hand-local frame to rifle space: local +Y along `distal`,
    +Z near `dorsal`, turned by `roll` about +Y, and the middle knuckle at `mcp_target`."""
    y = Vector(distal).normalized()
    z = Vector(dorsal) - y * y.dot(Vector(dorsal))
    z = (Quaternion(y, roll) @ z).normalized()
    x = y.cross(z)
    M = frame(x, y, z, (0, 0, 0))
    if mirror:
        M = M @ MIRROR
    knuckle = M @ Vector(arms.MCP['middle'])
    M.col[3][:3] = Vector(mcp_target) - knuckle
    return M


class Obstacle:
    """Signed distance to the rifle's surface from a BVH of its meshes (negative inside)."""

    def __init__(self, objects):
        verts, polys = [], []
        for obj in objects:
            me = obj.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh()
            base = len(verts)
            verts += [obj.matrix_world @ v.co for v in me.vertices]
            polys += [[base + i for i in p.vertices] for p in me.polygons]
        self.bvh = BVHTree.FromPolygons(verts, polys)

    def distance(self, p):
        hit = self.bvh.find_nearest(p, 0.05)
        if hit[0] is None:
            return 0.05
        loc, normal = hit[0], hit[1]
        d = (p - loc).length
        return d if (p - loc).dot(normal) >= 0 else -d


def bone_points(rig, mesh_obj, side, stride=1):
    """Rest-pose vertex positions of `mesh_obj` grouped by their dominant bone."""
    names = {g.index: g.name for g in mesh_obj.vertex_groups}
    points = {}
    for v in mesh_obj.data.vertices[::stride]:
        if not v.groups:
            continue
        g = max(v.groups, key=lambda g: g.weight)
        name = names[g.group]
        if name.startswith(side + '_') and g.weight > 0.5:
            points.setdefault(name, []).append(v.co.copy())
    return points


def deform(rig, name):
    pb = rig.pose.bones[name]
    return pb.matrix @ rig.data.bones[name].matrix_local.inverted()


def aim_forearm(rig, side, elbow):
    """Swing the forearm about the wrist so its far end sits at `elbow`; the hand keeps
    its placed orientation (the wrist absorbs the difference)."""
    fore = rig.pose.bones[f'{side}_forearm']
    hand = rig.pose.bones[f'{side}_hand']
    rest_fore = rig.data.bones[fore.name].matrix_local
    rest_hand = rig.data.bones[hand.name].matrix_local
    wrist = rest_fore @ Vector((0, rig.data.bones[fore.name].length, 0))
    new_y = (wrist - Vector(elbow)).normalized()
    turn = (rest_fore.to_3x3() @ Vector((0, 1, 0))).rotation_difference(new_y)
    M = (turn.to_matrix() @ rest_fore.to_3x3()).to_4x4()
    M.translation = wrist - new_y * rig.data.bones[fore.name].length
    fore.matrix = M
    bpy.context.view_layer.update()
    hand.matrix = rest_hand
    bpy.context.view_layer.update()


def flex(rig, name, angle, spread=0.0):
    pb = rig.pose.bones[name]
    pb.rotation_mode = 'QUATERNION'
    pb.rotation_quaternion = Quaternion((0, 0, 1), spread) @ Quaternion((1, 0, 0), -angle)


def close_chain(rig, chain, points, obstacle, limits, ratio, step=math.radians(1.5), margin=0.0008, base=None):
    """Grasp closing: all joints of `chain` flex together (in `ratio`) from `base`; when
    a phalanx would enter the rifle, it and the joints before it stop."""
    angles = list(base or [0.0] * len(chain))
    active = [True] * len(chain)
    for name, a in zip(chain, angles):
        flex(rig, name, a)
    bpy.context.view_layer.update()

    def touching(k):
        M = deform(rig, chain[k])
        return any(obstacle.distance(M @ p) < margin for p in points.get(chain[k], []))

    # A digit that starts inside the rifle opens (extends) until it is clear.
    opened = 0
    while any(touching(k) for k in range(len(chain))) and opened < 40:
        angles = [a - step * r for a, r in zip(angles, ratio)]
        for name, a in zip(chain, angles):
            flex(rig, name, a)
        bpy.context.view_layer.update()
        opened += 1
    if opened >= 40:
        return None
    for _ in range(400):
        if not any(active):
            break
        prev = list(angles)
        for i in range(len(chain)):
            if active[i]:
                angles[i] = min(limits[i], angles[i] + step * ratio[i])
                if angles[i] >= limits[i]:
                    active[i] = False
                flex(rig, chain[i], angles[i])
        bpy.context.view_layer.update()
        hit = -1
        for k in range(len(chain) - 1, -1, -1):
            if touching(k):
                hit = k
                break
        if hit >= 0:
            for i in range(hit + 1):
                if angles[i] != prev[i]:
                    angles[i] = prev[i]
                    flex(rig, chain[i], angles[i])
                active[i] = False
            bpy.context.view_layer.update()
    return angles


# ------------------------------------------------------------------ the hold

# Firing hand: metacarpals forward along the grip's right face (raked with it), back
# of the hand outward, knuckles at the grip's front-right corner so the first
# phalanges cross the front strap and the rest wrap the left face; the index knuckle
# then sits about 50 mm from the trigger face, a bent finger's reach. Support hand: handguard in the
# palm, fingers up the far (right) side, thumb along the near side.
HOLD = {
    'R': {'distal': GRIP_NORMAL, 'dorsal': (1, 0, 0), 'roll': 0.0, 'mcp': (0.029, 0.013, -0.056),
          'elbow_dir': (0.30, -0.78, -0.55), 'mirror': False, 'curl': (30, 45, 25)},
    'L': {'distal': (0.88, 0.06, 0.47), 'dorsal': (-0.45, 0.0, -0.89), 'roll': math.radians(0), 'mcp': (0.030, 0.430, 0.006),
          'elbow_dir': (-0.72, -0.50, -0.48), 'mirror': True, 'curl': (20, 30, 15)},
}
# Per finger: (MCP, PIP, DIP) flexion limits and closing ratio.
LIMITS = (math.radians(95), math.radians(105), math.radians(80))
RATIO = (1.0, 1.15, 0.85)
THUMB_LIMITS = (math.radians(35), math.radians(60), math.radians(75))


def settle(M, mesh_obj, obstacle, margin=0.0008, step=0.0005, limit=0.04):
    """Slide a placement along the back of the hand until no vertex of the hand bone
    (palm, back of the hand, heel) is inside the rifle or within `margin` of it.
    Fingers and thumb are opened and closed afterwards. Returns the matrix and the
    distance moved."""
    names = {g.index: g.name for g in mesh_obj.vertex_groups}
    glove = [v.co.copy() for v in mesh_obj.data.vertices
             if v.groups and names[max(v.groups, key=lambda g: g.weight).group] == 'R_hand']
    dorsal = (M.to_3x3() @ Vector((0, 0, 1))).normalized()
    moved = 0.0
    while moved <= limit:
        if all(obstacle.distance(M @ p) >= margin for p in glove[::2]):
            return M, moved
        M = Matrix.Translation(dorsal * step) @ M
        moved += step
    raise RuntimeError('hand did not clear the rifle within %.0f mm' % (limit * 1000))


TRIGGER_FACE = Vector((0.0, 0.0555, -0.0225))   # front face of the trigger blade, rifle space


def pad_point(rig, name):
    """The pad of a distal phalanx: 55 % along the bone, on its palm side."""
    bone = rig.data.bones[name]
    radius = 0.0085
    return bone.matrix_local @ Vector((0, bone.length * 0.55, -radius))


def reach(rig, chain, points, obstacle, target, start=None, report=print):
    """Coordinate descent on (MCP flex, MCP spread, PIP flex, DIP flex) to put the
    distal pad on `target` without the finger passing through the rifle."""
    x = list(start or [0.0, 0.0, math.radians(30), math.radians(20)])
    bounds = [(-0.6, 1.2), (-0.35, 0.35), (0.0, 1.7), (0.0, 1.2)]

    def apply(v):
        flex(rig, chain[0], v[0], v[1])
        flex(rig, chain[1], v[2])
        flex(rig, chain[2], v[3])
        bpy.context.view_layer.update()

    def cost(v):
        apply(v)
        pad = deform(rig, chain[2]) @ pad_point(rig, chain[2])
        inside = 0
        for name in chain:
            M = deform(rig, name)
            inside += sum(obstacle.distance(M @ p) < -0.0006 for p in points.get(name, [])[::2])
        return (pad - target).length + 0.004 * inside, inside

    best, _ = cost(x)
    for step in (0.14, 0.07, 0.035, 0.017):
        improved = True
        while improved:
            improved = False
            for i in range(4):
                for sign in (1, -1):
                    y = list(x)
                    y[i] = min(bounds[i][1], max(bounds[i][0], y[i] + sign * step))
                    c, _ = cost(y)
                    if c < best - 1e-6:
                        x, best, improved = y, c, True
    c, inside = cost(x)
    apply(x)
    report('trigger reach: pad %.1f mm from the trigger face, %d points inside' % ((c - 0.004 * inside) * 1000, inside), [round(math.degrees(a)) for a in x])
    return x


def import_rifle(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    return [o for o in bpy.data.objects if o not in before and o.type == 'MESH']


def pose_hold(rig, low_by_side, obstacle, hold=HOLD, report=print):
    for side, h in hold.items():
        wrist = rig.data.bones[f'{side}_hand'].head_local
        aim_forearm(rig, side, wrist + Vector(h['elbow_dir']).normalized() * arms.np.linalg.norm(arms.ELBOW))
        pts = bone_points(rig, low_by_side[side], side)
        inside = {n: sum(obstacle.distance(deform(rig, n) @ p) < 0 for p in ps) for n, ps in pts.items()}
        report(side, 'initial penetration', {n: c for n, c in inside.items() if c})
        for name in arms.FINGERS:
            chain = [f'{side}_{name}_{i}' for i in (1, 2, 3)]
            if side == 'R' and name == 'index':
                reach(rig, chain, pts, obstacle, TRIGGER_FACE, start=[math.radians(a) for a in (15, 0, 50, 30)], report=report)
                continue
            angles = close_chain(rig, chain, pts, obstacle, LIMITS, RATIO, base=[math.radians(a) for a in h['curl']])
            report(side, name, None if angles is None else [round(math.degrees(a)) for a in angles])
        chain = [f'{side}_thumb_{i}' for i in (1, 2, 3)]
        angles = close_chain(rig, chain, pts, obstacle, THUMB_LIMITS, (0.6, 1.0, 1.0))
        report(side, 'thumb', None if angles is None else [round(math.degrees(a)) for a in angles])


def build_rig(out_dir, rifle_glb, preview=False, h_high=0.0005, hold=HOLD, size=2048, samples=48):
    """Everything up to the solved hold. Without `preview` it also bakes the textures
    into `out_dir` (raw passes for textures.py)."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    parts = right_arm_meshes(h_high, 0.0011, 2300, 520, high=not preview)
    low = parts['arm_low']
    missing = auto_weights(low)
    print('weights: %d vertices without a bone' % len(missing))
    unwrap(low)
    if not preview:
        bake_arm(parts, out_dir, size, samples)
    rifle = import_rifle(rifle_glb)
    obstacle = Obstacle([o for o in rifle if o.name not in ('stock',)])
    placements = {}
    for side, h in hold.items():
        M, moved = settle(hand_frame(h['distal'], h['dorsal'], h['mcp'], h['mirror'], h['roll']), low, obstacle)
        print('placement', side, 'cleared the rifle after %.1f mm' % (moved * 1000))
        placements[side] = M
    sides = {side: place_arm(low, side, M) for side, M in placements.items()}
    rig = make_armature(placements)
    for obj in sides.values():
        mod = obj.modifiers.new('rig', 'ARMATURE')
        mod.object = rig
        obj.parent = rig
    low.hide_render = True
    select(rig)
    bpy.ops.object.mode_set(mode='POSE')
    pose_hold(rig, sides, obstacle, hold)
    bpy.ops.object.mode_set(mode='OBJECT')
    return rig, sides, rifle, parts, placements


def build(out_dir, rifle_glb, glb_path, size=2048, samples=48, h_high=0.0005):
    rig, sides, rifle, parts, placements = build_rig(out_dir, rifle_glb, False, h_high, HOLD, size, samples)
    bpy.data.objects.remove(parts['arm_low'], do_unlink=True)
    arms_obj = bind_pose(rig, sides)
    select(rig)
    bpy.ops.object.mode_set(mode='POSE')
    magazine = next(o for o in rifle if o.name == 'magazine')
    grab = grab_pose(rig, arms_obj, placements['L'], magazine)
    reload_clip(rig, grab)
    bpy.ops.object.mode_set(mode='OBJECT')
    for obj in rifle:
        bpy.data.objects.remove(obj, do_unlink=True)
    tris = sum(len(p.vertices) - 2 for p in arms_obj.data.polygons)
    print('ARMS triangles=%d bones=%d' % (tris, len(rig.data.bones)))
    export(rig, arms_obj, glb_path)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out_dir, 'relay_ar_arms.blend'), compress=True)
    return rig, arms_obj


# ------------------------------------------------------------------ UVs and bake

def unwrap(low, sleeve_scale=0.55):
    """Smart-UV atlas for the right arm (the left arm shares it, mirrored). Sleeve
    islands are shrunk so the gloves, which fill more of the screen, get about
    twice the sleeve's texel density."""
    select(low)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=0.002, area_weight=0.0, correct_aspect=True, scale_to_bounds=False)
    bpy.ops.uv.average_islands_scale()
    bpy.ops.object.mode_set(mode='OBJECT')
    sleeve_index = low.data.materials.find('sleeve')
    bm = bmesh.new()
    bm.from_mesh(low.data)
    uv = bm.loops.layers.uv.active
    for f in bm.faces:
        if f.material_index == sleeve_index:
            for loop in f.loops:
                loop[uv].uv *= sleeve_scale
    bm.to_mesh(low.data)
    bm.free()
    select(low)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.pack_islands(rotate=True, scale=True, margin=0.004)
    bpy.ops.object.mode_set(mode='OBJECT')


def _nodes(mat):
    tree = mat.node_tree
    for n in list(tree.nodes):
        tree.nodes.remove(n)
    return tree, tree.nodes, tree.links


def detail_material(name, colour, rough, kind):
    """High-poly surface for the bake: object-space colour variation, convexity wear
    (knuckles, fingertips, fold crests) and a fine fabric bump."""
    mat = bpy.data.materials[name]
    tree, nodes, links = _nodes(mat)
    out = nodes.new('ShaderNodeOutputMaterial')
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    links.new(bsdf.outputs[0], out.inputs['Surface'])
    coord = nodes.new('ShaderNodeTexCoord')
    geo = nodes.new('ShaderNodeNewGeometry')
    # Large-scale tone and grime variation.
    tone = nodes.new('ShaderNodeTexNoise')
    tone.inputs['Scale'].default_value = 40.0
    tone.inputs['Detail'].default_value = 6.0
    links.new(coord.outputs['Object'], tone.inputs['Vector'])
    # Wear: convex areas (pointiness above 0.5) lighten, concave areas darken.
    ramp = nodes.new('ShaderNodeMapRange')
    ramp.inputs['From Min'].default_value = 0.47
    ramp.inputs['From Max'].default_value = 0.60
    links.new(geo.outputs['Pointiness'], ramp.inputs['Value'])
    base = nodes.new('ShaderNodeMix')
    base.data_type = 'RGBA'
    base.inputs['A'].default_value = (*[c * 0.82 for c in colour], 1)
    base.inputs['B'].default_value = (*[c * 1.12 for c in colour], 1)
    links.new(tone.outputs['Fac'], base.inputs['Factor'])
    wear_colour = {'fabric': (0.21, 0.18, 0.13), 'palm': (0.12, 0.105, 0.085), 'shell': (0.075, 0.075, 0.072),
                   'strap': (0.07, 0.065, 0.058), 'cuff': (0.16, 0.13, 0.095), 'sleeve': (0.10, 0.11, 0.08), 'hem': (0.08, 0.09, 0.065)}[name]
    worn = nodes.new('ShaderNodeMix')
    worn.data_type = 'RGBA'
    worn.inputs['B'].default_value = (*wear_colour, 1)
    links.new(base.outputs['Result'], worn.inputs['A'])
    wear_amount = nodes.new('ShaderNodeMath')
    wear_amount.operation = 'MULTIPLY'
    wear_amount.inputs[1].default_value = 0.55
    links.new(ramp.outputs['Result'], wear_amount.inputs[0])
    links.new(wear_amount.outputs[0], worn.inputs['Factor'])
    links.new(worn.outputs['Result'], bsdf.inputs['Base Color'])
    r = nodes.new('ShaderNodeMapRange')
    r.inputs['To Min'].default_value = rough - 0.04
    r.inputs['To Max'].default_value = min(1.0, rough + 0.05)
    links.new(tone.outputs['Fac'], r.inputs['Value'])
    links.new(r.outputs['Result'], bsdf.inputs['Roughness'])
    # Fabric bump: a fine weave (ripstop grid on the jacket), none on the rubber shell.
    bump = nodes.new('ShaderNodeBump')
    bump.inputs['Distance'].default_value = 0.0004
    if kind == 'ripstop':
        grid = nodes.new('ShaderNodeTexBrick')
        grid.inputs['Scale'].default_value = 160.0
        grid.inputs['Mortar Size'].default_value = 0.08
        grid.offset = 0.0
        grid.squash = 1.0
        links.new(coord.outputs['Object'], grid.inputs['Vector'])
        bump.inputs['Strength'].default_value = 0.35
        links.new(grid.outputs['Fac'], bump.inputs['Height'])
    else:
        weave = nodes.new('ShaderNodeTexNoise')
        weave.inputs['Scale'].default_value = {'shell': 300.0}.get(name, 1400.0)
        weave.inputs['Detail'].default_value = 2.0
        links.new(coord.outputs['Object'], weave.inputs['Vector'])
        bump.inputs['Strength'].default_value = {'shell': 0.05, 'strap': 0.6, 'palm': 0.35}.get(name, 0.25)
        links.new(weave.outputs['Fac'], bump.inputs['Height'])
    links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    return mat


def bake_arm(parts, out_dir, size=2048, samples=48):
    """Bake the high-poly glove and sleeve onto the right arm's low-poly atlas."""
    low = parts['arm_low']
    for name, (colour, rough) in PALETTE.items():
        detail_material(name, colour, rough, 'ripstop' if name == 'sleeve' else 'fabric')
    target = bpy.data.materials.new('arms')
    target.use_nodes = True
    sleeve_faces = [p.material_index == low.data.materials.find('sleeve') for p in low.data.polygons]
    low.data.materials.clear()
    low.data.materials.append(target)
    low['sleeve_faces'] = sleeve_faces
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    if scene.world is None:
        scene.world = bpy.data.worlds.new('bake')
    scene.world.light_settings.distance = 0.012
    tex = target.node_tree.nodes.new('ShaderNodeTexImage')
    target.node_tree.nodes.active = tex
    select(parts['glove_high'], parts['sleeve_high'], low, active=low)
    os.makedirs(out_dir, exist_ok=True)

    def bake(kind, label, space, count, **kw):
        img = bpy.data.images.new(f'relay_ar_arms_{label}', size, size, alpha=False)
        img.colorspace_settings.name = space
        tex.image = img
        scene.cycles.samples = count
        bpy.ops.object.bake(type=kind, use_selected_to_active=True, cage_extrusion=0.003, max_ray_distance=0.008,
                            margin=8, use_clear=True, target='IMAGE_TEXTURES', **kw)
        img.filepath_raw = os.path.join(out_dir, f'relay_ar_arms_{label}_raw.png')
        img.file_format = 'PNG'
        img.save()
        print('BAKED', label)

    bake('DIFFUSE', 'albedo', 'sRGB', 1, pass_filter={'COLOR'})
    bake('ROUGHNESS', 'roughness', 'Non-Color', 1)
    bake('NORMAL', 'normal', 'Non-Color', 4, normal_space='TANGENT')
    bake('AO', 'occlusion', 'Non-Color', samples)
    black = bpy.data.images.new('relay_ar_arms_metallic', 8, 8, alpha=False)
    black.generated_color = (0, 0, 0, 1)
    black.scale(size, size)
    black.filepath_raw = os.path.join(out_dir, 'relay_ar_arms_metallic_raw.png')
    black.file_format = 'PNG'
    black.save()
    for obj in (parts['glove_high'], parts['sleeve_high']):
        bpy.data.objects.remove(obj, do_unlink=True)


# ------------------------------------------------------------------ bind pose, reload, export

def bind_pose(rig, sides):
    """Freeze the solved hold as the rest pose and join both arms into one skinned mesh."""
    for obj in sides.values():
        select(obj)
        bpy.ops.object.modifier_apply(modifier='rig')
    select(rig)
    bpy.ops.object.mode_set(mode='POSE')
    bpy.ops.pose.armature_apply(selected=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    objs = list(sides.values())
    select(*objs)
    bpy.ops.object.join()
    arms_obj = objs[0]
    arms_obj.name = arms_obj.data.name = 'arms'
    mod = arms_obj.modifiers.new('rig', 'ARMATURE')
    mod.object = rig
    arms_obj.parent = rig
    return arms_obj


# The game moves the magazine straight down its well (rifle space) by 0.23 m times
# extraction(p); see actor.gd. The clip follows the same curve.
MAG_DROP = 0.23


def extraction(p):
    return math.sin(min(1.0, max(0.0, (p - 0.12) / 0.72)) * math.pi)


def smooth(t):
    t = min(1.0, max(0.0, t))
    return t * t * (3 - 2 * t)


GRAB = {'distal': (0.0, 1.0, -0.35), 'dorsal': (-1.0, 0.0, 0.0), 'mcp': (-0.030, 0.150, -0.080),
        'elbow_dir': (-0.60, -0.45, -0.66), 'curl': (10, 15, 10)}


def grab_pose(rig, arms_obj, placement_L, magazine, report=print):
    """Solve the support hand round the seated magazine. Returns per-bone armature
    matrices (forearm, hand) and local finger rotations."""
    obstacle = Obstacle([magazine])
    names = {g.index: g.name for g in arms_obj.vertex_groups}
    grab = hand_frame(GRAB['distal'], GRAB['dorsal'], GRAB['mcp'], True)
    # Rigid move of the whole left hand from its bind placement to the grab, then out
    # along the back of the hand until the palm clears the magazine.
    T = grab @ placement_L.inverted()
    palm = [v.co.copy() for v in arms_obj.data.vertices
            if v.groups and names[max(v.groups, key=lambda g: g.weight).group] == 'L_hand'][::2]
    dorsal = (grab.to_3x3() @ Vector((0, 0, 1))).normalized()
    for _ in range(80):
        if all(obstacle.distance(T @ p) >= 0.0008 for p in palm):
            break
        T = Matrix.Translation(dorsal * 0.0005) @ T
    hand = rig.pose.bones['L_hand']
    hand_rest = rig.data.bones['L_hand'].matrix_local
    wrist = T @ hand_rest.translation
    elbow = wrist + Vector(GRAB['elbow_dir']).normalized() * float(np.linalg.norm(arms.ELBOW))
    fore = rig.pose.bones['L_forearm']
    rest_fore = rig.data.bones['L_forearm'].matrix_local
    new_y = (wrist - elbow).normalized()
    turn = (rest_fore.to_3x3() @ Vector((0, 1, 0))).rotation_difference(new_y)
    M = (turn.to_matrix() @ rest_fore.to_3x3()).to_4x4()
    M.translation = elbow
    fore.matrix = M
    bpy.context.view_layer.update()
    hand.matrix = T @ hand_rest
    bpy.context.view_layer.update()
    # Fingers close on the magazine from a light curl.
    pts = {}
    rest_points = {}
    for v in arms_obj.data.vertices:
        if not v.groups:
            continue
        g = max(v.groups, key=lambda g: g.weight)
        n = names[g.group]
        if n.startswith('L_') and g.weight > 0.5:
            rest_points.setdefault(n, []).append(v.co.copy())
    for name in arms.FINGERS + ('thumb',):
        chain = [f'L_{name}_{i}' for i in (1, 2, 3)]
        limits = THUMB_LIMITS if name == 'thumb' else LIMITS
        angles = close_chain(rig, chain, rest_points, obstacle, limits, RATIO, base=[math.radians(a) for a in GRAB['curl']])
        report('grab', name, None if angles is None else [round(math.degrees(a)) for a in angles])
    pose = {'forearm': fore.matrix.copy(), 'hand': hand.matrix.copy(), 'T': T}
    pose['fingers'] = {pb.name: pb.rotation_quaternion.copy() for pb in rig.pose.bones
                       if pb.name.startswith('L_') and pb.name not in ('L_forearm', 'L_hand')}
    return pose


def reload_clip(rig, grab, fps=30):
    """Key the support arm over a one-second clip that the game seeks by reload progress."""
    scene = bpy.context.scene
    scene.render.fps = fps
    rig.animation_data_create()
    action = bpy.data.actions.new('reload')
    rig.animation_data.action = action
    fore, hand = rig.pose.bones['L_forearm'], rig.pose.bones['L_hand']
    rest_fore = rig.data.bones['L_forearm'].matrix_local
    rest_hand = rig.data.bones['L_hand'].matrix_local
    fingers = [rig.pose.bones[n] for n in grab['fingers']]
    for pb in [fore, hand] + fingers:
        pb.rotation_mode = 'QUATERNION'
    loc_r, rot_r, _ = rest_hand.decompose()
    loc_g, rot_g, _ = (grab['T'] @ rest_hand).decompose()
    for frame in range(fps + 1):
        p = frame / fps
        # Reach the magazine by 0.11, hold it until 0.84 (it is seated again), seat it with
        # a short push, then return to the handguard by 1.0.
        w = smooth(p / 0.11) if p < 0.5 else 1.0 - smooth((p - 0.88) / 0.12)
        drop = Vector((0, 0, -MAG_DROP * extraction(p)))
        push = Vector((0, 0, 0.010 * math.sin(min(1.0, max(0.0, (p - 0.84) / 0.06)) * math.pi)))
        loc = loc_r.lerp(loc_g, w) + (drop + push) * w
        rot = rot_r.slerp(rot_g, w)
        H = Matrix.LocRotScale(loc, rot, None)
        wrist = H.translation
        grab_elbow = grab['forearm'].translation
        rest_elbow = rest_fore.translation
        elbow = rest_elbow.lerp(grab_elbow + (drop + push) * w * 0.6, w)
        new_y = (wrist - elbow).normalized()
        turn = (rest_fore.to_3x3() @ Vector((0, 1, 0))).rotation_difference(new_y)
        F = (turn.to_matrix() @ rest_fore.to_3x3()).to_4x4()
        F.translation = wrist - new_y * rig.data.bones['L_forearm'].length
        fore.matrix = F
        bpy.context.view_layer.update()
        hand.matrix = H
        bpy.context.view_layer.update()
        # Fingers open in transit and close on arrival.
        opening = math.sin(math.pi * w) * 0.35 if 0.0 < w < 1.0 else 0.0
        for pb in fingers:
            q = Quaternion().slerp(grab['fingers'][pb.name], w)
            pb.rotation_quaternion = Quaternion((1, 0, 0), opening) @ q if pb.name[2:] not in ('thumb_1',) else q
        for pb in [fore, hand] + fingers:
            pb.keyframe_insert('location', frame=frame, group=pb.name)
            pb.keyframe_insert('rotation_quaternion', frame=frame, group=pb.name)
    scene.frame_start, scene.frame_end = 0, fps
    for pb in rig.pose.bones:
        pb.location = (0, 0, 0)
        pb.rotation_quaternion = (1, 0, 0, 0)
    return action


def export(rig, arms_obj, path):
    select(rig, arms_obj, active=rig)
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=True, export_apply=False,
                              export_animations=True, export_skins=True, export_animation_mode='ACTIONS',
                              export_def_bones=False, export_force_sampling=True, export_materials='PLACEHOLDER')
    print('EXPORTED', path)


if __name__ == '__main__':
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    out = os.path.abspath(argv[0])
    here = os.path.dirname(os.path.abspath(__file__))
    rifle_glb = argv[argv.index('--rifle') + 1] if '--rifle' in argv else os.path.join(here, '../../game/assets/weapons/relay_ar/relay_ar.glb')
    glb = argv[argv.index('--glb') + 1] if '--glb' in argv else os.path.join(out, 'relay_ar_arms.glb')
    size = int(argv[argv.index('--size') + 1]) if '--size' in argv else 2048
    samples = int(argv[argv.index('--samples') + 1]) if '--samples' in argv else 48
    if '--preview' in argv:
        build_rig(out, rifle_glb, preview=True)
    else:
        build(out, rifle_glb, glb, size, samples)
