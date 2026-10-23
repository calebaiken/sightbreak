"""Recompute narrow reached facts in the two original failed native stages."""
import argparse
import json
import math
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('receipts', type=Path)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
base = args.receipts / 'evidence'
read = lambda path: json.loads(path.read_text())
lines = lambda path: [json.loads(line) for line in path.read_text().splitlines() if line]
pick = lambda state: {key: state.get(key) for key in ('wall_msec', 'simulation_tick', 'drawn_frames', 'elapsed',
    'phase', 'round_number', 'objective_state', 'local_actor', 'local_input', 'ui')}

journey = read(base / 'offline-input/results.json')
actions = read(base / 'offline-input/actions.json')
observed = lambda label: next(row for row in actions if row.get('event') == 'offline_observation' and row.get('label') == label)
labels = ('Game consumed physical W and LMB before native focus loss', 'Native focus loss pauses actual offline match',
          'Actual game observes restored focus', 'Explicit resume with W and LMB still physically held',
          'Fresh held-input guard sample 1', 'Fresh held-input guard sample 2', 'Released held focus-test controls')
rows = [observed(label) for label in labels]
released = rows[-1]['state']
key_down = next(row for row in actions if row.get('event') == 'key_after' and row.get('key') == 'w'
                and row.get('down') is True and row['seconds'] > rows[-1]['seconds'])
wait = next(row for row in actions if row.get('event') == 'wait_begin'
            and row.get('label') == 'Fresh W press moves actual player after focus recovery')
last = journey['last_offline_observation']
events = lines(base / 'offline-input/restart-profile-trace/events.jsonl')
dead = next(row for row in events if row.get('event') == 'alive' and row.get('local_actor', {}).get('alive') is False)
focus = {'whole_stage_passed': journey['passed'], 'original_error': journey['error'],
         'checks': {
             'recorded_release_actor_already_dead': released['local_actor']['alive'] is False and released['local_actor']['health'] == 0,
             'recorded_release_guard_clear_and_native_controls_up': released['ui']['waiting_for_input_release'] is False
                 and rows[-1]['native_state']['lmb_down'] is False and rows[-1]['native_state']['keys_down']['w'] is False,
             'later_native_focused_W_down': key_down['native_state']['target_focused'] is True and key_down['native_state']['keys_down']['w'] is True,
             'original_ten_second_movement_budget': wait['budget_seconds'] == 10,
             'final_authority_input_nonzero_while_dead': last['local_input']['move'] != [0, 0] and last['local_actor']['alive'] is False,
             'no_successful_post_release_movement_observation_or_capture': not any(row.get('event') == 'offline_observation'
                 and row.get('label') == wait['label'] for row in actions)
                 and not any(row.get('capture') == '11c-fresh-press-movement' for row in actions)},
         'recorded_contexts': [{'label': row['label'], 'driver_seconds': row['seconds'],
             'state': pick(row['state']), 'native_state': row['native_state']} for row in rows],
         'first_retained_death_state': pick(dead), 'fresh_W_native_record': key_down,
         'fresh_W_wait_begin': wait, 'last_retained_observation': pick(last),
         'diagnosis': 'The original living-movement predicate is unmet after a recorded death. These records do not establish lost delivery of fresh input to a living actor.'}

plant = read(base / 'offline-plant/results.json')
actions = lines(base / 'offline-plant/actions.jsonl')
events = lines(base / 'offline-plant/trace/events.jsonl')
hold = plant['objective_hold']
started, completed = hold['input_started'], hold['completion_notification']
edges = [row for row in events if row['event'] == 'local_interact_input'
         and hold['command_simulation_tick'] < row['simulation_tick'] <= completed['simulation_tick']]
resolution = next(row for row in actions if row.get('event') == 'observed' and row.get('label') == 'Natural objective round resolution')
movement = next(row for row in actions if row.get('event') == 'movement_completed')
movement_start = next(index for index, row in enumerate(actions) if row.get('event') == 'movement_control')
movement_upper = movement['seconds'] - actions[movement_start - 1]['seconds']
movement_error = math.hypot(movement['destination'][0] - movement['requested'][0],
                            movement['destination'][2] - movement['requested'][1])
record = {'whole_stage_passed': plant['passed'], 'original_error': plant['error'],
          'reached_checks': {
              'original_movement_budget_tolerance_and_settle': movement_upper < 15 and movement_error < .45
                  and movement['horizontal_speed'] <= .05 and len(set(movement['settled_simulation_ticks'])) == 2,
              'exact_180_consumed_ticks': completed['simulation_tick'] - started['simulation_tick'] == hold['simulation_ticks'] == 180,
              'raw_start_and_completion_edges_retained': started in events and completed in events,
              'single_final_consumed_E_down': len(edges) == 1 and edges[0]['held'] is True,
              'interrupted_hold_reset_native_receipt': plant['partial_checks']['interrupted_E_reset'] is True,
              'one_contribution_and_300_credits': plant['local_contribution_after'] == plant['local_contribution_before'] + 1
                  and plant['credits_before'] == 800 and plant['credits_after'] == 1100,
              'POST_still_planted': resolution['observed']['phase'] == 'post' and resolution['observed']['objective_state'] == 'planted',
              'ordinary_elimination_notification': any(row.get('message') == 'Attackers win • Defenders eliminated' for row in events),
              'no_defuse_or_detonation_notification': not any('Relay device defused' in row.get('message', '')
                  or 'Relay device detonated' in row.get('message', '') for row in events),
              'next_buy_and_restart_unreached': not any(row.get('label') == 'Natural next round after objective resolution'
                  for row in actions) and plant['reopened_exit'] is None},
          'consumed_E_start_tick': started['simulation_tick'], 'arm_tick': completed['simulation_tick'],
          'movement_endpoint_error_m': movement_error, 'movement_wall_upper_bound_seconds': movement_upper,
          'movement_settled_ticks': movement['settled_simulation_ticks'],
          'resolution': resolution, 'original_partial_checks': plant['partial_checks'],
          'diagnosis': 'Player plant/role guidance is reached, then elimination ends the round with the device still planted. The required device defuse/detonation, next buy and restart are not qualified.'}

result = {'run_id': 39907358390, 'source_commit': 'b2e0293a546961230afbd73e5cd2a1a307d69e94',
          'focus_failure': focus, 'plant_failure': record,
          'scope': 'Narrow original-record facts within a failed attempt. No new native execution, cause attribution, rerun or whole-stage acceptance.'}
args.output.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({'focus_fact_checks': focus['checks'], 'plant_reached_checks': record['reached_checks']}))
