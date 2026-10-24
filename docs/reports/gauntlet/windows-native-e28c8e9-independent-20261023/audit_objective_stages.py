"""Reconstruct original objective stage actions and unchanged next-buy bounds."""
import argparse
import json
from pathlib import Path

READ = lambda path: json.loads(path.read_text())
LINES = lambda path: [json.loads(line) for line in path.read_text().splitlines() if line]


def audit(root):
    cases = []
    for scenario in ('plant', 'defuse'):
        directory = root / 'evidence' / ('offline-' + scenario)
        receipt = READ(directory / 'results.json')
        actions = LINES(directory / 'actions.jsonl')
        events = LINES(directory / 'trace/events.jsonl')
        if not receipt.get('passed'):
            cases.append({'scenario': scenario, 'all_stage_checks_passed': False,
                          'actual_error': receipt.get('error'), 'actual_partial_checks': receipt.get('partial_checks')})
            continue
        named = lambda label: next(action for action in actions if action.get('event') == 'observed' and action.get('label') == label)
        captured = lambda name: next(action for action in actions if action.get('event') == 'capture_end' and action.get('capture') == name)
        resolved = named('Natural objective round resolution')
        resolved_image = captured('07-objective-round-resolved')
        next_buy = named('Natural next round after objective resolution')
        next_image = captured('08-natural-next-round')
        original_round = receipt['initial']['round_number']
        state = next_buy['observed']
        actor = state['local_actor']
        conservative_bound = next_buy['seconds'] - resolved_image['seconds']
        checks = {'full_original_fixture_passed': receipt['passed'] is True,
                  'natural_device_resolution_recorded': resolved['observed']['objective_state'] in ('defused', 'detonated')
                  and any(event.get('event') == 'notification' and ('Relay device defused' in event.get('message', '') or 'Relay device detonated' in event.get('message', '')) for event in events),
                  'conservative_next_buy_bound_below_original_12_seconds': 0 < conservative_bound < 12,
                  'next_round_buy_same_local_id_living': state['round_number'] == original_round + 1 and state['phase'] == 'buy'
                  and actor['id'] == receipt['initial']['local_actor']['id'] and actor['alive'] is True and actor['health'] > 0,
                  'clean_normal_close_and_reopen': receipt['initial_exit'] == receipt['reopened_exit'] == 0 and receipt['cleanup_errors'] == [],
                  'original_restart_comparison_passed': receipt['progression_settings_restart_equal'] is True}
        record = {'scenario': scenario, 'checks': checks, 'resolution_observation': resolved,
                  'resolution_capture_action': resolved_image, 'next_buy_observation': next_buy,
                  'next_buy_capture_action': next_image,
                  'next_buy_conservative_wall_upper_bound_seconds': conservative_bound,
                  'profile_files_retained': [path.relative_to(directory).as_posix() for path in directory.rglob('offline_training.json')],
                  'restart_scope': 'Incomplete objective round; no training save is created. Frozen controller compares the initial defaults when the file is absent. Clean default-profile restart is not proof of loading an earned disk profile.'}
        if scenario == 'plant':
            role = named('Actual attacker HUD restores post-plant role guidance')
            role_image = captured('06b-postplant-role-guidance')
            living = lambda value: (value['phase'] == 'live' and value['round_number'] == original_round
                and value['objective_state'] == 'planted' and value['local_actor']['id'] == receipt['initial']['local_actor']['id']
                and value['local_actor']['team'] == 0 and value['local_actor']['alive'] is True and 0 < value['local_actor']['health'] <= 100)
            checks['same_living_attacker_at_role_observation_and_capture'] = all(living(value['observed']) for value in (role, role_image))
            checks['native_role_partial_flag_passed'] = receipt['partial_checks']['postplant_attacker_role_guidance'] is True
            record.update(role_observation=role, role_capture_action=role_image,
                          role_status_scope='The action projection does not serialize ui.status_text. Exact frozen predicate and original native PNG supply the status-text evidence; inspect the PNG directly.')
        record['all_stage_checks_passed'] = all(checks.values())
        cases.append(record)
    return {'run_id': 39926044462, 'cases': cases,
            'all_stage_checks_passed': len(cases) == 2 and all(case['all_stage_checks_passed'] for case in cases),
            'scope': 'Read-only reconstruction of transferred original actions/events/results. No engine or OCR runs.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.root)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'all_stage_checks_passed': result['all_stage_checks_passed'],
                      'next_buy_conservative_bounds_seconds': [case.get('next_buy_conservative_wall_upper_bound_seconds') for case in result['cases']],
                      'profile_files_retained': [case.get('profile_files_retained') for case in result['cases']]}))
