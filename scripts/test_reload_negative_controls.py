#!/usr/bin/env python3
"""Pure/mocked controls. Never launches Godot, Blender, imports, or child processes.

Set NEGATIVE_AUDIO_TEST_OUT to a new/empty evidence parent to retain the fixture
checkouts, rejected attempts, raw logs/receipts/captures, and classification cases.
The WAV/CSV fixtures are synthetic, NOT native/audio-validation evidence.
"""
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import reload_negative_controls as controls


MAINTAINED_SOURCE = tuple(controls.SOURCE)


def summary(tag='RELOAD_AUDIO_CAPTURE', checks=14, failures=0, scenario='reload', reduced='false'):
    fields = ''
    if tag == 'RELOAD_AUDIO_CAPTURE':
        fields = ' scenario=%s reduced=%s' % (scenario, reduced)
    elif tag == 'RELOAD_VISIBILITY_TEST':
        fields = ' view=sunlit reduced=%s frames=51' % reduced
    return '%s%s checks=%s failures=%s\n' % (tag, fields, checks, failures)


class PureCase(unittest.TestCase):
    def setUp(self):
        evidence = os.environ.get('NEGATIVE_AUDIO_TEST_OUT')
        if evidence:
            self.directory = Path(evidence) / self.id()
            self.directory.mkdir(parents=True)
        else:
            temporary = tempfile.TemporaryDirectory(prefix='negative-audio-unit-')
            self.addCleanup(temporary.cleanup)
            self.directory = Path(temporary.name)
        self.judgments = []
        self.addCleanup(lambda: controls.write_json(self.directory / 'judgments.json', self.judgments))
        for target in ('run', 'Popen', 'check_output'):
            guard = patch.object(subprocess, target, side_effect=AssertionError('native/process execution forbidden'))
            guard.start()
            self.addCleanup(guard.stop)
        guard = patch.object(controls, 'run_process', side_effect=AssertionError('unmocked process invocation forbidden'))
        guard.start()
        self.addCleanup(guard.stop)

    def patched(self, name, value=None, **kwargs):
        patcher = patch.object(controls, name, value, **kwargs) if value is not None else patch.object(controls, name, **kwargs)
        result = patcher.start()
        self.addCleanup(patcher.stop)
        return result

    def judged(self, text, code, expected_state, *, tag='RELOAD_AUDIO_CAPTURE', fields=None, errors=()):
        state, details, parsed = controls.classify(text, code, tag, fields, errors)
        self.judgments.append({'output': text, 'exit': code, 'expected_state': expected_state,
                               'state': state, 'errors': details, 'summary': parsed})
        self.assertEqual(state, expected_state, details)
        return details


class ClassificationTests(PureCase):
    def test_nonzero_exit_with_passing_summary_never_passes_or_counts_as_caught(self):
        for code in (1, 2, 139, -11):
            with self.subTest(code=code):
                self.judged(summary(), code, 'BROKEN')

    def test_expected_assertion_errors_need_failing_summary_and_exit_one(self):
        text = 'ERROR: a deliberate assertion\nFAIL a deliberate assertion\n' + summary(failures=1)
        self.judged(text, 1, 'FAILED', fields={'scenario': 'reload', 'reduced': 'false'})
        for code in (0, 2, 139, -11):
            with self.subTest(code=code):
                self.judged(text, code, 'BROKEN')
        self.judged('ERROR: a deliberate assertion\n' + summary(), 0, 'BROKEN')

    def test_summary_without_error_lines_can_be_a_completed_assertion_failure(self):
        self.judged(summary(failures=2), 1, 'FAILED')
        self.judged(summary(), 0, 'passed')

    def test_native_error_cannot_hide_beside_a_valid_failing_summary(self):
        self.judged('ERROR: could not open resource\n   at: load (core/io/resource_loader.cpp:1)\n'
                    + summary(failures=1), 1, 'BROKEN')
        self.judged('ERROR: expected assertion\n   at: push_error (core/variant/variant_utility.cpp:1)\n'
                    + summary(failures=1), 1, 'FAILED')
        self.judged(('ERROR: expected assertion\n' * 2) + 'FAIL expected assertion\n'
                    + summary(failures=1), 1, 'BROKEN')

    def test_missing_wrong_duplicate_or_incomplete_summary_is_not_caught(self):
        for text, state in (
            ('ERROR: assertion, but execution aborted\n', 'CRASHED'),
            ('Segmentation fault\n', 'CRASHED'),
            (summary('RELOAD_AUDIO_TEST', failures=1), 'BROKEN'),
            (summary(failures=1) * 2, 'BROKEN'),
            ('RELOAD_AUDIO_CAPTURE failures=1\n', 'BROKEN'),
            (summary(checks=0, failures=0), 'BROKEN'),
            (summary(checks=1, failures=2), 'BROKEN'),
            (summary(checks='14oops', failures=1), 'BROKEN'),
            (summary(failures=-1), 'BROKEN'),
            (summary(failures=1).replace('checks=14', 'checks=14 checks=14'), 'BROKEN'),
        ):
            with self.subTest(text=text):
                self.judged(text, 1, state)

    def test_expected_capture_scenario_and_reduced_flag_are_required(self):
        fields = {'scenario': 'cancel', 'reduced': 'false'}
        for text in (summary(failures=1), summary(failures=1, scenario='cancel', reduced='true'),
                     summary(failures=1, scenario='cancel').replace(' reduced=false', '')):
            with self.subTest(text=text):
                self.judged(text, 1, 'BROKEN', fields=fields)
        self.judged(summary(failures=1, scenario='cancel'), 1, 'FAILED', fields=fields)

    def test_harness_parse_script_crash_and_all_resource_leaks_are_fatal(self):
        for diagnostic in (
            'HARNESS_ERROR descendants survived command exit',
            'SCRIPT ERROR: Invalid call. Nonexistent function',
            'Parse Error: Expected end of statement',
            'ERROR: Failed to load script res://tests/reload_audio_capture.gd',
            'Compile Error: dependency failed',
            'WARNING: 12 ObjectDB instances were leaked at exit',
            'Leaked instance: AudioStreamPlaybackWAV:123',
            'ERROR: 2 resources still in use at exit',
            'WARNING: 3 RID allocations leaked at exit',
            'Orphan StringName: Master',
            'StringName: 1 unclaimed string names at exit',
            'handle_crash: Program crashed with signal 11',
            'FATAL: engine aborted',
        ):
            for failures, code in ((0, 0), (1, 1)):
                with self.subTest(diagnostic=diagnostic, failures=failures):
                    self.judged(summary(failures=failures) + diagnostic + '\n', code, 'BROKEN')

    def test_containment_errors_cannot_be_hidden_by_a_summary(self):
        for failures, code in ((0, 0), (1, 1)):
            self.judged(summary(failures=failures), code, 'BROKEN',
                        errors=['descendants survived command exit'])

    def test_control_state_distinguishes_caught_missed_and_crashed(self):
        for states, expected in ((['FAILED'], 'caught'), (['passed'], 'MISSED'),
                                 (['FAILED', 'passed'], 'MISSED'), (['BROKEN'], 'crashed'),
                                 (['FAILED', 'CRASHED'], 'crashed'), ([], 'MISSED')):
            with self.subTest(states=states):
                self.assertEqual(controls.control_state([('fixture', state, []) for state in states]), expected)


class MutationTests(PureCase):
    def test_maintained_audio_controls_have_unique_anchors_and_original_scenarios(self):
        expected_tests = {'A5': [controls.CAP], 'A6': [controls.CAP_CANCEL], 'A7': [controls.CAP]}
        inventory = []
        for cid, _, edits, _, tests in MAINTAINED_SOURCE:
            if cid not in expected_tests:
                continue
            self.assertEqual(tests, expected_tests[cid])
            for filename, old, new in edits:
                data = Path(filename).read_bytes()
                anchor, _, newlines = controls.mutation_bytes(data, old, new)
                count = data.count(anchor)
                inventory.append({'control': cid, 'path': filename, 'matches': count,
                                  'newlines': newlines,
                                  'source_sha256': hashlib.sha256(data).hexdigest(),
                                  'anchor_sha256': hashlib.sha256(anchor).hexdigest()})
                self.assertEqual(count, 1, (cid, filename, old))
                self.assertNotEqual(old, new)
        controls.write_json(self.directory / 'anchor-inventory.json', inventory)
        self.assertEqual(controls.BASELINE_TESTS, (controls.SEQ, controls.ART, controls.AUD, controls.CAP,
                                                  controls.CAP_CANCEL, controls.VIS, controls.VIS_REDUCED,
                                                  controls.DISC, controls.LIGHT))
        self.assertIn('--scenario=reload', controls.CAP[1])
        self.assertIn('--scenario=cancel', controls.CAP_CANCEL[1])
        self.assertIn('--step=2', controls.VIS[1])

    def test_byte_restoration_preserves_bom_crlf_and_non_ascii(self):
        path = self.directory / 'actor.gd'
        original = b'\xef\xbb\xbf# caf\xc3\xa9\r\n\tanchor\r\n# tail\r\n'
        path.write_bytes(original)
        changes = controls.apply_mutations([(str(path), '\tanchor', '\tmutant')])
        self.assertNotEqual(path.read_bytes(), original)
        self.assertEqual(changes[0]['matches'], 1)
        controls.restore_files({path: original})
        self.assertEqual(path.read_bytes(), original)
        controls.write_json(self.directory / 'restoration.json', {
            'before_sha256': hashlib.sha256(original).hexdigest(),
            'after_sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'changes': changes})

    def test_all_anchors_are_preflighted_exactly_once_before_any_write(self):
        first, second = self.directory / 'first.gd', self.directory / 'second.gd'
        for bad in ('absent', 'anchor anchor'):
            with self.subTest(bad=bad):
                first.write_bytes(b'anchor\n')
                second.write_text(bad, encoding='utf-8')
                with self.assertRaisesRegex(ValueError, 'exactly one anchor'):
                    controls.apply_mutations([(str(first), 'anchor', 'mutant'), (str(second), 'anchor', 'mutant')])
                self.assertEqual(first.read_bytes(), b'anchor\n')
                self.assertEqual(second.read_text(), bad)

    def test_multiline_crlf_anchor_is_exact_and_inserted_lines_keep_crlf(self):
        path = self.directory / 'actor.gd'
        original = b'\xef\xbb\xbffirst\r\n\tanchor one\r\n\tanchor two\r\nlast\r\n'
        path.write_bytes(original)
        changes = controls.apply_mutations([(str(path), '\tanchor one\n\tanchor two\n', '\tmutant one\n\tmutant two\n')])
        self.assertEqual(path.read_bytes(), original.replace(b'anchor', b'mutant'))
        self.assertEqual(changes[0]['newlines'], 'CRLF')
        controls.restore_files({path: original})
        self.assertEqual(path.read_bytes(), original)

    def test_duplicate_anchor_across_lf_and_crlf_is_invalid(self):
        path = self.directory / 'actor.gd'
        original = b'\tanchor\n\tanchor\r\n'
        path.write_bytes(original)
        with self.assertRaisesRegex(ValueError, 'found 2'):
            controls.apply_mutations([(str(path), '\tanchor\n', '\tmutant\n')])
        self.assertEqual(path.read_bytes(), original)

    def test_empty_and_noop_mutations_are_invalid(self):
        path = self.directory / 'actor.gd'
        path.write_bytes(b'anchor')
        for old, new in (('', 'mutant'), ('anchor', 'anchor')):
            with self.subTest(old=old, new=new), self.assertRaises(ValueError):
                controls.apply_mutations([(str(path), old, new)])
        self.assertEqual(path.read_bytes(), b'anchor')


class HarnessTests(PureCase):
    def setUp(self):
        super().setUp()
        self.checkout = self.directory / 'disposable-checkout'
        self.checkout.mkdir()
        selected = [control for control in MAINTAINED_SOURCE if control[0] in ('A5', 'A6', 'A7')]
        paths = {controls.ACTOR, controls.PHASES, controls.AUDIO, controls.CAPTURE_SCRIPT}
        mapping = {path: str(self.checkout / Path(path).name) for path in paths}
        contents = {path: b'\xef\xbb\xbf# synthetic fixture, not a Godot program\n' for path in mapping.values()}
        for _, _, edits, _, _ in selected:
            for path, old, _ in edits:
                if old.encode() not in contents[mapping[path]]:
                    contents[mapping[path]] += old.encode() + b'\n'
        for path, data in contents.items():
            Path(path).write_bytes(data + b'# unchanged CRLF tail: caf\xc3\xa9\r\n')
        for constant in ('ACTOR', 'PHASES', 'AUDIO', 'CAPTURE_SCRIPT'):
            self.patched(constant, mapping[getattr(controls, constant)])
        self.patched('SOURCE', [(cid, what, [(mapping[path], old, new) for path, old, new in edits], env, tests)
                               for cid, what, edits, env, tests in selected])
        self.patched('CLIPS', [])
        self.patched('REPO', str(self.checkout))
        glb = self.checkout / 'relay_ar_arms.glb'
        glb.write_bytes(b'fixture GLB\x00\xff')
        self.patched('GLB', str(glb))
        self.originals = {Path(path): Path(path).read_bytes() for path in contents}
        self.originals[glb] = glb.read_bytes()
        csv = self.checkout / 'docs/reports/media/art-v9/hands/logs/clip_contact.csv'
        csv.parent.mkdir(parents=True)
        csv.write_text('synthetic contact CSV; never parsed by a native process\n')
        self.command_builder = self.patched('godot_command', side_effect=lambda args, **kw: [
            'fixture Godot with spaces.exe', '--path', str(kw['root'] / 'game'), *args])
        self.env_builder = self.patched('godot_environment', side_effect=lambda **kw: {
            **kw['env'], 'PORTABLE_FIXTURE': 'true'})
        self.process = self.patched('run_process', side_effect=self.fake_process)
        self.events = []
        self.inject = lambda role, control, command: {}
        self.calls = 0

    def fake_process(self, command, *, cwd, env, log, result_path, timeout):
        parts = result_path.parent.name.split('-')
        role, control = parts[1], parts[2] if parts[1] == 'mutant' else None
        failures = 1 if role == 'mutant' else 0
        code = 1 if failures else 0
        if '--script' in command:
            script = command[command.index('--script') + 1].rsplit('/', 1)[-1]
            tag = controls.SUMMARY_TAGS[script]
        else:
            tag = 'RELOAD_CONTACT_TEST'
        scenario = next((arg.split('=', 1)[1] for arg in command if arg.startswith('--scenario=')), 'reload')
        text = ('ERROR: expected fixture assertion\nFAIL expected fixture assertion\n' if failures else '')
        text += summary(tag, failures=failures, scenario=scenario, reduced='true' if '--reduced' in command else 'false')
        override = self.inject(role, control, command)
        if 'raise' in override:
            raise override['raise']
        code, text = override.get('code', code), override.get('output', text)
        log.write(text)
        log.flush()
        receipt = override.get('receipt', {'complete': True, 'exit': code, 'errors': []})
        if receipt is not None:
            controls.write_json(result_path, receipt)
        out_args = [arg for arg in command if arg.startswith('--out=')]
        if out_args and override.get('artifacts', True):
            capture = Path(out_args[0].split('=', 1)[1])
            self.assertEqual(list(capture.iterdir()), [], 'capture must be fresh before invocation')
            (capture / ('mix_%s.wav' % scenario)).write_bytes(b'RIFF synthetic WAV fixture, not real audio')
            (capture / ('voices_%s.csv' % scenario)).write_text('event,voice\nfixture,0\n')
            (capture / ('report_%s.txt' % scenario)).write_text('synthetic report\n' + text)
        self.events.append({'role': role, 'control': control, 'command': list(command), 'exit': code,
                            'source_sha256': controls.hashes({path: path.read_bytes() for path in self.originals})})
        self.assertEqual(Path(cwd), self.checkout)
        if '--script' in command and self.env_builder.called:
            self.assertEqual(env['PORTABLE_FIXTURE'], 'true')
        return code

    def call_main(self, extra=(), *, baseline=True, raw=True):
        self.calls += 1
        self.out = self.directory / ('raw-%d' % self.calls)
        self.log = self.directory / ('summary-%d.log' % self.calls)
        arguments = ['--only', 'A5,A6,A7', '--log', str(self.log), *extra]
        if raw:
            arguments += ['--raw-out', str(self.out)]
        if not baseline:
            arguments.append('--no-baseline')
        stdout, stderr = io.StringIO(), io.StringIO()
        try:
            with patch('sys.stdout', stdout), patch('sys.stderr', stderr):
                return controls.main(arguments)
        finally:
            (self.directory / ('console-%d.txt' % self.calls)).write_text(stdout.getvalue() + stderr.getvalue(), encoding='utf-8')
            controls.write_json(self.directory / ('invocations-%d.json' % self.calls), self.events)

    def assert_restored(self):
        for path, data in self.originals.items():
            self.assertEqual(path.read_bytes(), data, str(path))
        after = json.loads((self.out / 'sources-after.json').read_text())
        self.assertTrue(after['byte_restored'])
        before = json.loads((self.out / 'sources-before.json').read_text())
        self.assertEqual(before['sources'], after['sources'])

    def result(self):
        return json.loads((self.out / 'result.json').read_text())

    def test_all_original_baselines_then_three_controls_with_unique_raw_captures(self):
        self.assertEqual(self.call_main(), 0)
        baseline = [event for event in self.events if event['role'] == 'baseline']
        self.assertEqual(len(baseline), 10)  # All nine Godot groups plus existing contact CSV.
        self.assertEqual([row[0] for row in self.result()['baseline']],
                         [test[0] for test in controls.BASELINE_TESTS] + ['contact'])
        self.assertEqual(self.result()['controls'], [['A5', 'caught'], ['A6', 'caught'], ['A7', 'caught']])
        original_hashes = controls.hashes(self.originals)
        self.assertTrue(all(event['source_sha256'] == original_hashes for event in baseline))
        self.assertTrue(all(event['source_sha256'] != original_hashes for event in self.events[10:]))
        self.assertFalse(any('--import' in event['command'] for event in self.events))
        captures = [Path(arg.split('=', 1)[1]) for event in self.events for arg in event['command'] if arg.startswith('--out=')]
        self.assertEqual(len(captures), 5)  # baseline reload/cancel, then A5/A6/A7
        self.assertEqual(len(set(captures)), 5)
        self.assertTrue(all(len(list(path.iterdir())) == 3 for path in captures))
        attempts = sorted(self.out.glob('*/attempt.json'))
        self.assertEqual(len(attempts), 13)
        for path in attempts:
            record = json.loads(path.read_text())
            self.assertIn(record['role'], ('baseline', 'mutant'))
            self.assertEqual(record['control'] is None, record['role'] == 'baseline')
            self.assertTrue((path.parent / 'native.log').is_file())
            self.assertTrue((path.parent / 'process.json').is_file())
            self.assertTrue((path.parent / 'command.json').is_file())
            self.assertTrue((path.parent / 'assessment.json').is_file())
            self.assertEqual(json.loads((path.parent / 'command.json').read_text())['command'], record['command'])
        self.assert_restored()

    def test_nonzero_passing_baseline_blocks_mutations_but_keeps_all_baseline_attempts(self):
        self.inject = lambda role, control, cmd: {'code': 1} if 'res://tests/reload_audio_test.gd' in cmd else {}
        self.assertEqual(self.call_main(), 2)
        self.assertEqual(len(self.events), 10)
        self.assertEqual(self.result()['controls'], [])
        self.assertIn('BASELINE FAILS', self.log.read_text())
        self.assertTrue(all(event['role'] == 'baseline' for event in self.events))
        self.assertEqual(len(list(self.out.glob('*/attempt.json'))), 10)
        self.assert_restored()

    def test_baseline_assertion_error_or_leak_is_not_waived(self):
        self.inject = lambda role, control, cmd: {
            'output': summary('RELOAD_AUDIO_TEST') + 'WARNING: ObjectDB instances leaked at exit\n'
        } if 'res://tests/reload_audio_test.gd' in cmd else {}
        self.assertEqual(self.call_main(), 2)
        self.assertEqual(self.result()['controls'], [])
        self.assertIn('unsafe native output', self.log.read_text())
        self.assert_restored()

    def test_mutant_crash_retained_as_crash_not_caught_with_later_controls_continuing(self):
        self.inject = lambda role, control, cmd: {'code': 139, 'output': 'Segmentation fault\n'} if control == 'A6' else {}
        self.assertEqual(self.call_main(baseline=False), 1)
        self.assertEqual(self.result()['controls'], [['A5', 'caught'], ['A6', 'crashed'], ['A7', 'caught']])
        attempt = next(self.out.glob('*-A6-*/attempt.json'))
        record = json.loads(attempt.read_text())
        self.assertEqual(record['exit'], 139)
        self.assertEqual((attempt.parent / 'native.log').read_text(), 'Segmentation fault\n')
        self.assert_restored()

    def test_raw_failure_log_is_streamed_and_never_truncated(self):
        message = 'complete failure evidence ' * 2500
        text = 'ERROR: ' + message + '\nFAIL ' + message + '\n' + summary(failures=1)
        self.inject = lambda role, control, cmd: {'output': text} if control == 'A5' else {}
        self.assertEqual(self.call_main(baseline=False), 0)
        log = next(self.out.glob('*-A5-*/native.log'))
        self.assertEqual(log.read_text(encoding='utf-8'), text)
        self.assertGreater(log.stat().st_size, 50000)
        self.assert_restored()

    def test_containment_receipt_error_cannot_count_as_caught(self):
        self.inject = lambda role, control, cmd: {
            'receipt': {'complete': True, 'exit': 1, 'errors': ['descendants survived command exit']}
        } if control == 'A6' else {}
        self.assertEqual(self.call_main(baseline=False), 1)
        self.assertEqual(self.result()['controls'][1], ['A6', 'crashed'])
        self.assertIn('descendants survived command exit', self.log.read_text())
        self.assert_restored()

    def test_missing_capture_files_are_not_silently_accepted(self):
        self.inject = lambda role, control, cmd: {'artifacts': False} if control == 'A7' else {}
        self.assertEqual(self.call_main(baseline=False), 1)
        self.assertEqual(self.result()['controls'][2], ['A7', 'crashed'])
        self.assertIn('missing/empty capture artifact', self.log.read_text())
        self.assert_restored()

    def test_process_launch_error_retains_attempt_and_restores_source_bytes(self):
        self.inject = lambda role, control, cmd: {'raise': OSError('fixture launch denied')} if control == 'A5' else {}
        self.assertEqual(self.call_main(baseline=False), 1)
        path = next(self.out.glob('*-A5-*/attempt.json'))
        self.assertIn('HARNESS_ERROR fixture launch denied', (path.parent / 'native.log').read_text())
        self.assertFalse((path.parent / 'process.json').exists())  # Never fabricate a clean receipt.
        self.assertEqual(json.loads((path.parent / 'assessment.json').read_text())['state'], 'CRASHED')
        self.assert_restored()

    def test_interruption_retains_raw_attempt_and_restores_all_bytes(self):
        self.inject = lambda role, control, cmd: {'raise': KeyboardInterrupt('fixture interrupted')} if control == 'A5' else {}
        with self.assertRaises(KeyboardInterrupt):
            self.call_main(baseline=False)
        path = next(self.out.glob('*-A5-*/attempt.json'))
        self.assertIn('HARNESS_ERROR KeyboardInterrupt', (path.parent / 'native.log').read_text())
        self.assertEqual(self.result()['exit'], 2)
        self.assert_restored()

    def test_invalid_anchor_fails_control_without_partial_mutation(self):
        actor = Path(controls.ACTOR)
        old = next(control for control in controls.SOURCE if control[0] == 'A6')[2][1][1]
        actor.write_bytes(actor.read_bytes().replace(old.encode(), b'# anchor deliberately drifted\n'))
        self.originals[actor] = actor.read_bytes()
        self.assertEqual(self.call_main(baseline=False), 1)
        self.assertEqual(self.result()['controls'][1], ['A6', 'invalid'])
        self.assertEqual([event['control'] for event in self.events], ['A5', 'A7'])
        self.assertIn('exactly one anchor', (self.out / 'control-A6.json').read_text())
        self.assert_restored()

    def test_stale_raw_directory_is_rejected_without_overwriting_or_launching(self):
        raw = self.directory / 'raw-1'
        raw.mkdir()
        sentinel = raw / 'previous-failure.log'
        sentinel.write_bytes(b'old failure evidence\x00\xff')
        self.assertEqual(self.call_main(), 2)
        self.process.assert_not_called()
        self.assertEqual(sentinel.read_bytes(), b'old failure evidence\x00\xff')
        self.assertEqual(list(raw.iterdir()), [sentinel])

    def test_existing_summary_log_is_exclusive(self):
        log = self.directory / 'summary-1.log'
        log.write_bytes(b'retain previous failure')
        self.assertEqual(self.call_main(), 2)
        self.process.assert_not_called()
        self.assertEqual(log.read_bytes(), b'retain previous failure')

    def test_existing_empty_raw_directory_is_allowed(self):
        (self.directory / 'raw-1').mkdir()
        self.assertEqual(self.call_main(baseline=False), 0)
        self.assert_restored()

    def test_legacy_mode_still_contains_processes_and_restores_bytes(self):
        self.assertEqual(self.call_main(baseline=False, raw=False), 0)
        self.command_builder.assert_not_called()
        self.env_builder.assert_not_called()
        self.assertEqual(len(self.events), 3)
        self.assertTrue(all(event['command'][0].endswith('scripts' + os.sep + 'godot.sh') for event in self.events))
        self.assertTrue(all(not any(arg.startswith('--out=') for arg in event['command']) for event in self.events))
        for path, original in self.originals.items():
            self.assertEqual(path.read_bytes(), original)


class ReceiptAndFreshnessTests(PureCase):
    def test_missing_invalid_and_mismatched_receipts_fail_closed(self):
        path = self.directory / 'process.json'
        self.assertTrue(controls.receipt_errors(path, 1))
        for receipt in ([], {}, {'complete': False, 'exit': 1, 'errors': []},
                        {'complete': True, 'exit': True, 'errors': []},
                        {'complete': True, 'exit': 0, 'errors': []},
                        {'complete': True, 'exit': 1, 'errors': 'not a list'},
                        {'complete': True, 'exit': 1, 'errors': [False]}):
            with self.subTest(receipt=receipt):
                path.write_text(json.dumps(receipt))
                self.assertTrue(controls.receipt_errors(path, 1))
        path.write_text('{incomplete receipt')
        self.assertTrue(controls.receipt_errors(path, 1))
        path.write_text(json.dumps({'complete': True, 'exit': 1, 'errors': []}))
        self.assertEqual(controls.receipt_errors(path, 1), [])

    def test_attempt_directory_cannot_be_reused_or_overwritten(self):
        old = self.directory / '001-baseline-audio'
        old.mkdir()
        sentinel = old / 'native.log'
        sentinel.write_bytes(b'previous raw log')
        runner = controls.AttemptRunner(self.directory, raw=True)
        with self.assertRaises(FileExistsError):
            runner.invoke('audio', controls.AUD[1], role='baseline', native=True)
        self.assertEqual(sentinel.read_bytes(), b'previous raw log')
        controls.run_process.assert_not_called()

    def test_caller_cannot_redirect_capture_into_older_evidence(self):
        runner = controls.AttemptRunner(self.directory, raw=True)
        with self.assertRaisesRegex(ValueError, 'owned by this invocation'):
            runner.invoke('audio', controls.CAP[1] + ['--out=old-evidence'], role='mutant', control='A5', native=True)
        controls.run_process.assert_not_called()


if __name__ == '__main__':
    unittest.main()
