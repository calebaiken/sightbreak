#!/usr/bin/env python3
"""Independent source emitter/queue witnesses, then complete-reader adjudication."""
import argparse,copy,hashlib,importlib.util,json,os,sys
from pathlib import Path
cp=copy.deepcopy

def cmd(sequence,fire=True,reload=False):return dict(sequence=sequence,fire=fire,reload=reload,move=[0.,0.])

class Emitter:
 def __init__(self,template):
  self.template=cp(template);self.t=12000;self.index=0;self.last_emit=-1000;self.epoch=1;self.simulation=0;self.counter={};self.latest={};self.edges={};self.states={};self.actors={};self.selected=0;self.last_actor=0;self.generation=0;self.rejected=0;self.skipped=0;self.rows=[];self.events=[];self.emit('ready')
 def emit(self,reason,peer=0,value=None,step=1):
  self.t+=step;self.counter[reason]=self.counter.get(reason,0)+1
  if peer:
   self.selected=peer
   if self.states[peer]['bound']:self.last_actor=self.states[peer]['actor']
  if value is not None:self.latest[reason]={**cp(value),'wall_msec':self.t}
  v=self.latest.get(reason,{})
  edge=(v.get('fire',0),v.get('reload',0),tuple(v.get('move',[])),v.get('moving',0))
  changed=self.edges.get(reason)!=edge;self.edges[reason]=edge
  lifecycle=reason in {'ready','peer_connected','peer_bound','peer_expired','peer_disconnected'}
  control=reason in {'input_received','input_accepted','input_consumed'} and changed
  if not lifecycle and not control and (reason!='authority_tick' or self.t-self.last_emit<1000):return
  s=self.states.get(self.selected);bound=bool(s and s['bound']);actor=self.actors.get(self.last_actor)
  r=cp(self.template);self.index+=1
  r.update(reason=reason,index=self.index,wall_msec=self.t,wall_unix_msec=100000+self.t,process_frames=self.index,physics_frames=self.index*2,drawn_frames=self.index,peer=self.selected,bound_actor=s['actor'] if bound else 0,last_bound_actor=self.last_actor,peer_bound=bound,generation=s['generation'] if s else -1,joined=bound,input_age_msec=0 if bound else -1,deadline_remaining_msec=20000 if bound else -1,simulation_tick=self.simulation,authority_epoch=self.epoch,stream_ack=s['ack'] if s else -1,queue_count=len(s['queue']) if s else 0,stream_rejected=self.rejected,stream_skipped=self.skipped,counters=cp(self.counter),latest=cp(self.latest),actor=cp(actor) if actor else {})
  self.rows.append(r);self.last_emit=self.t
 def connect(self,peer,actor):
  self.generation+=1;self.states[peer]=dict(generation=self.generation,actor=actor,bound=False,ack=-1,queue={});self.events.append(dict(event='connect',peer=peer,generation=self.generation));self.emit('peer_connected',peer)
  self.states[peer]['bound']=True;self.actors.setdefault(actor,dict(id=actor,alive=True,ammo=30,reserve=90,reload=0.,input=cmd(-1,False)));self.emit('peer_bound',peer)
 def packet(self,commands):return dict(epoch=self.epoch,count=len(commands),first=commands[0]['sequence'],last=commands[-1]['sequence'],fire=sum(c['fire'] for c in commands),reload=sum(c['reload'] for c in commands),moving=sum(c['move']!=[0.,0.] for c in commands))
 def accept(self,commands,peer=9):
  s=self.states[peer];ack=max(0,s['ack']);assert s['bound'] and 1<=len(commands)<=12 and all(1<=c['sequence']<=ack+120 for c in commands)
  h=self.packet(commands);self.emit('input_received',peer,h)
  staged={c['sequence']:cp(c) for c in commands if c['sequence']>ack};assert staged
  for k,v in staged.items():s['queue'].setdefault(k,v)
  self.emit('input_accepted',peer,h);self.events.append(dict(event='accept',peer=peer,epoch=self.epoch,commands=cp(commands),queue=cp(s['queue'])))
 def pop(self,peer=9):
  self.tick();s=self.states[peer];keys=sorted(s['queue']);assert keys and s['bound']
  if len(keys)>6:
   while len(keys)>2:del s['queue'][keys.pop(0)];self.skipped+=1
  key=keys[0];c=s['queue'].pop(key);s['ack']=key;self.actors[s['actor']]['input']=cp(c)
  self.emit('input_consumed',peer,{**c,'peer':peer,'actor':s['actor'],'generation':s['generation']});self.events.append(dict(event='pop',peer=peer,command=cp(c),queue=cp(s['queue'])));return c
 def tick(self,flush=False):
  if flush:self.t=max(self.t,self.last_emit+1000)
  self.simulation+=1;self.emit('authority_tick')
 def select(self,peer):self.emit('input_decode_rejected',peer)
 def reset(self,epoch=None):
  self.epoch=epoch or self.epoch+1
  for s in self.states.values():s.update(ack=-1,queue={})
  for a in self.actors.values():a['input']=cmd(-1,False)
  self.events.append(dict(event='reset_epoch',epoch=self.epoch))
 def disconnect(self,peer):
  self.emit('peer_disconnected',peer);self.states.pop(peer);self.events.append(dict(event='disconnect',peer=peer))
 def expire(self,peer):self.emit('peer_expired',peer);self.events.append(dict(event='expiry_hook_before_disconnect',peer=peer))

def corpus(template):
 cases=[]
 def base():
  w=Emitter(template);w.connect(9,1);w.accept([cmd(1)]);w.pop();w.tick(True);return w
 def add(name,w,expected='CONSISTENT',mutate=None,basis=''):
  rows=cp(w.rows)
  if mutate:mutate(rows)
  cases.append(dict(name=name,authority=rows,expected=expected,source_events=cp(w.events),source_basis=basis,counterfactual=mutate is not None))
 def queue(n):return lambda rows:rows[-1].update(queue_count=n)
 w=base();w.accept([cmd(2)]);w.connect(10,2);w.accept([cmd(1,False)],10);w.select(9);w.tick(True)
 add('owned_A_header_survives_global_B',w,basis='B connection proves hidden A acceptance; B latest cannot replace A queue1.')
 add('cached_A_cannot_disappear',w,'INVALID',queue(0));add('cached_A_cannot_duplicate',w,'INVALID',queue(2))
 w.tick(True);add('cached_call_not_replayed_on_zero_local_delta',w);add('zero_local_delta_cannot_erase_queue',w,'INVALID',queue(0))
 w=base();w.accept([cmd(2,False),cmd(3),cmd(2,False)]);w.connect(10,2);w.accept([cmd(1,False)],10);w.select(9);w.tick(True)
 add('opaque_cached_A_retains_two_unique_keys',w);add('opaque_duplicate_endpoints_cannot_make_three_keys',w,'INVALID',queue(3))
 w.pop(9);w.tick(True);add('opaque_cached_A_pops_mandatory_endpoint2',w)
 def pop3(rows):
  for r in rows:
   if r['latest'].get('input_consumed',{}).get('sequence')==2:
    r['latest']['input_consumed']['sequence']=3;r['actor']['input']['sequence']=3;r['stream_ack']=3
 add('opaque_cached_A_cannot_pop_past2',w,'INVALID',pop3)
 for before in (False,True):
  w=base()
  if before:w.reset()
  w.accept([cmd(1 if before else 2)]);w.connect(10,2)
  if not before:w.reset()
  w.accept([cmd(1,False)],10);w.select(9);w.tick(True)
  name='new_receipt_after_reset' if before else 'old_receipt_cleared_by_later_reset'
  add(name,w);add(name+'_wrong_queue',w,'INVALID',queue(0 if before else 1))
 w=base();w.accept([cmd(2)]);w.connect(10,2);w.accept([cmd(1,False)],10);w.disconnect(9);w.connect(9,1);w.tick(True)
 add('same_peer_new_generation_has_fresh_queue',w);add('old_generation_cache_cannot_seed_new_queue',w,'INVALID',queue(1))
 w=base();w.accept([cmd(2)]);w.expire(9);w.disconnect(9);w.connect(9,1);w.tick(True);add('expiry_then_disconnect_rebind_preserves_old_history_only',w)
 w=base();w.connect(10,2);w.accept([cmd(1,False)],10);w.select(9);w.tick(True);w.accept([cmd(2)]);w.tick(True);w.pop(9);w.connect(11,3);w.pop(10);w.select(9);w.tick(True)
 add('foreign_lifecycle_exposes_A_pop_before_global_B_pop',w)
 add('cached_A_ACK_cannot_regress_to_old_pop',w,'INVALID',lambda rows:rows[-1].update(stream_ack=1))
 for jump in (2,3):
  w=base();w.reset(jump);w.accept([cmd(1)]);w.tick(True);add('fresh_epoch_'+str(jump)+'_acceptance_uses_zero_ACK',w)
  add('fresh_epoch_'+str(jump)+'_acceptance_cannot_be_erased',w,'INVALID',queue(0))
 w=base();w.accept([cmd(2)]);w.reset(3);w.tick(True);add('old_epoch_call_cleared_across_larger_jump',w)
 add('old_epoch_call_cannot_survive_larger_jump',w,'INVALID',queue(1))
 w=base();w.connect(10,2);w.accept([cmd(1)],10);w.tick(True);w.accept([cmd(1)],10);w.select(9);w.tick(True)
 add('genuine_duplicate_owner_ambiguity',w,'UNKNOWN')
 w=base();w.accept([cmd(2)]);w.accept([cmd(3)]);w.tick(True);add('multiple_hidden_local_calls_declared_incomplete',w,'UNKNOWN')
 return cases

def main():
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert sorted(os.sched_getaffinity(0))==[4];a.output.mkdir(parents=True,exist_ok=False)
 sys.path.insert(0,str(a.source/'scripts'));from test_input_consumption_observation import declared_rows,text
 # Complete source witnesses and expectations are fixed before candidate import.
 cases=corpus(declared_rows('authority')[0]);client=declared_rows('client')
 spec=importlib.util.spec_from_file_location('final_reader',a.source/'scripts/analyze_input_consumption.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 results=[]
 for case in cases:
  folder=a.output/case['name'];folder.mkdir();ct=text(client);at=text(case.pop('authority'));(folder/'client.txt').write_text(ct);(folder/'authority.txt').write_text(at);r=m.analyze(ct,at)
  actual=r['transition_status'];item={**case,'actual':actual,'matched':actual==case['expected'],'result':r};(folder/'RESULT.json').write_text(json.dumps(item,indent=2)+'\n');results.append(item)
 summary=dict(scope='Independent complete-reader causal source witnesses; no native approval',source=str(a.source),analyzer_sha256=hashlib.sha256((a.source/'scripts/analyze_input_consumption.py').read_bytes()).hexdigest(),cases=len(results),matches=sum(r['matched'] for r in results),unexpected=[{k:r[k] for k in ('name','expected','actual','result')} for r in results if not r['matched']],cpu_affinity=[4],native_executed=False)
 (a.output/'SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2));return int(bool(summary['unexpected']))
if __name__=='__main__':raise SystemExit(main())
