#!/usr/bin/env python3
"""Negative controls for the reload tests: inject one defect at a time and check that the test that is
meant to catch it fails, cleanly (a summary line with failures, not a crash). Restores every file it
touches. Needs the Godot and Blender tools of scripts/setup.sh, and a native display for the visibility
controls (Xvfb on :99 is what the logs were made with).

    python3 scripts/reload_negative_controls.py [--only N5,N7] [--log path] [--raw-out dir]

Run serially in a DISPOSABLE checkout, never a shared working tree: these controls mutate sources.
--raw-out must be new/empty. It retains each command, streamed log, containment receipt, assessment,
and audio capture (mix_<scenario>.wav, voices_<scenario>.csv, report_<scenario>.txt). --log is exclusive.
Selecting A5,A6,A7 still runs ALL original baseline groups, including native visibility/lighting and
the contact CSV when present. Linux CI needs the pinned Godot, imported assets, and Xvfb on DISPLAY
(default :99); selecting only A5,A6,A7 does not require Blender. Do not use --no-baseline for acceptance.

Each control is a defect the reload could really have had, not an arbitrary edit:
  actor / phases source edits   the single-node replacement, the unseen replacement, no node swap, a grip
                                offset, reduced motion shrinking the staging, clicks from the authoritative
                                fraction, an early click, a click at the let-go, a double click on a rewind,
                                brass at the shooter's feet, the animation writing the timer, a drifted
                                phase constant, the old magazine returning to the well, the wrong sound
  rebuilt clips (Blender)       a hand that does not reach the magazine, the old grasp that hides the thumb,
                                the old approach from below the frame, a replacement fetched from below the frame
"""
import argparse
from contextlib import ExitStack
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time

from godot_process import godot_command, godot_environment, prepare_output
from matrix_process import run_process

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
GAME = os.path.join(REPO, 'game')
ACTOR = os.path.join(GAME, 'scripts', 'gameplay', 'actor.gd')
PHASES = os.path.join(GAME, 'scripts', 'gameplay', 'reload_phases.gd')
AUDIO = os.path.join(GAME, 'scripts', 'gameplay', 'reload_audio.gd')
CAPTURE_SCRIPT = os.path.join(GAME, 'tests', 'reload_audio_capture.gd')
GLB = os.path.join(GAME, 'assets', 'weapons', 'relay_ar', 'relay_ar_arms.glb')
SHADING = os.path.join(GAME, 'scripts', 'gameplay', 'viewmodel_shading.gd')
COSMETIC = os.path.join(GAME, 'scripts', 'ui', 'cosmetic_material.gd')
WEAPON_MODEL = os.path.join(GAME, 'scripts', 'gameplay', 'weapon_model.gd')
BPY = os.environ.get('BPY', os.path.join(os.path.dirname(REPO), 'tools', 'bpy-venv', 'bin', 'python'))
RIFLE = os.path.join(GAME, 'assets', 'weapons', 'relay_ar', 'relay_ar.glb')
SUMMARY_TAGS = {
    'reload_sequence_test.gd': 'RELOAD_SEQUENCE_TEST',
    'weapon_art_test.gd': 'WEAPON_ART_TEST',
    'reload_audio_test.gd': 'RELOAD_AUDIO_TEST',
    'reload_audio_capture.gd': 'RELOAD_AUDIO_CAPTURE',
    'reload_visibility_test.gd': 'RELOAD_VISIBILITY_TEST',
    'reload_discolour_probe.gd': 'RELOAD_DISCOLOUR_TEST',
    'viewmodel_light_probe.gd': 'VIEWMODEL_LIGHT_TEST',
}
SUMMARY = re.compile(r'^(?:' + '|'.join([*SUMMARY_TAGS.values(), 'RELOAD_CONTACT_TEST']) + r')\b[^\r\n]*', re.M)
ERRORS = re.compile(r'^[ \t]*ERROR:[^\r\n]*', re.M)
UNSAFE = re.compile(
    r'HARNESS_ERROR|SCRIPT ERROR|(?:Parse|Parser|Compile) Error|'
    r'Failed to (?:load script|compile)|Error parsing|\bleak(?:ed|s|ing)?\b|'
    r'(?:resources?|RIDs?)[^\r\n]*still in use|'
    r'Orphan StringName|unclaimed string names|'
    r'FATAL|CRASH|Segmentation fault|signal (?:6|11)\b', re.I)

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
BASELINE_TESTS = (SEQ, ART, AUD, CAP, CAP_CANCEL, VIS, VIS_REDUCED, DISC, LIGHT)

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
    ('A7', 'an unlogged reload voice plays before the first scheduled event', [(CAPTURE_SCRIPT, '\tactor.start_reload()\n', '\taudio._voices[0].stream = SBReloadAudio._streams["unlatch"][1]\n\taudio._voices[0].play()\n\tactor.start_reload()\n')], None, [CAP]),
]
CLIPS = [
    ('N15', 'a hand that does not reach the magazine (knuckle 50 mm off)', {'ARMS_GRAB_JSON': '{"mcp": [0.064, 0.15, -0.19]}'}, ['contact']),
    ('N16', 'the previous grasp, which hides the thumb behind the magazine', {'ARMS_GRAB_JSON': '{"distal": [1.0, 0.0, 0.0], "mcp": [0.034, 0.15, -0.19], "roll": 0}'}, [VIS]),
    ('N17', 'the previous approach from below the frame (the hand leaves the picture)', {'ARMS_APPROACH': '-0.020,-0.010,-0.085'}, [VIS]),
    ('N23', 'the replacement taken from just under the well, in view: it appears in the picture before the hand has it', {'ARMS_PATH_JSON': '{"hip": [-0.05, 0.03, -0.07], "carry": [-0.03, 0.04, -0.05]}'}, [SEQ]),
    ('N24', 'the magazine and hand move in straight lines between keys (robotic, with velocity jumps)', {'ARMS_LINEAR_PATHS': '1'}, [ART]),
    ('N18', 'the replacement fetched from far below the frame', {'ARMS_PATH_JSON': '{"hip": [-0.20, 0.04, -0.60], "carry": [-0.115, 0.05, -0.40]}'}, [VIS, SEQ]),
]


def write_json(path, value):
    with path.open('x', encoding='utf-8') as output:
        json.dump(value, output, indent=2)
        output.write('\n')


def receipt_errors(path, code):
    try:
        receipt = json.loads(path.read_text(encoding='utf-8'))
        if (not isinstance(receipt, dict) or receipt.get('complete') is not True
                or type(receipt.get('exit')) is not int
                or receipt['exit'] != code or not isinstance(receipt.get('errors'), list)
                or any(not isinstance(error, str) for error in receipt['errors'])):
            return ['invalid/mismatched process receipt']
        return list(receipt['errors'])
    except (OSError, ValueError) as error:
        return ['missing/unreadable process receipt: ' + str(error)]


class AttemptRunner:
    """All commands stream through the shared descendant owner, even without --raw-out."""
    def __init__(self, directory, raw=False):
        self.directory = directory
        self.raw = raw
        self.count = 0

    def invoke(self, name, arguments, *, role, control=None, native=False,
               display=True, timeout=900, env_extra=None):
        self.count += 1
        label = re.sub(r'[^a-zA-Z0-9_-]+', '-', '-'.join(filter(None, [role, control, name]))).strip('-')
        directory = self.directory / ('%03d-%s' % (self.count, label))
        directory.mkdir()  # Never reuse an invocation, even if a caller supplies a stale runner.
        log_path, result_path = directory / 'native.log', directory / 'process.json'
        arguments = list(map(str, arguments))
        capture = None
        if self.raw and native and 'res://tests/reload_audio_capture.gd' in arguments:
            if any(arg.startswith('--out=') for arg in arguments):
                raise ValueError('capture output must be owned by this invocation')
            capture = directory / 'capture'
            capture.mkdir()
            arguments.append('--out=' + str(capture.resolve()))
        command = None
        code = 1
        errors = []
        interrupted = None
        started = time.monotonic()
        with log_path.open('x', encoding='utf-8') as log:
            try:
                env = dict(os.environ, **(env_extra or {}))
                if native:
                    if display:
                        env.setdefault('DISPLAY', ':99')
                    if self.raw:
                        env = godot_environment(root=Path(REPO), env=env)
                        command = godot_command(arguments, root=Path(REPO), env=env)
                    else:
                        command = [os.path.join(REPO, 'scripts', 'godot.sh'), *arguments]
                else:
                    command = arguments
                write_json(directory / 'command.json', {
                    'command': command, 'cwd': REPO, 'timeout': timeout,
                    'role': role, 'control': control, 'environment_overrides': {
                        key: env[key] for key in ('DISPLAY', 'GODOT_BIN', 'SIGHTBREAK_TOOLS_DIR',
                                                 'SIGHTBREAK_STATE_DIR', 'XDG_DATA_HOME',
                                                 'XDG_CONFIG_HOME', 'XDG_CACHE_HOME',
                                                 'ANDROID_USER_HOME', *(env_extra or {})) if key in env},
                })
                code = run_process(command, cwd=Path(REPO), env=env, log=log,
                                   result_path=result_path, timeout=timeout)
            except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as error:
                errors.append(str(error))
                log.write('\nHARNESS_ERROR ' + str(error) + '\n')
            except (KeyboardInterrupt, SystemExit) as error:
                interrupted = error
                errors.append(type(error).__name__ + ': ' + str(error))
                log.write('\nHARNESS_ERROR ' + errors[-1] + '\n')
        if not (directory / 'command.json').exists():
            write_json(directory / 'command.json', {'command': command, 'arguments': arguments,
                                                    'cwd': REPO, 'role': role, 'control': control})
        errors.extend(receipt_errors(result_path, code))
        artifacts = {}
        if capture is not None:
            scenario = next(arg.split('=', 1)[1] for arg in arguments if arg.startswith('--scenario='))
            for filename in ('mix_%s.wav', 'voices_%s.csv', 'report_%s.txt'):
                path = capture / (filename % scenario)
                if not path.is_file() or path.is_symlink() or not path.stat().st_size:
                    errors.append('missing/empty capture artifact: ' + path.name)
                else:
                    artifacts[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
        out = log_path.read_text(encoding='utf-8', errors='replace')
        write_json(directory / 'attempt.json', {
            'name': name, 'role': role, 'control': control, 'command': command,
            'exit': code, 'seconds': round(time.monotonic() - started, 3),
            'log': log_path.name, 'process_receipt': result_path.name,
            'containment_and_artifact_errors': errors, 'capture_sha256': artifacts,
        })
        if interrupted is not None:
            raise interrupted
        return {'directory': directory, 'exit': code, 'output': out, 'errors': errors}


def unexpected_assertion_errors(out):
    """Assertions print FAIL (capture/contact/verbose) or Godot's push_error context.

    A generic native ERROR, e.g. a failed resource load, is not a detector result
    merely because another assertion also failed in the same invocation.
    """
    messages = {message.strip() for message in re.findall(r'^FAIL[ \t]+([^\r\n]+)', out, re.M)}
    unexpected = []
    for match in ERRORS.finditer(out):
        message = match.group().strip().removeprefix('ERROR:').strip()
        context = []
        for line in out[match.end():].splitlines():
            if line and not line[0].isspace():
                break
            context.append(line)
        if message not in messages and not re.search(r'^\s+at: push_error\s*\(', '\n'.join(context), re.M):
            unexpected.append(match.group().strip())
    return unexpected


def classify(out, code, expected, fields=None, process_errors=()):
    """FAILED means a completed assertion failure, never a broken test or a crash."""
    errors = list(process_errors)
    if type(code) is not int:
        errors.append('native exit must be an integer')
    unsafe = UNSAFE.search(out)
    if unsafe:
        errors.append('unsafe native output: ' + unsafe.group())
    matches = SUMMARY.findall(out)
    summary = None
    if len(matches) != 1 or matches[0].split()[0] != expected:
        errors.append('expected exactly one %s summary (exit %s)' % (expected, code))
    else:
        line = matches[0]
        values = {}
        for key in ('checks', 'failures', *(fields or {})):
            found = re.findall(r'(?:^|\s)' + re.escape(key) + r'=([^\s]+)', line)
            if len(found) != 1:
                errors.append('missing/duplicate summary field: ' + key)
            else:
                values[key] = found[0]
        if not all(re.fullmatch(r'\d+', values.get(key, '')) for key in ('checks', 'failures')):
            errors.append('summary must contain integer checks and failures')
        else:
            checks, failures = int(values['checks']), int(values['failures'])
            if checks <= 0 or failures > checks:
                errors.append('incomplete/inconsistent summary counts')
            else:
                summary = {'line': line, 'checks': checks, 'failures': failures}
        for key, value in (fields or {}).items():
            if values.get(key) != value:
                errors.append('unexpected summary %s (expected %s)' % (key, value))
    if errors:
        return ('CRASHED' if not matches else 'BROKEN'), errors, summary
    logged_errors = [line.strip() for line in ERRORS.findall(out)]
    if summary['failures']:
        if code != 1:
            return 'BROKEN', ['failing summary requires expected assertion exit 1, got %s' % code] + logged_errors, summary
        if unexpected_assertion_errors(out) or len(logged_errors) > summary['failures']:
            return 'BROKEN', ['unrelated/excess ERROR output is not an expected assertion'] + logged_errors, summary
        # Only a complete failing summary + exit 1 permits expected check()/push_error output.
        return 'FAILED', logged_errors, summary
    if code != 0 or logged_errors:
        return 'BROKEN', ['passing summary requires exit 0 and no ERROR output (exit %s)' % code] + logged_errors, summary
    return 'passed', [], summary


def assess(attempt, name, expected, fields=None):
    state, errors, summary = classify(attempt['output'], attempt['exit'], expected,
                                      fields, attempt['errors'])
    write_json(attempt['directory'] / 'assessment.json', {
        'name': name, 'state': state, 'summary': summary, 'errors': errors,
    })
    return name, state, errors


def run_test(test, runner, *, role='baseline', control=None):
    name, args = test
    script = args[args.index('--script') + 1].rsplit('/', 1)[-1]
    fields = {}
    if script == 'reload_audio_capture.gd':
        fields['scenario'] = next(arg.split('=', 1)[1] for arg in args if arg.startswith('--scenario='))
    if script in ('reload_audio_capture.gd', 'reload_visibility_test.gd'):
        fields['reduced'] = 'true' if '--reduced' in args else 'false'
    attempt = runner.invoke(name, args, role=role, control=control, native=True)
    return assess(attempt, name, SUMMARY_TAGS[script], fields)


def run_contact(csv_path, runner, *, role='baseline', control=None):
    attempt = runner.invoke('contact', [sys.executable, os.path.join(REPO, 'scripts', 'test_reload_contact.py'), csv_path],
                            role=role, control=control)
    return assess(attempt, 'contact', 'RELOAD_CONTACT_TEST')


def operation(attempt):
    errors = list(attempt['errors'])
    if attempt['exit'] != 0 or UNSAFE.search(attempt['output']) or ERRORS.search(attempt['output']):
        errors.append('operation did not exit cleanly (exit %s)' % attempt['exit'])
    write_json(attempt['directory'] / 'assessment.json', {'passed': not errors, 'errors': errors})
    return not errors


def build(env_extra, out, runner, control):
    return operation(runner.invoke('Blender build', [BPY, os.path.join(REPO, 'tools', 'art', 'arms_build.py'),
                                                    out, '--no-bake', '--rifle', RIFLE],
                                   role='mutant', control=control, env_extra=env_extra, timeout=600))


def import_assets(runner, *, role, control=None):
    return operation(runner.invoke('asset import', ['--headless', '--editor', '--import', '--quit'],
                                   native=True, display=False, role=role, control=control))


def mutation_bytes(before, old, new):
    """Match one exact anchor across LF/CRLF encodings, not fuzzy text/whitespace.

    Historical text-mode reads accepted either checkout encoding. Keep that
    portability without normalizing unrelated source bytes during restoration.
    A duplicate anchor in either encoding is still an invalid control.
    """
    anchors = [old.encode('utf-8')] if old else []
    if '\n' in old and '\r' not in old:
        anchors.append(old.replace('\n', '\r\n').encode('utf-8'))
    count = sum(before.count(anchor) for anchor in anchors)
    if count != 1:
        raise ValueError('expected exactly one anchor, found %d: %r' % (count, old[:80]))
    anchor = next(anchor for anchor in anchors if before.count(anchor))
    crlf = b'\r\n' in anchor or (b'\n' not in anchor and b'\r\n' in before
                                and before.count(b'\n') == before.count(b'\r\n'))
    replacement = new.replace('\r\n', '\n').replace('\n', '\r\n') if crlf else new
    return anchor, replacement.encode('utf-8'), 'CRLF' if crlf else 'LF'


def apply_mutations(edits):
    """Preflight all exact, unique anchors before writing any mutation."""
    pending = {}
    changes = []
    for filename, old, new in edits:
        path = Path(filename)
        before = pending[path] if path in pending else path.read_bytes()
        try:
            anchor, replacement, newlines = mutation_bytes(before, old, new)
        except ValueError as error:
            raise ValueError(path.name + ': ' + str(error)) from error
        after = before.replace(anchor, replacement, 1)
        if after == before:
            raise ValueError('mutation must change source bytes: ' + str(path))
        pending[path] = after
        changes.append({'path': str(path), 'old': old, 'new': new, 'matches': 1, 'newlines': newlines,
                        'before_sha256': hashlib.sha256(before).hexdigest(),
                        'after_sha256': hashlib.sha256(after).hexdigest()})
    for path, data in pending.items():
        path.write_bytes(data)
    return changes


def restore_files(originals):
    errors = []
    for path, data in originals.items():
        try:
            if not path.is_file() or path.read_bytes() != data:
                path.write_bytes(data)
            if path.read_bytes() != data:
                errors.append('bytes differ: ' + str(path))
        except OSError as error:
            errors.append(str(path) + ': ' + str(error))
    if errors:
        raise RuntimeError('byte restoration failed: ' + '; '.join(errors))


def hashes(contents):
    return {str(path): hashlib.sha256(data).hexdigest() for path, data in contents.items()}


def control_state(states):
    if states and all(state == 'FAILED' for _, state, _ in states):
        return 'caught'
    if any(state in ('CRASHED', 'BROKEN') for _, state, _ in states):
        return 'crashed'
    return 'MISSED'


def run_controls(args, runner, say):
    # Snapshot and restore BYTES: text-mode restoration silently changed CRLF/encoding before.
    paths = sorted({ACTOR, PHASES, AUDIO} | {path for c in SOURCE for path, _, _ in c[2]})
    originals = {Path(path): Path(path).read_bytes() for path in paths}
    glb = Path(GLB)
    glb_backup = glb.read_bytes()
    snapshots = {**originals, glb: glb_backup}
    tools = {path: path.read_bytes() for path in (Path(__file__), Path(__file__).with_name('matrix_process.py'),
                                                Path(__file__).with_name('godot_process.py'),
                                                Path(__file__).with_name('test_reload_negative_controls.py'))}
    write_json(runner.directory / 'sources-before.json', {
        'repo': REPO, 'python': sys.version, 'executable': sys.executable,
        'sources': hashes(snapshots), 'tooling': hashes(tools),
        'only': sorted(args.only) if args.only else None, 'baseline_skipped': args.no_baseline,
    })
    results, base = [], []
    exit_code = 2
    clip_changed = False

    def show(states):
        for name, state, errors in states:
            say('  %-30s %s' % (name, state))
            for error in errors:
                say('      ' + error[:200])  # Full evidence remains in native.log/assessment.json.

    try:
        say('# Baseline (no defect injected): every test passes')
        if args.no_baseline:
            say('  (skipped by --no-baseline: NOT baseline acceptance evidence)')
        else:
            # --only never narrows the baseline or changes any original scenario/threshold.
            base = [run_test(test, runner) for test in BASELINE_TESTS]
            csv_good = os.path.join(REPO, 'docs', 'reports', 'media', 'art-v9', 'hands', 'logs', 'clip_contact.csv')
            if os.path.exists(csv_good):
                base.append(run_contact(csv_good, runner))
        show(base)
        if any(state != 'passed' for _, state, _ in base):
            say('BASELINE FAILS: the controls below mean nothing until it passes')
            return 2
        for cid, what, edits, _, tests in SOURCE:
            if args.only and cid not in args.only:
                continue
            say('\n## %s: %s' % (cid, what))
            try:
                try:
                    changes = apply_mutations(edits)
                except ValueError as error:
                    say('  INVALID CONTROL: ' + str(error))
                    write_json(runner.directory / ('control-%s.json' % cid), {'control': cid, 'error': str(error)})
                    results.append((cid, 'invalid'))
                    continue
                write_json(runner.directory / ('control-%s.json' % cid), {'control': cid, 'description': what, 'edits': changes})
                states = [run_test(test, runner, role='mutant', control=cid) for test in tests]
                show(states)
                results.append((cid, control_state(states)))
            finally:
                restore_files(originals)
        for cid, what, env_extra, tests in CLIPS:
            if args.only and cid not in args.only:
                continue
            say('\n## %s: %s' % (cid, what))
            tmp = runner.directory / ('clip-' + cid) if runner.raw else Path(tempfile.mkdtemp(prefix='nc-'))
            if runner.raw:
                tmp.mkdir()
            try:
                if not build(env_extra, str(tmp), runner, cid):
                    say('  the Blender build failed')
                    results.append((cid, 'invalid'))
                    continue
                states = []
                for test in tests:
                    if test == 'contact':
                        states.append(run_contact(str(tmp / 'clip_contact.csv'), runner, role='mutant', control=cid))
                    else:
                        shutil.copy(tmp / 'relay_ar_arms.glb', GLB)
                        clip_changed = True
                        if not import_assets(runner, role='mutant', control=cid):
                            states.append(('asset import', 'BROKEN', ['import failed; see raw attempt']))
                            break
                        states.append(run_test(test, runner, role='mutant', control=cid))
                show(states)
                results.append((cid, control_state(states)))
            finally:
                restore_files({glb: glb_backup})
                if not runner.raw:
                    shutil.rmtree(tmp, ignore_errors=True)
        # Source-only controls do not change imported assets. Do not launch an unrelated import.
        restored_import = not clip_changed or import_assets(runner, role='restore')
        say('\n# Summary')
        for cid, state in results:
            say('  %-4s %s' % (cid, state))
        say('  %d controls: %d caught, %d crashed, %d missed, %d invalid' % (
            len(results), sum(s == 'caught' for _, s in results), sum(s == 'crashed' for _, s in results),
            sum(s == 'MISSED' for _, s in results), sum(s == 'invalid' for _, s in results)))
        exit_code = 0 if results and all(state == 'caught' for _, state in results) and restored_import else 1
        return exit_code
    finally:
        restoration_error = None
        try:
            restore_files(snapshots)
        except RuntimeError as error:
            restoration_error = str(error)
            exit_code = 2
        after = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
                 for path in snapshots}
        write_json(runner.directory / 'sources-after.json', {
            'sources': after, 'byte_restored': after == hashes(snapshots), 'error': restoration_error})
        write_json(runner.directory / 'result.json', {'exit': exit_code, 'baseline': base, 'controls': results,
                                                    'baseline_skipped': args.no_baseline})
        if restoration_error:
            raise RuntimeError(restoration_error)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--only', help='comma-separated control IDs; never narrows the baseline')
    parser.add_argument('--no-baseline', action='store_true', help='diagnostic only; not baseline acceptance')
    parser.add_argument('--log', type=Path, help='new summary log (exclusive, no overwrite)')
    parser.add_argument('--raw-out', type=Path, help='new/empty directory for all raw attempts and captures')
    args = parser.parse_args(argv)
    if args.only is not None:
        args.only = {value.strip() for value in args.only.split(',')}
        known = {control[0] for control in SOURCE + CLIPS}
        if not args.only or not args.only <= known:
            parser.error('unknown/empty control IDs: ' + ', '.join(sorted(args.only - known)))
    with ExitStack() as stack:
        log = None
        try:
            directory = prepare_output(args.raw_out) if args.raw_out else Path(stack.enter_context(
                tempfile.TemporaryDirectory(prefix='reload-negative-controls-')))
            log = stack.enter_context(args.log.open('x', encoding='utf-8')) if args.log else None

            def say(text=''):
                print(text, flush=True)
                if log:
                    log.write(text + '\n')
                    log.flush()

            return run_controls(args, AttemptRunner(directory, raw=args.raw_out is not None), say)
        except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as error:
            message = 'HARNESS_ERROR ' + str(error)
            print(message, file=sys.stderr, flush=True)
            if log:
                log.write(message + '\n')
                log.flush()
            return 2


if __name__ == '__main__':
    sys.exit(main())
