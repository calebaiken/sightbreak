#!/usr/bin/env python3
"""Synthetic oracle falsifiers only; these are not engine or gameplay evidence."""
from copy import deepcopy
import math
import unittest

from witness_oracle import audit, NAMES


HEADER = {'dt': .12, 'deploy_seconds': .3, 'weapon_definitions': {
    'smg': {'reload': 1.85, 'magazine': 30}, 'rifle': {'reload': 2.25, 'magazine': 30},
    'marksman': {'reload': 2.8, 'magazine': 8}, 'sidearm': {'reload': 1.45, 'magazine': 15}}}


def actor(target=False):
    value = dict(actor_id=1 if target else 6, team=0 if target else 1, weapon='rifle', ammo=0, reserve=0,
                 reload=0., deploy=0., cooldowns={}, inventory=['rifle'], ammo_store={}, health=100., alive=True,
                 credits=800, kills=0, assists=0, deaths=0, grenades=0, smokes=0, recoil=[0., 0.],
                 position=[1. if target else -1., 0., -20.], velocity=[0., 0., 0.], yaw=0., pitch=0.,
                 fire_previous=False, floor_contact=False, crouching=False, actual_action_spread=.047)
    if target:
        value['input_state'] = {}
    return value


def controls():
    """Explicit legal control timelines for testing the checker, never a native substitute."""
    rows = []
    for name in NAMES:
        weapon = name.removeprefix('reload_') if name != 'kill_rifle' else 'rifle'
        definition = HEADER['weapon_definitions'][weapon]
        budget = 8 if name == 'kill_rifle' else math.ceil(definition['reload'] / .12) + 3
        if name == 'reload_sidearm':
            budget = 20
        shooter, target = actor(), actor(True)
        if name == 'kill_rifle':
            shooter['ammo'], target['health'] = 1, 10.
        elif name != 'reload_sidearm':
            shooter['weapon'], shooter['inventory'], shooter['reserve'] = weapon, [weapon], definition['magazine']
        else:
            shooter['inventory'], shooter['ammo_store'] = ['sidearm', 'rifle'], {'sidearm': [0, 15]}
        for step in range(budget):
            before, target_before = deepcopy(shooter), deepcopy(target)
            fire = name == 'kill_rifle' and step == 2
            reload_input = name != 'kill_rifle' and not (name == 'reload_sidearm' and step == 0) and shooter['ammo'] == 0
            shot_list, damages, eliminations = [], [], []
            shooter['deploy'] = max(shooter['deploy'] - .12, 0)
            if name == 'reload_sidearm' and step == 0:
                shooter.update(weapon='sidearm', reserve=15, deploy=.3)
                shooter['ammo_store']['rifle'] = [0, 0]
            elif reload_input and shooter['reload'] == 0:
                shooter['reload'] = definition['reload']
            elif shooter['reload'] > 0:
                shooter['reload'] = max(shooter['reload'] - .12, 0)
                if shooter['reload'] == 0:
                    shooter['ammo'], shooter['reserve'] = definition['magazine'], 0
            if fire:
                shooter.update(ammo=0, kills=1, credits=1100)
                target.update(health=0., alive=False, deaths=1)
                shot_list = [{'weapon': 'rifle'}]
                damages = [{'victim': 1, 'attacker': 6, 'amount': 10.}]
                eliminations = [{'victim': 1, 'killer': 6}]
            shooter['fire_previous'] = fire
            objective = dict(phase='live', round=2, attack_score=0, defend_score=0, time_left=100., state='carried',
                             timer=0., progress=0., position=[-15., 0., 10.], carrier=0, contributions={}, interactions={}, elapsed=20. + step * .12, tick=0)
            rows.append({'scenario': {'control': name}, 'step': step, 'elapsed': 20. + step * .12,
                         'before': before, 'after_decision': deepcopy(before), 'after_action': deepcopy(shooter),
                         'enemy_before': target_before, 'enemy_after_decision': deepcopy(target_before), 'enemy_after_action': deepcopy(target),
                         'objective_before': objective, 'objective_after_decision': deepcopy(objective),
                         'lane': {'in_bounds': True, 'world_clear': True, 'pose_settle': {'barriers': 2, 'before_frame': 1, 'after_frame': 3}, 'stock_trace': {'actor_id': 1 if target_before['alive'] else 0}},
                         'command': {'fire': fire, 'reload': reload_input}, 'actual_shots': shot_list, 'shot_delta': len(shot_list),
                         'damage_events': damages, 'elimination_events': eliminations,
                         'target_damage_delta': target_before['health'] - target['health']})
    return rows


class WitnessFalsifiers(unittest.TestCase):
    def test_registered_synthetic_controls_are_accepted(self):
        result = audit(HEADER, controls())
        self.assertEqual(result['kill_rifle']['shots'], 1)
        self.assertEqual(sum(len(row['reload_completions']) for row in result.values()), 4)

    def test_bad_evidence_is_rejected(self):
        def missing_control(rows):
            rows[:] = [row for row in rows if row['scenario']['control'] != 'reload_marksman']
        def no_fire(rows):
            for row in rows:
                if row['scenario']['control'] == 'kill_rifle':
                    row['actual_shots'], row['shot_delta'] = [], 0
        def no_damage(rows):
            rows[2]['damage_events'] = []
        def no_reward(rows):
            for row in rows:
                if row['scenario']['control'] == 'kill_rifle' and row['step'] >= 2:
                    row['after_action']['credits'] = 800
                    if row['step'] > 2:
                        row['before']['credits'] = row['after_decision']['credits'] = 800
        def decision_damage(rows):
            rows[2]['enemy_after_decision']['health'] = 5.
        def decision_objective(rows):
            rows[0]['objective_after_decision']['progress'] = .5
        def missing_snapshot(rows):
            del rows[0]['enemy_after_decision']['ammo_store']
        def blocked(rows):
            rows[0]['lane']['world_clear'] = False
        def forged_bounds(rows):
            rows[0]['before']['position'][0] = 30.
            rows[0]['after_decision']['position'][0] = 30.
        def unsettled(rows):
            rows[0]['lane']['pose_settle']['after_frame'] = 1
        def missing_reload(rows):
            for row in rows:
                if row['scenario']['control'] == 'reload_smg':
                    row['before']['reload'] = row['after_decision']['reload'] = row['after_action']['reload'] = 0.
        def illegal_transfer(rows):
            for row in rows:
                if row['scenario']['control'] == 'reload_rifle' and row['after_action']['ammo'] == 30:
                    row['after_action']['reserve'] = 30
                    break
        def no_completion(rows):
            for row in rows:
                if row['scenario']['control'] == 'reload_sidearm' and row['step'] >= 14:
                    row['after_action']['ammo'], row['after_action']['reserve'] = 0, 15
                    if row['step'] > 14:
                        row['before']['ammo'] = row['after_decision']['ammo'] = 0
                        row['before']['reserve'] = row['after_decision']['reserve'] = 15
        def boolean_alias(rows):
            rows[0]['lane']['world_clear'] = 1
        for mutate in (missing_control, no_fire, no_damage, no_reward, decision_damage, decision_objective,
                       missing_snapshot, blocked, forged_bounds, unsettled, missing_reload, illegal_transfer,
                       no_completion, boolean_alias):
            with self.subTest(falsifier=mutate.__name__):
                rows = controls()
                mutate(rows)
                with self.assertRaises(ValueError):
                    audit(HEADER, rows)


if __name__ == '__main__':
    unittest.main()
