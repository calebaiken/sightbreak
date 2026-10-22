#!/usr/bin/env python3
"""Independent process/error controls; no Godot or GPU process is started."""
import base64,ctypes,json,os,signal,sys,tempfile,time
from pathlib import Path
repo=Path('/workspace/sightbreak-macos-render')
sys.path.insert(0,str(repo/'scripts'))
import diagnose_macos_startup as startup
from diagnose_macos_render import draw_trace
from PIL import Image
review=Path('/workspace/reviews/macos-diagnostic-critic')
# Adopt/reap test-owned grandchildren when exercising an exited root. This keeps
# Linux PID 1 zombie behavior out of the native macOS cleanup implementation.
ctypes.CDLL(None).prctl(36,1,0,0,0) # PR_SET_CHILD_SUBREAPER
startup.GRAPHICAL_SECONDS=0.5
rows=[]
trace='\n'.join(f'RENDER_DIAG phase=drawn frame={n} case=full msec={n*10} draws=135.0 primitives=43330.0' for n in range(1,16))
with tempfile.TemporaryDirectory(prefix='critic-native-cleanup-') as temp:
    temp=Path(temp)
    capture=temp/'reference.png'; Image.new('RGB',(8,8),(32,64,128)).save(capture)
    paths={}
    normal="print('RENDER_DIAG_EXIT capture_error=0 case=full msec=200',flush=True)"
    commands={
      'success': normal,
      'dirty-log': normal+"\nprint('ERROR: deliberate dirty log')",
      'missing-marker': "print('clean exit without evidence')",
      'nonzero': normal+"\nraise SystemExit(7)",
      'timeout': "import signal,time\nsignal.signal(signal.SIGTERM,signal.SIG_IGN)\ntime.sleep(30)",
      'missing-capture':normal,
      'bad-capture':normal,
    }
    for label,code in commands.items():
        path=capture
        if label=='missing-capture': path=temp/'absent.png'
        if label=='bad-capture':
            path=temp/'bad.png';path.write_bytes(b'not a png')
        result=startup.native_trial(temp,label,[sys.executable,'-c',code],path,'RENDER_DIAG_EXIT capture_error=0')
        expected=label=='success'
        assert result['passed']==expected,(label,result)
        assert not result['surviving_owned_group'],(label,result)
        if label=='timeout':assert result['timed_out'] and result['native_exit_code'] is None and result['exit_code_after_cleanup']==-signal.SIGKILL
        rows.append({'control':label,'passed_expected':result['passed']==expected,'native_exit':result['native_exit_code'],'timed_out':result['timed_out'],'cleanup_exit':result['exit_code_after_cleanup'],'survivors':result['surviving_owned_group']})
        paths[label]=json.loads((temp/(label+'.json')).read_text())
    # A real process tree: target root owns and reaps its child on group SIGTERM.
    parentcode='''import subprocess,signal,time,sys
child=subprocess.Popen([sys.executable,'-c','import time; time.sleep(30)'])
def stop(sig,frame):
    child.wait(timeout=2)
    raise SystemExit(128+sig)
signal.signal(signal.SIGTERM,stop)
print('child='+str(child.pid),flush=True)
time.sleep(30)
'''
    result=startup.native_trial(temp,'timeout-tree',[sys.executable,'-c',parentcode],capture,'RENDER_DIAG_EXIT capture_error=0')
    assert not result['passed'] and result['timed_out'] and not result['surviving_owned_group'],result
    paths['timeout-tree']=result
    rows.append({'control':'timeout-tree','passed_expected':not result['passed'],'timed_out':result['timed_out'],'survivors':result['surviving_owned_group']})
    # A subprocess SIGTERM should unwind native_trial, kill its owned target and
    # still retain the interruption receipt. A harness process sends the signal.
    interruptioncode='''import os,signal,sys,threading
from pathlib import Path
sys.path.insert(0,sys.argv[1])
import diagnose_macos_startup as startup
startup.GRAPHICAL_SECONDS=30
signal.signal(signal.SIGTERM,startup.interrupted)
threading.Timer(.3,lambda:os.kill(os.getpid(),signal.SIGTERM)).start()
startup.native_trial(Path(sys.argv[2]),'interrupted',[sys.executable,'-c','import time; time.sleep(30)'],Path(sys.argv[3]),'RENDER_DIAG_EXIT capture_error=0')
'''
    import subprocess
    p=subprocess.run([sys.executable,'-c',interruptioncode,str(repo/'scripts'),str(temp),str(capture)],capture_output=True,text=True,timeout=10)
    result=json.loads((temp/'interrupted.json').read_text())
    assert p.returncode==143 and result['interrupted']==143 and not result['passed'] and not result['surviving_owned_group'],(p,result)
    paths['interrupted']=result
    rows.append({'control':'interrupted','passed_expected':not result['passed'],'runner_exit':p.returncode,'interruption':result['interrupted'],'survivors':result['surviving_owned_group']})
    (review/'raw/process-control-receipts.json').write_text(json.dumps(paths,indent=2)+'\n')
(review/'raw/process-controls-summary.json').write_text(json.dumps(rows,indent=2)+'\n')
print(json.dumps(rows,indent=2))
