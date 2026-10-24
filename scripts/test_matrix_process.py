#!/usr/bin/env python3
"""Pure ownership/cleanup controls; real CPython trees live in test_validate_matrix."""
import io
import json
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import matrix_process as processes


class SupervisorTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.result = Path(temporary.name) / 'process.json'

    def receipt(self):
        return json.loads(self.result.read_text())

    def test_windows_joins_job_before_launch_and_disallows_handle_inheritance(self):
        events = []
        job = Mock()
        job.join.side_effect = lambda: events.append('join')
        job.active.return_value = 1
        process = Mock()
        process.wait.return_value = 7
        def launch(*args, **kwargs):
            self.assertEqual(events, ['join'])
            self.assertTrue(kwargs['close_fds'])
            events.append('launch')
            return process
        with patch.object(processes.os, 'name', 'nt'), \
                patch.object(processes, 'WindowsJob', return_value=job), \
                patch.object(processes.subprocess, 'Popen', side_effect=launch):
            processes.supervise(['fixture-command'], self.result, 2, 'fixture-job')
        self.assertEqual(self.receipt(), {'complete': True, 'exit': 7, 'errors': []})
        job.close.assert_called_once()

    def test_windows_failed_assignment_never_launches_command(self):
        job = Mock()
        job.join.side_effect = OSError('fixture assignment denied')
        with patch.object(processes.os, 'name', 'nt'), \
                patch.object(processes, 'WindowsJob', return_value=job), \
                patch.object(processes.subprocess, 'Popen') as launch, \
                patch('sys.stdout', new_callable=io.StringIO):
            processes.supervise(['fixture-command'], self.result, 2, 'fixture-job')
        launch.assert_not_called()
        self.assertIn('assignment denied', self.receipt()['errors'][0])

    def test_windows_surviving_descendants_fail_even_when_command_exits_zero(self):
        job = Mock()
        job.active.return_value = 2  # supervisor + surviving descendant
        process = Mock()
        process.wait.return_value = 0
        with patch.object(processes.os, 'name', 'nt'), \
                patch.object(processes, 'WindowsJob', return_value=job), \
                patch.object(processes.subprocess, 'Popen', return_value=process), \
                patch('sys.stdout', new_callable=io.StringIO):
            processes.supervise(['fixture-command'], self.result, 2, 'fixture-job')
        self.assertEqual(self.receipt()['exit'], 0)
        self.assertIn('descendants survived command exit', self.receipt()['errors'])

    def test_posix_ownership_failure_never_launches_command(self):
        with patch.object(processes.os, 'name', 'posix'), \
                patch.object(processes, 'enable_subreaper', side_effect=RuntimeError('ownership unavailable')), \
                patch.object(processes.subprocess, 'Popen') as launch, \
                patch('sys.stdout', new_callable=io.StringIO):
            processes.supervise(['fixture-command'], self.result, 2)
        launch.assert_not_called()
        self.assertIn('ownership unavailable', self.receipt()['errors'])

    def test_unsupported_posix_host_fails_closed(self):
        with patch.object(processes.sys, 'platform', 'darwin'):
            with self.assertRaisesRegex(RuntimeError, 'requires Linux'):
                processes.enable_subreaper()

    @unittest.skipUnless(processes.os.name == 'nt', 'Windows handle inheritance control')
    def test_job_guard_handle_is_not_inheritable(self):
        job = processes.WindowsJob()
        try:
            self.assertFalse(processes.os.get_handle_inheritable(job.handle))
        finally:
            job.close()

    def test_posix_surviving_detached_children_are_cleaned(self):
        events = []
        process = Mock()
        process.wait.return_value = 0
        with patch.object(processes.os, 'name', 'posix'), \
                patch.object(processes, 'enable_subreaper', side_effect=lambda: events.append('own')), \
                patch.object(processes.subprocess, 'Popen', side_effect=lambda *a, **kw: events.append('launch') or process), \
                patch.object(processes, 'posix_children_alive', return_value=True), \
                patch.object(processes, 'cleanup_posix_children') as cleanup, \
                patch('sys.stdout', new_callable=io.StringIO):
            processes.supervise(['fixture-command'], self.result, 2)
        self.assertEqual(events, ['own', 'launch'])
        self.assertEqual(self.receipt()['exit'], 0)
        self.assertIn('descendants survived command exit', self.receipt()['errors'])
        cleanup.assert_called_once()
        self.assertTrue(self.receipt()['posix_cleanup_verified'])

    def test_posix_cleanup_failure_is_retained(self):
        process = Mock()
        process.wait.side_effect = subprocess.TimeoutExpired('fixture-command', 2)
        with patch.object(processes.os, 'name', 'posix'), \
                patch.object(processes, 'enable_subreaper'), \
                patch.object(processes.subprocess, 'Popen', return_value=process), \
                patch.object(processes, 'cleanup_posix_children', side_effect=OSError('fixture cleanup denied')), \
                patch('sys.stdout', new_callable=io.StringIO):
            processes.supervise(['fixture-command'], self.result, 2)
        self.assertEqual(self.receipt()['exit'], 1)
        self.assertTrue(any('timed out' in error for error in self.receipt()['errors']))
        self.assertTrue(any('cleanup denied' in error for error in self.receipt()['errors']))
        self.assertFalse(self.receipt()['posix_cleanup_verified'])

    def test_posix_kills_group_even_after_leader_exit(self):
        process = Mock(pid=12345)
        process.poll.return_value = 0
        with patch.object(processes, 'posix_children', side_effect=FileNotFoundError), \
                patch.object(processes, 'kill_posix_group') as kill:
            processes.cleanup_posix_supervisor(process, cleanup_verified=True)
        kill.assert_called_once_with(12345)
        process.wait.assert_called_once_with(timeout=processes.CLEANUP_TIMEOUT)

    def test_posix_dead_owner_cleanup_reports_uncertainty_without_guessing_other_groups(self):
        process = Mock(pid=41000, returncode=-9)
        process.wait.return_value = -9
        with patch.object(processes, 'posix_children', side_effect=FileNotFoundError), \
                patch.object(processes, 'kill_posix_group') as kill:
            with self.assertRaisesRegex(RuntimeError, 'detached-descendant cleanup unverified'):
                processes.cleanup_posix_supervisor(process)
        kill.assert_called_once_with(41000)
        process.wait.assert_called_once_with(timeout=processes.CLEANUP_TIMEOUT)

    def test_posix_parent_requires_completed_cleanup_attestation(self):
        cases = [(None, -9, 1, False),
                 ({'complete': True, 'exit': 7, 'errors': []}, 0, 7, False),
                 ({'complete': True, 'exit': 0, 'errors': [], 'posix_cleanup_verified': False}, 0, 0, False),
                 ({'complete': True, 'exit': 0, 'errors': [], 'posix_cleanup_verified': True}, -9, 0, False),
                 ({'complete': True, 'exit': 0, 'errors': [], 'posix_cleanup_verified': True}, 0, 0, True)]
        for receipt, supervisor_exit, expected_exit, verified in cases:
            with self.subTest(receipt=receipt, supervisor_exit=supervisor_exit):
                self.result.unlink(missing_ok=True)
                process = Mock(pid=41000, returncode=supervisor_exit)
                process.poll.return_value = supervisor_exit
                def wait(**kwargs):
                    if receipt is not None:
                        self.result.write_text(json.dumps(receipt))
                process.wait.side_effect = wait
                log = io.StringIO()
                fake_os = SimpleNamespace(name='posix', killpg=Mock(side_effect=ProcessLookupError))
                with patch.object(processes, 'os', fake_os), \
                        patch.object(processes, 'posix_children', side_effect=FileNotFoundError), \
                        patch.object(processes, 'kill_posix_group') as kill, \
                        patch.object(processes.subprocess, 'Popen', return_value=process):
                    code = processes.run_process(['not-executed'], cwd=self.result.parent, env={},
                                                 log=log, result_path=self.result, timeout=1)
                self.assertEqual(code, expected_exit)
                kill.assert_called_once_with(41000)
                if verified:
                    self.assertEqual(log.getvalue(), '')
                else:
                    self.assertIn('HARNESS_ERROR', log.getvalue())
                    self.assertIn('detached-descendant cleanup unverified', log.getvalue())

    def test_posix_detached_groups_and_individual_children_are_both_signalled(self):
        with patch.object(processes, 'posix_children_alive', side_effect=[True, False]), \
                patch.object(processes, 'posix_children', return_value=[111, 222]), \
                patch.object(processes.os, 'getpgid', side_effect=[111, 999], create=True), \
                patch.object(processes.os, 'getpgrp', return_value=999, create=True), \
                patch.object(processes.signal, 'SIGKILL', 9, create=True), \
                patch.object(processes, 'kill_posix_group') as kill_group, \
                patch.object(processes.os, 'kill') as kill, \
                patch.object(processes.time, 'sleep'):
            processes.cleanup_posix_children()
        kill_group.assert_called_once_with(111)
        self.assertEqual([call.args[0] for call in kill.call_args_list], [111, 222])

    def run_parent(self, receipt, *, job_stop_error=None, returncode=0):
        log = io.StringIO()
        job = Mock(name='job')
        job.name = 'fixture-job'
        job.active.return_value = 0
        if job_stop_error:
            job.stop.side_effect = job_stop_error
        process = Mock(returncode=returncode)
        process.poll.return_value = returncode
        def wait(**kwargs):
            if receipt is not None:
                self.result.write_text(json.dumps(receipt))
        process.wait.side_effect = wait
        # Do not mutate the shared os module: POSIX pathlib must stay POSIX.
        windows_os = Mock(wraps=processes.os)
        windows_os.name = 'nt'
        with patch.object(processes, 'os', windows_os), \
                patch.object(processes, 'WindowsJob', return_value=job), \
                patch.object(processes.subprocess, 'Popen', return_value=process) as launch:
            code = processes.run_process(['fixture-command'], cwd=self.result.parent,
                                         env={}, log=log, result_path=self.result, timeout=2)
        self.assertTrue(launch.call_args.kwargs['close_fds'])
        self.assertEqual(launch.call_args.args[0][0], processes.sys.executable)
        job.stop.assert_called_once()
        job.close.assert_called_once()
        return code, log.getvalue()

    def test_parent_keeps_actual_exit(self):
        code, log = self.run_parent({'complete': True, 'exit': 7, 'errors': []})
        self.assertEqual(code, 7)
        self.assertEqual(log, '')

    def test_parent_cleanup_error_cannot_pass_zero_exit(self):
        code, log = self.run_parent({'complete': True, 'exit': 0, 'errors': []},
                                    job_stop_error=RuntimeError('fixture cleanup failed'))
        self.assertEqual(code, 0)
        self.assertIn('HARNESS_ERROR Job Object cleanup failed', log)

    def test_parent_missing_receipt_fails_closed(self):
        code, log = self.run_parent(None)
        self.assertNotEqual(code, 0)
        self.assertIn('HARNESS_ERROR', log)

    def test_parent_invalid_receipt_fails_closed(self):
        for receipt in [[], {}, {'complete': True, 'exit': False, 'errors': []},
                        {'complete': True, 'exit': 0, 'errors': 'not-a-list'}]:
            with self.subTest(receipt=receipt):
                self.result.unlink(missing_ok=True)
                code, log = self.run_parent(receipt)
                self.assertNotEqual(code, 0)
                self.assertIn('HARNESS_ERROR', log)

    def test_parent_crashed_supervisor_cannot_pass_receipt_zero(self):
        code, log = self.run_parent({'complete': True, 'exit': 0, 'errors': []}, returncode=9)
        self.assertEqual(code, 0)
        self.assertIn('HARNESS_ERROR process supervisor exited 9', log)


if __name__ == '__main__':
    unittest.main()
