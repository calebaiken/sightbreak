#!/usr/bin/env python3
"""Audit immutable originals without engine execution or pixel-oracle replay."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time
import zipfile
from PIL import Image
import numpy as np

OUT = Path(__file__).resolve().parent
REPO = Path('/workspace/sightbreak-touch-contrast-recovered')
RAW = Path('/workspace/sightbreak-touch-contrast-native-recovered-r4b-r3')
COMP = REPO / 'docs/reports/gauntlet/m6-touch-contrast-recovered'
SOURCE = '108d1cdc6cf471daa7390298c234bb1c087ae865'
HANDOFF = 'b9bd7e62c70d3f5a061c4177ede6c73c21dc9d35'
load = lambda p: json.loads(Path(p).read_text())
git = lambda source, path: subprocess.check_output(['git', '-C', str(REPO), 'show', source + ':' + str(path)])
started = time.monotonic()
checks = []


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def require(test, message):
    if not test:
        raise AssertionError(message)


def audit(name, fn):
    try:
        checks.append({'name': name, 'pass': True, 'observation': fn()})
    except Exception as exc:
        checks.append({'name': name, 'pass': False, 'error': repr(exc)})


start = load(RAW / 'lane-start.json')
end = load(RAW / 'lane-end.json')
freeze = load(RAW / 'SOURCE_FREEZE-r4b-r3.json')
admission = load(RAW / 'admission-source.json')
post = load(RAW / 'post-source.json')
original = load(RAW / 'recomputed.json')


def identity():
    release = git('f312ee8c53b8a848c9db20a1b6ee9bd2f90a2386', 'docs/reports/gauntlet/m6-touch-contrast-recovered/ROOT_RELEASE_R4B_R3.md')
    require(start['root_release'].encode() == release, 'actual release exact bytes')
    require(datetime.datetime.fromisoformat(start['start_utc']) > datetime.datetime(2026, 10, 23, 9, 58, 9, tzinfo=datetime.timezone.utc), 'release commit before admission')
    require(sha(RAW / 'SOURCE_FREEZE-r4b-r3.json') == start['freeze_sha256'] == '4282c67c984b1840ca43158b16c0ecb03f4254d01e5cb300478682cc8adbe921', 'freeze identity')
    require(start['source_freeze'] == SOURCE, 'source identity')
    require(sha(start['engine']) == start['engine_sha256'] == '8d106cbe6144c2dc7e881d61d2429c1a8a76e6b22ef48bd5e48dcf934953f71e', 'engine binary')
    require(hashlib.sha512(Path(start['engine_archive']).read_bytes()).hexdigest() == start['engine_archive_sha512'], 'engine archive')
    with zipfile.ZipFile(start['engine_archive']) as archive:
        require(hashlib.sha256(archive.read('Godot_v4.7.2-stable_linux.x86_64')).hexdigest() == start['engine_sha256'], 'engine archive member')
    require((RAW / 'engine-version.log').read_text().strip() == '4.7.2.stable.official.ed1daf0bf', 'actual engine version')
    require(start['taskset'] == [0, 1, 2, 3] and start['LP_NUM_THREADS'] == start['OMP_NUM_THREADS'] == '2', 'selectors')
    require(start['cpu_max'] == '400000 100000' and start['memory_max'] == '17179869184' and start['display'] == ':131', 'admission resource selectors')
    require(start['attempt_limit'] == 1 and end['acquisition_complete'] is True and end['error'] is None, 'recorded acquisition')
    require(load(RAW / 'controller-exit.json')['exit_code'] == 0, 'controller exit')
    for name in ('controller.py', 'package_evidence.py'):
        require((RAW / name).read_bytes() == git(HANDOFF, Path('docs/reports/gauntlet/m6-touch-contrast-recovered/acquisition-r4b-r3') / name), 'frozen packet ' + name)
    return {'root_release_commit': 'f312ee8c53b8a848c9db20a1b6ee9bd2f90a2386', 'admission_utc': start['start_utc'], 'engine_archive_binary_member_exact': True, 'controller_exit': 0, 'recorded_acquisition_complete': True, 'template_pending_labels_retained_without_false_runtime_meaning': True}


def sources():
    require(len(admission['frozen_files']) == 24 and post['errors'] == [], 'frozen count/post errors')
    require(dict(post['frozen_files']) == {row['path']: row['sha256'] for row in admission['frozen_files']}, 'post frozen receipt')
    for row in admission['frozen_files']:
        data = (REPO / row['path']).read_bytes()
        require(len(data) == row['bytes'] and hashlib.sha256(data).hexdigest() == row['sha256'], row['path'])
        require(data == git(SOURCE, row['path']), 'frozen Git source')
    stages = []
    for item in admission['staged']:
        root = Path(start['fixture_root']) / item['name']
        require(sha(root / 'SOURCE.json') == item['manifest_sha256'], 'source manifest')
        receipt = load(root / 'SOURCE.json')
        hashes = dict(item['actual_path_hashes'])
        require(len(hashes) == item['checked_paths'] == 327 and item['unique_uids'] == 138 and item['preimport_cache_absent'], 'stage declarations')
        for relative, expected in hashes.items():
            require(sha(root / relative) == expected, 'current staged source/UID')
        require(len(receipt['files']) == 323, 'original game count')
        for row in receipt['files']:
            require((root / row['path']).read_bytes() == git(item['source'], row['path']), 'original game Git identity')
        uids = [(root / path).read_text().strip() for path in hashes if path.endswith('.uid')]
        require(len(uids) == len(set(uids)) == 138, 'copied UID identity')
        fences = []
        for path in RAW.glob('*-' + item['name'] + '-source.json'):
            row = load(path)
            require(row['unchanged'] and row['checked_paths'] == 327 and dict(row['actual_path_hashes']) == hashes and row['manifest_sha256'] == item['manifest_sha256'], 'source fence ' + path.name)
            fences.append(path.name)
        post_stage = next(row for row in post['staged'] if row['name'] == item['name'])
        require(dict(post_stage['actual_path_hashes']) == hashes and post_stage['checked_paths'] == 327, 'post stage')
        stages.append({'name': item['name'], 'source': item['source'], 'paths': 327, 'original_git_paths': 323, 'unique_uids': 138, 'fences': sorted(fences), 'all_original_paths_unchanged': True})
    return {'frozen_files': 24, 'stages': stages, 'post_source_errors': []}


def producers():
    expected = ['engine-version', 'import-baseline', 'import-candidate', 'backgrounds', 'controls-baseline', 'controls-candidate', 'regression-baseline-touch', 'regression-baseline-input_mode', 'regression-candidate-touch', 'regression-candidate-input_mode']
    require([row['label'] for row in end['events']] == expected, 'producer order/count')
    observed = []
    for row in end['events']:
        label = row['label']
        require(row == load(RAW / (label + '-result.json')), 'event result')
        command = load(RAW / (label + '-command.json'))
        require(all(row[key] == value for key, value in command.items()), 'command result')
        require(row['command'][:4] == ['taskset', '-c', '0,1,2,3', start['engine']], 'engine selector')
        cap = 30 if label == 'engine-version' else 600 if label.startswith('controls-') else 300
        require(row['exit_code'] == 0 and not row['engine_errors'] and row['wall_seconds'] < cap and sha(RAW / (label + '.log')) == row['log_sha256'], 'producer result/log/cap')
        env = row['environment_selectors']; private = RAW / 'private-state' / label
        require(env['DISPLAY'] == ':131' and env['LP_NUM_THREADS'] == env['OMP_NUM_THREADS'] == '2' and env['SIGHTBREAK_STATE_DIR'] == str(private), 'private selectors')
        for key, leaf in [('XDG_DATA_HOME', 'data'), ('XDG_CONFIG_HOME', 'config'), ('XDG_CACHE_HOME', 'cache')]:
            require(env[key] == str(private / leaf), 'private path ' + key)
        observed.append({'label': label, 'pid': row['pid'], 'exit': row['exit_code'], 'wall_seconds': row['wall_seconds'], 'original_cap': cap})
    analyzer = load(RAW / 'analyzer-result.json')
    require(analyzer['exit_code'] == 1 and analyzer['analyzer_sha256'] == original['analysis_sha256'] == 'c47bb2fd7a3b8eab83765fd75ee76885815fc5ae467ffac6b99859e72be05141', 'original analyzer failure/identity')
    return {'ordered_producers': observed, 'original_analyzer_exit': 1, 'whole_operation_hard_timeout': False}


def images():
    sizes = {'mobile-min': ([960, 720], .7, 32), 'mobile-max': ([960, 720], 1.5, 32), 'desktop-min': ([1280, 720], .7, 0), 'desktop-max': ([1280, 720], 1.5, 0)}
    backgrounds = ['white', 'gray', 'arena', 'smoke']
    matrix = {layout + '-' + bg + '-' + state for layout in sizes for bg in backgrounds for state in ('idle', 'held')}
    background_receipt = load(RAW / 'backgrounds/capture.json')
    require(background_receipt['mode'] == 'backgrounds' and len(background_receipt['images']) == 16, 'background matrix')
    frozen_backgrounds = load(RAW / 'background-freeze.json')['files']
    require(set(frozen_backgrounds) == {p.name for p in (RAW / 'backgrounds').iterdir() if p.is_file()}, 'background freeze paths')
    for path, digest in frozen_backgrounds.items():
        require(sha(RAW / 'backgrounds' / path) == digest, 'frozen background')
    results = []
    for expected in freeze['fixtures']:
        name = expected['name']; root = RAW / name; capture = load(root / 'capture.json')
        require(capture['source'] == expected['source_full'] and capture['source_manifest_sha256'] == expected['manifest_sha256'], 'capture source')
        require(capture['background_manifest_sha256'] == sha(RAW / 'backgrounds/capture.json') and capture['source_verified_before_after'] is True, 'capture background/fences')
        require(capture['renderer'] == background_receipt['renderer'] and capture['engine'] == background_receipt['engine'], 'native renderer identity')
        require([capture['engine'][key] for key in ('major', 'minor', 'patch')] == [4, 7, 2], 'native version')
        require(len(capture['images']) == 2816 and {str(p) for p in root.rglob('*.png')} == set(capture['images']), 'complete PNG identity set')
        records = {row['id']: row for row in capture['records']}
        require(len(capture['records']) == len(records) == 32 and set(records) == matrix, 'exact scene set')
        for scene, row in records.items():
            require(load(root / scene / 'scene.json') == row, 'scene receipt')
            layout, bg, state = row['layout'], scene.split('-')[-2], scene.split('-')[-1]
            size, scale, inset = sizes[layout]
            require(row['size'] == size and row['scale'] == scale and row['inset'] == inset and row['held'] == (state == 'held'), 'scene selectors')
            require(row['counts'] == {'grenade': 0, 'smoke': 1} and row['actions'] == (['fire', 'reload', 'interact'] if state == 'held' else []) and row['movement'] == ([.65, .45] if state == 'held' else [0, 0]), 'scene actions/counts')
            for filename, digest in row['images'].items():
                path = root / scene / filename
                require(sha(path) == digest == capture['images'][str(path)], 'image hash')
                with Image.open(path) as image:
                    require(list(image.size) == size, 'image dimensions')
            require(np.array_equal(np.asarray(Image.open(root / scene / 'normal.png')), np.asarray(Image.open(root / scene / 'original.png'))), 'original/wrapped normal equality')
        results.append({'name': name, 'scenes': 32, 'pngs': 2816, 'all_image_hashes_dimensions': True, 'normal_original_equal': 32, 'renderer': capture['renderer'], 'engine': capture['engine']})
    counts = {name: len(list((RAW / name).rglob('*.png'))) for name in ('baseline', 'candidate', 'backgrounds')}
    require(counts == post['png_counts'] == {'baseline': 2816, 'candidate': 2816, 'backgrounds': 16}, 'actual complete PNG counts')
    return {'sources': results, 'counts': counts, 'total_pngs': sum(counts.values()), 'shared_backgrounds_checked': len(frozen_backgrounds)}


def strict_logs():
    pattern = re.compile(r'orphan|unclaimed|StringName|leak|resource.*(?:in use|still)|SCRIPT ERROR|Parse Error|ERROR:|WARNING:', re.I)
    rows = []
    for path in sorted(RAW.rglob('*.log')):
        matches = [{'line': n, 'text': text} for n, text in enumerate(path.read_text(errors='replace').splitlines(), 1) if pattern.search(text)]
        rows.append({'path': str(path.relative_to(RAW)), 'sha256': sha(path), 'matches': matches})
    warnings = sum(len(row['matches']) for row in rows)
    return {'logs': rows, 'warning_error_match_count': warnings, 'strict_log_clean': warnings == 0, 'orphan_unclaimed_leak_matches': [row for row in rows if any(re.search(r'orphan|unclaimed|StringName|leak|resource.*(?:in use|still)', hit['text'], re.I) for hit in row['matches'])]}


def terminal():
    groups = {row['pid'] for row in end['owned_cleanup']}
    members, unreadable = [], []
    for root in Path('/proc').iterdir():
        if not root.name.isdigit():
            continue
        try:
            text = (root / 'stat').read_text(); fields = text[text.rfind(')') + 2:].split()
            if int(fields[2]) in groups or int(fields[3]) in groups:
                members.append({'pid': int(root.name), 'comm': (root / 'comm').read_text().strip(), 'state': fields[0], 'ppid': int(fields[1]), 'pgid': int(fields[2]), 'sid': int(fields[3]), 'start_ticks': int(fields[19])})
        except (OSError, ValueError, IndexError) as exc:
            unreadable.append({'pid': int(root.name), 'error': repr(exc)})
    return {'time_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'controller_leader_absence_receipts': end['owned_cleanup'], 'current_group_members': members, 'unreadable_proc_records': unreadable, 'display_socket_absent': not Path('/tmp/.X11-unix/X131').exists(), 'display_lock_absent': not Path('/tmp/.X131-lock').exists(), 'complete_group_cleanup_pass': not members and not unreadable, 'live_observer_terminal_descendant_retained_separately': True}


for name, fn in [('identity_release_engine_packet', identity), ('source_uid_all_fences', sources), ('original_producers', producers), ('complete_matrix_images_backgrounds', images), ('strict_recursive_logs', strict_logs), ('current_terminal_group_scan', terminal)]:
    audit(name, fn)
result = {'scope': 'INDEPENDENT_ORIGINAL_METADATA_HASH_LOG_AUDIT_NO_ENGINE_NO_PIXEL_ORACLE_REPLAY', 'source': SOURCE, 'handoff': HANDOFF, 'time_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'checks': checks, 'metadata_checks_pass': all(row['pass'] for row in checks), 'wall_seconds': time.monotonic() - started, 'numeric_quality_acceptance': False, 'archive_audit': 'PENDING_PACKAGE_COMPLETION_AND_ROOT_LANE_CLEARANCE'}
(OUT / 'actual-metadata-checks.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result))
raise SystemExit(not result['metadata_checks_pass'])
