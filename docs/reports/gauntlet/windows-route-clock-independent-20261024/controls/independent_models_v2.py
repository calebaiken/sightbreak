#!/usr/bin/env python3
"""Independent exact-helper models; no native calls, OS sleep or builder mocks."""
import argparse, ast, ctypes as C, hashlib, json, math, os
from fractions import Fraction as F
from pathlib import Path
import subprocess, time

BASE='7101350e5d0a2f6e4afb9a913b5b1bcf2107857a'
CANDIDATE='4cf6ac8e744603ed6af122a362036d276754cc76'

def h(data):return hashlib.sha256(data).hexdigest()
def clean(value):
 if isinstance(value,float) and not math.isfinite(value):return repr(value)
 if isinstance(value,dict):return {str(k):clean(v) for k,v in value.items()}
 if isinstance(value,(tuple,list,set)):return [clean(v) for v in value]
 if isinstance(value,(str,int,float,bool)) or value is None:return value
 return repr(value)

def helper(source):
 tree=ast.parse(source)
 cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='WinUI')
 method=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='key_pulse')
 module=ast.Module(body=[method],type_ignores=[])
 namespace={'C':C,'time':time}
 exec(compile(ast.fix_missing_locations(module),'<exact frozen key_pulse>','exec'),namespace)
 return namespace['key_pulse'],h(ast.dump(method,include_attributes=False).encode())

def fault(name):
 if name=='nan':return float('nan')
 if name=='inf':return float('inf')
 if name=='-inf':return -float('inf')
 if name=='bool':return True
 if name=='string':return '0'
 if name=='none':return None
 if name=='backward':return -100000
 if name=='oserror':raise OSError('independent declared clock failure')
 if name=='interrupt':raise KeyboardInterrupt('independent cancellation')
 if name=='exit':raise SystemExit('independent cancellation')
 raise AssertionError(name)

class World:
 def __init__(self,**config):
  self.cfg=config;self.t=F(0);self.events=[];self.waits=[];self.reads=[];self.held=set(config.get('initial_held',()))
  self.receipt={};self.window=34;self.pid=12;self.tick=config.get('tick');self.phase=F(str(config.get('phase',0)))
  self.epoch=config.get('epoch',767.968);self.watch_epoch=config.get('watch_epoch',1234567)
  self.watch_rate=F(str(config.get('watch_rate',1)));self.watch_started=None;self.route_calls=0;self.watch_calls=0
  self.user=self;self.sleep_returns=0;self.first_expiry=None
 def stage(self):
  checks=self.receipt.get('down_checks',[])
  if checks and checks[-1]['status']=='IN_PROGRESS':return 'before_'+checks[-1]['key']
  if not self.events:return 'preflight'
  return 'after_down' if self.events[-1]['down'] else 'after_release'
 def advance(self,amount):self.t+=F(str(amount))
 def IsWindowVisible(self,window):
  stage=self.stage();self.reads.append({'stage':stage,'time':float(self.t)})
  self.advance(self.cfg.get('state_cost',0)+self.cfg.get('stage_cost',{}).get(stage,0))
  if self.cfg.get('state_error')==stage:raise OSError('independent unreadable '+stage)
  if self.cfg.get('state_change')==stage:
   self.held.update(self.cfg.get('foreign_held',()))
  return not (self.cfg.get('state_change')==stage and self.cfg.get('state_field')=='visible')
 def GetWindowThreadProcessId(self,window,pointer):
  changed=self.cfg.get('state_change')==self.stage() and self.cfg.get('state_field')=='owner'
  C.cast(pointer,C.POINTER(C.c_uint32))[0]=99 if changed else self.pid
  return 56
 def GetForegroundWindow(self):
  changed=self.cfg.get('state_change')==self.stage() and self.cfg.get('state_field')=='focus'
  return 99 if changed else self.window
 def GetAsyncKeyState(self,vk):return 0x8000 if ('lmb' if vk==1 else chr(vk).lower()) in self.held else 0
 def key(self,name,down):
  self.events.append({'key':name,'down':down,'time':float(self.t)})
  self.advance(self.cfg.get('down_cost' if down else 'up_cost',0))
  if down:self.held.add(name)
  elif name not in self.cfg.get('up_error',()):self.held.discard(name)
  if name in self.cfg.get('down_error' if down else 'up_error',()):raise OSError('independent declared edge failure')
 def active_fault(self,kind):
  mode=self.cfg.get(kind+'_fault_when')
  edges=self.receipt.get('edges',[]);last=edges[-1] if edges else {}
  if mode=='after_first_read':return (self.route_calls if kind=='route' else self.watch_calls)>1
  if mode=='at_down_pre':return last.get('down') is True and 'before_monotonic' not in last
  if mode=='at_down_post':return bool(self.events and self.events[-1]['down']) and not any(not e['down'] for e in self.events)
  if mode=='after_sleep_return':return self.sleep_returns>0 and not any(not e['down'] for e in self.events)
  if mode=='at_release_pre':return last.get('down') is False and 'before_monotonic' not in last
  if mode=='at_release_post':return last.get('down') is False and 'before_monotonic' in last and 'after_monotonic' not in last and 'after_clock_error' not in last and bool(self.events and not self.events[-1]['down'])
  if mode=='at_final_record':return bool(self.receipt.get('os_states') and self.receipt['os_states'][-1]['label']=='after_release')
  return mode=='always' or mode=='after_two_downs' and sum(e['down'] for e in self.events)>=2
 def clock(self):
  self.route_calls+=1
  if self.route_calls>100000:raise RuntimeError('HARNESS ABORT: model exceeded 100000 clock reads')
  if self.active_fault('route'):return fault(self.cfg['route_fault'])
  delta=self.t
  if self.cfg.get('frozen') or delta<F(str(self.cfg.get('freeze_until',0))):delta=F(0)
  if self.tick:
   tick=F(str(self.tick));delta=((delta+self.phase)//tick)*tick
  return self.epoch+float(delta)
 def elapsed(self):
  self.watch_calls+=1
  if self.active_fault('watch'):return fault(self.cfg['watch_fault'])
  if self.watch_started is None:self.watch_started=self.t
  value=self.watch_epoch+float(self.t*self.watch_rate)
  if self.first_expiry is None and 'elapsed_watchdog_start' in self.receipt and value-self.receipt['elapsed_watchdog_start']>=self.receipt['elapsed_watchdog_budget_seconds']:
   self.first_expiry={'event_index':len(self.events),'sleep_index':len(self.waits),'value':value}
  return value
 def sleep(self,seconds):
  assert type(seconds) in (int,float) and math.isfinite(seconds) and seconds>0,'invalid sleeper request'
  now=self.clock();remaining=self.receipt['hold_until_monotonic']-now
  assert seconds<=remaining,'sleep exceeds unchanged route-clock H'
  elapsed=0 if self.watch_started is None else float((self.t-self.watch_started)*self.watch_rate)
  budget=self.receipt.get('elapsed_watchdog_budget_seconds')
  if budget is not None:assert seconds<=budget-elapsed+1e-8,'sleep exceeds original elapsed allowance'
  self.waits.append({'request':seconds,'route_before':now,'time':float(self.t),'watch_elapsed':elapsed})
  if self.cfg.get('sleep_error'):fault(self.cfg['sleep_error'])
  quantum=F(1,10_000_000);amount=F.from_float(seconds)*F(str(self.cfg.get('wake_ratio',1)))
  units=-(-amount//quantum);self.t+=units*quantum
  if self.cfg.get('sleep_extra'):self.advance(self.cfg['sleep_extra'])
  self.sleep_returns+=1

def trial(name,implementation,fn,expected=True,**config):
 world=World(**config);error=None
 seconds=config.get('seconds',.12567175974707734);names=config.get('names',('w','d'));remaining=config.get('remaining',4)
 deadline=config.get('deadline',world.epoch+remaining)
 try:
  kwargs={'deadline':deadline,'receipt':world.receipt,'clock':world.clock,'sleep':world.sleep}
  if implementation=='candidate':kwargs['elapsed_clock']=world.elapsed
  fn(world,names,seconds,**kwargs)
 except BaseException as exc:error={'type':type(exc).__name__,'message':str(exc)}
 accepted=error is None
 failures=[]
 if accepted!=expected:failures.append('unexpected outcome')
 attempted=world.receipt.get('attempted_keys',[])
 ups=[e['key'] for e in world.events if not e['down']]
 if ups!=attempted:failures.append('not every owned attempt received exactly one up attempt')
 if accepted:
  r=world.receipt
  if r.get('status')!='API_RETURNED_WITH_OS_RELEASE' or not r.get('release_complete') or world.held:failures.append('invalid successful release result')
  if not r['finished_monotonic']>=r['hold_until_monotonic'] or not r['finished_monotonic']<deadline:failures.append('success outside fixed route boundary')
  # H starts after initial preflight; all later work must consume this fixed H.
  expected_h=min(r['os_states'][0]['read_end_monotonic']+seconds,deadline)
  if r['hold_until_monotonic']!=expected_h:failures.append('target changed or setup target mismatch')
 if config.get('no_downs') and any(e['down'] for e in world.events):failures.append('fault/invalid request dispatched a down')
 if config.get('only_first_down') and [e['key'] for e in world.events if e['down']]!=['w']:failures.append('second down bypassed failed check')
 if config.get('frozen') and implementation=='candidate' and world.watch_rate==1:
  used=float((world.t-world.watch_started)*world.watch_rate)
  if used>remaining+1e-6:failures.append('frozen-route model exceeded original watchdog allowance')
 if config.get('freeze_until') and accepted and float(world.t)<=seconds:failures.append('did not exercise operation-longer-than-pulse watchdog case')
 if world.first_expiry is not None:
  if accepted:failures.append('expired elapsed operation returned success')
  if any(e['down'] for e in world.events[world.first_expiry['event_index']:]):failures.append('down dispatched after elapsed expiry was observed')
  if len(world.waits)>world.first_expiry['sleep_index']:failures.append('slept again after elapsed expiry was observed')
 return clean({'first_expiry':world.first_expiry,'name':name,'implementation':implementation,'expected_acceptance':expected,'accepted':accepted,'met_expectation':not failures,'failures':failures,'config':config,'error':error,'model_time':float(world.t),'events':world.events,'waits':world.waits,'clock_reads':world.route_calls,'watchdog_reads':world.watch_calls,'receipt':world.receipt})

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--source',type=Path,required=True);parser.add_argument('--baseline',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
 assert sorted(os.sched_getaffinity(0))==[4]
 source=(args.source/'scripts/verify_integration_export.py').read_bytes();base=args.baseline.read_bytes()
 current,ca=helper(source);previous,ba=helper(base)
 args.output.mkdir(parents=True,exist_ok=False)
 results=[]
 def run(name,expected=True,**cfg):results.append(trial(name,'candidate',current,expected,**cfg))
 for tick in (None,.001,.015625,.0625,.25):
  phases=(0,) if tick is None else (0,tick/8,tick/2,tick*7/8)
  for phase in phases:
   for epoch in (0,767.968,2**40):
    for duration in (.0004,.015625,.12567175974707734,2.5):
     run('quantized_phase',tick=tick,phase=phase,epoch=epoch,seconds=duration)
 for tick in (None,.015625):
  for ratio in (1/3,2/3):
   for epoch in (-10000,0,1000000):run('genuine_early_wakes',tick=tick,phase=.003,wake_ratio=ratio,watch_epoch=epoch)
 run('state_dispatch_costs',state_cost=.003,down_cost=.01,up_cost=.002,remaining=.5)
 run('late_second_state',False,stage_cost={'before_d':.2},seconds=.125,only_first_down=True)
 run('late_post_down_state',False,stage_cost={'after_down':.2},seconds=.125)
 for rate in (.5,1,2):
  for epoch in (-10000,0,1000000):run('frozen_route',False,frozen=True,watch_rate=rate,watch_epoch=epoch,seconds=.03,remaining=.2)
 run('watchdog_is_operation_remaining',freeze_until=.08,seconds=.03,remaining=.2)
 for remaining in (.125,.08):run('deadline_clip_or_equal',False,remaining=remaining,seconds=.125)
 run('oversleep',False,remaining=.2,seconds=.125,sleep_extra=.3)
 run('late_release',False,remaining=.2,seconds=.125,up_cost=.1)
 run('late_release_state',False,remaining=.2,seconds=.125,stage_cost={'after_release':.3})
 for value in (0,-1,2.5001,float('nan'),float('inf'),True):run('invalid_duration',False,seconds=value,no_downs=True)
 for value in (float('nan'),float('inf'),-float('inf'),True):run('invalid_deadline',False,deadline=value,no_downs=True)
 for names in ((),('w','w'),('w','s'),('a','d'),('q',),('w','d','a'),'w',(True,)):
  run('invalid_keys',False,names=names,no_downs=True)
 for kind in ('route','watch'):
  for value in ('nan','inf','-inf','bool','string','none','backward','oserror','interrupt','exit'):
   for when in ('always','after_two_downs'):
    actual_when='after_first_read' if value=='backward' and when=='always' else when
    run('invalid_'+kind+'_'+value+'_'+actual_when,False,**{kind+'_fault_when':actual_when,kind+'_fault':value,'no_downs':when=='always'})
 run('consistent_negative_epochs',epoch=-100000,watch_epoch=-20000)
 for value in ('backward','nan','inf','-inf'):
  for when in ('at_down_pre','at_down_post','after_sleep_return','at_release_pre','at_release_post','at_final_record'):
   run('route_fault_stage_'+value+'_'+when,False,route_fault_when=when,route_fault=value,no_downs=when=='at_down_pre')
  for when in ('at_down_post','after_sleep_return','at_final_record'):
   run('watchdog_fault_stage_'+value+'_'+when,False,watch_fault_when=when,watch_fault=value)
 for value in ('oserror','interrupt','exit'):run('sleep_exception_'+value,False,sleep_error=value)
 for stage in ('preflight','before_w','before_d','after_down','after_release'):
  run('state_exception_'+stage,False,state_error=stage,no_downs=stage in ('preflight','before_w'))
 for stage in ('before_w','before_d'):
  for field in ('owner','focus','visible'):
   run('state_gate_'+stage+'_'+field,False,state_change=stage,state_field=field,no_downs=stage=='before_w',only_first_down=stage=='before_d')
 run('physically_nonneutral_before',False,initial_held=('a',),no_downs=True)
 run('foreign_input_before_second',False,state_change='before_d',foreign_held=('a',),only_first_down=True)
 run('partial_down_failure',False,down_error=('d',))
 run('up_failure',False,up_error=('w',))
 run('partial_down_and_up_failure',False,down_error=('d',),up_error=('w',))
 # The old method is compiled from exact retained source, never patched for comparison.
 results.append(trial('old_coarse_clock_boundary','base',previous,False,tick=.015625,epoch=767.968,seconds=.12567175974707734))
 results.append(trial('candidate_same_coarse_boundary','candidate',current,True,tick=.015625,epoch=767.968,seconds=.12567175974707734))
 summary={'candidate':CANDIDATE,'baseline':BASE,'source_sha256':h(source),'baseline_sha256':h(base),'candidate_helper_ast_sha256':ca,'base_helper_ast_sha256':ba,'cpu_affinity':sorted(os.sched_getaffinity(0)),'cases':len(results),'passed':sum(r['met_expectation'] for r in results),'failures':[{'index':i,'name':r['name'],'failures':r['failures'],'error':r['error']} for i,r in enumerate(results) if not r['met_expectation']],'native_executed':False}
 (args.output/'cases.json').write_text(json.dumps(results,indent=2,allow_nan=False)+'\n');(args.output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
 print(json.dumps(summary,indent=2));return int(bool(summary['failures']))

if __name__=='__main__':raise SystemExit(main())
