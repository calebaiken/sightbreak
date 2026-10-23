#!/usr/bin/env python3
"""Independent source-only adversarial controls; synthetic native APIs only."""
import json
import copy
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(sys.argv.pop(1)).resolve()
sys.path.insert(0, str(ROOT / 'scripts'))
import macos_semantic_deploy as semantic
from test_macos_semantic_deploy import SemanticController
from test_macos_semantic_deploy import semantic_receipt
from test_macos_ax_read_only import synthetic_capture


class AdversarialController(SemanticController):
    def __init__(self, directory, attack):
        self.attack = attack
        self.identities = []
        self.post_times = []
        super().__init__(directory)

    def make_ui(self):
        base, harness = super().make_ui(), self
        class UI(base):
            def __init__(self, *args):
                super().__init__(*args)
                original = self.cg.CGEventPost
                original_trace = self.trace
                def trace(event, **details):
                    if (harness.attack.startswith('delay:') and event == 'cg_event_post_attempt'
                            and details['event_kind'] == harness.attack.split(':', 1)[1]):
                        harness.now += 5.001
                    return original_trace(event, **details)
                self.trace = trace
                def posted(tap, event):
                    harness.post_times.append((event[0], harness.now,
                        self.semantic_deploy_target.expires if getattr(self, 'semantic_deploy_target', None) is not None else None))
                    original(tap, event)
                    if event[0] == 5 and harness.attack.startswith('replace:'):
                        path = harness.directory / harness.attack.split(':', 1)[1]
                        raw = path.read_bytes()
                        before = path.stat()
                        retained = path.with_name(path.name + '.retained')
                        path.rename(retained)
                        path.write_bytes(raw)
                        os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns))
                        after = path.stat()
                        harness.identities.append((before.st_ino, after.st_ino))
                    if event[0] == 1 and harness.attack == 'down-post-exception':
                        raise RuntimeError('Independent exception after delivered OS down')
                self.cg.CGEventPost = posted
        return UI


class IndependentBoundaries(unittest.TestCase):
    def execute(self, attack):
        with tempfile.TemporaryDirectory() as temporary:
            harness = AdversarialController(Path(temporary).resolve() / 'synthetic', attack)
            code, result = harness.execute()
            return code, result, harness

    def test_same_byte_original_file_replacement_after_move_never_posts_down(self):
        for name in ('01-focused-menu.png', '01-focused-menu.json', 'semantic-deploy-ax.json'):
            with self.subTest(name=name):
                code, result, harness = self.execute('replace:' + name)
                self.assertTrue(all(first != second for first, second in harness.identities))
                print(json.dumps({'attack': name, 'code': code, 'posts': harness.native_posts,
                                  'inode_before_after': harness.identities, 'passed': result['passed']}))
                self.assertNotEqual(code, 0, 'Replaced original identity still authorized a complete click')
                self.assertEqual(harness.native_posts, [5])

    def test_fifo_is_rejected_without_reading(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary).resolve() / 'receipt.json'
            os.mkfifo(path)
            # Writer is bounded by this reader; keep a sentinel open so cleanup
            # never hangs if a corrected reader rejects before opening the FIFO.
            sentinel = os.open(path, os.O_RDWR | os.O_NONBLOCK)
            try:
                os.write(sentinel, b'{}')
                # read_text would wait for EOF while sentinel is open. Patch it
                # only to expose that production reaches the forbidden read.
                with patch.object(Path, 'read_text', return_value='{}') as read:
                    try:
                        semantic.read_public_json(path)
                    except RuntimeError:
                        pass
                    self.assertFalse(read.called, 'Special FIFO reached the ordinary unbounded read')
            finally:
                os.close(sentinel)

    def test_growth_after_stat_cannot_exceed_receipt_byte_bound(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary).resolve() / 'receipt.json'
            path.write_text('{}')
            original = Path.read_text
            def grows(current, *args, **kwargs):
                current.write_text(json.dumps({'pad': 'x' * (semantic.CAPS['receipt_bytes'] + 1)}))
                return original(current, *args, **kwargs)
            with patch.object(Path, 'read_text', grows):
                with self.assertRaises(RuntimeError):
                    semantic.read_public_json(path)

    def test_delivered_down_exception_releases_recorded_owned_button(self):
        code, result, harness = self.execute('down-post-exception')
        self.assertNotEqual(code, 0)
        self.assertEqual(harness.native_posts[:3], [5, 1, 2])
        self.assertFalse(harness.mouse_down)
        self.assertEqual(harness.active_ui.held, set())

    def test_trace_delay_after_semantic_check_cannot_post_expired_move_or_down(self):
        for kind in ('pointer_move', 'lmb_down'):
            with self.subTest(kind=kind):
                code, result, harness = self.execute('delay:' + kind)
                print(json.dumps({'delay_before': kind, 'code': code, 'post_times_kind_now_expires': harness.post_times}))
                expired = [row for row in harness.post_times if row[0] in (5, 1)
                           and row[2] is not None and row[1] >= row[2]]
                self.assertEqual(expired, [], 'Original trace work runs after freshness check and posts stale event')

    def test_native_identity_count_and_zero_event_types_fail_closed(self):
        receipt = semantic_receipt(12, [40, 60, 960, 568], 99, 'a' * 32, 10)
        receipt['snapshots'][-1]['nodes'][1]['frame_points'][1] = 320
        capture = synthetic_capture()
        binding = dict(pid=12, window=34, bounds=[40, 60, 960, 568], observer_pid=99,
                       nonce='a' * 32, started=10, finished=10.2, budget=5)
        def validate(value):
            semantic.private_shape(value)
            return semantic.validate_observation(value, capture, **binding)
        self.assertTrue(validate(receipt)['unique_semantic_candidate'])
        changes = {
            'window_pid_float': lambda value: value['snapshots'][-1]['windows'][0].update(pid=12.0),
            'cg_owner_float': lambda value: value['snapshots'][-1]['cg_after'][0].update(owner_pid=12.0),
            'examined_nodes_float': lambda value: value.update(examined_nodes=float(value['examined_nodes'])),
            'input_events_false': lambda value: value.update(input_events_posted=False),
            'permission_requests_false': lambda value: value.update(permission_requests_made=False),
        }
        for name, change in changes.items():
            with self.subTest(name=name):
                value = copy.deepcopy(receipt)
                change(value)
                with self.assertRaises(RuntimeError):
                    validate(value)


if __name__ == '__main__':
    unittest.main(verbosity=2)
