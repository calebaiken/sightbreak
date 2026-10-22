#!/usr/bin/env python3
"""Recompute the declared fixed-window outcomes from native authority rows."""
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
ERROR = re.compile(r'SCRIPT ERROR|ERROR:|ObjectDB instances leaked|resources still in use', re.I)


def verify_source(name):
    directory = ROOT / name
    summary = json.loads((directory / 'summary.json').read_text())
    assert summary['source_unchanged']
    assert not summary['source_before']['status']
    assert len(summary['checks']) == 9
    assert len(summary['trials']) == 8
    checks = []
    for check in summary['checks']:
        log = directory / check['log']
        assert check['exit'] == 0 and not ERROR.search(log.read_text())
        assert hashlib.sha256(log.read_bytes()).hexdigest() == check['log_sha256']
    for trial in summary['trials']:
        folder = directory / trial['directory']
        metrics = json.loads((folder / 'metrics.json').read_text())
        assert metrics == trial['metrics']
        server = json.loads((folder / 'server.json').read_text())
        client = json.loads((folder / 'client.json').read_text())
        rows = server['rows']
        assert all(a['t'] <= b['t'] for a, b in zip(rows, rows[1:]))
        assert all(a['simulation_t'] <= b['simulation_t'] for a, b in zip(rows, rows[1:]))
        assert len(rows) > 100
        assert all(code == 0 for code in metrics['exits'].values())
        assert not any(ERROR.search((folder / (role + '.log')).read_text()) for role in ('server', 'client'))
        assert metrics['transport_authority_privacy_pass']
        assert server['protocol'] == 6 and client['privacy_violations'] == 0 and server['hit_history_frames'] == 0
        assert client['prediction'] == metrics['prediction'] and client['max_pending'] <= 120
        assert all(metrics['barrier_read_retries'][role] > 0 for role in ('server', 'client'))
        window = [r for r in rows if 3.8 <= r['t'] <= 4.8]
        assert window
        displacement = abs(window[-1]['x'] - window[0]['x'])
        speed = max(abs(r['vx']) for r in window)
        assert abs(displacement - metrics['stale_window_displacement_m']) < 1e-9
        assert abs(speed - metrics['stale_window_max_speed_mps']) < 1e-9
        if metrics['scenario'] == 'stale-replay':
            outcome = 31.5 <= server['disconnected_at'] <= 32.5 and all(server[k] == 0 for k in ('final_peer_count', 'lifecycle_entries', 'input_queues', 'pending_joins'))
        else:
            recovery = [r for r in rows if 7.0 <= r['t'] <= 7.8]
            assert recovery and max(r['vx'] for r in recovery) < -.9
            assert server['shots'] == 2 and rows[-1]['ammo'] == 13 and server['final_peer_count'] == 1
            if metrics['scenario'] == 'snapshot-gap':
                assert client['max_pending'] == 120 and client['dropped_snapshots'] > 0
                before_resume = [r for r in rows if 2.0 <= r['t'] < 4.8]
                changes = [r for i, r in enumerate(before_resume) if i == 0 or r['ack'] != before_resume[i - 1]['ack']]
                last_ack = changes[-1]['t']
                stopped = [r for r in rows if last_ack <= r['t'] < 5 and abs(r['vx']) < .001 and abs(r['move_x']) < .001]
                stop_delay = stopped[0]['t'] - last_ack if stopped else None
                assert stop_delay == metrics['stop_after_last_ack_seconds']
                outcome = displacement < .001 and speed < .001 and stop_delay is not None and stop_delay <= .35
            else:
                outcome = True
        assert outcome == metrics['improvement_gate']
        checks.append({'case': trial['directory'], 'meets_declared_outcome': outcome, 'stale_displacement_m': displacement,
                       'max_speed_mps': speed, 'stop_after_last_ack_s': metrics['stop_after_last_ack_seconds'],
                       'retired_at_s': server['disconnected_at']})
    return {'source': summary['source_before'], 'native_pairs': len(checks), 'declared_outcomes_met': sum(c['meets_declared_outcome'] for c in checks),
            'focused_groups': len(summary['checks']), 'checks': checks,
            'probe_sha256': summary['probe_sha256'], 'driver_sha256': summary['driver_sha256'], 'godot_sha256': summary['godot_sha256']}

if __name__ == '__main__':
    results = {name: verify_source(name) for name in ('baseline-r1', 'candidate-r1')}
    for key in ('probe_sha256', 'driver_sha256', 'godot_sha256'):
        assert results['baseline-r1'][key] == results['candidate-r1'][key]
    print(json.dumps({'verification': 'PASS', 'scope': 'Recomputed native headless source outcomes, not independent approval or platform release acceptance', 'results': results}, indent=2))
