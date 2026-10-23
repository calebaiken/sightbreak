"""Read-only packet audit; no application, database, network or repository access."""
from pathlib import Path
import hashlib
import json
import math
import runpy


def main():
    root = Path(__file__).resolve().parent
    entries = {}
    for line in (root / 'SHA256SUMS.txt').read_text(encoding='utf-8').splitlines():
        digest, name = line.split('  ', 1)
        path = (root / name).resolve()
        assert path.is_relative_to(root), name
        assert name not in entries, name
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, name
        entries[name] = digest
    actual = {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}
    assert actual == set(entries) | {'SHA256SUMS.txt'}, 'Missing or unmanifested files'

    verifier = runpy.run_path(str(root / 'verify_artifacts.py'))
    verified = {label: verifier['verify'](root / label) for label in ('M', 'V')}
    records = {label: json.loads((root / label / 'measurement.json').read_text(encoding='utf-8'))
               for label in ('M', 'V')}
    equivalence = json.loads((root / 'equivalence.json').read_text(encoding='utf-8'))
    assert records['M']['environment'] == records['V']['environment']
    assert len(equivalence['rows']) == 7

    def load(label, descriptor):
        return json.loads((root / label / descriptor['file']).read_bytes())

    for index, pair in enumerate(equivalence['rows']):
        rows = {label: record['rows'][index] for label, record in records.items()}
        bodies, tables = {}, {}
        for label, row in rows.items():
            assert records[label]['variant'] == label
            assert (row['trades'], row['items_per_side']) == (pair['trades'], pair['items_per_side'])
            budget = 3 + (math.ceil((row['trades'] + 1) / 500) if row['trades'] else 0)
            budget += math.ceil(2 * row['trades'] * row['items_per_side'] / 500)
            assert row['budget'] == budget
            assert all(type(s['statements']) is int and s['statements'] > 0 for s in row['samples'])
            received = [*row['warmups'], *(sample['response'] for sample in row['samples'])]
            for response in received:
                raw = load(label, response['raw'])
                assert isinstance(raw, dict) and set(raw) == {'trades'}, response['raw']['file']
            bodies[label] = [load(label, response['canonical']) for response in received]
            tables[label] = {name: load(label, descriptor)
                             for name, descriptor in row['state_before']['tables'].items()}
            assert pair['actual_response_sha256s'][label] == row['actual_response_sha256s']
            assert pair['expected_response_sha256'][label] == row['expected_response_sha256']
            assert pair['state_sha256'][label] == {phase: row['state_' + phase]['sha256']
                                                 for phase in ('before', 'after')}
            assert pair['snapshot_rows_equal_within_run'][label] is True
        assert all(body == bodies['M'][0] for values in bodies.values() for body in values)
        assert pair['actual_canonical_responses_equal'] is True
        table_equality = {name: tables['M'][name] == tables['V'][name] for name in tables['M']}
        assert pair['cross_variant_table_rows_equal'] == table_equality
        differences = {}
        for name, same in table_equality.items():
            if not same:
                left, right = tables['M'][name], tables['V'][name]
                if name == 'sessions':
                    left, right = [sorted(value, key=lambda row: row['token_hash']) for value in (left, right)]
                assert len(left) == len(right)
                differences[name] = sorted({key for a, b in zip(left, right, strict=True)
                                             for key in a.keys() | b.keys() if a.get(key) != b.get(key)})
        assert pair['cross_variant_differing_columns'] == differences
        assert differences == {'sessions': ['expires_at']}

    print(json.dumps({'packet_files_verified': len(entries), 'variants': verified,
                      'actual_cross_variant_canonical_bodies_equal': True,
                      'complete_top_level_response_envelopes_checked': True,
                      'cross_variant_state_difference': 'sessions.expires_at only',
                      'application_or_database_executed': False}, indent=2))


if __name__ == '__main__':
    main()
