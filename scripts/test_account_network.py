#!/usr/bin/env python3
"""Real Godot -> HTTP -> PostgreSQL join-ticket bridge against the local development API.
Creates one fictional account. Does not grant rewards. Requires dev-api.sh already running.
The server credential is read from the ignored local secret file and never logged.
"""
from pathlib import Path
import json
import os
import secrets
import subprocess
import tempfile
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
API_URL = os.environ.get('SIGHTBREAK_TEST_ECONOMY_URL', 'http://127.0.0.1:8080')

def post(path, data, token=None):
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = 'Bearer ' + token
    request = urllib.request.Request(API_URL + path, json.dumps(data).encode(), headers)
    with urllib.request.urlopen(request, timeout=10) as response:
        return json.load(response)


def main():
    session = post('/auth/register', {'username': 'bridge_' + secrets.token_hex(6), 'password': secrets.token_urlsafe(24), 'display_name': 'Account bridge QA'})
    ticket = post('/auth/game-ticket', {'server_id': 'local-relay'}, session['token'])['ticket']
    env = os.environ.copy()
    env.pop('SIGHTBREAK_SERVER_KEY', None)
    server_env = env.copy()
    server_env['SIGHTBREAK_SERVER_KEY'] = os.environ.get('SIGHTBREAK_SERVER_KEY') or (ROOT / '.local/secrets/server.key').read_text().strip()
    command = [str(ROOT / 'scripts/godot.sh'), '--headless', '--script', 'res://tests/account_network_probe.gd', '--']
    with tempfile.TemporaryFile(mode='w+') as log:
        server = subprocess.Popen(command + ['--role=server'], cwd=ROOT, env=server_env, stdout=log, stderr=subprocess.STDOUT)
        try:
            for _ in range(80):
                log.seek(0)
                if 'SIGHTBREAK_SERVER_READY' in log.read():
                    break
                if server.poll() is not None:
                    raise RuntimeError('Account server exited during startup')
                time.sleep(0.1)
            for role in ('guest', 'mismatch', 'client', 'replay', 'reclaim'):
                client_env = env.copy()
                if role == 'reclaim':
                    ticket = post('/auth/game-ticket', {'server_id': 'local-relay'}, session['token'])['ticket']
                client_env['SIGHTBREAK_JOIN_TICKET'] = ticket
                result = subprocess.run(command + ['--role=' + ('client' if role == 'reclaim' else role)], cwd=ROOT, env=client_env, text=True, capture_output=True, timeout=18)
                print(result.stdout, end='')
                if result.returncode or 'FAIL' in result.stdout or 'ERROR:' in result.stderr:
                    print(result.stderr)
                    raise RuntimeError('Account network assertion failed for ' + role)
            print('ACCOUNT_NETWORK_TEST: guest rejection, incompatible-protocol rejection without ticket or slot use, authenticated identity, waiting roster, replay rejection, account reclaim passed')
        finally:
            server.terminate()
            server.wait(timeout=10)
            log.seek(0)
            server_output = log.read()
            if 'ERROR:' in server_output:
                print(server_output)
                raise RuntimeError('Server emitted an error')

if __name__ == '__main__':
    main()
