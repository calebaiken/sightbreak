#!/usr/bin/env python3
"""Join independently recorded source/process/SQL identities to one fresh run."""
from datetime import datetime
import hashlib
import json
from pathlib import Path
import sys

run, review, output = (Path(arg).resolve() for arg in sys.argv[1:4])
expected_source, expected_game = sys.argv[4:6]
observations = Path(sys.argv[6]).resolve()


def load(path):
    return json.loads(path.read_text())


def stamp(value):
    return datetime.fromisoformat(value.replace('Z', '+00:00'))


report = load(run / 'report.json')
before, after = (load(review / name) for name in ('source-before.json', 'source-after.json'))
assert before == after, 'Frozen source or pinned engine changed during execution'
assert report['source_dirty'] is False
assert report['source_commit'] == before['source_commit'] == expected_source
assert report['game_tree'] == before['trees']['game'][before['source_commit']] == expected_game
for path, digest in report['sha256'].items():
    assert before['files'][path]['sha256'] == digest
    assert hashlib.sha256((Path(before['worktree']) / path).read_bytes()).hexdigest() == digest
assert report['engine']['sha256'] == before['engine']['sha256']
assert report['engine']['path'] == before['engine']['path']
live = load(review / 'live-processes.json')
assert live['source_commit'] == report['source_commit'] and live['game_port'] == report['game_port']
native = [p for p in live['children'] if 'role' in p]
assert len(native) == live['native_count'] == 11
assert sum(p['role'] == 'server' for p in native) == 1
assert all(p['exe'] == report['engine']['path'] and p['exe_sha256'] == report['engine']['sha256'] for p in native)
assert all(p['ppid'] == live['driver_pid'] for p in native)
assert {p['pid'] for p in live['children']} <= {p['pid'] for p in report['process_exits']}
assert len(live['owned_game_bindings']) == 1
binding = live['owned_game_bindings'][0]
assert binding['protocol'] == 'udp6' and binding['local_hex'].split(':')[0] == '0' * 32
assert int(binding['local_hex'].split(':')[1], 16) == report['game_port']
observer = load(observations / 'observer-report.json')
container = load(observations / 'owned-container-provenance.json')
assert observer['status'] == 'finished' and observer['run_status'] == report['status']
assert observer['source_commit'] == report['source_commit'] and observer['game_tree'] == report['game_tree']
assert observer['container'] == report['container'] and observer['postgres_port'] == report['postgres_port']
assert container['name'] == '/' + report['container'] and container['auto_remove'] is True
assert container['ports'] == {'5432/tcp': [{'HostIp': '127.0.0.1', 'HostPort': str(report['postgres_port'])}]}
samples = [json.loads(line) for line in (observations / 'postgres-samples.jsonl').read_text().splitlines()]
assert samples and observer['sample_count'] >= len(samples)
assert all(stamp(report['started_at_utc']) <= stamp(p['database_utc']) <= stamp(report['finished_at_utc']) for p in samples)
assert all(p['read_only'] == 'on' for p in samples)
cleanup = load(review / 'independent-cleanup.json')
assert observer['post_replay_owned_query_status'] == 'observed'
assert cleanup['status'] == 'passed' and cleanup['container'] == report['container']
result = dict(status='passed', source_commit=report['source_commit'], game_tree=report['game_tree'],
              before_after_source_equal=True, report_file_hashes_match=True,
              native_count=len(native), observed_engine_sha256=report['engine']['sha256'],
              observed_game_binding=binding, owned_container=report['container'],
              retained_sql_observations=len(samples), actual_sql_samples=observer['sample_count'],
              sql_samples_inside_run_utc_bounds=True, observer_finished=True,
              independently_verified_cleanup=True)
output.write_text(json.dumps(result, indent=2) + '\n')
print('Independent source/process/SQL/cleanup join passed for', report['source_commit'])
