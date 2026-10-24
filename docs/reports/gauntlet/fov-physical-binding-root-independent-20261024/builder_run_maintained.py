"""Run unchanged maintained bodies with real target operations forbidden."""
import argparse
from contextlib import ExitStack
import importlib
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

parser=argparse.ArgumentParser();parser.add_argument('--source',type=Path,required=True);parser.add_argument('--result',type=Path,required=True);args=parser.parse_args()
sys.path.insert(0,str(args.source/'scripts'))
names=('test_fov_math_reference','test_fov_binary_input','test_fov_owned_ancestry','test_native_log')
for name in names:importlib.import_module(name)
import acquire_fov_math_reference as a
suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(name) for name in names)
attempts=[]
def forbid(label):
    def called(*args,**kwargs):
        attempts.append(label);raise AssertionError('forbidden real target operation: '+label)
    return called
real_open=Path.open;real_readlink=a.os.readlink

def open_source(path,*args,**kwargs):
    if str(path)=='/proc' or str(path).startswith('/proc/'):return forbid('proc path open')(path)
    return real_open(path,*args,**kwargs)

def readlink_source(path,*args,**kwargs):
    if str(path)=='/proc' or str(path).startswith('/proc/'):return forbid('proc readlink')(path)
    return real_readlink(path,*args,**kwargs)

with ExitStack() as stack:
    for owner,name,label in ((a.subprocess,'Popen','Popen'),(a.subprocess,'run','run'),(a.subprocess,'check_output','check_output'),
                             (a.os,'pidfd_open','pidfd_open'),(a.os,'waitpid','waitpid'),(a.os,'read','read'),
                             (a.os,'sched_setaffinity','sched_setaffinity'),(a.signal,'pidfd_send_signal','pidfd_send_signal'),
                             (a.ctypes,'CDLL','CDLL'),(a.selectors,'DefaultSelector','DefaultSelector')):
        stack.enter_context(patch.object(owner,name,side_effect=forbid(label),create=True))
    stack.enter_context(patch.object(a.os,'getpid',return_value=50))
    stack.enter_context(patch.object(a.os,'sched_getaffinity',return_value={4}))
    stack.enter_context(patch.object(Path,'open',open_source))
    stack.enter_context(patch.object(a.os,'readlink',readlink_source))
    result=unittest.TextTestRunner(verbosity=2).run(suite)
record=dict(methods=result.testsRun,failures=len(result.failures),errors=len(result.errors),skips=len(result.skipped),
            forbidden_entrypoint_attempts=attempts,passed=result.wasSuccessful() and not attempts,
            scope='unchanged maintained bodies with modeled PID/affinity and real target/process/kernel/proc/selector/library calls forbidden; inner registered fakes only')
args.result.write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record));raise SystemExit(not record['passed'])
