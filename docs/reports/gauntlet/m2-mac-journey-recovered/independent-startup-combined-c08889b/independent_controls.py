#!/usr/bin/env python3
"""Independent pure review controls. No native API, capture, OCR or engine runs.

Run from the repository root. Three expected-to-reject tests expose the late
same-PID ambiguity at frozen source 0146497; their failure blocks approval.
"""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / 'scripts'))
import macos_native_input as base
import macos_ordinary_input as ordinary
import verify_macos_ordinary as driver
from test_macos_ordinary import capture
from test_macos_ordinary_controller import SyntheticController


def controller(rows=None):
    ui = object.__new__(ordinary.MacOrdinaryUI)
    ui.pid, ui.window, ui.bounds = 123, 34, [40, 32, 960, 568]
    ui.held, ui.event_post_attempts, ui.input_geometry_pinned = set(), 0, False
    ui.private_directory, ui.default_before = Path('/synthetic-only'), {}
    ui.preflight = lambda: {'CGPreflightPostEventAccess': True, 'CGPreflightScreenCaptureAccess': True}
    ui.windows = lambda pid: copy.deepcopy(rows if rows is not None else [owned()])
    ui.trace = lambda *args, **kwargs: None
    ui.current_foreground_pid = lambda: 123
    ui.neutral = lambda: None
    ui.diagnostics = lambda: {'foreground_pid': 123}
    return ui


def owned(window=34, **changes):
    return dict({'owner_pid': 123, 'onscreen': True, 'window_id': window,
                 'bounds_points_including_chrome': [40, 32, 960, 568]}, **changes)


class LateAmbiguity(SyntheticController):
    """Use actual window guard and pin, with mocked OS metadata and clicks."""
    def __init__(self, directory):
        self.second_window = False
        super().__init__(directory)

    def native_capture(self, name):
        image = super().native_capture(name)
        if name.startswith('00-startup'):
            self.second_window = True
        return image

    def make_ui(self):
        harness = self
        synthetic_ui = super().make_ui()

        class UI(synthetic_ui):
            def __init__(self, pid, window, bounds, trace):
                super().__init__(pid, window, bounds, trace)
                self.trace = trace
                self.preflight = lambda: {'CGPreflightPostEventAccess': True, 'CGPreflightScreenCaptureAccess': True}
                self.current_foreground_pid = lambda: self.pid

            def windows(self, pid):
                rows = [owned(self.window, owner_pid=pid)]
                if harness.second_window:
                    rows.append(owned(self.window+1, owner_pid=pid))
                return rows

            require_window = ordinary.MacOrdinaryUI.require_window
            require_target = base.MacMenuUI.require_target
            pin_for_input = ordinary.MacOrdinaryUI.pin_for_input

        return UI


class IndependentReview(unittest.TestCase):
    def test_late_same_pid_ambiguity_at_pin_must_be_rejected(self):
        rows, records, error = [owned(), owned(35)], [], None
        ui = controller(rows)
        ui.trace = lambda event, **details: records.append({'event': event, **copy.deepcopy(details)})
        with patch.object(ordinary, 'require_private_userdir'):
            try:
                ui.pin_for_input(capture())
            except RuntimeError as caught:
                error = caught
        summary = {'scope': 'Pure actual-method counterexample, native APIs mocked',
                   'selected_window': owned(), 'current_owned_visible_windows': rows,
                   'error': str(error) if error else None,
                   'input_geometry_pinned': ui.input_geometry_pinned,
                   'cg_event_post_attempts': ui.event_post_attempts, 'actions': records}
        (Path(__file__).parent/'zero-event-pin-counterexample.json').write_text(json.dumps(summary, indent=2)+'\n')
        self.assertIsNotNone(error, summary)
        self.assertFalse(ui.input_geometry_pinned)

    def test_late_same_pid_ambiguity_after_pin_must_be_rejected(self):
        ui = controller([owned(), owned(35)])
        ui.input_geometry_pinned, ui.event_post_attempts = True, 1
        with patch.object(ordinary, 'require_private_userdir'):
            with self.assertRaisesRegex(RuntimeError, 'window|geometry|ambig'):
                ui.require_target()

    def test_late_same_pid_ambiguity_cannot_reach_deploy(self):
        with tempfile.TemporaryDirectory() as temporary:
            harness = LateAmbiguity(Path(temporary).resolve() / 'synthetic')
            with patch.object(ordinary, 'require_private_userdir'):
                code, report = harness.execute()
            rows = [row for row in report['actions'] if row['event'] == 'owned_window_guard']
            summary = {'scope': 'Pure synthetic counterexample, never native evidence',
                       'code': code, 'deployed': harness.deployed,
                       'pinned': harness.active_ui.input_geometry_pinned,
                       'reported_pass': report['passed'],
                       'maximum_owned_visible_windows': max(len(row['observed_owned_layer_zero_windows']) for row in rows),
                       'selected_actions': [row for row in report['actions'] if row['event'] in
                                            ('startup_window_observation', 'startup_window_candidate',
                                             'owned_window_guard', 'input_geometry_pinned')]}
            (Path(__file__).parent / 'late-ambiguity-counterexample.json').write_text(json.dumps(summary, indent=2)+'\n')
            self.assertFalse(harness.deployed, summary)

    def test_actual_pin_rejects_foreign_window_mapping_identity_and_focus(self):
        for change in ('foreign', 'window', 'bounds', 'chrome', 'scale', 'splash', 'low', 'mixed', 'focus'):
            ui, pixels = controller(), capture()
            if change == 'foreign': pixels['owner_pid'] = 999
            elif change == 'window': pixels['window_id'] = 35
            elif change == 'bounds': pixels['bounds_points_including_chrome'][0] += 1
            elif change == 'chrome': pixels['scwindow_frame_points'][2] -= 1
            elif change == 'scale': pixels['point_pixel_scale'] = True
            elif change == 'splash': pixels['text'] = [dict(pixels['text'][0], text='GODOT')]
            elif change == 'low': pixels['text'][0]['confidence'] = .799999
            elif change == 'mixed': pixels['text'].append(dict(pixels['text'][0], text='FIELD SETTINGS'))
            else: ui.current_foreground_pid = lambda: 999
            with self.subTest(change=change), patch.object(ordinary, 'require_private_userdir'):
                with self.assertRaises(RuntimeError): ui.pin_for_input(pixels)
                self.assertFalse(ui.input_geometry_pinned)
                self.assertEqual(ui.event_post_attempts, 0)

    def test_post_barrier_releases_unposted_event_and_pin_never_repeats(self):
        ui, posts, releases = controller(), [], []
        ui.cf = types.SimpleNamespace(CFRelease=releases.append)
        ui.cg = types.SimpleNamespace(CGEventSetFlags=lambda *args: None,
                                      CGEventPost=lambda *args: posts.append(args))
        with self.assertRaises(RuntimeError): ui.post(77, 'synthetic-event')
        self.assertEqual((posts, releases, ui.event_post_attempts), ([], [77], 0))
        with patch.object(ordinary, 'require_private_userdir'):
            ui.pin_for_input(capture())
            with self.assertRaises(RuntimeError): ui.pin_for_input(capture())
            ui.post(88, 'synthetic-event')
            with self.assertRaises(RuntimeError): ui.pin_for_input(capture())
        self.assertEqual((posts, releases, ui.event_post_attempts), ([(0, 88)], [77, 88], 1))

    def test_every_later_geometry_dimension_and_disappearance_remain_strict(self):
        for change in ('x', 'y', 'width', 'height', 'id', 'missing', 'hidden', 'duplicate'):
            rows = [owned()]
            if change in ('x', 'y', 'width', 'height'):
                rows[0]['bounds_points_including_chrome'][('x', 'y', 'width', 'height').index(change)] += .501
            elif change == 'id': rows[0]['window_id'] = 35
            elif change == 'missing': rows.clear()
            elif change == 'hidden': rows[0]['onscreen'] = False
            else: rows.append(owned())
            ui = controller(rows)
            ui.input_geometry_pinned, ui.event_post_attempts = True, 1
            records = []
            ui.trace = lambda event, **details: records.append((event, copy.deepcopy(details)))
            with self.subTest(change=change), patch.object(ordinary, 'require_private_userdir'):
                with self.assertRaises(ordinary.OwnedWindowChanged): ui.require_window()
                self.assertEqual(records[-1][1]['observed_owned_layer_zero_windows'], rows)
                self.assertEqual(ui.bounds, [40, 32, 960, 568])

    def test_inherited_half_point_tolerance_remains_unchanged(self):
        row = owned()
        row['bounds_points_including_chrome'][0] += .5
        with patch.object(ordinary, 'require_private_userdir'):
            controller([row]).require_window()

    def test_owned_os_metadata_excludes_foreign_and_nonzero_layer_spoofs(self):
        values = [dict(kCGWindowOwnerPID=pid, kCGWindowLayer=layer, kCGWindowNumber=34,
                       kCGWindowBounds=dict(X=40, Y=32, Width=960, Height=568), kCGWindowIsOnscreen=True)
                  for pid, layer in ((999, 0), (123, 1), (123, 0))]
        self.assertEqual(base.MacReadOnly.windows.__module__, 'probe_macos_input')
        from probe_macos_input import owned_windows
        self.assertEqual(owned_windows(values, 123), [owned()])

    def test_late_ready_and_late_focus_full_driver_cannot_deploy(self):
        for fault in ('focus_late', 'focused_change', 'startup_foreign', 'startup_mapping', 'startup_helper_error'):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as temporary:
                harness = SyntheticController(Path(temporary).resolve() / 'synthetic', fault)
                code, report = harness.execute()
                self.assertEqual(code, 1)
                self.assertFalse(harness.deployed)
                self.assertEqual(report['cg_event_post_attempts'], 0)
                self.assertTrue(all(row['owned_group_gone'] for row in report['cleanup']))

    def test_late_menu_and_persistent_splash_do_not_extend_readiness(self):
        class LateMenu(SyntheticController):
            def native_capture(self, name):
                image = super().native_capture(name)
                if name.startswith('00-startup'): self.now += 60.001
                return image
        class MissingMenu(SyntheticController):
            def native_capture(self, name):
                image = super().native_capture(name)
                if name.startswith('00-startup'):
                    self.now += 1
                    image['text'] = [dict(image['text'][0], text='GODOT')]
                return image
        for case in (LateMenu, MissingMenu):
            with self.subTest(case=case.__name__), tempfile.TemporaryDirectory() as temporary:
                harness = case(Path(temporary).resolve()/'synthetic')
                code, report = harness.execute()
                self.assertEqual(code, 1)
                self.assertEqual(report['failure']['type'], 'TimeoutError')
                self.assertFalse(harness.deployed)
                self.assertEqual(harness.focus_calls, 0)
                self.assertEqual(report['cg_event_post_attempts'], 0)
                observations = [row for row in report['actions'] if row['event'] == 'startup_window_observation']
                self.assertLess(max(row['seconds'] for row in observations), 60)

    def test_gameplay_cleanup_budgets_and_capture_helper_bytes_unchanged(self):
        def previous(path):
            return subprocess.check_output(['git', 'show', 'bd9ac47:'+path], cwd=ROOT)
        current = (ROOT/'scripts/verify_macos_ordinary.py').read_bytes()
        old = previous('scripts/verify_macos_ordinary.py')
        boundary = b"            ui.click_label(menu, 'DEPLOY"
        self.assertEqual(current[current.index(boundary):], old[old.index(boundary):])
        self.assertEqual(driver.BUDGETS, {'total':300,'compile':60,'window':30,'focus':5,'menu':60,
                         'deploy':30,'live':60,'fire':5,'reload_start':5,'reload_complete':15,
                         'reload_frames':5,'field_menu':10,'return_menu':30,'close':20,'capture':25})
        for path in ('scripts/macos_native_input.py', 'scripts/verify_macos_menu.py', 'scripts/macos_window_capture.swift'):
            self.assertEqual((ROOT/path).read_bytes(), previous(path))
        self.assertEqual(subprocess.check_output(['git','diff','bd9ac47','0146497','--','game'],cwd=ROOT), b'')


if __name__ == '__main__':
    unittest.main(verbosity=2)
