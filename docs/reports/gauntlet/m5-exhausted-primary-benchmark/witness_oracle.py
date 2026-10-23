#!/usr/bin/env python3
"""Pure checker for required positive controls; never starts the game engine."""
import json
import math
from pathlib import Path
import sys

NAMES = ('kill_rifle', 'reload_smg', 'reload_rifle', 'reload_marksman', 'reload_sidearm')
PROTECTED = set('actor_id team weapon ammo reserve reload deploy cooldowns inventory ammo_store health alive credits kills assists deaths grenades smokes recoil position velocity yaw pitch fire_previous floor_contact crouching actual_action_spread'.split())
OBJECTIVE = set('phase round attack_score defend_score time_left state timer progress position carrier contributions interactions elapsed tick'.split())


def require(condition, message):
    if not condition:
        raise ValueError(message)


def number(value):
    require(type(value) in (int, float) and math.isfinite(value), 'finite number required')
    return value


def near(a, b):
    return abs(number(a) - number(b)) <= 1e-5


def boolean(value):
    require(type(value) is bool, 'strict Boolean required')
    return value


def audit(header, rows):
    dt = number(header['dt'])
    require(dt > 0, 'positive timestep required')
    weapons = header['weapon_definitions']
    budgets = {'kill_rifle': 8}
    for weapon in ('smg', 'rifle', 'marksman'):
        budgets['reload_' + weapon] = math.ceil(number(weapons[weapon]['reload']) / dt) + 3
    budgets['reload_sidearm'] = math.ceil(number(header['deploy_seconds']) / dt) + math.ceil(number(weapons['sidearm']['reload']) / dt) + 4
    grouped = {name: [] for name in NAMES}
    for row in rows:
        name = row['scenario']['control']
        require(name in grouped, 'unexpected positive control')
        grouped[name].append(row)
    result = {}
    for name, control in grouped.items():
        require(len(control) == budgets[name], name + ': missing/extra steps')
        require([row['step'] for row in control] == list(range(budgets[name])), name + ': step identity')
        starts, completions = [], []
        shots = damage = eliminations = draws = 0
        damage_amount = 0
        for step, row in enumerate(control):
            before, decision, after = row['before'], row['after_decision'], row['after_action']
            target_before, target_decision, target_after = row['enemy_before'], row['enemy_after_decision'], row['enemy_after_action']
            require(all(PROTECTED <= actor.keys() for actor in (before, decision, after)), name + ': incomplete shooter snapshot')
            require(all(PROTECTED | {'input_state'} <= actor.keys() for actor in (target_before, target_decision, target_after)), name + ': incomplete target snapshot')
            require(OBJECTIVE <= row['objective_before'].keys() and OBJECTIVE <= row['objective_after_decision'].keys(), name + ': incomplete objective snapshot')
            require(before == decision and target_before == target_decision, name + ': decision mutated an actor')
            require(row['objective_before'] == row['objective_after_decision'], name + ': decision mutated objective')
            if step:
                require(before == control[step - 1]['after_action'], name + ': shooter reset between steps')
                require(target_before == control[step - 1]['enemy_after_action'], name + ': target reset between steps')
                require(near(row['elapsed'] - control[step - 1]['elapsed'], dt), name + ': elapsed step')
            lane = row['lane']
            require(boolean(lane['in_bounds']) and boolean(lane['world_clear']), name + ': blocked/out-of-bounds lane')
            require(lane['pose_settle']['barriers'] == 2 and lane['pose_settle']['after_frame'] > lane['pose_settle']['before_frame'], name + ': unsettled query')
            for actor in (before, target_before):
                require(all(abs(number(actor['position'][axis])) + .3 < 23.5 for axis in (0, 2)), name + ': actual position outside yard')
            if boolean(target_before['alive']):
                require(lane['stock_trace']['actor_id'] == 1, name + ': stock trace misses live target')
            require(type(row['shot_delta']) is int and row['shot_delta'] == len(row['actual_shots']), name + ': actual shot count')
            if row['shot_delta']:
                require(boolean(row['command']['fire']) and all(shot['weapon'] == decision['weapon'] for shot in row['actual_shots']), name + ': shot without real fire command')
            require(near(row['target_damage_delta'], target_decision['health'] - target_after['health']), name + ': target damage phase')
            require(near(sum(number(event['amount']) for event in row['damage_events']), row['target_damage_delta']), name + ': damage events disagree')
            require(all(event['victim'] == 1 and event['attacker'] == 6 and number(event['amount']) > 0 for event in row['damage_events']), name + ': wrong damage witness')
            require(all(event['victim'] == 1 and event['killer'] == 6 for event in row['elimination_events']), name + ': wrong elimination witness')
            shots += row['shot_delta']
            damage += len(row['damage_events'])
            damage_amount += row['target_damage_delta']
            eliminations += len(row['elimination_events'])
            switched = before['weapon'] != after['weapon']
            draws += int(switched)
            if switched:
                require(name == 'reload_sidearm' and step == 0 and after['weapon'] == 'sidearm' and near(after['deploy'], header['deploy_seconds']), name + ': wrong draw')
            else:
                reload_seconds = weapons[after['weapon']]['reload']
                if before['reload'] == 0 and after['reload'] > 0:
                    starts.append(step)
                    require(boolean(row['command']['reload']), name + ': reload without registered input')
                    require(near(after['reload'], reload_seconds) and before['ammo'] == after['ammo'] and before['reserve'] == after['reserve'], name + ': reload start')
                elif before['reload'] > 0:
                    require(near(after['reload'], max(before['reload'] - dt, 0)), name + ': reload timer drift')
                    if after['reload'] == 0:
                        completions.append(step)
                        amount = min(weapons[after['weapon']]['magazine'] - before['ammo'], before['reserve'])
                        require(amount > 0 and after['ammo'] == before['ammo'] + amount - row['shot_delta'] and after['reserve'] == before['reserve'] - amount, name + ': illegal completion transfer')
                        require(starts and reload_seconds - 1e-5 <= (step - starts[-1]) * dt <= reload_seconds + dt + 1e-5, name + ': completion timing')
                    else:
                        require(before['ammo'] == after['ammo'] and before['reserve'] == after['reserve'], name + ': premature transfer')
        initial, final = control[0]['before'], control[-1]['after_action']
        initial_target, final_target = control[0]['enemy_before'], control[-1]['enemy_after_action']
        if name == 'kill_rifle':
            require(near(initial_target['health'], 10) and shots == 1 and damage >= 1 and near(damage_amount, 10), name + ': no real damage/shot')
            require(eliminations == 1 and not boolean(final_target['alive']) and final_target['deaths'] == initial_target['deaths'] + 1, name + ': no real death')
            require(final['kills'] == initial['kills'] + 1 and final['credits'] == initial['credits'] + 300, name + ': ordinary kill/reward absent')
            require(draws == 0 and starts == [] and completions == [], name + ': changed firing setup')
        else:
            weapon = name.removeprefix('reload_')
            require(len(starts) == len(completions) == 1, name + ': accepted/completed reload absent')
            require(final['weapon'] == weapon and final['ammo'] == weapons[weapon]['magazine'] and final['reserve'] == 0 and near(final['reload'], 0), name + ': wrong final magazine')
            require(shots == damage == eliminations == 0 and initial_target == final_target, name + ': reload target changed')
            require(draws == int(name == 'reload_sidearm'), name + ': missing/unexpected draw')
        result[name] = {'steps': len(control), 'shots': shots, 'damage_events': damage, 'damage': damage_amount,
                        'eliminations': eliminations, 'draws': draws, 'reload_starts': starts, 'reload_completions': completions}
    return result


def main():
    header, rows = None, []
    for line in Path(sys.argv[1]).read_text().splitlines():
        if line.startswith('BOT_EXHAUSTED_HEADER '):
            require(header is None, 'duplicate header')
            header = json.loads(line.split(' ', 1)[1])
        elif line.startswith('BOT_EXHAUSTED_CONTROL_STEP '):
            rows.append(json.loads(line.split(' ', 1)[1]))
    require(header is not None, 'header missing')
    print(json.dumps(audit(header, rows), indent=2))


if __name__ == '__main__':
    main()
