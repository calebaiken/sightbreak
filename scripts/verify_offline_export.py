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
from PIL import Image
from native_log import failed
from verify_integration_export import NativeUI, WinUI, windows_job
import toolchain


REFERENCE = (1280, 720)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--target', choices=('linux', 'windows'), default='windows' if os.name == 'nt' else 'linux')
    parser.add_argument('--display', default=':104', help='Free isolated numbered X11 display (Linux only)')
    parser.add_argument('--xvfb', default=os.environ.get('XVFB_BIN') or shutil.which('Xvfb'))
    parser.add_argument('--quit-after', type=int, default=0, help='Premature-exit negative control; successful flow closes normally')
    parser.add_argument('--timeout', type=float, default=300, help='Whole-flow wall deadline, plus separately bounded failure cleanup')
    parser.add_argument('--tesseract', default=os.environ.get('TESSERACT_BIN') or shutil.which('tesseract'))
    args = parser.parse_args()
    if args.target != ('windows' if os.name == 'nt' else 'linux') or platform.system() not in ('Linux', 'Windows'):
        parser.error('Run the selected export on native Linux/Windows; macOS gameplay input is UNVERIFIED')
    if not args.tesseract:
        parser.error('Set --tesseract or TESSERACT_BIN; native rendered health/ammunition checks require Tesseract')
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
        with (out / 'ocr-stderr.log').open('ab') as stderr:
            stderr.write(('\nOCR ' + label + '\n').encode('utf-8'))
            try:
                completed = subprocess.run(command, input=data.getvalue(), stdout=subprocess.PIPE, stderr=stderr,
                                           timeout=min(20, remaining()))
            except subprocess.TimeoutExpired:
                entry.update(timed_out=True, exit_code=None)
                raise
            finally:
                entry['finished_seconds'] = time.monotonic() - started
                (out / 'ocr-commands.json').write_text(json.dumps(ocr_commands, indent=2) + '\n')
        entry['exit_code'] = completed.returncode
        if completed.returncode:
            raise RuntimeError('Tesseract failed: ' + label + '; raw stderr retained')
        return completed.stdout.decode('utf-8', errors='replace')

    def read_hud(name):
        with Image.open(out / (name + '.png')) as image:
            def text(box):
                # Crop coordinates describe the reference layout; raw captures
                # retain the actual native client dimensions and pixels.
                crop = image.crop(tuple(round(value * image.size[index % 2] / REFERENCE[index % 2])
                                        for index, value in enumerate(box)))
                crop = crop.resize(((box[2] - box[0]) * 3, (box[3] - box[1]) * 3))
                return ocr(crop, 6, name + ':' + str(box))
            status = text((0, 630, 450, 720))
            health = re.search(r'(?<!\d)(\d{1,3})\s*[^A-Z0-9]*HEALTH', status.upper())
            ammo_text = text((980, 625, 1280, 710))
        match = re.search(r'(\d+)\s*/\s*(\d+)', ammo_text)
        if health is None or not 0 < int(health[1]) <= 100 or 'ELIMINATED' in status.upper() or 'SPECTATING' in status.upper() or match is None:
            raise RuntimeError('Rendered living-player/ammunition check failed: ' + repr((status, ammo_text)))
        return {'health': int(health[1]), 'ammo': int(match[1]), 'reserve': int(match[2]),
                'status_ocr': status, 'ammo_ocr': ammo_text}

    def ocr_words():
        remaining()
        ui.capture(out / 'ocr-current.png')
        # Analysis only: scale text coordinates into the shared1280x720 layout.
        # The saved native screenshot itself is never resized or thresholded.
        with Image.open(out / 'ocr-current.png') as native:
            image = native.convert('L').point(lambda value: 0 if value > 145 else 255)
            image = image.resize((REFERENCE[0] * 2, REFERENCE[1] * 2))
        raw = ocr(image, 11, 'current-native-ui')
        rows = [row for row in csv.DictReader(io.StringIO(raw), delimiter='\t') if row.get('text', '').strip()]
        for row in rows:
            for name in ('left', 'top', 'width', 'height'):
                row[name] = int(row[name]) // 2
        return rows

    def click_text(word):
        row = next((row for row in ocr_words() if row['text'].upper() == word), None)
        if row is None:
            raise RuntimeError('Native UI text not found: ' + word)
        ui.click(row['left'] + row['width'] // 2, row['top'] + row['height'] // 2)
        trace('click_text', text=word)
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
        wait_for(ui.menu_visible, 60, 'Native menu', client)
        capture('01-menu')
        # Loading can leave old menu pixels on screen after capture starts.
        # Wait for departure without sending that absolute click into gameplay.
        trace('deploy_click_before', x=248, y=319)
        ui.click(248, 319)
        trace('deploy_click_after', x=248, y=319)
        def offline_observation():
            try:
                state = json.loads((initial_trace / 'status.json').read_text(encoding='utf-8'))
            except (OSError, ValueError):
                return {}
            if state.get('scope') != 'debug_offline_read_only_observation':
                raise RuntimeError('Unexpected offline observation scope')
            result['last_offline_observation'] = state
            return state

        def observed(predicate, seconds, label, after=-1):
            latest = {}
            def ready():
                nonlocal latest
                latest = offline_observation()
                return latest.get('wall_msec', -1) > after and predicate(latest)
            wait_for(ready, seconds, label, client)
            trace('offline_observation', label=label, state=latest)
            return latest

        observed(lambda state: state.get('ui', {}).get('screen') == 'game' and bool(state.get('local_actor')),
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
        for _ in range(2):
            button(True)
            pause(1.0)
            button(False)
            pause(.35)
        capture('05-after-fire')
        fired_hud = read_hud('05-after-fire')
        if not 0 < fired_hud['ammo'] < 15 or fired_hud['reserve'] != 60:
            raise RuntimeError('Native fire did not deplete the initial sidearm magazine')
        key('r', True)
        pause(1.0)
        key('r', False)
        pause(2.5)
        capture('06-after-reload')
        reloaded_hud = read_hud('06-after-reload')
        if reloaded_hud['ammo'] != 15 or reloaded_hud['reserve'] >= fired_hud['reserve'] or sum(reloaded_hud[k] for k in ('ammo', 'reserve')) != sum(fired_hud[k] for k in ('ammo', 'reserve')):
            raise RuntimeError('Native offline reload did not conserve rendered ammunition')
        key('Tab', True)
        pause(.8)
        capture('06b-scoreboard')
        key('Tab', False)
        wait_for(lambda: client_has('MATCH: Round 2'), 160, 'Natural exported round completion', client)
        capture('06c-next-round')
        tap('b')
        capture('06d-funded-requisition')
        click_text('VECTORLINE')
        capture('06e-purchased-smg')
        purchased_hud = read_hud('06e-purchased-smg')
        if purchased_hud['ammo'] != 30 or purchased_hud['reserve'] != 120:
            raise RuntimeError('Authoritative requisition did not equip the purchased SMG')
        wait_for(lambda: (out / 'client.log').read_text(encoding='utf-8', errors='replace').count('MATCH: Round live.') >= 2,
                 35, 'Second active round for weapon switching', client)
        tap('2')
        capture('06f-switched-sidearm')
        switched_hud = read_hud('06f-switched-sidearm')
        if switched_hud['ammo'] != 15:
            raise RuntimeError('Native sidearm switch did not reach the HUD')
        tap('1')
        capture('06g-switched-primary')
        primary_hud = read_hud('06g-switched-primary')
        if primary_hud['ammo'] != 30 or primary_hud['reserve'] != 120:
            raise RuntimeError('Native primary switch did not restore the purchased weapon')
        tap('Escape')
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
        tap('Escape')
        capture('07d-explicit-resume')
        resumed_hud = read_hud('07d-explicit-resume')
        focus_start = observed(lambda state: state.get('ui', {}).get('focused') is True
                               and state.get('ui', {}).get('paused') is False
                               and state.get('phase') == 'live' and state.get('local_actor', {}).get('alive') is True,
                               15, 'Living active player before native focus loss')
        try:
            key('w', True)
            button(True)
            trace('native_focus_loss_before', method='XSetInputFocus(root)' if args.target == 'linux' else 'ShowWindow(SW_MINIMIZE)')
            if args.target == 'linux':
                ui.x.XSetInputFocus(ui.d, ui.x.XDefaultRootWindow(ui.d), 1, 0)
                ui.x.XFlush(ui.d)
            else:
                ui.user.ShowWindow(ui.window, 6)  # SW_MINIMIZE
            trace('native_focus_loss_after')
            lost = observed(lambda state: state.get('ui', {}).get('focused') is False
                            and state.get('ui', {}).get('paused') is True,
                            10, 'Native focus loss pauses actual offline match', focus_start['wall_msec'])
            trace('native_focus_restore_before')
            if args.target == 'windows':
                ui.user.ShowWindow(ui.window, 9)  # SW_RESTORE; focus_game retains the same HWND
            wait_for(ui.focus_game, 10, 'Restore actual native input focus', client)
            trace('native_focus_restore_after')
            restored = observed(lambda state: state.get('ui', {}).get('focused') is True,
                                10, 'Actual game observes restored focus', lost['wall_msec'])
            if restored['ui'].get('paused') is not True or restored['ui'].get('mouse_mode') != 0:
                raise RuntimeError('Native focus restoration resumed gameplay or hid the pointer without explicit resume')
            capture('07e-restored-focus-still-paused')
            tap('Escape')
            guarded = observed(lambda state: state.get('ui', {}).get('paused') is False,
                               10, 'Explicit resume with W and LMB still physically held', restored['wall_msec'])
            baseline_actor = restored['local_actor']
            guard_samples = []
            def check_guard(state, stable_position=None):
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
                guarded = observed(lambda state: True, 10, 'Neutral held input while ordinary inertia settles',
                                   guarded['wall_msec'])
                check_guard(guarded)
                if guarded['elapsed'] - settle_start > 1.0:
                    raise RuntimeError('Neutral movement inertia failed to settle within one simulation second')
            stable_position = guarded['local_actor']['position'][:]
            for index in range(2):
                guarded = observed(lambda state: True, 10, 'Fresh held-input guard sample ' + str(index + 1),
                                   guarded['wall_msec'])
                check_guard(guarded, stable_position)
            capture('07f-resumed-held-input-neutral')
        finally:
            key('w', False)
            button(False)
        released = observed(lambda state: state.get('local_input', {}).get('move') == [0, 0]
                            and state.get('local_input', {}).get('fire') is False,
                            10, 'Released held focus-test controls', guarded['wall_msec'])
        try:
            key('w', True)
            moved = observed(lambda state: state.get('local_actor', {}).get('alive') is True
                             and state.get('local_input', {}).get('move', [0, 0]) != [0, 0]
                             and state.get('local_actor', {}).get('position') != released['local_actor']['position'],
                             10, 'Fresh W press moves actual player after focus recovery', released['wall_msec'])
        finally:
            key('w', False)
        capture('07g-fresh-press-movement')
        result['native_focus_recovery'] = {'lost': lost, 'restored_paused': restored,
                                           'held_neutral_samples': guard_samples, 'released': released,
                                           'fresh_press_movement': moved}
        tap('Escape')
        click_text('LEAVE')
        wait_for(ui.menu_visible, 30, 'Return from offline match', client)
        capture('08-return-menu')
        ui.request_close()
        client.wait(timeout=min(20, remaining()))
        initial_exit = client.returncode
        if initial_exit != 0:
            raise RuntimeError('Initial native client did not exit cleanly')
        loaded_trace = out / 'restart-profile-trace'
        reopened = launch('reopened', [str(executable), '--audio-driver', 'Dummy', *flags, '--',
                                     '--offline-validation', '--offline-trace-dir=' + str(loaded_trace)], env)
        client = reopened
        if args.target == 'windows':
            ui.pid = reopened.pid
        wait_for(ui.focus_game, 30, 'Reopened native window', reopened)
        wait_for(ui.menu_visible, 45, 'Reopened native menu', reopened)
        capture('09-reopened-menu')
        if json.loads(saved_path.read_text(encoding='utf-8')) != saved:
            raise RuntimeError('Local settings/training data changed across restart')
        # Disk equality alone cannot prove load_profile worked. Enter a fresh
        # ordinary match and observe the profile actually loaded by this process.
        trace('reopened_deploy_click_before', x=248, y=319)
        ui.click(248, 319)
        trace('reopened_deploy_click_after', x=248, y=319)
        wait_for(lambda: (loaded_trace / 'events.jsonl').is_file(), 30,
                 'Reopened process loaded profile into ordinary offline match', reopened)
        with (loaded_trace / 'events.jsonl').open(encoding='utf-8') as stream:
            loaded = json.loads(stream.readline())
        if loaded.get('initial_conditions') != 'stock_spawns_teams_random_seeds' or loaded.get('initial_profile') != saved:
            raise RuntimeError('Reopened process did not load saved settings/training')
        capture('10-reopened-loaded-settings')
        ui.request_close()
        reopened.wait(timeout=min(20, remaining()))
        reopened_exit = reopened.returncode
        if reopened_exit or failed((out / 'reopened.log').read_text(encoding='utf-8', errors='replace')):
            raise RuntimeError('Reopened export failed clean shutdown')
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
