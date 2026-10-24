#!/usr/bin/env python3
"""Read-only pre-run source binding; launches no engine or workflow."""
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SOURCE = 'c32415148db1f110bbc7eadfca3793d4693429ff'
QUALIFIER = 'qualifier/windows-collector-c324-20261024'
WORKFLOW = '.github/workflows/desktop-alpha.yml'
PREVIOUS = '49ae54b0e4f5d880bdf06e4eb783a616b2dff684'
ROOT_RECEIPT = '817f7a831aa7b36f8181c8fcf8a64fb87a9d403b'
ROOT_INTEGRATION = 'b436a641'


def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args])


def inventory(ref):
    result = {}
    for row in git('ls-tree', '-rz', ref).split(b'\0'):
        if not row:
            continue
        metadata, raw_path = row.split(b'\t', 1)
        path = raw_path.decode()
        if path.startswith('docs/'):
            continue
        mode, kind, blob = metadata.decode().split()
        data = git('cat-file', '-p', blob)
        result[path] = dict(mode=mode, kind=kind, blob=blob,
                            size=len(data), sha256=hashlib.sha256(data).hexdigest())
    return result


def main():
    original = inventory(SOURCE)
    current = inventory('HEAD')
    assert len(original) == 507 and original == current
    assert git('diff', '--name-only', SOURCE, '--', '.', ':!docs') == b''
    assert git('diff', '--cached', '--name-only', '--', '.', ':!docs') == b''
    bindings = {}
    for path, expected in original.items():
        actual = ROOT / path
        assert expected['kind'] == 'blob' and actual.is_file() and not actual.is_symlink(), path
        digest = hashlib.sha256(actual.read_bytes()).hexdigest()
        assert digest == expected['sha256'], path
        bindings[path] = expected
    connector = json.loads((HERE / 'connector-prerun-source.json').read_text())
    fetched = connector['workflow']['value']['structuredContent']
    workflow_bytes = fetched['content'].encode('utf-8')
    assert fetched['sha'] == original[WORKFLOW]['blob']
    assert workflow_bytes == git('show', SOURCE + ':' + WORKFLOW)
    assert hashlib.sha256(workflow_bytes).hexdigest() == '5f59b1e2eb4d1b945c0bf3958d403d3d0166ae7ce8e01a5488e29e9171b62c7a'
    remote = git('ls-remote', '--exit-code', 'origin', 'refs/heads/' + QUALIFIER).decode()
    assert remote == SOURCE + '\trefs/heads/' + QUALIFIER + '\n'
    assert inventory(ROOT_INTEGRATION) == original
    receipt_bytes = git('show', ROOT_RECEIPT + ':docs/reports/gauntlet/windows-collector-actual-20261024/ROOT_QUALIFIER_CREATION.json')
    root_receipt = json.loads(receipt_bytes)
    assert root_receipt['source'] == SOURCE and root_receipt['branch'] == QUALIFIER
    assert root_receipt['absence']['exit_code'] == 0 and root_receipt['absence']['output'] == ''
    assert root_receipt['creation']['arguments'] == dict(repository_full_name='calebaiken/sightbreak', branch_name=QUALIFIER, sha=SOURCE)
    assert root_receipt['creation']['result']['isError'] is False
    assert root_receipt['readback']['exit_code'] == 0 and root_receipt['readback']['output'] == remote
    assert root_receipt['workflow_readback']['sha256'] == hashlib.sha256(workflow_bytes).hexdigest()
    reader_paths = [path for path in original if 'consumption' in path or 'input_trace' in path]
    assert reader_paths == [], reader_paths
    match = (ROOT / 'game/scripts/gameplay/match.gd').read_text()
    hooks = []
    function = ''
    for number, line in enumerate(match.splitlines(), 1):
        if line.startswith('func ') or line.startswith('static func '):
            function = line.split('func ', 1)[1].split('(', 1)[0]
        if 'INPUT_OBSERVATION_HOOK' in line:
            hooks.append(dict(line=number, function=function, source=line.strip()))
    report = dict(scope='Read-only exact source/workflow preparation; no native acceptance',
                  source=SOURCE, head=git('rev-parse', 'HEAD').decode().strip(),
                  qualifier=QUALIFIER, actual_remote_readback=remote,
                  workflow=dict(path=WORKFLOW, git_blob=fetched['sha'],
                                decoded_bytes=len(workflow_bytes),
                                sha256=hashlib.sha256(workflow_bytes).hexdigest(),
                                exact_connector_bytes_equal_source=True),
                  non_document_count=len(original), full_source_inventory=bindings,
                  all_materialized_source_bytes_equal=True, reader_paths=reader_paths,
                  game_tree=git('rev-parse', SOURCE + ':game').decode().strip(),
                  uid_count=sum(path.startswith('game/') and path.endswith('.uid') for path in original),
                  collector_hooks=hooks,
                  source_unchanged_from_preregistration=True,
                  expected_native_total=29567, expected_movement=742,
                  expectations_are_not_execution=True,
                  root_integration=dict(commit=git('rev-parse', ROOT_INTEGRATION).decode().strip(), all_non_doc_objects_equal=True),
                  root_qualifier_receipt=dict(commit=ROOT_RECEIPT, sha256=hashlib.sha256(receipt_bytes).hexdigest(), data=root_receipt),
                  baseline=PREVIOUS)
    (HERE / 'source-binding.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({key: report[key] for key in ('source', 'head', 'non_document_count', 'workflow', 'game_tree', 'uid_count')}))


if __name__ == '__main__':
    main()
