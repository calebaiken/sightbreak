#!/usr/bin/env python3
"""Recompute actual receipts from native logs, raw HTTP records and SQLite."""
import base64
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import time

RUN = Path('/workspace/sightbreak-client-receipt-runtime-r1')
CANDIDATE = Path('/workspace/sightbreak-client-result-recovery')
BASELINE = Path('/workspace/sightbreak-client-receipt-baseline')
EXPECTED = {'candidate': '79e076ed83651aea3ff8e439a64c0f979d35ecf2',
            'baseline': 'b97fd81b0f10f45bda92f4a873314b0d270086db'}


def read(path):
    return json.loads(path.read_bytes())


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args]).decode().strip()


def main():
    summary = read(RUN / 'summary.json')
    assert summary['godot'] == '4.7.2.stable.official.ed1daf0bf'
    for key, path in [('probe_sha256', CANDIDATE / 'game/tests/transaction_crash_probe.gd'),
                      ('lifecycle_probe_sha256', CANDIDATE / 'game/tests/receipt_lifecycle_probe.gd'),
                      ('harness_sha256', CANDIDATE / 'scripts/validate_transaction_restart.py')]:
        assert summary[key] == hashlib.sha256(path.read_bytes()).hexdigest()
    report = {'observed_utc_ns': time.time_ns(), 'method': 'independent raw-file and read-only immutable SQLite audit',
              'sources': {}, 'rows': [], 'lifecycle': {}, 'totals': {}}
    for label, root in [('baseline', BASELINE), ('candidate', CANDIDATE)]:
        source = {'commit': git(root, 'rev-parse', 'HEAD'), 'game_tree': git(root, 'rev-parse', 'HEAD:game'),
                  'status': git(root, 'status', '--porcelain', '--untracked-files=all')}
        assert source['commit'] == EXPECTED[label] and source['status'] == ''
        assert summary['runs'][label]['source'] == summary['runs'][label]['source_after'] == source
        report['sources'][label] = source
        import_log = (RUN / f'{label}-import.log').read_text()
        assert all(marker not in import_log for marker in ['SCRIPT ERROR', 'ERROR:', 'Parse Error'])
        fixtures = sorted((RUN / label).glob('*/fixture.json'))
        assert len(fixtures) == 12
        observed_grid = set()
        for fixture_path in fixtures:
            directory = fixture_path.parent
            repeat, kind, boundary = directory.name.split('-')
            assert repeat == '0'
            observed_grid.add((kind, boundary))
            config = read(fixture_path)
            price = 10000000 if kind == 'market' else 100
            expected_path = {'store': '/store/buy', 'case': '/cases/open', 'market': '/market/listing-instance/buy'}[kind]
            assert config['path'] == expected_path
            events = [json.loads(line) for line in (directory / 'timeline.jsonl').read_bytes().splitlines()]
            named = lambda name: [row for row in events if row['event'] == name]
            assert not named('barrier_timeout')
            for clock in ['wall_ns', 'monotonic_ns']:
                assert all(a[clock] <= b[clock] for a, b in zip(events, events[1:]))
            initial, killed = named('client_started'), named('kill_confirmed')
            assert len(initial) == len(killed) == 1 and initial[0]['pid'] == killed[0]['pid'] and killed[0]['returncode'] == -9
            inbound = named('request_received')
            assert len(inbound) == (3 if label == 'candidate' and boundary in ['late_commit', 'recovery_kill'] else 2 if label == 'candidate' else 1)
            raw = base64.b64decode(inbound[0]['raw_body_base64'], validate=True)
            for request in inbound:
                assert request['method'] == 'POST' and request['path'] == expected_path
                assert request['body'] == config['payload'] == json.loads(base64.b64decode(request['raw_body_base64'], validate=True))
                assert base64.b64decode(request['raw_body_base64'], validate=True) == raw
            database = sqlite3.connect(f'file:{directory / "authority.sqlite3"}?mode=ro&immutable=1', uri=True)
            assert database.execute('PRAGMA integrity_check').fetchone() == ('ok',)
            receipts = database.execute('SELECT key,payload,response FROM receipts').fetchall()
            costs = [row[0] for row in database.execute('SELECT cost FROM mutations')]
            db_requests = database.execute('SELECT method,path,raw_body,body FROM requests').fetchall()
            database.close()
            committed = label == 'candidate' or boundary != 'before_commit'
            assert costs == ([price] if committed else []) and len(receipts) == int(committed)
            assert len(db_requests) == (1 if boundary == 'before_commit' else 2) if label == 'candidate' else len(db_requests) == int(committed)
            for method, path, request_raw, canonical in db_requests:
                assert method == 'POST' and path == expected_path and request_raw.encode() == raw and json.loads(canonical) == config['payload']
            if committed:
                assert receipts[0][0] == config['payload']['idempotency_key'] and json.loads(receipts[0][1]) == config['payload']
                server_response = json.loads(receipts[0][2])
                assert server_response['credits'] == 10000000 - price
                if kind == 'market':
                    assert server_response['fee'] == 300000
            first = read(directory / 'journal-first-kill-state.json')
            final = read(directory / 'journal-after-recovery.json')
            assert first['exists'] == (label == 'candidate') and not final['exists']
            assert final['bytes_base64'] is None and final['sha256'] is None and not Path(config['journal']).exists()
            if label == 'candidate':
                journal_raw = base64.b64decode(first['bytes_base64'], validate=True)
                assert first['sha256'] == hashlib.sha256(journal_raw).hexdigest()
                assert journal_raw == (directory / 'journal-at-kill.json').read_bytes()
                saved = json.loads(journal_raw)['transaction']
                assert set(saved) == {'path', 'payload', 'server', 'owner', 'method', 'message'}
                assert saved['payload'] == config['payload'] and saved['path'] == expected_path and saved['method'] == 2
                assert saved['owner'] == config['owner'] and saved['server'] == config['url']
                assert all(term not in journal_raw for term in [config['token'].encode(), b'Bearer', b'password', b'Authorization'])
            if boundary in ['late_commit', 'recovery_kill']:
                released = named('original_commit_released_after_retry')[0]
                original = [row for row in named('transaction_committed_or_replayed') if row['first']][0]
                for clock in ['wall_ns', 'monotonic_ns']:
                    assert released[clock] < original[clock]
                if label == 'candidate':
                    rejected = named('retry_rejected_before_original_commit')
                    assert len(rejected) == 1 and rejected[0]['status'] == 409
                    rejected_disk = read(directory / 'journal-after-rejected-recovery.json')
                    assert rejected_disk['bytes_base64'] == first['bytes_base64'] and rejected_disk['sha256'] == first['sha256']
                    for clock in ['wall_ns', 'monotonic_ns']:
                        assert rejected[0][clock] < rejected_disk[clock] < released[clock] < original[clock]
                    if boundary == 'recovery_kill':
                        observed, retry_killed = named('recovery_observation_before_kill')[0], named('recovery_kill_confirmed')[0]
                        assert observed['observation']['pending'] and observed['observation']['result']['_status'] == 409
                        assert observed['pid'] == retry_killed['pid'] and retry_killed['returncode'] == -9
                        for clock in ['wall_ns', 'monotonic_ns']:
                            assert rejected[0][clock] < observed[clock] < retry_killed[clock] < rejected_disk[clock]
            phases = named('recovery_started')
            assert len({row['pid'] for row in [*initial, *phases]}) == 1 + len(phases)
            for finish in named('recovery_finished'):
                assert finish['returncode'] == (-9 if boundary == 'recovery_kill' and finish['phase'] == 'restarted-client' else 0)
            for log in directory.glob('*.log'):
                assert all(marker not in log.read_text() for marker in ['SCRIPT ERROR', 'ERROR:', 'Parse Error'])
            final_phase = 'after-late-commit' if boundary in ['late_commit', 'recovery_kill'] else 'restarted-client'
            observations = [json.loads(line.removeprefix('RECEIPT_PROBE ')) for line in (directory / f'{final_phase}.log').read_text().splitlines() if line.startswith('RECEIPT_PROBE ')]
            assert len(observations) == 1 and observations[0]['recovered'] == (label == 'candidate')
            if label == 'candidate':
                assert observations[0]['result'] == server_response and not observations[0]['pending']
            assert named('recovery_finished')[-1]['monotonic_ns'] < final['monotonic_ns']
            report['rows'].append({'label': label, 'kind': kind, 'boundary': boundary, 'recovered': observations[0]['recovered'],
                                   'debit': sum(costs), 'mutations': len(costs), 'inbound_requests': len(inbound), 'pids': [row['pid'] for row in [*initial, *phases]]})
        assert observed_grid == {(kind, boundary) for kind in ['store', 'case', 'market'] for boundary in ['before_commit', 'after_commit', 'late_commit', 'recovery_kill']}
        native = (RUN / label / 'lifecycle/native.log').read_text()
        assert all(marker not in native for marker in ['SCRIPT ERROR', 'ERROR:', 'Parse Error'])
        result = [json.loads(line.removeprefix('RECEIPT_LIFECYCLE ')) for line in native.splitlines() if line.startswith('RECEIPT_LIFECYCLE ')]
        assert len(result) == 1 and result[0] == summary['runs'][label]['lifecycle']
        retry, logout = result[0]['retry'], result[0]['logout']
        assert retry['pending_after_lost_response'] and retry['retry_status'] == 409
        assert retry['calls'][0] == retry['calls'][1]
        assert retry['pending_after_rejected_retry'] == retry['journal_after_rejected_retry'] == (label == 'candidate')
        assert logout['token_cleared'] and logout['account_cleared']
        assert logout['pending_after_logout'] == logout['pending_after_recreation'] == (label == 'candidate')
        assert not logout['pending_after_confirmation']
        if label == 'candidate':
            assert logout['calls'][0]['payload']['idempotency_key'] == '112a501d-3ca0-4811-9783-385cdecb073e'
            assert logout['calls'][0]['path'] == '/store/buy' and logout['calls'][0]['method'] == 2
            assert logout['result'] == {'item': {'id': 'fixture-server-confirmed-item'}, 'credits': 0}
            assert logout['account'] == {'credits': 0, 'xp': 0}
        report['lifecycle'][label] = result[0]
        label_rows = [row for row in report['rows'] if row['label'] == label]
        report['totals'][label] = {'recovered': sum(row['recovered'] for row in label_rows), 'cases': len(label_rows),
                                   'mutations': sum(row['mutations'] for row in label_rows), 'debit': sum(row['debit'] for row in label_rows)}
    return report


if __name__ == '__main__':
    print(json.dumps(main(), indent=2))
