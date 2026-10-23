#!/usr/bin/env python3
"""Strict native log controls using preserved engine output; stdlib only."""
import hashlib
import json
from pathlib import Path
import unittest

from native_log import failed


FIXTURES = Path(__file__).resolve().parent / 'fixtures' / 'native_log'
CORPUS_SHA256 = 'a50a819152083c3d73564f21a5f15d36571c1b79c7178831667092f07537a218'
DIAGNOSTICS_SHA256 = '0b763d8e87812ec6ea07183bd17f3566072fdb6b9811c62f26be5d5527475350'


class NativeLogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = (FIXTURES / 'input-mode.log').read_bytes()
        cls.lines = cls.raw.decode('utf-8').splitlines(keepends=True)
        cls.orphans = cls.lines[6938:7291]
        cls.summary = cls.lines[7291]

    def test_original_full_corpus_is_bound_and_rejected(self):
        provenance = json.loads((FIXTURES / 'provenance.json').read_text())
        self.assertEqual(len(self.raw), 2000315)
        self.assertEqual(hashlib.sha256(self.raw).hexdigest(), CORPUS_SHA256)
        self.assertEqual(provenance['corpus']['bytes'], len(self.raw))
        self.assertEqual(provenance['corpus']['sha256'], CORPUS_SHA256)
        self.assertEqual(len(self.lines), 7292)
        self.assertEqual(len(self.orphans), 353)
        self.assertEqual(sum(line.startswith('Orphan StringName: ') for line in self.lines), 353)
        diagnostics = ''.join(self.orphans) + self.summary
        self.assertEqual(hashlib.sha256(diagnostics.encode()).hexdigest(), DIAGNOSTICS_SHA256)
        self.assertEqual(self.summary, 'StringName: 353 unclaimed string names at exit.\n')
        self.assertTrue(failed(self.raw.decode('utf-8')))

    def test_every_original_orphan_rejects_without_other_errors(self):
        for number, original in enumerate(self.orphans, 6939):
            self.assertTrue(original.startswith('Orphan StringName: '))
            for ending in ('\n', '\r\n', ''):
                with self.subTest(line=number, ending=repr(ending)):
                    self.assertTrue(failed('Native startup\n' + original.rstrip('\n') + ending))

    def test_positive_summary_rejects_without_orphan_details(self):
        for summary in (self.summary.rstrip('\n'),
                        'StringName: 1 unclaimed string names at exit.',
                        'StringName: 123456789 unclaimed string names at exit.'):
            for ending in ('\n', '\r\n', ''):
                with self.subTest(summary=summary, ending=repr(ending)):
                    self.assertTrue(failed('Native shutdown\n' + summary + ending))

    def test_quoted_embedded_split_and_zero_records_are_clean(self):
        for original in (self.orphans[0].rstrip('\n'), self.summary.rstrip('\n')):
            for text in (json.dumps({'message': original}), repr(original),
                         'Recorded text: ' + original, original + ' quoted suffix',
                         json.dumps({'message': 'before\n' + original + '\nafter'})):
                with self.subTest(text=text):
                    self.assertFalse(failed(text))
        for text in ('', 'Godot Engine v4.7.2\nWARNING: Could not set V-Sync mode',
                     'INPUT_MODE_TEST checks=462 failures=0\n',
                     'StringName: 0 unclaimed string names at exit.\n',
                     'StringName: 0 unclaimed string names at exit.\r\n',
                     'Orphan StringName: name\n (static: 0, total: 1)\n',
                     'Orphan StringName: name (static: 0,\n total: 1)\n'):
            with self.subTest(text=text):
                self.assertFalse(failed(text))

    def test_existing_error_and_leak_formats_still_reject(self):
        for text in ('ERROR: failed', 'SCRIPT ERROR: broken', 'Parse Error: invalid',
                     'WARNING: ObjectDB instances leaked at exit',
                     'WARNING: 4 ObjectDB instances were leaked at exit (run with `--verbose` for details).',
                     'Leaked instance: AudioStreamWAV'):
            with self.subTest(text=text):
                self.assertTrue(failed('Native startup\n' + text + '\n'))


if __name__ == '__main__':
    unittest.main()
