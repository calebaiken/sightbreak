"""Box-modelled glove cage: the low-poly glove built the way a hand is blocked out by an artist, instead of by QuadriFlow.

A palm block (a cuff-to-knuckle tube of ten-vertex rings), four finger tubes and a thumb tube extruded from its faces with an
edge loop either side of every joint, subdivided once and projected onto the glove's signed distance field. The topology is what
the retopology of a voxel mesh cannot give: the loops run round the fingers and sit at the knuckles, so a finger bends at a
loop, the silhouette of a fingertip is a ring of eight and not whatever the quad flow happened to be, and a joint's crease lies
along edges (the bake still carries the detail from the high-poly glove).

Hand-local frame (the right hand): +Y toward the fingers, +Z the back of the hand, +X toward the little finger (the thumb is at -X).
The joints come from relay_ar_arms.py (the same ones the rig's bones are built from).

    build_cage() -> (vertices, faces)                  the cage: numpy vertices, lists of vertex indices (mostly quads)
    glove_low_object(name, subdivide=1)                a Blender mesh object: the cage subdivided and projected onto the glove
"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import relay_ar_arms as arms  # noqa: E402

try:
    import bmesh  # noqa: E402
    from mathutils import Matrix, Vector  # noqa: E402
except ImportError:   # the numeric parts can be used without Blender
    bmesh = None

X = np.array((1.0, 0.0, 0.0))
Y = np.array((0.0, 1.0, 0.0))
Z = np.array((0.0, 0.0, 1.0))

# Palm block rings: (y, centre x, centre z, half width, half thickness). The cuff runs from under the sleeve hem to the wrist, the palm
# from the wrist to the plane the fingers leave from (a little behind the knuckles).
PALM_RINGS = (
    (-0.0600, 0.0000, -0.0020, 0.0335, 0.0262),
    (-0.0400, 0.0000, -0.0015, 0.0338, 0.0264),
    (-0.0200, 0.0000, -0.0010, 0.0335, 0.0258),
    (0.0000, 0.0005, -0.0008, 0.0330, 0.0235),
    (0.0160, 0.0015, -0.0035, 0.0345, 0.0200),
    (0.0380, 0.0022, -0.0045, 0.0370, 0.0178),
    (0.0600, 0.0028, -0.0040, 0.0385, 0.0168),
    (0.0790, 0.0030, -0.0030, 0.0388, 0.0158),
)
FINGER_ORDER = ('index', 'middle', 'ring', 'pinky')
ACROSS = 4          # quads across the palm's front plane (one per finger)


def _ring_positions(joints, lengths, radii, tip_radius):
    """Rings along a finger from just behind the knuckle to the tip: (position along the chain in metres from the MCP, radius scale
    knuckle bulge). Two loops either side of every joint, one at the middle of each phalanx."""
    l0, l1, l2 = lengths
    j1, j2, j3 = l0, l0 + l1, l0 + l1 + l2
    rings = [(-0.0075, 1.00), (-0.0020, 1.04), (0.0040, 1.06), (0.0100, 1.0), (0.5 * l0, 0.97),
             (j1 - 0.0070, 0.99), (j1 - 0.0015, 1.03), (j1 + 0.0035, 1.03), (j1 + 0.0090, 0.99),
             (0.5 * (j1 + j2), 0.96), (j2 - 0.0060, 0.97), (j2 - 0.0015, 1.02), (j2 + 0.0035, 1.00),
             (0.5 * (j2 + j3), 0.93), (j3 - 0.0030, 0.92), (j3 + 0.0030, 0.80), (j3 + tip_radius * 0.80, 0.50), (j3 + tip_radius * 0.97, 0.18)]
    return rings


def _along(joints, distance):
    """Position, direction and segment index at `distance` metres along the finger's chain from its first joint."""
    remaining = distance
    for i in range(3):
        seg = joints[i + 1] - joints[i]
        length = float(np.linalg.norm(seg))
        if remaining <= length or i == 2:
            d = seg / length
            return joints[i] + d * remaining, d, i
        remaining -= length
    raise AssertionError


def _radius_at(radii, lengths, distance):
    """Half-width at `distance` along the chain (linear between the joints' radii)."""
    marks = (0.0, lengths[0], lengths[0] + lengths[1], sum(lengths))
    return float(np.interp(distance, marks, radii))


def build_cage():
    """The box-modelled cage (palm block, four fingers, thumb). Needs Blender's bmesh."""
    assert bmesh is not None, 'build_cage needs Blender (bmesh)'
    bm = bmesh.new()
    # --- the palm block: rings of ten vertices (five on the back, five on the palm side), joined in quads
    rings = []
    for (y, cx, cz, hw, ht) in PALM_RINGS:
        top = [bm.verts.new((cx - hw + 2 * hw * k / ACROSS, y, cz + ht)) for k in range(ACROSS + 1)]
        bottom = [bm.verts.new((cx - hw + 2 * hw * k / ACROSS, y, cz - ht)) for k in range(ACROSS + 1)]
        rings.append((top, bottom))
    for a, b in zip(rings[:-1], rings[1:]):
        for k in range(ACROSS):
            bm.faces.new((a[0][k], a[0][k + 1], b[0][k + 1], b[0][k]))      # back of the hand
            bm.faces.new((a[1][k + 1], a[1][k], b[1][k], b[1][k + 1]))      # palm side
        bm.faces.new((a[0][0], b[0][0], b[1][0], a[1][0]))                 # radial side (the thumb's)
        bm.faces.new((a[0][ACROSS], a[1][ACROSS], b[1][ACROSS], b[0][ACROSS]))   # ulnar side
    first = rings[0]
    bm.faces.new([*first[0], *reversed(first[1])][::-1])                   # the cuff's open end, closed (it lies under the sleeve)
    last = rings[-1]
    front = [bm.faces.new((last[0][k], last[1][k], last[1][k + 1], last[0][k + 1])) for k in range(ACROSS)]   # the finger bases
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    # make sure the finger-base faces face forward (+Y)
    for f in front:
        if f.normal.y < 0:
            f.normal_flip()
    thumb_face = None
    # the radial-side face of the ring gap the thumb leaves from (between y = 0.0 and 0.038)
    for f in bm.faces:
        c = f.calc_center_median()
        if abs(f.normal.x) > 0.8 and f.normal.x < 0 and 0.0 < c.y < 0.04:
            thumb_face = f
    assert thumb_face is not None
    # --- fingers
    for name, face in zip(FINGER_ORDER, front):
        _extrude_finger(bm, face, name)
    _extrude_thumb(bm, thumb_face)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    verts = np.array([tuple(v.co) for v in bm.verts])
    index = {v: i for i, v in enumerate(bm.verts)}
    faces = [[index[v] for v in f.verts] for f in bm.faces]
    bm.free()
    return verts, faces


def _corner_signs(face_center, face_axes, vertex):
    off = np.asarray(vertex) - face_center
    return tuple(1.0 if float(np.dot(off, a)) >= 0 else -1.0 for a in face_axes)


def _extrude_tube(bm, face, ring_specs, corner_axes):
    """Extrude `face` through the rings; each spec is (centre, direction, up, half_side, half_up). The face's corners keep their
    (side, up) signs. Returns the final ring's face."""
    face_center = np.array(tuple(face.calc_center_median()))
    sign_of = {v: _corner_signs(face_center, corner_axes, tuple(v.co)) for v in face.verts}
    current = face
    for centre, d, up, hs, hu in ring_specs:
        ret = bmesh.ops.extrude_face_region(bm, geom=[current])
        new_verts = [e for e in ret['geom'] if isinstance(e, bmesh.types.BMVert)]
        new_set = set(new_verts)
        new_face = next(e for e in ret['geom'] if isinstance(e, bmesh.types.BMFace) and set(e.verts) == new_set)
        # map each new vertex to its source corner (the extruded copy sits on the old position)
        old_verts = list(current.verts)
        s = np.cross(d, up)
        s /= np.linalg.norm(s)
        u = np.cross(s, d)
        for nv in new_verts:
            src = min(old_verts, key=lambda ov: (ov.co - nv.co).length)
            sx, su = sign_of.get(src, (1.0, 1.0))
            nv.co = Vector(tuple(np.asarray(centre) + s * (sx * hs) + u * (su * hu)))
            sign_of[nv] = (sx, su)
        bmesh.ops.delete(bm, geom=[current], context='FACES_ONLY')
        current = new_face
    return current


def _extrude_finger(bm, face, name):
    joints, ups = arms.finger_chain(name)
    joints = [np.asarray(j, dtype=np.float64) for j in joints]
    lengths = arms.LENGTHS[name]
    radii = arms.RADII[name]
    tip_radius = radii[3]
    specs = []
    for distance, scale in _ring_positions(joints, lengths, radii, tip_radius):
        beyond = distance > sum(lengths)
        centre, d, seg = _along(joints, distance if distance >= 0 else 0.0)
        if distance < 0:
            centre = joints[0] + (joints[1] - joints[0]) / lengths[0] * distance
            d = (joints[1] - joints[0]) / lengths[0]
        r = _radius_at(radii, lengths, min(max(distance, 0.0), sum(lengths))) * scale
        if beyond:
            r = tip_radius * scale
        up = np.asarray(ups[min(seg, 2)])
        up = up - d * float(np.dot(up, d))
        up /= np.linalg.norm(up)
        specs.append((centre, d, up, r, r * 0.88))
    final = _extrude_tube(bm, face, specs, (X, Z))
    bmesh.ops.pointmerge(bm, verts=list(final.verts), merge_co=final.calc_center_median())


def _extrude_thumb(bm, face):
    joints, ups = arms.thumb_chain()
    joints = [np.asarray(j, dtype=np.float64) for j in joints]
    lengths = arms.THUMB_LENGTHS
    radii = arms.THUMB_RADII
    l0, l1, l2 = lengths
    j1, j2, j3 = l0, l0 + l1, l0 + l1 + l2
    # The thumb's first joint (the carpometacarpal one) lies inside the palm block: the tube leaves the palm's radial face about
    # 25 mm along the chain, and the loops start there (earlier ones would lie inside the palm and kink the base of the thumb).
    marks = [(0.0250, 1.12), (0.0310, 1.08), (j1 - 0.0070, 1.04), (j1 - 0.0010, 1.04), (j1 + 0.0050, 1.0), (0.5 * (j1 + j2), 0.97),
             (j2 - 0.0050, 0.97), (j2 + 0.0020, 1.0), (0.5 * (j2 + j3), 0.94), (j3 - 0.0020, 0.92), (j3 + 0.0030, 0.80),
             (j3 + radii[3] * 0.80, 0.50), (j3 + radii[3] * 0.97, 0.18)]
    specs = []
    for distance, scale in marks:
        beyond = distance > j3
        centre, d, seg = _along(joints, max(distance, 0.0))
        if distance < 0:
            d0 = (joints[1] - joints[0]) / lengths[0]
            centre = joints[0] + d0 * distance
            d = d0
        r = (radii[3] if beyond else _radius_at(radii, lengths, min(max(distance, 0.0), j3))) * scale
        up = np.asarray(ups[min(seg, 2)])
        up = up - d * float(np.dot(up, d))
        up /= np.linalg.norm(up)
        specs.append((centre, d, up, r, r * 0.92))
    # the thumb leaves a radial-side face, whose corners are (+-y, +-z): map them as (side, up) with the face's own axes
    final = _extrude_tube(bm, face, specs, (Y, Z))
    bmesh.ops.pointmerge(bm, verts=list(final.verts), merge_co=final.calc_center_median())


def project_to_surface(points, distance, iterations=10, step=0.85, eps=0.0004):
    """Move points onto the zero level of a signed distance function by gradient steps (the function takes an (N, 3) array)."""
    p = np.asarray(points, dtype=np.float64).copy()
    for _ in range(iterations):
        d = distance(p)
        g = np.stack([(distance(p + e * eps) - distance(p - e * eps)) / (2 * eps) for e in np.eye(3)], axis=1)
        norm = np.maximum(np.linalg.norm(g, axis=1, keepdims=True), 1e-9)
        p -= step * d[:, None] * g / norm
    return p


def glove_low_object(name='glove_low', subdivide=1, shapes=None, smooth_passes=2):
    """The low-poly glove: cage, one level of Catmull-Clark, projected onto the glove's (plain) signed distance field, relaxed a
    little. A Blender mesh object in the hand-local frame."""
    import bpy
    verts, faces = build_cage()
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(map(float, v)) for v in verts], [], [tuple(f) for f in faces])
    me.update()
    obj = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    if subdivide:
        mod = obj.modifiers.new('subd', 'SUBSURF')
        mod.levels = mod.render_levels = subdivide
        mod.subdivision_type = 'CATMULL_CLARK'
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.ops.object.modifier_apply(modifier=mod.name)
    if shapes is None:
        full = arms.glove_shapes()
        shapes = ([(shape, k) for shape, k in full[0] if shape.region != 'seam'], full[1])   # the piping is bake detail, not mesh
    pts = np.array([tuple(v.co) for v in obj.data.vertices])
    pts = project_to_surface(pts, lambda P: arms.glove_distance(P, shapes))
    for v, p in zip(obj.data.vertices, pts):
        v.co = tuple(float(c) for c in p)
    # a light relaxation along the surface keeps the projection from bunching the quads (the SDF's own detail is in the normal map)
    if smooth_passes:
        mod = obj.modifiers.new('relax', 'SMOOTH')
        mod.factor, mod.iterations = 0.25, smooth_passes
        bpy.ops.object.modifier_apply(modifier=mod.name)
        pts = np.array([tuple(v.co) for v in obj.data.vertices])
        pts = project_to_surface(pts, lambda P: arms.glove_distance(P, shapes), iterations=4)
        for v, p in zip(obj.data.vertices, pts):
            v.co = tuple(float(c) for c in p)
    for poly in obj.data.polygons:
        poly.use_smooth = True
    return obj
