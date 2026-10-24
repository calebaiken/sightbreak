#!/usr/bin/env python3
"""Independent R2 checks using the unchanged R1 real-flow synthetic Harness."""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

OUT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('unchanged_r1', OUT/'unchanged_r1_controls.py')
retained = importlib.util.module_from_spec(spec)
spec.loader.exec_module(retained)
subject = retained.subject
WITNESSES = []


def save(h, name, code, report):
    target = OUT/'explicit'/name
    shutil.copytree(h.output, target, dirs_exist_ok=True)
    witness = dict(name=name, exit=code, report=report,
                   scope='Synthetic processes/source only; not an actual native result')
    (target/'independent-witness.json').write_text(json.dumps(witness, indent=2, sort_keys=True)+'\n')
    WITNESSES.append(witness)


class R2Controls(unittest.TestCase):
    def rejected(self, h, code, report):
        self.assertEqual(code, 1)
        self.assertFalse(report['passed'])
        self.assertFalse(report['acquisition_integrity'])
        self.assertTrue(report['finalization_errors'])
        self.assertFalse(report['private_state_removed'])
        self.assertFalse(report['private_project_removed'])
        self.assertTrue(report['originals_preserved_due_integrity_failure'])
        self.assertEqual((h.output/'private-state/data/produced.txt').read_text(),
                         'original produced private bytes\n')

    def archive_fault(self, name, mutation):
        with tempfile.TemporaryDirectory() as tmp:
            h = retained.Harness(Path(tmp))
            original = subject.copy_owned_tree
            def copy(source, destination, deadline):
                original(source, destination, deadline)
                mutation(h, source, destination)
            with patch.object(subject, 'copy_owned_tree', side_effect=copy):
                code, report = h.run()
            save(h, name, code, report)
            self.rejected(h, code, report)
            return report

    def test_original_archive_fault_now_rejects_and_preserves(self):
        with tempfile.TemporaryDirectory() as tmp:
            h = retained.Harness(Path(tmp)); code, report = h.run(archive_fault=True)
            save(h, 'original-archive-fault-corrected-requirement', code, report)
            self.rejected(h, code, report)
            self.assertFalse(report['private_state_archive_verified'])
            self.assertNotEqual(subject.sha(h.output/'private-state/data/produced.txt'),
                                subject.sha(h.output/'produced-private-state/data/produced.txt'))

    def test_clean_and_known_strict_leak_share_correct_integrity(self):
        for mode, expected_exit in [('clean', 0), ('leak', 1)]:
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as tmp:
                h = retained.Harness(Path(tmp), mode); code, report = h.run()
                save(h, 'boundary-'+mode, code, report)
                self.assertEqual(code, expected_exit)
                self.assertTrue(report['acquisition_integrity'])
                self.assertEqual(report['sample_strict_clean'], expected_exit == 0)
                self.assertTrue(report['phase_logs_sealed'])
                self.assertEqual(report['finalization_errors'], [])
                self.assertTrue(report['private_state_archive_verified'])
                self.assertFalse(report['original_leak_blocker_resolved'])
                self.assertTrue(report['private_state_removed'])
                rows = json.loads((h.output/'final-phase-snapshots.json').read_text())
                analysis = json.loads((h.output/'analysis.json').read_text())
                for row in rows:
                    raw = (h.output/row['retained_log']).read_bytes()
                    phase = next(p for p in report['phases'] if p['label'] == row['label'])
                    self.assertEqual(raw, (h.output/row['original_log']).read_bytes())
                    self.assertEqual(hashlib.sha256(raw).hexdigest(), phase['log_sha256'])
                    self.assertEqual(len(raw), phase['log_bytes'])
                    self.assertEqual(subject.failed(raw.decode()), not phase['clean_log'])
                    self.assertTrue(row['receipt_matches'] and row['matches_phase_snapshot'])
                    if row['label'] == 'input-mode':
                        self.assertEqual(analysis['raw_log_sha256'], phase['log_sha256'])
                        self.assertEqual(analysis['strict_raw_log_failed'], not phase['clean_log'])
                self.assertEqual(json.loads((h.output/'private-state-final.json').read_text()),
                                 json.loads((h.output/'private-state-archive.json').read_text()))

    def test_all_original_and_snapshot_logs_mutated_during_archive_reject(self):
        for label in ['engine-version', 'private-import', 'before-input-mode', 'input-mode', 'after-input-mode']:
            for form in ['original', 'snapshot']:
                with self.subTest(label=label, form=form):
                    def mutation(h, source, destination):
                        path = h.output/(label+'.log') if form == 'original' else h.output/'final-phase-logs'/(label+'.log')
                        with path.open('a') as stream:
                            stream.write('WARNING: ObjectDB instances leaked at exit\n')
                    report = self.archive_fault(label+'-'+form+'-drift', mutation)
                    self.assertFalse(report['phase_logs_sealed'])

    def test_all_persisted_phase_receipts_mutated_during_archive_reject(self):
        for label in ['engine-version', 'private-import', 'before-input-mode', 'input-mode', 'after-input-mode']:
            with self.subTest(label=label):
                def mutation(h, source, destination):
                    path = h.output/(label+'.receipt.json')
                    data = json.loads(path.read_text()); data['command'].append('--undeclared')
                    path.write_text(json.dumps(data))
                report = self.archive_fault(label+'-receipt-drift', mutation)
                self.assertFalse(report['phase_logs_sealed'])

    def test_analysis_drift_and_scanner_disagreement_reject(self):
        self.archive_fault('retained-analysis-drift', lambda h,s,d: (h.output/'analysis.json').write_text('{}'))
        original = subject.analyze
        def wrong(text):
            result = original(text); result['strict_raw_log_failed'] = not result['strict_raw_log_failed']; return result
        with tempfile.TemporaryDirectory() as tmp:
            h = retained.Harness(Path(tmp))
            with patch.object(subject, 'analyze', side_effect=wrong): code, report = h.run()
            save(h, 'scanner-analyzer-disagreement', code, report)
            self.rejected(h, code, report)
            self.assertTrue(any(e['stage'] == 'final_analysis' for e in report['finalization_errors']))

    def test_archive_missing_extra_and_source_drift_reject(self):
        mutations = {
            'missing': lambda h,s,d: (d/'data/produced.txt').unlink(),
            'extra': lambda h,s,d: (d/'unexpected').write_text('unexpected'),
            'source': lambda h,s,d: (s/'added-during-copy').write_text('unexpected')}
        for name, mutation in mutations.items():
            with self.subTest(name=name):
                report = self.archive_fault('archive-'+name, mutation)
                self.assertFalse(report['private_state_archive_verified'])

    def test_uid_archive_corrupt_missing_extra_reject(self):
        mutations = {
            'corrupt': lambda p: (p/'tests/audio_lifecycle_probe.gd.uid').write_text('changed'),
            'missing': lambda p: (p/'tests/audio_lifecycle_probe.gd.uid').unlink(),
            'extra': lambda p: (p/'unexpected.uid').write_text('uid://syntheticextra')}
        for name, mutate in mutations.items():
            with self.subTest(name=name):
                self.archive_fault('uid-'+name, lambda h,s,d: mutate(h.output/'generated-uids'))

    def test_archive_and_uid_changes_after_first_verification_reject(self):
        original = subject.seal_phase_snapshots
        for name in ['archive', 'uid']:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as tmp:
                h = retained.Harness(Path(tmp))
                def seal(*args):
                    original(*args)
                    target = h.output/('produced-private-state/data/produced.txt' if name == 'archive'
                                      else 'generated-uids/tests/audio_lifecycle_probe.gd.uid')
                    target.write_text('changed after initial verification')
                with patch.object(subject, 'seal_phase_snapshots', side_effect=seal): code, report = h.run()
                save(h, 'post-first-verification-'+name, code, report)
                self.rejected(h, code, report)

    def test_auxiliary_native_json_is_not_part_of_phase_seal(self):
        for label in ['before-input-mode', 'after-input-mode']:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as tmp:
                h = retained.Harness(Path(tmp))
                original = subject.copy_owned_tree
                def copy(source, destination, deadline):
                    original(source, destination, deadline)
                    path = h.output/(label+'.json'); data = json.loads(path.read_text())
                    data['driver'] = 'synthetic-changed-driver'; path.write_text(json.dumps(data))
                with patch.object(subject, 'copy_owned_tree', side_effect=copy): code, report = h.run()
                save(h, 'auxiliary-'+label+'-drift', code, report)
                # Characterization of a boundary, not an assertion that altered raw data is native proof.
                self.assertEqual(code, 0)
                self.assertEqual(report['native_before' if label == 'before-input-mode' else 'native_after']['driver'], 'Dummy')
                self.assertEqual(json.loads((h.output/(label+'.json')).read_text())['driver'], 'synthetic-changed-driver')


if __name__ == '__main__':
    result = unittest.main(exit=False, verbosity=2).result
    (OUT/'explicit-summary.json').write_text(json.dumps(WITNESSES, indent=2, sort_keys=True)+'\n')
    raise SystemExit(not result.wasSuccessful())
