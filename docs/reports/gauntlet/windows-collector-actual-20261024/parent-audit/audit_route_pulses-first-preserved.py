"""Read actual route pulse API/OS brackets; game consumption is a separate gate."""
import argparse
import hashlib
import json
import math
from pathlib import Path


def number(value):
    return type(value) in (int, float) and math.isfinite(value)


def audit(root):
    directory = root / 'evidence/offline-input'
    result = json.loads((directory / 'results.json').read_text())
    actions = json.loads((directory / 'actions.json').read_text())
    route = result.get('settings_cover_route', {})
    pulses = route.get('native_pulses', [])
    before = [a for a in actions if a.get('event') == 'settings_route_native_pulse_before']
    after = [a for a in actions if a.get('event') == 'settings_route_native_pulse_after']
    rows = []
    for index, pulse in enumerate(pulses):
        keys = pulse.get('keys', [])
        states = pulse.get('os_states', [])
        down_checks = pulse.get('down_checks', [])
        edges = pulse.get('edges', [])
        samples = states + [s for check in down_checks for s in check.get('os_states', [])]
        first = states[0] if states else {}
        checks = {
            'actual_completed_API_status': pulse.get('status') == 'API_RETURNED_WITH_OS_RELEASE',
            'valid_request': isinstance(keys, list) and 1 <= len(keys) <= 2 and len(set(keys)) == len(keys)
                and all(k in ('w', 'a', 's', 'd') for k in keys)
                and not {'w', 's'} <= set(keys) and not {'a', 'd'} <= set(keys)
                and number(pulse.get('requested_seconds')) and 0 < pulse['requested_seconds'] <= 2.5,
            'same_original_absolute_deadline': pulse.get('absolute_deadline') == route.get('original_second_live_absolute_deadline')
                and number(pulse.get('finished_monotonic'))
                and pulse.get('finished_monotonic', math.inf) < pulse.get('absolute_deadline', -math.inf),
            'original_published_request_and_receipt': index < len(before) and index < len(after)
                and before[index].get('keys') == keys
                and before[index].get('requested_seconds') == pulse.get('requested_seconds')
                and after[index].get('receipt') == pulse
                and before[index]['seconds'] <= after[index]['seconds'],
            'all_requested_downs_and_releases': pulse.get('attempted_keys') == keys == pulse.get('released_keys')
                and pulse.get('release_errors') == [] and pulse.get('release_complete') is True
                and [(e.get('key'), e.get('down')) for e in edges] == [(k, True) for k in keys] + [(k, False) for k in keys],
            'every_native_edge_has_ordered_API_brackets': bool(edges) and all('error' not in e
                and number(e.get('before_monotonic')) and number(e.get('after_monotonic'))
                and e['before_monotonic'] <= e['after_monotonic'] for e in edges)
                and all(a['after_monotonic'] <= b['before_monotonic'] for a, b in zip(edges, edges[1:])),
            'every_down_has_fresh_same_owner_check': [c.get('key') for c in down_checks] == keys
                and all(c.get('status') == 'CHECKED' and c.get('owned_keys') == keys[:i]
                    and len(c.get('os_states', [])) == 1
                    and c['os_states'][0].get('label') == 'before_key_down'
                    and c['os_states'][0].get('lmb_down') is False
                    and not any(v and k not in keys[:i] for k, v in c['os_states'][0].get('keys_down', {}).items())
                    and c.get('read_end_monotonic', math.inf) < pulse.get('hold_until_monotonic', -math.inf)
                    and c.get('read_end_monotonic', math.inf) <= edges[i].get('before_monotonic', -math.inf)
                    for i, c in enumerate(down_checks)),
            'all_OS_reads_same_visible_focused_owned_window': bool(samples)
                and type(first.get('expected_pid')) is int and first['expected_pid'] > 0
                and type(first.get('target_window')) is int and first['target_window'] > 0
                and all(s.get('visible') is True and s.get('window_thread', 0) > 0
                    and s.get('expected_pid') == s.get('window_pid') == first['expected_pid']
                    and s.get('target_window') == s.get('foreground_window') == first['target_window']
                    and set(s.get('keys_down', {})) == {'w', 'a', 's', 'd'}
                    and number(s.get('read_begin_monotonic')) and number(s.get('read_end_monotonic'))
                    and s['read_begin_monotonic'] <= s['read_end_monotonic'] for s in samples),
            'initial_and_final_OS_controls_neutral': len(states) == 3
                and [s.get('label') for s in states] == ['before_down', 'after_down', 'after_release']
                and all(s.get('lmb_down') is False and not any(s.get('keys_down', {}).values()) for s in (states[:1] + states[-1:])),
        }
        if keys and len(edges) > len(keys) and number(pulse.get('hold_until_monotonic')) and number(pulse.get('absolute_deadline')):
            checks['single_fixed_hold_inside_deadline_and_release_boundary'] = (
                pulse['hold_until_monotonic'] <= pulse['absolute_deadline']
                and edges[0]['before_monotonic'] < pulse['hold_until_monotonic']
                and edges[len(keys)]['before_monotonic'] >= pulse['hold_until_monotonic']
                and pulse['hold_until_monotonic'] - edges[0]['before_monotonic'] <= pulse.get('requested_seconds', -math.inf))
        rows.append({'pulse': index, 'checks': checks, 'all_passed': all(checks.values()), 'original': pulse})
    checks = {'at_least_one_actual_pulse': bool(rows),
              'complete_before_after_publications': len(before) == len(after) == len(pulses),
              'every_actual_pulse_API_OS_predicate_passes': bool(rows) and all(row['all_passed'] for row in rows)}
    return {'checks': checks, 'all_pulse_checks_passed': all(checks.values()), 'rows': rows,
            'original_route_status': route.get('status'), 'original_journey_passed': result.get('passed'),
            'actions_sha256': hashlib.sha256((directory / 'actions.json').read_bytes()).hexdigest(),
            'scope': 'Actual API-return and OS-state bracket validation only. Route gameplay consumption, stopped endpoint, life/context and timing gates remain separate. No physical hold interval or causal improvement inferred.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = audit(args.root)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'all_pulse_checks_passed': report['all_pulse_checks_passed'], 'pulses': len(report['rows']),
                      'failed_checks': [k for k, v in report['checks'].items() if not v]}))
