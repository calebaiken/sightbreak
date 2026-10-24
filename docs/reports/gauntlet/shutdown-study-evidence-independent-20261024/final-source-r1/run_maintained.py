"""Component58 only; explicit fixed baseline instead of runtime historical Git."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--data',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
a=p.parse_args();assert os.sched_getaffinity(0)=={4};source=a.source.resolve();a.output.mkdir(parents=True,exist_ok=False)
baseline=(a.data/'frozen-control-source/verify_offline_export-8ee93ac7.py').read_bytes();binding=json.loads((a.data/'SOURCE_UNION_AND_DEPTH.json').read_text())['legacy_baseline']
assert len(baseline)==binding['bytes'] and hashlib.sha256(baseline).hexdigest()==binding['sha256']
queries=[]
def baseline_only(command,**options):
    assert command==['git','show','8ee93ac725d519c9f6d7f1ffbb3f7c9ee960baf8:scripts/verify_offline_export.py'],command
    assert Path(options['cwd']).resolve()==source,options
    queries.append(dict(command=command,baseline_sha256=binding['sha256'],served_from_bound_file=True))
    return baseline
sys.path.insert(0,str(source/'scripts'));rows=[]
with patch('subprocess.Popen',side_effect=AssertionError('real process forbidden')),patch('subprocess.check_output',baseline_only),patch('os.kill',side_effect=AssertionError('real signal forbidden')),patch('ctypes.CDLL',side_effect=AssertionError('native library forbidden')):
    for name,pattern in [('old28','test_windows_shutdown_study.py'),('evidence30','test_shutdown_study_evidence.py')]:
        suite=unittest.defaultTestLoader.discover(str(source/'scripts'),pattern=pattern)
        with (a.output/(name+'.stderr')).open('w') as stream:r=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
        rows.append(dict(name=name,methods=r.testsRun,failures=len(r.failures),errors=len(r.errors),skips=len(r.skipped),successful=r.wasSuccessful()))
result=dict(source=str(source),suites=rows,methods=sum(row['methods'] for row in rows),baseline_adapter_queries=queries,
            unchanged_binding_methods_not_repeated=11,native_invocations=0,real_git_or_processes_during_tests=0)
(a.output/'MAINTAINED.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
raise SystemExit(not all(row['successful'] for row in rows))
