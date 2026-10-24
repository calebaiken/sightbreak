#!/usr/bin/env python3
"""Strict source-bound reader for objective observations; never launches Godot."""
import argparse
from collections import Counter
import copy
import difflib
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
REPORT = 'docs/reports/gauntlet/m5-objective-observability'
R2 = REPORT + '/correction-r2'
ACQUISITION_INVENTORY = 'docs/reports/gauntlet/m5-objective-observability-r4-20261024/acquisition-inventory.json'
PREFIX = 'BOT_OBJECTIVE_'
POSES = [120, 122, 127]
CONTROLS = ['plant', 'defuse', 'wrong_site', 'moving', 'no_interact']
KINDS = {'HEADER', 'PAIR', 'DECISION', 'AUTHORITY', 'INTERACTION', 'CONTROL_START', 'CONTROL', 'START', 'CALL', 'RESULT'}
DT = 1 / 60
IDS = {str(i) for i in range(1, 11)}
BOOL_COMMAND = {'interact', 'fire', 'reload', 'jump', 'crouch', 'smoke', 'grenade'}
COMMAND = BOOL_COMMAND | {'move', 'look', 'weapon'}
DECISION_ROLES = {'rifle', 'defuser', 'post_plant_hold', 'retake_cover', 'recover_device', 'carrier', 'split_flank', 'entry', 'escort', 'investigate_sound', 'anchor', 'rotate_investigate', 'pursue_memory'}
ACTOR_FIELDS = {'team', 'kills', 'assists', 'deaths', 'position', 'velocity', 'yaw', 'pitch', 'alive', 'health', 'weapon', 'ammo', 'reserve', 'reload', 'deploy', 'ammo_store', 'inventory', 'credits', 'grenades', 'smokes', 'recoil', 'rng', 'cooldowns', 'shot_index', 'fire_previous', 'jump_previous', 'grenade_previous', 'smoke_previous', 'crouching', 'head_height', 'floor_contact', 'collision_disabled', 'collision_height', 'collision_position', 'input'}
STATE_FIELDS = {'actors', 'utilities', 'rng', 'bots', 'teams', 'heard', 'objective', 'carrier', 'objective_position', 'objective_timer', 'contributions', 'interaction_progress', 'damage_history', 'round', 'attack_score', 'defend_score', 'bot_clock', 'interactions', 'time_left', 'tick', 'elapsed', 'phase'}
OBJECTIVE_FIELDS = {'objective', 'carrier', 'objective_position', 'objective_timer', 'contributions', 'interaction_progress', 'interactions', 'phase', 'time_left', 'attack_score', 'defend_score'}


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def integer(value, low=0, high=2**63-1):
    return type(value) is int and low <= value <= high


def number(value):
    return type(value) in (int, float) and math.isfinite(value)


def rng_state(value):
    return type(value) is str and re.fullmatch(r'-?\d+', value) is not None and -(2**63) <= int(value) < 2**63


def vector(value, size):
    return type(value) is list and len(value) == size and all(number(x) for x in value)


def same(a, b):
    if type(a) is dict and type(b) is dict:
        return a.keys() == b.keys() and all(same(a[k], b[k]) for k in a)
    if type(a) is list and type(b) is list:
        return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    if number(a) and number(b):
        return math.isclose(a, b, rel_tol=0, abs_tol=1e-8)
    return type(a) is type(b) and a == b


def contract(root=ROOT):
    return json.loads((Path(root) / 'game/tests/fixtures/bot_objective_contract.json').read_text())


BOT_FIELDS = frozenset(contract()["bot_reset"])

def original(root=ROOT):
    return {r['event_index']: r for r in map(json.loads, (Path(root) / 'game/tests/fixtures/bot_objective_timeout.jsonl').read_text().splitlines())}


def source_audit(root=ROOT):
    root = Path(root)
    identity = json.loads((root / REPORT / 'benchmark-identity.json').read_text())
    ai_path = 'game/scripts/gameplay/bot_ai.gd'
    ai = (root / ai_path).read_text()
    erased = re.sub(r'^[\t ]*# OBJECTIVE_OBSERVATION_BEGIN\n.*?^[\t ]*# OBJECTIVE_OBSERVATION_END\n', '', ai, flags=re.M | re.S)
    erased = erased.replace('_acquire_target(', 'acquire_target(')
    for name in ('acquire_target', 'compute_bot_input'):
        erased = re.sub(rf'(static func {name}\([^\n]*), observation: Dictionary = \{{\}}(\) ->)', r'\1\2', erased)
    erased = erased.replace('acquire_target(match_node, actor, state, profile, observation if observing else {})', 'acquire_target(match_node, actor, state, profile)')
    require(digest(erased.encode()) == identity['source'][ai_path], 'erasure does not recover inspected baseline AI')
    for path, expected in identity['source'].items():
        if path != ai_path:
            require(digest((root / path).read_bytes()) == expected, 'changed gameplay: ' + path)
    raw = (root / REPORT / 'original-timeout-slice.jsonl').read_bytes()
    require(digest(raw) == identity['selected_bytes_sha256'], 'changed original slice')
    require(raw == (root / 'game/tests/fixtures/bot_objective_timeout.jsonl').read_bytes(), 'changed fixture bytes')
    inventory = json.loads((root / ACQUISITION_INVENTORY).read_text())
    require(inventory['scope'] == 'complete_tracked_game_and_scripts', 'wrong inventory scope')
    files = inventory['files']
    require(all(path.startswith(('game/', 'scripts/')) and '..' not in Path(path).parts for path in files), 'invalid inventory path')
    if (root / '.git').exists():
        actual = subprocess.check_output(['git', 'ls-files', '-z', '--', 'game', 'scripts'], cwd=root).decode().split('\0')
        require(set(filter(None, actual)) == set(files), 'tracked acquisition inventory differs')
    for path, expected in files.items():
        require(digest((root / path).read_bytes()) == expected, 'changed acquisition dependency: ' + path)
    required = {'game/project.godot', ai_path, 'game/scripts/gameplay/utility.gd', 'game/scripts/network/movement_step.gd', 'game/tests/bot_objective_observation_probe.gd', 'game/tests/bot_objective_observation_probe.gd.uid', 'scripts/verify_bot_objective_observation.py'}
    require(required <= files.keys(), 'incomplete acquisition inventory')
    c = contract(root)
    historical = (root / R2 / 'source-reference/original-0527715-bot_ai.gd.txt').read_bytes()
    delta = list(difflib.ndiff(historical.decode().splitlines(), erased.splitlines()))
    require(digest(historical) == c['historical_ai_sha256'] and sum(line.startswith('+ ') for line in delta) == 13 and not any(line.startswith('- ') for line in delta), 'historical AI drift proof differs')
    require(c['baseline_ai_sha256'] == identity['source'][ai_path] and c['reconstruction_baseline'] == identity['base_commit'] and c['historical_ai_added_lines'] == 13 and c['historical_ai_sha256'] != c['baseline_ai_sha256'], 'historical/current source distinction missing')
    return {'source_erasure_passed': True, 'source_base': identity['base_commit'], 'acquisition_files': len(files), 'native_executed': False, 'compilation_verified': False}


def no_duplicate(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'duplicate JSON key')
        result[key] = value
    return result


def records(text):
    rows = []
    for line in text.splitlines():
        require(not re.search(r'SCRIPT ERROR|Parse Error|ERROR:|WARNING:|Orphan StringName|ObjectDB instances leaked', line), 'native log is not strict-clean')
        if not line.startswith(PREFIX):
            continue
        kind, sep, body = line[len(PREFIX):].partition(' ')
        require(sep and kind in KINDS, 'unknown or malformed record')
        value = json.loads(body, object_pairs_hook=no_duplicate, parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite JSON')))
        require(type(value) is dict, 'record must be an object')
        rows.append((kind, value))
    return rows


def command(value, neutral=False):
    require(type(value) is dict, 'command object missing')
    if neutral and set(value) == {'move', 'look'}:
        require(value['move'] == [0, 0] and vector(value['look'], 2), 'invalid suspended command')
        return
    require(set(value) == COMMAND, 'incomplete command schema')
    require(all(type(value[k]) is bool for k in BOOL_COMMAND), 'command boolean type')
    require(vector(value['move'], 2) and vector(value['look'], 2), 'command finite vectors')
    require(type(value['weapon']) is str and value['weapon'] in ('', 'sidearm', 'smg', 'rifle', 'marksman'), 'invalid weapon command')


def state(value):
    require(type(value) is dict and set(value) == STATE_FIELDS, 'incomplete protected state schema')
    require(value['phase'] in ('buy', 'live', 'post', 'match_over') and value['objective'] in ('carried', 'dropped', 'planted', 'defused'), 'invalid objective or phase')
    for key in ('tick', 'round', 'attack_score', 'defend_score', 'carrier'):
        require(integer(value[key], 0, 10 if key == 'carrier' else 2**63-1), 'state integer role: ' + key)
    for key in ('elapsed', 'time_left', 'objective_timer', 'interaction_progress'):
        require(number(value[key]) and value[key] >= 0, 'state numeric role: ' + key)
    require(number(value['bot_clock']) and vector(value['objective_position'], 3), 'state clock/position')
    require(rng_state(value['rng']), 'state RNG precision')
    require(type(value['actors']) is dict and set(value['actors']) == IDS, 'ten actor states required')
    for aid, actor in value['actors'].items():
        require(type(actor) is dict and set(actor) == ACTOR_FIELDS, 'incomplete actor protection ' + aid)
        require(integer(actor['team'], 0, 1), 'typed team')
        for key in ('kills', 'assists', 'deaths', 'ammo', 'reserve', 'credits', 'grenades', 'smokes', 'shot_index'):
            require(integer(actor[key]), 'actor integer role: ' + key)
        for key in ('yaw', 'pitch', 'health', 'reload', 'deploy', 'head_height', 'collision_height'):
            require(number(actor[key]), 'actor numeric role: ' + key)
        for key in ('alive', 'fire_previous', 'jump_previous', 'grenade_previous', 'smoke_previous', 'crouching', 'floor_contact', 'collision_disabled'):
            require(type(actor[key]) is bool, 'actor boolean role: ' + key)
        require(vector(actor['position'], 3) and vector(actor['velocity'], 3) and vector(actor['recoil'], 2) and vector(actor['collision_position'], 3), 'actor finite vectors')
        require(type(actor['inventory']) is list and all(type(w) is str and w in ('sidearm', 'smg', 'rifle', 'marksman') for w in actor['inventory']) and actor['weapon'] in actor['inventory'], 'actor inventory')
        require(type(actor['ammo_store']) is dict and all(vector(v, 2) and all(integer(x) for x in v) for v in actor['ammo_store'].values()), 'holstered resources')
        require(type(actor['cooldowns']) is dict and all(number(v) for v in actor['cooldowns'].values()), 'weapon cooldowns')
        require(rng_state(actor['rng']), 'actor RNG precision')
        command(actor['input'], neutral=value['phase'] != 'live')
    for key in ('bots', 'teams', 'heard', 'damage_history', 'interactions', 'contributions'):
        require(type(value[key]) is dict, 'state dictionary: ' + key)
    require(set(value['bots']) == IDS and set(value['teams']) == {'0', '1'}, 'complete bot/team memory required')
    bot_vectors = {'last_position', 'last_seen', 'heard_pos', 'damaged_from'}
    bot_flags = {'smoke_used', 'grenade_used'}
    for bot in value['bots'].values():
        require(set(bot) == BOT_FIELDS, 'bot memory schema')
        for key, item in bot.items():
            if key in bot_vectors: require(vector(item, 3), 'bot memory vector')
            elif key in bot_flags: require(type(item) is bool, 'bot memory boolean')
            elif key == 'role': require(type(item) is str and item, 'bot role')
            elif key in ('target', 'attacker_id'): require(integer(item, 0, 10), 'bot memory actor ID')
            elif key == 'recovery_wp': require(integer(item, -1), 'bot recovery waypoint')
            else: require(number(item), 'bot memory number')
    for team in value['teams'].values():
        require(set(team) == {'primary_site', 'target_site', 'contacts', 'death_alert_pos', 'death_alert_at'} and integer(team['primary_site'], 0, 1) and integer(team['target_site'], 0, 1) and vector(team['death_alert_pos'], 3) and number(team['death_alert_at']) and type(team['contacts']) is dict, 'team memory schema')
        for aid, report in team['contacts'].items():
            require(aid in IDS and set(report) == {'position', 'time', 'reporter'} and vector(report['position'], 3) and number(report['time']) and integer(report['reporter'], 1, 10), 'team contact schema')
    for aid, event in value['heard'].items():
        require(aid in IDS and set(event) == {'position', 'time'} and vector(event['position'], 3) and number(event['time']), 'heard event schema')
    for victim, history in value['damage_history'].items():
        require(victim in IDS and type(history) is dict and all(aid in IDS and number(amount) and amount >= 0 for aid, amount in history.items()), 'damage memory schema')
    for aid, progress in value['interactions'].items():
        require(aid in IDS and number(progress) and progress >= 0, 'invalid progress')
    require(all(aid in IDS and integer(v) for aid, v in value['contributions'].items()), 'objective contributions')
    require(type(value['utilities']) is list, 'utility state missing')
    for utility in value['utilities']:
        require(set(utility) == {'kind', 'position', 'velocity', 'owner_id', 'owner_team', 'fuse', 'lifetime', 'detonated', 'visual_only'}, 'utility schema')
        require(utility['kind'] in ('smoke', 'grenade') and vector(utility['position'], 3) and vector(utility['velocity'], 3) and integer(utility['owner_id'], 0, 10) and integer(utility['owner_team'], 0, 1), 'utility identity/pose')
        require(number(utility['fuse']) and number(utility['lifetime']) and type(utility['detonated']) is bool and type(utility['visual_only']) is bool, 'utility state types')


def bind_pose(value, pose, c, subject=None, seed_progress=False):
    expected = {'phase': 'live', 'round': pose['round_number'], 'tick': pose['simulation_tick'], 'elapsed': pose['elapsed'], 'time_left': pose['time_left'], 'attack_score': pose['attack_score'], 'defend_score': pose['defend_score'], 'objective': pose['objective_state'], 'carrier': pose['objective_carrier'], 'objective_position': pose['objective_position'], 'objective_timer': pose['objective_timer']}
    if subject == 'defuse':
        expected.update(objective='planted', objective_position=[-15, 0, 10], objective_timer=35)
    for key, wanted in expected.items():
        require(same(value[key], wanted), 'source pose mismatch: ' + key)
    require(value['contributions'] == {} and value['damage_history'] == {} and value['heard'] == {} and value['utilities'] == [] and value['bot_clock'] == 0, 'reset match assumptions differ')
    require(value['interactions'] == ({'6': .25} if seed_progress else {}), 'reset interaction assumptions differ')
    expected_bots = {}
    for record in pose['actors']:
        bot = copy.deepcopy(c['bot_reset']); bot['last_position'] = record['position']
        expected_bots[str(record['id'])] = bot
    expected_teams = {'0': copy.deepcopy(c['team_reset']), '1': copy.deepcopy(c['team_reset'])}
    expected_teams['0'].update(primary_site=pose['round_number'] % 2, target_site=pose['round_number'] % 2)
    require(same(value['bots'], expected_bots) and same(value['teams'], expected_teams), 'reset bot/team memory differs')
    for recorded in pose['actors']:
        actor = value['actors'][str(recorded['id'])]
        for key in ('team', 'alive', 'position', 'velocity', 'yaw', 'pitch', 'health', 'weapon', 'ammo', 'reserve', 'reload', 'credits', 'grenades', 'smokes', 'inventory', 'kills', 'assists', 'deaths'):
            wanted = recorded[key]
            if recorded['id'] == 6 and subject:
                if key == 'position': wanted = [0, 0, -20] if subject == 'wrong_site' else [-15, 0, 10]
                if key == 'team' and subject == 'defuse': wanted = 1
            require(same(actor[key], wanted), 'source actor mismatch: ' + str(recorded['id']) + '/' + key)
        require(actor['deploy'] == 0 and actor['cooldowns'] == {} and actor['shot_index'] == 0 and actor['recoil'] == [0, 0], 'reset action assumptions differ')
        require(all(actor[k] is False for k in ('fire_previous', 'jump_previous', 'grenade_previous', 'smoke_previous', 'crouching')), 'reset edge/stance assumptions differ')
        require(same(actor['head_height'], 1.62) and math.isclose(actor['collision_height'], 1.8, abs_tol=1e-6) and all(math.isclose(x, y, abs_tol=1e-6) for x, y in zip(actor['collision_position'], [0, .9, 0])) and actor['collision_disabled'] == (not recorded['alive']), 'reset head/collision assumptions differ')
        require(actor['ammo_store'] == {w: c['ammo_defaults'][w] for w in actor['inventory']}, 'reset holstered resources differ')
        neutral = {'move': [0, 0], 'look': actor['input']['look'], **dict.fromkeys(BOOL_COMMAND, False), 'weapon': ''}
        require(same(actor['input'], neutral) and all(math.isclose(x, y, abs_tol=1e-6) for x, y in zip(actor['input']['look'], [recorded['yaw'], recorded['pitch']])), 'reset neutral input differs')


def observation(obs, complete=True):
    require(type(obs) is dict and obs.get('enabled') is True and obs.get('operation') == 'decision' and obs.get('status') == 'complete', 'current complete decision status missing')
    required = {'enabled', 'operation', 'status', 'rng_before', 'candidates', 'plan', 'movement_mode', 'navigation_waypoint', 'navigation_destination', 'target_distance', 'aligned', 'decision'}
    require(set(obs) == required, 'decision observation schema')
    dec = obs['decision']
    require(set(dec) == {'actor_id', 'target_id', 'role', 'destination', 'interact', 'stuck', 'command', 'rng_after'}, 'decision result schema')
    require(integer(dec['actor_id'], 1, 10) and integer(dec['target_id'], 0, 10) and type(dec['role']) is str and dec['role'] in DECISION_ROLES and type(dec['interact']) is bool and number(dec['stuck']) and dec['stuck'] >= 0, 'typed decision roles')
    command(dec['command'])
    require(dec['command']['interact'] == dec['interact'], 'interaction command mismatch')
    require(set(obs['plan']) == {'destination', 'interact', 'primary_site'} and vector(obs['plan']['destination'], 3) and type(obs['plan']['interact']) is bool and integer(obs['plan']['primary_site'], 0, 1), 'plan schema')
    require(vector(dec['destination'], 3) and vector(obs['navigation_waypoint'], 3), 'destination/waypoint missing')
    mode = obs['movement_mode']
    require(mode in {'interact', 'idle', 'combat_cover', 'combat_brake', 'combat_strafe', 'navigate', 'scan'}, 'movement mode')
    require((vector(obs['navigation_destination'], 3) if mode in ('navigate', 'combat_cover') else obs['navigation_destination'] is None), 'stale navigation branch data')
    if mode == 'navigate': require(same(obs['navigation_destination'], dec['destination']), 'navigation/effective destination mismatch')
    if dec['role'] != 'pursue_memory': require(same(obs['plan']['destination'], dec['destination']), 'plan/effective destination mismatch')
    if dec['target_id'] == 0:
        require(obs['target_distance'] is None and obs['aligned'] is None, 'stale target branch data')
    else:
        require(number(obs['target_distance']) and obs['target_distance'] >= 0 and type(obs['aligned']) is bool, 'target branch data missing')
    require(rng_state(obs['rng_before']) and rng_state(dec['rng_after']), 'decision RNG precision')
    require(type(obs['candidates']) is list, 'candidate list')
    candidates = obs['candidates']
    require(len({c['id'] for c in candidates}) == len(candidates), 'duplicate candidate')
    for candidate in candidates:
        require(integer(candidate['id'], 1, 10) and number(candidate['distance']) and candidate['distance'] >= 0 and candidate['reason'] in ('range', 'fov', 'visibility', 'eligible'), 'typed perception result')
        require(set(candidate) == ({'id', 'distance', 'reason', 'score'} if candidate['reason'] == 'eligible' else {'id', 'distance', 'reason'}), 'candidate schema')
        if candidate['reason'] == 'eligible': require(number(candidate['score']), 'candidate score')
    require(dec['target_id'] == 0 or any(c['id'] == dec['target_id'] and c['reason'] == 'eligible' for c in candidates), 'unperceived target')


def decision(row):
    require(integer(row['actor_id'], 1, 10) and integer(row['tick']) and number(row['elapsed']) and same(row['dt'], .12), 'decision tick/actor/timestep')
    state(row['before']); state(row['after']); observation(row['observation'])
    before, after, obs = row['before'], row['after'], row['observation']
    aid = str(row['actor_id']); actor = before['actors'][aid]
    require(row['tick'] == before['tick'] == after['tick'] and same(row['elapsed'], before['elapsed']) and same(before['elapsed'], after['elapsed']) and same(row['position'], actor['position']), 'decision pose/tick unbound')
    require(actor['alive'] and before['phase'] == 'live' and obs['decision']['actor_id'] == row['actor_id'], 'ineligible decision actor')
    require(obs['plan']['primary_site'] == before['teams']['0']['primary_site'], 'plan site differs from team state')
    if obs['decision']['role'] == 'carrier': require(actor['team'] == 0 and row['actor_id'] == before['carrier'] and before['objective'] == 'carried', 'carrier role contradicts objective')
    if obs['decision']['role'] == 'defuser': require(actor['team'] == 1 and before['objective'] == 'planted', 'defuser role contradicts objective')
    require(obs['plan']['interact'] == obs['decision']['interact'], 'plan interaction mismatch')
    if obs['decision']['interact']: require(obs['decision']['command']['move'] == [0, 0] and obs['decision']['command']['fire'] is False and obs['decision']['command']['weapon'] == '', 'interaction command conflicts with action')
    require(obs['rng_before'] == before['rng'] and obs['decision']['rng_after'] == after['rng'] and same(obs['decision']['command'], after['actors'][aid]['input']), 'command/RNG does not bind actual decision')
    expected_interact = actor['team'] == 0 and row['actor_id'] == before['carrier'] and before['objective'] == 'carried' and site(actor['position']) >= 0
    if before['objective'] == 'planted' and actor['team'] == 1:
        defenders = [(math.dist(a['position'], before['objective_position']), int(i)) for i, a in before['actors'].items() if a['alive'] and a['team'] == 1]
        nearest = min(defenders)[1] if defenders else 0
        expected_interact = row['actor_id'] == nearest and math.dist(actor['position'], before['objective_position']) <= 2.6
        require((obs['decision']['role'] == 'defuser') == (row['actor_id'] == nearest), 'defuser role contradicts protected identity')
        if row['actor_id'] == nearest:
            require(same(obs['plan']['destination'], before['objective_position']), 'defuser destination contradicts device')
    require(obs['decision']['interact'] == expected_interact, 'plan interaction contradicts objective pose')
    if actor['team'] == 0 and row['actor_id'] == before['carrier'] and before['objective'] == 'carried':
        require(same(obs['plan']['destination'], [-15 if obs['plan']['primary_site'] == 0 else 15, 0, 10]), 'carrier plan destination contradicts site')
    expected = copy.deepcopy(before)
    for key in ('bots', 'teams', 'rng'): expected[key] = copy.deepcopy(after[key])
    expected['actors'][aid]['input'] = copy.deepcopy(after['actors'][aid]['input'])
    require(same(expected, after), 'decision changed protected actor/objective state')
    enemies = {int(i) for i, a in before['actors'].items() if a['alive'] and a['team'] != actor['team']}
    require({c['id'] for c in obs['candidates']} == enemies, 'perception omitted or invented enemy')
    for candidate in obs['candidates']:
        target = before['actors'][str(candidate['id'])]
        require(math.isclose(candidate['distance'], math.dist(actor['position'], target['position']), abs_tol=1e-4), 'candidate distance mismatch')
    vision = contract()['profiles']['normal']['vision_range']
    require([v['id'] for v in obs['candidates']] == sorted(enemies), 'candidate order differs from stock actors')
    selected, score = 0, vision
    for candidate in obs['candidates']:
        require((candidate['distance'] > vision) == (candidate['reason'] == 'range'), 'candidate range rejection contradicts source profile')
        if candidate['reason'] == 'eligible' and candidate['score'] < score:
            selected, score = candidate['id'], candidate['score']
    require(obs['decision']['target_id'] == selected, 'selected target contradicts scored candidates')
    if obs['decision']['target_id']:
        target = before['actors'][str(obs['decision']['target_id'])]
        require(math.isclose(obs['target_distance'], math.dist(actor['position'], target['position']), abs_tol=1e-4), 'target distance mismatch')


def site(position):
    for i, center in enumerate(([-15, 0, 10], [15, 0, 10])):
        if math.hypot(position[0]-center[0], position[2]-center[2]) < 3.8: return i
    return -1


def end_round(value, winner):
    value['attack_score' if winner == 0 else 'defend_score'] += 1
    for actor in value['actors'].values(): actor['credits'] = min(9000, actor['credits'] + (2700 if actor['team'] == winner else 1900))
    value['phase'] = 'match_over' if max(value['attack_score'], value['defend_score']) >= 7 or value['round'] >= 12 else 'post'
    value['time_left'] = 5


def interaction(row):
    require(integer(row['tick']) and type(row['dt']) is float and same(row['dt'], DT) and row['dt'] > 0, 'interaction fixed positive 60 Hz timestep')
    state(row['before']); state(row['after'])
    before, after = row['before'], row['after']
    require(before['phase'] == 'live' and before['tick'] == after['tick'] == row['tick'] and same(before['elapsed'], after['elapsed']), 'interaction tick/phase')
    require(row['objective_before'] == before['objective'] and row['objective_after'] == after['objective'] and row['carrier_before'] == before['carrier'] and row['carrier_after'] == after['carrier'] and same(row['progress_after'], after['interactions']), 'authority summary contradicts states')
    require(set(row['actors_before']) == IDS, 'authority actor predicates missing')
    for aid, a in before['actors'].items():
        predicate = {'alive': a['alive'], 'team': a['team'], 'position': a['position'], 'interact': a['input']['interact'], 'move': a['input']['move'], 'site': site(a['position']), 'objective_distance': math.dist(a['position'], before['objective_position']), 'progress': before['interactions'].get(aid, 0.0)}
        actual = row['actors_before'][aid]
        require(set(actual) == set(predicate), 'authority predicate schema')
        require(all(same(actual[k], v) if k != 'objective_distance' else number(actual[k]) and math.isclose(actual[k], v, abs_tol=1e-4) for k, v in predicate.items()), 'authority predicate contradicts state')
    expected = copy.deepcopy(before); expected['interaction_progress'] = 0
    if expected['objective'] == 'planted':
        expected['objective_timer'] = max(0, expected['objective_timer'] - DT)
        if expected['objective_timer'] <= 0:
            end_round(expected, 0)
            require(same(expected, after), 'detonation early-return state mismatch')
            return
    if expected['objective'] == 'dropped':
        for aid, actor in expected['actors'].items():
            if actor['alive'] and actor['team'] == 0 and math.dist(actor['position'], expected['objective_position']) < 2:
                expected.update(carrier=int(aid), objective='carried'); break
    for aid, actor in expected['actors'].items():
        eligible = actor['alive'] and actor['input']['interact'] and math.hypot(*actor['input']['move']) < .2
        planting = actor['team'] == 0 and int(aid) == expected['carrier'] and expected['objective'] == 'carried' and site(actor['position']) >= 0
        defusing = actor['team'] == 1 and expected['objective'] == 'planted' and math.dist(actor['position'], expected['objective_position']) <= 2.8
        if not eligible or not (planting or defusing):
            expected['interactions'].pop(aid, None); continue
        progress = expected['interactions'].get(aid, 0.0) + DT
        expected['interactions'][aid] = progress
        if progress >= (3 if planting else 5):
            expected['interactions'].clear()
            actor['credits'] = min(9000, actor['credits'] + 300)
            expected['contributions'][aid] = expected['contributions'].get(aid, 0) + 1
            if planting: expected.update(objective='planted', objective_position=actor['position'], objective_timer=35)
            else:
                expected['objective'] = 'defused'; end_round(expected, 1)
            break
    require(same(expected, after), 'objective progress/first threshold/transition/reward mismatch')


def action_handoff(current, observed):
    """Necessary source invariants between decisions/actions and the consumer.

    This does not reconstruct damage rays or validate the whole combat outcome.
    """
    unchanged = {'tick', 'elapsed', 'rng', 'bot_clock', 'round', 'phase', 'time_left',
                 'objective_timer', 'interactions', 'interaction_progress',
                 'contributions', 'attack_score', 'defend_score'}
    require(all(same(observed[k], current[k]) for k in unchanged), 'action phase changed protected match/objective state')
    deaths = Counter()
    kills = Counter()
    for aid in IDS:
        before, after = current['actors'][aid], observed['actors'][aid]
        require(after['team'] == before['team'], 'action phase reassigned actor team')
        require(same(after['input'], before['input']), 'actual command does not reach authority')
        require(not (not before['alive'] and after['alive']), 'action phase revived an actor')
        death_delta = after['deaths'] - before['deaths']
        require(death_delta == int(before['alive'] and not after['alive']), 'action death counter does not bind elimination')
        kill_delta = after['kills'] - before['kills']
        require(kill_delta >= 0, 'action phase removed kills')
        deaths[before['team']] += death_delta
        kills[before['team']] += kill_delta
        require(after['credits'] == min(9000, before['credits'] + 300 * kill_delta), 'action credits do not bind kill awards')
    require(all(kills[team] <= deaths[1 - team] for team in (0, 1)), 'action kills exceed opposing eliminations')
    carrier = str(current['carrier'])
    carrier_died = (current['objective'] == 'carried' and carrier in IDS
                    and current['actors'][carrier]['alive'] and not observed['actors'][carrier]['alive'])
    if carrier_died:
        require(observed['objective'] == 'dropped' and observed['carrier'] == 0
                and same(observed['objective_position'], observed['actors'][carrier]['position']),
                'action phase omitted required carrier drop')
    else:
        require(observed['objective'] == current['objective'] and observed['carrier'] == current['carrier'] and same(observed['objective_position'], current['objective_position']), 'action phase invented objective transition or device identity/position')


def verify_records(rows, root=ROOT):
    require(rows and rows[0][0] == 'HEADER' and rows[-1][0] == 'RESULT', 'missing header or terminal result')
    groups = {k: [r for tag, r in rows if tag == k] for k in KINDS}
    require(len(groups['HEADER']) == len(groups['RESULT']) == 1, 'duplicate boundary records')
    header, result = groups['HEADER'][0], groups['RESULT'][0]
    c = contract(root); source = original(root)
    require(set(header) == set(c) | {'engine', 'time_scale', 'physics_ticks_per_second'}, 'header contract schema')
    require(all(same(header[k], v) for k, v in c.items()), 'header/source contract mismatch')
    require(all(type(v) is int for v in header['source_events']) and all(type(header[k]) is int for k in ('forward_source_event', 'forward_ticks', 'historical_ai_added_lines')), 'header integer roles')
    require(type(header['schema']) is int and type(header['protocol']) is int and number(header['time_scale']) and type(header['time_scale']) is not bool and header['time_scale'] == 1 and type(header['physics_ticks_per_second']) is int and header['physics_ticks_per_second'] == 60, 'header scalar roles')
    require(all(type(header['engine'][k]) is int for k in ('major', 'minor', 'patch')) and tuple(header['engine'][k] for k in ('major', 'minor', 'patch')) == (4, 7, 2), 'wrong engine')
    modes, reasons = Counter(), Counter()
    seen = set()
    for row in groups['DECISION']:
        decision(row)
        key = (row['label'], row['tick'], row['actor_id'])
        require(key not in seen, 'duplicate decision'); seen.add(key)
        modes[row['observation']['movement_mode']] += 1
        reasons.update(v['reason'] for v in row['observation']['candidates'])
    require([p['event_index'] for p in groups['PAIR']] == POSES, 'paired poses incomplete')
    for pair in groups['PAIR']:
        for key in ('before_off', 'before_on', 'after_off', 'after_on'): state(pair[key])
        require(pair['equal'] is True and same(pair['before_off'], pair['before_on']) and same(pair['after_off'], pair['after_on']), 'trace changed protected state')
        bind_pose(pair['before_on'], source[pair['event_index']], c)
        matched = [r for r in groups['DECISION'] if r['label'] == 'pose_' + str(pair['event_index'])]
        require(len(matched) == 1 and matched[0]['actor_id'] == 6 and same(matched[0]['before'], pair['before_on']) and same(matched[0]['after'], pair['after_on']), 'pair decision unbound')
    require([r['case'] for r in groups['CALL']] == c['freshness_cases'], 'freshness cases incomplete')
    for row in groups['CALL']:
        name, out = row['case'], row['output']
        if name == 'empty_default': require(out == {}, 'default output not empty')
        elif name in ('live_complete', 'branch_change'):
            observation(out)
            require(out['decision']['actor_id'] == 6, 'freshness call describes another actor')
            if name == 'branch_change': require(out['decision']['target_id'] == 0 and out['target_distance'] is None and out['aligned'] is None and out['navigation_destination'] != [999, 999, 999], 'branch output stale')
        elif name == 'direct_perception':
            require(set(out) == {'enabled', 'operation', 'status', 'candidates', 'target_id'} and out['enabled'] is True and out['operation'] == 'perception' and out['status'] == 'complete' and integer(out['target_id'], 0, 10) and type(out['candidates']) is list, 'direct perception stale result')
            require(out['target_id'] == 0 or any(type(candidate) is dict and candidate.get('id') == out['target_id'] and candidate.get('reason') == 'eligible' for candidate in out['candidates']), 'direct perception selected an unperceived target')
        else:
            wanted = {'live_to_dead': 'dead', 'live_to_post': 'non_live', 'offline_to_online': 'blocked'}.get(name, 'disabled')
            require(same(out, {'enabled': wanted != 'disabled', 'operation': 'decision', 'status': wanted}), 'stale early-return/gated output')
    for row in groups['INTERACTION']: interaction(row)
    require(len(groups['START']) == 1 and type(groups['START'][0]['source_event']) is int and groups['START'][0]['source_event'] == 122, 'forward start missing')
    start = groups['START'][0]['state']; state(start); bind_pose(start, source[122], c)
    authority = groups['AUTHORITY']
    require(len(authority) == 120, 'forward authority count')
    previous = start
    forward_decisions = [r for r in groups['DECISION'] if r['label'] == 'forward_live_122']
    consumed = set(); expected_clock = 0.0
    for step in authority:
        require(step['label'] == 'forward_live_122' and integer(step['tick']) and type(step['dt']) is float and same(step['dt'], DT) and step['dt'] > 0, 'typed forward authority step')
        before, after = step['before'], step['after']; state(before); state(after)
        expected = copy.deepcopy(previous); expected['elapsed'] += DT
        # Utility nodes have their own engine physics callbacks between manual steps.
        expected['utilities'] = before['utilities']
        require(same(expected, before) and after['tick'] == before['tick'] + 1 == step['tick'] and same(before['elapsed'], after['elapsed']), 'forward authority continuity')
        batch = [r for r in forward_decisions if r['tick'] == step['tick']]
        expected_clock -= DT
        if expected_clock <= 0:
            expected_clock = .12
            expected_ids = [int(aid) for aid, a in before['actors'].items() if a['alive']] if before['phase'] == 'live' else []
            require([r['actor_id'] for r in batch] == expected_ids, 'forward decision batch incomplete')
        else: require(not batch, 'unexpected forward decision tick')
        require(same(after['bot_clock'], expected_clock), 'forward bot clock mismatch')
        current = copy.deepcopy(before); current['tick'] += 1; current['bot_clock'] = expected_clock
        for row in batch:
            require(same(row['before'], current), 'forward decision before state unbound')
            current = row['after']; consumed.add((row['tick'], row['actor_id']))
        objectives = [r for r in groups['INTERACTION'] if r['label'] == 'forward_live_122' and r['tick'] == step['tick']]
        require(len(objectives) == (1 if before['phase'] == 'live' else 0), 'forward objective observation missing')
        if objectives:
            obj = objectives[0]
            action_handoff(current, obj['before'])
            # Movement, actions and resulting damage occur between input and objective.
            post = copy.deepcopy(obj['after'])
            if post['phase'] == 'live':
                attackers = sum(a['alive'] and a['team'] == 0 for a in post['actors'].values())
                defenders = sum(a['alive'] and a['team'] == 1 for a in post['actors'].values())
                if defenders == 0: end_round(post, 0)
                elif attackers == 0 and post['objective'] != 'planted': end_round(post, 1)
            if post['phase'] != 'match_over': post['time_left'] = max(0, post['time_left'] - DT)
            require(same(after, post), 'forward post-objective state unbound')
        else:
            require(all(same(after[k], before[k]) for k in OBJECTIVE_FIELDS - {'time_left'}) and same(after['time_left'], before['time_left'] if before['phase'] == 'match_over' else max(0, before['time_left'] - DT)), 'nonlive authority state mismatch')
        previous = after
    require(len(consumed) == len(forward_decisions), 'forward decision outside authority ticks')
    require([r['name'] for r in groups['CONTROL_START']] == CONTROLS and [r['name'] for r in groups['CONTROL']] == CONTROLS, 'authority controls incomplete')
    for begin, summary in zip(groups['CONTROL_START'], groups['CONTROL']):
        name = summary['name']; state(begin['state']); state(summary['final'])
        bind_pose(begin['state'], source[127], c, subject=name, seed_progress=name not in ('plant', 'defuse'))
        steps = [r for r in groups['INTERACTION'] if r['label'] == 'control_' + name]
        require(integer(summary['ticks'], 1, 301) and len(steps) == summary['ticks'] and summary['valid'] is True, 'control row count/result')
        previous = begin['state']
        consumed_control = set()
        control_decisions = [r for r in groups['DECISION'] if r['label'] == 'control_' + name]
        for index, row in enumerate(steps):
            require(row['tick'] == previous['tick'] + 1 and same(row['before']['elapsed'], previous['elapsed'] + DT), 'control consecutive ticks')
            thinking = [r for r in control_decisions if r['tick'] == row['tick']]
            require(len(thinking) == (1 if index % 8 == 0 else 0), 'control decision stream incomplete')
            if thinking:
                event = thinking[0]
                expected = copy.deepcopy(previous); expected['tick'] += 1; expected['elapsed'] += DT
                require(event['actor_id'] == 6 and same(event['before'], expected), 'control decision state unbound')
                current_command = copy.deepcopy(event['after']['actors']['6']['input'])
                context = copy.deepcopy(event['after'])
                consumed_control.add(event['tick'])
            else:
                current_command = copy.deepcopy(previous['actors']['6']['input'])
                context = copy.deepcopy(previous)
                context['tick'] += 1
                context['elapsed'] += DT
            if name not in ('plant', 'defuse'):
                current_command['interact'] = name != 'no_interact'
                current_command['move'] = [0, 1] if name == 'moving' else [0, 0]
            require(same(row['before']['actors']['6']['input'], current_command), 'control actual command unbound')
            context['actors']['6']['input'] = current_command
            action_handoff(context, row['before'])
            require(all(same(row['before']['actors'][aid]['position'], context['actors'][aid]['position']) for aid in IDS - {'6'}), 'isolated control moved a non-subject actor')
            require(all(same(row['before'][key], previous[key]) for key in OBJECTIVE_FIELDS), 'cross-row objective/progress discontinuity')
            require(all(row['before']['actors'][aid]['credits'] == previous['actors'][aid]['credits'] for aid in IDS), 'cross-row credit discontinuity')
            previous = row['after']
        require(len(consumed_control) == len(control_decisions), 'control decision outside authority ticks')
        require(same(summary['final'], previous) and summary['objective'] == previous['objective'] and same(summary['contributions'], previous['contributions']), 'control summary contradicts terminal authority')
        if name in ('plant', 'defuse'):
            require(previous['objective'] == ('planted' if name == 'plant' else 'defused') and previous['contributions'] == {'6': 1} and previous['interactions'] == {}, 'positive terminal state')
            require(all(r['after']['objective'] == r['before']['objective'] for r in steps[:-1]) and steps[-1]['after']['objective'] != steps[-1]['before']['objective'], 'completion not at first final threshold')
        else:
            require(len(steps) == 1 and previous['objective'] == 'carried' and previous['interactions'] == {} and previous['contributions'] == {}, 'negative control outcome')
            a = steps[0]['actors_before']['6']
            require((name == 'wrong_site' and a['site'] == -1) or (name == 'moving' and math.hypot(*a['move']) >= .2) or (name == 'no_interact' and a['interact'] is False), 'negative control not exercised')
    expected_labels = {'pose_' + str(i) for i in POSES} | {'forward_live_122'} | {'control_' + n for n in CONTROLS}
    require(all(row['label'] in expected_labels for k in ('DECISION', 'INTERACTION', 'AUTHORITY') for row in groups[k]), 'unknown record label')
    require(all(type(result[k]) is int for k in ('checks', 'pairs', 'controls', 'decisions', 'interactions', 'authority')), 'terminal integer roles')
    require(result['failures'] == [] and integer(result['checks'], 20) and result['pairs'] == 3 and result['controls'] == 5 and result['decisions'] == len(groups['DECISION']) and result['interactions'] == len(groups['INTERACTION']) and result['authority'] == len(authority) and result['scope'] == 'diagnostic_only_no_objective_quality_acceptance', 'incomplete terminal result')
    return {'observable_contract_passed': True, 'decision_rows': len(groups['DECISION']), 'interaction_rows': len(groups['INTERACTION']), 'movement_modes': dict(modes), 'perception_results': dict(reasons), 'scope': 'current_source_reconstruction_not_historical_cause_or_G2_acceptance'}


def verify(text, root=ROOT):
    return verify_records(records(text), root)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--log', type=Path)
    args = parser.parse_args()
    report = {'source': source_audit(args.root)}
    if args.log: report['observations'] = verify(args.log.read_text(), args.root)
    print(json.dumps(report, indent=2))


if __name__ == '__main__': main()
