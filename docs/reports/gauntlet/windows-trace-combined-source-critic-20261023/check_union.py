#!/usr/bin/env python3
"""Compare the complete source union of exact independently accepted components."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

BASE = '49ae54b0e4f5d880bdf06e4eb783a616b2dff684'
ROUTE = 'ea6c330a'
ADAPTER = 'b4a2cf4af787dbd811f1b59e0db8264692598b11'
ADAPTER_BASE = 'b4145dde093fa77604ff7a073ab8a8e7167897f9'


def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args])


def exact(repo, ref):
    return git(repo, 'rev-parse', ref).decode().strip()


def tree(repo, ref):
    result = {}
    for row in git(repo, 'ls-tree', '-rz', ref).split(b'\0'):
        if not row:
            continue
        metadata, raw_path = row.split(b'\t', 1)
        path = raw_path.decode()
        if path.startswith('docs/'):
            continue
        mode, kind, blob = metadata.decode().split()
        assert kind == 'blob', (path, kind)
        data = git(repo, 'cat-file', 'blob', blob)
        result[path] = dict(mode=mode, kind=kind, blob=blob, bytes=len(data),
                            sha256=hashlib.sha256(data).hexdigest())
    return result


def changes(before, after):
    return {path: after.get(path) for path in sorted(before.keys() | after.keys())
            if before.get(path) != after.get(path)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--source', required=True)
    parser.add_argument('--accepted-trace', required=True)
    parser.add_argument('--trace-acceptance', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert sorted(os.sched_getaffinity(0)) == [4]
    source, trace = exact(args.repo, args.source), exact(args.repo, args.accepted_trace)
    baseline = tree(args.repo, BASE)
    route = tree(args.repo, ROUTE)
    traced = tree(args.repo, trace)
    adapter_base = tree(args.repo, ADAPTER_BASE)
    adapter = tree(args.repo, ADAPTER)
    components = {'initial_pulse': changes(baseline, route),
                  'accepted_trace': changes(baseline, traced),
                  'dispatch_adapter': changes(adapter_base, adapter)}
    assert sorted(components['initial_pulse']) == ['scripts/native_approach.py', 'scripts/test_native_route_pulse.py']
    assert sorted(components['dispatch_adapter']) == ['.github/workflows/desktop-alpha.yml']
    expected, owners = baseline.copy(), {}
    for component, delta in components.items():
        for path, entry in delta.items():
            assert path not in owners, ('Overlapping source requires separate contextual proof', path, owners.get(path), component)
            owners[path] = component
            if entry is None:
                expected.pop(path, None)
            else:
                expected[path] = entry
    actual = tree(args.repo, source)
    mismatches = {path: {'expected': expected.get(path), 'actual': actual.get(path)}
                  for path in sorted(expected.keys() | actual.keys())
                  if expected.get(path) != actual.get(path)}
    result = dict(source=source, protected_base=BASE, initial_pulse=exact(args.repo, ROUTE),
                  accepted_trace=trace, trace_acceptance=args.trace_acceptance,
                  adapter=ADAPTER, cpu_affinity=[4],
                  scope='Complete tracked non-document path/mode/blob/content union; source only',
                  baseline_paths=len(baseline), expected_paths=len(expected), actual_paths=len(actual),
                  component_changes=components, path_owners=owners, mismatches=mismatches,
                  expected_source=expected, actual_source=actual, passed=not mismatches)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k not in {'expected_source', 'actual_source'}}, indent=2))
    raise SystemExit(bool(mismatches))


if __name__ == '__main__':
    main()
