#!/usr/bin/env python3
"""Actual ARM Mac stock Deploy / living sidearm / FIELD MENU / leave component.

No gameplay mutation, fixture seed, source project or replacement HOME is used.
Source controls are readiness only; raw native output requires independent review.
"""
import argparse
import copy
import json
import os
from pathlib import Path
import signal
import subprocess
import time
import uuid

from build_manifest import BUILDS, OUTPUTS, clean, source, validate_record
from macos_native_input import same_bounds
from macos_deploy_ocr import PROFILE as DEPLOY_ANALYSIS_PROFILE, bind_analysis, png_dimensions
from macos_ordinary_input import (MacOrdinaryUI, OwnedWindowChanged, account_home, capture_geometry, default_inventory, hud_values, inventory,
    living_context, no_symlinks, owned_visible_windows, require_field_menu, require_initial, require_private_userdir,
    stage_app, verify_staged_app)
from native_log import failed
from native_observation import read_observation_json
from probe_macos_input import MacReadOnly, NativePrerequisiteBlocked, digest, reap, require_absent_profile
from verify_macos_menu import (CAPTURE_SOURCE, ordinary_failure_close,
                               require_preflight, require_screen)
import toolchain


BUDGETS = {'total': 300, 'compile': 60, 'window': 30, 'focus': 5, 'menu': 60,
           'deploy': 30, 'live': 60, 'fire': 5, 'reload_start': 5,
           'reload_complete': 15, 'reload_frames': 5, 'field_menu': 10,
           'return_menu': 30, 'close': 20, 'capture': 25}
ENVIRONMENT_KEYS = ('HOME', 'PATH', 'DISPLAY', 'DEVELOPER_DIR', 'SDKROOT', 'MACOSX_DEPLOYMENT_TARGET',
                    'DYLD_LIBRARY_PATH', 'DYLD_FRAMEWORK_PATH', 'DYLD_INSERT_LIBRARIES',
                    'GODOT_RENDERING_DRIVER', 'GODOT_RENDERING_METHOD', 'GODOT_EDITOR_SETTINGS_PATH',
                    'GODOT_PROJECT_DATA_DIR', 'VK_ICD_FILENAMES', 'LIBGL_ALWAYS_SOFTWARE',
                    'MESA_LOADER_DRIVER_OVERRIDE', 'LP_NUM_THREADS', 'XDG_DATA_HOME', 'XDG_CONFIG_HOME',
                    'XDG_CACHE_HOME', 'APPDATA', 'LOCALAPPDATA', 'SIGHTBREAK_TOOLS_DIR',
                    'SIGHTBREAK_STATE_DIR', 'SIGHTBREAK_BUILDS_DIR')


class StartupMenuNotReady(RuntimeError):
    pass


def discover_startup_menu(api, client, select_candidate, capture, remaining, trace, until):
    """Read-only discovery under one deadline; no candidate authorizes input."""
    attempt = 0
    while True:
        remaining(until)
        if client.poll() is not None:
            raise RuntimeError('Exact native client exited before startup menu readiness')
        rows = api.windows(client.pid)
        trace('startup_window_observation', observed_owned_layer_zero_windows=rows)
        owned = owned_visible_windows(rows, client.pid)
        if len(owned) == 1:
            ui = select_candidate(owned[0])
            if ui.event_post_attempts:
                raise RuntimeError('Startup discovery cannot select after any CGEvent attempt')
            attempt += 1
            try:
                menu = capture('00-startup-menu-'+str(attempt), 'menu', require_focus=False, until=until)
                remaining(until)
                return ui, menu
            except NativePrerequisiteBlocked:
                raise
            except (StartupMenuNotReady, OwnedWindowChanged) as error:
                trace('startup_candidate_rejected', attempt=attempt, failure=str(error))
        time.sleep(min(.05, remaining(until)))


def run(output, preflight_path, *, deploy_target='ocr'):
    if deploy_target not in ('ocr', 'owned-ax'):
        raise ValueError('Unknown explicit Mac Deploy target mode')
    output = Path(output).absolute()
    no_symlinks(output)
    if output.exists() and any(output.iterdir()):
        raise RuntimeError('Preserve native attempts; choose a fresh evidence directory')
    if output.is_relative_to(toolchain.ROOT / 'game') or output.is_relative_to(BUILDS / 'macos'):
        raise RuntimeError('Evidence must be outside source and original native payload')
    output.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    deadline = started + BUDGETS['total']
    before = manifest = client = ui = staged = private_directory = default_before = None
    processes, actions = [], []
    result = {'scope': 'ARM Mac stock Deploy/living sidearm fire+reload/FIELD MENU/leave/ordinary close only; '
                       'no objectives, full match, restart, Intel or physical-device acceptance',
              'passed': False, 'permission_requests_made': 0, 'controller_pid': os.getpid(),
              'budgets_seconds': BUDGETS, 'actions': actions, 'captures': [], 'capture_attempts': [],
              'deploy_target_mode': deploy_target}

    def remaining(until=None):
        value = min(deadline, until if until is not None else deadline) - time.monotonic()
        if value <= 0:
            raise TimeoutError('Native Mac component stage or whole-flow deadline exceeded')
        return value

    def trace(event, **details):
        actions.append({'event': event, 'seconds': time.monotonic()-started, **copy.deepcopy(details)})
        (output / 'actions.json').write_text(json.dumps(actions, indent=2)+'\n')

    def pause(seconds):
        if seconds > remaining():
            raise TimeoutError('Input schedule would exceed native Mac whole-flow deadline')
        time.sleep(seconds)
        remaining()

    def command(name, arguments, budget, *, allow_failure=False, return_process=False):
        until = min(deadline, time.monotonic()+budget)
        trace('helper_command', name=name, command=arguments, budget_seconds=budget)
        with (output / (name+'.log')).open('w', encoding='utf-8') as log:
            process = subprocess.Popen(arguments, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            processes.append((name, process))
            process.wait(timeout=remaining(until))
        remaining(until)
        if failed((output / (name+'.log')).read_text(errors='replace')):
            raise RuntimeError('Strict native error/leak signature in '+name)
        if process.returncode and not allow_failure:
            raise RuntimeError(name+' failed; original log retained')
        return process if return_process else process.returncode

    def capture(name, screen=None, *, require_focus=True, until=None):
        remaining(until)
        png, receipt = output / (name+'.png'), output / (name+'.json')
        analysis_png = output / (name+'-deploy-2x.png')
        analyze_deploy = name == '01-focused-menu' and deploy_target == 'ocr'
        attempt = {'name': name, 'screen': screen, 'foreground_required': require_focus,
                   'started_seconds': time.monotonic()-started, 'accepted': False}
        result['capture_attempts'].append(attempt)
        try:
            (ui.require_target if require_focus else ui.require_window)()
            arguments = [str(helper), '--pid', str(client.pid), '--window', str(ui.window),
                         '--png', str(png), '--report', str(receipt)]
            if analyze_deploy:
                arguments += ['--analysis-mode', DEPLOY_ANALYSIS_PROFILE, '--deploy-analysis-png', str(analysis_png)]
            status = command(name, arguments,
                             min(BUDGETS['capture'], remaining(until)), allow_failure=True)
            data = json.loads(receipt.read_text())
            if data.get('permissions', {}).get('CGPreflightScreenCaptureAccess') is not True:
                raise NativePrerequisiteBlocked('Native screenshot helper lacks current capture permission')
            if (status or data.get('passed') is not True or data.get('owner_pid') != client.pid
                    or data.get('window_id') != ui.window
                    or not same_bounds(data.get('bounds_points_including_chrome', []), ui.bounds)
                    or data.get('input_events_posted') != 0 or data.get('permission_requests_made') != 0):
                raise RuntimeError('OS screenshot does not bind the exact successful owned window')
            capture_geometry(data)
            if analyze_deploy:
                bind_analysis(data, digest(png), digest(analysis_png), png_dimensions(png), png_dimensions(analysis_png))
            elif 'derived_deploy_analysis' in data:
                raise RuntimeError('Derived Deploy analysis is forbidden outside the one focused menu capture')
            if screen in ('menu', 'settings'):
                try:
                    require_screen(data, screen)
                except RuntimeError as error:
                    if screen == 'menu' and not require_focus and not getattr(ui, 'input_geometry_pinned', False):
                        raise StartupMenuNotReady(str(error)) from error
                    raise
            elif screen == 'field_menu':
                require_field_menu(data)
            elif screen is not None:
                raise ValueError('Unknown native screenshot screen')
            (ui.require_target if require_focus else ui.require_window)()
            remaining(until)
            capture_record = {'name': name, 'screen': screen, 'png_sha256': digest(png),
                              'receipt_sha256': digest(receipt), 'window_id': ui.window,
                              'foreground_required': require_focus}
            if deploy_target == 'owned-ax' and name == '01-focused-menu':
                from macos_semantic_deploy import seal_native_capture
                seals = seal_native_capture(png, receipt, data)
                capture_record.update(png_sha256=seals[0].sha256, receipt_sha256=seals[1].sha256,
                                      semantic_original_files=[seal.metadata() for seal in seals])
            result['captures'].append(capture_record)
            attempt['accepted'] = True
            trace('native_capture', capture=name, screen=screen, native_state=ui.diagnostics() if require_focus else ui.focus_state())
            return data
        except BaseException as error:
            attempt['failure'] = {'type': type(error).__name__, 'message': str(error)}
            raise
        finally:
            attempt['finished_seconds'] = time.monotonic()-started
            attempt['retained_files'] = {path.name: {'bytes': path.stat().st_size, 'sha256': digest(path)}
                                         for path in (png, receipt, analysis_png) if path.is_file()}

    def wait(predicate, budget, label):
        until = min(deadline, time.monotonic()+budget)
        trace('stage_begin', label=label, budget_seconds=budget)
        while True:
            remaining(until)
            if client is not None and client.poll() is not None:
                raise RuntimeError('Exact native client exited during '+label)
            value = predicate()
            remaining(until)
            if value:
                trace('stage_complete', label=label)
                return value
            time.sleep(min(.05, remaining(until)))

    def observation():
        try:
            state = read_observation_json(trace_directory / 'status.json')
        except (OSError, ValueError):
            return {}
        if not isinstance(state, dict) or state.get('scope') != 'debug_offline_read_only_observation':
            raise RuntimeError('Unexpected offline observation schema/scope')
        result['last_observation'] = state
        return state

    def observed(predicate, budget, label, after=-1):
        def ready():
            state = observation()
            if not state:
                return None
            wall = state.get('wall_msec')
            if not isinstance(wall, int) or isinstance(wall, bool):
                raise RuntimeError('Malformed native observation freshness')
            return state if wall > after and predicate(state) else None
        state = wait(ready, budget, label)
        trace('authoritative_observation', label=label, state=state)
        return state

    def check_context(state, *, paused=False):
        return living_context(state, initial, paused=paused)

    def screenshot_hud(name, expected):
        before_capture = observed(lambda state: bool(check_context(state)), 5, name+' before screenshot', expected['wall_msec'])
        if any(before_capture['local_actor'][key] != expected['local_actor'][key] for key in ('ammo', 'reserve', 'reload')):
            raise RuntimeError('Authoritative ammunition changed before '+name)
        pixels = capture(name)
        # The actual screenshot process includes Vision analysis. Require the
        # same live state afterwards; elapsed capture time cannot hide a death.
        after_capture = observed(lambda state: bool(check_context(state)), 5, name+' after screenshot', before_capture['wall_msec'])
        values = hud_values(pixels)
        if (any(after_capture['local_actor'][key] != expected['local_actor'][key] for key in ('ammo', 'reserve', 'reload'))
                or any(values[key] != expected['local_actor'][key] for key in ('ammo', 'reserve'))):
            raise RuntimeError('Native HUD ammunition differs from same-life authority')
        if not after_capture['local_actor']['health'] <= values['health'] <= before_capture['local_actor']['health']:
            raise RuntimeError('Native health does not fall between bracketing same-life observations')
        result.setdefault('living_hud_captures', []).append({'name': name, 'before': before_capture,
                                                          'after': after_capture, 'rendered': values})
        return after_capture

    try:
        api = MacReadOnly()  # No helper compilation or launch on other hosts.
        before = source()
        clean(before)
        manifest = validate_record('macos', before)
        preflight = json.loads(Path(preflight_path).read_text())
        require_preflight(preflight, before, manifest)
        home = account_home()
        result.update(source=before, artifact_source=manifest, preflight_sha256=digest(preflight_path),
                      engine=toolchain.verify_engine(), permissions=api.preflight(), account_home=str(home),
                      environment_scope='Inherited process environment; selected non-secret path/render/toolchain values only',
                      environment_whitelist={key: os.environ.get(key) for key in ENVIRONMENT_KEYS})
        if any(result['permissions'].get(key) is not True for key in ('CGPreflightPostEventAccess', 'CGPreflightScreenCaptureAccess')):
            raise NativePrerequisiteBlocked('Current controller native capture/input permissions absent')
        default_before = default_inventory()
        require_absent_profile()
        result['default_user_directory_before'] = default_before
        name = 'SIGHTBREAK-mac-ordinary-'+uuid.uuid4().hex
        private_directory = home / 'Library/Application Support' / name
        if inventory(private_directory)['directory_exists'] or os.path.lexists(private_directory):
            raise RuntimeError('Private user-directory entry already exists')
        result['private_user_directory'] = str(private_directory)
        original = (BUILDS / OUTPUTS['macos']).parents[2]
        staged = stage_app(original, output / 'native/SIGHTBREAK.app', name)
        result['native_artifact_attestation'] = staged
        if staged['executable_sha256'] != manifest['artifact']['sha256']:
            raise RuntimeError('Staged executable disagrees with exact export manifest')
        helper = output / 'macos-window-capture'
        command('compile-capture-helper', ['xcrun', 'swiftc', '-parse-as-library', '-swift-version', '5',
                '-target', 'arm64-apple-macos14.0', str(CAPTURE_SOURCE), '-framework', 'AppKit',
                '-framework', 'CoreGraphics', '-framework', 'ScreenCaptureKit', '-framework', 'Vision',
                '-framework', 'ImageIO', '-framework', 'UniformTypeIdentifiers', '-o', str(helper)], BUDGETS['compile'])
        result['capture_helper'] = {'source_sha256': digest(CAPTURE_SOURCE), 'executable_sha256': digest(helper)}
        executable = Path(staged['staged']) / 'Contents/MacOS/SIGHTBREAK'
        trace_directory = output / 'stock-offline-trace'
        arguments = [str(executable), '--audio-driver', 'Dummy', '--log-file', 'user://mac-ordinary-engine.log',
                     '--windowed', '--resolution', '1280x720', '--position', '40,60', '--',
                     '--offline-validation', '--offline-trace-dir='+str(trace_directory)]
        if deploy_target == 'owned-ax':
            # Explicit engine exposure only; never request or force OS trust.
            arguments[arguments.index('--'):arguments.index('--')] = ['--accessibility', 'always']
            from macos_semantic_deploy import SOURCES
            result['semantic_deploy_source_sha256'] = {path.name: digest(path) for path in SOURCES}
        result['client_command'] = arguments
        with (output / 'client.log').open('w', encoding='utf-8') as log:
            client = subprocess.Popen(arguments, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            processes.append(('client', client))
            result['client_pid'] = client.pid
            window = wait(lambda: next(iter([entry for entry in api.windows(client.pid)
                                            if entry['owner_pid'] == client.pid and entry['onscreen']]), None),
                          BUDGETS['window'], 'Exact owned visible native window')
            result['first_client_window'] = window
            result['private_user_directory_before_input'] = require_private_userdir(private_directory, default_before)
            menu_deadline = min(deadline, time.monotonic()+BUDGETS['menu'])
            def select_candidate(candidate):
                nonlocal ui
                if ui is not None:
                    if ui.event_post_attempts or getattr(ui, 'input_geometry_pinned', False):
                        raise RuntimeError('Startup geometry cannot be replaced after pinning or any event attempt')
                    ui.close()
                ui = MacOrdinaryUI(client.pid, candidate['window_id'], candidate['bounds_points_including_chrome'], trace)
                ui.private_directory, ui.default_before = private_directory, default_before
                trace('startup_window_candidate', window=candidate, cg_event_post_attempts=ui.event_post_attempts)
                return ui
            ui, _background_menu = discover_startup_menu(api, client, select_candidate, capture, remaining, trace, menu_deadline)
            focus_deadline = min(menu_deadline, time.monotonic()+BUDGETS['focus'])
            ui.focus(seconds=remaining(focus_deadline))
            remaining(focus_deadline)
            ui.neutral()
            menu = capture('01-focused-menu', 'menu', until=menu_deadline)
            ui.pin_for_input(menu)
            remaining(menu_deadline)
            result['selected_client_window'] = {'owner_pid': ui.pid, 'window_id': ui.window,
                                                'bounds_points_including_chrome': list(ui.bounds)}
            if deploy_target == 'owned-ax':
                from macos_semantic_deploy import acquire_target
                ui.semantic_deploy_target = acquire_target(ui, menu, output, command, remaining, menu_deadline, result)
            ui.click_label(menu, 'DEPLOY · OFFLINE 5V5')
            ready = observed(lambda state: state.get('ui', {}).get('screen') == 'game' and bool(state.get('local_actor')),
                             BUDGETS['deploy'], 'Stock match after one native Deploy click')
            with (trace_directory / 'events.jsonl').open(encoding='utf-8') as events:
                initial = json.loads(events.readline())
            require_initial(initial)
            result['initial_event'] = initial
            origin = observed(lambda state: state.get('phase') == 'live', BUDGETS['live'], 'Ordinary first live phase', ready['wall_msec'])
            actor = check_context(origin)
            if actor['ammo'] != 15 or actor['reserve'] != 60 or actor['reload'] != 0:
                raise RuntimeError('Native fire requires the initial full sidearm')
            for _ in range(2):
                hold_deadline = min(deadline, time.monotonic()+1)
                trace('fire_hold_slot', hold_budget_seconds=1)
                ui.fire_button(True)
                try:
                    ui.observed_state('lmb', True, seconds=min(2, remaining(hold_deadline)))
                    # OS acknowledgement consumes the existing one-second hold;
                    # a delayed receipt cannot add another second of firing.
                    pause(remaining(hold_deadline))
                finally:
                    release_deadline = min(deadline, time.monotonic()+.35)
                    ui.fire_button(False)
                ui.observed_state('lmb', False, seconds=min(2, remaining(release_deadline)))
                pause(remaining(release_deadline))
            fire_frame = [None]
            def fired(state):
                actor = check_context(state)
                if actor['reserve'] != 60 or actor['reload'] != 0:
                    raise RuntimeError('Fire altered reserve/reload context')
                if not 0 < actor['ammo'] < 15:
                    return False
                if fire_frame[0] is None or fire_frame[0][0] != actor['ammo']:
                    fire_frame[0] = (actor['ammo'], state['drawn_frames'])
                return state['drawn_frames'] >= fire_frame[0][1]+2
            depleted = observed(fired, BUDGETS['fire'], 'Depleted live sidearm plus two drawn frames', origin['wall_msec'])
            result['native_fire'] = {'origin': origin, 'depleted': depleted}
            depleted = screenshot_hud('05-after-fire', depleted)
            def reload_started(state):
                actor = check_context(state)
                if any(actor[key] != depleted['local_actor'][key] for key in ('ammo', 'reserve')):
                    raise RuntimeError('Ammunition transferred before observed reload countdown')
                return actor['reload'] > 0
            reload_deadline = min(deadline, time.monotonic()+BUDGETS['reload_start'])
            ui.reload_key(True)
            try:
                ui.observed_state('reload', True, seconds=min(2, remaining(reload_deadline)))
                beginning = observed(reload_started, remaining(reload_deadline), 'Real native R begins reload', depleted['wall_msec'])
                completion_deadline = min(deadline, time.monotonic()+BUDGETS['reload_complete'])
            finally:
                ui.reload_key(False)
            ui.observed_state('reload', False, seconds=min(2, remaining(completion_deadline)))
            def reload_completed(state):
                actor = check_context(state)
                if actor['reload'] > 0:
                    return False
                if (actor['ammo'] != 15 or actor['reserve'] != 60-(15-depleted['local_actor']['ammo'])
                        or state['elapsed']-beginning['elapsed'] < beginning['local_actor']['reload']-1/60):
                    raise RuntimeError('Reload did not conserve ammunition over its observed simulation countdown')
                return True
            completed = observed(reload_completed, remaining(completion_deadline), 'Native reload completion', beginning['wall_msec'])
            rendered = observed(lambda state: reload_completed(state) and state['drawn_frames'] >= completed['drawn_frames']+2,
                                BUDGETS['reload_frames'], 'Two drawn frames after native reload', completed['wall_msec'])
            result['native_reload'] = {'before': depleted, 'started': beginning, 'completed': completed, 'rendered': rendered}
            settled = screenshot_hud('06-after-reload', rendered)
            field_deadline = min(deadline, time.monotonic()+BUDGETS['field_menu'])
            ui.tap_escape()
            paused = observed(lambda state: state.get('ui', {}).get('paused') is True,
                              remaining(field_deadline), 'Native Escape opens FIELD MENU', settled['wall_msec'])
            check_context(paused, paused=True)
            field = capture('07-field-menu', 'field_menu')
            after_field = observed(lambda state: state.get('ui', {}).get('paused') is True, 5,
                                   'Living paused state after FIELD MENU screenshot', paused['wall_msec'])
            check_context(after_field, paused=True)
            if (after_field['elapsed'] != paused['elapsed'] or after_field['simulation_tick'] != paused['simulation_tick']
                    or after_field['local_actor'] != paused['local_actor']):
                raise RuntimeError('Native FIELD MENU failed to freeze the living offline state')
            result['native_field_menu'] = {'before': settled, 'paused': paused, 'after_capture': after_field}
            ui.click_label(field, 'LEAVE MATCH')
            menu_until = min(deadline, time.monotonic()+BUDGETS['return_menu'])
            capture('08-returned-menu', 'menu', until=menu_until)
            release = ui.release_owned()
            result['input_release'] = release
            if release['held_after_release'] or release['errors'] or any(release['native_state'][key] for key in ('lmb_down', 'escape_down', 'reload_down')):
                raise RuntimeError('Native controls failed final neutral release')
            close_deadline = min(deadline, time.monotonic()+BUDGETS['close'])
            result['ordinary_termination_requested'] = ui.request_close()
            if not result['ordinary_termination_requested']:
                raise RuntimeError('Public AppKit ordinary close refused')
            client.wait(timeout=remaining(close_deadline))
            remaining(close_deadline)
            result['normal_exit_code'] = client.returncode
            if client.returncode:
                raise RuntimeError('Ordinary native close returned nonzero')
        result['passed'] = True
    except NativePrerequisiteBlocked as error:
        result['blocker'] = str(error)
    except BaseException as error:
        result['failure'] = {'type': type(error).__name__, 'message': str(error)}
    finally:
        finalization = []
        if ui is not None:
            try:
                result['final_input_release'] = ui.release_owned()
                result['cg_event_post_attempts'] = ui.event_post_attempts
                release = result['final_input_release']
                if (release['held_after_release'] or release['errors']
                        or any(release['native_state'][key] for key in ('lmb_down', 'escape_down', 'reload_down'))):
                    raise RuntimeError('Native controls remain held at finalization')
                result['failure_ordinary_close'] = ordinary_failure_close(ui, client)
            except BaseException as error:
                finalization.append('input/ordinary_close: '+str(error))
        result['cleanup'] = []
        for name, process in processes:
            try:
                receipt = reap(process)
                result['cleanup'].append({'name': name, **receipt})
                if not receipt['owned_group_gone'] or (result['passed'] and receipt['signals_sent']):
                    raise RuntimeError('Owned native group survived ordinary exit or required fallback signals')
            except BaseException as error:
                finalization.append(name+'_cleanup: '+str(error))
        if ui is not None:
            try:
                ui.close()
            except BaseException as error:
                finalization.append('AppKit pool: '+str(error))
        if staged is not None:
            try:
                verify_staged_app(staged)
                result['payload_unchanged'] = True
            except BaseException as error:
                finalization.append('native_payload: '+str(error))
        if default_before is not None:
            try:
                result['default_user_directory_after'] = default_inventory()
                result['default_user_directory_unchanged'] = result['default_user_directory_after'] == default_before
                if not result['default_user_directory_unchanged']:
                    raise RuntimeError('Default native directory changed; all native files preserved')
            except BaseException as error:
                finalization.append('default_userdata: '+str(error))
        if private_directory is not None:
            try:
                result['private_user_directory_after'] = inventory(private_directory)
                logfile = private_directory / 'mac-ordinary-engine.log'
                if logfile.is_file():
                    (output / 'engine.log').write_bytes(logfile.read_bytes())
                if result['passed']:
                    require_private_userdir(private_directory, default_before)
            except BaseException as error:
                finalization.append('private_userdata: '+str(error))
        for path in sorted(output.glob('*.log')):
            try:
                if failed(path.read_text(errors='replace')):
                    raise RuntimeError('Strict native error/leak signature in '+path.name)
            except BaseException as error:
                finalization.append('native_logs: '+str(error))
        if before is not None:
            try:
                result['source_unchanged'] = source() == before
                validate_record('macos', before)
                if not result['source_unchanged']:
                    raise RuntimeError('Source/export changed during native component')
            except BaseException as error:
                finalization.append('source_export: '+str(error))
        if time.monotonic()-started > BUDGETS['total']:
            finalization.append('whole_flow: original 300-second deadline exceeded')
        if finalization:
            result['finalization_failures'] = finalization
            result['passed'] = False
        result['seconds'] = time.monotonic()-started
        result['status'] = ('PASS_ORDINARY_MAC_COMPONENT_ONLY' if result['passed'] else
                            'BLOCKED_EXTERNALLY' if 'blocker' in result and not finalization else 'FAILED')
        (output / 'results.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))
    return 0 if result['passed'] else 2 if result['status'] == 'BLOCKED_EXTERNALLY' else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--preflight', type=Path, required=True)
    parser.add_argument('--deploy-target', choices=('ocr', 'owned-ax'), default='ocr')
    arguments = parser.parse_args()
    def interrupted(signum, _frame):
        raise SystemExit('Native Mac ordinary component interrupted by signal '+str(signum))
    for signum in (signal.SIGTERM, signal.SIGINT):
        signal.signal(signum, interrupted)
    return run(arguments.output, arguments.preflight, deploy_target=arguments.deploy_target)


if __name__ == '__main__':
    raise SystemExit(main())
