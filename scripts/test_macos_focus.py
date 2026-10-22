#!/usr/bin/env python3
"""Pure focus observer controls; synthetic samples never qualify native behavior."""
import types
import unittest
from unittest.mock import patch

import macos_native_input as adapter
from probe_macos_input import NativePrerequisiteBlocked
import verify_macos_menu as driver


class Clock:
    now = 0.0
    def monotonic(self):
        return self.now
    def sleep(self, seconds):
        self.now += seconds


class FocusControls(unittest.TestCase):
    def fixture(self, *, request=True, update_on_pump=False, active=False, overrun=False):
        # Invented fixture identities; neither ID is an actual-run observation.
        ui = object.__new__(adapter.MacMenuUI)
        ui.pid, ui.window, ui.bounds, ui.held = 4100, 88, [40, 32, 960, 568], set()
        state, clock, records = {'foreground': 4000}, Clock(), []
        ui.application = lambda: 1
        ui.message = lambda *args, **kwargs: request
        ui.trace = lambda event, **details: records.append((event, details))
        ui.focus_state = lambda: {'foreground_pid': state['foreground'], 'target_pid': ui.pid,
                                  'target_active': active, 'target_window': ui.window}
        ui.diagnostics = lambda: {'foreground_pid': state['foreground'], 'lmb_down': False, 'escape_down': False}
        def require_target():
            if state['foreground'] != ui.pid:
                raise RuntimeError('target not foreground')
        ui.require_target = require_target
        def pump(seconds):
            clock.now += 5.1 if overrun else seconds
            if update_on_pump:
                state['foreground'] = ui.pid
            return {'elapsed_seconds': seconds, 'return_code': 3, 'controller_main_run_loop': True}
        ui.pump_run_loop = pump
        return ui, clock, records, state

    def test_raw_before_and_pumped_after_samples_are_distinct(self):
        ui, clock, records, _ = self.fixture(update_on_pump=True, request=False)
        with patch.object(adapter.time, 'monotonic', clock.monotonic), patch.object(adapter.time, 'sleep', clock.sleep):
            ui.focus()
        sample = next(data for event, data in records if event == 'focus_sample')
        self.assertEqual(sample['before_run_loop']['foreground_pid'], 4000)
        self.assertEqual(sample['after_run_loop']['foreground_pid'], 4100)
        request = next(data for event, data in records if event == 'focus_request_returned')
        self.assertFalse(request['request_accepted'])
        self.assertEqual(request['activation_options'], 3)
        self.assertEqual(ui.held, set())

    def test_request_active_or_visible_window_never_substitutes_for_foreground(self):
        ui, clock, records, _ = self.fixture(request=True, active=True)
        with (patch.object(adapter.time, 'monotonic', clock.monotonic), patch.object(adapter.time, 'sleep', clock.sleep),
              self.assertRaisesRegex(RuntimeError, 'exact foreground PID')):
            ui.focus()
        self.assertAlmostEqual(clock.now, 5)
        self.assertFalse(any(event == 'focus_observed' for event, _ in records))
        self.assertEqual(records[-1][0], 'focus_timeout')
        self.assertEqual(ui.held, set())

    def test_target_after_five_second_deadline_is_rejected(self):
        ui, clock, records, _ = self.fixture(update_on_pump=True, overrun=True)
        with (patch.object(adapter.time, 'monotonic', clock.monotonic), patch.object(adapter.time, 'sleep', clock.sleep),
              self.assertRaisesRegex(RuntimeError, 'exact foreground PID')):
            ui.focus()
        self.assertGreater(clock.now, 5)
        self.assertFalse(any(event == 'focus_observed' for event, _ in records))

    def test_newer_diagnostics_focus_loss_cannot_be_ignored(self):
        ui, clock, records, _ = self.fixture(update_on_pump=True)
        ui.diagnostics = lambda: {'foreground_pid': 4000}
        with (patch.object(adapter.time, 'monotonic', clock.monotonic), patch.object(adapter.time, 'sleep', clock.sleep),
              self.assertRaisesRegex(RuntimeError, 'exact foreground PID')):
            ui.focus()
        self.assertFalse(any(event == 'focus_observed' for event, _ in records))

    def test_non_main_run_loop_is_rejected_without_running_it(self):
        ui = object.__new__(adapter.MacMenuUI)
        calls = []
        ui.cf = types.SimpleNamespace(CFRunLoopGetCurrent=lambda: 1, CFRunLoopGetMain=lambda: 2,
                                      CFRunLoopRunInMode=lambda *args: calls.append(args))
        with self.assertRaisesRegex(RuntimeError, 'controller main run loop'):
            ui.pump_run_loop(.05)
        self.assertEqual(calls, [])

    def test_input_guard_refreshes_public_observer_and_still_rejects_other_pid(self):
        ui = object.__new__(adapter.MacMenuUI)
        ui.pid = 4100
        order = []
        ui.require_window = lambda: order.append('window')
        ui.pump_run_loop = lambda seconds: order.append('run_loop')
        ui.foreground_pid = lambda: order.append('foreground') or 4000
        with self.assertRaisesRegex(RuntimeError, 'not foreground'):
            ui.require_target()
        self.assertEqual(order, ['window', 'run_loop', 'foreground'])

    def test_failed_background_capture_still_gets_focus_data_then_blocks_progress(self):
        order, result = [], {}
        def capture(*args, **kwargs):
            self.assertFalse(kwargs['require_focus'])
            self.assertIsNone(args[1])
            order.append('read_only_capture')
            raise NativePrerequisiteBlocked('helper capture denied')
        ui = types.SimpleNamespace(focus=lambda: order.append('focus_diagnostic'))
        with self.assertRaisesRegex(NativePrerequisiteBlocked, 'helper capture denied'):
            driver.background_then_focus(ui, capture, result, lambda *args, **kwargs: None)
        self.assertEqual(order, ['read_only_capture', 'focus_diagnostic'])
        self.assertEqual(result['background_capture_status'], 'BLOCKED_EXTERNALLY')

    def test_background_capture_does_not_turn_failed_focus_into_success(self):
        result = {}
        def focus():
            raise RuntimeError('exact foreground PID absent')
        ui = types.SimpleNamespace(focus=focus)
        with self.assertRaisesRegex(RuntimeError, 'exact foreground PID absent'):
            driver.background_then_focus(ui, lambda *args, **kwargs: None, result, lambda *args, **kwargs: None)
        self.assertEqual(result['background_capture_status'], 'PASS_CAPTURE_ONLY_NO_FOCUS_OR_INPUT')


if __name__ == '__main__':
    unittest.main()
