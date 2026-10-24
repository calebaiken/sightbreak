#!/usr/bin/env python3
"""Audit retained original files only. Does not run engine, compiler, input or OCR."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import struct
import subprocess
import sys

REPORT = Path(__file__).resolve().parent
ROOT = REPORT.parents[4]
sys.path.insert(0, str(ROOT / 'scripts'))
from native_log import failed


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--raw-directory', type=Path, default=ROOT / 'builds/review-c088')
    parser.add_argument('--output', type=Path, default=REPORT / 'audit.json')
    args = parser.parse_args()
    qa, receipts = args.raw_directory / 'qa', args.raw_directory / 'receipts'
    assertions = 0

    def check(value, label):
        nonlocal assertions
        assertions += 1
        if not value:
            raise AssertionError(label)

    def read(path):
        return json.loads(path.read_text())

    def qread(name):
        return read(qa / name)

    identity = read(REPORT / 'source-audit.json')
    fields = ('source_commit', 'source_game_tree', 'source_content_sha256', 'source_validation_sha256')

    def source(record):
        check(all(record[key] == identity[key] for key in fields), 'Exact source identity')
        check(record['source_dirty'] is False and record['source_game_dirty'] is False, 'Clean actual source')

    def labels(capture, phrase):
        wanted = ' '.join(phrase.upper().split())
        rows = [r for r in capture.get('text', []) if isinstance(r.get('confidence'), (int,float))
                and not isinstance(r['confidence'],bool) and math.isfinite(r['confidence']) and r['confidence'] >= .8
                and ' '.join(r.get('text','').upper().split()) == wanted]
        for row in rows:
            box = row.get('box_normalized_bottom_left', [])
            check(len(box) == 4 and all(isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v) for v in box)
                  and min(box[:2]) >= 0 and min(box[2:]) > 0 and box[0]+box[2] <= 1 and box[1]+box[3] <= 1, 'Original confident in-bounds label')
        return rows

    run, job = read(REPORT / 'run-final.json'), read(REPORT / 'job-final.json')
    check(run['id'] == 39912086121 and job['id'] == 120277159133 and job['run_id'] == run['id'], 'Exact run/job')
    check(run['head_sha'] == job['head_sha'] == identity['source_commit'], 'Exact frozen head')
    check(run['head_branch'] == job['head_branch'] == 'codex/v1-qualify-mac-c08889b', 'Immutable qualification ref')
    check(run['run_attempt'] == job['run_attempt'] == 1 and run['event'] == 'workflow_dispatch', 'One original attempt')
    check(run['path'] == '.github/workflows/desktop-alpha.yml' and run['created_at'] == '2026-10-23T06:32:13Z', 'Workflow and creation')
    check(run['conclusion'] == job['conclusion'] == 'failure', 'Retain actual workflow failure')
    jobs = read(REPORT / 'jobs-final.json')['jobs']
    check(len(jobs) == 1 and jobs[0]['id'] == job['id'] and job['labels'] == ['macos-15'], 'Sole selected ARM lane')
    steps = {row['number']: row for row in job['steps']}
    check([n for n, row in steps.items() if row['conclusion'] == 'failure'] == [17, 19, 25], 'Three original failed steps')
    check(all(steps[n]['conclusion'] == 'success' for n in (12, 13, 14, 20, 21, 22, 23, 24, 35, 37, 38)), 'Separate completed scopes')
    log = (REPORT / 'job-decoded.txt').read_text()
    check('Image: macos-15-arm64' in log and '4.7.2.stable.official.ed1daf0bf' in log, 'Actual runner and engine headers')
    check(identity['source_commit'] in log and 'git log -1 --format=%H' in log, 'Original checkout output')
    controls_log = log.split('##[group]Run python scripts/test_macos_ordinary.py -v',1)[1].split('##[group]Run python scripts/verify_macos_ordinary.py',1)[0]
    check([int(x) for x in re.findall(r'Ran (\d+) tests',controls_log)] == [14,7,2,11] and len(re.findall(r'Z OK\s*$',controls_log,re.M)) == 4, 'All four ordinary source commands passed 34 tests')

    # Independently reproduce all tracked input hashes from exact Git objects.
    tracked = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', identity['source_commit'], 'game', 'scripts', '.github'], cwd=ROOT, text=True).splitlines()
    inputs, contents, validation = {}, hashlib.sha256(), hashlib.sha256()
    blobs = {}
    for name in tracked:
        data = subprocess.check_output(['git', 'show', identity['source_commit']+':'+name], cwd=ROOT)
        blobs[name] = data
        inputs[name] = hashlib.sha256(data).hexdigest()
        if name.startswith('game/') and not name.startswith('game/tests/'):
            contents.update(name[5:].encode()+b'\0'+data+b'\0')
    for prefix in ('scripts/', '.github/', 'game/tests/'):
        for name in tracked:
            if name.startswith(prefix):
                validation.update(name.encode()+b'\0'+blobs[name]+b'\0')
    check(inputs == identity['all_input_sha256'], 'Complete Git input hashes')
    check(contents.hexdigest() == identity['source_content_sha256'] and validation.hexdigest() == identity['source_validation_sha256'], 'Independent content and validation digests')
    check(len(identity['game_resources_sha256']) == 323, 'Complete 323-file game inventory')

    meta = read(REPORT / 'artifacts-final.json')['artifacts']
    for identifier, name in ((12483606939, 'arm-39912086121-qa.zip'), (12483084532, 'arm-39912086121-receipts.zip')):
        row = next(row for row in meta if row['id'] == identifier)
        path = REPORT / name
        check(path.stat().st_size == row['size_in_bytes'] and sha(path) == row['digest'].removeprefix('sha256:'), 'Original outer ZIP digest')
        check(row['workflow_run']['head_sha'] == identity['source_commit'] and row['workflow_run']['id'] == run['id'], 'Artifact belongs to exact run')
    inner = args.raw_directory / 'receipts-outer/qa-receipts.zip'
    check(inner.stat().st_size == 1267232 and sha(inner) == '94f4a0ed63ad14f7988120e2832cad08f228b24b86477689a489c30e00e76f84', 'Inner packaged-receipt digest in original log')
    index = read(receipts / 'qa-receipts-index.json')
    duplicates = 0
    for row in index['files']:
        path = receipts / row['archive_path']
        check(path.stat().st_size == row['bytes'] and sha(path) == row['sha256'], 'Indexed original receipt '+row['path'])
        other = qa / row['path']
        if other.is_file():
            check(path.read_bytes() == other.read_bytes(), 'Original artifact overlap '+row['path'])
            duplicates += 1
    files = [{'path': str(p.relative_to(qa)), 'bytes': p.stat().st_size, 'sha256': sha(p)} for p in sorted(qa.rglob('*')) if p.is_file()]
    (REPORT / 'files.json').write_text(json.dumps(files, indent=2)+'\n')

    manifest, verification = qread('macos/source.json'), qread('verification/results.json')
    source(manifest)
    source(verification)
    check(manifest['export_completed'] and manifest['built_at_utc'].startswith('2026-10-23T06:33:00'), 'Fresh export after dispatch')
    check(all(row['exit_code'] == 0 and row['clean_log'] for row in verification['runs']), 'Original startup exits')
    check(verification['targets']['macos']['pck_resources'] == 134, 'Recorded native package resource inspection')
    pre, menu, ordinary = (qread(name+'/results.json') for name in ('macos-input-preflight', 'macos-menu-input', 'macos-ordinary-input'))
    for data in (pre, menu, ordinary):
        source(data['source'])
        check(data['artifact_source'] == manifest and data['source_unchanged'], 'Fresh export and source preserved')
        check(data['permission_requests_made'] == 0, 'No permission requests')
    check(pre['status'] == 'READY_FOR_INPUT_ATTEMPT' and pre['architecture'] == 'arm64' and pre['input_events_posted'] == 0, 'Read-only native preflight')
    check(all(pre['permissions'][key] is True for key in ('CGPreflightPostEventAccess', 'CGPreflightScreenCaptureAccess')), 'Actual preflight permissions')
    check(pre['executable_sha256'] == menu['executable_sha256'] == manifest['artifact']['sha256'], 'Native executable descriptor binding')
    check(pre['normal_exit_code'] == 0 and pre['cleanup']['owned_group_gone'] and not pre['cleanup']['signals_sent'], 'Preflight ordinary teardown')
    check(pre['profile_entries_unchanged'] and pre['seconds'] < 90, 'Preflight preserved profile and bounded')
    for data in (menu, ordinary):
        check(data['preflight_sha256'] == sha(qa/'macos-input-preflight/results.json'), 'Same preflight bytes')
    check(menu['passed'] and menu['status'] == 'PASS_MENU_NAVIGATION_ONLY' and menu['seconds'] < 150, 'Actual menu scope passes')
    check(menu['ordinary_termination_requested'] and menu['normal_exit_code'] == 0 and menu['profile_entries_unchanged'], 'Menu ordinary close and profile')
    check(menu['cg_event_post_attempts'] == menu['cg_event_post_attempts_after_cleanup'] == 5, 'Five actual menu event posts')
    for row in menu['cleanup']:
        check(row['owned_group_gone'] and not row['signals_sent'] and row['exit_code'] == 0, 'Menu group exits normally')
    for row in menu['captures']:
        base = qa/'macos-menu-input'/row['name']
        cap = read(base.with_suffix('.json'))
        check(list(struct.unpack('>II',base.with_suffix('.png').read_bytes()[16:24])) == cap['image_dimensions'], 'Independent original PNG dimensions')
        check(sha(base.with_suffix('.png')) == row['png_sha256'] and sha(base.with_suffix('.json')) == row['receipt_sha256'], 'Original menu capture hashes')
        check(cap['owner_pid'] == menu['client_pid'] and cap['window_id'] == menu['selected_client_window']['window_id'], 'Exact menu owner/window')
        check(cap['image_dimensions'] == [960, 568] and cap['point_pixel_scale'] == 1 and cap['bounds_points_including_chrome'] == [40, 32, 960, 568], 'Actual menu pixel mapping')
        check(cap['input_events_posted'] == cap['permission_requests_made'] == 0, 'Read-only menu capture')
        check(cap['passed'] and cap['permissions']['CGPreflightScreenCaptureAccess'], 'Original native successful capture')
        if row['screen_checked'] == 'menu':
            check(all(len(labels(cap,label)) == 1 for label in ('SETTINGS','OPERATOR RECORD')) and not labels(cap,'FIELD SETTINGS'), 'Actual home labels')
        if row['screen_checked'] == 'settings':
            check(len(labels(cap,'FIELD SETTINGS')) == 1 and not labels(cap,'OPERATOR RECORD') and not labels(cap,'SETTINGS'), 'Actual Settings labels')
    menu_actions = menu['actions']
    settings = qread('macos-menu-input/01-menu-0.json')
    target = next(row for row in settings['text'] if row['text'] == 'SETTINGS' and row['confidence'] >= .8)
    x,y,w,h = target['box_normalized_bottom_left']
    mapped = [40+(x+w/2)*960, 32+(1-y-h/2)*568]
    # Current target coordinates come from original Vision boxes and chrome.
    check(all(math.isfinite(x) for x in mapped), 'Finite menu target')
    posts = [a for a in menu_actions if a['event'] == 'cg_event_post_attempt']
    check([a['event_kind'] for a in posts] == ['pointer_move','lmb_down','lmb_up','escape_down','escape_up'], 'Original menu event schedule')
    pointer = next(a for a in menu_actions if a['event'] == 'settings_pointer_observed')
    check(pointer['target_points'] == mapped and max(abs(a-b) for a,b in zip(mapped,pointer['actual_pointer_points'])) < .001, 'Independent mapping agrees with actual native pointer')
    controls = [a for a in menu_actions if a['event'] == 'native_control_observed']
    check([(a['control'],a['down']) for a in controls] == [('lmb',True),('lmb',False),('escape',True),('escape',False)], 'Actual OS down/up acknowledgements')
    check([a['screen'] for a in menu_actions if a['event']=='screen_confirmed'] == ['menu','settings','menu'], 'Original successful menu navigation order')

    suites, counts = qread('regressions/results.json'), {}
    check([row['suite'] for row in suites] == ['actor','match','authority_order','state_privacy','movement_prediction','peer_lifecycle','input_mode'], 'Retain stopped seven-suite prefix')
    for row in suites:
        text = (qa/'regressions'/Path(row['log']).name).read_text()
        check(row['exit'] == 0 and row['wall_seconds'] < 120 and row['clean_log'] is (not failed(text)), 'Actual suite exit/budget/strict scan')
        matches = re.findall(r'checks[=:]([0-9]+)', text)
        if matches:
            counts[row['suite']] = int(matches[-1])
        else:
            match = re.search(r'(\d+)/(\d+) passed|(\d+) checks, 0 failures', text)
            counts[row['suite']] = int(next(v for v in match.groups() if v is not None))
        for field in ('before', 'after'):
            receipt = row[field]
            producer = qread('regressions/'+Path(receipt['producer_receipt']).name)
            check(all(producer[k] == receipt[k] for k in producer), 'Exact retained native producer')
            check(receipt['run']['exit'] == 0 and receipt['run']['clean_log'] and receipt['run']['wall_seconds'] < 30, 'Producer exit and original bound')
            check(producer['uses_custom_user_dir'] and producer['custom_user_dir'].endswith('/'+row['suite']), 'Suite native private identity')
        check(row['before']['user_data_dir'] == row['after']['user_data_dir'] and not row['before']['profile_exists'] and not row['before']['diagnostics_exist'], 'Fresh stable suite identity')
    check(sum(counts.values()) == 1584 and not suites[-1]['clean_log'] and all(r['clean_log'] for r in suites[:-1]), 'Six clean suites and failed leak gate after 1584 assertions')
    for name in ('regressions/isolation.json', 'source-leak-verbose/repeat/isolation.json'):
        data = qread(name)
        check(data['source_resources_sha256'] == identity['game_resources_sha256'], 'Exact complete game inventory')
        check(data['passed'] is False and data['failure']['message'] == 'input_mode failed; raw output retained', 'Original strict failure retained')
        check(data['source_resources_unchanged'] and data['copied_resources_unchanged'] and data['temporary_project_removed'], 'Source/copy/temp preservation')
        check(not data['finalization_failures'] and all(r['removed'] for r in data['cleanup']), 'Owned native-test namespace removal')
    verbose = qread('source-leak-verbose/diagnostic.json')
    source(verbose['source'])
    source(verbose['source_after'])
    check(not verbose['passed'] and verbose['status'] == 'FAILED' and verbose['selected_suite'] == 'input_mode' and verbose['seconds'] < 240, 'Bounded actual verbose failure')
    check(verbose['source_unchanged'] and verbose['original_evidence_unchanged'], 'Verbose preserved original failure and source')
    for row in verbose['owned_processes']:
        check(not row['timed_out'] and row['wall_seconds'] < row['timeout_seconds'] and row['cleanup']['owned_group_gone'] and not row['cleanup']['signals_sent'], 'Verbose owned group cleanup')
    verbose_text = (qa/'source-leak-verbose/repeat/input_mode.log').read_text()
    check('Leaked instance: AudioStreamPlaybackWAV:' in verbose_text and 'Leaked instance: AudioStreamWAV:' in verbose_text and 'Orphan StringName: Master ' in verbose_text, 'Actual verbose leaked types')

    # Actual ordinary attempt: accepted startup is a separate, limited success.
    check(not ordinary['passed'] and ordinary['status'] == 'FAILED' and ordinary['seconds'] < 300, 'Bounded ordinary failure')
    check(ordinary['failure'] == {'type':'RuntimeError','message':'Expected one exact confident in-bounds native label: DEPLOY · OFFLINE 5V5'}, 'Exact original target rejection')
    check(ordinary['cg_event_post_attempts'] == 0 and not any(a['event'] == 'cg_event_post_attempt' for a in ordinary['actions']), 'Zero ordinary OS input posts')
    check(ordinary['engine'] == menu['engine'] == pre['engine'] == '4.7.2.stable.official.ed1daf0bf', 'Pinned actual editor identity')
    check(ordinary['capture_helper']['source_sha256'] == identity['all_input_sha256']['scripts/macos_window_capture.swift'], 'Actual read-only capture helper source')
    command = ordinary['client_command']
    check(command[1:12] == ['--audio-driver','Dummy','--log-file','user://mac-ordinary-engine.log','--windowed','--resolution','1280x720','--position','40,60','--','--offline-validation']
          and len(command)==13 and command[-1].startswith('--offline-trace-dir='), 'Exact unchanged ordinary launch arguments')
    check(not any(key in ordinary for key in ('initial_event','native_fire','native_reload','native_field_menu','living_hud_captures')), 'Do not invent unreached gameplay witnesses')
    check(not (qa/'macos-ordinary-input/stock-offline-trace').exists(), 'No stock gameplay trace produced')
    check(ordinary['budgets_seconds'] == {'total':300,'compile':60,'window':30,'focus':5,'menu':60,'deploy':30,'live':60,'fire':5,'reload_start':5,'reload_complete':15,'reload_frames':5,'field_menu':10,'return_menu':30,'close':20,'capture':25}, 'Original budgets retained')
    actions = ordinary['actions']
    check(read(qa/'macos-ordinary-input/actions.json') == actions, 'Exact separate action trace')
    pins = [a for a in actions if a['event'] == 'input_geometry_pinned']
    focuses = [a for a in actions if a['event'] == 'focus_before_request']
    check(len(pins) == len(focuses) == 1 and focuses[0]['focus_budget_seconds'] <= 5, 'One focus and irreversible pin')
    check(pins[0]['seconds'] < 70 and pins[0]['bounds_points_including_chrome'] == [0,25,1004,664], 'Actual stable geometry pinned within menu bound')
    observed_focus = next(a for a in actions if a['event']=='focus_observed')
    check(observed_focus['seconds']-focuses[0]['seconds'] < 5 and observed_focus['native_state']['foreground_pid']==3247, 'Actual focus observed within original five seconds')
    started_window = next(a for a in actions if a['event']=='stage_begin' and a['label']=='Exact owned visible native window')
    found_window = next(a for a in actions if a['event']=='stage_complete' and a['label']==started_window['label'])
    check(found_window['seconds']-started_window['seconds'] < 30 and pins[0]['seconds']-found_window['seconds'] < 60, 'Actual window/menu deadlines')
    helpers = [a for a in actions if a['event']=='helper_command']
    check(helpers[0]['budget_seconds']==60 and all(a['budget_seconds']<=25 for a in helpers[1:]), 'Unchanged compiler/capture allocations')
    check(ordinary['first_client_window']['bounds_points_including_chrome'] == [0,25,1024,684], 'Initial native window differs from final window')
    check(ordinary['selected_client_window'] == {'owner_pid':3247,'window_id':55,'bounds_points_including_chrome':[0,25,1004,664]}, 'Exact selected current native window')
    for a in actions:
        if a['event'] == 'owned_window_guard' and a['seconds'] >= pins[0]['seconds']:
            rows = [r for r in a['observed_owned_layer_zero_windows'] if r['owner_pid'] == 3247 and r['onscreen'] is True]
            check(len(rows) == 1 and rows[0]['window_id'] == 55 and rows[0]['bounds_points_including_chrome'] == [0,25,1004,664], 'Unique current pinned owned visible window')
    attempts = ordinary['capture_attempts']
    check(len(attempts) == 8 and [r['accepted'] for r in attempts] == [False]*6+[True,True], 'Six rejected splashes, two accepted menus')
    for row in attempts:
        check(row['finished_seconds']-row['started_seconds'] < 25 and row['finished_seconds'] < 70, 'Actual startup capture bound')
        for name, descriptor in row['retained_files'].items():
            path = qa/'macos-ordinary-input'/name
            check(path.stat().st_size == descriptor['bytes'] and sha(path) == descriptor['sha256'], 'Retained original capture attempt bytes')
    deploy_rows = []
    for row in ordinary['captures']:
        base = qa/'macos-ordinary-input'/row['name']
        cap = read(base.with_suffix('.json'))
        check(list(struct.unpack('>II',base.with_suffix('.png').read_bytes()[16:24])) == cap['image_dimensions'], 'Independent ordinary PNG dimensions')
        check(sha(base.with_suffix('.png')) == row['png_sha256'] and sha(base.with_suffix('.json')) == row['receipt_sha256'], 'Accepted ordinary original captures')
        check(cap['owner_pid'] == 3247 and cap['window_id'] == 55 and cap['image_dimensions'] == [1004,664] and cap['point_pixel_scale'] == 1, 'Actual ordinary owner/window/pixels')
        check(cap['bounds_points_including_chrome'] == cap['scwindow_frame_points'] == [0,25,1004,664], 'SCWindow/CG mapping agrees')
        check(cap['input_events_posted'] == cap['permission_requests_made'] == 0, 'Read-only ordinary screenshot')
        check(cap['passed'] and cap['permissions']['CGPreflightScreenCaptureAccess'] and all(len(labels(cap,label))==1 for label in ('SETTINGS','OPERATOR RECORD')) and not labels(cap,'FIELD SETTINGS'), 'Actual accepted home identity')
        targets = [r for r in cap['text'] if 'DEPLOY' in r['text']]
        check(len(targets) == 1 and targets[0]['confidence'] == .5 and targets[0]['text'] == 'DEPLOY • OFFLINE 5V5', 'Actual unreadied target text and confidence')
        deploy_rows.append({'capture':row['name'],**targets[0]})
    check(ordinary['failure_ordinary_close'] == {'needed':True,'request_accepted':True,'exit_code':0}, 'Actual failure-path ordinary exit zero')
    for row in ordinary['cleanup']:
        check(row['exit_code'] == 0 and row['owned_group_gone'] and not row['signals_sent'], 'Ordinary owned group clean exit')
    for data, releases in ((menu,('input_release','final_input_release')),(ordinary,('final_input_release',))):
        for key in releases:
            release = data[key]
            check(not release['held_after_release'] and not release['errors'], 'No held owned controls or release errors')
            check(not any(release['native_state'].get(k,False) for k in ('lmb_down','escape_down','reload_down')), 'Final native session controls neutral')

    staged = ordinary['native_artifact_attestation']
    payload = {r['path'].removeprefix('macos/SIGHTBREAK.app/'):{k:r[k] for k in ('bytes','sha256','mode')} for r in manifest['payload'] if r['path'].startswith('macos/SIGHTBREAK.app/')}
    check(staged['original_inventory']['files'] == payload, 'Exact original native payload descriptors')
    check(staged['staged_inventory']['directories'] == staged['original_inventory']['directories'], 'Staging preserves directories')
    copied = staged['staged_inventory']['files']
    check(set(copied) == set(payload)|{'Contents/MacOS/override.cfg'} and all(copied[n] == d for n,d in payload.items()), 'Only new sibling override, same bytes/modes')
    name = Path(ordinary['private_user_directory']).name
    override = '[application]\nconfig/use_custom_user_dir=true\nconfig/custom_user_dir_name="'+name+'"\n'
    check(re.fullmatch(r'SIGHTBREAK-mac-ordinary-[0-9a-f]{32}',name) is not None and staged['override_text'] == override, 'Unique exact two-setting override')
    check(hashlib.sha256(override.encode()).hexdigest() == staged['override_sha256'] == copied['Contents/MacOS/override.cfg']['sha256'], 'Exact override bytes hash')
    check(staged['executable_sha256'] == manifest['artifact']['sha256'] and staged['pck_sha256'] == payload['Contents/Resources/SIGHTBREAK.pck']['sha256'], 'Staged binary/PCK descriptors')
    check(ordinary['payload_unchanged'] and ordinary['default_user_directory_unchanged'] and ordinary['default_user_directory_before'] == ordinary['default_user_directory_after'], 'Entire default userdata and native payload preserved')
    check(ordinary['account_home'] == ordinary['environment_whitelist']['HOME'] == '/Users/runner' and ordinary['private_user_directory'].startswith('/Users/runner/Library/Application Support/'), 'Actual account home and native private data location')
    check(all(ordinary['environment_whitelist'][key] is None for key in ('GODOT_RENDERING_DRIVER','GODOT_RENDERING_METHOD','DYLD_INSERT_LIBRARIES','GODOT_PROJECT_DATA_DIR')), 'No selected rendering/injection/project-data overrides')
    check('mac-ordinary-engine.log' in ordinary['private_user_directory_before_input']['files'], 'Actual native-created private log before input')
    engine_log = qa/'macos-ordinary-input/engine.log'
    check('Godot Engine v4.7.2.stable.official.ed1daf0bf' in engine_log.read_text() and sha(engine_log) == ordinary['private_user_directory_after']['files']['mac-ordinary-engine.log']['sha256'], 'Retained native private engine log bytes')
    check(not any(n.startswith('offline_training.json') for n in ordinary['private_user_directory_after']['files']), 'No fabricated private gameplay profile')

    diagnostics = qread('macos-diagnostics/results.json')
    source(diagnostics['source'])
    check(diagnostics['all_default_graphical_passed'] and diagnostics['exact_source_unchanged'] and len(diagnostics['trials']) == 5, 'Separate startup diagnostic scope')
    for trial in diagnostics['trials']:
        check(trial['passed'] and trial['native_exit_code'] == 0 and trial['clean_log'] and not trial['timed_out'] and not trial['surviving_owned_group'], 'Bounded diagnostic startup/cleanup')
        check(trial['capture']['sha256'] == sha(qa/'macos-diagnostics'/(trial['label']+'.png')), 'Diagnostic original pixels')
    ios = qread('ios-compile/compile.json')
    source(ios['source'])
    ios_export = qread('ios-compile/exported-source.json')
    source(ios_export)
    check(ios_export['export_completed'] and ios_export['target']=='ios', 'Same-source completed iOS export')
    check(ios['compile_completed'] and ios['status'] == 'PASS' and ios['seconds'] < 900 and len(ios['commands']) == 15, 'Separate unsigned iOS compiler scope')
    check(qread('ios-compile/source-before.log') == qread('ios-compile/source-after.log'), 'iOS exact source before/after')
    check('** BUILD SUCCEEDED **' in (qa/'ios-compile/xcodebuild-device.log').read_text(), 'Original successful device build output')
    for row in ios['commands']:
        check(row['exit_code'] == (1 if row['label']=='unsigned-app' else 0) and not row['timed_out'] and row['seconds'] < row['timeout_seconds'], 'iOS actual command exit/bounds')
        check(row['cleanup_complete'] and not row['unexpected_descendants'] and not row['surviving_owned_processes'] and not row['cleanup_errors'], 'iOS recorded command-group cleanup only')
    app = ios['app']
    check(next(r['sha256'] for r in ios_export['payload'] if r['path']=='ios/sightbreak.pck') == app['pck_sha256'], 'Actual unsigned app/export PCK descriptors agree')
    check(app['executable']['architecture'] == 'arm64' and app['executable']['platform'] == 'iOS device' and app['executable']['code_signature_load_command'] is False and not app['signature_directory'] and not app['embedded_profile'], 'Recorded native unsigned arm64 descriptors')
    check(app['pck_resources'] == 134, 'Recorded native iOS resource inspection')
    orphans = re.findall(r'Terminate orphan process: pid \((\d+)\) \(([^)]+)\)', log)
    check(orphans == [('5323','ibtoold'),('5317','ibtoold')], 'Retain actual runner-reaped orphan daemons')
    check(not any('ibtoold' in json.dumps(r.get('surviving_owned_processes')) for r in ios['commands']), 'Command receipts did not establish orphan cleanup')
    logs = list(qa.rglob('*.log'))
    bad_logs = [str(p.relative_to(qa)) for p in logs if failed(p.read_text(errors='replace'))]
    check(bool(bad_logs) and 'regressions/input_mode.log' in bad_logs and 'source-leak-verbose/repeat/input_mode.log' in bad_logs, 'Actual strict failures retained')
    check(not any(p.startswith(('macos-ordinary-input/','macos-menu-input/','ios-compile/')) for p in bad_logs), 'Narrow menu/ordinary/iOS logs are strict-clean')
    images = read(REPORT/'images.json')
    pngs = [r for r in files if r['path'].endswith('.png')]
    check(images['count'] == len(pngs) == 19 and images['unique_sha256'] == len({r['sha256'] for r in pngs}) == 14, 'All original PNGs indexed without omission')
    check({r['path']:r['sha256'] for r in images['images']} == {r['path']:r['sha256'] for r in pngs}, 'Visual coverage binds every original PNG')
    for row in read(REPORT/'witnesses.json'):
        witness, original = REPORT/row['witness'], qa/row['original']
        check(witness.read_bytes() == original.read_bytes() and sha(witness)==row['sha256'] and witness.stat().st_size==row['bytes'], 'Unmodified direct witness copies')
    result = {'evidence_integrity_audit_passed':True,'assertions':assertions,'scope':'Read-only original-file audit; no native run, OCR or final binary reparse',
        'source_commit':identity['source_commit'],'workflow_conclusion':'failure','receipt_index_files':len(index['files']),'identical_qa_overlaps':duplicates,'qa_files':len(files),
        'native_suites_observed':len(suites),'native_reported_assertions':counts,'native_reported_assertions_total':sum(counts.values()),'native_15_suite_9434_gate_passed':False,
        'strict_logs_scanned':len(logs),'strict_failing_logs':bad_logs,'verbose_leaked_types':['AudioStreamPlaybackWAV','AudioStreamWAV'],'runner_reaped_orphans':orphans,
        'preflight_seconds':pre['seconds'],'menu_seconds':menu['seconds'],'menu_settings_target_points':mapped,'menu_groups':len(menu['cleanup']),
        'ordinary_component_passed':False,'ordinary_failure':ordinary['failure'],'ordinary_seconds':ordinary['seconds'],'ordinary_event_posts':ordinary['cg_event_post_attempts'],
        'ordinary_startup_captures':len(attempts),'ordinary_rejected_splashes':6,'ordinary_pin_seconds':pins[0]['seconds'],'ordinary_deploy_vision':deploy_rows,
        'ordinary_group_count':len(ordinary['cleanup']),'ordinary_failure_path_close_exit':0,'ordinary_complete_gameplay_close_qualified':False,
        'ios_compile_seconds':ios['seconds'],'ios_xcodebuild_seconds':next(r['seconds'] for r in ios['commands'] if r['label']=='xcodebuild-device'),'ios_command_groups':len(ios['commands']),
        'ios_binary_independently_reparsed':False,'complete_descendant_cleanup_established':False,'comparison_winner':'c088 startup observation and failure-path close only; neither ordinary gameplay component passes'}
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__ == '__main__':
    main()
