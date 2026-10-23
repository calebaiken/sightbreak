#!/usr/bin/env python3
"""Mocked OS/clock calls only. No native input, helper process or timing proof."""
import ast
import ctypes as C
from pathlib import Path
import unittest

from verify_integration_export import WinUI
from native_approach import approach_floor
from native_settings_route import relocate_settings_actor
from test_native_approach import SampledWalker
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


class RealKeyPulse(MockPulse):
    """Keep actual key mapping/_input; replace User32 and time only."""
    def __init__(self):
        super().__init__()
        self.state_user = self.ui.user
        self.ui.user = self
        del self.ui.key
        self.calls, self.read_stages = [], []
        self.read_hook = None
        self.thread = 56

    def IsWindowVisible(self, window):
        checks = self.receipt.get('down_checks', [])
        if checks and checks[-1]['status'] == 'IN_PROGRESS':
            stage = 'before_key_down:' + checks[-1]['key']
        elif self.events:
            stage = 'after_down' if self.events[-1][1] else 'after_release'
        else:
            stage = 'before_down'
        self.read_stages.append(stage)
        if self.read_hook:
            self.read_hook(stage)
        return self.state_user.IsWindowVisible(window)

    def GetWindowThreadProcessId(self, window, pointer):
        self.state_user.GetWindowThreadProcessId(window, pointer)
        return self.thread

    def GetForegroundWindow(self):
        return self.state_user.GetForegroundWindow()

    def GetAsyncKeyState(self, vk):
        return self.state_user.GetAsyncKeyState(vk)

    def MapVirtualKeyW(self, vk, mode):
        return vk

    def SendInput(self, count, pointer, size):
        event = pointer._obj
        name, down = chr(event.data.key.scan).lower(), not bool(event.data.key.flags & 0x2)
        self.calls.append({'key': name, 'down': down, 'time': self.now,
                           'foreground': self.foreground, 'owner': self.owner,
                           'visible': self.visible, 'flags': event.data.key.flags})
        self.key(name, down)
        return 1


class TracedSettingsWalker(SettingsWalker):
    """Declared diagnostic costs, not a reconstruction of native scheduling.

    Keep the independent 60 Hz plant and 13-tick publications. Traced key
    callbacks advance motion before/after each edge, as synchronous controller
    diagnostics can. The pulse has no diagnostic writes between its edges.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.fallback_downs, self.pulses = [], []

    def key(self, name, down):
        self.pause(.06)
        if down:
            self.fallback_downs.append((name, self.wall))
        super().key(name, down)
        self.pause(.06)

    def record(self, event, **data):
        self.pause(.06)
        super().record(event, **data)

    def observe(self):
        self.pause(.03)
        return super().observe()

    def pulse(self, names, seconds, deadline):
        row = {'start': self.wall, 'seconds': seconds, 'deadline': deadline,
               'keys': names, 'position': self.position[:]}
        self.pulses.append(row)
        for name in names:
            SampledWalker.key(self, name, True)
        try:
            self.pause(min(seconds, max(0, deadline - self.wall)))
        finally:
            for name in names:
                SampledWalker.key(self, name, False)
            row['released'] = self.wall

    def route_with_pulse(self, deadline=35):
        return relocate_settings_actor(self.observe(), actor_id=1, round_number=2,
                                       observe=self.observe, key=self.key, pause=self.pause,
                                       record=self.record, deadline=deadline, receipt=self.receipt,
                                       clock=self.clock, pulse=self.pulse)


class FirstDisplacementPulseControls(unittest.TestCase):
    def test_original_continuous_walk_loses_unchanged_corridor_with_slow_diagnostics(self):
        world = TracedSettingsWalker(rate=.7, delivery=.1, publication_lag=.1)
        with self.assertRaisesRegex(RuntimeError, 'left_declared_clear_corridor'):
            world.route()
        self.assertTrue(world.fallback_downs)
        self.assertFalse(world.requested)
        self.assertNotIn('endpoint', world.receipt)
        self.assertLess(world.receipt['precondition_loss']['rejected_state']['local_actor']['position'][0], -8.5)

    def test_opt_in_pulses_own_first_displacement_and_reach_stopped_original_endpoint(self):
        for rate in (.4, .7, 1):
            for delivery in (0, .1, .2):
                with self.subTest(rate=rate, delivery=delivery):
                    world = TracedSettingsWalker(rate=rate, delivery=delivery, publication_lag=.1)
                    endpoint = world.route_with_pulse()
                    self.assertTrue(world.pulses)
                    self.assertEqual(world.pulses[0]['position'], [-4.4, -21])
                    self.assertFalse(world.fallback_downs)
                    self.assertFalse(world.requested)
                    self.assertEqual(world.receipt['status'], 'FIXED_ROUTE_REACHED')
                    self.assertLess(abs(endpoint[0] + 7.8), .45)
                    self.assertLess(world.wall, 35)
                    for row in world.pulses:
                        self.assertEqual(row['deadline'], 35)
                        self.assertLessEqual(row['seconds'], 2.5)
                        self.assertLessEqual(row['released'] - row['start'], row['seconds'] + 1e-8)
                    states = world.receipt['observations']
                    for state in states:
                        self.assertGreaterEqual(state['local_actor']['position'][0], -8.5)
                    stopped = states[-2:]
                    self.assertLess(stopped[0]['simulation_tick'], stopped[1]['simulation_tick'])
                    for state in stopped:
                        self.assertEqual(state['local_input']['move'], [0, 0])
                        self.assertLessEqual(abs(state['local_actor']['velocity'][0]), .05)

    def test_pulse_route_block_or_read_failure_keeps_original_cap_and_releases(self):
        for failure in ('blocked', 'unreadable'):
            with self.subTest(failure=failure):
                world = TracedSettingsWalker(blocked=failure == 'blocked')
                if failure == 'unreadable':
                    world.failure = 2
                with self.assertRaises((TimeoutError, OSError)):
                    world.route_with_pulse(deadline=5)
                self.assertFalse(world.requested)
                self.assertFalse(world.fallback_downs)
                self.assertNotIn('endpoint', world.receipt)
                self.assertEqual(world.receipt['original_second_live_absolute_deadline'], 5)
                self.assertTrue(all(row['deadline'] == 5 for row in world.pulses))

    def test_identity_focus_or_life_loss_after_a_pulse_cannot_reuse_the_route(self):
        for section, field, value in (('local_actor', 'deaths', 2), ('', 'round_number', 3),
                                      ('ui', 'focused', False), ('local_actor', 'alive', False)):
            with self.subTest(field=field):
                world = TracedSettingsWalker()
                def changed(state):
                    if world.pulses:
                        (state[section] if section else state)[field] = value
                    return state
                world.mutation = changed
                with self.assertRaisesRegex(RuntimeError, 'lost precondition'):
                    world.route_with_pulse()
                self.assertEqual(len(world.pulses), 1)
                self.assertFalse(world.requested)
                self.assertFalse(world.fallback_downs)
                self.assertNotIn('endpoint', world.receipt)


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
        trial.state_delays[4] = .2
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


class RealKeyPerDownControls(unittest.TestCase):
    def test_real_key_two_key_positive_recognizes_prior_owned_input(self):
        for names in (('w', 'd'), ['w', 'd'], ('a', 's')):
            with self.subTest(names=names):
                trial = RealKeyPulse()
                result = trial.run(names)
                self.assertEqual([row['flags'] for row in trial.calls], [8, 8, 10, 10])
                self.assertEqual(result['down_checks'][1]['owned_keys'], [names[0]])
                state = result['down_checks'][1]['os_states'][0]
                self.assertTrue(state['keys_down'][names[0]])
                self.assertFalse(state['keys_down'][names[1]])
                self.assertAlmostEqual(trial.calls[2]['time'], .125)
                self.assertTrue(result['release_complete'])

    def test_real_key_focus_or_owner_loss_stops_second_down(self):
        for field in ('foreground', 'owner'):
            with self.subTest(field=field):
                trial = RealKeyPulse()
                trial.after_down_hook = lambda: setattr(trial, field, 99)
                with self.assertRaisesRegex(RuntimeError, 'owned visible focused window'):
                    trial.run(('w', 'd'))
                self.assertEqual([(r['key'], r['down']) for r in trial.calls], [('w', True), ('w', False)])
                self.assertFalse(trial.down)
                self.assertEqual(trial.receipt['attempted_keys'], ['w'])
                check = trial.receipt['down_checks'][-1]
                self.assertEqual(check['status'], 'FAILED')
                self.assertEqual(check['os_states'][0]['foreground_window' if field == 'foreground' else 'window_pid'], 99)

    def test_real_key_visibility_or_pinned_identity_loss_stops_second_down(self):
        for field, value in (('visible', False), ('thread', 0), ('window', 99), ('pid', 99)):
            with self.subTest(field=field):
                trial = RealKeyPulse()
                target = trial if field in ('visible', 'thread') else trial.ui
                trial.after_down_hook = lambda: setattr(target, field, value)
                with self.assertRaises(RuntimeError): trial.run(('w', 'd'))
                self.assertEqual(trial.events, [('w', True, 0), ('w', False, .005)])
                self.assertFalse(trial.down)

    def test_real_key_later_external_controls_stop_down_without_owning_them(self):
        for name in ('a', 's', 'd', 'lmb'):
            with self.subTest(name=name):
                trial = RealKeyPulse()
                trial.after_down_hook = lambda: trial.down.add(name)
                with self.assertRaisesRegex(RuntimeError, 'unowned controls'):
                    trial.run(('w', 'd'))
                self.assertEqual([(r['key'], r['down']) for r in trial.calls], [('w', True), ('w', False)])
                self.assertEqual(trial.down, {name})
                self.assertEqual(trial.receipt['released_keys'], ['w'])
                self.assertFalse(trial.receipt['release_complete'])

    def test_real_key_first_down_is_rechecked_after_initial_preflight(self):
        for field, value in (('foreground', 99), ('owner', 99), ('visible', False)):
            with self.subTest(field=field):
                trial = RealKeyPulse()
                trial.read_hook = lambda stage: setattr(trial, field, value) if stage == 'before_key_down:d' else None
                with self.assertRaises(RuntimeError): trial.run()
                self.assertFalse(trial.calls)
                self.assertEqual(trial.receipt['down_checks'][0]['status'], 'FAILED')

    def test_real_key_unknown_later_read_or_interrupt_releases_prior_attempt(self):
        for error in (OSError('unknown read'), KeyboardInterrupt(), SystemExit('cancel')):
            with self.subTest(error=type(error).__name__):
                trial = RealKeyPulse()
                def read(stage):
                    if stage == 'before_key_down:d': raise error
                trial.read_hook = read
                with self.assertRaises(type(error)): trial.run(('w', 'd'))
                self.assertEqual(trial.events, [('w', True, 0), ('w', False, .005)])
                self.assertTrue(trial.receipt['release_complete'])
                self.assertEqual(trial.receipt['down_checks'][-1]['error_type'], type(error).__name__)

    def test_real_key_late_per_down_check_consumes_fixed_hold_and_absolute_cap(self):
        for deadline, delay in ((35, .2), (.1, .2)):
            with self.subTest(deadline=deadline):
                trial = RealKeyPulse()
                def read(stage):
                    if stage == 'before_key_down:d': trial.now += delay
                trial.read_hook = read
                with self.assertRaises(TimeoutError): trial.run(('w', 'd'), seconds=.125, deadline=deadline)
                self.assertEqual([(r['key'], r['down']) for r in trial.calls], [('w', True), ('w', False)])
                self.assertEqual(trial.receipt['hold_until_monotonic'], min(.125, deadline))
                self.assertTrue(trial.receipt['release_complete'])
                self.assertGreater(trial.receipt['down_checks'][-1]['read_end_monotonic'], .2)

    def test_real_key_post_down_and_release_unknown_reads_keep_semantic_stages(self):
        for stage in ('after_down', 'after_release'):
            with self.subTest(stage=stage):
                trial = RealKeyPulse()
                def read(actual):
                    if actual == stage: raise OSError('unknown ' + stage)
                trial.read_hook = read
                with self.assertRaises(BaseException): trial.run(('w', 'd'))
                self.assertEqual([(r['key'], r['down']) for r in trial.calls],
                                 [('w', True), ('d', True), ('w', False), ('d', False)])
                self.assertFalse(trial.down)
                self.assertEqual(len(trial.receipt['edges']), 4)

    def test_real_key_late_release_read_fails_after_all_releases(self):
        trial = RealKeyPulse()
        trial.read_hook = lambda stage: setattr(trial, 'now', trial.now + .2) if stage == 'after_release' else None
        with self.assertRaises(TimeoutError): trial.run(('w', 'd'), seconds=.1, deadline=.15)
        self.assertTrue(trial.receipt['release_complete'])
        self.assertEqual(trial.receipt['status'], 'FAILED')
        self.assertFalse(trial.down)

    def test_real_key_partial_down_and_up_interrupt_still_attempt_all_owned_releases(self):
        trial = RealKeyPulse()
        trial.error_down, trial.error_up = {'d'}, {'w'}
        with self.assertRaises(OSError): trial.run(('w', 'd'))
        self.assertEqual([(r['key'], r['down']) for r in trial.calls],
                         [('w', True), ('d', True), ('w', False), ('d', False)])
        self.assertEqual(trial.receipt['attempted_keys'], ['w', 'd'])
        self.assertFalse(trial.receipt['release_complete'])
        self.assertFalse(trial.down)

    def test_real_key_receipts_own_samples_and_request_list_after_return(self):
        trial = RealKeyPulse()
        names = ['w', 'd']
        result = trial.run(names)
        names[:] = ['s']
        trial.down.add('a')
        trial.foreground = trial.owner = trial.ui.pid = trial.ui.window = 99
        self.assertEqual(result['keys'], ['w', 'd'])
        self.assertEqual(result['down_checks'][0]['owned_keys'], [])
        self.assertEqual(result['down_checks'][1]['owned_keys'], ['w'])
        for check in result['down_checks']:
            state = check['os_states'][0]
            self.assertEqual((state['target_window'], state['window_pid'], state['foreground_window']), (34, 12, 34))
            self.assertFalse(state['keys_down']['a'])
        self.assertFalse(any(result['os_states'][-1]['keys_down'].values()))


if __name__ == '__main__':
    unittest.main()
