#!/usr/bin/env python3
"""Independent Linux-safe probes; native frameworks and engines never load."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / 'scripts'))
parser = argparse.ArgumentParser()
parser.add_argument('--revision', required=True)
arguments, unittest_arguments = parser.parse_known_args()
revision = subprocess.check_output(['git', 'rev-parse', arguments.revision], cwd=ROOT, text=True).strip()
adapter_bytes = subprocess.check_output(['git', 'show', revision + ':scripts/macos_native_input.py'], cwd=ROOT)
adapter = types.ModuleType('frozen_macos_native_input')
exec(compile(adapter_bytes, 'git:' + revision + ':scripts/macos_native_input.py', 'exec'), adapter.__dict__)
driver_bytes = subprocess.check_output(['git', 'show', revision + ':scripts/verify_macos_menu.py'], cwd=ROOT)
driver = types.ModuleType('frozen_verify_macos_menu')
driver.__file__ = str(ROOT / 'scripts/verify_macos_menu.py')
exec(compile(driver_bytes, 'git:' + revision + ':scripts/verify_macos_menu.py', 'exec'), driver.__dict__)


def capture_fixture():
    return {'passed': True, 'scope': 'OS window screenshot from ScreenCaptureKit; read-only helper',
            'permissions': {'CGPreflightScreenCaptureAccess': True},
            'owner_pid': 123, 'window_id': 34, 'bounds_points_including_chrome': [40, 32, 960, 568],
            'scwindow_frame_points': [40, 32, 960, 568], 'filter_content_rect_points': [0, 0, 960, 568],
            'point_pixel_scale': 2, 'image_dimensions': [1920, 1136],
            'text': [{'text': 'TACTICAL OPERATIONS', 'confidence': .99},
                     {'text': 'SETTINGS', 'confidence': .99, 'box_normalized_bottom_left': [.1, .2, .2, .05]}]}


class FakeCG:
    def __init__(self):
        self.left = self.escape = False
        self.allocations = []

    def CGEventSourceButtonState(self, source, button):
        return self.left

    def CGEventSourceKeyState(self, source, key):
        return self.escape if key == 53 else False

    def CGEventCreateMouseEvent(self, source, kind, point, button):
        self.allocations.append(('mouse', kind))
        return ('mouse', kind)

    def CGEventCreateKeyboardEvent(self, source, key, down):
        self.allocations.append(('key', bool(down)))
        return ('key', bool(down))


def fake_ui():
    ui = object.__new__(adapter.MacMenuUI)
    ui.pid, ui.window, ui.bounds = 123, 34, [40, 32, 960, 568]
    ui.held, ui.last_pointer_point, ui.event_post_attempts = set(), None, 0
    ui.cg = FakeCG()
    ui.preflight = lambda: {'CGPreflightPostEventAccess': True, 'CGPreflightScreenCaptureAccess': True}
    ui.windows = lambda pid: [{'window_id': 34, 'onscreen': True,
                              'bounds_points_including_chrome': [40, 32, 960, 568]}]
    ui.foreground_pid = lambda: 123
    ui.trace = lambda *args, **kwargs: None
    ui.diagnostics = lambda: {'foreground_pid': ui.foreground_pid(), 'lmb_down': ui.cg.left,
                             'escape_down': ui.cg.escape, 'pointer_points': [232, 472.2]}
    ui.posts = []
    def post(event, kind):
        ui.posts.append(kind)
        if kind == 'lmb_down': ui.cg.left = True
        elif kind == 'lmb_up': ui.cg.left = False
        elif kind == 'escape_down': ui.cg.escape = True
        elif kind == 'escape_up': ui.cg.escape = False
    ui.post = post
    return ui


class IndependentControls(unittest.TestCase):
    def test_failure_quit_skips_missing_or_already_exited_owned_client(self):
        class Exited:
            def poll(self): return 0
        ui = fake_ui()
        ui.request_close = lambda: self.fail('must not request quit')
        self.assertEqual(driver.ordinary_failure_close(None, Exited()), {'needed': False})
        self.assertEqual(driver.ordinary_failure_close(ui, None), {'needed': False})
        self.assertEqual(driver.ordinary_failure_close(ui, Exited()), {'needed': False})

    def test_failure_quit_refusal_returns_immediately_for_group_fallback(self):
        class Running:
            def poll(self): return None
            def wait(self, timeout): self.fail('must not wait after refusal')
        ui = fake_ui()
        ui.request_close = lambda: False
        self.assertEqual(driver.ordinary_failure_close(ui, Running()),
                         {'needed': True, 'request_accepted': False})

    def test_failure_quit_wait_is_bounded_to_three_seconds(self):
        observed = []
        class Running:
            def poll(self): return None
            def wait(self, timeout):
                observed.append(timeout)
                raise subprocess.TimeoutExpired('mock-owned-client', timeout)
        ui = fake_ui()
        ui.request_close = lambda: True
        self.assertEqual(driver.ordinary_failure_close(ui, Running()),
                         {'needed': True, 'request_accepted': True, 'timed_out': True})
        self.assertEqual(observed, [3])

    def test_latest_diagnostics_foreground_loss_refuses_both_down_paths(self):
        for name in ('lmb', 'escape'):
            ui = fake_ui()
            ui.diagnostics = lambda: {'foreground_pid': 999, 'lmb_down': False,
                                     'escape_down': False, 'pointer_points': [232, 472.2]}
            with self.subTest(control=name), patch.object(adapter, 'require_absent_profile'):
                with self.assertRaisesRegex(RuntimeError, 'Foreground'):
                    if name == 'lmb': ui.button(True, [232, 472.2])
                    else: ui.escape(True)
            self.assertEqual(ui.posts, [])
            self.assertEqual(ui.held, set())

    def test_function_modifier_baseline_refuses_both_down_paths(self):
        for name in ('lmb', 'escape'):
            ui = fake_ui()
            ui.cg.CGEventSourceKeyState = lambda source, key: key == 63
            with self.subTest(control=name), patch.object(adapter, 'require_absent_profile'):
                with self.assertRaisesRegex(RuntimeError, 'modifier'):
                    if name == 'lmb': ui.button(True, [232, 472.2])
                    else: ui.escape(True)
            self.assertEqual(ui.posts, [])
            self.assertEqual(ui.held, set())

    def test_dirty_baseline_at_actual_button_down_refuses_post(self):
        ui = fake_ui()
        ui.cg.escape = True
        with patch.object(adapter, 'require_absent_profile'):
            with self.assertRaises(RuntimeError):
                ui.button(True, [232, 472.2])
        self.assertEqual(ui.posts, [])
        self.assertEqual(ui.held, set())

    def test_dirty_baseline_at_actual_escape_down_refuses_post(self):
        ui = fake_ui()
        ui.cg.left = True
        with patch.object(adapter, 'require_absent_profile'):
            with self.assertRaises(RuntimeError):
                ui.escape(True)
        self.assertEqual(ui.posts, [])
        self.assertEqual(ui.held, set())

    def test_keyboard_post_cancellation_retains_ownership_for_final_release(self):
        ui = fake_ui()
        def cancelled_post(event, kind):
            if kind == 'escape_down': raise SystemExit('injected cancellation before native post')
            ui.posts.append(kind)
            ui.cg.escape = False
        ui.post = cancelled_post
        with patch.object(adapter, 'require_absent_profile'):
            with self.assertRaises(SystemExit): ui.tap_escape()
        self.assertEqual(ui.held, {'escape'})
        report = ui.release_owned()
        self.assertEqual(ui.posts, ['escape_up'])
        self.assertEqual(report['held_after_release'], [])
        self.assertEqual(report['errors'], [])

    def test_pointer_post_cancellation_retains_ownership_for_final_release(self):
        ui = fake_ui()
        def cancelled_post(event, kind):
            if kind == 'lmb_down': raise KeyboardInterrupt('injected cancellation before native post')
            ui.posts.append(kind)
            ui.cg.left = False
        ui.post = cancelled_post
        with patch.object(adapter, 'require_absent_profile'):
            with self.assertRaises(KeyboardInterrupt): ui.button(True, [232, 472.2])
        self.assertEqual(ui.held, {'lmb'})
        report = ui.release_owned()
        self.assertEqual(ui.posts, ['lmb_up'])
        self.assertEqual(report['held_after_release'], [])
        self.assertEqual(report['errors'], [])

    def test_failed_release_preserves_control_for_later_cleanup_retry(self):
        ui = fake_ui()
        ui.held = {'escape'}
        ui.cg.escape = True
        ui.post = lambda event, kind: None
        with patch.object(adapter.time, 'monotonic', side_effect=[0, 0, 2]):
            report = ui.release_owned()
        self.assertEqual(report['held_after_release'], ['escape'])
        self.assertEqual(len(report['errors']), 1)
        ui.cg.escape = False
        self.assertEqual(ui.release_owned()['held_after_release'], [])

    def test_acknowledgement_requires_focus_and_does_not_accept_stale_neutral(self):
        ui = fake_ui()
        ui.cg.escape = True
        ui.foreground_pid = lambda: 999
        with self.assertRaisesRegex(RuntimeError, 'Foreground'):
            ui.observed_state('escape', True)
        ui.foreground_pid = lambda: 123
        ui.cg.escape = False
        with patch.object(adapter.time, 'monotonic', side_effect=[0, 0, 3]):
            with self.assertRaisesRegex(RuntimeError, 'did not acknowledge'):
                ui.observed_state('escape', True)

    def test_changed_target_after_pointer_move_refuses_button_post(self):
        ui = fake_ui()
        original = ui.post
        def move_then_change_window(event, kind):
            original(event, kind)
            if kind == 'pointer_move':
                ui.windows = lambda pid: []
        ui.post = move_then_change_window
        with patch.object(adapter, 'require_absent_profile'), patch.object(adapter.time, 'sleep'):
            with self.assertRaisesRegex(RuntimeError, 'geometry changed'):
                ui.click_settings(capture_fixture())
        self.assertEqual(ui.posts, ['pointer_move'])
        self.assertEqual(ui.held, set())

    def test_dirty_state_after_pointer_move_refuses_button_post(self):
        ui = fake_ui()
        original = ui.post
        def move_then_change_state(event, kind):
            original(event, kind)
            if kind == 'pointer_move': ui.cg.escape = True
        ui.post = move_then_change_state
        with patch.object(adapter, 'require_absent_profile'), patch.object(adapter.time, 'sleep'):
            with self.assertRaises(RuntimeError):
                ui.click_settings(capture_fixture())
        self.assertEqual(ui.posts, ['pointer_move'])
        self.assertEqual(ui.held, set())


if __name__ == '__main__':
    print(json.dumps({'scope': 'mocked source controls only; no native frameworks, engine or OCR',
                      'source': revision,
                      'adapter_sha256': hashlib.sha256(adapter_bytes).hexdigest(),
                      'driver_sha256': hashlib.sha256(driver_bytes).hexdigest()}), flush=True)
    unittest.main(argv=[sys.argv[0], *unittest_arguments], verbosity=2)
