"""Finalize only this critic's new external evidence, without repeating tests."""
import datetime
import hashlib
import json
from pathlib import Path
from audit import snapshot

OUT = Path(__file__).resolve().parent
BOUND = 2 * 1024 * 1024

snapshot('seal')
snapshots = sorted(OUT.glob('source-*.json'))
baseline = json.loads((OUT / 'source-before.json').read_text(encoding='utf-8'))
drift_checks = []
for path in snapshots:
    current = json.loads(path.read_text(encoding='utf-8'))
    changed = [name for name, item in baseline['files'].items() if item != current['files'].get(name)]
    drift_checks.append(dict(snapshot=path.name, file_drift=changed,
                             head_changed=current['head'] != baseline['head'],
                             status_changed=current['status'] != baseline['status']))
files = sorted(path for path in OUT.rglob('*') if path.is_file())
lines = [hashlib.sha256(path.read_bytes()).hexdigest() + '  ' + path.relative_to(OUT).as_posix() + '\n' for path in files]
manifest = ''.join(lines).encode('utf-8')
before = sum(path.stat().st_size for path in files)
result = dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
              head=baseline['head'], no_selected_drift=not any(item['file_drift'] or item['head_changed'] or item['status_changed'] for item in drift_checks),
              source_snapshot_checks=drift_checks, manifest_entries=len(files),
              manifest_sha256=hashlib.sha256(manifest).hexdigest(),
              bound_bytes=BOUND, bytes_before_final_receipts=before,
              manifest_excludes_own_hash_and_finalization=True)
result['total_bytes'] = 0
for _ in range(10):
    raw = (json.dumps(result, indent=2) + '\n').encode('utf-8')
    size = before + len(manifest) + len(raw)
    if size == result['total_bytes']:
        break
    result['total_bytes'] = size
raw = (json.dumps(result, indent=2) + '\n').encode('utf-8')
assert before + len(manifest) + len(raw) == result['total_bytes'] < BOUND
with (OUT / 'SHA256SUMS.txt').open('xb') as stream:
    stream.write(manifest)
with (OUT / 'FINALIZATION.json').open('xb') as stream:
    stream.write(raw)
actual = sum(path.stat().st_size for path in OUT.rglob('*') if path.is_file())
assert actual == result['total_bytes'] < BOUND
print(json.dumps(dict(no_selected_drift=result['no_selected_drift'],
                      evidence_files=len(files) + 2, evidence_bytes=actual, bound_bytes=BOUND,
                      report=str(OUT / 'REPORT.md')), indent=2))
