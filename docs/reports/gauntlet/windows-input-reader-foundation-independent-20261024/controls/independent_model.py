#!/usr/bin/env python3
import argparse,copy,hashlib,importlib.util,json,os,sys
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert sorted(os.sched_getaffinity(0))==[4];a.output.mkdir(parents=True,exist_ok=False)
path=a.source/'scripts/input_consumption_foundation_model.py';assert hashlib.sha256(path.read_bytes()).hexdigest()=='19b869626fc9b2488a4a220aeddf68e7d3590a63ce4392e56cc3be62c4ceb53e';spec=importlib.util.spec_from_file_location('frozen_foundation_source_model',path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);records=[]
def check(name,actual,expected,source_basis):
 r=dict(name=name,actual=actual,expected=expected,matched=actual==expected,source_basis=source_basis);records.append(r)
def projection(peer,generation,joined,age,remaining,actor,last):return dict(peer=peer,generation=generation,joined=joined,input_age_msec=age,deadline_remaining_msec=remaining,bound_actor=actor,last_bound_actor=last,peer_bound=actor>0)
def selected(row):return {k:row[k] for k in projection(0,0,False,0,0,0,0)}
for C in [0,1,2000]:
 for delay in [0,1,19999,20000,20001,100000]:
  w=m.AuthorityProjectionEmitter();accepted,r=w.connect(9,C,C+delay);check('connect-'+str(C)+'-delay'+str(delay),dict(accepted=accepted,projection=selected(r)),dict(accepted=True,projection=projection(9,1,False,delay,20000-delay,0,0)),'successful connected fixes L=C,D=C+20000; observer samples later')
for C in [0,2000]:
 for off in [0,1,19999]:
  for delay in [0,1,20000,30000]:
   w=m.AuthorityProjectionEmitter();w.connect(9,C);r=w.bind(9,1,C+off,C+off+delay);check('admit-'+str(C)+'-'+str(off)+'-delay'+str(delay),selected(r),projection(9,1,True,delay,20000-off-delay,1,1),'A<C+20000; L=A and fixed original deadline')
 for off in [20000,20001]:
  w=m.AuthorityProjectionEmitter();w.connect(9,C);blocked=False
  try:w.bind(9,1,C+off)
  except ValueError:blocked=True
  check('admit-denied-'+str(C)+'-'+str(off),dict(blocked=blocked,joined=w.lifecycle.peers[9]['joined']),dict(blocked=True,joined=False),'begin_join/current use strict now<deadline')
for active in [29999,30000,30001]:
 for delay in [0,1,30000]:
  w=m.AuthorityProjectionEmitter();w.connect(9,0);w.bind(9,1,0);gate=w.lifecycle.allow_input(9,29999);w.lifecycle.active(9,active);r=w.capture('input_accepted',active+delay,9);L=active if active<30000 else 0;check('active-'+str(active)+'-delay'+str(delay),dict(gate=gate,projection=selected(r)),dict(gate=True,projection=projection(9,1,True,active+delay-L,20000-active-delay,1,1)),'gate can pass before idle, active may fail later, observer later still')
for joined in [False,True]:
 for R in [0,1,29999]:
  for delay in [499,500,501]:
   w=m.AuthorityProjectionEmitter();w.connect(9,0)
   if joined:w.bind(9,1,0)
   w.lifecycle.reject(9,R);w.lifecycle.reject(9,R+1);w.lifecycle.active(9,R+2);r=w.capture('authority_tick',R+delay);expired=w.lifecycle.expired(R+delay);eligible=delay>=500 or joined and R+delay>=30000;check('reject-'+str(joined)+'-'+str(R)+'-observe'+str(delay),dict(projection=selected(r),expired=expired),dict(projection=projection(9,1,joined,R+delay,500-delay,int(joined),int(joined)),expired=[9] if eligible else []),'reject once fixes D=R+500/L0; joined idle may win independently')
w=m.AuthorityProjectionEmitter();actual=[];actual.append(w.connect(9,0)[1]);actual.append(w.bind(9,1,1,2));actual.append(w.connect(10,3,5)[1]);actual.append(w.bind(10,2,6,8));assert w.lifecycle.allow_input(9,9);actual.append(w.capture('input_received',10,9));actual.append(w.disconnect(9,11));actual.append(w.capture('authority_tick',12));actual.append(w.connect(9,13,15)[1]);actual.append(w.bind(9,3,16,17));assert w.lifecycle.allow_input(10,18);actual.append(w.capture('input_received',19,10))
expected=[projection(9,1,False,0,20000,0,0),projection(9,1,True,1,19998,1,1),projection(10,2,False,2,19998,0,1),projection(10,2,True,2,19995,2,2),projection(9,1,True,9,19990,1,1),projection(9,1,True,10,19989,1,1),projection(9,-1,False,-1,-1,0,1),projection(9,3,False,2,19998,0,1),projection(9,3,True,1,19996,3,3),projection(10,2,True,13,19984,2,2)]
for i,(r,e) in enumerate(zip(actual,expected),1):check('sticky-pre-forget-interleave-'+str(i),selected(r),e,'selected peer, globally incremented generation, sticky last actor and pre-forget ordering')
sys.path.insert(0,str(a.source/'scripts'));from test_input_consumption_observation import declared_rows,text
old=declared_rows('authority');saved=copy.deepcopy(old);expected=copy.deepcopy(old);values=[(-1,-1),(0,20000),(0,19000),(5000,14000),(0,13000),(1000,12000),(2000,11000)]
for row,(age,remaining) in zip(expected,values):row.update(input_age_msec=age,deadline_remaining_msec=remaining)
new,w=m.reproject_authority_rows(old);check('constructor-whole-object-exact',new,expected,'C2000,A3000,L9000,D22000; all other fields exact and synthetic/unadjudicated');check('constructor-no-original-mutation',old,saved,'proposed reprojection must copy rather than rewrite original fixture')
# Preserve all original/expected/actual arrays for the pre-edit record.
(a.output/'original-authority.json').write_text(json.dumps(saved,indent=2)+'\n');(a.output/'independent-expected-authority.json').write_text(json.dumps(expected,indent=2)+'\n');(a.output/'actual-versioned-authority.json').write_text(json.dumps(new,indent=2)+'\n')
for i,r in enumerate(records,1):(a.output/('case-'+str(i)+'.json')).write_text(json.dumps(r,indent=2)+'\n')
s=dict(scope='Independent bounded lifecycle/identity projection controls; no full fixture/native acceptance',model_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),cases=len(records),matches=sum(r['matched'] for r in records),mismatches=[{k:r[k] for k in ['name','actual','expected']} for r in records if not r['matched']],cpu_affinity=[4],native_executed=False);(a.output/'SUMMARY.json').write_text(json.dumps(s,indent=2)+'\n');print(json.dumps(s,indent=2));raise SystemExit(bool(s['mismatches']))
