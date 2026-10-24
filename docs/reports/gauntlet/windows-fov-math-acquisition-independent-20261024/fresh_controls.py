"""Registered pure lifecycle models; never constructs a native job/process/SDK."""
import copy,gzip,hashlib,json,os,sys,tempfile,traceback
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent;ROOT=Path(os.environ.get('MATH_REVIEW_ROOT','/workspace/reviews/windows-fov-math-acquisition-runtime-20261024'))
OUT=HERE/os.environ.get('MATH_REVIEW_LABEL','own-controls');OUT.mkdir(exist_ok=True)
sys.path.insert(0,str(ROOT/'scripts'))
import windows_fov_math as w
from test_fov_math_reference import declared_binary_records,encoded
RAW=encoded(declared_binary_records());PAYLOAD=json.loads((ROOT/w.PROJECT/w.reference.BINARY_CASES_NAME).read_bytes())
assert sorted(os.sched_getaffinity(0))==[4]
class Clock:
 def __init__(self):self.now=100.
 def __call__(self):return self.now
 def sleep(self,seconds):self.now+=seconds
class Handle:
 def __init__(self,name,token):self.name=name;self.token=token;self.attempts=0;self.closed=False
 def close(self):self.attempts+=1;self.closed=True
class Pipe(Handle):
 def fileno(self):return self.token
class RootProcess:
 def __init__(self,clock):
  self.clock=clock;self.pid=200;self._handle=501;self.birth=20000;self.finish=100.03;self.code=0;self.waited=False
  self.stdout=Pipe('root-stdout-pipe',901);self.stderr=Pipe('root-stderr-pipe',902)
 def poll(self):return self.code if self.clock()>=self.finish else None
 def wait(self,timeout):
  if self.poll() is None:raise TimeoutError('modeled root still alive')
  self.waited=True;return self.code
 def kill(self):self.finish=self.clock();self.code=1
class Sink:
 def __init__(self,path,fail_close=False,fail_flush=False):self.file=path.open('xb');self.name=path.name;self.fail_close=fail_close;self.fail_flush=fail_flush;self.attempts=0
 def write(self,data):return self.file.write(data)
 def flush(self):
  if self.fail_flush:raise OSError('modeled sink flush error')
  self.file.flush()
 def close(self):
  self.attempts+=1
  if self.fail_close:raise OSError('modeled first sink close error')
  self.file.close()
class Job:
 def __init__(self,clock,root,mode):
  self.clock,self.process,self.mode=clock,root,mode;self.pid=100;self.created=False;self.calls=0;self.closed=False;self.close_calls=0
  self.handles={};self.owned=[];self.extra_alive='unexpected' in mode;self.extra_seen=self.extra_alive
  self.extra=Handle('unexpected-child-held-handle',502);self.controller=dict(pid=100,birth=10000,exited=False,exit_code=259,exit_time=0,kernel_time=0,user_time=0)
  self.baseline=dict(total=1,active=1,terminated=0,page_faults=0,ids=[100])
 def sample(self):
  self.calls+=1
  if self.mode=='query_error' and self.calls>=3:raise OSError('later modeled job query failure')
  ids=[100]+([200] if self.created and self.process.poll() is None else [])+([300] if self.extra_alive else [])
  return dict(total=1+int(self.created)+int(self.extra_seen),active=len(ids),terminated=0,page_faults=100+self.calls,ids=sorted(ids),total_user_time=0,total_kernel_time=0,period_user_time=0,period_kernel_time=0)
 def bind(self,process):
  assert process is self.process;self.handles[200]=(501,process.birth);return self.root(process)
 def root(self,process):
  assert process is self.process
  if self.handles.get(200)!=(501,process.birth):raise ValueError('unbound modeled root')
  exited=process.poll() is not None
  return dict(pid=200,birth=process.birth,exit_time=30000 if exited else 0,kernel_time=0,user_time=0,exited=exited,exit_code=process.poll() if exited else 259)
 def hold_unexpected(self,pid):
  assert pid==300;self.handles[300]=(502,25000)
  if self.extra not in self.owned:self.owned.append(self.extra)
  return dict(pid=300,birth=25000,exited=not self.extra_alive,exit_time=35000 if not self.extra_alive else 0,kernel_time=0,user_time=0,exit_code=0 if not self.extra_alive else 259)
 def terminate(self,pid):
  assert pid!=100 and pid in self.handles
  if pid==200:self.process.kill()
  elif pid==300:self.extra_alive=False
 def close_held(self):
  self.close_calls+=1
  for handle in self.owned:handle.close()
  self.closed=True
class Streams:
 def __init__(self,out,clock,root,mode):
  self.clock,self.process,self.mode=clock,root,mode;self.calls=0;self.position=0;self.eof=dict.fromkeys(w.LIMITS,False)
  self.files={name:Sink(out/(name+'.log'),fail_close=name=='stdout' and 'close_error' in mode,fail_flush=name=='stdout' and mode=='flush_error') for name in w.LIMITS}
  self.pipes={};self.counts=dict.fromkeys(w.LIMITS,0);self.retained=dict(self.counts);self.errors={}
 def attach(self,process):assert process is self.process;self.pipes={'stdout':process.stdout,'stderr':process.stderr}
 def poll(self,deadline,clock):
  self.calls+=1
  if self.mode=='pipe_error' and self.calls==2:raise OSError('later modeled pipe error')
  if self.position<len(RAW):
   block=RAW[self.position:self.position+65536];self.position+=len(block);self.files['stdout'].write(block);self.counts['stdout']+=len(block);self.retained['stdout']+=len(block)
  if self.process.poll() is not None and self.position==len(RAW) and self.mode!='no_eof':self.eof=dict.fromkeys(w.LIMITS,True)
  return self.mode=='overflow' and self.calls>=3
 def state(self):
  if self.mode=='state_error':raise OSError('modeled stream state error')
  return dict(eof=dict(self.eof),complete=all(self.eof.values()) and not(self.mode=='overflow' and self.calls>=3))
 def close(self):
  # Execute the actual source close ordering over four DISTINCT resources.
  w.PipeRetention.close(self)
  if self.mode=='late_close':self.clock.sleep(2.)
 def force(self):
  for sink in self.files.values():
   if not sink.file.closed:sink.file.close()
  for pipe in self.pipes.values():pipe.closed=True

def model(mode):
 clock=Clock();process=RootProcess(clock);job=Job(clock,process,mode)
 with tempfile.TemporaryDirectory() as td:
  out=Path(td);target=out/'project';target.mkdir()
  for name in ('reference.gd',w.reference.BINARY_CASES_NAME):(target/name).write_bytes((ROOT/w.PROJECT/name).read_bytes())
  streams=Streams(out,clock,process,mode);assert len({id(process),id(job),id(streams)})==3
  captured=[];original=w.Audit
  class CapturedAudit(original):
   def __init__(self,*args):super().__init__(*args);captured.append(self)
  def spawn(command,**options):job.created=True;return process
  result=None;escaped=None
  try:
   with patch.object(w,'Audit',CapturedAudit):result=w.execute_prepared(out/w.MEMBER,target,out,PAYLOAD,101,clock=clock,sleep=clock.sleep,process_factory=spawn,job_factory=lambda:job,stream_factory=lambda path:streams)
  except BaseException as error:escaped=dict(type=type(error).__name__,message=str(error),traceback=traceback.format_exc())
  audit=captured[0].receipt() if captured else None
  resources=dict(sinks={name:dict(attempts=sink.attempts,closed=sink.file.closed) for name,sink in streams.files.items()},pipes={name:dict(attempts=pipe.attempts,closed=pipe.closed) for name,pipe in streams.pipes.items()},owned_extra=dict(token=502,attempts=job.extra.attempts,closed=job.extra.closed),job_close_calls=job.close_calls,job_closed=job.closed,process_waited=process.waited)
  expected_pass=mode=='normal';structured=isinstance(result,dict);expected_audit=mode in ('normal','pipe_error','query_error','unexpected')
  obligations=dict(structured_failed_or_success_return=structured and result['passed']==expected_pass,owned_close_attempted=job.closed,final_times_recorded=structured and 'finished' in result and 'elapsed' in result)
  if expected_audit:obligations['prefailure_audit_retained']=structured and result.get('audit')==audit
  row=dict(name=mode,source_scope='injected source lifecycle only; no native process',input=dict(root_pid=200,root_handle=501,root_birth=20000,controller_pid=100,controller_birth=10000,extra_pid=300,extra_handle=502,extra_birth=25000,deadline=101,raw_bytes=len(RAW),raw_sha256=hashlib.sha256(RAW).hexdigest(),distinct_objects=True),expected_pass=expected_pass,result=result,escaped=escaped,actual_source_audit=audit,resources=resources,obligations=obligations,matched=all(obligations.values()))
  streams.force();return row
rows=[model(mode) for mode in ('normal','close_error','unexpected_close_error','state_error','flush_error','late_close','pipe_error','query_error','unexpected','no_eof','overflow')]
# Direct actual PipeRetention.close: first error must not skip three later resources.
class CloseWitness:
 def __init__(self,name,fail=False):self.name=name;self.fail=fail;self.attempts=0;self.closed=False
 def close(self):
  self.attempts+=1
  if self.fail:raise OSError('first resource failure')
  self.closed=True
resources=[CloseWitness('stdout-sink',True),CloseWitness('stderr-sink'),CloseWitness('stdout-pipe'),CloseWitness('stderr-pipe')]
assert len({id(r) for r in resources})==4
obj=w.PipeRetention.__new__(w.PipeRetention);obj.files=dict(zip(('stdout','stderr'),resources[:2]));obj.pipes=dict(zip(('stdout','stderr'),resources[2:]))
try:obj.close();error=None
except OSError as e:error=str(e)
rows.append(dict(name='direct_pipe_close_first_error',error=error,resources=[vars(r) for r in resources],matched=all(r.attempts==1 for r in resources),scope='source finalizer objects, no OS descriptors'))
# Actual close_held over two independent held handle IDs, fake kernel only.
class Kernel:
 def __init__(self):self.attempts=[]
 def CloseHandle(self,h):self.attempts.append(h);return 0 if h==501 else 1
job=w.WindowsJob.__new__(w.WindowsJob);job.k=Kernel();job.owned_handles=[501,502]
def checked(value,label):
 if not value:raise OSError(label)
 return value
job.ok=checked
try:job.close_held();error=None
except OSError as e:error=str(e)
rows.append(dict(name='direct_held_close_first_error',error=error,attempts=job.k.attempts,held_after=job.owned_handles,matched=job.k.attempts==[501,502],scope='fake CloseHandle function, no Windows API'))
# API robustness only. These snapshots lack an established single-controller
# creation history for1->2, and cannot support a native/source verdict by themselves.
for first,final in ((1,1),(1,2),(2,2)):
 class Observations:
  pid=100
  def __init__(self):self.calls=0
  def sample(self):
   self.calls+=1;total=first if self.calls==1 else final
   return dict(total=total,active=1,terminated=0,ids=[100])
 job=Observations();clock=Clock();result=w.cleanup_unreturned(job,None,105,clock=clock,sleep=clock.sleep)
 rows.append(dict(name='coverage_observation_'+str(first)+'_'+str(final),scope='API-observation robustness MODEL ONLY; lifecycle feasibility unestablished, excluded from source verdict',input=dict(first_total=first,final_total=final),result=result,expected_coverage=final==1,matched=result['identity_coverage_complete']==(final==1)))
with gzip.open(OUT/'all-results.jsonl.gz','wt',encoding='utf-8') as stream:
 for row in rows:stream.write(json.dumps(row,sort_keys=True)+'\n')
summary=dict(source='b16b012d720c0981cfc28146a651b3ba5f8a9caa',cpu=[4],actual_native_invocations=0,controls=len(rows),source_controls=[dict(name=r['name'],matched=r['matched'],obligations=r.get('obligations'),resources=r.get('resources'),escaped_type=(r.get('escaped') or {}).get('type')) for r in rows if not r.get('name','').startswith('coverage_observation')],robustness_only=[dict(name=r['name'],matched=r['matched']) for r in rows if r.get('name','').startswith('coverage_observation')])
(OUT/'SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
