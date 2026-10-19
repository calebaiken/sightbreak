#!/usr/bin/env python3
"""Actual CPython timeout/receipt controls, not native exported-client passes."""
import contextlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

import export_flow
from verify_offline_export import ocr_text


class FlowWatchdogTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.output = self.root / 'evidence'
        self.worker = self.root / 'synthetic.py'

    def run_worker(self, body, timeout=5):
        self.worker.write_text('import json, sys, time\nfrom pathlib import Path\n'
                               'out = Path(sys.argv[sys.argv.index("--output") + 1])\n'
                               'print("synthetic CPython worker", flush=True)\n' + body, encoding='utf-8')
        with contextlib.redirect_stdout(io.StringIO()):
            code = export_flow.supervise(self.worker, ['--output', str(self.output)], self.output, timeout)
        return code, json.loads((self.output / 'results.json').read_text())

    def test_actual_zero_exit_and_passing_receipt(self):
        code, result = self.run_worker('(out / "results.json").write_text(json.dumps({"passed": True}))\n')
        self.assertEqual(code, 0)
        self.assertTrue(result['passed'])
        self.assertTrue(result['watchdog']['passed'])
        self.assertIn('synthetic CPython', (self.output / 'watchdog.log').read_text())

    def test_hard_deadline_retains_partial_output_and_failed_receipt(self):
        started = time.monotonic()
        code, result = self.run_worker('print("stalled OCR control", flush=True)\ntime.sleep(30)\n', .25)
        self.assertLess(time.monotonic() - started, 4)
        self.assertEqual(code, 1)
        self.assertFalse(result['passed'])
        self.assertIn('hard wall-clock', result['watchdog_error'])
        self.assertIn('stalled OCR control', (self.output / 'watchdog.log').read_text())

    def test_nonzero_exit_cannot_leave_a_passing_receipt(self):
        code, result = self.run_worker('(out / "results.json").write_text(json.dumps({"passed": True}))\nsys.exit(7)\n')
        self.assertEqual(code, 1)
        self.assertFalse(result['passed'])
        self.assertEqual(result['watchdog']['worker_exit'], 7)

    def test_zero_exit_without_a_successful_flow_is_not_pass(self):
        code, result = self.run_worker('pass\n')
        self.assertEqual(code, 1)
        self.assertFalse(result['passed'])

    def test_native_error_is_not_masked_by_passing_json(self):
        code, result = self.run_worker('print("ERROR: adversarial native error", flush=True)\n'
                                       '(out / "results.json").write_text(json.dumps({"passed": True}))\n')
        self.assertEqual(code, 1)
        self.assertFalse(result['passed'])

    def test_malformed_result_is_a_retained_failure(self):
        code, result = self.run_worker('(out / "results.json").write_text("not json")\n')
        self.assertEqual(code, 1)
        self.assertFalse(result['passed'])

    def test_old_output_is_not_reused(self):
        self.output.mkdir()
        old = self.output / 'results.json'
        old.write_bytes(b'earlier result, retained unchanged')
        with self.assertRaises(FileExistsError):
            self.run_worker('pass\n')
        self.assertEqual(old.read_bytes(), b'earlier result, retained unchanged')

    def test_supervised_worker_requires_the_owning_token(self):
        self.output.mkdir()
        (self.output / 'watchdog.json').write_text(json.dumps({'token': 'owner'}))
        with patch.dict(os.environ, {export_flow.TOKEN_ENV: 'different'}):
            with self.assertRaisesRegex(RuntimeError, 'token'):
                export_flow.prepare_flow_output(self.output, True)
        with patch.dict(os.environ, {export_flow.TOKEN_ENV: 'owner'}):
            self.assertEqual(export_flow.prepare_flow_output(self.output, True), self.output.resolve())


class OCRDeadlineTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.output = self.root / 'ocr'

    def command(self, code):
        return [sys.executable, '-c', code]

    def test_actual_subprocess_output_is_retained(self):
        result = ocr_text(self.command('print("100 HEALTH")'), b'fixture image', time.monotonic() + 5, self.output)
        self.assertEqual(result.strip(), '100 HEALTH')
        self.assertEqual(self.output.with_suffix('.stdout.txt').read_text().strip(), '100 HEALTH')

    def test_timeout_kills_ocr_and_retains_partial_streams(self):
        started = time.monotonic()
        with self.assertRaisesRegex(TimeoutError, 'wall-clock'):
            ocr_text(self.command('import time; print("partial OCR", flush=True); time.sleep(30)'),
                     b'fixture image', started + .25, self.output)
        self.assertLess(time.monotonic() - started, 4)
        self.assertIn('partial OCR', self.output.with_suffix('.stdout.txt').read_text())

    def test_nonzero_ocr_is_not_parseable_success(self):
        with self.assertRaisesRegex(RuntimeError, 'exited 3'):
            ocr_text(self.command('import sys; print("100 HEALTH"); sys.exit(3)'),
                     b'fixture image', time.monotonic() + 5, self.output)
        self.assertIn('100 HEALTH', self.output.with_suffix('.stdout.txt').read_text())

    def test_expired_deadline_does_not_launch_ocr(self):
        with patch('verify_offline_export.subprocess.Popen') as launch:
            with self.assertRaises(TimeoutError):
                ocr_text(self.command('pass'), b'fixture image', time.monotonic() - 1, self.output)
        launch.assert_not_called()


if __name__ == '__main__':
    unittest.main()
