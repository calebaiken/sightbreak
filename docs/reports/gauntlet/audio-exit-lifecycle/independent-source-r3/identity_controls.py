#!/usr/bin/env python3
"""Pure identity checks against retained actual context and synthetic probes."""
from pathlib import Path
import json
import sys
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / 'scripts'))
import analyze_audio_lifecycle as diagnostic

OUT = Path(__file__).resolve().parent
OLD = OUT.parent / 'independent-source-r2-original'
ARM = Path('/workspace/sightbreak-v1-recovered/docs/reports/gauntlet/m2-mac-journey-recovered/native-actual-c088-independent/arm-39912086121-qa.zip')
BANNER = diagnostic.ENGINE + ' - https://godotengine.org'


class IdentityControls(unittest.TestCase):
    def test_both_original_arm_log_contexts_are_recognized(self):
        with zipfile.ZipFile(ARM) as archive:
            for path, line in [('regressions/input_mode.log', 1),
                               ('source-leak-verbose/repeat/input_mode.log', 2)]:
                text = archive.read(path).decode()
                with self.subTest(path=path):
                    self.assertEqual(diagnostic.engine_context(text)['banner_line'], line)
                    # Old uninstrumented logs still cannot replace probe evidence.
                    with self.assertRaises(ValueError): diagnostic.analyze(text)

    def test_complete_probe_with_actual_original_verbose_prefix_and_dummy(self):
        with zipfile.ZipFile(ARM) as archive:
            original = archive.read('source-leak-verbose/repeat/input_mode.log').decode()
        prefix = '\n'.join(original.splitlines()[:2]) + '\n'
        saved = (OLD / 'complete-default-headless.synthetic.log').read_text()
        complete = prefix + saved.split('\n', 1)[1]
        report = diagnostic.analyze(complete)
        self.assertEqual(report['driver'], 'Dummy')
        self.assertEqual(report['engine_context'], {
            'banner_line': 2,
            'verbose_preamble': ['WorkerThreadPool: 3 threads, 1 max low-priority.']})
        self.assertIn('no audible or physical qualification', report['audio_scope'])
        self.assertIn('required separately', report['driver_provenance'])
        self.assertTrue(report['strict_raw_log_failed'])
        self.assertEqual(len(report['forced_weak_snapshots']), 15)
        self.assertEqual(report['final_alive_player_ids'], ['11'])
        (OUT / 'actual-prefix-complete.synthetic.log').write_text(complete)
        (OUT / 'actual-prefix-complete.report.json').write_text(json.dumps(report, indent=2) + '\n')

    def test_engine_identity_falsifiers_are_rejected(self):
        text = (OLD / 'complete-default-headless.synthetic.log').read_text()
        cases = {
            'wrong': text.replace('ed1daf0bf', 'unknown'),
            'missing': text.replace(BANNER, ''),
            'partial': text.replace(BANNER, diagnostic.ENGINE),
            'quoted': text.replace(BANNER, '"' + BANNER + '"'),
            'buried': 'ordinary prefix\n' + text,
            'duplicate': BANNER + '\n' + text,
            'conflicting': text + 'Godot Engine vwrong\n',
            'split': text.replace(BANNER, 'Godot\nEngine v4.7.2'),
        }
        for name, value in cases.items():
            with self.subTest(case=name), self.assertRaises(ValueError):
                diagnostic.analyze(value)


if __name__ == '__main__':
    unittest.main()
