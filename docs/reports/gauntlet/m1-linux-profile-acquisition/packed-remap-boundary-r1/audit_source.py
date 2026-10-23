#!/usr/bin/env python3
"""Pure source/pin audit that works with only this candidate's depth-one tree."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[5]
REPORT = Path(__file__).resolve().parent


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args])


def main():
    frozen = json.loads((REPORT / 'source.json').read_text())
    rows = git('ls-tree', '-r', '-z', 'HEAD').split(b'\0')
    kept = []
    for row in rows:
        if not row:
            continue
        path = row.split(b'\t', 1)[1].decode()
        if path not in frozen['candidate_files'] and not path.startswith(frozen['report_prefix']):
            kept.append(row)
    assert sha(b'\0'.join(kept) + b'\0') == frozen['unchanged_tree_sha256']
    for path, expected in frozen['candidate_files'].items():
        assert sha((ROOT / path).read_bytes()) == expected, path
    for name, expected in json.loads((REPORT / 'fixture-identities.json').read_text()).items():
        raw = (REPORT / 'fixtures' / name).read_bytes()
        assert len(raw) == expected['bytes'] and sha(raw) == expected['sha256'], name
    supervisor = (ROOT / 'scripts/linux_profile_acquire.py').read_bytes()
    assert sha(supervisor.replace(b"OUTPUT = ROOT / 'builds/linux-profile-acquisition-r3'",
                                  b"OUTPUT = ROOT / 'builds/linux-profile-acquisition-r2'")) == frozen['original_supervisor_sha256']
    test = (ROOT / 'scripts/test_linux_profile_acquire.py').read_bytes()
    assert sha(test.replace(b'false\\n}\\n\\0\',', b'false\\n}\\n\',')) == frozen['original_acquisition_test_sha256']
    assert not (ROOT / 'builds/linux-profile-acquisition-r3').exists()
    assert not (ROOT / 'builds/linux-profile-acquisition-r3.claim').exists()
    print(json.dumps({'passed': True, 'source': git('rev-parse', 'HEAD').decode().strip(),
                      'shallow': git('rev-parse', '--is-shallow-repository').decode().strip() == 'true',
                      'unchanged_tree_sha256': frozen['unchanged_tree_sha256'],
                      'changed_source_files': sorted(frozen['candidate_files']),
                      'actual_fixture_identities_verified': True,
                      'r3_output_and_claim_absent': True}, indent=2))


if __name__ == '__main__':
    main()
