#!/usr/bin/env python3
"""Targeted trade-read bound and fixture-provenance controls; never runs full suites."""
import argparse
import ast
import difflib
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import tarfile
import time
import xml.etree.ElementTree as ET

import psycopg
from psycopg import sql
from sqlalchemy.engine import make_url

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = '4a8e9ea73aa8b286d9f1751b0a6b485479737294'
CASES = ['test_trade_read_payload_privacy_and_query_budget[40-20]',
         'test_trade_read_payload_privacy_and_query_budget[501-0]']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8', newline='\n')


def git(*args):
    return subprocess.check_output(['git', '-c', 'core.longpaths=true', *args], cwd=ROOT, text=True).strip()


def copy_backend(revision, destination):
    destination.mkdir(parents=True, exist_ok=False)
    archive = subprocess.check_output(['git', 'archive', revision, 'backend'], cwd=ROOT)
    with tarfile.open(fileobj=io.BytesIO(archive)) as stream:
        for member in stream:
            if member.isdir():
                continue
            path = (destination / member.name).resolve()
            assert member.isfile() and path.is_relative_to(destination.resolve())
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(stream.extractfile(member).read())


def fixture_probe(source, fixture_root, expected):
    """Same import precedence as the benchmark; block all DB connects in this probe."""
    calls = []
    def deny_connect(*args, **kwargs):
        calls.append(True)
        raise AssertionError('Fixture import probe must not connect to a database')
    psycopg.connect = deny_connect
    os.environ['DATABASE_URL'] = 'postgresql+psycopg://unused:unused@127.0.0.1:1/import_probe_test'
    spec = importlib.util.spec_from_file_location('trade_benchmark', ROOT / 'scripts/benchmark_trade_reads.py')
    benchmark = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(benchmark)
    sys.path[:0] = [str(source / 'backend'), str(source / 'backend/tests'), str(fixture_root / 'backend/tests')]
    import test_trade_reads as fixture
    receipt = {'source_path': str(source), 'fixture_root': str(fixture_root),
               'actual_module_file': fixture.__file__, 'actual_sha256': sha(Path(fixture.__file__)),
               'expected_sha256': expected, 'database_connect_calls': len(calls)}
    try:
        receipt['checked_identity'] = benchmark.fixture_identity(fixture, expected)
    except RuntimeError:
        receipt['mismatch_rejected'] = True
        print(json.dumps(receipt, indent=2), flush=True)
        raise
    assert not calls
    receipt['mismatch_rejected'] = False
    print(json.dumps(receipt, indent=2), flush=True)


def run_controls(out):
    out.mkdir(parents=True, exist_ok=False)
    commit = git('rev-parse', 'HEAD')
    assert not git('status', '--porcelain', '--', 'backend', 'scripts/benchmark_trade_reads.py',
                   'scripts/check_trade_read_assurance.py'), 'Freeze code before controls'
    assert not git('diff', '--name-only', RUNTIME, commit, '--', 'backend', ':(exclude)backend/tests')
    tracked = git('ls-tree', '-r', '--name-only', commit, '--', 'backend').splitlines()
    before = {name: sha(ROOT / name) for name in tracked}
    frozen = {'commit': commit, 'runtime_reference': RUNTIME,
              'runtime_match_scope': 'backend excluding backend/tests',
              'backend_tree_including_tests': git('rev-parse', commit + ':backend'),
              'backend_files_before': before,
              'harness_sha256': sha(ROOT / 'scripts/benchmark_trade_reads.py'),
              'control_runner_sha256': sha(Path(__file__)),
              'test_fixture_sha256': sha(ROOT / 'backend/tests/test_trade_reads.py'),
              'python': sys.version, 'tests': CASES,
              'full_suites_or_seven_workload_benchmarks_executed': False}
    write(out / 'freeze.json', frozen)
    scratch = out.parent / (out.name + '-scratch-' + secrets.token_hex(4))
    scratch.mkdir(exist_ok=False)
    mutant = scratch / 'batch-5000'
    copy_backend(commit, mutant)
    app = mutant / 'backend/app.py'
    original = app.read_text(encoding='utf-8')
    node = next(n for n in ast.parse(original).body if isinstance(n, ast.FunctionDef) and n.name == 'trades')
    assert sum(isinstance(n, ast.Constant) and n.value == 500 for n in ast.walk(node)) == 4
    segment = ast.get_source_segment(original, node)
    assert segment.count('500') == 4
    mutated = original.replace(segment, segment.replace('500', '5000'), 1)
    app.write_bytes(mutated.encode('utf-8'))
    (out / 'batch-5000.patch').write_text(''.join(difflib.unified_diff(original.splitlines(True),
        mutated.splitlines(True), fromfile='frozen/backend/app.py', tofile='isolated-control/backend/app.py')),
        encoding='utf-8', newline='\n')
    (out / 'batch-5000-app.py.txt').write_bytes(app.read_bytes())
    write(out / 'mutation.json', {'scratch_source': str(mutant), 'copied_commit': commit,
          'frozen_app_sha256': before['backend/app.py'], 'mutant_app_sha256': sha(app),
          'changes': 'Only four constants in trades: both item/player loop steps and slices 500 -> 5000',
          'shipping_app_edited': False})

    admin = make_url(os.environ['SIGHTBREAK_TEST_ADMIN_URL']).set(drivername='postgresql')
    assert admin.get_backend_name() == 'postgresql'
    env = os.environ.copy()
    env.update(PYTHONDONTWRITEBYTECODE='1', SIGHTBREAK_SERVER_ID='local-relay')
    env.pop('SIGHTBREAK_SERVER_KEY', None)
    summaries = []
    for label, source, expected_exit in (('candidate', ROOT, 0), ('batch-5000', mutant, 1)):
        folder = out / label
        folder.mkdir()
        database = 'sightbreak_trade_assurance_' + secrets.token_hex(6) + '_test'
        with psycopg.connect(admin.render_as_string(hide_password=False), autocommit=True) as db:
            version = db.execute('SELECT version()').fetchone()[0]
            db.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(database)))
        test_env = env | {'DATABASE_URL': admin.set(drivername='postgresql+psycopg', database=database).render_as_string(hide_password=False),
                          'PYTHONPATH': os.pathsep.join([str(source / 'backend'), str(source / 'backend/tests')])}
        command = [sys.executable, '-B', '-m', 'pytest', '-p', 'no:cacheprovider', '--import-mode=importlib',
                   '-o', 'junit_family=legacy', '--junitxml=' + str(folder / 'pytest.xml'),
                   '-q', '--tb=short', *['backend/tests/test_trade_reads.py::' + case for case in CASES]]
        receipt = {'command': command, 'cwd': str(source), 'frozen_commit': commit,
                   'app_sha256': sha(source / 'backend/app.py'),
                   'test_fixture_sha256': sha(source / 'backend/tests/test_trade_reads.py'),
                   'database': database, 'postgresql': version, 'expected_exit': expected_exit}
        try:
            start = time.monotonic()
            with (folder / 'pytest.log').open('w', encoding='utf-8', newline='\n') as log:
                result = subprocess.run(command, cwd=source, env=test_env, stdout=log, stderr=subprocess.STDOUT, timeout=120)
            receipt.update(exit=result.returncode, seconds=time.monotonic() - start)
        finally:
            with psycopg.connect(admin.render_as_string(hide_password=False), autocommit=True) as db:
                db.execute(sql.SQL('DROP DATABASE {} WITH (FORCE)').format(sql.Identifier(database)))
            receipt['database_dropped'] = True
            write(folder / 'run.json', receipt)
        assert result.returncode == expected_exit, (label, result.returncode)
        cases = ET.parse(folder / 'pytest.xml').findall('.//testcase')
        assert len(cases) == 2
        for case in cases:
            properties = {p.attrib['name']: p.attrib['value'] for p in case.findall('./properties/property')}
            counts = ast.literal_eval(properties['query_parameter_counts'])
            assert int(properties['query_count']) <= int(properties['query_budget'])
            assert max(counts) == (500 if label == 'candidate' else 1600 if '[40-20]' in case.attrib['name'] else 502)
            failure = case.find('failure')
            assert (failure is None) == (expected_exit == 0)
            if failure is not None:
                assert 'assert all(size <= 500' in (failure.text or '')
            summaries.append({'variant': label, 'test': case.attrib['name'],
                              'old_upper_query_budget_passes': True, 'parameter_counts': counts,
                              'direct_bound_passes': failure is None})
        print(json.dumps({'variant': label, 'exit': result.returncode, 'targeted_cases': len(cases)}), flush=True)
    write(out / 'bound-results.json', summaries)

    mismatch = scratch / 'fixture-mismatch'
    copy_backend(commit, mismatch)
    mismatch_file = mismatch / 'backend/tests/test_trade_reads.py'
    mismatch_file.write_bytes(mismatch_file.read_bytes() + b'\n# Isolated provenance-negative byte change.\n')
    probes = [('fixture-positive', ROOT, ROOT, frozen['test_fixture_sha256'], 0, 'current_import_control'),
              ('fixture-mismatch', mismatch, ROOT, frozen['test_fixture_sha256'], 1, 'source_fixture_shadowing_control')]
    pinned = {}
    for revision in ('701ce2c4d7f8b2872cf1fefa64cb6edd0cd1a3fd', RUNTIME,
                     '8070436f53dd98e9529e8c21ea7b0f7e3ecb6daf'):
        pinned[revision] = scratch / ('pinned-' + revision[:7])
        copy_backend(revision, pinned[revision])
    for round_name, harness, archive in (
        ('round1', RUNTIME, ROOT / 'docs/reports/backend-trade-read-v3'),
        ('round2', '8070436f53dd98e9529e8c21ea7b0f7e3ecb6daf', ROOT / 'docs/reports/backend-trade-read-v3/retention-r2')):
        for role in ('baseline', 'candidate'):
            report_file = archive / (role + '-measurement' if round_name == 'round1' else role) / 'measurement.json'
            report = json.loads(report_file.read_text())
            source_commit = report['source']['commit']
            probes.append((round_name + '-' + role + '-posthoc', pinned[source_commit], pinned[harness],
                           report['fixture_sha256'], 0, 'posthoc_import_replay_not_original_capture'))
    probe_results = []
    for name, source, fixture_root, expected_sha, expected_exit, kind in probes:
        command = [sys.executable, '-B', str(Path(__file__).resolve()), '--probe-fixture', str(source),
                   '--fixture-root', str(fixture_root), '--expected-fixture-sha', expected_sha]
        result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True, timeout=60)
        (out / (name + '-stdout.json')).write_text(result.stdout, encoding='utf-8', newline='\n')
        (out / (name + '-stderr.log')).write_text(result.stderr, encoding='utf-8', newline='\n')
        receipt = {'name': name, 'kind': kind, 'command': command, 'exit': result.returncode,
                   'expected_exit': expected_exit, 'actual': json.loads(result.stdout)}
        probe_results.append(receipt)
        write(out / 'fixture-probes.json', probe_results)
        assert result.returncode == expected_exit
        assert receipt['actual']['database_connect_calls'] == 0
        assert receipt['actual']['mismatch_rejected'] == (expected_exit != 0)
        if expected_exit:
            assert 'Imported fixture byte mismatch' in result.stderr
        print(json.dumps({'probe': name, 'exit': result.returncode, 'kind': kind}), flush=True)
    after = {name: sha(ROOT / name) for name in tracked}
    assert before == after and not git('status', '--porcelain', '--', 'backend', 'scripts')
    write(out / 'completion.json', {'completed': True, 'freeze_commit': commit,
          'candidate_targeted_passes': 2, 'mutant_direct_bound_failures': 2,
          'current_fixture_positive': 1, 'fixture_mismatch_rejected': 1,
          'posthoc_pinned_import_matches': 4, 'posthoc_is_original_capture': False,
          'shipping_and_test_source_bytes_unchanged_during_controls': True,
          'all_created_databases_dropped': True, 'server_stop_or_reconfiguration': False,
          'full_suites_or_seven_workload_benchmarks_executed': False,
          'sol_synthetic_controls_counted_as_executed': False})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path)
    parser.add_argument('--probe-fixture', type=Path)
    parser.add_argument('--fixture-root', type=Path, default=ROOT)
    parser.add_argument('--expected-fixture-sha')
    args = parser.parse_args()
    if args.probe_fixture:
        if not args.expected_fixture_sha:
            parser.error('--expected-fixture-sha is required for an import probe')
        fixture_probe(args.probe_fixture.resolve(), args.fixture_root.resolve(), args.expected_fixture_sha)
    else:
        if args.out is None:
            parser.error('--out is required for targeted controls')
        run_controls(args.out.resolve())
