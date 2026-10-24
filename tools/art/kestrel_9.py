"""Kestrel 9 — original compact 9 mm sidearm for SIGHTBREAK's first-person view.

Built entirely in headless Blender from code (no third-party meshes). Blender axes:
X right, Y forward (muzzle; exports to Godot -Z), Z up. Metres. Bore axis at x = 0,
z = BORE (same bore height as the Relay AR). Slide rear face at y = 0.

Design (concept 1 with the art director's borrowings): faceted hex-section slide in dark
anodised metal over an angular graphite frame, two square-gated sight teeth over a clean
12 mm top flat, a slide that overhangs a raked chin like a beak, an open square guard with a
hooked front strut, a 17 degree grip rake shared with the Relay AR (grip, magazine and the
stadium cocking slots all lean the same way), a tan squared magazine foot, a hexagonal ejection
port that shows the chamber block and extractor, and a 3-slot mini-rail under the dust cover.

Object naming is the integration contract read by the game:
  paint_slide   takes the cosmetic finish
  grip          the whole graphite frame (stippled by the bake)
  magazine      origin at its seated top centre; second material 'brass' = the top round
  muzzle        empty at the muzzle crown
  ejection      empty at the ejection port
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
import bmesh  # noqa: E402
from mathutils import Vector  # noqa: E402
import hardsurface as hs  # noqa: E402

BORE = 0.025
TAN = math.tan(math.radians(17.0))          # the 17 degree rake rule shared with the Relay AR
SLIDE_Y1 = 0.176                            # slide front face
SLIDE_Z0, SLIDE_Z1 = 0.0105, 0.0405         # slide underside / top flat
MUZZLE_Y = 0.180                            # collar crown
DECK = 0.0092                               # outer strips of the frame under the slide (1.3 mm parting gap)
LEDGE = (-0.0140, -0.0097, 0.0240, 0.0580, 0.0030, 0.0105)    # left thumb ledge cutter (x0, x1, y0, y1, z0, z1)
PLATEAU = 0.0100                            # the central plateau the slide rails ride just above (0.5 mm)
GRIP_DEPTH = 0.0425                         # horizontal frontstrap-to-backstrap depth
FRAME_BOTTOM = -0.0873
FOOT_TOP, FOOT_BOTTOM = -0.0885, -0.0980    # 10 mm tall tan foot, 1.2 mm of clearance under the frame

# Game mesh groups (export.py). Each group is one draw; parts not listed join 'body'.
GROUPS = {
    'paint_slide': ('paint_slide',),
    'grip': ('grip',),
    'magazine': ('magazine',),
}
# Hand anchors for the first-person rig: centre of the firing grip at mid height, and the support
# palm and fingers around the frontstrap below the guard.
ANCHORS = {
    'grip_hand': (0.0, 0.021, -0.052),
    'support_hand': (0.0, 0.040, -0.046),
}


# ------------------------------------------------------------ small helpers

def yb(z):
    """Backstrap line (y) at height z: raked 17 degrees, top forward."""
    return -0.0105 + TAN * (z + 0.090)


def yf(z):
    return yb(z) + GRIP_DEPTH


def swell(z):
    """Palm swell: the backstrap bulges back up to 3.5 mm around z = -0.050."""
    return 0.0035 * max(0.0, 1.0 - ((z + 0.050) / 0.032) ** 2)


def mag_yc(z):
    """Magazine centre line (y) at height z; passes through the seated top centre."""
    return 0.0407 + TAN * (z - 0.0095)


def fil(points, setback, segments=2):
    """hs.fillet driven by the setback (tangent length) instead of the radius, so shallow corners
    round as much as sharp ones do."""
    n = len(points)
    if not isinstance(setback, (list, tuple)):
        setback = [setback] * n
    radii = []
    for i in range(n):
        p0, p1, p2 = Vector(points[i - 1]), Vector(points[i]), Vector(points[(i + 1) % n])
        angle = (p0 - p1).angle(p2 - p1)
        if setback[i] <= 0 or angle < 1e-4 or abs(angle - math.pi) < 1e-4:
            radii.append(0.0)
        else:
            radii.append(setback[i] * math.tan(angle / 2))
    return hs.fillet(points, radii, segments)


def capsule(p0, p1, r, n=4):
    """Stadium outline between two centres, as a polygon."""
    p0, p1 = Vector(p0), Vector(p1)
    d = (p1 - p0).normalized()
    nrm = Vector((-d.y, d.x))
    pts = []
    for i in range(n + 1):
        t = math.pi * i / n
        pts.append(tuple(p1 + (d * math.sin(t) + nrm * math.cos(t)) * r))
    for i in range(n + 1):
        t = math.pi * i / n
        pts.append(tuple(p0 - (d * math.sin(t) + nrm * math.cos(t)) * r))
    return pts


def offset_poly(points, d):
    """Miter offset of a convex polygon (d > 0 grows it)."""
    n = len(points)
    P = [Vector(p) for p in points]
    area = sum(P[i].x * P[(i + 1) % n].y - P[(i + 1) % n].x * P[i].y for i in range(n)) / 2
    sgn = 1.0 if area > 0 else -1.0
    out = []
    for i in range(n):
        e1 = (P[i] - P[i - 1]).normalized()
        e2 = (P[(i + 1) % n] - P[i]).normalized()
        n1, n2 = Vector((e1.y, -e1.x)) * sgn, Vector((e2.y, -e2.x)) * sgn
        out.append(tuple(P[i] + (n1 + n2) * (d / (1.0 + n1.dot(n2)))))
    return out


def cutter(name, outline, rings, axis='X', material='steel'):
    """A cutting tool made of stacked outlines: rings = [(position along the axis, offset)]. A growing offset
    towards the surface gives the cut a true 45 degree chamfer on its rim, without a bevel modifier."""
    bm = bmesh.new()
    stacks = []
    for pos, d in rings:
        pts = offset_poly(outline, d) if d else outline
        stacks.append([bm.verts.new((pos, u, v) if axis == 'X' else (u, pos, v)) for u, v in pts])
    n = len(outline)
    for a, b in zip(stacks, stacks[1:]):
        for k in range(n):
            bm.faces.new((a[k], a[(k + 1) % n], b[(k + 1) % n], b[k]))
    bm.faces.new(stacks[0][::-1])
    bm.faces.new(stacks[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return hs.from_bmesh(name, bm, material)


def span_box(name, x0, x1, y0, y1, z0, z1, material='steel'):
    return hs.box(name, ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), (x1 - x0, y1 - y0, z1 - z0), material)


def lathe(name, profile, material, segments=24, centre=(0.0, 0.0, 0.0)):
    """Revolve (radius, y) around the Y axis. A radius of zero becomes one apex vertex, so no
    degenerate faces; open ends get proper n-gon caps."""
    bm = bmesh.new()
    rings = []
    for r, y in profile:
        if r < 1e-9:
            rings.append([bm.verts.new((centre[0], centre[1] + y, centre[2]))])
        else:
            rings.append([bm.verts.new((centre[0] + r * math.cos(2 * math.pi * s / segments), centre[1] + y,
                                        centre[2] + r * math.sin(2 * math.pi * s / segments))) for s in range(segments)])
    for a, b in zip(rings, rings[1:]):
        for s in range(segments):
            t = (s + 1) % segments
            if len(a) == 1 and len(b) == 1:
                continue
            if len(a) == 1:
                bm.faces.new((a[0], b[t], b[s]))
            elif len(b) == 1:
                bm.faces.new((a[s], a[t], b[0]))
            else:
                bm.faces.new((a[s], a[t], b[t], b[s]))
    if len(rings[0]) > 1:
        bm.faces.new(rings[0][::-1])
    if len(rings[-1]) > 1:
        bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return hs.from_bmesh(name, bm, material)


def loft(name, sections, material, segments=3):
    """Rounded-rectangle sections (z, y centre, half width, half depth, corner radius) joined into one solid."""
    bm = bmesh.new()
    rings = []
    for z, yc, hw, hd, r in sections:
        outline = hs.fillet([(-hw, yc - hd), (hw, yc - hd), (hw, yc + hd), (-hw, yc + hd)], r, segments)
        rings.append([bm.verts.new((x, y, z)) for x, y in outline])
    n = len(rings[0])
    for a, b in zip(rings, rings[1:]):
        for k in range(n):
            bm.faces.new((a[k], a[(k + 1) % n], b[(k + 1) % n], b[k]))
    bm.faces.new(rings[0][::-1])
    bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return hs.from_bmesh(name, bm, material)


def clean(obj, dist=0.00012):
    """Weld and dissolve the micro-fragments an exact boolean can leave where a cut ends on a rounded edge."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=dist)
    bmesh.ops.dissolve_degenerate(bm, dist=dist, edges=bm.edges)
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()
    return obj


def shade(obj, angle=40, weighted=True):
    """Smooth shading with real sharp edges (this Blender has no Mesh.set_sharp_from_angle, so hs.finish leaves every
    edge soft): edges whose faces meet at more than `angle` degrees are marked sharp, then weighted normals."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    limit = math.radians(angle)
    for f in bm.faces:
        f.smooth = True
    for e in bm.edges:
        e.smooth = len(e.link_faces) == 2 and e.calc_face_angle(0.0) < limit
    bm.to_mesh(obj.data)
    bm.free()
    if weighted:
        mod = obj.modifiers.new('weighted', 'WEIGHTED_NORMAL')
        mod.keep_sharp = True
        mod.weight = 50
        hs.apply_all(obj)
    return obj


def finish(obj, bevel=0.0, segments=1, angle=40, weighted=True):
    """Optional bevel, then proper shading."""
    if bevel > 0:
        hs.finish(obj, bevel, segments, angle, weighted=False)
    return shade(obj, angle, weighted)


def shear_rake(obj, z_ref):
    """Shear a mesh so everything leans with the grip: y += tan(17 deg) * (z - z_ref)."""
    for v in obj.data.vertices:
        v.co.y += TAN * (v.co.z - z_ref)
    obj.data.update()
    return obj


# ------------------------------------------------------------ slide

def slide():
    """Hex-section slide: 12 mm bright top flat, 35 degree facets, vertical flanks, 1.5 mm lower chamfer.
    The long edges are rounded in the section itself (2 segments on the top-flat edges) and the perimeter
    edges are chamfered by the side and plan outlines, so no bevel modifier is needed and no slivers appear."""
    sec = [(-0.006, SLIDE_Z1), (0.006, SLIDE_Z1), (0.013, 0.0355), (0.013, 0.0120), (0.0115, SLIDE_Z0),
           (-0.0115, SLIDE_Z0), (-0.013, 0.0120), (-0.013, 0.0355)]
    sec = fil(sec, [0.0008, 0.0008, 0.0007, 0.0006, 0.0005, 0.0005, 0.0006, 0.0007], 2)
    body = hs.extrude_profile('paint_slide', sec, 0.196, 'anodized', 'Y', offset=0.088)
    # Side outline: rear face at y = 0 with a 0.0035 x 45 degree top chamfer, front face at 0.176 with a 0.002 top
    # chamfer, 0.4 mm chamfers on the lower edges.
    side = [(0.0, 0.0109), (0.0, 0.0370), (0.0050, 0.0420), (0.1725, 0.0420), (0.1760, 0.0385), (0.1760, 0.0109),
            (0.1750, 0.0099), (0.1750, 0.0), (0.0010, 0.0), (0.0010, 0.0099)]
    hs.boolean(body, hs.extrude_profile('slide_side', side, 0.1, 'anodized', 'X'), 'INTERSECT')
    # Plan outline: 0.0045 x 0.014 nose chamfers and 0.6 mm chamfers up the rear corners.
    plan = [(-0.0104, -0.002), (0.0104, -0.002), (0.0135, 0.0011), (0.0135, 0.1604), (0.0085, SLIDE_Y1), (0.0085, 0.2),
            (-0.0085, 0.2), (-0.0085, SLIDE_Y1), (-0.0135, 0.1604), (-0.0135, 0.0011)]
    hs.boolean(body, hs.extrude_profile('slide_plan', plan, 0.1, 'anodized', 'Z', offset=0.025), 'INTERSECT')

    # Underside channel: 3 mm flank walls, 6 mm of metal over the barrel, 7 mm rear wall, 12 mm nose wall; the lower
    # 2 mm steps in to 16 mm wide so the slide has real rails that ride just above the frame plateau.
    channel = [(-0.0080, 0.005), (0.0080, 0.005), (0.0080, 0.0125), (0.0100, 0.0125), (0.0100, 0.0345), (-0.0100, 0.0345),
               (-0.0100, 0.0125), (-0.0080, 0.0125)]
    hs.boolean(body, hs.extrude_profile('channel', channel, 0.157, 'anodized', 'Y', offset=(0.007 + 0.164) / 2))
    # Muzzle hole: the barrel overlaps its wall by 0.4 mm, so there is no gap behind the collar.
    hs.boolean(body, hs.cylinder('muzzle_hole', (0, 0.1640, BORE), (0, 0.1800, BORE), 0.0068, 'anodized', 28))
    # Hexagonal ejection port on the right: raked front edge, chamfered corners, 0.7 mm chamfered rim, open to the chamber.
    port = [(0.0540, 0.0215), (0.0560, 0.0195), (0.0985, 0.0195), (0.1002, 0.0212), (0.0942, 0.0312),
            (0.0922, 0.0330), (0.0560, 0.0330), (0.0540, 0.0310)]
    hs.boolean(body, cutter('port', port, [(0.0090, 0), (0.0123, 0), (0.0145, 0.0022)]))
    # Six stadium cocking slots per flank, raked 17 degrees top forward, 1.3 mm deep with drafted rims, stopping 7 mm
    # short of the port.
    slots = []
    for sign in (1, -1):
        for i in range(6):
            yc = 0.0155 + 0.0055 * i
            outline = capsule((yc - 0.0023, 0.0168), (yc + 0.0023, 0.0317), 0.0013, 4)
            slots.append(cutter(f'slot_{sign}_{i}', outline, [(sign * 0.0117, 0), (sign * 0.0126, 0), (sign * 0.0140, 0.0014)]))
    hs.boolean(body, hs.join(slots, 'slots'))
    # Rear face: a recess for the striker plate (chamfered rim), and the firing-pin bore behind it.
    recess = [(-0.00725, BORE - 0.00625), (0.00725, BORE - 0.00625), (0.00725, BORE + 0.00625), (-0.00725, BORE + 0.00625)]
    hs.boolean(body, cutter('plate_recess', recess, [(0.0020, 0), (0.0004, 0), (-0.0010, 0.0014)], 'Y'))
    hs.boolean(body, hs.cylinder('pin_bore', (0, -0.001, BORE), (0, 0.0050, BORE), 0.0022, 'anodized', 20))
    # Sight pockets (the sights fill them exactly).
    hs.boolean(body, span_box('rear_pocket', -0.0075, 0.0075, 0.009, 0.019, 0.0380, 0.0450, 'anodized'))
    hs.boolean(body, span_box('front_pocket', -0.0045, 0.0045, 0.150, 0.162, 0.0380, 0.0450, 'anodized'))
    clean(body)
    finish(body, 0, 1, 50)
    return body


def striker():
    """Steel plate seated in the rear recess (1 mm step all round) with the firing-pin hole and the pin tip behind it."""
    plate = span_box('striker_plate', -0.00625, 0.00625, 0.0008, 0.0020, BORE - 0.00525, BORE + 0.00525, 'steel')
    hs.boolean(plate, hs.cylinder('plate_hole', (0, 0.0, BORE), (0, 0.0030, BORE), 0.0022, 'steel', 20))
    finish(plate, 0.0002, 1, weighted=False)
    tip = hs.cylinder('pin_tip', (0, 0.0023, BORE), (0, 0.0052, BORE), 0.0014, 'steel', 14)
    finish(tip, 0.0002, 1, weighted=False)
    return [plate, tip]


# ------------------------------------------------------------ sights

def rear_sight():
    """Square-gated rear sight: two 4.5 mm wings, a 6 mm notch, vertical rear face with bevelled lips,
    front face raked back 20 degrees. 6 mm above the top flat."""
    side = [(0.009, 0.0380), (0.019, 0.0380), (0.019, SLIDE_Z1), (0.0168, 0.0465), (0.009, 0.0465)]
    gate = hs.extrude_profile('rear_sight', side, 0.0150, 'steel', 'X')
    top = [(-0.0075, 0.0380), (0.0075, 0.0380), (0.0075, 0.0447), (0.0057, 0.0465), (-0.0057, 0.0465), (-0.0075, 0.0447)]
    hs.boolean(gate, hs.extrude_profile('gate_top', top, 0.05, 'steel', 'Y', offset=0.014), 'INTERSECT')
    # 6 mm square notch, floor at z = 0.0430; its rim on the shooter's side is chamfered 0.6 mm so the outline catches light.
    notch = [(-0.0030, 0.0430), (0.0030, 0.0430), (0.0030, 0.0500), (-0.0030, 0.0500)]
    hs.boolean(gate, cutter('notch', notch, [(0.0075, 0.0021), (0.0096, 0.0), (0.0200, 0.0)], 'Y'))
    finish(gate, 0.0004, 1, 40)
    return gate


def front_sight():
    """Ramped front blade: 3.4 mm wide, vertical rear face, 45 degree front ramp, on a 9 mm wide base."""
    base = hs.extrude_profile('front_sight', [(0.1500, 0.0380), (0.1620, 0.0380), (0.1620, 0.0408), (0.1585, 0.0425), (0.1500, 0.0425)],
                              0.0090, 'steel', 'X')
    blade = hs.extrude_profile('front_blade', [(0.1500, 0.0420), (0.1500, 0.0465), (0.1530, 0.0465), (0.1570, 0.0425), (0.1570, 0.0420)],
                               0.0034, 'steel', 'X')
    hs.boolean(base, blade, 'UNION')
    finish(base, 0.0005, 1, 40)
    return base


def front_bead():
    """Brass dot set into the rear face of the blade: a 4.4 mm dome (the aiming dot, large enough to read in first person)."""
    R, y_s = 0.0022, 0.1511
    prof = [(0.0, y_s - R)] + [(R * math.sin(math.radians(a)), y_s - R * math.cos(math.radians(a))) for a in (22, 44, 56)] + [(0.00182, 0.1503)]
    dot = lathe('front_bead', prof, 'brass', 12, centre=(0, 0, 0.0435))
    shade(dot, 50, False)
    return dot


# ------------------------------------------------------------ barrel and the mechanism seen through the port

def barrel():
    """Barrel tube, chamfered hex muzzle collar (4 mm proud of the slide face), recessed bore."""
    tube = lathe('barrel', [(0.0072, 0.0850), (0.0072, 0.1765)], 'steel', 24, centre=(0, 0, BORE))
    collar = hs.cylinder('collar', (0, 0.1755, BORE), (0, MUZZLE_Y, BORE), 0.0095, 'steel', 6)
    hs.boolean(tube, collar, 'UNION')
    hs.boolean(tube, hs.cylinder('bore', (0, 0.1680, BORE), (0, 0.1810, BORE), 0.0045, 'steel', 24))
    finish(tube, 0.0006, 1, 40)
    return tube


def chamber_block():
    """Steel chamber block under the port (y 0.052 to 0.085): flat top, chamfered corners, extractor seat."""
    c = 0.0018
    sec = [(-0.0085 + c, 0.0165), (0.0085 - c, 0.0165), (0.0085, 0.0165 + c), (0.0085, 0.0335 - c),
           (0.0085 - c, 0.0335), (-0.0085 + c, 0.0335), (-0.0085, 0.0335 - c), (-0.0085, 0.0165 + c)]
    block = hs.extrude_profile('chamber_block', sec, 0.033, 'steel', 'Y', offset=0.0685)
    hs.boolean(block, span_box('extractor_seat', 0.0070, 0.0100, 0.0560, 0.0735, 0.0210, 0.0300))
    finish(block, 0.0004, 1, 40, weighted=False)
    return block


def extractor():
    """Claw-ended bar in its seat on the right of the block: the lighter metal the player sees in the port."""
    prof = [(0.0575, 0.0225), (0.0715, 0.0225), (0.0715, 0.0285), (0.0690, 0.0285), (0.0690, 0.0245), (0.0575, 0.0245)]
    bar = hs.extrude_profile('extractor', prof, 0.0038, 'steel', 'X', offset=0.0089)
    finish(bar, 0.0004, 1, 40, weighted=False)
    return bar


def guide_rod():
    rod = hs.cylinder('guide_rod', (0, 0.1100, 0.0150), (0, 0.1645, 0.0150), 0.0031, 'steel', 14)
    finish(rod, 0.0003, 1, weighted=False)
    return rod


# ------------------------------------------------------------ frame and grip

def grip():
    """The whole graphite frame as one object: tang and beavertail, web notch, raked backstrap with palm swell,
    heel, frontstrap, square guard, dust cover and chin."""
    zb = [-0.0873, -0.080, -0.068, -0.056, -0.044, -0.032, -0.020, -0.010]
    back = [(yb(z) - swell(z), z) for z in zb]
    outline = ([(0.0030, DECK), (0.1500, DECK), (0.1464, 0.0040), (0.0955, 0.0040), (0.1015, -0.0215), (0.0975, -0.0255),
                (yf(-0.0255), -0.0255), (yf(FRAME_BOTTOM), FRAME_BOTTOM)] + back[::1] + [(0.0178, 0.0035), (0.0030, 0.0035)])
    # corner setbacks, in outline order
    sb = [0.0020, 0, 0, 0.0015, 0, 0, 0.0020, 0.0040] + [0.0040, 0, 0, 0, 0, 0, 0, 0] + [0.0060, 0.0015]
    side = fil(outline, sb, 3)
    body = hs.extrude_profile('grip', side, 0.06, 'grip_polymer', 'X')
    # Cross-section: 23.6 wide deck under the slide (1.2 mm overhang), 45 degree flare out to 31 wide at the palm,
    # tapering to 30 at the heel.
    sec = [(-0.0118, 0.0120), (0.0118, 0.0120), (0.0118, 0.0045), (0.0155, 0.0008), (0.0155, -0.0600), (0.0150, -0.0873),
           (0.0148, -0.1000), (-0.0148, -0.1000), (-0.0150, -0.0873), (-0.0155, -0.0600), (-0.0155, 0.0008), (-0.0118, 0.0045)]
    hs.boolean(body, hs.extrude_profile('grip_sec', sec, 0.40, 'grip_polymer', 'Y', offset=0.05), 'INTERSECT')
    # Plan, raked with the grip: chamfered rear corners that show on the palm swell, widest at the palm, then a
    # chamfer in to the 22.4 wide dust cover and guard.
    z_ref = -0.0255
    y0 = yb(z_ref)
    plan = [(-0.0120, y0 - 0.0060), (0.0120, y0 - 0.0060), (0.0155, y0 - 0.0025), (0.0155, 0.0555), (0.0112, 0.0615), (0.0112, 0.170),
            (-0.0112, 0.170), (-0.0112, 0.0615), (-0.0155, 0.0555), (-0.0155, y0 - 0.0025)]
    plan_obj = hs.extrude_profile('grip_plan', plan, 0.40, 'grip_polymer', 'Z', offset=z_ref)
    shear_rake(plan_obj, z_ref)
    hs.boolean(body, plan_obj, 'INTERSECT')
    # Round the outer edges once, on the clean base solid (long edges only, so the bevel cannot collapse).
    finish(body, 0.0011, 2, 40)

    # Plateau: the central 20 mm of the deck stands 0.8 mm proud, 0.5 mm under the slide rails, so the 1.3 mm parting
    # gap reads as a clean dark line and nothing inside the slide shows through it.
    hs.boolean(body, span_box('plateau', -0.0100, 0.0100, 0.0060, 0.1470, DECK - 0.001, PLATEAU, 'grip_polymer'), 'UNION')

    # Open square guard: 45 degree corner chamfers, front strut hooked forward 6 mm, about 40 x 26 mm opening.
    opening = [(yf(-0.0219) + 0.0030, -0.0219), (yf(-0.0219) - 0.0004, -0.0219 + 0.0030), (yf(0.0040), 0.0040), (0.0915, 0.0040),
               (0.0975, -0.0215), (0.0945, -0.0219)]
    hs.boolean(body, hs.extrude_profile('opening', opening, 0.05, 'grip_polymer', 'X'))
    # Trigger slot through the roof; magazine well with its flared mouth, and the narrow feed neck.
    hs.boolean(body, span_box('trigger_slot', -0.0052, 0.0052, 0.0650, 0.0755, 0.0030, 0.0105, 'grip_polymer'))
    wide = [(-0.1000, 0.0132, 0.0200, 0.0030), (FRAME_BOTTOM, 0.0132, 0.0200, 0.0030), (-0.0840, 0.0125, 0.01825, 0.0030),
            (0.0010, 0.0125, 0.01825, 0.0030)]
    hs.boolean(body, loft('well', [(z, mag_yc(z), hw, hd, r) for z, hw, hd, r in wide], 'grip_polymer'))
    neck = [(0.0000, 0.0086, 0.0165, 0.0020), (0.0105, 0.0086, 0.0165, 0.0020)]
    hs.boolean(body, loft('neck', [(z, mag_yc(z), hw, hd, r) for z, hw, hd, r in neck], 'grip_polymer'))
    # Three finger grooves on the frontstrap, sunk 2 mm.
    grooves = [hs.cylinder(f'groove{i}', (-0.02, yf(z) + 0.0030, z), (0.02, yf(z) + 0.0030, z), 0.0050, 'grip_polymer', 20)
               for i, z in enumerate((-0.0345, -0.0555, -0.0765))]
    hs.boolean(body, hs.join(grooves, 'grooves'))
    # Recessed stipple panel on each side (1.2 mm), 3.5 mm borders, raked with the grip.
    zt, zbm = -0.0190, -0.0740
    panel = fil([(yb(zt) + 0.0045, zt), (yf(zt) - 0.0045, zt), (yf(zbm) - 0.0045, zbm), (yb(zbm) + 0.0045, zbm)], 0.0030, 3)
    panels = [cutter(f'panel{s}', panel, [(s * 0.0143, 0), (s * 0.0152, 0), (s * 0.0170, 0.0018)]) for s in (1, -1)]
    hs.boolean(body, hs.join(panels, 'panels'))
    # Pocket for the left magazine release button.
    hs.boolean(body, hs.cylinder('release_pocket', (-0.0170, 0.0485, -0.0075), (-0.0139, 0.0485, -0.0075), 0.0058, 'grip_polymer', 24))
    # Backstrap channel: 19 mm wide, 0.8 mm deep, following the rake and the palm swell (same samples as the outline).
    floor = [(yb(z) - swell(z) + 0.0008, z) for z in zb[1:-1]]
    channel = floor + [(floor[-1][0] - 0.010, zb[-2]), (floor[0][0] - 0.010, zb[1])]
    hs.boolean(body, hs.extrude_profile('backstrap_channel', channel, 0.019, 'grip_polymer', 'X'))
    # Three-slot mini-rail under the dust cover.
    rail = [span_box(f'rail_slot{i}', -0.02, 0.02, y - 0.0017, y + 0.0017, 0.0030, 0.0060, 'grip_polymer') for i, y in enumerate((0.1080, 0.1170, 0.1260))]
    hs.boolean(body, hs.join(rail, 'rail_slots'))
    # Left thumb ledge: a flat shelf cut into the deck wall, 1.7 mm deep.
    hs.boolean(body, span_box('thumb_ledge', *LEDGE, 'grip_polymer'))
    clean(body)
    finish(body, 0, 1, 40)
    return body


# ------------------------------------------------------------ controls and pins

def trigger():
    """Steel shoe 8.5 mm wide, face leaning forward 12 degrees, pivoting on the trigger pin, with a 3.5 mm safety blade."""
    outline = [(0.0670, 0.0088), (0.0735, 0.0088), (0.0735, 0.0040), (0.0762, -0.0190), (0.0750, -0.0202), (0.0710, -0.0202),
               (0.0678, 0.0020)]
    shoe = hs.extrude_profile('trigger', fil(outline, [0.0005, 0.0005, 0.0010, 0.0010, 0.0006, 0.0006, 0.0005], 2), 0.0085, 'steel', 'X')
    blade = hs.extrude_profile('trigger_safety', [(0.0731, 0.0030), (0.0772, 0.0030), (0.0777, -0.0170), (0.0755, -0.0170), (0.0745, -0.0120)],
                               0.0035, 'steel', 'X')
    hs.boolean(shoe, blade, 'UNION')
    hs.boolean(shoe, hs.cylinder('trigger_hole', (-0.008, 0.0705, 0.0062), (0.008, 0.0705, 0.0062), 0.0022, 'steel', 14))
    finish(shoe, 0, 1, 40, weighted=False)
    return shoe


def slide_stop():
    """Left-side lever: a thumb paddle at the rear, a thin arm, and a pivot boss around the locking pin."""
    paddle = [(0.0745, 0.0050), (0.0840, 0.0050), (0.0840, 0.0097), (0.0745, 0.0097)]
    arm = [(0.0820, 0.0062), (0.0975, 0.0062), (0.0975, 0.0092), (0.0820, 0.0092)]
    lever = hs.extrude_profile('slide_stop', fil(paddle, 0.0008, 2), 0.0027, 'steel', 'X', offset=-0.01245)
    arm_o = hs.extrude_profile('slide_stop_arm', arm, 0.0020, 'steel', 'X', offset=-0.01210)
    boss = hs.cylinder('slide_stop_boss', (-0.0111, 0.0975, 0.0065), (-0.0136, 0.0975, 0.0065), 0.0032, 'steel', 18)
    hs.boolean(lever, arm_o, 'UNION')
    hs.boolean(lever, boss, 'UNION')
    # a notch in the paddle face for the thumb
    hs.boolean(lever, span_box('thumb_cut', -0.0150, -0.0134, 0.0765, 0.0825, 0.0063, 0.0083))
    finish(lever, 0.0003, 1, 40, weighted=False)
    return lever


def mag_release():
    """Left button in its pocket (bevelled rim) and the flush reversing boss on the right."""
    button = hs.cylinder('mag_release', (-0.0139, 0.0485, -0.0075), (-0.0165, 0.0485, -0.0075), 0.0046, 'steel', 24)
    boss = hs.cylinder('mag_release_boss', (0.0150, 0.0485, -0.0075), (0.0161, 0.0485, -0.0075), 0.0035, 'steel', 20)
    for p in (button, boss):
        finish(p, 0.0004, 1, weighted=False)
    return [button, boss]


def pins():
    parts = []
    for name, y, z, x0, x1 in (('pin_trigger', 0.0705, 0.0062, -0.0121, 0.0121), ('pin_locking', 0.0975, 0.0065, -0.0141, 0.0118),
                               ('pin_rear', 0.0085, 0.0066, -0.0124, 0.0124)):
        body = hs.cylinder(name, (x0, y, z), (x1, y, z), 0.0022, 'steel', 14)
        for x, s in ((x0, -1), (x1, 1)):
            # hex socket 0.5 mm deep in each head
            hs.boolean(body, hs.cylinder('hex', (x, y, z), (x - s * 0.0010, y, z), 0.0008, 'steel', 6))
        finish(body, 0.0003, 1, weighted=False)
        parts.append(body)
    return parts


# ------------------------------------------------------------ magazine

def magazine():
    """Tan polymer magazine lofted along the 17 degree axis, with a narrow feed neck, a recessed side panel
    with four raised ribs, three witness pockets, a squared foot and the brass top round. Origin: seated top centre."""
    secs = [(0.0095, 0.0078, 0.0153, 0.0020), (0.0012, 0.0078, 0.0153, 0.0020), (0.0008, 0.01175, 0.01775, 0.0030),
            (-0.0915, 0.01175, 0.01775, 0.0030)]
    body = loft('magazine', [(z, mag_yc(z), hw, hd, r) for z, hw, hd, r in secs], 'polymer')
    # Squared tan foot, 44.5 x 31 x 10 mm with 3 mm 30 degree bottom chamfers, 1.2 mm under the frame.
    foot_side = [(-0.0105, FOOT_TOP), (0.0340, FOOT_TOP), (0.0340, -0.0963), (0.0310, FOOT_BOTTOM), (-0.0075, FOOT_BOTTOM), (-0.0105, -0.0963)]
    foot = hs.extrude_profile('mag_foot', foot_side, 0.06, 'polymer', 'X')
    foot_sec = [(-0.0155, -0.0800), (0.0155, -0.0800), (0.0155, -0.0963), (0.0125, FOOT_BOTTOM), (-0.0125, FOOT_BOTTOM), (-0.0155, -0.0963)]
    hs.boolean(foot, hs.extrude_profile('foot_sec', foot_sec, 0.2, 'polymer', 'Y', offset=0.02), 'INTERSECT')
    foot_plan = hs.fillet([(-0.0155, -0.0105), (0.0155, -0.0105), (0.0155, 0.0340), (-0.0155, 0.0340)], 0.0030, 3)
    hs.boolean(foot, hs.extrude_profile('foot_plan', foot_plan, 0.2, 'polymer', 'Z', offset=-0.09), 'INTERSECT')
    finish(foot, 0.0006, 1, 40)
    hs.boolean(body, foot, 'UNION')
    # Recessed panel with four raised ribs: five shallow grooves per side.
    gh, rh, z_top = 0.0112, 0.0035, -0.0075
    cutters = []
    for sign in (1, -1):
        for i in range(5):
            z1 = z_top - i * (gh + rh)
            z0 = z1 - gh
            outline = fil([(mag_yc(z0) - 0.0120, z0), (mag_yc(z0) + 0.0120, z0), (mag_yc(z1) + 0.0120, z1), (mag_yc(z1) - 0.0120, z1)], 0.0012, 2)
            cutters.append(hs.extrude_profile(f'groove_{sign}_{i}', outline, 0.0030, 'polymer', 'X', offset=sign * 0.01275 + sign * -0.0008))
    hs.boolean(body, hs.join(cutters, 'mag_grooves'))
    # Witness pockets on the right at the 5, 10 and 15 round heights.
    pockets = [hs.cylinder(f'witness{i}', (0.0108, mag_yc(z) + 0.0150, z), (0.0140, mag_yc(z) + 0.0150, z), 0.0015, 'polymer', 12)
               for i, z in enumerate((-0.020, -0.045, -0.070))]
    hs.boolean(body, hs.join(pockets, 'witness'))
    clean(body)
    finish(body, 0, 1, 40)
    # Top round: a 9 x 19 style cartridge, zig-zag offset 3 mm, nose forward, resting on the feed lips.
    zc = 0.0138
    y_base = mag_yc(zc) - 0.0155
    profile = [(0.0042, 0.0), (0.0049, 0.0007), (0.0048, 0.0185), (0.0045, 0.0190), (0.0045, 0.0215), (0.0036, 0.0262), (0.0012, 0.0290)]
    rnd = lathe('top_round', profile, 'brass', 12, centre=(0.0026, y_base, zc))
    shade(rnd, 40, False)
    mag = hs.join([body, rnd], 'magazine')
    bpy.context.scene.cursor.location = (0, 0.0407, 0.0095)
    hs.select_only(mag)
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    return mag


# ------------------------------------------------------------ assembly

def build():
    hs.reset_scene()
    static = [slide()] + striker() + [rear_sight(), front_sight(), front_bead(), barrel(), chamber_block(), extractor(), guide_rod(),
                                      grip(), trigger(), slide_stop()] + mag_release() + pins()
    mag = magazine()
    for name, at in (('muzzle', (0, MUZZLE_Y, BORE)), ('ejection', (0.015, 0.078, 0.030))):
        empty = bpy.data.objects.new(name, None)
        hs.link(empty)
        empty.location = at
    return static, mag


if __name__ == '__main__':
    static, mag = build()
    meshes = [o for o in bpy.data.objects if o.type == 'MESH']
    print('KESTREL_9 objects=%d tris=%d' % (len(meshes), hs.triangles(meshes)))
    if '--' in sys.argv:
        out = sys.argv[sys.argv.index('--') + 1]
        bpy.ops.export_scene.gltf(filepath=out, export_format='GLB', export_apply=True, export_extras=True)
