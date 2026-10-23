"""Read original focus receipts independently; never launch native code or OCR."""
import argparse
import hashlib
import json
import math
from pathlib import Path

SOURCE = 'a089473481ced0f2e7b2a7468bbc5d079f92f0ff'
READ = lambda p: json.loads(p.read_text())


def number(v):
    return type(v) is int or (type(v) is float and math.isfinite(v))


def structural_reason(s):
    if not isinstance(s, dict):
        return 'observation_not_object'
    if type(s.get('schema')) is not int or s['schema'] != 1 or s.get('scope') != 'debug_offline_read_only_observation' or s.get('scenario') != 'standard':
        return 'observation_contract_changed'
    for k in ('wall_msec', 'simulation_tick', 'drawn_frames'):
        if type(s.get(k)) is not int or s[k] < 0:
            return 'invalid_' + k
    for k in ('local_actor', 'ui', 'local_input'):
        if not isinstance(s.get(k), dict):
            return k + '_not_object'
    a, u, i = (s[k] for k in ('local_actor', 'ui', 'local_input'))
    if type(s.get('round_number')) is not int or s['round_number'] < 1:
        return 'round_identity_changed'
    if type(a.get('id')) is not int or a['id'] < 1:
        return 'actor_identity_changed'
    if type(a.get('deaths')) is not int or a['deaths'] < 0:
        return 'actor_life_changed'
    if type(a.get('alive')) is not bool:
        return 'invalid_actor_alive'
    if not number(a.get('health')):
        return 'actor_health_invalid'
    if not number(s.get('time_scale')):
        return 'simulation_speed_changed'
    for v, length, reason in ((a.get('position'), 3, 'invalid_actor_position'), (i.get('move'), 2, 'invalid_input_move')):
        if not isinstance(v, list) or len(v) != length or not all(number(x) for x in v):
            return reason
    if any(type(i.get(k)) is not bool for k in ('fire', 'interact', 'reload')):
        return 'invalid_input_buttons'
    if any(type(u.get(k)) is not bool for k in ('focused', 'paused', 'scoreboard_visible', 'waiting_for_input_release')):
        return 'unknown_focus_or_pause_context'
    return None


def living_reason(s, base):
    reason = structural_reason(s)
    if reason:
        return reason
    a, b, u = s['local_actor'], base['local_actor'], s['ui']
    if s.get('phase') != 'live':
        return 'live_phase_lost'
    if s['round_number'] != base['round_number']:
        return 'round_identity_changed'
    if a['id'] != b['id']:
        return 'actor_identity_changed'
    if a['deaths'] != b['deaths']:
        return 'actor_life_changed'
    if not a['alive']:
        return 'actor_not_alive'
    if not 0 < a['health'] <= 100:
        return 'actor_health_invalid'
    if s['time_scale'] != 1:
        return 'simulation_speed_changed'
    if u.get('screen') != 'game' or u['scoreboard_visible']:
        return 'game_ui_context_lost'
    return None


def audit(root, full):
    d = root / 'evidence/offline-input'
    r, actions = READ(d / 'results.json'), READ(d / 'actions.json')
    focus = r.get('native_focus_recovery', {})
    fence, fresh = focus.get('context_fence', {}), focus.get('fresh_press', {})
    base = fence.get('baseline')
    checks = {'whole_journey_passed': r.get('passed') is True,
              'source_clean_exact': r.get('source', {}).get('source_commit') == SOURCE and r.get('source', {}).get('source_dirty') is False,
              'focus_claim_passed': focus.get('passed') is True,
              'complete_living_context_status': fence.get('status') == 'LIVING_CONTEXT_PRESERVED_THROUGH_CAPTURE',
              'fresh_living_movement_status': fresh.get('status') == 'LIVING_MOVEMENT_OBSERVED'}
    states = []
    for label in ('held_input_acknowledged', 'lost', 'restored_paused', 'released', 'fresh_press_movement'):
        if label in focus:
            states.append({'label': label, 'state': focus[label]})
    states += [{'label': 'held_neutral_' + str(n), 'state': s} for n, s in enumerate(focus.get('held_neutral_samples', []))]
    states += [{'label': 'fresh_' + k, 'state': fresh[k]} for k in ('released', 'before_key', 'last_after_key', 'moved') if k in fresh]
    for capture, bracket in focus.get('capture_context', {}).items():
        states += [{'label': capture + ':' + k, 'state': s} for k, s in bracket.items() if k in ('before', 'after')]
    raw = [a for a in actions if a.get('event') == 'offline_observation']
    state_rows = []
    for row in states:
        s = row['state']
        reason = living_reason(s, base) if base is not None else 'missing_baseline'
        matches = [a for a in raw if a.get('state') == s]
        state_rows.append(row | {'independent_context_reason': reason,
                                  'matching_observation_actions': matches})
    checks['all_reached_accepted_contexts_living'] = bool(states) and base is not None and all(x['independent_context_reason'] is None for x in state_rows)
    rejection = fence.get('precondition_loss')
    rejection_audit = None
    if rejection:
        rejected = rejection.get('rejected_state')
        prior = rejection.get('previous_valid_state')
        computed = living_reason(rejected, base) if base is not None else 'missing_baseline'
        # Focus, pause, release and regression predicates are stage-dependent.
        # Recompute only when the claimed core/shape predicate did not reject.
        if computed is None and isinstance(rejected, dict):
            reason = rejection.get('reason')
            if reason == 'required_focus_lost' and rejected['ui']['focused'] is not True:
                computed = reason
            elif reason == 'required_pause_context_lost':
                computed = 'requires_manual_stage_pause_comparison'
            elif reason == 'controls_not_released' and (rejected['ui']['waiting_for_input_release'] is not False or rejected['local_input']['move'] != [0, 0] or rejected['local_input']['fire'] is not False):
                computed = reason
            elif isinstance(prior, dict):
                for k in ('wall_msec', 'simulation_tick', 'drawn_frames'):
                    if rejected[k] < prior[k]:
                        computed = 'regressed_' + k
                        break
        rejection_audit = {'original': rejection, 'independently_computed_reason': computed,
                           'reason_matches': computed == rejection.get('reason'),
                           'previous_state_independently_living': base is not None and living_reason(prior, base) is None,
                           'typed_failure_retained': r.get('failure_kind') == fence.get('status') == rejection.get('kind') == 'FOCUS_PRECONDITION_LOST',
                           'native_result_remains_failed': r.get('passed') is False and focus.get('passed') is False}
    def matched(s):
        return next((a for a in raw if a.get('state') == s), None)
    lost, restored = focus.get('lost'), focus.get('restored_paused')
    held, released, moved, before = focus.get('held_neutral_samples', []), focus.get('released'), focus.get('fresh_press_movement'), fresh.get('before_key')
    checks['loss_pauses_actual_native_game'] = bool(lost and lost['ui']['focused'] is False and lost['ui']['paused'] is True)
    checks['restored_stays_explicitly_paused_visible_pointer'] = bool(restored and restored['ui']['focused'] is True and restored['ui']['paused'] is True and restored['ui'].get('mouse_mode') == 0)
    checks['held_has_two_stable_newer_samples'] = (len(held) >= 3 and held[-1]['wall_msec'] > held[-2]['wall_msec'] and held[-1]['local_actor']['position'] == held[-2]['local_actor']['position'])
    if held and restored:
        actor = restored['local_actor']
        checks['every_held_sample_neutral_and_native_held'] = all(
            s['local_input']['move'] == [0, 0] and all(s['local_input'][k] is False for k in ('fire', 'interact', 'reload'))
            and s['ui']['waiting_for_input_release'] is True and s['ui']['paused'] is False and s['ui']['focused'] is True
            and all(s['local_actor'][k] == actor[k] for k in ('ammo', 'weapon', 'yaw', 'pitch'))
            and matched(s) is not None and matched(s).get('native_state', {}).get('lmb_down') is True
            and matched(s).get('native_state', {}).get('keys_down', {}).get('w') is True for s in held)
    else:
        checks['every_held_sample_neutral_and_native_held'] = False
    release_action = matched(released) if released else None
    checks['released_actual_native_controls_and_guard'] = bool(release_action and release_action['native_state']['lmb_down'] is False and release_action['native_state']['keys_down']['w'] is False and released['local_input']['move'] == [0, 0] and released['local_input']['fire'] is False and released['ui']['waiting_for_input_release'] is False)
    waits = [a for a in actions if a.get('event') == 'wait_begin' and a.get('label') == 'Fresh W press moves actual player after focus recovery']
    checks['fresh_original_ten_second_wait'] = len(waits) == 1 and waits[0].get('budget_seconds') == 10
    downs = [a for a in actions if a.get('event') == 'key_after' and a.get('key') == 'w' and a.get('down') is True and release_action and a['seconds'] > release_action['seconds']]
    checks['one_actual_fresh_native_W_dispatched'] = len(downs) == 1 and fresh.get('key_down_dispatched') is True and downs[0]['native_state']['target_focused'] is True and downs[0]['native_state']['keys_down']['w'] is True
    checks['before_fresh_key_living_released_context'] = bool(before and base and living_reason(before, base) is None and before['ui']['focused'] is True and before['ui']['paused'] is False and before['ui']['waiting_for_input_release'] is False and before['local_input']['move'] == [0, 0] and before['local_input']['fire'] is False)
    checks['newer_fresh_ack_and_actual_displacement'] = bool(before and moved and fresh.get('moved') == moved and moved['wall_msec'] > before['wall_msec'] and moved['simulation_tick'] > before['simulation_tick'] and moved['local_input']['move'] != [0, 0] and moved['local_actor']['position'] != before['local_actor']['position'])
    brackets = []
    for name in ('11a-restored-focus-still-paused', '11b-resumed-held-input-neutral', '11c-fresh-press-movement'):
        bracket = focus.get('capture_context', {}).get(name, {})
        png = full / 'offline-input' / (name + '.png')
        records = [a for a in actions if a.get('capture') == name and a.get('event') in ('capture_begin', 'capture_end')]
        valid = (base is not None and set(bracket) == {'before', 'after'} and all(living_reason(s, base) is None for s in bracket.values()) and len(records) == 2 and png.is_file())
        brackets.append({'capture': name, 'complete_living_bracket': valid, 'bracket': bracket,
                         'actions': records, 'original_png_transferred': png.is_file(),
                         'sha256': hashlib.sha256(png.read_bytes()).hexdigest() if png.is_file() else None})
    checks['all_three_living_focus_capture_brackets'] = all(x['complete_living_bracket'] for x in brackets)
    checks['normal_close_settings_and_training_unchanged'] = r.get('clean_exit') is True and r.get('exit') == 0 and r.get('initial_exit') == 0 and r.get('incomplete_training_unchanged_after_reopened_exit') is True and r.get('cleanup_errors') == []
    return {'run_id': 39916539053, 'source_commit': SOURCE, 'checks': checks,
            'all_focus_checks_passed': all(checks.values()), 'original_journey_error': r.get('error'),
            'original_failure_kind': r.get('failure_kind'), 'original_focus_receipt': focus,
            'independent_state_rows': state_rows, 'independent_rejection_audit': rejection_audit,
            'fresh_wait_actions': waits, 'fresh_native_key_actions': downs, 'capture_brackets': brackets,
            'complete_original_captures': r.get('captures'), 'cleanup_errors': r.get('cleanup_errors'),
            'scope': 'Original-byte receipt/state/action audit. Direct pixels remain separately required. No native execution, latency or causal runtime benefit claim.'}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('root', type=Path)
    p.add_argument('full', type=Path)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    result = audit(a.root, a.full)
    a.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'all_focus_checks_passed': result['all_focus_checks_passed'],
                      'failed_checks': [k for k, v in result['checks'].items() if not v],
                      'original_failure_kind': result['original_failure_kind']}))
