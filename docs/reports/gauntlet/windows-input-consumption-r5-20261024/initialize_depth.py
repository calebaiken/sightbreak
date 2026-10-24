#!/usr/bin/env python3
"""Initialize one fresh, sparse depth-one source view using the shared objects."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[4]
DEPTH = ROOT / '.local/depth-one-source'
ALTERNATE = Path('/workspace/sightbreak/.git/objects')
SELECTED = ['.claude', 'scripts', 'game', 'server']


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
            result[os.fsdecode(path)] = (mode, blob)
    return result


def index(root):
    result = {}
    for row in git(root, 'ls-files', '--stage', '-z').split(b'\0'):
        if row:
            info, path = row.split(b'\t', 1)
            mode, blob, stage = info.decode().split()
            require(stage == '0', 'Nonzero index stage')
            result[os.fsdecode(path)] = (mode, blob)
    return result


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source', required=True, help='Exact 40-character frozen source commit')
parser.add_argument('--depth', type=Path, default=DEPTH, help='Fresh sparse source directory')
parser.add_argument('--output', type=Path, required=True, help='Fresh receipt JSON outside the depth view')
args = parser.parse_args()
DEPTH = args.depth.resolve()
if sorted(os.sched_getaffinity(0)) != [4]:
    raise RuntimeError('Depth setup requires CPU 4 only')
output = args.output.resolve()
require(re.fullmatch(r'[0-9a-f]{40}', args.source) is not None, 'Use an exact full source commit')
require(not os.path.lexists(output), 'Preserve prior output; use a fresh receipt path')
require(not output.is_relative_to(DEPTH), 'Receipt must be outside the depth source')
report = {'scope': 'Sparse source setup only; shared objects, no native execution',
          'source': args.source, 'depth': str(DEPTH), 'cpu_affinity': [4],
          'selected_directories': SELECTED, 'shared_object_alternate': str(ALTERNATE),
          'independent_object_copy': False, 'commands': [], 'passed': False}


def run(*words):
    command = ['git', '-C', str(DEPTH), *words]
    result = subprocess.run(command, capture_output=True)
    report['commands'].append({'command': command, 'exit_code': result.returncode,
                               'stdout': result.stdout.decode(errors='replace'),
                               'stderr': result.stderr.decode(errors='replace')})
    require(result.returncode == 0, 'Depth Git command failed: ' + ' '.join(words))


try:
    require(git(ROOT, 'rev-parse', args.source + '^{commit}').decode().strip() == args.source,
            'Frozen source is not the exact available commit')
    require(ALTERNATE.is_dir(), 'Shared Git object directory is absent')
    require(not os.path.lexists(DEPTH), 'Preserve existing depth source; target must be fresh')
    DEPTH.parent.mkdir(parents=True, exist_ok=True)
    initialized = subprocess.run(['git', 'init', '--quiet', str(DEPTH)], capture_output=True)
    report['commands'].append({'command': ['git', 'init', '--quiet', str(DEPTH)],
                               'exit_code': initialized.returncode,
                               'stdout': initialized.stdout.decode(errors='replace'),
                               'stderr': initialized.stderr.decode(errors='replace')})
    require(initialized.returncode == 0, 'Git initialization failed')
    alternate_file = DEPTH / '.git/objects/info/alternates'
    alternate_file.write_text(str(ALTERNATE.resolve()) + '\n')
    run('symbolic-ref', 'HEAD', 'refs/heads/r4-depth-one')
    run('update-ref', 'refs/heads/r4-depth-one', args.source)
    (DEPTH / '.git/shallow').write_text(args.source + '\n')
    run('sparse-checkout', 'init', '--cone', '--no-sparse-index')
    run('sparse-checkout', 'set', '--no-sparse-index', *SELECTED)
    # Populate the entire index explicitly; worktree-only restore is insufficient.
    run('read-tree', '--reset', '-u', 'HEAD')
    expected = tree(ROOT, args.source)
    require(index(DEPTH) == expected, 'Depth index does not contain the exact full tree')
    require(not git(DEPTH, 'status', '--porcelain=v1', '--untracked-files=all'), 'Depth source is dirty')
    require(git(DEPTH, 'rev-parse', 'HEAD').decode().strip() == args.source, 'Wrong depth HEAD')
    require(git(DEPTH, 'rev-parse', '--is-shallow-repository').decode().strip() == 'true', 'Depth view is not shallow')
    require(git(DEPTH, 'rev-list', '--count', 'HEAD').decode().strip() == '1', 'Depth view exposes more than one commit')
    for path in expected:
        if any(path.startswith(directory + '/') for directory in SELECTED) or '/' not in path:
            require(os.path.lexists(DEPTH / path), 'Selected depth file is absent: ' + path)
    report.update(depth_head=args.source, depth_shallow=True, depth_commit_count=1,
                  tracked_index_paths=len(expected), status='',
                  alternate_file=str(alternate_file), alternate_contents=alternate_file.read_text(), passed=True)
except Exception as error:
    report['error'] = {'type': type(error).__name__, 'message': str(error)}
output.parent.mkdir(parents=True, exist_ok=True)
with output.open('x') as stream:
    json.dump(report, stream, indent=2)
    stream.write('\n')
print(json.dumps({key: value for key, value in report.items() if key != 'commands'}, indent=2))
raise SystemExit(not report['passed'])
