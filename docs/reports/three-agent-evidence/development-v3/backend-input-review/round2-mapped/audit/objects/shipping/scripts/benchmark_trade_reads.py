#!/usr/bin/env python3
"""Matched PostgreSQL trade-read measurement; Windows/Linux, no running API needed.

Set SIGHTBREAK_TEST_ADMIN_URL to a PostgreSQL admin URL. Only a newly created,
uniquely named *_test database is populated/dropped. --source selects the backend
under test; this script and its deterministic fixture stay fixed across revisions.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import platform
import secrets
import statistics
import subprocess
import sys
import time

import psycopg
from psycopg import sql
from sqlalchemy.engine import make_url

ROOT = Path(__file__).resolve().parents[1]


def sha256(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def identity(root):
    def git(*args):
        return subprocess.check_output(['git', *args], cwd=root, text=True).strip()
    return {'commit': git('rev-parse', 'HEAD'),
            'backend_tree': git('rev-parse', 'HEAD:backend'),
            'backend_dirty': git('status', '--porcelain', '--', 'backend'),
            'backend_files': {str(p.relative_to(root)).replace('\\', '/'): sha256(p)
                              for p in (root / 'backend').rglob('*')
                              if p.is_file() and p.suffix in ('.py', '.sql', '.toml', '.lock', '.json')
                              and '__pycache__' not in p.parts}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=ROOT)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--samples', type=int, default=10)
    args = parser.parse_args()
    if args.samples < 2:
        parser.error('--samples must be at least two')
    source = args.source.resolve()
    args.out.mkdir(parents=True, exist_ok=False)
    initial = identity(source)
    if initial['backend_dirty']:
        raise SystemExit('Backend must be committed/clean before measurement')
    admin = make_url(os.environ['SIGHTBREAK_TEST_ADMIN_URL'])
    if admin.get_backend_name() != 'postgresql':
        raise SystemExit('Real PostgreSQL required')
    database = 'sightbreak_trade_read_' + secrets.token_hex(6) + '_test'
    db_url = admin.set(drivername='postgresql+psycopg', database=database)
    report = {'started_at': datetime.now(timezone.utc).isoformat(), 'source': initial,
              'harness_sha256': sha256(Path(__file__)),
              'fixture_sha256': sha256(ROOT / 'backend/tests/test_trade_reads.py'),
              'platform': platform.platform(), 'python': sys.version,
              'packages': {p: importlib.metadata.version(p) for p in
                           ('sqlalchemy', 'psycopg', 'psycopg-binary', 'fastapi', 'starlette', 'httpx', 'pytest')},
              'database': database, 'rows': [], 'completed': False}
    admin_dsn = admin.set(drivername='postgresql').render_as_string(hide_password=False)
    engine = None
    with psycopg.connect(admin_dsn, autocommit=True) as connection:
        report['postgresql'] = connection.execute('SELECT version()').fetchone()[0]
        connection.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(database)))
    try:
        os.environ['DATABASE_URL'] = db_url.render_as_string(hide_password=False)
        # Use the frozen backend, but the same new measurement fixture for both.
        sys.path[:0] = [str(source / 'backend'), str(source / 'backend/tests'),
                        str(ROOT / 'backend/tests')]
        from app import Base, app, engine
        from fastapi.testclient import TestClient
        from sqlalchemy import event, text
        from test_trade_reads import canonical_trades, database_snapshot, seed_workload
        Base.metadata.create_all(engine)
        with engine.begin() as db:
            for migration in sorted((source / 'backend/migrations').glob('*.sql')):
                db.exec_driver_sql(migration.read_text())
        for count, per_side in ((0, 0), (1, 0), (1, 2), (10, 1), (40, 1), (40, 20), (501, 0)):
            with engine.begin() as db:
                db.execute(text('TRUNCATE ' + ', '.join('"' + t + '"' for t in Base.metadata.tables) + ' CASCADE'))
            headers, expected = seed_workload(count, per_side)
            expected = canonical_trades({'trades': expected})
            before = database_snapshot()
            row = {'trades': count, 'items_per_side': per_side, 'samples': [],
                   'budget': 3 + (math.ceil((count + 1) / 500) if count else 0) + math.ceil(count * per_side * 2 / 500)}
            with TestClient(app) as client:
                # Warm the pool/SQL compilation, never an ORM Session across requests.
                for _ in range(2):
                    response = client.get('/trades', headers=headers)
                    assert response.status_code == 200
                    assert canonical_trades(response.json()) == expected
                statements = []
                def record(conn, cursor, statement, parameters, context, executemany):
                    statements.append(statement)
                event.listen(engine, 'before_cursor_execute', record)
                try:
                    for _ in range(args.samples):
                        statements.clear()
                        start = time.perf_counter_ns()
                        response = client.get('/trades', headers=headers)
                        elapsed = (time.perf_counter_ns() - start) / 1e6
                        assert response.status_code == 200
                        payload = canonical_trades(response.json())
                        assert payload == expected
                        assert all(s.lstrip().upper().startswith('SELECT') for s in statements)
                        row['samples'].append({'milliseconds': elapsed, 'statements': len(statements)})
                    # SQL shapes only: never bearer tokens or bound parameters.
                    row['sql_shapes'] = list(dict.fromkeys(statements))
                finally:
                    event.remove(engine, 'before_cursor_execute', record)
            row['response_sha256'] = hashlib.sha256(json.dumps(expected, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
            row['read_only'] = database_snapshot() == before
            assert row['read_only']
            durations = sorted(s['milliseconds'] for s in row['samples'])
            row['median_ms'] = statistics.median(durations)
            row['p95_ms'] = durations[math.ceil(len(durations) * .95) - 1]
            row['query_counts'] = sorted({s['statements'] for s in row['samples']})
            report['rows'].append(row)
            (args.out / 'measurement.json').write_text(json.dumps(report, indent=2) + '\n')
            print(json.dumps({k: row[k] for k in ('trades', 'items_per_side', 'query_counts', 'median_ms', 'p95_ms', 'read_only')}), flush=True)
        report['final_source'] = identity(source)
        assert report['final_source'] == initial, 'Backend changed during the measurement'
        report['completed'] = True
    finally:
        if engine is not None:
            engine.dispose()
        with psycopg.connect(admin_dsn, autocommit=True) as connection:
            connection.execute(sql.SQL('DROP DATABASE {} WITH (FORCE)').format(sql.Identifier(database)))
        report['database_dropped'] = True
        (args.out / 'measurement.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    main()
