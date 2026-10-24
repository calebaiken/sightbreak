#!/usr/bin/env python3
"""Audit preserved failed attempt; never launch engine or modify original evidence."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tarfile
import time
import zipfile

START = time.monotonic()
OUT = Path(__file__).resolve().parent
REPO = Path('/workspace/sightbreak-touch-contrast-recovered')
RAW = Path('/workspace/sightbreak-touch-contrast-native-recovered-r4b-r2')
REPORT = REPO / 'docs/reports/gauntlet/m6-touch-contrast-recovered/native-r4b-r2'
HANDOFF = '384d17d0b44c5e5c46178023e52009010bc280f7'
load = lambda path: json.loads(Path(path).read_text())
sha = lambda data: hashlib.sha256(data).hexdigest()
digest = lambda path: sha(Path(path).read_bytes())
git = lambda *args: subprocess.check_output(['git', '-C', str(REPO), *args])
result = {'scope': 'bounded source/log/archive/current-process audit of one failed attempt; zero native executions by reviewer',
          'handoff': HANDOFF, 'time_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()}
assert git('rev-parse', 'HEAD').decode().strip() == HANDOFF
assert not git('status', '--porcelain')
receipt = load(REPORT / 'ARCHIVE.json')
manifest = load(REPORT / 'payload-manifest.json')
assert digest(REPORT / 'payload-manifest.json') == receipt['payload_manifest_sha256']
entries = manifest['files']
expected = {x['path']: x for x in entries}
assert len(entries) == len(expected) == 628
paths = {str(p.relative_to(RAW)) for p in RAW.rglob('*') if p.is_file()}
assert paths == set(expected)
for relative, item in expected.items():
    actual = RAW / relative
    assert actual.stat().st_size == item['bytes'] and digest(actual) == item['sha256'], relative
assert sum(x['bytes'] for x in entries) == manifest['raw_bytes'] == 10619634
assert manifest['png_count'] == len(list(RAW.rglob('*.png'))) == 0
archive = RAW.with_suffix('.tar.xz')
assert archive.stat().st_size == receipt['archive_bytes'] == 3662336
assert digest(archive) == receipt['archive_sha256'] == '9e5cfa76aaffc0b4c41b9bbead37c2e872c983545eff24117a99118e890d46e6'
reassembly = hashlib.sha256()
for part in receipt['parts']:
    data = (REPORT / part['path']).read_bytes()
    assert len(data) == part['bytes'] <= 24 * 1024 * 1024 and sha(data) == part['sha256']
    assert data == git('show', HANDOFF + ':' + str((REPORT / part['path']).relative_to(REPO)))
    reassembly.update(data)
assert reassembly.hexdigest() == receipt['archive_sha256']
seen = set()
with tarfile.open(archive, 'r:xz') as bundle:
    for member in bundle:
        assert member.isfile() and member.name not in seen
        seen.add(member.name)
        data = bundle.extractfile(member).read()
        if member.name == 'payload-manifest.json':
            assert data == (REPORT / 'payload-manifest.json').read_bytes()
        else:
            assert member.name.startswith('raw/')
            item = expected[member.name[4:]]
            assert len(data) == member.size == item['bytes'] and sha(data) == item['sha256']
assert seen == {'payload-manifest.json'} | {'raw/' + x for x in expected}
assert len(seen) == receipt['members'] == 629
result['preservation'] = {'all_raw_paths_hashes_sizes': True, 'raw_files': len(entries), 'raw_bytes': manifest['raw_bytes'],
                          'archive_bytes': archive.stat().st_size, 'archive_sha256': receipt['archive_sha256'],
                          'archive_members': len(seen), 'embedded_manifest_exact': True, 'parts': len(receipt['parts']),
                          'part_hashes_sizes_and_reassembly': True, 'committed_part_exact': True, 'pngs': 0}
start = load(RAW / 'lane-start.json')
end = load(RAW / 'lane-end.json')
assert manifest['acquisition_complete'] is end['acquisition_complete'] is False
assert manifest['acquisition_error'] == end['error'] == 'import-candidate failed; immutable raw log retained'
assert load(RAW / 'controller-exit.json')['exit_code'] == 1
release = load(RAW / 'release-identity.json')
assert release['root_release_commit'] == 'ea4db3b00095871f6cfb82316895e4d2f18192b8'
release_data = git('show', release['root_release_commit'] + ':docs/reports/gauntlet/m6-touch-contrast-recovered/native-r4b-r2-root/ROOT_RELEASE.md')
assert release_data == (RAW / 'ROOT_RELEASE.md').read_bytes()
assert start['root_release'].encode() == release_data
assert datetime.datetime.fromisoformat(release['root_release_time']) < datetime.datetime.fromisoformat(start['start_utc'])
assert (RAW / 'INDEPENDENT_PREREGISTRATION.md').read_bytes() == (OUT / 'PREREGISTRATION.md').read_bytes()
assert (RAW / 'controller.py').read_bytes() == git('show', '2ecc3083c149cfcbb035d113fbc1a4b40a10f27b:docs/reports/gauntlet/m6-touch-contrast-recovered/acquisition-r4b-r2/controller.py')
assert (RAW / 'package_evidence.py').read_bytes() == git('show', '2ecc3083c149cfcbb035d113fbc1a4b40a10f27b:docs/reports/gauntlet/m6-touch-contrast-recovered/acquisition-r4b-r2/package_evidence.py')
assert digest(start['engine']) == start['engine_sha256']
engine_archive = Path(start['engine_archive']).read_bytes()
assert hashlib.sha512(engine_archive).hexdigest() == start['engine_archive_sha512']
with zipfile.ZipFile(start['engine_archive']) as bundle:
    assert sha(bundle.read('Godot_v4.7.2-stable_linux.x86_64')) == start['engine_sha256']
assert (RAW / 'engine-version.log').read_text().strip() == '4.7.2.stable.official.ed1daf0bf'
assert start['cpu_max'] == '400000 100000' and start['memory_max'] == '17179869184'
assert start['taskset'] == [0, 1, 2, 3] and start['LP_NUM_THREADS'] == start['OMP_NUM_THREADS'] == '2'
assert start['display'] == ':131' and start['attempt_limit'] == 1
admission = load(RAW / 'admission-source.json')
freeze = load(RAW / 'SOURCE_FREEZE-r4b-r2.json')
assert digest(RAW / 'SOURCE_FREEZE-r4b-r2.json') == start['freeze_sha256'] == 'f9d292d7cb04fc129eee7df84fdc1c0591ae14600497bcf63aac0243cd7f2563'
assert len(admission['frozen_files']) == 22
for item in admission['frozen_files']:
    assert digest(REPO / item['path']) == item['sha256']
    assert (REPO / item['path']).stat().st_size == item['bytes']
    assert sha(git('show', 'b001fc5087960729535f63c896b40d6dc25bd272:' + item['path'])) == item['sha256']
post = load(RAW / 'post-source.json')
assert dict(post['frozen_files']) == {x['path']: x['sha256'] for x in admission['frozen_files']}
fences = []
for source in admission['staged']:
    root = Path(start['fixture_root']) / source['name']
    assert digest(root / 'SOURCE.json') == source['manifest_sha256']
    originals = load(root / 'SOURCE.json')
    rows = dict(source['actual_path_hashes'])
    assert len(rows) == source['checked_paths'] == 327
    assert source['preimport_cache_absent'] is True
    for relative, expected_sha in rows.items():
        assert digest(root / relative) == expected_sha
    for item in originals['files']:
        assert sha(git('show', source['source'] + ':' + item['path'])) == rows[item['path']]
    assert len(originals['files']) == 323
    uids = [(root / relative).read_text().strip() for relative in rows if relative.endswith('.uid')]
    assert len(uids) == len(set(uids)) == 138
    matched = []
    for path in RAW.glob('*-' + source['name'] + '-source.json'):
        check = load(path)
        assert check['unchanged'] and check['checked_paths'] == 327
        assert dict(check['actual_path_hashes']) == rows and check['manifest_sha256'] == source['manifest_sha256']
        matched.append(path.name)
    post_stage = next(x for x in post['staged'] if x['name'] == source['name'])
    assert dict(post_stage['actual_path_hashes']) == rows and post_stage['checked_paths'] == 327
    fences.append({'name': source['name'], 'paths': len(rows), 'original_git_paths': 323, 'unique_uids': len(uids),
                   'source_fences': sorted(matched), 'all_before_after_post_source_unchanged': True})
snapshot = load(RAW / 'source-snapshot-manifest.json')
for item in snapshot['files']:
    assert digest(RAW / item['path']) == digest(item['source_path']) == item['sha256']
    assert (RAW / item['path']).stat().st_size == item['bytes']
assert len(snapshot['files']) == snapshot['file_count'] == 578
result['source_integrity'] = {'frozen_files': 22, 'staged': fences, 'snapshot_files': 578,
                             'snapshot_and_original_hashes_equal': True, 'source_mutations': []}
assert [x['label'] for x in end['events']] == ['engine-version', 'import-baseline', 'import-candidate']
result['producers'] = []
for index, event in enumerate(end['events']):
    label = event['label']; assert event == load(RAW / (label + '-result.json'))
    command = load(RAW / (label + '-command.json'))
    for key, value in command.items(): assert event[key] == value
    assert event['command'][:4] == ['taskset', '-c', '0,1,2,3', start['engine']]
    assert digest(RAW / (label + '.log')) == event['log_sha256']
    assert event['exit_code'] == 0 and event['wall_seconds'] < (30 if index == 0 else 300)
    env = event['environment_selectors']; state = RAW / 'private-state' / label
    assert env['DISPLAY'] == ':131' and env['SIGHTBREAK_STATE_DIR'] == str(state)
    assert env['LP_NUM_THREADS'] == env['OMP_NUM_THREADS'] == '2'
    for variable, leaf in [('XDG_DATA_HOME', 'data'), ('XDG_CONFIG_HOME', 'config'), ('XDG_CACHE_HOME', 'cache')]:
        assert env[variable] == str(state / leaf)
    result['producers'].append({'label': label, 'pid': event['pid'], 'exit': event['exit_code'],
                                'wall_seconds': event['wall_seconds'], 'engine_errors': event['engine_errors'],
                                'command_and_private_state_receipts_valid': True})
assert [len(x['engine_errors']) for x in end['events']] == [0, 0, 3]
not_run = ['xvfb-command.json', 'xvfb.log', 'backgrounds', 'background-freeze.json', 'baseline', 'candidate',
           'analyzer.log', 'analyzer-result.json', 'recomputed.json']
assert all(not (RAW / name).exists() for name in not_run)
assert not list(RAW.glob('regression-*-command.json'))
assert post['png_counts'] == {'baseline': 0, 'candidate': 0, 'backgrounds': 0}
assert len(post['errors']) == 5 and load(RAW / 'post-source-exit.json')['exit_code'] == 1
result['not_run'] = not_run + ['all four regressions']
pattern = re.compile(r'orphan|unclaimed|StringName|leak|resource.*(?:in use|still)|SCRIPT ERROR|Parse Error|ERROR:|WARNING:', re.I)
log_rows = []
for path in sorted(RAW.rglob('*.log')):
    matches = [{'line': i, 'text': line} for i, line in enumerate(path.read_text(errors='replace').splitlines(), 1) if pattern.search(line)]
    log_rows.append({'path': str(path.relative_to(RAW)), 'sha256': digest(path), 'matches': matches})
saved_logs = load(RAW / 'strict-log-review-complete.json')
assert log_rows == saved_logs['logs'] and len(log_rows) == 6
assert sum(len(x['matches']) for x in log_rows) == 3
assert saved_logs['strict_log_clean'] is False and saved_logs['orphan_unclaimed_leak_matches'] == []
result['strict_log_scan'] = log_rows
result['strict_log_clean'] = False
candidate = Path(start['fixture_root']) / 'candidate/game/scripts/ui/touch_controls.gd'
line = candidate.read_text().splitlines()[213]
assert line.strip() == 'var compact := key != "fire" and r < 32.0'
assert digest(candidate) == 'afa8fa5b311e20eca4f71fc8d3e46a5f7adb8fce65e0c5dfda4c53851c9219de'
result['source_failure_witness'] = {'path': str(candidate), 'line': 214, 'text': line,
                                    'sha256': digest(candidate), 'next_hypothesis': 'explicit bool annotation preserving the expression; source-only preregistration/review then separately authorized native verification'}
owned = {x['pid'] for x in end['events']}
assert owned == {96995, 96998, 97238}
assert len(end['owned_cleanup']) == 3
assert all(x['pid'] in owned and not x['was_running'] and x['exit_code'] == 0 and x['proc_path_absent'] for x in end['owned_cleanup'])
members, unreadable = [], []
for proc in Path('/proc').iterdir():
    if not proc.name.isdigit(): continue
    try:
        fields = (proc / 'stat').read_text().rsplit(')', 1)[1].split()
        if int(fields[2]) in owned: members.append({'pid': int(proc.name), 'pgid': int(fields[2]), 'state': fields[0]})
    except FileNotFoundError: pass
    except PermissionError: unreadable.append(int(proc.name))
assert not members
assert all(not Path('/proc/' + str(pid)).exists() for pid in owned)
display_absent = all(not Path(path).exists() for path in ('/tmp/.X11-unix/X131', '/tmp/.X131-lock'))
assert display_absent
terminal = load(RAW / 'terminal-pgid-display.json')
assert terminal['owned_pgids'] == sorted(owned) and terminal['current_members'] == []
assert terminal['live_launch_getpgid_observation_available'] is False and terminal['display_started'] is False
result['cleanup'] = {'expected_pgids_from_pid_and_start_new_session': sorted(owned), 'current_members': members,
                     'current_leaders_absent': True, 'display_absent': display_absent, 'unreadable_proc_pids': unreadable,
                     'live_launch_getpgid_observed': False, 'historical_terminal_scan_unchanged': True}
assert load(REPORT / 'packaging-exit.json')['exit_code'] == 0
# A final read of raw hashes ensures the audit itself did not mutate the payload.
assert {str(p.relative_to(RAW)) for p in RAW.rglob('*') if p.is_file()} == set(expected)
assert all(digest(RAW / relative) == item['sha256'] for relative, item in expected.items())
result.update({'audit_pass': True, 'acquisition_pass': False, 'product_quality': 'UNOBSERVED; candidate compile readiness FAILED',
               'visual_winner': None, 'native_or_analyzer_executions_by_reviewer': 0,
               'retained_failed_attempt_archive_valid': True, 'wall_seconds': time.monotonic() - START})
(OUT / 'actual-checks.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({k: result[k] for k in ('audit_pass', 'acquisition_pass', 'product_quality', 'preservation', 'cleanup', 'wall_seconds')}))
