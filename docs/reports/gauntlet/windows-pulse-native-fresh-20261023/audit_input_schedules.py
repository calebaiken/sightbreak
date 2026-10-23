"""Recompute the three unchanged native input schedules and original wait outcomes."""
import argparse
import hashlib
import json
from pathlib import Path


def audit(root):
    scenarios = []
    for name, expected_schedule, expected_delay in [('native-input', 'legacy', 0),
            ('reload-release-first', 'release-first', 4), ('reload-legacy-delayed', 'legacy', 4)]:
        directory = root / 'evidence' / name
        if not (directory / 'results.json').is_file():
            scenarios.append({'scenario': name, 'all_passed': False, 'unreached': True})
            continue
        result = json.loads((directory / 'results.json').read_text())
        actions = json.loads((directory / 'actions.json').read_text())
        checks = {'original_schedule_and_delay': result.get('input_schedule') == expected_schedule
                  and result.get('synthetic_fire_capture_delay_seconds') == expected_delay,
                  'original_inner_result_passed': result.get('passed') is True}
        pending, waits = [], []
        for action in actions:
            if action.get('event') == 'wait_begin':
                pending.append(action)
            elif action.get('event') in ('wait_completed', 'wait_timeout'):
                begin = next((w for w in reversed(pending) if w.get('label') == action.get('label')), None)
                if begin is not None:
                    pending.remove(begin)
                duration = action['seconds'] - begin['seconds'] if begin else None
                waits.append({'label': action.get('label'), 'outcome': action['event'],
                              'budget_seconds': begin.get('budget_seconds') if begin else None,
                              'wall_seconds': duration,
                              'completed_within_original_wait': begin is not None
                                  and action['event'] == 'wait_completed' and 0 <= duration < begin['budget_seconds'],
                              'begin': begin, 'end': action})
        checks['every_reached_wait_completed_before_its_deadline'] = bool(waits) and not pending and all(w['completed_within_original_wait'] for w in waits)
        for label, cap in [('Authority confirms reload start', 10), ('Authority reload completion', 5)]:
            found = [w for w in waits if w['label'] == label]
            checks['original_reload_wait:' + label] = len(found) == 1 and found[0]['budget_seconds'] == cap and found[0]['completed_within_original_wait']
        downs = [(i, a) for i, a in enumerate(actions) if a.get('event') == 'button_after' and a.get('down') is True]
        ups = [(i, a) for i, a in enumerate(actions) if a.get('event') == 'button_after' and a.get('down') is False]
        captures = [(i, a) for i, a in enumerate(actions) if a.get('event') == 'capture_begin' and a.get('capture') == '04-fire-input']
        checks['one_original_fire_down_release_and_capture'] = len(downs) == len(ups) == len(captures) == 1
        if downs and ups and captures:
            checks['actual_fire_capture_release_order'] = (downs[0][0] < captures[0][0] < ups[0][0]
                if expected_schedule == 'legacy' else downs[0][0] < ups[0][0] < captures[0][0])
        delays = [a for a in actions if a.get('event') == 'synthetic_capture_delay_begin']
        checks['actual_synthetic_capture_pressure_matches'] = (delays == [] if expected_delay == 0 else len(delays) == 1 and delays[0].get('delay_seconds') == expected_delay)
        diagnostic = directory / 'diagnostic-exit.json'
        if name == 'reload-legacy-delayed':
            receipt = json.loads(diagnostic.read_text()) if diagnostic.is_file() else {}
            checks['legacy_inner_exit_zero'] = receipt.get('exit_code') == 0
        scenarios.append({'scenario': name, 'checks': checks, 'all_passed': all(checks.values()),
                          'original_passed': result.get('passed'), 'original_error': result.get('error'),
                          'elapsed_seconds_including_cleanup': result.get('elapsed_seconds'),
                          'waits': waits, 'unterminated_waits': pending,
                          'actions_sha256': hashlib.sha256((directory / 'actions.json').read_bytes()).hexdigest()})
    return {'all_three_original_schedules_passed': len(scenarios) == 3 and all(s['all_passed'] for s in scenarios),
            'scenarios': scenarios,
            'scope': 'Original driver schedule and wait brackets. Authority resource/input consumption is audited separately. An expired wait remains failed even if later final ammunition is complete.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = audit(args.root)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'all_three_original_schedules_passed': report['all_three_original_schedules_passed'],
                      'scenarios': [{'scenario': s['scenario'], 'passed': s['all_passed'],
                                     'error': s.get('original_error')} for s in report['scenarios']]}))
