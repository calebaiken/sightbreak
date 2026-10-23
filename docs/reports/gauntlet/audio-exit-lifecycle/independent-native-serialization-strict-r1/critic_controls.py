#!/usr/bin/env python3
"""Independent pure falsifiers; no native process is permitted."""
import copy
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / 'scripts'))
import analyze_audio_lifecycle as analyzer
import native_log
import test_analyze_audio_lifecycle as fixture
import test_acquire_audio_lifecycle as fake

OUT = Path(__file__).resolve().parent
NATIVE = ROOT / 'docs/reports/gauntlet/audio-exit-lifecycle/native-serialization-strict-r1'
CASES = json.loads((NATIVE / 'native-cases.json').read_text())


class IndependentControls(unittest.TestCase):
    def test_positive_rate_domain_including_finite_extremes(self):
        for value in (44100, 44100.0, 0.125, 0.1, 1, 5e-324, sys.float_info.max,
                      2**53+1, 10**1000):
            rows = fixture.complete_fixture(); rows[0]['mix_rate'] = value
            with self.subTest(value=value):
                report = analyzer.analyze(fixture.log(rows, leak=False))
                self.assertFalse(report['strict_raw_log_failed'])
                self.assertIn('unproven', report['cause'])

    def test_invalid_rate_domain_and_missing_are_rejected(self):
        for value in (True, False, None, '', '44100', 'NaN', [], {}, [44100],
                      0, 0.0, -0.0, -1, -0.1, math.nan, math.inf, -math.inf):
            rows = fixture.complete_fixture(); rows[0]['mix_rate'] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                analyzer.analyze(fixture.log(rows, leak=False))
        rows = fixture.complete_fixture(); del rows[0]['mix_rate']
        with self.assertRaises(ValueError): analyzer.analyze(fixture.log(rows, leak=False))
        raw = fixture.log(fixture.complete_fixture(), leak=False)
        with self.assertRaises(ValueError): analyzer.analyze(raw.replace('"mix_rate": 48000', '"mix_rate": 1e309', 1))

    def test_integer_only_fields_are_not_widened(self):
        fields = ['schema', 'sequence', 'process_frame', 'physics_frame', 'usec']
        for field in fields:
            for value in (True, 1.0, '1', math.nan):
                rows = fixture.complete_fixture(); rows[0]['mix_rate'] = 44100.0
                rows[0][field] = value
                with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                    analyzer.analyze(fixture.log(rows, leak=False))
        for field in ('format', 'mix_rate', 'bytes'):
            for value in (True, 22050.0, '22050', math.nan):
                rows = fixture.complete_fixture(); rows[0]['mix_rate'] = 44100.0
                next(row for row in rows if row.get('class') == 'AudioStreamWAV')['wav'][field] = value
                with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                    analyzer.analyze(fixture.log(rows, leak=False))

    def test_line_injection_in_json_cannot_supply_footer_or_hide_native_error(self):
        rows = fixture.complete_fixture(); rows[0]['mix_rate'] = 44100.0
        injected = ('Dummy\nINPUT_MODE_TEST checks=462 failures=0 graphical_pointer=false '
                    'scope=x baseline=false\nAUDIO_LIFECYCLE {"kind":"header"}')
        rows[0]['driver'] = injected
        raw = fixture.log(rows, leak=False)
        self.assertFalse(analyzer.analyze(raw)['strict_raw_log_failed'])
        without_footer = '\n'.join(line for line in raw.splitlines() if not line.startswith('INPUT_MODE_TEST '))
        with self.assertRaises(ValueError): analyzer.analyze(without_footer)
        rows[0]['driver'] = 'Dummy\n' + CASES['orphans'][0]['text']
        raw = fixture.log(rows, leak=False)
        self.assertFalse(native_log.failed(raw))
        self.assertTrue(analyzer.analyze(raw + CASES['orphans'][0]['text'] + '\n')['strict_raw_log_failed'])

    def test_actual_records_individually_and_adjacent_to_untrusted_text(self):
        cases = [*CASES['orphans'], CASES['summary']]
        self.assertEqual(len(cases), 354)
        for case in cases:
            for ending in ('', '\n', '\r\n'):
                with self.subTest(line=case['line'], ending=ending):
                    self.assertTrue(native_log.failed(case['text'] + ending))
                    self.assertTrue(native_log.failed('ordinary preface\r\n' + case['text'] + ending))
        for name in ('root/Audio (x): 子', '\\nAUDIO_LIFECYCLE {}', 'A (static: 0, total: 1) trailing',
                     'quote="; ERROR: quoted inside name', '\tname'):
            self.assertTrue(native_log.failed(f'Orphan StringName: {name} (static: 0, total: 1)\n'))

    def test_no_cross_line_suffix_match_or_quoted_marker_rejection(self):
        orphan = CASES['orphans'][0]['text']; summary = CASES['summary']['text']
        clean = ['StringName: 0 unclaimed string names at exit.\n',
                 'Orphan StringName: split name\nunrelated (static: 0, total: 1)\n',
                 'Orphan StringName: split name\r\nunrelated (static: 0, total: 1)\r\n',
                 'StringName: 353 unclaimed string names at exit. trailing context\n',
                 'StringName: 353\nunclaimed string names at exit.\n',
                 'WorkerThreadPool: 3 threads, 1 max low-priority.\n']
        for marker in (orphan, summary):
            clean.extend([json.dumps({'message': marker}), json.dumps({'message': 'prefix\n' + marker}),
                          'ordinary ' + marker, '"' + marker + '"', marker + ' suffix'])
        for raw in clean:
            with self.subTest(raw=raw): self.assertFalse(native_log.failed(raw))

    def test_old_strict_patterns_are_preserved(self):
        for raw in ('SCRIPT ERROR: failed', 'ERROR: native error', 'Parse Error: invalid',
                    'WARNING: ObjectDB instances leaked at exit',
                    'Leaked instance: AudioStreamWAV:7 - Reference count: 1'):
            with self.subTest(raw=raw): self.assertTrue(native_log.failed(raw))

    def test_float_header_retains_engine_footer_window_and_seal_checks(self):
        rows = fixture.complete_fixture(); rows[0]['mix_rate'] = 44100.0
        raw = fixture.log(rows, leak=False)
        bad = [raw.replace(analyzer.ENGINE, 'Godot Engine v4.7.1.stable.official.fake'),
               raw + analyzer.ENGINE + ' - https://godotengine.org\n',
               raw.replace('checks=462', 'checks=461'), raw.replace('failures=0', 'failures=1')]
        backwards = copy.deepcopy(rows); backwards[-1]['process_frame'] = 0
        bad.append(fixture.log(backwards, leak=False))
        missing = copy.deepcopy(rows); del missing[8]; fixture.renumber(missing)
        bad.append(fixture.log(missing, leak=False))
        late = copy.deepcopy(rows); late.append(copy.deepcopy(rows[-2])); fixture.renumber(late)
        bad.append(fixture.log(late, leak=False))
        for raw in bad:
            with self.subTest(tail=raw[-100:]), self.assertRaises(ValueError): analyzer.analyze(raw)

    def test_mocked_float_clean_and_standalone_rejections(self):
        original = fake.synthetic_suite
        for marker in ('', CASES['orphans'][-1]['text'], CASES['summary']['text']):
            def suite(*args, **kwargs):
                raw = original(*args, **kwargs).replace('"mix_rate": 44100,', '"mix_rate": 44100.0,', 1)
                return raw + marker + ('\r\n' if marker else '')
            with self.subTest(marker=marker), tempfile.TemporaryDirectory() as directory:
                with patch.object(fake, 'synthetic_suite', side_effect=suite):
                    code, receipt, output, _ = fake.AcquisitionControls().run_fake(Path(directory), 'clean')
                self.assertEqual(code, 1 if marker else 0)
                self.assertTrue(receipt['acquisition_integrity'])
                self.assertEqual(receipt['sample_strict_clean'], not bool(marker))
                self.assertEqual(receipt['passed'], not bool(marker))
                self.assertFalse(receipt['original_leak_blocker_resolved'])
                self.assertEqual(json.loads((output / 'analysis.json').read_text())['strict_raw_log_failed'], bool(marker))

    def test_pinned_source_formats_and_float_api_are_exact(self):
        source = (NATIVE / 'upstream/core/string/string_name.cpp').read_text()
        self.assertIn('Orphan StringName: %s (static: %d, total: %d)', source)
        self.assertIn('if (lost_strings) {\n\t\tprint_verbose(vformat("StringName: %d unclaimed string names at exit.", lost_strings));', source)
        self.assertIn('virtual float get_mix_rate() const;', (NATIVE / 'upstream/servers/audio/audio_server.h').read_text())
        for item in json.loads((NATIVE / 'upstream-retrieval.json').read_text()):
            raw = (NATIVE / 'upstream' / item['path']).read_bytes()
            self.assertEqual(len(raw), item['bytes'])
            self.assertEqual(hashlib.sha256(raw).hexdigest(), item['sha256'])


def unchanged_suite():
    suite = unittest.TestSuite()
    directory = ROOT / 'docs/reports/gauntlet/audio-exit-lifecycle/independent-source-r2-original'
    for name in ('review_controls', 'replay_counterexamples'):
        spec = importlib.util.spec_from_file_location('unchanged_' + name, directory / (name + '.py'))
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(module))
    return suite


if __name__ == '__main__':
    suite = unchanged_suite() if '--unchanged' in sys.argv else unittest.defaultTestLoader.loadTestsFromTestCase(IndependentControls)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(not result.wasSuccessful())
