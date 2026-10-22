#!/usr/bin/env python3
"""Independently verify retained QA receipt index bytes and source identities."""
import argparse
import hashlib
import json
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('directory', type=Path)
    parser.add_argument('--identity', type=Path, required=True)
    args = parser.parse_args()
    base = args.directory
    index = json.loads((base / 'qa-receipts-index.json').read_text())
    expected = json.loads(args.identity.read_text())
    checks, mismatches, identities = [], [], []
    for entry in index['files']:
        file = base / entry['archive_path']
        actual = {'path': entry['path'], 'bytes': file.stat().st_size, 'sha256': sha(file)}
        checks.append(actual)
        if actual['bytes'] != entry['bytes'] or actual['sha256'] != entry['sha256']:
            mismatches.append(actual)
        if file.suffix == '.json':
            data = json.loads(file.read_text())
            if isinstance(data, dict) and 'source_commit' in data:
                keys = ('source_commit','source_game_tree','source_content_sha256','source_validation_sha256')
                same = all(data.get(key) == expected[key] for key in keys)
                identities.append({'path': entry['path'], 'matches_candidate': same,
                                   'identity': {key: data.get(key) for key in keys}})
    report = {'index_files': len(checks), 'verified_bytes': sum(x['bytes'] for x in checks),
              'mismatches': mismatches, 'source_records': identities,
              'index_sha256': sha(base / 'qa-receipts-index.json')}
    print(json.dumps(report, indent=2))
    if mismatches:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
