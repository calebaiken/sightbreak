#!/usr/bin/env python3
"""Adversarial tests of matrix evidence gates, independent of Godot/SDKs."""
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

import validate_matrix as matrix


class MatrixGateTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)

    def check(self, body, timeout=20):
        return matrix.run_check('control', [sys.executable, '-c', body],
                                self.directory, os.environ.copy(), 'fixture-commit', timeout)

    def test_success_requires_clean_log_and_zero_exit(self):
        record = self.check('print("assertion control completed")')
        self.assertTrue(record['passed'])
        self.assertEqual(record['source_commit'], 'fixture-commit')
        self.assertEqual(record['exit'], 0)

    def test_ok_text_cannot_hide_nonzero_exit(self):
        record = self.check('print("OK"); raise SystemExit(7)')
        self.assertFalse(record['passed'])
        self.assertEqual(record['exit'], 7)

    def test_zero_exit_cannot_hide_engine_error_or_leak(self):
        record = self.check('print("WARNING: ObjectDB instances leaked at exit")')
        self.assertFalse(record['passed'])
        self.assertTrue(record['logged_errors'])
        self.assertEqual(record['exit'], 0)

    def test_timeout_is_retained_as_failure(self):
        record = self.check('import time; time.sleep(30)', timeout=0.2)
        self.assertFalse(record['passed'])
        self.assertIn('HARNESS_ERROR', (self.directory / record['log']).read_text())

    def descendant(self, *, wait=False, timeout=False, detached=False):
        started = self.directory / 'child-started'
        finished = self.directory / 'child-finished'
        child = ('from pathlib import Path; import os, time; '
                 'print("child raw output retained", flush=True); '
                 f'Path({str(started)!r}).write_text(str(os.getpid())); '
                 'time.sleep(.7); print("ERROR: late descendant output", flush=True); '
                 f'Path({str(finished)!r}).write_text("finished")')
        if wait:
            child = 'print("normally awaited child completed", flush=True)'
        options = ''
        if detached:
            options = (', creationflags=0x200' if os.name == 'nt'
                       else ', start_new_session=True')
        parent = ('from pathlib import Path; import subprocess, sys, time; '
                  f'p = subprocess.Popen([sys.executable, "-B", "-c", {child!r}]{options}); '
                  + ('p.wait(); ' if wait else
                     f'marker = Path({str(started)!r}); '
                     '\nwhile not marker.exists(): time.sleep(.005)\n')
                  + 'print("parent raw output retained", flush=True); '
                  + ('time.sleep(30)' if timeout else 'print("parent completed", flush=True)'))
        return self.check(parent, timeout=.4 if timeout else 20), started, finished

    def assert_descendant_stopped(self, record, started, finished):
        self.assertTrue(started.is_file())
        self.assertFalse(record['passed'])
        text = (self.directory / record['log']).read_bytes()
        self.assertIn(b'HARNESS_ERROR', text)
        time.sleep(.9)
        self.assertFalse(finished.exists(), 'descendant survived cleanup')
        self.assertEqual((self.directory / record['log']).read_bytes(), text,
                         'raw log changed after run_check returned')

    def test_zero_exit_with_surviving_descendant_fails_and_stops_late_output(self):
        record, started, finished = self.descendant()
        self.assertEqual(record['exit'], 0)
        self.assert_descendant_stopped(record, started, finished)

    def test_new_process_group_cannot_escape_cleanup(self):
        record, started, finished = self.descendant(detached=True)
        self.assertEqual(record['exit'], 0)
        self.assert_descendant_stopped(record, started, finished)

    def test_timeout_cleans_descendants_and_retains_raw_output(self):
        record, started, finished = self.descendant(timeout=True, detached=True)
        self.assert_descendant_stopped(record, started, finished)
        text = (self.directory / record['log']).read_text()
        self.assertIn('child raw output retained', text)
        self.assertIn('parent raw output retained', text)

    def test_normally_awaited_children_do_not_fail(self):
        record, _, _ = self.descendant(wait=True)
        self.assertTrue(record['passed'])

    def test_normally_awaited_nested_matrix_check_passes(self):
        nested = self.directory / 'nested'
        nested.mkdir()
        body = ('import os, sys; from pathlib import Path; '
                f'sys.path.insert(0, {str(matrix.ROOT / "scripts")!r}); '
                'from validate_matrix import run_check; '
                f'record = run_check("inner", [sys.executable, "-B", "-c", '
                f'\'print("nested child completed")\'], Path({str(nested)!r}), '
                'os.environ.copy(), "nested-fixture", 10); '
                'raise SystemExit(0 if record["passed"] else 1)')
        self.assertTrue(self.check(body)['passed'])

    @unittest.skipUnless(os.name == 'nt', 'Windows Job Object breakaway control')
    def test_windows_job_disallows_breakaway(self):
        body = ('import subprocess, sys\n'
                'try:\n'
                '    p = subprocess.Popen([sys.executable, "-B", "-c", "pass"], '
                'creationflags=0x01000000)\n'
                'except OSError:\n'
                '    print("Job Object blocked breakaway", flush=True)\n'
                'else:\n'
                '    p.wait()\n'
                '    raise SystemExit(9)\n')
        record = self.check(body)
        self.assertTrue(record['passed'])
        self.assertIn('blocked breakaway', (self.directory / record['log']).read_text())

    def test_existing_process_receipt_is_not_modified(self):
        path = self.directory / 'control.process.json'
        path.write_bytes(b'original process evidence\n')
        record = self.check('print("replacement")')
        self.assertFalse(record['passed'])
        self.assertEqual(path.read_bytes(), b'original process evidence\n')

    def test_process_cleanup_error_cannot_become_success(self):
        def cleanup_failure(*args, **kwargs):
            raise RuntimeError('fixture cleanup could not be verified')
        with patch.object(matrix, 'run_process', side_effect=cleanup_failure):
            record = self.check('print("not launched")')
        self.assertFalse(record['passed'])
        self.assertIn('cleanup could not be verified',
                      (self.directory / record['log']).read_text())

    def test_launch_failure_is_retained(self):
        record = matrix.run_check('missing', [str(self.directory / 'missing.exe')],
                                  self.directory, os.environ.copy(), 'fixture-commit')
        self.assertFalse(record['passed'])
        self.assertIn('HARNESS_ERROR', (self.directory / record['log']).read_text())

    def test_existing_raw_log_is_not_modified(self):
        path = self.directory / 'control.log'
        path.write_bytes(b'original failed attempt\n')
        with self.assertRaises(FileExistsError):
            self.check('print("replacement")')
        self.assertEqual(path.read_bytes(), b'original failed attempt\n')

    def test_dirty_source_refuses_to_launch_matrix(self):
        out = self.directory / 'matrix'
        with patch.object(sys, 'argv', ['validate_matrix.py', '--out', str(out)]), \
                patch.object(matrix, 'source', return_value={'source_dirty': True}), \
                patch.object(matrix, 'source_snapshot', return_value={'dirty': True}), \
                patch.object(matrix.subprocess, 'check_output', side_effect=['fixture\n', ' M scripts/validate_matrix.py\n']), \
                patch.object(matrix, 'run_check') as run:
            self.assertEqual(matrix.main(), 1)
        run.assert_not_called()
        report = json.loads((out / 'summary.json').read_text())
        self.assertFalse(report['checks'][0]['passed'])
        self.assertEqual(report['checks'][0]['name'], 'frozen-source-precondition')

    def test_existing_evidence_directory_refuses_to_run(self):
        (self.directory / 'earlier.log').write_bytes(b'retain failure')
        with patch.object(sys, 'argv', ['validate_matrix.py', '--out', str(self.directory)]), \
                patch.object(matrix, 'source') as snapshot:
            with self.assertRaises(FileExistsError):
                matrix.main()
        snapshot.assert_not_called()
        self.assertEqual((self.directory / 'earlier.log').read_bytes(), b'retain failure')

    def test_inventory_keeps_existing_rows_and_adds_maintained_python_units(self):
        out = self.directory / 'matrix'
        calls = []
        clean = {'dirty': False}
        def fake_check(label, command, directory, env, commit, timeout=600):
            calls.append((label, command))
            return {'name': label, 'passed': True, 'seconds': 0}
        with patch.object(sys, 'argv', ['validate_matrix.py', '--out', str(out)]), \
                patch.object(matrix, 'source', return_value=clean), \
                patch.object(matrix, 'source_snapshot', return_value=clean), \
                patch.object(matrix.subprocess, 'check_output', side_effect=['fixture\n', '', '']), \
                patch.object(matrix, 'godot_command', return_value=['fixture-native-not-executed']), \
                patch.object(matrix, 'godot_environment', side_effect=lambda env: env), \
                patch.object(matrix, 'is_windows', return_value=False), \
                patch('sys.stdout', new_callable=io.StringIO), \
                patch.object(matrix, 'run_check', side_effect=fake_check):
            self.assertEqual(matrix.main(), 0)
        commands = dict(calls)
        for label, script in [('source-identity-unit', 'test_source_identity.py'),
                              ('verifier-unit', 'test_verify_builds.py'),
                              ('matrix-process-unit', 'test_matrix_process.py'),
                              ('matrix-harness-unit', 'test_validate_matrix.py'),
                              ('network-harness-unit', 'test_godot_process.py')]:
            self.assertEqual(commands[label], [sys.executable, 'scripts/' + script])
        for label in ('network-soak', 'network-soak-ten', 'connection-lifecycle',
                      'build-manifest', 'worker-unit', 'reload-contact'):
            self.assertIn(label, commands)
        report = json.loads((out / 'summary.json').read_text())
        self.assertTrue(next(row for row in report['checks']
                             if row['name'] == 'frozen-source-identity')['passed'])

    def test_nested_leak_and_final_source_gates_are_not_bypassed(self):
        out = self.directory / 'matrix'
        initial = {'dirty': False, 'content_sha256': 'initial'}
        final = {'dirty': True, 'content_sha256': 'changed'}
        def fake_check(label, command, directory, env, commit, timeout=600):
            nested = directory / 'nested'
            nested.mkdir(exist_ok=True)
            (nested / 'client.log').write_text('WARNING: ObjectDB instances leaked at exit\n')
            return {'name': label, 'passed': True, 'seconds': 0}
        with patch.object(sys, 'argv', ['validate_matrix.py', '--out', str(out)]), \
                patch.object(matrix, 'source', side_effect=[initial, final]), \
                patch.object(matrix, 'source_snapshot', side_effect=[initial, final]), \
                patch.object(matrix.subprocess, 'check_output', side_effect=['fixture\n', '', ' M changed\n']), \
                patch.object(matrix, 'godot_command', return_value=['fixture-native-not-executed']), \
                patch.object(matrix, 'godot_environment', side_effect=lambda env: env), \
                patch.object(matrix, 'is_windows', return_value=False), \
                patch('sys.stdout', new_callable=io.StringIO), \
                patch.object(matrix, 'run_check', side_effect=fake_check):
            self.assertEqual(matrix.main(), 1)
        rows = {row['name']: row for row in json.loads((out / 'summary.json').read_text())['checks']}
        self.assertFalse(rows['nested-resource-cleanup']['passed'])
        self.assertFalse(rows['frozen-source-identity']['passed'])


if __name__ == '__main__':
    unittest.main()
