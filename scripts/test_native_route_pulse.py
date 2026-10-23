#!/usr/bin/env python3
"""Mocked OS/clock calls only. No native input, helper process or timing proof."""
import ast
import ctypes as C
from pathlib import Path
import unittest

from verify_integration_export import WinUI
from native_approach import approach_floor
from native_settings_route import relocate_settings_actor
from test_native_settings_route import SettingsWalker


class MockPulse:
    def __init__(self):
        self.now, self.events, self.down = 0., [], set()
        self.owner, self.foreground, self.visible = 12, 34, True
        self.edge_delay = .005
        self.up_delay = None
        self.error_down, self.error_up = set(), set()
        self.sleep_error, self.sleep_extra = None, 0
        self.state_delay, self.state_delays, self.state_reads, self.after_down_hook = 0, {}, 0, None
        self.ui = object.__new__(WinUI)
        self.ui.pid, self.ui.window = 12, 34
        parent = self
        class User:
            def IsWindowVisible(_, window):
                parent.state_reads += 1
                parent.now += parent.state_delay + parent.state_delays.get(parent.state_reads, 0)
                return parent.visible
            def GetWindowThreadProcessId(_, window, pointer):
                C.cast(pointer, C.POINTER(C.c_uint32))[0] = parent.owner
                return 56
            def GetForegroundWindow(_):
                return parent.foreground
            def GetAsyncKeyState(_, vk):
                return 0x8000 if (chr(vk).lower() if vk != 1 else 'lmb') in parent.down else 0
        self.ui.user = User()
        self.ui.key = self.key
        self.receipt = {}

    def key(self, name, down):
        self.events.append((name, down, self.now))
        self.now += self.up_delay if not down and self.up_delay is not None else self.edge_delay
        (self.down.add if down else self.down.discard)(name)
        if down and self.after_down_hook:
            self.after_down_hook()
        if name in (self.error_down if down else self.error_up):
            raise OSError('declared native edge failure')

    def sleep(self, seconds):
        if self.sleep_error:
            raise self.sleep_error
        self.now += seconds + self.sleep_extra

    def run(self, names=('d',), seconds=.125, deadline=35):
        return self.ui.key_pulse(names, seconds, deadline=deadline, receipt=self.receipt,
                                 clock=lambda: self.now, sleep=self.sleep)


class NativeRoutePulseControls(unittest.TestCase):
    def test_actual_method_keeps_edge_brackets_and_all_wasd_os_states(self):
        trial = MockPulse()
        receipt = trial.run()
        self.assertEqual(receipt['status'], 'API_RETURNED_WITH_OS_RELEASE')
        self.assertEqual(trial.events, [('d', True, 0), ('d', False, .125)])
        self.assertAlmostEqual(trial.now, .130)
        self.assertEqual([row['before_monotonic'] for row in receipt['edges']], [0, .125])
        self.assertEqual([row['after_monotonic'] for row in receipt['edges']], [.005, .130])
        self.assertEqual(set(receipt['os_states'][0]['keys_down']), {'w', 'a', 's', 'd'})
        self.assertTrue(receipt['os_states'][1]['keys_down']['d'])
        self.assertFalse(any(receipt['os_states'][-1]['keys_down'].values()))

    def test_partial_down_failure_attempts_every_owned_up(self):
        trial = MockPulse()
        trial.error_down = {'d'}
        with self.assertRaises(OSError):
            trial.run(('w', 'd'))
        self.assertEqual([(name, down) for name, down, _ in trial.events],
                         [('w', True), ('d', True), ('w', False), ('d', False)])
        self.assertFalse(trial.down)
        self.assertEqual(trial.receipt['status'], 'FAILED')

    def test_sleep_exception_and_interrupt_always_attempt_release(self):
        for error in (OSError('declared sleep error'), KeyboardInterrupt()):
            trial = MockPulse()
            trial.sleep_error = error
            with self.subTest(error=type(error).__name__), self.assertRaises(type(error)):
                trial.run()
            self.assertEqual(trial.events[-1][:2], ('d', False))
            self.assertTrue(trial.receipt['release_complete'])

    def test_up_failure_does_not_skip_other_owned_releases_or_pass(self):
        trial = MockPulse()
        trial.error_up = {'w'}
        with self.assertRaisesRegex(RuntimeError, 'release'):
            trial.run(('w', 'd'))
        self.assertEqual(trial.events[-1][:2], ('d', False))
        self.assertFalse(trial.receipt['release_complete'])
        self.assertEqual(len(trial.receipt['release_errors']), 1)

    def test_expired_or_late_before_state_read_prevents_any_down(self):
        for deadline, delay in ((0, 0), (.1, .2)):
            trial = MockPulse()
            trial.state_delay = delay
            with self.subTest(delay=delay), self.assertRaises(TimeoutError):
                trial.run(deadline=deadline)
            self.assertEqual(trial.events, [])

    def test_dispatch_cost_consumes_requested_hold_instead_of_restarting_sleep(self):
        trial = MockPulse()
        trial.edge_delay = .2
        with self.assertRaisesRegex(TimeoutError, 'requested pulse window'):
            trial.run(seconds=.1)
        self.assertEqual(trial.events[-1], ('d', False, .2))
        self.assertFalse(trial.down)

    def test_late_successful_up_or_sleep_still_fails_original_cap_after_release(self):
        for up_delay, sleep_extra in ((.2, 0), (None, .2)):
            trial = MockPulse()
            trial.up_delay, trial.sleep_extra = up_delay, sleep_extra
            with self.subTest(up_delay=up_delay), self.assertRaisesRegex(TimeoutError, 'Original route deadline'):
                trial.run(seconds=.1, deadline=.15)
            self.assertTrue(trial.receipt['release_complete'])
            self.assertEqual(trial.receipt['status'], 'FAILED')
            self.assertFalse(trial.down)

    def test_late_successful_os_release_read_cannot_pass_original_cap(self):
        trial = MockPulse()
        trial.state_delays[3] = .2
        with self.assertRaisesRegex(TimeoutError, 'Original route deadline'):
            trial.run(seconds=.1, deadline=.15)
        self.assertTrue(trial.receipt['release_complete'])
        self.assertGreater(trial.receipt['os_states'][-1]['read_end_monotonic'], .15)

    def test_fresh_focus_owner_visibility_and_pinned_window_are_required(self):
        for change in ('focus', 'owner', 'visible', 'pin'):
            trial = MockPulse()
            def mutate():
                if change == 'focus': trial.foreground = 99
                elif change == 'owner': trial.owner = 99
                elif change == 'visible': trial.visible = False
                else: trial.ui.window = trial.foreground = 99
            trial.after_down_hook = mutate
            with self.subTest(change=change), self.assertRaisesRegex(RuntimeError, 'owned visible focused window'):
                trial.run()
            self.assertEqual(trial.events[-1][:2], ('d', False))

    def test_external_a_key_is_observed_and_never_released_as_owned(self):
        trial = MockPulse()
        trial.down.add('a')
        with self.assertRaisesRegex(RuntimeError, 'physically neutral'):
            trial.run()
        self.assertEqual(trial.events, [])
        self.assertTrue(trial.receipt['os_states'][0]['keys_down']['a'])

    def test_invalid_requests_do_not_dispatch(self):
        for names, seconds, deadline in ((None, .1, 35), ('d', .1, 35), (('w', 's'), .1, 35),
                                         (('a', 'a'), .1, 35), (('d',), True, 35),
                                         (('d',), float('nan'), 35), (('d',), 3, 35),
                                         (('d',), .1, float('inf'))):
            trial = MockPulse()
            with self.subTest(names=names, seconds=seconds), self.assertRaises(RuntimeError):
                trial.run(names, seconds, deadline)
            self.assertEqual(trial.events, [])
            self.assertEqual(trial.receipt['status'], 'FAILED')

    def test_controller_publishes_full_receipt_after_release_even_on_failure(self):
        tree = ast.parse((Path(__file__).parent / 'verify_offline_export.py').read_text())
        node = next(value for value in ast.walk(tree) if isinstance(value, ast.FunctionDef) and value.name == 'settings_route_pulse')
        for fail in (False, True):
            trial = MockPulse()
            if fail: trial.sleep_error = OSError('declared sleep failure')
            native = trial.ui.key_pulse
            trial.ui.key_pulse = lambda names, seconds, **kw: native(names, seconds, **kw, clock=lambda: trial.now, sleep=trial.sleep)
            route, held, traces = {}, set(), []
            namespace = {'remaining': lambda: 35 - trial.now, 'ui': trial.ui, 'settings_route': route,
                         'held_keys': held, 'trace': lambda event, **data: traces.append((event, data, set(trial.down)))}
            exec(compile(ast.Module(body=[node], type_ignores=[]), 'actual-controller:pulse', 'exec'), namespace)
            if fail:
                with self.assertRaises(OSError): namespace['settings_route_pulse'](('d',), .125, 35)
            else:
                namespace['settings_route_pulse'](('d',), .125, 35)
            self.assertEqual([row[0] for row in traces], ['settings_route_native_pulse_before', 'settings_route_native_pulse_after'])
            self.assertFalse(traces[-1][2])
            self.assertEqual(traces[-1][1]['receipt'], route['native_pulses'][0])
            self.assertFalse(held)

    def test_pulse_hook_is_opt_in_and_still_requires_living_stopped_route_endpoint(self):
        for use_pulse in (False, True):
            world = SettingsWalker()
            calls = []
            def pulse(names, seconds, deadline):
                calls.append((names, seconds, deadline))
                for name in names: world.key(name, True)
                try: world.pause(seconds)
                finally:
                    for name in names: world.key(name, False)
            relocate_settings_actor(world.observe(), actor_id=1, round_number=2, observe=world.observe,
                                    key=world.key, pause=world.pause, record=world.record, deadline=35,
                                    receipt=world.receipt, clock=world.clock, pulse=pulse if use_pulse else None)
            self.assertEqual(bool(calls), use_pulse)
            self.assertEqual(world.receipt['status'], 'FIXED_ROUTE_REACHED')
            self.assertFalse(world.requested)
            self.assertLess(abs(world.receipt['endpoint'][0] + 7.8), .45)

    def test_late_successful_pulse_callback_cannot_pass_approach_cap(self):
        world = SettingsWalker()
        def late(names, seconds, deadline):
            world.pause(deadline - world.wall + .01)
        with self.assertRaises(TimeoutError):
            approach_floor(-7.8, -21, observe=world.observe, key=world.key, pause=world.pause,
                           record=world.record, deadline=35, clock=world.clock, pulse=late)
        self.assertFalse(world.requested)


if __name__ == '__main__':
    unittest.main()
