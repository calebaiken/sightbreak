#!/usr/bin/env python3
"""Independent, read-only audit of retained native run receipts; no engine/API use."""
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import struct

HERE = Path(__file__).resolve().parent
RAW = HERE / 'raw'


def read(name):
    return json.loads((RAW / name).read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def native_path(path):
    # macOS /var is a system symlink to /private/var. Do not resolve on Linux.
    return str(PurePosixPath('/private' + path if path.startswith('/var/') else path)).rstrip('/')


def same_identity(record):
    assert all(record[k] == v for k, v in expected.items())
    assert record['source_dirty'] is False and record['source_game_dirty'] is False


def clean_log(path):
    text = path.read_text(errors='replace')
    assert not re.search(r'^(?:SCRIPT ERROR|ERROR:)|Parse Error|ObjectDB.*leaked|Leaked instance', text, re.M), path
    return text


freeze = json.loads((HERE / 'source-verification.json').read_text())
expected = freeze['identity']
artifacts = json.loads((HERE / 'artifacts.json').read_text())['structuredContent']['artifacts']
archives = json.loads((HERE / 'archive-verification.json').read_text())
artifact_ids = {'receipts': 12409463411, 'qa': 12409623065}
for archive in archives:
    artifact = next(row for row in artifacts if row['id'] == artifact_ids[archive['kind']])
    assert archive['bytes'] == artifact['size_in_bytes'] and 'sha256:' + archive['sha256'] == artifact['digest']
    assert artifact['workflow_run']['id'] == 39741565795 and artifact['workflow_run']['head_sha'] == expected['source_commit']
index = json.loads((HERE / 'qa-receipts-index.json').read_text())
for item in index['files']:
    path = RAW / item['path']
    assert path.stat().st_size == item['bytes'] and digest(path) == item['sha256']

strict = read('regressions/results.json')
isolation = read('regressions/isolation.json')
names = ['actor', 'match', 'authority_order', 'state_privacy', 'movement_prediction',
         'peer_lifecycle', 'input_mode', 'menu_focus', 'offline_diagnostics',
         'hud_objective_hint', 'activity_provenance', 'bot_squad_symmetry', 'transaction_journal', 'gunplay_rules']
assert [row['suite'] for row in strict] == names
assert isolation['source_resources_sha256'] == freeze['game_resource_inventory']
assert all(isolation[k] is True for k in ('passed', 'source_resources_unchanged',
           'copied_resources_unchanged', 'temporary_project_removed'))
assert isolation['failure'] is None and isolation['finalization_failures'] == []
assert len(isolation['cleanup']) == 1 and isolation['cleanup'][0]['removed'] is True
namespace = isolation['namespace']
assert isolation['engine'] == '4.7.2.stable.official.ed1daf0bf'
assert re.fullmatch(r'SIGHTBREAK-native-tests-[0-9a-f]{32}', namespace)
bootstrap = read('regressions/producer-01-bootstrap.json')
assert bootstrap['custom_user_dir'] == namespace + '/bootstrap'
assert bootstrap['profile_exists'] is False and bootstrap['diagnostics_exist'] is False
assert bootstrap['uses_custom_user_dir'] is True and bootstrap['os'] == 'macOS'
assert native_path(bootstrap['user_data_dir']) == native_path(bootstrap['data_dir'] + '/' + namespace + '/bootstrap')
assert native_path(isolation['cleanup'][0]['user_namespace']) == native_path(bootstrap['data_dir'] + '/' + namespace)
clean_log(RAW / 'regressions/producer-01-bootstrap.log')
assert isolation['import']['exit'] == 0 and isolation['import']['clean_log'] is True
clean_log(RAW / 'regressions/private-import.log')
summaries = []
for row in strict:
    suite = row['suite']
    assert type(row['exit']) is int and row['exit'] == 0 and row['clean_log'] is True
    command = row['command']
    assert command[0].endswith('/godot-4.7.2/Godot.app/Contents/MacOS/Godot')
    wanted = (['--headless', '--audio-driver', 'Dummy', '--script', 'res://tests/gunplay_rules_probe.gd'] if suite == 'gunplay_rules' else ['--headless', '--script', 'res://tests/' + suite + '_test.gd'])
    assert command[1] == '--path' and command[3:] == wanted
    assert native_path(command[2]) == native_path(bootstrap['project_path'])
    for phase in ('before', 'after'):
        receipt = row[phase]
        assert receipt['uses_custom_user_dir'] is True and receipt['custom_user_dir'] == namespace + '/' + suite
        assert native_path(receipt['user_data_dir']) == native_path(receipt['data_dir'] + '/' + namespace + '/' + suite)
        assert native_path(receipt['project_path']) == native_path(command[2])
        assert receipt['run']['exit'] == 0 and receipt['run']['clean_log'] is True
        original = read('regressions/' + PurePosixPath(receipt['producer_receipt']).name)
        assert all(receipt[k] == value for k, value in original.items())
        clean_log(RAW / 'regressions' / PurePosixPath(receipt['run']['log']).name)
    assert row['before']['profile_exists'] is False and row['before']['diagnostics_exist'] is False
    data_dir = RAW / 'regressions' / (suite + '-userdata')
    copied = {p.relative_to(data_dir).as_posix(): digest(p) for p in data_dir.rglob('*') if p.is_file() and '.godot' not in p.parts}
    assert copied == row['produced_files_sha256']
    text = clean_log(RAW / 'regressions' / (suite + '.log'))
    if suite == 'actor':
        match = re.search(r'ACTOR TESTS: (\d+) checks, (\d+) failures', text)
    elif suite in ('match', 'transaction_journal'):
        pattern = r'MATCH_TEST: (\d+)/(\d+) passed' if suite == 'match' else r'TRANSACTION_JOURNAL (\d+)/(\d+) passed'
        match = re.search(pattern, text)
        assert match and match[1] == match[2]
    elif suite == 'gunplay_rules':
        result = json.loads(re.search(r'^GUNPLAY_RULES (.+)$', text, re.M)[1])
        assert result['failures'] == []
        match = (None, str(result['checks']), '0')
    else:
        match = re.search(r'checks=(\d+) failures=(\d+)', text)
    assert match and (suite in ('match', 'transaction_journal') or int(match[2]) == 0)
    summaries.append({'suite': suite, 'checks': int(match[1]), 'failures': 0,
                      'exit': row['exit'], 'seconds': row['wall_seconds'],
                      'log_sha256': digest(RAW / 'regressions' / (suite + '.log'))})
journal = (RAW / 'regressions/transaction_journal.log').read_text()
child_output = json.loads(re.search(r'^COMPETING_PROCESS (.+)$', journal, re.M)[1])
child = json.loads(re.search(r'OWNER_BLOCKED (\{[^\n]+\})', '\n'.join(child_output))[1])
assert type(child['pid']) is int and child['pid'] > 0 and child['unchanged'] is True
assert all(child[key] != 0 for key in ('claim', 'clear', 'stage'))
gunplay = (RAW / 'regressions/gunplay_rules.log').read_text()
cases = [json.loads(line[len('GUNPLAY_CASE '):]) for line in gunplay.splitlines() if line.startswith('GUNPLAY_CASE ')]
assert len(cases) == 52 and {row['weapon'] for row in cases} == {'sidearm', 'smg', 'rifle', 'marksman'}
for weapon in ('sidearm', 'smg', 'rifle', 'marksman'):
    rows = [row for row in cases if row['weapon'] == weapon]
    assert len(rows) == 13
    for row in rows:
        if row['kind'] == 'damage':
            before_health, after_health = row['target_before']['health'], row['target_after']['health']
            assert abs(min(before_health, row['expected_damage']) - row['applied_damage']) < .00001
            assert abs(max(0, before_health - row['expected_damage']) - after_health) < .00001
            assert abs(before_health - after_health - row['applied_damage']) < .00001
            assert row['authority_after_visual_matches'] is True and row['feedback_after_remaining'] == 0
        if row['kind'] == 'negative':
            assert row['damage_events'] == row['confirmations'] == 0
            if row['control'] in ('dry', 'reload', 'deploy'):
                assert row['shots'] == 0 and row['ammo_before'] == row['ammo']
assert not (RAW / 'source-leak-verbose').exists()
jobs = json.loads((HERE / 'jobs-final.json').read_text())['structuredContent']['jobs']
assert len(jobs) == 1 and jobs[0]['id'] == 119699758860 and jobs[0]['conclusion'] == 'success'
steps = {row['number']: row for row in jobs[0]['steps']}
assert steps[17]['conclusion'] == 'success' and steps[18]['conclusion'] == steps[19]['conclusion'] == 'skipped'

preflight = read('macos-input-preflight/results.json')
menu = read('macos-menu-input/results.json')
mac_export = read('macos/source.json')
same_identity(mac_export)
assert mac_export['export_completed'] is True
assert mac_export['artifact']['sha256'] == preflight['executable_sha256'] == menu['executable_sha256']
for record in (preflight, menu):
    same_identity(record['source'])
    same_identity(record['artifact_source'])
    assert record['source_unchanged'] is True and record['profile_entries_unchanged'] is True
    assert record['permission_requests_made'] == 0 and record['normal_exit_code'] == 0
assert preflight['status'] == 'READY_FOR_INPUT_ATTEMPT' and preflight['input_events_posted'] == 0
assert preflight['cleanup']['owned_group_gone'] is True
assert menu['preflight_sha256'] == digest(RAW / 'macos-input-preflight/results.json')
assert menu['passed'] is True and menu['status'] == 'PASS_MENU_NAVIGATION_ONLY'
assert menu['cg_event_post_attempts'] == menu['cg_event_post_attempts_after_cleanup'] == 5
assert all(row['owned_group_gone'] and row['exit_code'] == 0 and row['signals_sent'] == [] for row in menu['cleanup'])
for key in ('input_release', 'final_input_release'):
    assert menu[key]['errors'] == menu[key]['held_after_release'] == []
    assert menu[key]['native_state']['lmb_down'] is menu[key]['native_state']['escape_down'] is False
events = read('macos-menu-input/actions.json')
assert [row['event_kind'] for row in events if row['event'] == 'cg_event_post_attempt'] == ['pointer_move', 'lmb_down', 'lmb_up', 'escape_down', 'escape_up']
observed = [row for row in events if row['event'] in ('focus_observed', 'screen_confirmed', 'native_control_observed')]
assert observed and all(row['native_state']['foreground_pid'] == menu['client_pid'] for row in observed)
assert [(row['control'], row['down']) for row in events if row['event'] == 'native_control_observed'] == [('lmb', True), ('lmb', False), ('escape', True), ('escape', False)]
screens = []
for capture in menu['captures']:
    prefix = 'macos-menu-input/' + capture['name']
    receipt = read(prefix + '.json')
    png = RAW / (prefix + '.png')
    assert digest(png) == capture['png_sha256'] and digest(RAW / (prefix + '.json')) == capture['receipt_sha256']
    assert receipt['owner_pid'] == menu['client_pid'] and receipt['window_id'] == menu['selected_client_window']['window_id']
    assert receipt['input_events_posted'] == receipt['permission_requests_made'] == 0
    assert list(struct.unpack('>II', png.read_bytes()[16:24])) == receipt['image_dimensions'] == [960, 568]
    labels = {row['text']: row['confidence'] for row in receipt['text'] if row['confidence'] >= .8}
    if capture['screen_checked'] == 'menu':
        assert all(labels.get(label) == 1 for label in ('SIGHTBREAK', 'OPERATOR RECORD', 'SETTINGS')) and 'FIELD SETTINGS' not in labels
    elif capture['screen_checked'] == 'settings':
        assert labels['FIELD SETTINGS'] == 1 and all(label not in labels for label in ('SIGHTBREAK', 'OPERATOR RECORD', 'SETTINGS'))
    screens.append({'name': capture['name'], 'screen_checked': capture['screen_checked'], 'labels': labels, 'sha256': digest(png)})
for directory in ('macos-input-preflight', 'macos-menu-input'):
    for log in (RAW / directory).glob('*.log'):
        clean_log(log)

ios = read('ios-compile/compile.json')
same_identity(ios['source'])
assert ios['compile_completed'] is True and ios['status'] == 'PASS' and ios['seconds'] < ios['total_command_budget_seconds'] == 900
for name in ('source-before.log', 'source-after.log'):
    same_identity(json.loads((RAW / 'ios-compile' / name).read_text()))
assert (RAW / 'ios-compile/source-before.log').read_bytes() == (RAW / 'ios-compile/source-after.log').read_bytes()
export = read('ios-compile/exported-source.json')
same_identity(export)
pck = [row for row in export['payload'] if row['path'] == 'ios/sightbreak.pck']
assert len(pck) == 1 and pck[0]['sha256'] == ios['app']['pck_sha256']
assert ios['app']['executable']['architecture'] == 'arm64' and ios['app']['executable']['code_signature_load_command'] is False
for command in ios['commands']:
    assert command['exit_code'] == (1 if command['label'] == 'unsigned-app' else 0)
    assert command['timed_out'] is command['unexpected_descendants'] is False
    assert command['cleanup_complete'] is True and command['cleanup_errors'] == command['surviving_owned_processes'] == []
build = (RAW / 'ios-compile/xcodebuild-device.log').read_text()
assert '** BUILD SUCCEEDED **' in build and '** BUILD FAILED **' not in build
assert re.search(r'^CompileC ', build, re.M) and re.search(r'^Ld .* normal(?: arm64)? \(in target', build, re.M)
assert 'CODE_SIGNING_ALLOWED = NO' in build and 'code object is not signed at all' in (RAW / 'ios-compile/unsigned-app.log').read_text()
startup = read('macos-diagnostics/results.json')
same_identity(startup['source'])
assert startup['exact_source_unchanged'] is startup['all_default_graphical_passed'] is True
assert len(startup['trials']) == 5
for trial in startup['trials']:
    assert trial['passed'] is True and trial['native_exit_code'] == 0 and trial['timed_out'] is False
    assert trial['surviving_owned_group'] == [] and trial['elapsed_before_cleanup'] < trial['budget_seconds'] == 120
    assert digest(RAW / 'macos-diagnostics' / (trial['label'] + '.png')) == trial['capture']['sha256']
    clean_log(RAW / 'macos-diagnostics' / (trial['label'] + '.log'))
report = {'strict': {'status': 'PASS_THIS_EXACT_NATIVE_RUN', 'suite_count': len(summaries), 'registration': 'Original12 plus transaction_journal and gunplay_rules', 'checks': sum(row['checks'] for row in summaries), 'suites': summaries, 'namespace': namespace},
          'verbose': {'status': 'NOT_RUN_WORKFLOW_CONDITION', 'reason': 'Strict regressions passed; controls/repeat steps18/19 skipped. No diagnostic directory or verbose object types.'},
          'menu': {'status': menu['status'], 'seconds': menu['seconds'], 'client_pid': menu['client_pid'], 'window': menu['selected_client_window'], 'screens': screens},
          'ios': {'status': 'PASS_UNSIGNED_COMPILE_RECEIPTS_ONLY', 'seconds': ios['seconds'], 'xcode': ios['xcode_version'], 'sdk': ios['iphoneos_sdk_version'], 'pck': pck[0], 'executable': ios['app']['executable'], 'independent_final_binary_reparse': False},
          'startup': {'status': 'PASS_STARTUP_CONTROLS_ONLY', 'trials': len(startup['trials']), 'physical_gpu': False},
          'added_suite_evidence': {'journal_competing_process': child, 'gunplay_cases': len(cases), 'gunplay_cases_per_weapon': 13},
          'receipt_index_files_verified': len(index['files'])}
(HERE / 'verification.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({key: value if key == 'verbose' else {k: v for k, v in value.items() if k not in ('suites', 'screens')} if isinstance(value, dict) else value for key, value in report.items()}, indent=2))
