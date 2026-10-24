"""Reconstruct reached settings resume and later lost-life context from raw bytes."""
import argparse
import json
from pathlib import Path

READ = lambda p: json.loads(p.read_text())


def audit(root):
    d = root / 'evidence/offline-input'
    r, a = READ(d / 'results.json'), READ(d / 'actions.json')
    events = [json.loads(line) for line in (d / 'initial-offline-trace/events.jsonl').read_text().splitlines() if line]
    primary = next(x for x in r['hud_analysis_pauses'] if x['capture'] == '06g-switched-primary')
    hud = next(x for x in r['hud_analysis_pauses'] if x['capture'] == '07d-explicit-resume')
    def named(label):
        return next(x for x in a if x.get('event') == 'offline_observation' and x.get('label') == label)
    settings = named('Fresh paused player after native settings change')
    resumed = named('Actual living player explicitly resumes after field settings')
    ready = named('Two drawn frames after explicit native settings resume')
    paused = named('Native pause before saved-HUD OCR: 07d-explicit-resume')
    before = hud['before']
    base = primary['paused']
    states = [primary['paused'], primary['after_analysis'], settings['state'], resumed['state'], ready['state'], before]
    actor = base['local_actor']
    def same_living(s):
        return (s['phase'] == base['phase'] and s['round_number'] == base['round_number'] and s['time_scale'] == 1
                and s['ui']['screen'] == 'game' and s['ui']['focused'] is True
                and s['local_actor']['alive'] is True and 0 < s['local_actor']['health'] <= 100
                and all(s['local_actor'][k] == actor[k] for k in ('id', 'deaths', 'weapon', 'ammo', 'reserve')))
    index = a.index(resumed)
    down = next(x for x in reversed(a[:index]) if x.get('event') == 'key_after' and x.get('key') == 'Escape' and x.get('down') is True)
    release = next(x for x in a[index:] if x.get('event') == 'key_after' and x.get('key') == 'Escape' and x.get('down') is False and x.get('scope') == 'field_settings_resume')
    begin = next(x for x in a if x.get('event') == 'capture_begin' and x.get('capture') == '07d-explicit-resume')
    end = next(x for x in a if x.get('event') == 'capture_end' and x.get('capture') == '07d-explicit-resume')
    death_notice = next(x for x in events if x.get('event') == 'notification' and x.get('message') == 'Kestrel  ›  Operator' and x['simulation_tick'] > before['simulation_tick'])
    death = next(x for x in events if x.get('event') == 'alive' and x['round_number'] == 2 and x['local_actor']['alive'] is False)
    disk = READ(next(d.rglob('offline_training.json')))
    initial = events[0]['initial_profile']
    last = paused['state']
    checks = {
        'original_failed_result_retained': r['passed'] is False and r['error'] == 'Explicit resume changed living player, focus, round, weapon, ammunition, or simulation speed',
        'whole_original_300s_budget_not_exhausted': r['elapsed_seconds'] < 300,
        'same_living_actor_through_resume_frame_fence_and_after_capture_before_analysis': all(same_living(s) for s in states),
        'settings_stay_frozen_until_explicit_resume': primary['resume_after_analysis'] is False and 'resumed' not in primary and all(primary['after_analysis'][k] == base[k] for k in ('elapsed', 'simulation_tick'))
            and base['elapsed'] == settings['state']['elapsed'] and base['simulation_tick'] == settings['state']['simulation_tick']
            and all(s['ui']['paused'] is True for s in (base, primary['after_analysis'], settings['state']))
            and primary['after_analysis']['local_actor']['health'] == base['local_actor']['health'] == settings['state']['local_actor']['health'] == 100,
        'physical_Escape_ACK_release_and_two_frame_fence': down['seconds'] < resumed['seconds'] < release['seconds'] < ready['seconds'] < begin['seconds'] < end['seconds']
            and resumed['state']['ui']['paused'] is False and ready['state']['ui']['paused'] is False
            and ready['state']['drawn_frames'] >= resumed['state']['drawn_frames'] + 2,
        'resume_frame_fence_inside_original_10_seconds': 0 < ready['seconds'] - down['seconds'] < 10,
        'resumed_screenshot_before_analysis_pause': before['wall_msec'] > ready['state']['wall_msec'] and before['simulation_tick'] > ready['state']['simulation_tick']
            and before['local_actor']['alive'] is True and before['local_actor']['health'] == 100,
        'later_raw_death_notice_and_dead_paused_state': before['simulation_tick'] < death_notice['simulation_tick'] <= death['simulation_tick'] == last['simulation_tick']
            and last['local_actor']['alive'] is False and last['local_actor']['health'] == 0
            and last['local_actor']['deaths'] == actor['deaths'] + 1 and last['local_actor']['id'] == actor['id']
            and last['ui']['focused'] is True and last['ui']['paused'] is True,
        'resumed_HUD_analysis_not_completed': 'paused' not in hud and 'after_analysis' not in hud
            and not any(x['label'].startswith('07d-explicit-resume:') for x in r['ocr_commands']) and 'native_settings_resume' not in r,
        'disk_settings_changed_but_reload_not_reached': initial['settings']['sensitivity'] == .0028 and disk['settings']['sensitivity'] == .0051
            and 'settings_loaded_into_reopened_process' not in r and len(r['commands']) == 1,
        'LEAVE_reopen_focus_and_typed_fence_unreached': not any(x.get('event') == 'click_text' and x.get('caption') == 'LEAVE MATCH' for x in a)
            and not (d / 'restart-profile-trace').exists() and 'native_focus_recovery' not in r and 'failure_kind' not in r
            and not any(x.get('event', '').startswith('native_focus') for x in a),
        'failed_client_terminated_not_normal_close': r['commands'][0]['exit_code'] == 1 and r['cleanup_errors'] == [],
    }
    return {'run_id': 39916539053, 'source_commit': 'a089473481ced0f2e7b2a7468bbc5d079f92f0ff',
            'whole_journey_passed': False, 'checks_of_reached_failure_facts': checks, 'all_reached_fact_checks_passed': all(checks.values()),
            'original_error': r['error'], 'elapsed_seconds': r['elapsed_seconds'],
            'native_settings_resume_transaction_unavailable': 'native_settings_resume' not in r,
            'typed_focus_rejection': 'UNREACHED; no native_focus_recovery or failure_kind field exists',
            'primary_pause': primary, 'settings_ready': settings, 'native_resume': resumed, 'Escape_down': down,
            'Escape_release': release, 'two_frame_fence': ready, 'resume_transition_wall_seconds': ready['seconds'] - down['seconds'],
            'capture_begin': begin, 'capture_end': end, 'after_capture_before_HUD_analysis': before,
            'ordinary_death_notification': death_notice, 'dead_state_event': death, 'analysis_pause_observation': paused,
            'saved_profile': disk, 'initial_profile': initial, 'commands': r['commands'],
            'unreached': ['completed living resumed-HUD analysis', 'strict LEAVE OCR/click and menu return', 'normal first-client close',
                          'reopened settings load and 10 capture bracket', 'held native focus loss/restoration', 'typed focus-liveness rejection',
                          'release and fresh W response', '11a/11b/11c living capture sequence', 'normal second-client close'],
            'scope': 'Recompute partial facts of an actual failed journey. Original PNG shows living 100-health SMG; no exact pixel-to-tick claim. Death invalidates the later living analysis predicate; this does not establish missed input, incorrect pause behavior or source-caused regression.'}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('root', type=Path)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    r = audit(a.root)
    a.output.write_text(json.dumps(r, indent=2) + '\n')
    print(json.dumps({'whole_journey_passed': False, 'all_reached_fact_checks_passed': r['all_reached_fact_checks_passed'],
                      'checks': r['checks_of_reached_failure_facts'], 'resume_transition_wall_seconds': r['resume_transition_wall_seconds']}))
