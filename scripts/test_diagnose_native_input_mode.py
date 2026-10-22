#!/usr/bin/env python3
"""Pure failure-selection/process controls; no engine, native APIs, or OCR."""
import copy
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import diagnose_native_input_mode as diagnostic


class Clock:
    now = 0
    def monotonic(self):
        return self.now


class DiagnosticControls(unittest.TestCase):
    def failure_fixture(self, directory):
        result = [{'suite': 'input_mode', 'exit': 0, 'clean_log': False}]
        isolation = {'passed': False, 'failure': {'message': 'input_mode failed; raw output retained'},
                     'source_resources_unchanged': True, 'copied_resources_unchanged': True,
                     'temporary_project_removed': True, 'finalization_failures': [],
                     'cleanup': [{'removed': True}], 'source_resources_sha256': {'source': 'invented-hash'}}
        directory.mkdir()
        (directory / 'results.json').write_text(json.dumps(result))
        (directory / 'isolation.json').write_text(json.dumps(isolation))
        (directory / 'input_mode.log').write_text('WARNING: 2 ObjectDB instances were leaked at exit\n')
        return result, isolation

    def test_only_proven_original_failure_selects_and_original_bytes_are_untouched(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / 'original'
            result, isolation = self.failure_fixture(directory)
            original = diagnostic.evidence(directory)
            with patch.object(diagnostic, 'inventory', return_value={'source': 'invented-hash'}):
                self.assertIsNone(diagnostic.select_failure(directory))
                for key, value in [('passed', True), ('failure', {}), ('cleanup', []),
                                   ('source_resources_unchanged', False), ('copied_resources_unchanged', False),
                                   ('temporary_project_removed', False), ('finalization_failures', [{}]),
                                   ('source_resources_sha256', {})]:
                    bad = copy.deepcopy(isolation)
                    bad[key] = value
                    (directory / 'isolation.json').write_text(json.dumps(bad))
                    with self.subTest(key=key): self.assertIsNotNone(diagnostic.select_failure(directory))
                (directory / 'isolation.json').write_text(json.dumps(isolation))
                for change in ('nonzero', 'clean', 'duplicate', 'later', 'wrong'):
                    bad = copy.deepcopy(result)
                    if change == 'nonzero': bad[0]['exit'] = 9
                    elif change == 'clean': bad[0]['clean_log'] = True
                    elif change == 'duplicate': bad.append(copy.deepcopy(bad[0]))
                    elif change == 'later': bad.append({'suite': 'menu_focus'})
                    else: bad[0]['suite'] = 'actor'
                    (directory / 'results.json').write_text(json.dumps(bad))
                    with self.subTest(change=change): self.assertIsNotNone(diagnostic.select_failure(directory))
                (directory / 'results.json').write_text(json.dumps(result))
                self.assertEqual(diagnostic.evidence(directory), original)
                (directory / 'input_mode.log').write_text('ERROR: some other failure\n')
                self.assertIsNotNone(diagnostic.select_failure(directory))

    def fake_runner(self, directory, deadline=10):
        runner = object.__new__(diagnostic.VerboseInputMode)
        runner.output, runner.project = directory, directory / 'private-project'
        runner.deadline, runner.processes, runner.report = deadline, [], {}
        return runner

    def test_verbose_only_changes_exact_input_mode_command_and_retains_leak_gate(self):
        clock = Clock()
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            runner = self.fake_runner(directory)
            class Process:
                pid, returncode = 4100, 0  # Invented process only.
                def __init__(self, command, **kwargs):
                    self.command = command
                    self.kwargs = kwargs
                    kwargs['stdout'].write('WARNING: 2 ObjectDB instances were leaked at exit\n')
                def wait(self, timeout): self.timeout = timeout
            with (patch.object(diagnostic.time, 'monotonic', clock.monotonic),
                  patch.object(diagnostic.toolchain, 'binary', return_value='invented-engine'),
                  patch.object(diagnostic.toolchain, 'environment', return_value={}),
                  patch.object(diagnostic.subprocess, 'Popen', Process),
                  patch.object(diagnostic, 'reap', return_value={'owned_group_gone': True, 'signals_sent': []}) as cleanup):
                receipt = runner.execute('input_mode', ['--headless', '--script', 'res://tests/input_mode_test.gd'], 120)
                self.assertEqual(receipt['command'][-4:], ['--headless', '--verbose', '--script', 'res://tests/input_mode_test.gd'])
                self.assertFalse(receipt['clean_log'])
                self.assertEqual(receipt['exit'], 0)
                self.assertEqual(receipt['timeout_seconds'], 10)
                self.assertEqual(receipt['cleanup']['signals_sent'], [])
                cleanup.assert_called_once()
                self.assertEqual(json.loads((directory / 'owned-processes.json').read_text())[0], receipt)
                with self.assertRaises(RuntimeError):
                    runner.execute('input_mode', ['--script', 'res://tests/something_else.gd'], 120)

    def test_timeout_still_records_owned_group_cleanup_and_original_exception(self):
        clock = Clock()
        with tempfile.TemporaryDirectory() as temporary:
            runner = self.fake_runner(Path(temporary))
            class Process:
                pid, returncode = 4101, -15
                def __init__(self, command, **kwargs): self.command = command
                def wait(self, timeout):
                    raise subprocess.TimeoutExpired(self.command, timeout)
            with (patch.object(diagnostic.time, 'monotonic', clock.monotonic),
                  patch.object(diagnostic.toolchain, 'binary', return_value='invented-engine'),
                  patch.object(diagnostic.toolchain, 'environment', return_value={}),
                  patch.object(diagnostic.subprocess, 'Popen', Process),
                  patch.object(diagnostic, 'reap', return_value={'owned_group_gone': True, 'signals_sent': ['SIGTERM']}) as cleanup):
                with self.assertRaises(subprocess.TimeoutExpired):
                    runner.execute('input_mode', ['--headless', '--script', 'res://tests/input_mode_test.gd'], 120)
                self.assertTrue(runner.processes[0]['timed_out'])
                self.assertEqual(runner.processes[0]['cleanup']['signals_sent'], ['SIGTERM'])
                cleanup.assert_called_once()
            clock.now = 11
            with patch.object(diagnostic.time, 'monotonic', clock.monotonic), patch.object(diagnostic.subprocess, 'Popen') as launch:
                with self.assertRaises(TimeoutError): runner.execute('later', [], 30)
                launch.assert_not_called()

    def test_unreaped_owned_group_cannot_report_clean_process(self):
        clock = Clock()
        with tempfile.TemporaryDirectory() as temporary:
            runner = self.fake_runner(Path(temporary))
            class Process:
                pid, returncode = 4102, 0
                def __init__(self, command, **kwargs): pass
                def wait(self, timeout): pass
            with (patch.object(diagnostic.time, 'monotonic', clock.monotonic),
                  patch.object(diagnostic.toolchain, 'binary', return_value='invented-engine'),
                  patch.object(diagnostic.toolchain, 'environment', return_value={}),
                  patch.object(diagnostic.subprocess, 'Popen', Process),
                  patch.object(diagnostic, 'reap', return_value={'owned_group_gone': False})):
                with self.assertRaisesRegex(RuntimeError, 'group remained'):
                    runner.execute('input_mode', ['--headless', '--script', 'res://tests/input_mode_test.gd'], 120)
                self.assertFalse(runner.processes[0]['cleanup']['owned_group_gone'])

    def test_clean_repeat_never_repairs_original_failed_gate_and_skips_launch_no_engine(self):
        for selected in (True, False):
            with tempfile.TemporaryDirectory() as temporary:
                directory = Path(temporary)
                original = directory / 'original'
                self.failure_fixture(original)
                hashes = diagnostic.evidence(original)
                identity = {'source_commit': 'invented', 'source_game_tree': 'invented', 'source_content_sha256': 'invented',
                            'source_validation_sha256': 'invented', 'source_dirty': False, 'source_game_dirty': False}
                class Runner:
                    report = {'passed': True}
                    processes = []
                    def __init__(self, *args): pass
                    def __enter__(self): return self
                    def __exit__(self, *args): return False
                    def run(self, suite):
                        if suite != 'input_mode': raise AssertionError('Wrong suite')
                with (patch.object(diagnostic.platform, 'system', return_value='Darwin'),
                      patch.object(diagnostic.platform, 'machine', return_value='arm64'),
                      patch.object(diagnostic, 'source', return_value=identity),
                      patch.object(diagnostic, 'select_failure', return_value=None if selected else 'unrelated'),
                      patch.object(diagnostic, 'VerboseInputMode', side_effect=Runner) as launch):
                    self.assertEqual(diagnostic.run(original, directory / 'new'), 0)
                    report = json.loads((directory / 'new/diagnostic.json').read_text())
                    self.assertFalse(report['strict_gate_repaired'])
                    self.assertTrue(report['original_evidence_unchanged'])
                    self.assertEqual(diagnostic.evidence(original), hashes)
                    self.assertEqual(launch.call_count, int(selected))
                    self.assertEqual(report['status'], 'DIAGNOSTIC_CLEAN_REPEAT' if selected else 'SKIPPED_DIFFERENT_OR_UNPROVEN_FAILURE')

    def test_refuses_non_arm_host_and_overlapping_or_existing_output_without_launch(self):
        with tempfile.TemporaryDirectory() as temporary:
            original = Path(temporary) / 'original'
            self.failure_fixture(original)
            with patch.object(diagnostic.platform, 'system', return_value='Linux'), patch.object(diagnostic, 'VerboseInputMode') as launch:
                self.assertEqual(diagnostic.run(original, Path(temporary) / 'new'), 1)
                launch.assert_not_called()
            for output in (original, original / 'nested', Path(temporary)):
                with self.subTest(output=output), self.assertRaises(RuntimeError): diagnostic.run(original, output)


if __name__ == '__main__':
    unittest.main()
