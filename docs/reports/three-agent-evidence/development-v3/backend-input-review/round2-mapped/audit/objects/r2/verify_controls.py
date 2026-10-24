"""Offline artifact falsifiers. No application/database imports or reruns."""
from pathlib import Path
import hashlib
import json
import secrets
import shutil
import subprocess
import sys

root = Path(__file__).resolve().parent
repo = Path('C:/Users/blith/AppData/Local/Temp/opencode/sightbreak-backend-trade-read-v3')
scratch = root.parent / ('trade-artifact-controls-' + secrets.token_hex(6))
scratch.mkdir()
def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
def change(path, value):
    path.write_bytes(encoded(value))
    return hashlib.sha256(path.read_bytes()).hexdigest()

records = []
for control in ('received-body-checksum', 'received-body-semantic', 'authoritative-row-mutation'):
    target = scratch / control
    shutil.copytree(root / 'candidate', target)
    report = json.loads((target / 'measurement.json').read_text())
    row = report['rows'][2]
    edits = []
    if control.startswith('received-body'):
        entries = [*row['warmups'], *(sample['response'] for sample in row['samples'])]
        raw_path = target / entries[0]['raw']['file']
        raw = json.loads(raw_path.read_bytes())
        raw['trades'][0]['revision'] += 1
        raw_hash = change(raw_path, raw)
        edits.append(raw_path.relative_to(target).as_posix())
        if control.endswith('semantic'):
            canonical = {'trades': sorted(raw['trades'], key=lambda trade: trade['id'])}
            canonical_path = target / entries[0]['canonical']['file']
            actual_hash = change(canonical_path, canonical)
            for response in entries:
                response['raw']['sha256'] = raw_hash
                response['canonical']['sha256'] = actual_hash
            row['actual_response_sha256s'] = [actual_hash]
            edits.append(canonical_path.relative_to(target).as_posix())
    else:
        descriptor = row['state_after']['tables']['players']
        path = target / descriptor['file']
        players = json.loads(path.read_bytes())
        players[0]['credits'] += 1
        players.sort(key=encoded)
        descriptor['sha256'] = change(path, players)
        tables = {name: json.loads((target / table['file']).read_bytes())
                  for name, table in row['state_after']['tables'].items()}
        row['state_after']['sha256'] = hashlib.sha256(encoded(tables)).hexdigest()
        edits.append(path.relative_to(target).as_posix())
    (target / 'measurement.json').write_text(json.dumps(report, indent=2) + '\n')
    command = [sys.executable, '-B', str(repo / 'scripts/verify_trade_read_artifacts.py'), str(target)]
    result = subprocess.run(command, capture_output=True, text=True, timeout=30)
    (root / (control + '.log')).write_text(result.stdout + result.stderr)
    assert result.returncode != 0 and 'AssertionError' in result.stderr
    records.append({'control': control, 'exit': result.returncode, 'rejected': True,
                    'command': command, 'edited_artifacts': edits,
                    'metadata_rehashed': control != 'received-body-checksum'})
(root / 'artifact-negative-controls.json').write_text(json.dumps(records, indent=2) + '\n')
print(json.dumps([{k: row[k] for k in ('control', 'exit', 'rejected')} for row in records], indent=2))
