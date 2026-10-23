#!/usr/bin/env python3
"""Explicit replay of retained actual-flow pure faults; no engine execution."""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

import acquire_audio_lifecycle as subject

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = ROOT / 'docs/reports/gauntlet/audio-exit-lifecycle/independent-wrapper-r1-337d82aa/review_controls.py'
spec = importlib.util.spec_from_file_location('retained_wrapper_controls', ORIGINAL)
retained = importlib.util.module_from_spec(spec); spec.loader.exec_module(retained)


class FinalRetainedBytesControls(unittest.TestCase):
    def assert_rejected_and_preserved(self, harness, code, report):
        self.assertEqual(code, 1); self.assertFalse(report['passed']); self.assertFalse(report['acquisition_integrity'])
        self.assertFalse(report['private_state_removed']); self.assertFalse(report['private_project_removed'])
        self.assertTrue(report['originals_preserved_due_integrity_failure'])
        self.assertTrue((harness.output/'private-state/data/produced.txt').is_file())
        self.assertTrue(report['finalization_errors'])

    def test_complete_positive_final_bytes_receipts_analysis_and_archive_agree(self):
        with tempfile.TemporaryDirectory() as tmp:
            h=retained.Harness(Path(tmp));code,r=h.run()
            self.assertEqual(code,0);self.assertTrue(r['phase_logs_sealed'])
            rows=json.loads((h.output/'final-phase-snapshots.json').read_text())
            self.assertEqual(len(rows),5);self.assertTrue(all(row['receipt_matches'] and row['matches_phase_snapshot'] for row in rows))
            analysis=json.loads((h.output/'analysis.json').read_text())
            suite=next(row for row in rows if row['label']=='input-mode')
            self.assertEqual(analysis['raw_log_sha256'],suite['sha256'])
            self.assertEqual(analysis['raw_log_bytes'],suite['bytes'])
            self.assertEqual(analysis['strict_raw_log_failed'],not suite['clean_log'])
            self.assertTrue(r['private_state_archive_verified'])
            self.assertEqual(json.loads((h.output/'private-state-final.json').read_text()),json.loads((h.output/'private-state-archive.json').read_text()))

    def test_original_late_suite_and_import_faults_fail_and_preserve(self):
        for mode,label in [('late-suite-leak','input-mode'),('late-import-leak','private-import')]:
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                h=retained.Harness(Path(tmp),mode);code,r=h.run();self.assert_rejected_and_preserved(h,code,r)
                rows=json.loads((h.output/'final-phase-snapshots.json').read_text())
                row=next(row for row in rows if row['label']==label)
                self.assertFalse(row['matches_phase_snapshot']);self.assertFalse(row['clean_log'])
                self.assertEqual(subject.sha(h.output/row['retained_log']),subject.sha(h.output/row['original_log']))

    def test_original_archive_fault_fails_and_keeps_actual_original_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            h=retained.Harness(Path(tmp));code,r=h.run(archive_fault=True);self.assert_rejected_and_preserved(h,code,r)
            self.assertEqual((h.output/'private-state/data/produced.txt').read_text(),'original produced private bytes\n')
            self.assertNotEqual(subject.sha(h.output/'private-state/data/produced.txt'),subject.sha(h.output/'produced-private-state/data/produced.txt'))
            self.assertFalse(r['private_state_archive_verified'])

    def test_every_phase_late_raw_drift_during_archive_is_rejected(self):
        original=subject.copy_owned_tree
        for label in ['engine-version','private-import','before-input-mode','input-mode','after-input-mode']:
            with self.subTest(label=label),tempfile.TemporaryDirectory() as tmp:
                h=retained.Harness(Path(tmp))
                def copy(source,destination,deadline):
                    original(source,destination,deadline)
                    with (h.output/(label+'.log')).open('a') as stream:stream.write('WARNING: ObjectDB instances leaked at exit\n')
                with patch.object(subject,'copy_owned_tree',side_effect=copy):code,r=h.run()
                self.assert_rejected_and_preserved(h,code,r);self.assertFalse(r['phase_logs_sealed'])
                seal=json.loads((h.output/'phase-seal.json').read_text())
                self.assertEqual(len(seal['checks']),5);self.assertTrue(seal['errors'])

    def test_missing_extra_corrupt_archive_and_source_change_preserve_originals(self):
        original=subject.copy_owned_tree
        for mode in ['missing','extra','corrupt','source-change']:
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                h=retained.Harness(Path(tmp))
                def copy(source,destination,deadline):
                    original(source,destination,deadline)
                    if mode=='missing':(destination/'data/produced.txt').unlink()
                    elif mode=='extra':(destination/'extra.txt').write_text('extra')
                    elif mode=='corrupt':(destination/'data/produced.txt').write_text('corrupt')
                    else:(source/'data/produced.txt').write_text('source changed during copy')
                with patch.object(subject,'copy_owned_tree',side_effect=copy):code,r=h.run()
                self.assert_rejected_and_preserved(h,code,r);self.assertFalse(r['private_state_archive_verified'])

    def test_phase_receipt_or_retained_snapshot_or_analysis_drift_is_rejected(self):
        original=subject.copy_owned_tree
        for mode in ['receipt','snapshot','analysis']:
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                h=retained.Harness(Path(tmp))
                def copy(source,destination,deadline):
                    original(source,destination,deadline)
                    if mode=='receipt':
                        path=h.output/'private-import.receipt.json';data=json.loads(path.read_text());data['clean_log']=False;path.write_text(json.dumps(data))
                    elif mode=='snapshot':(h.output/'final-phase-logs/input-mode.log').write_text('changed retained snapshot')
                    else:(h.output/'analysis.json').write_text('{}')
                with patch.object(subject,'copy_owned_tree',side_effect=copy):code,r=h.run()
                self.assert_rejected_and_preserved(h,code,r);self.assertFalse(r['phase_logs_sealed'])

    def test_uid_archive_corruption_is_rejected_before_original_deletion(self):
        original=shutil.copy2
        with tempfile.TemporaryDirectory() as tmp:
            h=retained.Harness(Path(tmp))
            def copy(source,destination,*args,**kwargs):
                result=original(source,destination,*args,**kwargs)
                if 'generated-uids' in Path(destination).parts:Path(destination).write_text('corrupt uid archive')
                return result
            with patch.object(subject.shutil,'copy2',side_effect=copy):code,r=h.run()
            self.assert_rejected_and_preserved(h,code,r)

    def test_archive_or_uid_drift_after_initial_archive_verification_is_rejected(self):
        original=subject.seal_phase_snapshots
        for mode in ['private-archive','uid-archive']:
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                h=retained.Harness(Path(tmp))
                def seal(*args):
                    original(*args)
                    target=(h.output/'produced-private-state/data/produced.txt' if mode=='private-archive'
                            else h.output/'generated-uids/tests/audio_lifecycle_probe.gd.uid')
                    target.write_text('changed after initial archive verification')
                with patch.object(subject,'seal_phase_snapshots',side_effect=seal):code,r=h.run()
                self.assert_rejected_and_preserved(h,code,r)


if __name__=='__main__':unittest.main()
