#!/usr/bin/env python3
"""Recompute retained raw native evidence; do not invoke production predicates."""
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

OUT = Path(__file__).resolve().parent
ROOT = Path('/workspace/sightbreak-offline-candidate')
PROBE = ROOT / 'builds/candidate-r2-settings-probe-r3'
COMMIT = '171169e545a91e271ad8c73a571aeee6fe37dd90'


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    result = json.loads((PROBE / 'results.json').read_text())
    actions = json.loads((PROBE / 'actions.json').read_text())
    events = [json.loads(line) for line in (PROBE / 'initial-offline-trace/events.jsonl').read_text().splitlines()]
    resume = result['native_settings_resume']
    before, after, resumed, ready, captured = (resume[name] for name in ('paused_before_settings', 'paused_after_settings', 'resumed', 'capture_ready', 'after_capture'))
    source = subprocess.check_output(['git', '-C', str(ROOT), 'show', COMMIT + ':scripts/verify_offline_export.py'])
    source_text = source.decode()
    block = source_text[source_text.index("        capture('07-field-menu')\n"):source_text.index('        ui.request_close()\n        client.wait(timeout=min(20, remaining()))')]
    start = next(row for row in actions if row.get('event') == 'wait_begin' and row.get('label') == 'Actual living player explicitly resumes after field settings')
    fence = next(row for row in actions if row.get('event') == 'wait_completed' and row.get('label') == 'Two drawn frames after explicit native settings resume')
    key_up = next(row for row in actions if row.get('scope') == 'field_settings_resume' and row.get('key') == 'Escape' and row.get('down') is False)
    capture = next(row for row in actions if row.get('event') == 'capture_begin' and row.get('capture') == '07d-explicit-resume')
    observation_states = [row['state'] for row in actions if row.get('event') == 'offline_observation']
    contexts = [before, after, resumed, ready, captured]
    contexts += [row[name] for row in result['hud_analysis_pauses'] if row['capture'] == '07d-explicit-resume' for name in ('before', 'paused', 'after_analysis')]
    checks = {
        'frozen_clean_source': result['source']['source_commit'] == COMMIT and result['source']['source_dirty'] is False,
        'export_identity_matches_file': digest(ROOT / 'builds/candidate-r2/linux/sightbreak.x86_64') == result['executable_sha256'] == result['artifact_source']['artifact']['sha256'],
        'production_script_hash': hashlib.sha256(source).hexdigest() == result['settings_only_driver']['production_controller_sha256'],
        'verbatim_settings_block_hash': hashlib.sha256(block.encode()).hexdigest() == result['settings_only_driver']['verbatim_settings_block_sha256'],
        'stock_initial_conditions': events[0]['initial_conditions'] == 'stock_spawns_teams_random_seeds' and events[0]['protocol'] == 6 and events[0]['prediction_enabled'] is False,
        'unchanged_stock_rules': events[0]['rules'] == {'buy_seconds': 15.0, 'defuse_seconds': 5.0, 'device_seconds': 35.0, 'plant_seconds': 3.0, 'round_seconds': 100.0, 'win_score': 7},
        'all_contexts_same_living_focused_player': all(state['phase'] == 'live' and state['round_number'] == 1 and state['time_scale'] == 1 and state['ui']['screen'] == 'game' and state['ui']['focused'] is True and state['local_actor']['alive'] is True and state['local_actor']['deaths'] == 0 and (state['local_actor']['id'], state['local_actor']['weapon'], state['local_actor']['ammo'], state['local_actor']['reserve']) == (1, 'sidearm', 15, 60) for state in contexts),
        'settings_freeze_exact_tick_time_health': before['simulation_tick'] == after['simulation_tick'] and before['elapsed'] == after['elapsed'] and before['local_actor']['health'] == after['local_actor']['health'] and before['ui']['paused'] is True and after['ui']['paused'] is True,
        'fresh_pause_and_resume_observations': before['wall_msec'] < after['wall_msec'] < resumed['wall_msec'] < ready['wall_msec'],
        'real_resume_has_simulation_progress': resumed['simulation_tick'] > after['simulation_tick'] and resumed['elapsed'] > after['elapsed'] and resumed['ui']['paused'] is False,
        'two_actual_drawn_frames': ready['drawn_frames'] >= resumed['drawn_frames'] + 2 and ready['ui']['paused'] is False,
        'states_retained_in_raw_actions': all(state in observation_states for state in (before, after, resumed, ready)),
        'escape_released_before_fence_capture': start['held_keys'] == ['Escape'] and start['seconds'] < key_up['seconds'] < fence['seconds'] < capture['seconds'] and key_up['held_keys'] == [],
        'shared_transition_budget_10s': start['budget_seconds'] <= 10 and fence['seconds'] - start['seconds'] < 10 and resume['transition_watchdog_seconds'] == 10,
        'raw_hud_values_agree': all((result[name]['health'], result[name]['ammo'], result[name]['reserve']) == (100, 15, 60) for name in ('boundary_hud', 'resumed_hud')),
        'actual_clean_exit': result['passed'] is True and result['initial_exit'] == 0 and result['cleanup_errors'] == [] and all(row['exit_code'] == 0 for row in result['commands']),
        'scope_does_not_claim_full_journey': result['native_settings_only'] is True and result['full_offline_journey'] == 'UNVERIFIED' and result['settings_restart'] == 'NOT_RUN',
    }
    summary = {'source_commit': COMMIT, 'scope': 'actual Linux native first stock live match, default sidearm, exact settings block; no full journey or restart',
               'checks': checks, 'all_checks_pass': all(checks.values()), 'elapsed_seconds': result['elapsed_seconds'],
               'transition_wall_seconds': fence['seconds'] - start['seconds'], 'receipt': resume,
               'raw_files': []}
    paths = [path for path in PROBE.rglob('*') if path.is_file() and not any(part in ('cache', 'shader_cache') for part in path.parts)]
    with zipfile.ZipFile(OUT / 'native-focused-raw.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(paths):
            relative = path.relative_to(PROBE)
            summary['raw_files'].append({'path': str(relative), 'sha256': digest(path), 'bytes': path.stat().st_size})
            archive.write(path, relative)
    summary['raw_archive_sha256'] = digest(OUT / 'native-focused-raw.zip')
    (OUT / 'native-recomputed.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps({'checks': len(checks), 'all_checks_pass': summary['all_checks_pass'], 'failed': [name for name, value in checks.items() if not value],
                      'transition_wall_seconds': summary['transition_wall_seconds'], 'raw_files': len(paths)}, indent=2))


if __name__ == '__main__':
    main()
