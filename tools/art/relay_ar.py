"""Relay AR (v2) — original 5.56-class carbine for SIGHTBREAK's first-person view.

Built entirely in headless Blender from code (no third-party meshes). Blender axes:
X right, Y forward (barrel; exports to Godot -Z), Z up. Metres. Bore axis at
x = 0, z = BORE. Receiver rear face at y = 0. Real-world-based proportions:
~0.92 m overall, 14.5-inch-class barrel, 36 mm upper receiver.

Object naming is the integration contract read by the game:
  paint_*    surfaces that take the cosmetic finish (receiver, handguard)
  magazine   animated on reload (pivot at its seated top)
  muzzle     empty at the muzzle crown, origin of flashes and tracers
  ejection   empty at the ejection port, origin of shell casings
  reticle    emissive dot of the reflex sight
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402
import hardsurface as hs  # noqa: E402

BORE = 0.025
RAIL_TOP = BORE + 0.0375        # top of the Picatinny teeth
UPPER_TOP = BORE + 0.028        # receiver flat-top under the rail
SPLIT = 0.0145                  # upper / lower parting line
RECEIVER_FRONT = 0.245
HANDGUARD_FRONT = 0.585
MUZZLE_Y = 0.676

# Game mesh groups (export.py). Each group is one draw; parts not listed join 'body'.
GROUPS = {
    'paint_receiver': ('paint_upper', 'paint_lower', 'paint_rail_upper'),
    'paint_handguard': ('paint_handguard', 'paint_rail_handguard'),
    'magazine': ('magazine',),
}
# Hand anchors for the first-person rig: centre of the firing-hand grip and the
# support-hand hold under the handguard.
ANCHORS = {
    'grip_hand': (0.0, -0.008, -0.060),
    'support_hand': (0.0, 0.420, BORE - 0.030),
}


# ------------------------------------------------------------ upper receiver

def picatinny(name, y0, y1, base_z, material='anodized'):
    """MIL-STD-1913-style cross-section with transverse recoil slots every 10 mm."""
    section = [(-0.0106, base_z + 0.0095), (0.0106, base_z + 0.0095), (0.0106, base_z + 0.0075),
               (0.0080, base_z + 0.0050), (0.0080, base_z), (-0.0080, base_z),
               (-0.0080, base_z + 0.0050), (-0.0106, base_z + 0.0075)]
    rail = hs.extrude_profile(name, section, y1 - y0, material, axis='Y', offset=(y0 + y1) / 2)
    pitch = 0.010
    count = int((y1 - y0 - 0.006) / pitch)
    start = y0 + (y1 - y0 - (count - 1) * pitch) / 2
    slots = hs.array_join(lambda i, d: hs.box(f'{name}_slot{i}', (0, start + d.y, base_z + 0.0095 - 0.0016), (0.03, 0.0052, 0.0034)),
                          count, (0, pitch, 0), name + '_slots')
    hs.boolean(rail, slots)
    return hs.finish(rail, 0.0004, 1)


def upper_receiver():
    side = hs.fillet([(0.0, SPLIT - 0.0005), (0.0, UPPER_TOP - 0.004), (0.004, UPPER_TOP), (RECEIVER_FRONT, UPPER_TOP),
                      (RECEIVER_FRONT, SPLIT + 0.006), (RECEIVER_FRONT - 0.012, SPLIT - 0.0005)],
                     [0.0, 0.002, 0.0, 0.0, 0.003, 0.0])
    plan = hs.fillet([(-0.0165, -0.01), (0.0165, -0.01), (0.018, 0.02), (0.018, RECEIVER_FRONT - 0.01), (0.0172, RECEIVER_FRONT + 0.01),
                      (-0.0172, RECEIVER_FRONT + 0.01), (-0.018, RECEIVER_FRONT - 0.01), (-0.018, 0.02)], 0.004)
    upper = hs.silhouette('paint_upper', side, plan, 'anodized')
    # Ejection port (right side) opened onto the bolt carrier; lightening flutes on the left.
    port = hs.extrude_profile('port_cut', hs.fillet([(0.095, 0.021), (0.168, 0.021), (0.168, 0.044), (0.095, 0.044)], 0.002), 0.02, 'steel', 'X', offset=0.019)
    flutes = [hs.extrude_profile(f'flute{i}', hs.fillet([(0.06 + i * 0.05, 0.030), (0.095 + i * 0.05, 0.030), (0.095 + i * 0.05, 0.036), (0.06 + i * 0.05, 0.036)], 0.0028), 0.004, 'steel', 'X', offset=-0.0185) for i in range(3)]
    hs.cut(upper, port, *flutes)
    hs.finish(upper, 0.0007, 2)
    bolt = hs.box('bolt_carrier', (0.010, 0.131, BORE + 0.006), (0.012, 0.072, 0.019), 'steel')
    hs.cut(bolt, hs.cylinder('bolt_lug', (0.02, 0.112, BORE + 0.006), (0.0, 0.112, BORE + 0.006), 0.004, segments=16))
    hs.finish(bolt, 0.0006, 1)
    # Dust cover hinged at the port's lower edge, swung open.
    cover = hs.box('dust_cover', (0.0, 0.0, 0.0), (0.0016, 0.078, 0.022), 'anodized')
    cover.location = (0.0215, 0.1315, SPLIT + 0.0045)
    cover.rotation_euler = (0, math.radians(-100), 0)
    hs.apply_all(cover)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    hs.finish(cover, 0.0004, 1)
    deflector = hs.silhouette('deflector', hs.fillet([(0.07, SPLIT + 0.008), (0.090, SPLIT + 0.008), (0.092, UPPER_TOP - 0.004), (0.074, UPPER_TOP - 0.006)], 0.002),
                              [(0.014, 0.065), (0.0235, 0.065), (0.0235, 0.095), (0.014, 0.095)], 'anodized')
    hs.finish(deflector, 0.0006, 2)
    rail = picatinny('paint_rail_upper', 0.002, RECEIVER_FRONT, UPPER_TOP)
    # Ambidextrous T charging handle behind the rail.
    handle_side = hs.fillet([(-0.026, BORE + 0.018), (0.004, BORE + 0.018), (0.004, UPPER_TOP - 0.001), (-0.020, UPPER_TOP - 0.001), (-0.026, BORE + 0.024)], 0.002)
    handle_plan = hs.fillet([(-0.006, -0.026), (0.006, -0.026), (0.006, -0.014), (0.024, -0.020), (0.026, -0.010), (0.008, 0.006),
                             (-0.008, 0.006), (-0.026, -0.010), (-0.024, -0.020), (-0.006, -0.014)], 0.002)
    handle = hs.silhouette('charging_handle', handle_side, handle_plan, 'anodized')
    hs.finish(handle, 0.0005, 2)
    # Barrel nut collar between receiver and handguard.
    collar = hs.lathe('barrel_nut', [(0.0, RECEIVER_FRONT - 0.002), (0.0168, RECEIVER_FRONT - 0.002), (0.0168, RECEIVER_FRONT + 0.010), (0.0, RECEIVER_FRONT + 0.010)], 'steel', 40, centre=(0, 0, BORE))
    hs.finish(collar, 0.0005, 1)
    return [upper, bolt, cover, deflector, rail, handle, collar]


# ------------------------------------------------------------ handguard / barrel

def handguard():
    length = HANDGUARD_FRONT - (RECEIVER_FRONT + 0.008)
    centre_y = RECEIVER_FRONT + 0.008 + length / 2
    outer = hs.fillet([(-0.0225, BORE + 0.027), (0.0225, BORE + 0.027), (0.0235, BORE + 0.006), (0.0175, BORE - 0.022),
                       (-0.0175, BORE - 0.022), (-0.0235, BORE + 0.006)], [0.0055, 0.0055, 0.008, 0.006, 0.006, 0.008])
    inner = hs.fillet([(-0.0195, BORE + 0.0245), (0.0195, BORE + 0.0245), (0.0205, BORE + 0.006), (0.0155, BORE - 0.0195),
                       (-0.0155, BORE - 0.0195), (-0.0205, BORE + 0.006)], [0.001, 0.001, 0.006, 0.005, 0.005, 0.006])
    guard = hs.extrude_profile('paint_handguard', outer, length, 'anodized', 'Y', offset=centre_y)
    bore = hs.extrude_profile('hg_inner', inner, length + 0.02, 'anodized', 'Y', offset=centre_y)
    hs.boolean(guard, bore)
    slots = []
    for i in range(5):
        y = RECEIVER_FRONT + 0.05 + i * 0.058
        slot = hs.fillet([(y, BORE - 0.0005), (y + 0.034, BORE - 0.0005), (y + 0.034, BORE + 0.0075), (y, BORE + 0.0075)], 0.0035)
        slots.append(hs.extrude_profile(f'side_slots{i}', slot, 0.06, 'steel', 'X'))
        if i < 4:
            under = hs.fillet([(-0.0035, y + 0.01), (0.0035, y + 0.01), (0.0035, y + 0.044), (-0.0035, y + 0.044)], 0.0034)
            slots.append(hs.extrude_profile(f'under_slot{i}', under, 0.02, 'steel', 'Z', offset=BORE - 0.022))
    hs.cut(guard, *slots)
    hs.finish(guard, 0.0006, 2)
    rail = picatinny('paint_rail_handguard', RECEIVER_FRONT + 0.012, HANDGUARD_FRONT - 0.004, BORE + 0.026)
    # Sling cup and two cap screws on the left.
    cup = hs.lathe('qd_cup', [(0.0, 0.0), (0.0062, 0.0), (0.0062, 0.0045), (0.0045, 0.0050), (0.0, 0.0050)], 'steel', 24)
    cup.rotation_euler = (0, 0, math.radians(90))
    cup.location = (-0.0235, HANDGUARD_FRONT - 0.03, BORE + 0.004)
    hs.apply_all(cup)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    screws = []
    for y in (RECEIVER_FRONT + 0.022, RECEIVER_FRONT + 0.036):
        head = hs.cylinder(f'screw_{y:.3f}', (-0.0232, y, BORE + 0.012), (-0.0248, y, BORE + 0.012), 0.0032, 'steel', 20)
        hs.cut(head, hs.cylinder('hex', (-0.0255, y, BORE + 0.012), (-0.0238, y, BORE + 0.012), 0.0016, 'steel', 6))
        screws.append(hs.finish(head, 0.0002, 1, weighted=False))
    # Angled hand stop under the front of the handguard.
    stop = hs.silhouette('hand_stop', hs.fillet([(0.500, BORE - 0.0205), (0.546, BORE - 0.0205), (0.546, BORE - 0.026), (0.536, BORE - 0.041), (0.528, BORE - 0.041)],
                                                [0.0, 0.0, 0.003, 0.003, 0.004]),
                         hs.fillet([(-0.0085, 0.49), (0.0085, 0.49), (0.0085, 0.56), (-0.0085, 0.56)], 0.003), 'polymer')
    hs.finish(stop, 0.0010, 2, 40)
    return [guard, rail, cup, stop] + screws


def barrel():
    y0, y1 = RECEIVER_FRONT + 0.006, 0.622
    profile = [(0.0, y0), (0.0098, y0), (0.0098, y0 + 0.05), (0.0086, y0 + 0.056), (0.0086, 0.47), (0.0079, 0.48),
               (0.0079, y1 - 0.004), (0.0074, y1), (0.0, y1)]
    tube = hs.lathe('barrel', profile, 'steel', 32, centre=(0, 0, BORE))
    hs.smooth(tube, 30)
    gas = hs.lathe('gas_block', [(0.0, 0.0), (0.0122, 0.0), (0.0128, 0.002), (0.0128, 0.020), (0.0122, 0.022), (0.0, 0.022)], 'steel', 28, centre=(0, 0.505, BORE))
    hs.smooth(gas, 30)
    # Muzzle brake: chamfered body, three side ports each side, two top vents, open crown.
    brake = hs.lathe('muzzle_brake', [(0.0, 0.618), (0.0098, 0.618), (0.0112, 0.622), (0.0112, MUZZLE_Y - 0.004), (0.0098, MUZZLE_Y), (0.0, MUZZLE_Y)], 'steel', 36, centre=(0, 0, BORE))
    ports = [hs.extrude_profile(f'port{i}', hs.fillet([(0.632 + i * 0.012, BORE - 0.0042), (0.640 + i * 0.012, BORE - 0.0042), (0.640 + i * 0.012, BORE + 0.0042), (0.632 + i * 0.012, BORE + 0.0042)], 0.0015), 0.04, 'steel', 'X') for i in range(3)]
    vents = [hs.cylinder(f'vent{i}', (0, y, BORE), (0, y, BORE + 0.02), 0.0019, 'steel', 16) for i, y in enumerate((0.636, 0.648))]
    crown = hs.cylinder('crown', (0, MUZZLE_Y - 0.02, BORE), (0, MUZZLE_Y + 0.01, BORE), 0.0041, 'steel', 24)
    hs.cut(brake, *ports, *vents, crown)
    hs.finish(brake, 0.0004, 1)
    return [tube, gas, brake]


# ------------------------------------------------------------ lower, grip, controls

def lower_receiver():
    side = hs.fillet([(-0.004, SPLIT), (0.214, SPLIT), (0.214, SPLIT - 0.011), (0.196, SPLIT - 0.017), (0.158, SPLIT - 0.020),
                      (0.156, -0.058), (0.160, -0.066), (0.072, -0.066), (0.075, -0.058), (0.074, SPLIT - 0.030),
                      (0.030, SPLIT - 0.030), (-0.004, SPLIT - 0.026)],
                     [0.0, 0.0, 0.002, 0.004, 0.003, 0.002, 0.0015, 0.0015, 0.002, 0.004, 0.003, 0.002])
    plan = hs.fillet([(-0.017, -0.01), (0.017, -0.01), (0.017, 0.22), (-0.017, 0.22)], 0.003)
    lower = hs.silhouette('paint_lower', side, plan, 'anodized')
    # Flared magazine well lip and the hollow the magazine seats into.
    lip = hs.silhouette('mag_well_lip', hs.fillet([(0.068, -0.059), (0.164, -0.059), (0.168, -0.068), (0.064, -0.068)], 0.0015),
                        hs.fillet([(-0.0215, 0.06), (0.0215, 0.06), (0.0215, 0.172), (-0.0215, 0.172)], 0.004), 'anodized')
    hs.boolean(lower, lip, 'UNION')
    well = hs.extrude_profile('well', hs.fillet([(-0.0128, 0.083), (0.0128, 0.083), (0.0128, 0.149), (-0.0128, 0.149)], 0.003), 0.16, 'steel', 'Z', offset=-0.03)
    hs.boolean(lower, well)
    hs.finish(lower, 0.0007, 2)
    # Integral trigger guard loop.
    guard_side = [(0.026, SPLIT - 0.026), (0.074, SPLIT - 0.026), (0.074, -0.038), (0.068, -0.0425), (0.028, -0.0425), (0.020, -0.034),
                  (0.026, -0.034), (0.031, -0.0385), (0.067, -0.0385), (0.069, -0.034), (0.069, SPLIT - 0.026)]
    guard = hs.extrude_profile('trigger_guard', guard_side, 0.010, 'anodized', 'X')
    hs.finish(guard, 0.0006, 2)
    trigger = hs.extrude_profile('trigger', hs.fillet([(0.049, SPLIT - 0.026), (0.055, SPLIT - 0.026), (0.054, -0.024), (0.050, -0.033), (0.045, -0.035), (0.047, -0.029), (0.049, -0.022)], 0.001), 0.0055, 'steel', 'X')
    hs.finish(trigger, 0.0003, 1)
    # Pistol grip: raked, palm swell from the plan view, front finger ridge.
    grip_side = hs.fillet([(-0.006, SPLIT - 0.024), (0.026, SPLIT - 0.024), (0.022, -0.030), (0.012, -0.060), (0.010, -0.075), (0.006, -0.090),
                           (-0.002, -0.118), (-0.036, -0.121), (-0.038, -0.112), (-0.024, -0.060)],
                          [0.002, 0.004, 0.006, 0.006, 0.006, 0.006, 0.006, 0.006, 0.006, 0.01])
    grip_plan = hs.fillet([(-0.0135, -0.05), (0.0135, -0.05), (0.0155, -0.01), (0.0135, 0.03), (-0.0135, 0.03), (-0.0155, -0.01)], 0.006)
    grip = hs.silhouette('grip', grip_side, grip_plan, 'polymer')
    hs.finish(grip, 0.0018, 3, 40)
    # Controls: rotary selector (left), magazine release with fence (right), bolt catch, pins.
    selector = hs.silhouette('selector', hs.fillet([(0.018, -0.006), (0.034, -0.009), (0.035, -0.004), (0.020, 0.001)], 0.002),
                             [(-0.0198, 0.0), (-0.0172, 0.0), (-0.0172, 0.04), (-0.0198, 0.04)], 'steel')
    selector_hub = hs.cylinder('selector_hub', (-0.0175, 0.020, -0.0035), (-0.0196, 0.020, -0.0035), 0.0048, 'steel', 24)
    release = hs.cylinder('mag_release', (0.0170, 0.072, -0.016), (0.0198, 0.072, -0.016), 0.0042, 'steel', 24)
    fence = hs.extrude_profile('release_fence', hs.fillet([(0.064, -0.026), (0.080, -0.026), (0.080, -0.008), (0.064, -0.008)], 0.003), 0.003, 'anodized', 'X', offset=0.0175)
    hs.cut(fence, hs.cylinder('fence_hole', (0.016, 0.072, -0.016), (0.021, 0.072, -0.016), 0.0052, 'steel', 24))
    catch = hs.silhouette('bolt_catch', hs.fillet([(0.150, SPLIT - 0.004), (0.172, SPLIT - 0.006), (0.170, -0.012), (0.152, -0.010)], 0.0015),
                          [(-0.0198, 0.14), (-0.0172, 0.14), (-0.0172, 0.18), (-0.0198, 0.18)], 'steel')
    pins = [hs.cylinder(f'pin{i}', (-0.0178, y, z), (0.0178, y, z), 0.0031, 'steel', 18) for i, (y, z) in enumerate(((0.004, SPLIT - 0.008), (0.206, SPLIT - 0.006)))]
    parts = [selector, selector_hub, release, fence, catch] + pins
    for p in parts:
        hs.finish(p, 0.0003, 1, weighted=False)
    return [lower, guard, trigger, grip] + parts


def stock():
    tube = hs.lathe('buffer_tube', [(0.0, -0.205), (0.0128, -0.205), (0.0148, -0.201), (0.0148, -0.010), (0.0, -0.010)], 'anodized', 36, centre=(0, 0, BORE))
    hs.smooth(tube, 30)
    nut = hs.lathe('castle_nut', [(0.0, -0.012), (0.0178, -0.012), (0.0178, -0.002), (0.0, -0.002)], 'steel', 36, centre=(0, 0, BORE))
    notches = [hs.box(f'notch{i}', (0, -0.007, BORE), (0.006, 0.012, 0.05), 'steel') for i in range(3)]
    for i, n in enumerate(notches):
        n.rotation_euler = (0, math.radians(i * 60), 0)
        n.location = (0, 0, 0)
        hs.apply_all(n)
    for n in notches:
        hs.boolean(nut, n)
    hs.finish(nut, 0.0004, 1)
    body_side = hs.fillet([(-0.262, BORE - 0.070), (-0.240, BORE - 0.070), (-0.100, BORE - 0.023), (-0.094, BORE - 0.019),
                           (-0.094, BORE + 0.021), (-0.118, BORE + 0.024), (-0.152, BORE + 0.033), (-0.246, BORE + 0.037),
                           (-0.262, BORE + 0.035)],
                          [0.004, 0.006, 0.006, 0.003, 0.003, 0.008, 0.02, 0.006, 0.004])
    body_plan = hs.fillet([(-0.021, -0.27), (0.021, -0.27), (0.0215, -0.21), (0.0185, -0.12), (0.0175, -0.09),
                           (-0.0175, -0.09), (-0.0185, -0.12), (-0.0215, -0.21)], 0.004)
    body = hs.silhouette('stock_body', body_side, body_plan, 'polymer')
    # Triangular lightening window under the tube sleeve leaves a rear frame and a diagonal strut.
    window = hs.extrude_profile('stock_window', hs.fillet([(-0.241, BORE - 0.053), (-0.241, BORE - 0.024), (-0.142, BORE - 0.024)],
                                                          [0.006, 0.006, 0.004]), 0.06, 'polymer', 'X')
    tube_hole = hs.lathe('tube_hole', [(0.0, -0.30), (0.0152, -0.30), (0.0152, -0.05), (0.0, -0.05)], 'steel', 36, centre=(0, 0, BORE))
    # Sling slot through the rear frame and a recessed cheek panel on each side.
    sling = hs.extrude_profile('sling_slot', hs.fillet([(-0.256, BORE - 0.064), (-0.246, BORE - 0.064), (-0.246, BORE - 0.036), (-0.256, BORE - 0.036)], 0.0035), 0.06, 'polymer', 'X')
    panels = [hs.extrude_profile(f'cheek_panel{side}', hs.fillet([(-0.236, BORE + 0.006), (-0.160, BORE + 0.006), (-0.150, BORE + 0.024), (-0.236, BORE + 0.029)], 0.004),
                                 0.004, 'polymer', 'X', offset=side * 0.0215) for side in (-1, 1)]
    hs.cut(body, window, tube_hole, sling, *panels)
    hs.finish(body, 0.0014, 3, 40)
    lever = hs.silhouette('stock_lever', hs.fillet([(-0.135, BORE - 0.026), (-0.104, BORE - 0.026), (-0.100, BORE - 0.019), (-0.135, BORE - 0.019)], 0.002),
                          hs.fillet([(-0.006, -0.14), (0.006, -0.14), (0.006, -0.098), (-0.006, -0.098)], 0.002), 'steel')
    hs.finish(lever, 0.0004, 1)
    pad = hs.silhouette('butt_pad', hs.fillet([(-0.274, BORE - 0.074), (-0.261, BORE - 0.074), (-0.261, BORE + 0.037), (-0.274, BORE + 0.035)], 0.004),
                        hs.fillet([(-0.0225, -0.276), (0.0225, -0.276), (0.0225, -0.258), (-0.0225, -0.258)], 0.004), 'rubber')
    ridges = [hs.box(f'pad_ridge{i}', (0, -0.2745, BORE - 0.066 + i * 0.012), (0.05, 0.003, 0.0035), 'rubber') for i in range(9)]
    hs.cut(pad, *ridges)
    hs.finish(pad, 0.001, 2)
    return [tube, nut, body, lever, pad]


# ------------------------------------------------------------ optic, magazine

def optic():
    y0, y1 = 0.060, 0.128
    base_z = RAIL_TOP
    mount = hs.silhouette('optic_mount', hs.fillet([(y0, base_z - 0.004), (y1, base_z - 0.004), (y1, base_z + 0.006), (y0, base_z + 0.006)], 0.0015),
                          hs.fillet([(-0.0135, y0), (0.0135, y0), (0.0135, y1), (-0.0135, y1)], 0.002), 'anodized')
    hood_side = hs.fillet([(y0 + 0.004, base_z + 0.006), (y1, base_z + 0.006), (y1, base_z + 0.040), (y1 - 0.016, base_z + 0.046),
                           (y0 + 0.016, base_z + 0.046), (y0 + 0.004, base_z + 0.034)], [0.0, 0.002, 0.004, 0.006, 0.006, 0.004])
    hood_plan = hs.fillet([(-0.0145, y0), (0.0145, y0), (0.0155, y1), (-0.0155, y1)], 0.003)
    hood = hs.silhouette('optic_body', hood_side, hood_plan, 'anodized')
    tunnel = hs.extrude_profile('optic_tunnel', hs.fillet([(-0.0112, base_z + 0.012), (0.0112, base_z + 0.012), (0.0112, base_z + 0.039), (-0.0112, base_z + 0.039)], 0.0045), 0.2, 'steel', 'Y', offset=(y0 + y1) / 2)
    hs.boolean(hood, tunnel)
    knob = hs.cylinder('optic_knob', (0.0150, 0.088, base_z + 0.022), (0.0195, 0.088, base_z + 0.022), 0.0065, 'anodized', 24)
    clamp = hs.cylinder('optic_clamp', (-0.0170, 0.094, base_z + 0.001), (-0.0205, 0.094, base_z + 0.001), 0.0048, 'steel', 6)
    lens = hs.box('optic_lens', (0, y1 - 0.010, base_z + 0.0255), (0.0226, 0.0012, 0.0272), 'glass')
    for p in (mount, hood):
        hs.finish(p, 0.0007, 2)
    for p in (knob, clamp):
        hs.finish(p, 0.0004, 1, weighted=False)
    reticle = bpy.data.objects.new('reticle', None)
    hs.link(reticle)
    reticle.location = (0, y1 - 0.0105, base_z + 0.0255)
    return [mount, hood, knob, clamp, lens]


def magazine():
    """Curved polymer magazine lofted from rounded sections; pivot at its seated top."""
    import bmesh
    bm = bmesh.new()
    sections = []
    steps = 14
    for i in range(steps + 1):
        t = i / steps
        z = 0.004 - t * 0.170
        y_mid = 0.116 + 0.026 * t * t
        half_depth = 0.0315 + 0.003 * t
        half_w = 0.0118
        ring = hs.fillet([(-half_w, y_mid - half_depth), (half_w, y_mid - half_depth), (half_w, y_mid + half_depth), (-half_w, y_mid + half_depth)], 0.003, 3)
        sections.append([bm.verts.new((x, y, z)) for x, y in ring])
    count = len(sections[0])
    for a, b in zip(sections, sections[1:]):
        for k in range(count):
            bm.faces.new((a[k], a[(k + 1) % count], b[(k + 1) % count], b[k]))
    bm.faces.new(sections[0])
    bm.faces.new(sections[-1][::-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    body = hs.from_bmesh('magazine', bm, 'polymer')
    hs.smooth(body, 40)
    ribs = []
    for i in range(6):
        t = (i + 6) / steps
        z = 0.004 - t * 0.170 + 0.004
        y_mid = 0.116 + 0.026 * t * t
        ribs.append(hs.box(f'mag_rib{i}', (0, y_mid, z), (0.0255, 0.040, 0.0022), 'polymer'))
    floor = hs.silhouette('mag_floor', hs.fillet([(0.116 + 0.026 - 0.040, -0.177), (0.116 + 0.026 + 0.040, -0.177), (0.116 + 0.026 + 0.038, -0.165), (0.116 + 0.026 - 0.038, -0.165)], 0.003),
                          hs.fillet([(-0.0145, 0.09), (0.0145, 0.09), (0.0145, 0.19), (-0.0145, 0.19)], 0.004), 'polymer')
    hs.finish(floor, 0.0012, 2)
    for r in ribs:
        hs.finish(r, 0.0009, 2, weighted=False)
    cartridge = hs.lathe('top_round', [(0.0, 0.0), (0.0048, 0.0), (0.0048, 0.040), (0.0028, 0.050), (0.0028, 0.057), (0.0, 0.057)], 'brass', 20, centre=(0.003, 0.088, 0.006))
    mag = hs.join([body, floor, cartridge] + ribs, 'magazine')
    # Pivot at the seated top centre so reload animation rotates/slides naturally.
    bpy.context.scene.cursor.location = (0, 0.116, 0.004)
    hs.select_only(mag)
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    return mag


def build():
    hs.reset_scene()
    static = upper_receiver() + handguard() + barrel() + lower_receiver() + stock() + optic()
    mag = magazine()
    for name, at in (('muzzle', (0, MUZZLE_Y, BORE)), ('ejection', (0.024, 0.13, BORE + 0.006))):
        empty = bpy.data.objects.new(name, None)
        hs.link(empty)
        empty.location = at
    return static, mag


if __name__ == '__main__':
    static, mag = build()
    meshes = [o for o in bpy.data.objects if o.type == 'MESH']
    print('RELAY_AR objects=%d tris=%d' % (len(meshes), hs.triangles(meshes)))
    if '--' in sys.argv:
        out = sys.argv[sys.argv.index('--') + 1]
        bpy.ops.export_scene.gltf(filepath=out, export_format='GLB', export_apply=True, export_extras=True)
