"""Fresh combined-boundary falsifiers using actual WinUI key/_input, fake OS."""
from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
import unittest

OUT = Path(__file__).resolve().parent
ROOT = Path(sys.argv.pop(1)).resolve()
saved = sys.argv[:]
sys.argv = [sys.argv[0], str(ROOT)]
spec = importlib.util.spec_from_file_location('combined_source_semantic_rig', OUT / 'semantic_controls.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
sys.argv = saved
import native_log

TRIALS = []


class StageRig(m.Rig):
    def __init__(self):
        super().__init__()
        self.hook = None

    def IsWindowVisible(self, window):
        checks = self.receipt.get('down_checks', [])
        stage = self.semantic_stage()
        name = checks[-1]['key'] if stage == 'before_key_down' else None
        if self.hook:
            self.hook(stage, name)
        return super().IsWindowVisible(window)


class FreshCombinedControls(unittest.TestCase):
    def setUp(self):
        m.CURRENT_TEST = self._testMethodName
        self.rigs = []

    def rig(self):
        r = StageRig()
        self.rigs.append(r)
        return r

    def tearDown(self):
        for r in self.rigs:
            TRIALS.append({'test': self._testMethodName, 'calls': deepcopy(r.calls),
                           'receipt': deepcopy(r.receipt), 'remaining_keys': sorted(r.down),
                           'finished': r.now})

    def test_callback_two_key_then_ordinary_key_then_next_pulse_has_no_leak(self):
        r = self.rig()
        traces = []
        fn, route, held = m.callback(r, lambda event, **data: traces.append((event, deepcopy(data), sorted(r.down))))
        first = fn(('w', 'd'), .125, 35)
        saved_first = deepcopy(first)
        r.ui.key('a', True)
        r.ui.key('a', False)
        second = fn(('s',), .1, 35)
        self.assertEqual(r.edges(), [('w', True), ('d', True), ('w', False), ('d', False),
                                     ('a', True), ('a', False), ('s', True), ('s', False)])
        self.assertFalse(r.down)
        self.assertFalse(held)
        self.assertIsNot(first, second)
        self.assertEqual(first, saved_first)
        self.assertEqual(len(route['native_pulses']), 2)
        self.assertTrue(all(row[2] == [] for row in traces if row[0].endswith('_after')))
        self.assertEqual([row['flags'] for row in r.calls], [8, 8, 10, 10, 8, 10, 8, 10])
        TRIALS.append({'test': self._testMethodName, 'route': deepcopy(route), 'traces': traces})

    def test_focus_loss_after_first_down_blocks_second_then_recovered_ordinary_key_works(self):
        r = self.rig()
        r.send_hook = lambda key, down: setattr(r, 'foreground', 99) if down else None
        with self.assertRaises(RuntimeError):
            r.run(('w', 'd'))
        self.assertEqual(r.edges(), [('w', True), ('w', False)])
        self.assertEqual(r.receipt['attempted_keys'], ['w'])
        self.assertEqual(r.receipt['down_checks'][-1]['status'], 'FAILED')
        saved_receipt = deepcopy(r.receipt)
        r.foreground, r.send_hook = 34, None
        r.ui.key('d', True)
        r.ui.key('d', False)
        self.assertFalse(r.down)
        self.assertEqual(r.receipt, saved_receipt)

    def test_ownership_loss_on_first_down_does_not_claim_unattempted_second_key(self):
        r = self.rig()
        r.send_hook = lambda key, down: setattr(r, 'owner', 99) if down else None
        with self.assertRaises(RuntimeError):
            r.run(('w', 'd'))
        self.assertEqual(r.edges(), [('w', True), ('w', False)])
        self.assertEqual(r.receipt['released_keys'], ['w'])
        self.assertFalse(r.receipt['release_complete'])
        self.assertEqual(r.receipt['down_checks'][-1]['os_states'][0]['window_pid'], 99)

    def test_late_second_check_respects_fixed_hold_and_absolute_cap(self):
        for seconds, deadline, delay in ((.1, 35, .11), (.25, .15, .2)):
            with self.subTest(seconds=seconds, deadline=deadline):
                r = self.rig()
                r.hook = lambda stage, name: setattr(r, 'now', r.now + delay) if stage == 'before_key_down' and name == 'd' else None
                with self.assertRaises(TimeoutError):
                    r.run(('w', 'd'), seconds=seconds, deadline=deadline)
                self.assertEqual(r.edges(), [('w', True), ('w', False)])
                self.assertEqual(r.receipt['hold_until_monotonic'], min(seconds, deadline))
                self.assertFalse(r.down)
                self.assertEqual(r.receipt['status'], 'FAILED')

    def test_callback_failed_up_retains_cleanup_ownership_and_error(self):
        r = self.rig()
        r.send_error['w', False] = OSError('fresh declared up failure')
        fn, route, held = m.callback(r, lambda *args, **kwargs: None)
        with self.assertRaises(RuntimeError):
            fn(('w', 'd'), .125, 35)
        receipt = route['native_pulses'][0]
        self.assertEqual(r.edges(), [('w', True), ('d', True), ('w', False), ('d', False)])
        self.assertEqual(held, {'w', 'd'})
        self.assertFalse(receipt['release_complete'])
        self.assertEqual(receipt['status'], 'FAILED')
        self.assertIn('fresh declared up failure', receipt['release_errors'][0])
        TRIALS.append({'test': self._testMethodName, 'route': deepcopy(route), 'held': sorted(held)})

    def test_returned_receipt_request_and_all_state_snapshots_are_stable(self):
        r = self.rig()
        names = ['w', 'd']
        returned = r.run(names)
        saved_receipt = deepcopy(returned)
        names[:] = ['a', 's']
        r.down.add('lmb')
        r.foreground = r.owner = r.ui.window = r.ui.pid = 99
        self.assertEqual(returned, saved_receipt)
        self.assertEqual(returned['keys'], ['w', 'd'])
        self.assertIsNot(returned['os_states'][0]['keys_down'], returned['os_states'][-1]['keys_down'])
        self.assertIsNot(returned['down_checks'][0]['owned_keys'], returned['down_checks'][1]['owned_keys'])
        self.assertEqual(returned['down_checks'][1]['owned_keys'], ['w'])

    def test_strict_stringname_guard_and_quoted_zero_controls(self):
        positives = ['Orphan StringName: Master (static: 0, total: 1)\n',
                     'StringName: 353 unclaimed string names at exit.\r\n']
        for text in positives:
            with self.subTest(text=text):
                self.assertTrue(native_log.failed(text))
        for text in ('StringName: 0 unclaimed string names at exit.\n',
                     'Recorded text: ' + positives[0], json.dumps({'message': positives[1]})):
            self.assertFalse(native_log.failed(text))

    def test_strict_falsifiers_reject_the_pre_stringname_weakening(self):
        tree = __import__('ast').parse((ROOT / 'scripts/native_log.py').read_text())
        call = next(n for n in __import__('ast').walk(tree) if isinstance(n, __import__('ast').Call) and isinstance(n.func, __import__('ast').Attribute) and n.func.attr == 'search')
        pattern = call.args[0].value
        weak = pattern.split('|^Orphan StringName:')[0]
        for text in ('Orphan StringName: Master (static: 0, total: 1)\n',
                     'StringName: 353 unclaimed string names at exit.\n'):
            self.assertTrue(native_log.failed(text))
            self.assertIsNone(re.search(weak, text, re.M))
        self.assertIsNotNone(re.search(weak, 'ERROR: retained original failure\n', re.M))


if __name__ == '__main__':
    assert sorted(os.sched_getaffinity(0)) == [4]
    result = unittest.main(exit=False, verbosity=2).result
    (OUT / 'combined-controls-receipts.json').write_text(json.dumps(TRIALS, indent=2) + '\n')
    (OUT / 'combined-controls-result.json').write_text(json.dumps({'source': '49ae54b0e4f5d880bdf06e4eb783a616b2dff684',
        'methods': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
        'cpu_affinity': sorted(os.sched_getaffinity(0))}, indent=2) + '\n')
    sys.exit(not result.wasSuccessful())
