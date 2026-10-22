#!/usr/bin/env python3
"""Verify accepted trial originals, Git blobs and preservation of blocked trial."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

builder, output = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
base = Path('docs/reports/gauntlet/m3-account-activity')
relative = base / 'round-2'
archive, run, builds = builder / relative, builder / 'builds/account-activity-stock-2', builder / 'builds'
commit, frozen, first = '08fd5cc', '3b5cf7640e256dff404b401bf2b27ffaff157bdd', 'e689416'


def git(*args):
    return subprocess.check_output(['git', *args], cwd=builder)


indexed = {}
for line in (archive / 'sha256.txt').read_text().splitlines():
    digest, name = line.split('  ', 1)
    assert name not in indexed and Path(name).name == name
    indexed[name] = digest
assert len(indexed) == 58
assert {p.name for p in archive.iterdir()} == set(indexed) | {'sha256.txt'}
native, preflight, later = [], [], []
later_names = {'builder-raw-replay.txt', 'physical-cleanup-and-result-summary.json', 'trial-verdict.json'}
for name, expected in indexed.items():
    raw = (archive / name).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == expected
    assert git('show', commit + ':' + str(relative / name)) == raw
    if (run / name).exists():
        assert (run / name).read_bytes() == raw
        native.append(name)
    elif name in later_names:
        if (builds / name).exists():
            assert (builds / name).read_bytes() == raw
        later.append(name)
    else:
        assert (builds / name).read_bytes() == raw
        preflight.append(name)
assert len(native) == 50 and len(preflight) == 5 and set(later) == later_names
omitted = sorted(p.name for p in run.iterdir() if p.is_file() and p.name not in indexed)
assert omitted == ['results.sqlite.lock', 'stop']
assert all((run / name).stat().st_size == 0 for name in omitted)
assert git('rev-parse', commit + ':game') == git('rev-parse', frozen + ':game')
assert not git('diff', '--name-only', frozen, commit, '--', 'game', 'backend', 'server', 'scripts')
old_manifest = git('show', first + ':' + str(base / 'round-1/sha256.txt'))
old_names = [line.split('  ', 1)[1] for line in old_manifest.decode().splitlines()]
preserved = [base / 'HANDOFF.md', base / 'round-1/sha256.txt'] + [base / 'round-1' / name for name in old_names]
assert all(git('show', first + ':' + str(path)) == git('show', commit + ':' + str(path)) for path in preserved)
report = json.loads((archive / 'report.json').read_text())
assert report['source_commit'] == frozen and report['status'] == 'passed'
result = dict(status='passed', archive_commit=commit, runtime_source=frozen, indexed_files=len(indexed),
              native_originals_identical=len(native), preflight_and_driver_originals_identical=len(preflight),
              later_archive_receipts=later, only_omitted_original_files=omitted,
              product_and_harness_unchanged_by_archive=True, blocked_first_trial_files_byte_preserved=len(preserved),
              manifest_sha256=hashlib.sha256((archive / 'sha256.txt').read_bytes()).hexdigest(),
              trial_verdict=json.loads((archive / 'trial-verdict.json').read_text()),
              qualification='Bounded stock-match/process-crash recovery only; first trial remains BLOCKED; G3/G16 open')
output.write_text(json.dumps(result, indent=2) + '\n')
print('Trial2 archive integrity passed:58 indexed,50 native,5 preflight/driver,3 later; first62 files preserved.')
