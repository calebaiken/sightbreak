#!/usr/bin/env python3
"""Isolated PostgreSQL + HTTP + real Godot: capacity/duplicate rejection preserves tickets."""
from pathlib import Path
import hashlib
import json
import os
import secrets
import subprocess
import tempfile
import time
import urllib.request
import psycopg
from psycopg import sql

ROOT = Path(__file__).resolve().parents[1]

def main():
    admin = dict(host='127.0.0.1', port=55432, user='sightbreak', password='sightbreak_local_only', dbname='postgres', autocommit=True)
    database = 'sightbreak_capacity_' + secrets.token_hex(4) + '_test'
    out = ROOT / '.local' / 'validation' / ('capacity-' + secrets.token_hex(4))
    out.mkdir(parents=True)
    processes, logs = [], []
    with psycopg.connect(**admin) as db:
        db.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(database)))
    env = os.environ.copy()
    env['DATABASE_URL'] = 'postgresql+psycopg://sightbreak:sightbreak_local_only@127.0.0.1:55432/' + database
    env['SIGHTBREAK_SERVER_KEY'] = secrets.token_urlsafe(48)
    env['SIGHTBREAK_SERVER_ID'] = 'local-relay'

    def start(name, command, child_env):
        log = (out / (name + '.log')).open('w'); logs.append(log)
        child = subprocess.Popen(command, cwd=ROOT, env=child_env, stdout=log, stderr=subprocess.STDOUT)
        processes.append((name, child))
        return child

    def wait_text(name, text):
        for _ in range(150):
            data = (out / (name + '.log')).read_text()
            if text in data: return
            if 'ERROR:' in data: raise RuntimeError(name + ' logged error')
            time.sleep(.05)
        raise RuntimeError(name + ' did not produce ' + text)

    def post(path, payload, token=None):
        headers = {'Content-Type': 'application/json'}
        if token: headers['Authorization'] = 'Bearer ' + token
        request = urllib.request.Request('http://127.0.0.1:8182' + path, json.dumps(payload).encode(), headers)
        with urllib.request.urlopen(request, timeout=10) as response: return json.load(response)

    def consumed(ticket):
        with psycopg.connect(**{**admin, 'dbname': database}) as db:
            return db.execute('SELECT consumed_at IS NOT NULL FROM game_tickets WHERE ticket_hash=%s', (hashlib.sha256(ticket.encode()).hexdigest(),)).fetchone()[0]

    def client(name, ticket, expect, hold=False):
        control = out / (name + '.release')
        if not hold: control.touch()
        client_env = env.copy(); client_env.pop('SIGHTBREAK_SERVER_KEY'); client_env['SIGHTBREAK_JOIN_TICKET'] = ticket
        child = start(name, command + ['--role=client', '--expect=' + expect, '--control=' + str(control)], client_env)
        wait_text(name, 'CAPACITY_ADMITTED' if expect == 'admitted' else 'CAPACITY_REJECTED')
        if not hold: assert child.wait(timeout=8) == 0
        return child, control

    try:
        subprocess.run([str(ROOT / '.venv/bin/python'), 'backend/migrate.py'], env=env, cwd=ROOT, check=True, stdout=subprocess.DEVNULL)
        start('api', [str(ROOT / '.venv/bin/python'), '-m', 'uvicorn', 'app:app', '--app-dir', 'backend', '--host', '127.0.0.1', '--port', '8182'], env)
        wait_text('api', 'Application startup complete')
        account = post('/auth/register', {'username': 'capacity_' + secrets.token_hex(6), 'password': secrets.token_urlsafe(24), 'display_name': 'Capacity fixture'})
        ticket = post('/auth/game-ticket', {'server_id': 'local-relay'}, account['token'])['ticket']
        clear = out / 'capacity.release'
        command = [str(ROOT / 'scripts/godot.sh'), '--headless', '--max-fps', '60', '--script', 'res://tests/admission_capacity_probe.gd', '--', '--port=29910']
        start('server', command + ['--role=server', '--full', '--control=' + str(clear)], env)
        wait_text('server', 'SIGHTBREAK_SERVER_READY')
        client('full', ticket, 'rejected')
        assert not consumed(ticket), 'Full-server rejection consumed ticket'
        clear.touch(); time.sleep(.1)
        holder, release = client('holder', ticket, 'admitted', True)
        assert consumed(ticket)
        duplicate = post('/auth/game-ticket', {'server_id': 'local-relay'}, account['token'])['ticket']
        client('duplicate', duplicate, 'rejected')
        assert not consumed(duplicate), 'Duplicate-account rejection consumed ticket'
        release.touch(); assert holder.wait(timeout=8) == 0
        time.sleep(.3)
        client('reclaim', duplicate, 'admitted')
        assert consumed(duplicate)
        print('ADMISSION_CAPACITY_TEST full/duplicate rejection preserved tickets; same tickets subsequently admitted; consume/reclaim verified in PostgreSQL')
        print('Logs:', out)
    finally:
        for _, child in processes:
            if child.poll() is None: child.terminate()
        for _, child in processes:
            try: child.wait(timeout=8)
            except subprocess.TimeoutExpired: child.kill(); child.wait()
        for log in logs: log.close()
        errors = [name for name, _ in processes if name != 'api' and 'ERROR:' in (out / (name + '.log')).read_text()]
        with psycopg.connect(**admin) as db:
            db.execute(sql.SQL('DROP DATABASE {} WITH (FORCE)').format(sql.Identifier(database)))
        if errors: raise RuntimeError('Godot errors: ' + ', '.join(errors))

if __name__ == '__main__': main()
