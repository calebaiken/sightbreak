#!/usr/bin/env python3
"""Pure execution of actual focus-resume AST and existing controller helpers."""
import ast
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import unittest

from native_focus_fence import FocusContextFence, FocusPreconditionLost


ROOT = Path(__file__).resolve().parent
TREE = ast.parse((ROOT / 'verify_offline_export.py').read_text())
RAW = json.loads((ROOT / 'fixtures/offline_focus_observations.json').read_text())
LABEL = 'Explicit resume with W and LMB still physically held'


def function(tree, name):
    return next(node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == name)


def resume_block(tree):
    for node in ast.walk(tree):
        if not isinstance(node, ast.Try):
            continue
        for index, statement in enumerate(node.body):
            if (isinstance(statement, ast.Assign) and any(isinstance(value, ast.Constant) and value.value == LABEL
                                                        for value in ast.walk(statement))):
                # Exactly the physical down/hold/up prefix plus its existing ACK.
                begin = index - (1 if isinstance(node.body[index - 1], ast.Expr)
                                 and isinstance(node.body[index - 1].value, ast.Call)
                                 and getattr(node.body[index - 1].value.func, 'id', '') == 'tap' else 3)
                return node.body, begin, index
    raise AssertionError('Actual focus-resume block not found')


def state(offset, *, paused):
    value = deepcopy(RAW['last_living_guard'])
    value['wall_msec'] += offset * 100
    value['simulation_tick'] += offset
    value['drawn_frames'] += offset
    value['ui']['paused'] = paused
    return value


class ResumeTrial:
    def __init__(self, states=(), *, deadline=300):
        self.elapsed, self.events, self.held = 0, [], {'w'}
        self.states = list(states)
        self.context = {}
        fence = FocusContextFence(RAW['focus_start'], self.context)

        class Clock:
            def monotonic(_):
                return self.elapsed
            def sleep(_, seconds):
                self.events.append(('sleep', seconds, self.elapsed))
                self.elapsed += seconds

        class UI:
            def key(_, name, down):
                self.events.append(('physical_key', name, down, self.elapsed))

        def trace(event, **values):
            self.events.append((event, values, self.elapsed))

        namespace = {'time': Clock(), 'deadline': deadline, 'client': None,
                     'trace': trace, 'held_keys': self.held, 'ui': UI(), 'cleanup_errors': [],
                     'fence': fence,
                     'offline_observation': lambda: self.states.pop(0) if self.states else {},
                     'restored': state(0, paused=True),
                     'require_focus_context': lambda value, stage='focus_context', **kw: fence.require(value, stage, **kw)}
        for name in ('remaining', 'pause', 'wait_for', 'key', 'tap', 'observed', 'focus_observed'):
            node = function(TREE, name)
            exec(compile(ast.Module(body=[node], type_ignores=[]), 'actual-controller:' + name, 'exec'), namespace)
        body, begin, end = resume_block(TREE)
        module = ast.Module(body=deepcopy(body[begin:end + 1]), type_ignores=[])
        self.code = compile(ast.fix_missing_locations(module), 'actual-controller:focus-resume', 'exec')
        self.namespace = namespace
        # Preserve the actual whole-flow final cleanup loop for interrupted holds.
        cleanup = next(node for node in ast.walk(TREE) if isinstance(node, ast.For)
                       and ast.unparse(node.iter) == 'list(held_keys)')
        self.cleanup_code = compile(ast.Module(body=[deepcopy(cleanup)], type_ignores=[]), 'actual-controller:cleanup', 'exec')

    def run(self):
        exec(self.code, self.namespace)
        return self.namespace['guarded']


class FocusResumeTiming(unittest.TestCase):
    def test_actual_prefix_holds_escape_point_three_then_immediately_starts_explicit_ack(self):
        ready = state(1, paused=False)
        trial = ResumeTrial([ready])
        self.assertEqual(trial.run(), ready)
        self.assertEqual([event for event in trial.events if event[0] == 'physical_key'],
                         [('physical_key', 'Escape', True, 0), ('physical_key', 'Escape', False, .3)])
        begin = next(event for event in trial.events if event[0] == 'wait_begin')
        self.assertEqual(begin[2], .3)
        self.assertEqual(begin[1]['label'], LABEL)
        self.assertEqual(begin[1]['budget_seconds'], 10)
        self.assertEqual(trial.elapsed, .3)
        self.assertEqual(trial.held, {'w'})

    def test_pause_ack_requires_actual_unpaused_fresh_state_after_escape_up(self):
        trial = ResumeTrial([state(1, paused=True), state(2, paused=False)])
        self.assertEqual(trial.run()['ui']['paused'], False)
        self.assertAlmostEqual(trial.elapsed, .4)
        up = next(event for event in trial.events if event[:3] == ('physical_key', 'Escape', False))
        complete = next(event for event in trial.events if event[0] == 'wait_completed')
        self.assertGreater(complete[2], up[3])

    def test_dead_context_during_ack_remains_failed_and_escape_is_already_released(self):
        dead = state(1, paused=False)
        dead['local_actor'].update(alive=False, health=0)
        trial = ResumeTrial([dead])
        with self.assertRaises(FocusPreconditionLost):
            trial.run()
        self.assertEqual(trial.held, {'w'})
        self.assertEqual(trial.context['status'], 'FOCUS_PRECONDITION_LOST')
        self.assertEqual(trial.context['precondition_loss']['rejected_state'], dead)

    def test_original_ten_second_ack_deadline_is_retained(self):
        trial = ResumeTrial([state(1, paused=True)])
        with self.assertRaisesRegex(TimeoutError, LABEL):
            trial.run()
        self.assertGreaterEqual(trial.elapsed, 10.3)
        self.assertLess(trial.elapsed, 10.4 + 1e-9)
        self.assertEqual(trial.held, {'w'})

    def test_whole_deadline_still_caps_ack_wait(self):
        trial = ResumeTrial([state(1, paused=True)], deadline=.75)
        with self.assertRaises(TimeoutError):
            trial.run()
        self.assertGreaterEqual(trial.elapsed, .75)
        self.assertLess(trial.elapsed, .85)
        self.assertEqual(trial.held, {'w'})

    def test_existing_final_cleanup_releases_escape_when_deadline_blocks_hold(self):
        trial = ResumeTrial(deadline=.2)
        with self.assertRaisesRegex(TimeoutError, 'Whole offline-input flow deadline exceeded'):
            trial.run()
        self.assertEqual(trial.held, {'w', 'Escape'})
        exec(trial.cleanup_code, trial.namespace)
        self.assertIn(('physical_key', 'Escape', False, 0), trial.events)
        self.assertFalse(any(event[0] == 'wait_begin' for event in trial.events))

    def test_generic_tap_keeps_its_original_post_up_second(self):
        trial = ResumeTrial()
        trial.namespace['tap']('Escape')
        self.assertEqual([event[1] for event in trial.events if event[0] == 'sleep'], [.3, 1])
        self.assertAlmostEqual(trial.elapsed, 1.3)

    def test_controller_ast_diff_allows_only_this_one_focus_invocation_replacement(self):
        baseline = ast.parse(subprocess.check_output(
            ['git', 'show', 'fa718ef:scripts/verify_offline_export.py'], text=True))
        changed = deepcopy(TREE)
        before_body, before_start, before_end = resume_block(baseline)
        body, start, end = resume_block(changed)
        self.assertEqual([ast.unparse(node) for node in body[start:end]],
                         ["key('Escape', True)", 'pause(0.3)', "key('Escape', False)"])
        body[start:end] = deepcopy(before_body[before_start:before_end])
        self.assertEqual(ast.dump(changed), ast.dump(baseline))


if __name__ == '__main__':
    unittest.main()
