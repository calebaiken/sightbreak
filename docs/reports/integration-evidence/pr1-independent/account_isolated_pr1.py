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
ROOT = Path('/workspace/sightbreak-pr1-current')
LOGDIR = Path('/workspace/reviews/integration-20261013/pr1-independent')

def main():
    admin = dict(host='127.0.0.1', port=55432, user='sightbreak', password='sightbreak_local_only', dbname='postgres', autocommit=True)
    database = 'sightbreak_account_' + secrets.token_hex(6) + '_test'; service = None
    with psycopg.connect(**admin) as db: db.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(database)))
    env = os.environ.copy(); env['DATABASE_URL'] = 'postgresql+psycopg://sightbreak:sightbreak_local_only@127.0.0.1:55432/' + database
    env['SIGHTBREAK_SERVER_KEY'] = secrets.token_urlsafe(48); env['SIGHTBREAK_SERVER_ID'] = 'local-relay'
    port = 8080
    key_file = ROOT / '.local/secrets/server.key'
    key_file.parent.mkdir(parents=True, exist_ok=True)
    if key_file.exists(): raise RuntimeError('Refuse to overwrite existing reviewer key')
    key_file.write_text(env['SIGHTBREAK_SERVER_KEY'])
    key_file.chmod(0o600)
    env['SIGHTBREAK_TEST_ECONOMY_URL'] = f'http://127.0.0.1:{port}'
    try:
        subprocess.run(['/workspace/sightbreak/.venv/bin/python', 'backend/migrate.py'], env=env, cwd=ROOT, check=True, stdout=subprocess.DEVNULL)
        with (LOGDIR / 'account-pr1-backend.log').open('w+') as log:
            service = subprocess.Popen(['/workspace/sightbreak/.venv/bin/python', '-m', 'uvicorn', 'app:app', '--app-dir', 'backend', '--host', '127.0.0.1', '--port', str(port)], env=env, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
            for _ in range(150):
                log.seek(0)
                if 'Application startup complete' in log.read(): break
                if service.poll() is not None: raise RuntimeError('isolated API failed')
                time.sleep(.05)
            else: raise RuntimeError('isolated API timeout')
            subprocess.run(['/workspace/sightbreak/.venv/bin/python', '-c', "import runpy, tempfile; tempfile.TemporaryFile=lambda *a, **k: open('/workspace/reviews/integration-20261013/pr1-independent/account-pr1-godot-server.log', 'w+'); runpy.run_path('scripts/test_account_network.py', run_name='__main__')"], env=env, cwd=ROOT, check=True, timeout=120)
    finally:
        key_file.unlink(missing_ok=True)
        if service is not None:
            service.terminate()
            try: service.wait(timeout=10)
            except subprocess.TimeoutExpired: service.kill(); service.wait()
        with psycopg.connect(**admin) as db: db.execute(sql.SQL('DROP DATABASE {} WITH (FORCE)').format(sql.Identifier(database)))

if __name__ == '__main__': main()
