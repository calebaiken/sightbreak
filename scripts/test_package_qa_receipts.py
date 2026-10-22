#!/usr/bin/env python3
"""Verify raw receipt selection, byte fidelity, bounds and stable packaging."""
import hashlib
import json
from pathlib import Path
import random
import tempfile
import unittest
import zipfile

from package_qa_receipts import package


class ReceiptsTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.source = self.root / 'native-qa'
        self.source.mkdir()
        self.addCleanup(self.temporary.cleanup)

    def write(self, name, value):
        path = self.source / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(value)
        return path

    def test_all_receipts_reconstruct_and_repeat_exactly(self):
        expected = {'linux/source.json': b'{"source_commit":"actual-source-identity"}\n',
                    'offline-full-match/trace/events.jsonl': b'{"type":"match_result","winner":"attack"}\n',
                    'offline-full-match/state/offline_training.json': b'{"training_xp":150}\n',
                    'regressions/menu_focus.log': b'MENU_FOCUS_TEST checks=30 failures=0\n\n',
                    'macos-diagnostics/native.txt': b'Native diagnostic output\n'}
        for name, value in expected.items():
            self.write(name, value)
        for name in ('linux/sightbreak.x86_64', 'offline-full-match/final.png',
                     'qa.zip', 'state/cache/engine.json', '.godot/imported/cache.json',
                     '__pycache__/scratch.log', 'macos/SIGHTBREAK.app/Contents/resource.json', 'unrelated.txt'):
            self.write(name, b'Excluded payload')
        first, second = self.root / 'first.zip', self.root / 'second.zip'
        report = package(self.source, first)
        package(self.source, second)
        self.assertEqual(first.read_bytes(), second.read_bytes())
        self.assertEqual(report['files'], len(expected))
        self.assertLess(report['bytes'], report['bound_bytes'])
        with zipfile.ZipFile(first) as bundle:
            index = json.loads(bundle.read('qa-receipts-index.json'))
            self.assertEqual([record['path'] for record in index['files']], sorted(expected))
            self.assertEqual(len(bundle.namelist()), len(expected) + 1)
            for record in index['files']:
                actual = bundle.read(record['archive_path'])
                self.assertEqual(actual, expected[record['path']])
                self.assertEqual(record['sha256'], hashlib.sha256(actual).hexdigest())
                self.assertEqual(record['bytes'], len(actual))
                self.assertEqual((self.source / record['path']).read_bytes(), actual)

    def test_oversized_evidence_fails_without_partial_or_mutation(self):
        path = self.write('large.log', random.Random(17).randbytes(4096))
        original = path.read_bytes()
        output = self.root / 'oversize.zip'
        with self.assertRaisesRegex(RuntimeError, 'download bound'):
            package(self.source, output, max_bytes=1024)
        self.assertFalse(output.exists())
        self.assertEqual(path.read_bytes(), original)
        self.assertEqual(list(self.root.glob('sightbreak-qa-receipts-*')), [])

    def test_index_overhead_is_included_in_bound(self):
        self.write('receipt.json', b'{}')
        output = self.root / 'index-overflow.zip'
        with self.assertRaisesRegex(RuntimeError, 'download bound'):
            package(self.source, output, max_bytes=200)
        self.assertFalse(output.exists())

    def test_existing_output_and_source_output_are_rejected(self):
        self.write('source.json', b'{}')
        output = self.root / 'preserved.zip'
        output.write_bytes(b'Prior evidence')
        with self.assertRaisesRegex(RuntimeError, 'existing'):
            package(self.source, output)
        self.assertEqual(output.read_bytes(), b'Prior evidence')
        with self.assertRaisesRegex(RuntimeError, 'outside'):
            package(self.source, self.source / 'output.zip')

    def test_no_receipts_cannot_create_evidence_artifact(self):
        self.write('only.png', b'Screenshot belongs in original full QA artifact')
        with self.assertRaisesRegex(RuntimeError, 'No QA receipts'):
            package(self.source, self.root / 'empty.zip')

    @unittest.skipUnless(hasattr(Path, 'symlink_to'), 'Symlinks unavailable')
    def test_selected_symlink_is_rejected(self):
        outside = self.root / 'outside.json'
        outside.write_bytes(b'External file')
        link = self.source / 'linked.json'
        try:
            link.symlink_to(outside)
        except OSError as error:
            self.skipTest('Host does not permit symlink creation: ' + str(error))
        with self.assertRaisesRegex(RuntimeError, 'Symlinked QA receipt'):
            package(self.source, self.root / 'link.zip')


if __name__ == '__main__':
    unittest.main()
