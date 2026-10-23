"""Audit retained native phase-capture brackets without loading the controller."""
import argparse
import hashlib
import json
from pathlib import Path

SOURCE = 'a089473481ced0f2e7b2a7468bbc5d079f92f0ff'
READ = lambda path: json.loads(path.read_text())
STAGES = ['acknowledged', 'ready', 'before_capture', 'after_capture_barrier', 'after_capture']


def valid_context(state, actor_id, round_number):
    actor = state.get('local_actor', {})
    ui = state.get('ui', {})
    return (state.get('schema') == 1 and type(state.get('schema')) is int
            and state.get('scope') == 'debug_offline_read_only_observation'
            and state.get('scenario') == 'standard'
            and state.get('time_scale') == 1 and type(state.get('time_scale')) is not bool
            and state.get('phase') == 'buy' and state.get('round_number') == round_number
            and type(state.get('round_number')) is int
            and actor.get('id') == actor_id and type(actor.get('id')) is int
            and actor.get('alive') is True and type(actor.get('health')) in (float, int)
            and 0 < actor['health'] <= 100
            and ui.get('screen') == 'game' and ui.get('focused') is True
            and ui.get('paused') is False and ui.get('scoreboard_visible') is False
            and all(type(state.get(key)) is int and state[key] >= 0
                    for key in ('drawn_frames', 'wall_msec', 'simulation_tick')))


def audit(root, full=None):
    directory = root / 'evidence/offline-input'
    result = READ(directory / 'results.json')
    actions = READ(directory / 'actions.json')
    commands = READ(directory / 'commands.json')
    initial = json.loads((directory / 'initial-offline-trace/events.jsonl').read_text().splitlines()[0])
    loaded_path = directory / 'restart-profile-trace/events.jsonl'
    loaded = json.loads(loaded_path.read_text().splitlines()[0]) if loaded_path.is_file() else None
    disk = READ(next(directory.rglob('offline_training.json')))
    cases = []
    for name, round_number, watchdog, process_name, trace_name, first in [
            ('06c-next-round', 2, 160, 'client', 'initial-offline-trace', initial),
            ('10-reopened-loaded-settings', 1, 30, 'reopened', 'restart-profile-trace', loaded)]:
        fence = result.get('phase_capture_fences', {}).get(name, {})
        missing = [stage for stage in STAGES if stage not in fence]
        if missing:
            cases.append({'capture': name, 'accepted': False, 'missing_stages': missing,
                          'partial_native_receipt': fence, 'journey_error': result.get('error')})
            continue
        states = [fence[stage] for stage in STAGES]
        expected = fence['expected_binding']
        process = next(command for command in commands if command['name'] == process_name)
        captured = [action for action in actions if action.get('capture') == name
                    and action['event'] in ('capture_begin', 'capture_end')]
        raw_observations = [action for action in actions if action['event'] == 'offline_observation']
        retained = [next((action for action in raw_observations if action['state'] == state), None)
                    for state in states]
        checks = {
            'complete_five_state_native_bracket': not missing,
            'same_named_living_buy_context': all(valid_context(s, first['local_actor']['id'], round_number) for s in states),
            'strictly_new_publications_at_each_stage': all(b['wall_msec'] > a['wall_msec'] for a, b in zip(states, states[1:])),
            'monotonic_drawn_and_simulation_counters': all(b[key] >= a[key] for a, b in zip(states, states[1:]) for key in ('drawn_frames', 'simulation_tick')),
            'at_least_two_drawn_frames_before_capture': all(s['drawn_frames'] >= states[0]['drawn_frames'] + 2 for s in states[1:]),
            'actual_native_source_and_owned_process_binding': expected['source'] == result['source'] and expected['source']['source_commit'] == SOURCE
                and expected['source']['source_dirty'] is False and expected['source']['source_game_dirty'] is False
                and expected['process_pid'] == process['pid'] and expected['process_running'] is True,
            'same_binding_before_and_after_capture': fence['binding_before_capture'] == expected == fence['binding_after_capture'],
            'expected_trace_selected': expected['trace_directory'].replace('\\', '/').endswith('/' + trace_name),
            'original_watchdog_and_positive_remaining_budget': fence['transition_watchdog_seconds'] == watchdog
                and 0 < fence['remaining_original_budget_seconds'] <= watchdog,
            'same_actor_round_phase_receipt': fence['expected_actor_id'] == first['local_actor']['id']
                and fence['expected_round'] == round_number and fence['expected_phase'] == 'buy'
                and fence['additional_drawn_frames_required'] == 2,
            'all_states_retained_in_original_actions': all(action is not None for action in retained),
            'one_actual_raw_capture_pair': len(captured) == 2 and [a['event'] for a in captured] == ['capture_begin', 'capture_end'],
        }
        if all(action is not None for action in retained) and len(captured) == 2:
            checks['capture_order_inside_fresh_observation_actions'] = (retained[2]['seconds'] <= captured[0]['seconds']
                < captured[1]['seconds'] <= retained[3]['seconds'] < retained[4]['seconds'])
        if name.startswith('10'):
            checks['exact_original_loaded_and_disk_settings_around_capture'] = (expected['loaded_initial_event'] == loaded
                and expected['stored_profile'] == loaded['initial_profile'] == disk)
            checks['new_process_and_trace_distinct_from_retired_client'] = (expected['process_pid'] != next(c['pid'] for c in commands if c['name'] == 'client')
                and expected['trace_directory'] != result['phase_capture_fences']['06c-next-round']['expected_binding']['trace_directory'])
        png = full / 'offline-input' / (name + '.png') if full else None
        image = {'path': 'offline-input/' + name + '.png', 'original_transferred': bool(png and png.is_file()),
                 'direct_visual_review_still_required': True}
        if png and png.is_file():
            image.update(bytes=png.stat().st_size, sha256=hashlib.sha256(png.read_bytes()).hexdigest())
        cases.append({'capture': name, 'accepted': all(checks.values()), 'checks': checks,
                      'process_pid': process['pid'], 'trace_directory': expected['trace_directory'],
                      'watchdog_seconds': watchdog, 'remaining_original_budget_seconds': fence['remaining_original_budget_seconds'],
                      'state_samples': [{k: state.get(k) for k in ('simulation_tick', 'drawn_frames', 'wall_msec', 'phase', 'round_number')}
                                       | {'stage': stage, 'local_actor': state['local_actor'], 'ui': state['ui']}
                                       for stage, state in zip(STAGES, states)],
                      'capture_actions': captured, 'original_PNG': image})
    return {'run_id': 39916539053, 'source_commit': SOURCE, 'cases': cases,
            'all_native_bracket_checks_passed': len(cases) == 2 and all(c['accepted'] for c in cases),
            'scope': 'Retained raw authority/actions/PID/source/profile checks only. Original pixels require separate direct inspection; no native game or OCR is run.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    parser.add_argument('--full', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.root, args.full)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'all_native_bracket_checks_passed': result['all_native_bracket_checks_passed'],
                      'cases': [{'capture': c['capture'], 'accepted': c['accepted']} for c in result['cases']]}))
