#!/usr/bin/env python3
"""Read retained ARM receipts and original pixels; never execute native code/OCR."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[5] / 'scripts'))
from native_log import failed
from macos_native_input import same_bounds, settings_point
from verify_macos_menu import require_preflight, require_screen


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--qa', type=Path, required=True)
    parser.add_argument('--receipts', type=Path, required=True)
    parser.add_argument('--source-game', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    predicates = 0
    def check(value, description):
        nonlocal predicates
        predicates += 1
        if not value:
            raise AssertionError(description)
    def read(name):
        return json.loads((args.qa / name).read_text())
    identity = json.loads((Path(__file__).parent.parent / 'repeat-b2e0293/source.json').read_text())
    fields = ('source_commit', 'source_game_tree', 'source_content_sha256', 'source_validation_sha256')
    def source(record):
        check(all(record[k] == identity[k] for k in fields), 'Exact combined native source')
        check(record['source_dirty'] is False and record['source_game_dirty'] is False, 'Clean native source')

    index = json.loads((args.receipts / 'qa-receipts-index.json').read_text())
    duplicates = 0
    for row in index['files']:
        path = args.receipts / row['archive_path']
        check(path.stat().st_size == row['bytes'] and sha(path) == row['sha256'], 'Receipt index: '+row['path'])
        other = args.qa / row['path']
        if other.is_file():
            check(path.read_bytes() == other.read_bytes(), 'QA/receipt equality: '+row['path'])
            duplicates += 1
    manifest = read('macos/source.json')
    source(manifest)
    source(read('verification/results.json'))
    pre, menu = read('macos-input-preflight/results.json'), read('macos-menu-input/results.json')
    source(pre['source'])
    source(menu['source'])
    require_preflight(pre, menu['source'], manifest)
    check(menu['preflight_sha256'] == sha(args.qa / 'macos-input-preflight/results.json'), 'Preflight receipt binding')
    check(menu['artifact_source'] == manifest and pre['artifact_source'] == manifest, 'Exact export manifest binding')
    check(menu['executable_sha256'] == manifest['artifact']['sha256'] == pre['executable_sha256'], 'Exact exported executable')
    check(pre['normal_exit_code'] == 0 and pre['cleanup']['owned_group_gone'] and not pre['cleanup']['signals_sent'], 'Preflight ordinary exit')
    check(menu['passed'] and menu['status'] == 'PASS_MENU_NAVIGATION_ONLY' and menu['seconds'] < 150, 'Bounded actual menu')
    check(menu['ordinary_termination_requested'] and menu['normal_exit_code'] == 0, 'Menu ordinary close')
    check(menu['cg_event_post_attempts'] == menu['cg_event_post_attempts_after_cleanup'] == 5, 'Exactly five ordinary menu posts')
    for release in ('input_release', 'final_input_release'):
        data = menu[release]
        check(not data['held_after_release'] and not data['errors'], 'Owned release receipt')
        check(not data['native_state']['lmb_down'] and not data['native_state']['escape_down'], 'Neutral native controls')
    for group in menu['cleanup']:
        check(group['owned_group_gone'] and not group['signals_sent'] and group['exit_code'] == 0, 'Menu owned group gone')
    check(menu['source_unchanged'] and menu['profile_entries_unchanged'] and pre['source_unchanged'], 'Menu/preflight source/profile preservation')
    for cap in menu['captures']:
        base = args.qa / 'macos-menu-input' / cap['name']
        receipt = json.loads(base.with_suffix('.json').read_text())
        check(sha(base.with_suffix('.json')) == cap['receipt_sha256'] and sha(base.with_suffix('.png')) == cap['png_sha256'], 'Original menu capture hashes')
        check(receipt['owner_pid'] == menu['client_pid'] and receipt['window_id'] == menu['selected_client_window']['window_id'], 'Exact menu owned window')
        check(same_bounds(receipt['bounds_points_including_chrome'], [40, 32, 960, 568]), 'Pinned menu chrome')
        check(receipt['image_dimensions'] == [960, 568] and receipt['point_pixel_scale'] == 1, 'Actual menu pixel scale')
        check(receipt['input_events_posted'] == receipt['permission_requests_made'] == 0, 'Read-only capture helper')
        if cap['screen_checked']:
            require_screen(receipt, cap['screen_checked'])
    target = settings_point(read('macos-menu-input/01-menu-0.json'))

    suites, counts = read('regressions/results.json'), {}
    check(len(suites) == 15 and len({row['suite'] for row in suites}) == 15, 'All 15 native suites')
    for row in suites:
        check(row['exit'] == 0 and row['clean_log'] and row['wall_seconds'] < 120, 'Native suite exit/budget')
        text = (args.qa / 'regressions' / Path(row['log']).name).read_text()
        if row['suite'] in ('bot_dry_weapon', 'gunplay_rules'):
            prefix = 'BOT_DRY_WEAPON_RESULT ' if row['suite'] == 'bot_dry_weapon' else 'GUNPLAY_RULES '
            count = json.loads(next(line[len(prefix):] for line in text.splitlines() if line.startswith(prefix)))['checks']
        else:
            matches = re.findall(r'checks[=:]([0-9]+)', text)
            if matches:
                count = int(matches[-1])
            else:
                match = re.search(r'(\d+)/(\d+) passed|(\d+) checks, 0 failures', text)
                count = int(next(value for value in match.groups() if value is not None))
        counts[row['suite']] = count
        for receipt in (row['before'], row['after']):
            producer = read('regressions/' + Path(receipt['producer_receipt']).name)
            check(all(producer[k] == receipt[k] for k in producer), 'Retained native producer matches suite receipt')
            check(receipt['run']['exit'] == 0 and receipt['run']['clean_log'] and receipt['run']['wall_seconds'] < 30, 'Native producer exit/budget')
            check(producer['uses_custom_user_dir'] and producer['custom_user_dir'].endswith('/' + row['suite']), 'Native suite user identity')
        check(row['before']['user_data_dir'] == row['after']['user_data_dir'] and not row['before']['profile_exists'] and not row['before']['diagnostics_exist'], 'Fresh stable suite userdata')
    check(sum(counts.values()) == 9434, 'Exact reported assertion total')
    isolation = read('regressions/isolation.json')
    inventory = {p.relative_to(args.source_game).as_posix(): sha(p) for p in args.source_game.rglob('*') if p.is_file()}
    check(inventory == isolation['source_resources_sha256'], 'Exact 323-file game source inventory')
    check(isolation['passed'] and isolation['source_resources_unchanged'] and isolation['copied_resources_unchanged'] and isolation['temporary_project_removed'], 'Source-suite isolation finalization')
    check(not isolation['finalization_failures'] and all(row['removed'] for row in isolation['cleanup']), 'Source-suite cleanup')

    native_logs = list(args.qa.rglob('*.log'))
    check(not any(failed(path.read_text(errors='replace')) for path in native_logs), 'Strict native error/leak scan')
    ios = read('ios-compile/compile.json')
    source(ios['source'])
    check(ios['compile_completed'] and ios['status'] == 'PASS' and ios['seconds'] < 900, 'Bounded unsigned iOS compile')
    check(json.loads((args.qa/'ios-compile/source-before.log').read_text()) == json.loads((args.qa/'ios-compile/source-after.log').read_text()), 'iOS exact source before/after')
    check('** BUILD SUCCEEDED **' in (args.qa/'ios-compile/xcodebuild-device.log').read_text(), 'Actual Xcode success marker')
    check(len(ios['commands']) == 15, 'All iOS command receipts')
    for command in ios['commands']:
        expected = 1 if command['label'] == 'unsigned-app' else 0
        check(command['exit_code'] == expected and not command['timed_out'] and command['seconds'] < command['timeout_seconds'], 'iOS command exit/budget')
        check(command['cleanup_complete'] and not command['unexpected_descendants'] and not command['surviving_owned_processes'] and not command['cleanup_errors'], 'iOS owned group cleanup')
    check(not ios['app']['signature_directory'] and not ios['app']['embedded_profile'] and ios['app']['executable']['code_signature_load_command'] is False, 'Native unsigned app attestation')
    check(ios['app']['pck_resources'] == 134, 'Native iOS resource attestation')
    diagnostics = read('macos-diagnostics/results.json')
    source(diagnostics['source'])
    check(len(diagnostics['trials']) == 5, 'All startup diagnostic trials')
    for trial in diagnostics['trials']:
        check(trial['passed'] and trial['native_exit_code'] == 0 and trial['clean_log'] and not trial['timed_out'] and not trial['surviving_owned_group'], 'Bounded clean startup diagnostic')
        check(trial['capture']['sha256'] == sha(args.qa/'macos-diagnostics'/(trial['label']+'.png')), 'Diagnostic original PNG')
    ordinary = read('macos-ordinary-input/results.json')
    source(ordinary['source'])
    check(ordinary['artifact_source'] == manifest, 'Ordinary exact export manifest')
    check(ordinary['status'] == 'FAILED' and ordinary['passed'] is False, 'Retain ordinary failure')
    check(ordinary['failure'] == {'type': 'RuntimeError', 'message': 'Owned visible window or its geometry changed before input'}, 'Original ordinary window-context rejection')
    check(ordinary['cg_event_post_attempts'] == 0 and ordinary['captures'] == [], 'No ordinary input or accepted capture')
    check(ordinary['source_unchanged'] and ordinary['payload_unchanged'], 'Ordinary source/payload preservation')
    check(ordinary['default_user_directory_unchanged'] and ordinary['default_user_directory_before'] == ordinary['default_user_directory_after'], 'Whole default inventory preserved')
    staged = ordinary['native_artifact_attestation']
    original = staged['original_inventory']
    copied = staged['staged_inventory']
    payload = {row['path'].removeprefix('macos/SIGHTBREAK.app/'): {key: row[key] for key in ('bytes', 'sha256', 'mode')}
               for row in manifest['payload'] if row['path'].startswith('macos/SIGHTBREAK.app/')}
    check(original['files'] == payload, 'Exact original copied-app file descriptors')
    check(copied['directories'] == original['directories'], 'No additional app directories')
    check(set(copied['files']) == set(payload) | {'Contents/MacOS/override.cfg'}, 'Only added sibling override')
    check(all(copied['files'][name] == value for name, value in payload.items()), 'Copied payload bytes/modes preserved')
    private_name = Path(ordinary['private_user_directory']).name
    expected_override = '[application]\nconfig/use_custom_user_dir=true\nconfig/custom_user_dir_name="'+private_name+'"\n'
    override_sha = hashlib.sha256(expected_override.encode()).hexdigest()
    check(staged['override_text'] == expected_override and staged['override_sha256'] == override_sha == copied['files']['Contents/MacOS/override.cfg']['sha256'], 'Exact two-setting override bytes')
    check(staged['executable_sha256'] == manifest['artifact']['sha256'] and staged['pck_sha256'] == payload['Contents/Resources/SIGHTBREAK.pck']['sha256'], 'Staged executable and PCK bound to actual export')
    private_before = ordinary['private_user_directory_before_input']
    check(private_before['directory_exists'] and 'mac-ordinary-engine.log' in private_before['files'], 'Private engine log exists before any input')
    check('Godot Engine v4.7.2.stable.official.ed1daf0bf' in (args.qa/'macos-ordinary-input/engine.log').read_text(), 'Pinned native private engine header')
    check(ordinary['private_user_directory_after']['files']['mac-ordinary-engine.log']['sha256'] == sha(args.qa/'macos-ordinary-input/engine.log'), 'Retained private engine log hash')
    check(not any(name.startswith('offline_training.json') for name in ordinary['private_user_directory_after']['files']), 'Private gameplay profile not fabricated')
    background = read('macos-ordinary-input/00-background-window.json')
    check(background['passed'] and background['owner_pid'] == ordinary['client_pid'] and background['window_id'] == ordinary['selected_client_window']['window_id'], 'Successful read-only original background capture')
    check(same_bounds(background['bounds_points_including_chrome'], ordinary['selected_client_window']['bounds_points_including_chrome']), 'Background matches initially pinned geometry')
    check(background['image_dimensions'] == [1024, 684] and background['input_events_posted'] == background['permission_requests_made'] == 0, 'Original background dimensions and no events')
    check(ordinary['failure_ordinary_close'] == {'needed': True, 'request_accepted': True, 'timed_out': True}, 'Failed public-close timeout retained')
    release = ordinary['final_input_release']
    check(not release['held_after_release'] and not release['errors'] and not any(release['native_state'][key] for key in ('lmb_down', 'escape_down', 'reload_down')), 'Final ordinary native controls neutral')
    clients = [row for row in ordinary['cleanup'] if row['name'] == 'client']
    check(len(clients) == 1 and clients[0]['exit_code'] == -15 and clients[0]['signals_sent'] == ['SIGTERM'] and clients[0]['owned_group_gone'], 'Forced client cleanup remains a failed ordinary close')
    check(all(row['owned_group_gone'] for row in ordinary['cleanup']), 'All ordinary owned groups gone')
    result = {'scope': 'Independent read-only native receipt audit; no native execution or final binary reparse',
              'predicates': predicates, 'receipt_index_files': len(index['files']), 'identical_qa_duplicates': duplicates,
              'native_suites': len(suites), 'reported_assertions': counts, 'reported_assertions_total': sum(counts.values()),
              'game_inventory_files': len(inventory), 'strict_logs_scanned': len(native_logs),
              'menu_seconds': menu['seconds'], 'menu_target_points': target, 'menu_pid': menu['client_pid'],
              'menu_owned_groups': len(menu['cleanup']), 'ios_seconds': ios['seconds'], 'ios_command_groups': len(ios['commands']),
              'diagnostic_trials': len(diagnostics['trials']), 'ordinary_gameplay': 'FAILED_BEFORE_INPUT',
              'ordinary_component_passed': False, 'workflow_conclusion': 'failure',
              'ordinary_seconds': ordinary['seconds'], 'ordinary_cg_events': ordinary['cg_event_post_attempts'],
              'ordinary_private_userdata_established': True, 'ordinary_default_inventory_preserved': True,
              'ordinary_forced_client_cleanup': True, 'ordinary_later_window_geometry': 'NOT_RETAINED',
              'passed_receipt_audit': True}
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
