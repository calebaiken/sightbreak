#!/usr/bin/env python3
"""Replay unchanged critic function ASTs; fake processes only, no native launch.

The critic's full audit intentionally asserts old source bytes and old failures.
We retain it verbatim, and execute its three unchanged function definitions with
instrumentation that records their outcomes for both the rejected and new source.
Only fake-child cleanup is replaced: the old fake child has no failure-path wait
implementation, and using its invented PID for a real kill would be incorrect.
"""
import ast
from contextlib import ExitStack
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import ModuleType
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
FROZEN = '12901729f7be29d0f64d87a0d92219a84500f1a6'
sys.path.insert(0, str(ROOT / 'scripts'))
import linux_profile_overhead as candidate
import test_linux_profile_overhead as supplied

original = (HERE / 'retained-rejection/audit.py').read_bytes()
tree = ast.parse(original)
names = ('dead_display', 'late_condition', 'invalid_cold_clock')
functions = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names]
assert len(functions) == 3
compiled = compile(ast.Module(body=functions, type_ignores=[]), str(HERE / 'retained-rejection/audit.py'), 'exec')
old_bytes = subprocess.check_output(['git', 'show', FROZEN + ':scripts/linux_profile_overhead.py'], cwd=ROOT)
rejected = ModuleType('rejected_linux_profile_overhead')
rejected.__file__ = str(ROOT / 'scripts/linux_profile_overhead.py')
exec(compile(old_bytes, rejected.__file__, 'exec'), rejected.__dict__)

def replay(module):
    namespace = {'d': module, 'supplied': supplied, 'baseline': [supplied.manual_record(i) for i in range(4)],
                 'deepcopy': deepcopy, 'Path': Path, 'tempfile': tempfile, 'ExitStack': ExitStack,
                 'patch': patch, 'hashlib': hashlib}
    exec(compiled, namespace)
    events = {}
    start, run, evaluate = module.NativeRunner.start, module.run_block, module.evaluate
    def observed_start(self):
        try:
            result = start(self)
        except Exception as error:
            events['readiness'] = {'accepted': False, 'error_type': type(error).__name__, 'error': str(error)}
            raise
        events['readiness'] = {'accepted': True}
        return result
    def observed_run(*args, **kwargs):
        summary = run(*args, **kwargs)
        events['deadline'] = {'passed': summary['passed'], 'launched_clients': len(summary['records']),
                              'error': summary.get('error'), 'conditions': [
                                  {'exit_code': row.get('exit_code'), 'timeout': row.get('timeout'),
                                   'timing': row.get('timing'), 'error': row.get('error')}
                                  for row in summary['records']]}
        return summary
    def observed_evaluate(*args, **kwargs):
        try:
            result = evaluate(*args, **kwargs)
        except Exception as error:
            events['cold_endpoint'] = {'accepted': False, 'error_type': type(error).__name__, 'error': str(error)}
            raise
        events['cold_endpoint'] = {'accepted': result['comparable']}
        return result
    def fake_cleanup(process):
        assert 44000 <= process.pid < 44004
        forced = process.returncode is None
        if forced:
            process.returncode = -15
        return {'pid_absent': True, 'group_absent': True, 'forced': forced}
    results = {}
    with ExitStack() as stack:
        stack.enter_context(patch.object(module.NativeRunner, 'start', observed_start))
        stack.enter_context(patch.object(module, 'run_block', observed_run))
        stack.enter_context(patch.object(module, 'evaluate', observed_evaluate))
        stack.enter_context(patch.object(module, 'cleanup', fake_cleanup))
        stack.enter_context(patch.object(module.signal, 'setitimer'))
        # Any missing fake Popen scope is a test failure, never a real spawn.
        stack.enter_context(patch.object(module.subprocess, 'Popen', side_effect=AssertionError('No native process permitted')))
        for name in names:
            try:
                value = namespace[name]()
            except Exception as error:
                results[name] = {'old_falsifier_assertion_still_holds': False,
                                 'exception_type': type(error).__name__, 'exception': str(error)}
            else:
                results[name] = {'old_falsifier_assertion_still_holds': True, 'result': value}
    return {'events': events, 'function_results': results}

before, after = replay(rejected), replay(candidate)
assert all(item['old_falsifier_assertion_still_holds'] for item in before['function_results'].values()), before
assert before['events']['readiness']['accepted'] is True
assert before['events']['deadline']['passed'] is True and before['events']['deadline']['launched_clients'] == 4
assert before['events']['cold_endpoint']['accepted'] is True
assert after['events']['readiness']['accepted'] is False
assert after['events']['deadline']['passed'] is False and after['events']['deadline']['launched_clients'] == 1
assert after['events']['deadline']['conditions'][0]['timeout'] is True
assert after['events']['cold_endpoint']['accepted'] is False

result = {'rejected_source_commit': FROZEN, 'rejected_controller_sha256': hashlib.sha256(old_bytes).hexdigest(),
          'candidate_controller_sha256': candidate.digest(ROOT / 'scripts/linux_profile_overhead.py'),
          'unchanged_critic_audit_sha256': hashlib.sha256(original).hexdigest(),
          'critic_function_ast_segments_unchanged': True,
          'helper_note': 'Maintained manual_record adds timing evidence; other original synthetic fixture data remain. Fake cleanup replaces invented-PID teardown only. Virtual timers are mocked; no native process or clock delay.',
          'rejected_source': before, 'corrected_source': after,
          'engine_import_compile_uid_export_profiler_native_ocr_ci_runs': 0}
candidate.write(HERE / 'replay.json', candidate.safe_failure_report(result))
print(json.dumps(result, indent=2, allow_nan=False))
