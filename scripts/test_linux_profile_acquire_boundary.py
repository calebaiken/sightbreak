#!/usr/bin/env python3
"""R2 pure boundary regressions; Popen is fake or forbidden."""
from contextlib import ExitStack
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import linux_profile_acquire as acq
import test_linux_profile_acquire_sealing as maintained

RETAINED = acq.ROOT / 'docs/reports/gauntlet/m1-linux-profile-acquisition/correction-r2/retained-rejection/test_boundary_controls.py'
spec = importlib.util.spec_from_file_location('retained_r1_boundary_falsifiers', RETAINED)
critic = importlib.util.module_from_spec(spec)
spec.loader.exec_module(critic)
RESULTS = []


class BoundaryTests(unittest.TestCase):
    def test_unchanged_positive_and_real_source_drift_control(self):
        suite = unittest.TestSuite(critic.BoundaryControls(name) for name in (
            'test_real_finalization_positive_control',
            'test_source_drift_during_manifest_publication_must_reject'))
        result = unittest.TestResult()
        suite.run(result)
        RESULTS.extend(critic.RESULTS)
        self.assertEqual(result.testsRun, 2)
        self.assertEqual(result.errors, [])
        self.assertEqual(result.failures, [])
        row = next(row for row in reversed(critic.RESULTS) if row['control'] == 'source-during-manifest-publication')
        self.assertGreater(row['sources_checked'], row['checks_at_mutation'])

    def test_final_raw_log_read_must_match_first_accepted_identity(self):
        # Explicitly adapt the critic's obsolete read_text hook to the single raw
        # read used by R2. The exact original control and its failures are retained.
        state = {'overall': False, 'after_restore': False, 'mutated': False}
        original_write, original_timer, original_read = acq.write, acq.signal.setitimer, Path.read_bytes
        def write(path, value):
            original_write(path, value)
            if Path(path).name == 'overall.json' and value.get('passed'):
                state['overall'] = True
        def timer(kind, seconds):
            result = original_timer(kind, seconds)
            if seconds == 0 and state['overall']:
                state['after_restore'] = True
            return result
        def read(path):
            if state['after_restore'] and path.name == '01-version.stdout.log' and not state['mutated']:
                state['first_sha256'] = acq.digest(path)
                path.write_bytes(b'changed clean log observed by the final raw semantic read\n')
                state['changed_sha256'] = acq.digest(path)
                state['mutated'] = True
            raw = original_read(path)
            if state['mutated'] and path.name == '01-version.stdout.log':
                state['raw_validator_observed_changed_bytes'] = raw.startswith(b'changed clean log')
            return raw
        with patch.object(acq, 'write', side_effect=write), \
                patch.object(acq.signal, 'setitimer', side_effect=timer), patch.object(Path, 'read_bytes', read):
            result = maintained.independent.finalized('valid')
        RESULTS.append({**result, **state, 'control': 'adapted-final-raw-log-read'})
        self.assertTrue(state['mutated'])
        self.assertTrue(state['raw_validator_observed_changed_bytes'])
        self.assertNotEqual(state['first_sha256'], state['changed_sha256'])
        self.assertEqual(result['exit_code'], 1, result)
        self.assertFalse(result['passed'], result)

    def test_log_binding_and_validation_use_one_raw_semantic_observation(self):
        with tempfile.TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary); path = root / 'clean.log'; original = b'original clean log\n'
            stack.enter_context(patch.object(acq, 'OUTPUT', root))
            stack.enter_context(patch.object(acq.subprocess, 'Popen', side_effect=AssertionError('Pure only')))
            stack.enter_context(patch.object(Path, 'read_text', side_effect=AssertionError('No separate semantic reread')))
            path.write_bytes(original)
            evidence = acq.Evidence({})
            evidence.bind(path, raw=original, log=True)
            evidence.validate()
            path.write_bytes(b'different clean bytes\n')
            with self.assertRaisesRegex(acq.accepted.Invalid, 'accepted bytes|identity drift'):
                evidence.bind(path, raw=original, log=True)
            with self.assertRaisesRegex(acq.accepted.Invalid, 'identity drift'):
                evidence.validate()

    def test_source_observation_positive_boundary_and_original_deadline(self):
        for finish in (60.999, 61.0, 61.001):
            with self.subTest(finish=finish), ExitStack() as stack:
                clock = {'now': 0.0}
                stack.enter_context(patch.object(acq.time, 'monotonic', side_effect=lambda: clock['now']))
                stack.enter_context(patch.object(acq.subprocess, 'Popen', side_effect=AssertionError('Pure only')))
                controller = acq.Acquisition('c' * 40)
                controller.original = [{'synthetic': True}]
                controller.budget.phase_until = 61
                clock['now'] = 60
                def sources():
                    clock['now'] = finish
                    return controller.original
                with patch.object(controller, 'sources', side_effect=sources):
                    if finish < 61:
                        controller.observe_publication_source()
                    else:
                        with self.assertRaises(TimeoutError):
                            controller.observe_publication_source()
                row = controller.receipt['publication_source_observation']
                RESULTS.append({'control': 'publication-source-deadline', 'finish': finish, 'receipt': row})
                self.assertEqual(row['passed'], finish < 61)
                self.assertEqual(row['deadline_monotonic'], 61)
                self.assertEqual(row['ended_monotonic'], finish)
                self.assertIn('before overall', row['boundary'])
                self.assertIn('no immutability assertion afterward', row['scope'])


if __name__ == '__main__':
    unittest.main()
