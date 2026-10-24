#!/usr/bin/env python3
"""Complete synthetic schema controls. No fixture here claims native execution."""
import copy
import json
import math
from pathlib import Path
import shutil
import tempfile
import unittest
import verify_bot_objective_observation as oracle

ROOT = Path(__file__).resolve().parents[1]


def command(look=None, interact=False):
    return {'move': [0, 0], 'look': look or [0, 0], **dict.fromkeys(oracle.BOOL_COMMAND, False), 'weapon': '', 'interact': interact}


def protected(index=122):
    pose = oracle.original()[index]
    c = oracle.contract()
    actors = {}
    for r in pose['actors']:
        a = {k: copy.deepcopy(r[k]) for k in ('team', 'kills', 'assists', 'deaths', 'position', 'velocity', 'yaw', 'pitch', 'alive', 'health', 'weapon', 'ammo', 'reserve', 'reload', 'inventory', 'credits', 'grenades', 'smokes')}
        a.update(deploy=0.0, ammo_store={w: c['ammo_defaults'][w] for w in r['inventory']}, recoil=[0, 0], rng='-9215223372036854755', cooldowns={}, shot_index=0, fire_previous=False, jump_previous=False, grenade_previous=False, smoke_previous=False, crouching=False, head_height=1.62, floor_contact=False, collision_disabled=not r['alive'], collision_height=1.8, collision_position=[0, .9, 0], input=command([r['yaw'], r['pitch']]))
        actors[str(r['id'])] = a
    bots = {}
    for r in pose['actors']:
        b = copy.deepcopy(c['bot_reset']); b['last_position'] = r['position']; bots[str(r['id'])] = b
    teams = {'0': copy.deepcopy(c['team_reset']), '1': copy.deepcopy(c['team_reset'])}
    teams['0'].update(primary_site=pose['round_number'] % 2, target_site=pose['round_number'] % 2)
    return {'actors': actors, 'utilities': [], 'rng': '9223372036854775801', 'bots': bots, 'teams': teams, 'heard': {}, 'objective': pose['objective_state'], 'carrier': pose['objective_carrier'], 'objective_position': pose['objective_position'], 'objective_timer': pose['objective_timer'], 'contributions': {}, 'interaction_progress': 0.0, 'damage_history': {}, 'round': pose['round_number'], 'attack_score': pose['attack_score'], 'defend_score': pose['defend_score'], 'bot_clock': 0.0, 'interactions': {}, 'time_left': pose['time_left'], 'tick': pose['simulation_tick'], 'elapsed': pose['elapsed'], 'phase': 'live'}


def decision(label, before, aid=6, interact=False):
    before = copy.deepcopy(before)
    after = copy.deepcopy(before)
    actor = before['actors'][str(aid)]
    cmd = command([actor['yaw'], actor['pitch']], interact)
    after['actors'][str(aid)]['input'] = cmd
    candidates = [{'id': int(i), 'distance': math.dist(actor['position'], a['position']), 'reason': ('range' if math.dist(actor['position'], a['position']) > 38 else 'visibility')} for i, a in before['actors'].items() if a['alive'] and a['team'] != actor['team']]
    destination = [15, 0, 10]
    defenders = [(math.dist(a['position'], before['objective_position']), int(i)) for i, a in before['actors'].items() if a['alive'] and a['team'] == 1]
    defuser = before['objective'] == 'planted' and actor['team'] == 1 and aid == (min(defenders)[1] if defenders else 0)
    if defuser:
        destination = copy.deepcopy(before['objective_position'])
    obs = {'enabled': True, 'operation': 'decision', 'status': 'complete', 'candidates': candidates, 'rng_before': before['rng'], 'plan': {'destination': destination, 'interact': interact, 'primary_site': 1}, 'movement_mode': 'interact' if interact else 'navigate', 'navigation_waypoint': actor['position'], 'navigation_destination': None if interact else destination, 'target_distance': None, 'aligned': None, 'decision': {'actor_id': aid, 'target_id': 0, 'role': ('defuser' if interact and actor['team'] == 1 else ('carrier' if aid == before['carrier'] else ('anchor' if actor['team'] == 1 else 'escort'))), 'destination': destination, 'interact': interact, 'stuck': 0.0, 'command': cmd, 'rng_after': after['rng']}}
    if defuser:
        obs['decision']['role'] = 'defuser'
    return {'label': label, 'tick': before['tick'], 'elapsed': before['elapsed'], 'dt': .12, 'actor_id': aid, 'position': actor['position'], 'before': before, 'after': after, 'observation': obs}


def interaction(label, before, after):
    predicates = {aid: {'alive': a['alive'], 'team': a['team'], 'position': a['position'], 'interact': a['input']['interact'], 'move': a['input']['move'], 'site': oracle.site(a['position']), 'objective_distance': math.dist(a['position'], before['objective_position']), 'progress': before['interactions'].get(aid, 0.0)} for aid, a in before['actors'].items()}
    return {'label': label, 'tick': before['tick'], 'dt': oracle.DT, 'objective_before': before['objective'], 'objective_after': after['objective'], 'carrier_before': before['carrier'], 'carrier_after': after['carrier'], 'actors_before': predicates, 'progress_after': copy.deepcopy(after['interactions']), 'before': copy.deepcopy(before), 'after': copy.deepcopy(after)}


def synthetic_records():
    """Schema-positive data, with source poses and all streams. Not an engine model."""
    header = oracle.contract()
    header.update(engine={'major': 4, 'minor': 7, 'patch': 2}, time_scale=1.0, physics_ticks_per_second=60)
    rows = [('HEADER', header)]
    complete = decision('unused', protected(120))['observation']
    for name in header['freshness_cases']:
        if name in ('live_complete', 'branch_change'):
            out = copy.deepcopy(complete)
        elif name == 'empty_default': out = {}
        elif name == 'direct_perception': out = {'enabled': True, 'operation': 'perception', 'status': 'complete', 'candidates': [], 'target_id': 0}
        else:
            status = {'live_to_dead': 'dead', 'live_to_post': 'non_live', 'offline_to_online': 'blocked'}.get(name, 'disabled')
            out = {'enabled': status != 'disabled', 'operation': 'decision', 'status': status}
        rows.append(('CALL', {'case': name, 'output': out}))
    for index in oracle.POSES:
        before = protected(index)
        row = decision('pose_' + str(index), before)
        rows.append(('PAIR', {'event_index': index, 'equal': True, 'before_off': copy.deepcopy(before), 'before_on': copy.deepcopy(before), 'after_off': copy.deepcopy(row['after']), 'after_on': copy.deepcopy(row['after'])}))
        rows.append(('DECISION', row))
    current = protected()
    rows.append(('START', {'label': 'forward_live_122', 'source_event': 122, 'state': copy.deepcopy(current)}))
    for tick in range(120):
        before = copy.deepcopy(current); before['elapsed'] += oracle.DT
        working = copy.deepcopy(before); working['tick'] += 1
        clock = working['bot_clock'] - oracle.DT
        turn = clock <= 0
        working['bot_clock'] = .12 if turn else clock
        if turn:
            for aid, actor in list(working['actors'].items()):
                if not actor['alive']: continue
                row = decision('forward_live_122', working, int(aid))
                rows.append(('DECISION', row)); working = copy.deepcopy(row['after'])
        after_objective = copy.deepcopy(working)
        rows.append(('INTERACTION', interaction('forward_live_122', working, after_objective)))
        current = copy.deepcopy(after_objective); current['time_left'] -= oracle.DT
        rows.append(('AUTHORITY', {'label': 'forward_live_122', 'tick': current['tick'], 'dt': oracle.DT, 'before': before, 'after': copy.deepcopy(current)}))
    for name in oracle.CONTROLS:
        current = protected(127)
        actor = current['actors']['6']
        actor['position'] = [0, 0, -20] if name == 'wrong_site' else [-15, 0, 10]
        if name == 'defuse':
            actor['team'] = 1
            current.update(objective='planted', objective_position=[-15, 0, 10], objective_timer=35.0)
        positive = name in ('plant', 'defuse')
        if not positive: current['interactions'] = {'6': .25}
        rows.append(('CONTROL_START', {'name': name, 'state': copy.deepcopy(current)}))
        count = 0
        while True:
            current['tick'] += 1; current['elapsed'] += oracle.DT
            if count % 8 == 0:
                row = decision('control_' + name, current, interact=name != 'wrong_site')
                rows.append(('DECISION', row)); current = copy.deepcopy(row['after'])
            if not positive:
                current['actors']['6']['input']['interact'] = name != 'no_interact'
                current['actors']['6']['input']['move'] = [0, 1] if name == 'moving' else [0, 0]
            before = copy.deepcopy(current)
            if name == 'defuse': current['objective_timer'] -= oracle.DT
            if positive:
                progress = current['interactions'].get('6', 0.0) + oracle.DT
                current['interactions']['6'] = progress
                if progress >= (3 if name == 'plant' else 5):
                    current['interactions'] = {}; current['contributions'] = {'6': 1}
                    current['actors']['6']['credits'] += 300
                    if name == 'plant': current.update(objective='planted', objective_position=[-15, 0, 10], objective_timer=35.0)
                    else:
                        current.update(objective='defused', phase='post', time_left=5)
                        current['defend_score'] += 1
                        for a in current['actors'].values(): a['credits'] = min(9000, a['credits'] + (2700 if a['team'] == 1 else 1900))
            else: current['interactions'] = {}
            rows.append(('INTERACTION', interaction('control_' + name, before, current)))
            count += 1
            if not positive or current['objective'] == ('planted' if name == 'plant' else 'defused'): break
        rows.append(('CONTROL', {'name': name, 'valid': True, 'ticks': count, 'objective': current['objective'], 'contributions': current['contributions'], 'final': copy.deepcopy(current)}))
    rows.append(('RESULT', {'checks': 30, 'failures': [], 'pairs': 3, 'controls': 5, 'decisions': sum(k == 'DECISION' for k, _ in rows), 'interactions': sum(k == 'INTERACTION' for k, _ in rows), 'authority': 120, 'scope': 'diagnostic_only_no_objective_quality_acceptance'}))
    return rows


def log(rows):
    return '\n'.join(oracle.PREFIX + kind + ' ' + json.dumps(value, separators=(',', ':')) for kind, value in rows) + '\n'


class ObjectiveOracleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.valid = synthetic_records()

    def reject(self, rows):
        with self.assertRaises((ValueError, KeyError, TypeError)):
            oracle.verify_records(rows)

    def test_complete_source_bound_synthetic_contract(self):
        self.assertTrue(oracle.verify_records(self.valid)['observable_contract_passed'])

    def mutate(self, kind, predicate, change):
        rows = list(self.valid)
        index = next(i for i, (tag, row) in enumerate(rows) if tag == kind and predicate(row))
        tag, row = rows[index]
        row = copy.deepcopy(row); rows[index] = (tag, row)
        change(row)
        self.reject(rows)

    def test_forward_missing_fields_are_explicit_mutations(self):
        for field in ('dt', 'before', 'after', 'actors_before', 'objective_before', 'progress_after'):
            self.mutate('INTERACTION', lambda r: r['label'] == 'forward_live_122', lambda r, key=field: r.pop(key))
        for field in ('dt', 'before', 'after'):
            self.mutate('AUTHORITY', lambda r: True, lambda r, key=field: r.pop(key))

    def test_freshness_call_cannot_describe_another_actor(self):
        self.mutate('CALL', lambda r: r['case'] == 'live_complete', lambda r: r['output']['decision'].update(actor_id=7))

    def test_direct_perception_requires_an_eligible_target(self):
        self.mutate('CALL', lambda r: r['case'] == 'direct_perception', lambda r: r['output'].update(target_id=10))

    def test_decision_role_must_exist_in_source(self):
        self.mutate('DECISION', lambda r: r['label'] == 'pose_122', lambda r: r['observation']['decision'].update(role='invented_role_not_in_source'))

    def test_target_score_preserves_exact_independent_bonuses(self):
        before = protected(122)
        before['bots']['6'].update(target=0, attacker_id=0, damaged_at=-100)
        candidate = {'id': 1, 'distance': 10.0}
        self.assertEqual(oracle.target_score(before, 6, candidate), 10.0)
        before['bots']['6']['target'] = 1
        self.assertEqual(oracle.target_score(before, 6, candidate), 5.5)
        before['bots']['6'].update(attacker_id=1, damaged_at=before['elapsed'] - .5)
        self.assertEqual(oracle.target_score(before, 6, candidate), 1.5)
        before['bots']['6']['attacker_id'] = 2
        self.assertEqual(oracle.target_score(before, 6, candidate), 5.5)

    def test_target_score_accepts_legitimate_negative_total(self):
        before = protected(122)
        before.update(objective='carried', carrier=6)
        before['bots']['1'].update(target=6, attacker_id=6, damaged_at=before['elapsed'] - .5)
        self.assertEqual(oracle.target_score(before, 1, {'id': 6, 'distance': 1.0}), -11.0)

    def test_recent_attacker_bonus_expires_at_strict_boundary(self):
        before = protected(122)
        before.update(elapsed=1.2, carrier=6)
        before['bots']['6'].update(target=0, attacker_id=1, damaged_at=0.0)
        self.assertEqual(oracle.target_score(before, 6, {'id': 1, 'distance': 10.0}), 10.0)
        before['elapsed'] = math.nextafter(1.2, 0.0)
        self.assertEqual(oracle.target_score(before, 6, {'id': 1, 'distance': 10.0}), 6.0)

    def test_planted_nearest_defender_bonus_uses_device_pose(self):
        before = protected(122)
        before.update(objective='planted', objective_position=[-15, 0, 10])
        before['bots']['6'].update(target=0, attacker_id=0, damaged_at=-100)
        for aid, actor in before['actors'].items():
            if actor['team'] == 1:
                actor['position'] = [100 + int(aid), 0, 100]
        before['actors']['1'].update(team=1, position=[-15, 0, 10])
        self.assertEqual(oracle.target_score(before, 6, {'id': 1, 'distance': 10.0}), 4.0)
        before['actors']['1']['alive'] = False
        self.assertEqual(oracle.target_score(before, 6, {'id': 1, 'distance': 10.0}), 10.0)

    def test_fabricated_eligible_score_cannot_choose_target(self):
        def corrupt(row):
            candidate = next(c for c in row['observation']['candidates'] if c['distance'] < 38)
            candidate.update(reason='eligible', score=-999)
            row['observation']['decision']['target_id'] = candidate['id']
            row['observation'].update(target_distance=candidate['distance'], aligned=False)
        self.mutate('DECISION', lambda r: r['label'] == 'pose_122', corrupt)

    def test_defuser_cannot_forge_destination_or_legal_role(self):
        def move_plan(row):
            row['observation']['plan']['destination'] = [999, 0, 999]
            row['observation']['decision']['destination'] = [999, 0, 999]
        self.mutate('DECISION', lambda r: r['label'] == 'control_defuse', move_plan)
        self.mutate('DECISION', lambda r: r['label'] == 'control_defuse', lambda r: r['observation']['decision'].update(role='anchor'))

    def test_nearest_defuser_keeps_device_plan_outside_interaction_range(self):
        before = protected(127)
        before.update(objective='planted', objective_position=[-15, 0, 10], objective_timer=35.0)
        before['actors']['6'].update(team=1, position=[-15, 0, 6])
        row = decision('control_defuse', before)
        oracle.decision(row)
        self.assertFalse(row['observation']['decision']['interact'])
        self.assertEqual(row['observation']['plan']['destination'], [-15, 0, 10])

    def test_action_handoff_accepts_capped_kill_award_and_carrier_drop(self):
        before = protected(122)
        victim = str(before['carrier'])
        killer = next(aid for aid, actor in before['actors'].items() if actor['alive'] and actor['team'] != before['actors'][victim]['team'])
        before['actors'][killer]['credits'] = 8900
        after = copy.deepcopy(before)
        after['actors'][killer]['kills'] += 1
        after['actors'][killer]['credits'] = 9000
        after['actors'][victim].update(alive=False, health=0, position=[1, 0, 1])
        after['actors'][victim]['deaths'] += 1
        after.update(objective='dropped', carrier=0, objective_position=[1, 0, 1])
        oracle.action_handoff(before, after)

    def test_action_handoff_accepts_uncredited_world_elimination(self):
        before = protected(122)
        victim = next(aid for aid, actor in before['actors'].items() if actor['alive'] and int(aid) != before['carrier'])
        after = copy.deepcopy(before)
        after['actors'][victim].update(alive=False, health=0)
        after['actors'][victim]['deaths'] += 1
        oracle.action_handoff(before, after)

    def test_action_handoff_rejects_unearned_reward_and_team_change(self):
        before = protected(122)
        for field, value in (('credits', before['actors']['6']['credits'] + 100), ('team', 1 - before['actors']['6']['team']), ('kills', before['actors']['6']['kills'] + 1)):
            with self.subTest(field=field):
                after = copy.deepcopy(before)
                after['actors']['6'][field] = value
                with self.assertRaises(ValueError):
                    oracle.action_handoff(before, after)

    def test_action_handoff_rejects_preconsumer_objective_and_progress(self):
        before = protected(122)
        after = copy.deepcopy(before)
        after['objective'] = 'planted'
        with self.assertRaisesRegex(ValueError, 'invented objective transition'):
            oracle.action_handoff(before, after)
        after = copy.deepcopy(before)
        after['interactions']['6'] = 2.9
        with self.assertRaisesRegex(ValueError, 'protected match/objective state'):
            oracle.action_handoff(before, after)

    def test_complete_trace_requires_device_drop_when_carrier_dies(self):
        rows = copy.deepcopy(self.valid)
        row = [r for k, r in rows if k == 'INTERACTION' and r['label'] == 'forward_live_122'][-1]
        authority = [r for k, r in rows if k == 'AUTHORITY' and r['label'] == 'forward_live_122'][-1]
        victim = str(row['before']['carrier'])
        for value in (row['before'], row['after'], authority['after']):
            self.assertEqual(value['objective'], 'carried')
            self.assertTrue(value['actors'][victim]['alive'])
            value['actors'][victim].update(alive=False, health=0)
            value['actors'][victim]['deaths'] += 1
        row.update(interaction(row['label'], row['before'], row['after']))
        with self.assertRaisesRegex(ValueError, 'required carrier drop'):
            oracle.verify_records(rows)

    def test_isolated_control_rejects_locally_consistent_other_actor_teleport(self):
        rows = copy.deepcopy(self.valid)
        row = [r for k, r in rows if k == 'INTERACTION' and r['label'] == 'control_plant'][-1]
        summary = next(r for k, r in rows if k == 'CONTROL' and r['name'] == 'plant')
        for value in (row['before'], row['after'], summary['final']):
            value['actors']['1']['position'] = [999, 999, 999]
        row.update(interaction(row['label'], row['before'], row['after']))
        self.reject(rows)

    def test_isolated_control_rejects_match_rng_drift_without_thinking(self):
        rows = copy.deepcopy(self.valid)
        row = [r for k, r in rows if k == 'INTERACTION' and r['label'] == 'control_plant'][-1]
        self.assertFalse(any(k == 'DECISION' and r['label'] == row['label'] and r['tick'] == row['tick'] for k, r in rows))
        summary = next(r for k, r in rows if k == 'CONTROL' and r['name'] == 'plant')
        for value in (row['before'], row['after'], summary['final']):
            value['rng'] = '777'
        self.reject(rows)

    def test_complete_commands_and_scalar_boundaries(self):
        for field in oracle.COMMAND:
            self.mutate('DECISION', lambda r: True, lambda r, key=field: r['observation']['decision']['command'].pop(key))
        for field, value in [('protocol', 6.0), ('time_scale', True), ('physics_ticks_per_second', 60.0), ('profiles', {'normal': {'vision_range': -1}})]:
            self.mutate('HEADER', lambda r: True, lambda r, key=field, v=value: r.update({key: v}))

    def test_freshness_branch_and_gate_boundaries(self):
        for case in oracle.contract()['freshness_cases']:
            self.mutate('CALL', lambda r, c=case: r['case'] == c, lambda r: r['output'].update(decision={'stale': True}))
        self.mutate('CALL', lambda r: r['case'] == 'branch_change', lambda r: r['output'].update(target_distance=9))
        self.mutate('CALL', lambda r: r['case'] == 'live_to_dead', lambda r: r['output'].update(enabled=1))

    def test_source_pose_and_decision_context_boundaries(self):
        for change in [lambda r: r.update(tick=-50), lambda r: r.update(position=[900, 900, 900]), lambda r: r['observation']['plan'].update(destination=[8, 8, 8]), lambda r: r['before']['actors']['6'].update(ammo=31), lambda r: r.update(actor_id=True)]:
            self.mutate('DECISION', lambda r: r['label'] == 'forward_live_122', change)
        self.mutate('START', lambda r: True, lambda r: r['state']['actors']['6'].update(position=[0, 0, 0]))
        self.mutate('DECISION', lambda r: True, lambda r: r['observation'].update(rng_before=str(2**65)))

    def test_continuous_progress_fixed_dt_and_terminal_outcomes(self):
        changes = [lambda r: r.update(dt=-1.0), lambda r: r.update(dt=1.5), lambda r: r['before']['interactions'].update({'6': 1.5}), lambda r: r['after']['interactions'].update({'6': -1}), lambda r: r.update(objective_after='defused'), lambda r: r['after']['actors']['6'].update(credits=9000), lambda r: r['after'].update(phase='buy')]
        for change in changes:
            self.mutate('INTERACTION', lambda r: r['label'] == 'control_plant', change)
        self.mutate('CONTROL', lambda r: r['name'] == 'plant', lambda r: r.update(objective='defused'))
        rows = [row for row in self.valid if not (row[0] == 'DECISION' and row[1]['label'] == 'control_plant')]
        self.reject(rows)

    def test_pair_protection_includes_action_movement_and_objective_state(self):
        for field, value in [('shot_index', 1), ('jump_previous', True), ('head_height', 1.13), ('floor_contact', True)]:
            self.mutate('PAIR', lambda r: True, lambda r, k=field, v=value: r['after_on']['actors']['6'].update({k: v}))
        for field, value in [('objective_timer', 1), ('objective_position', [1, 2, 3]), ('contributions', {'6': 1}), ('damage_history', {'6': {}})]:
            self.mutate('PAIR', lambda r: True, lambda r, k=field, v=value: r['after_on'].update({k: v}))
        self.mutate('PAIR', lambda r: True, lambda r: r['before_on'].update(bots={}))

    def test_truncation_duplicates_unknown_and_strict_warnings(self):
        for rows in (self.valid[:-1], self.valid[1:], self.valid + [self.valid[-1]]): self.reject(rows)
        for warning in ('WARNING: leak', 'SCRIPT ERROR: bad type', 'ObjectDB instances leaked', 'Orphan StringName: Master'):
            with self.assertRaises(ValueError): oracle.records(warning + '\n')
        with self.assertRaises(ValueError): oracle.records('BOT_OBJECTIVE_HEADER {"x":1,"x":2}\n')

    def test_full_source_and_dependency_inventory(self):
        self.assertTrue(oracle.source_audit(ROOT)['source_erasure_passed'])

    def test_inventory_rejects_probe_utility_hidden_marker_and_resource_changes(self):
        files = json.loads((ROOT / oracle.ACQUISITION_INVENTORY).read_text())['files']
        extras = [oracle.REPORT + '/benchmark-identity.json', oracle.REPORT + '/original-timeout-slice.jsonl', oracle.ACQUISITION_INVENTORY, oracle.R2 + '/source-reference/original-0527715-bot_ai.gd.txt']
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for path in list(files) + extras:
                (root / path).parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(ROOT / path, root / path)
            for path in ('game/tests/bot_objective_observation_probe.gd', 'game/scripts/gameplay/utility.gd', 'game/project.godot', 'game/scripts/gameplay/bot_ai.gd'):
                raw = (root / path).read_bytes()
                if path.endswith('bot_ai.gd'):
                    changed = raw.replace(b'# OBJECTIVE_OBSERVATION_BEGIN\n', b'# OBJECTIVE_OBSERVATION_BEGIN\n\tmatch_node._rng.randf() # hidden inside erasure marker\n', 1)
                elif path.endswith('bot_objective_observation_probe.gd'):
                    changed = raw.replace(b'super._objective_tick(delta)', b'pass # removed authority consumer')
                else: changed = raw + b'\n# mutation control\n'
                (root / path).write_bytes(changed)
                with self.assertRaises(ValueError): oracle.source_audit(root)
                (root / path).write_bytes(raw)


if __name__ == '__main__': unittest.main()
