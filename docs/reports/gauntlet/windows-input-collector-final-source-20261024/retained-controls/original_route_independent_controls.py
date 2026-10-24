"""Independent pure controls: real WinUI.key -> _input, fake User32 only."""
import ast
from copy import deepcopy
import ctypes as C
import json
import os
from pathlib import Path
import sys
import unittest

ROOT = Path(sys.argv.pop(1)).resolve()
sys.path.insert(0, str(ROOT / 'scripts'))
from verify_integration_export import WinUI
from native_approach import approach_floor
from native_settings_route import relocate_settings_actor

TRIALS = []
CURRENT_TEST = None


class Rig:
    def __init__(self):
        self.now = 0.
        self.down = set()
        self.calls = []
        self.owner, self.foreground, self.visible, self.thread = 12, 34, True, 56
        self.state_index, self.read_delay = 0, {}
        self.read_error, self.send_error, self.map_error = {}, {}, {}
        self.edge_delay, self.sleep_extra = .005, 0.
        self.sleep_error, self.send_hook = None, None
        self.ui = object.__new__(WinUI)
        self.ui.window, self.ui.pid, self.ui.user = 34, 12, self
        self.receipt = {}

    def IsWindowVisible(self, window):
        self.state_index += 1
        self.now += self.read_delay.get(self.state_index, 0)
        if self.state_index in self.read_error:
            raise self.read_error[self.state_index]
        return self.visible

    def GetWindowThreadProcessId(self, window, pointer):
        C.cast(pointer, C.POINTER(C.c_uint32))[0] = self.owner
        return self.thread

    def GetForegroundWindow(self):
        return self.foreground

    def GetAsyncKeyState(self, vk):
        return 0x8000 if ('lmb' if vk == 1 else chr(vk).lower()) in self.down else 0

    def MapVirtualKeyW(self, vk, mode):
        name = chr(vk).lower()
        if name in self.map_error:
            raise self.map_error[name]
        return vk

    def SendInput(self, count, pointer, size):
        event = pointer._obj
        name, down = chr(event.data.key.scan).lower(), not bool(event.data.key.flags & 0x2)
        self.calls.append({'key': name, 'down': down, 'time': self.now,
                           'foreground': self.foreground, 'owner': self.owner,
                           'visible': self.visible, 'flags': event.data.key.flags})
        self.now += self.edge_delay
        (self.down.add if down else self.down.discard)(name)
        if self.send_hook:
            self.send_hook(name, down)
        if (name, down) in self.send_error:
            raise self.send_error[name, down]
        return 1

    def sleep(self, duration):
        if self.sleep_error:
            raise self.sleep_error
        self.now += duration + self.sleep_extra

    def run(self, names=('d',), seconds=.125, deadline=35):
        try:
            return self.ui.key_pulse(names, seconds, deadline=deadline,
                                     receipt=self.receipt, clock=lambda: self.now, sleep=self.sleep)
        finally:
            TRIALS.append({'test': CURRENT_TEST, 'calls': deepcopy(self.calls), 'receipt': deepcopy(self.receipt),
                           'remaining_keys': sorted(self.down), 'finished': self.now})

    def edges(self):
        return [(row['key'], row['down']) for row in self.calls]


def callback(rig, trace):
    tree = ast.parse((ROOT / 'scripts/verify_offline_export.py').read_text())
    node = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == 'settings_route_pulse')
    route, held = {}, set()
    original = rig.ui.key_pulse
    rig.ui.key_pulse = lambda names, seconds, **kw: original(names, seconds, **kw, clock=lambda: rig.now, sleep=rig.sleep)
    def remaining():
        if rig.now >= 35:
            raise TimeoutError('whole cap')
        return 35 - rig.now
    ns = {'remaining': remaining, 'ui': rig.ui, 'settings_route': route,
          'held_keys': held, 'trace': trace}
    exec(compile(ast.Module(body=[node], type_ignores=[]), 'frozen-settings-route-pulse', 'exec'), ns)
    return ns['settings_route_pulse'], route, held


class IndependentPulseControls(unittest.TestCase):
    def setUp(self):
        global CURRENT_TEST
        CURRENT_TEST = self._testMethodName

    def test_real_key_mapping_and_sendinput_flags_and_receipt(self):
        rig = Rig()
        result = rig.run(('w', 'd'))
        self.assertEqual(rig.edges(), [('w', True), ('d', True), ('w', False), ('d', False)])
        self.assertEqual([r['flags'] for r in rig.calls], [8, 8, 10, 10])
        self.assertAlmostEqual(rig.calls[2]['time'], .125)
        self.assertTrue(result['release_complete'])
        self.assertEqual(len(result['edges']), 4)
        self.assertEqual([r['label'] for r in result['os_states']], ['before_down', 'after_down', 'after_release'])
        for row in result['os_states']:
            self.assertEqual(set(row['keys_down']), {'w', 'a', 's', 'd'})
            self.assertEqual((row['window_pid'], row['foreground_window']), (12, 34))
            self.assertLessEqual(row['read_begin_monotonic'], row['read_end_monotonic'])

    def test_preflight_focus_owner_visibility_thread_and_pin(self):
        for field, value in [('foreground', 99), ('owner', 99), ('visible', False), ('thread', 0)]:
            with self.subTest(field=field):
                rig = Rig()
                setattr(rig, field, value)
                with self.assertRaises(RuntimeError): rig.run()
                self.assertFalse(rig.calls)

    def test_all_observed_external_inputs_prevent_injection(self):
        for name in ('w', 'a', 's', 'd', 'lmb'):
            with self.subTest(name=name):
                rig = Rig()
                rig.down.add(name)
                with self.assertRaises(RuntimeError): rig.run()
                self.assertFalse(rig.calls)
                self.assertEqual(rig.down, {name})
                self.assertFalse(rig.receipt['release_complete'])

    def test_unknown_initial_os_read_fails_without_down(self):
        rig = Rig()
        rig.read_error[1] = OSError('unknown OS state')
        with self.assertRaises(OSError): rig.run()
        self.assertFalse(rig.calls)
        self.assertEqual(rig.receipt['status'], 'FAILED')

    def test_partial_dispatch_exception_and_interrupt_release_every_attempt(self):
        for error in (OSError('partial down'), KeyboardInterrupt(), SystemExit('cancel')):
            with self.subTest(error=type(error).__name__):
                rig = Rig()
                rig.send_error['d', True] = error
                with self.assertRaises(type(error)): rig.run(('w', 'd'))
                self.assertEqual(rig.edges(), [('w', True), ('d', True), ('w', False), ('d', False)])
                self.assertFalse(rig.down)
                self.assertTrue(rig.receipt['release_complete'])
                self.assertEqual(rig.receipt['error_type'], type(error).__name__)

    def test_mapping_failure_keeps_previous_owned_release(self):
        rig = Rig()
        rig.map_error['d'] = OSError('cannot map d')
        with self.assertRaises(OSError): rig.run(('w', 'd'))
        self.assertIn(('w', False), rig.edges())
        self.assertEqual(rig.receipt['attempted_keys'], ['w', 'd'])
        self.assertEqual(len(rig.receipt['release_errors']), 1)
        self.assertFalse(rig.down)

    def test_post_down_read_and_sleep_errors_release(self):
        for stage in ('read', 'sleep'):
            with self.subTest(stage=stage):
                rig = Rig()
                if stage == 'read': rig.read_error[2] = OSError('post down read')
                else: rig.sleep_error = SystemExit('cancel sleep')
                with self.assertRaises(BaseException): rig.run(('w', 'd'))
                self.assertEqual(rig.edges()[-2:], [('w', False), ('d', False)])
                self.assertFalse(rig.down)

    def test_up_interrupt_keeps_later_key_release_attempt(self):
        rig = Rig()
        rig.send_error['w', False] = KeyboardInterrupt()
        with self.assertRaises(RuntimeError): rig.run(('w', 'd'))
        self.assertEqual(rig.edges()[-2:], [('w', False), ('d', False)])
        self.assertFalse(rig.receipt['release_complete'])
        self.assertEqual(rig.receipt['status'], 'FAILED')

    def test_after_release_read_failure_retains_all_edges(self):
        rig = Rig()
        rig.read_error[3] = OSError('post release read')
        with self.assertRaises(RuntimeError): rig.run()
        self.assertEqual(rig.edges(), [('d', True), ('d', False)])
        self.assertEqual(len(rig.receipt['edges']), 2)
        self.assertFalse(rig.receipt['release_complete'])

    def test_late_preflight_never_injects(self):
        rig = Rig()
        rig.read_delay[1] = 1.
        with self.assertRaises(TimeoutError): rig.run(deadline=.1)
        self.assertFalse(rig.calls)

    def test_dispatch_cost_consumes_hold(self):
        rig = Rig()
        rig.edge_delay = .08
        with self.assertRaises(TimeoutError): rig.run(('w', 'd'), seconds=.1)
        self.assertAlmostEqual(rig.calls[2]['time'], .16)
        self.assertFalse(rig.down)

    def test_late_successful_sleep_up_and_os_read_fail_same_cap(self):
        for stage in ('sleep', 'up', 'read'):
            with self.subTest(stage=stage):
                rig = Rig()
                if stage == 'sleep': rig.sleep_extra = .2
                elif stage == 'read': rig.read_delay[3] = .2
                else:
                    rig.send_hook = lambda name, down: setattr(rig, 'now', rig.now + (.2 if not down else 0))
                with self.assertRaises(TimeoutError): rig.run(seconds=.1, deadline=.15)
                self.assertFalse(rig.down)
                self.assertEqual(rig.receipt['status'], 'FAILED')

    def test_early_sleep_return_fails_and_releases(self):
        rig = Rig()
        rig.sleep_extra = -.01
        with self.assertRaisesRegex(RuntimeError, 'before its requested boundary'): rig.run()
        self.assertFalse(rig.down)

    def test_post_dispatch_target_rebind_fails_and_releases(self):
        rig = Rig()
        def change(name, down):
            if down: rig.ui.window = 99
        rig.send_hook = change
        with self.assertRaises(RuntimeError): rig.run()
        self.assertEqual(rig.edges()[-1], ('d', False))

    def test_observed_later_external_key_is_not_claimed_as_owned_release(self):
        rig = Rig()
        def external(name, down):
            if down: rig.down.add('a')
        rig.send_hook = external
        with self.assertRaises(RuntimeError): rig.run()
        self.assertEqual(rig.receipt['released_keys'], ['d'])
        self.assertEqual(rig.down, {'a'})
        self.assertFalse(rig.receipt['release_complete'])

    def test_two_key_dispatch_stops_when_focus_changes_after_first_down(self):
        rig = Rig()
        def lose_focus(name, down):
            if down: rig.foreground = 99
        rig.send_hook = lose_focus
        with self.assertRaises(RuntimeError): rig.run(('w', 'd'))
        unsafe = [r for r in rig.calls if r['down'] and r['foreground'] != 34]
        self.assertEqual(unsafe, [], 'A second down was injected after focus was lost')

    def test_two_key_dispatch_stops_when_owner_changes_after_first_down(self):
        rig = Rig()
        def lose_owner(name, down):
            if down: rig.owner = 99
        rig.send_hook = lose_owner
        with self.assertRaises(RuntimeError): rig.run(('w', 'd'))
        unsafe = [r for r in rig.calls if r['down'] and r['owner'] != 12]
        self.assertEqual(unsafe, [], 'A second down was injected after target ownership was lost')

    def test_pulse_callback_publishes_after_release_and_preserves_error(self):
        rig = Rig()
        rig.sleep_error = OSError('sleep failed')
        traces = []
        fn, route, held = callback(rig, lambda event, **data: traces.append((event, deepcopy(data), set(rig.down))))
        with self.assertRaises(OSError): fn(('d',), .125, 35)
        self.assertEqual([r[0] for r in traces], ['settings_route_native_pulse_before', 'settings_route_native_pulse_after'])
        self.assertFalse(traces[-1][2])
        self.assertEqual(route['native_pulses'][0]['error'], 'sleep failed')
        self.assertFalse(held)

    def test_trace_before_lateness_prevents_down_and_retains_failure(self):
        rig = Rig()
        def trace(event, **data):
            if event.endswith('_before'): rig.now = 36
        fn, route, held = callback(rig, trace)
        with self.assertRaises(TimeoutError): fn(('d',), .125, 35)
        self.assertFalse(rig.calls)
        self.assertEqual(route['native_pulses'][0]['status'], 'FAILED')
        self.assertFalse(held)

    def test_trace_after_failure_keeps_release_and_full_receipt(self):
        rig = Rig()
        def trace(event, **data):
            if event.endswith('_after'): raise OSError('trace write failed')
        fn, route, held = callback(rig, trace)
        with self.assertRaisesRegex(OSError, 'trace write failed'): fn(('d',), .125, 35)
        self.assertFalse(rig.down)
        self.assertTrue(route['native_pulses'][0]['release_complete'])
        self.assertFalse(held)

    def test_failed_release_retains_controller_held_keys_for_outer_cleanup(self):
        rig = Rig()
        rig.send_error['d', False] = OSError('up failed')
        fn, route, held = callback(rig, lambda *args, **kw: None)
        with self.assertRaises(RuntimeError): fn(('d',), .125, 35)
        self.assertEqual(held, {'d'})
        self.assertFalse(route['native_pulses'][0]['release_complete'])

    def test_late_callback_is_not_accepted_as_approach_completion(self):
        now, tick, completed = [0.], [0], []
        keys = set()
        def observe():
            tick[0] += 1
            return {'simulation_tick': tick[0], 'elapsed': tick[0] / 60,
                    'round_number': 2, 'phase': 'live', 'local_input': {'move': [0, 0]},
                    'local_actor': {'id': 1, 'alive': True, 'health': 100, 'position': [-6.8, 0, -21],
                                    'velocity': [0, 0, 0], 'yaw': 0}}
        def pulse(names, seconds, deadline): now[0] = deadline + .1
        def pause(seconds): now[0] += seconds
        with self.assertRaises(TimeoutError):
            approach_floor(-7.8, -21, observe=observe, key=lambda name, down: (keys.add if down else keys.discard)(name),
                           pause=pause, record=lambda event, **kw: completed.append(event), deadline=1,
                           clock=lambda: now[0], pulse=pulse)
        self.assertNotIn('movement_completed', completed)
        self.assertFalse(keys)

    def test_route_keeps_same_cap_when_after_trace_is_late(self):
        now, tick = [0.], [0]
        sent, records, route = [], [], {}
        def observation():
            tick[0] += 1
            x = -4.4 if tick[0] == 1 else -6.8
            return {'schema': 1, 'scope': 'debug_offline_read_only_observation', 'scenario': 'standard',
                    'phase': 'live', 'round_number': 2, 'time_scale': 1,
                    'simulation_tick': tick[0], 'wall_msec': tick[0] * 16, 'elapsed': tick[0] / 60,
                    'ui': {'screen': 'game', 'focused': True, 'paused': False, 'scoreboard_visible': False,
                           'waiting_for_input_release': False},
                    'local_input': {'move': [0, 0], 'fire': False, 'interact': False, 'reload': False},
                    'local_actor': {'id': 1, 'alive': True, 'health': 100, 'team': 0, 'deaths': 1,
                                    'weapon': 'smg', 'ammo': 30, 'reserve': 120, 'yaw': 0,
                                    'position': [x, 0, -21], 'velocity': [0, 0, 0]}}
        def pulse(names, seconds, deadline):
            sent.append({'names': names, 'seconds': seconds, 'deadline': deadline})
            now[0] = deadline + .2  # Model successful after-release trace returning late.
        with self.assertRaises(TimeoutError):
            relocate_settings_actor(observation(), actor_id=1, round_number=2,
                                    observe=observation, key=lambda *args: None,
                                    pause=lambda seconds: now.__setitem__(0, now[0] + seconds),
                                    record=lambda event, **kw: records.append(event), deadline=1,
                                    receipt=route, clock=lambda: now[0], pulse=pulse)
        self.assertEqual(sent[0]['deadline'], 1)
        self.assertEqual(route['original_second_live_absolute_deadline'], 1)
        self.assertNotIn('endpoint', route)
        self.assertEqual(route['status'], 'FIXED_ROUTE_FAILED')
        self.assertNotIn('movement_completed', records)


if __name__ == '__main__':
    result = unittest.main(exit=False, verbosity=2).result
    receipt_path = Path(os.environ.get('SIGHTBREAK_PULSE_RECEIPTS', str(Path(__file__).with_name('independent-receipts.json'))))
    receipt_path.write_text(json.dumps(TRIALS, indent=2) + '\n')
    sys.exit(not result.wasSuccessful())
