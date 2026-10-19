"""Hard-surface modelling toolkit for headless Blender (bpy as a Python module).

Coordinates: metres, Blender Z-up. Weapons are modelled with the barrel along +Y so
the glTF export (Y-up, -Z forward) lands on Godot's -Z barrel convention.
"""
import math
import bpy  # must precede bmesh when Blender runs as a Python module
import bmesh
from mathutils import Matrix, Vector

# ---------------------------------------------------------------- scene / materials

MATERIALS = {
    # name: base colour (linear), metallic, roughness
    'anodized': ((0.040, 0.043, 0.047), 0.70, 0.40),
    'steel': ((0.028, 0.029, 0.031), 1.0, 0.30),
    'polymer': ((0.105, 0.088, 0.064), 0.0, 0.62),  # muted earth-tone: the magazine
    'grip_polymer': ((0.040, 0.040, 0.043), 0.0, 0.74),  # graphite furniture: grip, stock, hand stop
    'rubber': ((0.018, 0.018, 0.019), 0.0, 0.86),
    'glass': ((0.015, 0.03, 0.026), 0.0, 0.04),
    'brass': ((0.42, 0.27, 0.08), 1.0, 0.32),
}


def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for name, (colour, metal, rough) in MATERIALS.items():
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes['Principled BSDF']
        bsdf.inputs['Base Color'].default_value = (*colour, 1)
        bsdf.inputs['Metallic'].default_value = metal
        bsdf.inputs['Roughness'].default_value = rough


def link(obj):
    bpy.context.collection.objects.link(obj)
    return obj


def from_bmesh(name, bm, material):
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = link(bpy.data.objects.new(name, mesh))
    obj.data.materials.append(bpy.data.materials[material])
    return obj


def select_only(obj):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def apply_all(obj):
    select_only(obj)
    for mod in list(obj.modifiers):
        bpy.ops.object.modifier_apply(modifier=mod.name)


def remove(obj):
    bpy.data.objects.remove(obj, do_unlink=True)


# ---------------------------------------------------------------- 2D profiles

def fillet(points, radii, segments=4):
    """Round the corners of a closed 2D polygon. radii: one value or one per corner."""
    if not isinstance(radii, (list, tuple)):
        radii = [radii] * len(points)
    out = []
    n = len(points)
    for i in range(n):
        p0, p1, p2 = Vector(points[i - 1]), Vector(points[i]), Vector(points[(i + 1) % n])
        r = radii[i]
        if r <= 0:
            out.append(tuple(p1))
            continue
        a, b = (p0 - p1), (p2 - p1)
        la, lb = a.length, b.length
        a.normalize(); b.normalize()
        angle = a.angle(b)
        if angle < 1e-4 or abs(angle - math.pi) < 1e-4:
            out.append(tuple(p1))
            continue
        d = min(r / math.tan(angle / 2), la * 0.49, lb * 0.49)
        start, end = p1 + a * d, p1 + b * d
        # Quadratic Bezier through the corner approximates the arc well for small radii.
        for s in range(segments + 1):
            t = s / segments
            q = start * (1 - t) ** 2 + p1 * 2 * t * (1 - t) + end * t * t
            out.append((q.x, q.y))
    return out


def extrude_profile(name, points, depth, material, axis='X', offset=0.0):
    """Extrude a closed 2D profile. axis='X': points are (y, z), depth along X.
    axis='Z': points are (x, y), depth along Z. axis='Y': points are (x, z)."""
    bm = bmesh.new()
    verts = []
    for u, v in points:
        if axis == 'X':
            co = (offset - depth / 2, u, v)
        elif axis == 'Z':
            co = (u, v, offset - depth / 2)
        else:
            co = (u, offset - depth / 2, v)
        verts.append(bm.verts.new(co))
    face = bm.faces.new(verts)
    shift = {'X': (depth, 0, 0), 'Z': (0, 0, depth), 'Y': (0, depth, 0)}[axis]
    geom = bmesh.ops.extrude_face_region(bm, geom=[face])['geom']
    bmesh.ops.translate(bm, verts=[g for g in geom if isinstance(g, bmesh.types.BMVert)], vec=shift)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return from_bmesh(name, bm, material)


def silhouette(name, side, plan, material, width=0.2, height=0.6):
    """Two-view modelling: side profile (y, z) extruded across X intersected with the
    plan profile (x, y) extruded along Z. Gives tapers and chamfers in both views."""
    body = extrude_profile(name, side, width, material, 'X')
    cutter = extrude_profile(name + '_plan', plan, height, material, 'Z')
    boolean(body, cutter, 'INTERSECT')
    return body


# ---------------------------------------------------------------- primitives

def box(name, centre, size, material='steel'):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=size, verts=bm.verts)
    bmesh.ops.translate(bm, vec=centre, verts=bm.verts)
    return from_bmesh(name, bm, material)


def cylinder(name, start, end, radius, material='steel', segments=32, radius_end=None):
    """Cylinder/cone between two points."""
    start, end = Vector(start), Vector(end)
    axis = end - start
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segments, radius1=radius,
                          radius2=radius if radius_end is None else radius_end, depth=axis.length)
    rot = Vector((0, 0, 1)).rotation_difference(axis.normalized()).to_matrix()
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=rot)
    bmesh.ops.translate(bm, verts=bm.verts, vec=(start + end) / 2)
    return from_bmesh(name, bm, material)


def lathe(name, profile_rz, material, segments=40, axis_y=True, centre=(0, 0, 0)):
    """Revolve a (radius, position) profile around the Y axis (barrels, muzzle devices)."""
    bm = bmesh.new()
    rings = []
    for r, y in profile_rz:
        ring = []
        for s in range(segments):
            a = 2 * math.pi * s / segments
            ring.append(bm.verts.new((centre[0] + r * math.cos(a), centre[1] + y, centre[2] + r * math.sin(a))))
        rings.append(ring)
    for r0, r1 in zip(rings, rings[1:]):
        for s in range(segments):
            bm.faces.new((r0[s], r0[(s + 1) % segments], r1[(s + 1) % segments], r1[s]))
    bm.faces.new(rings[0][::-1])
    bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return from_bmesh(name, bm, material)


# ---------------------------------------------------------------- operations

def boolean(target, cutter, operation='DIFFERENCE', keep=False, keep_material=False):
    """EXACT boolean. Cut faces take the target's first material unless keep_material."""
    if not keep_material and operation != 'UNION' and target.data.materials:
        cutter.data.materials.clear()
        cutter.data.materials.append(target.data.materials[0])
    mod = target.modifiers.new('bool', 'BOOLEAN')
    mod.object = cutter
    mod.operation = operation
    mod.solver = 'EXACT'
    mod.use_hole_tolerant = True
    apply_all(target)
    if not keep:
        remove(cutter)
    return target


def cut(target, *cutters):
    for c in cutters:
        boolean(target, c)
    return target


def join(objects, name=None):
    objects = [o for o in objects if o is not None]
    select_only(objects[0])
    for o in objects[1:]:
        o.select_set(True)
    bpy.ops.object.join()
    if name:
        objects[0].name = name
    return objects[0]


def array_join(make, count, step, name):
    parts = []
    for i in range(count):
        parts.append(make(i, Vector(step) * i))
    return join(parts, name)


def finish(obj, bevel=0.0008, segments=2, angle=30, weighted=True):
    """Bevel sharp edges, harden normals and smooth shading for a machined look."""
    if bevel > 0:
        mod = obj.modifiers.new('bevel', 'BEVEL')
        mod.width = bevel
        mod.segments = segments
        mod.limit_method = 'ANGLE'
        mod.angle_limit = math.radians(angle)
        mod.miter_outer = 'MITER_ARC'
        mod.harden_normals = True
        mod.use_clamp_overlap = True
        apply_all(obj)
    for poly in obj.data.polygons:
        poly.use_smooth = True
    if hasattr(obj.data, 'set_sharp_from_angle'):
        obj.data.set_sharp_from_angle(angle=math.radians(angle))
    if weighted:
        wn = obj.modifiers.new('weighted', 'WEIGHTED_NORMAL')
        wn.keep_sharp = True
        wn.weight = 50
        apply_all(obj)
    return obj


def smooth(obj, angle=40):
    for poly in obj.data.polygons:
        poly.use_smooth = True
    if hasattr(obj.data, 'set_sharp_from_angle'):
        obj.data.set_sharp_from_angle(angle=math.radians(angle))
    return obj


def triangles(objects):
    return sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in objects)
