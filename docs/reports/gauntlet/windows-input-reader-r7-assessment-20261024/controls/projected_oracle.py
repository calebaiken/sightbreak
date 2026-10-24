#!/usr/bin/env python3
"""Independent concrete PeerLifecycle replay and projected alternative closure."""
import argparse,hashlib,importlib.util,itertools,json,os
from pathlib import Path

class Lifecycle:
 def __init__(self,at):
  assert at>=0;self.now=at;self.last_input=at;self.deadline=at+20000;self.joined=False;self.rejected=False;self.events=[['connected',at]]
 def admitted(self,at):
  assert self.now<=at<self.deadline and not self.rejected;self.now=at;self.joined=True;self.last_input=at;self.events.append(['admitted',at])
 def active(self,at):
  assert self.now<=at and self.joined and not self.rejected and at-self.last_input<30000;self.now=at;self.last_input=at;self.events.append(['active',at])
 def reject(self,at):
  assert at>=self.now and not self.rejected;self.now=at;self.rejected=True;self.deadline=at+500;self.events.append(['reject',at])
 def observe(self,at):
  assert at>=self.now;return dict(wall_msec=at,input_age_msec=at-self.last_input,deadline_remaining_msec=self.deadline-at,joined=self.joined)
 def expired(self,at):return ((self.rejected or not self.joined) and at>=self.deadline) or (self.joined and at-self.last_input>=30000)

def alternatives(row):
 now,age,remaining,joined=(row[k] for k in ('wall_msec','input_age_msec','deadline_remaining_msec','joined'));witnesses=[]
 if age<0 or age>now:return witnesses
 last=now-age;deadline=now+remaining
 # The unmodified source gives a unique connection time for an unrejected
 # deadline. Replay that concrete source history, including any activity chain.
 connected=deadline-20000
 if 0<=connected<=last and (joined or connected==last):
  s=Lifecycle(connected)
  if joined:
   s.admitted(connected)
   while s.last_input<last:s.active(min(last,s.last_input+29999))
  assert s.observe(now)==row;witnesses.append(dict(rejected=False,eligible=s.expired(now),events=s.events))
 # For a rejected deadline the sole reject time is deadline-500. A concrete
 # source witness can connect/admit at final last_input, then reject afterward.
 rejection=deadline-500
 if last<=rejection<=now:
  s=Lifecycle(last)
  if joined:s.admitted(last)
  s.reject(rejection);assert s.observe(now)==row;witnesses.append(dict(rejected=True,eligible=s.expired(now),events=s.events))
 return witnesses

def corpus():
 cases=[]
 for now in [0,1,499,500,19999,20000,20001,29999,30000,30001,50000,100000]:
  ages=sorted({-1,0,1,499,500,501,19999,20000,29999,30000,30001,now,now+1})
  remaining=sorted({-now-1,-now,-30000,-20000,-500,-1,0,1,499,500,501,19999,20000,20001})
  for age,rem,joined in itertools.product(ages,remaining,[False,True]):
   row=dict(wall_msec=now,input_age_msec=age,deadline_remaining_msec=rem,joined=joined);w=alternatives(row);eligible=[x['eligible'] for x in w]
   expected='INVALID' if not any(eligible) else 'CONSISTENT' if all(eligible) else 'UNKNOWN'
   cases.append(dict(row=row,source_witnesses=w,expected=expected))
 return cases

def main():
 p=argparse.ArgumentParser();p.add_argument('--prototype',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert sorted(os.sched_getaffinity(0))==[4];a.output.mkdir(parents=True,exist_ok=False)
 cases=corpus() # independent expected source histories fixed before import
 spec=importlib.util.spec_from_file_location('unfrozen_expiry_candidate',a.prototype);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);counts={k:0 for k in ['CONSISTENT','UNKNOWN','INVALID']};mismatches=[]
 with (a.output/'CASES.jsonl').open('w') as stream:
  for i,c in enumerate(cases,1):
   error=None
   try:actual=m.expiry_projection(c['row'])
   except (ValueError,KeyError,TypeError) as e:actual='INVALID';error=type(e).__name__+': '+str(e)
   counts[c['expected']]+=1;r=dict(id=i,**c,actual=actual,error=error,matched=actual==c['expected']);stream.write(json.dumps(r,separators=(',',':'))+'\n')
   if not r['matched']:mismatches.append(r)
 summary=dict(scope='UNFROZEN isolated projected-state guard only; not history/whole-reader approval',prototype_sha256=hashlib.sha256(a.prototype.read_bytes()).hexdigest(),cases=len(cases),matches=len(cases)-len(mismatches),expected=counts,mismatches=mismatches,cpu_affinity=[4],native_executed=False)
 (a.output/'SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2));return int(bool(mismatches))
if __name__=='__main__':raise SystemExit(main())
