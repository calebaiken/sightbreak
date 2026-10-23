#!/usr/bin/env python3
"""Replay unchanged independent falsifiers in isolated pure-Python source copies.

Only Git reads and Python unittest children run. Target Popen is always fake.
No retained original report is overwritten, and no engine/tool is invoked.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
BASE = '04bc153e52341228b2f0d6f4ce72f784528ef1d4'
FILES = ('linux_profile_acquire.py', 'linux_profile_payload.py', 'test_linux_profile_acquire.py',
         'linux_profile_overhead.py', 'test_linux_profile_overhead.py', 'native_log.py', 'toolchain.py')
PROGRAM = '''
import importlib.util, json, pathlib, sys, unittest
spec = importlib.util.spec_from_file_location('unchanged_falsifiers', sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(module.IndependentControls))
pathlib.Path(sys.argv[2]).write_text(json.dumps({'synthetic_only': True, 'native_runs': 0,
    'methods': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
    'skips': len(result.skipped), 'results': module.RESULTS}, indent=2) + '\\n')
sys.exit(0 if result.wasSuccessful() else 1)
'''


def main():
    summary = {'rejected_commit': BASE, 'preregistration_commit': 'b75017d', 'synthetic_only': True,
               'native_runs': 0, 'controls_sha256': hashlib.sha256((HERE / 'retained-rejection/test_independent_controls.py').read_bytes()).hexdigest(),
               'runs': {}}
    for label in ('rejected', 'corrected'):
        with tempfile.TemporaryDirectory(prefix='acquisition-source-replay-') as temporary:
            scripts = Path(temporary) / 'scripts'
            scripts.mkdir()
            sources = {}
            for name in FILES:
                raw = subprocess.run(['git', 'show', BASE + ':scripts/' + name], cwd=ROOT,
                                     check=True, stdout=subprocess.PIPE).stdout if label == 'rejected' else (ROOT / 'scripts' / name).read_bytes()
                (scripts / name).write_bytes(raw)
                sources[name] = hashlib.sha256(raw).hexdigest()
            env = dict(os.environ, PYTHONPATH=str(scripts), PYTHONDONTWRITEBYTECODE='1')
            result = subprocess.run([sys.executable, '-B', '-c', PROGRAM,
                                     str(HERE / 'retained-rejection/test_independent_controls.py'),
                                     str(HERE / 'pure-controls' / (label + '-replay.json'))],
                                    cwd=temporary, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=60)
            (HERE / 'pure-controls' / (label + '-replay.txt')).write_bytes(result.stdout)
            details = json.loads((HERE / 'pure-controls' / (label + '-replay.json')).read_text())
            assert details['methods'] == 3 and details['errors'] == details['skips'] == 0, details
            assert details['failures'] == (10 if label == 'rejected' else 0), details
            assert result.returncode == (1 if label == 'rejected' else 0), result.stdout.decode()
            positive = next(row for row in details['results'] if row['mode'] == 'valid')
            assert positive['exit_code'] == 0 and positive['passed'] is True, positive
            summary['runs'][label] = {'exit_code': result.returncode, 'methods': 3,
                                      'failures': details['failures'], 'errors': 0, 'skips': 0, 'source_sha256': sources}
    (HERE / 'pure-controls/replay-summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps({name: {'failures': row['failures'], 'errors': row['errors']} for name, row in summary['runs'].items()}))


if __name__ == '__main__':
    main()
