"""First-person gloved hands and sleeves posed on the Relay AR (original geometry).

Same space as relay_ar.py (metres, Blender Z up, barrel +Y). Each finger is a chain of
tapered capsules through explicit joint positions placed around the real grip and
handguard sections; the chains, palm and thumb are fused by a voxel remesh, smoothed
and decimated to the mobile budget. Forearms run toward the elbows of the viewmodel
pose in weapon_model.gd (eye at about (-0.25, -0.15, 0.14) in this space), so they
leave the frame instead of ending on screen.

python relay_ar_hands.py [-- out.glb]
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
import bmesh  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402
import hardsurface as hs  # noqa: E402

BORE = 0.025
GROUPS = {'hands': ('glove_right', 'glove_left', 'sleeve_right', 'sleeve_left', 'cuff_right', 'cuff_left')}
ANCHORS = {}
FINGER_RADIUS = {'index': 0.0092, 'middle': 0.0096, 'ring': 0.0091, 'pinky': 0.0082, 'thumb': 0.0108}


def capsule_chain(bm, points, radii, segments=14):
    """Tapered cylinders between successive joints plus a sphere at every joint."""
    for (p0, r0), (p1, r1) in zip(zip(points, radii), zip(points[1:], radii[1:])):
        p0, p1 = Vector(p0), Vector(p1)
        axis = p1 - p0
        geom = bmesh.ops.create_cone(bm, cap_ends=True, segments=segments, radius1=r0, radius2=r1, depth=axis.length)
        verts = geom['verts']
        rot = Vector((0, 0, 1)).rotation_difference(axis.normalized()).to_matrix()
        bmesh.ops.rotate(bm, verts=verts, cent=(0, 0, 0), matrix=rot)
        bmesh.ops.translate(bm, verts=verts, vec=(p0 + p1) / 2)
    for p, r in zip(points, radii):
        geom = bmesh.ops.create_uvsphere(bm, u_segments=14, v_segments=10, radius=r)
        bmesh.ops.translate(bm, verts=geom['verts'], vec=Vector(p))


def ellipsoid(bm, centre, axes, half):
    """Ellipsoid with half-extents `half` along the orthonormal `axes` (x, y, z)."""
    geom = bmesh.ops.create_uvsphere(bm, u_segments=20, v_segments=14, radius=1.0)
    basis = Matrix((axes[0] * half[0], axes[1] * half[1], axes[2] * half[2])).transposed()
    for v in geom['verts']:
        v.co = basis @ v.co + Vector(centre)


def finish_organic(name, bm, material, voxel=0.0011, target_tris=3200):
    obj = hs.from_bmesh(name, bm, material)
    remesh = obj.modifiers.new('fuse', 'REMESH')
    remesh.mode = 'VOXEL'
    remesh.voxel_size = voxel
    smooth = obj.modifiers.new('soften', 'SMOOTH')
    smooth.factor = 0.6
    smooth.iterations = 4
    hs.apply_all(obj)
    faces = len(obj.data.polygons)
    decimate = obj.modifiers.new('budget', 'DECIMATE')
    decimate.ratio = min(1.0, target_tris / max(1, faces * 2))
    hs.apply_all(obj)
    hs.smooth(obj, 180)
    return obj


def right_hand():
    """Firing hand: palm on the back strap, fingers round the front onto the left
    face, index on the trigger, thumb along the left side under the selector."""
    bm = bmesh.new()
    grip_axis = Vector((0, 0.27, 0.96)).normalized()          # raked pistol grip, bottom to top
    across = Vector((1, 0, 0))
    ellipsoid(bm, (0.029, -0.024, -0.058), (grip_axis, Vector((0, 0.96, -0.27)), across), (0.046, 0.036, 0.014))
    for finger, z in (('middle', -0.040), ('ring', -0.062), ('pinky', -0.083)):
        r = FINGER_RADIUS[finger]
        yf = 0.026 - (-0.0095 - z) * 0.25
        pts = [(0.027, yf - 0.012, z), (0.012, yf + r + 0.004, z - 0.002), (-0.012, yf + r * 0.6, z - 0.004),
               (-0.024, yf - 0.006, z - 0.005), (-0.025, yf - 0.020, z - 0.005)]
        capsule_chain(bm, pts, [r * 1.05, r, r * 0.95, r * 0.9, r * 0.82])
    r = FINGER_RADIUS['index']
    capsule_chain(bm, [(0.026, 0.004, -0.018), (0.016, 0.030, -0.023), (0.009, 0.045, -0.027), (0.002, 0.049, -0.031), (-0.002, 0.046, -0.036)],
                  [r * 1.05, r, r * 0.95, r * 0.88, r * 0.8])
    r = FINGER_RADIUS['thumb']
    capsule_chain(bm, [(0.022, -0.040, -0.040), (0.008, -0.036, -0.016), (-0.016, -0.024, -0.012), (-0.024, -0.004, -0.010), (-0.024, 0.016, -0.009)],
                  [r * 1.3, r * 1.1, r, r * 0.92, r * 0.82])
    # Wrist into the forearm.
    capsule_chain(bm, [(0.031, -0.050, -0.072), (0.040, -0.085, -0.092)], [0.026, 0.028])
    return finish_organic('glove_right', bm, 'glove')


def left_hand():
    """Support hand under the handguard: palm up, fingers up the right face, thumb
    forward along the left face, which is the side the camera sees."""
    bm = bmesh.new()
    ellipsoid(bm, (-0.016, 0.424, -0.014), (Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))), (0.045, 0.041, 0.014))
    # Thenar pad: the thumb's muscular base reads as the hand's mass from the left.
    thumb_dir = Vector((0, 0.86, 0.5)).normalized()
    ellipsoid(bm, (-0.035, 0.430, -0.006), (Vector((1, 0, 0)), thumb_dir, Vector((1, 0, 0)).cross(thumb_dir)), (0.015, 0.027, 0.013))
    for finger, y in (('index', 0.452), ('middle', 0.432), ('ring', 0.412), ('pinky', 0.394)):
        r = FINGER_RADIUS[finger]
        length = {'index': 1.0, 'middle': 1.08, 'ring': 1.02, 'pinky': 0.85}[finger]
        pts = [(0.016, y, -0.006), (0.032, y, 0.004 + 0.012 * length), (0.035, y, 0.020 + 0.012 * length),
               (0.028, y, 0.040 + 0.006 * length), (0.016, y, 0.049 + 0.004 * length)]
        capsule_chain(bm, pts, [r * 1.05, r, r * 0.95, r * 0.9, r * 0.82])
    r = FINGER_RADIUS['thumb']
    capsule_chain(bm, [(-0.036, 0.420, -0.010), (-0.038, 0.442, 0.004), (-0.036, 0.464, 0.017), (-0.033, 0.484, 0.025), (-0.030, 0.500, 0.028)],
                  [0.0140, 0.0125, 0.0115, 0.0105, 0.0090])
    capsule_chain(bm, [(-0.048, 0.405, -0.020), (-0.070, 0.385, -0.032)], [0.025, 0.027])
    return finish_organic('glove_left', bm, 'glove')


def sleeve(name, wrist, elbow, r_wrist, r_elbow, material='sleeve'):
    """Tapered sleeve with soft folds, open at the elbow end, plus a ribbed cuff."""
    wrist, elbow = Vector(wrist), Vector(elbow)
    axis = elbow - wrist
    bm = bmesh.new()
    rings, segments = 18, 20
    rot = Vector((0, 0, 1)).rotation_difference(axis.normalized()).to_matrix()
    grid = []
    for i in range(rings + 1):
        t = i / rings
        ring = []
        for j in range(segments):
            a = 2 * math.pi * j / segments
            fold = 1.0 + 0.06 * math.sin(t * 19.0 + a * 2.0) * math.sin(a * 3.0 + t * 7.0) * min(1.0, t * 4.0)
            r = (r_wrist + (r_elbow - r_wrist) * t) * fold
            ring.append(bm.verts.new(wrist + rot @ Vector((r * math.cos(a), r * math.sin(a), axis.length * t))))
        grid.append(ring)
    for r0, r1 in zip(grid, grid[1:]):
        for j in range(segments):
            bm.faces.new((r0[j], r0[(j + 1) % segments], r1[(j + 1) % segments], r1[j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    obj = hs.from_bmesh(name, bm, material)
    hs.smooth(obj, 180)
    cuff = hs.lathe('cuff_' + name.split('_')[1], [(0.0, -0.012), (r_wrist * 1.06, -0.012), (r_wrist * 1.12, -0.006), (r_wrist * 1.12, 0.012), (0.0, 0.016)],
                    'glove', 24)
    cuff.matrix_world = Matrix.Translation(wrist) @ Vector((0, 1, 0)).rotation_difference(axis.normalized()).to_matrix().to_4x4()
    hs.apply_all(cuff)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    hs.smooth(cuff, 50)
    return [obj, cuff]


def build(reset=True):
    if reset:
        hs.reset_scene()
    for name, (colour, rough) in {'glove': ((0.030, 0.033, 0.030), 0.78), 'sleeve': ((0.026, 0.036, 0.043), 0.86)}.items():
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes['Principled BSDF']
        bsdf.inputs['Base Color'].default_value = (*colour, 1)
        bsdf.inputs['Roughness'].default_value = rough
    parts = [right_hand(), left_hand()]
    parts += sleeve('sleeve_right', (0.040, -0.088, -0.094), (0.150, -0.330, -0.200), 0.036, 0.058)
    parts += sleeve('sleeve_left', (-0.072, 0.383, -0.034), (-0.190, 0.140, -0.170), 0.034, 0.056)
    return parts, None


if __name__ == '__main__':
    build()
    meshes = [o for o in bpy.data.objects if o.type == 'MESH']
    print('HANDS objects=%d tris=%d' % (len(meshes), hs.triangles(meshes)), {o.name: hs.triangles([o]) for o in meshes})
