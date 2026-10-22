#!/usr/bin/env python3
"""Independent pure controls for 1260217; no Mac APIs, engine, OCR or events."""
from contextlib import ExitStack, redirect_stdout
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / 'scripts'))
import macos_native_input as adapter
import verify_macos_menu as driver
from probe_macos_input import NativePrerequisiteBlocked


class Clock:
    def __init__(self):
        self.now = 0.0
    def monotonic(self):
        return self.now
    def sleep(self, duration):
        self.now += duration


class IndependentFocusControls(unittest.TestCase):
    def test_controller_metadata_labels_the_raw_pid_without_a_run_loop_turn(self):
        ui = object.__new__(adapter.MacMenuUI)
        ui.pid, ui.window, ui.bounds = 6100, 109, [40, 32, 960, 568]
        ui.application = lambda: None
        ui.pump_run_loop = lambda duration: self.fail('raw snapshot must not process the run loop')
        for foreground, is_controller in ((7300, True), (6200, False), (None, False)):
            with self.subTest(foreground=foreground), patch.object(adapter.os, 'getpid', return_value=7300):
                ui.foreground_pid = lambda: foreground
                state = ui.focus_state()
            self.assertEqual(state['controller_pid'], 7300)
            self.assertEqual(state['foreground_pid'], foreground)
            self.assertIs(state['foreground_is_controller'], is_controller)
            self.assertEqual(state['target_pid'], 6100)
            self.assertEqual(state['target_window'], 109)

    def fixture(self, *, request_delay=0, guard_delay=0, diagnostics_delay=0, immediate=False):
        clock, records, requests = Clock(), [], []
        ui = object.__new__(adapter.MacMenuUI)
        ui.pid, ui.window, ui.bounds, ui.held = 6100, 109, [40, 32, 960, 568], set()
        state = {'foreground': 6200}
        ui.application = lambda: 1
        def message(*args, **kwargs):
            requests.append((args, kwargs))
            clock.now += request_delay
            state['foreground'] = ui.pid
            return True
        ui.message = message
        ui.focus_state = lambda: {'foreground_pid': state['foreground'], 'target_pid': ui.pid,
                                  'target_window': ui.window, 'target_active': True}
        ui.trace = lambda event, **data: records.append((event, data))
        def pump(duration):
            elapsed = 0 if immediate else duration
            clock.now += elapsed
            return {'elapsed_seconds': elapsed, 'return_code': 1 if immediate else 3}
        ui.pump_run_loop = pump
        def guard():
            clock.now += guard_delay
        ui.require_target = guard
        def diagnostics():
            clock.now += diagnostics_delay
            return {'foreground_pid': state['foreground']}
        ui.diagnostics = diagnostics
        return ui, clock, records, requests, state

    def run_focus(self, ui, clock):
        with patch.object(adapter.time, 'monotonic', clock.monotonic), patch.object(adapter.time, 'sleep', clock.sleep):
            return ui.focus()

    def test_request_duration_consumes_the_five_second_budget(self):
        ui, clock, records, requests, _ = self.fixture(request_delay=5.01)
        with self.assertRaisesRegex(RuntimeError, 'exact foreground PID'):
            self.run_focus(ui, clock)
        self.assertEqual(len(requests), 1)
        self.assertFalse(any(event == 'focus_observed' for event, _ in records))
        self.assertFalse(any(event == 'focus_sample' for event, _ in records))

    def test_late_guard_and_late_diagnostics_cannot_accept_an_earlier_good_sample(self):
        for field in ('guard_delay', 'diagnostics_delay'):
            with self.subTest(field=field):
                ui, clock, records, requests, _ = self.fixture(**{field: 5})
                with self.assertRaisesRegex(RuntimeError, 'exact foreground PID'):
                    self.run_focus(ui, clock)
                self.assertEqual(len(requests), 1)
                self.assertFalse(any(event == 'focus_observed' for event, _ in records))

    def test_immediate_finished_run_loop_is_not_a_focus_proxy_or_a_busy_loop(self):
        ui, clock, records, _, state = self.fixture(immediate=True)
        original_message = ui.message
        def message(*args, **kwargs):
            accepted = original_message(*args, **kwargs)
            state['foreground'] = 6200
            return accepted
        ui.message = message
        with self.assertRaisesRegex(RuntimeError, 'exact foreground PID'):
            self.run_focus(ui, clock)
        self.assertAlmostEqual(clock.now, 5)
        samples = [data for event, data in records if event == 'focus_sample']
        self.assertGreaterEqual(len(samples), 99)
        self.assertLessEqual(len(samples), 102)

    def test_newer_guard_focus_loss_refuses_acceptance_without_a_second_request(self):
        ui, clock, records, requests, _ = self.fixture()
        def guard():
            raise RuntimeError('exact target lost at guard')
        ui.require_target = guard
        with self.assertRaisesRegex(RuntimeError, 'exact target lost at guard'):
            self.run_focus(ui, clock)
        self.assertEqual(len(requests), 1)
        self.assertFalse(any(event == 'focus_observed' for event, _ in records))


class IndependentDriverControls(unittest.TestCase):
    def run_fake_driver(self, *, capture_failure=None, focus_failure=False):
        """Run the real orchestration, replacing every native/child boundary."""
        identity = {'source_commit': 'synthetic-source', 'source_game_tree': 'game',
                    'source_content_sha256': 'content', 'source_validation_sha256': 'validation'}
        manifest = {**identity, 'artifact': {'sha256': 'synthetic-digest'}}
        permission = {'CGPreflightPostEventAccess': True, 'CGPreflightScreenCaptureAccess': True}
        window = {'window_id': 109, 'owner_pid': 6100, 'onscreen': True,
                  'bounds_points_including_chrome': [40, 32, 960, 568]}
        inventory = {'directory_exists': False, 'directories': [], 'files': {}}
        order, processes, ui_instances = [], [], []
        class Process:
            def __init__(self, command, **kwargs):
                self.command, self.pid, self.returncode = command, 7100 + len(processes), 0
                processes.append(self)
                if command[0].endswith('/macos/game'):
                    self.pid, self.returncode = 6100, None
                    Path(command[command.index('--log-file') + 1]).write_text('')
                elif '--report' in command:
                    name = Path(command[command.index('--report') + 1]).stem
                    order.append(name)
                    data = {'passed': True, 'scope': 'OS window screenshot from ScreenCaptureKit; read-only helper',
                            'owner_pid': 6100, 'window_id': 109, 'permissions': permission,
                            'bounds_points_including_chrome': [40, 32, 960, 568],
                            'input_events_posted': 0, 'permission_requests_made': 0,
                            'text': [{'text': 'FIELD SETTINGS', 'confidence': .99}] if name == '02-field-settings' else
                                    [{'text': 'TACTICAL OPERATIONS', 'confidence': .99},
                                     {'text': 'SETTINGS', 'confidence': .99}]}
                    if name == '00-background-window' and capture_failure:
                        data.update(capture_failure)
                    Path(command[command.index('--report') + 1]).write_text(json.dumps(data))
                    Path(command[command.index('--png') + 1]).write_bytes(b'SYNTHETIC_NOT_A_PNG')
            def poll(self):
                return self.returncode
            def wait(self, timeout):
                return self.returncode
        class UI:
            def __init__(self, pid, window_id, bounds, trace):
                self.pid, self.window, self.bounds, self.trace = pid, window_id, bounds, trace
                self.event_post_attempts = 0
                ui_instances.append(self)
            def require_window(self):
                order.append('window_guard')
            def require_target(self):
                order.append('target_guard')
            def diagnostics(self):
                return {'foreground_pid': self.pid, 'lmb_down': False, 'escape_down': False}
            def focus_state(self):
                order.append('raw_focus_observation')
                return {'foreground_pid': self.pid, 'target_pid': self.pid, 'target_window': self.window}
            def focus(self):
                order.append('focus')
                self.trace('synthetic_focus_called', target_pid=self.pid)
                if focus_failure:
                    raise RuntimeError('synthetic exact foreground failure')
            def neutral(self):
                order.append('neutral')
            def click_settings(self, capture):
                order.append('pointer_transaction')
                self.event_post_attempts += 3
            def tap_escape(self):
                order.append('escape_transaction')
                self.event_post_attempts += 2
            def release_owned(self):
                return {'held_after_release': [], 'errors': [], 'native_state': self.diagnostics()}
            def request_close(self):
                order.append('ordinary_close')
                next(process for process in processes if process.pid == self.pid).returncode = 0
                return True
            def close(self):
                order.append('pool_close')
        class API:
            def preflight(self):
                return permission
            def windows(self, pid):
                return [window] if pid == 6100 else []
        with tempfile.TemporaryDirectory() as temporary:
            temporary = Path(temporary)
            preflight = temporary / 'preflight.json'
            preflight.write_text(json.dumps({'status': 'READY_FOR_INPUT_ATTEMPT', 'source': identity,
                'artifact_source': manifest, 'executable_sha256': 'synthetic-digest', 'source_unchanged': True,
                'normal_exit_code': 0, 'cleanup': {'owned_group_gone': True}, 'profile_entries_unchanged': True,
                'permissions': permission, 'window_observations': [{'windows': [
                    {'owner_pid': 6050, 'window_id': 25, 'onscreen': True}]}]}))
            patches = {'MacReadOnly': API, 'MacMenuUI': UI, 'source': lambda: identity, 'clean': lambda before: None,
                'validate_record': lambda *args: manifest, 'require_absent_profile': lambda: {}, 'profile_entries': lambda: {},
                'user_directory_inventory': lambda: inventory, 'digest': lambda path: 'synthetic-digest',
                'BUILDS': temporary / 'builds', 'OUTPUTS': {'macos': 'macos/game'},
                'reap': lambda process: {'pid': process.pid, 'owned_group_gone': True, 'signals_sent': [], 'exit_code': process.returncode}}
            with ExitStack() as stack:
                for key, value in patches.items():
                    stack.enter_context(patch.object(driver, key, value))
                stack.enter_context(patch.object(driver.toolchain, 'verify_engine', return_value={'synthetic': True}))
                stack.enter_context(patch.object(driver.subprocess, 'Popen', side_effect=Process))
                stack.enter_context(patch.object(driver.time, 'sleep', lambda seconds: None))
                stack.enter_context(redirect_stdout(io.StringIO()))
                exit_code = driver.run(temporary / 'evidence', preflight)
            result = json.loads((temporary / 'evidence/results.json').read_text())
        return exit_code, result, order, ui_instances

    def test_foreign_background_receipt_collects_focus_then_all_input_stays_blocked(self):
        for bad in ({'owner_pid': 6050}, {'window_id': 25}, {'bounds_points_including_chrome': [40, 32, 800, 568]},
                    {'input_events_posted': 1}, {'permission_requests_made': 1}, {'permissions': {}}):
            with self.subTest(bad=bad):
                code, result, order, ui = self.run_fake_driver(capture_failure=bad)
                self.assertNotEqual(code, 0)
                self.assertFalse(result['passed'])
                self.assertIn('focus', order)
                self.assertNotIn('pointer_transaction', order)
                self.assertNotIn('escape_transaction', order)
                self.assertEqual(ui[0].event_post_attempts, 0)
                self.assertEqual(result['selected_client_window']['owner_pid'], 6100)
                self.assertEqual(result['selected_client_window']['window_id'], 109)
                self.assertIn('ordinary_close', order)

    def test_capture_success_and_failed_focus_do_not_reach_neutral_or_events(self):
        code, result, order, ui = self.run_fake_driver(focus_failure=True)
        self.assertEqual(code, 1)
        self.assertEqual(result['background_capture_status'], 'PASS_CAPTURE_ONLY_NO_FOCUS_OR_INPUT')
        self.assertEqual(len(result['captures']), 1)
        self.assertFalse(result['captures'][0]['foreground_required'])
        self.assertIsNone(result['captures'][0]['screen_checked'])
        self.assertNotIn('neutral', order)
        self.assertEqual(ui[0].event_post_attempts, 0)

    def test_dual_failure_retains_both_causes_and_zero_events(self):
        code, result, order, ui = self.run_fake_driver(capture_failure={'permissions': {}}, focus_failure=True)
        self.assertEqual(code, 1)
        self.assertEqual(result['background_capture_status'], 'BLOCKED_EXTERNALLY')
        self.assertIn('Capture helper permission denied', result['background_capture_failure']['message'])
        self.assertIn('foreground failure', result['failure']['message'])
        self.assertEqual(ui[0].event_post_attempts, 0)


if __name__ == '__main__':
    unittest.main()
