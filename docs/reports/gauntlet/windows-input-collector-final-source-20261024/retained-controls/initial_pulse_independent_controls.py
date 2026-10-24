#!/usr/bin/env python3
"""Independent source/model falsifiers. No engine, native helper or OS input."""
import copy
import importlib.util
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import types
import unittest
from unittest.mock import patch

ROOT = Path(os.environ.get('REVIEW_SOURCE', Path(__file__).resolve().parents[5])).resolve()
sys.path.insert(0, str(ROOT / 'scripts'))
import native_approach
import native_settings_route as route
from test_native_approach import SampledWalker
from test_native_settings_route import SettingsWalker
from test_native_route_pulse import RealKeyPulse

ROWS = []
BASELINE = Path(__file__).with_name('originals') / '49ae54b0-native_approach.py.txt'


class CostedPlant(SettingsWalker):
    """Charge different explicit costs from builder; not actual Windows timing."""
    def __init__(self, **kw):
        super().__init__(**kw)
        self.pulses, self.fallback, self.read_count = [], [], 0
        self.change = None
        self.read_delay = .04

    def key(self, name, down):
        self.pause(.065)
        if down:
            self.fallback.append((name, self.wall))
        SampledWalker.key(self, name, down)
        self.pause(.065)

    def record(self, event, **kw):
        self.pause(.07)
        super().record(event, **kw)

    def observe(self):
        self.pause(self.read_delay)
        self.read_count += 1
        value = super().observe()
        if self.change:
            value = self.change(value)
        return value

    def pulse(self, names, seconds, deadline):
        row = {'wall': self.wall, 'seconds': seconds, 'deadline': deadline,
               'origin': self.position[:], 'names': list(names)}
        self.pulses.append(row)
        for name in names:
            SampledWalker.key(self, name, True)
        try:
            self.pause(min(seconds, max(0, deadline - self.wall)))
        finally:
            for name in names:
                SampledWalker.key(self, name, False)
            row['release'] = self.wall

    def run_route(self, *, pulse=True, deadline=35, start=None):
        return route.relocate_settings_actor(self.observe() if start is None else start,
            actor_id=1, round_number=2, observe=self.observe, key=self.key,
            pause=self.pause, record=self.record, clock=self.clock,
            deadline=deadline, receipt=self.receipt, pulse=self.pulse if pulse else None)


def changed(value, path, bad):
    target = value
    for part in path[:-1]:
        target = target[part]
    target[path[-1]] = copy.deepcopy(bad)
    return value


GUARDS = [
    (('schema',), True), (('scope',), 'network'), (('scenario',), 'other'),
    (('phase',), 'post'), (('round_number',), 3), (('round_number',), True),
    (('time_scale',), .5), (('time_scale',), True),
    (('local_actor', 'id'), 2), (('local_actor', 'id'), True),
    (('local_actor', 'alive'), False), (('local_actor', 'alive'), 1),
    (('local_actor', 'health'), 0), (('local_actor', 'health'), 101),
    (('local_actor', 'health'), True), (('local_actor', 'health'), float('nan')),
    (('local_actor', 'position'), [0, 0]),
    (('local_actor', 'position'), [-8.51, 0, -21]),
    (('local_actor', 'position'), [-4.4, .11, -21]),
    (('local_actor', 'position'), [-4.4, 0, -20.24]),
    (('local_actor', 'velocity'), None), (('local_actor', 'velocity'), [0, 0, float('inf')]),
    (('local_actor', 'yaw'), float('nan')), (('elapsed',), -1),
    (('simulation_tick',), True), (('simulation_tick',), -1),
    (('wall_msec',), True), (('wall_msec',), -1),
    (('local_actor', 'deaths'), 2), (('local_actor', 'deaths'), True),
    (('local_actor', 'team'), 1), (('local_actor', 'team'), True),
    (('local_actor', 'weapon'), 'rifle'), (('local_actor', 'ammo'), 29),
    (('local_actor', 'reserve'), 119),
    (('local_input', 'move'), [float('nan'), 0]), (('local_input', 'move'), None),
    (('local_input', 'fire'), True), (('local_input', 'interact'), True),
    (('local_input', 'reload'), True),
    (('ui', 'screen'), 'menu'), (('ui', 'focused'), False), (('ui', 'focused'), 1),
    (('ui', 'paused'), True), (('ui', 'scoreboard_visible'), True),
    (('ui', 'waiting_for_input_release'), True), (('local_actor',), None),
    (('ui',), None), (('local_input',), None),
]


class IndependentControls(unittest.TestCase):
    def test_actual_inspired_boundary_original_fails_candidate_uses_pulse_first(self):
        base = '49ae54b0e4f5d880bdf06e4eb783a616b2dff684'
        original = types.ModuleType('original_approach')
        data = BASELINE.read_bytes()
        exec(compile(data, base + ':native_approach.py', 'exec'), original.__dict__)
        world = CostedPlant(rate=.7, delivery=.1, publication_lag=.13)
        with patch.object(route, 'approach_floor', original.approach_floor):
            with self.assertRaisesRegex(RuntimeError, 'left_declared_clear_corridor'):
                world.run_route()
        self.assertTrue(world.fallback)
        self.assertFalse(world.pulses)
        self.assertFalse(world.requested)
        ROWS.append({'case': 'original boundary', 'receipt': world.receipt,
                     'fallback_downs': world.fallback, 'pulses': world.pulses})
        for rate in (.4, .7, 1):
            for delivery in (0, .1, .2):
                with self.subTest(rate=rate, delivery=delivery):
                    world = CostedPlant(rate=rate, delivery=delivery, publication_lag=.13)
                    endpoint = world.run_route()
                    self.assertTrue(world.pulses)
                    self.assertEqual(world.pulses[0]['origin'], [-4.4, -21])
                    self.assertFalse(world.fallback)
                    self.assertFalse(world.requested)
                    self.assertEqual(world.receipt['status'], 'FIXED_ROUTE_REACHED')
                    self.assertLess(math.hypot(endpoint[0]+7.8, endpoint[2]+21), .45)
                    self.assertLess(world.wall, 35)
                    self.assertTrue(all(-8.5 <= s['local_actor']['position'][0] <= -3.9
                                        for s in world.receipt['observations']))
                    self.assertTrue(all(0 < p['seconds'] <= 2.5 and p['deadline'] == 35
                                        for p in world.pulses))
                    ROWS.append({'case': 'candidate boundary', 'rate': rate, 'delivery': delivery,
                                 'wall_seconds': world.wall, 'endpoint': endpoint,
                                 'pulses': world.pulses, 'final_samples': world.receipt['observations'][-2:]})

    def test_default_none_path_is_identical_to_original(self):
        for source in ('candidate', 'baseline'):
            world = CostedPlant(rate=.7, delivery=.1, publication_lag=.13)
            fn = native_approach.approach_floor
            if source == 'baseline':
                module = types.ModuleType('old')
                raw = BASELINE.read_bytes()
                exec(compile(raw, 'old', 'exec'), module.__dict__)
                fn = module.approach_floor
            with patch.object(route, 'approach_floor', fn):
                with self.assertRaisesRegex(RuntimeError, 'left_declared_clear_corridor'):
                    world.run_route(pulse=False)
            snapshot = (world.wall, world.receipt, world.fallback, world.records)
            if source == 'candidate':
                candidate = snapshot
            else:
                self.assertEqual(candidate, snapshot)

    def test_all_existing_guards_before_dispatch_after_pulse_and_at_arrival(self):
        for stage in ('first_read', 'after_pulse', 'arrival'):
            for path, bad in GUARDS:
                with self.subTest(stage=stage, path=path, bad=bad):
                    world = CostedPlant()
                    count = [0]
                    def mutate(value):
                        actor = value['local_actor']
                        ready = (world.read_count > 1 if stage == 'first_read' else bool(world.pulses)
                                 if stage == 'after_pulse' else bool(world.pulses)
                                 and abs(actor['position'][0] + 7.8) < .45
                                 and math.hypot(actor['velocity'][0], actor['velocity'][2]) <= .05)
                        if ready:
                            count[0] += 1
                            return changed(value, path, bad)
                        return value
                    world.change = mutate
                    with self.assertRaisesRegex(RuntimeError, 'lost precondition'):
                        world.run_route()
                    self.assertTrue(count[0])
                    self.assertFalse(world.requested)
                    self.assertFalse(world.fallback)
                    self.assertNotIn('endpoint', world.receipt)
                    self.assertEqual(len(world.pulses), 0 if stage == 'first_read' else 1
                                     if stage == 'after_pulse' else len(world.pulses))

    def test_start_must_be_neutral_stopped_at_stock_spawn(self):
        for path, bad in ((('local_actor', 'velocity'), [-.051, 0, 0]),
                          (('local_input', 'move'), [1, 0]),
                          (('local_actor', 'position'), [-7.7, 0, -21])):
            world = CostedPlant()
            start = changed(world.observe(), path, bad)
            with self.subTest(path=path), self.assertRaisesRegex(RuntimeError, 'lost precondition'):
                world.run_route(start=start)
            self.assertFalse(world.pulses)
            self.assertNotIn('endpoint', world.receipt)

    def test_moving_arrival_and_duplicate_stopped_tick_cannot_succeed(self):
        for state_type in ('moving', 'held', 'duplicate'):
            world = CostedPlant()
            initial_tick = [None]
            def mutate(state):
                if world.pulses:
                    state['local_actor']['position'] = [-7.8, 0, -21]
                    state['local_actor']['velocity'] = [.051 if state_type == 'moving' else 0, 0, 0]
                    state['local_input']['move'] = [1, 0] if state_type == 'held' else [0, 0]
                    if state_type == 'duplicate':
                        initial_tick[0] = initial_tick[0] or state['simulation_tick']
                        state['simulation_tick'] = initial_tick[0]
                return state
            world.change = mutate
            with self.subTest(state_type=state_type), self.assertRaises(TimeoutError):
                world.run_route(deadline=5)
            self.assertNotIn('endpoint', world.receipt)
            self.assertFalse(world.requested)
            self.assertEqual(len(world.pulses), 1)

    def test_late_telemetry_after_first_pulse_has_no_second_dispatch(self):
        world = CostedPlant()
        observe = world.observe
        def delayed():
            if world.pulses:
                world.pause(6)
            return observe()
        world.observe = delayed
        with self.assertRaises(TimeoutError):
            world.run_route(deadline=5)
        self.assertEqual(len(world.pulses), 1)
        self.assertFalse(world.requested)
        self.assertNotIn('endpoint', world.receipt)

    def test_callback_failure_and_interrupt_after_down_release_all(self):
        for error in (OSError('after down'), KeyboardInterrupt(), SystemExit('stop')):
            world = CostedPlant()
            def failure(names, seconds, deadline):
                world.pulses.append({'names': names})
                for name in names:
                    SampledWalker.key(world, name, True)
                raise error
            world.pulse = failure
            with self.subTest(error=type(error).__name__), self.assertRaises(type(error)):
                world.run_route()
            self.assertFalse(world.requested)
            self.assertFalse(world.fallback)
            self.assertEqual(len(world.pulses), 1)
            self.assertNotIn('endpoint', world.receipt)

    def test_late_callback_and_unreadable_after_pulse_reject(self):
        for kind in ('late', 'unreadable'):
            world = CostedPlant()
            pulse = world.pulse
            def callback(names, seconds, deadline):
                pulse(names, seconds, deadline)
                if kind == 'late':
                    world.pause(deadline - world.wall + .01)
                else:
                    world.failure = world.wall
            world.pulse = callback
            with self.subTest(kind=kind), self.assertRaises(TimeoutError if kind == 'late' else OSError):
                world.run_route(deadline=5)
            self.assertEqual(len(world.pulses), 1)
            self.assertFalse(world.requested)
            self.assertNotIn('endpoint', world.receipt)

    def test_regressed_positive_counters_after_pulse_reject(self):
        for counter in ('simulation_tick', 'wall_msec'):
            world = CostedPlant()
            def mutate(state):
                if world.pulses:
                    state[counter] = 0
                return state
            world.change = mutate
            with self.subTest(counter=counter), self.assertRaisesRegex(RuntimeError, 'regressed_'):
                world.run_route()
            self.assertEqual(len(world.pulses), 1)
            self.assertFalse(world.requested)
            self.assertNotIn('endpoint', world.receipt)

    def test_context_loss_on_second_stopped_arrival_sample_rejects(self):
        world = CostedPlant()
        stopped_ticks = set()
        def mutate(state):
            actor = state['local_actor']
            if (world.pulses and abs(actor['position'][0] + 7.8) < .45
                    and state['local_input']['move'] == [0, 0]
                    and math.hypot(actor['velocity'][0], actor['velocity'][2]) <= .05):
                stopped_ticks.add(state['simulation_tick'])
                if len(stopped_ticks) >= 2:
                    state['ui']['paused'] = True
            return state
        world.change = mutate
        with self.assertRaisesRegex(RuntimeError, 'lost precondition'):
            world.run_route()
        self.assertEqual(len(stopped_ticks), 2)
        self.assertFalse(world.requested)
        self.assertNotIn('endpoint', world.receipt)

    def test_slow_rate_estimate_is_clamped_to_existing_callback_maximum(self):
        world = SettingsWalker()
        sequence = [0]
        calls = []
        def observe():
            state = world.observe()
            sequence[0] += 1
            state['simulation_tick'] = sequence[0]
            state['elapsed'] = sequence[0] * .000001
            return state
        def callback(names, seconds, deadline):
            calls.append((names, seconds, deadline))
            raise OSError('stop after measuring cap')
        with self.assertRaises(OSError):
            native_approach.approach_floor(-7.8, -21, observe=observe,
                key=world.key, pause=world.pause, record=world.record,
                deadline=35, clock=world.clock, pulse=callback)
        self.assertEqual(calls[0][1:], (2.5, 35))
        self.assertFalse(world.requested)

    def test_logging_delay_at_final_arrival_cannot_create_success_after_cap(self):
        world = CostedPlant()
        record = world.record
        def slow_final(event, **kw):
            record(event, **kw)
            if event == 'movement_completed':
                world.pause(35 - world.wall + .01)
        world.record = slow_final
        with self.assertRaises(TimeoutError):
            world.run_route()
        self.assertFalse(world.requested)
        self.assertNotIn('endpoint', world.receipt)
        self.assertEqual(world.receipt['status'], 'FIXED_ROUTE_FAILED')

    def test_real_key_context_loss_and_external_controls_at_each_guard(self):
        for stage in ('before_down', 'before_key_down:w', 'before_key_down:d', 'after_down', 'after_release'):
            for field, bad in (('foreground', 99), ('owner', 99), ('visible', False), ('thread', 0)):
                trial = RealKeyPulse()
                def hook(actual):
                    if actual == stage:
                        setattr(trial, field, bad)
                trial.read_hook = hook
                with self.subTest(stage=stage, field=field), self.assertRaises(RuntimeError):
                    trial.run(('w', 'd'))
                self.assertFalse(trial.down)
                self.assertEqual(trial.receipt['status'], 'FAILED')
        for name in ('a', 's', 'd', 'lmb'):
            trial = RealKeyPulse()
            trial.read_hook = lambda actual: trial.down.add(name) if actual == 'before_key_down:d' else None
            with self.subTest(external=name), self.assertRaises(RuntimeError):
                trial.run(('w', 'd'))
            self.assertEqual(trial.down, {name})
            self.assertEqual(trial.receipt['attempted_keys'], ['w'])

    def test_real_key_delay_at_every_state_cannot_restart_hold_or_cap(self):
        for stage in ('before_down', 'before_key_down:w', 'before_key_down:d', 'after_down', 'after_release'):
            trial = RealKeyPulse()
            trial.read_hook = lambda actual: setattr(trial, 'now', trial.now + .2) if actual == stage else None
            with self.subTest(stage=stage), self.assertRaises(TimeoutError):
                trial.run(('w', 'd'), seconds=.1, deadline=.15)
            self.assertFalse(trial.down)
            self.assertEqual(trial.receipt['status'], 'FAILED')
        trial = RealKeyPulse()
        trial.ui.key_pulse(('d',), 2.5, deadline=3, receipt=trial.receipt,
                           clock=lambda: trial.now, sleep=trial.sleep)
        self.assertEqual(trial.calls[1]['time'], 2.5)
        self.assertTrue(trial.receipt['release_complete'])


if __name__ == '__main__':
    if sorted(os.sched_getaffinity(0)) != [4]:
        raise RuntimeError('Independent pure checks require CPU 4')
    result = unittest.main(exit=False, verbosity=2).result
    output = Path(os.environ.get('REVIEW_ROWS', str(Path(__file__).with_name('independent-model-rows.json'))))
    output.write_text(json.dumps({'source_root': str(ROOT), 'rows': ROWS,
                                 'guard_cases_per_stage': len(GUARDS), 'successful': result.wasSuccessful(),
                                 'methods': result.testsRun}, indent=2) + '\n')
    raise SystemExit(not result.wasSuccessful())
