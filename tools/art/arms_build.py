"""Builds the rigged first-person arms (relay_ar_arms.glb) from relay_ar_arms.py.

Stages, all headless Blender (bpy module):
1. Mesh the right arm's glove and sleeve as high-poly surfaces (bake sources) and a
   medium surface without seams that QuadriFlow retopologises into the game mesh.
2. Bones from the same landmarks; automatic (bone heat) weights on the right arm.
3. The left arm is the right arm mirrored, with mirrored weights.
4. Both arms are placed on the rifle (Blender rifle space: barrel +Y, Z up) and the
   fingers close on the grip, trigger and handguard: each joint flexes until its
   phalanx would touch the rifle's surface (a BVH of the rifle's own meshes).
5. The posed arms become the bind pose. The support hand then performs the reload on a
   60 fps, one-second clip the game seeks by reload progress: it comes up to the seated
   magazine from below, cups its base, slides it out along its well, lifts it out to the
   rifle's left, brings it back, enters it and pushes it to its stop, stays closed on it until
   it is seated and lets go only then (the phase boundaries are P_* below and Actor.RELOAD_*).
   The magazine is not keyed here: the game poses it from the hand bone while the hand holds it.
6. review_clip() measures, at every frame, how far the posed arms enter the rifle and the
   moving magazine (clip_contact.csv); the build prints the deepest vertex.

python arms_build.py <out_dir> [--preview] [--no-bake] [--h-high 0.0005] [--rifle relay_ar.glb]

--no-bake skips the high-poly bake and the textures (about 13 s instead of about 4 minutes); the
clip, rig and contact review are the same, so motion can be reviewed in the game. That mesh is
not the shipped one's and is never shipped. ARMS_GRAB_JSON overrides entries of GRAB for one build.
"""
import math
import os
import re
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


# Linear base colour and roughness. A charcoal glove with black moulded parts and a
# slightly lighter suede palm, and a muted olive-drab jacket. The v4 jacket (0.082, 0.092,
# 0.052) measured a median luma of 141-146 in sun, twice the receiver's and the furniture's,
# and read as chartreuse; this one is about half as bright in linear terms and far less
# saturated (target about 110 in sun), and the gloves are about 25 % lighter (the v4 gloves
# measured 15-16 in a dark interior). The v3 glove at 0.050 with strong tan wear read as bare
# skin and measured level with the sleeve, so the glove stays well under the jacket.
PALETTE = {
    'fabric': ((0.030, 0.027, 0.024), 0.86), 'palm': ((0.042, 0.037, 0.032), 0.93),
    'shell': ((0.012, 0.012, 0.013), 0.48), 'strap': ((0.022, 0.020, 0.018), 0.80),
    'cuff': ((0.027, 0.025, 0.022), 0.88),
    'sleeve': ((0.045, 0.051, 0.041), 0.90), 'hem': ((0.037, 0.042, 0.034), 0.88),
}


# Game-mesh density: about 8.3k triangles for both arms (v3 was 10,672; the documented
# hands-and-sleeves budget is 10,000). The sleeve's folds are in the normal map.
GLOVE_QUADS = 1800
SLEEVE_SEGMENTS = 32
SLEEVE_RINGS = 20


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
    v, f = arms.sleeve_low_mesh(SLEEVE_SEGMENTS, SLEEVE_RINGS)
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
    'L': {'distal': (0.88, 0.06, 0.47), 'dorsal': (-0.45, 0.0, -0.89), 'roll': math.radians(0), 'mcp': (0.030, 0.430, -0.006),
          'elbow_dir': (-0.62, -0.45, -0.64), 'mirror': True, 'curl': (20, 30, 15)},
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

    def descend(x):
        best, _ = cost(x)
        for step in (0.14, 0.07, 0.035, 0.017, 0.008):
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
        return best, x

    # Several starts: a single descent stalled about 10 mm short of the trigger.
    starts = [x, [0.25, 0.0, 0.9, 0.5], [0.5, 0.15, 0.6, 0.4], [0.0, -0.1, 1.1, 0.7]]
    best, x = min((descend(list(start)) for start in starts), key=lambda r: r[0])
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
    parts = right_arm_meshes(h_high, 0.0011, GLOVE_QUADS, 520, high=not preview)
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


def build(out_dir, rifle_glb, glb_path, size=2048, samples=48, h_high=0.0005, bake=True):
    """`bake=False` skips the high-poly bake and textures: the clip, the rig and the mesh
    export as usual, so motion can be reviewed in the game in about a minute. Its mesh is
    not the shipped one's (the UVs may differ), so it is never shipped."""
    rig, sides, rifle, parts, placements = build_rig(out_dir, rifle_glb, not bake, h_high, HOLD, size, samples)
    bpy.data.objects.remove(parts['arm_low'], do_unlink=True)
    arms_obj = bind_pose(rig, sides)
    select(rig)
    bpy.ops.object.mode_set(mode='POSE')
    magazine = next(o for o in rifle if o.name == 'magazine')
    grab = grab_pose(rig, arms_obj, placements['L'], magazine)
    axis, _ = well_axis(magazine)
    reload_clip(rig, grab, axis)
    review_clip(rig, arms_obj, rifle, axis, out_dir)
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
    # Wear lightens only slightly: scuffed fabric, not a different colour.
    wear_colour = {'fabric': (0.060, 0.055, 0.049), 'palm': (0.068, 0.061, 0.053), 'shell': (0.040, 0.040, 0.041),
                   'strap': (0.036, 0.034, 0.032), 'cuff': (0.045, 0.043, 0.040), 'sleeve': (0.080, 0.088, 0.068), 'hem': (0.066, 0.072, 0.056)}[name]
    worn = nodes.new('ShaderNodeMix')
    worn.data_type = 'RGBA'
    worn.inputs['B'].default_value = (*wear_colour, 1)
    links.new(base.outputs['Result'], worn.inputs['A'])
    wear_amount = nodes.new('ShaderNodeMath')
    wear_amount.operation = 'MULTIPLY'
    wear_amount.inputs[1].default_value = 0.40
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


def _arm_part(low, sleeve, name):
    """A copy of the low arm with only its sleeve faces (or only its glove faces)."""
    obj = low.copy()
    obj.data = low.data.copy()
    obj.name = name
    bpy.context.scene.collection.objects.link(obj)
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    flags = list(low['sleeve_faces'])
    bmesh.ops.delete(bm, geom=[f for f, s in zip(bm.faces, flags) if bool(s) != sleeve], context='FACES')
    bm.to_mesh(obj.data)
    bm.free()
    return obj


def _uv_mask(low, sleeve, size, grow=0):
    """Texels covered by the sleeve (or glove) faces' UV islands, grown by `grow` texels.
    Rows run bottom to top, as in Blender's image pixels."""
    mask = np.zeros((size, size), dtype=bool)
    uv = low.data.uv_layers.active.data
    flags = list(low['sleeve_faces'])
    for poly, flag in zip(low.data.polygons, flags):
        if bool(flag) != sleeve:
            continue
        pts = np.array([uv[i].uv[:] for i in poly.loop_indices]) * size - 0.5
        for k in range(1, len(pts) - 1):
            tri = pts[[0, k, k + 1]]
            lo = np.maximum(np.floor(tri.min(0)).astype(int), 0)
            hi = np.minimum(np.ceil(tri.max(0)).astype(int), size - 1)
            if (hi < lo).any():
                continue
            xs, ys = np.meshgrid(np.arange(lo[0], hi[0] + 1), np.arange(lo[1], hi[1] + 1))
            (x0, y0), (x1, y1), (x2, y2) = tri
            den = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
            if abs(den) < 1e-12:
                continue
            a = ((y1 - y2) * (xs - x2) + (x2 - x1) * (ys - y2)) / den
            b = ((y2 - y0) * (xs - x2) + (x0 - x2) * (ys - y2)) / den
            inside = (a >= -0.02) & (b >= -0.02) & (a + b <= 1.02)
            mask[ys[inside], xs[inside]] = True
    for _ in range(grow):
        grown = mask.copy()
        grown[1:] |= mask[:-1]
        grown[:-1] |= mask[1:]
        grown[:, 1:] |= mask[:, :-1]
        grown[:, :-1] |= mask[:, 1:]
        mask = grown
    return mask


def bake_arm(parts, out_dir, size=2048, samples=48):
    """Bake the high-poly glove and sleeve onto the right arm's low-poly atlas. The glove
    faces bake only from the high glove and the sleeve faces only from the high sleeve
    (the v3 bake let the cuff's rays reach the sleeve's hem), then the two are merged by
    UV island. Occlusion still sees the whole arm."""
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
    os.makedirs(out_dir, exist_ok=True)
    glove_part, sleeve_part = _arm_part(low, False, 'bake_glove'), _arm_part(low, True, 'bake_sleeve')
    margin = 8
    glove_core = _uv_mask(low, False, size)
    sleeve_core = _uv_mask(low, True, size)
    sleeve_wide = _uv_mask(low, True, size, margin) & ~glove_core

    def bake_part(high, part, kind, space, count, **kw):
        img = bpy.data.images.new(f'bake_{part.name}', size, size, alpha=False)
        img.colorspace_settings.name = space
        tex.image = img
        scene.cycles.samples = count
        # Only the high-poly surfaces may occlude: the other low copies sit inside them
        # but poke out where the game mesh is smoother, and would blacken the AO.
        for obj in (low, glove_part, sleeve_part):
            obj.hide_render = obj is not part
        select(high, part, active=part)
        # The cage clears the 3 mm knuckle guard, so its rays reach the guard's top
        # rather than grazing its sides (which tore its edge in the v3 bake).
        bpy.ops.object.bake(type=kind, use_selected_to_active=True, cage_extrusion=0.005, max_ray_distance=0.012,
                            margin=margin, use_clear=True, target='IMAGE_TEXTURES', **kw)
        px = np.empty(size * size * 4, dtype=np.float32)
        img.pixels.foreach_get(px)
        bpy.data.images.remove(img)
        return px.reshape(size, size, 4)

    def bake(kind, label, space, count, **kw):
        out = bake_part(parts['glove_high'], glove_part, kind, space, count, **kw)
        sleeve = bake_part(parts['sleeve_high'], sleeve_part, kind, space, count, **kw)
        out[sleeve_core | sleeve_wide] = sleeve[sleeve_core | sleeve_wide]
        img = bpy.data.images.new(f'relay_ar_arms_{label}', size, size, alpha=False)
        img.colorspace_settings.name = space
        img.pixels.foreach_set(out.ravel())
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
    low.hide_render = False
    for obj in (parts['glove_high'], parts['sleeve_high'], glove_part, sleeve_part):
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


# The reload, as fractions of its length, comes from game/scripts/gameplay/reload_phases.gd, the
# single definition (the game seeks the clip by reload progress and times the magazine's carry,
# the click sounds and the old magazine's drop from the same names; the tests measure the
# imported clip against them). Read here by pattern, so there is no second copy to drift.
#   0.00-REACH       the support hand leaves the handguard and comes up to the magazine from below
#   REACH-GRASP      the fingers close on it
#   GRASP-UNLATCH    the hand takes its weight; at UNLATCH the latch lets go
#   UNLATCH-CLEAR    it slides out along its well and clears it
#   CLEAR-DROP       it swings out to the left; at DROP the fingers open and it is let go
#   DROP-ACQUIRE     the empty hand goes to the pouch, down and to the left
#   at ACQUIRE       the fingers close on the replacement (a second magazine)
#   ACQUIRE-ALIGN    it is brought up into view and lined up under the well
#   ALIGN-ENTER-SEAT it enters and is pushed to its stop: seated at SEAT
#   SEAT-LETGO       the hand stays closed on the seated magazine
#   LETGO-1.00       the fingers open and the hand returns to the handguard
HERE = os.path.dirname(os.path.abspath(__file__))


def load_phases(path=None):
    path = path or os.path.join(HERE, '../../game/scripts/gameplay/reload_phases.gd')
    with open(path) as f:
        found = {m.group(1): float(m.group(2)) for m in re.finditer(r'^const ([A-Z_]+) := ([0-9.]+)\s*$', f.read(), re.M)}
    missing = [k for k in ('REACH', 'GRASP', 'UNLATCH', 'CLEAR', 'DROP', 'ACQUIRE', 'ALIGN', 'ENTER', 'SEAT', 'LETGO') if k not in found]
    if missing:
        raise SystemExit('reload_phases.gd does not define %s' % ', '.join(missing))
    order = [found[k] for k in ('REACH', 'GRASP', 'UNLATCH', 'CLEAR', 'DROP', 'ACQUIRE', 'ALIGN', 'ENTER', 'SEAT', 'LETGO')]
    if order != sorted(order) or len(set(order)) != len(order) or order[0] <= 0 or order[-1] >= 1:
        raise SystemExit('reload_phases.gd: the phases must be strictly increasing inside (0, 1): %s' % order)
    return found


PHASES = load_phases()
P_REACH, P_GRASP, P_UNLATCH, P_CLEAR, P_DROP = (PHASES[k] for k in ('REACH', 'GRASP', 'UNLATCH', 'CLEAR', 'DROP'))
P_ACQUIRE, P_ALIGN, P_ENTER, P_SEAT, P_LETGO = (PHASES[k] for k in ('ACQUIRE', 'ALIGN', 'ENTER', 'SEAT', 'LETGO'))
# The hand arrives at, and leaves, the magazine from the left and a little above its grasp: it first goes
# to a point this far from the grasp (rifle space) and only then closes on the base, so it never crosses
# the magazine on a straight line between the handguard and the grasp. (Until v7 the point was 85 mm BELOW
# the grasp, which is below the bottom of the frame: the support hand left the picture for about 0.06 of the
# reload on the way in and again on the way out. reload_visibility_test.gd counts the hand's pixels.)
APPROACH = Vector((-0.080, 0.000, 0.010))
APPROACH_AT = 0.65
if os.environ.get('ARMS_APPROACH'):   # exploration hook: ARMS_APPROACH='x,y,z[,at]' for one build
    _a = [float(v) for v in os.environ['ARMS_APPROACH'].split(',')]
    APPROACH = Vector(_a[:3])
    APPROACH_AT = _a[3] if len(_a) > 3 else APPROACH_AT


def well_axis(magazine):
    """Unit vector from the magazine's top to its bottom, rifle space (the way it slides
    out), and the centre of its top face."""
    verts = [magazine.matrix_world @ v.co for v in magazine.data.vertices]
    zs = [v.z for v in verts]
    lo, hi = min(zs), max(zs)
    top = sum((v for v in verts if v.z > hi - 0.01), Vector()) / sum(1 for v in verts if v.z > hi - 0.01)
    bottom = sum((v for v in verts if v.z < lo + 0.01), Vector()) / sum(1 for v in verts if v.z < lo + 0.01)
    return (bottom - top).normalized(), top


# Paths of the two magazines relative to where a magazine sits when seated: (progress, travel out
# of the well in metres, offset in rifle space, turn in degrees about the rifle's X, Y and Z).
# The well holds a magazine 0.075 m deep, so it is clear at 0.09. Between keys the motion eases,
# so a repeated key is a pause. Rifle space: x right, y toward the muzzle, z up.
WELL_DEPTH = 0.075
ZERO3 = (0.0, 0.0, 0.0)
# The old magazine: the hand takes it, it slides out, clears the well and swings out to the left,
# where the fingers open and let it go (it falls; the game drops it, nothing here needs it after).
# Exploration hook (like ARMS_GRAB_JSON): ARMS_PATH_JSON='{"swing": [x, y, z], "pouch": [x, y, z], "mid": [x, y, z]}'
# overrides where the old magazine is let go, where the replacement waits and its midway point, for one build.
_PATH = {'swing': (-0.070, 0.020, -0.010), 'pouch': (-0.170, 0.120, -0.020), 'mid': (-0.070, 0.050, -0.020), 'pouch_turn': (-10, 0, 10)}
if os.environ.get('ARMS_PATH_JSON'):
    import json
    _PATH.update({k: tuple(v) for k, v in json.loads(os.environ['ARMS_PATH_JSON']).items()})
MAG_KEYS_OLD = (
    (0.00, 0.000, ZERO3, (0, 0, 0)),
    (P_GRASP, 0.000, ZERO3, (0, 0, 0)),
    (P_UNLATCH, 0.000, ZERO3, (0, 0, 0)),                                  # seated until the latch lets go (the click), then it slides
    (P_CLEAR, 0.098, ZERO3, (0, 0, 0)),                                    # clear of the well
    (P_DROP, 0.100, _PATH['swing'], (-10, 0, 12)),                         # swung out to the left; let go
)
# Where the replacement waits: the hand's pouch, to the left of the well (relative to the seated
# place, with the 0.1 m of travel included). Tuned against the probe's frame counts.
POUCH_OFFSET = _PATH['pouch']
POUCH_TURN = _PATH['pouch_turn']
# The replacement: taken from the pouch, brought up into view, lined up, entered and pushed home.
MAG_KEYS_NEW = (
    (P_ACQUIRE, 0.100, POUCH_OFFSET, POUCH_TURN),
    (P_ACQUIRE + (P_ALIGN - P_ACQUIRE) * 0.55, 0.100, _PATH['mid'], (-10, 0, 9)),   # coming up toward the well
    (P_ALIGN, 0.088, ZERO3, (-3, 0, 0)),                                   # lined up under it
    (P_ENTER, 0.030, ZERO3, (-1, 0, 0)),                                   # entering
    (P_SEAT, 0.000, ZERO3, (0, 0, 0)),                                     # pushed to its stop
    (1.00, 0.000, ZERO3, (0, 0, 0)),
)
MAG_PIVOT = Vector((0.0, 0.13, -0.08))   # about the middle of the part the hand holds


def _path(keys, p, axis):
    """A magazine's rigid motion (rifle space) at progress p along one key table; before the
    first key it is at the first key's pose, after the last at the last."""
    if p <= keys[0][0]:
        p = keys[0][0]
    if p >= keys[-1][0]:
        p = keys[-1][0]
    for i in range(len(keys) - 1):
        if keys[i][0] <= p <= keys[i + 1][0]:
            a, b = keys[i], keys[i + 1]
            t = smooth((p - a[0]) / max(b[0] - a[0], 1e-6)) if (a[1:] != b[1:]) else 0.0
            travel = a[1] + (b[1] - a[1]) * t
            offset = Vector(a[2]).lerp(Vector(b[2]), t)
            turn = Vector(a[3]).lerp(Vector(b[3]), t)
            rot = Matrix.Rotation(math.radians(turn.z), 4, 'Z') @ Matrix.Rotation(math.radians(turn.y), 4, 'Y') @ Matrix.Rotation(math.radians(turn.x), 4, 'X')
            pivot = Matrix.Translation(MAG_PIVOT) @ rot @ Matrix.Translation(-MAG_PIVOT)
            return Matrix.Translation(offset + axis * travel) @ pivot
    return Matrix.Identity(4)


def holding(p):
    """Which magazine the hand holds at progress p: 'old' from the grasp to the drop, 'new' from
    the acquisition to the let-go, None while it travels empty or is not on a magazine."""
    if P_GRASP <= p <= P_DROP:
        return 'old'
    if P_ACQUIRE <= p <= P_LETGO:
        return 'new'
    return None


def mag_path(p, axis, which=None):
    """The motion of the magazine the hand holds (or `which`) at progress p."""
    which = which or holding(p) or ('old' if p < P_GRASP else 'new')
    return _path(MAG_KEYS_OLD if which == 'old' else MAG_KEYS_NEW, p, axis)


def smooth(t):
    t = min(1.0, max(0.0, t))
    return t * t * (3 - 2 * t)


# The grasp, chosen by measurement (v7): the palm under the magazine's base and a little to its rear, the
# fingers pointing across and forward (30 degrees toward the muzzle) and curling up the front and right
# faces, the thumb rolled round onto the REAR face where the camera sees it. Every digit tip touches the
# surface (0 to 4 mm) and the thumb is 111 degrees round the magazine from the fingers (clip_contact.csv);
# in the frame the thumb and three fingertips are drawn in every held frame (reload_visibility_test.gd).
# The v6 grasp (the same palm, fingers across at 0 degrees, thumb on the front face) hid the thumb and
# two fingertips behind the magazine; it was found by counting their pixels, not by eye. The search that
# found this one ran the build over distal directions, dorsal directions, knuckle offsets and rolls and
# kept those with every digit within 6.5 mm of the magazine and nothing sunk into it or the rifle.
GRAB = {'distal': (0.866, 0.5, 0.0), 'dorsal': (0.0, 0.0, -1.0), 'mcp': (0.014, 0.150, -0.190), 'roll': 25,
        'elbow_dir': (-0.60, -0.50, -0.60), 'curl': (25, 30, 20), 'thumb': (-40, -30, 0)}
# Bones whose rest points must clear the magazine before the fingers close: the palm,
# the first phalanges and the thumb's metacarpal (the v3 solve cleared only the palm, so
# the thumb and little finger started inside the magazine and never closed).
# Extra spread of each finger's first joint in the grasp (radians about its own Z): the index
# and middle lean toward the thumb, the ring and little finger away from it.
GRAB_FAN = {'index': -0.10, 'middle': -0.02, 'ring': 0.08, 'pinky': 0.18}
# How closed the fingers are while the empty hand travels to the pouch (0 open, 1 as on a magazine).
RELAXED = 0.18
GRAB_CLEAR = ('L_hand', 'L_index_1', 'L_middle_1', 'L_ring_1', 'L_pinky_1', 'L_thumb_1')
# Exploration hook: ARMS_GRAB_JSON='{"elbow_dir": [x, y, z], "mcp": [x, y, z]}' overrides
# entries of GRAB for one build, so a grasp can be tried without editing the file.
if os.environ.get('ARMS_GRAB_JSON'):
    import json
    GRAB.update({k: tuple(v) if isinstance(v, list) else v for k, v in json.loads(os.environ['ARMS_GRAB_JSON']).items()})
    print('GRAB overridden:', GRAB)


def grab_pose(rig, arms_obj, placement_L, magazine, report=print):
    """Solve the support hand round the seated magazine. Returns per-bone armature
    matrices (forearm, hand) and local finger rotations."""
    obstacle = Obstacle([magazine])
    names = {g.index: g.name for g in arms_obj.vertex_groups}
    grab = hand_frame(GRAB['distal'], GRAB['dorsal'], GRAB['mcp'], True, math.radians(GRAB.get('roll', 0.0)))
    # Rigid move of the whole left hand from its bind placement to the grab, then out
    # along the back of the hand until the palm clears the magazine.
    T = grab @ placement_L.inverted()
    palm = [v.co.copy() for v in arms_obj.data.vertices
            if v.groups and names[max(v.groups, key=lambda g: g.weight).group] in GRAB_CLEAR][::2]
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
        base = GRAB['thumb'] if name == 'thumb' else GRAB['curl']
        angles = close_chain(rig, chain, rest_points, obstacle, limits, RATIO, base=[math.radians(a) for a in base])
        report('grab', name, None if angles is None else [round(math.degrees(a)) for a in angles])
        if name != 'thumb':
            # Fan the fingers a little (the cupped hand is not a fist): this is what keeps
            # them from fusing into one mass when the hand is seen from the side.
            first = rig.pose.bones[chain[0]]
            first.rotation_quaternion = Quaternion((0, 0, 1), GRAB_FAN[name]) @ first.rotation_quaternion
    pose = {'forearm': fore.matrix.copy(), 'hand': hand.matrix.copy(), 'T': T}
    pose['fingers'] = {pb.name: pb.rotation_quaternion.copy() for pb in rig.pose.bones
                       if pb.name.startswith('L_') and pb.name not in ('L_forearm', 'L_hand')}
    return pose


def reload_clip(rig, grab, axis, fps=60):
    """Key the support arm over a one-second clip that the game seeks by reload progress.
    The hand reaches the seated magazine, closes on it, carries it out and lets it go; goes
    empty to the pouch, closes on the replacement and carries it to the well; lets go only
    after it is seated and a short hold has passed."""
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
    grab_hand = grab['T'] @ rest_hand
    grab_elbow = grab['forearm'].translation
    rest_elbow = rest_fore.translation
    loc_r, rot_r, _ = rest_hand.decompose()
    loc_g, rot_g, _ = grab_hand.decompose()
    loc_p = loc_g + APPROACH
    elbow_p = grab_elbow + APPROACH * 0.5

    def routed(w):
        """Hand location, rotation and elbow between the handguard (w=0) and the grasp (w=1),
        by way of the point below the grasp."""
        if w <= APPROACH_AT:
            t = smooth(w / APPROACH_AT)
            return loc_r.lerp(loc_p, t), rot_r.slerp(rot_g, t), rest_elbow.lerp(elbow_p, t)
        t = smooth((w - APPROACH_AT) / (1.0 - APPROACH_AT))
        return loc_p.lerp(loc_g, t), rot_g, elbow_p.lerp(grab_elbow, t)

    def held(p):
        """Hand matrix and elbow while it holds a magazine."""
        M = mag_path(p, axis, holding(p))
        return M @ grab_hand, grab_elbow + M.translation * 0.5

    # The empty hand's journey from the old magazine's release to the replacement's pouch.
    drop_H, drop_elbow = held(P_DROP)
    take_H, take_elbow = held(P_ACQUIRE)
    drop_loc, drop_rot, _ = drop_H.decompose()
    take_loc, take_rot, _ = take_H.decompose()

    def transit(p):
        t = smooth((p - P_DROP) / (P_ACQUIRE - P_DROP))
        loc = drop_loc.lerp(take_loc, t)
        # Bow the path outward (left) so the empty hand does not cut back across the rifle.
        loc += Vector((-0.03, 0.0, 0.0)) * math.sin(math.pi * t)
        return Matrix.LocRotScale(loc, drop_rot.slerp(take_rot, t), None), drop_elbow.lerp(take_elbow, t)

    for frame in range(fps + 1):
        p = frame / fps
        # Where the hand is between the handguard and the magazine: 0 on the handguard, 1 on
        # the magazine. It rides a magazine while it holds one.
        reach = smooth(p / P_REACH) if p < P_GRASP else 1.0 - smooth((p - P_LETGO) / (1.0 - P_LETGO))
        if holding(p) is not None:
            H, elbow = held(p)
        elif P_DROP < p < P_ACQUIRE:
            H, elbow = transit(p)
        else:
            loc, rot, elbow = routed(reach)
            H = Matrix.LocRotScale(loc, rot, None)
        wrist = H.translation
        new_y = (wrist - elbow).normalized()
        turn = (rest_fore.to_3x3() @ Vector((0, 1, 0))).rotation_difference(new_y)
        F = (turn.to_matrix() @ rest_fore.to_3x3()).to_4x4()
        F.translation = wrist - new_y * rig.data.bones['L_forearm'].length
        fore.matrix = F
        bpy.context.view_layer.update()
        hand.matrix = H
        bpy.context.view_layer.update()
        # The fingers open in transit, close on the old magazine between REACH and GRASP, stay
        # closed until it is let go, relax while the hand travels to the pouch, close on the
        # replacement by ACQUIRE, stay closed until the let-go, and open only then.
        if p < P_GRASP:
            closing = smooth((p - P_REACH) / (P_GRASP - P_REACH))
        elif p <= P_DROP:
            closing = 1.0
        elif p < P_ACQUIRE:
            opened = 1.0 - smooth((p - P_DROP) / 0.05) * (1.0 - RELAXED)
            closing_again = smooth((p - (P_ACQUIRE - 0.07)) / 0.07)
            closing = max(RELAXED, opened) if p < P_ACQUIRE - 0.07 else RELAXED + (1.0 - RELAXED) * closing_again
        elif p <= P_LETGO:
            closing = 1.0
        else:
            closing = 1.0 - smooth((p - P_LETGO) / 0.05)
        flare = math.sin(math.pi * min(1.0, max(0.0, p / P_REACH))) * 0.45 if p < P_REACH else 0.0
        flare += math.sin(math.pi * min(1.0, max(0.0, (p - P_LETGO) / (1.0 - P_LETGO)))) * 0.25 if p > P_LETGO else 0.0
        if P_DROP < p < P_ACQUIRE:
            flare += math.sin(math.pi * (p - P_DROP) / (P_ACQUIRE - P_DROP)) * 0.30
        for pb in fingers:
            q = Quaternion().slerp(grab['fingers'][pb.name], closing)
            pb.rotation_quaternion = Quaternion((1, 0, 0), flare) @ q if pb.name[2:] not in ('thumb_1',) else q
        for pb in [fore, hand] + fingers:
            pb.keyframe_insert('location', frame=frame, group=pb.name)
            pb.keyframe_insert('rotation_quaternion', frame=frame, group=pb.name)
    scene.frame_start, scene.frame_end = 0, fps
    for pb in rig.pose.bones:
        pb.location = (0, 0, 0)
        pb.rotation_quaternion = (1, 0, 0, 0)
    return action


INF_GAP = 1e9


def review_clip(rig, arms_obj, rifle, axis, out_dir, fps=60):
    """Contact review of the reload clip: at every frame, how far the posed arms (both
    sleeves and gloves) enter the rifle and the moving magazine. Writes clip_contact.csv."""
    scene = bpy.context.scene
    body = Obstacle([o for o in rifle if o.name not in ('stock', 'magazine', 'magazine_rounds')])
    magazine = next(o for o in rifle if o.name == 'magazine')
    mag_verts = [magazine.matrix_world @ v.co for v in magazine.data.vertices]
    mag_polys = [list(p.vertices) for p in magazine.data.polygons]
    digits = ('thumb', 'index', 'middle', 'ring', 'pinky')
    rows = ['frame,progress,left_inside_body,left_depth_body_mm,left_inside_magazine,left_depth_magazine_mm,right_inside_body,right_depth_body_mm,held,'
            + ','.join('gap_%s_mm' % d for d in digits) + ',gap_palm_mm,thumb_opposition_deg']
    names = {g.index: g.name for g in arms_obj.vertex_groups}
    tip_groups = {'L_%s_3' % d: d for d in digits}
    for frame in range(fps + 1):
        p = frame / fps
        scene.frame_set(frame)
        graph = bpy.context.evaluated_depsgraph_get()
        evaluated = arms_obj.evaluated_get(graph)
        mesh = evaluated.to_mesh()
        which = holding(p)
        M = mag_path(p, axis, which) if which else None
        mag = BVHTree.FromPolygons([M @ v for v in mag_verts], mag_polys) if M is not None else None
        stats = {'L': [0, 0.0, 0, 0.0], 'R': [0, 0.0, 0, 0.0]}
        # The closest each fingertip (the distal phalanx's vertices), the thumb and the palm come to the
        # held magazine's surface, in mm: positive outside it, negative inside. Fingertips that do not
        # reach it, or that sink into it, are what a wrong grasp looks like.
        gap = {d: INF_GAP for d in digits}
        gap['palm'] = INF_GAP
        tip_points = {d: [] for d in digits}
        for v, src in zip(mesh.vertices, arms_obj.data.vertices):
            if not src.groups:
                continue
            group = names[max(src.groups, key=lambda g: g.weight).group]
            side = group[0]
            if side == 'L' and mag is not None and (group in tip_groups or group == 'L_hand'):
                point = evaluated.matrix_world @ v.co
                near = mag.find_nearest(point, 0.2)
                if near[0] is not None:
                    signed = (point - near[0]).length * (-1.0 if (point - near[0]).dot(near[1]) < 0 else 1.0)
                    key = tip_groups.get(group, 'palm')
                    gap[key] = min(gap[key], signed)
                    if key != 'palm':
                        tip_points[key].append(point)
            if side not in stats:
                continue
            world = evaluated.matrix_world @ v.co
            d = body.distance(world)
            if d < -0.0005:
                stats[side][0] += 1
                stats[side][1] = max(stats[side][1], -d)
            if side == 'L' and mag is not None:
                hit = mag.find_nearest(world, 0.05)
                if hit[0] is not None:
                    inside = (world - hit[0]).dot(hit[1]) < 0
                    if inside and (world - hit[0]).length > 0.0005:
                        stats['L'][2] += 1
                        stats['L'][3] = max(stats['L'][3], (world - hit[0]).length)
        evaluated.to_mesh_clear()
        # How opposed the thumb is to the other four digits about the held magazine's long axis
        # (180 degrees: on the far side of it; near 0: on the same side).
        opposition = -1.0
        if mag is not None and all(tip_points[d] for d in digits):
            def centroid(points):
                total = Vector((0.0, 0.0, 0.0))
                for q in points:
                    total += q
                return total / len(points)
            centre = M @ Vector(sum((v for v in mag_verts), Vector((0.0, 0.0, 0.0))) / len(mag_verts))
            along = (M.to_3x3() @ axis).normalized()
            flat = lambda vec: vec - along * vec.dot(along)
            to_thumb = flat(centroid(tip_points['thumb']) - centre)
            to_fingers = flat(centroid([q for d in digits[1:] for q in tip_points[d]]) - centre)
            if to_thumb.length > 1e-6 and to_fingers.length > 1e-6:
                opposition = math.degrees(to_thumb.angle(to_fingers))
        gap_mm = ','.join(('%.2f' % (gap[d] * 1000)) if gap[d] != INF_GAP else 'nan' for d in digits + ('palm',))
        rows.append('%d,%.3f,%d,%.2f,%d,%.2f,%d,%.2f,%s,%s,%.1f' % (frame, p, stats['L'][0], stats['L'][1] * 1000, stats['L'][2], stats['L'][3] * 1000, stats['R'][0], stats['R'][1] * 1000, which or '-', gap_mm, opposition))
    scene.frame_set(0)
    path = os.path.join(out_dir, 'clip_contact.csv')
    with open(path, 'w') as f:
        f.write('\n'.join(rows) + '\n')
    worst_body = max(float(r.split(',')[3]) for r in rows[1:])
    worst_mag = max(float(r.split(',')[5]) for r in rows[1:])
    worst_right = max(float(r.split(',')[7]) for r in rows[1:])
    print('CLIP CONTACT: deepest left-arm vertex in the rifle %.1f mm, in the magazine %.1f mm; right arm in the rifle %.1f mm (%s)' % (worst_body, worst_mag, worst_right, path))


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
        build(out, rifle_glb, glb, size, samples, bake='--no-bake' not in argv)
