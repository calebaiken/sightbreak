#!/usr/bin/env python3
"""Actual native output plus scoped finalization faults; no game-source edits."""
import argparse
from contextlib import ExitStack
import json
from pathlib import Path
import shutil
from unittest.mock import patch

import run_native_regressions as native


def control(output, fault=None, native_failure=False):
    runner = native.NativeSceneSuites(output)
    observed_error = original_error = None
    namespace = private = real_temporary_cleanup = None
    real_rmtree, real_inventory = shutil.rmtree, native.inventory
    native_failure_receipt = None
    with ExitStack() as patches:
        try:
            with runner:
                success = runner.run('peer_lifecycle')
                assert success['exit'] == 0 and success['clean_log']
                namespace = next(iter(runner.user_roots))
                private = Path(runner.temporary.name)
                real_temporary_cleanup = runner.temporary.cleanup
                if fault == 'namespace':
                    def blocked_namespace(path, *args, **kwargs):
                        if Path(path) == namespace:
                            raise PermissionError('Control injected namespace cleanup failure')
                        return real_rmtree(path, *args, **kwargs)
                    patches.enter_context(patch.object(shutil, 'rmtree', blocked_namespace))
                elif fault == 'temporary':
                    def blocked_temporary():
                        raise PermissionError('Control injected temporary-project cleanup failure')
                    patches.enter_context(patch.object(runner.temporary, 'cleanup', blocked_temporary))
                elif fault == 'inventory':
                    def blocked_inventory(path):
                        if Path(path) == runner.source:
                            raise PermissionError('Control injected source-inventory read failure')
                        return real_inventory(path)
                    patches.enter_context(patch.object(native, 'inventory', blocked_inventory))
                if native_failure:
                    script = runner.output / 'intentional_native_failure.gd'
                    script.write_text('extends SceneTree\nfunc _initialize() -> void:\n    push_error("Intentional native cleanup control failure")\n    quit(9)\n', encoding='utf-8')
                    native_failure_receipt = runner.execute('intentional-native-failure', ['--headless', '--script', str(script)], 120)
                    assert native_failure_receipt['exit'] == 9 and not native_failure_receipt['clean_log']
                    original_error = RuntimeError('Actual native cleanup control exited 9; raw output retained')
                    raise original_error
        except BaseException as error:
            observed_error = error
    try:
        receipt = json.loads((runner.output / 'isolation.json').read_text(encoding='utf-8'))
        assert len(receipt['cleanup']) == len(runner.user_roots) > 0
        assert receipt['cleanup'][0]['user_namespace'] == str(namespace)
        expected_failure = fault is not None or native_failure
        assert receipt['passed'] is not expected_failure
        if not expected_failure:
            assert observed_error is None and receipt['failure'] is None
            assert receipt['finalization_failures'] == []
        else:
            assert observed_error is not None
            assert receipt['failure']['type'] == type(observed_error).__name__
            assert receipt['failure']['message'] == str(observed_error)
            assert receipt['finalization_failures']
        if native_failure:
            assert observed_error is original_error, 'Cleanup replaced the original native failure'
            assert native_failure_receipt['exit'] == 9 and not native_failure_receipt['clean_log']
        if fault == 'namespace':
            assert namespace.exists() and not receipt['cleanup'][0]['removed']
            assert receipt['cleanup'][0]['error']['type'] == 'PermissionError'
            assert receipt['temporary_project_removed'] and not private.exists()
        elif fault == 'temporary':
            assert not namespace.exists() and receipt['cleanup'][0]['removed']
            assert private.exists() and not receipt['temporary_project_removed']
            assert receipt['temporary_project_cleanup_error']['type'] == 'PermissionError'
        else:
            assert not namespace.exists() and receipt['cleanup'][0]['removed']
            assert receipt['temporary_project_removed'] and not private.exists()
        if fault == 'inventory':
            assert not receipt['source_resources_unchanged']
            assert receipt['failure']['stage'] == 'source_resource_inventory'
        result = {'fault': fault, 'actual_native_failure': native_failure_receipt,
                  'raised': None if observed_error is None else {'type': type(observed_error).__name__, 'message': str(observed_error)},
                  'passed': receipt['passed'], 'failure': receipt['failure'],
                  'cleanup': receipt['cleanup'], 'temporary_project_removed': receipt['temporary_project_removed'],
                  'finalization_failures': receipt['finalization_failures'], 'control_assertions_passed': True}
    finally:
        # Release only these controls' registered resources after preserving the
        # failed receipt. These removals do not change its observed outcome.
        if namespace is not None and namespace.exists():
            assert namespace.name == runner.namespace
            real_rmtree(namespace)
        if private is not None and private.exists():
            real_temporary_cleanup()
    result['control_teardown_removed_resources'] = not namespace.exists() and not private.exists()
    assert result['control_teardown_removed_resources']
    (runner.output / 'cleanup-control.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    cases = [('success', None, False), ('namespace-failure', 'namespace', False),
             ('temporary-failure', 'temporary', False), ('inventory-failure', 'inventory', False),
             ('native-and-cleanup-failure', 'namespace', True)]
    results = {name: control(args.output / name, fault, native_failure) for name, fault, native_failure in cases}
    (args.output / 'results.json').write_text(json.dumps(results, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(results, indent=2))


if __name__ == '__main__':
    main()
