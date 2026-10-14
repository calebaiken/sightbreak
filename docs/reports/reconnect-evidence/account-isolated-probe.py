#!/usr/bin/env python3
"""Protocol/account ticket matrix against a fresh current backend and isolated PG."""
import os
from pathlib import Path
import secrets
import socket
import subprocess
import tempfile
import time
import urllib.request
import psycopg
from psycopg import sql
ROOT = Path('/workspace/sightbreak-reconnect')

def main():
    admin = dict(host='127.0.0.1', port=55432, user='sightbreak', password='sightbreak_local_only', dbname='postgres', autocommit=True)
    database = 'sightbreak_account_' + secrets.token_hex(6) + '_test'; service = None
    with psycopg.connect(**admin) as db: db.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(database)))
    env = os.environ.copy(); env['DATABASE_URL'] = 'postgresql+psycopg://sightbreak:sightbreak_local_only@127.0.0.1:55432/' + database
    env['SIGHTBREAK_SERVER_KEY'] = secrets.token_urlsafe(48); env['SIGHTBREAK_SERVER_ID'] = 'local-relay'
    port = 8080  # PR5 baseline probes use this fixed loopback endpoint.
    env['SIGHTBREAK_TEST_ECONOMY_URL'] = f'http://127.0.0.1:{port}'
    secret_path = ROOT / '.local/secrets/server.key'
    owned_secret = False
    try:
        secret_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with secret_path.open('x') as secret:
            owned_secret = True
            secret_path.chmod(0o600)
            secret.write(env['SIGHTBREAK_SERVER_KEY'])
        subprocess.run([str(ROOT / '.venv/bin/python'), 'backend/migrate.py'], env=env, cwd=ROOT, check=True, stdout=subprocess.DEVNULL)
        with tempfile.TemporaryFile(mode='w+') as log:
            service = subprocess.Popen([str(ROOT / '.venv/bin/python'), '-m', 'uvicorn', 'app:app', '--app-dir', 'backend', '--host', '127.0.0.1', '--port', str(port)], env=env, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
            for _ in range(150):
                if service.poll() is not None: raise RuntimeError('isolated API failed')
                try:
                    with urllib.request.urlopen(env['SIGHTBREAK_TEST_ECONOMY_URL'] + '/health', timeout=.5) as response:
                        if response.status == 200: break
                except (OSError, urllib.error.URLError): pass
                time.sleep(.05)
            else: raise RuntimeError('isolated API health timeout')
            subprocess.run([str(ROOT / '.venv/bin/python'), 'scripts/test_account_network.py'], env=env, cwd=ROOT, check=True, timeout=120)
    finally:
        if owned_secret: secret_path.unlink(missing_ok=True)
        if service is not None:
            service.terminate()
            try: service.wait(timeout=10)
            except subprocess.TimeoutExpired: service.kill(); service.wait()
        with psycopg.connect(**admin) as db: db.execute(sql.SQL('DROP DATABASE {} WITH (FORCE)').format(sql.Identifier(database)))

if __name__ == '__main__': main()
