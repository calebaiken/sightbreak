"""Outer guard for declared pure source controls; no subprocess/API/proc run."""
import argparse,ctypes,json,os,runpy,signal,subprocess,sys,time
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch
p=argparse.ArgumentParser();p.add_argument('--guard-result',type=Path,required=True);p.add_argument('script',type=Path);p.add_argument('args',nargs=argparse.REMAINDER);a=p.parse_args()
assert sorted(os.sched_getaffinity(0))==[4]
attempts=[]
def forbidden(*args,**kwargs):
    attempts.append('real process/API/proc entry');raise AssertionError('real process/API/proc forbidden')
real_open=Path.open;real_link=os.readlink
def source_open(path,*args,**kwargs):
    if str(path)=='/proc' or str(path).startswith('/proc/'):return forbidden()
    return real_open(path,*args,**kwargs)
def source_link(path,*args,**kwargs):
    if str(path)=='/proc' or str(path).startswith('/proc/'):return forbidden()
    return real_link(path,*args,**kwargs)
started=time.monotonic();code=0;error=None
with ExitStack() as stack:
    for owner,names in ((subprocess,('Popen','run','call','check_call','check_output')),
                        (os,('system','fork','forkpty','posix_spawn','posix_spawnp','pidfd_open','kill','waitpid','waitid')),
                        (signal,('pidfd_send_signal',)),(ctypes,('CDLL','WinDLL'))):
        for name in names:
            if hasattr(owner,name):stack.enter_context(patch.object(owner,name,side_effect=forbidden))
    stack.enter_context(patch.object(Path,'open',source_open));stack.enter_context(patch.object(os,'readlink',source_link))
    sys.argv=[str(a.script),*a.args]
    try:runpy.run_path(str(a.script),run_name='__main__')
    except SystemExit as e:code=e.code if isinstance(e.code,int) else int(e.code is not None)
    except BaseException:
        import traceback
        error=traceback.format_exc();code=1
result=dict(script=str(a.script),exit=code,exception=error,forbidden_attempts=attempts,seconds=time.monotonic()-started,scope='pure source/test execution only; no actual207/native/API/proc/study/capability')
a.guard_result.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result));raise SystemExit(code or bool(attempts))
