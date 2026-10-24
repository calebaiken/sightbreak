#!/usr/bin/env python3
"""Read original remote evidence. Never run engine, compiler, native input or OCR."""
import argparse
import copy
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
from macos_deploy_ocr import bind_analysis, derived_deploy_row, canonical_caption, LABEL


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def dimensions(path):
    data = path.read_bytes()
    assert data[:8] == b'\x89PNG\r\n\x1a\n' and data[8:16] == b'\x00\x00\x00\rIHDR'
    return list(struct.unpack('>II', data[16:24]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--raw-directory', type=Path, required=True)
    args = parser.parse_args()
    qa, receipts = args.raw_directory / 'qa', args.raw_directory / 'receipts'
    qread = lambda name: read(qa / name)
    assertions = 0

    def check(value, label):
        nonlocal assertions
        assertions += 1
        if not value:
            raise AssertionError(label)

    identity = read(REPORT / 'source-audit.json')

    def source(record):
        for key in ('source_commit', 'source_game_tree', 'source_content_sha256', 'source_validation_sha256'):
            check(record[key] == identity[key], 'Exact actual source '+key)
        check(record['source_dirty'] is False and record['source_game_dirty'] is False, 'Actual source clean')

    run, job = read(REPORT / 'run-final.json'), read(REPORT / 'job-final.json')
    check(job['run_id'] == run['id'] and run['head_sha'] == job['head_sha'] == identity['source_commit'], 'Exact run/job/source')
    check(run['head_branch'] == job['head_branch'] == 'codex/v1-qualify-mac-c838907', 'Frozen ref')
    check(run['run_attempt'] == job['run_attempt'] == 1 and run['event'] == 'workflow_dispatch', 'One original dispatch attempt')
    check(run['path'] == '.github/workflows/desktop-alpha.yml' and job['labels'] == ['macos-15'], 'Original workflow/ARM lane')
    check(len(read(REPORT / 'jobs-final.json')['jobs']) == 1, 'One selected host')
    check(run['created_at'] > '2026-10-23T07:52:43Z', 'Preregistration commit before dispatch')
    log = (REPORT / 'job-decoded.txt').read_text()
    check('Image: macos-15-arm64' in log and identity['source_commit'] in log, 'Original runner and checkout log')

    # Recompute the exact objects independently of the actual manifest.
    tracked = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', identity['source_commit'], 'game', 'scripts', '.github'], cwd=ROOT, text=True).splitlines()
    check(set(tracked) == set(identity['all_input_sha256']), 'Complete exact tracked source inventory')
    blobs = {}
    for name, digest in identity['all_input_sha256'].items():
        data = subprocess.check_output(['git', 'show', identity['source_commit']+':'+name], cwd=ROOT)
        blobs[name] = data
        check(hashlib.sha256(data).hexdigest() == digest, 'Exact Git object '+name)
    content, validation = hashlib.sha256(), hashlib.sha256()
    for name in tracked:
        if name.startswith('game/') and not name.startswith('game/tests/'):
            content.update(name[5:].encode()+b'\0'+blobs[name]+b'\0')
    for prefix in ('scripts/', '.github/', 'game/tests/'):
        for name in tracked:
            if name.startswith(prefix):
                validation.update(name.encode()+b'\0'+blobs[name]+b'\0')
    check(content.hexdigest() == identity['source_content_sha256'] and validation.hexdigest() == identity['source_validation_sha256'], 'Independent shipping/validation digests')
    meta = read(REPORT / 'artifacts-final.json')['artifacts']
    for archive in REPORT.glob('arm-*-*.zip'):
        row = next(r for r in meta if r['id'] == int(archive.stem.split('-')[-1]))
        check(archive.stat().st_size == row['size_in_bytes'] and sha(archive) == row['digest'].removeprefix('sha256:'), 'Original outer ZIP digest')
        check(row['workflow_run']['id'] == run['id'] and row['workflow_run']['head_sha'] == identity['source_commit'], 'Artifact source/run binding')
    index = read(receipts / 'qa-receipts-index.json')
    overlaps = 0
    for row in index['files']:
        path = receipts / row['archive_path']
        check(path.stat().st_size == row['bytes'] and sha(path) == row['sha256'], 'Raw indexed receipt '+row['path'])
        other = qa / row['path']
        if other.is_file():
            check(other.read_bytes() == path.read_bytes(), 'Overlapping original artifact '+row['path'])
            overlaps += 1
    files = [{'path': str(p.relative_to(qa)), 'bytes': p.stat().st_size, 'sha256': sha(p)}
             for p in sorted(qa.rglob('*')) if p.is_file()]
    (REPORT / 'files.json').write_text(json.dumps(files, indent=2)+'\n')
    manifest = qread('macos/source.json')
    source(manifest)
    verification = qread('verification/results.json')
    source(verification)
    pre, menu, ordinary = (qread(name+'/results.json') for name in ('macos-input-preflight', 'macos-menu-input', 'macos-ordinary-input'))
    for data in (pre, menu, ordinary):
        source(data['source'])
        check(data['artifact_source'] == manifest and data['source_unchanged'], 'Fresh unchanged export')
        check(data['permission_requests_made'] == 0, 'No permission requests')
    check(pre['architecture'] == 'arm64' and pre['input_events_posted'] == 0, 'Actual read-only ARM preflight')
    check(pre['status']=='READY_FOR_INPUT_ATTEMPT' and pre['seconds'] < 90 and pre['normal_exit_code']==0 and pre['cleanup']['owned_group_gone'] and not pre['cleanup']['signals_sent'], 'Bounded preflight native exit')
    check(pre['profile_entries_unchanged'] and all(pre['permissions'][k] is True for k in ('CGPreflightPostEventAccess','CGPreflightScreenCaptureAccess')), 'Actual preflight permissions/profile')
    check(menu['passed'] and menu['status']=='PASS_MENU_NAVIGATION_ONLY' and menu['seconds'] < 150 and menu['ordinary_termination_requested'] and menu['normal_exit_code']==0 and menu['profile_entries_unchanged'], 'Bounded separate native menu scope')
    menu_posts = [a['event_kind'] for a in menu['actions'] if a['event']=='cg_event_post_attempt']
    check(menu_posts == ['pointer_move','lmb_down','lmb_up','escape_down','escape_up'] and menu['cg_event_post_attempts']==menu['cg_event_post_attempts_after_cleanup']==5, 'Genuine menu native event schedule')
    check([(a['control'],a['down']) for a in menu['actions'] if a['event']=='native_control_observed']==[('lmb',True),('lmb',False),('escape',True),('escape',False)], 'Native menu down/up acknowledgements')
    check([a['screen'] for a in menu['actions'] if a['event']=='screen_confirmed']==['menu','settings','menu'], 'Native menu response order')
    for row in menu['cleanup']:
        check(row['owned_group_gone'] and not row['signals_sent'] and row['exit_code']==0, 'Menu ordinary group removal')
    for data in (menu, ordinary):
        check(data['preflight_sha256'] == sha(qa/'macos-input-preflight/results.json'), 'Same preflight bytes')
    check(ordinary['capture_helper']['source_sha256'] == identity['all_input_sha256']['scripts/macos_window_capture.swift'], 'Actual capture helper source')
    check(ordinary['engine'] == menu['engine'] == pre['engine'] == '4.7.2.stable.official.ed1daf0bf', 'Pinned engine version')
    check(ordinary['budgets_seconds'] == {'total':300,'compile':60,'window':30,'focus':5,'menu':60,'deploy':30,'live':60,'fire':5,'reload_start':5,'reload_complete':15,'reload_frames':5,'field_menu':10,'return_menu':30,'close':20,'capture':25}, 'Unchanged original budgets')
    command = ordinary['client_command']
    check(command[1:12] == ['--audio-driver','Dummy','--log-file','user://mac-ordinary-engine.log','--windowed','--resolution','1280x720','--position','40,60','--','--offline-validation'] and len(command)==13 and command[-1].startswith('--offline-trace-dir='), 'Unchanged native launch arguments')
    actions = ordinary['actions']
    check(qread('macos-ordinary-input/actions.json') == actions, 'Original action files agree')
    check(all(a['seconds'] <= b['seconds'] for a,b in zip(actions, actions[1:])), 'Monotonic original actions')
    pins = [a for a in actions if a['event']=='input_geometry_pinned']
    focuses = [a for a in actions if a['event']=='focus_before_request']
    focused = [a for a in actions if a['event']=='focus_observed']
    check(len(pins)==len(focuses)==len(focused)==1 and focused[0]['seconds']-focuses[0]['seconds'] < 5 and focused[0]['native_state']['foreground_pid']==ordinary['client_pid'], 'One bounded actual focus and pin')
    begin = next(a for a in actions if a['event']=='stage_begin' and a['label']=='Exact owned visible native window')
    found = next(a for a in actions if a['event']=='stage_complete' and a['label']==begin['label'])
    check(found['seconds']-begin['seconds'] < 30 and pins[0]['seconds']-found['seconds'] < 60, 'Original actual window/menu deadlines')
    for action in actions:
        if action['event']=='owned_window_guard' and action['seconds'] >= pins[0]['seconds']:
            rows=[r for r in action['observed_owned_layer_zero_windows'] if r['owner_pid']==ordinary['client_pid'] and r['onscreen'] is True]
            check(len(rows)==1 and rows[0]['window_id']==ordinary['selected_client_window']['window_id'] and rows[0]['bounds_points_including_chrome']==pins[0]['bounds_points_including_chrome'], 'Unique current owned pinned window')
    helpers=[a for a in actions if a['event']=='helper_command']
    check(helpers[0]['budget_seconds']==60 and all(a['budget_seconds']<=25 for a in helpers[1:]), 'Original helper budgets')
    check([a['name'] for a in helpers if '--analysis-mode' in a['command']]==['01-focused-menu'], 'Only one focused analysis invocation')
    captures = []
    for scope, data in (('macos-menu-input', menu), ('macos-ordinary-input', ordinary)):
        for row in data['captures']:
            base = qa/scope/row['name']
            cap = read(base.with_suffix('.json'))
            check(dimensions(base.with_suffix('.png')) == cap['image_dimensions'], 'Actual native PNG dimensions')
            check(sha(base.with_suffix('.png')) == row['png_sha256'] and sha(base.with_suffix('.json')) == row['receipt_sha256'], 'Original capture hashes')
            check(cap['owner_pid'] == data['client_pid'] and cap['window_id'] == data['selected_client_window']['window_id'], 'Capture exact owned window')
            check(cap['input_events_posted'] == cap['permission_requests_made'] == 0, 'Read-only capture')
            captures.append({'scope':scope, 'name':row['name'], 'dimensions':cap['image_dimensions'], 'owner_pid':cap['owner_pid'], 'window_id':cap['window_id']})
    for row in ordinary['capture_attempts']:
        check(row['finished_seconds']-row['started_seconds'] < 25, 'Actual capture duration within original cap')
        for name, descriptor in row['retained_files'].items():
            path = qa/'macos-ordinary-input'/name
            check(path.stat().st_size == descriptor['bytes'] and sha(path) == descriptor['sha256'], 'All capture-attempt evidence retained')

    # Replay only the pure source selector on actual original remote OCR rows.
    # This neither performs OCR nor edits any retained receipt.
    focus = qa/'macos-ordinary-input/01-focused-menu.json'
    derived = {'present': focus.exists()}
    if focus.exists():
        cap = read(focus)
        original = qa/'macos-ordinary-input/01-focused-menu.png'
        scaled = qa/'macos-ordinary-input/01-focused-menu-deploy-2x.png'
        analysis = cap.get('derived_deploy_analysis')
        derived.update(raw_rows=[r for r in cap['text'] if 'DEPLOY' in r['text']], analysis=analysis)
        if analysis is not None:
            bind_analysis(cap, sha(original), sha(scaled), dimensions(original), dimensions(scaled))
            derived['provenance_binding_passed'] = True
            raw=[r for r in cap['text'] if canonical_caption(r['text'])==LABEL]
            transformed=[r for r in analysis['text'] if canonical_caption(r['text'])==LABEL]
            check(len(raw)==len(transformed)==1, 'Actual unique full raw/derived captions')
            def center(box): return [box[0]+box[2]/2,box[1]+box[3]/2]
            def contains(box,point): return box[0]<=point[0]<=box[0]+box[2] and box[1]<=point[1]<=box[1]+box[3]
            rb,db=raw[0]['box_normalized_bottom_left'],transformed[0]['box_normalized_bottom_left']
            check(contains(rb,center(db)) and contains(db,center(rb)), 'Actual reciprocal corresponding boxes')
            derived['reciprocal_boxes_passed']=True
            try:
                native = derived_deploy_row(cap)
                x,y,w,h = native['box_normalized_bottom_left']
                bx,by,bw,bh = cap['bounds_points_including_chrome']
                point = [bx+(x+w/2)*bw, by+(1-y-h/2)*bh]
                derived.update(selector_accepted=True, original_native_row=native, original_target_points=point)
                targets = [a for a in actions if a['event']=='derived_deploy_target']
                check(len(targets)==1 and targets[0]['original_native_row']==native and targets[0]['target_points']==point, 'Actual target uses original native center')
            except RuntimeError as error:
                derived.update(selector_accepted=False, selector_rejection=str(error))
                check(not any(a['event']=='derived_deploy_target' for a in actions), 'Rejected target posts no accepted derived target')
    check(not any('derived_deploy_analysis' in read(p) for p in (qa/'macos-ordinary-input').glob('*.json') if p.name not in ('01-focused-menu.json','results.json','actions.json')), 'Derived analysis only focused Deploy capture')
    posts = [a for a in actions if a['event']=='cg_event_post_attempt']
    check(len(posts) == ordinary['cg_event_post_attempts'], 'Actual CGEvent count')
    check(ordinary['seconds'] < 300 and not ordinary.get('finalization_failures'), 'Bounded ordinary finalization')
    check(not any(k in ordinary for k in ('initial_event','native_fire','native_reload','native_field_menu','living_hud_captures')) and not (qa/'macos-ordinary-input/stock-offline-trace').exists(), 'All gameplay phases remain unreached')
    check(ordinary['failure_ordinary_close']=={'needed':True,'request_accepted':True,'exit_code':0}, 'Actual failure-path close')
    for row in ordinary['cleanup']:
        check(row['owned_group_gone'] and not row['signals_sent'] and row['exit_code']==0, 'Ordinary groups exit without fallback signals')
    for data in (menu, ordinary):
        release = data['final_input_release']
        check(not release['held_after_release'] and not release['errors'] and not any(release['native_state'].get(k,False) for k in ('lmb_down','escape_down','reload_down')), 'Actual final controls neutral')

    staged = ordinary['native_artifact_attestation']
    payload = {r['path'].removeprefix('macos/SIGHTBREAK.app/'):{k:r[k] for k in ('bytes','sha256','mode')} for r in manifest['payload'] if r['path'].startswith('macos/SIGHTBREAK.app/')}
    check(staged['original_inventory']['files'] == payload, 'Complete original payload descriptors')
    check(staged['staged_inventory']['directories'] == staged['original_inventory']['directories'], 'Same staged directories')
    copied = staged['staged_inventory']['files']
    check(set(copied) == set(payload)|{'Contents/MacOS/override.cfg'} and all(copied[n] == d for n,d in payload.items()), 'Only sibling override added')
    name = Path(ordinary['private_user_directory']).name
    override = '[application]\nconfig/use_custom_user_dir=true\nconfig/custom_user_dir_name="'+name+'"\n'
    check(re.fullmatch(r'SIGHTBREAK-mac-ordinary-[0-9a-f]{32}',name) is not None and staged['override_text']==override, 'Exact isolated userdata override')
    check(hashlib.sha256(override.encode()).hexdigest() == staged['override_sha256'] == copied['Contents/MacOS/override.cfg']['sha256'], 'Exact override hash')
    check(staged['executable_sha256'] == manifest['artifact']['sha256'] and staged['pck_sha256'] == payload['Contents/Resources/SIGHTBREAK.pck']['sha256'], 'Staged executable and PCK identity')
    check(ordinary['payload_unchanged'] and ordinary['default_user_directory_unchanged'] and ordinary['default_user_directory_before']==ordinary['default_user_directory_after'], 'Payload/default userdata preserved')
    check(ordinary['account_home'] == ordinary['environment_whitelist']['HOME'] == '/Users/runner' and ordinary['private_user_directory'].startswith('/Users/runner/Library/Application Support/'), 'Actual OS account home/private directory')
    check(all(ordinary['environment_whitelist'][key] is None for key in ('GODOT_RENDERING_DRIVER','GODOT_RENDERING_METHOD','DYLD_INSERT_LIBRARIES','GODOT_PROJECT_DATA_DIR')), 'No selected renderer/injection overrides')
    check('mac-ordinary-engine.log' in ordinary['private_user_directory_before_input']['files'], 'Native-created private engine log before input')
    check(sha(qa/'macos-ordinary-input/engine.log') == ordinary['private_user_directory_after']['files']['mac-ordinary-engine.log']['sha256'], 'Exact retained private engine log')
    check(not any(n.startswith('offline_training.json') for n in ordinary['private_user_directory_after']['files']), 'No fabricated private progression profile')

    suites, counts = qread('regressions/results.json'), {}
    check([r['suite'] for r in suites]==['actor','match','authority_order','state_privacy','movement_prediction','peer_lifecycle','input_mode','menu_focus','offline_diagnostics','hud_objective_hint','activity_provenance','bot_squad_symmetry','bot_dry_weapon','transaction_journal','gunplay_rules'], 'All 15 exact original native suites')
    for row in suites:
        text = (qa/'regressions'/Path(row['log']).name).read_text()
        check(row['clean_log'] is (not failed(text)), 'Actual suite strict scan')
        check(row['exit']==0 and row['clean_log'] and row['wall_seconds'] < 120, 'Suite native exit/strict/original cap')
        matches = re.findall(r'checks["\s]*[=:]\s*([0-9]+)',text)
        match = re.search(r'(\d+)/(\d+) passed|(\d+) checks, 0 failures',text)
        counts[row['suite']] = int(matches[-1]) if matches else int(next(v for v in match.groups() if v is not None))
        for field in ('before','after'):
            receipt = row[field]
            producer = qread('regressions/'+Path(receipt['producer_receipt']).name)
            check(all(producer[k]==receipt[k] for k in producer), 'Original native producer receipt')
            check(producer['uses_custom_user_dir'] and producer['custom_user_dir'].endswith('/'+row['suite']), 'Private suite native identity')
            check(receipt['run']['exit']==0 and receipt['run']['clean_log'] and receipt['run']['wall_seconds'] < 30, 'Actual producer original cap/strict exit')
    isolation = qread('regressions/isolation.json')
    check(isolation['source_resources_sha256']==identity['game_resources_sha256'] and isolation['source_resources_unchanged'] and isolation['copied_resources_unchanged'], 'Suite source and copied resources preserved')
    check(isolation['temporary_project_removed'] and not isolation['finalization_failures'] and all(r['removed'] for r in isolation['cleanup']), 'Suite namespaces/temp project cleanup')
    check(isolation['passed'] is True and sum(counts.values())==9434, 'Current complete strict suite scope')
    diagnostics=qread('macos-diagnostics/results.json')
    source(diagnostics['source'])
    check(diagnostics['all_default_graphical_passed'] and diagnostics['exact_source_unchanged'] and len(diagnostics['trials'])==5, 'Separate five default-renderer startup controls')
    for trial in diagnostics['trials']:
        check(trial['passed'] and trial['native_exit_code']==0 and trial['clean_log'] and not trial['timed_out'] and not trial['surviving_owned_group'], 'Default startup bounded group/strict exit')
        check(trial['capture']['sha256']==sha(qa/'macos-diagnostics'/(trial['label']+'.png')), 'Original diagnostic pixels')
    logs = list(qa.rglob('*.log'))
    bad_logs = [str(p.relative_to(qa)) for p in logs if failed(p.read_text(errors='replace'))]
    ios = qread('ios-compile/compile.json')
    source(ios['source'])
    ios_export = qread('ios-compile/exported-source.json')
    source(ios_export)
    check(ios['compile_completed'] and ios['status']=='PASS' and ios['seconds'] < 900 and len(ios['commands'])==15, 'Separate actual unsigned compile scope')
    check('** BUILD SUCCEEDED **' in (qa/'ios-compile/xcodebuild-device.log').read_text(), 'Original device build succeeds')
    for row in ios['commands']:
        check(row['exit_code']==(1 if row['label']=='unsigned-app' else 0) and not row['timed_out'] and row['seconds'] < row['timeout_seconds'], 'Actual iOS command exit/original bound')
        check(row['cleanup_complete'] and not row['unexpected_descendants'] and not row['surviving_owned_processes'] and not row['cleanup_errors'], 'iOS recorded command-group cleanup only')
    check(ios['app']['executable']['architecture']=='arm64' and ios['app']['executable']['platform']=='iOS device' and ios['app']['executable']['code_signature_load_command'] is False and not ios['app']['signature_directory'] and not ios['app']['embedded_profile'] and ios['app']['pck_resources']==134, 'Recorded unsigned arm64/PCK descriptors')
    check(qread('ios-compile/source-before.log')==qread('ios-compile/source-after.log'), 'iOS source unchanged')
    check(next(r['sha256'] for r in ios_export['payload'] if r['path']=='ios/sightbreak.pck')==ios['app']['pck_sha256'], 'iOS app/PCK descriptor binding')
    orphans = re.findall(r'Terminate orphan process: pid \((\d+)\) \(([^)]+)\)',log)
    images=read(REPORT/'images.json')
    pngs=[r for r in files if r['path'].endswith('.png')]
    check(images['count']==len(pngs)==19 and images['unique_sha256']==len({r['sha256'] for r in pngs})==15, 'All original image coverage')
    check({r['path']:r['sha256'] for r in images['images']}=={r['path']:r['sha256'] for r in pngs}, 'Visual coverage binds original hashes')
    for row in read(REPORT/'witnesses.json'):
        original,witness=qa/row['original'],REPORT/row['witness']
        check(original.read_bytes()==witness.read_bytes() and sha(witness)==row['sha256'] and witness.stat().st_size==row['bytes'], 'Exact unmodified native witness copy')
    output = {'scope':'Read-only remote-original integrity audit; no new native/OCR/Swift work or binary reparse', 'evidence_integrity_audit_passed':True, 'assertions':assertions,
              'run_id':run['id'], 'job_id':job['id'], 'workflow_conclusion':run['conclusion'], 'source_commit':identity['source_commit'],
              'receipt_index_files':len(index['files']), 'identical_qa_overlaps':overlaps, 'qa_files':len(files),
              'failed_steps':[r['name'] for r in job['steps'] if r['conclusion']=='failure'], 'captures':captures,
              'derived_deploy':derived, 'ordinary_component_passed':ordinary['passed'], 'ordinary_failure':ordinary.get('failure'),
              'ordinary_seconds':ordinary['seconds'], 'ordinary_event_posts':len(posts), 'ordinary_cleanup':ordinary['cleanup'],
              'ordinary_failure_close':ordinary.get('failure_ordinary_close'), 'ordinary_normal_exit':ordinary.get('normal_exit_code'),
              'native_suites_observed':len(suites), 'native_assertions':counts, 'native_reported_assertions_total':sum(counts.values()),
              'strict_logs_scanned':len(logs), 'strict_failing_logs':bad_logs, 'runner_reaped_orphans':orphans,
              'preflight_seconds':pre['seconds'], 'menu_seconds':menu['seconds'], 'ios_compile_seconds':ios['seconds'],
              'ios_xcodebuild_seconds':next(r['seconds'] for r in ios['commands'] if r['label']=='xcodebuild-device')}
    (REPORT/'audit.json').write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps({k:v for k,v in output.items() if k not in ('derived_deploy','ordinary_cleanup','captures')},indent=2))


if __name__ == '__main__':
    main()
