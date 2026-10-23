#!/usr/bin/env python3
"""Pure replay of the pre-review alarm-restoration counterexample; no native spawn."""
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
from types import ModuleType
import unittest

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'scripts'))
import linux_profile_acquire as current
import test_linux_profile_acquire as controls

FROZEN = '22bb1f8'
old_bytes = subprocess.check_output(['git', 'show', FROZEN + ':scripts/linux_profile_acquire.py'], cwd=ROOT)
old = ModuleType('old_acquisition')
old.__file__ = str(ROOT / 'scripts/linux_profile_acquire.py')
exec(compile(old_bytes, old.__file__, 'exec'), old.__dict__)
names = ('BudgetTests.test_positive_original_phase_boundary_and_late_publication_read_hash',
         'MainPublicationTests.test_main_positive_final_boundary_and_all_late_finalization_paths_reject')
results = {}
for label, module in [('before', old), ('corrected', current)]:
    controls.acq = module
    stream = io.StringIO()
    suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(name, controls) for name in names)
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    (HERE / 'pure-controls' / ('alarm-restore-' + label + '.txt')).write_text(stream.getvalue())
    results[label] = {'methods': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
                      'passed': result.wasSuccessful()}
controls.acq = current
assert results['before'] == {'methods': 2, 'failures': 2, 'errors': 0, 'passed': False}, results
assert results['corrected'] == {'methods': 2, 'failures': 0, 'errors': 0, 'passed': True}, results
receipt = {'initial_savepoint': subprocess.check_output(['git', 'rev-parse', FROZEN], cwd=ROOT, text=True).strip(),
           'old_wrapper_sha256': hashlib.sha256(old_bytes).hexdigest(),
           'corrected_wrapper_sha256': current.digest(ROOT / 'scripts/linux_profile_acquire.py'),
           'controls_sha256': current.digest(ROOT / 'scripts/test_linux_profile_acquire.py'), 'results': results,
           'scope': 'Virtual time advances when the alarm is disarmed/restored. The old phase returns late and old main returns exit 0 after the final cap. Corrected source rejects. All Popen is fake/forbidden; no native process.',
           'engine_import_compile_export_native_runs': 0}
current.write(HERE / 'pure-controls/alarm-restore-replay.json', receipt)
print(json.dumps(receipt, indent=2))
