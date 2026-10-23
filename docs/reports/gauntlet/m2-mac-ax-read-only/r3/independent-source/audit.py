#!/usr/bin/env python3
"""Recompute exact source, retained evidence and depth-one provenance."""
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

parser = argparse.ArgumentParser()
parser.add_argument('--root', type=Path, required=True)
parser.add_argument('--depth-one', type=Path, required=True)
parser.add_argument('--actual-root', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
root, depth, actual = args.root.resolve(), args.depth_one.resolve(), args.actual_root.resolve()
base, candidate = 'd6cb78aa4b0bc5a8265d9b82a0d379b4ee386e53', '4854aed946d25d27482af66c332f84aa51cea8fb'
report = Path(__file__).resolve().parent
assert os.sched_getaffinity(0) == {4}

def git(*arguments, cwd=root):
    return subprocess.check_output(['git', *arguments], cwd=cwd)

def digest(data):
    return hashlib.sha256(data).hexdigest()

def snapshot(ref):
    result = {}
    for row in git('ls-tree', '-r', ref).decode().splitlines():
        metadata, path = row.split('\t', 1)
        mode, kind, oid = metadata.split()
        result[path] = dict(mode=mode, type=kind, oid=oid)
    return result

before, after = snapshot(base), snapshot(candidate)
changes = [path for path in sorted(set(before) | set(after)) if before.get(path) != after.get(path)]
source_changes = [path for path in changes if not path.startswith('docs/reports/')]
assert source_changes == ['scripts/probe_macos_ax.py', 'scripts/test_macos_ax_untitled.py']
removed = sorted(set(before) - set(after))
assert not removed
modified_existing = [path for path in changes if path in before]
assert modified_existing == ['scripts/probe_macos_ax.py']
source_union = []
for path in source_changes:
    frozen = git('show', candidate + ':' + path)
    assert frozen == (root / path).read_bytes() == (depth / path).read_bytes()
    source_union.append(dict(path=path, sha256=digest(frozen), bytes=len(frozen),
        base_blob=before.get(path), candidate_blob=after[path]))
unchanged = ['game', '.github', 'scripts/macos_window_capture.swift', 'scripts/verify_macos_ax_read_only.py',
    'scripts/macos_ax_contract.py', 'scripts/macos_ax_appkit.py', 'scripts/macos_deploy_ocr.py',
    'scripts/macos_ordinary_input.py', 'scripts/verify_macos_ordinary.py', 'scripts/macos_native_input.py',
    'scripts/probe_macos_input.py', 'scripts/test_macos_ax_read_only.py',
    'scripts/test_macos_ax_controller.py', 'scripts/test_macos_ax_paths.py', 'scripts/fixtures']
identical = {}
for path in unchanged:
    old = git('rev-parse', base + ':' + path).decode().strip()
    new = git('rev-parse', candidate + ':' + path).decode().strip()
    assert old == new
    identical[path] = new
preserved_reports = [path for path in before if path.startswith('docs/reports/gauntlet/m2-mac-ax-read-only/')]
assert all(before[path] == after[path] for path in preserved_reports)
legacy_path = 'docs/reports/gauntlet/m2-mac-ax-read-only/independent-fresh-source/replay_native_boundaries.py'
r1 = git('show', '12ec93dd:' + legacy_path)
copy_path = 'docs/reports/gauntlet/m2-mac-ax-read-only/r3/legacy-controls/replay_native_boundaries.py'
assert r1 == git('show', candidate + ':' + copy_path)
r2_path = 'docs/reports/gauntlet/m2-mac-ax-read-only/r2/independent-fresh-source/review_r2_boundaries.py'
r2 = git('show', '114f2224:' + r2_path)
assert r2 == (report / 'original-r2-boundaries.py').read_bytes()

actual_prefix = 'docs/reports/gauntlet/m2-mac-ax-read-only/r2/independent-actual/'
actual_members = {}
for path in git('ls-tree', '-r', '--name-only', 'e1221ba2', '--', actual_prefix).decode().splitlines():
    blob = git('show', 'e1221ba2:' + path)
    assert (actual / path).read_bytes() == blob
    actual_members[path] = dict(bytes=len(blob), sha256=digest(blob))
raw_path = actual_prefix + 'native-39939989024/qa/ax-read-only/ax-observation.json'
receipt = json.loads((actual / raw_path).read_bytes())
controller = json.loads((actual / (actual_prefix + 'native-39939989024/qa/ax-read-only/results.json')).read_bytes())
sys.path.insert(0, str(root / 'scripts'))
import macos_ax_contract as contract
request, pin = controller['ax_observation'], controller['pinned_window']
binding = dict(pid=pin['owner_pid'], window=pin['window_id'], bounds=pin['bounds_points'],
    nonce=request['nonce'], observer_pid=request['observer_pid'], started=request['started_monotonic'],
    finished=request['finished_monotonic'], budget=request['budget_seconds'])
contract.validate_request(receipt, **binding)
try:
    contract.validate_collection(receipt, **binding)
except RuntimeError as error:
    original_rejection = str(error)
else:
    raise AssertionError('Original incomplete failure unexpectedly accepted')
assert original_rejection == 'AX traversal did not complete'
assert receipt['failure']['message'] == 'Required AX attribute unavailable: AXTitle code=-25212'

assert git('rev-parse', 'HEAD', cwd=depth).decode().strip() == candidate
assert git('rev-parse', '--is-shallow-repository', cwd=depth) == b'true\n'
assert git('rev-list', '--all', '--count', cwd=depth) == b'1\n'
assert git('remote', '-v', cwd=depth) == b''
assert git('status', '--porcelain', cwd=depth) == b''
absent = {}
for ref in (base, '90f77959de153b7779bc9202de94b6ef79118c17', 'c08889b', '12ec93dd', '114f2224'):
    result = subprocess.run(['git', 'cat-file', '-e', ref + '^{commit}'], cwd=depth, capture_output=True)
    assert result.returncode != 0
    absent[ref] = dict(exit=result.returncode, stderr=result.stderr.decode().strip())
commit_objects = git('cat-file', '--batch-all-objects', '--batch-check=%(objecttype) %(objectname)', cwd=depth)
commit_objects = [line for line in commit_objects.decode().splitlines() if line.startswith('commit ')]
assert commit_objects == ['commit ' + candidate]

remote = git('ls-remote', 'origin', 'refs/heads/codex/m2-mac-ax-untitled-r3').decode().strip()
assert remote.split()[0] == '115ecbc07821815b30fdb1f82ed8d133c15495c8'
remote_delta = git('diff', '--name-only', candidate, '115ecbc07821815b30fdb1f82ed8d133c15495c8').decode().splitlines()
assert all(path.startswith('docs/reports/gauntlet/m2-mac-ax-read-only/r3/')
           or path == 'docs/engineering/NEXT_SESSION.md' for path in remote_delta)

suite_counts = {}
import re
for name in ('maintained-corrected.log', 'depth-one-maintained.log', 'challenge-final.log',
             'depth-one-challenge.log', 'r2-boundaries-source.log', 'r2-boundaries-depth-one.log'):
    content = (report / name).read_text()
    counts = [int(value) for value in re.findall(r'^Ran (\d+) tests? in', content, re.M)]
    suite_counts[name] = dict(test_methods=sum(counts), runs=len(counts), sha256=digest(content.encode()))
    assert 'FAILED (' not in content

result = dict(candidate=candidate, control=base, preregistration='57c790689a3570d4aea254931d2b3099399ce6d5',
    cpu_affinity=sorted(os.sched_getaffinity(0)), source_union=source_union,
    exact_changed_paths=changes, removed_paths=removed, modified_existing_paths=modified_existing,
    unchanged_tree_and_blob_ids=identical, preserved_existing_ax_report_files=len(preserved_reports),
    r1_original_falsifier_sha256=digest(r1), r2_original_boundary_sha256=digest(r2),
    actual_review_commit='e1221ba2ab391810005f63a3e43b58bc26d06e21',
    actual_original_members=actual_members, original_collection_rejection=original_rejection,
    original_failure=receipt['failure'], depth_one=dict(path=str(depth), head=candidate, shallow=True,
        reachable_commits=1, commit_objects=commit_objects, remotes=[], clean=True, absent_history=absent,
        initialized_sparse_paths=git('sparse-checkout', 'list', cwd=depth).decode().splitlines()),
    remote=dict(advertised_ref=remote, documentation_only_delta_from_candidate=remote_delta),
    suite_counts=suite_counts, no_native_or_ci_execution=True)
args.output.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(dict(changed_source_files=len(source_union), retained_actual_files=len(actual_members),
    preserved_ax_reports=len(preserved_reports), depth_one_commit_objects=len(commit_objects), suites=suite_counts), indent=2))
