#!/usr/bin/env python3
"""Pure declared counterexamples based on retained raw Windows observations."""
from copy import deepcopy
import ast
import json
from pathlib import Path
import unittest

from native_focus_fence import FocusContextFence, FocusPreconditionLost, fresh_focus_movement


RAW = json.loads((Path(__file__).parent / 'fixtures/offline_focus_observations.json').read_text())


def living(offset=0, moving=False):
    state = deepcopy(RAW['last_living_guard'])
    state['wall_msec'] += offset * 100
    state['simulation_tick'] += offset
    state['drawn_frames'] += offset
    state['ui']['waiting_for_input_release'] = False
    if moving:
        state['local_input']['move'] = [0, 1]
        state['local_actor']['position'][2] += 1
    return state


class DeclaredInput:
    def __init__(self, *, released=None, before=None, states=()):
        self.released = deepcopy(released if released is not None else living())
        self.before = deepcopy(before if before is not None else living(1))
        self.states, self.keys, self.waits = list(states), [], []
        self.receipt, self.context = {}, {}
        self.fence = FocusContextFence(RAW['focus_start'], self.context)

    def observed(self, predicate, seconds, label, after):
        self.waits.append({'seconds': seconds, 'label': label, 'after': after})
        for state in self.states:
            if state['wall_msec'] > after and predicate(state):
                return state
        raise TimeoutError(label)

    def run(self):
        return fresh_focus_movement(fence=self.fence, released=self.released,
                                    snapshot=lambda: self.before, observed=self.observed,
                                    key=lambda name, down: self.keys.append((name, down)),
                                    receipt=self.receipt)


class ActualObservedInput(DeclaredInput):
    """Use the real controller's reader/freshness/wait logic with declared data."""
    def __init__(self, *, reader_guard=False, **kwargs):
        super().__init__(**kwargs)
        self.elapsed = 0

        def read():
            state = self.states.pop(0) if self.states else {}
            if isinstance(state, OSError):
                raise state
            return state

        class Clock:
            def monotonic(_):
                return self.elapsed
            def sleep(_, seconds):
                self.elapsed += seconds

        namespace = {'time': Clock(), 'deadline': 300, 'trace': lambda *args, **kw: None,
                     'client': None, 'offline_observation': read,
                     'read_observation_json': lambda path: read(),
                     'initial_trace': Path('/declared/trace'), 'result': {}}
        tree = ast.parse((Path(__file__).parent / 'verify_offline_export.py').read_text())
        for name in (('offline_observation',) if reader_guard else ()) + ('wait_for', 'observed'):
            node = next(node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == name)
            exec(compile(ast.Module(body=[node], type_ignores=[]), 'actual-controller:' + name, 'exec'), namespace)
        self.actual_observed = namespace['observed']

    def observed(self, predicate, seconds, label, after):
        self.waits.append({'seconds': seconds, 'label': label, 'after': after})
        return self.actual_observed(predicate, seconds, label, after)


class FocusFenceControls(unittest.TestCase):
    def test_invalid_timestamp_cannot_hide_dead_state_before_actual_freshness_filter(self):
        for value in (None, -1, False, True, 'later', 1.0):
            bad = living(2, True)
            bad['local_actor'].update(alive=False, health=0)
            if value is None:
                del bad['wall_msec']
            else:
                bad['wall_msec'] = value
            trial = ActualObservedInput(states=[bad, living(3, True)])
            with self.subTest(value=value), self.assertRaises(FocusPreconditionLost):
                trial.run()
            self.assertEqual(trial.context['precondition_loss']['rejected_state'], bad)
            self.assertEqual(trial.keys, [('w', True), ('w', False)])

    def test_malformed_nested_and_nonobject_values_retain_exact_raw_json(self):
        for value in (None, [], True, 'raw-string', 3):
            for field in ('local_input', 'local_actor', 'ui', None):
                bad = living(2)
                if field is None:
                    bad = value
                else:
                    bad[field] = value
                for boundary in ('before', 'during'):
                    trial = ActualObservedInput(before=bad if boundary == 'before' else living(1),
                                                states=[bad, living(3, True)])
                    # DeclaredInput's None default predates raw-null controls.
                    if boundary == 'before':
                        trial.before = deepcopy(bad)
                    with self.subTest(field=field, value=value, boundary=boundary), self.assertRaises(FocusPreconditionLost):
                        trial.run()
                    self.assertEqual(trial.context['precondition_loss']['rejected_state'], bad)
                    self.assertNotIn('moved', trial.receipt)

    def test_actual_reader_scope_rejection_is_structured_and_retains_raw_state(self):
        bad = living(2, True)
        bad['scope'] = 'other'
        trial = ActualObservedInput(reader_guard=True, states=[bad, living(3, True)])
        with self.assertRaises(FocusPreconditionLost):
            trial.run()
        self.assertEqual(trial.context['precondition_loss']['rejected_state'], bad)

    def test_boolean_or_wrong_type_movement_rejects_before_key_and_during_actual_wait(self):
        for move in ([False, False], [True, 0], [0, '1'], [], None, '0,0', [0, float('nan')]):
            bad = living(2, True)
            bad['local_input']['move'] = move
            for boundary in ('before', 'during'):
                trial = ActualObservedInput(before=bad if boundary == 'before' else living(1),
                                            states=[bad, living(3, True)])
                with self.subTest(move=move, boundary=boundary), self.assertRaisesRegex(FocusPreconditionLost, 'invalid_input_move'):
                    trial.run()
                self.assertEqual(trial.keys, [] if boundary == 'before' else [('w', True), ('w', False)])

    def test_actual_wait_preserves_stale_and_unavailable_reads_then_valid_living_move(self):
        for numeric in (0, 0.0):
            stale = living(1, True)
            stale.update(phase='buy', round_number=99)
            moved = living(3, True)
            moved['time_scale'] = 1.0
            moved['local_input']['move'] = [numeric, 1.0]
            trial = ActualObservedInput(reader_guard=True,
                                        states=[OSError('declared publication gap'), stale, living(2), moved])
            self.assertEqual(trial.run(), moved)
            self.assertEqual(trial.receipt['status'], 'LIVING_MOVEMENT_OBSERVED')
            self.assertEqual(trial.keys, [('w', True), ('w', False)])
            self.assertEqual(trial.waits[0]['seconds'], 10)

    def test_original_dead_release_never_dispatches_fresh_key_or_wait(self):
        trial = DeclaredInput(released=RAW['dead_release_ack'])
        with self.assertRaisesRegex(FocusPreconditionLost, 'actor_life_changed|actor_not_alive'):
            trial.run()
        self.assertEqual(trial.keys, [])
        self.assertEqual(trial.waits, [])
        self.assertEqual(trial.receipt['status'], 'FOCUS_PRECONDITION_LOST')
        self.assertEqual(trial.context['precondition_loss']['rejected_state'], RAW['dead_release_ack'])
        self.assertEqual(trial.context['precondition_loss']['previous_valid_state'], RAW['focus_start'])

    def test_death_between_release_and_key_rejects_the_actual_dispatch_boundary(self):
        dead = living(1)
        dead['local_actor'].update(alive=False, health=0)
        trial = DeclaredInput(before=dead, states=[living(2, True)])
        with self.assertRaisesRegex(FocusPreconditionLost, 'before_fresh_w_down'):
            trial.run()
        self.assertEqual(trial.keys, [])
        self.assertEqual(trial.waits, [])
        self.assertEqual(trial.receipt['before_key'], dead)
        self.assertEqual(trial.context['precondition_loss']['previous_valid_state'], trial.released)

    def test_death_during_wait_including_displacement_cannot_pass_or_wait_for_another_life(self):
        for displaced in (False, True):
            dead = living(3, displaced)
            dead['local_actor'].update(alive=False, health=0)
            trial = DeclaredInput(states=[living(2), dead, living(4, True)])
            with self.subTest(displaced=displaced), self.assertRaisesRegex(FocusPreconditionLost, 'actor_not_alive'):
                trial.run()
            self.assertEqual(trial.keys, [('w', True), ('w', False)])
            self.assertEqual(trial.context['precondition_loss']['previous_valid_state'], living(2))
            self.assertEqual(trial.context['precondition_loss']['rejected_state'], dead)
            self.assertEqual(trial.receipt['last_after_key'], dead)
            self.assertNotIn('moved', trial.receipt)

    def test_moved_actor_round_phase_or_life_replacement_cannot_pass(self):
        for section, field, value, reason in (
                ('local_actor', 'id', 2, 'actor_identity_changed'),
                ('local_actor', 'deaths', 1, 'actor_life_changed'),
                ('', 'round_number', 2, 'round_identity_changed'),
                ('', 'phase', 'post', 'live_phase_lost')):
            changed = living(2, True)
            (changed[section] if section else changed)[field] = value
            for boundary in ('before', 'during'):
                trial = DeclaredInput(before=changed if boundary == 'before' else None,
                                      states=[changed, living(3, True)])
                with self.subTest(field=field, boundary=boundary), self.assertRaisesRegex(FocusPreconditionLost, reason):
                    trial.run()
                self.assertEqual(trial.keys, [] if boundary == 'before' else [('w', True), ('w', False)])
                self.assertNotIn('moved', trial.receipt)

    def test_positive_finite_health_and_strict_identity_are_required(self):
        for section, field, values in (
                ('local_actor', 'health', [0, -1, True, None, float('nan'), float('inf'), 101]),
                ('local_actor', 'id', [True, 1.0]),
                ('', 'round_number', [True, 1.0]),
                ('', 'time_scale', [True, 2]),
                ('', 'schema', [True, 2])):
            for value in values:
                before = living(1)
                (before[section] if section else before)[field] = value
                trial = DeclaredInput(before=before)
                with self.subTest(field=field, value=value), self.assertRaises(FocusPreconditionLost):
                    trial.run()
                self.assertEqual(trial.keys, [])

    def test_focus_pause_ui_contract_and_counter_loss_fail_closed(self):
        for section, field, value in (
                ('ui', 'focused', False), ('ui', 'paused', True), ('ui', 'screen', 'menu'),
                ('ui', 'scoreboard_visible', True), ('', 'scope', 'other'),
                ('', 'scenario', 'plant'), ('', 'wall_msec', 0),
                ('', 'drawn_frames', -1), ('', 'simulation_tick', True),
                ('local_actor', 'position', [0, float('nan'), 0])):
            changed = living(2, True)
            (changed[section] if section else changed)[field] = value
            trial = DeclaredInput(states=[changed])
            # Counter regressions must reach the predicate rather than the
            # callback's freshness filter, so test those at the key boundary.
            if field == 'wall_msec':
                trial.before = changed
            with self.subTest(field=field), self.assertRaises(FocusPreconditionLost):
                trial.run()
            self.assertNotIn('moved', trial.receipt)

    def test_living_move_retains_raw_before_after_and_original_ten_second_wait(self):
        moved = living(3, True)
        trial = DeclaredInput(states=[living(2), moved])
        self.assertEqual(trial.run(), moved)
        self.assertEqual(trial.receipt['status'], 'LIVING_MOVEMENT_OBSERVED')
        self.assertEqual(trial.receipt['before_key'], living(1))
        self.assertEqual(trial.receipt['last_after_key'], moved)
        self.assertEqual(trial.receipt['moved'], moved)
        self.assertEqual(trial.waits[0]['seconds'], 10)
        self.assertEqual(trial.waits[0]['after'], living(1)['wall_msec'])
        self.assertEqual(trial.keys, [('w', True), ('w', False)])

    def test_displacement_before_key_is_not_a_response_to_fresh_key(self):
        before = living(1, True)
        before['local_input']['move'] = [0, 0]
        unchanged = deepcopy(before)
        unchanged.update(wall_msec=before['wall_msec'] + 100, simulation_tick=before['simulation_tick'] + 1,
                         drawn_frames=before['drawn_frames'] + 1)
        unchanged['local_input']['move'] = [0, 1]
        trial = DeclaredInput(before=before, states=[unchanged])
        with self.assertRaises(TimeoutError):
            trial.run()
        self.assertNotIn('moved', trial.receipt)

    def test_timeout_is_unqualified_response_and_always_releases_key(self):
        for states in ([], [living(2)], [living(2, True)]):
            # A stale published moving snapshot cannot satisfy the response.
            trial = DeclaredInput(states=states)
            if states and states[0]['local_input']['move'] != [0, 0]:
                trial.before = deepcopy(states[0])
                trial.before['local_input']['move'] = [0, 0]
            with self.subTest(states=len(states)), self.assertRaises(TimeoutError):
                trial.run()
            self.assertEqual(trial.receipt['status'], 'RESPONSE_NOT_OBSERVED_BEFORE_ORIGINAL_DEADLINE')
            self.assertEqual(trial.keys[-1], ('w', False))
            self.assertEqual(trial.waits[0]['seconds'], 10)

    def test_release_guard_cannot_reengage_between_ack_and_key(self):
        for section, field, value in (
                ('ui', 'waiting_for_input_release', True),
                ('local_input', 'move', [0, 1]), ('local_input', 'fire', True)):
            before = living(1)
            before[section][field] = value
            trial = DeclaredInput(before=before)
            with self.subTest(field=field), self.assertRaisesRegex(FocusPreconditionLost, 'controls_not_released'):
                trial.run()
            self.assertEqual(trial.keys, [])
            self.assertEqual(trial.waits, [])

    def test_receipts_own_raw_values_instead_of_later_mutable_aliases(self):
        trial = DeclaredInput(states=[living(2, True)])
        trial.run()
        trial.before['local_actor']['health'] = 0
        trial.states[-1]['local_actor']['position'][2] += 10
        self.assertEqual(trial.receipt['before_key'], living(1))
        self.assertEqual(trial.receipt['moved'], living(2, True))


if __name__ == '__main__':
    unittest.main()
