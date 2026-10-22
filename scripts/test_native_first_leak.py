#!/usr/bin/env python3
"""Pure first-failed-suite selection and no-launch controls; every process is fake."""
import contextlib
import copy
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import diagnose_native_input_mode as diagnostic
import test_diagnose_native_input_mode as legacy_controls


FIXTURES = Path(__file__).resolve().parents[1] / 'docs/reports/gauntlet/m2-macos-first-leak/fixtures'
IDENTITY = {'source_commit': 'invented', 'source_game_tree': 'invented', 'source_content_sha256': 'invented',
            'source_validation_sha256': 'invented', 'source_dirty': False, 'source_game_dirty': False}


class FirstFailedLeak(unittest.TestCase):
    def fixture(self, path, suite='actor'):
        return legacy_controls.DiagnosticControls().failure_fixture(path, suite)

    def run_fake(self, original, output, **kwargs):
        with (patch.object(diagnostic.platform, 'system', return_value='Darwin'),
              patch.object(diagnostic.platform, 'machine', return_value='arm64'),
              patch.object(diagnostic.toolchain, 'binary', return_value='/invented/pinned-engine'),
              patch.object(diagnostic, 'inventory', return_value={'source': 'invented-hash'}),
              patch.object(diagnostic, 'source', return_value=IDENTITY),
              contextlib.redirect_stdout(io.StringIO())):
            return diagnostic.run(original, output)

    def test_both_actual_original_boundaries_select_without_changing_bytes(self):
        manifest = json.loads((FIXTURES / 'provenance.json').read_text())
        for run, info in manifest['runs'].items():
            directory = FIXTURES / run
            for name, receipt in info['files'].items():
                self.assertEqual(hashlib.sha256((directory / name).read_bytes()).hexdigest(), receipt['sha256'])
            isolation = json.loads((directory / 'isolation.json').read_text())
            row = json.loads((directory / 'results.json').read_text())[-1]
            # Linux cannot resolve macOS's /var -> /private/var symlink. This
            # explicit pure path simulation is readiness only, never native proof.
            def simulated_mac_path(left, right):
                def normalized(value): return str(Path(value)).removeprefix('/private') if isinstance(value, str) else None
                return normalized(left) is not None and normalized(left) == normalized(right)
            selection = {}
            with (patch.object(diagnostic, 'inventory', return_value=isolation['source_resources_sha256']),
                  patch.object(diagnostic.toolchain, 'binary', return_value=row['command'][0]),
                  patch.object(diagnostic, 'same_native_path', side_effect=simulated_mac_path)):
                self.assertIsNone(diagnostic.select_failure(directory, selection))
            self.assertEqual(selection, {'suite': info['failed_suite']})

    def test_only_selected_whitelisted_suite_runs_and_original_gate_stays_failed(self):
        for suite in diagnostic.LEAK_SUITES:
            with tempfile.TemporaryDirectory() as temporary:
                original, output = Path(temporary) / 'original', Path(temporary) / 'new'
                self.fixture(original, suite)
                hashes = diagnostic.evidence(original)
                calls = []
                class Runner:
                    report, processes = {'passed': True}, []
                    def __init__(self, destination, deadline, selected): calls.append(('construct', selected))
                    def __enter__(self): return self
                    def __exit__(self, *args): return False
                    def run(self, selected): calls.append(('run', selected))
                with patch.object(diagnostic, 'VerboseInputMode', Runner):
                    self.assertEqual(self.run_fake(original, output), 0)
                report = json.loads((output / 'diagnostic.json').read_text())
                self.assertEqual(calls, [('construct', suite), ('run', suite)])
                self.assertEqual(report['selected_suite'], suite)
                self.assertFalse(report['strict_gate_repaired'])
                self.assertEqual(diagnostic.evidence(original), hashes)

    def test_foreign_or_unclean_proof_launches_no_runner_or_process(self):
        variants = ('engine_argv', 'script_argv', 'project_argv', 'project_receipt', 'producer_user',
                    'producer_namespace', 'producer_warning', 'original_state', 'cleanup_namespace',
                    'cleanup_failed', 'source', 'engine_version', 'unsupported', 'nonzero', 'bool_exit', 'absent_log')
        for variant in variants:
            with self.subTest(variant=variant), tempfile.TemporaryDirectory() as temporary:
                original, output = Path(temporary) / 'original', Path(temporary) / 'new'
                rows, isolation = self.fixture(original)
                row = rows[0]
                if variant == 'engine_argv': row['command'][0] = '/foreign/engine'
                elif variant == 'script_argv': row['command'][-1] = 'res://tests/foreign_test.gd'
                elif variant == 'project_argv': row['command'][2] = '/foreign/project'
                elif variant == 'project_receipt': row['before']['project_path'] = '/foreign/project'
                elif variant == 'producer_user': row['after']['user_data_dir'] = '/foreign/actor'
                elif variant == 'producer_namespace': row['before']['custom_user_dir'] = 'foreign/actor'
                elif variant == 'producer_warning': row['before']['run']['clean_log'] = False
                elif variant == 'original_state': row['before']['profile_exists'] = True
                elif variant == 'cleanup_namespace': isolation['cleanup'][0]['user_namespace'] = '/foreign'
                elif variant == 'cleanup_failed': isolation['cleanup'][0]['removed'] = False
                elif variant == 'source': isolation['source_resources_sha256'] = {}
                elif variant == 'engine_version': isolation['engine'] = 'foreign'
                elif variant == 'unsupported':
                    row['suite'] = 'match'
                    isolation['failure']['message'] = 'match failed; raw output retained'
                elif variant == 'nonzero': row['exit'] = 9
                elif variant == 'bool_exit': row['exit'] = False
                else: (original / 'actor.log').unlink()
                (original / 'results.json').write_text(json.dumps(rows))
                (original / 'isolation.json').write_text(json.dumps(isolation))
                with patch.object(diagnostic, 'VerboseInputMode') as runner, patch.object(diagnostic.subprocess, 'Popen') as process:
                    self.assertEqual(self.run_fake(original, output), 0)
                    runner.assert_not_called(); process.assert_not_called()
                report = json.loads((output / 'diagnostic.json').read_text())
                self.assertEqual(report['status'], 'SKIPPED_DIFFERENT_OR_UNPROVEN_FAILURE')
                self.assertFalse(report['passed'])

    def test_earlier_failure_duplicate_unknown_or_later_result_never_falls_through(self):
        for variant in ('earlier_unsupported', 'earlier_supported', 'later_success', 'duplicate', 'unknown'):
            with self.subTest(variant=variant), tempfile.TemporaryDirectory() as temporary:
                original, output = Path(temporary) / 'original', Path(temporary) / 'new'
                rows, _isolation = self.fixture(original, 'input_mode')
                prior = {'suite': 'actor', 'exit': 0, 'clean_log': False}
                if variant == 'earlier_unsupported': prior['suite'] = 'match'
                if variant.startswith('earlier'): rows.insert(0, prior)
                elif variant == 'later_success': rows.append({'suite': 'menu_focus', 'exit': 0, 'clean_log': True})
                elif variant == 'duplicate': rows.append(copy.deepcopy(rows[0]))
                else: rows.insert(0, {'suite': 'foreign', 'exit': 0, 'clean_log': True})
                (original / 'results.json').write_text(json.dumps(rows))
                with patch.object(diagnostic, 'VerboseInputMode') as runner, patch.object(diagnostic.subprocess, 'Popen') as process:
                    self.assertEqual(self.run_fake(original, output), 0)
                    runner.assert_not_called(); process.assert_not_called()

    def test_actor_verbose_argv_and_other_suite_refusal(self):
        with tempfile.TemporaryDirectory() as temporary:
            runner = legacy_controls.DiagnosticControls().fake_runner(Path(temporary))
            runner.suite = 'actor'
            class Process:
                pid, returncode = 4200, 0
                def __init__(self, command, **kwargs): self.command = command
                def wait(self, timeout): pass
            with (patch.object(diagnostic.time, 'monotonic', return_value=0),
                  patch.object(diagnostic.toolchain, 'binary', return_value='/invented/pinned-engine'),
                  patch.object(diagnostic.toolchain, 'environment', return_value={}),
                  patch.object(diagnostic.subprocess, 'Popen', Process),
                  patch.object(diagnostic, 'reap', return_value={'owned_group_gone': True})):
                result = runner.execute('actor', ['--headless', '--script', 'res://tests/actor_test.gd'], 120)
                self.assertEqual(result['command'][-4:], ['--headless', '--verbose', '--script', 'res://tests/actor_test.gd'])
                for other in ('input_mode', 'match'):
                    with self.assertRaises(RuntimeError):
                        runner.execute(other, ['--headless', '--script', 'res://tests/' + other + '_test.gd'], 120)

    def test_original_or_source_mutation_during_selection_prevents_launch(self):
        for mutation in ('original', 'source'):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as temporary:
                original, output = Path(temporary) / 'original', Path(temporary) / 'new'
                self.fixture(original)
                real_select = diagnostic.select_failure
                source = dict(IDENTITY)
                def select(directory, selection):
                    reason = real_select(directory, selection)
                    if mutation == 'original': (original / 'actor.log').write_text('changed after selection\n')
                    else: source['source_content_sha256'] = 'changed'
                    return reason
                snapshots = []
                def current_source():
                    snapshots.append(dict(source))
                    return dict(source)
                with (patch.object(diagnostic.platform, 'system', return_value='Darwin'),
                      patch.object(diagnostic.platform, 'machine', return_value='arm64'),
                      patch.object(diagnostic.toolchain, 'binary', return_value='/invented/pinned-engine'),
                      patch.object(diagnostic, 'inventory', return_value={'source': 'invented-hash'}),
                      patch.object(diagnostic, 'source', side_effect=current_source),
                      patch.object(diagnostic, 'select_failure', side_effect=select),
                      patch.object(diagnostic, 'VerboseInputMode') as runner,
                      patch.object(diagnostic.subprocess, 'Popen') as process,
                      contextlib.redirect_stdout(io.StringIO())):
                    self.assertEqual(diagnostic.run(original, output), 1)
                    runner.assert_not_called(); process.assert_not_called()
                report = json.loads((output / 'diagnostic.json').read_text())
                self.assertIn('no launch', report['failure']['message'])


if __name__ == '__main__':
    unittest.main()
