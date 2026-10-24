"""Own source-only execution wrapper; blocks forbidden process/API entrypoints."""
import argparse
import contextlib
import ctypes
import hashlib
import importlib
import inspect
import json
import os
from pathlib import Path
import runpy
import signal
import subprocess
import sys
import time
import unittest

parser=argparse.ArgumentParser()
parser.add_argument('--root',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
parser.add_argument('--script',type=Path)
parser.add_argument('--selected',action='store_true')
args=parser.parse_args()
assert sorted(os.sched_getaffinity(0))==[4]
args.output.mkdir(parents=True,exist_ok=False)
forbidden_calls=[]
def forbidden(*a,**k):
    forbidden_calls.append('forbidden entrypoint')
    raise AssertionError('real process/Windows API/pidfd/signal is forbidden')
for owner,names in [(subprocess,('Popen','run','call','check_call','check_output')),
                    (os,('system','fork','forkpty','posix_spawn','posix_spawnp','pidfd_open','kill')),
                    (signal,('pidfd_send_signal',)),(ctypes,('CDLL','WinDLL'))]:
    for name in names:
        if hasattr(owner,name) or (owner is ctypes and name=='WinDLL'):
            setattr(owner,name,forbidden)
sys.path.insert(0,str(args.root/'scripts'))
os.environ['MATH_REVIEW_ROOT']=str(args.root)
start=time.monotonic();result={'scope':'Source-only controlled execution, no native/API proof','root':str(args.root),'cpu':[4]}
try:
    if args.script:
        # The copied script writes only this own report's selected output label.
        os.environ['MATH_REVIEW_LABEL']=args.output.name
        runpy.run_path(str(args.script),run_name='__main__')
        result.update(script=str(args.script),script_sha256=hashlib.sha256(args.script.read_bytes()).hexdigest(),completed=True)
    else:
        suite=unittest.TestSuite();selected=[];omitted=[]
        for name in ('test_windows_fov_math','test_fov_math_reference','test_fov_binary_input','test_native_log','test_windows_fov_math_finalization'):
            module=importlib.import_module(name)
            for _,cls in inspect.getmembers(module,inspect.isclass):
                if not issubclass(cls,unittest.TestCase) or cls.__module__!=name:continue
                for method in unittest.defaultTestLoader.getTestCaseNames(cls):
                    identity=name+'.'+cls.__name__+'.'+method
                    if cls.__name__=='ProcInterfaceControls' or method=='test_authenticated_generated_sdk_fixture_extracts_only_gui_and_records_measured_member':
                        omitted.append(identity)
                    else:selected.append(identity);suite.addTest(cls(method))
        assert len(selected)==96 and len(omitted)==5,(len(selected),len(omitted))
        with (args.output/'stdout').open('w') as stdout,(args.output/'stderr').open('w') as stderr,contextlib.redirect_stdout(stdout):
            checked=unittest.TextTestRunner(stream=stderr,verbosity=2).run(suite)
        result.update(selected=selected,omitted=omitted,methods=checked.testsRun,failures=len(checked.failures),errors=len(checked.errors),skips=len(checked.skipped),passed=checked.wasSuccessful())
except BaseException as error:
    import traceback
    result.update(completed=False,exception_type=type(error).__name__,exception=str(error),traceback=traceback.format_exc())
finally:
    result.update(seconds=time.monotonic()-start,forbidden_calls=forbidden_calls,actual_native_invocations=0)
    (args.output/'GUARD_RESULT.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ('selected','omitted','traceback')}))
raise SystemExit(0 if (result.get('completed') or result.get('passed')) and not forbidden_calls else 1)
