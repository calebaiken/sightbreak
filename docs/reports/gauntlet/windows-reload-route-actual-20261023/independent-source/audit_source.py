#!/usr/bin/env python3
"""Record exact source union, populated shallow fixture and original receipts."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument('--source', type=Path, required=True)
parser.add_argument('--depth-one', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
if sorted(os.sched_getaffinity(0)) != [4]:
    raise RuntimeError('CPU 4 only')
candidate = 'ea6c330a272f17a8a68ef94af868c70bda95a91e'
baseline = '49ae54b0e4f5d880bdf06e4eb783a616b2dff684'
source, shallow = args.source.resolve(), args.depth_one.resolve()

def git(root, *words, check=True):
    return subprocess.run(['git', '-C', str(root), *words], capture_output=True, check=check)

def value(root, *words):
    return git(root, *words).stdout.decode().strip()

def digest(data):
    return hashlib.sha256(data).hexdigest()

def blob(ref, name):
    return git(source, 'show', ref + ':' + name).stdout

scopes = ('game', 'scripts', '.github', 'server', 'backend')
changed = value(source, 'diff', '--name-only', baseline, candidate, '--', *scopes).splitlines()
assert changed == ['scripts/native_approach.py', 'scripts/test_native_route_pulse.py'], changed
old, new = (blob(ref, 'scripts/native_approach.py') for ref in (baseline, candidate))
expected = old.replace(b'    fine = False\n', b'    fine = pulse is not None\n').replace(
    b'    Success is determined only from actual later neutral stopped observations.\n',
    b'    An explicit native pulse callback owns every displacement from rest, so\n'
    b'    traced coarse steering cannot hold keys across delayed readbacks.\n'
    b'    Success is determined only from actual later neutral stopped observations.\n')
assert new == expected
unchanged = ['scripts/verify_offline_export.py', 'scripts/native_settings_route.py',
             'scripts/fixtures/export_integration.gd', 'scripts/verify_integration_export.py',
             'scripts/validate.sh', 'scripts/build_manifest.py']
bindings = []
for name in unchanged + changed:
    before, after = blob(baseline, name), blob(candidate, name)
    bindings.append({'path': name, 'baseline_bytes': len(before), 'baseline_sha256': digest(before),
                     'candidate_bytes': len(after), 'candidate_sha256': digest(after), 'same': before == after})
assert all(row['same'] for row in bindings[:len(unchanged)])
trees = {name: {ref: value(source, 'rev-parse', ref + ':' + name)
                for ref in (baseline, candidate)} for name in ('game', '.github', 'server', 'backend')}
assert all(len(set(row.values())) == 1 for row in trees.values())
parent = git(shallow, 'rev-parse', '--verify', 'HEAD^', check=False)
base_available = git(shallow, 'cat-file', '-e', baseline + '^{commit}', check=False)
shallow_row = dict(root=str(shallow), head=value(shallow, 'rev-parse', 'HEAD'),
    shallow=value(shallow, 'rev-parse', '--is-shallow-repository'),
    commit_count=int(value(shallow, 'rev-list', '--count', 'HEAD')),
    status=value(shallow, 'status', '--porcelain', '--untracked-files=all'),
    parent_lookup_exit=parent.returncode, parent_lookup_stderr=parent.stderr.decode(),
    baseline_object_lookup_exit=base_available.returncode,
    baseline_object_lookup_stderr=base_available.stderr.decode(),
    alternates_file_exists=(shallow / '.git/objects/info/alternates').exists())
assert shallow_row['head'] == candidate and shallow_row['shallow'] == 'true'
assert shallow_row['commit_count'] == 1 and shallow_row['status'] == ''
assert parent.returncode != 0 and base_available.returncode != 0
assert not shallow_row['alternates_file_exists']
files = []
for name in value(shallow, 'ls-files').splitlines():
    path = shallow / name
    if not path.is_file():
        continue
    if name.startswith(('scripts/', '.github/', '.claude/', 'server/', 'game/')) or name in ('AGENTS.md', 'CLAUDE.md'):
        a, b, frozen = (source / name).read_bytes(), path.read_bytes(), blob(candidate, name)
        assert a == b == frozen, name
        files.append(dict(path=name, bytes=len(frozen), sha256=digest(frozen)))
assert len(files) > 400
here = Path(__file__).parent
original = here / 'originals'
assert (original / '49ae54b0-native_approach.py.txt').read_bytes() == old
actions_raw = (original / 'original-offline-input-actions.json').read_bytes()
results_raw = (original / 'original-offline-input-results.json').read_bytes()
actions, results = json.loads(actions_raw), json.loads(results_raw)
receipt = results['settings_cover_route']
loss = receipt['precondition_loss']
last, rejected = loss['previous_valid_state'], loss['rejected_state']
assert loss['reason'] == 'left_declared_clear_corridor'
assert abs(last['local_actor']['position'][0] + 8.39777946472168) < 1e-9
assert abs(rejected['local_actor']['position'][0] + 11.5494470596313) < 1e-9
assert not receipt.get('native_pulses')
events = [row for row in actions if row['event'].startswith('settings_route_')]
assert not any('native_pulse' in row['event'] for row in events)
route_original = dict(actions_sha256=digest(actions_raw), results_sha256=digest(results_raw),
    route_status=receipt['status'], loss_reason=loss['reason'],
    last_accepted={k:last[k] for k in ('simulation_tick', 'elapsed', 'wall_msec', 'local_actor', 'local_input')},
    rejected={k:rejected[k] for k in ('simulation_tick', 'elapsed', 'wall_msec', 'local_actor', 'local_input')},
    pulse_count=len(receipt.get('native_pulses', [])), route_events=events,
    overall_passed=results['passed'], original_error=results['error'])
report = dict(candidate=candidate, baseline=baseline, changed_code_paths=changed, trees=trees,
    bindings=bindings, depth_one=shallow_row, populated_file_count=len(files), populated_files=files,
    original_failure=route_original, all_checks_passed=True)
args.output.write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({k:v for k,v in report.items() if k not in ('populated_files', 'original_failure')}, indent=2))
