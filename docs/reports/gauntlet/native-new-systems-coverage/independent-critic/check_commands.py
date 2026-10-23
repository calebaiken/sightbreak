#!/usr/bin/env python3
"""Exercise the real runner's selection/error paths with all native calls mocked."""
import ast
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from unittest.mock import Mock, patch

ROOT = Path('/workspace/sightbreak-native-new-systems-coverage')
BASE = 'ecc2690dc783a3243291f8ac3438d44fe0151117'
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('native_coverage_candidate_review', ROOT / 'scripts/run_native_regressions.py')
candidate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate)
base_source = subprocess.check_output(['git', '-C', str(ROOT), 'show', BASE + ':scripts/run_native_regressions.py']).decode()
base_ast = ast.parse(base_source)
old_suites = ast.literal_eval(next(node.value for node in base_ast.body if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'SUITES' for t in node.targets)))


def run_suite(name, *, exit_code=0, clean=True, stale=False):
    with tempfile.TemporaryDirectory(prefix='native-coverage-critic-') as temporary:
        parent = Path(temporary)
        userdata = parent / 'owned-userdata'
        userdata.mkdir()
        sentinel = userdata / 'sentinel.txt'
        sentinel.write_bytes(b'preserved-output')
        output = parent / 'evidence'
        output.mkdir()
        runner = object.__new__(candidate.NativeSceneSuites)
        runner.output = output
        runner.receipts = []
        before = {'profile_exists': stale, 'diagnostics_exist': False}
        runner.prepare = Mock(return_value=before)
        runner.probe = Mock(return_value={'user_data_dir': str(userdata)})
        runner.execute = Mock(return_value={'exit': exit_code, 'clean_log': clean})
        failure = None
        try:
            runner.run(name)
        except RuntimeError as error:
            failure = str(error)
        if stale:
            assert failure and 'Refusing existing suite state' in failure
            assert not runner.execute.called and sentinel.read_bytes() == b'preserved-output'
            return {'suite': name, 'stale_rejected_before_execute': True}
        args, kwargs = runner.execute.call_args
        assert not kwargs and args[0] == name and args[2] == 120
        assert runner.probe.call_args.args == ('after-' + name,)
        assert (output / (name + '-userdata/sentinel.txt')).read_bytes() == b'preserved-output'
        assert json.loads((output / 'results.json').read_text())[0]['suite'] == name
        assert bool(failure) == (exit_code != 0 or not clean)
        return {'suite': name, 'arguments': args[1], 'timeout': args[2], 'failure': failure,
                'results_and_userdata_retained': True}


def main():
    assert len(old_suites) == 12
    assert candidate.SUITES == old_suites + ('transaction_journal', 'gunplay_rules')
    assert set(candidate.SUITE_ARGUMENTS) == {'gunplay_rules'}
    records = []
    for suite in candidate.SUITES:
        result = run_suite(suite)
        expected = ['--headless', '--script', 'res://tests/' + suite + '_test.gd']
        if suite == 'gunplay_rules':
            expected = ['--headless', '--audio-driver', 'Dummy', '--script', 'res://tests/gunplay_rules_probe.gd']
        assert result['arguments'] == expected
        records.append(result)
    # Original preparation rejects identifiers before configuration/probing.
    runner = object.__new__(candidate.NativeSceneSuites)
    runner.configure, runner.probe = Mock(), Mock()
    for unknown in ['gunplay_rules_probe', 'transaction_journal_test', 'foreign', '../actor', '']:
        try:
            runner.prepare(unknown)
        except ValueError:
            pass
        else:
            raise AssertionError('Unknown suite admitted: ' + unknown)
    assert not runner.configure.called and not runner.probe.called
    # CLI default and explicit selection use the maintained fourteen; duplicate
    # and unknown choices must reject before any context/native entrypoint.
    cli = {}
    class FakeContext:
        def __init__(self, _output):
            self.report = dict(passed=True, source_resources_unchanged=True, temporary_project_removed=True)
            self.selected = []
        def __enter__(self): return self
        def __exit__(self, *_args): return False
        def run(self, suite): self.selected.append(suite)
    for label, extra, expected in [('default', [], list(candidate.SUITES)),
                                   ('explicit', ['--suites', 'gunplay_rules', 'transaction_journal'], ['gunplay_rules', 'transaction_journal'])]:
        context = FakeContext(None)
        with patch.object(sys, 'argv', ['runner', '--output', '/unused-output', *extra]), \
             patch.object(candidate, 'NativeSceneSuites', return_value=context), patch('builtins.print'):
            assert candidate.main() == 0
        assert context.selected == expected
        cli[label] = context.selected
    for extra in [['--suites', 'actor', 'actor'], ['--suites', 'foreign']]:
        with patch.object(sys, 'argv', ['runner', '--output', '/unused-output', *extra]), \
             patch.object(candidate, 'NativeSceneSuites') as mocked:
            try:
                candidate.main()
            except SystemExit as error:
                assert error.code == 2
            else:
                raise AssertionError('Invalid CLI selection admitted')
        assert not mocked.called
    controls = [run_suite('transaction_journal', exit_code=2),
                run_suite('gunplay_rules', clean=False), run_suite('gunplay_rules', stale=True)]
    # Apart from run(), all methods are unchanged ASTs; raw diff is reviewed too.
    new_ast = ast.parse((ROOT / 'scripts/run_native_regressions.py').read_text())
    def methods(tree):
        node = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'NativeSceneSuites')
        return {n.name: ast.dump(n, include_attributes=False) for n in node.body if isinstance(n, ast.FunctionDef)}
    before, after = methods(base_ast), methods(new_ast)
    assert set(before) == set(after)
    assert all(before[name] == after[name] for name in before if name != 'run')
    return {'comparison_base': BASE, 'original_suites': list(old_suites), 'candidate_suites': list(candidate.SUITES),
            'command_records': records, 'cli': cli, 'unknown_identifiers_rejected_before_configuration': 5,
            'negative_retention_controls': controls, 'all_other_runner_methods_ast_identical': True,
            'native_and_server_entrypoints_launched': 0}


if __name__ == '__main__':
    print(json.dumps(main(), indent=2))
