"""First-person gloved hands and sleeves posed on the Vectorline (original geometry).

Same space and build method as relay_ar_hands.py and kestrel_9_hands.py (metres, Blender Z up, muzzle +Y, bore on x = 0):
flattened ellipsoid segments fused by a voxel remesh, smoothed and decimated, with tapered sleeves, cuffs and straps. The
firing hand (right) lies on the right face of the raked grip with its fingers wrapped round the front onto the left face,
the index along the right flank of the receiver to the trigger and the thumb forward along the left flank. The support
hand (left) holds the shroud from below, a C clamp: palm and heel under it, four fingers up the right face to the top,
the thumb along the left face, behind the chin that stops it. The forearms run back and down, out of the frame, to the
elbows of the viewmodel pose.

python vectorline_hands.py
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402,F401
import bmesh  # noqa: E402
from mathutils import Vector  # noqa: E402
import hardsurface as hs  # noqa: E402
import relay_ar_hands as rh  # noqa: E402  (the building blocks: blob, segment, digit, finish_organic, sleeve, wrist_trim, materials)

GROUPS = {'hands': ('glove_right', 'glove_left', 'sleeve_right', 'sleeve_left', 'cuff_right', 'cuff_left',
                    'strap_right', 'strap_left')}
ANCHORS = {}
X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))
RAKE = 0.265                                        # the grip's back strap, y per metre of height (vectorline.py grip())
GRIP_AXIS = Vector((0, RAKE, 1)).normalized()       # bottom to top along the grip
GRIP_NORMAL = Vector((0, 1, -RAKE)).normalized()    # perpendicular, toward the muzzle
HALF = 0.018                                        # half the grip's width


def y_back(z):
    """The backstrap line (the grip's rear edge) at height z."""
    return 0.0045 + (z + 0.028) * RAKE


def y_front(z):
    """The front strap line at height z."""
    return 0.0585 + (z + 0.027) * 0.195


def right_hand():
    """Firing hand: palm on the right face, three fingers round the front, index along the receiver to the trigger, thumb forward."""
    bm = bmesh.new()
    mid = lambda z: (y_back(z) + y_front(z)) / 2
    rh.blob(bm, (HALF + 0.0115, mid(-0.058), -0.058), (GRIP_AXIS, GRIP_NORMAL, X), (0.046, 0.034, 0.0125))
    rh.blob(bm, (HALF + 0.0105, mid(-0.092) - 0.004, -0.090), (GRIP_AXIS, GRIP_NORMAL, X), (0.021, 0.027, 0.0130))   # heel
    rh.blob(bm, (HALF + 0.0105, mid(-0.028) - 0.004, -0.028), (GRIP_AXIS, GRIP_NORMAL, X), (0.022, 0.025, 0.0135))  # web under the thumb
    for finger, z in (('middle', -0.050), ('ring', -0.068), ('pinky', -0.086)):
        yf = y_front(z)
        joints = [(0.0265, yf - 0.014, z), (0.0215, yf + 0.004, z - 0.001), (0.0, yf + 0.0090, z - 0.002),
                  (-0.0215, yf + 0.0055, z - 0.003), (-0.0250, yf - 0.014, z - 0.003), (-0.0255, yf - 0.026, z - 0.003)]
        rh.digit(bm, joints, rh.FINGER_WIDTH[finger], (0, yf - 0.020, z), rh.PHALANX + (0.74,))
    # Index: along the receiver's right flank, then in to the blade (y 0.0675 to 0.075, z -0.008 to -0.034).
    rh.digit(bm, [(0.031, 0.0105, -0.014), (0.0385, 0.036, -0.0165), (0.0345, 0.0585, -0.0215), (0.0120, 0.0690, -0.0225), (0.0, 0.0695, -0.0225)],
             rh.FINGER_WIDTH['index'], (0.0, 0.030, -0.014))
    # Thumb: over the back of the receiver's lower edge and forward along the left flank.
    rh.digit(bm, [(0.022, y_back(-0.030) - 0.004, -0.032), (0.006, y_back(-0.016) + 0.002, -0.016), (-0.020, 0.008, -0.0125),
                  (-0.0365, 0.030, -0.0115), (-0.0385, 0.054, -0.0105)],
             0.0235, (0.010, 0.010, -0.014), (1.15, 1.05, 0.95, 0.84))
    rh.segment(bm, (0.034, y_back(-0.082) - 0.006, -0.082), (0.044, -0.034, -0.112), 0.052, 0.042, (0.0, -0.04, -0.07))
    return rh.finish_organic('glove_right', bm, 'glove', voxel=0.0010)


def left_hand():
    """Support hand under the shroud (C clamp): palm and heel underneath, four fingers up the right face over the top, a thick
    thumb along the left face, which is the side the camera sees. The chin at y 0.371 is its stop."""
    bm = bmesh.new()
    rh.blob(bm, (-0.010, 0.318, -0.0115), (X, Y, Z), (0.045, 0.040, 0.0135))
    rh.blob(bm, (-0.044, 0.292, -0.0145), (X, Y, Z), (0.021, 0.027, 0.0150))                    # heel at the wrist
    guard_mid = (0.0, 0.318, 0.029)
    for finger, y, reach in (('index', 0.350, 1.0), ('middle', 0.330, 1.0), ('ring', 0.310, 1.0), ('pinky', 0.291, 0.78)):
        joints = [(0.012, y, -0.0125), (0.0275, y, -0.0045), (0.0362, y, 0.0150), (0.0362, y, 0.0400), (0.0295, y, 0.0585)]
        if reach < 1.0:
            joints = joints[:4]
        rh.digit(bm, joints, rh.FINGER_WIDTH[finger], (0.0, y, 0.029), rh.PHALANX + (0.74,))
    # Thumb: thenar mass, proximal and distal phalanges along the left face.
    rh.digit(bm, [(-0.042, 0.300, -0.0125), (-0.0405, 0.331, -0.0020), (-0.0385, 0.354, 0.0085), (-0.0365, 0.368, 0.0150)],
             0.0305, guard_mid, (1.0, 0.90, 0.82, 0.74), thickness=0.90)
    rh.segment(bm, (-0.047, 0.292, -0.018), (-0.070, 0.270, -0.030), 0.052, 0.042, guard_mid)
    return rh.finish_organic('glove_left', bm, 'glove', voxel=0.0010)


def build(reset=True):
    if reset:
        hs.reset_scene()
    rh.materials()
    parts = [right_hand(), left_hand()]
    right_wrist, right_elbow = (0.044, -0.034, -0.112), (0.262, -0.585, -0.350)
    left_wrist, left_elbow = (-0.070, 0.270, -0.030), (-0.495, -0.140, -0.307)
    parts.append(rh.sleeve('right', right_wrist, right_elbow, 0.034, 0.075, 0.4))
    parts.append(rh.sleeve('left', left_wrist, left_elbow, 0.033, 0.074, -0.4))
    parts += rh.wrist_trim('right', right_wrist, right_elbow, 0.034)
    parts += rh.wrist_trim('left', left_wrist, left_elbow, 0.033)
    return parts, None


if __name__ == '__main__':
    build()
    meshes = [o for o in bpy.data.objects if o.type == 'MESH']
    print('VECTORLINE_HANDS objects=%d tris=%d' % (len(meshes), hs.triangles(meshes)), {o.name: hs.triangles([o]) for o in meshes})
