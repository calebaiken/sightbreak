"""Read-only cross-check of retained PostgreSQL qualification evidence.

Runs no migration, pytest, application, game or SQL. Docker calls select only
non-secret image fields or test absence of exact owned resources.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import socket
import subprocess
from datetime import datetime, timezone
from pathlib import Path
import xml.etree.ElementTree as ET


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_json(path):
    return json.loads(path.read_text())


def stat(pid):
    try:
        tail = Path(f'/proc/{pid}/stat').read_text().rsplit(')', 1)[1].split()
    except FileNotFoundError:
        return None
    return dict(pid=pid, state=tail[0], ppid=int(tail[1]), pgrp=int(tail[2]),
                start_ticks=int(tail[19]))


def run(args, cwd=None):
    result = subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=30)
    return dict(argv=args, exit_code=result.returncode, stdout=result.stdout, stderr=result.stderr)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    before = read_json(args.run / 'source-before.json')
    after = read_json(args.run / 'source-after.json')
    assert before == after and before['status'] == ''
    assert before['head'] == '48da99428d01d9ea8164457428643aa740b0eacd'
    assert before['trees'] == before['base_trees']
    base = 'a3b7070f7739ae854e643f905230ae2b6f1a85cb'

    def git(*argv):
        r = subprocess.run(['git', *argv], cwd=args.source, capture_output=True, check=True)
        return r.stdout

    paths = git('ls-tree', '-r', '--name-only', before['head'], '--',
                'backend', 'game', 'scripts', 'server', '.github', '.claude').decode().splitlines()
    hashes = {path: sha((args.source / path).read_bytes()) for path in paths}
    assert len(hashes) == before['production_file_count']
    assert sha(json.dumps(hashes, sort_keys=True).encode()) == before['production_content_sha256']
    assert {p: h for p, h in hashes.items() if p.startswith('backend/')} == before['backend_sha256']
    for name, tree in before['trees'].items():
        assert git('rev-parse', f'{base}:{name}').decode().strip() == tree
        assert git('rev-parse', f'{before["head"]}:{name}').decode().strip() == tree
    for name, digest in before['harness_sha256'].items():
        assert sha((args.source / name).read_bytes()) == digest
        assert sha(git('show', f'{before["head"]}:{name}')) == digest
    backend_base = git('rev-parse', 'b09cfe1:backend').decode().strip()
    assert backend_base == before['trees']['backend']

    # Build the expected complete node set directly from unchanged AST literals.
    tree = ast.parse((args.source / 'backend/tests/test_economy.py').read_text())
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)
                 and node.name.startswith('test_')]
    expected = []
    for node in functions:
        params = [decorator for decorator in node.decorator_list
                  if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute)
                  and decorator.func.attr == 'parametrize']
        if not params:
            expected.append('tests/test_economy.py::' + node.name)
        else:
            assert len(params) == 1 and not params[0].keywords
            for value in ast.literal_eval(params[0].args[1]):
                parts = value if isinstance(value, tuple) else (value,)
                expected.append('tests/test_economy.py::' + node.name +
                                '[' + '-'.join(str(part) for part in parts) + ']')
    assert len(functions) == 44 and len(expected) == len(set(expected)) == 61
    collection = (args.run / 'collection.log').read_text()
    collected = [line for line in collection.splitlines() if line.startswith('tests/test_economy.py::')]
    stdout = (args.run / 'pytest.log').read_text()
    passed = re.findall(r'^(tests/test_economy.py::\S+)\s+PASSED\s+\[', stdout, re.M)
    summary = re.findall(r'^PASSED (tests/test_economy.py::\S+)$', stdout, re.M)
    junit = ET.parse(args.run / 'pytest-junit.xml').getroot()
    junit_nodes = ['tests/test_economy.py::' + item.attrib['name'] for item in junit.iter('testcase')]
    assert expected == collected == passed == summary == junit_nodes
    assert not any(list(junit.iter(name)) for name in ('failure', 'error', 'skipped'))
    suites = list(junit.iter('testsuite'))
    assert len(suites) == 1
    assert {key: suites[0].get(key) for key in ('tests', 'failures', 'errors', 'skipped')} == {
        'tests': '61', 'failures': '0', 'errors': '0', 'skipped': '0'}
    assert '61 passed, 1 warning in 6.43s' in stdout
    assert '61 tests collected' in collection
    assert 'StarletteDeprecationWarning' in stdout
    assert (args.run / 'migration.log').read_text().strip() == 'PostgreSQL schema migrated to version 4'
    schema = (args.run / 'schema-after-migration.log').read_text()
    assert 'PostgreSQL database dump' in schema and 'CREATE TABLE public.players' in schema

    state = read_json(args.run / 'state.json')
    steps = {step['name']: step for step in state['steps']}
    assert not any('failure' in key for key in state)
    for step in state['steps']:
        assert not step['timed_out'] and not step['remaining_live_group_members']
        expected_exit = 1 if step['name'] in ('container-absence', 'volume-absence') else (
            2 if step['name'] in ('readiness-00', 'readiness-01') else 0)
        assert step['exit_code'] == expected_exit
    for name, bound in [('migration', 60), ('collection', 60), ('pytest', 300)]:
        assert steps[name]['timeout_seconds'] == bound
        assert steps[name]['duration_seconds'] < bound
    assert steps['pytest']['argv'][3:] == ['pytest', '-vv', '-rA', '-p', 'no:cacheprovider',
        '--junitxml=' + str(args.run / 'pytest-junit.xml'), 'tests/test_economy.py']
    order = [step['name'] for step in state['steps']]
    assert order.index('identity-before-migration-container-sql') < order.index('migration')
    assert order.index('identity-before-tests-container-sql') < order.index('pytest')
    assert order.index('identity-after-tests-container-sql') > order.index('pytest')

    owned = read_json(args.run / 'container-before.json')
    assert owned == read_json(args.run / 'container-before-cleanup.json')
    label = 'io.sightbreak.qualification'
    assert owned['labels'] == {label: state['run'], 'io.sightbreak.owner': 'backend_regression_builder'}
    assert owned['name'] == '/' + state['run']
    assert owned['ports'] == {'5432/tcp': [{'HostIp': '127.0.0.1', 'HostPort': '32773'}]}
    assert owned['image_id'] == 'sha256:327daa8fae7178d61f93142f146b098467b345e10997b9eb79f63bd58e5c8f3c'
    identities = []
    for phase in ['before-migration', 'before-tests', 'after-tests']:
        record = read_json(args.run / f'identity-{phase}.json')
        internal = (args.run / f'identity-{phase}-container-sql.log').read_text().strip().split('|')
        assert record['database'] == internal[0] == state['database']
        assert record['database'].endswith('_test')
        assert record['role'] == internal[1] == 'sb_regression'
        assert record['verified_container_id'] == owned['id']
        assert record['external_host'] == '127.0.0.1' and record['external_port'] == 32773 != 55432
        assert record['identity_checks_passed'] is True
        assert record['server_port'] == 5432 and internal[4] == '5432'
        assert record['system_identifier'] == internal[6] == '7699384166174421036'
        assert record['postmaster_started'] == internal[5]
        assert record['version'] == internal[2] and record['version'].startswith('PostgreSQL 17.11 ')
        identities.append(record)
    assert len({row['system_identifier'] for row in identities}) == 1

    # Observe only the exact disposable resources after the builder's cleanup.
    # Never inspect environment or process command lines.
    docker = ['docker', '--host=unix:///var/run/docker.sock']
    observations = []
    attempts = [args.report / 'attempt-1-identity-rejected', args.report / 'attempt-2-startup-rejected', args.run]
    failures = []
    for attempt in attempts:
        receipt = read_json(attempt / 'state.json')
        pre = read_json(attempt / 'container-before.json')
        cleanup = read_json(attempt / 'cleanup.json')
        assert cleanup['container_absent'] and cleanup['volume_absent'] and cleanup['postmaster_identity_gone']
        assert cleanup['listener_absent'] and cleanup['label_containers_absent']
        assert cleanup['port_connect_ex'] != 0
        assert read_json(attempt / 'source-before.json') == read_json(attempt / 'source-after.json')
        queries = [('container', ['inspect', '--format', '{{.Id}}', pre['id']], 1),
                   ('volume', ['volume', 'inspect', '--format', '{{.Name}}', receipt['run'] + '-data'], 1),
                   ('label', ['ps', '-aq', '--filter', f'label={label}={receipt["run"]}'], 0)]
        evidence = dict(run=receipt['run'], checked_utc=datetime.now(timezone.utc).isoformat(), docker=[])
        for name, command, exit_code in queries:
            result = run(docker + command)
            assert result['exit_code'] == exit_code
            if name == 'label':
                assert not result['stdout'].strip()
            evidence['docker'].append(result)
        pid_receipt = cleanup['postmaster_before']
        current = stat(pid_receipt['pid'])
        assert current is None or current['start_ticks'] != pid_receipt['start_ticks']
        evidence['postmaster_current'] = current
        port = int(pre['ports']['5432/tcp'][0]['HostPort'])
        with socket.socket() as sock:
            sock.settimeout(1)
            connect_result = sock.connect_ex(('127.0.0.1', port))
        assert connect_result != 0
        listener = run(['ss', '-ltnp', f'sport = :{port}'])
        assert listener['exit_code'] == 0 and len(listener['stdout'].strip().splitlines()) == 1
        evidence.update(port=port, connect_ex=connect_result, listener=listener)
        alive = []
        for process in Path('/proc').iterdir():
            if process.name.isdigit():
                now = stat(int(process.name))
                if now and now['state'] != 'Z' and now['pgrp'] in {step['process']['pgrp'] for step in receipt['steps'] if step['process']}:
                    alive.append(now)
        assert not alive
        evidence['live_recorded_child_group_members'] = alive
        observations.append(evidence)
        if attempt != args.run:
            assert 'failure' in receipt and not (attempt / 'migration.log').exists()
            assert not (attempt / 'pytest.log').exists()
            failures.append(dict(run=receipt['run'], failure=receipt['failure'],
                                 source_head=read_json(attempt / 'source-before.json')['head']))
    manifest_counts = {}
    for archive in [args.report / name for name in ('attempt-1-identity-rejected', 'attempt-2-startup-rejected', 'attempt-3')]:
        lines = (archive / 'SHA256SUMS').read_text().splitlines()
        manifest_names = set()
        for line in lines:
            digest, name = line.split('  ', 1)
            assert len(digest) == 64 and sha((archive / name).read_bytes()) == digest
            manifest_names.add(name)
        assert manifest_names == {str(path.relative_to(archive)) for path in archive.rglob('*')
                                  if path.is_file() and path.name != 'SHA256SUMS'}
        manifest_counts[archive.name] = len(lines)
    raw_names = {str(path.relative_to(args.run)) for path in args.run.rglob('*') if path.is_file()}
    archive_names = {str(path.relative_to(args.report / 'attempt-3'))
                     for path in (args.report / 'attempt-3').rglob('*') if path.is_file() and path.name != 'SHA256SUMS'}
    assert raw_names == archive_names
    for name in raw_names:
        assert (args.run / name).read_bytes() == (args.report / 'attempt-3' / name).read_bytes()
    builder_commit = '79c52a97c289756452a1a1da453db2754afa0748'
    changed = git('diff', '--name-only', base, builder_commit).decode().splitlines()
    assert changed and all(path.startswith('docs/reports/gauntlet/m3-backend-regression/') for path in changed)
    image = run(docker + ['image', 'inspect', '--format', '{{json .Id}}\n{{json .RepoDigests}}', owned['image_id']])
    assert image['exit_code'] == 0
    assert 'postgres@sha256:2d2b8998d31037bf721cfdf764d76ba74171b4fab3431b7f72c27c56ddbdf9e3' in image['stdout']
    result = dict(verdict='PASS: bounded unchanged PostgreSQL regression', source=before,
                  backend_matches_b09cfe1=backend_base, case_count=len(expected), function_count=len(functions),
                  complete_expected_cases=expected, junit_attributes=suites[0].attrib,
                  steps={name: steps[name] for name in ('migration', 'collection', 'pytest')},
                  native_identity_receipts=identities, preserved_failures=failures,
                  builder_evidence_commit=builder_commit, builder_changed_paths=changed,
                  archive_manifest_counts=manifest_counts, archived_third_attempt_equals_raw=True,
                  direct_resource_absence_observations=observations, cached_image_observation=image,
                  raw_file_sha256={str(path.relative_to(args.run)): sha(path.read_bytes())
                                   for path in sorted(args.run.rglob('*')) if path.is_file()},
                  independent_live_sql=False, runtime_duplicated=False,
                  checked_utc=datetime.now(timezone.utc).isoformat())
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps({key: result[key] for key in ('verdict', 'case_count', 'function_count',
          'backend_matches_b09cfe1', 'independent_live_sql', 'runtime_duplicated')}, indent=2))


if __name__ == '__main__':
    main()
