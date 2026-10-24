#!/usr/bin/env python3
"""Independently rehash retained responses/table rows. Standard library; no DB."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import statistics


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')


def verify(directory):
    root = Path(directory).resolve()
    report = json.loads((root / 'measurement.json').read_text(encoding='utf-8'))
    assert report['schema'] == 'trade-read-retained-artifacts-v2'
    assert report['completed'] and report['database_dropped']
    table_names = {'players', 'sessions', 'ledger', 'items', 'operations', 'audit',
                   'listings', 'trades', 'rewards', 'rate_buckets', 'game_tickets', 'loadouts'}
    responses = 0
    table_snapshots = 0

    def load(descriptor, canonical_file=False):
        path = (root / descriptor['file']).resolve()
        assert path.is_relative_to(root), descriptor['file']
        data = path.read_bytes()
        assert hashlib.sha256(data).hexdigest() == descriptor['sha256'], descriptor['file']
        value = json.loads(data)
        if canonical_file:
            assert data == canonical(value), descriptor['file']
        return value

    def state(snapshot):
        nonlocal table_snapshots
        assert snapshot['representation'] == 'full_rows_per_table'
        assert set(snapshot['tables']) == table_names
        tables = {}
        for name, descriptor in snapshot['tables'].items():
            assert descriptor['representation'] == 'full_rows'
            rows = load(descriptor, canonical_file=True)
            assert isinstance(rows, list) and len(rows) == descriptor['row_count']
            assert rows == sorted(rows, key=canonical)
            tables[name] = rows
            table_snapshots += 1
        assert hashlib.sha256(canonical(tables)).hexdigest() == snapshot['sha256']
        assert all(row['password_hash'] == 'fixture-unusable' for row in tables['players'])
        return tables

    cases = [(0, 0), (1, 0), (1, 2), (10, 1), (40, 1), (40, 20), (501, 0)]
    assert [(r['trades'], r['items_per_side']) for r in report['rows']] == cases
    for row in report['rows']:
        expected = load(row['expected_response'], canonical_file=True)
        assert row['expected_response_sha256'] == row['expected_response']['sha256']
        assert len(row['warmups']) == 2 and len(row['samples']) == 10
        actual_hashes = set()
        for response in [*row['warmups'], *(sample['response'] for sample in row['samples'])]:
            raw = load(response['raw'])
            normalized = {'trades': sorted(raw['trades'], key=lambda trade: trade['id'])}
            actual = load(response['canonical'], canonical_file=True)
            assert normalized == actual == expected
            assert response['status'] == 200 and response['matches_expected']
            actual_hashes.add(hashlib.sha256(canonical(normalized)).hexdigest())
            responses += 1
        assert row['actual_response_sha256s'] == sorted(actual_hashes)
        before, after = state(row['state_before']), state(row['state_after'])
        assert before == after and row['read_only']
        assert row['state_before']['sha256'] == row['state_after']['sha256']
        durations = sorted(s['milliseconds'] for s in row['samples'])
        assert all(math.isfinite(t) and t >= 0 for t in durations)
        assert math.isclose(statistics.median(durations), row['median_ms'], rel_tol=1e-12)
        assert durations[math.ceil(len(durations) * .95) - 1] == row['p95_ms']
        assert row['query_counts'] == sorted({s['statements'] for s in row['samples']})
        assert all(statement.lstrip().upper().startswith('SELECT') for statement in row['sql_shapes'])
    return {'verified_workloads': len(report['rows']), 'verified_received_responses': responses,
            'verified_full_table_snapshots': table_snapshots,
            'actual_bodies_match_expected': True, 'authoritative_rows_unchanged': True,
            'application_or_database_executed': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    print(json.dumps(verify(parser.parse_args().directory), indent=2))
