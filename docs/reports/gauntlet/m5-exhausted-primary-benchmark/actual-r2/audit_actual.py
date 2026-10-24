#!/usr/bin/env python3
"""Builder's pure resource/authority recomputation; not independent acceptance.

Usage: python3 audit_actual.py <raw stdout or stdout.gz> <frozen source root>
No engine, mutation of game source, network, or policy preference.
"""
import copy
import gzip
import hashlib
import json
import math
from pathlib import Path
import re
import sys
from collections import Counter, defaultdict

raw, source = Path(sys.argv[1]), Path(sys.argv[2])
data = gzip.decompress(raw.read_bytes()) if raw.suffix == '.gz' else raw.read_bytes()
parsed = defaultdict(list)
for line in data.decode().splitlines():
    if line.startswith('BOT_EXHAUSTED_'):
        tag, value = line.split(' ', 1)
        if tag != 'BOT_EXHAUSTED_FAILURE':
            parsed[tag.removeprefix('BOT_EXHAUSTED_')].append(json.loads(value))
checks, failures = 0, []


def check(value, message):
    global checks
    checks += 1
    if not value:
        failures.append(message)


def near(a, b, tolerance=1e-5):
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return math.isfinite(a) and math.isfinite(b) and abs(a-b) < tolerance
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(near(a[k], b[k], tolerance) for k in a)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(near(x, y, tolerance) for x, y in zip(a, b))
    return a == b


def constant(path, name):
    text = path.read_text().split('const ' + name + ' := ', 1)[1]
    text = text[:text.index('\n}\n') + 2]
    text = re.sub(r'Color\("[^"\n]+"\)', 'null', text)
    return json.loads(text)


check(len(parsed['HEADER']) == len(parsed['RESULT']) == 1, 'one header and result')
h, result = parsed['HEADER'][0], parsed['RESULT'][0]
weapons = constant(source / 'game/scripts/gameplay/weapons.gd', 'DATA')
profiles = constant(source / 'game/scripts/gameplay/bot_ai.gd', 'PROFILES')
check(profiles == h['profiles'], 'header profiles match frozen source')
for weapon, definition in weapons.items():
    check({k:v for k,v in definition.items() if k != 'color'} ==
          {k:v for k,v in h['weapon_definitions'][weapon].items() if k != 'color'},
          'header gameplay definition ' + weapon)
check(h['engine']['string'] == '4.7.2-stable (official)', 'pinned engine header')
check(h['dt'] == .12 and h['seed'] == 52039 and h['deploy_seconds'] == .3, 'fixture constants')
dt = h['dt']
expected_counts = {'CASE':567, 'STEP':576, 'SEQUENCE':72, 'CONTROL_STEP':96, 'CONTROL':5}
for kind, count in expected_counts.items():
    check(len(parsed[kind]) == count, kind + ' row count')
check(result['matrix_cases'] == 567 and result['sequence_steps'] == 576 and
      result['sequences'] == 72 and result['control_steps'] == 96 and
      result['failures'] == [] and result['checks'] == 18499, 'terminal reported result')

targets = ('near', 'fallback_boundary', 'far', 'outside_sidearm', 'outside_vision', 'no_target')
expected_matrix = set()
for difficulty in profiles:
    for primary in ('smg', 'rifle', 'marksman'):
        for target in targets:
            for active in ('exhausted', 'reloadable'):
                for sidearm in ('loaded', 'dry', 'unknown'):
                    expected_matrix.add(('core', difficulty, primary, active, sidearm, target, 'none'))
            expected_matrix.add(('loaded_primary', difficulty, primary, 'loaded', 'loaded', target, 'none'))
        for target in ('near', 'far', 'no_target'):
            expected_matrix.add(('reserve_only_sidearm', difficulty, primary, 'exhausted', 'reserve_only', target, 'none'))
            expected_matrix.add(('unowned_sidearm', difficulty, primary, 'exhausted', 'unowned', target, 'none'))
            for active in ('exhausted', 'reloadable', 'loaded'):
                expected_matrix.add(('stale_active_cache', difficulty, primary, active, 'loaded', target, 'none'))
            for objective in ('carrier', 'defuser'):
                expected_matrix.add(('objective_guard', difficulty, primary, 'exhausted', 'loaded', target, objective))
actual_matrix = [tuple(r['label'].split('/')) for r in parsed['CASE']]
check(len(set(actual_matrix)) == 567 and set(actual_matrix) == expected_matrix, 'exact registered matrix identities')


def resources(snap):
    out = {}
    for weapon, definition in weapons.items():
        row = {'owned': weapon in snap['inventory'], 'source':'unowned', 'clip':None, 'reserve':None,
               'equip_default':[definition['magazine'], definition['reserve']]}
        if row['owned']:
            if weapon == snap['weapon']:
                row.update(source='active_fields', clip=snap['ammo'], reserve=snap['reserve'])
            elif weapon in snap['ammo_store']:
                row.update(source='holstered_store', clip=snap['ammo_store'][weapon][0], reserve=snap['ammo_store'][weapon][1])
            else:
                row['source'] = 'unknown'
        out[weapon] = row
    return out


def projected(row):
    return sum(sum(r['equip_default']) if r['source'] == 'unknown' else r['clip'] + r['reserve']
               for r in row.values() if r['owned'])


def simulate_resources(before, command):
    # Stock order: timers/completion, equip, reload request, fire, cooldown clamp.
    s = copy.deepcopy(before)
    s['deploy'] = max(0, s['deploy']-dt)
    s['cooldowns'] = {w:t-dt for w,t in s['cooldowns'].items()}
    if s['reload'] > 0:
        s['reload'] = max(0, s['reload']-dt)
        if s['reload'] == 0:
            amount = min(weapons[s['weapon']]['magazine']-s['ammo'], s['reserve'])
            s['ammo'] += amount
            s['reserve'] -= amount
    request = command['weapon']
    if request and request != s['weapon'] and request in s['inventory']:
        s['ammo_store'][s['weapon']] = [s['ammo'], s['reserve']]
        s['weapon'] = request
        s['ammo'], s['reserve'] = s['ammo_store'].get(request, [weapons[request]['magazine'], weapons[request]['reserve']])
        s['reload'] = 0
        s['deploy'] = h['deploy_seconds']

    def reload_if_legal():
        if s['reload'] <= 0 and s['ammo'] < weapons[s['weapon']]['magazine'] and s['reserve'] > 0:
            s['reload'] = weapons[s['weapon']]['reload']
    if command['reload']:
        reload_if_legal()
    fired = 0
    firing = command['fire']
    if firing and (weapons[s['weapon']]['automatic'] or not before['fire_previous']) and s['deploy'] <= 1e-6 and s['cooldowns'].get(s['weapon'], 0) <= 1e-6 and s['reload'] <= 0:
        if s['ammo'] > 0:
            fired = 1
            s['ammo'] -= 1
            cool = s['cooldowns'].get(s['weapon'], 0)
            carry = cool if before['fire_previous'] and cool <= 0 and cool > -(1/60)*.999 else 0
            s['cooldowns'][s['weapon']] = carry + weapons[s['weapon']]['interval']
        else:
            reload_if_legal()
    for weapon in s['cooldowns']:
        if not fired or weapon != s['weapon']:
            s['cooldowns'][weapon] = max(0, s['cooldowns'][weapon])
    s['fire_previous'] = firing
    return s, fired


rows = parsed['CASE'] + parsed['STEP'] + parsed['CONTROL_STEP']
for r in rows:
    key = r['label'] + '/' + str(r['step'])
    b, d, a, command = r['before'], r['after_decision'], r['after_action'], r['command']
    eb, ed, ea = r['enemy_before'], r['enemy_after_decision'], r['enemy_after_action']
    check(b == d and eb == ed and r['objective_before'] == r['objective_after_decision'], key + ' planning fences')
    check(r['objective_before'] == r['objective_after_action'], key + ' no match authority tick')
    rb, ra = resources(b), resources(a)
    check(rb == r['resources_before'] and ra == r['resources_after'], key + ' independent active/holstered resource map')
    predicted, fired = simulate_resources(d, command)
    for field in ('weapon', 'ammo', 'reserve', 'ammo_store', 'reload', 'deploy', 'cooldowns', 'fire_previous'):
        check(near(predicted[field], a[field]), key + ' stock action ' + field)
    check(fired == r['shot_delta'] == len(r['actual_shots']), key + ' shot consumption')
    for weapon in weapons:
        before_total = (sum(rb[weapon]['equip_default']) if rb[weapon]['source'] == 'unknown' else
                        rb[weapon]['clip'] + rb[weapon]['reserve']) if rb[weapon]['owned'] else 0
        after_total = (sum(ra[weapon]['equip_default']) if ra[weapon]['source'] == 'unknown' else
                       ra[weapon]['clip'] + ra[weapon]['reserve']) if ra[weapon]['owned'] else 0
        check(before_total == after_total + sum(s['weapon'] == weapon for s in r['actual_shots']), key + ' per-weapon conservation ' + weapon)
    check(projected(rb) == r['equip_semantics_total_before'] and projected(ra) == r['equip_semantics_total_after'], key + ' independent total projection')
    sidearm = rb['sidearm']
    known = sidearm['owned'] and sidearm['source'] not in ('unknown','unowned') and sidearm['clip'] + sidearm['reserve'] > 0
    check(known == r['known_sidearm_resources'], key + ' known availability')
    check(all(a[k] == d[k] for k in ('health','alive','inventory','position','velocity','yaw','pitch','grenades','smokes','assists','deaths','team')), key + ' shooter stable authority')
    damage = sum(e['amount'] for e in r['damage_events'])
    killed = ed['alive'] and not ea['alive']
    check(near(ed['health']-damage, ea['health']) and near(damage,r['target_damage_delta']) and ea['alive'] == (ea['health'] > 0), key + ' damage health/alive transition')
    check(len(r['elimination_events']) == int(killed) and ea['deaths'] == ed['deaths'] + int(killed), key + ' target death transition')
    check(a['kills'] == d['kills'] + int(killed) and a['credits'] == min(9000,d['credits']+300*int(killed)) and r['reward_delta'] == a['credits']-d['credits'], key + ' real kill/reward transition')
    check(all(ea[k] == ed[k] for k in ed if k not in ('health','alive','deaths')), key + ' other full target state stable')
    for shot in r['actual_shots']:
        check(shot['weapon'] == a['weapon'] and shot['ammo_after_shot'] == a['ammo'] and shot['reserve'] == a['reserve'], key + ' shot event resource fields')
    for e in r['damage_events']:
        check(e['victim'] == 1 and e['attacker'] == 6 and e['amount'] > 0 and near(e['victim_state']['health'], ea['health']), key + ' damage event identity/snapshot')
    for e in r['elimination_events']:
        check(e['victim'] == 1 and e['killer'] == 6 and e['victim_state'] == ea and e['shooter_state']['kills'] == a['kills'] and e['shooter_state']['credits'] == a['credits'], key + ' elimination event snapshots')
    events = sorted(r['damage_events'] + r['elimination_events'] + r['actual_shots'], key=lambda e:e['serial'])
    check(len({e['serial'] for e in events}) == len(events), key + ' unique event serials')
    if killed and r['actual_shots']:
        check(r['damage_events'][0]['serial'] < r['elimination_events'][0]['serial'] < r['actual_shots'][0]['serial'], key + ' damage/death/shot signal order')
    lane = r['lane']
    check(lane['pose_settle']['barriers'] == 2 and lane['pose_settle']['after_frame'] > lane['pose_settle']['before_frame'] and lane['observation_frame'] >= lane['pose_settle']['after_frame'], key + ' settled world query')
    distance = r['scenario']['target']['distance']
    if r['scenario']['objective'] != 'none':
        pose = [-15,0,10]
        target = [-15+distance,0,10]
    elif distance > 45.5:
        c = distance*.5/math.sqrt(2)
        pose, target = [-c,0,-c], [c,0,c]
    else:
        pose, target = [-distance*.5,0,-20], [distance*.5,0,-20]
    check(near(b['position'], pose) and near(eb['position'], target) and near(lane['shooter'],pose) and near(lane['target'],target), key + ' exact registered poses')
    check(lane['in_bounds'] and all(abs(p[axis])+.31 < 23.5 for p in (pose,target) for axis in (0,2)), key + ' actual 0.31m footprint bounds')
    origin = [pose[0],1.62,pose[2]]
    direction = [-math.sin(b['yaw'])*math.cos(b['pitch']), math.sin(b['pitch']), -math.cos(b['yaw'])*math.cos(b['pitch'])]
    endpoint = [x+y*(distance+.5) for x,y in zip(origin,direction)]
    check(lane['world_mask'] == 1 and near(lane['ray_from'],origin) and near(lane['ray_to'],endpoint), key + ' nominal world ray endpoints')
    if r['scenario']['objective'] == 'none' and distance <= 45.5:
        check(lane['world_clear'] and lane['world_hit_position'] is None and lane['world_hit_path'] == '', key + ' unobstructed ordinary world ray')
        if eb['alive'] and distance <= weapons[b['weapon']]['range']:
            check(lane['stock_trace']['actor_id'] == 1 and lane['stock_trace']['hit'], key + ' stock trace reaches target')
    expected_target = int(r['visibility_injected'] and eb['alive'] and distance <= profiles[r['scenario']['difficulty']]['vision_range'])
    check(r['decision_bot_state']['target'] == expected_target, key + ' registered vision acquisition')
    check(command['interact'] == (r['scenario']['objective'] != 'none'), key + ' objective interaction guard')

sequence_summaries = []
for summary in parsed['SEQUENCE']:
    group = [r for r in parsed['STEP'] if r['label'] == summary['label']]
    check([r['step'] for r in group] == list(range(8)), summary['label'] + ' exact step identities')
    for previous, current in zip(group,group[1:]):
        check(previous['after_action'] == current['before'] and previous['enemy_after_action'] == current['enemy_before'], summary['label'] + ' no reset between steps')
    expected = {'switches':sum(r['before']['weapon'] != r['after_action']['weapon'] for r in group),
                'empty_reload_requests':sum(r['command']['reload'] and r['before']['ammo'] == 0 and r['before']['reserve'] == 0 and not r['switched'] for r in group),
                'empty_fire_requests':sum(r['command']['fire'] and r['before']['ammo'] == 0 and not r['shot_delta'] and not r['switched'] for r in group),
                'shots':sum(r['shot_delta'] for r in group), 'known_sidearm_resource_steps':sum(r['known_sidearm_resources'] for r in group)}
    check(all(summary[k] == v for k,v in expected.items()), summary['label'] + ' recomputed sequence aggregates')
    sequence_summaries.append(dict(summary, final={k:group[-1]['after_action'][k] for k in ('weapon','ammo','reserve','reload')},
                                   target=group[0]['scenario']['target'], sidearm=group[0]['scenario']['sidearm_resource']))

out = {'scope':'Builder recomputation only; fresh independent output review required. No full match, balance, movement or visual acceptance.',
       'raw_stdout_sha256':hashlib.sha256(data).hexdigest(), 'checks':checks, 'failures':failures,
       'row_counts':{k:len(v) for k,v in parsed.items()}, 'sequence_summaries':sequence_summaries,
       'limits':['Decorative weapon color excluded from source/header comparison.',
                 'Does not independently raycast world or reproduce spread/RNG/hit volumes; checks emitted query identities, raw health, events and mandatory witness output.',
                 'Intermediate event-count planning fences are source assertions only, not separately emitted counters.',
                 'Full AI planning state and every non-resource actor field are not simulated; this is a bounded raw resource/authority audit.']}
print(json.dumps(out,indent=2))
sys.exit(bool(failures))
