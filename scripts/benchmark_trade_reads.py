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


def canonical_bytes(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')


def retain_json(root, relative, value):
    data = canonical_bytes(value)
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return {'file': relative.as_posix(), 'sha256': hashlib.sha256(data).hexdigest()}


def retain_response(root, folder, response, expected, canonicalize):
    # Retain received bytes, not a regeneration of the expected fixture response.
    raw = response.content
    raw_hash = hashlib.sha256(raw).hexdigest()
    raw_path = folder / 'responses' / (raw_hash + '.json')
    (root / raw_path).parent.mkdir(parents=True, exist_ok=True)
    (root / raw_path).write_bytes(raw)
    payload = canonicalize(response.json())
    payload_hash = hashlib.sha256(canonical_bytes(payload)).hexdigest()
    canonical = retain_json(root, folder / 'canonical-responses' / (payload_hash + '.json'), payload)
    record = {'status': response.status_code,
              'raw': {'file': raw_path.as_posix(), 'sha256': raw_hash},
              'canonical': canonical, 'matches_expected': payload == expected}
    assert response.status_code == 200 and record['matches_expected'], record
    return record


def retain_state(root, folder, phase, snapshot):
    # Full rows from this run's private fictional-fixture database. No bearer
    # headers are retained; sessions already contain only token hashes in SQL.
    tables = {name: sorted((json.loads(row) for row in rows), key=canonical_bytes)
              for name, rows in sorted(snapshot.items())}
    assert all(p['password_hash'] == 'fixture-unusable' for p in tables['players'])
    records = {}
    for name, rows in tables.items():
        records[name] = {**retain_json(root, folder / 'state' / phase / (name + '.json'), rows),
                         'row_count': len(rows), 'representation': 'full_rows'}
    return {'sha256': hashlib.sha256(canonical_bytes(tables)).hexdigest(),
            'representation': 'full_rows_per_table', 'tables': records}


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
    parser.add_argument('--runtime-reference', default='HEAD',
                        help='Git revision whose complete backend tree must match --source')
    args = parser.parse_args()
    if args.samples < 2:
        parser.error('--samples must be at least two')
    source = args.source.resolve()
    args.out.mkdir(parents=True, exist_ok=False)
    initial = identity(source)
    if initial['backend_dirty']:
        raise SystemExit('Backend must be committed/clean before measurement')
    runtime_reference = subprocess.check_output(['git', 'rev-parse', args.runtime_reference], cwd=source, text=True).strip()
    reference_tree = subprocess.check_output(['git', 'rev-parse', runtime_reference + ':backend'], cwd=source, text=True).strip()
    if initial['backend_tree'] != reference_tree:
        raise SystemExit('Backend tree differs from the requested runtime reference')
    harness_commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    harness_status = subprocess.check_output(['git', 'status', '--porcelain', '--',
                                              'scripts/benchmark_trade_reads.py',
                                              'scripts/verify_trade_read_artifacts.py',
                                              'backend/tests/test_trade_reads.py'], cwd=ROOT, text=True).strip()
    if harness_status:
        raise SystemExit('Measurement harness/fixture must be committed/clean')
    admin = make_url(os.environ['SIGHTBREAK_TEST_ADMIN_URL'])
    if admin.get_backend_name() != 'postgresql':
        raise SystemExit('Real PostgreSQL required')
    database = 'sightbreak_trade_read_' + secrets.token_hex(6) + '_test'
    db_url = admin.set(drivername='postgresql+psycopg', database=database)
    report = {'schema': 'trade-read-retained-artifacts-v2',
              'started_at': datetime.now(timezone.utc).isoformat(), 'source': initial,
              'runtime_reference': {'commit': runtime_reference, 'backend_tree': reference_tree},
              'harness_commit': harness_commit,
              'harness_sha256': sha256(Path(__file__)),
              'artifact_verifier_sha256': sha256(ROOT / 'scripts/verify_trade_read_artifacts.py'),
              'fixture_sha256': sha256(ROOT / 'backend/tests/test_trade_reads.py'),
              'platform': platform.platform(), 'python': sys.version,
              'packages': {p: importlib.metadata.version(p) for p in
                           ('sqlalchemy', 'psycopg', 'psycopg-binary', 'fastapi', 'starlette', 'httpx', 'pytest')},
              'database': database, 'rows': [], 'completed': False,
              'retention': {'responses': 'all distinct raw and canonical received bodies; hashes for every warm-up/timed response',
                            'state': 'full before/after rows for every authoritative ORM table; per-table and aggregate SHA256',
                            'credentials': 'fictional fixture accounts; unusable password markers and SQL session token hashes only; no bearer headers'},
              'canonicalization': {'json': 'UTF-8 json.dumps(sort_keys=True,separators=(comma,colon),allow_nan=False), ensure_ascii=True, no newline',
                                   'response': 'sort top-level trades by ID; preserve all nested arrays',
                                   'state': 'parse PostgreSQL to_jsonb rows; sort each table by canonical JSON bytes; aggregate sorted-key table-to-rows object'}}
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
        for index, (count, per_side) in enumerate(((0, 0), (1, 0), (1, 2), (10, 1), (40, 1), (40, 20), (501, 0))):
            with engine.begin() as db:
                db.execute(text('TRUNCATE ' + ', '.join('"' + t + '"' for t in Base.metadata.tables) + ' CASCADE'))
            headers, expected = seed_workload(count, per_side)
            expected = canonical_trades({'trades': expected})
            before = database_snapshot()
            folder = Path('workloads') / f'{index:02d}-{count}-{per_side}'
            row = {'trades': count, 'items_per_side': per_side, 'samples': [], 'warmups': [],
                   'expected_response': retain_json(args.out, folder / 'expected-response.json', expected),
                   'state_before': retain_state(args.out, folder, 'before', before),
                   'budget': 3 + (math.ceil((count + 1) / 500) if count else 0) + math.ceil(count * per_side * 2 / 500)}
            report['rows'].append(row)
            with TestClient(app) as client:
                # Warm the pool/SQL compilation, never an ORM Session across requests.
                for _ in range(2):
                    response = client.get('/trades', headers=headers)
                    row['warmups'].append(retain_response(args.out, folder, response, expected, canonical_trades))
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
                        received = retain_response(args.out, folder, response, expected, canonical_trades)
                        assert all(s.lstrip().upper().startswith('SELECT') for s in statements)
                        row['samples'].append({'milliseconds': elapsed, 'statements': len(statements), 'response': received})
                    # SQL shapes only: never bearer tokens or bound parameters.
                    row['sql_shapes'] = list(dict.fromkeys(statements))
                finally:
                    event.remove(engine, 'before_cursor_execute', record)
            row['expected_response_sha256'] = row['expected_response']['sha256']
            row['actual_response_sha256s'] = sorted({entry['canonical']['sha256'] for entry in
                                                    [*row['warmups'], *(sample['response'] for sample in row['samples'])]})
            after = database_snapshot()
            row['state_after'] = retain_state(args.out, folder, 'after', after)
            row['read_only'] = after == before
            assert row['read_only']
            assert row['state_before']['sha256'] == row['state_after']['sha256']
            durations = sorted(s['milliseconds'] for s in row['samples'])
            row['median_ms'] = statistics.median(durations)
            row['p95_ms'] = durations[math.ceil(len(durations) * .95) - 1]
            row['query_counts'] = sorted({s['statements'] for s in row['samples']})
            (args.out / 'measurement.json').write_text(json.dumps(report, indent=2) + '\n')
            print(json.dumps({k: row[k] for k in ('trades', 'items_per_side', 'query_counts', 'median_ms', 'p95_ms', 'read_only')}), flush=True)
        report['final_source'] = identity(source)
        assert report['final_source'] == initial, 'Backend changed during the measurement'
        assert sha256(Path(__file__)) == report['harness_sha256'], 'Harness changed during measurement'
        assert sha256(ROOT / 'backend/tests/test_trade_reads.py') == report['fixture_sha256'], 'Fixture changed during measurement'
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
