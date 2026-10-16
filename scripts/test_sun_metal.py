#!/usr/bin/env python3
"""The Relay AR's machined metal reads as metal and its polymer handguard reads as polymer, in sun, and the shade is not worse.

Renders the shipped finish with game/tests/viewmodel_metal_probe.gd (native display; Xvfb on :99 is what the logs were made with) in the
sun, the shade and the dark-interior views at the ready pose (reload tick 134), takes each part's visible pixels (the pixels that change
when the part is hidden), and asserts the bounds below. Every bound is EMPIRICAL: set after measuring the baseline (240a5f8) and this
build, midway or on the safe side of the two, and none is a visual standard (see docs/reports/media/art-v11/sunmetal/README.md).

    SUN_METAL_TEST checks=N failures=M

    python3 scripts/test_sun_metal.py [--frames <dir>] [--skin]

                                                         baseline   this build   bound
  sun, receiver (r - b) / luma                           +0.018     -0.020       <= -0.005   cooler, not warm olive
  sun, receiver share of pixels 25 luma above its median  0.011      0.033       >= 0.020    edges and bevels catch the light
  sun, receiver local detail (luma, 3 px neighbours)      3.32       4.29        >= 3.80     structure on the large faces
  sun, handguard minus receiver (r - b) / luma            0.056      0.094       >= 0.070    polymer and metal differ in hue
  sun, handguard median luma                              67.9       67.8        62 to 74    the polymer is not changed by the metal finish
  shade and dark interior, receiver median luma           28.4/28.7  34.6/35.4   >= 28.0     not worse than the baseline
  shade and dark interior, handguard median luma          31.2/31.2  31.2/31.2   >= 29.0     likewise
"""
import argparse
import os
import subprocess
import sys
import tempfile

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(REPO, 'tools', 'art'))
import metal_probe_stats as stats  # noqa: E402


def render(out, skin):
    env = dict(os.environ)
    env.setdefault('DISPLAY', ':99')
    args = [os.path.join(REPO, 'scripts', 'godot.sh'), '--audio-driver', 'Dummy', '--rendering-method', 'gl_compatibility',
            '--script', 'res://tests/viewmodel_metal_probe.gd', '--', '--out=' + out, '--views=sunlit,shade,dark', '--ticks=134']
    if skin:
        args.append('--skin')
    r = subprocess.run(args, capture_output=True, text=True, env=env, timeout=1200)
    text = r.stdout + r.stderr
    if 'VIEWMODEL_METAL_PROBE' not in text:
        print(text[-2000:])
        raise SystemExit('the probe did not finish (exit %d)' % r.returncode)


def part(out, view, name):
    base = stats.load(os.path.join(out, '%s_134.png' % view))
    hidden = stats.load(os.path.join(out, '%s_134_%s.png' % (view, name)))
    return stats.stats(base, hidden)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--frames')
    ap.add_argument('--skin', action='store_true', help='measure a patterned cosmetic finish (the handguard bounds are skipped)')
    args = ap.parse_args()
    out = args.frames or tempfile.mkdtemp(prefix='sun_metal_')
    os.makedirs(out, exist_ok=True)
    render(out, args.skin)
    rec = {v: part(out, v, 'receiver') for v in ('sunlit', 'shade', 'dark')}
    hg = {v: part(out, v, 'handguard') for v in ('sunlit', 'shade', 'dark')}
    checks = 0
    failures = 0

    def check(ok, text):
        nonlocal checks, failures
        checks += 1
        failures += 0 if ok else 1
        print('%s %s' % ('ok  ' if ok else 'FAIL', text))

    r = rec['sunlit']
    check(r['chroma'] <= -0.005, 'sun receiver (r - b) / luma %+.3f (at most -0.005)' % r['chroma'])
    check(r['hot'] >= 0.020, 'sun receiver share of pixels 25 luma above its median %.3f (at least 0.020)' % r['hot'])
    check(r['detail'] >= 3.80, 'sun receiver local detail %.2f (at least 3.80)' % r['detail'])
    if not args.skin:
        h = hg['sunlit']
        check(h['chroma'] - r['chroma'] >= 0.070, 'sun handguard minus receiver (r - b) / luma %.3f (at least 0.070)' % (h['chroma'] - r['chroma']))
        check(62.0 <= h['median'] <= 74.0, 'sun handguard median luma %.1f (62 to 74: the polymer is not changed by the metal finish)' % h['median'])
    for view in ('shade', 'dark'):
        check(rec[view]['median'] >= 28.0, '%s receiver median luma %.1f (at least 28.0, the baseline 28.4)' % (view, rec[view]['median']))
        if not args.skin:
            check(hg[view]['median'] >= 29.0, '%s handguard median luma %.1f (at least 29.0, the baseline 31.2)' % (view, hg[view]['median']))
    print('SUN_METAL_TEST skin=%s checks=%d failures=%d' % (args.skin, checks, failures))
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
