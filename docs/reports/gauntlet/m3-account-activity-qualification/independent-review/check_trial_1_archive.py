#!/usr/bin/env python3
"""Validate the blocked trial's archive without changing its qualification."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

builder, output = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
relative = Path('docs/reports/gauntlet/m3-account-activity/round-1')
archive, run, builds = builder / relative, builder / 'builds/account-activity-stock-1', builder / 'builds'
commit = 'e689416'
indexed = {}
for line in (archive / 'sha256.txt').read_text().splitlines():
    digest, name = line.split('  ', 1)
    assert name not in indexed and Path(name).name == name
    indexed[name] = digest
assert len(indexed) == 60
assert {p.name for p in archive.iterdir()} == set(indexed) | {'sha256.txt'}
native, preparation, later = [], [], []
for name, expected in indexed.items():
    raw = (archive / name).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == expected
    blob = subprocess.check_output(['git', 'show', commit + ':' + str(relative / name)], cwd=builder)
    assert blob == raw, name + ' differs from committed archive'
    if (run / name).exists():
        assert (run / name).read_bytes() == raw
        native.append(name)
    elif (builds / name).exists():
        assert (builds / name).read_bytes() == raw
        preparation.append(name)
    else:
        later.append(name)
omitted = sorted(p.name for p in run.iterdir() if p.is_file() and p.name not in indexed)
assert omitted == ['results.sqlite.lock', 'stop']
assert all((run / name).stat().st_size == 0 for name in omitted)
assert later == ['builder-raw-replay.txt', 'trial-verdict.json']
verdict = json.loads((archive / 'trial-verdict.json').read_text())
assert json.loads((archive / 'report.json').read_text())['status'] == 'passed'
result = dict(status='passed_archive_integrity_only', qualification='BLOCKED; missing retained post-replay SQL witness unchanged',
              archive_commit=commit, indexed_files=len(indexed), native_files_identical=len(native),
              preparation_files_identical=len(preparation), later_archive_receipts=later,
              only_omitted_original_files=omitted, raw_harness_status='passed', trial_verdict=verdict,
              manifest_sha256=hashlib.sha256((archive / 'sha256.txt').read_bytes()).hexdigest())
output.write_text(json.dumps(result, indent=2) + '\n')
print('Blocked-trial archive integrity passed:', len(indexed), 'indexed;', len(native), 'native;', len(preparation), 'preflight;', len(later), 'later receipts')
