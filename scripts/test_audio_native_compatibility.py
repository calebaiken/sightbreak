#!/usr/bin/env python3
"""Pure native-token replay and synthetic controls; never launches Godot."""
import copy
import hashlib
import json
import math
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

import analyze_audio_lifecycle as diagnostic
import native_log
import test_acquire_audio_lifecycle as acquisition_controls
from test_analyze_audio_lifecycle import complete_fixture, log

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / 'docs/reports/gauntlet/audio-exit-lifecycle/native-serialization-strict-r1'
CASES = json.loads((EVIDENCE / 'native-cases.json').read_text())


class NativeMixRateControls(unittest.TestCase):
    def test_actual_native_float_token_and_positive_integer_float_controls(self):
        native = json.loads(CASES['header']['text'][len(diagnostic.PREFIX):])
        self.assertIs(type(native['mix_rate']), float)
        self.assertEqual(native['mix_rate'], 44100.0)
        for rate in (native['mix_rate'], 44100, 48000.0, 0.5, 1, 1e308):
            rows = complete_fixture()
            rows[0]['mix_rate'] = rate
            with self.subTest(rate=rate):
                report = diagnostic.analyze(log(rows, leak=False))
                self.assertFalse(report['strict_raw_log_failed'])
                self.assertEqual(report['records'], len(rows))

    def test_boolean_nonfinite_nonpositive_and_wrong_types_are_rejected(self):
        for rate in (True, False, None, '44100.0', [], {}, 0, 0.0, -0.0,
                     -1, -0.5, math.nan, math.inf, -math.inf):
            rows = complete_fixture()
            rows[0]['mix_rate'] = rate
            with self.subTest(rate=rate), self.assertRaisesRegex(ValueError, 'Probe header is invalid'):
                diagnostic.analyze(log(rows, leak=False))
        rows = complete_fixture()
        del rows[0]['mix_rate']
        with self.assertRaisesRegex(ValueError, 'Probe header is invalid'):
            diagnostic.analyze(log(rows, leak=False))

    def test_native_float_compatibility_does_not_change_other_numeric_fields(self):
        for kind, field in (('header', 'schema'), ('header', 'sequence'),
                            ('header', 'process_frame'), ('header', 'physics_frame'),
                            ('header', 'usec'), ('object', 'wav.mix_rate')):
            rows = complete_fixture()
            rows[0]['mix_rate'] = 44100.0
            if field == 'wav.mix_rate':
                next(row for row in rows if row.get('class') == 'AudioStreamWAV')['wav']['mix_rate'] = 22050.0
            else:
                rows[0][field] = float(rows[0][field])
            with self.subTest(field=field), self.assertRaises(ValueError):
                diagnostic.analyze(log(rows))

    def test_native_float_keeps_chronology_final_seal_and_footer_checks(self):
        original = complete_fixture()
        original[0]['mix_rate'] = 44100.0
        backwards = copy.deepcopy(original)
        backwards[-1]['usec'] = 0
        missing_window = copy.deepcopy(original)
        del missing_window[8]
        postfinal = copy.deepcopy(original)
        postfinal.append(copy.deepcopy(original[-1]))
        for text in (log(backwards), log(missing_window), log(postfinal),
                     log(original).replace('checks=462', 'checks=461'),
                     log(original).replace(diagnostic.ENGINE, 'Godot Engine v4.6.3')):
            with self.subTest(text=text[-120:]), self.assertRaises(ValueError):
                diagnostic.analyze(text)


class StandaloneStringNameControls(unittest.TestCase):
    def test_every_actual_orphan_and_positive_summary_independently_fail(self):
        self.assertEqual(len(CASES['orphans']), 353)
        self.assertEqual(CASES['header']['line'], 17)
        self.assertEqual(CASES['summary']['line'], 7292)
        self.assertEqual(CASES['summary']['text'], 'StringName: 353 unclaimed string names at exit.')
        for case in [*CASES['orphans'], CASES['summary']]:
            for ending in ('\n', '\r\n', ''):
                with self.subTest(line=case['line'], ending=ending):
                    self.assertTrue(native_log.failed(case['text'] + ending))

    def test_orphan_names_and_zero_total_are_not_exempted(self):
        for name, static, total in (('Master', 0, 1), ('ReloadAudio', 0, 280),
                                    ('root/Player: 子 name (x)', 1, 0), ('Z', 3, 2)):
            text = f'Orphan StringName: {name} (static: {static}, total: {total})\n'
            with self.subTest(text=text):
                self.assertTrue(native_log.failed(text))
        for count in (1, 353, 1000000):
            self.assertTrue(native_log.failed(f'StringName: {count} unclaimed string names at exit.\n'))

    def test_zero_summary_quoted_and_embedded_markers_are_nonerrors(self):
        orphan = CASES['orphans'][0]['text']
        summary = CASES['summary']['text']
        for text in ('StringName: 0 unclaimed string names at exit.\n',
                     'StringName: 0 unclaimed string names at exit.\r\n',
                     'StringName reference ranking (from most to least referenced):\n',
                     'Out of 20 StringNames, 0 StringNames were never referenced during this run (0 times) (0.00%).',
                     'WorkerThreadPool: 3 threads, 1 max low-priority.\n',
                     'WARNING: Could not set V-Sync mode\n',
                     json.dumps({'example': orphan}), json.dumps({'example': summary}),
                     'Example: ' + orphan, 'Example: ' + summary,
                     '"' + orphan + '"', '"' + summary + '"',
                     orphan + ' example', summary + ' example'):
            with self.subTest(text=text):
                self.assertFalse(native_log.failed(text))

    def test_existing_error_patterns_still_fail(self):
        for text in ('SCRIPT ERROR: broken', 'ERROR: failed', 'Parse Error: invalid',
                     'WARNING: ObjectDB instances leaked at exit',
                     'Leaked instance: AudioStreamWAV:99 - Reference count: 1'):
            with self.subTest(text=text):
                self.assertTrue(native_log.failed(text))

    def test_standalone_failures_remain_untyped_and_do_not_claim_cause(self):
        rows = complete_fixture()
        rows[0]['mix_rate'] = 44100.0
        for case in (CASES['orphans'][0], CASES['summary']):
            with self.subTest(line=case['line']):
                report = diagnostic.analyze(log(rows, leak=False) + case['text'] + '\n')
                self.assertTrue(report['strict_raw_log_failed'])
                self.assertEqual(report['sample_status'], 'untyped_strict_failure')
                self.assertEqual(report['leaks'], [])
                self.assertIn('unknown', report['server_drain'])
                self.assertIn('unproven', report['cause'])

    def test_mocked_acquisition_rejects_float_header_with_each_standalone_failure(self):
        original = acquisition_controls.synthetic_suite
        for case in (CASES['orphans'][0], CASES['summary']):
            def synthetic_with_standalone(*args, **kwargs):
                return original(*args, **kwargs).replace('"mix_rate": 44100,', '"mix_rate": 44100.0,', 1) + case['text'] + '\n'
            with self.subTest(line=case['line']), tempfile.TemporaryDirectory() as tmp:
                with patch.object(acquisition_controls, 'synthetic_suite', side_effect=synthetic_with_standalone):
                    code, receipt, output, _ = acquisition_controls.AcquisitionControls().run_fake(Path(tmp), 'clean')
                self.assertEqual(code, 1)
                self.assertTrue(receipt['acquisition_integrity'])
                self.assertFalse(receipt['sample_strict_clean'])
                self.assertFalse(receipt['passed'])
                self.assertFalse(receipt['original_leak_blocker_resolved'])
                parsed = json.loads((output / 'analysis.json').read_text())
                self.assertTrue(parsed['strict_raw_log_failed'])
                self.assertEqual(parsed['sample_status'], 'untyped_strict_failure')


class PinnedGodotContractControls(unittest.TestCase):
    def test_retrieved_source_hashes_and_native_float_api_match(self):
        receipts = json.loads((EVIDENCE / 'upstream-retrieval.json').read_text())
        self.assertEqual(len(receipts), 4)
        for item in receipts:
            raw = (EVIDENCE / 'upstream' / item['path']).read_bytes()
            with self.subTest(path=item['path']):
                self.assertEqual(len(raw), item['bytes'])
                self.assertEqual(hashlib.sha256(raw).hexdigest(), item['sha256'])
                self.assertIn('/ed1daf0bf/', item['url'])
        xml = ET.parse(EVIDENCE / 'upstream/doc/classes/AudioServer.xml')
        self.assertEqual(xml.find('./methods/method[@name="get_mix_rate"]/return').attrib['type'], 'float')
        self.assertIn('virtual float get_mix_rate() const;', (EVIDENCE / 'upstream/servers/audio/audio_server.h').read_text())
        self.assertIn('float AudioServer::get_mix_rate() const {', (EVIDENCE / 'upstream/servers/audio/audio_server.cpp').read_text())

    def test_stringname_cleanup_source_defines_exact_native_formats(self):
        text = (EVIDENCE / 'upstream/core/string/string_name.cpp').read_text()
        self.assertIn('if (d->static_count.get() != d->refcount.get()) {', text)
        self.assertIn('Orphan StringName: %s (static: %d, total: %d)', text)
        self.assertIn('if (lost_strings) {\n\t\tprint_verbose(vformat("StringName: %d unclaimed string names at exit.", lost_strings));', text)


if __name__ == '__main__':
    unittest.main()
