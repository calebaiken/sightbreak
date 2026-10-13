import copy
from contextlib import closing
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from uuid import uuid4

from server.result_outbox import Outbox, MAX_PENDING_AGE, RETENTION, canonical, http_transport


def payload():
    return {'match_id': str(uuid4()), 'mode': 'ranked_5v5', 'started_at': '2026-01-01T00:00:00Z', 'ended_at': '2026-01-01T00:10:00Z', 'participants': [
        {'player_id': str(uuid4()), 'won': i < 5, 'active_seconds': 500, 'objective_contributions': 0, 'abandoned': False} for i in range(10)]}

class OutboxTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.box = Outbox(self.root / 'queue.sqlite', max_records=2)
    def tearDown(self): self.tmp.cleanup()
    def row(self):
        with closing(self.box.connect()) as db: return dict(db.execute('SELECT * FROM results').fetchone())
    def test_restart_and_exact_identity(self):
        data = payload(); self.box.enqueue(data, 0)
        restarted = Outbox(self.box.path)
        self.assertEqual(restarted.enqueue(data, 1), 'pending')
        different = copy.deepcopy(data); different['participants'][0]['won'] = False
        with self.assertRaises(ValueError): restarted.enqueue(different, 1)
        self.assertEqual(self.row()['payload'], canonical(data)[1])
    def test_retry_then_ack_without_duplicate_local_delivery(self):
        data = payload(); self.box.enqueue(data, 0); calls = []
        def fail(raw): calls.append(raw); return 503, b''
        def success(raw): calls.append(raw); return 200, json.dumps({'match_id': data['match_id'], 'rewards': [{}] * 10}).encode()
        self.assertTrue(self.box.deliver_one(fail, 0))
        self.assertFalse(self.box.deliver_one(success, 1))
        self.assertTrue(self.box.deliver_one(success, 2))
        self.assertEqual(calls[0], calls[1])
        self.assertEqual(self.row()['state'], 'committed')
        self.assertFalse(self.box.deliver_one(success, 100))
    def test_capacity_and_retention(self):
        self.box.enqueue(payload(), 0); self.box.enqueue(payload(), 1)
        with self.assertRaises(OverflowError): self.box.enqueue(payload(), 2)
        self.box.deliver_one(lambda _: (400, b''), 2)
        self.box.maintenance(RETENTION + 3)
        self.box.enqueue(payload(), RETENTION + 3)
    def test_pending_is_not_silently_pruned(self):
        self.box.enqueue(payload(), 0); self.box.maintenance(RETENTION * 2)
        self.assertEqual(self.row()['state'], 'pending')
        self.box.deliver_one(lambda _: (503, b''), MAX_PENDING_AGE + 1)
        self.assertEqual(self.row()['state'], 'dead')
    def test_spool_import_commit_before_unlink_and_partial_recovery(self):
        spool = self.root / 'spool'; spool.mkdir(); data = payload()
        source = spool / (data['match_id'] + '.json'); source.write_text(json.dumps(data))
        self.assertEqual(self.box.import_spool(spool), 1); self.assertFalse(source.exists())
        # Duplicate replay of a completed file is safely imported once.
        source.write_text(json.dumps(data)); self.assertEqual(self.box.import_spool(spool), 1)
        partial = spool / (str(uuid4()) + '.tmp'); partial.write_text('{')
        os.utime(partial, (0, 0)); self.box.import_spool(spool, 100)
        self.assertFalse(partial.exists())
        quarantined = partial.with_suffix(".tmp.invalid"); self.assertTrue(quarantined.exists())
        self.box.import_spool(spool, MAX_PENDING_AGE + 1); self.assertFalse(quarantined.exists())
    def test_producer_rename_during_scan(self):
        spool = self.root / 'spool'; spool.mkdir(); data = payload()
        source = spool / (data['match_id'] + '.tmp'); target = source.with_suffix('.json')
        source.write_text(json.dumps(data)); original = Path.stat; calls = 0
        def stat(path, *args, **kwargs):
            nonlocal calls
            if path == source:
                calls += 1
                if calls == 3: source.rename(target) # is_symlink, is_file, then age.
            return original(path, *args, **kwargs)
        with patch.object(Path, 'stat', stat): self.box.import_spool(spool)
        self.assertTrue(target.exists())
        self.assertEqual(self.box.import_spool(spool), 1)
        self.assertEqual(self.row()['payload'], canonical(data)[1])
    def test_capacity_keeps_spool(self):
        self.box.enqueue(payload()); self.box.enqueue(payload())
        spool = self.root / 'spool'; spool.mkdir(); data = payload(); source = spool / (data['match_id'] + '.json'); source.write_text(json.dumps(data))
        self.assertEqual(self.box.import_spool(spool), 0); self.assertTrue(source.exists())
    def test_bad_success_is_retried_redirect_is_terminal(self):
        self.box.enqueue(payload(), 0)
        self.box.deliver_one(lambda _: (200, b'{}'), 0)
        self.assertEqual(self.row()['state'], 'pending')
        self.box.deliver_one(lambda _: (302, b''), 2)
        self.assertEqual(self.row()['state'], 'dead')
    def test_payload_and_origin_limits(self):
        for invalid in ([], {}, {**payload(), 'server_key': 'must-not-persist'}):
            with self.assertRaises(ValueError): canonical(invalid)
        for origin in ('http://example.com', 'https://user:secret@example.com', 'https://example.com/path', 'https://example.com?token=x'):
            with self.assertRaises(ValueError): http_transport(origin, 'x' * 32)
        self.assertEqual(os.stat(self.box.path).st_mode & 0o777, 0o600)

if __name__ == '__main__': unittest.main()
