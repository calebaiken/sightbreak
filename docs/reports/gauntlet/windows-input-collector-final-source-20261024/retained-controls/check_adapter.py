#!/usr/bin/env python3
"""Source-only byte proof for the exact default-off Windows workflow adapter."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path


WORKFLOW = '.github/workflows/desktop-alpha.yml'
BASE = 'b4145dde093fa77604ff7a073ab8a8e7167897f9'
ADAPTER = 'b4a2cf4af787dbd811f1b59e0db8264692598b11'
INPUT = b'''      observe_windows_input:
        description: Retain bounded guest-loopback Windows input stage observations
        type: boolean
        required: false
        default: false
'''
ARGUMENT = b" ${{ runner.os == 'Windows' && inputs.observe_windows_input && '--observe-input-consumption' || '' }}"
COMMAND = b'        run: python scripts/verify_integration_export.py --target ${{ matrix.target }} --visit-armory --timeout 240 --output builds/desktop-playability/native-input'


def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args])


def sha(data):
    return hashlib.sha256(data).hexdigest()


def source_tree(repo, commit):
    rows = git(repo, 'ls-tree', '-rz', commit).split(b'\0')
    result = {}
    for row in rows:
        if row:
            metadata, path = row.split(b'\t', 1)
            if not path.startswith(b'docs/'):
                mode, kind, blob = metadata.decode().split()
                result[path.decode()] = {'mode': mode, 'kind': kind, 'blob': blob}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--source', default=ADAPTER)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    source = git(args.repo, 'rev-parse', args.source).decode().strip()
    original = git(args.repo, 'show', BASE + ':' + WORKFLOW)
    frozen_adapter = git(args.repo, 'show', ADAPTER + ':' + WORKFLOW)
    candidate = git(args.repo, 'show', source + ':' + WORKFLOW)
    assert candidate == frozen_adapter, 'The reviewed workflow differs from exact adapter'
    assert candidate.count(INPUT) == 1
    assert candidate.count(ARGUMENT) == 1
    assert candidate.count(COMMAND + ARGUMENT + b'\n') == 1
    recovered = candidate.replace(INPUT, b'', 1).replace(ARGUMENT, b'', 1)
    assert recovered == original, 'Reverse adapter does not restore all original bytes'
    assert b'  workflow_dispatch:\n    inputs:\n' in candidate
    assert candidate.index(INPUT) > candidate.index(b'  workflow_dispatch:\n')
    assert candidate.index(INPUT) < candidate.index(b'permissions:\n')
    assert candidate.count(b'observe_windows_input') == 2
    assert candidate.count(b'--observe-input-consumption') == 1
    assert b'permissions:\n  contents: read\n  actions: read\n' in recovered
    assert b'      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683\n' in recovered
    assert b"        if: always() && steps.export.outcome == 'success' && runner.os != 'macOS'\n" + COMMAND + ARGUMENT in candidate
    # workflow_dispatch is the only workflow event with inputs in this workflow.
    # GitHub keeps declared Boolean inputs typed in the inputs context; missing
    # properties are empty strings. This finite model tests the fixed expression
    # under that declared contract. It does not claim a real Actions evaluation.
    cases = []
    for event in ('workflow_dispatch', 'push'):
        for lane in ('all', 'windows', 'linux', 'arm-macos-ios', None):
            for runner in ('Windows', 'Linux', 'macOS'):
                for value in (None, False, True):
                    effective = value if event == 'workflow_dispatch' else None
                    flag = '--observe-input-consumption' if runner == 'Windows' and effective is True else ''
                    expected = event == 'workflow_dispatch' and runner == 'Windows' and value is True
                    assert bool(flag) == expected
                    command = (COMMAND.decode().strip() + (' ' + flag if flag else ''))
                    assert command.count('--observe-input-consumption') == int(expected)
                    assert '--input-schedule' not in command
                    assert '--fire-capture-delay' not in command
                    cases.append({'event': event, 'lane': lane, 'runner_os': runner,
                                  'declared_boolean': value, 'effective_flag': flag})
    before = source_tree(args.repo, BASE)
    after = source_tree(args.repo, ADAPTER)
    changed = sorted(path for path in before.keys() | after.keys() if before.get(path) != after.get(path))
    assert changed == [WORKFLOW], changed
    assert before[WORKFLOW]['mode'] == after[WORKFLOW]['mode'] == '100644'
    result = {'source': source, 'adapter': ADAPTER, 'original': BASE,
              'scope': 'Pure source/byte/context model; no Actions or native execution',
              'workflow_sha256': sha(candidate), 'original_sha256': sha(original),
              'reverse_sha256': sha(recovered), 'original_bytes': len(original),
              'candidate_bytes': len(candidate), 'non_document_paths_before': len(before),
              'non_document_paths_after': len(after), 'changed_non_document_paths': changed,
              'context_model_cases': len(cases), 'context_model': cases,
              'whole_original_workflow_recovered': True}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'context_model'}, indent=2))


if __name__ == '__main__':
    main()
