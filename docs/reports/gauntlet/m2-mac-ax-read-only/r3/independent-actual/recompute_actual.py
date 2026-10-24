#!/usr/bin/env python3
"""Pure review of original R3 artifact bytes; never construct native APIs."""
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
BASE = REPORT / 'native-39943145541'
SOURCE = '4854aed946d25d27482af66c332f84aa51cea8fb'
assert os.sched_getaffinity(0) == {4}
sys.path.insert(0, str(ROOT / 'scripts'))
from macos_ax_contract import CAPS
from native_log import failed
from verify_macos_ordinary import BUDGETS


def read(name):
    return json.loads((BASE / name).read_text())


def sha(data):
    return hashlib.sha256(data).hexdigest()


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


run, jobs, artifacts = read('run-metadata.json'), read('jobs-metadata.json'), read('artifacts-metadata.json')
result = read('qa/ax-read-only/results.json')
capture = read('qa/ax-read-only/00-startup-menu-1.json')
manifest = read('qa/macos/source.json')
actions = read('qa/ax-read-only/actions.json')
log = (BASE / 'job-120379229239-original.log').read_text()
assert run['id'] == 39943145541 and run['run_attempt'] == 1
assert run['head_sha'] == SOURCE and run['event'] == 'workflow_dispatch'
assert run['head_branch'] == 'qualifier/m2-mac-ax-r3-read-only-4854aed9'
assert run['status'] == 'completed' and run['conclusion'] == 'failure'
assert run['head_commit']['tree_id'] == git('rev-parse', SOURCE + '^{tree}').decode().strip()
diagnostic = next(job for job in jobs['jobs'] if job['id'] == 120379229239)
normal = next(job for job in jobs['jobs'] if job['name'] == 'native')
assert len(jobs['jobs']) == 2 and diagnostic['name'] == 'macos_ax_read_only'
assert diagnostic['head_sha'] == SOURCE and diagnostic['labels'] == ['macos-15']
assert normal['conclusion'] == 'skipped' and diagnostic['conclusion'] == 'failure'
assert result['source']['source_commit'] == SOURCE
assert result['source']['source_game_tree'] == git('rev-parse', SOURCE + ':game').decode().strip()
assert not result['source']['source_dirty'] and not result['source']['source_game_dirty']
assert manifest == result['artifact_source']
assert all(result['source'][key] == manifest[key] for key in result['source'])
assert result['source_unchanged'] and result['payload_unchanged']
assert result['budgets_seconds'] == BUDGETS and result['ax_caps'] == CAPS
source_hashes = {}
for name, expected in result['bound_source_sha256'].items():
    frozen = git('show', SOURCE + ':scripts/' + name)
    actual = (ROOT / 'scripts' / name).read_bytes()
    assert sha(frozen) == sha(actual) == expected
    source_hashes[name] = expected

# Reconstruct the validation digest from exact tracked source blobs without
# populating game/assets or running an engine. The content digest remains a
# native attestation; this review does not rehash the full game asset tree.
validation = hashlib.sha256()
validation_files, validation_bytes = 0, 0
for directory in ('scripts', '.github', 'game/tests'):
    listing = git('ls-tree', '-r', '--format=%(objectname)\t%(path)', SOURCE, directory).decode().splitlines()
    entries = []
    for line in listing:
        blob, name = line.split('\t', 1)
        path = Path(name)
        if any(part in ('__pycache__', '.godot') for part in path.parts) or path.suffix == '.pyc':
            continue
        entries.append((name, blob))
    entries.sort()
    batch = subprocess.run(['git', 'cat-file', '--batch'], cwd=ROOT,
                           input=('\n'.join(blob for _, blob in entries) + '\n').encode(),
                           capture_output=True, check=True)
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
original_files = attestation['original_inventory']['files']
staged_files = attestation['staged_inventory']['files']
app_manifest = {entry['path'].removeprefix('macos/SIGHTBREAK.app/'): entry
                for entry in manifest['payload'] if entry['path'].startswith('macos/SIGHTBREAK.app/')}
assert set(original_files) == set(app_manifest)
for name, entry in original_files.items():
    assert all(entry[key] == app_manifest[name][key] for key in ('bytes', 'sha256', 'mode'))
    assert entry == staged_files[name]
assert set(staged_files) - set(original_files) == {'Contents/MacOS/override.cfg'}
assert sha(attestation['override_text'].encode()) == attestation['override_sha256']
assert staged_files['Contents/MacOS/override.cfg']['sha256'] == attestation['override_sha256']
assert staged_files['Contents/MacOS/override.cfg']['bytes'] == len(attestation['override_text'].encode())
assert attestation['executable_sha256'] == manifest['artifact']['sha256']
assert attestation['pck_sha256'] == original_files['Contents/Resources/SIGHTBREAK.pck']['sha256']
assert result['capture_helper']['source_sha256'] == source_hashes['macos_window_capture.swift']
assert result['engine'] == '4.7.2.stable.official.ed1daf0bf'

assert result['status'] == 'FAILED' and result['passed'] is False
assert result['failure']['message'] == 'Original read-only capture helper failed'
assert capture['failure']['message'] == 'Captured pixel dimensions or owned-window bounds changed'
assert capture['passed'] is False and capture['owner_pid'] == result['client_pid'] == 3602
requested_dimensions = [math.ceil(value * capture['point_pixel_scale'])
                        for value in capture['filter_content_rect_points'][2:]]
assert requested_dimensions == capture['image_dimensions'] == [1024, 684]
assert capture['window_id'] == result['first_client_window']['window_id'] == 24
assert result['permissions']['AXIsProcessTrusted'] is True
assert result['permissions']['CGPreflightScreenCaptureAccess'] is True
assert result['cg_event_post_attempts'] == result['permission_requests_made'] == result['focus_requests'] == 0
assert capture['input_events_posted'] == capture['permission_requests_made'] == 0
assert all(result[key] is False for key in ('query_prerequisites', 'bounded_traversal_complete',
    'unique_semantic_candidate', 'native_pixel_frame_agreement', 'gameplay_target_accepted', 'ocr_confidence_threshold_changed'))
assert len(result['capture_attempts']) == 1 and result['captures'] == []
assert json.loads((BASE / 'qa/ax-read-only/00-startup-menu-1.log').read_text()) == capture
for name, record in result['capture_attempts'][0]['retained_files'].items():
    raw = (BASE / 'qa/ax-read-only' / name).read_bytes()
    assert len(raw) == record['bytes'] and sha(raw) == record['sha256']
assert 'pinned_window' not in result and 'ax_observation' not in result
assert not list((BASE / 'qa').rglob('*.png')) and not list((BASE / 'qa').rglob('ax-observation.json'))
assert actions == result['actions']
assert [a['name'] for a in actions if a['event'] == 'helper_command'] == ['compile-capture-helper', '00-startup-menu-1']
assert result['ordinary_termination_requested'] is True and result['normal_exit_code'] == 0
assert len(result['cleanup']) == 3 and not result.get('finalization_failures')
assert all(row['owned_group_gone'] and not row['signals_sent'] for row in result['cleanup'])
assert result['default_user_directory_before'] == result['default_user_directory_after']
assert result['default_user_directory_unchanged'] and result['private_menu_profile_files_present'] == []
assert all(name == 'mac-ordinary-engine.log' or name.startswith('shader_cache/')
           for name in result['private_user_directory_after']['files'])
assert result['private_user_directory_after']['files']['mac-ordinary-engine.log']['sha256'] == sha((BASE / 'qa/ax-read-only/engine.log').read_bytes())
strict_logs = {str(path.relative_to(BASE)): not failed(path.read_text()) for path in sorted((BASE / 'qa').rglob('*.log'))}
assert all(strict_logs.values())

plain = re.sub(r'^\ufeff?\d{4}-\d\d-\d\dT\S+Z ', '', log, flags=re.M)
controller_region = plain[plain.index('##[group]Run python scripts/verify_macos_ax_read_only.py'):]
printed, _ = json.JSONDecoder().raw_decode(controller_region[controller_region.index('{\n'):])
assert printed == result
start = plain.index('##[group]Run python scripts/test_macos_ax_read_only.py -v')
end = plain.index('##[group]Run python scripts/toolchain.py setup --targets macos', start)
method_counts = [int(value) for value in re.findall(r'Ran (\d+) tests? in ', plain[start:end])]
assert len(method_counts) == 12 and sum(method_counts) == 118
for entry in artifacts['artifacts']:
    assert entry['workflow_run']['head_sha'] == SOURCE and entry['workflow_run']['id'] == run['id']
    assert entry['digest'].removeprefix('sha256:') in log

crosscheck = []
with zipfile.ZipFile(BASE / 'receipts/qa-receipts.zip') as archive:
    index_bytes = archive.read('qa-receipts-index.json')
    index = json.loads(index_bytes)
    assert len(index['files']) == 11 and len(archive.infolist()) == 12
    for entry in index['files']:
        data = archive.read(entry['archive_path']); raw = (BASE / 'qa' / entry['path']).read_bytes()
        assert data == raw and len(data) == entry['bytes'] and sha(data) == entry['sha256']
        crosscheck.append(dict(entry, full_qa_bytes_equal=True))
(BASE / 'qa-receipts-index-original.json').write_bytes(index_bytes)
assert sha((BASE / 'receipts/qa-receipts.zip').read_bytes()) in log
(BASE / 'receipt-crosscheck.json').write_text(json.dumps(crosscheck, indent=2) + '\n')

first_poll = next(a['seconds'] for a in actions if a['event'] == 'first_window_observation')
first_window = next(a['seconds'] for a in actions if a['event'] == 'first_window_observation' and a['observed_owned_layer_zero_windows'])
capture_command = next(a['seconds'] for a in actions if a['event'] == 'helper_command' and a['name'] == '00-startup-menu-1')
attempt = result['capture_attempts'][0]
timing = {'whole_seconds': result['seconds'], 'compile_conservative_upper_bound_seconds': first_poll,
    'first_owned_window_from_whole_start_seconds': first_window,
    'capture_attempt_seconds': attempt['finished_monotonic'] - attempt['started_monotonic'],
    'remaining_after_first_window_upper_bound_seconds': result['seconds'] - first_window,
    'close_and_finalization_upper_bound_from_capture_command_seconds': result['seconds'] - capture_command}
assert timing['whole_seconds'] < 300 and first_poll < 60 and first_window < 30
assert timing['capture_attempt_seconds'] < 25
assert timing['remaining_after_first_window_upper_bound_seconds'] < 60
assert timing['close_and_finalization_upper_bound_from_capture_command_seconds'] < 20
summary = {'exact_source': SOURCE, 'actual_run_id': run['id'], 'diagnostic_job_id': diagnostic['id'],
    'verdict': 'FAILED_BEFORE_AX_OBSERVATION', 'cpu_affinity': sorted(os.sched_getaffinity(0)),
    'bound_source_sha256': source_hashes, 'validation_digest_independently_recomputed': validation.hexdigest(),
    'validation_files': validation_files, 'validation_bytes': validation_bytes,
    'content_digest_scope': 'Native attestation plus exact Git game-tree binding; full asset bytes not rehashed here.',
    'remote_source_control_commands': len(method_counts), 'remote_source_control_methods': sum(method_counts),
    'controller_stdout_equals_original_result': True, 'strict_logs': strict_logs, 'timing': timing,
    'original_capture_failure': capture['failure'], 'original_images': 0, 'original_ax_observations': 0,
    'geometry_inference': {'source_bound_requested_dimensions': requested_dimensions,
        'reported_image_dimensions': capture['image_dimensions'],
        'inference': 'Both dimension predicates pass; under the exact helper source the failed predicate is the post-capture owned-window bounds comparison.',
        'limit': 'The reobserved post-capture bounds and cause of the geometry change were not retained.'},
    'private_files_after_window': len(result['private_menu_inventory_after_window']['files']),
    'private_files_final': len(result['private_user_directory_after']['files']),
    'default_inventory_equal': True, 'recorded_groups': result['cleanup'],
    'descendant_limit': 'No complete parent/descendant telemetry. Three recorded groups are gone; runner orphan-cleanup line lists no process.',
    'untransferred_payloads': ['native executable', 'PCK', 'compiled capture helper', 'Python interpreter'],
    'unobserved_ax_properties': ['observer trust', 'no-value/null native handling', 'native CF lifetimes', 'individual AX call durations', 'permitted tree', 'Deploy semantics/frame'],
    'retained_files_equal_across_original_artifacts': len(crosscheck)}
(BASE / 'independent-recomputation.json').write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps(summary, indent=2))
