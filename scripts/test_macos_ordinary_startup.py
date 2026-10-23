#!/usr/bin/env python3
"""Pure startup/readiness falsifiers; no engine, native event, capture or OCR."""
import copy
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch

import macos_native_input as base
import macos_ordinary_input as ordinary
import verify_macos_ordinary as driver
from test_macos_ordinary import capture
from test_macos_ordinary_controller import SyntheticController


class StartupControls(unittest.TestCase):
    def test_splash_and_changed_startup_candidate_are_rejected_then_menu_is_pinned_once(self):
        for fault in ('startup_splash', 'startup_change'):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as temporary:
                harness = SyntheticController(Path(temporary).resolve(strict=True) / 'synthetic', fault)
                code, report = harness.execute()
                self.assertEqual(code, 0, report.get('failure'))
                self.assertEqual(harness.focus_calls, 1)
                self.assertTrue(harness.active_ui.input_geometry_pinned)
                attempts = report['capture_attempts']
                self.assertFalse(attempts[0]['accepted'])
                self.assertIn('00-startup-menu-1.json', attempts[0]['retained_files'])
                self.assertEqual(attempts[-1]['name'], '08-returned-menu')
                self.assertTrue(next(row for row in attempts if row['name'] == '01-focused-menu')['accepted'])
                self.assertTrue(next(row for row in report['captures'] if row['name'] == '01-focused-menu')['foreground_required'])

    def test_churn_and_invalid_captures_cannot_authorize_input_or_reset_menu_deadline(self):
        for fault in ('startup_churn', 'startup_foreign', 'startup_mapping', 'startup_helper_error'):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as temporary:
                harness = SyntheticController(Path(temporary).resolve(strict=True) / 'synthetic', fault)
                code, report = harness.execute()
                self.assertEqual(code, 1)
                self.assertEqual(report['cg_event_post_attempts'], 0)
                self.assertEqual(harness.focus_calls, 0)
                self.assertFalse(any(row['accepted'] for row in report['capture_attempts']))
                if fault != 'startup_churn':
                    self.assertEqual(report['failure']['type'], 'RuntimeError')
                    self.assertEqual(len(report['capture_attempts']), 1)
                    continue
                self.assertEqual(report['failure']['type'], 'TimeoutError')
                observations = [row for row in report['actions'] if row['event'] == 'startup_window_observation']
                helpers = [row for row in report['actions'] if row['event'] == 'helper_command'
                           and row['name'].startswith('00-startup')]
                self.assertLess(max(row['seconds'] for row in observations), driver.BUDGETS['menu'])
                self.assertLessEqual(max(row['seconds']+row['budget_seconds'] for row in helpers), driver.BUDGETS['menu'])

    def test_late_focus_and_post_focus_change_fail_without_repeated_focus_or_input(self):
        for fault in ('focus_late', 'focused_change'):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as temporary:
                harness = SyntheticController(Path(temporary).resolve(strict=True) / 'synthetic', fault)
                code, report = harness.execute()
                self.assertEqual(code, 1)
                self.assertEqual(harness.focus_calls, 1)
                self.assertEqual(report['cg_event_post_attempts'], 0)
                self.assertFalse(harness.active_ui.input_geometry_pinned)

    def discover(self, rows, *, late=False, attempted=False):
        clock = types.SimpleNamespace(now=0.)
        client = types.SimpleNamespace(pid=123, poll=lambda: None)
        api = types.SimpleNamespace(windows=lambda pid: rows)
        calls = []
        def remaining(until):
            if clock.now >= until: raise TimeoutError('fixed synthetic menu deadline')
            return until-clock.now
        def select(row):
            calls.append('select')
            return types.SimpleNamespace(event_post_attempts=1 if attempted else 0)
        def snapshot(*args, **kwargs):
            calls.append('capture')
            if late: clock.now = 60.001
            return capture()
        with patch.object(driver.time, 'sleep', lambda seconds: setattr(clock, 'now', clock.now+seconds)):
            try:
                result = driver.discover_startup_menu(api, client, select, snapshot, remaining,
                                                     lambda *args, **kwargs: None, 60)
                return result, calls, None
            except Exception as error:
                return None, calls, error

    def test_foreign_or_ambiguous_windows_never_authorize_capture_selection(self):
        owned = {'owner_pid': 123, 'onscreen': True, 'window_id': 34}
        for rows in ([dict(owned, owner_pid=999)], [owned, dict(owned, window_id=35)]):
            result, calls, error = self.discover(rows)
            self.assertIsInstance(error, TimeoutError)
            self.assertEqual(calls, [])
            self.assertIsNone(result)

    def test_late_ready_menu_and_any_existing_event_attempt_are_rejected(self):
        rows = [{'owner_pid': 123, 'onscreen': True, 'window_id': 34}]
        result, calls, error = self.discover(rows, late=True)
        self.assertIsInstance(error, TimeoutError)
        self.assertIsNone(result)
        result, calls, error = self.discover(rows, attempted=True)
        self.assertIsInstance(error, RuntimeError)
        self.assertEqual(calls, ['select'])
        self.assertIsNone(result)

    def fake_ui(self):
        ui = object.__new__(ordinary.MacOrdinaryUI)
        ui.pid, ui.window, ui.bounds = 123, 34, [40, 32, 960, 568]
        ui.held, ui.event_post_attempts, ui.input_geometry_pinned = set(), 0, False
        ui.require_target = lambda: None
        ui.neutral = lambda: None
        ui.diagnostics = lambda: {'foreground_pid': 123}
        ui.trace = lambda *args, **kwargs: None
        return ui

    def test_pin_requires_exact_menu_identity_ownership_mapping_and_is_permanent(self):
        for change in ('splash', 'foreign', 'wrong_window', 'bounds', 'mapping', 'event'):
            ui, image = self.fake_ui(), capture()
            if change == 'splash': image['text'] = [dict(image['text'][0], text='GODOT')]
            elif change == 'foreign': image['owner_pid'] = 999
            elif change == 'wrong_window': image['window_id'] = 35
            elif change == 'bounds': image['bounds_points_including_chrome'] = [0, 25, 1024, 684]
            elif change == 'mapping': image['point_pixel_scale'] = True
            else: ui.event_post_attempts = 1
            with self.subTest(change=change), self.assertRaises(RuntimeError):
                ui.pin_for_input(image)
            self.assertFalse(ui.input_geometry_pinned)
        ui = self.fake_ui()
        ui.pin_for_input(capture())
        self.assertTrue(ui.input_geometry_pinned)
        with self.assertRaises(RuntimeError):
            ui.pin_for_input(capture())

    def test_no_cgevent_is_posted_before_pin_and_allocated_event_is_released(self):
        ui = self.fake_ui()
        released = []
        ui.cf = types.SimpleNamespace(CFRelease=released.append)
        with patch.object(base.MacMenuUI, 'post') as post:
            with self.assertRaisesRegex(RuntimeError, 'before permanent input geometry'):
                ui.post(77, 'lmb_down')
            self.assertEqual(released, [77])
            post.assert_not_called()
            ui.input_geometry_pinned = True
            ui.post(88, 'lmb_down')
            post.assert_called_once_with(88, 'lmb_down')

    def test_post_input_geometry_change_is_strict_and_actual_decision_rows_are_retained(self):
        ui = self.fake_ui()
        ui.input_geometry_pinned, ui.event_post_attempts = True, 1
        ui.private_directory, ui.default_before = Path('/synthetic-only'), {}
        ui.preflight = lambda: {'CGPreflightPostEventAccess': True, 'CGPreflightScreenCaptureAccess': True}
        changed = {'owner_pid': 123, 'onscreen': True, 'window_id': 34,
                   'bounds_points_including_chrome': [0, 25, 1024, 684]}
        ui.windows = lambda pid: [changed]
        records = []
        ui.trace = lambda event, **details: records.append((event, copy.deepcopy(details)))
        with patch.object(ordinary, 'require_private_userdir'), self.assertRaises(RuntimeError):
            ordinary.MacOrdinaryUI.require_window(ui)
        self.assertEqual(records[-1][0], 'owned_window_guard')
        self.assertEqual(records[-1][1]['observed_owned_layer_zero_windows'], [changed])
        self.assertTrue(records[-1][1]['input_geometry_pinned'])
        self.assertEqual(records[-1][1]['cg_event_post_attempts'], 1)
        self.assertEqual(ui.bounds, [40, 32, 960, 568])


if __name__ == '__main__':
    unittest.main()
