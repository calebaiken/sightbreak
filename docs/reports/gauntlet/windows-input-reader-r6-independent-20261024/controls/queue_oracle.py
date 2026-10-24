#!/usr/bin/env python3
"""Independent source queue oracle and isolated UNFROZEN transition assessment."""
import argparse,copy,hashlib,importlib.util,json,os
from pathlib import Path

def cp(value):return copy.deepcopy(value)
def command(sequence,fire=False):return dict(sequence=sequence,fire=fire,reload=False,move=[0.,0.])

class SourceOracle:
 def __init__(self):
  self.states={};self.owners=set();self.counters={};self.latest={};self.rows=[];self.truth=[];self.edges={};self.selected=None;self.skipped=0;self.t=0;self.last_emit=-1000;self.epoch=1
 def state(self,peer):return self.states[peer]
 def note(self,reason,peer,*,lifecycle=False):
  self.t+=1;before=set(self.owners);self.selected=peer;self.counters[reason]=self.counters.get(reason,0)+1
  value=self.latest.get(reason,{});edge=(value.get('fire',0),value.get('reload',0),tuple(value.get('move',[])),value.get('moving',0))
  changed=self.edges.get(reason)!=edge;self.edges[reason]=edge
  control=reason in ('input_received','input_accepted','input_consumed') and changed
  emit=lifecycle or control or reason=='authority_tick' and self.t-self.last_emit>=1000
  if emit:
   s=self.state(peer)
   row=dict(role='authority',reason=reason,peer=peer,generation=s['generation'],bound_actor=s['actor'] if peer in self.owners or reason=='peer_bound' else 0,authority_epoch=self.epoch,stream_ack=s['ack'],queue_count=len(s['queue']),stream_skipped=self.skipped,counters=cp(self.counters),latest=cp(self.latest))
   self.rows.append({'row':row,'owners_before':sorted((p,self.state(p)['generation']) for p in before)})
   self.last_emit=self.t
 def connect(self,peer=9,generation=1,actor=1):
  self.states[peer]={'generation':generation,'actor':actor,'ack':-1,'queue':{}}
  self.note('peer_connected',peer,lifecycle=True);self.note('peer_bound',peer,lifecycle=True);self.owners.add(peer)
 def accept(self,commands,peer=9):
  s=self.state(peer);ack=max(0,s['ack']);assert 1<=len(commands)<=12 and all(1<=c['sequence']<=ack+120 for c in commands)
  packet=dict(epoch=self.epoch,count=len(commands),first=commands[0]['sequence'],last=commands[-1]['sequence'],fire=sum(c['fire'] for c in commands),reload=sum(c['reload'] for c in commands),moving=sum(c['move']!=[0.,0.] for c in commands),wall_msec=self.t+1)
  self.latest['input_received']=cp(packet);self.note('input_received',peer)
  staged={c['sequence']:cp(c) for c in commands if c['sequence']>ack};assert staged
  for key,value in staged.items():s['queue'].setdefault(key,value)
  packet['wall_msec']=self.t+1;self.latest['input_accepted']=cp(packet);self.note('input_accepted',peer)
  self.truth.append({'event':'accept','peer':peer,'commands':cp(commands),'ack':s['ack'],'queue':cp(s['queue'])})
 def pop(self,peer=9):
  # The actual authority hook runs before pop and may be coalesced.
  self.note('authority_tick',peer)
  s=self.state(peer);keys=sorted(s['queue']);assert keys
  if len(keys)>6:
   while len(keys)>2:del s['queue'][keys.pop(0)];self.skipped+=1
  key=keys[0];value=s['queue'].pop(key);s['ack']=key
  self.latest['input_consumed']={**cp(value),'peer':peer,'generation':s['generation'],'actor':s['actor'],'wall_msec':self.t+1};self.note('input_consumed',peer)
  self.truth.append({'event':'pop','peer':peer,'command':cp(value),'ack':key,'queue':cp(s['queue']),'skipped':self.skipped});return value
 def flush(self,peer=None):
  self.t=max(self.t,self.last_emit+1000);self.note('authority_tick',peer or self.selected)
 def noise(self,peer):self.note('input_decode_rejected',peer)


def source_models():
 models=[]
 def add(name,w,expected='VALID',mutation=None,basis=''):
  rows=cp(w.rows)
  if mutation:mutation(rows[-1]['row'])
  models.append(dict(name=name,expected_model=expected,source_basis=basis,ground_truth=cp(w.truth),source_states=cp(w.states),projected_rows=rows,counterfactual=mutation is not None))
 def changed_pop(row,sequence):row['latest']['input_consumed']['sequence']=sequence;row['stream_ack']=sequence
 w=SourceOracle();w.connect();w.accept([command(1),command(2,True),command(1)]);assert w.pop()['sequence']==1
 add('fresh_endpoint_is_mandatory',w,basis='Count3 endpoints1/1 atACK0 andqueue2 necessarily include fresh1.')
 add('opaque_batch_cannot_pop_past_mandatory1',w,'INVALID',lambda r:changed_pop(r,2),'Every possible count3 body includes fresh1; skip0 cannot pop2 first.')
 w=SourceOracle();w.connect();w.accept([command(1,True)]);w.accept([command(1),command(2),command(1)]);assert w.pop()['fire']
 add('known_payload_survives_opaque_duplicate',w,basis='Existingkey1 fireTrue is never replaced by later duplicate payloads.')
 add('opaque_batch_cannot_erase_old_signature',w,'INVALID',lambda r:r['latest']['input_consumed'].update(fire=False),'Old queued1/fireTrue must remain immutable despite count3 uncertainty.')
 w=SourceOracle();w.connect();w.accept([command(1),command(2,True),command(1)]);w.pop();w.pop();assert not w.state(9)['queue'];w.accept([command(3,True)]);w.flush()
 add('observed_empty_then_fresh_accept_adds_one',w,basis='Observedempty is exact, later count1 fresh3 must createqueue1 without pop/skip.')
 add('empty_resynchronization_cannot_be_lost',w,'INVALID',lambda r:r.update(queue_count=0),'Queue was observedempty; newA1/noC/K cannot leavezero.')
 w=SourceOracle();w.connect();w.accept([command(i,True) for i in range(1,8)]);assert w.pop()['sequence']==6 and w.skipped==5
 add('opaque_backlog_seven_valid_rank',w,basis='Sevenunique positivekeys truncate5 andpopsecondlargest6.')
 add('opaque_backlog_cannot_pop_rank2',w,'INVALID',lambda r:changed_pop(r,2),'Secondlargest of7positiveunique keys atinitialACK0 isatleast6.')
 w=SourceOracle();w.connect()
 for i in range(1,8):w.accept([command(i,bool(i%2))])
 assert w.pop()['sequence']==6
 add('exposed_backlog_seven_valid_rank',w,basis='Samebacklog with everykey exposed remainsvalid.')
 add('exposed_backlog_rank2_rejected',w,'INVALID',lambda r:changed_pop(r,2),'Knownkeys1..7 mustpop6, not2.')
 w=SourceOracle();w.connect();w.accept([command(2),command(120,True)]);assert w.pop()['sequence']==2 and w.pop()['sequence']==120
 add('sparse_queued_sequences_need_no_adjacency',w,basis='ACK follows sortedqueue identities, not consecutive integer ticks.')
 w=SourceOracle();w.connect(9,1,1);w.connect(10,2,2);w.accept([command(1)],9);w.pop(9);w.accept([command(1,True),command(2,True)],10);w.pop(10);w.pop(10);w.accept([command(2,True)],9)
 add('explicit_B_pop_can_be_seen_in_A_row',w,basis='Bpop2 coalesces afterBpop1; nextA receivehas explicitB latest and known priorB queue{2}.')
 w=SourceOracle();w.connect(9,1,1);w.connect(10,2,2);w.accept([command(1,True)],9);w.accept([command(1,True)],10);w.accept([command(1,True)],10);w.noise(9);w.flush(9)
 add('genuinely_ambiguous_duplicate_accept_owner',w,'UNKNOWN',basis='Both livequeues containfreshunacked1; hidden duplicate canbelongeither withoutqueuegrowth; selectedA doesnotidentifyitsowner.')
 return models


def main():
 p=argparse.ArgumentParser();p.add_argument('--prototype',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert sorted(os.sched_getaffinity(0))==[4];a.output.mkdir(parents=True,exist_ok=False)
 spec=importlib.util.spec_from_file_location('unapproved_r6_prototype',a.prototype);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 results=[]
 for case in source_models():
  model=m.InputTransitions();actual='VALID';error=None
  try:
   for record in case['projected_rows']:model.observe(record['row'],set(map(tuple,record['owners_before'])))
  except m.UnknownTransition as e:actual='UNKNOWN';error=str(e)
  except (ValueError,KeyError,TypeError) as e:actual='INVALID';error=type(e).__name__+': '+str(e)
  result={**case,'actual_model':actual,'matches_expectation':actual==case['expected_model'],'error':error};results.append(result)
  (a.output/(case['name']+'.json')).write_text(json.dumps(result,indent=2)+'\n')
 summary={'scope':'Isolated UNAPPROVED UNFROZEN InputTransitions model assessment; not whole-reader or final candidate qualification','prototype_sha256':hashlib.sha256(a.prototype.read_bytes()).hexdigest(),'cases':len(results),'matches':sum(r['matches_expectation'] for r in results),'invalid_accepted':[r['name'] for r in results if r['expected_model']=='INVALID' and r['actual_model']=='VALID'],'coverage_unknown':[r['name'] for r in results if r['expected_model']=='VALID' and r['actual_model']=='UNKNOWN'],'valid_rejected':[r['name'] for r in results if r['expected_model']=='VALID' and r['actual_model']=='INVALID'],'cpu_affinity':[4],'native_executed':False}
 (a.output/'SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2));raise SystemExit(any(not r['matches_expectation'] for r in results))
if __name__=='__main__':main()
