#!/usr/bin/env python3
import argparse,hashlib,json,os,sys
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert sorted(os.sched_getaffinity(0))==[4];a.output.mkdir(parents=True,exist_ok=False);sys.path.insert(0,str(a.source/'scripts'));import analyze_input_consumption as m
cases=[]
def row(reason,t,peer=0,gen=-1,joined=False,L=None,D=None,actor=0,last=0):return dict(reason=reason,wall_msec=t,peer=peer,generation=gen,joined=joined,input_age_msec=t-L if L is not None else -1,deadline_remaining_msec=D-t if D is not None else -1,bound_actor=actor,peer_bound=actor>0,last_bound_actor=last)
def counted(spec):
 result=[];counts={}
 for r,visible in spec:
  counts[r['reason']]=counts.get(r['reason'],0)+1;r={**r,'counters':dict(counts)}
  if visible:result.append(r)
 return result
for delay in [0,1,19999,20000,20001,100000]:cases.append(dict(name='delayed-connect-'+str(delay),rows=counted([(row('ready',1000),True),(row('peer_connected',2000+delay,9,1,False,2000,22000),True)]),expected='POSSIBLE'))
for delay in [0,1,8001,30000]:cases.append(dict(name='delayed-admission-'+str(delay),rows=counted([(row('ready',1000),True),(row('peer_connected',2000,9,1,False,2000,22000),True),(row('peer_bound',21999+delay,9,1,True,21999,22000,1,1),True)]),expected='POSSIBLE'))
for delta in [0,1]:cases.append(dict(name='gate-crosses-idle-'+str(delta),rows=counted([(row('ready',1000),True),(row('peer_connected',2000,9,1,False,2000,22000),True),(row('peer_bound',3000,9,1,True,3000,22000,1,1),True),(row('input_received',33000+delta,9,1,True,3000,22000,1,1),True),(row('input_accepted',33002+delta,9,1,True,3000,22000,1,1),True)]),expected='POSSIBLE',witness='allow_input32999 before idle; processing/active33001+ cannot refresh L3000'))
for kind in ['input_gate_rejected','input_decode_rejected']:
 spec=[(row('ready',0),True),(row('peer_connected',1,9,1,False,1,20001),True),(row('peer_bound',2,9,1,True,2,20001,1,1),True),(row('peer_connected',3,10,2,False,3,20003,0,1),True),(row('peer_bound',4,10,2,True,4,20003,2,2),True),(row(kind,5,9,1,True,2,20001,1,1),False),(row('authority_tick',6,9,1,True,2,20001,1,1),True)]
 cases.append(dict(name='hidden-selection-'+kind,rows=counted(spec),expected='UNKNOWN'))
spec=[(row('ready',0),True),(row('peer_connected',1,9,1,False,1,20001),True),(row('peer_bound',2,9,1,True,2,20001,1,1),True),(row('peer_connected',3,10,2,False,3,20003,0,1),True),(row('peer_disconnected',4,9,1,True,2,20001,1,1),True),(row('input_gate_rejected',5,10,2,False,3,20003,0,1),False),(row('authority_tick',6,10,2,False,3,20003,0,1),True)];cases.append(dict(name='hidden-pending-peer-selection',rows=counted(spec),expected='UNKNOWN'))
results=[]
for c in cases:
 error=None
 try:m.authority_lifecycle_foundation(c['rows']);actual='POSSIBLE'
 except m.UnknownTransition as e:actual='UNKNOWN';error=str(e)
 except (ValueError,KeyError,TypeError) as e:actual='INVALID';error=str(e)
 r={**c,'actual':actual,'matched':actual==c['expected'],'error':error};results.append(r);(a.output/(c['name']+'.json')).write_text(json.dumps(r,indent=2)+'\n')
s=dict(reader_sha256=hashlib.sha256((a.source/'scripts/analyze_input_consumption.py').read_bytes()).hexdigest(),cases=len(results),matches=sum(r['matched'] for r in results),mismatches=[r for r in results if not r['matched']],scope='Independent bounded source projection prefixes; no native/whole-fixture claim',cpu_affinity=[4],native_executed=False);(a.output/'SUMMARY.json').write_text(json.dumps(s,indent=2)+'\n');print(json.dumps(s,indent=2));raise SystemExit(bool(s['mismatches']))
