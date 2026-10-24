"""Bounded serial source/synthetic controls. No engine, network, database, or repo writes.

Run a copy in a NEW external directory using the approved interpreter and -B.
The isolated POSIX pathlib control is a platform mock, not Linux execution.
"""
import hashlib
import inspect
import io
import json
import os
import pathlib
from pathlib import Path
import subprocess
import sys
import time
import types
import unittest
from unittest.mock import Mock, patch

ROOT = Path(r'C:\Users\blith\AppData\Local\Temp\opencode\sightbreak-v3')
OUT = Path(__file__).resolve().parent
APPROVED = r'C:\Users\blith\AppData\Local\Temp\opencode\sightbreak-tools\python\cpython-3.13.15-windows-x86_64-none\python.exe'
if sys.executable != APPROVED or sys.version_info[:3] != (3, 13, 15):
    raise RuntimeError('Use the exact approved CPython 3.13.15')
sys.dont_write_bytecode = True
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
sys.path.insert(0, str(ROOT / 'scripts'))
import godot_process
import matrix_process
import verify_offline_export


def save(name, value):
    with (OUT / name).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')


def ocr_case(name, code, *, budget=5, expected_error=None):
    prefix = OUT / name
    started = time.monotonic()
    error = value = None
    try:
        value = verify_offline_export.ocr_text(
            [APPROVED, '-B', '-c', code], b'critic fixture image',
            started + budget, prefix)
    except Exception as caught:
        error = {'type': type(caught).__name__, 'message': str(caught)}
    row = {'name': name, 'command': [APPROVED, '-B', '-c', code],
           'budget': budget, 'seconds': time.monotonic() - started,
           'returned_text': value, 'error': error,
           'receipt': json.loads(prefix.with_suffix('.process.json').read_text())}
    if expected_error is None:
        row['control_passed'] = error is None and value.strip() == '100 HEALTH'
    else:
        row['control_passed'] = error is not None and expected_error in error['message']
    save(name + '.control.json', row)
    return row


rows = []
rows.append(ocr_case('ocr-success',
    'import sys; assert sys.stdin.buffer.read() == b"critic fixture image"; '
    'print("stderr retained", file=sys.stderr); print("100 HEALTH")'))
rows.append(ocr_case('ocr-exit-3',
    'import sys; print("100 HEALTH"); sys.exit(3)', expected_error='exited 3'))
timeout_late = OUT / 'timeout-late.txt'
rows.append(ocr_case('ocr-timeout',
    'import pathlib, time; print("partial OCR", flush=True); time.sleep(2); '
    f'pathlib.Path({str(timeout_late)!r}).write_text("escaped timeout")',
    budget=.45, expected_error='wall-clock'))

late = OUT / 'descendant-late.txt'
ready = OUT / 'descendant-ready.txt'
child = ('import pathlib, time; '
         f'pathlib.Path({str(ready)!r}).write_text("ready"); '
         'time.sleep(1.2); '
         f'pathlib.Path({str(late)!r}).write_text("escaped descendant")')
parent = ('import pathlib, subprocess, sys, time; '
          f'p=subprocess.Popen([sys.executable, "-B", "-c", {child!r}], '
          'creationflags=subprocess.CREATE_NEW_PROCESS_GROUP); '
          f'ready=pathlib.Path({str(ready)!r}); '
          'deadline=time.monotonic()+2; '
          '\nwhile not ready.exists() and time.monotonic()<deadline: time.sleep(.01)'
          '\nassert ready.exists(); print("100 HEALTH", flush=True)')
rows.append(ocr_case('ocr-late-descendant', parent, expected_error='containment'))

stale = OUT / 'ocr-stale'
stale.with_suffix('.stdout.txt').write_text('STALE-EVIDENCE', encoding='utf-8')
with patch.object(verify_offline_export, 'run_process') as launch:
    caught = None
    try:
        verify_offline_export.ocr_text([APPROVED, '-B', '-c', 'pass'], b'new input',
                                       time.monotonic() + 5, stale)
    except FileExistsError as error:
        caught = str(error)
    stale_row = {'name': 'ocr-stale-rejected', 'error': caught,
                 'launch_calls': launch.call_count,
                 'stale_stdout': stale.with_suffix('.stdout.txt').read_text()}
    stale_row['control_passed'] = bool(caught) and launch.call_count == 0 and stale_row['stale_stdout'] == 'STALE-EVIDENCE'
rows.append(stale_row)
save('ocr-stale.control.json', stale_row)

process = Mock(pid=42000)
process.poll.return_value = 0
process.wait.return_value = 0
with patch.object(godot_process, 'is_windows', return_value=True), \
        patch.object(godot_process.subprocess, 'run') as taskkill:
    failures = godot_process.cleanup_processes([('already-exited-root', process)])
    dead_root = {'name': 'windows-dead-root-fail-closed', 'failures': failures,
                 'taskkill_calls': taskkill.call_count,
                 'control_passed': bool(failures) and 'unverified' in failures[0]}
rows.append(dead_root)
save('windows-dead-root.control.json', dead_root)

linux_result = OUT / 'mock-linux.process.json'
process = Mock(pid=41000, returncode=0)
process.poll.return_value = 0
def wait(**kwargs):
    if not linux_result.exists():
        with linux_result.open('x') as stream:
            json.dump({'complete': True, 'exit': 0, 'errors': [],
                       'posix_cleanup_verified': False}, stream)
process.wait.side_effect = wait
log = io.StringIO()
with patch.object(matrix_process, 'os', types.SimpleNamespace(name='posix', killpg=Mock(side_effect=ProcessLookupError))), \
        patch.object(matrix_process, 'posix_children', side_effect=FileNotFoundError), \
        patch.object(matrix_process, 'kill_posix_group') as kill, \
        patch.object(matrix_process.subprocess, 'Popen', return_value=process):
    code = matrix_process.run_process(['not-executed'], cwd=OUT, env={}, log=log,
                                     result_path=linux_result, timeout=1)
with (OUT / 'mock-linux.log').open('x') as stream:
    stream.write(log.getvalue())
linux = {'name': 'linux-missing-cleanup-attestation', 'actual_command_exit': code,
         'log': log.getvalue(), 'group_signals': [list(c.args) for c in kill.call_args_list],
         'control_passed': code == 0 and 'HARNESS_ERROR' in log.getvalue()
                           and 'detached-descendant cleanup unverified' in log.getvalue()}
rows.append(linux)
save('mock-linux.control.json', linux)

# CPython defines unsupported concrete Path.__new__ at stdlib import time.
# Initialize a PRIVATE copy with POSIX platform identity; never replace the
# interpreter's actual pathlib module or launch a Linux/native command.
local_module = sys.modules[pathlib.Path.__module__]
local_source = inspect.getsource(local_module)
posix_pathlib = types.ModuleType('pathlib._critic_posix')
posix_pathlib.__package__ = 'pathlib'
with patch.object(os, 'name', 'posix'):
    exec(compile(local_source, '<isolated-POSIX-pathlib>', 'exec'), posix_pathlib.__dict__)
import test_matrix_process
trace = io.StringIO()
with patch.object(matrix_process, 'Path', posix_pathlib.Path):
    result = unittest.TextTestRunner(stream=trace, verbosity=2).run(
        unittest.TestSuite([test_matrix_process.SupervisorTests('test_parent_keeps_actual_exit')]))
with (OUT / 'linux-pathlib-existing-unit.log').open('x', encoding='utf-8') as stream:
    stream.write(trace.getvalue())
compat = {'name': 'linux-pathlib-windows-mock-existing-unit',
          'limit': 'POSIX-initialized actual CPython 3.13.15 stdlib on Windows; NOT actual Linux or workflow Python 3.12',
          'stdlib_source_module': pathlib.Path.__module__,
          'stdlib_source_sha256': hashlib.sha256(local_source.encode()).hexdigest(),
          'existing_test': 'test_matrix_process.SupervisorTests.test_parent_keeps_actual_exit',
          'tests_run': result.testsRun, 'errors': len(result.errors),
          'failures': len(result.failures), 'successful': result.wasSuccessful(),
          'verified_compatibility_defect': not result.wasSuccessful(),
          'traceback_log': 'linux-pathlib-existing-unit.log'}
save('linux-pathlib-existing-unit.control.json', compat)

# Observe after the finite child controls would naturally have written.
time.sleep(2.25)
settled = {'name': 'late-write-observation', 'descendant_started': ready.exists(),
           'descendant_late_write': late.exists(), 'timeout_late_write': timeout_late.exists()}
settled['control_passed'] = ready.exists() and not late.exists() and not timeout_late.exists()
rows.append(settled)
save('late-write-observation.control.json', settled)

summary = {'python': sys.executable, 'version': sys.version, 'controls': rows,
           'ordinary_controls_passed': all(row['control_passed'] for row in rows),
           'platform_compatibility_control': compat,
           'scope': 'Serial pure/synthetic CPython only; source/mock Linux; no engine/import/export/network/DB.'}
save('controls-summary.json', summary)
print(json.dumps(summary, indent=2))
raise SystemExit(1 if compat['verified_compatibility_defect'] or not summary['ordinary_controls_passed'] else 0)
