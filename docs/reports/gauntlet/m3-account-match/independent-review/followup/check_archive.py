#!/usr/bin/env python3
"""Verify manifest, committed blobs, and archived bytes against original outputs."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

source = Path(sys.argv[1]).resolve()
commit = sys.argv[2]
archive_relative = Path('docs/reports/gauntlet/m3-account-match/round-1')
archive = source / archive_relative
original = source / 'builds/account-match-stock-1'
external = {
    'driver.log': Path('/workspace/account-match-stock-1-driver.log'),
    'engine-check-only.log': Path('/workspace/account-match-check-only.log'),
    'initial-output-unit.log': Path('/workspace/account-match-output-unit.log'),
    'server-unit.log': Path('/workspace/account-match-server-unit.log'),
}
listed = {}
for line in (archive / 'sha256.txt').read_text().splitlines():
    digest, filename = line.split('  ', 1)
    assert len(digest) == 64 and all(c in '0123456789abcdef' for c in digest)
    path = Path(filename)
    assert not path.is_absolute() and '..' not in path.parts and filename not in listed
    listed[filename] = digest
actual = {str(p.relative_to(archive)) for p in archive.rglob('*') if p.is_file()}
assert actual == set(listed) | {'sha256.txt'}, actual ^ (set(listed) | {'sha256.txt'})
comparisons = []
for filename, digest in sorted(listed.items()):
    raw = (archive / filename).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == digest, filename
    committed = subprocess.check_output(['git', 'show', f'{commit}:{archive_relative / filename}'], cwd=source)
    assert committed == raw, filename
    origin = original / filename
    kind = 'native_build_output'
    if not origin.exists():
        origin = external.get(filename)
        kind = 'external_preflight_or_driver'
    if origin is not None and origin.exists():
        assert origin.read_bytes() == raw, filename
        comparisons.append(dict(file=filename, source=str(origin), bytes=len(raw), sha256=digest, kind=kind, equal=True))
    else:
        comparisons.append(dict(file=filename, bytes=len(raw), sha256=digest, kind='archive_only_pure_followup_receipt', equal_to_committed_blob=True))
manifest = subprocess.check_output(['git', 'show', f'{commit}:{archive_relative / "sha256.txt"}'], cwd=source)
assert manifest == (archive / 'sha256.txt').read_bytes()
unarchived = sorted(p.name for p in original.iterdir() if p.is_file() and p.name not in listed)
assert all(name in ('stop', 'results.sqlite.lock', 'results.sqlite-wal', 'results.sqlite-shm') for name in unarchived)
result = dict(status='passed', observed_at_utc=datetime.now(timezone.utc).isoformat(),
              archive_commit=subprocess.check_output(['git', 'rev-parse', commit], cwd=source, text=True).strip(),
              indexed_file_count=len(listed), manifest_sha256=hashlib.sha256(manifest).hexdigest(),
              native_build_matches=sum(r['kind'] == 'native_build_output' for r in comparisons),
              external_matches=sum(r['kind'] == 'external_preflight_or_driver' for r in comparisons),
              archive_only_followup_receipts=sum(r['kind'] == 'archive_only_pure_followup_receipt' for r in comparisons),
              unarchived_runtime_control_files=unarchived, comparisons=comparisons)
if len(sys.argv) > 3:
    previous = sys.argv[3]
    old_manifest = subprocess.check_output(['git', 'show', f'{previous}:{archive_relative / "sha256.txt"}'], cwd=source).decode()
    old_files = [line.split('  ', 1)[1] for line in old_manifest.splitlines()]
    for filename in old_files:
        old_raw = subprocess.check_output(['git', 'show', f'{previous}:{archive_relative / filename}'], cwd=source)
        assert old_raw == (archive / filename).read_bytes(), filename
    result['previous_archive_commit'] = previous
    result['previous_indexed_files_byte_unchanged'] = len(old_files)
print(json.dumps(result, indent=2))
