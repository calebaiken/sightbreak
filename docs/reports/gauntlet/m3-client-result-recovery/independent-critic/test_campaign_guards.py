#!/usr/bin/env python3
"""Independent pure checks: all native/server entrypoints are mocked."""
import importlib.util
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

SOURCE = Path('/workspace/sightbreak-client-result-recovery/scripts/validate_transaction_restart.py')
spec = importlib.util.spec_from_file_location('receipt_campaign_review', SOURCE)
campaign = importlib.util.module_from_spec(spec)
spec.loader.exec_module(campaign)


class Guards(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory(prefix='receipt-critic-')
        self.addCleanup(self.scratch.cleanup)
        self.path = Path(self.scratch.name)
        self.baseline = self.path / 'baseline'
        self.candidate = self.path / 'candidate'
        self.out = self.path / 'output'
        self.before = {'commit': 'frozen', 'game_tree': 'tree', 'status': ''}

    def run_main(self, extra=(), identity=None, imported=None, version=None):
        args = ['campaign', '--godot', '/never-run-godot', '--baseline', str(self.baseline),
                '--candidate', str(self.candidate), '--out', str(self.out), '--repetitions', '1', *extra]
        imported = imported or SimpleNamespace(returncode=0, stdout='', stderr='')
        with patch.object(sys, 'argv', args), \
             patch.object(campaign.subprocess, 'check_output', return_value=version or campaign.PINNED_GODOT), \
             patch.object(campaign.subprocess, 'run', return_value=imported), \
             patch.object(campaign, 'identity', side_effect=identity or [self.before, self.before]), \
             patch.object(campaign, 'lifecycle', return_value={}), \
             patch.object(campaign, 'run_case', return_value={'recovered': False}):
            campaign.main()

    def test_zero_and_negative_repetitions_reject(self):
        for value in ('0', '-2'):
            with self.subTest(value=value), self.assertRaises(SystemExit) as raised:
                self.run_main(['--repetitions', value])
            self.assertEqual(raised.exception.code, 2)
        self.assertFalse(self.out.exists())

    def test_output_inside_either_source_rejects(self):
        for source in (self.baseline, self.candidate):
            with self.subTest(source=source), self.assertRaises(SystemExit) as raised:
                self.run_main(['--out', str(source / 'evidence')])
            self.assertEqual(raised.exception.code, 2)

    def test_wrong_engine_rejects_before_output_creation(self):
        with self.assertRaises(SystemExit) as raised:
            self.run_main(version='4.6.3.stable')
        self.assertEqual(raised.exception.code, 2)
        self.assertFalse(self.out.exists())

    def test_clean_but_changed_commit_or_game_rejects(self):
        for field in ('commit', 'game_tree'):
            with self.subTest(field=field):
                after = dict(self.before, **{field: 'changed'})
                self.out = self.path / field
                with self.assertRaisesRegex(RuntimeError, 'Source changed'):
                    self.run_main(identity=[self.before, after])

    def test_dirty_source_rejects(self):
        with self.assertRaisesRegex(RuntimeError, 'Dirty source tree'):
            self.run_main(identity=[dict(self.before, status=' M unexpected')])

    def test_import_stdout_error_rejects_and_retains_output(self):
        original = 'Godot\nERROR: independent fake native failure\n'
        with self.assertRaisesRegex(RuntimeError, 'Import failed'):
            self.run_main(imported=SimpleNamespace(returncode=0, stdout=original, stderr=''))
        self.assertEqual((self.out / 'baseline-import.log').read_text(), original)


if __name__ == '__main__':
    unittest.main(verbosity=2)
