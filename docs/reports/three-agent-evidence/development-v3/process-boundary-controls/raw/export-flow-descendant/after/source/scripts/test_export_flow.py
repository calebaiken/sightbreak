#!/usr/bin/env python3
"""Actual CPython timeout/receipt controls, not native exported-client passes."""
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import textwrap
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

    def test_nonobject_result_is_a_retained_failure(self):
        code, result = self.run_worker('(out / "results.json").write_text("[]")\n')
        self.assertEqual(code, 1)
        self.assertFalse(result['passed'])

    def test_truthy_nonboolean_result_is_not_success(self):
        code, result = self.run_worker('(out / "results.json").write_text(json.dumps({"passed": 1}))\n')
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
        marker = {'token': 'owner', 'passed': False, 'status': 'incomplete',
                  'process_receipt': export_flow.PROCESS_RECEIPT}
        (self.output / 'watchdog.json').write_text(json.dumps(marker))
        (self.output / 'watchdog.log').write_bytes(b'owned raw bytes\n')
        (self.output / 'results.json').write_text('{"passed": false, "status": "incomplete"}')
        (self.output / export_flow.PROCESS_RECEIPT).write_text('{"complete": false}')
        with patch.dict(os.environ, {export_flow.TOKEN_ENV: 'different'}):
            with self.assertRaisesRegex(RuntimeError, 'token'):
                export_flow.prepare_flow_output(self.output, True)
        with patch.dict(os.environ, {export_flow.TOKEN_ENV: ''}):
            with self.assertRaisesRegex(RuntimeError, 'token'):
                export_flow.prepare_flow_output(self.output, True)
        with patch.dict(os.environ, {export_flow.TOKEN_ENV: 'owner'}):
            self.assertEqual(export_flow.prepare_flow_output(self.output, True), self.output.resolve())
            (self.output / 'earlier.log').write_bytes(b'unowned evidence')
            with self.assertRaises(FileExistsError):
                export_flow.prepare_flow_output(self.output, True)
        self.assertEqual((self.output / 'watchdog.log').read_bytes(), b'owned raw bytes\n')

    def test_completed_watchdog_cannot_reuse_token_to_overwrite_evidence(self):
        self.run_worker('(out / "results.json").write_text(json.dumps({"passed": True}))\n')
        before = {path.name: path.read_bytes() for path in self.output.iterdir()}
        state = json.loads((self.output / 'watchdog.json').read_text())
        with patch.dict(os.environ, {export_flow.TOKEN_ENV: state['token']}):
            with self.assertRaises(FileExistsError):
                export_flow.prepare_flow_output(self.output, True)
        self.assertEqual({path.name: path.read_bytes() for path in self.output.iterdir()}, before)

    def test_old_process_receipt_alone_refuses_a_new_attempt(self):
        self.output.mkdir()
        receipt = self.output / export_flow.PROCESS_RECEIPT
        receipt.write_bytes(b'earlier process receipt')
        with self.assertRaises(FileExistsError):
            self.run_worker('pass\n')
        self.assertEqual(receipt.read_bytes(), b'earlier process receipt')

    def fake_passing_runner(self, command, *, cwd, env, log, result_path, timeout):
        state = json.loads((self.output / 'watchdog.json').read_text())
        initial = json.loads((self.output / 'results.json').read_text())
        self.assertFalse(state['passed'])
        self.assertEqual(state['status'], 'incomplete')
        self.assertFalse(initial['passed'])
        self.assertEqual(initial['status'], 'incomplete')
        self.assertEqual(env[export_flow.TOKEN_ENV], state['token'])
        self.assertEqual(command[0], sys.executable)
        self.assertIn(export_flow.WORKER_FLAG, command)
        self.assertEqual(state['controller_sha256'], hashlib.sha256(self.worker.read_bytes()).hexdigest())
        self.assertEqual(result_path, self.output / export_flow.PROCESS_RECEIPT)
        self.assertFalse(result_path.exists(), 'process receipt must be fresh before launch')
        self.assertGreater(timeout, 0)
        result_path.write_text(json.dumps({'complete': True, 'exit': 0, 'errors': []}))
        (self.output / 'results.json').write_text('{"passed": true}')
        return 0

    def test_initial_failed_receipts_and_source_hash_exist_before_launch(self):
        with patch.object(export_flow, 'run_process', side_effect=self.fake_passing_runner):
            code, result = self.run_worker('pass\n')
        self.assertEqual(code, 0)
        self.assertTrue(result['passed'])

    def test_harness_error_cannot_be_hidden_by_zero_exit_and_passing_json(self):
        def failed_cleanup(*args, **kwargs):
            code = self.fake_passing_runner(*args, **kwargs)
            kwargs['log'].write('HARNESS_ERROR fixture containment cleanup failed\n')
            return code
        with patch.object(export_flow, 'run_process', side_effect=failed_cleanup):
            code, result = self.run_worker('pass\n')
        self.assertEqual(code, 1)
        self.assertFalse(result['passed'])
        self.assertEqual(result['watchdog']['worker_exit'], 0)
        self.assertIn('HARNESS_ERROR', result['watchdog_error'])

    def test_cleanup_exception_is_a_retained_failure(self):
        with patch.object(export_flow, 'run_process', side_effect=RuntimeError('fixture cleanup failed')):
            code, result = self.run_worker('pass\n')
        self.assertEqual(code, 1)
        self.assertFalse(result['passed'])
        self.assertIn('HARNESS_ERROR RuntimeError: fixture cleanup failed',
                      (self.output / 'watchdog.log').read_text())

    def test_late_zero_exit_cannot_pass_wall_clock_deadline_including_cleanup(self):
        with patch.object(export_flow, 'run_process', side_effect=self.fake_passing_runner), \
                patch.object(export_flow.time, 'monotonic', side_effect=[0, .1, 2, 2, 2]):
            code, result = self.run_worker('pass\n', 1)
        self.assertEqual(code, 1)
        self.assertEqual(result['watchdog']['worker_exit'], 0)
        self.assertIn('hard wall-clock', result['watchdog_error'])
        self.assertIn('including cleanup', (self.output / 'watchdog.log').read_text())

    def test_expired_startup_deadline_does_not_launch_worker(self):
        with patch.object(export_flow, 'run_process') as launch, \
                patch.object(export_flow.time, 'monotonic', side_effect=[0, 2, 2, 2, 2]):
            code, result = self.run_worker('pass\n', 1)
        launch.assert_not_called()
        self.assertEqual(code, 1)
        self.assertFalse(result['passed'])
        self.assertIn('before launch', result['watchdog_error'])

    def test_final_audit_cannot_turn_an_expired_deadline_into_success(self):
        with patch.object(export_flow, 'run_process', side_effect=self.fake_passing_runner), \
                patch.object(export_flow.time, 'monotonic', side_effect=[0, .1, .2, 2, 2]):
            code, result = self.run_worker('pass\n', 1)
        self.assertEqual(code, 1)
        self.assertFalse(result['passed'])
        self.assertIn('final audit', result['watchdog_error'])
        self.assertIn('HARNESS_ERROR', (self.output / 'watchdog.log').read_text())

    def test_missing_controller_retains_initial_failure_without_launch(self):
        with patch.object(export_flow, 'run_process') as launch, \
                contextlib.redirect_stdout(io.StringIO()):
            code = export_flow.supervise(self.worker, [], self.output, 5)
        launch.assert_not_called()
        self.assertEqual(code, 1)
        result = json.loads((self.output / 'results.json').read_text())
        self.assertFalse(result['passed'])
        self.assertEqual(result['stage'], 'watchdog-start')
        self.assertIn('HARNESS_ERROR', (self.output / 'watchdog.log').read_text())

    def entry_worker(self, *, detached=False, stalled=False, awaited=False, timeout=5):
        """Exercise entry -> token-bound worker -> real CPython descendant."""
        started = self.root / 'child-started'
        finished = self.root / 'child-finished'
        child = ('from pathlib import Path; import os, time; '
                 'print("synthetic descendant partial output", flush=True); '
                 f'Path({str(started)!r}).write_text(str(os.getpid())); '
                 'time.sleep(1.1); print("ERROR: late synthetic descendant", flush=True); '
                 f'Path({str(finished)!r}).write_text("finished")')
        if awaited:
            child = 'print("normally awaited synthetic descendant", flush=True)'
        self.worker.write_text(textwrap.dedent(f'''\
            import argparse, json, os, subprocess, sys, time
            from pathlib import Path
            sys.path.insert(0, {str(Path(export_flow.__file__).resolve().parent)!r})
            import export_flow

            def main(supervised=False):
                parser = argparse.ArgumentParser()
                parser.add_argument('--output', type=Path, required=True)
                parser.add_argument('--timeout', type=float, required=True)
                args = parser.parse_args()
                out = export_flow.prepare_flow_output(args.output, supervised)
                state = json.loads((out / 'watchdog.json').read_text())
                initial = json.loads((out / 'results.json').read_text())
                assert state['token'] == os.environ[export_flow.TOKEN_ENV]
                assert state['status'] == initial['status'] == 'incomplete'
                assert state['passed'] is initial['passed'] is False
                (out.parent / 'worker-initial.json').write_text(json.dumps(initial))
                print('synthetic worker validated owner token', flush=True)
                options = {{}}
                if {detached!r}:
                    options = ({{'creationflags': 0x200}} if os.name == 'nt'
                               else {{'start_new_session': True}})
                child = subprocess.Popen([sys.executable, '-B', '-c', {child!r}], **options)
                if {awaited!r}:
                    child.wait()
                else:
                    while not Path({str(started)!r}).exists():
                        time.sleep(.005)
                (out / 'results.json').write_text(json.dumps(
                    {{'passed': True, 'synthetic_control_not_native_evidence': True}}))
                if {stalled!r}:
                    time.sleep(30)

            if __name__ == '__main__':
                raise SystemExit(export_flow.entry(main, __file__))
            '''), encoding='utf-8')
        command = [sys.executable, '-B', str(self.worker), '--output', str(self.output),
                   '--timeout', str(timeout)]
        process = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=12)
        result = json.loads((self.output / 'results.json').read_text())
        return process.returncode, result, started, finished

    def assert_stopped_entry_descendant(self, code, result, started, finished):
        self.assertTrue(started.exists())
        self.assertEqual(code, 1)
        self.assertFalse(result['passed'])
        initial = json.loads((self.root / 'worker-initial.json').read_text())
        self.assertFalse(initial['passed'])
        text = (self.output / 'watchdog.log').read_bytes()
        self.assertIn(b'synthetic worker validated owner token', text)
        self.assertIn(b'synthetic descendant partial output', text)
        self.assertIn(b'HARNESS_ERROR', text)
        self.assertIn('HARNESS_ERROR', result['watchdog_error'])
        receipt = json.loads((self.output / export_flow.PROCESS_RECEIPT).read_text())
        self.assertTrue(receipt['complete'])
        self.assertTrue(receipt['errors'])
        result_bytes = (self.output / 'results.json').read_bytes()
        time.sleep(1.3)
        self.assertFalse(finished.exists(), 'descendant escaped export containment')
        self.assertEqual((self.output / 'watchdog.log').read_bytes(), text)
        self.assertEqual((self.output / 'results.json').read_bytes(), result_bytes)

    def test_entry_token_bound_worker_cannot_leave_descendant_after_zero_exit(self):
        code, result, started, finished = self.entry_worker()
        self.assertEqual(result['watchdog']['worker_exit'], 0)
        self.assert_stopped_entry_descendant(code, result, started, finished)

    def test_entry_new_process_group_cannot_escape(self):
        code, result, started, finished = self.entry_worker(detached=True)
        self.assertEqual(result['watchdog']['worker_exit'], 0)
        self.assert_stopped_entry_descendant(code, result, started, finished)

    def test_entry_timeout_cleans_token_bound_descendant_despite_passing_json(self):
        started_at = time.monotonic()
        code, result, started, finished = self.entry_worker(detached=True, stalled=True, timeout=.6)
        self.assertLess(time.monotonic() - started_at, 4)
        self.assertIn('hard wall-clock', result['watchdog_error'])
        self.assert_stopped_entry_descendant(code, result, started, finished)

    def test_entry_normally_awaited_descendant_passes(self):
        code, result, _, _ = self.entry_worker(awaited=True)
        self.assertEqual(code, 0)
        self.assertTrue(result['passed'])
        self.assertTrue(result['synthetic_control_not_native_evidence'])


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
