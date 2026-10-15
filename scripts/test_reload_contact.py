#!/usr/bin/env python3
"""Checks the reload clip's contact review (clip_contact.csv, written by tools/art/arms_build.py).

    python3 scripts/test_reload_contact.py [clip_contact.csv]

For every frame of the 1 s clip the build measures, from the posed arms and the magazine the hand holds
(old from GRASP to DROP, replacement from ACQUIRE to LETGO, in game/scripts/gameplay/reload_phases.gd):
how far the left arm sinks into the rifle and into that magazine, how close each of the five fingertips
(the distal phalanx's nearest vertex), and the palm, come to the magazine's surface, and how opposed the
thumb is to the other four digits about the magazine's long axis. This test says whether the hand is ON
the magazine, not whether it looks like a hand: a grasp that touches everywhere can still look wrong.
"""
import csv
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT = os.path.join(HERE, '..', 'docs', 'reports', 'media', 'art-v7', 'reload-two-magazines', 'logs', 'clip_contact.csv')
PHASES = os.path.join(HERE, '..', 'game', 'scripts', 'gameplay', 'reload_phases.gd')
DIGITS = ('thumb', 'index', 'middle', 'ring', 'pinky')
# What "on the magazine" means, in millimetres from its surface (negative: inside it).
TIP_NEAR, TIP_SUNK = 6.5, -2.0
PALM_NEAR = 15.0
PENETRATION = 1.0        # the deepest any left-arm vertex may sink into the rifle or the magazine
RIGHT_PENETRATION = 1.5  # the trigger finger rests this far into the trigger, by the grip solve's design
OPPOSITION = 60.0        # degrees: the thumb is at least this far round the magazine from the fingers

checks = 0
failures = []


def check(condition, message):
    global checks
    checks += 1
    if not condition:
        failures.append(message)
        print('FAIL', message)


def phases():
    with open(PHASES) as f:
        return {m.group(1): float(m.group(2)) for m in re.finditer(r'^const ([A-Z_]+) := ([0-9.]+)\s*$', f.read(), re.M)}


GLB = os.path.join(HERE, '..', 'game', 'assets', 'weapons', 'relay_ar', 'relay_ar_arms.glb')


def glb_hash():
    import hashlib
    with open(GLB, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()


def main(path):
    P = phases()
    # The numbers are only about the shipped clip if the CSV was produced for THIS GLB: the build's log
    # records the hash of the GLB it exported next to the CSV (clip_contact.glb.sha256). A rebuild that
    # is not followed by refreshing both leaves the test failing rather than passing on a stale CSV.
    stamp = os.path.join(os.path.dirname(path), 'clip_contact.glb.sha256')
    if os.path.exists(stamp):
        check(open(stamp).read().split()[0] == glb_hash(), 'clip_contact.csv was made for the GLB in game/assets (hash %s...)' % glb_hash()[:12])
    elif os.path.abspath(path).startswith(os.path.abspath(os.path.join(HERE, '..', 'docs'))):
        check(False, 'clip_contact.glb.sha256 is missing next to the committed CSV')
    rows = list(csv.DictReader(open(path)))
    check(len(rows) == 61, 'the clip has 61 frames at 60 fps (%d)' % len(rows))
    eps = 0.5 / 60
    old = [r for r in rows if r['held'] == 'old']
    new = [r for r in rows if r['held'] == 'new']
    expected_old = [r for r in rows if P['GRASP'] - eps <= float(r['progress']) <= P['DROP'] + eps]
    expected_new = [r for r in rows if P['ACQUIRE'] - eps <= float(r['progress']) <= P['LETGO'] + eps]
    check(len(old) >= 10 and set(r['frame'] for r in old) <= set(r['frame'] for r in expected_old), 'the old magazine is held only between the grasp and the drop (%d frames)' % len(old))
    check(len(new) >= 15 and set(r['frame'] for r in new) <= set(r['frame'] for r in expected_new), 'the replacement is held only between the acquisition and the let-go (%d frames)' % len(new))
    check(not [r for r in rows if r['held'] != '-' and P['DROP'] + eps < float(r['progress']) < P['ACQUIRE'] - eps], 'the empty hand holds nothing on its way to the replacement')
    stable_old = [r for r in old if P['GRASP'] + 0.02 <= float(r['progress']) <= P['DROP'] - 0.012]
    stable_new = [r for r in new if P['ACQUIRE'] + 0.02 <= float(r['progress']) <= P['SEAT']]
    check(len(stable_old) >= 5 and len(stable_new) >= 8, 'frames of a settled grip: %d old, %d replacement' % (len(stable_old), len(stable_new)))
    for label, frames in (('old', stable_old), ('replacement', stable_new)):
        for digit in DIGITS:
            gaps = [float(r['gap_%s_mm' % digit]) for r in frames]
            check(gaps and TIP_SUNK <= min(gaps) and max(gaps) <= TIP_NEAR, 'the %s magazine: the %s tip is within %.1f mm of its surface and not more than %.1f mm into it (%.1f to %.1f)' % (label, digit, TIP_NEAR, -TIP_SUNK, min(gaps or [0]), max(gaps or [0])))
        palm = [float(r['gap_palm_mm']) for r in frames]
        check(palm and max(palm) <= PALM_NEAR and min(palm) >= TIP_SUNK, 'the %s magazine: the palm is within %.0f mm of its surface (%.1f to %.1f)' % (label, PALM_NEAR, min(palm or [0]), max(palm or [0])))
        opposition = [float(r['thumb_opposition_deg']) for r in frames]
        check(opposition and min(opposition) >= OPPOSITION, 'the %s magazine: the thumb is opposed to the fingers by at least %.0f degrees (%.0f)' % (label, OPPOSITION, min(opposition or [0])))
    if stable_old and stable_new:
        worst = max(abs(float(stable_old[0]['gap_%s_mm' % d]) - float(stable_new[0]['gap_%s_mm' % d])) for d in DIGITS + ('palm',))
        check(worst < 0.5, 'both magazines are held with the same grip (worst difference %.2f mm)' % worst)
    # No part of the left arm goes into the rifle or either magazine, in any frame; the right arm's
    # trigger finger is the one documented contact.
    check(max(float(r['left_depth_body_mm']) for r in rows) <= PENETRATION, 'the left arm is never more than %.1f mm into the rifle (%.2f)' % (PENETRATION, max(float(r['left_depth_body_mm']) for r in rows)))
    check(max(float(r['left_depth_magazine_mm']) for r in rows) <= PENETRATION, 'the left arm is never more than %.1f mm into the magazine it holds (%.2f)' % (PENETRATION, max(float(r['left_depth_magazine_mm']) for r in rows)))
    check(max(float(r['right_depth_body_mm']) for r in rows) <= RIGHT_PENETRATION, 'the right arm is never more than %.1f mm into the rifle (%.2f)' % (RIGHT_PENETRATION, max(float(r['right_depth_body_mm']) for r in rows)))
    print('RELOAD_CONTACT_TEST checks=%d failures=%d (%s)' % (checks, len(failures), os.path.relpath(path)))
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else DEFAULT))
