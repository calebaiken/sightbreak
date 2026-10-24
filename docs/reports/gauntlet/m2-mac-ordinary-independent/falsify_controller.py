#!/usr/bin/env python3
"""Execute frozen controller predicates with invented data; never run native code.

The AST extraction keeps actual nested controller functions under test. No Godot,
CGEvent, Swift compiler, graphics API, subprocess or network operation is invoked.
Pass a checkout of the frozen candidate as the sole argument.
"""
import ast
import copy
import json
from pathlib import Path
import sys
import types
import unittest


ROOT = Path(sys.argv.pop(1)).resolve()
sys.path.insert(0, str(ROOT / 'scripts'))
import macos_ordinary_input as ordinary

CONTROLLER = ROOT / 'scripts/verify_macos_ordinary.py'
TREE = ast.parse(CONTROLLER.read_text())
RUN = next(node for node in TREE.body if isinstance(node, ast.FunctionDef) and node.name == 'run')


def actual(name, environment):
    nodes = [node for node in ast.walk(RUN) if isinstance(node, ast.FunctionDef) and node.name == name]
    if len(nodes) != 1:
        raise AssertionError('Expected exactly one actual controller function: '+name)
    code = ast.fix_missing_locations(ast.Module(body=[copy.deepcopy(nodes[0])], type_ignores=[]))
    exec(compile(code, str(CONTROLLER), 'exec'), environment)
    return environment[name]


def state():
    return {'schema': 1, 'scope': 'debug_offline_read_only_observation', 'scenario': 'standard',
            'time_scale': 1, 'phase': 'live', 'wall_msec': 100, 'drawn_frames': 100,
            'simulation_tick': 100, 'elapsed': 10., 'round_number': 1,
            'local_actor': {'alive': True, 'health': 100, 'weapon': 'sidearm', 'id': 1,
                            'ammo': 14, 'reserve': 60, 'reload': 0},
            'ui': {'screen': 'game', 'focused': True, 'paused': False}}


class Clock:
    def __init__(self):
        self.now = 0.
    def monotonic(self):
        return self.now
    def sleep(self, seconds):
        self.now += seconds


class ControllerFalsifiers(unittest.TestCase):
    def test_acknowledgements_do_not_extend_original_fire_schedule(self):
        loops = [node for node in ast.walk(RUN) if isinstance(node, ast.For)
                 and isinstance(node.target, ast.Name) and node.target.id == '_']
        self.assertEqual(len(loops), 1)
        clock, events = Clock(), []
        def fire(down):
            events.append((down, clock.now))
        def acknowledge(*args, **kwargs):
            clock.sleep(.2)
        env = {'ui': types.SimpleNamespace(fire_button=fire, observed_state=acknowledge),
               'pause': clock.sleep, 'time': clock, 'deadline': 300, 'BUDGETS': {'fire': 5},
               'trace': lambda *a, **kw: None}
        actual('remaining', env)
        fragment = ast.fix_missing_locations(ast.Module(body=[copy.deepcopy(loops[0])], type_ignores=[]))
        try:
            exec(compile(fragment, str(CONTROLLER), 'exec'), env)
        except (RuntimeError, TimeoutError):
            self.assertTrue(events)
            self.assertFalse(events[-1][0], 'A rejected delayed acknowledgement must still release LMB')
            return
        self.assertEqual([down for down, _ in events], [True, False, True, False])
        self.assertAlmostEqual(events[1][1]-events[0][1], 1.)
        self.assertAlmostEqual(events[3][1]-events[2][1], 1.)
        self.assertAlmostEqual(events[2][1]-events[1][1], .35)

    def test_helper_command_rejects_success_returning_after_its_original_budget(self):
        import tempfile
        for budget in (25, 60):
            with tempfile.TemporaryDirectory() as temporary:
                clock = Clock()
                def wait(timeout):
                    self.assertLessEqual(timeout, budget)
                    clock.now = budget + .001
                process = types.SimpleNamespace(wait=wait, returncode=0)
                env = {'time': clock, 'deadline': 300, 'trace': lambda *a, **kw: None,
                       'output': Path(temporary), 'processes': [], 'failed': lambda _: False,
                       'subprocess': types.SimpleNamespace(Popen=lambda *a, **kw: process, STDOUT=-2)}
                actual('remaining', env)
                command = actual('command', env)
                with self.subTest(budget=budget), self.assertRaises(TimeoutError):
                    command('invented-helper', ['never-executed'], budget)

    def test_capture_rejects_foreign_window_geometry_permission_and_missing_evidence(self):
        import tempfile
        bounds = [40, 60, 1280, 748]
        original = {'passed': True, 'scope': 'OS window screenshot from ScreenCaptureKit; read-only helper',
                    'owner_pid': 1234, 'window_id': 44, 'bounds_points_including_chrome': bounds,
                    'scwindow_frame_points': bounds, 'filter_content_rect_points': [0, 0, 1280, 748],
                    'point_pixel_scale': 2, 'image_dimensions': [2560, 1496], 'text': [],
                    'permissions': {'CGPreflightScreenCaptureAccess': True},
                    'input_events_posted': 0, 'permission_requests_made': 0}
        for fault in ('none', 'pid', 'window', 'bounds', 'retina', 'permission', 'posted', 'no-png', 'no-receipt'):
            with tempfile.TemporaryDirectory() as temporary:
                output = Path(temporary)
                data = copy.deepcopy(original)
                if fault == 'pid': data['owner_pid'] += 1
                elif fault == 'window': data['window_id'] += 1
                elif fault == 'bounds': data['bounds_points_including_chrome'][0] += 10
                elif fault == 'retina': data['image_dimensions'][0] -= 1
                elif fault == 'permission': data['permissions']['CGPreflightScreenCaptureAccess'] = False
                elif fault == 'posted': data['input_events_posted'] = 1
                def command(_, arguments, *args, **kwargs):
                    if fault != 'no-png': Path(arguments[arguments.index('--png')+1]).write_bytes(b'invented, never displayed')
                    if fault != 'no-receipt': Path(arguments[arguments.index('--report')+1]).write_text(json.dumps(data))
                    return 0
                ui = types.SimpleNamespace(pid=1234, window=44, bounds=bounds, require_target=lambda: None,
                                           require_window=lambda: None, diagnostics=lambda: {}, focus_state=lambda: {})
                env = {'remaining': lambda *_: 100, 'ui': ui, 'client': types.SimpleNamespace(pid=1234),
                       'output': output, 'helper': output / 'invented-helper', 'command': command,
                       'BUDGETS': {'capture': 25}, 'json': json, 'same_bounds': ordinary.same_bounds,
                       'capture_geometry': ordinary.capture_geometry, 'trace': lambda *a, **kw: None,
                       'result': {'captures': []}, 'digest': ordinary.digest,
                       'NativePrerequisiteBlocked': ordinary.NativePrerequisiteBlocked}
                capture = actual('capture', env)
                with self.subTest(fault=fault):
                    if fault == 'none': self.assertEqual(capture('invented'), data)
                    else:
                        with self.assertRaises((RuntimeError, OSError)):
                            capture('invented')

    def test_wait_rejects_late_predicate_success_and_clips_total(self):
        for stage, total in ((5., 300.), (300., 5.)):
            clock = Clock()
            env = {'time': clock, 'deadline': total, 'client': None, 'trace': lambda *a, **kw: None}
            actual('remaining', env)
            wait = actual('wait', env)
            def late():
                clock.now = 5.001
                return {'success': True}
            with self.subTest(stage=stage, total=total), self.assertRaises(TimeoutError):
                wait(late, stage, 'invented late success')

    def test_observed_rejects_stale_wall_and_boolean_timestamp(self):
        for wall in (99, 100, True):
            env = {'trace': lambda *a, **kw: None, 'observation': lambda: {'wall_msec': wall},
                   'wait': lambda predicate, *_: predicate()}
            observed = actual('observed', env)
            if wall is True:
                with self.assertRaises(RuntimeError):
                    observed(lambda _: True, 5, 'invented stale state', 100)
            else:
                self.assertIsNone(observed(lambda _: True, 5, 'invented stale state', 100))

    def test_fire_requires_same_living_context_depletion_and_two_frames(self):
        origin = state()
        origin['local_actor']['ammo'] = 15
        env = {'check_context': lambda row: ordinary.living_context(row, origin), 'fire_frame': [None]}
        fired = actual('fired', env)
        self.assertFalse(fired(origin))
        ack = state()
        self.assertFalse(fired(ack))
        ack['drawn_frames'] = 101
        self.assertFalse(fired(ack))
        ack['drawn_frames'] = 102
        self.assertTrue(fired(ack))
        for path, value in [('phase', 'post'), ('time_scale', 2), ('round_number', 2),
                            ('local_actor.alive', False), ('local_actor.health', 0),
                            ('local_actor.id', 2), ('local_actor.weapon', 'rifle'),
                            ('local_actor.reserve', 59), ('local_actor.reload', .1),
                            ('ui.focused', False), ('ui.paused', True)]:
            bad = copy.deepcopy(ack)
            parts = path.split('.')
            (bad if len(parts) == 1 else bad[parts[0]])[parts[-1]] = value
            with self.subTest(path=path), self.assertRaises(RuntimeError):
                fired(bad)

    def test_reload_requires_observed_countdown_no_early_transfer_and_conservation(self):
        depleted = state()
        env = {'check_context': lambda row: ordinary.living_context(row, depleted), 'depleted': depleted}
        started = actual('reload_started', env)
        self.assertFalse(started(depleted))
        beginning = copy.deepcopy(depleted)
        beginning['local_actor']['reload'] = 1.3
        self.assertTrue(started(beginning))
        early = copy.deepcopy(beginning)
        early['local_actor']['ammo'] = 15
        early['local_actor']['reserve'] = 59
        with self.assertRaises(RuntimeError):
            started(early)
        env['beginning'] = beginning
        completed = actual('reload_completed', env)
        self.assertFalse(completed(beginning))
        good = copy.deepcopy(depleted)
        good['local_actor'].update(ammo=15, reserve=59)
        good['elapsed'] += 1.3
        self.assertTrue(completed(good))
        for change in ('early', 'reserve', 'ammo', 'dead', 'round', 'weapon'):
            bad = copy.deepcopy(good)
            if change == 'early': bad['elapsed'] -= .1
            elif change == 'reserve': bad['local_actor']['reserve'] = 60
            elif change == 'ammo': bad['local_actor']['ammo'] = 14
            elif change == 'dead': bad['local_actor']['alive'] = False
            elif change == 'round': bad['round_number'] = 2
            else: bad['local_actor']['weapon'] = 'rifle'
            with self.subTest(change=change), self.assertRaises(RuntimeError):
                completed(bad)

    def test_hud_capture_rejects_dead_bracket_and_wrong_rendered_ammunition(self):
        expected = state()
        before, after = copy.deepcopy(expected), copy.deepcopy(expected)
        before['wall_msec'], after['wall_msec'] = 101, 102
        for fault in ('none', 'dead-before', 'dead-after', 'wrong-ammo', 'wrong-reserve', 'health-outside'):
            observations = [copy.deepcopy(before), copy.deepcopy(after)]
            values = {'health': 100, 'ammo': 14, 'reserve': 60}
            if fault == 'dead-before': observations[0]['local_actor']['alive'] = False
            elif fault == 'dead-after': observations[1]['local_actor']['alive'] = False
            elif fault == 'wrong-ammo': values['ammo'] = 15
            elif fault == 'wrong-reserve': values['reserve'] = 59
            elif fault == 'health-outside': values['health'] = 99
            def observed(predicate, *_):
                row = observations.pop(0)
                if not predicate(row):
                    raise AssertionError('Unexpected invented predicate false')
                return row
            env = {'observed': observed, 'check_context': lambda row: ordinary.living_context(row, expected),
                   'capture': lambda _: {}, 'hud_values': lambda _: values, 'result': {}}
            screenshot = actual('screenshot_hud', env)
            with self.subTest(fault=fault):
                if fault == 'none':
                    self.assertEqual(screenshot('invented', expected), after)
                else:
                    with self.assertRaises(RuntimeError):
                        screenshot('invented', expected)

    def test_finalization_turns_cleanup_leak_or_source_failure_into_failure(self):
        final = next(node for node in RUN.body if isinstance(node, ast.Try) and node.finalbody).finalbody
        code = compile(ast.fix_missing_locations(ast.Module(body=copy.deepcopy(final), type_ignores=[])),
                       str(CONTROLLER), 'exec')
        import tempfile
        for fault in ('none', 'group-survives', 'fallback-signal', 'source-change', 'leak', 'release-error', 'whole-timeout'):
            with tempfile.TemporaryDirectory() as temporary:
                output = Path(temporary)
                if fault == 'leak': (output / 'client.log').write_text('ObjectDB instances leaked at exit\n')
                clock = Clock()
                if fault == 'whole-timeout': clock.now = 300.001
                released = {'held_after_release': [], 'errors': [],
                            'native_state': {'lmb_down': False, 'escape_down': False, 'reload_down': False}}
                if fault == 'release-error': released['errors'] = ['invented release failure']
                ui = types.SimpleNamespace(release_owned=lambda: released, event_post_attempts=7, close=lambda: None)
                result = {'passed': True}
                env = {'ui': ui, 'client': None, 'result': result, 'processes': [('invented-helper', types.SimpleNamespace(pid=1))],
                       'ordinary_failure_close': lambda *_: {'needed': False},
                       'reap': lambda _: {'pid': 1, 'owned_group_gone': fault != 'group-survives',
                                         'signals_sent': ['SIGTERM'] if fault == 'fallback-signal' else []},
                       'staged': None, 'default_before': None, 'private_directory': None,
                       'before': {'frozen': True}, 'source': lambda: {'frozen': fault != 'source-change'},
                       'validate_record': lambda *_: None, 'time': clock, 'started': 0.,
                       'BUDGETS': {'total': 300}, 'output': output, 'json': json,
                       'failed': lambda content: 'leaked' in content}
                exec(code, env)
                with self.subTest(fault=fault):
                    self.assertEqual(result['passed'], fault == 'none')
                    self.assertEqual(result['status'], 'PASS_ORDINARY_MAC_COMPONENT_ONLY' if fault == 'none' else 'FAILED')
                    self.assertTrue((output / 'results.json').is_file())


if __name__ == '__main__':
    unittest.main(verbosity=2)
