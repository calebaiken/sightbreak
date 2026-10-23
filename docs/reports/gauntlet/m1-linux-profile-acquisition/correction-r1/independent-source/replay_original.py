#!/usr/bin/env python3
"""Independent exact-source replay; only Git reads and pure Python children."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[6]
HERE = Path(__file__).resolve().parent
FREEZE = 'd0d94bec27f539b63e324c5468516ff2f0dd96d7'
REJECT = '04bc153e52341228b2f0d6f4ce72f784528ef1d4'
CRITIC = 'ff4cc71b1a81c073a92acea1b56007e4508282e7'
CONTROL = 'docs/reports/gauntlet/m1-linux-profile-acquisition/independent-fresh-source/test_independent_controls.py'
FILES = ('linux_profile_acquire.py', 'linux_profile_payload.py', 'test_linux_profile_acquire.py',
         'linux_profile_overhead.py', 'test_linux_profile_overhead.py', 'native_log.py', 'toolchain.py')
PROGRAM = '''
import importlib.util,json,pathlib,sys,unittest
spec=importlib.util.spec_from_file_location('original_critic',sys.argv[1])
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(module.IndependentControls))
pathlib.Path(sys.argv[2]).write_text(json.dumps({'methods':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skips':len(result.skipped),'results':module.RESULTS},indent=2)+'\\n')
sys.exit(0 if result.wasSuccessful() else 1)
'''

def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)

original = git('show', CRITIC + ':' + CONTROL)
summary = {'candidate': FREEZE, 'rejected_candidate': REJECT, 'critic': CRITIC,
           'unchanged_control_sha256': hashlib.sha256(original).hexdigest(), 'native_runs': 0, 'runs': {}}
for label, commit in (('rejected', REJECT), ('corrected', FREEZE)):
    with tempfile.TemporaryDirectory(prefix='independent-acq-replay-') as temporary:
        folder = Path(temporary)
        scripts = folder / 'scripts'
        scripts.mkdir()
        hashes = {}
        for name in FILES:
            raw = git('show', commit + ':scripts/' + name)
            (scripts / name).write_bytes(raw)
            hashes[name] = hashlib.sha256(raw).hexdigest()
        control = folder / 'a/b/c/d/e/test_independent_controls.py'
        control.parent.mkdir(parents=True)
        control.write_bytes(original)
        assert control.read_bytes() == original
        result = subprocess.run([sys.executable, '-B', '-c', PROGRAM, str(control), str(HERE / (label + '-results.json'))],
                                cwd=folder, env=dict(os.environ, PYTHONPATH=str(scripts), PYTHONDONTWRITEBYTECODE='1'),
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=60)
        (HERE / (label + '-original-controls.txt')).write_bytes(result.stdout)
        details = json.loads((HERE / (label + '-results.json')).read_text())
        assert details['methods'] == 3 and details['errors'] == details['skips'] == 0, details
        assert details['failures'] == (10 if label == 'rejected' else 0), details
        assert result.returncode == (1 if label == 'rejected' else 0), details
        summary['runs'][label] = {'exit': result.returncode, 'failures': details['failures'], 'errors': 0, 'source_sha256': hashes}
(HERE / 'replay-summary.json').write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps({label: {'failures': value['failures'], 'errors': value['errors']} for label, value in summary['runs'].items()}))
