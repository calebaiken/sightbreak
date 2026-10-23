#!/usr/bin/env python3
"""Declared 60 Hz motion/counterexamples, never native input or collision proof."""
from copy import deepcopy
import math
import unittest

from native_settings_route import SETTINGS_COVER, relocate_settings_actor
from test_native_approach import SampledWalker


class SettingsWalker(SampledWalker):
    def __init__(self, **kwargs):
        super().__init__(position=(-4.4, -21), yaw=math.pi, **kwargs)
        self.receipt = {}
        self.mutation = None

    def observe(self):
        state = super().observe()
        state.update(schema=1, scope='debug_offline_read_only_observation', scenario='standard',
                     round_number=2, time_scale=1, wall_msec=state['simulation_tick'] * 10 + 100)
        state['ui'] = {'screen': 'game', 'focused': True, 'paused': False,
                       'scoreboard_visible': False, 'waiting_for_input_release': False}
        state['local_actor'].update(deaths=1, team=0, weapon='smg', ammo=30, reserve=120)
        state['local_input'].update(fire=False, interact=False, reload=False)
        if self.mutation is not None and self.wall > .3:
            state = self.mutation(state)
        return state

    def route(self, *, deadline=35, start=None):
        return relocate_settings_actor(self.observe() if start is None else start,
                                       actor_id=1, round_number=2, observe=self.observe,
                                       key=self.key, pause=self.pause, record=self.record,
                                       deadline=deadline, receipt=self.receipt, clock=self.clock)


class SettingsRouteControls(unittest.TestCase):
    def test_fixed_route_reaches_cover_with_delayed_digital_delivery_and_readbacks(self):
        for rate in (.4, .7, 1):
            for delivery in (0, .1, .2):
                world = SettingsWalker(rate=rate, delivery=delivery, publication_lag=.1)
                endpoint = world.route()
                with self.subTest(rate=rate, delivery=delivery):
                    self.assertLess(math.hypot(endpoint[0] - SETTINGS_COVER[0], endpoint[2] - SETTINGS_COVER[1]), .45)
                    self.assertLess(world.wall, 35)
                    self.assertFalse(world.requested)
                    self.assertEqual(world.receipt['status'], 'FIXED_ROUTE_REACHED')
                    self.assertEqual(world.receipt['original_second_live_absolute_deadline'], 35)
                    self.assertEqual(world.receipt['start']['local_actor']['position'], [-4.4, 0, -21])
                    self.assertGreater(len(world.receipt['observations']), 2)
                    event = next(row for row in world.records if row['event'] == 'movement_completed')
                    self.assertLess(event['horizontal_speed'], .05 + 1e-9)
                    self.assertLess(event['settled_simulation_ticks'][0], event['settled_simulation_ticks'][1])

    def test_living_health_loss_is_observed_without_changing_health_or_rules(self):
        world = SettingsWalker()
        def damage(state):
            state['local_actor']['health'] = 63
            return state
        world.mutation = damage
        world.route()
        self.assertEqual(world.receipt['start']['local_actor']['health'], 100)
        self.assertEqual(world.receipt['after']['local_actor']['health'], 63)
        self.assertEqual(world.receipt['after']['local_actor']['deaths'], 1)

    def test_death_life_actor_round_phase_or_focus_loss_never_selects_another_trial(self):
        for section, field, value in (
                ('local_actor', 'alive', False), ('local_actor', 'health', 0),
                ('local_actor', 'deaths', 2), ('local_actor', 'id', 2),
                ('', 'round_number', 3), ('', 'phase', 'post'),
                ('ui', 'focused', False), ('ui', 'paused', True)):
            world = SettingsWalker()
            def changed(state):
                (state[section] if section else state)[field] = value
                return state
            world.mutation = changed
            with self.subTest(field=field), self.assertRaisesRegex(RuntimeError, 'lost precondition'):
                world.route()
            self.assertFalse(world.requested)
            loss = world.receipt['precondition_loss']
            self.assertEqual((loss['rejected_state'][section] if section else loss['rejected_state'])[field], value)
            self.assertIsNotNone(loss['previous_valid_state'])
            self.assertNotIn('endpoint', world.receipt)

    def test_fixed_corridor_loss_fails_and_retains_actual_bad_position(self):
        world = SettingsWalker()
        def outside(state):
            state['local_actor']['position'][2] = -19
            return state
        world.mutation = outside
        with self.assertRaisesRegex(RuntimeError, 'left_declared_clear_corridor'):
            world.route()
        self.assertFalse(world.requested)
        self.assertEqual(world.receipt['precondition_loss']['rejected_state']['local_actor']['position'][2], -19)

    def test_no_alternate_origin_or_malformed_health_can_start_route(self):
        for field, value in (('position', [-7, 0, -21]), ('health', True), ('health', float('nan')),
                             ('id', True), ('ammo', 30.0), ('team', 1)):
            world = SettingsWalker()
            start = world.observe()
            start['local_actor'][field] = value
            with self.subTest(field=field), self.assertRaises(RuntimeError):
                world.route(start=start)
            self.assertFalse(world.requested)
            self.assertNotIn('endpoint', world.receipt)

    def test_phase_readiness_time_is_not_replaced_with_a_new_route_budget(self):
        world = SettingsWalker()
        world.pause(34.95)
        with self.assertRaises(TimeoutError):
            world.route(deadline=35)
        self.assertLessEqual(world.wall, 35 + 1e-8)
        self.assertFalse(world.requested)
        self.assertNotIn('endpoint', world.receipt)
        self.assertEqual(world.receipt['original_second_live_absolute_deadline'], 35)

    def test_expired_budget_or_blocked_motion_cannot_pass(self):
        for blocked, deadline in ((False, 0), (True, 35)):
            world = SettingsWalker(blocked=blocked)
            with self.subTest(blocked=blocked), self.assertRaises(TimeoutError):
                world.route(deadline=deadline)
            self.assertFalse(world.requested)
            self.assertNotIn('endpoint', world.receipt)

    def test_receipt_raw_snapshots_are_not_mutable_observation_aliases(self):
        world = SettingsWalker()
        world.route()
        saved = deepcopy(world.receipt['after'])
        world.position[0] = 100
        self.assertEqual(world.receipt['after'], saved)
        self.assertNotEqual(world.receipt['start']['local_actor']['position'], saved['local_actor']['position'])


if __name__ == '__main__':
    unittest.main()
