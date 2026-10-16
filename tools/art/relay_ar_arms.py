"""Rigged first-person arms for the Relay AR: gloved hands and jacket sleeves.

Original geometry. Each arm is modelled once, as a right arm in a relaxed rest pose,
from anatomical landmarks (adult hand, about 19 cm wrist to fingertip): carpal block,
four metacarpals that give the palm its arch and the back of the hand its tendon
ridges, thenar and hypothenar masses, and tapered, flattened phalanges with dorsal
knuckles and palmar pads. Signed-distance shapes blend these with smooth unions, so
the web between the fingers and the knuckle line form without seams. A tactical glove
is the hand dilated by 1 mm with a moulded knuckle guard, padded first phalanges,
side seams, a cuff and a hook-and-loop strap; the jacket sleeve is a hollow cloth tube
with a hem, a seam and compression folds.

The same landmarks place the bones: forearm, hand, three bones per finger and three
for the thumb. The left arm is the mirror image. See build() for the stages.

Space: metres, Blender Z up. Hand-local frame for the right hand: wrist joint at the
origin, +Y toward the fingers, +Z the back of the hand, thumb toward -X.
"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sdf  # noqa: E402

GLOVE = 0.0010          # glove thickness added to the skin
FLAT = 0.84             # finger section, front to back over side to side
X, Y, Z = np.eye(3)


def unit(v):
    v = np.asarray(v, dtype=np.float64)
    return v / np.linalg.norm(v)


def rotate(v, axis, angle):
    """Rodrigues rotation of `v` about unit `axis`."""
    axis = unit(axis)
    return v * math.cos(angle) + np.cross(axis, v) * math.sin(angle) + axis * np.dot(axis, v) * (1 - math.cos(angle))


# ------------------------------------------------------------------ anatomy

# Knuckle (MCP) joint centres. The arc puts the middle finger farthest out and the
# little finger about 13 mm back.
MCP = {'index': (-0.0255, 0.0905, 0.0010), 'middle': (-0.0050, 0.0945, 0.0015),
       'ring': (0.0150, 0.0905, 0.0005), 'pinky': (0.0330, 0.0810, -0.0020)}
# Proximal, middle and distal segment lengths (joint to joint; the last ends at the
# centre of the fingertip's rounded end).
LENGTHS = {'index': (0.0400, 0.0235, 0.0170), 'middle': (0.0445, 0.0275, 0.0185),
           'ring': (0.0420, 0.0265, 0.0180), 'pinky': (0.0330, 0.0195, 0.0160)}
# Half-widths at the MCP, PIP and DIP joints and the tip.
RADII = {'index': (0.0098, 0.0090, 0.0081, 0.0074), 'middle': (0.0101, 0.0093, 0.0083, 0.0076),
         'ring': (0.0096, 0.0088, 0.0079, 0.0072), 'pinky': (0.0086, 0.0079, 0.0072, 0.0066)}
# Fingers fan out from the knuckles.
SPREAD = {'index': (-0.10, 1, 0), 'middle': (-0.02, 1, 0), 'ring': (0.07, 1, 0), 'pinky': (0.17, 1, 0)}
# Metacarpal bases at the carpus.
CARPAL = {'index': (-0.0160, 0.0240, 0.0035), 'middle': (-0.0040, 0.0255, 0.0045),
          'ring': (0.0090, 0.0240, 0.0035), 'pinky': (0.0205, 0.0210, 0.0010)}
REST_CURL = (math.radians(10), math.radians(18), math.radians(10))
THUMB_CMC = (-0.0215, 0.0215, -0.0075)
THUMB_DIRS = ((-0.55, 0.78, -0.30), (-0.30, 0.90, -0.32), (-0.15, 0.95, -0.27))
THUMB_LENGTHS = (0.042, 0.028, 0.022)
THUMB_RADII = (0.0122, 0.0100, 0.0089, 0.0076)
THUMB_NAIL = (-0.75, 0.0, 0.66)       # the thumbnail faces out and up
ELBOW = (0.002, -0.262, -0.010)
FINGERS = ('index', 'middle', 'ring', 'pinky')
# Glove cuff: from over the wrist to under the sleeve hem.
CUFF = ((0.0, 0.006, 0.0), (0.0, -0.060, -0.002))
CUFF_RADII = (0.0335, 0.0352)
CUFF_FLAT = 0.78
GEAR = ('shell', 'strap', 'cuff', 'seam', 'tip', 'pad')    # parts added outside the glove's skin dilation


def finger_chain(name, curls=REST_CURL):
    """Joints (MCP, PIP, DIP, tip) and the dorsal direction of each segment."""
    d = unit(SPREAD[name])
    up = unit(np.cross(d, np.cross(Z, d)))
    joints = [np.asarray(MCP[name], dtype=np.float64)]
    ups = []
    for length, curl in zip(LENGTHS[name], curls):
        axis = unit(np.cross(up, d))
        d = rotate(d, axis, curl)
        up = rotate(up, axis, curl)
        joints.append(joints[-1] + d * length)
        ups.append(up)
    return joints, ups


def thumb_chain():
    joints = [np.asarray(THUMB_CMC, dtype=np.float64)]
    ups = []
    for direction, length in zip(THUMB_DIRS, THUMB_LENGTHS):
        d = unit(direction)
        up = unit(np.asarray(THUMB_NAIL) - d * np.dot(THUMB_NAIL, d))
        joints.append(joints[-1] + d * length)
        ups.append(up)
    return joints, ups


def skeleton():
    """Rest-pose joint positions of the right arm in the hand-local frame."""
    joints = {'elbow': np.asarray(ELBOW), 'wrist': np.zeros(3), 'thumb': thumb_chain()[0]}
    for name in FINGERS:
        joints[name] = finger_chain(name)[0]
    return joints


# ------------------------------------------------------------------ glove

def _knuckle_axes():
    across = unit(np.asarray(MCP['index']) - np.asarray(MCP['pinky']))
    up = unit(Z - across * np.dot(Z, across))
    return np.stack((across, np.cross(up, across), up))


def glove_shapes():
    """(adds, subs) for the gloved right hand, cuff and strap."""
    adds = []
    # Carpus and palm: wrist block, metacarpals, palm filler, thenar and hypothenar.
    adds.append((sdf.ellipsoid_shape((0.0015, 0.0090, -0.0005), np.eye(3), (0.0290, 0.0200, 0.0170), 'fabric'), 0.012))
    for name in FINGERS:
        r = RADII[name][0]
        adds.append((sdf.cone_shape(CARPAL[name], MCP[name], r * 1.05, r, flat=0.80, region='fabric'), 0.010))
    adds.append((sdf.box_shape((0.0030, 0.0520, -0.0040), np.eye(3), (0.0330, 0.0330, 0.0100), 0.0090, 'palm'), 0.008))
    # Extensor tendons: a raised cord along the back of each metacarpal, from the carpus to under the knuckle's dome,
    # so the back of the hand reads as tendons over bone and not as a smooth slab (the glove's fabric follows them).
    for name in FINGERS:
        r = RADII[name][0]
        a = np.asarray(CARPAL[name]) + np.array((0.0, 0.004, r * 0.74))
        b = np.asarray(MCP[name]) + np.array((0.0, -0.004, r * 0.80))
        adds.append((sdf.cone_shape(a, b, 0.0027, 0.0025, flat=0.75, region='fabric'), 0.0040))
    thumb_axis = unit(THUMB_DIRS[0])
    thenar_axes = np.stack((unit(np.cross(thumb_axis, Z)), thumb_axis, unit(np.cross(np.cross(thumb_axis, Z), thumb_axis))))
    adds.append((sdf.ellipsoid_shape((-0.0215, 0.0400, -0.0085), thenar_axes, (0.0150, 0.0270, 0.0125), 'palm'), 0.010))
    adds.append((sdf.ellipsoid_shape((0.0265, 0.0450, -0.0060), np.eye(3), (0.0110, 0.0300, 0.0110), 'palm'), 0.010))
    # Forearm inside the cuff.
    adds.append((sdf.cone_shape((0.0, 0.004, 0.0), (0.001, -0.050, -0.002), 0.0265, 0.0285, flat=0.74, region='fabric'), 0.010))
    # Fingers: tapered flattened phalanges, a dorsal knuckle at each joint, palmar pads.
    for name in FINGERS:
        joints, ups = finger_chain(name)
        radii = RADII[name]
        for i in range(3):
            # Shafts are narrower than the joints at either end (the joints read as knuckles).
            shaft = sdf.cone_shape(joints[i], joints[i + 1], radii[i] * 0.90, radii[i + 1] * 0.90, ups[i], FLAT, 'fabric')
            adds.append((shaft, 0.0025))
            mid = (joints[i] + joints[i + 1]) / 2
            along = unit(joints[i + 1] - joints[i])
            pad_axes = np.stack((unit(np.cross(along, ups[i])), along, ups[i]))
            adds.append((sdf.ellipsoid_shape(mid - ups[i] * radii[i] * 0.42, pad_axes, (radii[i] * 0.80, np.linalg.norm(joints[i + 1] - joints[i]) * 0.42, radii[i] * 0.55), 'fabric'), 0.003))
        for i in (1, 2):
            axes = np.stack((unit(np.cross(unit(joints[i + 1] - joints[i]), ups[i])), unit(joints[i + 1] - joints[i]), ups[i]))
            adds.append((sdf.ellipsoid_shape(joints[i] + ups[i] * radii[i] * 0.38, axes, (radii[i] * 0.78, radii[i] * 0.70, radii[i] * 0.62), 'fabric'), 0.0025))
            # Joint condyles: the finger is widest across the joint.
            adds.append((sdf.ellipsoid_shape(joints[i], axes, (radii[i] * 1.10, radii[i] * 0.66, radii[i] * 0.88), 'fabric'), 0.0020))
    # Thumb: metacarpal sunk into the thenar mass, then two phalanges. The first web
    # (adductor and first dorsal interosseous) ties its metacarpal to the index's.
    joints, ups = thumb_chain()
    web_a = joints[0] + (joints[1] - joints[0]) * 0.92
    web_b = np.asarray(CARPAL['index']) + (np.asarray(MCP['index']) - np.asarray(CARPAL['index'])) * 0.55
    adds.append((sdf.cone_shape(web_a, web_b, 0.0085, 0.0080, flat=0.62, region='fabric'), 0.012))
    for i in range(3):
        adds.append((sdf.cone_shape(joints[i], joints[i + 1], THUMB_RADII[i], THUMB_RADII[i + 1], ups[i], 0.88 if i < 2 else 0.80, 'fabric'), 0.006 if i == 0 else 0.0025))
    for i in (1, 2):
        along = unit(joints[i + 1] - joints[i])
        axes = np.stack((unit(np.cross(along, ups[i])), along, ups[i]))
        adds.append((sdf.ellipsoid_shape((joints[i] + joints[i + 1]) / 2 - ups[i] * THUMB_RADII[i] * 0.40, axes, (THUMB_RADII[i] * 0.82, THUMB_LENGTHS[i] * 0.45, THUMB_RADII[i] * 0.58), 'fabric'), 0.003))
    # Glove: moulded knuckle guard over the MCP line with a dome per knuckle.
    kn = _knuckle_axes()
    centre = (np.asarray(MCP['index']) + np.asarray(MCP['pinky'])) / 2 + np.array((0.0, -0.0035, 0.0115))
    adds.append((sdf.box_shape(centre + np.array((0.0, 0.0, 0.0004)), kn, (0.0335, 0.0105, 0.0032), 0.0040, 'shell'), 0.0020))
    for name in FINGERS:
        adds.append((sdf.ellipsoid_shape(np.asarray(MCP[name]) + np.array((0, -0.001, RADII[name][0] * 1.20)), kn, (0.0074, 0.0066, 0.0042), 'shell'), 0.0020))
        joints, ups = finger_chain(name)
        mid = joints[0] + (joints[1] - joints[0]) * 0.55
        along = unit(joints[1] - joints[0])
        pad = np.stack((unit(np.cross(along, ups[0])), along, ups[0]))
        adds.append((sdf.box_shape(mid + ups[0] * RADII[name][1] * 0.86, pad, (RADII[name][1] * 0.64, LENGTHS[name][0] * 0.28, 0.0024), 0.0018, 'shell'), 0.0010))

    # Fingertip reinforcement (suede), thumb tip included: a cap over the last phalanx, a touch proud of the skin.
    for name in FINGERS:
        joints, ups = finger_chain(name)
        along = unit(joints[3] - joints[2])
        axes = np.stack((unit(np.cross(along, ups[2])), along, ups[2]))
        length = np.linalg.norm(joints[3] - joints[2])
        adds.append((sdf.ellipsoid_shape(joints[2] + along * length * 0.74, axes, (RADII[name][3] * 1.03, length * 0.62 + 0.0030, RADII[name][3] * 0.88), 'tip'), 0.0004))
    t_joints, t_ups = thumb_chain()
    t_along = unit(t_joints[3] - t_joints[2])
    t_axes = np.stack((unit(np.cross(t_along, t_ups[2])), t_along, t_ups[2]))
    adds.append((sdf.ellipsoid_shape(t_joints[2] + t_along * THUMB_LENGTHS[2] * 0.70, t_axes, (THUMB_RADII[3] * 1.04, THUMB_LENGTHS[2] * 0.62 + 0.0030, THUMB_RADII[3] * 0.92), 'tip'), 0.0004))
    # Piping seams down both sides of every finger segment (thread, a lighter line at gameplay size).
    for name in FINGERS:
        joints, ups = finger_chain(name)
        for sign in (-1, 1):
            for i in range(3):
                side = unit(np.cross(unit(joints[i + 1] - joints[i]), ups[i])) * sign
                r0, r1 = RADII[name][i] * 0.92 + GLOVE, RADII[name][i + 1] * 0.92 + GLOVE
                a = joints[i] + side * r0 + (unit(joints[i + 1] - joints[i]) * 0.0020 if i > 0 else 0)
                b = joints[i + 1] + side * r1 - (unit(joints[i + 1] - joints[i]) * 0.0020 if i < 2 else 0)
                adds.append((sdf.cone_shape(a, b, 0.00115, 0.00115, region='seam'), 0.0004))
    for i in range(2):
        for sign in (-1, 1):
            side = unit(np.cross(unit(t_joints[i + 1] - t_joints[i]), t_ups[i])) * sign
            a = t_joints[i] + side * (THUMB_RADII[i] * 0.90 + GLOVE)
            b = t_joints[i + 1] + side * (THUMB_RADII[i + 1] * 0.90 + GLOVE)
            adds.append((sdf.cone_shape(a, b, 0.00115, 0.00115, region='seam'), 0.0004))
    # A stitched line across the back of the hand just behind the knuckle guard, and one round the cuff's top edge.
    behind = centre + np.array((0.0, -0.0112, -0.0030))
    adds.append((sdf.cone_shape(behind + kn[0] * 0.0300, behind - kn[0] * 0.0300, 0.00105, 0.00105, region='seam'), 0.0004))
    adds.append((sdf.torus_shape((0.0, CUFF[0][1] - 0.0040, 0.0), Y, CUFF_RADII[0] + 0.0004, 0.00110, flat=CUFF_FLAT, region='seam'), 0.0004))
    # Palm: a darker rubberised pad across the heel of the hand.
    adds.append((sdf.ellipsoid_shape((0.0040, 0.0330, -0.0105), np.eye(3), (0.0290, 0.0210, 0.0050), 'pad'), 0.0020))
    # Cuff (flat ended, over the wrist) and a raised hook-and-loop strap with its tab.
    adds.append((sdf.capped_shape(CUFF[0], CUFF[1], CUFF_RADII[0], CUFF_RADII[1], flat=CUFF_FLAT, rounding=0.0025, region='cuff'), 0.006))
    adds.append((sdf.capped_shape((0.0, -0.019, 0.0), (0.0, -0.043, -0.001), CUFF_RADII[1] + 0.0028, CUFF_RADII[1] + 0.0030, flat=CUFF_FLAT, rounding=0.0012, region='strap'), 0.0008))
    adds.append((sdf.box_shape((0.0345, -0.031, 0.0040), np.eye(3), (0.0045, 0.0110, 0.0130), 0.0022, 'strap'), 0.0010))
    subs = []
    # Side seams along each finger and round the cuff (high-poly detail for the bake).
    for name in FINGERS:
        joints, ups = finger_chain(name)
        for sign in (-1, 1):
            for i in range(3):
                side = unit(np.cross(unit(joints[i + 1] - joints[i]), ups[i])) * sign
                r0, r1 = RADII[name][i] + GLOVE, RADII[name][i + 1] + GLOVE
                a = joints[i] + side * r0
                b = joints[i + 1] + side * r1 * (0.92 if i == 2 else 1.0)
                ext = unit(b - a) * 0.0025
                subs.append((sdf.cone_shape(a - ext * (i > 0), b + ext * (i < 2), 0.00055, 0.00055), 0.0004))
    # Palmar flexion creases at the base of each finger and across the PIP and DIP joints:
    # short grooves across the palm side, where a glove folds when the finger bends.
    for name in FINGERS:
        joints, ups = finger_chain(name)
        for i in (0, 1, 2):
            along = unit(joints[i + 1] - joints[i]) if i < 3 else unit(joints[i] - joints[i - 1])
            side = unit(np.cross(along, ups[i]))
            r = RADII[name][i] * 0.94 + GLOVE
            centre = joints[i] + along * (0.004 if i == 0 else 0.0) - ups[i] * r * 0.92
            subs.append((sdf.cone_shape(centre - side * r * 0.62, centre + side * r * 0.62, 0.00065, 0.00065), 0.0005))
    for t in (0.09, 0.93):
        y = CUFF[0][1] + (CUFF[1][1] - CUFF[0][1]) * t
        r = CUFF_RADII[0] + (CUFF_RADII[1] - CUFF_RADII[0]) * t
        subs.append((sdf.torus_shape((0.0, y, 0.0), Y, r, 0.0006, flat=CUFF_FLAT), 0.0003))
    return adds, subs


def glove_distance(P, shapes=None):
    adds, subs = shapes or glove_shapes()
    skin = [(s, k) for s, k in adds if s.region not in GEAR]
    gear = [(s, k) for s, k in adds if s.region in GEAR]
    d = sdf.compose(P, skin) - GLOVE
    for s, k in gear:
        m = s.mask(P, k + 0.002)
        if m.any():
            d[m] = sdf.smin(d[m], s.fn(P[m]), k)
    for s, k in subs:
        m = s.mask(P, k + 0.002)
        if m.any():
            d[m] = sdf.smax(d[m], -s.fn(P[m]), k)
    # The cuff ends square under the sleeve, with a rounded edge.
    return sdf.smax(d, -0.0600 - P[:, 1], 0.003)


def glove_bounds(margin=0.016):
    pts = np.vstack([np.atleast_2d(v) for k, v in skeleton().items() if k != 'elbow'])
    lo, hi = pts.min(0) - margin, pts.max(0) + margin
    lo[1] = -0.068
    hi[2] = max(hi[2], 0.036)
    lo[2] = min(lo[2], -0.040)
    lo[0] = min(lo[0], -0.045)
    hi[0] = max(hi[0], 0.050)
    return lo, hi


# ------------------------------------------------------------------ sleeve

SLEEVE_HEM = -0.034          # where the sleeve ends over the glove cuff (hand-local y)
SLEEVE_END = -0.400          # well past the elbow, so no framing shows its end
HEM_BAND = 0.013             # rolled hem
SEAM_ANGLE = math.radians(-60)   # seam along the ulnar underside


def _sleeve_frame():
    axis = unit(np.asarray(ELBOW) - np.zeros(3))
    return sdf.frame(axis, Z)       # rows: side, along (wrist to elbow), up


def sleeve_radius(t, theta):
    """Outer radius at axial distance `t` (m from the hem) and angle `theta`."""
    span = abs(SLEEVE_END - SLEEVE_HEM)
    u = np.clip(t / span, 0, 1)
    base = 0.0418 + 0.0105 * u ** 0.8                       # loose over the wrist, fuller at the elbow
    hem = 0.0014 * np.exp(-((t - HEM_BAND * 0.5) / (HEM_BAND * 0.45)) ** 4)
    # Compression folds: bunched rings above the hem, diagonal folds up the forearm,
    # and a deeper set at the inside of the elbow (theta near -90 degrees, palm side).
    # Phase and depth vary with angle and length, so no fold repeats evenly.
    wobble = 1.9 * np.sin(2.3 * theta + 0.7) + 1.1 * np.sin(5.1 * theta + 2.0) + 0.9 * np.sin(t * 37 + 1.3 * theta)
    depth = 0.55 + 0.45 * np.sin(1.7 * theta + t * 23 + 0.4) * np.sin(3.1 * theta - t * 41 + 1.9)
    bunch = np.exp(-((t - 0.030) / 0.020) ** 2) * 0.0023 * depth * np.maximum(0, np.sin(t * 410 + 1.7 * theta + 0.6 + wobble)) ** 3
    diag = 0.0012 * np.clip((t - 0.040) / 0.03, 0, 1) * depth * np.maximum(0, np.sin(t * 150 - 2.0 * theta + 1.1 + 0.8 * wobble + 1.4 * np.sin(t * 19))) ** 4
    elbow = 0.0030 * np.exp(-((t - 0.235) / 0.035) ** 2) * np.exp(-((((theta + math.pi / 2) + math.pi) % (2 * math.pi) - math.pi) / 0.9) ** 2) * np.maximum(0, np.sin(t * 260 + 0.4 * theta)) ** 2
    return base + hem + bunch + diag + elbow


def sleeve_distance(P, detail=True):
    R = _sleeve_frame()
    q = P @ R.T
    t = q[:, 1] + SLEEVE_HEM * np.linalg.norm(np.asarray(ELBOW)) / abs(ELBOW[1])
    x, z = q[:, 0], q[:, 2] / 0.86          # forearm section is oval
    rho = np.hypot(x, z)
    theta = np.arctan2(z, x)
    d = (rho - sleeve_radius(t, theta)) * 0.93
    span = abs(SLEEVE_END - SLEEVE_HEM)
    d = sdf.smax(d, -t, 0.002)                # hem end, slightly rounded
    d = sdf.smax(d, t - span, 0.004)
    if not detail:
        return d
    # Seams: a stitched groove along the underside and one above the hem band.
    seam_dist = np.abs(((theta - SEAM_ANGLE) + math.pi) % (2 * math.pi) - math.pi) * rho
    groove = np.hypot(seam_dist, d) - 0.0006
    d = sdf.smax(d, -groove, 0.0004)
    hem_groove = np.hypot(t - HEM_BAND, d) - 0.0005
    return sdf.smax(d, -hem_groove, 0.0003)


def sleeve_region(P):
    R = _sleeve_frame()
    t = (P @ R.T)[:, 1] + SLEEVE_HEM * np.linalg.norm(np.asarray(ELBOW)) / abs(ELBOW[1])
    return np.where(t < HEM_BAND, 'hem', 'sleeve')


def sleeve_bounds():
    return np.array((-0.068, SLEEVE_END - 0.012, -0.072)), np.array((0.068, SLEEVE_HEM + 0.010, 0.064))


def sleeve_low_mesh(segments=24, ring_count=20):
    """Game mesh of the sleeve: a quad tube on the sleeve's own axis and section, with
    edge loops packed toward the hem (where the wrist bends) and an inset cap at each
    end. It follows the cloth without the small folds, which the bake carries."""
    R = _sleeve_frame()
    k = np.linalg.norm(np.asarray(ELBOW)) / abs(ELBOW[1])
    span = abs(SLEEVE_END - SLEEVE_HEM)
    u = np.linspace(0, 1, ring_count)
    rings = list(span * u ** 1.6)
    thetas = np.linspace(-math.pi, math.pi, segments, endpoint=False)
    verts, faces = [], []

    def point(t, theta, r):
        q = np.array((r * math.cos(theta), t - SLEEVE_HEM * k, 0.86 * r * math.sin(theta)))
        return q @ R

    for t in rings:
        samples = np.array([[sleeve_radius(t + dt, th + dth) for dt in (-0.006, 0, 0.006) for dth in (-0.15, 0, 0.15)] for th in thetas])
        radii = samples.mean(1) - 0.0003
        for th, r in zip(thetas, radii):
            verts.append(point(t, th, r))
    n = segments
    for i in range(len(rings) - 1):
        for j in range(n):
            a, b = i * n + j, i * n + (j + 1) % n
            faces.append((a, b, b + n, a + n))
    for end, t, inward in ((0, rings[0], -1), (len(rings) - 1, rings[-1], 1)):
        base = len(verts)
        for j, th in enumerate(thetas):
            verts.append(point(t, th, sleeve_radius(t, th) * 0.80))
        centre = len(verts)
        verts.append(point(t, 0.0, 0.0))
        ring0 = end * n
        for j in range(n):
            a, b = ring0 + j, ring0 + (j + 1) % n
            c, d = base + (j + 1) % n, base + j
            faces.append((a, d, c, b) if inward < 0 else (a, b, c, d))
            faces.append((d, centre, c) if inward < 0 else (c, centre, d))
    return np.array(verts), faces
