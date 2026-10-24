"""Independently audit retained fixed-route states and ordinary input actions."""
import argparse
import hashlib
import json
import math
from pathlib import Path

SOURCE = 'e28c8e90b9ef2d0c766bd9152c194e3197ceba9a'
TARGET = (-7.8, -21.)
SPAWN = (-4.4, -21.)
READ = lambda p: json.loads(p.read_text())


def number(v):
    return type(v) is int or type(v) is float and math.isfinite(v)


def audit(root):
    d = root / 'evidence/offline-input'
    result, actions = READ(d / 'results.json'), READ(d / 'actions.json')
    route = result.get('settings_cover_route', {})
    states = route.get('observations', [])
    start = route.get('start')
    completed = [a for a in actions if a.get('event') == 'settings_route_movement_completed']
    start_action = next((a for a in actions if a.get('event') == 'offline_observation'
        and a.get('label') == 'Living second-round player before fixed settings route'), None)
    waits = [a for a in actions if a.get('event') == 'wait_begin'
        and a.get('label') == 'Second active round for weapon switching']
    checks = {'route_reached': route.get('status') == 'FIXED_ROUTE_REACHED',
              'frozen_source': result.get('source', {}).get('source_commit') == SOURCE,
              'fixed_requested_target': route.get('requested') == list(TARGET),
              'start_is_original_raw_observation': bool(start_action and start_action['state'] == start),
              'one_route_completion': len(completed) == 1,
              'route_has_raw_states': bool(states) and states[0] == start,
              'original_second_live_35s_wait': len(waits) == 1 and 0 < waits[0].get('budget_seconds', 0) <= 35,
              'remaining_original_budget_positive': number(route.get('remaining_original_second_live_budget'))
                  and 0 < route['remaining_original_second_live_budget'] <= 35}
    rows = []
    previous = None
    for index, state in enumerate(states):
        actor, ui, inputs = (state.get(k, {}) for k in ('local_actor', 'ui', 'local_input'))
        baseline = start['local_actor']
        p, v = actor.get('position', []), actor.get('velocity', [])
        predicates = {
            'schema_scope_scenario': type(state.get('schema')) is int and state['schema'] == 1
                and state.get('scope') == 'debug_offline_read_only_observation' and state.get('scenario') == 'standard',
            'same_living_round2_stock_actor': state.get('phase') == 'live' and state.get('round_number') == 2
                and actor.get('id') == baseline['id'] and actor.get('alive') is True
                and actor.get('deaths') == baseline['deaths'] and actor.get('team') == 0
                and number(actor.get('health')) and 0 < actor['health'] <= 100,
            'unaltered_weapon_ammo': actor.get('weapon') == 'smg' and actor.get('ammo') == 30 and actor.get('reserve') == 120,
            'focused_unpaused_unit_speed': state.get('time_scale') == 1 and type(state.get('time_scale')) is not bool
                and ui.get('screen') == 'game' and ui.get('focused') is True and ui.get('paused') is False
                and ui.get('scoreboard_visible') is False and ui.get('waiting_for_input_release') is False,
            'finite_motion': len(p) == len(v) == 3 and all(number(n) for n in p + v)
                and number(actor.get('yaw')) and number(state.get('elapsed')) and state['elapsed'] >= 0,
            'corridor': len(p) == 3 and -8.5 <= p[0] <= -3.9 and -.1 <= p[1] <= .1 and -21.75 <= p[2] <= -20.25,
            'ordinary_move_only': isinstance(inputs.get('move'), list) and len(inputs['move']) == 2
                and all(number(n) for n in inputs['move'])
                and all(inputs.get(k) is False for k in ('fire', 'interact', 'reload')),
            'valid_monotonic_native_counters': all(type(state.get(k)) is int and state[k] >= 0
                and (previous is None or state[k] >= previous[k]) for k in ('simulation_tick', 'wall_msec')),
        }
        rows.append({'sample': index, 'checks': predicates, 'all_passed': all(predicates.values()),
                     'state': state})
        previous = state
    checks['every_retained_route_state_valid'] = bool(rows) and all(row['all_passed'] for row in rows)
    details = {}
    loss = route.get('precondition_loss')
    if loss:
        rejected = loss['rejected_state']
        prior = loss['previous_valid_state']
        position = rejected['local_actor']['position']
        independent_reason = ('left_declared_clear_corridor' if not (
            -8.5 <= position[0] <= -3.9 and -.1 <= position[1] <= .1
            and -21.75 <= position[2] <= -20.25) else None)
        details['failure_reconstruction'] = {
            'original_reason': loss['reason'], 'independent_reason': independent_reason,
            'reason_matches': loss['reason'] == independent_reason,
            'previous_valid_state_is_last_accepted_original': bool(states) and prior == states[-1],
            'rejection_is_newer': rejected['wall_msec'] > prior['wall_msec']
                and rejected['simulation_tick'] > prior['simulation_tick'],
            'same_living_actor_at_rejection': rejected['local_actor']['alive'] is True
                and rejected['local_actor']['health'] == 100
                and all(rejected['local_actor'][k] == start['local_actor'][k]
                    for k in ('id','deaths','team','weapon','ammo','reserve')),
            'rejected_position': position, 'rejected_velocity': rejected['local_actor']['velocity'],
            'previous_tick': prior['simulation_tick'], 'rejected_tick': rejected['simulation_tick'],
            'outside_corridor_by_x_metres': max(-8.5-position[0], position[0]+3.9, 0),
            'target_distance_metres': math.hypot(position[0]-TARGET[0],position[2]-TARGET[1]),
        }
    if start:
        p, v = start['local_actor']['position'], start['local_actor']['velocity']
        checks['neutral_stopped_original_stock_spawn'] = math.hypot(p[0]-SPAWN[0], p[2]-SPAWN[1]) <= .25 \
            and math.hypot(v[0], v[2]) <= .05 and start['local_input']['move'] == [0, 0]
    if completed and states:
        end = completed[0]
        final = states[-1]
        actor = final['local_actor']
        p, v = actor['position'], actor['velocity']
        distance, speed = math.hypot(p[0]-TARGET[0], p[2]-TARGET[1]), math.hypot(v[0], v[2])
        ticks = end.get('settled_simulation_ticks', [])
        settled = [s for s in states if s['simulation_tick'] in ticks]
        checks['actual_endpoint_within_45cm_and_stopped'] = distance < .45 and speed <= .05 \
            and final['local_input']['move'] == [0, 0] and route.get('after') == final
        checks['endpoint_receipt_matches_raw'] = route.get('endpoint') == p == end.get('destination') \
            and end.get('requested') == list(TARGET) and abs(end['target_distance']-distance) < 1e-9 \
            and abs(end['horizontal_speed']-speed) < 1e-9
        checks['two_distinct_settled_native_ticks'] = len(ticks) == len(set(ticks)) == 2 and ticks[1] > ticks[0] \
            and len(settled) >= 2 and all(s['local_input']['move'] == [0, 0]
                and math.hypot(s['local_actor']['velocity'][0], s['local_actor']['velocity'][2]) <= .05 for s in settled)
        checks['native_tick_progress_and_displacement'] = final['simulation_tick'] > start['simulation_tick'] \
            and final['wall_msec'] > start['wall_msec'] and math.dist(start['local_actor']['position'], p) > 2.5
        if waits and start_action:
            route_actions = [a for a in actions if start_action['seconds'] <= a['seconds'] <= end['seconds']]
            key_events = [a for a in route_actions if a.get('event') == 'key_after']
            downs = [a for a in key_events if a.get('down') is True]
            checks['only_ordinary_WASD_input_during_route'] = bool(downs) \
                and all(a.get('key') in ('w', 'a', 's', 'd') for a in key_events)
            checks['native_route_keys_owned_focused_and_dispatched'] = bool(downs) and all(
                a.get('native_state', {}).get('target_focused') is True
                and a['key'] in a.get('held_keys', [])
                and (a['key'] not in a.get('native_state', {}).get('keys_down', {})
                     or a['native_state']['keys_down'][a['key']] is True) for a in downs)
            checks['completion_inside_original_shared_deadline'] = \
                0 <= end['seconds']-waits[0]['seconds'] < waits[0]['budget_seconds'] <= 35
            details.update(route_key_actions=key_events, route_completion=end,
                           wall_seconds_from_second_live_wait=end['seconds']-waits[0]['seconds'])
        details.update(endpoint_distance=distance, endpoint_horizontal_speed=speed,
                       starting_health=start['local_actor']['health'], ending_health=actor['health'], settled_ticks=ticks)
    return {'checks': checks, 'all_route_checks_passed': all(checks.values()), 'original_status': route.get('status'),
            'original_route_receipt': route, 'independent_sample_rows': rows, 'details': details,
            'original_journey_passed': result.get('passed'), 'original_journey_error': result.get('error'),
            'actions_sha256': hashlib.sha256((d/'actions.json').read_bytes()).hexdigest(),
            'scope': 'Retained original native route states and actions only. OS bitmap samples cover r/d/w, so a/s press evidence is the traced native API dispatch/held set plus authoritative input/displacement, not a separate a/s OS bitmap. Later cover survival/settings/focus are separate gates; no runtime or causal claim.'}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('root', type=Path)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    result = audit(a.root)
    a.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'all_route_checks_passed': result['all_route_checks_passed'],
                      'states': len(result['independent_sample_rows']),
                      'failed_checks': [k for k,v in result['checks'].items() if not v]}))
