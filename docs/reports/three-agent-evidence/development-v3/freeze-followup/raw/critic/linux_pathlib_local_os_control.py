"""Corrected positive comparison: module-local OS mock preserves POSIX pathlib."""
import inspect
import io
import json
import os
import pathlib
from pathlib import Path
import sys
import types
from unittest.mock import Mock, patch

ROOT = Path(r'C:\Users\blith\AppData\Local\Temp\opencode\sightbreak-v3')
OUT = Path(__file__).resolve().parent
if sys.version_info[:3] != (3, 13, 15) or sys.executable != r'C:\Users\blith\AppData\Local\Temp\opencode\sightbreak-tools\python\cpython-3.13.15-windows-x86_64-none\python.exe':
    raise RuntimeError('Use exact approved interpreter')
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / 'scripts'))
import matrix_process

source = inspect.getsource(sys.modules[pathlib.Path.__module__])
linux_pathlib = types.ModuleType('pathlib._critic_linux_local_os')
linux_pathlib.__package__ = 'pathlib'
with patch.object(os, 'name', 'posix'):
    exec(compile(source, '<isolated-POSIX-pathlib>', 'exec'), linux_pathlib.__dict__)
linux_pathlib.os = types.SimpleNamespace(**{**vars(os), 'name': 'posix'})
receipt = OUT / 'linux-pathlib-corrected-local-os.process.json'
job = Mock()
job.name = 'fixture-job'
job.active.return_value = 0
process = Mock(returncode=0)
process.poll.return_value = 0
def wait(**kwargs):
    if not receipt.exists():
        with receipt.open('x', encoding='utf-8') as stream:
            json.dump({'complete': True, 'exit': 7, 'errors': []}, stream)
process.wait.side_effect = wait
log = io.StringIO()
with patch.object(matrix_process, 'Path', linux_pathlib.Path), \
        patch.object(matrix_process, 'os', types.SimpleNamespace(**{**vars(os), 'name': 'nt'})), \
        patch.object(matrix_process, 'WindowsJob', return_value=job), \
        patch.object(matrix_process.subprocess, 'Popen', return_value=process) as launch:
    code = matrix_process.run_process(['not-executed'], cwd=OUT, env={}, log=log,
                                     result_path=receipt, timeout=1)
result = {'scope': 'Corrected positive comparison; POSIX-pathlib source/synthetic only',
          'returned_exit': code, 'log': log.getvalue(), 'mock_launch_calls': launch.call_count,
          'job_stop_calls': job.stop.call_count,
          'passed': code == 7 and not log.getvalue() and launch.call_count == 1 and job.stop.call_count == 1,
          'earlier_control_defect': 'linux_pathlib_repro.py positive comparison wrote its mock receipt on both waits; failure retained, not attributed to product'}
with (OUT / 'linux-pathlib-corrected-local-os.json').open('x', encoding='utf-8') as stream:
    json.dump(result, stream, indent=2)
    stream.write('\n')
print(json.dumps(result, indent=2))
raise SystemExit(0 if result['passed'] else 1)
