#!/usr/bin/env python3
"""Adversarial tests of matrix evidence gates, independent of Godot/SDKs."""
import json
import os
from pathlib import Path
import sys
import tempfile
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


if __name__ == '__main__':
    unittest.main()
