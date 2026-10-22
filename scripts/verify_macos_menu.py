#!/usr/bin/env python3
"""Qualify only ordinary Mac menu Settings pointer input and Escape return.

Requires a same-source successful native preflight, current permissions, actual
owned OS screenshots and observed OS control state. Source controls are readiness
only; the actual run's raw images/results need a fresh independent critic.
"""
import argparse
import json
from pathlib import Path
import signal
import subprocess
import time

from build_manifest import BUILDS, OUTPUTS, clean, same_source, source, validate_record
from macos_native_input import MacMenuUI, same_bounds
from native_log import failed
from probe_macos_input import (MacReadOnly, NativePrerequisiteBlocked, digest, profile_entries,
                               require_absent_profile, user_directory_inventory, reap)
import toolchain


CAPTURE_SOURCE = Path(__file__).with_name('macos_window_capture.swift')


def require_preflight(receipt, current, manifest):
    if (receipt.get('status') != 'READY_FOR_INPUT_ATTEMPT'
            or not same_source(receipt.get('source', {}), current)
            or not same_source(receipt.get('artifact_source', {}), manifest)
            or receipt.get('executable_sha256') != manifest['artifact']['sha256']
            or receipt.get('source_unchanged') is not True
            or receipt.get('normal_exit_code') != 0
            or receipt.get('cleanup', {}).get('owned_group_gone') is not True
            or receipt.get('profile_entries_unchanged') is not True
            or any(receipt.get('permissions', {}).get(name) is not True for name in
                   ('CGPreflightPostEventAccess', 'CGPreflightScreenCaptureAccess'))
            or not any(window.get('onscreen') is True for observation in receipt.get('window_observations', [])
                       for window in observation.get('windows', []))):
        raise NativePrerequisiteBlocked('Accepted same-source native permission/window preflight required before menu input')


def screen_text(capture, phrase, *, exact=False):
    wanted = ' '.join(phrase.upper().split())
    return [entry for entry in capture.get('text', []) if entry.get('confidence', 0) >= .8
            and ((' '.join(entry.get('text', '').upper().split()) == wanted) if exact
                 else wanted in ' '.join(entry.get('text', '').upper().split()))]


def require_screen(capture, name):
    if capture.get('passed') is not True:
        raise RuntimeError('OS screenshot helper failed: ' + json.dumps(capture.get('failure')))
    menu = bool(screen_text(capture, 'TACTICAL OPERATIONS')) and len(screen_text(capture, 'SETTINGS', exact=True)) == 1
    settings = bool(screen_text(capture, 'FIELD SETTINGS'))
    if (name == 'menu' and (not menu or settings)) or (name == 'settings' and (not settings or menu)):
        raise RuntimeError('Original OS screenshot did not confirm ' + name + ' screen')


def ordinary_failure_close(ui, client):
    """Try the public quit request before owned-group fallback on failure."""
    if ui is None or client is None or client.poll() is not None:
        return {'needed': False}
    report = {'needed': True, 'request_accepted': ui.request_close()}
    if report['request_accepted']:
        try:
            client.wait(timeout=3)
            report['exit_code'] = client.returncode
        except subprocess.TimeoutExpired:
            report['timed_out'] = True
    return report


def background_then_focus(ui, capture, result, trace):
    """Keep read-only capture and focus evidence separate; require both for input."""
    trace('observer_before_background_capture', native_state=ui.focus_state())
    background_error = None
    try:
        capture('00-background-window', None, require_focus=False)
        result['background_capture_status'] = 'PASS_CAPTURE_ONLY_NO_FOCUS_OR_INPUT'
    except (RuntimeError, OSError, ValueError, subprocess.TimeoutExpired) as error:
        background_error = error
        result['background_capture_status'] = 'BLOCKED_EXTERNALLY' if isinstance(error, NativePrerequisiteBlocked) else 'FAILED'
        result['background_capture_failure'] = {'type': type(error).__name__, 'message': str(error)}
        trace('background_capture_failed', **result['background_capture_failure'])
    ui.focus()
    if background_error is not None:
        raise background_error  # Focus diagnostics never authorize input after capture failure.


def capture_observation(ui, require_focus):
    # Preserve raw pre-activation state until the explicitly recorded focus-loop
    # experiment. Background receipt logging must not silently refresh it.
    return ui.diagnostics() if require_focus else ui.focus_state()


def run(output, preflight_path, timeout=150):
    output = Path(output).resolve()
    if output.exists() and any(output.iterdir()):
        raise RuntimeError('Preserve prior menu input evidence; choose fresh output')
    if output.is_relative_to(toolchain.ROOT / 'game') or output.is_relative_to(BUILDS / 'macos'):
        raise RuntimeError('Keep evidence outside source and native export')
    output.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    deadline = started + timeout
    before = manifest = client = ui = None
    profile_before = native_before = None
    helper_processes, actions = [], []
    result = {'scope': 'Actual ARM Mac ordinary menu pointer/Escape navigation only; no gameplay/device acceptance',
              'passed': False, 'permission_requests_made': 0, 'captures': [], 'actions': actions}

    def remaining():
        value = deadline - time.monotonic()
        if value <= 0:
            raise TimeoutError('Whole native Mac menu journey deadline exceeded')
        return value

    def trace(event, **details):
        actions.append({'event': event, 'seconds': time.monotonic() - started, **details})
        (output / 'actions.json').write_text(json.dumps(actions, indent=2) + '\n')

    def child_command(name, command, budget, *, allow_failure=False):
        remaining()
        trace('helper_command', name=name, command=command)
        with (output / (name + '.log')).open('w', encoding='utf-8') as log:
            process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            helper_processes.append((name, process))
            try:
                process.wait(timeout=min(budget, remaining()))
            except subprocess.TimeoutExpired:
                trace('helper_timeout', name=name, cleanup=reap(process))
                raise
        if process.returncode and not allow_failure:
            raise RuntimeError(name + ' failed exit=' + str(process.returncode) + '; original helper log/report retained')
        return process.returncode

    def capture(name, screen, *, require_focus=True):
        remaining()
        (ui.require_target if require_focus else ui.require_window)()
        png, receipt = output / (name + '.png'), output / (name + '.json')
        exit_code = child_command(name, [str(helper), '--pid', str(client.pid), '--window', str(ui.window),
                                        '--png', str(png), '--report', str(receipt)], 25, allow_failure=True)
        data = json.loads(receipt.read_text())
        denied = [name for name in ('CGPreflightScreenCaptureAccess',)
                  if data.get('permissions', {}).get(name) is not True]
        if denied:
            raise NativePrerequisiteBlocked('Capture helper permission denied: ' + ', '.join(denied) + '; ' + json.dumps(data.get('failure')))
        if exit_code:
            raise RuntimeError('ScreenCaptureKit/Vision helper failed: ' + json.dumps(data.get('failure')))
        if (data.get('owner_pid') != client.pid or data.get('window_id') != ui.window
                or not same_bounds(data.get('bounds_points_including_chrome', []), ui.bounds)
                or data.get('input_events_posted') != 0 or data.get('permission_requests_made') != 0):
            raise RuntimeError('OS capture receipt did not match exact current owned window')
        if screen is not None:
            require_screen(data, screen)
        (ui.require_target if require_focus else ui.require_window)()
        result['captures'].append({'name': name, 'png_sha256': digest(png),
                                   'receipt_sha256': digest(receipt), 'window_id': ui.window,
                                   'foreground_required': require_focus, 'screen_checked': screen})
        trace('screen_confirmed' if screen is not None else 'background_capture_observed',
              screen=screen, capture=name, foreground_required=require_focus,
              native_state=capture_observation(ui, require_focus))
        return data

    try:
        api = MacReadOnly()  # Reject non-native hosts before compilation or launch.
        before = source()
        clean(before)
        manifest = validate_record('macos', before)
        receipt = json.loads(Path(preflight_path).read_text())
        require_preflight(receipt, before, manifest)
        result.update(source=before, artifact_source=manifest, preflight_sha256=digest(preflight_path),
                      engine=toolchain.verify_engine(), controller_permissions=api.preflight())
        denied = [name for name in ('CGPreflightPostEventAccess', 'CGPreflightScreenCaptureAccess')
                  if result['controller_permissions'][name] is not True]
        if denied:
            raise NativePrerequisiteBlocked('Current controller permission denied: ' + ', '.join(denied))
        profile_before = require_absent_profile()
        native_before = user_directory_inventory()
        result['native_user_directory_before'] = native_before
        helper = output / 'macos-window-capture'
        child_command('compile-capture-helper', ['xcrun', 'swiftc', '-parse-as-library', '-swift-version', '5',
                      '-target', 'arm64-apple-macos14.0', str(CAPTURE_SOURCE), '-framework', 'AppKit',
                      '-framework', 'CoreGraphics', '-framework', 'ScreenCaptureKit', '-framework', 'Vision',
                      '-framework', 'ImageIO', '-framework', 'UniformTypeIdentifiers', '-o', str(helper)], 60)
        result['capture_helper'] = {'source_sha256': digest(CAPTURE_SOURCE), 'executable_sha256': digest(helper)}
        executable = BUILDS / OUTPUTS['macos']
        result['executable_sha256'] = digest(executable)
        require_absent_profile()
        command = [str(executable), '--audio-driver', 'Dummy', '--log-file', str(output / 'engine.log'),
                   '--windowed', '--resolution', '960x540', '--position', '40,60']
        result['client_command'] = command
        with (output / 'client.log').open('w', encoding='utf-8') as log:
            client = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            result['client_pid'] = client.pid
            window = None
            until = min(deadline, time.monotonic() + 30)
            while time.monotonic() < until:
                if client.poll() is not None:
                    raise RuntimeError('Exported client exited before native menu window')
                windows = [entry for entry in api.windows(client.pid) if entry['onscreen']]
                if windows:
                    window = max(windows, key=lambda entry: entry['bounds_points_including_chrome'][2] * entry['bounds_points_including_chrome'][3])
                    break
                time.sleep(.1)
            if window is None:
                raise TimeoutError('Exact exported visible window not observed')
            result['selected_client_window'] = window
            trace('client_window_selected', client_pid=client.pid, window=window)
            ui = MacMenuUI(client.pid, window['window_id'], window['bounds_points_including_chrome'], trace)
            background_then_focus(ui, capture, result, trace)
            ui.neutral()
            # Initial capture may start while the first native frame is being
            # drawn. Keep every failed image/receipt, with one bounded retry.
            menu = None
            for attempt in range(2):
                try:
                    menu = capture('01-menu-' + str(attempt), 'menu')
                    break
                except NativePrerequisiteBlocked:
                    raise
                except RuntimeError:
                    if attempt:
                        raise
                    time.sleep(min(1, remaining()))
            ui.click_settings(menu)
            time.sleep(min(.4, remaining()))
            capture('02-field-settings', 'settings')
            ui.tap_escape()
            time.sleep(min(.4, remaining()))
            capture('03-returned-menu', 'menu')
            release = ui.release_owned()
            result['input_release'] = release
            if release['held_after_release'] or release['errors'] or release['native_state']['lmb_down'] or release['native_state']['escape_down']:
                raise RuntimeError('Native held controls did not return to neutral')
            result['ordinary_termination_requested'] = ui.request_close()
            if not result['ordinary_termination_requested']:
                raise RuntimeError('Public AppKit ordinary termination request refused')
            client.wait(timeout=min(10, remaining()))
            result['normal_exit_code'] = client.returncode
        if client.returncode:
            raise RuntimeError('Ordinary exported menu close returned nonzero')
        for name in ('client.log', 'engine.log'):
            if failed((output / name).read_text(errors='replace')):
                raise RuntimeError('Native log emitted error: ' + name)
        result['passed'] = True
    except NativePrerequisiteBlocked as error:
        result['blocker'] = str(error)
    except BaseException as error:
        result['failure'] = {'type': type(error).__name__, 'message': str(error)}
    finally:
        failures = []
        if ui is not None:
            try:
                result['cg_event_post_attempts'] = ui.event_post_attempts
                result['final_input_release'] = ui.release_owned()
                result['cg_event_post_attempts_after_cleanup'] = ui.event_post_attempts
                if result['final_input_release']['held_after_release'] or result['final_input_release']['errors']:
                    raise RuntimeError('Owned controls remain held or native state could not be observed')
            except BaseException as error:
                failures.append('input_release: ' + str(error))
        try:
            result['failure_ordinary_close'] = ordinary_failure_close(ui, client)
        except BaseException as error:
            failures.append('ordinary_close: ' + str(error))
        result['cleanup'] = []
        for name, process in [*helper_processes, *([('client', client)] if client is not None else [])]:
            try:
                cleanup = reap(process)
                result['cleanup'].append({'name': name, **cleanup})
                if not cleanup['owned_group_gone']:
                    raise RuntimeError('Owned process group remains alive')
            except BaseException as error:
                failures.append(name + '_cleanup: ' + str(error))
        if ui is not None:
            try:
                ui.close()
            except BaseException as error:
                failures.append('appkit_pool: ' + str(error))
        if profile_before is not None:
            try:
                result['profile_entries_after'] = profile_entries()
                result['profile_entries_unchanged'] = result['profile_entries_after'] == profile_before
                if not result['profile_entries_unchanged']:
                    raise RuntimeError('Native player-profile entries appeared; existing files preserved')
                result['native_user_directory_after'] = user_directory_inventory()
                previous = native_before['files']
                current = result['native_user_directory_after']['files']
                result['native_user_directory_side_effects'] = {
                    'created_files': sorted(current.keys() - previous.keys()),
                    'removed_files': sorted(previous.keys() - current.keys()),
                    'changed_files': sorted(name for name in current.keys() & previous.keys() if current[name] != previous[name]),
                    'cleanup_scope': 'Owned process groups and held controls only; native user-directory files preserved'}
            except BaseException as error:
                failures.append('native_user_directory: ' + str(error))
        if before is not None:
            try:
                result['source_unchanged'] = source() == before
                validate_record('macos', before)
                if not result['source_unchanged']:
                    raise RuntimeError('Source changed during native Mac journey')
            except BaseException as error:
                failures.append('source_export: ' + str(error))
        if failures:
            result['finalization_failures'] = failures
            result['passed'] = False
        result['seconds'] = time.monotonic() - started
        result['status'] = 'PASS_MENU_NAVIGATION_ONLY' if result['passed'] else 'BLOCKED_EXTERNALLY' if 'blocker' in result and not failures else 'FAILED'
        (output / 'results.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
    return 0 if result['passed'] else 2 if result['status'] == 'BLOCKED_EXTERNALLY' else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--preflight', type=Path, required=True)
    arguments = parser.parse_args()
    def interrupted(signum, _frame):
        raise SystemExit('Native Mac menu validation interrupted by signal ' + str(signum))
    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    return run(arguments.output, arguments.preflight)


if __name__ == '__main__':
    raise SystemExit(main())
