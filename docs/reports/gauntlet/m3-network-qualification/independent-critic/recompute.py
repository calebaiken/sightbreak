#!/usr/bin/env python3
"""Read retained source/process evidence; launch no game processes or workloads."""
import argparse
import hashlib
import json
import statistics
from pathlib import Path

EXPECTED_SOURCE = '0ca125dfba637868e6e8e9772ff9c40400413e32'
CONDITIONS = ['rtt-0', 'rtt-50', 'rtt-100', 'rtt-150', 'rtt-200', 'jitter',
              'loss', 'reorder', 'impaired', 'blackout', 'reconnect', 'prediction-disabled']


def read(path):
    return json.loads(path.read_text())


def percentile(values, fraction):
    return sorted(values)[int((len(values)-1)*fraction)] if values else None


def logs_at(directory):
    results = []
    for path in sorted(directory.glob('*.log')):
        content = path.read_text(errors='replace')
        results.append({'path': path.name, 'godot_4_7_2': 'Godot Engine v4.7.2' in content,
                        'error': 'ERROR:' in content or 'SCRIPT ERROR' in content,
                        'resource_leak': 'ObjectDB instances leaked' in content or 'Leaked instance' in content})
    return results


def soak(directory):
    summary = read(directory/'summary.json')
    clients = [read(directory/f'client-{i}.json') for i in range(10)]
    server = read(directory/'server.json')
    recovery = [item for client in clients for item in client['recoveries']]
    times = [item['seconds'] for item in recovery]
    logs = logs_at(directory)
    checks = {
        'source_clean': summary['source'] == {'commit': EXPECTED_SOURCE, 'dirty': False},
        'summary_equals_raw': summary['processes'] == [server, *clients],
        'all_process_reports_pass': all(item['passed'] for item in [server, *clients]),
        'eight_reconnects_each': all(item['reconnects'] == 8 and len(item['recoveries']) == 8 for item in clients),
        'same_actor_each': all(item['same_actor_id'] and len({r['actor'] for r in item['recoveries']}) == 1 for item in clients),
        'ten_distinct_actors': len({item['recoveries'][0]['actor'] for item in clients}) == 10,
        'all_recovery_acks_positive': all(item['ack'] > 0 for item in recovery),
        'bounded_transport_peak': server['max_transports'] == server['max_peers'] == 10,
        'six_forced_round_resets': server['resets'] == 6,
        'eleven_clean_472_logs': len(logs) == 11 and all(l['godot_4_7_2'] and not l['error'] and not l['resource_leak'] for l in logs),
    }
    memory = server['static_memory_samples']
    return {'checks': checks, 'recovery_count': len(times), 'recovery_seconds': {
        'minimum': min(times), 'median': statistics.median(times), 'p95_lower_rank': percentile(times, .95), 'maximum': max(times)},
        'ack_range': [min(r['ack'] for r in recovery), max(r['ack'] for r in recovery)],
        'server': server, 'memory_sample_delta_bytes': memory[-1]-memory[0],
        'logs': logs,
        'limits': ['End-of-run empty temporary/binding dictionaries are asserted by fixture but their raw counts are not emitted.',
                   'Ten reservations remain within the source-defined 60 simulation-second expiry window.',
                   'Six memory samples over 64 simulation seconds do not establish leak freedom.']}


def condition(directory, row, expected_source=EXPECTED_SOURCE):
    summary = read(directory/'summary.json')
    server = read(directory/'server.json')
    clients = [read(directory/f'client-{i}.json') for i in range(10)]
    occupancy = server['occupancy']
    latest = occupancy[-1]['bindings']
    logs = logs_at(directory)
    ticks = server['tick_usec']
    intervals = server['tick_intervals_usec']
    prediction_errors = [e for client in clients for e in client['prediction_errors_m']]
    route_traffic = summary['per_client_traffic']
    traffic_equal = all(sum(route[direction][key] for route in route_traffic) == summary['traffic'][direction][key]
                        for direction in ('up', 'down') for key in ('received_packets', 'forwarded_packets', 'dropped_packets', 'udp_payload_bytes', 'datagrams_over_1200'))
    checks = {
        'campaign_exit_zero': row['exit'] == 0,
        'campaign_summary_equals_raw': row['summary'] == summary,
        'source_clean': summary['source']['commit'] == expected_source and summary['source']['dirty'] is False,
        'ten_clients': summary['conditions']['clients'] == len(clients) == 10,
        'no_reported_failures': summary['failures'] == [],
        'measurement_shared_stop': summary['shared_stop_reached'],
        'all_clients_fresh': all(c['state'] == 'connected' and c['accepted_snapshots'] >= 10 and c['last_accepted_age_seconds'] < .75 for c in clients),
        'all_clients_moved': all(c['max_displacement'] > .1 for c in clients),
        'unique_initial_actor_ids': len({c['initial_id'] for c in clients}) == 10,
        'all_final_actor_ids_match': all(c['initial_id'] == c['final_id'] for c in clients),
        'sampled_transport_and_authority_bounds': bool(occupancy) and all(len(o['enet']) <= 10 and len(o['bindings']) <= 10 and len({b['actor'] for b in o['bindings']}) == len(o['bindings']) for o in occupancy),
        'ten_final_bindings': len(latest) == 10,
        'fresh_final_input_authority': all(b['input_ack'] >= 10 and b['idle_msec'] < 750 for b in latest),
        'eleven_clean_472_logs': len(logs) == 11 and all(l['godot_4_7_2'] and not l['error'] and not l['resource_leak'] for l in logs),
        'traffic_reconciles': traffic_equal,
        'tick_p95_reconciles': percentile(ticks, .95) == summary['tick_usec_p95'],
        'interval_p95_reconciles': percentile(intervals, .95) == summary['tick_interval_usec_p95'],
        'prediction_error_p95_reconciles': percentile(prediction_errors, .95) == summary['prediction_error_at_ack_p95_m'],
    }
    if summary['conditions'].get('reconnect_at', -1) >= 0:
        checks['all_reconnect_pass'] = all(c['reconnect_requested'] and c['reconnect_passed'] for c in clients)
    recovery = [c['recovery_seconds'] for c in clients if c['recovery_seconds'] >= 0]
    result = {'name': directory.name, 'checks': checks,
            'maximum_accepted_age_seconds': max(c['last_accepted_age_seconds'] for c in clients),
            'final_input_ack_range': [min(b['input_ack'] for b in latest), max(b['input_ack'] for b in latest)],
            'maximum_final_input_idle_msec': max(b['idle_msec'] for b in latest),
            'maximum_sampled_transports': max(len(o['enet']) for o in occupancy),
            'maximum_sampled_bindings': max(len(o['bindings']) for o in occupancy),
            'occupancy_samples': len(occupancy),
            'same_actor_welcome_recovery_seconds': {'minimum': min(recovery), 'maximum': max(recovery)} if recovery else None,
            'start_offset_seconds': {'minimum': min(c['measurement_start_offset_seconds'] for c in [server, *clients]), 'maximum': max(c['measurement_start_offset_seconds'] for c in [server, *clients])},
            'maximum_stop_lateness_seconds': max(c['measurement_stop_lateness_seconds'] for c in [server, *clients]),
            'tick_usec': {'p50': percentile(ticks, .5), 'p95': percentile(ticks, .95), 'maximum': max(ticks)},
            'tick_interval_usec': {'p50': percentile(intervals, .5), 'p95': percentile(intervals, .95), 'maximum': max(intervals)},
            'prediction_error_p95_m': percentile(prediction_errors, .95),
            'hard_corrections': sum(c['hard_corrections'] for c in clients),
            'server_rss_peak_kib': summary['processes']['server']['rss_peak_kib'],
            'traffic': summary['traffic'], 'logs': logs}
    if summary['conditions'].get('reconnect_at', -1) >= 0:
        first_acks = []
        for final in latest:
            first = next((o for o in occupancy if any(b['peer'] == final['peer'] and b['input_ack'] > 0 for b in o['bindings'])), None)
            initial_peer = next(b['peer'] for o in occupancy for b in o['bindings'] if b['actor'] == final['actor'])
            upper_bound = (server['wall_elapsed_seconds'] + (first['msec'] - occupancy[-1]['msec'])/1000
                           - summary['conditions']['reconnect_at']) if first else None
            first_acks.append({'actor': final['actor'], 'initial_peer': initial_peer, 'final_peer': final['peer'],
                               'peer_changed': initial_peer != final['peer'],
                               'first_positive_ack_close_relative_upper_bound_seconds': upper_bound})
        result['first_ack_bounds'] = {
            'method': 'Last server occupancy precedes the report callback wall-time read. Therefore first positive ACK sample A is no later than report.wall_elapsed_seconds+(A.msec-last_occupancy.msec)/1000. Subtract nominal close time; actual close is at or after that time. Bounds apply only to emitted final bindings and do not measure client ACK delivery.',
            'rows': first_acks}
    return result


def campaign(directory, expected_source=EXPECTED_SOURCE):
    entries = read(directory/'campaign.json')
    rows = []
    for entry in entries:
        try:
            rows.append(condition(directory/entry['name'], entry, expected_source))
        except (KeyError, ValueError, FileNotFoundError, IndexError) as error:
            rows.append({'name': entry['name'], 'incomplete': str(error)})
    return {'source_expected': expected_source, 'twelve_conditions_present': [r['name'] for r in entries] == CONDITIONS, 'rows': rows}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--extra-condition', type=Path, action='append', default=[])
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    output = args.source/'builds/session-qualification'
    result = {'soak': soak(output/'ten-client-soak-r1')}
    campaign_path = output/'ten-client-campaign-r1'
    if (campaign_path/'campaign.json').exists():
        result['campaign'] = campaign(campaign_path)
    result['extra_conditions'] = [condition(path, {'exit': 0, 'summary': read(path/'summary.json')}) for path in args.extra_condition]
    for row in result['extra_conditions']:
        # Standalone runs have no campaign exit receipt. This reviewer does not
        # invent one; caller supplies the original controller receipt separately.
        row['checks'].pop('campaign_exit_zero')
        row['checks'].pop('campaign_summary_equals_raw')
    baseline = args.source/'docs/reports/three-agent-evidence/stabilization-v2/network-r2-imported'
    result['baseline'] = campaign(baseline, '701ce2c4d7f8b2872cf1fefa64cb6edd0cd1a3fd')
    (args.out/'raw-checks.json').write_text(json.dumps(result, indent=2)+'\n')
    files = [p for p in output.glob('*') if p.is_file()]
    for directory in [output/'ten-client-soak-r1', output/'ten-client-campaign-r1', output/'network-probe-raw',
                      output/'protocol-matrix-raw', output/'hostile-handshake-raw', *args.extra_condition]:
        files += [p for p in directory.rglob('*') if p.is_file() and p.suffix in ('.json', '.log', '.txt', '.md')]
    files += [p for p in baseline.rglob('*.json') if p.is_file()]
    files += [args.source/p for p in ['AGENTS.md', 'docs/roadmap/SIGHTBREAK_V1_ACCEPTANCE.md', 'docs/roadmap/SIGHTBREAK_V1_PROGRESS.md',
              'docs/network/RECONNECT_RECOVERY.md', 'scripts/test_network_soak.py', 'scripts/fixtures/network_soak.gd',
              'scripts/run_network_campaign.py', 'scripts/simulate_network.py', 'game/tests/network_simulation_probe.gd',
              'game/scripts/gameplay/match.gd', 'game/scripts/network/input_stream.gd', 'game/scripts/network/state_privacy.gd']]
    manifest = [{'path': str(p.relative_to(args.source)), 'bytes': p.stat().st_size,
                 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(files)]
    (args.out/'raw-source-sha256.json').write_text(json.dumps(manifest, indent=2)+'\n')
    print(json.dumps({'soak_checks': result['soak']['checks'], 'campaign_conditions': len(result.get('campaign', {}).get('rows', [])),
                      'failures': [{'condition': r['name'], 'failed_checks': [name for name, ok in r.get('checks', {}).items() if not ok],
                                    **({'incomplete':r['incomplete']} if 'incomplete' in r else {})}
                                   for r in [*result.get('campaign', {}).get('rows', []), *result['extra_conditions']]
                                   if 'incomplete' in r or not all(r['checks'].values())]}, indent=2))


if __name__ == '__main__':
    main()
