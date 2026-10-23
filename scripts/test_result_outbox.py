#!/usr/bin/env python3
"""SIGKILL actual Godot/worker and interrupt an isolated PostgreSQL database.

Then lose the HTTP response after backend commit and restart with the exact result.
No physical play or power-loss claim. Requires local development Postgres and venv.
"""
from contextlib import closing
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import hashlib
import json
import os
import secrets
import signal
import sqlite3
import subprocess
import threading
import time
import urllib.request
from uuid import uuid4
import psycopg
from psycopg import sql

ROOT = Path(__file__).resolve().parents[1]

def main():
    admin = dict(host='127.0.0.1', port=55432, user='sightbreak', password='sightbreak_local_only', dbname='postgres', autocommit=True)
    database = 'sightbreak_outbox_' + secrets.token_hex(4) + '_test'
    out = ROOT / '.local/validation' / ('outbox-' + secrets.token_hex(4)); out.mkdir(parents=True)
    spool = out / 'spool'; spool.mkdir(mode=0o700)
    sqlite_path = out / 'results.sqlite'
    env = os.environ.copy(); env['DATABASE_URL'] = 'postgresql+psycopg://sightbreak:sightbreak_local_only@127.0.0.1:55432/' + database
    env['SIGHTBREAK_SERVER_KEY'] = secrets.token_urlsafe(48); env['SIGHTBREAK_RESULT_SPOOL'] = str(spool)
    processes, logs = [], []
    committed = threading.Event(); release = threading.Event(); forwarded = []
    proxy = None

    def start(name, command, environment=env):
        log = (out / (name + '.log')).open('w'); logs.append(log)
        child = subprocess.Popen(command, env=environment, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
        processes.append((name, child)); return child
    def wait_for(predicate, label, timeout=20):
        until = time.monotonic() + timeout
        while time.monotonic() < until:
            if predicate(): return
            time.sleep(.05)
        raise AssertionError('Timed out: ' + label)
    def row():
        if not sqlite_path.exists(): return None
        try:
            with closing(sqlite3.connect(sqlite_path)) as db:
                db.row_factory = sqlite3.Row
                result = db.execute('SELECT * FROM results').fetchone()
                return dict(result) if result else None
        except sqlite3.OperationalError: return None
    def toggle_database(enabled):
        with psycopg.connect(**admin) as db:
            db.execute(sql.SQL('ALTER DATABASE {} ALLOW_CONNECTIONS {}').format(sql.Identifier(database), sql.SQL('true' if enabled else 'false')))
            if not enabled: db.execute('SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname=%s', (database,))
    def counts():
        with psycopg.connect(**{**admin, 'dbname': database}) as db:
            return db.execute('SELECT (SELECT count(*) FROM ledger),(SELECT count(*) FROM rewards),(SELECT sum(credits) FROM players)').fetchone()

    class LostAck(BaseHTTPRequestHandler):
        def do_POST(self):
            raw = self.rfile.read(int(self.headers['Content-Length']))
            forwarded.append(hashlib.sha256(raw).hexdigest())
            request = urllib.request.Request('http://127.0.0.1:8183/server/matches', raw, {'Content-Type': 'application/json', 'X-Server-Key': env['SIGHTBREAK_SERVER_KEY']})
            with urllib.request.urlopen(request, timeout=10) as response: body = response.read()
            committed.set(); release.wait(timeout=20)
            try:
                self.send_response(200); self.end_headers(); self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError): pass
        def log_message(self, *_args): pass

    with psycopg.connect(**admin) as db: db.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(database)))
    try:
        subprocess.run([str(ROOT / '.venv/bin/python'), 'backend/migrate.py'], cwd=ROOT, env=env, check=True, stdout=subprocess.DEVNULL)
        player_ids = [str(uuid4()) for _ in range(10)]
        with psycopg.connect(**{**admin, 'dbname': database}) as db:
            for index, identity in enumerate(player_ids):
                db.execute('INSERT INTO players(id,username,display_name,password_hash,credits,xp,active) VALUES(%s,%s,%s,%s,0,0,true)', (identity, 'outbox_' + str(index), 'Outbox fixture', 'fixture-login-disabled'))
        fixture = out / 'fixture.json'; fixture.write_text(json.dumps({'player_ids': player_ids})); fixture.chmod(0o600)
        start('api', [str(ROOT / '.venv/bin/python'), '-m', 'uvicorn', 'app:app', '--app-dir', 'backend', '--host', '127.0.0.1', '--port', '8183'])
        wait_for(lambda: 'Application startup complete' in (out / 'api.log').read_text(), 'API startup')
        game = start('godot', [str(ROOT / 'scripts/godot.sh'), '--headless', '--script', 'res://tests/result_outbox_crash_probe.gd', '--', '--fixture=' + str(fixture)])
        wait_for(lambda: 'OUTBOX_GAME_STAGED' in (out / 'godot.log').read_text(), 'Godot durable handoff')
        raw = next(spool.glob('*.json')).read_bytes(); original = json.loads(raw)
        game.kill(); assert game.wait(timeout=5) == -signal.SIGKILL
        toggle_database(False)
        worker_cmd = ['python3', str(ROOT / 'server/result_outbox.py'), '--database', str(sqlite_path), '--spool', str(spool)]
        outage = start('worker-outage', worker_cmd + ['--backend=http://127.0.0.1:8183'])
        wait_for(lambda: row() is not None and row()['attempts'] >= 1, 'actual database outage retry')
        assert row()['state'] == 'pending' and row()['status'] == 500 and not list(spool.glob('*.json'))
        outage.kill(); outage.wait(timeout=5)
        toggle_database(True)
        proxy = ThreadingHTTPServer(('127.0.0.1', 8184), LostAck)
        threading.Thread(target=proxy.serve_forever, daemon=True).start()
        lost = start('worker-lost-ack', worker_cmd + ['--backend=http://127.0.0.1:8184'])
        assert committed.wait(timeout=20), 'Backend did not commit before response loss'
        before = counts(); assert before[0:2] == (10, 10) and before[2] > 0
        assert row()['state'] == 'pending'
        lost.kill(); lost.wait(timeout=5); release.set()
        restart = start('worker-restart', worker_cmd + ['--backend=http://127.0.0.1:8183', '--once'])
        assert restart.wait(timeout=20) == 0
        assert row()['state'] == 'committed' and counts() == before
        assert json.loads(row()['payload']) == original and row()['fingerprint'] == forwarded[0]
        # A duplicate source file left around a crash cannot create another grant.
        (spool / (original['match_id'] + '.json')).write_bytes(raw)
        replay = start('worker-replay', worker_cmd + ['--backend=http://127.0.0.1:8183', '--once'])
        assert replay.wait(timeout=20) == 0 and counts() == before
        assert not list(spool.glob('*.json'))
        assert b'SIGHTBREAK_SERVER_KEY' not in row()['payload'] and env['SIGHTBREAK_SERVER_KEY'].encode() not in sqlite_path.read_bytes()
        print('RESULT_OUTBOX_CRASH_TEST passed: Godot SIGKILL after handoff, actual isolated database outage, worker SIGKILL, lost acknowledgment after commit, restart and duplicate spool replay; exactly10 grants/10 rewards with unchanged wallets and payload')
        print('Logs:', out)
    finally:
        release.set()
        if proxy: proxy.shutdown(); proxy.server_close()
        for _, child in processes:
            if child.poll() is None: child.terminate()
        for _, child in processes:
            try: child.wait(timeout=10)
            except subprocess.TimeoutExpired: child.kill(); child.wait()
        for log in logs: log.close()
        with psycopg.connect(**admin) as db: db.execute(sql.SQL('DROP DATABASE {} WITH (FORCE)').format(sql.Identifier(database)))

if __name__ == '__main__': main()
