"""Run the corrected existing unit with POSIX-initialized stdlib pathlib.

Synthetic platform control on Windows, not actual Linux execution.
"""
import hashlib
import inspect
import io
import json
import os
from pathlib import Path
import pathlib
import subprocess
import sys
import types
import unittest
from unittest.mock import patch

ROOT = Path(r'C:\Users\blith\AppData\Local\Temp\opencode\sightbreak-v3')
OUT = Path(__file__).with_name('pathlib-after')
OUT.mkdir(exist_ok=False)
sys.path.insert(0, str(ROOT / 'scripts'))
import matrix_process
import test_matrix_process

source = inspect.getsource(sys.modules[pathlib.Path.__module__])
posix_pathlib = types.ModuleType('pathlib._freeze_posix')
posix_pathlib.__package__ = 'pathlib'
with patch.object(os, 'name', 'posix'):
    exec(compile(source, '<isolated-POSIX-pathlib>', 'exec'), posix_pathlib.__dict__)
posix_os = types.SimpleNamespace(**{**vars(os), 'name': 'posix'})
posix_pathlib.os = posix_os
trace = io.StringIO()
with patch.object(matrix_process, 'Path', posix_pathlib.Path), \
        patch.object(matrix_process, 'os', posix_os):
    result = unittest.TextTestRunner(stream=trace, verbosity=2).run(
        unittest.TestSuite([test_matrix_process.SupervisorTests('test_parent_keeps_actual_exit')]))
(OUT / 'posix-pathlib.log').write_text(trace.getvalue(), encoding='utf-8')
command = [sys.executable, '-B', '-X', 'faulthandler', str(ROOT / 'scripts/test_matrix_process.py'), '-v']
with (OUT / 'matrix-process-unit.log').open('xb') as stream:
    unit = subprocess.run(command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT, timeout=120)
result_data = {
    'scope': 'Test-only OS-mock fix; synthetic POSIX stdlib control and Windows unit suite, not actual Linux/native validation',
    'python': sys.executable, 'version': sys.version,
    'source_sha256': {'scripts/test_matrix_process.py': hashlib.sha256((ROOT / 'scripts/test_matrix_process.py').read_bytes()).hexdigest()},
    'posix_pathlib': {'tests': result.testsRun, 'errors': len(result.errors), 'failures': len(result.failures), 'passed': result.wasSuccessful()},
    'unit': {'command': command, 'exit': unit.returncode},
    'passed': result.wasSuccessful() and unit.returncode == 0,
}
(OUT / 'results.json').write_text(json.dumps(result_data, indent=2), encoding='utf-8')
print(json.dumps(result_data, indent=2))
raise SystemExit(0 if result_data['passed'] else 1)
