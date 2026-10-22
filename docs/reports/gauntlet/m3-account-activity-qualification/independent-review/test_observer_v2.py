#!/usr/bin/env python3
"""Pure temporal counterexamples; these never qualify an actual match."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('owned_observer_v2', ROOT / 'observe_owned_postgres_v2.py')
observer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(observer)


class EvidenceTimingControls(unittest.TestCase):
    def test_real_first_trial_in_flight_row_remains_rejected(self):
        samples = [json.loads(line) for line in (ROOT / 'observer-attempt-1/postgres-samples.jsonl').read_text().splitlines()]
        tagged = next(row for row in samples if 'duplicate-replayed-unchanged' in row['checkpoints_seen'])
        checkpoint = tagged['checkpoints_seen']['duplicate-replayed-unchanged']
        # This actual older row had the new checkpoint tag. The tag is not proof.
        self.assertLess(tagged['database_utc'], checkpoint)
        with self.assertRaises(AssertionError):
            observer.verify_final_query_time(tagged, checkpoint, checkpoint)

    def test_after_checkpoint_query_accepts_actual_later_database_clock(self):
        row = dict(read_only='on', database_utc='2026-10-22T06:18:50.200000+00:00')
        observer.verify_final_query_time(row, '2026-10-22T06:18:50.187242+00:00', '2026-10-22T06:18:50.190000+00:00')

    def test_future_row_cannot_hide_a_query_requested_before_checkpoint(self):
        row = dict(read_only='on', database_utc='2026-10-22T06:18:50.200000+00:00')
        with self.assertRaises(AssertionError):
            observer.verify_final_query_time(row, '2026-10-22T06:18:50.187242+00:00', '2026-10-22T06:18:50.180000+00:00')

    def test_after_checkpoint_row_still_must_follow_query_request(self):
        row = dict(read_only='on', database_utc='2026-10-22T06:18:50.190000+00:00')
        with self.assertRaises(AssertionError):
            observer.verify_final_query_time(row, '2026-10-22T06:18:50.187242+00:00', '2026-10-22T06:18:50.195000+00:00')

    def test_read_write_query_rejects(self):
        row = dict(read_only='off', database_utc='2026-10-22T06:18:50.200000+00:00')
        with self.assertRaises(AssertionError):
            observer.verify_final_query_time(row, '2026-10-22T06:18:50.187242+00:00', '2026-10-22T06:18:50.190000+00:00')

    def test_identical_recovery_samples_are_all_retained(self):
        for checkpoint in ('earned-staged', 'database-restored-zero', 'duplicate-replayed-unchanged'):
            checkpoints = {'earned-staged': 'time', checkpoint: 'time'}
            self.assertEqual(sum(observer.retain_sample('unchanged', 'unchanged', checkpoints) for _ in range(20)), 20)

    def test_unchanged_gameplay_sample_is_compacted(self):
        self.assertFalse(observer.retain_sample('same', 'same', {}))
        self.assertTrue(observer.retain_sample('old', 'new', {}))

    def test_partial_checkpoint_is_unpublished_until_valid_utc_exists(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / 'duplicate-replayed-unchanged.json'
            for raw in ('{"at_utc":', '{"at_utc":null}', '{"at_utc":"bad"}', '{"at_utc":"2026-10-22T06:18:50"}'):
                path.write_text(raw)
                self.assertNotIn('duplicate-replayed-unchanged', observer.read_checkpoints(root))
            value = '2026-10-22T06:18:50.187242+00:00'
            path.write_text(json.dumps(dict(at_utc=value)))
            self.assertEqual(observer.read_checkpoints(root), {'duplicate-replayed-unchanged': value})


if __name__ == '__main__':
    unittest.main()
