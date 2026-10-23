#!/usr/bin/env python3
"""Pure fake-process controls. Never starts a process or queries a database."""
import ast
from contextlib import redirect_stdout
from datetime import datetime
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
REVIEW = HERE.parent
EXPECTED = '9cdbbed715f257d76d693e8f8d58cf40fe13ce21c5d6839e5b975c94fcd99f53'
EXPECTED_OLD = 'ca1c8fb7bf5edf8b537fe1e4b132aa0b6c4b559eea1773673ad04e6adcde8824'
sha = lambda raw: hashlib.sha256(raw).hexdigest()
assert sha((REVIEW / 'observe_owned_postgres_v2.py').read_bytes()) == EXPECTED
assert sha((REVIEW / 'observe_owned_postgres.py').read_bytes()) == EXPECTED_OLD


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


observer = load_module('independent_observer', REVIEW / 'observe_owned_postgres_v2.py')
original_controls = load_module('original_controls', REVIEW / 'test_observer_v2.py')
proofs = {}


class MemoryPath:
    def __init__(self, name, files):
        self.name, self.files = name, files

    def __truediv__(self, suffix):
        return MemoryPath(self.name + '/' + suffix, self.files)

    def __str__(self):
        return self.name

    def resolve(self):
        return self

    def mkdir(self, **kwargs):
        pass

    def exists(self):
        return self.name in self.files

    def read_text(self):
        try:
            return self.files[self.name]
        except KeyError:
            raise FileNotFoundError(self.name)

    def read_bytes(self):
        return self.read_text().encode()

    def write_text(self, text):
        self.files[self.name] = text

    def open(self, *args):
        path = self

        class Stream(io.StringIO):
            def flush(self):
                path.write_text(self.getvalue())

            def close(self):
                if not self.closed:
                    self.flush()
                super().close()

        return Stream()


class Child:
    def __init__(self, pid, on_wait, stdout=''):
        self.pid, self.on_wait = pid, on_wait
        self.stdin, self.stdout = io.StringIO(), io.StringIO(stdout)
        self.returncode = None
        self.terminate_calls = self.wait_calls = self.kill_calls = 0

    def poll(self):
        return self.returncode

    def terminate(self):
        self.terminate_calls += 1

    def wait(self, **kwargs):
        self.wait_calls += 1
        self.returncode = 1
        self.on_wait()
        return self.returncode

    def kill(self):
        self.kill_calls += 1


class FakeProcessControls(unittest.TestCase):
    def exercise(self, broken_pipe=False):
        report = dict(postgres_port=12345, container='sightbreak-account-match-0123456789ab',
                      source_commit='a' * 40, game_tree='b' * 40, status='running')
        files = {'run/report.json': json.dumps(report)}
        run, output = MemoryPath('run', files), MemoryPath('output', files)

        def finish():
            report['status'] = 'passed'
            files['run/report.json'] = json.dumps(report)

        checkpoint = '2026-10-22T06:18:50.187242+00:00'
        row = dict(read_only='on', database_utc='2026-10-22T06:18:50.200000+00:00',
                   tables=dict(players=[], ledger=[], rewards=[], operations=[]))
        stream = Child(123456, finish, json.dumps(row) + '\n')
        if broken_pipe:
            class BrokenInput(io.StringIO):
                def write(self, text):
                    raise BrokenPipeError('synthetic outage')
            stream.stdin = BrokenInput()
        else:
            files['run/earned-staged.json'] = json.dumps({'at_utc': checkpoint})
            files['run/duplicate-replayed-unchanged.json'] = json.dumps({'at_utc': checkpoint})

        final = Child(123457, finish)
        final.communicate_calls = 0

        def communicate(*args, **kwargs):
            final.communicate_calls += 1
            if final.communicate_calls == 1:
                raise observer.subprocess.TimeoutExpired('synthetic query', 5,
                                                       output='partial stdout', stderr='partial stderr')
            final.returncode = -9
            return 'retained complete stdout\n', 'retained complete stderr\n'

        final.communicate = communicate
        spawned = []

        def popen(command, **kwargs):
            spawned.append(command)
            return stream if len(spawned) == 1 else final

        inspection = dict(image=observer.IMAGE, auto_remove=True, name='/' + report['container'],
                          ports={'5432/tcp': [{'HostIp': '127.0.0.1', 'HostPort': '12345'}]})
        args = SimpleNamespace(run=run, output=output)
        with patch.object(observer.argparse.ArgumentParser, 'parse_args', return_value=args), \
                patch.object(observer.subprocess, 'check_output', return_value=json.dumps(inspection)), \
                patch.object(observer.subprocess, 'Popen', side_effect=popen), \
                patch.object(observer.time, 'sleep', return_value=None), redirect_stdout(io.StringIO()):
            observer.main()
        summary = json.loads(files['output/observer-report.json'])
        self.assertEqual(stream.terminate_calls, 1)
        self.assertEqual(stream.wait_calls, 1)
        self.assertTrue(stream.stdin.closed and stream.stdout.closed)
        self.assertTrue(summary['all_psql_children_reaped'])
        self.assertEqual(summary['psql_pids'], [123456] if broken_pipe else [123456, 123457])
        proofs['broken_pipe' if broken_pipe else 'final_query_timeout'] = {
            'summary': summary,
            'captured_output': {key: value for key, value in files.items() if key.startswith('output/')},
            'stream_terminate_calls': stream.terminate_calls, 'stream_wait_calls': stream.wait_calls,
            'final_query_kill_calls': final.kill_calls, 'final_query_communicate_calls': final.communicate_calls}
        return files, summary, final

    def test_outage_child_reaped_and_error_pid_retained(self):
        files, summary, final = self.exercise(broken_pipe=True)
        self.assertEqual(summary['stream_error_types'], ['BrokenPipeError'])
        self.assertEqual(final.communicate_calls, 0)

    def test_timeout_output_retained_and_final_query_rejected(self):
        files, summary, final = self.exercise()
        receipt = json.loads(files['output/post-replay-owned-query.json'])
        self.assertEqual(receipt['status'], 'not_observed')
        self.assertEqual(receipt['error_type'], 'TimeoutExpired')
        self.assertEqual(receipt['returncode'], -9)
        self.assertEqual(final.kill_calls, 1)
        self.assertEqual(final.communicate_calls, 2)
        self.assertEqual(files['output/post-replay-query-stdout.txt'], 'retained complete stdout\n')
        self.assertEqual(files['output/post-replay-query-stderr.txt'], 'retained complete stderr\n')
        self.assertEqual(summary['post_replay_owned_query_status'], 'not_observed')


oracle_tree = ast.parse((REVIEW / 'recompute_current_run_v2.py').read_text())
start = next(i for i, node in enumerate(oracle_tree.body)
             if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'parse_time'
                                                     for t in node.targets))
end = next(i for i in range(start + 1, len(oracle_tree.body))
           if isinstance(oracle_tree.body[i], ast.Assert)
           and 'Historical payload' in ast.unparse(oracle_tree.body[i]))
# Execute only the temporal acceptance fragment. Do not import or run its SQLite code.
oracle_code = compile(ast.Module(body=oracle_tree.body[start:end], type_ignores=[]),
                      'recompute_current_run_v2.py:temporal_fragment', 'exec')


class OracleControls(unittest.TestCase):
    def check(self, change=None):
        checkpoint = {'at_utc': '2026-10-22T06:18:50.110000+00:00'}
        checkpoint_raw = json.dumps(checkpoint)
        tables = {'wallets': 'synthetic same tables'}
        committed = [dict(database_utc='2026-10-22T06:18:50.090000+00:00', tables=tables),
                     dict(database_utc='2026-10-22T06:18:50.120000+00:00', tables=tables)]
        final = dict(status='observed', returncode=0, container='synthetic-owned',
                     checkpoint_sha256=sha(checkpoint_raw.encode()), checkpoint_at_utc=checkpoint['at_utc'],
                     requested_at_utc='2026-10-22T06:18:50.111000+00:00',
                     completed_at_utc='2026-10-22T06:18:50.115000+00:00',
                     snapshot=dict(read_only='on', database_utc='2026-10-22T06:18:50.112000+00:00', tables=tables))
        if change:
            change(committed, final)
        files = {'run/duplicate-replayed-unchanged.json': checkpoint_raw,
                 'output/post-replay-owned-query.json': json.dumps(final)}
        scope = dict(datetime=datetime, json=json, sha=sha, committed=committed,
                     checkpoints={'duplicate-replayed-unchanged': checkpoint,
                                  'lost-ack-worker-killed': {'at_utc': '2026-10-22T06:18:50.100000+00:00'}},
                     report={'container': 'synthetic-owned'},
                     run=MemoryPath('run', files), observations=MemoryPath('output', files))
        exec(oracle_code, scope)

    def test_two_independent_boundaries_accept_synthetic_fixture(self):
        self.check()

    def test_replay_tag_cannot_replace_later_stream_row(self):
        def mutate(rows, final):
            rows.pop()
            rows[0]['checkpoints_seen'] = {'duplicate-replayed-unchanged': final['checkpoint_at_utc']}
        with self.assertRaisesRegex(AssertionError, 'No live SQL sample after duplicate replay'):
            self.check(mutate)

    def test_late_sql_cannot_replace_late_query_request(self):
        with self.assertRaises(AssertionError):
            self.check(lambda rows, final: final.update(requested_at_utc='2026-10-22T06:18:50.109000+00:00'))

    def test_failed_explicit_query_rejects_even_with_late_stream_row(self):
        with self.assertRaises(AssertionError):
            self.check(lambda rows, final: final.update(status='not_observed'))

    def test_changed_final_settlement_rejects(self):
        with self.assertRaisesRegex(AssertionError, 'Explicit final owned query changed settlement'):
            self.check(lambda rows, final: final['snapshot'].update(tables={'different': True}))


if __name__ == '__main__':
    suite = unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromModule(original_controls),
                               unittest.defaultTestLoader.loadTestsFromTestCase(FakeProcessControls),
                               unittest.defaultTestLoader.loadTestsFromTestCase(OracleControls)])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    receipt = dict(status='passed' if result.wasSuccessful() else 'failed', tests_run=result.testsRun,
                   failures=len(result.failures), errors=len(result.errors),
                   observer_v2_sha256=EXPECTED, original_observer_sha256=EXPECTED_OLD,
                   oracle_sha256=sha((REVIEW / 'recompute_current_run_v2.py').read_bytes()),
                   proof_script_sha256=sha(Path(__file__).read_bytes()), fake_process_proofs=proofs,
                   scope='Pure synthetic controls; no actual match qualification or runtime access')
    (HERE / 'proof-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    raise SystemExit(0 if result.wasSuccessful() else 1)
