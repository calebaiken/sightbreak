"""Replay only sealed critic fake-main wrapper method; no baseline setup/native."""
import importlib.util
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
assert os.sched_getaffinity(0)=={4}
ROOT=Path(__file__).resolve().parents[6]
sys.path.insert(0,str(ROOT/'scripts'))
import windows_shutdown_study as study
source=ROOT/'docs/reports/gauntlet/windows-shutdown-evidence-completeness-r2-20261024/critic-7f6-reference/independent_controls.py'
spec=importlib.util.spec_from_file_location('sealed_critic_controls',source);sealed=importlib.util.module_from_spec(spec);spec.loader.exec_module(sealed)
sealed.study=study;sealed.OUTPUT=Path(__file__).parent/'exact-critic-wrapper';sealed.OUTPUT.mkdir()
class WrapperOnly(sealed.ReceiptControls):
    @classmethod
    def setUpClass(cls):pass
    def setUp(self):pass
suite=unittest.TestSuite([WrapperOnly('test_08_wrapper_originals_and_publication_receipt_collision')])
with patch('subprocess.Popen',side_effect=AssertionError('native process forbidden')),patch('ctypes.CDLL',side_effect=AssertionError('native library forbidden')),patch('os.kill',side_effect=AssertionError('signal forbidden')):
    with (sealed.OUTPUT/'tests.stderr').open('w') as log:result=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
summary=dict(scope='Exact sealed critic method8 on new unfrozen source, fake main only',methods=result.testsRun,failures=len(result.failures),errors=len(result.errors),actual_native_invocations=0)
(sealed.OUTPUT/'SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary));raise SystemExit(not result.wasSuccessful())
