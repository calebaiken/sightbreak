"""Append custody correction without repeating tests or overwriting old evidence."""
import datetime
import hashlib
import json
from pathlib import Path
import subprocess

OUT = Path(__file__).resolve().parent
ROOT = OUT.parent / 'sightbreak-v3'
BOUND = 2 * 1024 * 1024
baseline = json.loads((OUT / 'source-before.json').read_text(encoding='utf-8'))

def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True, encoding='utf-8', errors='replace')

head = git('rev-parse', 'HEAD').strip()
status = git('status', '--porcelain=v1', '--untracked-files=all')
selected = {}
for relative, prior in baseline['files'].items():
    path = ROOT / relative
    actual = dict(sha256=hashlib.sha256(path.read_bytes()).hexdigest(), bytes=path.stat().st_size,
                  mtime_ns=path.stat().st_mtime_ns) if path.is_file() else dict(missing=True)
    selected[relative] = dict(actual=actual, same_as_tested=prior == actual)
check = dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), baseline_head=baseline['head'],
             observed_head=head, head_drift=head != baseline['head'], status_same=status == baseline['status'],
             status_sha256=hashlib.sha256(status.encode()).hexdigest(), selected=selected,
             changed_commit_paths=git('diff', '--name-status', baseline['head'], head),
             no_repeated_tests=True, original_failed_aggregate_receipt_preserved=True)
with (OUT / 'POST_SEAL_CHECK.json').open('x', encoding='utf-8') as stream:
    json.dump(check, stream, indent=2)
    stream.write('\n')
files = sorted(path for path in OUT.rglob('*') if path.is_file())
manifest = ''.join(hashlib.sha256(path.read_bytes()).hexdigest() + '  ' + path.relative_to(OUT).as_posix() + '\n'
                   for path in files).encode('utf-8')
before = sum(path.stat().st_size for path in files)
result = dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
              verdict='No scoped code blocker; concurrent HEAD drift retained; no exact-source Linux or release approval',
              observed_head=head, scoped_bytes_unchanged=all(item['same_as_tested'] for item in selected.values()),
              head_drift=check['head_drift'], status_same=check['status_same'],
              manifest_sha256=hashlib.sha256(manifest).hexdigest(), manifest_entries=len(files),
              manifest_excludes_own_hash_and_custody_receipt=True, bound_bytes=BOUND, total_bytes=0)
for _ in range(10):
    raw = (json.dumps(result, indent=2) + '\n').encode('utf-8')
    size = before + len(manifest) + len(raw)
    if size == result['total_bytes']:
        break
    result['total_bytes'] = size
raw = (json.dumps(result, indent=2) + '\n').encode('utf-8')
assert before + len(manifest) + len(raw) == result['total_bytes'] < BOUND
with (OUT / 'FINAL_SHA256SUMS.txt').open('xb') as stream:
    stream.write(manifest)
with (OUT / 'CUSTODY.json').open('xb') as stream:
    stream.write(raw)
assert sum(path.stat().st_size for path in OUT.rglob('*') if path.is_file()) == result['total_bytes']
print(json.dumps(result, indent=2))
