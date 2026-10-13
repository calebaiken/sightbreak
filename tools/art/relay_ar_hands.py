"""First-person gloved hands and sleeves posed on the Relay AR (original geometry).

Same space as relay_ar.py (metres, Blender Z up, barrel +Y). Each hand is built from
flattened ellipsoid segments: palm slabs, a thenar mass, and fingers of three phalanges
whose overlaps make the knuckles. Segments are placed through explicit joints around
the real grip and handguard sections, fused by a voxel remesh, smoothed and decimated
to the mobile budget. The sleeves taper from the wrist to the elbow with an oval
section, a seam and gathered cloth behind the cuff; each wrist has a flared cuff and a
strap. Forearms run toward the elbows of the viewmodel pose in weapon_model.gd, so they
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
GROUPS = {'hands': ('glove_right', 'glove_left', 'sleeve_right', 'sleeve_left', 'cuff_right', 'cuff_left',
                    'strap_right', 'strap_left')}
ANCHORS = {}
X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))
GRIP_AXIS = Vector((0, 0.27, 0.96)).normalized()      # raked pistol grip, bottom to top
GRIP_NORMAL = Vector((0, 0.96, -0.27)).normalized()   # perpendicular, toward the muzzle
# Finger widths (m) of the gloved hand; thickness is 0.88 of width.
FINGER_WIDTH = {'index': 0.0190, 'middle': 0.0195, 'ring': 0.0188, 'pinky': 0.0166}
# Per-phalanx width factors from the palm outward (the first is the part inside the palm).
PHALANX = (1.08, 1.04, 0.98, 0.90, 0.80)


# ------------------------------------------------------------------ primitives

def blob(bm, centre, axes, half, u=18, v=12):
    """Ellipsoid with half-extents `half` along the orthonormal `axes`."""
    geom = bmesh.ops.create_uvsphere(bm, u_segments=u, v_segments=v, radius=1.0)
    basis = Matrix((axes[0] * half[0], axes[1] * half[1], axes[2] * half[2])).transposed()
    for vert in geom['verts']:
        vert.co = basis @ vert.co + Vector(centre)


def segment(bm, p0, p1, width, thick, around, pad=0.0016):
    """Flattened ellipsoid between two joints. Its thin axis points away from `around`
    (the object being gripped), so a wrapped finger is thin radially and wide along it."""
    p0, p1 = Vector(p0), Vector(p1)
    axis = p1 - p0
    length = axis.length
    f = axis / length
    mid = (p0 + p1) / 2
    t = mid - Vector(around)
    t -= f * t.dot(f)
    if t.length < 1e-6:
        t = f.orthogonal()
    t.normalize()
    w = f.cross(t).normalized()
    blob(bm, mid, (f, w, t), (length / 2 + pad, width / 2, thick / 2))


def knuckle(bm, p, width, thick):
    geom = bmesh.ops.create_uvsphere(bm, u_segments=14, v_segments=10, radius=1.0)
    r = (width + thick) / 4 * 1.07
    for vert in geom['verts']:
        vert.co = vert.co * r + Vector(p)


def digit(bm, joints, width, around, widths=PHALANX, thickness=0.88):
    """A finger or thumb: one flattened segment per pair of joints and a bump at every
    joint but the first, which is where the digit joins the palm."""
    for i in range(len(joints) - 1):
        w = width * widths[min(i, len(widths) - 1)]
        segment(bm, joints[i], joints[i + 1], w, w * thickness, around)
    for i in range(1, len(joints)):
        w = width * widths[min(i - 1, len(widths) - 1)] * (1.0 if i < len(joints) - 1 else 0.9)
        knuckle(bm, joints[i], w, w * thickness)


def finish_organic(name, bm, material, voxel=0.0011, target_tris=3500):
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


# ------------------------------------------------------------------ hands

def right_hand():
    """Firing hand on the pistol grip: palm and heel on the back strap and right face,
    fingers wrapped round the front onto the left face, index along the right of the
    lower receiver and onto the trigger, thumb forward along the left side."""
    bm = bmesh.new()
    blob(bm, (0.030, -0.022, -0.058), (GRIP_AXIS, GRIP_NORMAL, X), (0.047, 0.036, 0.0125))
    blob(bm, (0.028, -0.031, -0.092), (GRIP_AXIS, GRIP_NORMAL, X), (0.021, 0.027, 0.0135))   # heel of the hand
    blob(bm, (0.027, -0.015, -0.026), (GRIP_AXIS, GRIP_NORMAL, X), (0.023, 0.026, 0.0140))   # web under the thumb
    for finger, z in (('middle', -0.050), ('ring', -0.070), ('pinky', -0.088)):
        yf = 0.026 + (z + 0.0095) * 0.258               # front edge of the raked grip at this height
        joints = [(0.027, yf - 0.012, z), (0.021, yf + 0.006, z - 0.001), (0.0, yf + 0.0093, z - 0.002),
                  (-0.0215, yf + 0.0062, z - 0.003), (-0.024, yf - 0.012, z - 0.003), (-0.0245, yf - 0.024, z - 0.003)]
        digit(bm, joints, FINGER_WIDTH[finger], (0, yf - 0.018, z), PHALANX + (0.74,))
    digit(bm, [(0.028, 0.0, -0.016), (0.0245, 0.022, -0.020), (0.0125, 0.0385, -0.0265), (0.0, 0.0405, -0.027)],
          FINGER_WIDTH['index'], (0.0, 0.020, -0.020))
    digit(bm, [(0.022, -0.040, -0.040), (0.009, -0.036, -0.018), (-0.016, -0.026, -0.013), (-0.0245, -0.006, -0.011), (-0.0245, 0.014, -0.0095)],
          0.0235, (0.02, -0.01, -0.012), (1.15, 1.05, 0.95, 0.84))
    # Wrist into the forearm.
    segment(bm, (0.031, -0.050, -0.072), (0.040, -0.088, -0.094), 0.052, 0.042, (0.0, -0.05, -0.05))
    return finish_organic('glove_right', bm, 'glove')


def left_hand():
    """Support hand under the handguard (C clamp): palm and heel underneath, four fingers
    up the right face to the top, a thick thumb along the left face, which is the side
    the camera sees."""
    bm = bmesh.new()
    blob(bm, (-0.014, 0.425, -0.014), (X, Y, Z), (0.045, 0.042, 0.0135))
    blob(bm, (-0.046, 0.404, -0.017), (X, Y, Z), (0.021, 0.027, 0.0150))                    # heel at the wrist
    guard = (0.0, 0.0, 0.027)
    guard_mid = (0.0, 0.45, 0.027)
    for finger, y, reach in (('index', 0.455, 1.0), ('middle', 0.435, 1.0), ('ring', 0.415, 1.0), ('pinky', 0.396, 0.78)):
        joints = [(0.012, y, -0.014), (0.0245, y, -0.0045), (0.0325, y, 0.015), (0.0325, y, 0.034), (0.0275, y, 0.0455)]
        if reach < 1.0:
            joints = joints[:4]
        digit(bm, joints, FINGER_WIDTH[finger], (guard[0], y, guard[2]), PHALANX + (0.74,))
    # Thumb: thenar mass, proximal and distal phalanges along the left face.
    digit(bm, [(-0.040, 0.409, -0.015), (-0.0385, 0.441, -0.004), (-0.0362, 0.466, 0.006), (-0.0338, 0.486, 0.0125)],
          0.0305, guard_mid, (1.0, 0.90, 0.82, 0.74), thickness=0.90)
    # Wrist into the forearm.
    segment(bm, (-0.047, 0.405, -0.020), (-0.070, 0.385, -0.032), 0.052, 0.042, guard_mid)
    return finish_organic('glove_left', bm, 'glove')


# ------------------------------------------------------------------ cloth and trim

def sleeve(side, wrist, elbow, r_wrist, r_elbow, flat_angle):
    """Tapered sleeve: oval section, gathered cloth behind the cuff, soft folds and a
    seam. Capped at both ends so it is watertight."""
    wrist, elbow = Vector(wrist), Vector(elbow)
    axis = elbow - wrist
    rot = Vector((0, 0, 1)).rotation_difference(axis.normalized()).to_matrix()
    bm = bmesh.new()
    rings, segments = 20, 18
    grid = []
    for i in range(rings + 1):
        t = i / rings
        base = r_wrist + (r_elbow - r_wrist) * t ** 0.85
        gathered = 1.0 + 0.11 * math.exp(-((t - 0.04) / 0.05) ** 2)
        ring = []
        for j in range(segments):
            a = 2 * math.pi * j / segments
            oval = 1.0 + 0.075 * math.cos(2 * (a - flat_angle))
            fold = 1.0 + 0.040 * math.sin(t * 30.0 + 2.5 * a) * math.sin(3 * a + t * 11.0) * min(1.0, t * 8.0)
            diff = (a - flat_angle - math.pi / 2 + math.pi) % (2 * math.pi) - math.pi
            seam = 1.0 + 0.045 * math.exp(-(diff / 0.11) ** 2)
            r = base * gathered * oval * fold * seam
            ring.append(bm.verts.new(wrist + rot @ Vector((r * math.cos(a), r * math.sin(a), axis.length * t))))
        grid.append(ring)
    for r0, r1 in zip(grid, grid[1:]):
        for j in range(segments):
            bm.faces.new((r0[j], r0[(j + 1) % segments], r1[(j + 1) % segments], r1[j]))
    bm.faces.new(grid[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    obj = hs.from_bmesh('sleeve_' + side, bm, 'sleeve')
    hs.smooth(obj, 180)
    return obj


def ring(name, wrist, axis, radius, y0, y1, material, flare=1.0):
    """A solid ring about `axis`, from y0 to y1 along it, flaring to `flare` x radius."""
    profile = [(0.0, y0), (radius, y0), (radius * flare, (y0 + y1) / 2), (radius * flare, y1), (radius, y1 + 0.002), (0.0, y1 + 0.002)]
    obj = hs.lathe(name, profile, material, 28)
    obj.matrix_world = Matrix.Translation(Vector(wrist)) @ Y.rotation_difference(Vector(axis).normalized()).to_matrix().to_4x4()
    hs.apply_all(obj)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    hs.smooth(obj, 50)
    return obj


def wrist_trim(side, wrist, elbow, r_wrist):
    axis = Vector(elbow) - Vector(wrist)
    cuff = ring('cuff_' + side, wrist, axis, r_wrist * 1.06, -0.012, 0.024, 'glove', flare=1.07)
    strap = ring('strap_' + side, wrist, axis, r_wrist * 1.07, 0.003, 0.0135, 'strap', flare=1.07)
    return [cuff, strap]


def materials():
    for name, (colour, rough) in {'glove': ((0.022, 0.021, 0.020), 0.88), 'sleeve': ((0.016, 0.022, 0.027), 0.92),
                                  'strap': ((0.20, 0.15, 0.06), 0.72)}.items():
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes['Principled BSDF']
        bsdf.inputs['Base Color'].default_value = (*colour, 1)
        bsdf.inputs['Roughness'].default_value = rough


def build(reset=True):
    if reset:
        hs.reset_scene()
    materials()
    parts = [right_hand(), left_hand()]
    right_wrist, right_elbow = (0.040, -0.088, -0.094), (0.293, -0.645, -0.338)
    left_wrist, left_elbow = (-0.072, 0.383, -0.034), (-0.505, -0.031, -0.311)
    parts.append(sleeve('right', right_wrist, right_elbow, 0.034, 0.075, 0.4))
    parts.append(sleeve('left', left_wrist, left_elbow, 0.033, 0.074, -0.4))
    parts += wrist_trim('right', right_wrist, right_elbow, 0.034)
    parts += wrist_trim('left', left_wrist, left_elbow, 0.033)
    return parts, None


if __name__ == '__main__':
    build()
    meshes = [o for o in bpy.data.objects if o.type == 'MESH']
    print('HANDS objects=%d tris=%d' % (len(meshes), hs.triangles(meshes)), {o.name: hs.triangles([o]) for o in meshes})
