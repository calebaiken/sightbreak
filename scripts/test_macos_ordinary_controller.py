#!/usr/bin/env python3
"""Mock the complete controller to falsify gates; these are never native receipts."""
from contextlib import ExitStack
import copy
import io
import json
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch

import verify_macos_ordinary as driver
from test_macos_ordinary import capture, hud_capture, initial, state


class SyntheticController:
    """All processes, permissions, screenshots and authority samples are mocked."""
    def __init__(self, directory, fault=None):
        self.directory, self.fault = Path(directory), fault
        self.now, self.wall, self.frames, self.tick, self.elapsed = 0., 100, 20, 5, .1
        self.deployed, self.paused, self.reload_mode, self.shots = False, False, 'idle', 0
        self.ammo, self.reserve, self.reload_elapsed = 15, 60, None
        self.reads, self.next_pid, self.client = 0, 9000, None
        self.default_reads, self.source_reads = 0, 0
        self.identity = {'source_commit': 'synthetic', 'source_game_tree': 'synthetic-game',
                         'source_content_sha256': 'synthetic-content', 'source_validation_sha256': 'synthetic-tools',
                         'source_dirty': False, 'source_game_dirty': False}
        self.default = {'directory_exists': False, 'directories': [], 'files': {}}
        self.ui = self.make_ui()

    def source(self):
        self.source_reads += 1
        return dict(self.identity, source_commit='changed') if self.fault == 'source' and self.source_reads > 1 else self.identity

    def default_inventory(self):
        self.default_reads += 1
        if self.fault == 'default' and self.default_reads > 1:
            return {'directory_exists': True, 'directories': [], 'files': {'unexpected.cache': {}}}
        return copy.deepcopy(self.default)

    def snapshot(self, _path):
        self.reads += 1
        if self.fault != 'stale' or not self.shots:
            self.wall += 1
        if self.fault != 'frames' and not (self.fault == 'reload_frames' and self.reload_mode == 'done'):
            self.frames += 1
        if not self.paused:
            self.tick += 1
            self.elapsed += 2
        sample = state()
        sample.update(wall_msec=self.wall, drawn_frames=self.frames, simulation_tick=self.tick, elapsed=self.elapsed)
        sample['phase'] = 'buy' if self.reads == 1 else 'live'
        sample['local_actor'].update(ammo=self.ammo, reserve=self.reserve)
        sample['ui']['paused'] = self.paused
        if self.reload_mode == 'started':
            sample['local_actor']['reload'] = 0 if self.fault == 'reload_start' else 1.3
            self.reload_elapsed = sample['elapsed']
        if self.reload_mode == 'done' and self.fault == 'reload_early':
            sample['elapsed'] = self.reload_elapsed+.1
        if self.fault == 'dead' and self.shots and any(path.name == '05-after-fire.json' for path in self.directory.glob('*.json')):
            sample['local_actor']['alive'] = False
        return sample

    def native_capture(self, name):
        if name.startswith(('05-', '06-')):
            image = hud_capture()
            image['text'][-1]['text'] = f'SIDEARM {self.ammo} / {self.reserve}'
            if self.fault == 'hud':
                image['text'][-1]['text'] = 'SIDEARM 01 / 99'
        elif name.startswith('07-'):
            image = capture()
            image['text'] = [dict(image['text'][0], text='FIELD MENU'), dict(image['text'][1], text='LEAVE MATCH')]
        else:
            image = capture()
        image['owner_pid'] = self.client.pid
        image['window_id'] = 34
        image.update(input_events_posted=0, permission_requests_made=0)
        return image

    def popen(self, arguments, **kwargs):
        harness = self
        self.next_pid += 1
        is_client = not any(flag in arguments for flag in ('--pid', '-parse-as-library'))
        class Process:
            pid = harness.next_pid
            returncode = None
            def poll(process):
                return process.returncode
            def wait(process, timeout):
                if not is_client:
                    if harness.fault == 'helper_deadline' and '-parse-as-library' in arguments:
                        harness.now += 61
                    process.returncode = 0
                return process.returncode
        process = Process()
        if is_client:
            self.client = process
            trace_directory = Path(next(arg.split('=', 1)[1] for arg in arguments if arg.startswith('--offline-trace-dir=')))
            trace_directory.mkdir()
            (trace_directory / 'events.jsonl').write_text(json.dumps(initial())+'\n')
            if self.fault == 'leak':
                kwargs['stdout'].write('ObjectDB instances leaked at exit\n')
        elif '--pid' in arguments:
            receipt = Path(arguments[arguments.index('--report')+1])
            receipt.write_text(json.dumps(self.native_capture(receipt.stem)))
        return process

    def make_ui(self):
        harness = self
        class UI:
            event_post_attempts = 0
            held = set()
            def __init__(self, pid, window, bounds, trace):
                self.pid, self.window, self.bounds = pid, window, bounds
            def require_target(self): pass
            def require_window(self): pass
            def focus_state(self): return {'foreground_pid': self.pid}
            def diagnostics(self):
                return {'foreground_pid': self.pid, 'lmb_down': False, 'escape_down': False, 'reload_down': False}
            def neutral(self): pass
            def focus(self): pass
            def observed_state(self, control, down, **kwargs):
                if harness.fault == 'fire_ack_delay' and control == 'lmb' and down:
                    harness.now += 1.01
                if harness.fault == 'fire_release_delay' and control == 'lmb' and not down:
                    harness.now += .36
                if harness.fault == 'reload_release_delay' and control == 'reload' and not down:
                    harness.now += 15.01
            def click_label(self, image, label):
                if label.startswith('DEPLOY'):
                    harness.deployed = True
            def fire_button(self, down):
                if not down:
                    harness.shots += 1
                    if harness.fault != 'depletion':
                        harness.ammo -= 1
            def reload_key(self, down):
                if down:
                    harness.reload_mode = 'started'
                else:
                    harness.reload_mode = 'done'
                    harness.reserve -= 15-harness.ammo
                    harness.ammo = 15
            def tap_escape(self): harness.paused = True
            def release_owned(self):
                return {'held_after_release': [], 'errors': [], 'native_state': self.diagnostics()}
            def request_close(self):
                if harness.fault == 'close': return False
                harness.client.returncode = 0
                return True
            def close(self): pass
        return UI

    def execute(self):
        api = types.SimpleNamespace(preflight=lambda: {'CGPreflightPostEventAccess': True, 'CGPreflightScreenCaptureAccess': True},
            windows=lambda pid: [{'owner_pid': pid, 'onscreen': True, 'window_id': 34,
                                  'bounds_points_including_chrome': [40, 32, 960, 568]}])
        manifest = {**self.identity, 'artifact': {'sha256': 'synthetic-hash'}}
        preflight = self.directory.parent / 'synthetic-preflight.json'
        preflight.write_text('{}')
        staged = {'staged': str(self.directory / 'native/SIGHTBREAK.app'), 'executable_sha256': 'synthetic-hash'}
        def reap(process):
            return {'pid': process.pid, 'exit_code': process.returncode, 'owned_group_gone': True,
                    'signals_sent': ['SIGTERM'] if self.fault == 'cleanup' else []}
        def payload(receipt):
            if self.fault == 'payload':
                raise RuntimeError('synthetic payload mutation')
        with ExitStack() as stack:
            patches = [(driver, 'MacReadOnly', lambda: api), (driver, 'source', self.source),
                       (driver, 'clean', lambda value: None), (driver, 'validate_record', lambda *args: manifest),
                       (driver, 'require_preflight', lambda *args: None), (driver, 'account_home', lambda: self.directory.parent / 'account'),
                       (driver, 'default_inventory', self.default_inventory), (driver, 'require_absent_profile', lambda: None),
                       (driver, 'inventory', lambda *args: copy.deepcopy(self.default)),
                       (driver, 'stage_app', lambda *args: staged), (driver, 'verify_staged_app', payload),
                       (driver, 'require_private_userdir', lambda *args: {'scope': 'synthetic only'}),
                       (driver, 'MacOrdinaryUI', self.ui), (driver, 'digest', lambda *args: 'synthetic-hash'),
                       (driver, 'read_observation_json', self.snapshot), (driver, 'reap', reap),
                       (driver.toolchain, 'verify_engine', lambda: {'scope': 'synthetic only'}),
                       (driver.subprocess, 'Popen', self.popen), (driver.time, 'monotonic', lambda: self.now),
                       (driver.time, 'sleep', lambda seconds: setattr(self, 'now', self.now+seconds))]
            for target, attribute, replacement in patches:
                stack.enter_context(patch.object(target, attribute, replacement))
            stack.enter_context(patch('sys.stdout', new_callable=io.StringIO))
            status = driver.run(self.directory, preflight)
        return status, json.loads((self.directory / 'results.json').read_text())


class ControllerFalsifiers(unittest.TestCase):
    def test_complete_synthetic_schedule_exercises_all_acceptance_stages(self):
        with tempfile.TemporaryDirectory() as temporary:
            harness = SyntheticController(Path(temporary).resolve(strict=True) / 'synthetic')
            code, report = harness.execute()
        self.assertEqual(code, 0)
        self.assertTrue(report['passed'])
        self.assertEqual(report['status'], 'PASS_ORDINARY_MAC_COMPONENT_ONLY')
        self.assertEqual(report['native_reload']['completed']['local_actor']['reserve'], 58)
        self.assertEqual([row['name'] for row in report['living_hud_captures']], ['05-after-fire', '06-after-reload'])
        self.assertTrue(report['source_unchanged'])
        self.assertTrue(report['default_user_directory_unchanged'])

    def test_stale_samples_no_ammo_effect_or_missing_drawn_frames_fail(self):
        for fault in ('stale', 'depletion', 'frames', 'reload_frames'):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as temporary:
                code, report = SyntheticController(Path(temporary).resolve(strict=True) / 'synthetic', fault).execute()
                self.assertEqual(code, 1)
                self.assertFalse(report['passed'])
                self.assertEqual(report['failure']['type'], 'TimeoutError')

    def test_unobserved_reload_or_early_transfer_never_pass(self):
        for fault in ('reload_start', 'reload_early'):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as temporary:
                code, report = SyntheticController(Path(temporary).resolve(strict=True) / 'synthetic', fault).execute()
                self.assertEqual(code, 1)
                self.assertFalse(report['passed'])
                self.assertIn('failure', report)

    def test_dead_or_mismatched_native_hud_never_pass(self):
        for fault in ('dead', 'hud'):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as temporary:
                code, report = SyntheticController(Path(temporary).resolve(strict=True) / 'synthetic', fault).execute()
                self.assertEqual(code, 1)
                self.assertFalse(report['passed'])

    def test_zero_exit_after_helper_stage_deadline_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            code, report = SyntheticController(Path(temporary).resolve(strict=True) / 'synthetic', 'helper_deadline').execute()
        self.assertEqual(code, 1)
        self.assertEqual(report['failure']['type'], 'TimeoutError')
        self.assertFalse(report['passed'])
        self.assertEqual(report['captures'], [])

    def test_delayed_os_acknowledgement_cannot_extend_original_input_slots(self):
        for fault in ('fire_ack_delay', 'fire_release_delay', 'reload_release_delay'):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as temporary:
                code, report = SyntheticController(Path(temporary).resolve(strict=True) / 'synthetic', fault).execute()
                self.assertEqual(code, 1)
                self.assertEqual(report['failure']['type'], 'TimeoutError')
                self.assertFalse(report['passed'])

    def test_finalization_checks_cannot_be_replaced_by_completed_gameplay(self):
        for fault in ('cleanup', 'payload', 'source', 'default', 'leak', 'close'):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as temporary:
                code, report = SyntheticController(Path(temporary).resolve(strict=True) / 'synthetic', fault).execute()
                self.assertEqual(code, 1)
                self.assertFalse(report['passed'])
                self.assertTrue(report.get('failure') or report.get('finalization_failures'))


if __name__ == '__main__':
    unittest.main()
