#!/usr/bin/env python3
"""Independent source and synthetic controls; no engine, input or OCR execution."""
import ast
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / 'scripts'))
from native_settings_route import relocate_settings_actor
from test_native_settings_route import SettingsWalker

BASE = 'a089473481ced0f2e7b2a7468bbc5d079f92f0ff'
TARGET = 'af13a9979988d8b19de670fe27b78672ad2369ed'
HANDOFF = '66cf2cbcfec56aa7c61ec03a8adf6488228395a5'
ORIGINAL = Path('/workspace/reviews/windows-native-a089/builds/windows-native-a089-review/full/offline-input')
OUT = Path(__file__).parent
RECEIPTS = []


def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args])


def source(rev, name):
    return git('show', rev + ':' + name).decode()


def change(section, field, value):
    def mutate(state):
        (state[section] if section else state)[field] = deepcopy(value)
        return state
    return mutate


def segment_interval(a, b, low, high):
    # Clip the parameter interval independently against each of six planes.
    enter, leave = 0., 1.
    for coord in range(3):
        d = b[coord] - a[coord]
        if d == 0:
            if not low[coord] <= a[coord] <= high[coord]:
                return None
        else:
            t0 = (low[coord] - a[coord]) / d
            t1 = (high[coord] - a[coord]) / d
            enter, leave = max(enter, min(t0, t1)), min(leave, max(t0, t1))
    return [enter, leave] if enter <= leave else None


class IndependentSourceControls(unittest.TestCase):
    def test_exact_candidate_source_and_four_path_delta(self):
        paths = git('diff', '--name-only', BASE, TARGET, '--', 'scripts').decode().splitlines()
        self.assertEqual(paths, ['scripts/native_settings_route.py', 'scripts/test_native_settings_route.py',
                                 'scripts/validate.sh', 'scripts/verify_offline_export.py'])
        for name in paths:
            self.assertEqual((ROOT / name).read_bytes(), git('show', TARGET + ':' + name))
            self.assertEqual(git('show', HANDOFF + ':' + name), git('show', TARGET + ':' + name))
        for name in ['game', '.github', 'scripts/native_approach.py', 'scripts/native_focus_fence.py',
                     'scripts/verify_integration_export.py', 'scripts/native_observation.py', 'scripts/toolchain.py']:
            self.assertEqual(git('rev-parse', TARGET + ':' + name), git('rev-parse', BASE + ':' + name))
        RECEIPTS.append({'source_paths': paths, 'unchanged_game_tree': git('rev-parse', TARGET + ':game').decode().strip(),
                         'source_sha256': {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in paths}})

    def test_entire_original_controller_restores_byte_exact(self):
        original = source(BASE, 'scripts/verify_offline_export.py')
        candidate = (ROOT / 'scripts/verify_offline_export.py').read_text()
        first = "        second_live_until = min(deadline, time.monotonic() + 35)\n"
        before = "        wait_for(lambda: (out / 'client.log').read_text(encoding='utf-8', errors='replace').count('MATCH: Round live.') >= 2,\n"
        end = "        tap('2')\n"
        old_block = original[original.index(before):original.index(end, original.index(before))]
        new_block = candidate[candidate.index(first):candidate.index(end, candidate.index(first))]
        restored = candidate.replace('from native_settings_route import relocate_settings_actor\n', '', 1).replace(new_block, old_block, 1)
        self.assertEqual(restored, original)
        self.assertEqual(new_block.count('min(deadline, time.monotonic() + 35)'), 1)
        tree = ast.parse(candidate)
        call = next(n for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == 'relocate_settings_actor')
        kw = {k.arg: ast.unparse(k.value) for k in call.keywords}
        self.assertEqual(kw['deadline'], 'second_live_until')
        self.assertEqual(kw['round_number'], '2')
        self.assertEqual(kw['observe'], 'offline_observation')
        self.assertEqual(kw['key'], 'key')
        self.assertIn("parser.add_argument('--timeout', type=float, default=300,", original)
        RECEIPTS.append({'original_controller_restores_byte_exact': True, 'route_keywords': kw,
                         'original_controller_sha256': hashlib.sha256(original.encode()).hexdigest()})

    def test_original_failed_state_and_static_segment_binding(self):
        package = json.loads((OUT.parent / 'original-comparison.json').read_text())
        for binding in package['bindings']:
            data = (ORIGINAL / binding['path']).read_bytes()
            self.assertEqual(len(data), binding['bytes'])
            self.assertEqual(hashlib.sha256(data).hexdigest(), binding['sha256'])
        result = json.loads((ORIGINAL / 'results.json').read_text())
        events = [json.loads(line) for line in (ORIGINAL / 'initial-offline-trace/events.jsonl').read_text().splitlines() if line]
        before = result['hud_analysis_pauses'][-1]['before']
        self.assertEqual(before, package['raw_post_capture_before_analysis'])
        self.assertFalse(result['passed'])
        self.assertEqual(result['source']['source_commit'], BASE)
        actions = json.loads((ORIGINAL / 'actions.json').read_text())
        self.assertEqual([a for a in actions if a['seconds'] >= 100], package['original_actions'])
        self.assertEqual((before['simulation_tick'], before['local_actor']['health'], before['local_actor']['alive']), (3060, 100, True))
        death = next(e for e in events if e.get('event') == 'alive' and e.get('round_number') == 2 and e.get('local_actor', {}).get('alive') is False)
        kill = next(e for e in events if e.get('event') == 'notification' and e.get('message') == 'Kestrel  ›  Operator' and e['simulation_tick'] > 3060)
        self.assertEqual(kill['simulation_tick'], 3066)
        self.assertEqual(death['simulation_tick'], 3071)
        self.assertEqual(death, package['raw_dead_state'])
        self.assertEqual(kill, package['raw_later_death_notice'])
        arena = source(BASE, 'game/scripts/gameplay/arena.gd')
        actor = source(BASE, 'game/scripts/gameplay/actor.gd')
        movement = source(BASE, 'game/scripts/network/movement_step.gd')
        for fact in ['_container(Vector3(-7, 0, -11), Color("5d3034"), 9)', 'Vector3(3.0, 3.1, length)',
                     'Vector3((i - 2) * 2.2, 0.05, -21)', '_box(Vector3(0, 3, -24), Vector3(48, 6, 1)']:
            self.assertIn(fact, arena)
        self.assertIn('capsule.radius = 0.31', actor)
        self.assertIn('const WALK_SPEED := 5.1', movement)
        self.assertIn('28.0 if grounded else 7.0', movement)
        intervals = []
        for enemy in before['actors']:
            if enemy['team'] == 1 and enemy['alive'] is True:
                eye = [enemy['position'][0], enemy['position'][1] + 1.62, enemy['position'][2]]
                exposed = segment_interval(eye, [-4.4, 1.62, -21], [-8.5, 0, -15.5], [-5.5, 3.1, -6.5])
                cover = segment_interval(eye, [-7.8, 1.62, -21], [-8.5, 0, -15.5], [-5.5, 3.1, -6.5])
                self.assertIsNone(exposed)
                self.assertIsNotNone(cover)
                intervals.append({'actor_id': enemy['id'], 'original_position': enemy['position'], 'cover_interval': cover})
        self.assertEqual(len(intervals), 3)
        self.assertAlmostEqual(-21.75 - .31 - (-23.5), 1.44)
        self.assertAlmostEqual(-15.5 - (-20.25 + .31), 4.44)
        RECEIPTS.append({'original_run': 39916539053, 'original_failed': True, 'alive_tick': 3060,
                         'kill_notice_tick': 3066, 'dead_pause_tick': 3071,
                         'static_container_segments': intervals, 'whole_corridor_capsule_wall_clearance_m': 1.44,
                         'whole_corridor_capsule_container_clearance_m': 4.44,
                         'limits': 'One static box and sparse original clocks do not prove native LOS, route collision, screenshot cost, death cause or survival.'})


class IndependentRouteControls(unittest.TestCase):
    def assert_rejected(self, mutate, error=RuntimeError):
        world = SettingsWalker()
        world.mutation = mutate
        with self.assertRaises(error):
            world.route()
        self.assertFalse(world.requested)
        self.assertNotIn('endpoint', world.receipt)
        self.assertNotEqual(world.receipt['status'], 'FIXED_ROUTE_REACHED')
        return world

    def test_identity_phase_health_weapon_and_input_loss_matrix(self):
        cases = [('', 'schema', True), ('', 'schema', 2), ('', 'scope', 'other'), ('', 'scenario', 'fixture'),
                 ('', 'round_number', True), ('', 'round_number', 3), ('', 'phase', 'post'),
                 ('', 'time_scale', .5), ('', 'simulation_tick', -1), ('', 'wall_msec', -1),
                 ('local_actor', 'id', 2), ('local_actor', 'id', True), ('local_actor', 'deaths', 0),
                 ('local_actor', 'deaths', 2), ('local_actor', 'deaths', True), ('local_actor', 'team', 1),
                 ('local_actor', 'weapon', 'sidearm'), ('local_actor', 'ammo', 29), ('local_actor', 'reserve', 119),
                 ('local_actor', 'ammo', 30.), ('local_actor', 'alive', False), ('local_actor', 'health', 0),
                 ('local_actor', 'health', 101), ('local_actor', 'health', True), ('local_actor', 'health', float('inf')),
                 ('ui', 'focused', False), ('ui', 'paused', True), ('ui', 'screen', 'menu'),
                 ('ui', 'scoreboard_visible', True), ('ui', 'waiting_for_input_release', True),
                 ('local_input', 'fire', True), ('local_input', 'interact', True), ('local_input', 'reload', True),
                 ('local_input', 'move', [True, 0]), ('local_input', 'move', [0, float('nan')])]
        for section, field, value in cases:
            with self.subTest(section=section, field=field, value=value):
                world = self.assert_rejected(change(section, field, value))
                self.assertIn('previous_valid_state', world.receipt['precondition_loss'])
                self.assertEqual(world.receipt['precondition_loss']['rejected_state'][section][field] if section else world.receipt['precondition_loss']['rejected_state'][field], value) if not (isinstance(value, list) and any(isinstance(x, float) and math.isnan(x) for x in value)) else None
        RECEIPTS.append({'additional_rejection_vectors': len(cases)})

    def test_ground_corridor_all_sides_and_nonfinite_motion(self):
        for field, index, value in [('position', 0, -8.51), ('position', 0, -3.89),
                                     ('position', 1, -.11), ('position', 1, .11),
                                     ('position', 2, -21.76), ('position', 2, -20.24),
                                     ('position', 0, float('nan')), ('velocity', 2, float('inf'))]:
            def mutate(state):
                state['local_actor'][field][index] = value
                return state
            with self.subTest(field=field, index=index, value=value):
                self.assert_rejected(mutate)

    def test_static_endpoint_tolerance_sampling_retains_recorded_occluder(self):
        package = json.loads((OUT.parent / 'original-comparison.json').read_text())
        samples = 0
        for enemy in package['raw_post_capture_before_analysis']['actors']:
            if enemy['team'] == 1 and enemy['alive'] is True:
                eye = [enemy['position'][0], enemy['position'][1] + 1.62, enemy['position'][2]]
                for degree in range(360):
                    target = [-7.8 + .449 * math.cos(math.radians(degree)), 1.62,
                              -21 + .449 * math.sin(math.radians(degree))]
                    self.assertIsNotNone(segment_interval(eye, target, [-8.5, 0, -15.5], [-5.5, 3.1, -6.5]))
                    samples += 1
        self.assertEqual(samples, 1080)
        RECEIPTS.append({'static_endpoint_tolerance_edge_segment_samples': samples,
                         'limits': 'Finite static samples only; no continuous native LOS or survival claim.'})

    def test_malformed_nested_state_and_missing_fields_fail(self):
        for mutate in [lambda s: None, change('', 'local_actor', []), change('', 'ui', None), change('', 'local_input', False),
                       lambda s: {k: v for k, v in s.items() if k != 'simulation_tick'},
                       change('local_actor', 'position', [-4.4, -21]), change('local_actor', 'yaw', False)]:
            self.assert_rejected(mutate)

    def test_positive_damage_is_retained_without_life_or_ammo_replacement(self):
        world = SettingsWalker(rate=.7, delivery=.2, publication_lag=.1)
        world.mutation = change('local_actor', 'health', 1)
        endpoint = world.route()
        self.assertEqual(world.receipt['after']['local_actor']['health'], 1)
        self.assertEqual(world.receipt['after']['local_actor']['deaths'], 1)
        self.assertEqual(world.receipt['after']['local_actor']['ammo'], 30)
        self.assertFalse(world.requested)
        (OUT / 'positive-damage-model.json').write_text(json.dumps({'receipt': world.receipt, 'records': world.records}, indent=2) + '\n')
        RECEIPTS.append({'positive_damage_control': {'start_health': 100, 'after_health': 1, 'endpoint': endpoint,
                         'seconds': world.wall, 'status': world.receipt['status']}})

    def test_late_observation_and_late_completion_record_cannot_pass_cap(self):
        for stage in ['observe', 'record']:
            world = SettingsWalker()
            if stage == 'observe':
                old = world.observe
                def slow():
                    state = old()
                    world.pause(1)
                    return state
                world.observe = slow
                cap = .5
            else:
                old = world.record
                def slow(event, **data):
                    old(event, **data)
                    if event == 'movement_completed':
                        world.pause(35)
                world.record = slow
                cap = 35
            with self.subTest(stage=stage), self.assertRaises(TimeoutError):
                world.route(deadline=cap)
            self.assertFalse(world.requested)
            self.assertNotIn('endpoint', world.receipt)
            self.assertEqual(world.receipt['status'], 'FIXED_ROUTE_FAILED')

    def test_short_original_remaining_cap_is_never_reset(self):
        for spent in [34., 34.9, 34.99, 35., 40.]:
            world = SettingsWalker()
            world.pause(spent)
            with self.subTest(spent=spent), self.assertRaises(TimeoutError):
                world.route(deadline=35)
            self.assertFalse(world.requested)
            self.assertNotIn('endpoint', world.receipt)
            self.assertLessEqual(world.wall, max(spent, 35) + 1e-8)

    def test_read_failure_after_movement_releases_all_keys(self):
        world = SettingsWalker()
        old = world.observe
        def unavailable():
            if world.wall > .6:
                raise OSError('independent unreadable producer')
            return old()
        world.observe = unavailable
        with self.assertRaisesRegex(OSError, 'independent unreadable producer'):
            world.route()
        self.assertFalse(world.requested)
        self.assertGreater(len(world.receipt['observations']), 1)
        self.assertNotIn('endpoint', world.receipt)

    def test_duplicate_stopped_endpoint_cannot_supply_two_later_ticks(self):
        world = SettingsWalker()
        old = world.observe
        frozen = None
        def repeat():
            nonlocal frozen
            state = old()
            if world.wall > .6:
                if frozen is None:
                    frozen = deepcopy(state)
                    frozen['local_actor'].update(position=[-7.8, 0, -21], velocity=[0, 0, 0])
                    frozen['local_input']['move'] = [0, 0]
                return deepcopy(frozen)
            return state
        world.observe = repeat
        with self.assertRaises(TimeoutError):
            world.route()
        self.assertFalse(world.requested)
        self.assertNotIn('endpoint', world.receipt)

    def test_native_delivery_exception_still_attempts_all_final_releases(self):
        world = SettingsWalker()
        old = world.key
        calls = []
        failed = False
        def delivery(name, down):
            nonlocal failed
            calls.append([name, down])
            if name == 'd' and down and not failed:
                failed = True
                old(name, down)
                raise OSError('independent native delivery exception')
            return old(name, down)
        world.key = delivery
        with self.assertRaisesRegex(OSError, 'independent native delivery exception'):
            world.route()
        self.assertFalse(world.requested)
        self.assertEqual(calls[-4:], [[k, False] for k in ('w', 'a', 's', 'd')])
        self.assertNotIn('endpoint', world.receipt)

    def test_release_error_attempts_every_key_and_cannot_pass(self):
        world = SettingsWalker()
        old = world.key
        calls = []
        def delivery(name, down):
            calls.append([name, down])
            if name == 'w' and not down:
                raise OSError('independent release error')
            return old(name, down)
        world.key = delivery
        with self.assertRaisesRegex(RuntimeError, 'could not release all'):
            world.route()
        self.assertEqual(calls, [[k, False] for k in ('w', 'a', 's', 'd')] * 2)
        self.assertNotIn('endpoint', world.receipt)


if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    run = unittest.TextTestRunner(verbosity=2).run(suite)
    (OUT / 'independent-results.json').write_text(json.dumps({'target': TARGET, 'base': BASE, 'handoff': HANDOFF,
        'pure_only': True, 'methods': run.testsRun, 'failures': len(run.failures), 'errors': len(run.errors),
        'receipts': RECEIPTS}, indent=2, allow_nan=False) + '\n')
    raise SystemExit(not run.wasSuccessful())
