#!/usr/bin/env python3
"""Linux-safe controller gates; no native event, engine or OCR execution."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import macos_native_input as adapter
from probe_macos_input import NativePrerequisiteBlocked
import verify_macos_menu as driver


def capture_fixture():
    return {'passed': True, 'scope': 'OS window screenshot from ScreenCaptureKit; read-only helper',
            'permissions': {'CGPreflightScreenCaptureAccess': True, 'CGPreflightPostEventAccess': True},
            'owner_pid': 123, 'window_id': 34, 'bounds_points_including_chrome': [40, 32, 960, 568],
            'scwindow_frame_points': [40, 32, 960, 568], 'filter_content_rect_points': [0, 0, 960, 568],
            'point_pixel_scale': 2, 'image_dimensions': [1920, 1136],
            'text': [{'text': 'TACTICAL OPERATIONS', 'confidence': .99},
                     {'text': 'SETTINGS', 'confidence': .99, 'box_normalized_bottom_left': [.1, .2, .2, .05]}]}


class MenuControls(unittest.TestCase):
    def test_retina_and_titlebar_use_one_window_coordinate_space(self):
        capture = capture_fixture()
        x, y = adapter.settings_point(capture)
        self.assertAlmostEqual(x, 232)
        self.assertAlmostEqual(y, 472.2)
        capture['point_pixel_scale'], capture['image_dimensions'] = 1, [960, 568]
        self.assertEqual(adapter.settings_point(capture), (x, y))

    def test_unknown_chrome_or_backing_scale_never_authorizes_pointer(self):
        variants = [('scwindow_frame_points', [40, 60, 960, 540]),
                    ('filter_content_rect_points', [0, 0, 960, 540]),
                    ('image_dimensions', [960, 568]), ('point_pixel_scale', True),
                    ('point_pixel_scale', float('nan')), ('passed', False), ('permissions', {})]
        for name, value in variants:
            with self.subTest(name=name):
                capture = capture_fixture()
                capture[name] = value
                with self.assertRaises(RuntimeError):
                    adapter.settings_point(capture)

    def test_target_requires_unique_exact_confident_in_bounds_text(self):
        for change in ('duplicate', 'partial', 'confidence', 'outside', 'nonfinite'):
            capture = capture_fixture()
            entry = capture['text'][1]
            if change == 'duplicate':
                capture['text'].append(copy.deepcopy(entry))
            elif change == 'partial':
                entry['text'] = 'FIELD SETTINGS'
            elif change == 'confidence':
                entry['confidence'] = .79
            elif change == 'outside':
                entry['box_normalized_bottom_left'] = [.9, .2, .2, .1]
            else:
                entry['box_normalized_bottom_left'][0] = float('nan')
            with self.subTest(change=change), self.assertRaises(RuntimeError):
                adapter.settings_point(capture)

    def test_screen_confirmation_requires_both_menu_and_settings_outcomes(self):
        menu = capture_fixture()
        driver.require_screen(menu, 'menu')
        with self.assertRaises(RuntimeError):
            driver.require_screen(menu, 'settings')
        settings = capture_fixture()
        settings['text'] = [{'text': 'FIELD SETTINGS', 'confidence': .95}]
        driver.require_screen(settings, 'settings')
        with self.assertRaises(RuntimeError):
            driver.require_screen(settings, 'menu')

    def test_prior_preflight_must_match_source_artifact_permissions_and_cleanup(self):
        identity = {'source_commit': 'current', 'source_game_tree': 'game',
                    'source_content_sha256': 'content', 'source_validation_sha256': 'validation'}
        manifest = {**identity, 'artifact': {'sha256': 'executable'}}
        receipt = {'status': 'READY_FOR_INPUT_ATTEMPT', 'source': identity, 'artifact_source': manifest,
                   'executable_sha256': 'executable', 'source_unchanged': True, 'normal_exit_code': 0,
                   'cleanup': {'owned_group_gone': True}, 'profile_entries_unchanged': True,
                   'permissions': {'CGPreflightPostEventAccess': True, 'CGPreflightScreenCaptureAccess': True},
                   'window_observations': [{'windows': [{'onscreen': True}]}]}
        driver.require_preflight(receipt, identity, manifest)
        for field, value in [('status', 'FAILED'), ('source', {}), ('artifact_source', {}),
                             ('executable_sha256', 'different'), ('source_unchanged', False),
                             ('normal_exit_code', 1), ('cleanup', {}), ('profile_entries_unchanged', False),
                             ('permissions', {}), ('window_observations', [])]:
            bad = copy.deepcopy(receipt)
            bad[field] = value
            with self.subTest(field=field), self.assertRaises(NativePrerequisiteBlocked):
                driver.require_preflight(bad, identity, manifest)

    def fake_ui(self):
        ui = object.__new__(adapter.MacMenuUI)
        ui.pid, ui.window, ui.bounds, ui.held = 123, 34, [40, 32, 960, 568], set()
        ui.preflight = lambda: {'CGPreflightPostEventAccess': True, 'CGPreflightScreenCaptureAccess': True}
        ui.windows = lambda pid: [{'window_id': 34, 'onscreen': True, 'bounds_points_including_chrome': [40, 32, 960, 568]}]
        ui.foreground_pid = lambda: 123
        return ui

    def test_wrong_focus_geometry_permission_or_profile_prevents_down_event(self):
        for condition in ('focus', 'geometry', 'permission', 'profile'):
            ui = self.fake_ui()
            if condition == 'focus':
                ui.foreground_pid = lambda: 999
            elif condition == 'geometry':
                ui.bounds = [40, 32, 800, 568]
            elif condition == 'permission':
                ui.preflight = lambda: {'CGPreflightPostEventAccess': False, 'CGPreflightScreenCaptureAccess': True}
            with (self.subTest(condition=condition),
                  patch.object(adapter, 'require_absent_profile', side_effect=NativePrerequisiteBlocked('existing') if condition == 'profile' else None),
                  patch.object(ui, 'post') as post):
                with self.assertRaises(RuntimeError):
                    ui.escape(True)
                post.assert_not_called()
                self.assertEqual(ui.held, set())

    def test_cleanup_releases_only_recorded_owned_controls(self):
        ui = self.fake_ui()
        ui.held, ui.last_pointer_point = {'escape', 'lmb'}, [100, 200]
        released = []
        def release(name):
            ui.held.discard(name)
            released.append(name)
        ui.escape = lambda down: release('escape')
        ui.button = lambda down, point: release('lmb')
        ui.diagnostics = lambda: {'lmb_down': False, 'escape_down': False}
        self.assertEqual(ui.release_owned()['held_after_release'], [])
        self.assertEqual(released, ['escape', 'lmb'])
        # Unknown externally held Escape is observed and never released.
        released.clear()
        ui.diagnostics = lambda: {'lmb_down': False, 'escape_down': True}
        ui.release_owned()
        self.assertEqual(released, [])

    def test_actual_down_boundary_rejects_newly_dirty_os_controls(self):
        for control in ('lmb', 'escape'):
            ui = self.fake_ui()
            ui.require_target = lambda: None
            ui.diagnostics = lambda: {'foreground_pid': 123, 'lmb_down': True, 'escape_down': False}
            with self.subTest(control=control), patch.object(ui, 'post') as post:
                with self.assertRaisesRegex(RuntimeError, 'not neutral'):
                    if control == 'lmb':
                        ui.button(True, [100, 200])
                    else:
                        ui.escape(True)
                post.assert_not_called()
                self.assertEqual(ui.held, set())

    def test_fresh_neutral_observation_cannot_ignore_lost_foreground(self):
        ui = self.fake_ui()
        ui.require_target = lambda: None
        ui.diagnostics = lambda: {'foreground_pid': 999, 'lmb_down': False, 'escape_down': False}
        with patch.object(ui, 'post') as post:
            with self.assertRaisesRegex(RuntimeError, 'Foreground process changed'):
                ui.escape(True)
            post.assert_not_called()
            self.assertEqual(ui.held, set())

    def test_failure_cleanup_tries_public_quit_before_owned_group_fallback(self):
        class Client:
            returncode = None
            def poll(self):
                return self.returncode
            def wait(self, timeout):
                self.returncode = 0
        client = Client()
        ui = self.fake_ui()
        with patch.object(ui, 'request_close', return_value=True) as request:
            report = driver.ordinary_failure_close(ui, client)
            self.assertTrue(report['request_accepted'])
            self.assertEqual(report['exit_code'], 0)
            driver.ordinary_failure_close(ui, client)
            request.assert_called_once()

    def test_non_mac_host_never_launches_helper_or_client(self):
        with tempfile.TemporaryDirectory() as temporary:
            with patch.object(driver, 'MacReadOnly', side_effect=RuntimeError('requires ARM Mac')), patch.object(driver.subprocess, 'Popen') as launch:
                self.assertEqual(driver.run(Path(temporary) / 'evidence', Path(temporary) / 'missing.json'), 1)
                launch.assert_not_called()
            report = json.loads((Path(temporary) / 'evidence/results.json').read_text())
            self.assertFalse(report['passed'])
            self.assertEqual(report['captures'], [])


if __name__ == '__main__':
    unittest.main()
