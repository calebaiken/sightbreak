#!/usr/bin/env python3
"""Compare every non-doc Git identity and erase only preregistered opt-in edits."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

BASE = 'c32415148db1f110bbc7eadfca3793d4693429ff'
PREREG = 'e939c30f6bc348b7e9b2521ccc2d8ef53ecf527b'
NEW = 'scripts/test_reopened_shutdown_diagnostic.py'


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args])


def tree(root, ref):
    rows = {}
    for row in git(root, 'ls-tree', '-r', '-z', ref).split(b'\0'):
        if not row:
            continue
        meta, name = row.split(b'\t', 1)
        name = name.decode()
        if not name.startswith('docs/'):
            mode, kind, oid = meta.decode().split()
            rows[name] = dict(mode=mode, kind=kind, oid=oid)
    return rows


def replace_once(raw, old, new):
    assert raw.count(old) == 1, (old, raw.count(old))
    return raw.replace(old, new)


def erase(name, raw):
    if name == 'scripts/verify_offline_export.py':
        raw = replace_once(raw,
            b"    parser.add_argument('--reopened-verbose', action='store_true',\n"
            b"                        help='Diagnostic engine verbosity for only the reopened process; original deadlines and strict gates apply')\n", b'')
        raw = replace_once(raw,
            b"        reopened = launch('reopened', [str(executable), '--audio-driver', 'Dummy', *flags,\n"
            b"                                     *(['--verbose'] if args.reopened_verbose else []), '--',\n",
            b"        reopened = launch('reopened', [str(executable), '--audio-driver', 'Dummy', *flags, '--',\n")
    elif name == '.github/workflows/desktop-alpha.yml':
        raw = replace_once(raw,
            b'      verbose_reopened_shutdown:\n'
            b'        description: Diagnose only reopened Windows client shutdown with engine verbose output\n'
            b'        type: boolean\n        required: false\n        default: false\n', b'')
        raw = replace_once(raw,
            b" ${{ runner.os == 'Windows' && inputs.verbose_reopened_shutdown && '--reopened-verbose' || '' }}", b'')
    elif name == 'scripts/validate.sh':
        raw = replace_once(raw, b'python3 scripts/test_reopened_shutdown_diagnostic.py -v\n', b'')
    return raw


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--candidate', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert sorted(os.sched_getaffinity(0)) == [4]
    root = args.source.resolve()
    subprocess.run(['git', '-C', str(root), 'merge-base', '--is-ancestor', PREREG, args.candidate], check=True)
    baseline, candidate = tree(root, BASE), tree(root, args.candidate)
    assert set(candidate) - set(baseline) == {NEW}
    assert not set(baseline) - set(candidate)
    changed, materialized, omitted, identities = [], [], [], []
    for name, original in sorted(baseline.items()):
        current = candidate[name]
        assert current['mode'] == original['mode'] and current['kind'] == original['kind'], name
        old = git(root, 'cat-file', 'blob', original['oid'])
        raw = git(root, 'cat-file', 'blob', current['oid'])
        assert erase(name, raw) == old, name
        if current != original:
            changed.append(name)
        path = root / name
        if path.exists():
            assert path.read_bytes() == raw, name
            materialized.append(name)
        else:
            omitted.append(name)
        identities.append(dict(path=name, baseline=original, candidate=current, erased_sha256=hashlib.sha256(old).hexdigest()))
    assert changed == ['.github/workflows/desktop-alpha.yml', 'scripts/validate.sh', 'scripts/verify_offline_export.py']
    new_raw = git(root, 'cat-file', 'blob', candidate[NEW]['oid'])
    assert (root / NEW).read_bytes() == new_raw
    assert not git(root, 'diff', '--name-only', args.candidate, '--', ':!docs/')
    report = dict(passed=True, base=BASE, preregistration=PREREG, candidate=args.candidate,
                  cpu_affinity=sorted(os.sched_getaffinity(0)), original_path_count=len(baseline),
                  candidate_path_count=len(candidate), changed_original_paths=changed,
                  new_paths=[dict(path=NEW, **candidate[NEW], sha256=hashlib.sha256(new_raw).hexdigest())],
                  full_union_erasure_equal=True, materialized_original_paths=materialized,
                  sparse_omitted_original_paths=omitted, identities=identities)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('identities','materialized_original_paths','sparse_omitted_original_paths')}, indent=2))


if __name__ == '__main__':
    main()
