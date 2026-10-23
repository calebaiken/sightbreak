#!/usr/bin/env python3
"""Opt-in AX exposure diagnostic. No input, selector change or gameplay claim."""
import argparse
import copy
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import uuid

from build_manifest import BUILDS, OUTPUTS, clean, source, validate_record
from macos_ax_appkit import AXWindow
from macos_ax_contract import (CAPS, require_capture, require_owned, validate_collection,
                               validate_observation, validate_request)
from macos_deploy_ocr import png_dimensions
from macos_ordinary_input import (account_home, capture_geometry, default_inventory, inventory,
    no_symlinks, stage_app, verify_staged_app)
from native_log import failed
from probe_macos_input import MacReadOnly, NativePrerequisiteBlocked, digest, reap, require_absent_profile
from verify_macos_menu import CAPTURE_SOURCE, require_screen
from verify_macos_ordinary import (BUDGETS, ENVIRONMENT_KEYS, StartupMenuNotReady,
                                   discover_startup_menu)
import toolchain


AX_SOURCE = Path(__file__).with_name('probe_macos_ax.py')
BOUND_SOURCES = (Path(__file__), AX_SOURCE, Path(__file__).with_name('macos_ax_contract.py'),
                 Path(__file__).with_name('macos_ax_appkit.py'), CAPTURE_SOURCE)


def launch_arguments(executable, trace_directory):
    # Sole declared engine amendment; the existing ordinary arguments keep order.
    return [str(executable), '--audio-driver', 'Dummy', '--log-file', 'user://mac-ordinary-engine.log',
            '--windowed', '--resolution', '1280x720', '--position', '40,60',
            '--accessibility', 'always', '--', '--offline-validation',
            '--offline-trace-dir=' + str(trace_directory)]


def private_menu_inventory(directory, default_before):
    """Inventory engine-created files by hash; never parse/retain profile fields."""
    if default_inventory() != default_before:
        raise RuntimeError('Default user directory changed during private AX diagnostic')
    require_absent_profile()
    current = inventory(directory)
    log = Path(directory) / 'mac-ordinary-engine.log'
    if not current['directory_exists'] or not log.is_file():
        raise NativePrerequisiteBlocked('Exact native artifact has not established its private user:// log')
    if 'Godot Engine v4.7.2.stable' not in log.read_text(errors='replace'):
        raise RuntimeError('Private engine log lacks pinned version header')
    return current


def run(output):
    output = Path(output).absolute()
    no_symlinks(output)
    if os.path.lexists(output) and (not output.is_dir() or any(output.iterdir())):
        raise RuntimeError('Preserve diagnostic evidence; choose a fresh output directory')
    if output.is_relative_to(toolchain.ROOT / 'game') or output.is_relative_to(BUILDS / 'macos'):
        raise RuntimeError('Evidence must be outside source and original payload')
    output.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    deadline = started + BUDGETS['total']
    before = manifest = client = ui = staged = private = default_before = None
    processes, actions = [], []
    result = {'scope': 'Opt-in --accessibility always read-only exported AX exposure diagnostic; no input or gameplay acceptance',
              'passed': False, 'permission_requests_made': 0, 'cg_event_post_attempts': 0,
              'controller_pid': os.getpid(), 'budgets_seconds': dict(BUDGETS), 'ax_caps': dict(CAPS),
              'actions': actions, 'capture_attempts': [], 'captures': [],
              'query_prerequisites': False, 'bounded_traversal_complete': False,
              'unique_semantic_candidate': False, 'native_pixel_frame_agreement': False,
              'gameplay_target_accepted': False, 'ocr_confidence_threshold_changed': False}

    def remaining(until=None):
        value = min(deadline, until if until is not None else deadline) - time.monotonic()
        if value <= 0:
            raise TimeoutError('Original AX diagnostic stage/whole deadline exceeded')
        return value

    def trace(event, **details):
        actions.append({'event': event, 'seconds': time.monotonic() - started, **copy.deepcopy(details)})
        (output / 'actions.json').write_text(json.dumps(actions, indent=2) + '\n')

    def command(name, arguments, budget, *, allow_failure=False):
        until = min(deadline, time.monotonic() + budget)
        trace('helper_command', name=name, command=arguments, budget_seconds=budget)
        with (output / (name + '.log')).open('w', encoding='utf-8') as log:
            process = subprocess.Popen(arguments, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            processes.append((name, process))
            process.wait(timeout=remaining(until))
        remaining(until)  # Late success never renews the helper's deadline.
        if failed((output / (name + '.log')).read_text(errors='replace')):
            raise RuntimeError('Strict native error/leak signature in ' + name)
        if process.returncode and not allow_failure:
            raise RuntimeError(name + ' failed; original output retained')
        return process

    def capture(name, screen='menu', *, require_focus=True, until=None):
        remaining(until)
        png, receipt = output / (name + '.png'), output / (name + '.json')
        attempt = {'name': name, 'accepted': False, 'started_monotonic': time.monotonic(),
                   'foreground_required': require_focus}
        result['capture_attempts'].append(attempt)
        try:
            (ui.require_target if require_focus else ui.require_window)()
            child = command(name, [str(helper), '--pid', str(client.pid), '--window', str(ui.window),
                                  '--png', str(png), '--report', str(receipt)],
                            min(BUDGETS['capture'], remaining(until)), allow_failure=True)
            data = json.loads(receipt.read_text())
            if child.returncode or data.get('passed') is not True:
                raise RuntimeError('Original read-only capture helper failed')
            if (data.get('owner_pid') != client.pid or data.get('window_id') != ui.window
                    or data.get('input_events_posted') != 0 or data.get('permission_requests_made') != 0):
                raise RuntimeError('Native screenshot owner/window/zero-event binding failed')
            capture_geometry(data)
            if png_dimensions(png) != data.get('image_dimensions'):
                raise RuntimeError('Original native PNG header/receipt dimensions disagree')
            if 'derived_deploy_analysis' in data:
                raise RuntimeError('Read-only AX preflight requests only the unchanged native capture defaults')
            try:
                require_screen(data, screen)
            except RuntimeError as error:
                if not require_focus and not ui.pinned:
                    raise StartupMenuNotReady(str(error)) from error
                raise
            require_capture(data, client.pid, ui.window, ui.bounds)
            (ui.require_target if require_focus else ui.require_window)()
            remaining(until)
            attempt['accepted'] = True
            result['captures'].append({'name': name, 'png_sha256': digest(png),
                                       'receipt_sha256': digest(receipt), 'foreground_required': require_focus})
            return data
        except BaseException as error:
            attempt['failure'] = {'type': type(error).__name__, 'message': str(error)}
            raise
        finally:
            attempt['finished_monotonic'] = time.monotonic()
            attempt['retained_files'] = {path.name: {'bytes': path.stat().st_size, 'sha256': digest(path)}
                                         for path in (png, receipt) if path.is_file()}

    try:
        api = MacReadOnly()  # Source controls never compile/launch on another host.
        before = source()
        clean(before)
        manifest = validate_record('macos', before)
        home = account_home()
        result.update(source=before, artifact_source=manifest, engine=toolchain.verify_engine(),
                      account_home=str(home), permissions=api.preflight(),
                      environment_whitelist={key: os.environ.get(key) for key in ENVIRONMENT_KEYS},
                      bound_source_sha256={path.name: digest(path) for path in BOUND_SOURCES},
                      interpreter={'path': sys.executable, 'sha256': digest(Path(sys.executable).resolve()),
                                   'version': sys.version})
        if result['permissions'].get('CGPreflightScreenCaptureAccess') is not True:
            raise NativePrerequisiteBlocked('Current controller capture permission absent; no request made')
        default_before = default_inventory()
        require_absent_profile()
        result['default_user_directory_before'] = default_before
        name = 'SIGHTBREAK-mac-ordinary-' + uuid.uuid4().hex
        private = home / 'Library/Application Support' / name
        if inventory(private)['directory_exists'] or os.path.lexists(private):
            raise RuntimeError('Private user-directory entry already exists')
        result['private_user_directory'] = str(private)
        staged = stage_app((BUILDS / OUTPUTS['macos']).parents[2], output / 'native/SIGHTBREAK.app', name)
        result['native_artifact_attestation'] = staged
        if staged['executable_sha256'] != manifest['artifact']['sha256']:
            raise RuntimeError('Exact staged executable/export manifest mismatch')
        helper = output / 'macos-window-capture'
        command('compile-capture-helper', ['xcrun', 'swiftc', '-parse-as-library', '-swift-version', '5',
                '-target', 'arm64-apple-macos14.0', str(CAPTURE_SOURCE), '-framework', 'AppKit',
                '-framework', 'CoreGraphics', '-framework', 'ScreenCaptureKit', '-framework', 'Vision',
                '-framework', 'ImageIO', '-framework', 'UniformTypeIdentifiers', '-o', str(helper)], BUDGETS['compile'])
        result['capture_helper'] = {'source_sha256': digest(CAPTURE_SOURCE), 'executable_sha256': digest(helper)}
        trace_directory = output / 'stock-offline-trace'
        arguments = launch_arguments(Path(staged['staged']) / 'Contents/MacOS/SIGHTBREAK', trace_directory)
        result['client_command'] = arguments
        result['launch_amendment'] = {'engine_arguments': ['--accessibility', 'always'],
                                      'scope': 'Explicit diagnostic only; ordinary launch/selector unchanged'}
        with (output / 'client.log').open('w', encoding='utf-8') as log:
            client = subprocess.Popen(arguments, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            processes.append(('client', client))
            result['client_pid'] = client.pid
            window_until = min(deadline, time.monotonic() + BUDGETS['window'])
            while True:
                remaining(window_until)
                if client.poll() is not None:
                    raise RuntimeError('Exported client exited before owned window readiness')
                rows = api.windows(client.pid)
                trace('first_window_observation', observed_owned_layer_zero_windows=rows)
                if len([row for row in rows if row.get('owner_pid') == client.pid and row.get('onscreen') is True]) == 1:
                    result['first_client_window'] = require_owned(rows, client.pid)
                    remaining(window_until)
                    break
                time.sleep(min(.05, remaining(window_until)))
            result['private_menu_inventory_after_window'] = private_menu_inventory(private, default_before)
            menu_until = min(deadline, time.monotonic() + BUDGETS['menu'])

            def select(candidate):
                nonlocal ui
                if ui is not None:
                    if ui.pinned or ui.event_post_attempts or ui.focus_requests:
                        raise RuntimeError('Cannot reselect geometry after focus/pin/event attempt')
                    ui.close()
                ui = AXWindow(client.pid, candidate['window_id'], candidate['bounds_points_including_chrome'],
                              trace, lambda: private_menu_inventory(private, default_before))
                return ui

            ui, _ = discover_startup_menu(api, client, select, capture, remaining, trace, menu_until)
            focus_until = min(menu_until, time.monotonic() + BUDGETS['focus'])
            ui.focus(remaining(focus_until))
            remaining(focus_until)
            focus_finished = time.monotonic()
            menu = capture('01-focused-menu', until=menu_until)
            ui.pin(menu)
            remaining(menu_until)
            result['pinned_window'] = {'owner_pid': ui.pid, 'window_id': ui.window, 'bounds_points': list(ui.bounds),
                                       'focus_finished_monotonic': focus_finished, 'pinned_monotonic': time.monotonic()}
            native_files = {path: digest(path) for path in (output / '01-focused-menu.png', output / '01-focused-menu.json')}
            before_rows = ui.require_target()
            nonce = uuid.uuid4().hex
            budget = min(CAPS['seconds'], remaining(menu_until))
            ax_started = time.monotonic()
            ax_until = min(menu_until, ax_started + budget)
            ax_file = output / 'ax-observation.json'
            child = command('ax-observer', [sys.executable, str(AX_SOURCE), '--pid', str(client.pid),
                            '--window', str(ui.window), '--bounds', *map(str, ui.bounds), '--nonce', nonce,
                            '--budget', str(budget), '--report', str(ax_file)], budget, allow_failure=True)
            remaining(menu_until)
            after_rows = ui.require_target()
            ax_finished = time.monotonic()
            remaining(ax_until)
            if ax_file.stat().st_size > CAPS['receipt_bytes']:
                raise RuntimeError('AX observer receipt exceeds preregistered byte bound')
            ax = json.loads(ax_file.read_text())
            result['ax_observation'] = {'sha256': digest(ax_file), 'observer_pid': child.pid,
                                        'nonce': nonce, 'started_monotonic': ax_started,
                                        'finished_monotonic': ax_finished, 'budget_seconds': budget,
                                        'owned_rows_before': before_rows, 'owned_rows_after': after_rows}
            binding = dict(pid=client.pid, window=ui.window, bounds=ui.bounds, nonce=nonce,
                           observer_pid=child.pid, started=ax_started, finished=ax_finished, budget=budget)
            validate_request(ax, **binding)
            result['query_prerequisites'] = True
            if child.returncode:
                raise RuntimeError('Read-only AX observer did not complete; original failure retained')
            validate_collection(ax, **binding)
            result['bounded_traversal_complete'] = True
            exposure = validate_observation(ax, menu, **binding)
            for path, expected in native_files.items():
                if digest(path) != expected:
                    raise RuntimeError('Original focused native capture/Vision bytes changed')
            remaining(ax_until)
            result.update(query_prerequisites=True, bounded_traversal_complete=True,
                          unique_semantic_candidate=True, native_pixel_frame_agreement=True,
                          semantic_exposure=exposure, original_native_ocr_unchanged=True)
            if os.path.lexists(trace_directory):
                raise RuntimeError('Unexpected stock match trace: read-only diagnostic must never deploy')
            remaining(menu_until)
        result['passed'] = True
    except NativePrerequisiteBlocked as error:
        result['blocker'] = str(error)
    except BaseException as error:
        result['failure'] = {'type': type(error).__name__, 'message': str(error)}
    finally:
        failures = []
        if client is not None and client.poll() is None:
            try:
                if ui is None:
                    ui = AXWindow(client.pid, None, None, trace, lambda: None)
                    result['close_only_adapter'] = True
                close_until = min(deadline, time.monotonic() + BUDGETS['close'])
                result['ordinary_termination_requested'] = ui.request_close()
                if not result['ordinary_termination_requested']:
                    raise RuntimeError('Public ordinary termination refused')
                client.wait(timeout=remaining(close_until))
                remaining(close_until)
                result['normal_exit_code'] = client.returncode
                if client.returncode:
                    raise RuntimeError('Ordinary diagnostic close returned nonzero')
            except BaseException as error:
                failures.append('ordinary_close: ' + str(error))
        elif client is not None:
            failures.append('ordinary_close: client exited before the declared ordinary termination')
        result['cleanup'] = []
        for name, process in processes:
            try:
                cleanup = reap(process)
                result['cleanup'].append({'name': name, **cleanup})
                if not cleanup['owned_group_gone'] or cleanup['signals_sent']:
                    raise RuntimeError('Owned group survived or required fallback signal')
            except BaseException as error:
                failures.append(name + '_cleanup: ' + str(error))
        if ui is not None:
            result['cg_event_post_attempts'] = ui.event_post_attempts
            result['focus_requests'] = ui.focus_requests
            if ui.event_post_attempts or ui.focus_requests > 1:
                failures.append('read_only: event attempt or repeated focus')
            try:
                ui.close()
            except BaseException as error:
                failures.append('appkit: ' + str(error))
        if staged is not None:
            try:
                verify_staged_app(staged)
                result['payload_unchanged'] = True
            except BaseException as error:
                failures.append('payload: ' + str(error))
        if default_before is not None:
            try:
                result['default_user_directory_after'] = default_inventory()
                if result['default_user_directory_after'] != default_before:
                    raise RuntimeError('Default userdata changed; all files preserved')
                result['default_user_directory_unchanged'] = True
                require_absent_profile()
            except BaseException as error:
                failures.append('default_userdata: ' + str(error))
        if private is not None:
            try:
                result['private_user_directory_after'] = inventory(private)
                result['private_menu_profile_files_present'] = [name for name in ('offline_training.json', 'offline_training.json.tmp')
                                                                 if os.path.lexists(private / name)]
                result['private_profile_scope'] = 'Engine-owned private menu files preserved with byte hashes; no profile fields parsed/retained; no input or reward action'
                log = private / 'mac-ordinary-engine.log'
                if log.is_file():
                    (output / 'engine.log').write_bytes(log.read_bytes())
                if result['passed']:
                    private_menu_inventory(private, default_before)
                if os.path.lexists(output / 'stock-offline-trace'):
                    raise RuntimeError('Unexpected match trace exists; no deploy/reward action is permitted')
            except BaseException as error:
                failures.append('private_userdata: ' + str(error))
        for path in sorted(output.glob('*.log')):
            if failed(path.read_text(errors='replace')):
                failures.append('strict_native_log: ' + path.name)
        if before is not None:
            try:
                result['source_unchanged'] = source() == before
                validate_record('macos', before)
                if not result['source_unchanged']:
                    raise RuntimeError('Source/export changed during diagnostic')
                if ('bound_source_sha256' in result
                        and result['bound_source_sha256'] != {path.name: digest(path) for path in BOUND_SOURCES}):
                    raise RuntimeError('Bound observer/controller/capture source changed')
            except BaseException as error:
                failures.append('source: ' + str(error))
        if time.monotonic() - started >= BUDGETS['total']:
            failures.append('whole_flow: original 300s deadline exceeded')
        if failures:
            result['finalization_failures'] = failures
            result['passed'] = False
        result['seconds'] = time.monotonic() - started
        result['status'] = ('PASS_READ_ONLY_AX_EXPOSURE_ONLY' if result['passed'] else
                            'BLOCKED_EXTERNALLY' if 'blocker' in result and not failures else 'FAILED')
        (output / 'results.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
    return 0 if result['passed'] else 2 if result['status'] == 'BLOCKED_EXTERNALLY' else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    def interrupted(signum, _frame):
        raise SystemExit('Read-only AX diagnostic interrupted by signal ' + str(signum))
    for signum in (signal.SIGTERM, signal.SIGINT):
        signal.signal(signum, interrupted)
    return run(args.output)


if __name__ == '__main__':
    raise SystemExit(main())
