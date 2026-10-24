#!/usr/bin/env python3
"""Persistent aggregate relation; isolated unfrozen model, not final analyzer."""
import argparse,copy,hashlib,importlib.util,json,os
from pathlib import Path
import queue_oracle as q
p=argparse.ArgumentParser();p.add_argument('--prototype',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert sorted(os.sched_getaffinity(0))==[4];a.output.mkdir(parents=True,exist_ok=False)
spec=importlib.util.spec_from_file_location('unfrozen_aggregate_prototype',a.prototype);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
w=q.SourceOracle();w.connect();w.accept([q.command(1),q.command(2,True)]);assert not w.pop()['fire'] and w.pop()['fire'];assert len(w.truth)==3
cases=[('one_true_across_two_immutable_pops',copy.deepcopy(w.rows),'VALID')]
pop_indices=[i for i,r in enumerate(w.rows) if r['row']['reason']=='input_consumed'];assert len(pop_indices)==2
for truth in (False,True):
 for coalesced in (False,True):
  rows=copy.deepcopy(w.rows)
  for i in pop_indices:rows[i]['row']['latest']['input_consumed']['fire']=truth
  if coalesced:
   last=rows[-1]['row'];last['reason']='authority_tick';last['counters']['authority_tick']+=1
  cases.append(('both_'+str(truth).lower()+'_pops_'+('coalesced' if coalesced else 'direct'),rows,'INVALID'))
results=[]
for name,rows,expected in cases:
 model=m.InputTransitions();actual='VALID';error=None
 try:
  for record in rows:model.observe(record['row'],set(map(tuple,record['owners_before'])))
 except m.UnknownTransition as e:actual='UNKNOWN';error=str(e)
 except (ValueError,KeyError,TypeError) as e:actual='INVALID';error=type(e).__name__+': '+str(e)
 r={'name':name,'scope':'UNFROZEN isolated transition model only','expected':expected,'actual':actual,'matches':actual==expected,'source_basis':'One sole accepted count2 distinctfreshkeys1/2/fireaggregate1 and no otheraccepts cannot yield bothfalse orbothtrue immutable pops.','ground_truth':w.truth,'projected_rows':rows,'error':error}
 (a.output/(name+'.json')).write_text(json.dumps(r,indent=2)+'\n');results.append(r)
summary={'prototype_sha256':hashlib.sha256(a.prototype.read_bytes()).hexdigest(),'scope':'Independent aggregate feasibility assessment of UNAPPROVED UNFROZEN InputTransitions; not final source review','cases':len(results),'matches':sum(r['matches'] for r in results),'invalid_accepted':[r['name'] for r in results if r['expected']=='INVALID' and r['actual']=='VALID'],'native_executed':False,'cpu_affinity':[4]}
(a.output/'SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2));raise SystemExit(any(not r['matches'] for r in results))
