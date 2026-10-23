#!/usr/bin/env python3
"""Ten real account clients finish a stock-rules match, then recover its earned result.

Only fake local accounts; owns an ephemeral loopback PostgreSQL container and ports.
No game-state/result injection, external services, saved credentials, or performance
claim. Requires the pinned engine, cached postgres image, and existing backend venv.
"""
import argparse
from contextlib import closing
from datetime import datetime, timezone
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import platform
import secrets
import signal
import socket
import sqlite3
import subprocess
import sys
import threading
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
IMAGE = 'postgres:17@sha256:2d2b8998d31037bf721cfdf764d76ba74171b4fab3431b7f72c27c56ddbdf9e3'
DOCKER = ['docker', '--host=unix:///var/run/docker.sock']
RULES = dict(buy=15.0, round=100.0, plant=3.0, defuse=5.0, device=35.0, win_score=7)


def free_port(kind=socket.SOCK_STREAM):
    with socket.socket(socket.AF_INET, kind) as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]


def read_report(path):
    return json.loads(path.read_text()) if path.exists() else {}


def verify_score_timeline(states):
    for state in states:
        number, phase = state['round'], state['phase']
        if number == 0:
            assert (state['attack'], state['defend']) == (0, 0)
        elif number <= 6:
            assert (state['attack'], state['defend']) == (number if phase == 'post' else number - 1, 0)
        else:
            assert number == 7
            assert (state['attack'], state['defend']) == (0, 7 if phase == 'match_over' else 6)


def verify_match(server, clients, identities):
    """Fail closed on incomplete observations, altered rules, identity or eligibility."""
    end = server['latest']
    assert end['stock_rules'] == RULES and end['protocol'] == 6
    assert end['phase'] == 'match_over' and end['reward_status'] == 'queued_for_delivery'
    assert end['ranked_started'] and end['ranked_eligible'] and end['match_duration'] >= 300
    assert 7 <= end['round'] <= 12 and max(end['attack'], end['defend']) == 7
    assert end['attack'] != end['defend']
    assert len(end['accounts']) == len(end['bindings']) == 10
    assert set(end['accounts'].values()) == set(identities)
    assert len(set(end['bindings'].values())) == 10
    assert set(end['bindings'].values()) == set(range(1, 11))
    assert all(value / end['match_duration'] >= .75 for value in end['activity_seconds'].values())
    assert set(end['activity_seconds']) == set(end['accounts'])
    transitions = server['transitions']
    verify_score_timeline(transitions)
    assert any(s['phase'] == 'waiting' and s['round'] == 0 and not s['ranked_started'] for s in transitions)
    for state in transitions:
        if state['ranked_started']:
            assert state['ranked_eligible'] and state['accounts'] == end['accounts']
            assert state['bindings'] == end['bindings']
    for number in range(1, end['round'] + 1):
        states = [s for s in transitions if s['round'] == number]
        buy = next(s for s in states if s['phase'] == 'buy')
        live = next(s for s in states if s['phase'] == 'live')
        assert live['elapsed'] - buy['elapsed'] >= RULES['buy'] - .15, ('short buy', number)
        finish = next(s for s in states if s['phase'] in ('post', 'match_over'))
        if number <= 6:
            planted = next(s for s in states if s['phase'] == 'live' and s['objective'] == 'planted')
            assert planted['elapsed'] - live['elapsed'] >= RULES['plant'] - .15
            assert finish['elapsed'] - planted['elapsed'] >= RULES['device'] - .15
        else:
            assert finish['elapsed'] - live['elapsed'] >= RULES['round'] - .15
    assert end['round'] == 7 and (end['attack'], end['defend']) == (0, 7)
    assert len(clients) == 10
    for index, client in enumerate(clients):
        observed = client['latest']
        assert observed['stock_rules'] == RULES and observed['protocol'] == 6
        assert observed['joined'] and observed['connection'] == 'connected'
        assert observed['initial_id'] == observed['local_id'] == index + 1
        assert observed['display_name'] == f'Account Match {index}'
        assert observed['phase'] == 'match_over' and observed['summary']['offline'] is False
        summary = observed['summary']
        assert summary['rounds'] == end['round'] and observed['snapshots'] > 100
        assert (summary['attack_score'], summary['defend_score']) == (end['attack'], end['defend'])
        assert summary['won'] == (index < 5) and summary['draw'] is False
        assert observed['reward_status'] == 'queued_for_delivery'
        assert observed['attack'] == end['attack'] and observed['defend'] == end['defend']
        assert not any(s['connection'] in ('failed', 'reconnecting') for s in client['transitions'])
        connected_states = [s for s in client['transitions'] if s['joined'] and s['round'] >= 1]
        verify_score_timeline(connected_states)
        for number in range(1, end['round'] + 1):
            states = [s for s in connected_states if s['round'] == number]
            assert any(s['phase'] == 'buy' for s in states), ('client missing buy', index, number)
            assert any(s['phase'] == 'live' for s in states), ('client missing live', index, number)
        assert next(s for s in client['transitions'] if s['round'] == 1 and s.get('team') is not None)['team'] == (0 if index < 5 else 1)
        assert observed['team'] == (1 if index < 5 else 0), 'stock halftime did not switch sides'


def verify_earned_payload(payload, server, clients):
    """Tie outgoing awards to the independently observed scenario and replicas."""
    end = server['latest']
    assert payload['match_id'] == end['match_id'] and payload['mode'] == 'ranked_5v5'
    participants = {p['player_id']: p for p in payload['participants']}
    assert len(payload['participants']) == len(participants) == 10
    assert set(participants) == set(end['accounts'].values())
    scoreboard = {s['id']: s for s in end['summary']['scoreboard']}
    assert set(scoreboard) == set(range(1, 11))
    # Latest reports may arrive after match over. Reconstruct the duration at
    # result emission, where production caps integer activity by match duration.
    terminal_duration = end['match_duration'] - (end['elapsed'] - end['summary']['duration'])

    def serialized_floors(value):
        floors = {int(value)}
        nearest = round(value)
        # Float accumulation and JSON serialization can straddle an integer.
        # Allow both adjacent floors only within 0.1 microseconds of that edge.
        if abs(value - nearest) <= 1e-7:
            floors.update((max(0, nearest - 1), nearest))
        return floors

    for index, client in enumerate(clients):
        actor_id = index + 1
        participant = participants[end['accounts'][str(actor_id)]]
        summary = client['latest']['summary']
        assert participant['won'] == summary['won'] == (actor_id <= 5)
        objectives = 6 if actor_id == 1 else 0
        assert participant['objective_contributions'] == summary['objectives'] == scoreboard[actor_id]['objectives'] == objectives
        possible_active = {min(duration, activity) for duration in serialized_floors(terminal_duration)
                           for activity in serialized_floors(end['activity_seconds'][str(actor_id)])}
        assert participant['active_seconds'] in possible_active
        assert participant['abandoned'] is False and scoreboard[actor_id]['bot'] is False
        assert summary['kills'] == summary['deaths'] == summary['assists'] == 0
    started = datetime.fromisoformat(payload['started_at'])
    ended = datetime.fromisoformat(payload['ended_at'])
    assert started.tzinfo and ended.tzinfo and 300 <= (ended - started).total_seconds() <= 7200


def main():
    import psycopg
    from psycopg import sql

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--timeout', type=float, default=1200, help='Wall seconds after all ten admissions; incomplete runs fail and retain reports')
    parser.add_argument('--python', type=Path, default=Path(sys.executable), help='Existing interpreter with backend dependencies')
    args = parser.parse_args()
    if not 30 <= args.timeout <= 2400:
        parser.error('timeout must be between 30 and 2400 seconds')
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    out.chmod(0o700)
    spool = out / 'spool'
    spool.mkdir(mode=0o700)
    sqlite_path = out / 'results.sqlite'
    control = out / 'stop'
    container = 'sightbreak-account-match-' + secrets.token_hex(6)
    database = 'sightbreak_match_test'
    password = secrets.token_urlsafe(24)
    api_port, game_port = free_port(), free_port(socket.SOCK_DGRAM)
    key = secrets.token_urlsafe(48)
    # Use only this run's generated local configuration. Never read saved keys.
    env = os.environ.copy()
    for name in ('SIGHTBREAK_JOIN_TICKET', 'SIGHTBREAK_SERVER_KEY', 'SIGHTBREAK_RESULT_SPOOL', 'DATABASE_URL',
                 'DOCKER_HOST', 'DOCKER_CONTEXT', 'DOCKER_TLS', 'DOCKER_TLS_VERIFY', 'DOCKER_CERT_PATH'):
        env.pop(name, None)
    env.update(SIGHTBREAK_SERVER_KEY=key, SIGHTBREAK_SERVER_ID='local-relay',
               SIGHTBREAK_RESULT_SPOOL=str(spool), SIGHTBREAK_TEST_ECONOMY_URL=f'http://127.0.0.1:{api_port}',
               SIGHTBREAK_STATE_DIR=str(out / 'state'), SIGHTBREAK_TOOLS_DIR='/workspace/tools')
    engine = Path('/workspace/tools/godot-4.7.2/Godot_v4.7.2-stable_linux.x86_64')
    env['GODOT_BIN'] = str(engine)
    engine_version = subprocess.check_output([str(engine), '--headless', '--version'], env=env, text=True).strip()
    assert engine_version == '4.7.2.stable.official.ed1daf0bf'
    processes, logs, accounts = [], [], []
    proxy = None
    committed, release = threading.Event(), threading.Event()
    forwarded = []
    report = {'status': 'in_progress', 'scope': 'loopback headless scripted no-combat stock match; fake accounts; no performance or human-play claim',
              'source_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
              'game_tree': subprocess.check_output(['git', 'rev-parse', 'HEAD:game'], cwd=ROOT, text=True).strip(),
              'source_dirty': bool(subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, text=True).strip()),
              'started_at_utc': datetime.now(timezone.utc).isoformat(),
              'engine': {'path': str(engine), 'version': engine_version, 'sha256': hashlib.sha256(engine.read_bytes()).hexdigest()},
              'platform': platform.platform(), 'timeout_seconds': args.timeout, 'container': container,
              'api_port': api_port, 'game_port': game_port,
              'sha256': {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in
                         ('scripts/test_account_match.py', 'game/tests/account_match_probe.gd', 'game/scripts/gameplay/match.gd')},
              'checks': {}, 'cleanup': {}}
    admin = None
    container_owned = False
    started = time.monotonic()

    def save():
        (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')

    def start(name, command, child_env=None):
        log = (out / (name + '.log')).open('w')
        logs.append(log)
        child = subprocess.Popen(command, cwd=ROOT, env=env if child_env is None else child_env, stdout=log, stderr=subprocess.STDOUT)
        processes.append((name, child))
        return child

    def wait_for(predicate, label, timeout=30):
        until = time.monotonic() + timeout
        while time.monotonic() < until:
            if predicate(): return
            time.sleep(.1)
        raise AssertionError('Timed out: ' + label)

    def request(path, data=None, token=None):
        headers = {'Content-Type': 'application/json'}
        if token: headers['Authorization'] = 'Bearer ' + token
        req = urllib.request.Request(env['SIGHTBREAK_TEST_ECONOMY_URL'] + path,
                                     None if data is None else json.dumps(data).encode(), headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.load(response)

    def row():
        if not sqlite_path.exists(): return None
        try:
            with closing(sqlite3.connect(sqlite_path)) as db:
                db.row_factory = sqlite3.Row
                result = db.execute('SELECT * FROM results').fetchone()
                return dict(result) if result else None
        except sqlite3.OperationalError:
            return None

    def economy():
        with psycopg.connect(**{**admin, 'dbname': database}) as db:
            return {'counts': list(db.execute('SELECT (SELECT count(*) FROM ledger),(SELECT count(*) FROM rewards),(SELECT count(*) FROM operations WHERE id LIKE \'match:%\')').fetchone()),
                    'wallets': [list(r) for r in db.execute('SELECT id,credits,xp FROM players ORDER BY id')],
                    'ledger': [list(r) for r in db.execute('SELECT player_id,amount,balance_after,reason,reference FROM ledger ORDER BY player_id')],
                    'rewards': [list(r) for r in db.execute('SELECT player_id,details FROM rewards ORDER BY player_id')]}

    def database_available(enabled):
        with psycopg.connect(**admin) as db:
            db.execute(sql.SQL('ALTER DATABASE {} ALLOW_CONNECTIONS {}').format(sql.Identifier(database), sql.SQL('true' if enabled else 'false')))
            if not enabled:
                db.execute('SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname=%s', (database,))

    def checkpoint(label, economy_snapshot=None):
        current_row = row()
        if current_row:
            for column in ('payload', 'response'):
                value = current_row[column]
                current_row[column + '_sha256'] = hashlib.sha256(value).hexdigest() if value else None
                current_row[column] = value.decode() if value else None
        receipt = {'at_utc': datetime.now(timezone.utc).isoformat(), 'wall_seconds': time.monotonic() - started,
                   'sqlite': current_row, 'economy': economy_snapshot,
                   'spool': [{'name': p.name, 'bytes': p.stat().st_size, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
                             for p in spool.glob('*.json')],
                   'processes': [{'name': name, 'pid': child.pid, 'returncode': child.poll()} for name, child in processes]}
        (out / (label + '.json')).write_text(json.dumps(receipt, indent=2) + '\n')

    class LostAck(BaseHTTPRequestHandler):
        def do_POST(self):
            raw = self.rfile.read(int(self.headers['Content-Length']))
            forwarded.append(hashlib.sha256(raw).hexdigest())
            req = urllib.request.Request(env['SIGHTBREAK_TEST_ECONOMY_URL'] + '/server/matches', raw,
                                         {'Content-Type': 'application/json', 'X-Server-Key': key})
            with urllib.request.urlopen(req, timeout=10) as response: body = response.read()
            committed.set()
            release.wait(timeout=30)
            try:
                self.send_response(200)
                self.end_headers()
                self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError): pass

        def log_message(self, *_args): pass

    try:
        save()
        subprocess.run(DOCKER + ['run', '--pull=never', '--rm', '-d', '--name', container,
                                '-p', '127.0.0.1::5432', '-e', 'POSTGRES_USER=sightbreak',
                                '-e', 'POSTGRES_PASSWORD=' + password, '-e', 'POSTGRES_DB=' + database, IMAGE],
                       env=env, check=True, stdout=subprocess.DEVNULL)
        container_owned = True
        port_text = subprocess.check_output(DOCKER + ['port', container, '5432/tcp'], env=env, text=True)
        db_port = int(port_text.strip().rsplit(':', 1)[1])
        report['postgres_port'] = db_port
        admin = dict(host='127.0.0.1', port=db_port, user='sightbreak', password=password, dbname='postgres', autocommit=True)

        def postgres_ready():
            try:
                with psycopg.connect(**admin): return True
            except psycopg.OperationalError: return False

        wait_for(postgres_ready, 'owned PostgreSQL startup')
        env['DATABASE_URL'] = f'postgresql+psycopg://sightbreak:{password}@127.0.0.1:{db_port}/{database}'
        migration = start('migration', [str(args.python), 'backend/migrate.py'])
        assert migration.wait(timeout=30) == 0, 'Migration failed; see migration.log'
        start('api', [str(args.python), '-m', 'uvicorn', 'app:app', '--app-dir', 'backend', '--host', '127.0.0.1', '--port', str(api_port)])
        wait_for(lambda: 'Application startup complete' in (out / 'api.log').read_text(), 'API startup')
        for index in range(10):
            account = request('/auth/register', {'username': 'match_' + secrets.token_hex(6),
                              'password': secrets.token_urlsafe(24), 'display_name': f'Account Match {index}'})
            accounts.append(account)
        identities = [a['player_id'] for a in accounts]
        assert len(set(identities)) == 10
        report['initial_economy'] = economy()
        assert report['initial_economy']['counts'] == [0, 0, 0]
        assert all(w[1:] == [0, 0] for w in report['initial_economy']['wallets'])
        command = [str(ROOT / 'scripts/godot.sh'), '--headless', '--max-fps', '60', '--script', 'res://tests/account_match_probe.gd', '--',
                   '--port=' + str(game_port), '--control=' + str(control)]
        server = start('server', command + ['--role=server', '--output=' + str(out / 'server.json')])
        wait_for(lambda: 'SIGHTBREAK_SERVER_READY' in (out / 'server.log').read_text(), 'server readiness', 60)
        clients = []
        for index, account in enumerate(accounts):
            # Tickets expire in 60 seconds. Mint immediately before each actual
            # admission so slow engine startup cannot age later clients' tickets.
            ticket = request('/auth/game-ticket', {'server_id': 'local-relay'}, account['token'])['ticket']
            child_env = env.copy()
            child_env.pop('SIGHTBREAK_SERVER_KEY')
            child_env.pop('SIGHTBREAK_RESULT_SPOOL')
            child_env.pop('DATABASE_URL')
            child_env['SIGHTBREAK_JOIN_TICKET'] = ticket
            name = 'client-' + str(index)
            clients.append(start(name, command + ['--role=client', '--output=' + str(out / (name + '.json'))], child_env))
            wait_for(lambda: 'ACCOUNT_MATCH_ADMITTED ' + str(index + 1) + '\n' in (out / (name + '.log')).read_text(), name + ' exact actor admission', 60)
        with psycopg.connect(**{**admin, 'dbname': database}) as db:
            consumed = list(db.execute('SELECT player_id,server_id,consumed_at IS NOT NULL FROM game_tickets ORDER BY player_id'))
        assert len(consumed) == 10 and {r[0] for r in consumed} == set(identities)
        assert all(r[1:] == ('local-relay', True) for r in consumed)
        report['consumed_tickets'] = [list(r) for r in consumed]
        report['checks']['ten_authenticated_admissions'] = True
        save()
        deadline = time.monotonic() + args.timeout
        last_progress = ''
        while time.monotonic() < deadline:
            observed = read_report(out / 'server.json').get('latest', {})
            progress = f"round={observed.get('round')} phase={observed.get('phase')} objective={observed.get('objective')} reward={observed.get('reward_status')}"
            if progress != last_progress:
                print(progress, flush=True)
                last_progress = progress
            assert server.poll() is None and all(c.poll() is None for c in clients), 'Godot exited before completion; see logs'
            assert observed.get('reward_status') not in ('ineligible_match', 'submission_failed'), progress
            if observed.get('reward_status') == 'queued_for_delivery' and all(read_report(out / f'client-{i}.json').get('latest', {}).get('reward_status') == 'queued_for_delivery' for i in range(10)):
                break
            time.sleep(.2)
        else:
            raise AssertionError('Stock match incomplete within wall deadline; retained latest state and transitions')
        server_report = read_report(out / 'server.json')
        client_reports = [read_report(out / f'client-{i}.json') for i in range(10)]
        verify_match(server_report, client_reports, identities)
        # Preserve the completion boundary separately from post-SIGKILL disconnects.
        (out / 'completed-server.json').write_text(json.dumps(server_report, indent=2) + '\n')
        for index, client_report in enumerate(client_reports):
            (out / f'completed-client-{index}.json').write_text(json.dumps(client_report, indent=2) + '\n')
        report['checks']['stock_match_completed'] = True
        files = list(spool.glob('*.json'))
        assert len(files) == 1
        raw = files[0].read_bytes()
        payload = json.loads(raw)
        verify_earned_payload(payload, server_report, client_reports)
        assert payload['match_id'] == server_report['latest']['match_id']
        assert {p['player_id'] for p in payload['participants']} == set(identities)
        assert sum(p['won'] for p in payload['participants']) == 5
        report['match_id'] = payload['match_id']
        report['earned_payload_sha256'] = hashlib.sha256(raw).hexdigest()
        (out / 'earned-result.json').write_bytes(raw)
        (out / 'earned-result.json').chmod(0o600)
        # No worker ran during gameplay: the game process is killed after its real
        # earned handoff, before any backend grant. Nothing can recompute a result.
        assert economy() == report['initial_economy']
        checkpoint('earned-staged', economy())
        server.kill()
        assert server.wait(timeout=10) == -signal.SIGKILL
        checkpoint('earned-godot-killed', economy())
        control.touch()
        for client in clients: assert client.wait(timeout=20) == 0
        report['checks']['godot_sigkill_after_earned_handoff'] = True
        worker_cmd = [str(args.python), 'server/result_outbox.py', '--database', str(sqlite_path), '--spool', str(spool)]
        database_available(False)
        outage = start('worker-outage', worker_cmd + ['--backend=' + env['SIGHTBREAK_TEST_ECONOMY_URL']])
        wait_for(lambda: row() is not None and row()['attempts'] >= 1, 'owned database outage retry')
        assert row()['state'] == 'pending' and row()['status'] == 500 and not list(spool.glob('*.json'))
        checkpoint('database-outage-pending')
        outage.kill()
        outage.wait(timeout=10)
        database_available(True)
        assert economy() == report['initial_economy']
        checkpoint('database-restored-zero', economy())
        report['checks']['database_outage_durable_pending'] = True
        proxy = ThreadingHTTPServer(('127.0.0.1', 0), LostAck)
        threading.Thread(target=proxy.serve_forever, daemon=True).start()
        lost = start('worker-lost-ack', worker_cmd + ['--backend=http://127.0.0.1:' + str(proxy.server_port)])
        assert committed.wait(timeout=30), 'Backend did not commit earned match'
        before = economy()
        assert before['counts'] == [10, 10, 1] and row()['state'] == 'pending'
        checkpoint('backend-committed-ack-held', before)
        lost.kill()
        assert lost.wait(timeout=10) == -signal.SIGKILL
        checkpoint('lost-ack-worker-killed', economy())
        release.set()
        restart = start('worker-restart', worker_cmd + ['--backend=' + env['SIGHTBREAK_TEST_ECONOMY_URL'], '--once'])
        assert restart.wait(timeout=30) == 0 and row()['state'] == 'committed'
        assert economy() == before and json.loads(row()['payload']) == payload and row()['fingerprint'] == forwarded[0]
        checkpoint('worker-restarted-committed', economy())
        report['checks']['lost_ack_worker_sigkill_exact_restart'] = True
        files[0].write_bytes(raw)
        replay = start('worker-replay', worker_cmd + ['--backend=' + env['SIGHTBREAK_TEST_ECONOMY_URL'], '--once'])
        assert replay.wait(timeout=30) == 0 and economy() == before and not list(spool.glob('*.json'))
        checkpoint('duplicate-replayed-unchanged', economy())
        report['checks']['duplicate_spool_no_second_grant'] = True
        rewards = {r[0]: r[1] for r in before['rewards']}
        participants = {p['player_id']: p for p in payload['participants']}
        config = json.loads((ROOT / 'backend/config/economy.json').read_text())
        for identity, credits, xp in before['wallets']:
            participant = participants[identity]
            expected_xp = config['xp_per_match'] + config['xp_per_win'] * participant['won'] + config['xp_per_objective'] * participant['objective_contributions']
            expected_credits = config['match_completion'] + config['match_win'] * participant['won'] + config['daily_first'] + config['level_reward'] * int((expected_xp / config['xp_level_base']) ** .5)
            assert (credits, xp) == (expected_credits, expected_xp)
            assert rewards[identity]['eligible'] and rewards[identity]['credits'] == credits and rewards[identity]['xp'] == xp
            ledger = next(r for r in before['ledger'] if r[0] == identity)
            assert ledger[1:] == [credits, credits, 'verified_match', payload['match_id']]
        report['final_economy'] = before
        report['http_profiles'] = [request('/me', token=a['token']) for a in accounts]
        assert sorted((p['player_id'], p['credits'], p['xp']) for p in report['http_profiles']) == [tuple(w) for w in before['wallets']]
        assert all(len(request('/history', token=a['token'])['matches']) == 1 for a in accounts)
        assert key.encode() not in row()['payload'] and key.encode() not in sqlite_path.read_bytes()
        assert report['source_commit'] == subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
        assert not subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, text=True).strip()
        assert all(hashlib.sha256((ROOT / p).read_bytes()).hexdigest() == digest for p, digest in report['sha256'].items())
        report['checks']['earned_rates_wallet_ledger_history_agree'] = True
        report['status'] = 'passed'
    except BaseException as error:
        report['status'] = 'failed'
        report['failure'] = type(error).__name__ + ': ' + str(error)
        raise
    finally:
        release.set()
        if proxy:
            proxy.shutdown()
            proxy.server_close()
        control.touch()
        for _, child in processes:
            if child.poll() is None: child.terminate()
        for _, child in processes:
            try: child.wait(timeout=10)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait(timeout=10)
        for log in logs: log.close()
        report['cleanup']['children_reaped'] = all(p.poll() is not None for _, p in processes)
        report['process_exits'] = [{'name': name, 'pid': child.pid, 'returncode': child.returncode} for name, child in processes]
        errors = [name for name, _ in processes if (name == 'server' or name.startswith('client-')) and
                  any(marker in (out / (name + '.log')).read_text() for marker in ('SCRIPT ERROR', 'ERROR:', 'Parse Error'))]
        report['godot_errors'] = errors
        if errors and report['status'] == 'passed':
            report['status'] = 'failed'
            report['failure'] = 'Godot errors: ' + ', '.join(errors)
        if container_owned:
            removed = subprocess.run(DOCKER + ['rm', '-f', container], env=env, text=True, capture_output=True)
            report['cleanup']['owned_container_removed'] = removed.returncode == 0 or 'No such container' in removed.stderr
        report['wall_seconds'] = time.monotonic() - started
        report['finished_at_utc'] = datetime.now(timezone.utc).isoformat()
        if not all(report['cleanup'].values()): report['status'] = 'failed'
        save()
    assert report['status'] == 'passed', report.get('failure', 'Cleanup failed')
    print('ACCOUNT_MATCH_TEST passed:', out, flush=True)


if __name__ == '__main__':
    main()
