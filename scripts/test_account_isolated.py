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
ROOT = Path(__file__).resolve().parents[1]

def main():
    admin = dict(host='127.0.0.1', port=55432, user='sightbreak', password='sightbreak_local_only', dbname='postgres', autocommit=True)
    database = 'sightbreak_account_' + secrets.token_hex(6) + '_test'; service = None
    with psycopg.connect(**admin) as db: db.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(database)))
    env = os.environ.copy(); env['DATABASE_URL'] = 'postgresql+psycopg://sightbreak:sightbreak_local_only@127.0.0.1:55432/' + database
    env['SIGHTBREAK_SERVER_KEY'] = secrets.token_urlsafe(48); env['SIGHTBREAK_SERVER_ID'] = 'local-relay'
    with socket.socket() as sock: sock.bind(('127.0.0.1', 0)); port = sock.getsockname()[1]
    env['SIGHTBREAK_TEST_ECONOMY_URL'] = f'http://127.0.0.1:{port}'
    try:
        subprocess.run([str(ROOT / '.venv/bin/python'), 'backend/migrate.py'], env=env, cwd=ROOT, check=True, stdout=subprocess.DEVNULL)
        with tempfile.TemporaryFile(mode='w+') as log:
            service = subprocess.Popen([str(ROOT / '.venv/bin/python'), '-m', 'uvicorn', 'app:app', '--app-dir', 'backend', '--host', '127.0.0.1', '--port', str(port)], env=env, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
            for _ in range(150):
                log.seek(0)
                if 'Application startup complete' in log.read(): break
                if service.poll() is not None: raise RuntimeError('isolated API failed')
                time.sleep(.05)
            else: raise RuntimeError('isolated API timeout')
            subprocess.run([str(ROOT / '.venv/bin/python'), 'scripts/test_account_network.py'], env=env, cwd=ROOT, check=True, timeout=120)
    finally:
        if service is not None:
            service.terminate()
            try: service.wait(timeout=10)
            except subprocess.TimeoutExpired: service.kill(); service.wait()
        with psycopg.connect(**admin) as db: db.execute(sql.SQL('DROP DATABASE {} WITH (FORCE)').format(sql.Identifier(database)))

if __name__ == '__main__': main()
