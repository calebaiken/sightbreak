"""Reproduce the Linux CI mock-platform bug using actual POSIX-initialized stdlib.

This is a source/synthetic platform control on approved Windows CPython 3.13.15.
It is not actual Linux, Python 3.12, Godot, import/export, network, or DB execution.
"""
import hashlib
import inspect
import io
import json
import os
import pathlib
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import Mock, patch

ROOT = Path(r'C:\Users\blith\AppData\Local\Temp\opencode\sightbreak-v3')
OUT = Path(__file__).resolve().parent
if sys.version_info[:3] != (3, 13, 15) or sys.executable != r'C:\Users\blith\AppData\Local\Temp\opencode\sightbreak-tools\python\cpython-3.13.15-windows-x86_64-none\python.exe':
    raise RuntimeError('Use the exact approved interpreter')
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / 'scripts'))
import matrix_process
import test_matrix_process

source = inspect.getsource(sys.modules[pathlib.Path.__module__])
linux_pathlib = types.ModuleType('pathlib._critic_linux')
linux_pathlib.__package__ = 'pathlib'
with patch.object(os, 'name', 'posix'):
    exec(compile(source, '<isolated-POSIX-pathlib>', 'exec'), linux_pathlib.__dict__)
# Both modules share one POSIX OS identity, just as on Linux.  Host OS identity
# stays untouched while the real existing test executes and mutates this copy.
linux_os = types.SimpleNamespace(**{**vars(os), 'name': 'posix'})
linux_pathlib.os = linux_os
errors = []
original_error = matrix_process.harness_error
def retain_error(log, error):
    errors.append(str(error))
    return original_error(log, error)

trace = io.StringIO()
with patch.object(matrix_process, 'Path', linux_pathlib.Path), \
        patch.object(matrix_process, 'os', linux_os), \
        patch.object(matrix_process, 'harness_error', side_effect=retain_error):
    result = unittest.TextTestRunner(stream=trace, verbosity=2).run(
        unittest.TestSuite([test_matrix_process.SupervisorTests('test_parent_keeps_actual_exit')]))
with (OUT / 'linux-pathlib-repro.log').open('x', encoding='utf-8') as stream:
    stream.write(trace.getvalue())
    stream.write('\nCaptured actual run_process HARNESS_ERROR values:\n')
    stream.write(json.dumps(errors, indent=2) + '\n')

# Demonstrate the minimal test-only boundary without modifying repository code:
# replace only matrix_process.os, instead of mutating shared os.name.
receipt = OUT / 'linux-pathlib-local-os.process.json'
job = Mock()
job.name = 'fixture-job'
job.active.return_value = 0
process = Mock(returncode=0)
process.poll.return_value = 0
def wait(**kwargs):
    with receipt.open('x', encoding='utf-8') as stream:
        json.dump({'complete': True, 'exit': 7, 'errors': []}, stream)
process.wait.side_effect = wait
log = io.StringIO()
with patch.object(matrix_process, 'Path', linux_pathlib.Path), \
        patch.object(matrix_process, 'os', types.SimpleNamespace(**{**vars(linux_os), 'name': 'nt'})), \
        patch.object(matrix_process, 'WindowsJob', return_value=job), \
        patch.object(matrix_process.subprocess, 'Popen', return_value=process) as launch:
    safe_code = matrix_process.run_process(['not-executed'], cwd=OUT, env={}, log=log,
                                          result_path=receipt, timeout=1)
report = {
    'scope': 'Actual existing test + actual POSIX-initialized CPython 3.13.15 pathlib, linked private OS namespace; NOT actual Linux or workflow Python 3.12',
    'python': sys.executable, 'version': sys.version,
    'stdlib_module': pathlib.Path.__module__,
    'stdlib_source_sha256': hashlib.sha256(source.encode()).hexdigest(),
    'existing_test': 'test_matrix_process.SupervisorTests.test_parent_keeps_actual_exit',
    'tests_run': result.testsRun, 'errors': len(result.errors), 'failures': len(result.failures),
    'captured_harness_errors': errors,
    'defect_reproduced': not result.wasSuccessful() and any('WindowsPath' in error for error in errors),
    'module_local_os_comparison': {'returned_exit': safe_code, 'log': log.getvalue(),
                                   'mock_launch_calls': launch.call_count,
                                   'job_stop_calls': job.stop.call_count,
                                   'passed': safe_code == 7 and not log.getvalue() and launch.call_count == 1},
}
with (OUT / 'linux-pathlib-repro.json').open('x', encoding='utf-8') as stream:
    json.dump(report, stream, indent=2)
    stream.write('\n')
print(json.dumps(report, indent=2))
raise SystemExit(1 if report['defect_reproduced'] else 0)
