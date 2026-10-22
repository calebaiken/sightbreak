#!/usr/bin/env python3
"""Declared callback/state controls; these do not capture or prove native pixels."""
from copy import deepcopy
import json
from pathlib import Path
import unittest

from verify_offline_export import capture_living_phase, require_living_capture_phase


REFERENCE = json.loads((Path(__file__).parent / 'fixtures/offline_capture_observations.json').read_text())


def advanced(state, frames=0, **changes):
    result = deepcopy(state)
    result.update(drawn_frames=state['drawn_frames'] + frames,
                  wall_msec=state['wall_msec'] + 100 * frames,
                  simulation_tick=state['simulation_tick'] + frames)
    result.update(changes)
    return result


class DeclaredCallbacks:
    def __init__(self, states, *, round_number=2, until=160, elapsed=0):
        self.states = list(states)
        self.round_number, self.until, self.elapsed = round_number, until, elapsed
        self.receipt, self.captures, self.wait_budgets = {}, [], []
        self.expected = {'source': {'source_commit': 'frozen', 'source_dirty': False},
                         'process_pid': 20, 'process_running': True, 'trace_directory': '/declared/trace'}
        if round_number == 1:
            self.expected.update(loaded_initial_event=deepcopy(REFERENCE['restart_initial']),
                                 stored_profile=deepcopy(REFERENCE['restart_initial']['initial_profile']))
        self.bindings = [deepcopy(self.expected) for _ in range(3)]
        self.binding_index = 0

    def binding(self):
        result = self.bindings[self.binding_index]
        self.binding_index += 1
        return deepcopy(result)

    def observed(self, predicate, seconds, label, after=-1):
        self.wait_budgets.append(seconds)
        until = self.elapsed + seconds
        while self.states:
            self.elapsed += .1
            if self.elapsed >= until:
                raise TimeoutError('Declared original budget expired: ' + label)
            state = deepcopy(self.states.pop(0))
            if state.get('wall_msec', -1) > after and predicate(state):
                return state
        self.elapsed = until
        raise TimeoutError('No further fresh declared observation: ' + label)

    def run(self):
        return capture_living_phase('declared-capture', actor_id=1, round_number=self.round_number,
                                    after=-1, until=self.until, observed=self.observed,
                                    capture=self.captures.append, binding=self.binding,
                                    expected_binding=deepcopy(self.expected), receipt=self.receipt,
                                    clock=lambda: self.elapsed)


def round_sequence():
    state = REFERENCE['round_2_buy']
    return [deepcopy(REFERENCE['old_post']), deepcopy(state), advanced(state, 1),
            advanced(state, 2), advanced(state, 3), advanced(state, 4)]


def reopened_sequence():
    menu = REFERENCE['restart_initial']
    game = advanced(menu, 1)
    game['ui'].update(screen='game', mouse_mode=2)
    return [deepcopy(menu), game, advanced(game, 1), advanced(game, 2), advanced(game, 3), advanced(game, 4)]


class CaptureFenceTests(unittest.TestCase):
    def test_actual_old_post_and_loaded_menu_cannot_authorize_capture(self):
        for key, number in [('old_post', 2), ('restart_initial', 1)]:
            with self.subTest(reference=key):
                with self.assertRaises(RuntimeError):
                    require_living_capture_phase(REFERENCE[key], 1, number)
                callbacks = DeclaredCallbacks([REFERENCE[key]], round_number=number)
                with self.assertRaises(TimeoutError):
                    callbacks.run()
                self.assertEqual(callbacks.captures, [])

    def test_declared_natural_round_fence_preserves_old_post_then_waits_two_frames(self):
        callbacks = DeclaredCallbacks(round_sequence())
        receipt = callbacks.run()
        self.assertEqual(callbacks.captures, ['declared-capture'])
        self.assertEqual(receipt['acknowledged']['drawn_frames'], 1142)
        self.assertEqual(receipt['ready']['drawn_frames'], 1144)
        self.assertEqual(receipt['before_capture']['drawn_frames'], 1145)
        self.assertEqual(receipt['after_capture']['drawn_frames'], 1146)
        self.assertFalse(REFERENCE['old_post']['local_actor']['alive'])

    def test_declared_reopened_trace_requires_game_hud_after_initial_profile_event(self):
        callbacks = DeclaredCallbacks(reopened_sequence(), round_number=1, until=30)
        receipt = callbacks.run()
        self.assertEqual(callbacks.captures, ['declared-capture'])
        self.assertEqual(receipt['acknowledged']['ui']['screen'], 'game')
        self.assertEqual(receipt['ready']['drawn_frames'], receipt['acknowledged']['drawn_frames'] + 2)
        self.assertEqual(REFERENCE['restart_initial']['ui']['screen'], 'menu')

    def test_one_frame_and_stalled_counter_never_capture(self):
        state = REFERENCE['round_2_buy']
        for states in ([state, advanced(state, 1)],
                       [state, advanced(state, 1), advanced(state, 1, wall_msec=state['wall_msec'] + 300)]):
            with self.subTest(length=len(states)):
                callbacks = DeclaredCallbacks(states)
                with self.assertRaises(TimeoutError):
                    callbacks.run()
                self.assertEqual(callbacks.captures, [])

    def test_stale_observation_does_not_supply_the_frame_fence(self):
        state = REFERENCE['round_2_buy']
        callbacks = DeclaredCallbacks([state, advanced(state, 4, wall_msec=state['wall_msec'])])
        with self.assertRaises(TimeoutError):
            callbacks.run()
        self.assertEqual(callbacks.captures, [])

    def test_invalid_frame_and_clock_values_fail_without_capture(self):
        for field in ('drawn_frames', 'wall_msec', 'simulation_tick'):
            for value in (None, True, -1, 1.5, '12'):
                with self.subTest(field=field, value=value):
                    item = deepcopy(REFERENCE['round_2_buy'])
                    item[field] = value
                    callbacks = DeclaredCallbacks([item])
                    with self.assertRaises((RuntimeError, TimeoutError, TypeError)):
                        callbacks.run()
                    self.assertEqual(callbacks.captures, [])

    def test_frame_regression_between_ready_and_capture_is_rejected(self):
        states = round_sequence()
        states[3]['drawn_frames'] += 3
        callbacks = DeclaredCallbacks(states)
        with self.assertRaisesRegex(RuntimeError, 'backward before'):
            callbacks.run()
        self.assertEqual(callbacks.captures, [])

    def test_frame_regression_after_raw_capture_cannot_pass(self):
        states = round_sequence()
        states[-1]['drawn_frames'] = states[-2]['drawn_frames'] - 1
        callbacks = DeclaredCallbacks(states)
        with self.assertRaisesRegex(RuntimeError, 'backward during'):
            callbacks.run()
        self.assertEqual(callbacks.captures, ['declared-capture'])
        self.assertNotIn('binding_after_capture', callbacks.receipt)

    def test_life_actor_phase_focus_speed_context_loss_never_passes(self):
        changes = [('local_actor', 'alive', False), ('local_actor', 'health', 0),
                   ('local_actor', 'id', 2), ('ui', 'focused', False), ('ui', 'paused', True),
                   ('ui', 'screen', 'menu'), ('ui', 'scoreboard_visible', True),
                   ('', 'round_number', 3), ('', 'phase', 'post'), ('', 'time_scale', 2),
                   ('', 'scenario', 'plant'), ('', 'scope', 'other'), ('', 'schema', 2)]
        for section, field, value in changes:
            for index in (2, 4, 5):
                with self.subTest(field=field, stage=index):
                    states = round_sequence()
                    (states[index][section] if section else states[index])[field] = value
                    callbacks = DeclaredCallbacks(states)
                    with self.assertRaises(RuntimeError):
                        callbacks.run()
                    self.assertEqual(bool(callbacks.captures), index == 5)
                    self.assertNotIn('binding_after_capture', callbacks.receipt)

    def test_source_process_trace_and_loaded_settings_races_cannot_pass(self):
        for field in ('source', 'process_pid', 'process_running', 'trace_directory',
                      'loaded_initial_event', 'stored_profile'):
            for index in (0, 1, 2):
                with self.subTest(field=field, stage=index):
                    callbacks = DeclaredCallbacks(reopened_sequence(), round_number=1, until=30)
                    callbacks.bindings[index][field] = 'changed'
                    with self.assertRaisesRegex(RuntimeError, 'changed source, native process, trace, or loaded settings'):
                        callbacks.run()
                    self.assertEqual(bool(callbacks.captures), index == 2)

    def test_original_absolute_budget_is_shared_across_all_waits(self):
        callbacks = DeclaredCallbacks(reopened_sequence(), round_number=1, until=30, elapsed=28)
        receipt = callbacks.run()
        self.assertEqual(receipt['absolute_deadline_monotonic'], 30)
        self.assertTrue(all(0 < seconds <= 2 for seconds in callbacks.wait_budgets))
        self.assertEqual(callbacks.wait_budgets, sorted(callbacks.wait_budgets, reverse=True))
        self.assertLess(receipt['remaining_original_budget_seconds'], 2)

    def test_frame_wait_cannot_gain_a_new_budget_after_event_arrival(self):
        callbacks = DeclaredCallbacks(round_sequence(), until=160, elapsed=159.7)
        with self.assertRaises(TimeoutError):
            callbacks.run()
        self.assertEqual(callbacks.captures, [])

    def test_capture_cannot_extend_the_original_deadline(self):
        callbacks = DeclaredCallbacks(reopened_sequence(), round_number=1, until=30)
        def capture(_):
            callbacks.captures.append('declared-capture')
            callbacks.elapsed = 30
        with self.assertRaises(TimeoutError):
            capture_living_phase('declared-capture', actor_id=1, round_number=1, after=-1, until=30,
                                 observed=callbacks.observed, capture=capture, binding=callbacks.binding,
                                 expected_binding=callbacks.expected, receipt=callbacks.receipt,
                                 clock=lambda: callbacks.elapsed)
        self.assertEqual(callbacks.captures, ['declared-capture'])
        self.assertNotIn('after_capture', callbacks.receipt)


if __name__ == '__main__':
    unittest.main()
