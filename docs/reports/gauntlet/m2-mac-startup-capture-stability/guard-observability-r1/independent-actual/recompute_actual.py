#!/usr/bin/env python3
"""Pure audit of the original admitted guard diagnostic; no native API construction."""
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import zipfile

ROOT = Path(subprocess.check_output(['git', 'rev-parse', '--show-toplevel'], text=True).strip())
REPORT = Path(__file__).resolve().parent
BASE = REPORT / 'native-39946498627'
SOURCE = 'd5277180a7705befd64d2f40a362ad566e83d91b'
assert os.sched_getaffinity(0) == {4}
sys.path.insert(0, str(ROOT / 'scripts'))
from macos_ax_contract import (CAPS, NODE_KEYS, PRUNED_ROLES, READ_APIS,
    inside, normalized_title, require_capture, validate_collection,
    validate_observation, validate_request)
from macos_deploy_ocr import png_dimensions
from macos_ordinary_input import capture_geometry, same_bounds
from native_log import failed
from verify_macos_menu import require_screen, unique_screen_label
from verify_macos_ordinary import BUDGETS


def read(name):
    return json.loads((BASE / name).read_text())


def sha(data):
    return hashlib.sha256(data).hexdigest()


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


run, jobs, artifacts = read('run-metadata.json'), read('jobs-metadata.json'), read('artifacts-metadata.json')
result, manifest = read('qa/ax-read-only/results.json'), read('qa/macos/source.json')
actions = read('qa/ax-read-only/actions.json')
ax, focused = read('qa/ax-read-only/ax-observation.json'), read('qa/ax-read-only/01-focused-menu.json')
log = (BASE / 'job-120390346371-original.log').read_text()
assert run['id'] == 39946498627 and run['run_attempt'] == 1
assert run['head_sha'] == SOURCE and run['event'] == 'workflow_dispatch'
assert run['head_branch'] == 'qualifier/m2-mac-guard-r1-d5277180'
assert run['status'] == 'completed' and run['conclusion'] == 'success'
assert run['head_commit']['tree_id'] == git('rev-parse', SOURCE + '^{tree}').decode().strip()
diagnostic = next(j for j in jobs['jobs'] if j['id'] == 120390346371)
normal = next(j for j in jobs['jobs'] if j['name'] == 'native')
assert len(jobs['jobs']) == 2 and diagnostic['name'] == 'macos_ax_read_only'
assert diagnostic['head_sha'] == SOURCE and diagnostic['labels'] == ['macos-15']
assert diagnostic['conclusion'] == 'success' and normal['conclusion'] == 'skipped'
assert result['source']['source_commit'] == SOURCE
assert result['source']['source_game_tree'] == git('rev-parse', SOURCE + ':game').decode().strip()
assert not result['source']['source_dirty'] and not result['source']['source_game_dirty']
assert manifest == result['artifact_source']
assert all(result['source'][k] == manifest[k] for k in result['source'])
assert result['source_unchanged'] and result['payload_unchanged']
assert result['budgets_seconds'] == BUDGETS and result['ax_caps'] == CAPS
source_hashes = {}
for name, expected in result['bound_source_sha256'].items():
    assert sha(git('show', SOURCE + ':scripts/' + name)) == sha((ROOT / 'scripts' / name).read_bytes()) == expected
    source_hashes[name] = expected

validation = hashlib.sha256()
validation_files = validation_bytes = 0
for directory in ('scripts', '.github', 'game/tests'):
    rows = git('ls-tree', '-r', '--format=%(objectname)\t%(path)', SOURCE, directory).decode().splitlines()
    entries = []
    for row in rows:
        blob, name = row.split('\t', 1)
        if any(p in ('__pycache__', '.godot') for p in Path(name).parts) or name.endswith('.pyc'):
            continue
        entries.append((name, blob))
    entries.sort()
    batch = subprocess.run(['git', 'cat-file', '--batch'], cwd=ROOT,
        input=('\n'.join(blob for _, blob in entries) + '\n').encode(), capture_output=True, check=True)
    stream = io.BytesIO(batch.stdout)
    for name, blob in entries:
        header = stream.readline().decode().split()
        assert header[0] == blob and header[1] == 'blob'
        data = stream.read(int(header[2])); assert stream.read(1) == b'\n'
        validation.update(name.encode() + b'\0' + data + b'\0')
        validation_files += 1; validation_bytes += len(data)
    assert not stream.read()
assert validation.hexdigest() == result['source']['source_validation_sha256']

attestation = result['native_artifact_attestation']
original, staged = attestation['original_inventory']['files'], attestation['staged_inventory']['files']
app_manifest = {e['path'].removeprefix('macos/SIGHTBREAK.app/'): e for e in manifest['payload']
                if e['path'].startswith('macos/SIGHTBREAK.app/')}
assert set(original) == set(app_manifest)
for name, entry in original.items():
    assert all(entry[k] == app_manifest[name][k] for k in ('bytes', 'sha256', 'mode'))
    assert entry == staged[name]
assert set(staged) - set(original) == {'Contents/MacOS/override.cfg'}
assert sha(attestation['override_text'].encode()) == attestation['override_sha256']
assert staged['Contents/MacOS/override.cfg']['sha256'] == attestation['override_sha256']
assert staged['Contents/MacOS/override.cfg']['bytes'] == len(attestation['override_text'].encode())
assert attestation['executable_sha256'] == manifest['artifact']['sha256']
assert attestation['pck_sha256'] == original['Contents/Resources/SIGHTBREAK.pck']['sha256']
assert result['capture_helper']['source_sha256'] == source_hashes['macos_window_capture.swift']
assert result['engine'] == '4.7.2.stable.official.ed1daf0bf'
assert result['passed'] is True and result['status'] == 'PASS_READ_ONLY_AX_EXPOSURE_ONLY'
assert not result.get('failure') and not result.get('blocker') and not result.get('finalization_failures')
assert actions == result['actions']
assert len(result['capture_attempts']) == 7 and len(result['captures']) == 2
capture_rows, image_hashes = [], {}
for index, attempt in enumerate(result['capture_attempts']):
    name = attempt['name']; capture = read('qa/ax-read-only/' + name + '.json')
    assert capture['passed'] is True and capture['owner_pid'] == result['client_pid'] == 3666
    assert capture['window_id'] == 24 and capture['post_capture_validation_stage'] == 'complete'
    assert capture['input_events_posted'] == capture['permission_requests_made'] == 0
    assert capture['point_pixel_scale'] == 1
    expected = [math.ceil(v * capture['point_pixel_scale']) for v in capture['filter_content_rect_points'][2:]]
    assert expected == capture['configured_image_dimensions'] == capture['image_dimensions']
    assert same_bounds(capture['bounds_points_including_chrome'], capture['post_capture_owned_window_bounds_points'])
    capture_geometry(capture)
    assert 'derived_deploy_analysis' not in capture
    png = BASE / 'qa/ax-read-only' / (name + '.png')
    assert png_dimensions(png) == expected
    rawlog = (BASE / 'qa/ax-read-only' / (name + '.log')).read_text()
    assert json.loads(rawlog[rawlog.index('{'):]) == capture
    assert rawlog[:rawlog.index('{')] == 'IOServiceMatchingfailed for: AppleM2ScalerParavirtDriver\n'
    for file, record in attempt['retained_files'].items():
        raw = (BASE / 'qa/ax-read-only' / file).read_bytes()
        assert len(raw) == record['bytes'] and sha(raw) == record['sha256']
    assert attempt['accepted'] is (index >= 5)
    if index < 5:
        assert attempt['failure'] == {'type': 'StartupMenuNotReady', 'message': 'Original OS screenshot did not confirm menu screen'}
        try:
            require_screen(capture, 'menu')
        except RuntimeError:
            pass
        else:
            raise AssertionError('Original splash receipt passed menu anchors')
    else:
        require_capture(capture, result['client_pid'], 24, result['pinned_window']['bounds_points'])
    duration = attempt['finished_monotonic'] - attempt['started_monotonic']
    assert 0 < duration < BUDGETS['capture']
    capture_rows.append({'name': name, 'accepted_menu': attempt['accepted'], 'helper_passed': True,
        'stage': capture['post_capture_validation_stage'], 'initial_bounds': capture['bounds_points_including_chrome'],
        'post_bounds': capture['post_capture_owned_window_bounds_points'], 'dimensions': expected,
        'capture_attempt_seconds': duration, 'png_sha256': sha(png.read_bytes())})
    image_hashes.setdefault(sha(png.read_bytes()), []).append(name + '.png')
for row in result['captures']:
    assert sha((BASE / 'qa/ax-read-only' / (row['name'] + '.png')).read_bytes()) == row['png_sha256']
    assert sha((BASE / 'qa/ax-read-only' / (row['name'] + '.json')).read_bytes()) == row['receipt_sha256']

binding_row = result['ax_observation']; pinned = result['pinned_window']
binding = dict(pid=result['client_pid'], window=pinned['window_id'], bounds=pinned['bounds_points'],
    nonce=binding_row['nonce'], observer_pid=binding_row['observer_pid'],
    started=binding_row['started_monotonic'], finished=binding_row['finished_monotonic'], budget=binding_row['budget_seconds'])
assert sha((BASE / 'qa/ax-read-only/ax-observation.json').read_bytes()) == binding_row['sha256']
assert (BASE / 'qa/ax-read-only/ax-observation.json').read_bytes() == (BASE / 'qa/ax-read-only/ax-observer.log').read_bytes()
validate_request(ax, **binding)
latest = validate_collection(ax, **binding)
exposure = validate_observation(ax, focused, **binding)
assert exposure == result['semantic_exposure']
assert len(ax['snapshots']) == 1 and len(latest['nodes']) == ax['examined_nodes'] == 36
assert len((BASE / 'qa/ax-read-only/ax-observation.json').read_bytes()) == 6875 < CAPS['receipt_bytes']
assert set(ax['api_call_counts']) <= set(READ_APIS)
assert all(set(n) <= NODE_KEYS for n in latest['nodes'])
assert all(not (set(n) & {'title', 'normalized_title'}) for n in latest['nodes'] if n['role'] not in ('AXButton', 'AXWindow'))
assert not any(n['role'] in PRUNED_ROLES for n in latest['nodes'])
assert max(n['depth'] for n in latest['nodes']) == 4
empty = [n['node'] for n in latest['nodes'] if n['role'] == 'AXButton' and n['title'] == '']
assert empty == [2, 3, 4]
assert exposure['button']['node'] == 18 and inside(exposure['original_text_frame_points'], exposure['button']['frame_points'], .5)
assert normalized_title(exposure['button']['title']) == 'DEPLOY · OFFLINE 5V5'
assert exposure['original_native_row']['confidence'] == .5
assert unique_screen_label(focused, 'DEPLOY · OFFLINE 5V5') is False
assert result['query_prerequisites'] and result['bounded_traversal_complete'] and result['unique_semantic_candidate'] and result['native_pixel_frame_agreement']
assert not result['gameplay_target_accepted'] and not result['ocr_confidence_threshold_changed']
assert result['original_native_ocr_unchanged'] is True
assert result['cg_event_post_attempts'] == result['permission_requests_made'] == 0 and result['focus_requests'] == 1
assert ax['input_events_posted'] == ax['permission_requests_made'] == 0
assert result['permissions']['CGPreflightScreenCaptureAccess'] is True and result['permissions']['AXIsProcessTrusted'] is True
assert result['ordinary_termination_requested'] is True and result['normal_exit_code'] == 0
assert len(result['cleanup']) == 10 and all(r['owned_group_gone'] and r['exit_code'] == 0 and not r['signals_sent'] for r in result['cleanup'])
assert result['default_user_directory_before'] == result['default_user_directory_after']
assert result['default_user_directory_unchanged'] and result['private_menu_profile_files_present'] == []
assert all(n == 'mac-ordinary-engine.log' or n.startswith('shader_cache/') for n in result['private_user_directory_after']['files'])
assert result['private_user_directory_after']['files']['mac-ordinary-engine.log']['sha256'] == sha((BASE / 'qa/ax-read-only/engine.log').read_bytes())
assert not any('stock-offline-trace' in p.relative_to(BASE / 'qa').parts for p in (BASE / 'qa').rglob('*'))
assert result['client_command'][10:13] == ['--accessibility', 'always', '--']
strict_logs = {str(p.relative_to(BASE)): not failed(p.read_text()) for p in sorted((BASE / 'qa').rglob('*.log'))}
assert len(strict_logs) == 14 and all(strict_logs.values())

plain = re.sub(r'^\ufeff?\d{4}-\d\d-\d\dT\S+Z ', '', log, flags=re.M)
region = plain[plain.index('##[group]Run python scripts/verify_macos_ax_read_only.py'):]
printed, _ = json.JSONDecoder().raw_decode(region[region.index('{\n'):])
assert printed == result
start = plain.index('##[group]Run python scripts/test_macos_ax_read_only.py -v')
end = plain.index('##[group]Run python scripts/toolchain.py setup --targets macos', start)
counts = [int(v) for v in re.findall(r'Ran (\d+) tests? in ', plain[start:end])]
assert len(counts) == 12 and sum(counts) == 118
archive_rows = []
for name, aid in [('qa', 12497749991), ('receipts', 12497879667)]:
    data = (BASE / (name + '-original.zip')).read_bytes()
    entry = next(a for a in artifacts['artifacts'] if a['id'] == aid)
    assert len(data) == entry['size_in_bytes'] < 32 * 1024 * 1024
    assert sha(data) == entry['digest'].removeprefix('sha256:') and sha(data) in log
    assert entry['workflow_run']['head_sha'] == SOURCE and entry['workflow_run']['id'] == run['id']
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        for info in z.infolist():
            assert z.read(info) == (BASE / name / info.filename).read_bytes()
    archive_rows.append({'artifact_id': aid, 'bytes': len(data), 'sha256': sha(data)})
crosscheck = []
with zipfile.ZipFile(BASE / 'receipts/qa-receipts.zip') as z:
    index_bytes = z.read('qa-receipts-index.json'); index = json.loads(index_bytes)
    assert len(index['files']) == 25 and len(z.infolist()) == 26
    for entry in index['files']:
        data = z.read(entry['archive_path']); raw = (BASE / 'qa' / entry['path']).read_bytes()
        assert data == raw and len(data) == entry['bytes'] and sha(data) == entry['sha256']
        crosscheck.append(dict(entry, full_qa_bytes_equal=True))
(BASE / 'qa-receipts-index-original.json').write_bytes(index_bytes)
assert sha((BASE / 'receipts/qa-receipts.zip').read_bytes()) in log
(BASE / 'receipt-crosscheck.json').write_text(json.dumps(crosscheck, indent=2) + '\n')
first_poll = next(a['seconds'] for a in actions if a['event'] == 'first_window_observation')
first_window = next(a['seconds'] for a in actions if a['event'] == 'first_window_observation' and a['observed_owned_layer_zero_windows'])
focus_begin = next(a['seconds'] for a in actions if a['event'] == 'focus_before_request')
focus_end = next(a['seconds'] for a in actions if a['event'] == 'focus_observed')
ax_command = next(a['seconds'] for a in actions if a['event'] == 'helper_command' and a['name'] == 'ax-observer')
timing = {'whole_seconds': result['seconds'], 'compile_upper_bound_from_whole_start': first_poll,
    'first_owned_window_from_whole_start': first_window, 'focus_trace_seconds': focus_end-focus_begin,
    'capture_attempt_seconds': [c['capture_attempt_seconds'] for c in capture_rows],
    'ax_controller_seconds': binding['finished'] - binding['started'],
    'ax_observer_seconds': ax['finished_monotonic'] - ax['started_monotonic'],
    'menu_and_remaining_upper_bound': result['seconds'] - first_window,
    'close_and_finalization_upper_bound_including_ax': result['seconds'] - ax_command}
assert result['seconds'] < 300 and first_poll < 60 and first_window < 30
assert 0 < focus_end-focus_begin < 5 and timing['menu_and_remaining_upper_bound'] < 60
assert timing['close_and_finalization_upper_bound_including_ax'] < 20
old = git('show', '617b348b:docs/reports/gauntlet/m2-mac-ax-read-only/r3/independent-actual/native-39943145541/qa/ax-read-only/00-startup-menu-1.json')
assert len(old) == 859 and sha(old) == 'd63129b91900c6ad5d2a99767e6d4c35dacc8ec254e54be28981a1613adb1ecf'
summary = {'exact_source': SOURCE, 'actual_run_id': run['id'], 'diagnostic_job_id': diagnostic['id'],
    'verdict': 'VERIFIED_READ_ONLY_ARM_GUARD_EMISSION_AND_AX_EXPOSURE_ONLY', 'cpu_affinity': sorted(os.sched_getaffinity(0)),
    'bound_source_sha256': source_hashes, 'validation_sha256': validation.hexdigest(),
    'validation_files': validation_files, 'validation_bytes': validation_bytes,
    'content_digest_scope': 'Native attestation plus exact Git game-tree binding; full asset bytes not rehashed.',
    'remote_source_commands': len(counts), 'remote_source_methods': sum(counts),
    'captures': capture_rows, 'original_image_hash_groups': image_hashes,
    'controller_stdout_equals_result': True, 'strict_logs': strict_logs, 'timing': timing,
    'ax_snapshots': len(ax['snapshots']), 'ax_nodes': ax['examined_nodes'], 'empty_title_nodes': empty,
    'api_call_counts': ax['api_call_counts'], 'semantic_exposure': exposure,
    'ordinary_ocr_threshold': .8, 'ordinary_deploy_ocr_rejected': True,
    'archives': archive_rows, 'raw_receipts_equal_across_artifacts': len(crosscheck),
    'recorded_groups': result['cleanup'], 'default_inventory_equal': True,
    'private_files_after_window': len(result['private_menu_inventory_after_window']['files']),
    'private_files_final': len(result['private_user_directory_after']['files']),
    'prior_failure': {'run_id': 39943145541, 'receipt_sha256': sha(old), 'status': 'FAILED',
        'limit': 'Old second owned frame and cause absent; this new run cannot supply them.'},
    'limits': ['No complete descendant telemetry; ten recorded groups gone and runner lists no orphan.',
        'No per-call native durations, C error/NULL boundary samples, CF retain/release instrumentation or OS-wide action trace.',
        'Successful native compile/behavior does not qualify all ABI/string edge cases.',
        'Executable, PCK, compiled helper and interpreter not transferred or reparsed.',
        'No within-capture guard mismatch occurred; failure-stage native emission remains unexercised.',
        'No causal startup fix, ordinary gameplay, Intel/iOS, physical/human or whole release-gate acceptance.']}
(BASE / 'independent-recomputation.json').write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps(summary, indent=2))
