#!/usr/bin/env python3
"""Independent scanner falsifiers; accepts an exact source checkout as argv[1]."""
import importlib.util
import json
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(sys.argv.pop(1)).resolve()
spec = importlib.util.spec_from_file_location('reviewed_native_log', ROOT / 'scripts/native_log.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
failed = module.failed
raw = (ROOT / 'scripts/fixtures/native_log/input-mode.log').read_bytes().decode()
orphans = re.findall(r'^Orphan StringName: .*$', raw, re.M)


class CriticControls(unittest.TestCase):
    def test_original_census_and_native_terminators(self):
        self.assertEqual(len(orphans), 353)
        for row in orphans:
            for ending in ('', '\n', '\r\n'):
                with self.subTest(row=row, ending=repr(ending)):
                    self.assertTrue(failed('ordinary prefix\n' + row + ending + ('ordinary suffix' if ending else '')))

    def test_unclaimed_summary_independent_counts(self):
        for count in (1, 2, 10, 353, 2147483647, 999999999999999999999999):
            row = f'StringName: {count} unclaimed string names at exit.'
            for ending in ('', '\n', '\r\n'):
                with self.subTest(count=count, ending=repr(ending)):
                    self.assertTrue(failed('ordinary prefix\n' + row + ending))

    def test_quoted_and_embedded_all_originals(self):
        for row in orphans + ['StringName: 353 unclaimed string names at exit.']:
            for text in (json.dumps(row), json.dumps({'native_output': row}), repr(row),
                         'prefix ' + row, '\t' + row, row + ' suffix',
                         json.dumps({'native_output': 'before\n' + row + '\nafter'})):
                with self.subTest(text=text):
                    self.assertFalse(failed(text))

    def test_malformed_and_zero_near_matches(self):
        for text in ('StringName: 0 unclaimed string names at exit.',
                     'StringName: 0353 unclaimed string names at exit.',
                     'StringName: -1 unclaimed string names at exit.',
                     'StringName: 353.0 unclaimed string names at exit.',
                     'StringName: 353 unclaimed string names at exit',
                     'StringName: 353\nunclaimed string names at exit.',
                     'Orphan StringName: name (static: -1, total: 1)',
                     'Orphan StringName: name (static: 0, total: -1)',
                     'Orphan StringName: name (static: 0.0, total: 1)',
                     'Orphan StringName: name (static: 0,\n total: 1)',
                     'Orphan StringName: name\r (static: 0, total: 1)',
                     'Orphan StringName: name\n (static: 0, total: 1)',
                     'Orphan StringName:  (static: 0, total: 1)'):
            for ending in ('', '\n', '\r\n'):
                with self.subTest(text=text, ending=repr(ending)):
                    self.assertFalse(failed('ordinary prefix\n' + text + ending))

    def test_actual_failure_survives_surrounding_serialized_text(self):
        for row in (orphans[0], orphans[-1], 'StringName: 1 unclaimed string names at exit.'):
            for ending in ('\n', '\r\n'):
                text = json.dumps({'quoted': row}) + ending + row + ending + json.dumps({'quoted': row})
                self.assertTrue(failed(text))

    def test_legacy_error_positions_and_noise(self):
        for row in ('SCRIPT ERROR: deliberate', 'ERROR: deliberate', 'Parse Error: deliberate',
                    'WARNING: ObjectDB instances leaked at exit',
                    'WARNING: 4 ObjectDB instances were leaked at exit (run with `--verbose` for details).',
                    'Leaked instance: deliberate'):
            for ending in ('', '\n', '\r\n'):
                self.assertTrue(failed('ordinary prefix\n' + row + ending))
        for text in ('script error: no', 'ordinary ERROR: text', 'ordinary SCRIPT ERROR: text',
                     'WARNING: ObjectDB is active', 'INPUT_MODE_TEST checks=462 failures=0',
                     'Godot Engine v4.7.2.stable.official.ed1daf0bf',
                     'AudioStreamPlaybackWAV', 'Master', 'StringName', 'Orphan StringName:', ''):
            self.assertFalse(failed(text))


if __name__ == '__main__':
    unittest.main(verbosity=2)
