"""Independent R2 semantic per-down controls; actual key/_input, fake User32."""
import importlib.util
import json
import os
from pathlib import Path
import sys
import unittest

root = sys.argv.pop(1)
saved_argv = sys.argv[:]
sys.argv = [sys.argv[0], root]
spec = importlib.util.spec_from_file_location('semantic_rig', Path(__file__).with_name('semantic_controls.py'))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
sys.argv = saved_argv


class BoundaryRig(m.Rig):
    def __init__(self):
        super().__init__()
        self.read_hook = None

    def IsWindowVisible(self, window):
        stage = self.semantic_stage()
        checks = self.receipt.get('down_checks', [])
        key = checks[-1]['key'] if stage == 'before_key_down' else None
        if self.read_hook:
            self.read_hook(stage, key)
        return super().IsWindowVisible(window)


class IndependentBoundaryControls(unittest.TestCase):
    def setUp(self):
        m.CURRENT_TEST = self._testMethodName

    def test_every_later_context_predicate_stops_before_second_down(self):
        for field, value in [('foreground', 99), ('owner', 99), ('visible', False), ('thread', 0), ('window', 99), ('pid', 99)]:
            with self.subTest(field=field):
                r = BoundaryRig()
                target = r.ui if field in ('window', 'pid') else r
                r.send_hook = lambda name, down: setattr(target, field, value) if down else None
                with self.assertRaises(RuntimeError): r.run(('w', 'd'))
                self.assertEqual(r.edges(), [('w', True), ('w', False)])
                self.assertEqual(r.receipt['attempted_keys'], ['w'])
                self.assertEqual(r.receipt['down_checks'][1]['status'], 'FAILED')

    def test_each_unowned_input_stops_before_second_down_without_owning_it(self):
        for name in ('a', 's', 'd', 'lmb'):
            with self.subTest(name=name):
                r = BoundaryRig()
                r.send_hook = lambda key, down: r.down.add(name) if down else None
                with self.assertRaises(RuntimeError): r.run(('w', 'd'))
                self.assertEqual(r.edges(), [('w', True), ('w', False)])
                self.assertEqual(r.down, {name})
                self.assertEqual(r.receipt['released_keys'], ['w'])
                self.assertFalse(r.receipt['release_complete'])

    def test_first_down_has_fresh_context_and_input_check(self):
        for field, value in [('foreground', 99), ('owner', 99), ('visible', False), ('thread', 0), ('window', 99), ('pid', 99), ('external', 'a')]:
            with self.subTest(field=field):
                r = BoundaryRig()
                def read(stage, key):
                    if stage == 'before_key_down':
                        if field == 'external': r.down.add(value)
                        else: setattr(r.ui if field in ('window', 'pid') else r, field, value)
                r.read_hook = read
                with self.assertRaises(RuntimeError): r.run()
                self.assertEqual(r.calls, [])
                self.assertEqual(r.receipt['attempted_keys'], [])
                self.assertEqual(r.receipt['down_checks'][0]['status'], 'FAILED')

    def test_later_unknown_read_and_cancellation_release_prior_owned_key(self):
        for error in (OSError('unknown'), KeyboardInterrupt(), SystemExit('cancel')):
            with self.subTest(error=type(error).__name__):
                r = BoundaryRig()
                def read(stage, key):
                    if stage == 'before_key_down' and key == 'd': raise error
                r.read_hook = read
                with self.assertRaises(type(error)): r.run(('w', 'd'))
                self.assertEqual(r.edges(), [('w', True), ('w', False)])
                self.assertFalse(r.down)
                self.assertTrue(r.receipt['release_complete'])
                self.assertEqual(r.receipt['down_checks'][-1]['error_type'], type(error).__name__)

    def test_late_first_or_later_check_consumes_fixed_hold_and_original_cap(self):
        for selected in ('w', 'd'):
            for deadline in (35, .15):
                with self.subTest(selected=selected, deadline=deadline):
                    r = BoundaryRig()
                    r.read_hook = lambda stage, key: setattr(r, 'now', r.now + .2) if stage == 'before_key_down' and key == selected else None
                    with self.assertRaises(TimeoutError): r.run(('w', 'd'), seconds=.1, deadline=deadline)
                    self.assertEqual(r.receipt['hold_until_monotonic'], .1)
                    self.assertEqual(r.edges(), [] if selected == 'w' else [('w', True), ('w', False)])
                    self.assertFalse(r.down)
                    self.assertEqual(r.receipt['status'], 'FAILED')

    def test_after_down_and_after_release_errors_and_interrupts_release_all(self):
        for stage in ('after_down', 'after_release'):
            for error in (OSError(stage), KeyboardInterrupt(), SystemExit('cancel ' + stage)):
                with self.subTest(stage=stage, error=type(error).__name__):
                    r = BoundaryRig()
                    r.semantic_read_error[stage] = error
                    with self.assertRaises(BaseException): r.run(('w', 'd'))
                    self.assertEqual(r.edges(), [('w', True), ('d', True), ('w', False), ('d', False)])
                    self.assertFalse(r.down)
                    self.assertEqual(len(r.receipt['edges']), 4)
                    self.assertEqual(r.receipt['status'], 'FAILED')

    def test_failed_up_does_not_skip_other_owned_up_even_with_context_loss(self):
        r = BoundaryRig()
        r.send_error['w', False] = KeyboardInterrupt()
        def read(stage, key):
            if stage == 'after_down': r.foreground = 99
        r.read_hook = read
        with self.assertRaises(RuntimeError): r.run(('w', 'd'))
        self.assertEqual(r.edges(), [('w', True), ('d', True), ('w', False), ('d', False)])
        self.assertEqual(len(r.receipt['release_errors']), 2)
        self.assertFalse(r.down)

    def test_per_edge_full_receipts_are_stable_and_hold_does_not_restart(self):
        r = BoundaryRig()
        r.read_hook = lambda stage, key: setattr(r, 'now', r.now + .01) if stage == 'before_key_down' else None
        names = ['w', 'd']
        r.run(names, seconds=.1)
        self.assertAlmostEqual(r.calls[2]['time'], .1)
        self.assertEqual(len(r.receipt['down_checks']), 2)
        for index, check in enumerate(r.receipt['down_checks']):
            self.assertEqual(check['status'], 'CHECKED')
            self.assertEqual(check['owned_keys'], names[:index])
            self.assertLessEqual(check['read_begin_monotonic'], check['read_end_monotonic'])
            state = check['os_states'][0]
            self.assertEqual((state['target_window'], state['expected_pid'], state['window_pid'], state['window_thread'], state['foreground_window']), (34, 12, 12, 56, 34))
            self.assertTrue(state['visible'])
            self.assertFalse(state['lmb_down'])
            self.assertEqual(set(state['keys_down']), {'w', 'a', 's', 'd'})
        names[:] = ['s']
        self.assertEqual(r.receipt['keys'], ['w', 'd'])


if __name__ == '__main__':
    result = unittest.main(exit=False, verbosity=2).result
    Path(os.environ['SIGHTBREAK_PULSE_RECEIPTS']).write_text(json.dumps(m.TRIALS, indent=2) + '\n')
    sys.exit(not result.wasSuccessful())
