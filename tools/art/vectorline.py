"""Vectorline (v1) - original compact submachine gun for SIGHTBREAK's first-person view.

Built entirely in headless Blender from code. Blender axes: X right, Y forward (the muzzle
points +Y; exports to Godot -Z), Z up. Metres. Bore axis on x = 0, z = BORE. Receiver rear
face at y = 0. A squat, slab-sided, pistol-calibre SMG: 0.425 m of body (0.565 m with the
picture-frame stock), a stepped-bench receiver with one straight ladder-rail spine, an
open square sight window, a wide shroud with four vertical slots a side stepping down to a
square muzzle block, a dead-vertical tan 30-round magazine ahead of the trigger guard and a
12 degree raked graphite grip.

Object naming is the integration contract read by the game:
  paint_*    surfaces that take the cosmetic finish (receiver, handguard)
  magazine   animated on reload (origin at its seated top centre, top round in brass)
  grip       the pistol grip, its own mesh
  muzzle     empty at the muzzle crown, origin of flashes and tracers
  ejection   empty at the ejection port, origin of shell casings
  reticle    empty at the centre of the sight window
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
import bmesh  # noqa: E402
import hardsurface as hs  # noqa: E402

BORE = 0.025
BODY_FRONT = 0.250            # receiver front face / shroud rear face
SHROUD_FRONT = 0.385
MUZZLE_Y = 0.425
SPINE_TOP = 0.056             # top of the cover's raised centre strip
RAIL_BASE = 0.055             # rail section starts 1 mm inside whatever carries it
RAIL_TOP = 0.0635
SIGHT_Z = 0.089               # centre of the sight window, 0.064 above the bore
LADDER = 0.010                # transverse slot pitch of the rail

# Game mesh groups (export.py). Each group is one draw; parts not listed join 'body'.
GROUPS = {
    # One paint mesh for the whole upper (receiver, cover, rails and shroud): the shroud is welded to the receiver, one finish
    # covers both, and one draw fewer keeps the first-person weapon within six nodes (actor_test).
    'paint_receiver': ('paint_body', 'paint_cover', 'paint_rail_body', 'paint_shroud', 'paint_rail_shroud'),
    'magazine': ('magazine',),
    'grip': ('grip',),
    # The stock sits behind the camera in first person, so it is its own mesh and the viewmodel leaves it out.
    'stock': ('stock_body', 'stock_block', 'stock_pin', 'butt_pad'),
}
# Hand anchors for the first-person rig: centre of the firing-hand grip and the support-hand hold under the shroud.
ANCHORS = {
    'grip_hand': (0.0, 0.024, -0.060),
    'support_hand': (0.0, 0.318, -0.006),
}


# ------------------------------------------------------------ small helpers

def prism(name, pts_xz, y0, y1, material='anodized'):
    """Cross-section (x, z) extruded along Y from y0 to y1: long edges are real chamfers."""
    return hs.extrude_profile(name, pts_xz, y1 - y0, material, 'Y', offset=(y0 + y1) / 2)


def block(name, x0, x1, y0, y1, z0, z1, material='steel'):
    return hs.box(name, ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), (x1 - x0, y1 - y0, z1 - z0), material)


def x_prism(name, pts_yz, x0, x1, material='steel'):
    return hs.extrude_profile(name, pts_yz, x1 - x0, material, 'X', offset=(x0 + x1) / 2)


def z_prism(name, pts_xy, z0, z1, material='steel'):
    return hs.extrude_profile(name, pts_xy, z1 - z0, material, 'Z', offset=(z0 + z1) / 2)


def rrect(a0, a1, b0, b1, r, seg=3):
    return hs.fillet([(a0, b0), (a1, b0), (a1, b1), (a0, b1)], r, seg)


def chamfer_rect(a0, a1, b0, b1, c):
    """Rectangle with all four corners cut by a straight c-long chamfer."""
    return hs.fillet([(a0, b0), (a1, b0), (a1, b1), (a0, b1)], c, 1)


def trim_side(obj, side_yz):
    """Intersect with a side profile (y, z) extruded across X: shapes the ends of a prism."""
    cutter = hs.extrude_profile(obj.name + '_side', side_yz, 0.3, 'steel', 'X')
    hs.boolean(obj, cutter, 'INTERSECT')
    return obj


def revolve(name, profile_ry, material, segments=24, centre=(0.0, 0.0, BORE)):
    """Lathe about an axis parallel to Y. profile_ry is (radius, y); a radius of 0 becomes one apex vertex, so no
    degenerate faces."""
    bm = bmesh.new()
    rings = []
    for r, y in profile_ry:
        if r <= 1e-9:
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


def loft(name, rings, material):
    """Closed solid skinned through rings of 3D points (equal counts, consecutive rings adjacent)."""
    bm = bmesh.new()
    vert_rings = [[bm.verts.new(p) for p in ring] for ring in rings]
    n = len(vert_rings[0])
    for a, b in zip(vert_rings, vert_rings[1:]):
        for k in range(n):
            bm.faces.new((a[k], a[(k + 1) % n], b[(k + 1) % n], b[k]))
    bm.faces.new(vert_rings[0])
    bm.faces.new(vert_rings[-1][::-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return hs.from_bmesh(name, bm, material)


def barrel_hole(name, y0, y1):
    """Cutter that matches the barrel's own 24-segment lathe exactly."""
    return revolve(name, [(0.0, y0), (0.0095, y0), (0.0095, y1), (0.0, y1)], 'steel', 24)


def ladder_rail(name, y0, y1, first, count):
    """Rail with real transverse slots on the shared 0.010 grid (slot k is centred on y = 0.024 + 0.010 k)."""
    section = [(-0.012, RAIL_BASE), (0.012, RAIL_BASE), (0.012, 0.0620), (0.0105, RAIL_TOP), (-0.0105, RAIL_TOP), (-0.012, 0.0620)]
    rail = prism(name, section, y0, y1)
    slots = hs.array_join(lambda i, d: hs.box(f'{name}_slot{i}', (0, 0.024 + LADDER * first + d.y, 0.0625), (0.03, 0.005, 0.005)),
                          count, (0, LADDER, 0), name + '_slots')
    hs.boolean(rail, slots)
    return hs.finish(rail, 0.0004, 1)


# ------------------------------------------------------------ receiver and top line

def receiver_body():
    """Slab body: x +-0.028, z -0.010..0.040, hollow pocket, ports, mag-well block with its flared lip."""
    section = [(-0.028, -0.005), (-0.023, -0.010), (0.023, -0.010), (0.028, -0.005), (0.028, 0.040), (-0.028, 0.040)]
    body = prism('paint_body', section, 0.0, BODY_FRONT)
    pocket = block('pocket', -0.0215, 0.0215, 0.012, 0.236, 0.008, 0.0425)
    port = x_prism('port_cut', hs.fillet([(0.060, 0.012), (0.150, 0.012), (0.150, 0.036), (0.060, 0.036)], 0.004), 0.0185, 0.0305)
    slot = x_prism('charge_slot', hs.fillet([(0.060, 0.021), (0.150, 0.021), (0.150, 0.029), (0.060, 0.029)], 0.0039), -0.0305, -0.0185)
    hs.cut(body, pocket, port, slot, barrel_hole('barrel_cut', 0.230, 0.256))
    # Mag-well block under the receiver, flared at its mouth, then the well opened up into the pocket.
    well = block('well_block', -0.0225, 0.0225, 0.1075, 0.1685, -0.0345, -0.008)
    lip_section = [(-0.0245, -0.0320), (-0.0220, -0.0345), (0.0220, -0.0345), (0.0245, -0.0320), (0.0245, -0.0310), (-0.0245, -0.0310)]
    lip = prism('well_lip', lip_section, 0.1035, 0.1725)
    hs.boolean(body, well, 'UNION')
    hs.boolean(body, lip, 'UNION')
    opening = z_prism('well_open', rrect(-0.0155, 0.0155, 0.114, 0.162, 0.004), -0.042, 0.012)
    release_seat = hs.cylinder('release_seat', (0.0195, 0.1235, -0.022), (0.026, 0.1235, -0.022), 0.0070, 'steel', 24)
    hs.cut(body, opening, release_seat)
    return hs.finish(body, 0.0007, 2)


def top_cover():
    """Stepped bench: two flat shoulders either side of a raised centre strip, 0.002 inside each body flank."""
    section = [(-0.026, 0.039), (0.026, 0.039), (0.026, 0.047), (0.0225, 0.0505), (0.0155, 0.0505), (0.0155, SPINE_TOP),
               (-0.0155, SPINE_TOP), (-0.0155, 0.0505), (-0.0225, 0.0505), (-0.026, 0.047)]
    cover = prism('paint_cover', section, 0.0, BODY_FRONT)
    trim_side(cover, [(0.0, 0.030), (BODY_FRONT, 0.030), (BODY_FRONT, 0.060), (0.006, 0.060), (0.0, 0.0505)])
    screws = []
    for sx in (-1, 1):
        for y in (0.028, 0.222):
            head = hs.cylinder('cover_screw', (sx * 0.019, y, 0.0500), (sx * 0.019, y, 0.0521), 0.0024, 'steel', 16)
            hs.cut(head, hs.cylinder('hex_socket', (sx * 0.019, y, 0.0509), (sx * 0.019, y, 0.0530), 0.0013, 'steel', 6))
            screws.append(hs.finish(head, 0.0002, 1, weighted=False))
    for i, s in enumerate(screws):
        s.name = f'cover_screw_{i}'
    hs.finish(cover, 0.0006, 2)
    rail = ladder_rail('paint_rail_body', 0.012, 0.246, 0, 22)
    return [cover, rail] + screws


def rear_plate():
    """End plate on the receiver's rear face, which is the largest flat thing the player sees of the weapon once the stock is
    left out of first person: an earth-tone polymer plate (the one warm surface on the black receiver, so the face reads),
    raised 12 mm and bevelled, four horizontal grip ribs across its lower half, one retaining screw above them, a screw at each
    corner and two relief grooves down the flanks. (A first version had a recessed round buffer cap here; critics read it as a
    camera lens, so it is gone.)"""
    plate = block('rear_plate', -0.0245, 0.0245, -0.012, 0.0006, -0.0065, 0.0465, 'plate')
    grooves = [block(f'rear_groove{i}', x - 0.0012, x + 0.0012, -0.0135, -0.0100, -0.0030, 0.0430, 'steel') for i, x in enumerate((-0.0195, 0.0195))]
    hs.cut(plate, *grooves)
    ribs = [block(f'rear_rib{i}', -0.0205, 0.0205, -0.0136, -0.0115, -0.0035 + 0.0066 * i, -0.0035 + 0.0066 * i + 0.0032, 'plate') for i in range(4)]
    hs.boolean(plate, hs.join(ribs, 'rear_ribs'), 'UNION')
    hs.finish(plate, 0.0010, 2)
    parts = [plate]
    retainer = hs.cylinder('retainer', (0.0, -0.0140, 0.0345), (0.0, -0.0112, 0.0345), 0.0046, 'steel', 6)
    hs.cut(retainer, hs.cylinder('retainer_socket', (0.0, -0.0150, 0.0345), (0.0, -0.0128, 0.0345), 0.0022, 'steel', 6))
    parts.append(hs.finish(retainer, 0.0004, 1, weighted=False))
    for i, (sx, z) in enumerate(((-1, -0.0030), (1, -0.0030), (-1, 0.0430), (1, 0.0430))):
        screw = hs.cylinder(f'rear_screw{i}', (sx * 0.0190, -0.0122, z), (sx * 0.0190, -0.0098, z), 0.0020, 'steel', 12)
        parts.append(hs.finish(screw, 0.0002, 1, weighted=False))
    return parts


# ------------------------------------------------------------ front end

def shroud():
    """Hollow 0.064 wide shroud, four through-slots a side (one cutter passes both walls), closed front wall."""
    outer = [(-0.026, 0.002), (0.026, 0.002), (0.032, 0.008), (0.032, 0.050), (0.026, 0.056), (-0.026, 0.056), (-0.032, 0.050), (-0.032, 0.008)]
    inner = [(-0.021, 0.009), (0.021, 0.009), (0.025, 0.013), (0.025, 0.045), (0.021, 0.049), (-0.021, 0.049), (-0.025, 0.045), (-0.025, 0.013)]
    guard = prism('paint_shroud', outer, BODY_FRONT, SHROUD_FRONT)
    cavity = prism('shroud_cavity', inner, BODY_FRONT - 0.0005, 0.377, 'steel')
    slots = hs.array_join(
        lambda i, d: x_prism(f'slot{i}', hs.fillet([(0.278 + 0.026 * i, 0.015), (0.288 + 0.026 * i, 0.015), (0.288 + 0.026 * i, 0.043), (0.278 + 0.026 * i, 0.043)], 0.0045), -0.04, 0.04),
        4, (0, 0, 0), 'shroud_slots')
    hs.cut(guard, cavity, barrel_hole('nose_hole', 0.372, 0.390), slots)
    hs.finish(guard, 0.0006, 1)
    rail = ladder_rail('paint_rail_shroud', 0.254, 0.380, 24, 11)
    # Full-width chin: the support hand's physical stop. It wraps the shroud's lower chamfers so its flanks are flush.
    chin_section = hs.fillet([(-0.032, -0.012), (0.032, -0.012), (0.032, 0.008), (-0.032, 0.008)], [0.004, 0.004, 0, 0], 1)
    chin = prism('hand_stop', chin_section, 0.371, SHROUD_FRONT, 'grip_polymer')
    trim_side(chin, [(0.371, 0.012), (SHROUD_FRONT, 0.012), (SHROUD_FRONT, -0.008), (0.381, -0.012), (0.371, -0.012)])
    hs.finish(chin, 0.0010, 2, 40)
    return [guard, rail, chin]


def barrel():
    """Visible only through the shroud slots, and as the muzzle block's socket. One object: tube, nut, retaining ring."""
    tube = revolve('barrel', [(0.0, 0.205), (0.0095, 0.205), (0.0095, 0.405), (0.0, 0.405)], 'steel', 24)
    nut = revolve('barrel_nut', [(0.0, 0.250), (0.0125, 0.250), (0.0125, 0.264), (0.0, 0.264)], 'steel', 24)
    ring = revolve('barrel_ring', [(0.0, 0.356), (0.0115, 0.356), (0.0115, 0.368), (0.0, 0.368)], 'steel', 24)
    part = hs.join([tube, nut, ring], 'barrel')
    hs.smooth(part, 30)
    return [part]


def muzzle_block():
    """Chamfered square nose, half the shroud's width, one top vent opening into the bore."""
    section = hs.fillet([(-0.016, 0.009), (0.016, 0.009), (0.016, 0.041), (-0.016, 0.041)], 0.004, 1)
    nose = prism('muzzle_block', section, SHROUD_FRONT, MUZZLE_Y, 'steel')
    inside = revolve('muzzle_bore', [(0.0, 0.384), (0.0095, 0.384), (0.0095, 0.405), (0.0050, 0.405), (0.0050, 0.421), (0.0085, 0.421), (0.0085, 0.426), (0.0, 0.426)], 'steel', 24)
    vent = block('muzzle_vent', -0.006, 0.006, 0.407, 0.417, 0.028, 0.0425)
    hs.cut(nose, inside, vent)
    return [hs.finish(nose, 0.0012, 1)]


# ------------------------------------------------------------ sight

def sight():
    """Open square window on an inverted-U foot gripping the rail. No lens: a real hole, two reticle ticks."""
    foot_section = [(-0.0155, SPINE_TOP), (-0.0155, 0.0695), (0.0155, 0.0695), (0.0155, SPINE_TOP), (0.012, SPINE_TOP),
                    (0.012, RAIL_TOP), (-0.012, RAIL_TOP), (-0.012, SPINE_TOP)]
    foot = hs.finish(prism('sight_foot', foot_section, 0.062, 0.128), 0.0012, 1)
    frame = prism('sight_frame', rrect(-0.020, 0.020, 0.0685, 0.1095, 0.003), 0.107, 0.123)
    # The window: a straight hole with a 1.5 mm chamfer round its rear mouth, so the opening has a bright knife edge.

    def ring(y, grow):
        return [(x, y, z) for x, z in rrect(-0.0155 - grow, 0.0155 + grow, 0.0745 - grow, 0.1035 + grow, 0.003 + grow)]
    window = loft('sight_window', [ring(0.1055, 0.0015), ring(0.107, 0.0015), ring(0.1085, 0.0), ring(0.124, 0.0)], 'steel')
    hs.boolean(frame, window)
    hs.finish(frame, 0.0008, 1)
    ticks = []
    for name, pts in (('reticle_tick_top', [(-0.002, 0.1040), (0.002, 0.1040), (0.001, 0.0955), (-0.001, 0.0955)]),
                      ('reticle_tick_bottom', [(-0.002, 0.0740), (0.002, 0.0740), (0.001, 0.0825), (-0.001, 0.0825)])):
        ticks.append(prism(name, pts, 0.113, 0.117, 'steel'))
    clamp = hs.cylinder('sight_clamp', (0.0155, 0.076, RAIL_TOP), (0.0200, 0.076, RAIL_TOP), 0.0045, 'steel', 6)
    hs.finish(clamp, 0.0004, 1, weighted=False)
    reticle = bpy.data.objects.new('reticle', None)
    hs.link(reticle)
    reticle.location = (0.0, 0.115, SIGHT_Z)
    return [foot, frame, clamp] + ticks


# ------------------------------------------------------------ grip, guard, trigger, magazine

def grip():
    """Raked 12 degree grip: flat front strap, palm swell, flared heel, recessed panel each side (stippled by the bake)."""
    side = hs.fillet([(0.010, -0.006), (0.062, -0.006), (0.0585, -0.027), (0.0463, -0.080), (0.0415, -0.114), (-0.0200, -0.114),
                      (-0.0140, -0.098), (-0.0040, -0.060), (0.0045, -0.028)], [0.003, 0.003, 0.0, 0.0, 0.004, 0.004, 0.0, 0.0, 0.0])
    plan = hs.fillet([(-0.0150, -0.030), (0.0150, -0.030), (0.0180, -0.020), (0.0180, 0.052), (0.0165, 0.068), (-0.0165, 0.068),
                      (-0.0180, 0.052), (-0.0180, -0.020)], 0.004)
    part = hs.silhouette('grip', side, plan, 'grip_polymer')
    hs.finish(part, 0.0014, 2, 40)
    # One panel per side, following the rake of the strap. 1.2 mm deep.
    panel = hs.fillet([(0.0137, -0.031), (0.0477, -0.031), (0.0347, -0.089), (0.0007, -0.089)], 0.004)
    for sx in (-1, 1):
        hs.boolean(part, x_prism('grip_panel', panel, sx * 0.0188 - 0.002, sx * 0.0188 + 0.002))
    return [hs.finish(part, 0.0004, 1, 40)]


def trigger_group():
    """Trigger guard with a flat keel joining the grip to the well lip, and the trigger blade inside it."""
    outline = hs.fillet([(0.050, -0.006), (0.050, -0.047), (0.1085, -0.047), (0.1085, -0.006), (0.1025, -0.006), (0.1025, -0.040),
                         (0.0575, -0.040), (0.0575, -0.006)], [0.0, 0.004, 0.004, 0.0, 0.0, 0.002, 0.002, 0.0])
    guard = x_prism('trigger_guard', outline, -0.008, 0.008, 'anodized')
    hs.finish(guard, 0.0008, 2)
    blade = x_prism('trigger', hs.fillet([(0.0675, -0.008), (0.0750, -0.008), (0.0750, -0.024), (0.0725, -0.034), (0.0655, -0.034), (0.0665, -0.024)], 0.0015),
                    -0.004, 0.004)
    hs.finish(blade, 0.0003, 1)
    return [guard, blade]


def magazine():
    """Straight 30-round tan stick: eight lofted rings with 1 mm of draft per side, flared floor plate, count windows on both
    faces, four grip grooves, brass top round. Origin at the seated top centre so the reload animation pivots there."""
    z_top, z_bot = 0.004, -0.145

    def grow(z):
        return 0.001 * (z_top - z) / 0.148
    rings = []
    for i in range(8):
        z = z_top + (z_bot - z_top) * i / 7
        g = grow(z)
        rings.append([(x, y, z) for x, y in rrect(-0.013 - g, 0.013 + g, 0.116 - g, 0.160 + g, 0.004)])
    body = loft('magazine', rings, 'polymer')
    hs.smooth(body, 40)
    cutters = []
    for z in (-0.018, -0.044, -0.070, -0.096, -0.122):
        for sx in (-1, 1):
            face = 0.013 + grow(z)
            lo, hi = sorted((sx * (face - 0.0015), sx * (face + 0.01)))
            cutters.append(block(f'count{len(cutters)}', lo, hi, 0.134, 0.142, z - 0.0025, z + 0.0025, 'polymer'))
    for z in (-0.030, -0.050, -0.070, -0.090):
        face = 0.160 + grow(z)
        cutters.append(block(f'groove{len(cutters)}', -0.009, 0.009, face - 0.0015, face + 0.01, z - 0.0015, z + 0.0015, 'polymer'))
    hs.boolean(body, hs.join(cutters, 'mag_cutters'))
    side = [(0.1105, -0.144), (0.1655, -0.144), (0.1655, -0.153), (0.1625, -0.156), (0.1135, -0.156), (0.1105, -0.153)]
    floor = hs.silhouette('mag_floor', side, rrect(-0.0175, 0.0175, 0.1105, 0.1655, 0.004), 'polymer')
    hs.finish(floor, 0.0010, 1)
    round_ = revolve('top_round', [(0.0, 0.1215), (0.0049, 0.1215), (0.0049, 0.141), (0.0045, 0.141), (0.0042, 0.1435), (0.0036, 0.1470),
                                   (0.0023, 0.1505), (0.0, 0.1505)], 'brass', 16, centre=(0.005, 0.0, 0.0074))
    mag = hs.join([body, floor, round_], 'magazine')
    bpy.context.scene.cursor.location = (0.0, 0.138, 0.004)
    hs.select_only(mag)
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    return mag


# ------------------------------------------------------------ mechanism, controls, fasteners

def mechanism():
    """Everything the player can see through the ports and on the flanks. All of it touches its neighbour."""
    parts = []
    # Open-bolt rest: the bolt sits at the rear of the pocket, 1 mm into its floor, seen through the right port.
    bolt = block('bolt', -0.0125, 0.0125, 0.040, 0.112, 0.007, 0.034)
    parts.append(hs.finish(bolt, 0.0008, 1))
    stem = block('charging_handle', -0.0300, -0.0115, 0.068, 0.078, 0.023, 0.027)
    knob = x_prism('charging_knob', hs.fillet([(0.064, 0.019), (0.082, 0.019), (0.082, 0.031), (0.064, 0.031)], 0.002, 1), -0.0380, -0.0295)
    hs.boolean(stem, knob, 'UNION')
    parts.append(hs.finish(stem, 0.0006, 1))
    cross = hs.cylinder('cross_bolt', (-0.032, 0.082, 0.001), (0.032, 0.082, 0.001), 0.0035, 'steel', 16)
    for sx in (-1, 1):
        head = hs.cylinder('cross_head', (sx * 0.028, 0.082, 0.001), (sx * 0.032, 0.082, 0.001), 0.0055, 'steel', 16)
        cross = hs.join([cross, head], 'cross_bolt')
    parts.append(hs.finish(cross, 0.0004, 1, weighted=False))
    for name, y in (('takedown_pin_rear', 0.014), ('takedown_pin_front', 0.238)):
        pin = hs.cylinder(name, (-0.030, y, 0.0), (0.030, y, 0.0), 0.0035, 'steel', 16)
        parts.append(hs.finish(pin, 0.0004, 1, weighted=False))
    release = hs.cylinder('mag_release', (0.0195, 0.1235, -0.022), (0.0240, 0.1235, -0.022), 0.0050, 'steel', 20)
    parts.append(hs.finish(release, 0.0004, 1, weighted=False))
    return parts


# ------------------------------------------------------------ stock

def stock():
    """Closed picture-frame stock with a small cheek riser. Behind the camera in first person."""
    outline = hs.fillet([(-0.016, 0.045), (-0.060, 0.049), (-0.070, 0.058), (-0.118, 0.058), (-0.128, 0.049), (-0.128, -0.022),
                         (-0.120, -0.030), (-0.062, -0.030), (-0.034, 0.003), (-0.016, 0.003)],
                        [0.0, 0.002, 0.003, 0.004, 0.002, 0.002, 0.004, 0.004, 0.002, 0.0])
    frame = x_prism('stock_body', outline, -0.0115, 0.0115, 'grip_polymer')
    window = x_prism('stock_window', hs.fillet([(-0.112, -0.010), (-0.068, -0.010), (-0.048, 0.012), (-0.048, 0.036), (-0.112, 0.036)],
                                               [0.004, 0.004, 0.004, 0.004, 0.004]), -0.03, 0.03)
    hs.cut(frame, window)
    hs.finish(frame, 0.0012, 2, 40)
    blk = prism('stock_block', chamfer_rect(-0.020, 0.020, 0.003, 0.047, 0.003), -0.020, 0.002, 'steel')
    hs.finish(blk, 0.0005, 1)
    pin = hs.cylinder('stock_pin', (-0.023, -0.014, 0.025), (0.023, -0.014, 0.025), 0.0045, 'steel', 20)
    hs.finish(pin, 0.0004, 1, weighted=False)
    pad = hs.silhouette('butt_pad', rrect(-0.140, -0.126, -0.028, 0.054, 0.003, 2), rrect(-0.026, 0.026, -0.150, -0.120, 0.005), 'rubber')
    grooves = hs.array_join(lambda i, d: hs.box(f'pad_groove{i}', (0, -0.1405, -0.012 + d.z), (0.06, 0.004, 0.003)), 5, (0, 0, 0.012), 'pad_grooves')
    hs.boolean(pad, grooves)
    hs.finish(pad, 0.0010, 2)
    return [frame, blk, pin, pad]


# ------------------------------------------------------------ assembly

def build():
    hs.reset_scene()
    static = [receiver_body()] + rear_plate() + top_cover() + shroud() + barrel() + muzzle_block() + sight() + grip() + trigger_group() + mechanism() + stock()
    mag = magazine()
    for name, at in (('muzzle', (0.0, MUZZLE_Y, BORE)), ('ejection', (0.028, 0.105, 0.024))):
        empty = bpy.data.objects.new(name, None)
        hs.link(empty)
        empty.location = at
    return static, mag


if __name__ == '__main__':
    static, mag = build()
    meshes = [o for o in bpy.data.objects if o.type == 'MESH']
    print('VECTORLINE objects=%d tris=%d' % (len(meshes), hs.triangles(meshes)))
    if '--' in sys.argv:
        out = sys.argv[sys.argv.index('--') + 1]
        bpy.ops.export_scene.gltf(filepath=out, export_format='GLB', export_apply=True, export_extras=True)
