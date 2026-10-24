"""Additional static protocol/collector integrity checks. No payload execution."""
import hashlib
import json
import pathlib
import re

BASE = pathlib.Path(__file__).resolve().parent
COLLECTION = BASE.parent / 'sightbreak-v3-evidence/ci-40082291663'
PROTOCOL = BASE / 'raw/artifact-12556088968.zip/builds/v3-matrix/protocol'
checks = []
rows = []
expected = [('release', 'release', 'join'), ('current', 'current', 'join'),
            ('release', 'current', 'server drops pre-handshake client'),
            ('current', 'release', 'client reports missing handshake'),
            ('future', 'current', 'explicit mismatch'), ('current', 'future', 'explicit mismatch'),
            ('previous', 'current', 'explicit mismatch'), ('current', 'previous', 'explicit mismatch')]
for client, server, wanted in expected:
    name = 'client-' + client + '.server-' + server
    cl = (PROTOCOL / (name + '.client.log')).read_text()
    sl = (PROTOCOL / (name + '.server.log')).read_text()
    summaries = re.findall(r'^PROTOCOL_CLIENT (\{.*\})$', cl, re.M)
    report = json.loads(summaries[0]) if len(summaries) == 1 else {}
    failed_at = [float(v) for v in re.findall(r'^PROTOCOL_STATE ([0-9.]+) failed$', cl, re.M)]
    drops = [float(v) for v in re.findall(r'^PROTOCOL_NOTICE ([0-9.]+) Server disconnected', cl, re.M)]
    first_notice = re.search(r'^PROTOCOL_NOTICE ([0-9.]+) ', cl, re.M)
    origin = float(first_notice.group(1)) if first_notice else 0.
    admitted = sl.count('joined Relay Yard')
    good = bool(report)
    if wanted == 'join':
        good = good and report['joined'] is True and report['final_state'] == 'connected' and admitted >= 1
    elif wanted == 'server drops pre-handshake client':
        good = good and report['joined'] is False and admitted == 0 and sl.count('PROTOCOL_TIMEOUT') >= 1 and bool(drops) and drops[0] - origin <= 6.5
    elif wanted == 'client reports missing handshake':
        good = good and report['final_state'] == 'failed' and any('No version handshake' in n for n in report['notices']) and bool(failed_at) and failed_at[0] <= 6.5 and admitted == 0
    else:
        good = good and report['final_state'] == 'failed' and any('Version mismatch' in n for n in report['notices']) and bool(failed_at) and failed_at[0] <= 2. and admitted == 0 and 'PROTOCOL_REJECTED' in sl
    checks.append({'id': 'nested-protocol/' + client + ':' + server, 'passed': bool(good)})
    rows.append({'client': client, 'server': server, 'expected': wanted, 'client_report': report,
                 'admissions': admitted, 'failed_at': failed_at, 'disconnects': drops, 'passed': bool(good)})

source = json.loads((BASE / 'source-manifest.json').read_text())
members = json.loads((BASE / 'member-index.json').read_text())
actual = {m['member']: m for m in members if m['archive'] == 'artifact-12556088968.zip'}
future_rows = []
prefix = 'builds/v3-matrix/protocol/future/'
for item in source['files']:
    name = item['path']
    if not name.startswith('game/'):
        continue
    expected_hash = item['sha256']
    if name == 'game/scripts/gameplay/match.gd':
        data = (BASE / 'frozen-source' / name).read_bytes()
        old, new = b'const PROTOCOL_VERSION := 6', b'const PROTOCOL_VERSION := 7'
        assert data.count(old) == 1
        expected_hash = hashlib.sha256(data.replace(old, new, 1)).hexdigest()
    member = actual.get(prefix + name, {})
    future_rows.append({'path': name, 'expected_sha256': expected_hash, 'actual_sha256': member.get('sha256'),
                        'passed': expected_hash == member.get('sha256')})
checks.append({'id': 'nested-protocol/future-exact-game-copy-except-declared-version',
               'passed': all(r['passed'] for r in future_rows), 'files': len(future_rows)})

archives = {a['identity']: a['sha256'] for a in json.loads((BASE / 'archive-index.json').read_text())}
collector_rows = []
for line in (COLLECTION / 'SHA256SUMS.txt').read_text().splitlines():
    expected_hash, name = line.split('  ', 1)
    if name in archives:
        digest = archives[name]
    else:
        with (COLLECTION / name).open('rb') as stream:
            digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    collector_rows.append({'path': name, 'expected': expected_hash, 'actual': digest, 'passed': digest == expected_hash})
checks.append({'id': 'collection/all-original-ledger-lines', 'passed': all(r['passed'] for r in collector_rows), 'entries': len(collector_rows)})
result = {'checks': checks, 'protocol_rows': rows, 'future_source_files': future_rows, 'collector_ledger': collector_rows}
(BASE / 'supplement.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(checks, indent=2))
