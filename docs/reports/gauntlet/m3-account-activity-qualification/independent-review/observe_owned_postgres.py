#!/usr/bin/env python3
"""Observe only the named run's fake PostgreSQL; never read credentials."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import time

DOCKER = ['docker', '--host=unix:///var/run/docker.sock']
IMAGE = 'postgres:17@sha256:2d2b8998d31037bf721cfdf764d76ba74171b4fab3431b7f72c27c56ddbdf9e3'
CHECKPOINTS = ('earned-staged', 'earned-godot-killed', 'database-outage-pending',
               'database-restored-zero', 'backend-committed-ack-held',
               'lost-ack-worker-killed', 'worker-restarted-committed',
               'duplicate-replayed-unchanged')
QUERY = """SELECT json_build_object(
 'database_utc', clock_timestamp(),
 'read_only', current_setting('transaction_read_only'),
 'tables', json_build_object(
  'players', (SELECT coalesce(json_agg(row_to_json(p)), '[]') FROM
   (SELECT id,display_name,credits,xp FROM players ORDER BY id) p),
  'ledger', (SELECT coalesce(json_agg(row_to_json(l)), '[]') FROM
   (SELECT player_id,amount,balance_after,reason,reference FROM ledger ORDER BY player_id) l),
  'rewards', (SELECT coalesce(json_agg(row_to_json(r)), '[]') FROM
   (SELECT player_id,details FROM rewards ORDER BY player_id) r),
  'operations', (SELECT coalesce(json_agg(row_to_json(o)), '[]') FROM
   (SELECT id,request_hash,response FROM operations WHERE id LIKE 'match:%' ORDER BY id) o),
  'consumed_tickets', (SELECT coalesce(json_agg(row_to_json(t)), '[]') FROM
   (SELECT player_id,server_id,consumed_at IS NOT NULL AS consumed FROM game_tickets ORDER BY player_id) t)
 ));"""


def now():
    return datetime.now(timezone.utc).isoformat()


def read(path):
    try:
        return json.loads(path.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    run, output = args.run.resolve(), args.output.resolve()
    # Each observation attempt is immutable evidence, including failures.
    output.mkdir(parents=True, exist_ok=False)
    start = time.monotonic()
    deadline = start + 1800
    summary = dict(started_at_utc=now(), run=str(run), method='Independent docker exec psql; no credential or environment access',
                   sample_count=0, connection_attempts=0, psql_pids=[], status='waiting_for_owned_run')
    summary_file = output / 'observer-report.json'

    def save():
        summary_file.write_text(json.dumps(summary, indent=2) + '\n')

    save()
    while time.monotonic() < deadline:
        report = read(run / 'report.json')
        if report.get('postgres_port'):
            break
        time.sleep(.05)
    else:
        raise RuntimeError('No owned run before observer deadline')
    container = report['container']
    assert container.startswith('sightbreak-account-match-') and len(container) == len('sightbreak-account-match-') + 12
    # Inspect selected nonsecret fields of this exact container only.
    inspect_template = ('{"id":{{json .Id}},"name":{{json .Name}},"image":{{json .Config.Image}},'
                        '"auto_remove":{{json .HostConfig.AutoRemove}},"ports":{{json .NetworkSettings.Ports}},'
                        '"mounts":{{json .Mounts}}}')
    inspection = json.loads(subprocess.check_output(DOCKER + ['inspect', '--format', inspect_template, container], text=True))
    assert inspection['image'] == IMAGE and inspection['auto_remove'] is True
    assert inspection['name'] == '/' + container
    assert inspection['ports']['5432/tcp'] == [{'HostIp': '127.0.0.1', 'HostPort': str(report['postgres_port'])}]
    (output / 'owned-container-provenance.json').write_text(json.dumps(inspection, indent=2) + '\n')
    summary.update(status='observing', container=container, postgres_port=report['postgres_port'],
                   source_commit=report['source_commit'], game_tree=report['game_tree'])
    save()
    last_signature = None
    last_at = None
    max_gap = 0.0
    samples = (output / 'postgres-samples.jsonl').open('w')
    errors = (output / 'postgres-observer-stderr.txt').open('w')
    while time.monotonic() < deadline:
        report = read(run / 'report.json')
        if report.get('status') in ('passed', 'failed'):
            break
        summary['connection_attempts'] += 1
        command = DOCKER + ['exec', '-i', container, 'psql', '-X', '-q', '-A', '-t',
                            '-v', 'ON_ERROR_STOP=1', '-U', 'sightbreak', '-d', 'sightbreak_match_test']
        child = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=errors, text=True)
        summary['psql_pids'].append(child.pid)
        # The intentional outage closes the gameplay observer connection. On
        # reconnect, all Godot processes have exited and recovery is brief. Use
        # a tighter interval to observe commit before the held reply is released.
        recovery = (run / 'earned-staged.json').exists()
        interval = '.001' if recovery else '.05'
        child.stdin.write('SET default_transaction_read_only=on;\n' + QUERY + '\n\\watch ' + interval + '\n')
        child.stdin.flush()
        child.stdin.close()
        try:
            for line in child.stdout:
                if not line.startswith('{'):
                    continue
                item = json.loads(line)
                assert item['read_only'] == 'on'
                observed = time.monotonic()
                if last_at is not None:
                    max_gap = max(max_gap, observed - last_at)
                last_at = observed
                summary['sample_count'] += 1
                checkpoints = {name: read(run / (name + '.json')).get('at_utc') for name in CHECKPOINTS
                               if (run / (name + '.json')).exists()}
                signature = hashlib.sha256(json.dumps([item['tables'], checkpoints], sort_keys=True).encode()).hexdigest()
                if signature != last_signature:
                    item.update(observer_utc=now(), checkpoints_seen=checkpoints, sample_index=summary['sample_count'])
                    samples.write(json.dumps(item, separators=(',', ':')) + '\n')
                    samples.flush()
                    last_signature = signature
                    print('Owned SQL observation:', len(item['tables']['players']), 'players,',
                          len(item['tables']['ledger']), 'ledger,', len(item['tables']['rewards']), 'rewards,',
                          len(item['tables']['operations']), 'operations;', ','.join(checkpoints), flush=True)
                    save()
                report = read(run / 'report.json')
                if report.get('status') in ('passed', 'failed') or time.monotonic() >= deadline:
                    break
        finally:
            if child.poll() is None:
                child.terminate()
            try:
                child.wait(timeout=5)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait(timeout=5)
            child.stdout.close()
        time.sleep(.005 if (run / 'earned-staged.json').exists() else .05)
    samples.close()
    errors.close()
    summary.update(status='finished', finished_at_utc=now(), wall_seconds=time.monotonic() - start,
                   largest_sample_gap_seconds=max_gap, run_status=read(run / 'report.json').get('status'),
                   all_psql_children_reaped=True)
    save()


if __name__ == '__main__':
    main()
