#!/usr/bin/env python3
"""Bind the full non-document Git union and initialized sparse depth-one view."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess

ROOT = Path(__file__).resolve().parents[4]
BASE = '7d8ec7dda37764e0f45fd2ea1e8d330f84bc2508'
ALTERNATE = Path('/workspace/sightbreak/.git/objects').resolve()
ALLOWED = {'scripts/analyze_input_consumption.py', 'scripts/test_input_consumption_state.py',
           'scripts/test_input_consumption_transitions.py', 'scripts/test_input_consumption_receipts.py'}
SELECTED = ('.claude/', '.github/', 'backend/', 'scripts/', 'game/', 'server/', 'tools/')


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def git(root, *words):
    return subprocess.check_output(['git', '-C', str(root), *words])


def tree(root, source):
    result = {}
    for row in git(root, 'ls-tree', '-rz', source).split(b'\0'):
        if row:
            info, path = row.split(b'\t', 1)
            mode, kind, blob = info.decode().split()
            result[os.fsdecode(path)] = {'mode': mode, 'type': kind, 'blob': blob}
    return result


def non_docs(entries):
    return {path: value for path, value in entries.items() if not path.startswith('docs/')}


def index(root):
    result = {}
    for row in git(root, 'ls-files', '--stage', '-z').split(b'\0'):
        if row:
            info, path = row.split(b'\t', 1)
            mode, blob, stage = info.decode().split()
            require(stage == '0', 'Nonzero index stage')
            result[os.fsdecode(path)] = {'mode': mode, 'type': 'commit' if mode == '160000' else 'blob', 'blob': blob}
    return result


def skipped_paths(root):
    return {os.fsdecode(row[2:]) for row in git(root, 'ls-files', '-v', '-z').split(b'\0')
            if row and row[:1] == b'S'}


def blob_hashes(entries):
    """Stream every unique union blob through Git and verify its object ID."""
    objects = sorted({value['blob'] for value in entries})
    report = {}
    child = subprocess.Popen(['git', '-C', str(ROOT), 'cat-file', '--batch'],
                             stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        for object_id in objects:
            child.stdin.write((object_id + '\n').encode())
            child.stdin.flush()
            header = child.stdout.readline().decode().strip().split()
            require(len(header) == 3 and header[:2] == [object_id, 'blob'], 'Missing/non-blob union object: ' + object_id)
            size = int(header[2])
            sha1 = hashlib.sha1(b'blob ' + str(size).encode() + b'\0')
            sha256 = hashlib.sha256()
            remaining = size
            while remaining:
                chunk = child.stdout.read(min(1024 * 1024, remaining))
                require(bool(chunk), 'Truncated Git blob: ' + object_id)
                sha1.update(chunk)
                sha256.update(chunk)
                remaining -= len(chunk)
            require(child.stdout.read(1) == b'\n', 'Invalid Git blob separator')
            require(sha1.hexdigest() == object_id, 'Git blob hash mismatch: ' + object_id)
            report[object_id] = {'bytes': size, 'sha256': sha256.hexdigest()}
        child.stdin.close()
        require(child.wait(timeout=30) == 0, 'Git blob reader failed')
    finally:
        if child.poll() is None:
            child.kill()
            child.wait()
        for pipe in (child.stdin, child.stdout, child.stderr):
            if pipe is not None and not pipe.closed:
                pipe.close()
    return report


def working_file(root, path, expected, hashes, skipped):
    target = root / path
    if not os.path.lexists(target):
        require(path in skipped, 'Missing file is not a sparse omission: ' + str(target))
        return {'state': 'sparse_omitted', 'git_mode': expected['mode'], 'blob': expected['blob'], **hashes}
    metadata = target.lstat()
    if stat.S_ISLNK(metadata.st_mode):
        mode = '120000'
        raw = os.fsencode(os.readlink(target))
        sha1 = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw)
        sha256 = hashlib.sha256(raw)
        size = len(raw)
    else:
        require(stat.S_ISREG(metadata.st_mode), 'Tracked path is not a file: ' + str(target))
        mode = '100755' if metadata.st_mode & 0o111 else '100644'
        size = metadata.st_size
        sha1 = hashlib.sha1(b'blob ' + str(size).encode() + b'\0')
        sha256 = hashlib.sha256()
        with target.open('rb') as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                sha1.update(chunk)
                sha256.update(chunk)
    require(mode == expected['mode'], 'Working Git mode mismatch: ' + str(target))
    require(sha1.hexdigest() == expected['blob'], 'Working blob mismatch: ' + str(target))
    require(size == hashes['bytes'] and sha256.hexdigest() == hashes['sha256'], 'Working bytes mismatch: ' + str(target))
    return {'state': 'materialized', 'git_mode': mode, 'blob': expected['blob'], **hashes}


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source', required=True, help='Exact frozen source commit')
parser.add_argument('--base', default=BASE, help='Exact R6 preregistered base commit')
parser.add_argument('--depth', type=Path, default=ROOT / '.local/depth-one-source')
parser.add_argument('--output', type=Path, required=True, help='Fresh receipt JSON')
args = parser.parse_args()
if sorted(os.sched_getaffinity(0)) != [4]:
    raise RuntimeError('Source binding requires CPU 4 only')
output, depth = args.output.resolve(), args.depth.resolve()
require(not os.path.lexists(output), 'Preserve prior output; use a fresh receipt path')
require(not output.is_relative_to(depth), 'Receipt must be outside the depth source')
require(args.base == BASE, 'Base must remain the preregistered R5 source commit')
require(all(re.fullmatch(r'[0-9a-f]{40}', value) for value in (args.base, args.source)), 'Use exact full commits')
report = {'scope': 'Full tracked non-document source identity; no native qualification',
          'source': args.source, 'base': args.base, 'depth': str(depth), 'cpu_affinity': [4],
          'independent_object_copy': False, 'shared_object_alternate': str(ALTERNATE), 'passed': False}
try:
    require(git(ROOT, 'rev-parse', '--show-object-format').decode().strip() == 'sha1', 'Unexpected Git object format')
    for commit in (args.base, args.source):
        require(git(ROOT, 'rev-parse', commit + '^{commit}').decode().strip() == commit, 'Unavailable exact commit: ' + commit)
    subprocess.run(['git', '-C', str(ROOT), 'merge-base', '--is-ancestor', args.base, args.source], check=True)
    subprocess.run(['git', '-C', str(ROOT), 'merge-base', '--is-ancestor', args.source, 'HEAD'], check=True)
    before_all, final_all = tree(ROOT, args.base), tree(ROOT, args.source)
    before, final = non_docs(before_all), non_docs(final_all)
    union = sorted(before.keys() | final.keys())
    delta = [path for path in union if before.get(path) != final.get(path)]
    require(set(delta) <= ALLOWED, 'Unexpected non-document delta: ' + repr(delta))
    require({'scripts/analyze_input_consumption.py', 'scripts/test_input_consumption_transitions.py'} <= set(delta), 'Expected analyzer/transition-suite delta is absent')
    require(non_docs(tree(ROOT, 'HEAD')) == final, 'Current non-document HEAD differs from frozen source')
    require(non_docs(index(ROOT)) == final, 'Current non-document index differs from frozen source')
    require(not git(ROOT, 'status', '--porcelain=v1', '--untracked-files=all', '--', '.', ':!docs'), 'Current non-document worktree is dirty')
    require(git(depth, 'rev-parse', 'HEAD').decode().strip() == args.source, 'Wrong depth source HEAD')
    require(git(depth, 'rev-parse', '--is-shallow-repository').decode().strip() == 'true', 'Depth view is not shallow')
    require(git(depth, 'rev-list', '--count', 'HEAD').decode().strip() == '1', 'Depth view has more than one commit')
    require(index(depth) == final_all, 'Depth index is incomplete or differs from frozen source')
    require(tree(depth, 'HEAD') == final_all, 'Depth Git tree differs from frozen source')
    require(not git(depth, 'status', '--porcelain=v1', '--untracked-files=all'), 'Depth source is dirty')
    alternate_file = depth / '.git/objects/info/alternates'
    alternates = alternate_file.read_text().splitlines()
    require(alternates == [str(ALTERNATE)], 'Unexpected depth object alternate')
    require((depth / '.git/shallow').read_text().splitlines() == [args.source], 'Unexpected shallow boundary')
    values = list(before.values()) + list(final.values())
    require(all(value['type'] == 'blob' and value['mode'] in {'100644', '100755', '120000'} for value in values), 'Unsupported non-document tree entry')
    hashes = blob_hashes(values)
    current_skipped, depth_skipped = skipped_paths(ROOT), skipped_paths(depth)
    files = []
    for path in union:
        old, expected = before.get(path), final.get(path)
        row = {'path': path, 'base': old, 'source': expected, 'changed': path in delta}
        if expected:
            row['worktree'] = working_file(ROOT, path, expected, hashes[expected['blob']], current_skipped)
            row['depth'] = working_file(depth, path, expected, hashes[expected['blob']], depth_skipped)
            if path.startswith(SELECTED) or '/' not in path:
                require(row['depth']['state'] == 'materialized', 'Selected depth file was omitted: ' + path)
        else:
            require(not os.path.lexists(ROOT / path) and not os.path.lexists(depth / path), 'Deleted source path remains materialized: ' + path)
            row.update(worktree={'state': 'absent_in_source'}, depth={'state': 'absent_in_source'})
        files.append(row)
    report.update(checkout_head=git(ROOT, 'rev-parse', 'HEAD').decode().strip(), non_doc_delta=delta,
                  non_doc_union_paths=len(union), protected_non_doc_paths=len(union) - len(delta),
                  verified_unique_blobs=len(hashes), full_union_modes_and_blobs_verified=True,
                  all_other_non_doc_git_blobs_and_modes_unchanged=True,
                  worktree_materialized_paths=sum(row['worktree']['state'] == 'materialized' for row in files),
                  worktree_sparse_omissions=sum(row['worktree']['state'] == 'sparse_omitted' for row in files),
                  depth_materialized_paths=sum(row['depth']['state'] == 'materialized' for row in files),
                  depth_sparse_omissions=sum(row['depth']['state'] == 'sparse_omitted' for row in files),
                  depth_shallow=True, depth_commit_count=1, depth_status='',
                  depth_tracked_index_paths=len(final_all), alternate_contents=alternates,
                  blobs=hashes, files=files, passed=True)
except Exception as error:
    report['error'] = {'type': type(error).__name__, 'message': str(error)}
output.parent.mkdir(parents=True, exist_ok=True)
with output.open('x') as stream:
    json.dump(report, stream, indent=2)
    stream.write('\n')
print(json.dumps({key: value for key, value in report.items() if key not in {'files', 'blobs'}}, indent=2))
raise SystemExit(not report['passed'])
