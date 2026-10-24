#!/usr/bin/env python3
"""Compare named exact source objects; this verifier deliberately needs base Git."""
import argparse
import json
from pathlib import Path
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument('--source', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
root = args.source.resolve()
BASE = 'c32415148db1f110bbc7eadfca3793d4693429ff'
CANDIDATE = '7101350e5d0a2f6e4afb9a913b5b1bcf2107857a'


def git(*values):
    return subprocess.check_output(['git', *values], cwd=root)


def tree(ref):
    result = {}
    for row in git('ls-tree', '-rz', ref).split(b'\0'):
        if not row:
            continue
        meta, name = row.split(b'\t', 1)
        if not name.startswith(b'docs/'):
            mode, kind, oid = meta.decode().split()
            result[name.decode()] = dict(mode=mode, kind=kind, oid=oid)
    return result


old, new = tree(BASE), tree(CANDIDATE)
changed = {name: dict(base=old.get(name), candidate=new.get(name))
           for name in sorted(old.keys() | new.keys()) if old.get(name) != new.get(name)}
assert set(changed) == {'.github/workflows/desktop-alpha.yml', 'scripts/verify_offline_export.py',
                        'scripts/validate.sh', 'scripts/test_reopened_shutdown_diagnostic.py'}
controller = git('show', CANDIDATE + ':scripts/verify_offline_export.py')
controller = controller.replace(b"    parser.add_argument('--reopened-verbose', action='store_true',\n                        help='Diagnostic engine verbosity for only the reopened process; original deadlines and strict gates apply')\n", b'')
controller = controller.replace(b"        reopened = launch('reopened', [str(executable), '--audio-driver', 'Dummy', *flags,\n                                     *(['--verbose'] if args.reopened_verbose else []), '--',\n", b"        reopened = launch('reopened', [str(executable), '--audio-driver', 'Dummy', *flags, '--',\n")
workflow = git('show', CANDIDATE + ':.github/workflows/desktop-alpha.yml')
workflow = workflow.replace(b"      verbose_reopened_shutdown:\n        description: Diagnose only reopened Windows client shutdown with engine verbose output\n        type: boolean\n        required: false\n        default: false\n", b'')
workflow = workflow.replace(b" ${{ runner.os == 'Windows' && inputs.verbose_reopened_shutdown && '--reopened-verbose' || '' }}", b'')
validate = git('show', CANDIDATE + ':scripts/validate.sh').replace(b'python3 scripts/test_reopened_shutdown_diagnostic.py -v\n', b'')
erasures = {name: data == git('show', BASE + ':' + name) for name, data in
            [('scripts/verify_offline_export.py', controller),
             ('.github/workflows/desktop-alpha.yml', workflow), ('scripts/validate.sh', validate)]}
assert all(erasures.values())
assert 'scripts/test_reopened_shutdown_diagnostic.py' not in old
assert git('rev-parse', BASE + ':game') == git('rev-parse', CANDIDATE + ':game')
for name, meta in new.items():
    path = root / name
    assert path.is_file(), name
    assert git('hash-object', '--', name).decode().strip() == meta['oid'], name
    assert bool(path.stat().st_mode & 0o111) == (meta['mode'] == '100755'), name
report = dict(base=BASE, candidate=CANDIDATE, base_count=len(old), candidate_count=len(new),
              union_count=len(old.keys() | new.keys()), changed=changed, erasures=erasures,
              new_test_absent_in_base=True, all_materialized_blobs_and_modes_match=True,
              protected_game_tree_equal=True, source_verifier_requires_named_base_object=True)
args.output.write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps({key:value for key,value in report.items() if key != 'changed'}))
