#!/usr/bin/env python3
"""Run one unchanged real ENet activity oracle on a frozen product checkout."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / 'game/tests/activity_provenance_probe.gd'
ERROR = re.compile(r'SCRIPT ERROR|ERROR:|ObjectDB instances leaked|resources still in use', re.I)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def identity(source):
    return {key: subprocess.check_output(['git', *args], cwd=source, text=True).strip()
            for key, args in [('commit', ['rev-parse', 'HEAD']), ('status', ['status', '--porcelain'])]}


def trial(godot, source, out, scenario):
    out.mkdir()
    barrier = out / 'barrier'
    barrier.mkdir()
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    children, logs, commands = {}, {}, {}
    env = os.environ.copy()
    for key in ('SIGHTBREAK_SERVER_KEY', 'SIGHTBREAK_JOIN_TICKET', 'SIGHTBREAK_RESULT_SPOOL'):
        env.pop(key, None)
    try:
        for role in ('server', 'client'):
            commands[role] = [str(godot), '--headless', '--path', str(source / 'game'), '--max-fps', '60', '--script', str(PROBE),
                              '--', f'--role={role}', f'--scenario={scenario}', f'--port={port}',
                              f'--output={out / (role + ".json")}', f'--barrier={barrier}']
            logs[role] = (out / (role + '.log')).open('wb')
            children[role] = subprocess.Popen(commands[role], cwd=source, env=env, stdout=logs[role], stderr=subprocess.STDOUT)
            deadline = time.monotonic() + 40
            while not (out / (role + '.json.ready')).exists():
                if children[role].poll() is not None or time.monotonic() >= deadline:
                    raise RuntimeError(f'{role} readiness failed: {out}')
                time.sleep(.02)
        (barrier / 'start.tmp').write_text(json.dumps({'epoch': time.time() + .4}))
        os.replace(barrier / 'start.tmp', barrier / 'start.json')
        deadline = time.monotonic() + 20
        while not all((out / (role + '.json')).exists() for role in children):
            if any(p.poll() is not None for p in children.values()) or time.monotonic() >= deadline:
                raise RuntimeError(f'incomplete reports: {out}')
            time.sleep(.02)
        (barrier / 'stop').write_text('observations latched')
        exits = {role: p.wait(timeout=10) for role, p in children.items()}
    finally:
        for p in children.values():
            if p.poll() is None:
                p.kill()
                p.wait()
        for log in logs.values():
            log.close()
    server = json.loads((out / 'server.json').read_text())
    client = json.loads((out / 'client.json').read_text())
    rows = [r for r in server['rows'] if .7 <= r['t'] <= 3.8]
    renewals = sum(rows[i]['last_activity'] > rows[i - 1]['last_activity'] for i in range(1, len(rows)))
    stable = all(abs(r['x'] - rows[0]['x']) < .0001 and abs(r['z'] - rows[0]['z']) < .0001
                 and r['ammo'] == rows[0]['ammo'] and r['interaction_count'] == 0 for r in rows)
    actual_aim_changes = sum(abs(rows[i]['yaw'] - rows[i - 1]['yaw']) > .004 for i in range(1, len(rows)))
    result = {'scenario': scenario, 'commands': commands, 'exits': exits, 'renewals': renewals,
              'actual_aim_changes': actual_aim_changes, 'stable_pose_ammo_no_objective': stable,
              'ack_advances': rows[-1]['ack'] - rows[0]['ack'], 'samples': len(rows),
              'protocol': server['protocol'], 'client_packets': client['packets'], 'client_snapshots': client['snapshots'],
              'native_errors': {role: bool(ERROR.search((out / (role + '.log')).read_text())) for role in children},
              'authority_active': all(r['peers'] == 1 for r in rows),
              'unranked_fixture': not server['ranked_started'] and not client['ranked_started'],
              'prediction_off': not server['prediction'] and not client['prediction'],
              'live_rewind_off': server['hit_history_frames'] == 0}
    result['controls_pass'] = (all(code == 0 for code in exits.values()) and not any(result['native_errors'].values())
                               and stable and result['ack_advances'] >= 30 and len(rows) >= 100
                               and result['protocol'] == 6 and result['authority_active'] and result['unranked_fixture']
                               and result['prediction_off'] and result['live_rewind_off'] and client['snapshots'] >= 20)
    result['activity_gate'] = renewals == 0 and actual_aim_changes == 0 if scenario == 'stale-tail' else renewals >= 3 and actual_aim_changes >= 3
    result['raw_sha256'] = {p.name: sha(p) for p in out.iterdir() if p.is_file()}
    (out / 'metrics.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--godot', type=Path, required=True)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--expect-fixed', action='store_true')
    args = parser.parse_args()
    source, out, godot = args.source.resolve(), args.out.resolve(), args.godot.resolve()
    if source in out.parents or out == source:
        parser.error('evidence must be outside measured source')
    before = identity(source)
    if before['status']:
        parser.error('source must be clean')
    out.mkdir(parents=True, exist_ok=False)
    report = {'source_before': before, 'driver_sha256': sha(Path(__file__)), 'probe_sha256': sha(PROBE),
              'godot_sha256': sha(godot), 'match_sha256': sha(source / 'game/scripts/gameplay/match.gd'),
              'input_stream_sha256': sha(source / 'game/scripts/network/input_stream.gd'), 'trials': []}
    for scenario in ('stale-tail', 'real-look'):
        report['trials'].append(trial(godot, source, out / scenario, scenario))
    report['source_after'] = identity(source)
    report['controls_pass'] = before == report['source_after'] and all(t['controls_pass'] for t in report['trials'])
    report['activity_gate'] = all(t['activity_gate'] for t in report['trials'])
    (out / 'summary.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'controls_pass': report['controls_pass'], 'activity_gate': report['activity_gate'],
                      'trials': [{k: t[k] for k in ('scenario', 'renewals', 'actual_aim_changes', 'ack_advances')} for t in report['trials']]}))
    return 0 if report['controls_pass'] and (report['activity_gate'] or not args.expect_fixed) else 1


if __name__ == '__main__':
    raise SystemExit(main())
