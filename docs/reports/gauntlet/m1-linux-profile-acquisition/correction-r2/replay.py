#!/usr/bin/env python3
"""Isolated pure-Python replays; original reports are never overwritten."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
REPORT = HERE.parent
ORIGINAL = '04bc153e52341228b2f0d6f4ce72f784528ef1d4'
R1 = 'd0d94bec27f539b63e324c5468516ff2f0dd96d7'
FILES = ('linux_profile_acquire.py', 'linux_profile_payload.py', 'test_linux_profile_acquire.py',
         'linux_profile_overhead.py', 'test_linux_profile_overhead.py', 'native_log.py', 'toolchain.py')
PROGRAM = '''
import importlib.util, json, pathlib, sys, unittest
spec = importlib.util.spec_from_file_location('replayed_controls', sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
import linux_profile_acquire as candidate
assert pathlib.Path(candidate.__file__).resolve().parents[1] == pathlib.Path.cwd(), candidate.__file__
result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(getattr(module, sys.argv[3])))
pathlib.Path(sys.argv[2]).write_text(json.dumps({'native_runs': 0, 'methods': result.testsRun,
 'failures': len(result.failures), 'errors': len(result.errors), 'skips': len(result.skipped),
 'results': module.RESULTS}, indent=2) + '\\n')
sys.exit(0 if result.wasSuccessful() else 1)
'''


def main():
    (HERE / 'pure-controls').mkdir(exist_ok=True)
    original_control = REPORT / 'correction-r1/retained-rejection/test_independent_controls.py'
    boundary_control = HERE / 'retained-rejection/test_boundary_controls.py'
    runs = (
        ('original-rejected', ORIGINAL, original_control, 'IndependentControls', 3, 10),
        ('r1-rejected', R1, boundary_control, 'BoundaryControls', 3, 2),
        ('corrected-original', None, original_control, 'IndependentControls', 3, 0),
        ('corrected-boundary', None, ROOT / 'scripts/test_linux_profile_acquire_boundary.py', 'BoundaryTests', 4, 0))
    summary = {'native_runs': 0, 'synthetic_only': True, 'runs': {}}
    for label, commit, control, suite, methods, failures in runs:
        with tempfile.TemporaryDirectory(prefix='acquisition-r2-pure-') as temporary:
            root = Path(temporary); scripts = root / 'scripts'; scripts.mkdir()
            selected = FILES + (('test_linux_profile_acquire_sealing.py',) if commit != ORIGINAL else ())
            selected += ('test_linux_profile_acquire_boundary.py',) if commit is None else ()
            hashes = {}
            for name in selected:
                raw = subprocess.run(['git', 'show', commit + ':scripts/' + name], cwd=ROOT,
                                     check=True, stdout=subprocess.PIPE).stdout if commit else (ROOT / 'scripts' / name).read_bytes()
                (scripts / name).write_bytes(raw)
                hashes[name] = hashlib.sha256(raw).hexdigest()
            for relative, source in (
                    ('correction-r1/retained-rejection/test_independent_controls.py', original_control),
                    ('correction-r2/retained-rejection/test_boundary_controls.py', boundary_control)):
                destination = root / 'docs/reports/gauntlet/m1-linux-profile-acquisition' / relative
                destination.parent.mkdir(parents=True, exist_ok=True); destination.write_bytes(source.read_bytes())
            env = dict(os.environ, PYTHONPATH=str(scripts), PYTHONDONTWRITEBYTECODE='1')
            if control == original_control:
                local_control = root / 'docs/reports/gauntlet/m1-linux-profile-acquisition/correction-r1/retained-rejection/test_independent_controls.py'
            elif control == boundary_control:
                local_control = root / 'docs/reports/gauntlet/m1-linux-profile-acquisition/correction-r2/retained-rejection/test_boundary_controls.py'
            else:
                local_control = scripts / control.name
            result = subprocess.run([sys.executable, '-B', '-c', PROGRAM, str(local_control),
                                     str(HERE / 'pure-controls' / (label + '.json')), suite],
                                    cwd=root, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=60)
            (HERE / 'pure-controls' / (label + '.txt')).write_bytes(result.stdout)
            details = json.loads((HERE / 'pure-controls' / (label + '.json')).read_text())
            assert details['methods'] == methods and details['errors'] == details['skips'] == 0, details
            assert details['failures'] == failures and result.returncode == int(failures > 0), result.stdout.decode()
            summary['runs'][label] = {'source_commit': commit, 'methods': methods, 'failures': failures,
                'errors': 0, 'skips': 0, 'exit_code': result.returncode, 'control_sha256': hashlib.sha256(control.read_bytes()).hexdigest(),
                'source_sha256': hashes}
    (HERE / 'pure-controls/replay-summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps({name: {'failures': row['failures'], 'errors': row['errors']} for name, row in summary['runs'].items()}))


if __name__ == '__main__':
    main()
