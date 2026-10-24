#!/usr/bin/env python3
"""Drive an actual Linux/Windows export through offline play and a normal restart.

Raw native captures require independent visual inspection. OCR only analyzes
scaled copies of those pixels. This checks the existing living-player weapon,
natural-round and settings flow; objective/full-match acceptance is separate.
"""
import argparse
import ctypes as C
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import re
import shutil
import signal
import subprocess
import sys
import time
from urllib.parse import quote

from build_manifest import BUILDS, OUTPUTS, source, validate_record
from PIL import Image, ImageChops
from native_log import failed
from native_observation import read_observation_json
from native_focus_fence import FocusContextFence, FocusPreconditionLost, fresh_focus_movement
from native_settings_route import relocate_settings_actor
from verify_integration_export import NativeUI, WinUI, windows_job
import toolchain


REFERENCE = (1280, 720)
MAX_OCR_STDOUT_BYTES = 2 * 1024 * 1024


def read_hud_pixels(path, ocr):
    with Image.open(path) as image:
        def text(box, health_contrast=False, psm=6):
            # Crop coordinates describe the reference layout; raw captures
            # retain the actual native client dimensions and pixels.
            crop = image.crop(tuple(round(value * image.size[index % 2] / REFERENCE[index % 2])
                                    for index, value in enumerate(box)))
            crop = crop.resize(((box[2] - box[0]) * 3, (box[3] - box[1]) * 3))
            if health_contrast:
                # Critical health is red. Ordinary grayscale OCR can erase
                # that text against the dark HUD; analyze channel brightness
                # without changing the original native screenshot.
                red, green, blue = crop.convert('RGB').split()
                crop = ImageChops.lighter(ImageChops.lighter(red, green), blue).point(lambda value: 0 if value > 145 else 255)
            return ocr(crop, psm, Path(path).stem + ':' + str(box))
        status = text((0, 630, 450, 720), health_contrast=True)
        health = re.search(r'(?<!\d)(\d{1,3})\s*[^A-Z0-9]*HEALTH', status.upper())
        # One text line: exclude the grenade inventory beneath the ammunition.
        ammo_text = text((980, 648, 1280, 680), psm=7)
    match = re.search(r'(\d+)\s*/\s*(\d+)', ammo_text)
    if health is None or not 0 < int(health[1]) <= 100 or 'ELIMINATED' in status.upper() or 'SPECTATING' in status.upper() or match is None:
        raise RuntimeError('Rendered living-player/ammunition check failed: ' + repr((status, ammo_text)))
    return {'health': int(health[1]), 'ammo': int(match[1]), 'reserve': int(match[2]),
            'status_ocr': status, 'ammo_ocr': ammo_text}


def exact_ocr_caption(rows, caption):
    """Locate one complete caption on one OCR line; ambiguous/missing fails."""
    lines = {}
    for row in rows:
        identity = tuple(row.get(key) for key in ('page_num', 'block_num', 'par_num', 'line_num'))
        if any(value in (None, '') for value in identity):
            continue
        lines.setdefault(identity, []).append(row)
    matches = []
    for line in lines.values():
        line.sort(key=lambda row: row['left'])
        if [row['text'].upper() for row in line] != caption.upper().split():
            continue
        left, top = min(row['left'] for row in line), min(row['top'] for row in line)
        right = max(row['left'] + row['width'] for row in line)
        bottom = max(row['top'] + row['height'] for row in line)
        matches.append({'left': left, 'top': top, 'width': right-left, 'height': bottom-top, 'text': caption})
    return matches[0] if len(matches) == 1 else None


def focus_controls_released(state):
    # Neutral commands also occur while the held-input safety guard is engaged.
    # Wait for the controller itself to acknowledge the physical release.
    return (state.get('ui', {}).get('waiting_for_input_release') is False
            and state.get('local_input', {}).get('move') == [0, 0]
            and state.get('local_input', {}).get('fire') is False)


def require_living_capture_phase(state, actor_id, round_number):
    """Validate the named buy HUD; a later life or stale menu cannot replace it."""
    actor, ui = state.get('local_actor', {}), state.get('ui', {})
    if (state.get('schema') != 1 or isinstance(state.get('schema'), bool)
            or state.get('scope') != 'debug_offline_read_only_observation'
            or state.get('scenario') != 'standard' or state.get('time_scale') != 1
            or isinstance(state.get('time_scale'), bool)
            or state.get('phase') != 'buy' or state.get('round_number') != round_number
            or isinstance(state.get('round_number'), bool) or actor.get('id') != actor_id
            or isinstance(actor.get('id'), bool) or actor.get('alive') is not True
            or isinstance(actor.get('health'), bool) or not isinstance(actor.get('health'), (int, float))
            or not 0 < actor['health'] <= 100 or ui.get('screen') != 'game'
            or ui.get('focused') is not True or ui.get('paused') is not False
            or ui.get('scoreboard_visible') is not False):
        raise RuntimeError('Named capture lost its living buy-phase actor/round/focus context')
    for field in ('drawn_frames', 'wall_msec', 'simulation_tick'):
        value = state.get(field)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise RuntimeError('Named capture requires a valid nonnegative integer ' + field)


def capture_living_phase(name, *, actor_id, round_number, after, until,
                         observed, capture, binding, expected_binding, receipt,
                         clock=time.monotonic):
    """Fence two real drawn frames inside the caller's existing absolute budget.

    Callbacks use the native controller in production. Declared observation
    sequences can test this scheduling logic but cannot establish rendered pixels.
    """
    receipt.update(capture=name, expected_actor_id=actor_id, expected_round=round_number,
                   expected_phase='buy', expected_binding=expected_binding,
                   absolute_deadline_monotonic=until, additional_drawn_frames_required=2)

    def budget():
        value = until - clock()
        if value <= 0:
            raise TimeoutError('Original transition budget expired before named capture: ' + name)
        return value

    def require_binding():
        current = binding()
        if current != expected_binding:
            receipt['rejected_binding'] = current
            raise RuntimeError('Named capture changed source, native process, trace, or loaded settings: ' + name)
        budget()
        return current

    def acknowledge(state):
        if not state:
            return False
        # Preserve the actual old POST/dead state while the natural round turns.
        # The reopened initial event can also precede build_hud on the menu.
        number = state.get('round_number')
        if isinstance(number, int) and not isinstance(number, bool) and 1 <= number < round_number:
            return False
        if number == round_number and state.get('ui', {}).get('screen') == 'menu':
            return False
        require_living_capture_phase(state, actor_id, round_number)
        return True

    require_binding()
    acknowledged = observed(acknowledge, budget(), 'Named living buy phase: ' + name, after)
    receipt['acknowledged'] = acknowledged
    latest_render_observation = acknowledged

    def rendered(state):
        nonlocal latest_render_observation
        require_living_capture_phase(state, actor_id, round_number)
        if any(state[field] < latest_render_observation[field]
               for field in ('drawn_frames', 'wall_msec', 'simulation_tick')):
            receipt['counter_regression'] = {'previous': latest_render_observation, 'current': state}
            raise RuntimeError('Named capture observation or frame counter moved backward: ' + name)
        latest_render_observation = state
        return (state['wall_msec'] > acknowledged['wall_msec']
                and state['drawn_frames'] >= acknowledged['drawn_frames'] + 2)

    ready = observed(rendered, budget(), 'Two drawn frames before named capture: ' + name,
                     acknowledged['wall_msec'])
    receipt['ready'] = ready

    before_capture = observed(rendered, budget(), 'Fresh named context immediately before capture: ' + name,
                              ready['wall_msec'])
    receipt['before_capture'] = before_capture
    receipt['binding_before_capture'] = require_binding()
    budget()
    capture(name)

    # Source/profile verification can take time before capture. Read a barrier
    # after the actual screenshot, then require another publication beyond it;
    # a state already available before capture cannot be the sole after proof.
    barrier = observed(rendered, budget(), 'Observation barrier after raw capture: ' + name,
                       before_capture['wall_msec'])
    receipt['after_capture_barrier'] = barrier
    receipt['after_capture'] = observed(rendered, budget(), 'Fresh named context beyond post-capture barrier: ' + name,
                                        barrier['wall_msec'])
    receipt['binding_after_capture'] = require_binding()
    receipt['remaining_original_budget_seconds'] = budget()
    return receipt


def main(*, study_observer=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--target', choices=('linux', 'windows'), default='windows' if os.name == 'nt' else 'linux')
    parser.add_argument('--display', default=':104', help='Free isolated numbered X11 display (Linux only)')
    parser.add_argument('--xvfb', default=os.environ.get('XVFB_BIN') or shutil.which('Xvfb'))
    parser.add_argument('--quit-after', type=int, default=0, help='Premature-exit negative control; successful flow closes normally')
    parser.add_argument('--timeout', type=float, default=300, help='Whole-flow wall deadline, plus separately bounded failure cleanup')
    parser.add_argument('--tesseract', default=os.environ.get('TESSERACT_BIN') or shutil.which('tesseract'))
    parser.add_argument('--hosted-render-priority', choices=('inherited', 'below-normal'), default='inherited')
    parser.add_argument('--reopened-verbose', action='store_true',
                        help='Diagnostic engine verbosity for only the reopened process; original deadlines and strict gates apply')
    args = parser.parse_args()
    if args.target != ('windows' if os.name == 'nt' else 'linux') or platform.system() not in ('Linux', 'Windows'):
        parser.error('Run the selected export on native Linux/Windows; macOS gameplay input is UNVERIFIED')
    if not args.tesseract:
        parser.error('Set --tesseract or TESSERACT_BIN; native rendered health/ammunition checks require Tesseract')
    if args.hosted_render_priority != 'inherited' and args.target != 'windows':
        parser.error('Hosted render priority requires native Windows; other targets retain inherited priority')
    if args.quit_after < 0 or args.timeout <= 0:
        parser.error('Frame budget must be nonnegative and timeout positive')
    display_socket = None
    if args.target == 'linux':
        if not args.xvfb or not re.fullmatch(r':[0-9]+', args.display):
            parser.error('Supply Xvfb and a free isolated numbered display')
        display_socket = Path('/tmp/.X11-unix/X' + args.display[1:])
        if display_socket.exists():
            parser.error('Display already in use: ' + args.display)
    out = args.output.resolve()
    if out.exists() and any(out.iterdir()):
        parser.error('Use a new or empty evidence directory; earlier attempts are retained')
    out.mkdir(parents=True, exist_ok=True)
    executable = BUILDS / OUTPUTS[args.target]
    logs, processes, commands, ocr_commands, actions, events = [], [], [], [], [], []
    held_keys = set()
    ui = client = job = None
    before = manifest = None
    initial_exit = reopened_exit = None
    started = time.monotonic()
    deadline = started + args.timeout
    result = {'passed': False, 'target': args.target, 'host': platform.platform(),
              'controller_command': [sys.executable, *sys.argv], 'captures': []}
    # BEGIN SHUTDOWN STUDY OBSERVATIONS
    if study_observer is not None:
        result['shutdown_study_observations'] = []

    def study_close(process, name):
        # Diagnostic only: preserve the original request and exact wait budget.
        # Job queries happen after the wait, never between request and wait.
        receipt = {'process': name, 'pid': process.pid, 'close_limit_seconds': 20,
                   'request_before_monotonic': time.monotonic(),
                   'request_before_wall_unix_ns': time.time_ns()}
        try:
            ui.request_close()
            receipt.update(request_returned_monotonic=time.monotonic(),
                           request_returned_wall_unix_ns=time.time_ns())
            process.wait(timeout=min(20, remaining()))
        except BaseException as error:
            receipt['original_close_error'] = type(error).__name__ + ': ' + str(error)
            raise
        finally:
            receipt.update(wait_finished_monotonic=time.monotonic(),
                           wait_finished_wall_unix_ns=time.time_ns(), exit_code=process.poll())
            result['shutdown_study_observations'].append(receipt)
            study_observer('close_wait_finished', **receipt)
    # END SHUTDOWN STUDY OBSERVATIONS
    (out / 'results.json').write_text(json.dumps(result, indent=2) + '\n')

    def interrupted(signum, _frame):
        raise SystemExit('Native validation interrupted by signal ' + str(signum))

    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)

    def remaining():
        value = deadline - time.monotonic()
        if value <= 0:
            raise TimeoutError('Whole offline-input flow deadline exceeded')
        return value

    def transition_budget(until, label):
        value = min(remaining(), until - time.monotonic())
        if value <= 0:
            raise TimeoutError('Original transition budget expired: ' + label)
        return value

    def pause(seconds):
        if seconds >= remaining():
            raise TimeoutError('Whole offline-input flow deadline exceeded')
        time.sleep(seconds)

    def trace(event, **details):
        entry = {'event': event, 'seconds': time.monotonic() - started,
                 'wall_unix_msec': time.time_ns() // 1_000_000,
                 'held_keys': sorted(held_keys), **details}
        if ui is not None:
            try:
                entry['native_state'] = ui.diagnostics()
            except Exception as error:
                entry['native_state_error'] = str(error)
        actions.append(entry)
        (out / 'actions.json').write_text(json.dumps(actions, indent=2) + '\n')

    def launch(name, command, env=None):
        remaining()
        log = (out / (name + '.log')).open('w', encoding='utf-8')
        logs.append(log)
        process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, env=env, cwd=out,
                                   start_new_session=os.name != 'nt')
        processes.append((name, process))
        commands.append({'name': name, 'command': command, 'pid': process.pid,
                         'started_seconds': time.monotonic() - started})
        (out / 'commands.json').write_text(json.dumps(commands, indent=2) + '\n')
        # BEGIN SHUTDOWN STUDY LAUNCH
        if study_observer is not None:
            study_observer('native_launch', name=name, pid=process.pid)
        # END SHUTDOWN STUDY LAUNCH
        return process

    def wait_for(condition, seconds, label, process=None):
        trace('wait_begin', label=label, budget_seconds=seconds)
        until = min(deadline, time.monotonic() + seconds)
        while time.monotonic() < until:
            if process is not None and process.poll() is not None:
                raise RuntimeError(label + ': native process exited early')
            if condition():
                trace('wait_completed', label=label)
                return
            time.sleep(.1)
        raise TimeoutError(label)

    def key(name, down):
        remaining()
        trace('key_before', key=name, down=down)
        ui.key(name, down)
        (held_keys.add if down else held_keys.discard)(name)
        trace('key_after', key=name, down=down)

    def button(down):
        remaining()
        trace('button', down=down)
        ui.button(down)

    def tap(name):
        key(name, True)
        pause(.3)
        key(name, False)
        pause(1)

    def capture(name):
        remaining()
        trace('capture_begin', capture=name)
        ui.capture(out / (name + '.png'))
        remaining()
        with Image.open(out / (name + '.png')) as image:
            dimensions = list(image.size)
        result['captures'].append({'name': name, 'dimensions': dimensions})
        events.append(name)
        trace('capture_end', capture=name, dimensions=dimensions)
        print(name, flush=True)

    def ocr(image, psm, label):
        command = [args.tesseract, 'stdin', 'stdout', '--psm', str(psm)]
        if psm == 11:
            command.append('tsv')
        data = io.BytesIO()
        image.save(data, format='PNG')
        entry = {'command': command, 'label': label, 'started_seconds': time.monotonic() - started}
        ocr_commands.append(entry)
        def retain_stdout(payload, complete):
            # Raw .log files remain in the existing bounded QA receipt pack.
            # Keep bytes even on timeout, without letting a receipt grow freely.
            retained = payload[:MAX_OCR_STDOUT_BYTES]
            path = out / 'ocr-stdout' / (str(len(ocr_commands)).zfill(3) + '.log')
            path.parent.mkdir(exist_ok=True)
            path.write_bytes(retained)
            entry.update(stdout_path=path.relative_to(out).as_posix(), stdout_total_bytes=len(payload),
                         stdout_retained_bytes=len(retained), stdout_sha256=hashlib.sha256(retained).hexdigest(),
                         stdout_complete=complete and len(retained) == len(payload),
                         stdout_truncated=len(retained) != len(payload))
        with (out / 'ocr-stderr.log').open('ab') as stderr:
            stderr.write(('\nOCR ' + label + '\n').encode('utf-8'))
            try:
                completed = subprocess.run(command, input=data.getvalue(), stdout=subprocess.PIPE, stderr=stderr,
                                           timeout=min(20, remaining()))
            except subprocess.TimeoutExpired as error:
                retain_stdout(error.output or b'', False)
                entry.update(timed_out=True, exit_code=None)
                raise
            else:
                retain_stdout(completed.stdout, True)
                entry['exit_code'] = completed.returncode
            finally:
                entry['finished_seconds'] = time.monotonic() - started
                (out / 'ocr-commands.json').write_text(json.dumps(ocr_commands, indent=2) + '\n')
        if entry['stdout_truncated']:
            raise RuntimeError('OCR stdout exceeded its bounded receipt budget; prefix retained')
        if completed.returncode:
            raise RuntimeError('Tesseract failed: ' + label + '; raw stderr retained')
        return completed.stdout.decode('utf-8', errors='replace')

    def read_hud(name, *, resume_after=True, require_context=None):
        # Analyze the already captured native pixels while ordinary Escape
        # pause protects the living player from time spent in external OCR.
        native = ui.diagnostics()
        if held_keys or native.get('lmb_down') is not False or any(native.get('keys_down', {}).values()):
            raise RuntimeError('HUD analysis requires physically released controls')
        before_analysis = offline_observation()
        actor = before_analysis.get('local_actor', {})
        if (before_analysis.get('ui', {}).get('screen') != 'game'
                or before_analysis.get('ui', {}).get('focused') is not True
                or before_analysis.get('time_scale') != 1 or actor.get('alive') is not True):
            raise RuntimeError('HUD analysis requires the actual living, focused offline player')
        if require_context is not None:
            require_context(before_analysis)
        if before_analysis.get('ui', {}).get('paused') is True:
            reading = read_hud_pixels(out / (name + '.png'), ocr)
            if require_context is not None:
                after_analysis = observed(lambda state: state.get('ui', {}).get('paused') is True,
                                          5, 'Fresh existing pause after saved-HUD OCR: ' + name, before_analysis['wall_msec'])
                require_context(after_analysis)
            return reading

        def require_analysis_context(state):
            if require_context is not None:
                require_context(state)
            current = state.get('local_actor', {})
            if (state.get('phase') != before_analysis['phase']
                    or state.get('round_number') != before_analysis['round_number'] or state.get('time_scale') != 1
                    or current.get('alive') is not True
                    or any(current.get(field) != actor.get(field) for field in ('id', 'weapon', 'ammo', 'reserve'))):
                raise RuntimeError('Player, round, life, weapon, or ammunition changed during saved-HUD analysis')

        def analysis_escape(cleanup=False):
            if cleanup:
                # Cleanup can release ordinary pause after the acceptance
                # deadline, just as the outer teardown releases held controls.
                ui.key('Escape', True)
                held_keys.add('Escape')
                trace('key_after', key='Escape', down=True, scope='saved_hud_analysis_cleanup')
            else:
                key('Escape', True)
            try:
                if cleanup:
                    time.sleep(.1)
                else:
                    pause(.1)
            finally:
                # Key-up remains mandatory even if the whole-flow deadline
                # expires while this ordinary native press is being delivered.
                ui.key('Escape', False)
                held_keys.discard('Escape')
                trace('key_after', key='Escape', down=False, scope='saved_hud_analysis')

        receipt = {'capture': name, 'before': before_analysis, 'scope': 'ordinary native pause for saved-pixel OCR',
                   'resume_after_analysis': resume_after}
        result.setdefault('hud_analysis_pauses', []).append(receipt)
        try:
            analysis_escape()
            paused_state = observed(lambda state: state.get('ui', {}).get('paused') is True,
                                    10, 'Native pause before saved-HUD OCR: ' + name, before_analysis['wall_msec'])
            require_analysis_context(paused_state)
            receipt['paused'] = paused_state
            reading = read_hud_pixels(out / (name + '.png'), ocr)
            after_analysis = observed(lambda state: state.get('ui', {}).get('paused') is True,
                                      5, 'Fresh paused observation after saved-HUD OCR: ' + name, paused_state['wall_msec'])
            require_analysis_context(after_analysis)
            if (after_analysis.get('elapsed') != paused_state.get('elapsed')
                    or after_analysis['local_actor'].get('health') != paused_state['local_actor'].get('health')):
                raise RuntimeError('Ordinary offline pause did not freeze gameplay during saved-HUD OCR')
            receipt['after_analysis'] = after_analysis
            return reading
        finally:
            if resume_after and client.poll() is None and offline_observation().get('ui', {}).get('paused') is True:
                analysis_escape(cleanup=True)
                resumed_state = observed(lambda state: state.get('ui', {}).get('paused') is False,
                                         10, 'Explicit native resume after saved-HUD OCR: ' + name)
                require_analysis_context(resumed_state)
                receipt['resumed'] = resumed_state

    def ocr_words():
        remaining()
        ui.capture(out / 'ocr-current.png')
        # Analysis only: scale text coordinates into the shared1280x720 layout.
        # The saved native screenshot itself is never resized or thresholded.
        with Image.open(out / 'ocr-current.png') as native:
            # Preserve native antialiasing while scaling. Saved-pixel replay
            # read LEAYE when tiny native glyphs were thresholded first.
            image = native.convert('L').resize((REFERENCE[0] * 2, REFERENCE[1] * 2))
            image = image.point(lambda value: 0 if value > 145 else 255)
        raw = ocr(image, 11, 'current-native-ui')
        rows = [row for row in csv.DictReader(io.StringIO(raw), delimiter='\t') if row.get('text', '').strip()]
        for row in rows:
            for name in ('left', 'top', 'width', 'height'):
                row[name] = int(row[name]) // 2
        return rows

    def click_text(word, *, caption=None, heading=None, require_context=None):
        if require_context is not None:
            require_context(offline_observation())
        rows = ocr_words()
        if heading is not None and exact_ocr_caption(rows, heading) is None:
            raise RuntimeError('Native UI heading not found: ' + heading)
        row = (exact_ocr_caption(rows, caption) if caption is not None
               else next((row for row in rows if row['text'].upper() == word), None))
        if row is None:
            raise RuntimeError('Native UI text not found: ' + word)
        if require_context is not None:
            require_context(offline_observation())
        ui.click(row['left'] + row['width'] // 2, row['top'] + row['height'] // 2)
        trace('click_text', text=word, caption=caption, heading=heading)
        pause(1)

    def client_has(message):
        return message in (out / 'client.log').read_text(encoding='utf-8', errors='replace')

    def audit_clients():
        if os.name == 'nt':
            accounting = C.create_string_buffer(48)
            if not job[0].QueryInformationJobObject(job[1], 1, accounting, len(accounting), None):
                raise C.WinError(C.get_last_error())
            if C.c_uint32.from_buffer(accounting, 40).value != 1:
                raise RuntimeError('Native roots exited but Windows job still owns a descendant')
        else:
            for name, process in processes:
                if name == 'xvfb':
                    continue
                try:
                    os.killpg(process.pid, 0)
                except ProcessLookupError:
                    continue
                raise RuntimeError(name + ': root exited but a native descendant remains alive')

    try:
        before = source()
        manifest = validate_record(args.target, before)
        with executable.open('rb') as stream:
            digest = hashlib.file_digest(stream, 'sha256').hexdigest()
        if digest != manifest['artifact']['sha256']:
            raise RuntimeError('Export executable does not match its exact-source receipt')
        result.update(source=before, artifact_source=manifest, executable_sha256=digest,
                      engine=toolchain.verify_engine())
        env = dict(os.environ)
        if args.target == 'linux':
            display = launch('xvfb', [args.xvfb, args.display, '-screen', '0', '1280x720x24', '-nolisten', 'tcp'])
            wait_for(display_socket.exists, 5, 'Xvfb readiness', display)
            env.update(DISPLAY=args.display, LIBGL_ALWAYS_SOFTWARE='1', LP_NUM_THREADS='2',
                       DBUS_SESSION_BUS_ADDRESS='unix:path=' + quote(str(out / 'unavailable-session-bus'), safe='/._-'))
            for variable, part in [('XDG_DATA_HOME', 'data'), ('XDG_CONFIG_HOME', 'config'), ('XDG_CACHE_HOME', 'cache')]:
                path = out / 'state' / part
                path.mkdir(parents=True, exist_ok=True)
                env[variable] = str(path)
            saved_path = Path(env['XDG_DATA_HOME']) / 'godot/app_userdata/SIGHTBREAK/offline_training.json'
            ui = NativeUI(args.display)
            flags = ['--accessibility', 'disabled', '--accessibility-driver', 'dummy']
        else:
            job = windows_job()
            for variable, part in [('APPDATA', 'roaming'), ('LOCALAPPDATA', 'local')]:
                path = out / 'state' / part
                path.mkdir(parents=True, exist_ok=True)
                env[variable] = str(path)
            saved_path = Path(env['APPDATA']) / 'Godot/app_userdata/SIGHTBREAK/offline_training.json'
            ui = WinUI()
            flags = ['--position', '0,0', '--resolution', f'{ui.width}x{ui.height}']
        result['profile_observation_path'] = str(saved_path)
        initial_trace = out / 'initial-offline-trace'
        client_command = [str(executable), '--audio-driver', 'Dummy', *flags]
        if args.quit_after:
            client_command += ['--quit-after', str(args.quit_after)]
        client_command += ['--', '--offline-validation', '--offline-trace-dir=' + str(initial_trace)]
        client = launch('client', client_command, env)
        if args.target == 'windows':
            ui.pid = client.pid
        wait_for(ui.focus_game, 30, 'Native export window', client)
        if args.hosted_render_priority == 'below-normal':
            result.setdefault('hosted_render_priority', []).append(ui.lower_owned_render_priority(client))
        wait_for(ui.menu_visible, 60, 'Native menu', client)
        capture('01-menu')
        # Loading can leave old menu pixels on screen after capture starts.
        # Wait for departure without sending that absolute click into gameplay.
        trace('deploy_click_before', x=248, y=319)
        ui.click(248, 319)
        trace('deploy_click_after', x=248, y=319)
        def offline_observation():
            try:
                state = read_observation_json(initial_trace / 'status.json')
            except (OSError, ValueError):
                return {}
            result['last_offline_observation'] = state
            if not isinstance(state, dict) or state.get('scope') != 'debug_offline_read_only_observation':
                error = RuntimeError('Unexpected offline observation scope')
                error.observation_state = state
                raise error
            return state

        def observed(predicate, seconds, label, after=-1):
            latest = {}
            def ready():
                nonlocal latest
                validate = getattr(predicate, 'validate_observation', None)
                try:
                    latest = offline_observation()
                except RuntimeError as error:
                    if validate is not None and hasattr(error, 'observation_state'):
                        validate(error.observation_state)
                    raise
                if validate is not None and latest != {}:
                    validate(latest)
                return latest.get('wall_msec', -1) > after and predicate(latest)
            wait_for(ready, seconds, label, client)
            trace('offline_observation', label=label, state=latest)
            return latest

        def phase_capture_binding(*, loaded_event=None):
            current = {'source': source(), 'process_pid': client.pid,
                       'process_running': client.poll() is None,
                       'trace_directory': str(initial_trace.resolve())}
            if loaded_event is not None:
                with (initial_trace / 'events.jsonl').open(encoding='utf-8') as stream:
                    current['loaded_initial_event'] = json.loads(stream.readline())
                current['stored_profile'] = json.loads(saved_path.read_text(encoding='utf-8'))
            return current

        initial_offline = observed(lambda state: state.get('ui', {}).get('screen') == 'game' and bool(state.get('local_actor')),
                                   30, 'Real offline match readiness after one Deploy click')
        pause(3)
        capture('02-offline-spawn')
        tap('b')
        capture('03-requisition')
        tap('Escape')
        # Deliver movement and aim in the actual live phase, rather than during
        # the buy phase where the authority correctly suppresses movement.
        wait_for(lambda: client_has('MATCH: Round live. Secure Relay Yard.'), 60,
                 'Actual offline live phase', client)
        wait_for(ui.focus_game, 5, 'Living-player input focus', client)
        key('d', True)
        pause(.3)
        key('d', False)
        ui.relative_motion(50, -10)
        trace('relative_motion', dx=50, dy=-10)
        capture('04-move-aim')
        pause(.25)
        fire_origin = offline_observation() or result.get('last_offline_observation', {})
        fire_actor = fire_origin.get('local_actor', {})
        if (fire_origin.get('phase') != 'live' or fire_origin.get('time_scale') != 1
                or fire_origin.get('round_number') != initial_offline.get('round_number')
                or fire_actor.get('id') != initial_offline.get('local_actor', {}).get('id')
                or fire_actor.get('alive') is not True or fire_actor.get('weapon') != 'sidearm'
                or fire_actor.get('ammo') != 15 or fire_actor.get('reserve') != 60
                or not isinstance(fire_origin.get('wall_msec'), int)
                or fire_origin['wall_msec'] <= initial_offline['wall_msec']):
            raise RuntimeError('Native fire requires an observed living player with the initial full sidearm')
        for _ in range(2):
            button(True)
            pause(1.0)
            button(False)
            pause(.35)
        fire_frame_ack = None
        def rendered_fire_ready(state):
            nonlocal fire_frame_ack
            if not state:
                return False
            actor = state.get('local_actor', {})
            if (state.get('time_scale') != 1
                    or state.get('phase') != 'live' or state.get('round_number') != fire_origin.get('round_number')
                    or actor.get('id') != fire_actor.get('id') or actor.get('alive') is not True
                    or actor.get('weapon') != 'sidearm' or actor.get('reserve') != 60 or actor.get('reload') != 0):
                raise RuntimeError('Fire acknowledgement changed player, round, life, weapon, reserve, or simulation speed')
            frames = state.get('drawn_frames')
            if not isinstance(frames, int) or isinstance(frames, bool) or frames < 0:
                raise RuntimeError('Fire capture requires a valid drawn-frame observation')
            if not 0 < actor.get('ammo', 15) < 15:
                return False
            if fire_frame_ack is None or fire_frame_ack[0] != actor['ammo']:
                fire_frame_ack = (actor['ammo'], frames)
            return frames >= fire_frame_ack[1] + 2
        # Reuse the original five-second authority budget, including this frame fence.
        before_reload = observed(rendered_fire_ready, 5, 'Authoritative depleted sidearm and two drawn frames', fire_origin['wall_msec'])
        capture('05-after-fire')
        fired_hud = read_hud('05-after-fire')
        if (not 0 < fired_hud['ammo'] < 15 or fired_hud['reserve'] != 60
                or any(fired_hud[field] != before_reload['local_actor'][field] for field in ('ammo', 'reserve'))):
            raise RuntimeError('Native fire rendered ammunition disagrees with acknowledged sidearm depletion')
        def reload_context(state):
            if not state:
                return None
            actor = state.get('local_actor', {})
            if (state.get('time_scale') != 1 or state.get('phase') != 'live'
                    or state.get('round_number') != before_reload['round_number']
                    or actor.get('id') != before_reload['local_actor']['id']
                    or actor.get('alive') is not True or actor.get('weapon') != 'sidearm'):
                raise RuntimeError('Reload observation changed player, round, weapon, life, or simulation speed')
            return actor

        def reload_began(state):
            actor = reload_context(state)
            if actor is None or actor.get('reload', 0) <= 0:
                return False
            if (actor.get('ammo') != before_reload['local_actor']['ammo']
                    or actor.get('reserve') != before_reload['local_actor']['reserve']):
                raise RuntimeError('Authoritative ammunition changed before the observed reload countdown completed')
            return True

        reload_input_seconds = time.monotonic() - started
        key('r', True)
        try:
            reload_started = observed(reload_began, 5, 'Real R input starts authoritative offline reload', before_reload['wall_msec'])
        finally:
            key('r', False)

        def reload_completed(state):
            actor = reload_context(state)
            if actor is None or actor.get('reload', 0) > 0:
                return False
            amount = 15 - before_reload['local_actor']['ammo']
            if actor.get('ammo') != 15 or actor.get('reserve') != before_reload['local_actor']['reserve'] - amount:
                raise RuntimeError('Authoritative offline reload did not transfer and conserve the exact ammunition')
            simulation_seconds = state['elapsed'] - reload_started['elapsed']
            if simulation_seconds < reload_started['local_actor']['reload'] - 1.0 / 60:
                raise RuntimeError('Authoritative offline reload finished before its observed simulation countdown')
            return True

        # A hosted software renderer may advance fewer than 60 physics ticks
        # per wall second. The retained failure completed a valid 1.3s reload
        # after 4.72 wall seconds; the old 2.5s sleep captured RELOADING 0.3s.
        # Wait for the real transfer, with a finite wall watchdog and the same
        # whole-flow deadline. This does not change game time or claim frame rate.
        reload_finished = observed(reload_completed, 15, 'Authoritative offline reload completion', reload_started['wall_msec'])
        finished_frames = reload_finished.get('drawn_frames')
        if not isinstance(finished_frames, int) or finished_frames < 0:
            raise RuntimeError('Offline reload capture requires a valid drawn-frame observation')

        def reload_rendered(state):
            return reload_completed(state) and state.get('drawn_frames', -1) >= finished_frames + 2

        reload_ready = observed(reload_rendered, 5, 'Two rendered frames after authoritative reload transfer', reload_finished['wall_msec'])
        result['native_reload'] = {'before': before_reload, 'started': reload_started, 'completed': reload_finished,
                                   'capture_ready': reload_ready, 'input_seconds': reload_input_seconds,
                                   'wall_seconds_after_input': time.monotonic() - started - reload_input_seconds,
                                   'observed_simulation_seconds': reload_finished['elapsed'] - reload_started['elapsed'],
                                   'completion_watchdog_seconds': 15, 'whole_flow_deadline_unchanged': True}
        capture('06-after-reload')
        reload_after_capture = offline_observation()
        if not reload_completed(reload_after_capture):
            raise RuntimeError('Offline reload state stopped being valid during native capture')
        result['native_reload']['after_capture'] = reload_after_capture
        reloaded_hud = read_hud('06-after-reload')
        if reloaded_hud['ammo'] != 15 or reloaded_hud['reserve'] >= fired_hud['reserve'] or sum(reloaded_hud[k] for k in ('ammo', 'reserve')) != sum(fired_hud[k] for k in ('ammo', 'reserve')):
            raise RuntimeError('Native offline reload did not conserve rendered ammunition')
        key('Tab', True)
        pause(.8)
        capture('06b-scoreboard')
        key('Tab', False)
        next_round_until = min(deadline, time.monotonic() + 160)
        wait_for(lambda: client_has('MATCH: Round 2'), transition_budget(next_round_until, 'Natural exported round completion'),
                 'Natural exported round completion', client)
        next_round_receipt = {'transition_watchdog_seconds': 160}
        result.setdefault('phase_capture_fences', {})['06c-next-round'] = next_round_receipt
        capture_living_phase('06c-next-round', actor_id=initial_offline['local_actor']['id'], round_number=2,
                             after=initial_offline['wall_msec'], until=next_round_until,
                             observed=observed, capture=capture, binding=phase_capture_binding,
                             expected_binding={'source': before, 'process_pid': client.pid, 'process_running': True,
                                               'trace_directory': str(initial_trace.resolve())}, receipt=next_round_receipt)
        tap('b')
        capture('06d-funded-requisition')
        click_text('VECTORLINE')
        capture('06e-purchased-smg')
        purchased_hud = read_hud('06e-purchased-smg')
        if purchased_hud['ammo'] != 30 or purchased_hud['reserve'] != 120:
            raise RuntimeError('Authoritative requisition did not equip the purchased SMG')
        second_live_until = min(deadline, time.monotonic() + 35)
        wait_for(lambda: (out / 'client.log').read_text(encoding='utf-8', errors='replace').count('MATCH: Round live.') >= 2,
                 transition_budget(second_live_until, 'Second active round for weapon switching'),
                 'Second active round for weapon switching', client)
        # This fixed ordinary-control route changes the test scenario: use the
        # existing freight container before spending time in settings captures.
        # Readiness and walking share the original 35s cap; no new life or budget.
        settings_route_start = observed(lambda state: state.get('phase') != 'buy',
                                        transition_budget(second_live_until, 'Living settings route start'),
                                        'Living second-round player before fixed settings route',
                                        next_round_receipt['after_capture']['wall_msec'])
        settings_route = result['settings_cover_route'] = {}
        def settings_route_pulse(names, seconds, until):
            remaining()
            receipt = {}
            settings_route.setdefault('native_pulses', []).append(receipt)
            trace('settings_route_native_pulse_before', keys=list(names), requested_seconds=seconds)
            held_keys.update(names)
            try:
                return ui.key_pulse(names, seconds, deadline=until, receipt=receipt)
            finally:
                if receipt.get('release_complete') or not receipt.get('attempted_keys'):
                    held_keys.difference_update(names)
                trace('settings_route_native_pulse_after', receipt=receipt)
        relocate_settings_actor(settings_route_start, actor_id=initial_offline['local_actor']['id'], round_number=2,
                                observe=offline_observation, key=key, pause=pause,
                                record=lambda event, **data: trace('settings_route_' + event, **data),
                                deadline=second_live_until, receipt=settings_route,
                                pulse=settings_route_pulse if args.target == 'windows' else None)
        transition_budget(second_live_until, 'Completed fixed settings route before weapon switching')
        tap('2')
        capture('06f-switched-sidearm')
        switched_hud = read_hud('06f-switched-sidearm')
        if switched_hud['ammo'] != 15:
            raise RuntimeError('Native sidearm switch did not reach the HUD')
        tap('1')
        capture('06g-switched-primary')
        # The next action is FIELD MENU. Retain the ordinary native pause
        # established for this OCR rather than briefly exposing the player to
        # combat between two consecutive uses of the same menu.
        primary_hud = read_hud('06g-switched-primary', resume_after=False)
        settings_pause = result['hud_analysis_pauses'][-1]['after_analysis']
        if primary_hud['ammo'] != 30 or primary_hud['reserve'] != 120:
            raise RuntimeError('Native primary switch did not restore the purchased weapon')
        capture('07-field-menu')
        click_text('SETTINGS')
        capture('07b-field-settings')
        words = ocr_words()
        mouse = next(row for row in words if row['text'].upper() == 'MOUSE')
        ui.click(800, mouse['top'] + mouse['height'] // 2)
        trace('settings_slider_click')
        pause(1)
        capture('07c-settings-changed')
        saved = json.loads(saved_path.read_text(encoding='utf-8'))
        if saved['scope'] != 'offline_training' or saved['settings']['sensitivity'] == 0.0028:
            raise RuntimeError('Native settings input was not persisted')
        # Settings must inherit the very same living paused transaction. A menu
        # that only hides input but leaves the offline authority running fails.
        settings_ready = observed(lambda state: state.get('ui', {}).get('paused') is True,
                                  5, 'Fresh paused player after native settings change', settings_pause['wall_msec'])
        def require_resume_context(state):
            actor, original = state.get('local_actor', {}), settings_pause['local_actor']
            if (state.get('ui', {}).get('screen') != 'game' or state.get('ui', {}).get('focused') is not True
                    or state.get('time_scale') != 1 or state.get('phase') != settings_pause['phase']
                    or state.get('round_number') != settings_pause['round_number'] or actor.get('alive') is not True
                    or any(actor.get(field) != original.get(field) for field in ('id', 'weapon', 'ammo', 'reserve'))):
                raise RuntimeError('Explicit resume changed living player, focus, round, weapon, ammunition, or simulation speed')
        require_resume_context(settings_ready)
        if (settings_ready.get('elapsed') != settings_pause.get('elapsed')
                or settings_ready['local_actor'].get('health') != settings_pause['local_actor'].get('health')):
            raise RuntimeError('Ordinary offline field settings did not retain the paused player')
        # A physical Escape is acknowledged by the actual game. The old generic
        # tap left the player idle in combat for one second before any capture.
        # Acknowledgment and the rendered-frame fence share one existing 10s
        # native transition budget; all surrounding deadlines stay unchanged.
        resume_until = min(deadline, time.monotonic() + 10)
        def resume_budget():
            value = resume_until - time.monotonic()
            if value <= 0:
                raise TimeoutError('Explicit native resume and rendered-frame acknowledgement')
            return value
        def resume_acknowledged(state):
            if not state:
                return False
            require_resume_context(state)
            return state.get('ui', {}).get('paused') is False
        key('Escape', True)
        try:
            resumed = observed(resume_acknowledged, resume_budget(),
                               'Actual living player explicitly resumes after field settings', settings_ready['wall_msec'])
        finally:
            # Always physically release Escape, including a failed/dead context.
            ui.key('Escape', False)
            held_keys.discard('Escape')
            trace('key_after', key='Escape', down=False, scope='field_settings_resume')
        resumed_frames = resumed.get('drawn_frames')
        if not isinstance(resumed_frames, int) or isinstance(resumed_frames, bool) or resumed_frames < 0:
            raise RuntimeError('Explicit native resume requires a valid drawn-frame observation')
        resumed_ready = observed(lambda state: resume_acknowledged(state)
                                 and state.get('drawn_frames', -1) >= resumed_frames + 2,
                                 resume_budget(), 'Two drawn frames after explicit native settings resume', resumed['wall_msec'])
        capture('07d-explicit-resume')
        resumed_after_capture = offline_observation()
        require_resume_context(resumed_after_capture)
        resumed_hud = read_hud('07d-explicit-resume', resume_after=False, require_context=require_resume_context)
        result['native_settings_resume'] = {'paused_before_settings': settings_pause, 'paused_after_settings': settings_ready,
                                             'resumed': resumed, 'capture_ready': resumed_ready, 'after_capture': resumed_after_capture,
                                             'transition_watchdog_seconds': 10, 'same_living_player_required': True}
        def require_leave_context(state):
            require_resume_context(state)
            if state.get('ui', {}).get('paused') is not True:
                raise RuntimeError('Native LEAVE input requires the same living paused field menu')
        click_text('LEAVE', caption='LEAVE MATCH', heading='FIELD MENU', require_context=require_leave_context)
        wait_for(ui.menu_visible, 30, 'Return from offline match', client)
        capture('08-return-menu')
        # BEGIN SHUTDOWN STUDY INITIAL CLOSE
        if study_observer is not None:
            study_close(client, 'client')
        else:
        # END SHUTDOWN STUDY INITIAL CLOSE
            ui.request_close()
            client.wait(timeout=min(20, remaining()))
        initial_exit = client.returncode
        if initial_exit != 0:
            raise RuntimeError('Initial native client did not exit cleanly')
        loaded_trace = out / 'restart-profile-trace'
        reopened = launch('reopened', [str(executable), '--audio-driver', 'Dummy', *flags,
                                     *(['--verbose'] if args.reopened_verbose else []), '--',
                                     '--offline-validation', '--offline-trace-dir=' + str(loaded_trace)], env)
        client = reopened
        if args.target == 'windows':
            ui.pid = reopened.pid
        wait_for(ui.focus_game, 30, 'Reopened native window', reopened)
        if args.hosted_render_priority == 'below-normal':
            result.setdefault('hosted_render_priority', []).append(ui.lower_owned_render_priority(reopened))
        wait_for(ui.menu_visible, 45, 'Reopened native menu', reopened)
        capture('09-reopened-menu')
        if json.loads(saved_path.read_text(encoding='utf-8')) != saved:
            raise RuntimeError('Local settings/training data changed across restart')
        # Disk equality alone cannot prove load_profile worked. Enter a fresh
        # ordinary match and observe the profile actually loaded by this process.
        trace('reopened_deploy_click_before', x=248, y=319)
        ui.click(248, 319)
        trace('reopened_deploy_click_after', x=248, y=319)
        loaded_until = min(deadline, time.monotonic() + 30)
        wait_for(lambda: (loaded_trace / 'events.jsonl').is_file(), transition_budget(loaded_until, 'Reopened profile load'),
                 'Reopened process loaded profile into ordinary offline match', reopened)
        with (loaded_trace / 'events.jsonl').open(encoding='utf-8') as stream:
            loaded = json.loads(stream.readline())
        if loaded.get('initial_conditions') != 'stock_spawns_teams_random_seeds' or loaded.get('initial_profile') != saved:
            raise RuntimeError('Reopened process did not load saved settings/training')
        # The initial profile event is published before build_hud. Observe this
        # reopened process, never the retired client's trace or last observation.
        initial_trace = loaded_trace
        loaded_receipt = {'transition_watchdog_seconds': 30}
        result.setdefault('phase_capture_fences', {})['10-reopened-loaded-settings'] = loaded_receipt
        capture_living_phase('10-reopened-loaded-settings', actor_id=loaded['local_actor']['id'], round_number=1,
                             after=loaded['wall_msec'], until=loaded_until,
                             observed=observed, capture=capture, binding=lambda: phase_capture_binding(loaded_event=loaded),
                             expected_binding={'source': before, 'process_pid': reopened.pid, 'process_running': True,
                                               'trace_directory': str(loaded_trace.resolve()),
                                               'loaded_initial_event': loaded, 'stored_profile': saved}, receipt=loaded_receipt)
        # The earlier round already exercises weapons and settings. Prove
        # focus recovery with a living player in this new, ordinary stock match.
        focus_start = observed(lambda state: state.get('ui', {}).get('focused') is True
                               and state.get('ui', {}).get('paused') is False
                               and state.get('time_scale') == 1
                               and state.get('phase') == 'live' and state.get('local_actor', {}).get('alive') is True,
                               60, 'Fresh stock match reaches a living active player before native focus loss', loaded['wall_msec'])
        focus_receipt = result['native_focus_recovery'] = {
            'scope': 'fresh stock match after settings restart', 'passed': False,
            'context_fence': {}, 'fresh_press': {}, 'capture_context': {}}
        fence = FocusContextFence(focus_start, focus_receipt['context_fence'])

        def require_focus_context(state, stage='focus_context', **context):
            return fence.require(state, stage, **context)

        def focus_raw_observation():
            try:
                return offline_observation()
            except RuntimeError as error:
                if not hasattr(error, 'observation_state'):
                    raise
                return error.observation_state

        def focus_observed(predicate, seconds, label, after=-1):
            def checked(state):
                require_focus_context(state, label)
                return predicate(state)
            checked.validate_observation = lambda state: fence.validate_observation(state, label + ':before_freshness')
            return observed(checked, seconds, label, after)

        require_focus_context(focus_raw_observation(), 'before_held_w_down', focused=True, paused=False)
        try:
            key('w', True)
            button(True)
            input_ack = focus_observed(lambda state: state.get('local_input', {}).get('fire') is True
                                 and state.get('local_input', {}).get('move', [0, 0]) != [0, 0],
                                 10, 'Game consumed physical W and LMB before native focus loss', focus_start['wall_msec'])
            require_focus_context(input_ack)
            if (input_ack.get('local_actor', {}).get('alive') is not True
                    or input_ack.get('ui', {}).get('focused') is not True
                    or input_ack.get('ui', {}).get('paused') is not False):
                raise RuntimeError('Physical input acknowledgment lost the living active focus-test context')
            trace('native_focus_held_input_acknowledged', state=input_ack)
            focus_receipt['held_input_acknowledged'] = input_ack
            trace('native_focus_loss_before', method='XSetInputFocus(root)' if args.target == 'linux' else 'ShowWindow(SW_MINIMIZE)')
            if args.target == 'linux':
                ui.x.XSetInputFocus(ui.d, ui.x.XDefaultRootWindow(ui.d), 1, 0)
                ui.x.XFlush(ui.d)
            else:
                ui.user.ShowWindow(ui.window, 6)  # SW_MINIMIZE
            trace('native_focus_loss_after')
            lost = focus_observed(lambda state: state.get('ui', {}).get('focused') is False
                            and state.get('ui', {}).get('paused') is True,
                            10, 'Native focus loss pauses actual offline match', focus_start['wall_msec'])
            require_focus_context(lost)
            focus_receipt['lost'] = lost
            trace('native_focus_restore_before')
            if args.target == 'windows':
                ui.user.ShowWindow(ui.window, 9)  # SW_RESTORE; focus_game retains the same HWND
            wait_for(ui.focus_game, 10, 'Restore actual native input focus', client)
            trace('native_focus_restore_after')
            restored = focus_observed(lambda state: state.get('ui', {}).get('focused') is True,
                                10, 'Actual game observes restored focus', lost['wall_msec'])
            require_focus_context(restored)
            if restored['ui'].get('paused') is not True or restored['ui'].get('mouse_mode') != 0:
                raise RuntimeError('Native focus restoration resumed gameplay or hid the pointer without explicit resume')
            focus_receipt['restored_paused'] = restored
            focus_receipt['capture_context']['11a-restored-focus-still-paused'] = {'before': restored}
            capture('11a-restored-focus-still-paused')
            after_capture = focus_raw_observation()
            focus_receipt['capture_context']['11a-restored-focus-still-paused']['after'] = after_capture
            require_focus_context(after_capture, 'after_restored_pause_capture', focused=True, paused=True)
            key('Escape', True)
            pause(.3)
            key('Escape', False)
            guarded = focus_observed(lambda state: state.get('ui', {}).get('paused') is False,
                               10, 'Explicit resume with W and LMB still physically held', restored['wall_msec'])
            baseline_actor = restored['local_actor']
            guard_samples = focus_receipt['held_neutral_samples'] = []
            def check_guard(state, stable_position=None):
                require_focus_context(state)
                inputs, actor = state.get('local_input', {}), state.get('local_actor', {})
                native = ui.diagnostics()
                if (state.get('ui', {}).get('focused') is not True or state['ui'].get('paused') is not False
                        or inputs.get('move') != [0, 0] or inputs.get('fire') is not False
                        or inputs.get('interact') is not False or inputs.get('reload') is not False
                        or actor.get('id') != baseline_actor.get('id') or actor.get('alive') is not True
                        or actor.get('ammo') != baseline_actor.get('ammo') or actor.get('weapon') != baseline_actor.get('weapon')
                        or abs(actor.get('yaw', 0) - baseline_actor.get('yaw', 0)) > 0.000001
                        or abs(actor.get('pitch', 0) - baseline_actor.get('pitch', 0)) > 0.000001
                        or native.get('lmb_down') is not True or native.get('keys_down', {}).get('w') is not True
                        or (stable_position is not None and actor.get('position') != stable_position)):
                    raise RuntimeError('Held input moved/fired after native focus recovery; raw observations retained')
                guard_samples.append(state)
            check_guard(guarded)
            # Focus-out can freeze ordinary pre-existing movement velocity.
            # Neutral input must hold throughout its bounded natural decay.
            settle_start = guarded['elapsed']
            while any(abs(guarded['local_actor']['velocity'][axis]) > .01 for axis in (0, 2)):
                guarded = focus_observed(lambda state: True, 10, 'Neutral held input while ordinary inertia settles',
                                   guarded['wall_msec'])
                check_guard(guarded)
                if guarded['elapsed'] - settle_start > 1.0:
                    raise RuntimeError('Neutral movement inertia failed to settle within one simulation second')
            stable_position = guarded['local_actor']['position'][:]
            for index in range(2):
                guarded = focus_observed(lambda state: True, 10, 'Fresh held-input guard sample ' + str(index + 1),
                                   guarded['wall_msec'])
                check_guard(guarded, stable_position)
            focus_receipt['capture_context']['11b-resumed-held-input-neutral'] = {'before': guarded}
            capture('11b-resumed-held-input-neutral')
            after_capture = focus_raw_observation()
            focus_receipt['capture_context']['11b-resumed-held-input-neutral']['after'] = after_capture
            require_focus_context(after_capture, 'after_held_neutral_capture', focused=True, paused=False)
        finally:
            key('w', False)
            button(False)
        released = focus_observed(focus_controls_released,
                            10, 'Released held focus-test controls', guarded['wall_msec'])
        focus_receipt['released'] = released
        moved = fresh_focus_movement(fence=fence, released=released, snapshot=focus_raw_observation,
                                    observed=observed, key=key, receipt=focus_receipt['fresh_press'])
        focus_receipt['capture_context']['11c-fresh-press-movement'] = {'before': moved}
        capture('11c-fresh-press-movement')
        after_capture = focus_raw_observation()
        focus_receipt['capture_context']['11c-fresh-press-movement']['after'] = after_capture
        require_focus_context(after_capture, 'after_fresh_movement_capture', focused=True, paused=False)
        focus_receipt['context_fence']['status'] = 'LIVING_CONTEXT_PRESERVED_THROUGH_CAPTURE'
        focus_receipt.update(passed=True, fresh_press_movement=moved)
        # BEGIN SHUTDOWN STUDY REOPENED CLOSE
        if study_observer is not None:
            study_close(reopened, 'reopened')
        else:
        # END SHUTDOWN STUDY REOPENED CLOSE
            ui.request_close()
            reopened.wait(timeout=min(20, remaining()))
        reopened_exit = reopened.returncode
        if reopened_exit or failed((out / 'reopened.log').read_text(encoding='utf-8', errors='replace')):
            raise RuntimeError('Reopened export failed clean shutdown')
        if json.loads(saved_path.read_text(encoding='utf-8')) != saved:
            raise RuntimeError('Uncompleted fresh focus-test match changed stored settings/training')
        result['incomplete_training_unchanged_after_reopened_exit'] = True
        if initial_exit != 0 or failed((out / 'client.log').read_text(encoding='utf-8', errors='replace')):
            raise RuntimeError('Export failed clean termination or native log gate')
        validate_record(args.target, before)
        if before != source():
            raise RuntimeError('Source changed during offline validation')
        audit_clients()
        remaining()
        result.update(passed=True, events=events, exit=reopened_exit, initial_exit=initial_exit, clean_exit=True,
                      exit_method='completion-driven WM_DELETE_WINDOW' if args.target == 'linux' else 'completion-driven WM_CLOSE',
                      settings_restart_equal=True, natural_round_completed=True, purchase_and_weapon_switch=True,
                      settings_loaded_into_reopened_process=True,
                      explicit_resume=True, exported_plant_defuse='UNVERIFIED',
                      training_progress='Stored record preserved; full exported match completion remains UNVERIFIED',
                      fired_hud=fired_hud, reloaded_hud=reloaded_hud, resumed_hud=resumed_hud,
                      capture_method='raw X11 desktop' if args.target == 'linux' else 'raw Windows client-area desktop capture',
                      movement_aim='Real native input delivered during live phase; authoritative displacement is not measured by this controller',
                      controller_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                      limits='Screenshots require visual review; no physical-device/performance acceptance. Linux isolated automation disables accessibility and D-Bus portals; their coverage remains UNVERIFIED.')
    except (Exception, SystemExit) as error:
        result.update(passed=False, error=str(error), source=before, artifact_source=manifest)
        if (isinstance(error, FocusPreconditionLost)
                or result.get('native_focus_recovery', {}).get('context_fence', {}).get('status') == 'FOCUS_PRECONDITION_LOST'):
            result['failure_kind'] = 'FOCUS_PRECONDITION_LOST'
        trace('failure', error=str(error))
    finally:
        cleanup_errors = []
        if ui:
            for name in list(held_keys):
                try:
                    ui.key(name, False)
                except Exception as error:
                    cleanup_errors.append('release ' + name + ': ' + str(error))
            try:
                ui.button(False)
                ui.close()
            except Exception as error:
                cleanup_errors.append('native input teardown: ' + str(error))
        for name, process in reversed(processes):
            try:
                if os.name != 'nt':
                    os.killpg(process.pid, signal.SIGTERM)
                elif process.poll() is None:
                    process.terminate()
            except ProcessLookupError:
                pass
            except Exception as error:
                cleanup_errors.append(name + ' termination: ' + str(error))
        for name, process in reversed(processes):
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                try:
                    if os.name != 'nt':
                        os.killpg(process.pid, signal.SIGKILL)
                    else:
                        process.kill()
                    process.wait(timeout=5)
                except Exception as error:
                    cleanup_errors.append(name + ' forced cleanup: ' + str(error))
            if os.name != 'nt':
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                except Exception as error:
                    cleanup_errors.append(name + ' descendant cleanup: ' + str(error))
        for entry, (name, process) in zip(commands, processes):
            entry['exit_code'] = process.returncode
        for log in logs:
            log.close()
        result.update(initial_exit=initial_exit, reopened_exit=reopened_exit, commands=commands,
                      events=events, cleanup_errors=cleanup_errors, ocr_commands=ocr_commands,
                      elapsed_seconds=time.monotonic() - started)
        if cleanup_errors:
            result.update(passed=False, error=result.get('error', 'Native process cleanup failed'))
        (out / 'commands.json').write_text(json.dumps(commands, indent=2) + '\n')
        (out / 'ocr-commands.json').write_text(json.dumps(ocr_commands, indent=2) + '\n')
        (out / 'results.json').write_text(json.dumps(result, indent=2) + '\n')
    if not result['passed']:
        print(json.dumps({'offline_input_failure': result, 'recent_actions': actions[-12:]}, indent=2))
        for name in ('client', 'reopened', 'ocr-stderr'):
            path = out / (name + '.log')
            if path.is_file():
                print(name + ' log tail (bounded):\n' + path.read_text(encoding='utf-8', errors='replace')[-12000:])
        raise RuntimeError(result.get('error', 'Native offline validation failed'))
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
