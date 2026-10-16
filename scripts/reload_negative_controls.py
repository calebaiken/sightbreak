#!/usr/bin/env python3
"""Negative controls for the reload tests: inject one defect at a time and check that the test that is
meant to catch it fails, cleanly (a summary line with failures, not a crash). Restores every file it
touches. Needs the Godot and Blender tools of scripts/setup.sh, and a native display for the visibility
controls (Xvfb on :99 is what the logs were made with).

    python3 scripts/reload_negative_controls.py [--only N5,N7] [--log path]

Each control is a defect the reload could really have had, not an arbitrary edit:
  actor / phases source edits   the single-node replacement, the unseen replacement, no node swap, a grip
                                offset, reduced motion shrinking the staging, clicks from the authoritative
                                fraction, an early click, a click at the let-go, a double click on a rewind,
                                brass at the shooter's feet, the animation writing the timer, a drifted
                                phase constant, the old magazine returning to the well, the wrong sound
  rebuilt clips (Blender)       a hand that does not reach the magazine, the old grasp that hides the thumb,
                                the old approach from below the frame, a replacement fetched from below the frame
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
GAME = os.path.join(REPO, 'game')
ACTOR = os.path.join(GAME, 'scripts', 'gameplay', 'actor.gd')
PHASES = os.path.join(GAME, 'scripts', 'gameplay', 'reload_phases.gd')
AUDIO = os.path.join(GAME, 'scripts', 'gameplay', 'reload_audio.gd')
GLB = os.path.join(GAME, 'assets', 'weapons', 'relay_ar', 'relay_ar_arms.glb')
SHADING = os.path.join(GAME, 'scripts', 'gameplay', 'viewmodel_shading.gd')
COSMETIC = os.path.join(GAME, 'scripts', 'ui', 'cosmetic_material.gd')
WEAPON_MODEL = os.path.join(GAME, 'scripts', 'gameplay', 'weapon_model.gd')
BPY = os.environ.get('BPY', os.path.join(os.path.dirname(REPO), 'tools', 'bpy-venv', 'bin', 'python'))
RIFLE = os.path.join(GAME, 'assets', 'weapons', 'relay_ar', 'relay_ar.glb')
SUMMARY = re.compile(r'^(RELOAD_SEQUENCE_TEST|WEAPON_ART_TEST|RELOAD_VISIBILITY_TEST|RELOAD_AUDIO_TEST|RELOAD_AUDIO_CAPTURE|RELOAD_DISCOLOUR_TEST|VIEWMODEL_LIGHT_TEST)\b.*?(?:checks=(\d+))?.*?failures=(\d+)', re.M)
ERRORS = re.compile(r'^ERROR: (?!.*(?:ObjectDB|leaked)).*$', re.M)

SEQ = ('sequence', ['--headless', '--script', 'res://tests/reload_sequence_test.gd'])
ART = ('weapon-art', ['--headless', '--script', 'res://tests/weapon_art_test.gd'])
AUD = ('audio', ['--headless', '--script', 'res://tests/reload_audio_test.gd'])
CAP = ('audio capture', ['--headless', '--audio-driver', 'Dummy', '--script', 'res://tests/reload_audio_capture.gd', '--', '--scenario=reload'])
CAP_CANCEL = ('audio capture (cancel)', ['--headless', '--audio-driver', 'Dummy', '--script', 'res://tests/reload_audio_capture.gd', '--', '--scenario=cancel'])
VIS = ('visibility', ['--audio-driver', 'Dummy', '--rendering-method', 'gl_compatibility', '--script', 'res://tests/reload_visibility_test.gd', '--', '--step=2'])
VIS_REDUCED = ('visibility (reduced motion)', VIS[1] + ['--reduced'])
# The parts separate in the lightings (sun and a dark interior at the ready pose: the quick form of the validate.sh run).
LIGHT = ('light separation', ['--audio-driver', 'Dummy', '--rendering-method', 'gl_compatibility', '--script', 'res://tests/viewmodel_light_probe.gd', '--', '--assert', '--poses=ready', '--scenarios=sun,dark interior'])
# The rifle's painted metal holds its finish through the reload (native: it renders the receiver and handguard at reload ticks).
DISC = ('finish stability', ['--audio-driver', 'Dummy', '--rendering-method', 'gl_compatibility', '--script', 'res://tests/reload_discolour_probe.gd', '--', '--assert', '--conditions=base', '--ticks=0,40,122,126,130,134'])

# (id, what, [(file, old, new)], build_env or None, tests that must fail)
SOURCE = [
    ('N1', 'the replacement is the first magazine again (one node, not two)', [(ACTOR, '_magazine_spare = _magazine.duplicate() as MeshInstance3D', '_magazine_spare = _magazine')], None, [SEQ]),
    ('N2', 'the replacement is never drawn', [(ACTOR, '_magazine_spare.visible = progress >= SBReloadPhases.ACQUIRE', '_magazine_spare.visible = false')], None, [SEQ]),
    ('N3', 'the nodes do not swap when the reload ends', [(ACTOR, '\t\t_magazine_swap_pending = true\n\t\t_seat_kick = 1.0', '\t\t_seat_kick = 1.0')], None, [SEQ]),
    ('N4', 'the magazine is held 30 mm from where the hand grips it', [(ACTOR, '\t_grip_offset = _hand_in_gun().affine_inverse() * _magazine_rest_transform\n', '\t_grip_offset = _hand_in_gun().affine_inverse() * _magazine_rest_transform\n\t_grip_offset.origin += Vector3(0.0, 0.0, 0.030)\n')], None, [SEQ]),
    ('N5', 'the old magazine comes back to the well while the replacement is drawn', [(ACTOR, '\t\t_magazine.transform = _dropped_transform(fall)\n', '\t\t_magazine.transform = _magazine_rest_transform\n')], None, [SEQ]),
    ('N6', 'reduced motion shrinks the reload staging to a fifth', [(ACTOR, '\t\tvar bob_weight := 0.0 if reduced_motion', '\t\tif reduced_motion:\n\t\t\treload_tilt *= 0.2\n\t\tvar bob_weight := 0.0 if reduced_motion')], None, [SEQ, VIS_REDUCED]),
    ('N7', 'the clicks follow the authoritative fraction instead of the visible reload', [(ACTOR, 'SBReloadPhases.crossed(_reload_visual_previous, visual_progress)', 'SBReloadPhases.crossed(_reload_visual_previous, SBReloadPhases.progress(reload_remaining, reload_duration))'), (ACTOR, '\t\t_reload_visual_previous = visual_progress\n\telif _reload_visual_active', '\t\t_reload_visual_previous = SBReloadPhases.progress(reload_remaining, reload_duration)\n\telif _reload_visual_active')], None, [SEQ, AUD]),
    ('N8', 'the seat click fires 0.05 of the reload early', [(PHASES, '["seat", SEAT]', '["seat", SEAT - 0.05]')], None, [SEQ]),
    ('N9', 'the seat click fires at the let-go instead of the seat', [(PHASES, '["seat", SEAT]', '["seat", LETGO]')], None, [SEQ, AUD]),
    ('N10', 'a clock correction that goes back over events plays them twice', [(ACTOR, '\tif _reload_fired.has(event):\n\t\treturn\n', '')], None, [SEQ, AUD]),
    ('N11', 'the seat click plays the release sound', [(ACTOR, '\t_reload_audio.play(event, progress, head_height)', '\t_reload_audio.play("unlatch" if event == "seat" else event, progress, head_height)')], None, [SEQ, AUD]),
    ('N12', 'brass lands at the shooter\'s feet again', [(ACTOR, '.casing(port, global_basis.x, _cosmetic_floor(port))', '.casing(port, global_basis.x, global_position.y)')], None, [SEQ]),
    ('N13', 'the animation completes the reload by writing the timer', [(ACTOR, '\t\t_magazine_swap_pending = true\n\t\t_seat_kick = 1.0', '\t\t_magazine_swap_pending = true\n\t\treload_remaining = 0.0\n\t\t_seat_kick = 1.0')], None, [SEQ]),
    ('N19', 'the SMG plays the rigged hand\'s whole set of sounds', [(ACTOR, 'if not rigged_events and (event == "unlatch" or not SBReloadPhases.PROCEDURAL_EVENTS.has(event)):', 'if false:')], None, [SEQ, AUD]),
    ('N20', 'reduced motion no longer calms the procedural weapons\' reload dip', [(ACTOR, '\t\t\treload_tilt *= 0.2 # the procedural weapons\' dip is plain motion: still calmed\n', '\t\t\tpass\n')], None, [SEQ]),
    ('N21', 'a reload restarted with no idle frame between does not reset its events', [(ACTOR, 'if reloading and _reload_visual_active and reload_remaining - _reload_clock > reload_duration * 0.5:', 'if false:')], None, [SEQ, AUD]),
    ('N25', 'first-person materials take the engine\'s sky radiance again (the viewmodel studio is not substituted): the sky\'s horizon band returns to the metal', [(SHADING, 'const RENDER_MODE := "render_mode ambient_light_disabled;\\n"', 'const RENDER_MODE := ""')], None, [ART, DISC]),
    ('N26', 'the studio\'s gradient has a hard edge at the horizon (a step instead of a smooth ramp)', [(SHADING, 'smoothstep(-1.0, 1.0, r.y)', 'step(0.0, r.y)')], None, [ART, DISC]),
    ('N27', 'the handguard gets the receiver\'s finish (no polymer material of its own)', [(COSMETIC, 'if first_person and part.name == "paint_handguard":', 'if false:')], None, [ART]),
    ('N28', 'the grip is not darkened over its baked graphite (it was level with the receiver and the gloves)', [(WEAPON_MODEL, 'const GRIP_DARKEN := 0.24', 'const GRIP_DARKEN := 1.0')], None, [LIGHT]),
    ('N29', 'the painted metal has no fill floor of its own (the rifle dissolves in a dark interior)', [(SHADING, 'const METAL_FLOOR := 0.12', 'const METAL_FLOOR := 0.0')], None, [ART, LIGHT]),
    ('N31', 'the arms reflect the whole studio (the gloves read as a pale veil beside the sleeves)', [(WEAPON_MODEL, 'const ARMS_REFLECT := 0.10', 'const ARMS_REFLECT := 1.0')], None, [ART, LIGHT]),
    ('N22', 'the replacement is drawn from the start of the hip trip: it floats in view with no hand on it', [(ACTOR, '_magazine_spare.visible = progress >= SBReloadPhases.ACQUIRE', '_magazine_spare.visible = progress >= SBReloadPhases.DROP')], None, [SEQ]),
    ('N14', 'the seat phase is changed in reload_phases.gd without rebuilding the clip', [(PHASES, 'const SEAT := 0.80', 'const SEAT := 0.78')], None, [ART, SEQ]),
    ('A1', 'a reload cut short leaves its sounds playing', [(ACTOR, '\telif _reload_visual_active and not _reload_fired.has("seat"):\n\t\t_reload_audio.stop_all() # cancelled before the seat: the sounds that were playing stop with it\n', '')], None, [AUD]),
    ('A2', 'every reload sound uses the same voice, so each cuts the one before', [(AUDIO, '\tvar index := _free_voice()', '\tvar index := 0')], None, [AUD]),
    ('A4', 'the slide-out has no sound', [(AUDIO, '\t\t_add("extract", _slide(0.17, 1700.0 * shift, 900.0 * shift, 105.0, seed_base + 2, false))\n', '')], None, [AUD]),
    ('A5', 'the reload sounds play 80 dB down (the voices are muted)', [(AUDIO, '\tvoice.volume_db = -15.0 + float(LEVELS.get(event, 0.0))', '\tvoice.volume_db = -95.0')], None, [CAP]),
    ('A6', 'a cancelled reload does not stop its voices (real audio, a cancel as the landing starts)', [(ACTOR, '\t_reload_audio.stop_all() # a weapon change cancels a reload: nothing of it keeps sounding', '\tpass'), (ACTOR, '\telif _reload_visual_active and not _reload_fired.has("seat"):\n\t\t_reload_audio.stop_all() # cancelled before the seat: the sounds that were playing stop with it\n', '')], None, [CAP_CANCEL]),
]
CLIPS = [
    ('N15', 'a hand that does not reach the magazine (knuckle 50 mm off)', {'ARMS_GRAB_JSON': '{"mcp": [0.064, 0.15, -0.19]}'}, ['contact']),
    ('N16', 'the previous grasp, which hides the thumb behind the magazine', {'ARMS_GRAB_JSON': '{"distal": [1.0, 0.0, 0.0], "mcp": [0.034, 0.15, -0.19], "roll": 0}'}, [VIS]),
    ('N17', 'the previous approach from below the frame (the hand leaves the picture)', {'ARMS_APPROACH': '-0.020,-0.010,-0.085'}, [VIS]),
    ('N23', 'the replacement taken from just under the well, in view: it appears in the picture before the hand has it', {'ARMS_PATH_JSON': '{"hip": [-0.05, 0.03, -0.07], "carry": [-0.03, 0.04, -0.05]}'}, [SEQ]),
    ('N24', 'the magazine and hand move in straight lines between keys (robotic, with velocity jumps)', {'ARMS_LINEAR_PATHS': '1'}, [ART]),
    ('N18', 'the replacement fetched from far below the frame', {'ARMS_PATH_JSON': '{"hip": [-0.20, 0.04, -0.60], "carry": [-0.115, 0.05, -0.40]}'}, [VIS, SEQ]),
]


def godot(args, display=True, timeout=900):
    env = dict(os.environ)
    if display:
        env.setdefault('DISPLAY', ':99')
    r = subprocess.run([os.path.join(REPO, 'scripts', 'godot.sh')] + args, capture_output=True, text=True, env=env, timeout=timeout)
    return r.returncode, r.stdout + r.stderr


def run_test(test):
    name, args = test
    code, out = godot(args)
    m = list(SUMMARY.finditer(out))
    if not m:
        return name, 'CRASHED', ['no summary line (exit %d)' % code]
    failures = int(m[-1].group(3))
    errors = [e for e in ERRORS.findall(out)][:3]
    script_errors = re.findall(r'^SCRIPT ERROR: .*$', out, re.M)
    if script_errors:  # a script error aborts a check mid-way even when the summary line says failures=0
        return name, 'FAILED', ['(script error) ' + script_errors[0]] + errors
    return name, ('FAILED' if failures else 'passed'), errors


def run_contact(csv_path):
    r = subprocess.run([sys.executable, os.path.join(REPO, 'scripts', 'test_reload_contact.py'), csv_path], capture_output=True, text=True)
    fails = [l[5:] for l in r.stdout.splitlines() if l.startswith('FAIL ')]
    return 'contact', ('FAILED' if r.returncode else 'passed'), fails[:3]


def build(env_extra, out):
    env = dict(os.environ, **env_extra)
    r = subprocess.run([BPY, os.path.join(REPO, 'tools', 'art', 'arms_build.py'), out, '--no-bake', '--rifle', RIFLE], capture_output=True, text=True, env=env, timeout=600)
    return r.returncode == 0


def main():
    only = None
    log = None
    args = sys.argv[1:]
    if '--only' in args:
        only = set(args[args.index('--only') + 1].split(','))
    if '--log' in args:
        log = open(args[args.index('--log') + 1], 'w')

    def say(text=''):
        print(text, flush=True)
        if log:
            log.write(text + '\n')
            log.flush()

    # Every file any source control edits is restored afterwards (a control that names a file missing here once left its edit in the tree).
    originals = {p: open(p).read() for p in sorted({ACTOR, PHASES, AUDIO} | {path for c in SOURCE for path, _, _ in c[2]})}
    glb_backup = open(GLB, 'rb').read()
    results = []
    try:
        say('# Baseline (no defect injected): every test passes')
        if '--no-baseline' in args:
            say('  (skipped by --no-baseline: run it once without, for the record)')
        base = [] if '--no-baseline' in args else [run_test(t) for t in (SEQ, ART, AUD, CAP, CAP_CANCEL)] + [run_test(VIS), run_test(VIS_REDUCED), run_test(DISC), run_test(LIGHT)]
        csv_good = os.path.join(REPO, 'docs', 'reports', 'media', 'art-v9', 'hands', 'logs', 'clip_contact.csv')
        if os.path.exists(csv_good) and '--no-baseline' not in args:
            base.append(run_contact(csv_good))
        for name, state, errs in base:
            say('  %-30s %s' % (name, state))
        if any(s != 'passed' for _, s, _ in base):
            say('BASELINE FAILS: the controls below mean nothing until it passes')
            return 2
        for cid, what, edits, _, tests in [(c[0], c[1], c[2], c[3], c[4]) for c in SOURCE]:
            if only and cid not in only:
                continue
            say('')
            say('## %s: %s' % (cid, what))
            try:
                for path, old, new in edits:
                    text = open(path).read()
                    if old not in text:
                        say('  INVALID CONTROL: the text to change is not in %s: %r' % (os.path.basename(path), old[:60]))
                        results.append((cid, 'invalid'))
                        break
                    open(path, 'w').write(text.replace(old, new, 1))
                else:
                    states = [run_test(t) for t in tests]
                    for name, state, errs in states:
                        say('  %-30s %s' % (name, state))
                        for e in errs:
                            say('      ' + e[:200])
                    results.append((cid, 'caught' if all(s == 'FAILED' for _, s, _ in states) else ('crashed' if any(s == 'CRASHED' for _, s, _ in states) else 'MISSED')))
            finally:
                for path, text in originals.items():
                    open(path, 'w').write(text)
        for cid, what, env_extra, tests in CLIPS:
            if only and cid not in only:
                continue
            say('')
            say('## %s: %s' % (cid, what))
            tmp = tempfile.mkdtemp(prefix='nc-')
            try:
                if not build(env_extra, tmp):
                    say('  the Blender build failed')
                    results.append((cid, 'invalid'))
                    continue
                states = []
                for t in tests:
                    if t == 'contact':
                        states.append(run_contact(os.path.join(tmp, 'clip_contact.csv')))
                    else:
                        shutil.copy(os.path.join(tmp, 'relay_ar_arms.glb'), GLB)
                        godot(['--headless', '--editor', '--import', '--quit'], display=False)
                        states.append(run_test(t))
                for name, state, errs in states:
                    say('  %-30s %s' % (name, state))
                    for e in errs:
                        say('      ' + e[:200])
                results.append((cid, 'caught' if all(s == 'FAILED' for _, s, _ in states) else ('crashed' if any(s == 'CRASHED' for _, s, _ in states) else 'MISSED')))
            finally:
                open(GLB, 'wb').write(glb_backup)
                shutil.rmtree(tmp, ignore_errors=True)
        godot(['--headless', '--editor', '--import', '--quit'], display=False)
        say('')
        say('# Summary')
        for cid, state in results:
            say('  %-4s %s' % (cid, state))
        say('  %d controls: %d caught, %d crashed, %d missed, %d invalid' % (len(results), sum(s == 'caught' for _, s in results), sum(s == 'crashed' for _, s in results), sum(s == 'MISSED' for _, s in results), sum(s == 'invalid' for _, s in results)))
        return 0 if all(s == 'caught' for _, s in results) else 1
    finally:
        for path, text in originals.items():
            open(path, 'w').write(text)
        open(GLB, 'wb').write(glb_backup)


if __name__ == '__main__':
    sys.exit(main())
