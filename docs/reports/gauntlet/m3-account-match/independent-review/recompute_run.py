#!/usr/bin/env python3
"""Recompute a completed run from raw artifacts without importing its validator."""
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import sys

run = Path(sys.argv[1]).resolve()
output = Path(sys.argv[2]).resolve()
ROOT = Path(__file__).resolve().parents[5]
review = Path(__file__).resolve().parent


def load(name):
    return json.loads((run / name).read_text())


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


report = load('report.json')
server = load('completed-server.json')
end = server['latest']
clients = [load(f'completed-client-{i}.json') for i in range(10)]
raw = (run / 'earned-result.json').read_bytes()
payload = json.loads(raw)
canonical = json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()
config = json.loads((ROOT / 'backend/config/economy.json').read_text())
accounts = end['accounts']
identities = set(accounts.values())
assert set(accounts) == {str(i) for i in range(1, 11)}
assert len(identities) == 10
assert set(r[0] for r in report['consumed_tickets']) == identities
assert len(report['consumed_tickets']) == 10
assert all(r[1:] == ['local-relay', True] for r in report['consumed_tickets'])
assert report['source_dirty'] is False
assert report['engine']['sha256'] == '8d106cbe6144c2dc7e881d61d2429c1a8a76e6b22ef48bd5e48dcf934953f71e'
assert report['engine']['version'] == '4.7.2.stable.official.ed1daf0bf'
assert end['phase'] == 'match_over' and end['round'] == 7
assert end['protocol'] == 6 and end['ranked_started'] is True and end['ranked_eligible'] is True
assert len(end['bindings']) == 10 and set(end['bindings'].values()) == set(range(1, 11))
assert (end['attack'], end['defend']) == (0, 7)
assert end['reward_status'] == 'queued_for_delivery'
assert end['stock_rules'] == dict(buy=15, round=100, plant=3, defuse=5, device=35, win_score=7)
assert set(end['activity_seconds']) == set(accounts)
assert end['match_id'] == payload['match_id'] == report['match_id']
assert report['earned_payload_sha256'] == sha(raw)
transitions = server['transitions']
assert all(a['elapsed'] <= b['elapsed'] for a, b in zip(transitions, transitions[1:]))
waiting = next(s for s in transitions if s['phase'] == 'waiting')
assert waiting['round'] == 0 and waiting['ranked_started'] is False
assert (waiting['attack'], waiting['defend']) == (0, 0)
rounds = []
for number in range(1, 8):
    states = [s for s in transitions if s['round'] == number]
    buy = next(s for s in states if s['phase'] == 'buy')
    live = next(s for s in states if s['phase'] == 'live')
    finish = next(s for s in states if s['phase'] in ('post', 'match_over'))
    before = (number - 1, 0) if number <= 6 else (0, 6)
    after = (number, 0) if number <= 6 else (0, 7)
    assert (buy['attack'], buy['defend']) == (live['attack'], live['defend']) == before
    assert (finish['attack'], finish['defend']) == after
    buy_seconds = live['elapsed'] - buy['elapsed']
    assert 14.9 <= buy_seconds <= 15.2
    item = dict(round=number, buy_seconds=buy_seconds, score_before=before, score_after=after)
    if number <= 6:
        planted = next(s for s in states if s['phase'] == 'live' and s['objective'] == 'planted')
        plant_elapsed = planted['elapsed'] - live['elapsed']
        fuse = finish['elapsed'] - planted['elapsed']
        assert plant_elapsed >= 2.9 and 34.9 <= fuse <= 35.2
        item.update(live_to_plant_seconds=plant_elapsed, fuse_seconds=fuse)
    else:
        live_seconds = finish['elapsed'] - live['elapsed']
        assert 99.9 <= live_seconds <= 100.2
        item['live_seconds'] = live_seconds
    rounds.append(item)
for state in transitions:
    if state['ranked_started']:
        assert state['ranked_eligible'] is True
        assert state['accounts'] == accounts and state['bindings'] == end['bindings']
simulation_seconds = end['match_duration']
terminal_seconds = simulation_seconds - (end['elapsed'] - end['summary']['duration'])
wall_seconds = (datetime.fromisoformat(payload['ended_at'].replace('Z', '+00:00')) -
                datetime.fromisoformat(payload['started_at'].replace('Z', '+00:00'))).total_seconds()
assert simulation_seconds >= terminal_seconds >= 300 and wall_seconds >= 300
assert set(p['player_id'] for p in payload['participants']) == identities
assert len(payload['participants']) == 10
participants = {p['player_id']: p for p in payload['participants']}
wallets = {r[0]: r[1:] for r in report['final_economy']['wallets']}
ledger = {r[0]: r[1:] for r in report['final_economy']['ledger']}
rewards = {r[0]: r[1] for r in report['final_economy']['rewards']}
profiles = {p['player_id']: p for p in report['http_profiles']}
assert len(wallets) == len(ledger) == len(rewards) == len(profiles) == 10
assert report['initial_economy']['counts'] == [0, 0, 0]
assert all(w[1:] == [0, 0] for w in report['initial_economy']['wallets'])
assert report['final_economy']['counts'] == [10, 10, 1]
earned = []
for actor in range(1, 11):
    identity = accounts[str(actor)]
    p = participants[identity]
    client = clients[actor - 1]
    observed = client['latest']
    won = actor <= 5
    objectives = 6 if actor == 1 else 0
    assert p['won'] is won and p['abandoned'] is False
    assert p['objective_contributions'] == objectives
    assert p['active_seconds'] <= wall_seconds
    assert p['active_seconds'] / wall_seconds >= .75
    assert end['activity_seconds'][str(actor)] / simulation_seconds >= .75
    observed_activity = min(terminal_seconds, end['activity_seconds'][str(actor)])
    # The production payload truncates the terminal duration and frozen activity.
    # A one-microsecond interval handles JSON/subtraction rounding at an integer.
    assert int(observed_activity - 1e-6) <= p['active_seconds'] <= int(observed_activity + 1e-6)
    assert observed['local_id'] == observed['initial_id'] == actor
    assert observed['display_name'] == profiles[identity]['display_name'] == f'Account Match {actor - 1}'
    assert observed['connection'] == 'connected' and observed['joined'] is True
    assert observed['reward_status'] == 'queued_for_delivery' and observed['snapshots'] > 100
    assert observed['team'] == (1 if won else 0)
    summary = observed['summary']
    assert summary['won'] is won and summary['draw'] is False and summary['offline'] is False
    assert summary['rounds'] == 7 and (summary['attack_score'], summary['defend_score']) == (0, 7)
    assert summary['objectives'] == objectives
    assert (summary['kills'], summary['deaths'], summary['assists']) == (0, 0, 0)
    for number in range(1, 8):
        states = [s for s in client['transitions'] if s['round'] == number and s['joined']]
        assert {'buy', 'live'} <= {s['phase'] for s in states}
        assert all(s['local_id'] == actor and s['initial_id'] == actor for s in states)
        assert all(s['display_name'] == f'Account Match {actor - 1}' for s in states)
        assert all(s['team'] == ((0 if won else 1) if number <= 6 else (1 if won else 0)) for s in states)
    assert not any(s['connection'] in ('failed', 'reconnecting') for s in client['transitions'])
    xp = config['xp_per_match'] + config['xp_per_win'] * won + config['xp_per_objective'] * objectives
    credits = config['match_completion'] + config['match_win'] * won + config['daily_first'] + config['level_reward'] * int((xp / config['xp_level_base']) ** .5)
    assert wallets[identity] == [credits, xp]
    assert ledger[identity] == [credits, credits, 'verified_match', payload['match_id']]
    assert rewards[identity]['credits'] == credits and rewards[identity]['xp'] == xp
    assert rewards[identity]['eligible'] is True
    assert rewards[identity]['won'] is won
    for stamp in ('started_at', 'ended_at'):
        assert datetime.fromisoformat(rewards[identity][stamp]) == datetime.fromisoformat(payload[stamp].replace('Z', '+00:00'))
    assert (profiles[identity]['credits'], profiles[identity]['xp']) == (credits, xp)
    earned.append(dict(actor=actor, player_id=identity, won=won, objectives=objectives,
                       active_seconds=p['active_seconds'], simulation_fraction=end['activity_seconds'][str(actor)] / simulation_seconds,
                       wall_fraction=p['active_seconds'] / wall_seconds, credits=credits, xp=xp, snapshots=observed['snapshots']))

checkpoints = {name: load(name + '.json') for name in (
    'earned-staged', 'earned-godot-killed', 'database-outage-pending', 'database-restored-zero',
    'backend-committed-ack-held', 'lost-ack-worker-killed', 'worker-restarted-committed', 'duplicate-replayed-unchanged')}
assert checkpoints['earned-staged']['sqlite'] is None
assert checkpoints['earned-staged']['economy'] == report['initial_economy']
assert len(checkpoints['earned-staged']['spool']) == 1
assert checkpoints['earned-staged']['spool'][0]['sha256'] == sha(raw)
assert checkpoints['earned-godot-killed']['sqlite'] is None
assert checkpoints['earned-godot-killed']['economy'] == report['initial_economy']
assert checkpoints['earned-godot-killed']['spool'] == checkpoints['earned-staged']['spool']
assert next(p for p in checkpoints['earned-godot-killed']['processes'] if p['name'] == 'server')['returncode'] == -9
for label, state in checkpoints.items():
    row = state['sqlite']
    if row:
        assert row['id'] == payload['match_id'] and row['payload'].encode() == canonical
        assert row['payload_sha256'] == row['fingerprint'] == sha(canonical)
for label in ('database-outage-pending', 'database-restored-zero', 'backend-committed-ack-held', 'lost-ack-worker-killed'):
    row = checkpoints[label]['sqlite']
    assert row['state'] == 'pending' and row['status'] == 500 and row['attempts'] >= 1
    assert checkpoints[label]['spool'] == []
assert checkpoints['database-restored-zero']['economy'] == report['initial_economy']
assert next(p for p in checkpoints['database-restored-zero']['processes'] if p['name'] == 'worker-outage')['returncode'] == -9
assert next(p for p in checkpoints['lost-ack-worker-killed']['processes'] if p['name'] == 'worker-lost-ack')['returncode'] == -9
for label in ('backend-committed-ack-held', 'lost-ack-worker-killed', 'worker-restarted-committed', 'duplicate-replayed-unchanged'):
    assert checkpoints[label]['economy'] == report['final_economy']
for label in ('worker-restarted-committed', 'duplicate-replayed-unchanged'):
    row = checkpoints[label]['sqlite']
    assert row['state'] == 'committed' and row['status'] == 200
    response = json.loads(row['response'])
    assert response['match_id'] == payload['match_id'] and len(response['rewards']) == 10
    assert {p['player_id']: p for p in response['rewards']} == {
        identity: dict(player_id=identity, **details) for identity, details in rewards.items()}
    assert row['response_sha256'] == sha(row['response'].encode())
exits = {p['name']: p['returncode'] for p in report['process_exits']}
assert exits['server'] == exits['worker-outage'] == exits['worker-lost-ack'] == -9
assert all(exits[f'client-{i}'] == 0 for i in range(10))
assert exits['worker-restart'] == exits['worker-replay'] == 0
with sqlite3.connect(run / 'results.sqlite') as db:
    rows = db.execute('SELECT id,payload,fingerprint,state,status FROM results').fetchall()
assert len(rows) == 1
assert rows[0] == (payload['match_id'], canonical, sha(canonical), 'committed', 200)
independent = json.loads((review / 'independent-postgres.json').read_text())
assert independent['status'] == 'observed'
tables = independent['tables']
assert [[r[0], r[2], r[3]] for r in tables['players']] == report['final_economy']['wallets']
assert tables['ledger'] == report['final_economy']['ledger']
assert tables['rewards'] == report['final_economy']['rewards']
assert tables['consumed_tickets'] == report['consumed_tickets']
assert len(tables['operations']) == 1
operation = tables['operations'][0]
assert operation[0] == 'match:' + payload['match_id'] and operation[1] == sha(canonical)
assert operation[2] == json.loads(checkpoints['worker-restarted-committed']['sqlite']['response'])
assert operation[2] == json.loads(checkpoints['duplicate-replayed-unchanged']['sqlite']['response'])
independent_initial = json.loads((review / 'independent-initial-postgres.json').read_text())
assert independent_initial['counts'] == [0, 0, 0]
assert len(independent_initial['players']) == 10
assert all(p[2:] == [0, 0] for p in independent_initial['players'])
assert all(report['cleanup'].values()) and report['godot_errors'] == []
for name in ('server', *(f'client-{i}' for i in range(10))):
    log = (run / (name + '.log')).read_text()
    assert 'Godot Engine v4.7.2.stable.official.ed1daf0bf' in log
    assert not any(marker in log for marker in ('SCRIPT ERROR', 'ERROR:', 'Parse Error', 'ObjectDB instances leaked'))
api_log = (run / 'api.log').read_text()
match_http_statuses = [int(v) for v in re.findall(r'POST /server/matches HTTP/1\.1" (\d+)', api_log)]
assert 500 in match_http_statuses and match_http_statuses[-2:] == [200, 200]
assert 'not currently accepting connections' in api_log
assert report['status'] == 'passed'
result = dict(status='passed', source_commit=report['source_commit'], engine=report['engine'],
              simulation_seconds=simulation_seconds, terminal_simulation_seconds=terminal_seconds, payload_wall_seconds=wall_seconds,
              raw_payload_sha256=sha(raw), canonical_payload_sha256=sha(canonical),
              rounds=rounds, earned=earned, checkpoints=list(checkpoints), process_exits=exits,
              backend_match_http_statuses=match_http_statuses,
              independent_postgres_observed_at_utc=independent['at_utc'],
              total_credits=sum(v[0] for v in wallets.values()), total_xp=sum(v[1] for v in wallets.values()))
output.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
