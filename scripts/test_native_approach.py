"""Independent 60 Hz movement plant for the native approach controller.

This models the inspected SBMovementStep ground acceleration and digital keys.
It does not prove native key delivery, collision paths or rendered gameplay.
"""
import copy
import json
import math
import unittest

from native_approach import approach_floor


class SampledWalker:
    def __init__(self, *, position=(0, 0), velocity=(0, 0), yaw=math.pi,
                 rate=.4, delivery=.1, publication_lag=0, blocked=False):
        self.position, self.velocity = list(position), list(velocity)
        self.yaw, self.rate, self.delivery = yaw, rate, delivery
        self.wall, self.tick = 0.0, 0
        self.requested, self.consumed, self.pending = set(), set(), []
        self.publication_lag, self.blocked = publication_lag, blocked
        self.phase, self.alive, self.failure = 'live', True, None
        self.history = [self.snapshot()]
        self.records, self.reads = [], []

    def clock(self):
        return self.wall

    def key(self, name, down):
        if down != (name in self.requested):
            (self.requested.add if down else self.requested.discard)(name)
            self.pending.append((self.wall + self.delivery / self.rate, name, down))

    def snapshot(self):
        return {'simulation_tick': self.tick, 'elapsed': self.tick / 60,
                'round_number': 1, 'phase': self.phase,
                'local_actor': {'id': 1, 'alive': self.alive, 'health': 100,
                                'position': [self.position[0], 0, self.position[1]],
                                'velocity': [self.velocity[0], 0, self.velocity[1]], 'yaw': self.yaw},
                'local_input': {'move': [int('d' in self.consumed) - int('a' in self.consumed),
                                         int('w' in self.consumed) - int('s' in self.consumed)]}}

    def pause(self, duration):
        finish = self.wall + duration
        while (self.tick + 1) / (60 * self.rate) <= finish + 1e-9:
            self.wall = (self.tick + 1) / (60 * self.rate)
            for queued in self.pending[:]:
                when, name, down = queued
                if when <= self.wall + 1e-9:
                    (self.consumed.add if down else self.consumed.discard)(name)
                    self.pending.remove(queued)
            side = int('d' in self.consumed) - int('a' in self.consumed)
            forward = int('w' in self.consumed) - int('s' in self.consumed)
            length = max(1, math.hypot(side, forward))
            side, forward = side / length, forward / length
            desired = [(math.cos(self.yaw) * side - math.sin(self.yaw) * forward) * 5.1,
                       (-math.sin(self.yaw) * side - math.cos(self.yaw) * forward) * 5.1]
            for axis in range(2):
                error = desired[axis] - self.velocity[axis]
                self.velocity[axis] += math.copysign(min(abs(error), 28 / 60), error) if error else 0
                if not self.blocked:
                    self.position[axis] += self.velocity[axis] / 60
                else:
                    self.velocity[axis] = 0
            self.tick += 1
            if self.tick % 13 == 0:
                self.history.append(self.snapshot())
        self.wall = finish

    def observe(self):
        if self.failure and self.wall >= self.failure:
            raise OSError('Observed producer became unreadable')
        available = [s for s in self.history if s['elapsed'] <= self.tick / 60 - self.publication_lag + 1e-9]
        state = copy.deepcopy(available[-1] if available else self.history[0])
        self.reads.append((self.wall, state))
        return state

    def record(self, event, **data):
        self.records.append({'event': event, 'wall': self.wall, **data})

    def run(self, target, deadline=15):
        return approach_floor(*target, observe=self.observe, key=self.key, pause=self.pause,
                              record=self.record, deadline=deadline, clock=self.clock)


class NativeApproachTests(unittest.TestCase):
    results = []

    def assert_arrived(self, world, target):
        end = world.run(target)
        completed = next(r for r in world.records if r['event'] == 'movement_completed')
        error = math.hypot(end[0] - target[0], end[2] - target[1])
        self.assertLess(error, .45)
        self.assertLessEqual(math.hypot(*world.velocity), .05)
        self.assertLess(world.wall, 15)
        self.assertFalse(world.requested)
        ticks = completed['settled_simulation_ticks']
        self.assertEqual(len(set(ticks)), 2)
        self.assertLess(ticks[0], ticks[1])
        states = {state['simulation_tick']: state for _, state in world.reads}
        for tick in ticks:
            self.assertEqual(states[tick]['local_input']['move'], [0, 0])
            velocity = states[tick]['local_actor']['velocity']
            self.assertLessEqual(math.hypot(velocity[0], velocity[2]), .05)
        self.results.append({'target': target, 'rate': world.rate, 'delivery_sim_seconds': world.delivery,
                             'publication_lag_sim_seconds': world.publication_lag,
                             'wall_seconds': world.wall, 'endpoint_error_m': error,
                             'settled_ticks': ticks})

    def test_delayed_sampled_ground_dynamics_reach_both_objective_approaches(self):
        for rate in [.4, .7, 1]:
            for delivery in [0, .1, .2]:
                for position, target, yaw in [((-15, 2), (-15, 8), math.pi),
                                               ((-20, 9), (-17, 9), -math.pi / 2),
                                               ((0, 0), (4, -3), .7)]:
                    with self.subTest(rate=rate, delivery=delivery, target=target):
                        self.assert_arrived(SampledWalker(position=position, yaw=yaw, rate=rate, delivery=delivery), target)

    def test_late_publication_and_repeated_snapshots_do_not_fake_settling(self):
        world = SampledWalker(position=(-15, 2), publication_lag=.2)
        self.assert_arrived(world, (-15, 8))
        self.assertGreater(len(world.reads), len({s['simulation_tick'] for _, s in world.reads}))

    def test_moving_arrival_must_stop_and_recorrect(self):
        world = SampledWalker(position=(0, 7.8), velocity=(0, 5.1))
        self.assert_arrived(world, (0, 8))
        self.assertGreater(world.wall, .5)

    def test_blocked_path_fails_original_deadline_and_releases_keys(self):
        world = SampledWalker(blocked=True)
        with self.assertRaisesRegex(TimeoutError, 'requested floor position'):
            world.run((0, 6))
        self.assertLessEqual(world.wall, 15 + 1e-8)
        self.assertFalse(world.requested)
        self.assertFalse(any(r['event'] == 'movement_completed' for r in world.records))

    def test_unreadable_observation_releases_pending_native_movement(self):
        world = SampledWalker()
        world.failure = 1.5
        with self.assertRaisesRegex(OSError, 'unreadable'):
            world.run((0, 6))
        self.assertFalse(world.requested)

    def test_duplicate_stopped_snapshot_cannot_supply_two_new_ticks(self):
        world = SampledWalker(position=(0, 8))
        initial = world.snapshot()
        world.observe = lambda: initial
        with self.assertRaises(TimeoutError):
            world.run((0, 8))
        self.assertFalse(world.requested)

    def test_round_change_during_approach_releases_controls_and_cannot_pass(self):
        world = SampledWalker()
        original = world.observe
        def changed_round():
            state = original()
            if world.wall > 1.5:
                state['round_number'] = 2
            return state
        world.observe = changed_round
        with self.assertRaisesRegex(RuntimeError, 'live round'):
            world.run((0, 6))
        self.assertFalse(world.requested)

    def test_observation_returning_after_deadline_cannot_accept_endpoint(self):
        world = SampledWalker(position=(0, 8))
        original = world.observe
        def slow_read():
            world.pause(.2)
            return original()
        world.observe = slow_read
        with self.assertRaises(TimeoutError):
            world.run((0, 8), deadline=.1)
        self.assertFalse(world.requested)
        self.assertFalse(any(r['event'] == 'movement_completed' for r in world.records))

    def test_nonfinite_snapshot_is_rejected_with_controls_released(self):
        world = SampledWalker()
        original = world.observe
        def invalid_motion():
            state = original()
            if world.wall > 1.5:
                state['local_actor']['velocity'][0] = float('nan')
            return state
        world.observe = invalid_motion
        with self.assertRaisesRegex(RuntimeError, 'non-finite'):
            world.run((0, 6))
        self.assertFalse(world.requested)

    @classmethod
    def tearDownClass(cls):
        print('NATIVE_APPROACH_DYNAMICS=' + json.dumps(cls.results, sort_keys=True))


if __name__ == '__main__':
    unittest.main()
