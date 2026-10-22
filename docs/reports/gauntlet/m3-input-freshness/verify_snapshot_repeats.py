#!/usr/bin/env python3
"""Recompute the unchanged snapshot-stop gate for critic-requested repeat trials."""
import json
import math
from pathlib import Path
import re
import statistics

ROOT = Path(__file__).resolve().parent
ERROR = re.compile(r'SCRIPT ERROR|ERROR:|ObjectDB instances leaked|resources still in use', re.I)

def verify():
    folder = ROOT / 'candidate-snapshot-repeats-r1'
    summary = json.loads((folder / 'summary.json').read_text())
    initial = json.loads((ROOT / 'candidate-r1/summary.json').read_text())
    assert summary['source_unchanged'] and not summary['source_before']['status']
    assert summary['source_before']['game_tree'] == initial['source_before']['game_tree']
    for key in ('probe_sha256', 'driver_sha256', 'godot_sha256'):
        assert summary[key] == initial[key]
    assert len(summary['trials']) == 6 and summary['checks'] == []
    assert {row['directory'] for row in summary['trials']} == {f'{n}-snapshot-gap-prediction-{mode}' for n in (1, 2, 3) for mode in ('off', 'on')}
    results = []
    for trial in summary['trials']:
        path = folder / trial['directory']
        server = json.loads((path / 'server.json').read_text())
        client = json.loads((path / 'client.json').read_text())
        metrics = json.loads((path / 'metrics.json').read_text())
        assert metrics == trial['metrics']
        assert all(value == 0 for value in metrics['exits'].values())
        for role in ('server', 'client'):
            text = (path / (role + '.log')).read_text()
            assert not ERROR.search(text)
            assert 'INPUT_FRESHNESS_PROBE role=' + role in text
            assert metrics['barrier_read_retries'][role] > 0
        assert server['protocol'] == 6 and server['hit_history_frames'] == 0
        assert client['privacy_violations'] == 0 and client['prediction'] == metrics['prediction']
        assert client['max_pending'] == 120 and client['dropped_snapshots'] > 0
        rows = server['rows']
        client_rows = client['rows']
        assert len(rows) > 100 and len(client_rows) > 100
        assert all(b['t'] >= a['t'] for a, b in zip(client_rows, client_rows[1:]))
        assert all(math.isfinite(r['t']) and math.isfinite(r['x']) for r in client_rows)
        for before, after in zip(rows, rows[1:]):
            assert after['t'] >= before['t'] and after['simulation_t'] >= before['simulation_t'] and after['ack'] >= before['ack']
        assert all(math.isfinite(r[key]) for r in rows for key in ('t', 'simulation_t', 'x', 'vx'))
        window = [r for r in rows if 3.8 <= r['t'] <= 4.8]
        displacement = abs(window[-1]['x'] - window[0]['x'])
        speed = max(abs(r['vx']) for r in window)
        fresh = [r for r in rows if 2 <= r['t'] < 4.8]
        changes = [r for index, r in enumerate(fresh) if index == 0 or r['ack'] != fresh[index - 1]['ack']]
        last_ack = changes[-1]['t']
        stopped = [r for r in rows if last_ack <= r['t'] < 5 and abs(r['vx']) < .001 and abs(r['move_x']) < .001]
        delay = stopped[0]['t'] - last_ack if stopped else None
        assert displacement < .001 and speed < .001 and delay is not None and delay <= .350
        assert abs(delay - metrics['stop_after_last_ack_seconds']) < 1e-9
        recovery = [r for r in rows if 7 <= r['t'] <= 7.8]
        assert recovery and max(r['vx'] for r in recovery) < -.9
        assert server['shots'] == 2 and rows[-1]['ammo'] == 13 and server['final_peer_count'] == 1
        assert metrics['transport_authority_privacy_pass'] and metrics['recovery_and_edges_pass'] and metrics['improvement_gate']
        results.append({'case': trial['directory'], 'authority_rows': len(rows), 'client_rows': len(client_rows), 'stop_after_last_ack_s': delay,
                        'minimum_bound_margin_s': .350 - delay, 'stale_displacement_m': displacement, 'stale_max_speed_mps': speed,
                        'max_sample_interval_s': max(b['t'] - a['t'] for a, b in zip(rows, rows[1:])),
                        'authority_equal_millisecond_clock_pairs': sum(a['t'] == b['t'] for a, b in zip(rows, rows[1:])),
                        'client_equal_millisecond_clock_pairs': sum(a['t'] == b['t'] for a, b in zip(client_rows, client_rows[1:])),
                        'recovery_largest_vx_mps': max(r['vx'] for r in recovery), 'passed': True})
    initial_delays = [row['metrics']['stop_after_last_ack_seconds'] for row in initial['trials'] if row['metrics']['scenario'] == 'snapshot-gap']
    delays = initial_delays + [r['stop_after_last_ack_s'] for r in results]
    return {'verification': 'PASS', 'scope': 'Focused repeats under unchanged gates, not independent approval or a hardware-wide timing guarantee',
            'source': summary['source_before'], 'source_unchanged': summary['source_unchanged'],
            'same_game_tree_driver_probe_engine_as_initial': True, 'extra_native_pairs': 6, 'extra_clean_peer_exits': 12,
            'extra_stop_delay_range_s': [min(r['stop_after_last_ack_s'] for r in results), max(r['stop_after_last_ack_s'] for r in results)],
            'combined_snapshot_trials': len(delays), 'combined_stop_delay_range_s': [min(delays), max(delays)],
            'combined_stop_delay_median_s': statistics.median(delays), 'unchanged_limit_s': .350,
            'smallest_observed_margin_s': .350 - max(delays), 'results': results}

if __name__ == '__main__':
    print(json.dumps(verify(), indent=2))
