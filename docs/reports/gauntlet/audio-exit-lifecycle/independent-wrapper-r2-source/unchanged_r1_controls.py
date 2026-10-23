#!/usr/bin/env python3
"""Independent pure controls. Git is real; every engine process is a fake object."""
import hashlib
import json
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / 'scripts'))
import acquire_audio_lifecycle as subject
from test_acquire_audio_lifecycle import synthetic_suite  # Synthetic text fixture only.

OUT = Path(__file__).resolve().parent
RESULTS = {}
REAL_POPEN = subprocess.Popen


class Harness:
    def __init__(self, root, mode='clean'):
        self.root, self.mode, self.clock = root, mode, 0.0
        self.source, self.output, self.engine = root/'source', root/'attempt', root/'inert-engine'
        self.source.mkdir()
        self.engine.write_bytes(b'INERT SOURCE REVIEW DATA; NEVER EXECUTE')
        files = {'game/project.godot': 'config_version=5\n[application]\nconfig/name="SIGHTBREAK"\n',
                 'game/tests/audio_lifecycle_probe.gd': 'extends RefCounted\n',
                 'game/tests/input_mode_test.gd': 'extends SceneTree\n'}
        for name, text in files.items():
            path = self.source/name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
        for args in [('init', '-q'), ('add', '.'), ('-c', 'user.name=Source Critic', '-c',
                     'user.email=source-critic@example.invalid', 'commit', '-qm', 'pure fixture')]:
            subprocess.run(['git', *args], cwd=self.source, check=True)
        self.freeze = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=self.source, text=True).strip()
        self.active, self.labels, self.commands, self.signals = {}, [], [], []

    def sleep(self, amount):
        self.clock += amount

    def kill(self, pid, signum):
        self.signals.append((pid, signum.name))
        self.active.pop(pid, None)

    def popen(self, command, **kwargs):
        if command[0] == 'git':
            return REAL_POPEN(command, **kwargs)
        if command[0] != str(self.engine):
            raise AssertionError('All non-Git native execution is forbidden')
        label = Path(kwargs['stdout'].name).stem
        self.labels.append(label)
        self.commands.append(command)
        pid = 4000 + len(self.labels)
        self.active[pid] = dict(pid=pid, ppid=1, pgid=pid, sid=pid, start_ticks=pid+10,
                                state='R', comm='synthetic', exe='inert')
        process = SimpleNamespace(pid=pid, returncode=None)
        interrupted = False
        def poll():
            nonlocal interrupted
            if label == 'input-mode' and self.mode in ('interrupt', 'keyboard-interrupt') and not interrupted:
                interrupted = True
                raise (InterruptedError('synthetic SIGTERM handler') if self.mode == 'interrupt' else KeyboardInterrupt())
            if label == 'input-mode' and self.mode == 'timeout' and pid in self.active:
                return None
            self.active.pop(pid, None)
            process.returncode = -15 if self.mode == 'timeout' and label == 'input-mode' else 0
            return process.returncode
        process.poll = poll
        stream, project = kwargs['stdout'], self.output/'project'
        raw = ''
        if label == 'engine-version':
            raw = subject.toolchain.ENGINE+'\n'
        elif label == 'private-import':
            (project/'tests/audio_lifecycle_probe.gd.uid').write_text('uid://synthetic123\n')
            if self.mode == 'import-warning':
                raw = 'benign line\n'*5000+'WARNING: ObjectDB instances leaked at exit\n'
        elif label in ('before-input-mode', 'after-input-mode'):
            custom = json.loads(next(x.split('=', 1)[1] for x in (project/'project.godot').read_text().splitlines()
                                     if x.startswith('config/custom_user_dir_name=')))
            data_dir = self.output/'private-state/data'
            user = data_dir/custom
            user.mkdir(parents=True, exist_ok=True)
            payload = dict(project_path=str(project), data_dir=str(data_dir), user_data_dir=str(user),
                           driver='Dummy', uses_custom_user_dir=True, custom_user_dir=custom,
                           profile_exists=False, diagnostics_exist=False)
            if self.mode == 'wrong-after-driver' and label == 'after-input-mode':
                payload['driver'] = 'ALSA'
            Path(command[-1].removeprefix('--receipt=')).write_text(json.dumps(payload))
            if self.mode == 'late-suite-leak' and label == 'after-input-mode':
                with (self.output/'input-mode.log').open('a') as output:
                    output.write('WARNING: 2 ObjectDB instances were leaked at exit\n')
            if self.mode == 'late-import-leak' and label == 'after-input-mode':
                with (self.output/'private-import.log').open('a') as output:
                    output.write('WARNING: ObjectDB instances leaked at exit\n')
        elif label == 'input-mode':
            raw = synthetic_suite(leak=self.mode == 'leak')
            (self.output/'private-state/data/produced.txt').write_text('original produced private bytes\n')
        stream.write(raw.encode())
        return process

    def run(self, archive_fault=False):
        real_copy = shutil.copy2
        def copy(source, destination, *args, **kwargs):
            result = real_copy(source, destination, *args, **kwargs)
            if archive_fault and 'produced-private-state' in Path(destination).parts and Path(destination).name == 'produced.txt':
                Path(destination).write_text('corrupt archived bytes\n')
            return result
        with patch.object(subject.platform, 'system', return_value='Linux'), \
             patch.object(subject.subprocess, 'Popen', side_effect=self.popen), \
             patch.object(subject, 'proc_table', side_effect=lambda: dict(self.active)), \
             patch.object(subject.os, 'kill', side_effect=self.kill), \
             patch.object(subject.time, 'monotonic', side_effect=lambda: self.clock), \
             patch.object(subject.time, 'sleep', side_effect=self.sleep), \
             patch.object(subject.shutil, 'copy2', side_effect=copy):
            code = subject.acquire(self.source, self.freeze, self.engine, subject.sha(self.engine), self.output)
        report = json.loads((self.output/'overall.json').read_text())
        return code, report

    def save(self, name, report):
        target = OUT/name
        target.mkdir(exist_ok=True)
        for item in self.output.iterdir():
            if item.is_file(): shutil.copy2(item, target/item.name)
            elif item.name in ('generated-uids', 'produced-private-state'):
                shutil.copytree(item, target/item.name, dirs_exist_ok=True)
        (target/'independent-witness.json').write_text(json.dumps(report, indent=2, sort_keys=True)+'\n')
        RESULTS[name] = report


class IndependentControls(unittest.TestCase):
    def test_positive_true_phases_full_flow_and_exact_argv(self):
        with tempfile.TemporaryDirectory() as tmp:
            h = Harness(Path(tmp))
            code, r = h.run()
            self.assertEqual(code, 0)
            self.assertTrue(r['acquisition_integrity'])
            self.assertEqual(h.labels, ['engine-version', 'private-import', 'before-input-mode', 'input-mode', 'after-input-mode'])
            self.assertEqual(h.commands[3][3:], ['--headless', '--verbose', '--script', 'res://tests/input_mode_test.gd', '--', '--audio-lifecycle-diagnostic'])
            self.assertTrue(all('--audio-driver' not in c for c in h.commands))
            self.assertEqual(r['native_before']['driver'], 'Dummy')
            self.assertEqual(r['native_after']['driver'], 'Dummy')
            self.assertTrue(all(p['cleanup_complete'] and p['root_identity'] for p in r['phases']))
            self.assertFalse(r['original_leak_blocker_resolved'])
            h.save('positive-clean', r)

    def test_positive_strict_leak_fails_exit_zero_suite(self):
        with tempfile.TemporaryDirectory() as tmp:
            h = Harness(Path(tmp), 'leak'); code, r = h.run()
            self.assertEqual(code, 1); self.assertTrue(r['acquisition_integrity'])
            self.assertFalse(r['sample_strict_clean']); self.assertEqual(r['phases'][3]['exit'], 0)
            h.save('positive-leak-rejection', r)

    def test_full_import_warning_scan_skips_suite(self):
        with tempfile.TemporaryDirectory() as tmp:
            h = Harness(Path(tmp), 'import-warning'); code, r = h.run()
            self.assertEqual(code, 1); self.assertEqual(h.labels, ['engine-version', 'private-import'])
            self.assertFalse(r['phases'][1]['clean_log'])
            h.save('positive-import-rejection', r)

    def test_after_identity_mismatch_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            h = Harness(Path(tmp), 'wrong-after-driver'); code, r = h.run()
            self.assertEqual(code, 1); self.assertFalse(r['acquisition_integrity'])
            self.assertIn('identity differs', r['error']['message'])

    def test_true_phase_timeout_retains_cleanup_and_finalization(self):
        with tempfile.TemporaryDirectory() as tmp:
            h = Harness(Path(tmp), 'timeout'); code, r = h.run()
            self.assertEqual(code, 1)
            self.assertEqual(h.labels[-1], 'input-mode')
            self.assertTrue(r['phases'][-1]['timed_out'])
            self.assertTrue(r['phases'][-1]['cleanup_complete'])
            self.assertTrue(h.signals)
            self.assertLessEqual(r['whole_wall_seconds'], 240)
            h.save('positive-timeout-rejection', r)

    def test_signal_handler_and_keyboard_exceptions_cleanup_and_receipt(self):
        for mode, kind in [('interrupt', 'InterruptedError'), ('keyboard-interrupt', 'KeyboardInterrupt')]:
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as tmp:
                h = Harness(Path(tmp), mode); code, r = h.run()
                self.assertEqual(code, 1)
                self.assertEqual(r['error']['type'], kind)
                self.assertEqual(r['phases'][-1]['error']['type'], kind)
                self.assertTrue(r['phases'][-1]['cleanup_complete'])
                self.assertTrue(r['private_project_removed'])
                h.save('positive-'+mode+'-rejection', r)

    def test_one_shot_reservation_refuses_second_attempt(self):
        with tempfile.TemporaryDirectory() as tmp:
            h = Harness(Path(tmp)); self.assertEqual(h.run()[0], 0)
            original = (h.output/'overall.json').read_bytes()
            with patch.object(subject.subprocess, 'Popen', side_effect=AssertionError('Forbidden second launch')):
                with self.assertRaises(FileExistsError):
                    subject.acquire(h.source, h.freeze, h.engine, subject.sha(h.engine), h.output)
            self.assertEqual((h.output/'overall.json').read_bytes(), original)

    def test_exact_reserve_boundary_refuses_and_next_float_allows_launch(self):
        for start, expected_spawn in [(227.0, False), (226.999, True)]:
            with self.subTest(start=start), tempfile.TemporaryDirectory() as tmp:
                h = Harness(Path(tmp)); h.output.mkdir(); h.clock = start
                phase = subject.Phases(h.output, h.engine, subject.sha(h.engine), 240, {})
                with patch.object(subject.subprocess, 'Popen', side_effect=h.popen), \
                     patch.object(subject, 'proc_table', side_effect=lambda: dict(h.active)), \
                     patch.object(subject.time, 'monotonic', side_effect=lambda: h.clock):
                    if expected_spawn:
                        r = phase.execute('engine-version', ['--headless', '--version'], 30)
                        self.assertAlmostEqual(r['timeout_seconds'], .001)
                        self.assertTrue(r['cleanup_complete'])
                    else:
                        with self.assertRaises(TimeoutError): phase.execute('engine-version', ['--headless', '--version'], 30)
                self.assertEqual(bool(h.labels), expected_spawn)

    def test_pid_reuse_never_signals_observed_different_start(self):
        old = dict(pid=10, start_ticks=100)
        with patch.object(subject, 'proc_table', return_value={10: dict(pid=10, start_ticks=101)}), \
             patch.object(subject.os, 'kill') as killed:
            self.assertFalse(subject.signal_identity(old, signal.SIGKILL)); killed.assert_not_called()

    def test_observed_escaped_child_survivor_and_reuse_boundaries(self):
        for mode in ['escaped', 'stubborn', 'reused']:
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as tmp:
                h = Harness(Path(tmp)); h.output.mkdir()
                root = dict(pid=10, ppid=1, pgid=10, sid=10, start_ticks=100, state='R', comm='fake', exe='fake')
                child = dict(pid=11, ppid=10, pgid=11, sid=11, start_ticks=101, state='R', comm='fake', exe='fake')
                h.active = {10: root, 11: child}
                process = SimpleNamespace(pid=10, returncode=None)
                def poll():
                    h.active.pop(10, None); process.returncode = 0
                    if mode == 'reused':
                        h.active[11] = dict(child, ppid=1, pgid=99, sid=99, start_ticks=102)
                    return 0
                process.poll = poll
                def kill(pid, signum):
                    h.signals.append((pid, signum.name))
                    if mode != 'stubborn': h.active.pop(pid, None)
                phase = subject.Phases(h.output, h.engine, subject.sha(h.engine), 240, {})
                with patch.object(subject.subprocess, 'Popen', return_value=process), \
                     patch.object(subject, 'proc_table', side_effect=lambda: dict(h.active)), \
                     patch.object(subject.os, 'kill', side_effect=kill), \
                     patch.object(subject.time, 'monotonic', side_effect=lambda: h.clock), \
                     patch.object(subject.time, 'sleep', side_effect=h.sleep):
                    if mode == 'stubborn':
                        with self.assertRaisesRegex(RuntimeError, 'cleanup'): phase.execute('child-boundary', [], 30)
                    else: phase.execute('child-boundary', [], 30)
                receipt = json.loads((h.output/'child-boundary.receipt.json').read_text())
                self.assertEqual({x['pid'] for x in receipt['observed']}, {10, 11})
                if mode == 'reused': self.assertEqual(h.signals, [])
                elif mode == 'escaped': self.assertEqual(h.signals, [(11, 'SIGTERM')])
                else:
                    self.assertEqual(h.signals, [(11, 'SIGTERM'), (11, 'SIGKILL')])
                    self.assertFalse(receipt['cleanup_complete'])
                    self.assertEqual(receipt['terminal_observed'][0]['start_ticks'], 101)
                    self.assertLessEqual(receipt['cleanup_wall_seconds'], 5)

    def test_real_git_blob_guard_refuses_changed_and_missing_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            h = Harness(Path(tmp))
            self.assertEqual(len(subject.tracked(h.source, h.freeze, subject.time.monotonic()+20)), 3)
            file = h.source/'game/tests/input_mode_test.gd'
            file.write_text('changed')
            with self.assertRaisesRegex(RuntimeError, 'not clean'): subject.tracked(h.source, h.freeze, subject.time.monotonic()+20)
            file.unlink()
            with self.assertRaisesRegex(RuntimeError, 'not clean'): subject.tracked(h.source, h.freeze, subject.time.monotonic()+20)

    def test_counterexample_current_raw_suite_leak_must_not_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            h = Harness(Path(tmp), 'late-suite-leak'); code, r = h.run()
            analysis = json.loads((h.output/'analysis.json').read_text())
            r['independent_current_suite_sha256'] = subject.sha(h.output/'input-mode.log')
            r['independent_analysis_strict_raw_log_failed'] = analysis['strict_raw_log_failed']
            h.save('counterexample-late-suite-leak', r)
            self.assertTrue(analysis['strict_raw_log_failed'])
            self.assertNotEqual(r['phases'][3]['log_sha256'], r['independent_current_suite_sha256'])
            self.assertEqual(code, 1, 'Current retained raw suite contains strict leak but wrapper returned success')

    def test_counterexample_current_raw_import_leak_must_not_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            h = Harness(Path(tmp), 'late-import-leak'); code, r = h.run()
            r['independent_current_import_sha256'] = subject.sha(h.output/'private-import.log')
            r['independent_current_import_failed'] = subject.failed((h.output/'private-import.log').read_text())
            h.save('counterexample-late-import-leak', r)
            self.assertTrue(r['independent_current_import_failed'])
            self.assertNotEqual(r['phases'][1]['log_sha256'], r['independent_current_import_sha256'])
            self.assertEqual(code, 1, 'Current retained raw import contains strict leak but wrapper returned success')

    def test_counterexample_archive_bytes_must_match_final_inventory(self):
        with tempfile.TemporaryDirectory() as tmp:
            h = Harness(Path(tmp)); code, r = h.run(archive_fault=True)
            original = json.loads((h.output/'private-state-final.json').read_text())
            archived = subject.sha(h.output/'produced-private-state/data/produced.txt')
            r['independent_archive_original_sha256'] = original['data/produced.txt']
            r['independent_archive_actual_sha256'] = archived
            h.save('counterexample-corrupt-archive', r)
            self.assertNotEqual(original['data/produced.txt'], archived)
            self.assertTrue(r['private_state_removed'])
            self.assertEqual(code, 1, 'Corrupted archive accepted and original private state removed')


if __name__ == '__main__':
    result = unittest.main(exit=False, verbosity=2).result
    (OUT/'counterexample-summary.json').write_text(json.dumps(RESULTS, indent=2, sort_keys=True)+'\n')
    raise SystemExit(not result.wasSuccessful())
