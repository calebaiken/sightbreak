"""Read-only file/arithmetic check. No repository, database or network access."""
from pathlib import Path
import hashlib
import json
import math
import statistics


def main():
    root = Path(__file__).resolve().parent
    entries = {}
    for line in (root / 'SHA256SUMS.txt').read_text(encoding='utf-8').splitlines():
        digest, name = line.split('  ', 1)
        path = root / name
        assert path.resolve().is_relative_to(root), name
        assert name not in entries, name
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, name
        entries[name] = digest
    actual = {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}
    assert actual == set(entries) | {'SHA256SUMS.txt'}, 'Unexpected or missing packet files'

    records = {label: json.loads((root / label / 'measurement.json').read_text(encoding='utf-8'))
               for label in ('K', 'R')}
    expected_cases = [(0, 0), (1, 0), (1, 2), (10, 1), (40, 1), (40, 20), (501, 0)]
    assert records['K']['environment'] == records['R']['environment']
    for label, record in records.items():
        assert record['variant'] == label
        assert record['completed'] and record['database_dropped']
        assert record['authoritative_state_hashes'] == {'before': None, 'after': None, 'status': 'not_retained'}
        assert [(r['trades'], r['items_per_side']) for r in record['rows']] == expected_cases
        for row in record['rows']:
            samples = row['samples']
            assert len(samples) == 10
            durations = sorted(s['milliseconds'] for s in samples)
            assert all(math.isfinite(t) and t >= 0 for t in durations)
            assert all(type(s['statements']) is int and s['statements'] > 0 for s in samples)
            assert row['query_counts'] == sorted({s['statements'] for s in samples})
            expected_budget = 3 + (math.ceil((row['trades'] + 1) / 500) if row['trades'] else 0)
            expected_budget += math.ceil(2 * row['trades'] * row['items_per_side'] / 500)
            assert row['budget'] == expected_budget
            assert math.isclose(row['median_ms'], statistics.median(durations), rel_tol=1e-12)
            assert math.isclose(row['p95_ms'], durations[math.ceil(len(durations) * .95) - 1], rel_tol=1e-12)
            assert row['read_only'] is True
            assert len(row['response_sha256']) == 64
            assert all(s.lstrip().upper().startswith('SELECT') for s in row['sql_shapes'])

    equivalence = json.loads((root / 'equivalence.json').read_text(encoding='utf-8'))
    assert len(equivalence['rows']) == len(expected_cases)
    for k, r, pair in zip(records['K']['rows'], records['R']['rows'], equivalence['rows'], strict=True):
        assert (pair['trades'], pair['items_per_side']) == (k['trades'], k['items_per_side'])
        assert pair['expected_response_sha256'] == {'K': k['response_sha256'], 'R': r['response_sha256']}
        assert pair['expected_response_fingerprints_equal'] == (k['response_sha256'] == r['response_sha256'])
        assert pair['recorded_snapshot_equality'] == {'K': k['read_only'], 'R': r['read_only']}
        assert pair['state_hash_equivalence'] == 'not_evaluable_not_retained'
    print(json.dumps({'packet_files_verified': len(entries), 'variants': 2, 'workloads': 14,
                      'raw_timed_samples': 140, 'arithmetic_consistent': True,
                      'state_hashes_independently_verified': False,
                      'application_or_database_executed': False}, indent=2))


if __name__ == '__main__':
    main()
