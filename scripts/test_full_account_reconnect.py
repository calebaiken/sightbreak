#!/usr/bin/env python3
"""Ten real account clients, isolated PostgreSQL/HTTP, lost-close recovery.

Only temporary fixture identities and credentials. No public service or rewards
are created. Client processes never inherit the dedicated-server signing key.
"""
import argparse
import json
import os
from pathlib import Path
import secrets
import subprocess
import tempfile
import time
import urllib.request

import psycopg
from psycopg import sql

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    database = 'sightbreak_reconnect_' + secrets.token_hex(6) + '_test'
    connection = dict(host='127.0.0.1', port=55432, user='sightbreak',
                      password='sightbreak_local_only', dbname='postgres', autocommit=True)
    env = dict(os.environ, DATABASE_URL='postgresql+psycopg://sightbreak:sightbreak_local_only@127.0.0.1:55432/' + database,
               SIGHTBREAK_SERVER_KEY=secrets.token_urlsafe(48), SIGHTBREAK_SERVER_ID='local-relay',
               SIGHTBREAK_TEST_ECONOMY_URL='http://127.0.0.1:8185')
    env.pop('SIGHTBREAK_RESULT_SPOOL', None)
    api = None
    with psycopg.connect(**connection) as db:
        db.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(database)))

    def post(path, payload, token=None):
        headers = {'Content-Type': 'application/json'}
        if token:
            headers['Authorization'] = 'Bearer ' + token
        request = urllib.request.Request(env['SIGHTBREAK_TEST_ECONOMY_URL'] + path,
                                         json.dumps(payload).encode(), headers)
        with urllib.request.urlopen(request, timeout=10) as response:
            return json.load(response)

    try:
        with (out / 'migrate.log').open('w') as log:
            subprocess.run([str(ROOT / '.venv/bin/python'), 'backend/migrate.py'], cwd=ROOT,
                           env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
        with (out / 'api.log').open('w') as api_log, tempfile.TemporaryDirectory(prefix='sightbreak-tickets-') as private:
            api = subprocess.Popen([str(ROOT / '.venv/bin/python'), '-m', 'uvicorn', 'app:app',
                                    '--app-dir', 'backend', '--host', '127.0.0.1', '--port', '8185'],
                                   cwd=ROOT, env=env, stdout=api_log, stderr=subprocess.STDOUT)
            deadline = time.monotonic() + 15
            while 'Application startup complete' not in (out / 'api.log').read_text():
                if api.poll() is not None or time.monotonic() >= deadline:
                    raise RuntimeError('isolated backend startup failed')
                time.sleep(.05)
            tickets = []
            expected_accounts = []
            for index in range(10):
                account = post('/auth/register', {'username': 'reconnect_' + secrets.token_hex(6),
                               'password': secrets.token_urlsafe(24), 'display_name': 'Account fixture ' + str(index)})
                expected_accounts.append(account['player_id'])
                tickets.append(post('/auth/game-ticket', {'server_id': 'local-relay'}, account['token'])['ticket'])
            ticket_file = Path(private) / 'tickets.json'
            ticket_file.write_text(json.dumps(tickets))
            ticket_file.chmod(0o600)
            command = ['python3', 'scripts/simulate_network.py', '--clients', '10', '--seconds', '22',
                       '--port', '33600', '--rtt-ms', '100', '--blackout-at', '7.8', '--blackout-seconds', '1.5',
                       '--reconnect-at', '8', '--no-prediction', '--account-tickets', str(ticket_file), '--out', str(out / 'network')]
            with (out / 'network.log').open('w') as log:
                result = subprocess.run(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=150)
            summary = json.loads((out / 'network/summary.json').read_text())
            server = json.loads((out / 'network/server.json').read_text())
            with psycopg.connect(**{**connection, 'dbname': database}) as db:
                ticket_count, consumed = db.execute('SELECT count(*), count(consumed_at) FROM game_tickets').fetchone()
                rewards = db.execute('SELECT count(*) FROM rewards').fetchone()[0]
                balances = db.execute('SELECT sum(credits) FROM players').fetchone()[0]
                ledger = db.execute('SELECT count(*) FROM ledger').fetchone()[0]
            ownership_preserved = True
            for index, account_id in enumerate(expected_accounts):
                client = json.loads((out / f'network/client-{index}.json').read_text())
                ownership_preserved &= server['initial_accounts'].get(str(client['initial_id'])) == account_id
                ownership_preserved &= server['final_accounts'].get(str(client['final_id'])) == account_id
            checks = {
                'each_ticket_retains_its_exact_account_and_actor': ownership_preserved,
                'all_ten_recovered_with_fresh_authority': result.returncode == 0 and not summary['failures'],
                'ten_distinct_account_bindings': server['account_count'] == 10 and len(set(server['account_ids'])) == 10,
                'one_ticket_per_initial_admission': ticket_count == 10 and consumed == 10,
                'ranked_disconnect_policy_preserved': server['ranked_started'] and not server['ranked_eligible'] and server['reward_status'] == 'ineligible_disconnect',
                'no_unexpected_issuance_during_recovery': rewards == 0 and balances == 0 and ledger == 0,
                'bounded_transports': summary['max_enet_occupancy'] <= 10,
            }
            report = {'source': summary['source'], 'checks': checks, 'ticket_rows': ticket_count,
                      'consumed_tickets': consumed, 'reward_rows': rewards, 'total_credits': balances,
                      'scope': 'ten real Godot clients; local PostgreSQL/HTTP; synthetic100msRTT+lostclose; no devices'}
            (out / 'results.json').write_text(json.dumps(report, indent=2) + '\n')
            print(json.dumps(report, indent=2))
            return 0 if all(checks.values()) else 1
    finally:
        if api is not None:
            api.terminate()
            try:
                api.wait(timeout=10)
            except subprocess.TimeoutExpired:
                api.kill()
                api.wait()
        with psycopg.connect(**connection) as db:
            db.execute(sql.SQL('DROP DATABASE {} WITH (FORCE)').format(sql.Identifier(database)))


if __name__ == '__main__':
    raise SystemExit(main())
