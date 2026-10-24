#!/usr/bin/env python3
"""Registered source-order/epoch/tie matrix with complete-reader outputs."""
import argparse,copy,hashlib,importlib.util,json,os,sys
from pathlib import Path
cp=copy.deepcopy

def main():
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert sorted(os.sched_getaffinity(0))==[4];a.output.mkdir(parents=True,exist_ok=False);home=Path(__file__).resolve().parent
 raw=(home/'causal_cases-v3.py').read_text();namespace={'__name__':'source_oracle_only','__file__':str(home/'causal_cases-v3.py')};exec(compile(raw,str(home/'causal_cases-v3.py'),'exec'),namespace);Emitter=namespace['Emitter'];cmd=namespace['cmd']
 # Equal-millisecond reads are legal: collapse per-hook clock increments and
 # the corresponding source last_input/deadline creation timestamps together.
 tie=raw.replace('step=1):','step=0):').replace('self.t+1','self.t').replace('self.t+20001','self.t+20000');tied={'__name__':'equal_clock_source_oracle','__file__':str(home/'causal_cases-v3.py')};exec(compile(tie,'equal_clock_source_oracle','exec'),tied);Tie=tied['Emitter']
 sys.path.insert(0,str(a.source/'scripts'));from test_input_consumption_observation import declared_rows,text
 template=declared_rows('authority')[0];client=declared_rows('client')
 for row in client:row['wall_unix_msec']+=9000
 cases=[]
 def base(cls=Emitter):
  w=cls(template);w.connect(9,1);w.accept([cmd(1)]);w.pop();w.tick(True);return w
 def add(name,w,expected='CONSISTENT',mutation=None,invalid_client=False):
  rows=cp(w.rows)
  if mutation:mutation(rows)
  cases.append(dict(name=name,expected=expected,rows=rows,source_events=cp(w.events),invalid_client=invalid_client,counterfactual=mutation is not None or invalid_client))
 for cls,label in [(Emitter,'ordered'),(Tie,'equal_millisecond')]:
  for before in (None,False,True):
   w=base(cls)
   if before is True:w.reset()
   w.accept([cmd(1 if before else 2)]);w.connect(10,2)
   if before is False:w.reset()
   w.accept([cmd(1,False)],10);w.select(9);w.tick(True)
   name=label+'_cached_A_'+('same_epoch' if before is None else 'after_reset' if before else 'before_reset')
   add(name,w);add(name+'_wrong_cardinality',w,'INVALID',lambda rows:rows[-1].update(queue_count=2 if rows[-1]['queue_count']==1 else 1))
 w=base();w.reset();w.tick(True);w.reset();w.tick(True);add('unchanged_old_latest_survives_two_resets',w)
 add('unchanged_count_cannot_restamp_old_latest_epoch',w,'INVALID',lambda rows:rows[-1]['latest']['input_accepted'].update(epoch=3))
 w=base();w.reset(2);w.accept([cmd(1)]);w.reset(3);w.tick(True);add('intermediate_epoch_accept_cleared_before_observed_epoch3',w)
 def epoch(e):
  def mutate(rows):
   for stage in ('input_received','input_accepted'):rows[-1]['latest'][stage]['epoch']=e
  return mutate
 add('accepted_epoch_below_observed_range',w,'INVALID',epoch(0));add('accepted_epoch_above_observed_range',w,'INVALID',epoch(4))
 w=base();w.reset(2);w.accept([cmd(1)]);w.tick(True);add('new_epoch_reset_cannot_borrow_old_ACK',w)
 def beyond(rows):
  for stage in ('input_received','input_accepted'):rows[-1]['latest'][stage].update(first=122,last=122)
 add('new_epoch_sequence122_exceeds_zero_ACK_window',w,'INVALID',beyond)
 for after in (False,True):
  w=base()
  if after:w.reset(2)
  w.accept([cmd(1 if after else 2)]);w.pop()
  if not after:w.reset(2)
  w.tick(True);name='unexposed_accept_pop_'+('after_reset' if after else 'before_reset')
  add(name,w,'UNKNOWN');add(name+'_plus_invalid_client_cache',w,'INVALID',invalid_client=True)
 # All source histories/expectations fixed before importing the candidate.
 spec=importlib.util.spec_from_file_location('final_epoch_reader',a.source/'scripts/analyze_input_consumption.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);results=[]
 for case in cases:
  folder=a.output/case['name'];folder.mkdir();c=cp(client)
  if case['invalid_client']:c[-1]['snapshot']={};c[-1]['snapshot_age_msec']=-1
  ct=text(c);at=text(case.pop('rows'));(folder/'client.txt').write_text(ct);(folder/'authority.txt').write_text(at);result=m.analyze(ct,at);actual=result['transition_status'];r={**case,'actual':actual,'matched':actual==case['expected'],'result':result};(folder/'RESULT.json').write_text(json.dumps(r,indent=2)+'\n');results.append(r)
 summary=dict(source=str(a.source),analyzer_sha256=hashlib.sha256((a.source/'scripts/analyze_input_consumption.py').read_bytes()).hexdigest(),cases=len(results),matches=sum(r['matched'] for r in results),unexpected=[{k:r[k] for k in ('name','expected','actual','result')} for r in results if not r['matched']],cpu_affinity=[4],native_executed=False)
 (a.output/'SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2));return int(bool(summary['unexpected']))
if __name__=='__main__':raise SystemExit(main())
