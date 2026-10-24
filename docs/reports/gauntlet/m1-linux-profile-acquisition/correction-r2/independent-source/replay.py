#!/usr/bin/env python3
"""Independent exact-Git replay; target Popen remains fake or forbidden."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[6]
HERE = Path(__file__).resolve().parent
CURRENT = 'f242a2f20adb3ba1d9c49feb1c6caca1bdbf52b9'
ORIGINAL = '04bc153e52341228b2f0d6f4ce72f784528ef1d4'
R1 = 'd0d94bec27f539b63e324c5468516ff2f0dd96d7'
FIRST_REVIEW = 'ff4cc71b1a81c073a92acea1b56007e4508282e7'
SECOND_REVIEW = 'c339065c80e13a945b87c7f01a65655639be8281'
PREFIX = 'docs/reports/gauntlet/m1-linux-profile-acquisition/'
BASE_FILES = ('linux_profile_acquire.py', 'linux_profile_payload.py', 'test_linux_profile_acquire.py',
              'linux_profile_overhead.py', 'test_linux_profile_overhead.py', 'native_log.py', 'toolchain.py')
PROGRAM = '''
import importlib.util,json,pathlib,sys,unittest
spec=importlib.util.spec_from_file_location('exact_controls',sys.argv[1])
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
import linux_profile_acquire as candidate
assert pathlib.Path(candidate.__file__).resolve().parent == pathlib.Path.cwd()/'scripts',candidate.__file__
result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(getattr(module,sys.argv[3])))
pathlib.Path(sys.argv[2]).write_text(json.dumps({'methods':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skips':len(result.skipped),'results':module.RESULTS,'imported_source':str(pathlib.Path(candidate.__file__).resolve())},indent=2)+'\\n')
sys.exit(0 if result.wasSuccessful() else 1)
'''
def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)
original = git('show', FIRST_REVIEW + ':' + PREFIX + 'independent-fresh-source/test_independent_controls.py')
boundary = git('show', SECOND_REVIEW + ':' + PREFIX + 'correction-r1/independent-source/test_boundary_controls.py')
summary = {'candidate': CURRENT, 'native_runs': 0, 'runs': {}}
for label, commit, suite, count, failures in (
        ('original-rejected', ORIGINAL, 'IndependentControls', 3, 10),
        ('r1-rejected', R1, 'BoundaryControls', 3, 2),
        ('corrected-original', CURRENT, 'IndependentControls', 3, 0),
        ('corrected-boundary', CURRENT, 'BoundaryTests', 4, 0)):
    with tempfile.TemporaryDirectory(prefix='critic-r2-replay-') as temporary:
        root = Path(temporary)
        scripts = root / 'scripts'
        scripts.mkdir()
        names = BASE_FILES + (('test_linux_profile_acquire_sealing.py',) if commit != ORIGINAL else ())
        if suite == 'BoundaryTests':
            names += ('test_linux_profile_acquire_boundary.py',)
        hashes = {}
        for name in names:
            raw = git('show', commit + ':scripts/' + name)
            (scripts / name).write_bytes(raw)
            hashes[name] = hashlib.sha256(raw).hexdigest()
        originals = root / PREFIX / 'correction-r1/retained-rejection/test_independent_controls.py'
        boundaries = root / PREFIX / 'correction-r2/retained-rejection/test_boundary_controls.py'
        for path, raw in ((originals, original), (boundaries, boundary)):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        control = originals if suite == 'IndependentControls' else boundaries if suite == 'BoundaryControls' else scripts / 'test_linux_profile_acquire_boundary.py'
        result = subprocess.run([sys.executable, '-B', '-c', PROGRAM, str(control), str(HERE / (label + '.json')), suite],
                                cwd=root, env=dict(os.environ, PYTHONPATH=str(scripts), PYTHONDONTWRITEBYTECODE='1'),
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=60)
        (HERE / (label + '.txt')).write_bytes(result.stdout)
        details = json.loads((HERE / (label + '.json')).read_text())
        assert details['methods'] == count and details['failures'] == failures, details
        assert details['errors'] == details['skips'] == 0 and result.returncode == int(failures > 0), details
        summary['runs'][label] = {'source_commit': commit, 'methods': count, 'failures': failures, 'errors': 0,
                                  'control_sha256': hashlib.sha256(control.read_bytes()).hexdigest(), 'source_sha256': hashes}
(HERE / 'replay-summary.json').write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps({label: {'failures': row['failures'], 'errors': row['errors']} for label, row in summary['runs'].items()}))
