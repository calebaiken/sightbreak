"""First-person gloved hands and sleeves posed on the Kestrel 9 (original geometry).

Same space and build method as relay_ar_hands.py (metres, Blender Z up, muzzle +Y, bore on x = 0): flattened
ellipsoid segments fused by a voxel remesh, smoothed and decimated, with tapered sleeves, cuffs and straps. The
firing hand (right) lies on the right face of the raked grip with its fingers wrapped round the front onto the left
face, the index along the frame to the trigger and the thumb forward on the left of the frame. The support hand
(left) lies on the left face, its fingers wrapped over the firing hand's fingers, its thumb forward along the dust
cover. Forearms run back and down, out of the frame, to the elbows of the viewmodel pose.

python kestrel_9_hands.py
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
X = Vector((1, 0, 0))
RAKE = 0.3057                                       # the grip's 17 degree rake, as in kestrel_9.py
GRIP_AXIS = Vector((0, RAKE, 1)).normalized()       # bottom to top along the grip
GRIP_NORMAL = Vector((0, 1, -RAKE)).normalized()    # perpendicular, toward the muzzle
HALF = 0.0155                                       # half the grip's width at the palm
DEPTH = 0.0415                                      # front-to-back depth of the grip


def y_back(z):
    """The backstrap line (the grip's rear edge) at height z."""
    return -0.0105 + RAKE * (z + 0.090)


def y_front(z):
    return y_back(z) + DEPTH


def right_hand():
    """Firing hand: palm on the right face, three fingers round the front, index to the trigger, thumb forward."""
    bm = bmesh.new()
    rh.blob(bm, (HALF + 0.0115, y_back(-0.055) + 0.019, -0.055), (GRIP_AXIS, GRIP_NORMAL, X), (0.044, 0.031, 0.0120))
    rh.blob(bm, (HALF + 0.0105, y_back(-0.085) + 0.010, -0.084), (GRIP_AXIS, GRIP_NORMAL, X), (0.020, 0.024, 0.0125))   # heel
    rh.blob(bm, (HALF + 0.0105, y_back(-0.024) + 0.012, -0.024), (GRIP_AXIS, GRIP_NORMAL, X), (0.021, 0.022, 0.0130))   # web under the thumb
    for finger, z in (('middle', -0.050), ('ring', -0.068), ('pinky', -0.086)):
        yf = y_front(z)
        joints = [(0.0250, yf - 0.012, z), (0.0200, yf + 0.004, z - 0.001), (0.0, yf + 0.0078, z - 0.002),
                  (-0.0195, yf + 0.0048, z - 0.003), (-0.0225, yf - 0.010, z - 0.003), (-0.0230, yf - 0.022, z - 0.003)]
        rh.digit(bm, joints, rh.FINGER_WIDTH[finger], (0, yf - 0.018, z), rh.PHALANX + (0.74,))
    rh.digit(bm, [(0.0235, 0.010, -0.014), (0.0170, 0.038, -0.0075), (0.0100, 0.060, -0.0040), (0.0, 0.0685, -0.0045)],
             rh.FINGER_WIDTH['index'], (0.0, 0.030, -0.006))
    rh.digit(bm, [(0.020, y_back(-0.030) - 0.004, -0.030), (0.0045, y_back(-0.016) + 0.002, -0.014), (-0.0150, 0.012, -0.0075),
                  (-0.0210, 0.034, -0.0040), (-0.0210, 0.058, -0.0025)],
             0.0225, (0.015, 0.0, -0.010), (1.15, 1.05, 0.95, 0.84))
    rh.segment(bm, (0.030, y_back(-0.080) - 0.006, -0.080), (0.040, -0.058, -0.110), 0.050, 0.040, (0.0, -0.04, -0.07))
    return rh.finish_organic('glove_right', bm, 'glove', voxel=0.0010)


def left_hand():
    """Support hand: palm on the left face, fingers over the firing hand's, thumb forward along the dust cover."""
    bm = bmesh.new()
    rh.blob(bm, (-(HALF + 0.0115), y_back(-0.062) + 0.020, -0.062), (GRIP_AXIS, GRIP_NORMAL, X), (0.040, 0.030, 0.0125))
    rh.blob(bm, (-(HALF + 0.0105), y_back(-0.090) + 0.012, -0.088), (GRIP_AXIS, GRIP_NORMAL, X), (0.020, 0.024, 0.0130))   # heel
    for finger, z, reach in (('index', -0.034, 1.0), ('middle', -0.052, 1.0), ('ring', -0.070, 1.0), ('pinky', -0.087, 0.78)):
        yf = y_front(z) + 0.0165                     # over the firing fingers
        joints = [(-0.0290, yf - 0.020, z), (-0.0235, yf + 0.0010, z), (-0.0110, yf + 0.0100, z - 0.001),
                  (0.0110, yf + 0.0105, z - 0.002), (0.0245, yf + 0.0040, z - 0.003), (0.0275, yf - 0.010, z - 0.003)]
        if reach < 1.0:
            joints = joints[:5]
        rh.digit(bm, joints, rh.FINGER_WIDTH[finger], (0, yf - 0.020, z), rh.PHALANX + (0.74,))
    rh.digit(bm, [(-0.027, y_back(-0.050) + 0.014, -0.040), (-0.0285, 0.026, -0.0230), (-0.0275, 0.048, -0.0130),
                  (-0.0255, 0.070, -0.0085), (-0.0240, 0.090, -0.0070)],
             0.0235, (-0.010, 0.040, -0.020), (1.12, 1.0, 0.9, 0.8, 0.72), thickness=0.90)
    rh.segment(bm, (-0.034, y_back(-0.086) - 0.004, -0.088), (-0.060, -0.052, -0.114), 0.050, 0.040, (0.0, 0.0, -0.05))
    return rh.finish_organic('glove_left', bm, 'glove', voxel=0.0010)


def build(reset=True):
    if reset:
        hs.reset_scene()
    rh.materials()
    parts = [right_hand(), left_hand()]
    right_wrist, right_elbow = (0.040, -0.058, -0.110), (0.255, -0.585, -0.345)
    left_wrist, left_elbow = (-0.060, -0.052, -0.114), (-0.330, -0.470, -0.360)
    parts.append(rh.sleeve('right', right_wrist, right_elbow, 0.034, 0.075, 0.4))
    parts.append(rh.sleeve('left', left_wrist, left_elbow, 0.033, 0.074, -0.4))
    parts += rh.wrist_trim('right', right_wrist, right_elbow, 0.034)
    parts += rh.wrist_trim('left', left_wrist, left_elbow, 0.033)
    return parts, None


if __name__ == '__main__':
    build()
    meshes = [o for o in bpy.data.objects if o.type == 'MESH']
    print('KESTREL_9_HANDS objects=%d tris=%d' % (len(meshes), hs.triangles(meshes)), {o.name: hs.triangles([o]) for o in meshes})
