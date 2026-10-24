#!/usr/bin/env python3
"""Independent operation/capture clocks and finite call-reachability witnesses."""
import argparse,copy,hashlib,importlib.util,json,os
from pathlib import Path
from projected_oracle import Lifecycle
cp=copy.deepcopy

def row(peer,time,reason,count=0):
 return {**peer.observe(time),'reason':reason,'peer_bound':peer.joined,'bound_actor':1 if peer.joined else 0,'counters':{'input_accepted':count} if count else {}}
def base(C=1000):
 s=Lifecycle(C);rows=[row(s,C,'peer_connected')];s.admitted(C+1);rows.append(row(s,C+1,'peer_bound'));return s,rows

def corpus():
 cases=[]
 def add(name,rows,expected,witness,other=None):cases.append(dict(name=name,rows=cp(rows),expected=expected,witness=cp(witness),known_other_calls=other or {}))
 for C in [0,1000,20000]:
  for off in [0,1,19999]:
   for delay in [0,1,500,20000,30000]:
    s=Lifecycle(C);rows=[row(s,C,'peer_connected')];s.admitted(C+off);bound=C+off+delay;rows.append(row(s,bound,'peer_bound'));expiry=max(bound+1,s.last_input+30000);rows.append(row(s,expiry,'peer_expired'));assert s.expired(expiry);add('admit-'+str(C)+'-'+str(off)+'-observe-delay'+str(delay),rows,'CONSISTENT',s.events)
  s=Lifecycle(C);rows=[row(s,C,'peer_connected')];s.joined=True;s.last_input=C+20000;rows.append(row(s,C+20001,'peer_bound'));rows.append(row(s,C+50000,'peer_expired'));add('invalid-admission-at-deadline-'+str(C),rows,'INVALID',[['impossible_admitted_at_join_deadline',C+20000]])
 for receive_delay in [0,1,2,30001]:
  for active_delay in [0,1]:
   for post_delay in [0,1,30000]:
    s,rows=base();old=s.last_input;gate=old+29999;assert s.joined and not s.rejected and gate-old<30000;received=gate+receive_delay;rows.append(row(s,received,'input_received'));at=received+active_delay
    if at-s.last_input<30000:s.active(at)
    else:s.events.append(['active_no_refresh_due_idle',at])
    accepted=at+post_delay;rows.append(row(s,accepted,'input_accepted',1));expiry=max(accepted+1,s.last_input+30000);rows.append(row(s,expiry,'peer_expired',1));assert s.expired(expiry);add('rpc-rx'+str(receive_delay)+'-active'+str(active_delay)+'-post'+str(post_delay),rows,'CONSISTENT',[*s.events,['allow_input_true',gate]])
 for previous_offset in [0,29998,29999,30000,30001]:
  for advance in [0,1,29999,30000,59998,60000]:
   for budget in [0,1,2,3]:
    s,rows=base();old=s.last_input;previous=old+previous_offset;target=previous+advance;rows.append(row(s,previous,'authority_tick'));steps=[];at=old
    feasible=target==old or previous-old<30000
    if target>old:
     while at<target:at=min(target,at+29999);steps.append(at)
     feasible &= bool(steps) and steps[0]>=previous and len(steps)<=budget
    expected=('UNKNOWN' if budget else 'CONSISTENT') if feasible else 'INVALID'
    if feasible:
     for at in steps:s.active(at)
     events=s.events+[['unallocated_possible_foreign_calls',budget-len(steps)]]
    else:
     s.last_input=target;events=[['counterfactual_unreachable_last_input',target],['budget',budget],['mathematical_source_steps',steps]]
    now=target+1;rows.append(row(s,now,'authority_tick',budget));rows.append(row(s,now+30000,'peer_expired',budget));add('reach-prev'+str(previous_offset)+'-advance'+str(advance)+'-A'+str(budget),rows,expected,events)
 for other in [1,2,3]:
  s,rows=base();now=s.last_input+100;rows.append(row(s,now,'authority_tick',other));rows.append(row(s,s.last_input+30000,'peer_expired',other));add('known-foreign-'+str(other)+'-unchanged',rows,'CONSISTENT',s.events+[['observed_other_peer_accepts',other]],{2:other})
  altered=cp(rows);altered[2]['input_age_msec']=0;altered[3]['input_age_msec']=altered[3]['wall_msec']-now;add('known-foreign-'+str(other)+'-cannot-fund-local',altered,'INVALID',s.events+[['known_other_calls_no_local_activity',other]],{2:other})
 return cases

def main():
 p=argparse.ArgumentParser();p.add_argument('--prototype',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert sorted(os.sched_getaffinity(0))==[4];a.output.mkdir(parents=True,exist_ok=False);cases=corpus()
 spec=importlib.util.spec_from_file_location('held_persistent_hypothesis_candidate',a.prototype);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);results=[]
 for c in cases:
  h=m.LifecycleHypotheses(c['rows'][0]);actual=None;error=None
  try:
   for i,r in enumerate(c['rows'][1:],1):
    for _ in range(c['known_other_calls'].get(i,0)):h.other_accepted()
    if r['reason']=='peer_expired':actual=h.expiry(r,r['bound_actor'])
    else:h.observe(r,r['bound_actor'])
  except (ValueError,KeyError,TypeError) as e:actual='INVALID';error=type(e).__name__+': '+str(e)
  result={**c,'actual':actual,'matched':actual==c['expected'],'error':error,'model_detail':h.detail,'model_errors':h.errors,'model_states':h.states};results.append(result);(a.output/(c['name']+'.json')).write_text(json.dumps(result,indent=2)+'\n')
 s=dict(scope='Independent isolated persistent lifecycle source-time/call assessment',prototype_sha256=hashlib.sha256(a.prototype.read_bytes()).hexdigest(),cases=len(results),matches=sum(r['matched'] for r in results),mismatches=[{k:r[k] for k in ['name','expected','actual','model_detail','model_errors']} for r in results if not r['matched']],cpu_affinity=[4],native_executed=False);(a.output/'SUMMARY.json').write_text(json.dumps(s,indent=2)+'\n');print(json.dumps(s,indent=2));return int(bool(s['mismatches']))
if __name__=='__main__':raise SystemExit(main())
