"""Reconstruct the actual failed undelayed schedule without inventing input consumption."""
import argparse
import hashlib
import json
from pathlib import Path


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('receipts', type=Path)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
base = args.receipts / 'evidence/native-input'
read = lambda name: json.loads((base / name).read_text())
result, actions = read('results.json'), read('actions.json')
samples = read('authority-telemetry.json')['samples']
joined = [s for s in samples if s.get('joined_id') == 1 and 'ammo' in s]
begin = next(a for a in actions if a.get('event') == 'wait_begin' and a.get('label') == 'Authority confirms reload start')
timeout = next(a for a in actions if a.get('event') == 'wait_timeout' and a.get('label') == begin['label'])
last_bound = max((s for s in joined if s.get('peer_bound') is True), key=lambda s: s['wall_unix_msec'])
first_later_unbound = next(s for s in joined if s['wall_unix_msec'] > last_bound['wall_unix_msec'] and s.get('peer_bound') is False)
edges = [a for a in actions if a.get('event') == 'button_after'
         or a.get('event') == 'key_after' and a.get('key') == 'r']
client, server = ((base / (name + '.log')).read_text(errors='replace') for name in ('client', 'server'))
checks = {
    'ordinary_undelayed_original_failed': result.get('input_schedule') == 'legacy'
        and result.get('synthetic_fire_capture_delay_seconds') == 0 and result.get('passed') is False
        and result.get('error') == 'Authority confirms reload start',
    'original_ten_second_reload_start_wait_expires': begin['budget_seconds'] == 10
        and timeout['seconds'] - begin['seconds'] >= 10,
    'zero_observed_authority_fire_reload_or_shots': bool(joined)
        and all(s.get('shots') == 0 and s.get('ammo') == 30 and s.get('reserve') == 90
                and s.get('fire_input') is False and s.get('reload_input') is False
                and s.get('reload_remaining') == 0 for s in joined),
    'native_disconnect_reconnect_and_takeover_notices_retained':
        'Server disconnected. Attempting to reconnect' in client
        and client.count('Connected • LAN practice session') == 2
        and server.count('Operator disconnected; bot taking over') == 2,
    'actual_OS_fire_down_up_and_R_down_observed':
        [(a.get('event'), a.get('key'), a.get('down')) for a in edges]
        == [('button_after', None, True), ('button_after', None, False), ('key_after', 'r', True)]
        and edges[0]['native_state']['lmb_down'] is True and edges[1]['native_state']['lmb_down'] is False
        and edges[2]['native_state']['keys_down']['r'] is True,
    'missing_success_only_authority_summary_retained': not (base / 'authority.json').exists()
        and result.get('authority') is None,
    'original_failure_cleanup_retained': result.get('cleanup_errors') == []
        and len(result.get('commands', [])) == 2
        and all(c.get('exit_code') == 1 for c in result['commands']),
}
report = {'checks_of_failure_facts': checks, 'all_failure_fact_checks_passed': all(checks.values()),
          'original_result_passed': result.get('passed'), 'actual_elapsed_seconds': result['elapsed_seconds'],
          'original_wait_begin': begin, 'original_timeout': timeout,
          'last_peer_bound_sample': last_bound, 'first_later_unbound_sample': first_later_unbound,
          'native_sample_gap_msec': first_later_unbound['wall_unix_msec'] - last_bound['wall_unix_msec'],
          'actual_OS_edges': edges, 'all_authority_samples': len(samples), 'joined_actor_samples': len(joined),
          'last_failure_observation': result.get('failure_authority_observation'),
          'source_bindings': {name: hashlib.sha256((base / name).read_bytes()).hexdigest()
                              for name in ('results.json', 'actions.json', 'authority-telemetry.json', 'client.log', 'server.log')},
          'limits': ['The 38.836-second gap brackets the native LMB-down and cannot identify the exact disconnect time.',
                     'OS/API observations do not establish game consumption; no fire or reload was observed at authority.',
                     'This record establishes neither a missed-input cause nor product latency, frame rate or a causal source regression.']}
args.output.write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({'all_failure_fact_checks_passed': report['all_failure_fact_checks_passed'],
                  'joined_actor_samples': len(joined), 'failed_checks': [k for k, v in checks.items() if not v]}))
