"""Run only declared pure suites, forbidding native/process effects."""
import argparse
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

parser=argparse.ArgumentParser();parser.add_argument('--source',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args();assert os.sched_getaffinity(0)=={4}
args.output.mkdir(parents=True,exist_ok=False)
source=args.source.resolve();sys.path.insert(0,str(source/'scripts'))
summary=[]
with patch('subprocess.Popen',side_effect=AssertionError('real process forbidden')),patch('os.kill',side_effect=AssertionError('real signal forbidden')),patch('ctypes.CDLL',side_effect=AssertionError('native library forbidden')):
    for name,pattern in [('math-codec','test_fov*.py'),('strict-log','test_native_log.py')]:
        suite=unittest.defaultTestLoader.discover(str(source/'scripts'),pattern=pattern)
        with (args.output/(name+'.stderr')).open('w') as stream:
            result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
        summary.append(dict(suite=name,methods=result.testsRun,failures=len(result.failures),
                            errors=len(result.errors),skips=len(result.skipped),successful=result.wasSuccessful()))
payload=dict(source=str(source),suites=summary,methods=sum(s['methods'] for s in summary),
             native_invocations=0,real_processes_forbidden=True)
(args.output/'MAINTAINED.json').write_text(json.dumps(payload,indent=2)+'\n')
print(json.dumps(payload))
raise SystemExit(not all(row['successful'] for row in summary))
