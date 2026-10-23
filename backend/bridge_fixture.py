"""Reproducible isolated Godot reward bridge fixture. Never targets the live DB.

Run backend/dev-db.sh first, then:
  .venv/bin/python backend/bridge_fixture.py --serve
Stop the isolated 8081 service before requesting --reset for another clean run.
Credentials stay in ignored .local/bridge-fixture.json mode 0600, never stdout.
"""
import argparse
import json
import os
from pathlib import Path
import secrets
import socket
import sys

import psycopg
from psycopg.errors import DuplicateDatabase

ROOT = Path(__file__).resolve().parents[1]
DB_NAME = 'sightbreak_bridge_test'
DB_URL = 'postgresql+psycopg://sightbreak:sightbreak_local_only@127.0.0.1:55432/' + DB_NAME
FIXTURE = ROOT / '.local/bridge-fixture.json'

def prepare(reset=False):
    if reset:
        with socket.socket() as probe:
            if probe.connect_ex(('127.0.0.1', 8081)) == 0:
                raise SystemExit('Stop the isolated port 8081 API before resetting its fixture')
    with psycopg.connect(host='127.0.0.1', port=55432, user='sightbreak',
                         password='sightbreak_local_only', dbname='postgres', autocommit=True) as connection:
        try:
            connection.execute('CREATE DATABASE sightbreak_bridge_test')
        except DuplicateDatabase:
            pass
    os.environ['DATABASE_URL'] = DB_URL
    from app import engine, transaction
    from models import Base, Player
    from sqlalchemy import text
    assert engine.url.database == DB_NAME
    Base.metadata.create_all(engine)
    with engine.begin() as connection:
        for migration in sorted((ROOT / 'backend/migrations').glob('*.sql')):
            connection.exec_driver_sql(migration.read_text())
        if reset:
            connection.execute(text('TRUNCATE ' + ', '.join('"' + t + '"' for t in Base.metadata.tables) + ' CASCADE'))
    if reset:
        FIXTURE.unlink(missing_ok=True)
    if FIXTURE.exists():
        fixture = json.loads(FIXTURE.read_text())
        if fixture.get('database_url') != DB_URL:
            raise SystemExit('Existing fixture database mismatch; refusing to reuse')
        return fixture
    ids = []
    with transaction() as db:
        for index in range(10):
            player = Player(username=f'bridge_fixture_{index}', display_name=f'Bridge Fixture {index}',
                            password_hash='fixture-login-disabled')
            db.add(player)
            db.flush()
            ids.append(player.id)
    fixture = {'server_key': secrets.token_urlsafe(48), 'server_id': 'local-relay',
               'api_url': 'http://127.0.0.1:8081', 'database_url': DB_URL, 'player_ids': ids}
    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(FIXTURE, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, 'w') as output:
        json.dump(fixture, output)
    return fixture

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reset', action='store_true', help='Clear only dedicated sightbreak_bridge_test fixture')
    parser.add_argument('--serve', action='store_true', help='Serve isolated test API on loopback port 8081')
    args = parser.parse_args()
    fixture = prepare(args.reset)
    print('Isolated bridge fixture ready; credentials retained only in .local/bridge-fixture.json', flush=True)
    if args.serve:
        os.environ['SIGHTBREAK_SERVER_KEY'] = fixture['server_key']
        os.environ['SIGHTBREAK_SERVER_ID'] = fixture['server_id']
        python = str(ROOT / '.venv/bin/python')
        os.execv(python, [python, '-m', 'uvicorn', 'app:app', '--app-dir', str(ROOT / 'backend'),
                         '--host', '127.0.0.1', '--port', '8081'])
