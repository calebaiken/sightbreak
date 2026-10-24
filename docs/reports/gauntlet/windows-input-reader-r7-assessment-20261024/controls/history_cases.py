#!/usr/bin/env python3
"""Independent expiry caller/history tests against a captured UNFROZEN reader."""
import argparse,copy,hashlib,importlib.util,json,os,sys
from pathlib import Path
cp=copy.deepcopy

def corpus(Emitter,command,template):
 cases=[]
 def base():
  w=Emitter(template);w.connect(9,1);w.accept([command(1)]);w.pop();w.tick(True);return w
 def add(name,w,expected='CONSISTENT',mutation=None,invalid_client=False,basis=''):
  rows=cp(w.rows)
  if mutation:mutation(rows)
  cases.append(dict(name=name,rows=rows,expected=expected,source_events=cp(w.events),invalid_client=invalid_client,counterfactual=mutation is not None or invalid_client,source_basis=basis))
 def expiry(rows):return next(r for r in rows if r['reason']=='peer_expired')
 w=base();w.expire(9);w.disconnect(9);w.connect(9,1);w.tick(True)
 add('joined_idle_positive',w,basis='Actual joined idle source branch, before disconnect and a new generation.')
 add('original_R6_impossible_expiry',w,'INVALID',lambda rows:expiry(rows).update(input_age_msec=0,deadline_remaining_msec=20000))
 add('expiry_last_input_before_proved_connect',w,'INVALID',lambda rows:expiry(rows).update(input_age_msec=expiry(rows)['wall_msec']),basis='last_input cannot precede the known connection or regress from earlier accepted activity; only a new invented connection makes the local state feasible.')
 add('expiry_cannot_unjoin_live_bound_generation',w,'INVALID',lambda rows:expiry(rows).update(joined=False),basis='admitted joinedtrue persists until forget; expiry still precedes disconnect and generation is unchanged.')
 add('expiry_cannot_drop_live_actor_binding_before_disconnect',w,'INVALID',lambda rows:expiry(rows).update(bound_actor=0,peer_bound=False),basis='Match peer actor binding is erased after the disconnect hook, later than expiry.')
 add('expiry_wrong_current_generation',w,'INVALID',lambda rows:expiry(rows).update(generation=999))
 add('expiry_nonexistent_peer',w,'INVALID',lambda rows:expiry(rows).update(peer=99))
 add('expiry_negative_age',w,'INVALID',lambda rows:expiry(rows).update(input_age_msec=-1))
 add('expiry_last_input_in_future',w,'INVALID',lambda rows:expiry(rows).update(input_age_msec=-2))
 w=base();w.t=100000;w.tick();w.emit('peer_expired',9);w.events.append(dict(event='idle_expired',at=w.t));w.disconnect(9);w.tick(True)
 add('long_idle_source_positive',w)
 add('expiry_last_input_advances_without_activity',w,'INVALID',lambda rows:expiry(rows).update(input_age_msec=expiry(rows)['wall_msec']-20000),basis='Since binding only the initial accepted call updated last_input, no counted accepted/admitted operation moves it from12006 to20000.')
 # A fresh unbound peer has its initialized clock even without a bound actor.
 for rejected in (False,True):
  w=base();peer=10;w.generation+=1;at=w.t+1;w.states[peer]=dict(generation=w.generation,actor=0,bound=False,ack=-1,queue={},last_input=at,deadline=at+20000);w.emit('peer_connected',peer)
  if rejected:
   w.t+=100;w.states[peer]['deadline']=w.t+500;w.events.append(dict(event='reject_unbound',at=w.t,peer=peer))
  w.t=w.states[peer]['deadline'];w.tick();w.emit('peer_expired',peer);w.events.append(dict(event='unbound_expiry',at=w.t,rejected=rejected));w.disconnect(peer);w.tick(True)
  add('unbound_'+('rejected500' if rejected else 'join20000')+'_positive',w)
 # An early rejected joined expiry may be uniquely explained or ambiguous when
 # only its local projected state is considered. Both actual source witnesses
 # are valid; UNKNOWN is the declared projected-policy result for mixed states.
 for reject_at,label,status in [(13200,'unique_early_rejected','CONSISTENT'),(23000,'mixed_rejection_projection','UNKNOWN')]:
  w=base();assert reject_at>=w.t;w.t=reject_at;w.states[9]['deadline']=reject_at+500;w.events.append(dict(event='reject_joined',at=reject_at,peer=9));w.t+=500;w.tick();w.emit('peer_expired',9);w.events.append(dict(event='rejected_expiry',at=w.t));w.disconnect(9);w.tick(True)
  add(label,w,status)
  if status=='UNKNOWN':
   add('deferred_UNKNOWN_then_later_authority_ACK_INVALID',w,'INVALID',lambda rows:rows[-1].update(stream_ack=0))
   add('authority_UNKNOWN_plus_client_cache_INVALID',w,'INVALID',invalid_client=True)
 # Source permits no repeated expiry of a still connected generation: service
 # immediately calls disconnect and forget after the first hook.
 w=base();w.expire(9);w.disconnect(9);w.connect(9,1);w.tick(True)
 def retired(rows):
  r=cp(rows[-1]);r.update(index=len(rows)+1,reason='peer_expired',generation=1,input_age_msec=30000,deadline_remaining_msec=-1);r['counters']['peer_expired']+=1;rows.append(r)
 add('retired_generation_cannot_expire_again',w,'INVALID',retired)
 return cases

def main():
 p=argparse.ArgumentParser();p.add_argument('--prototype',type=Path,required=True);p.add_argument('--schema-source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert sorted(os.sched_getaffinity(0))==[4];a.output.mkdir(parents=True,exist_ok=False);home=Path(__file__).resolve().parent
 namespace={'__name__':'independent_source_oracle','__file__':str(home/'r6-causal-v3-oracle.py')};exec(compile((home/'r6-causal-v3-oracle.py').read_text(),str(home/'r6-causal-v3-oracle.py'),'exec'),namespace)
 sys.path.insert(0,str(a.schema_source/'scripts'));from test_input_consumption_observation import declared_rows,text
 client=declared_rows('client')
 for row in client:row['wall_unix_msec']+=9000
 cases=corpus(namespace['Emitter'],namespace['cmd'],declared_rows('authority')[0])
 spec=importlib.util.spec_from_file_location('unfrozen_expiry_history_reader',a.prototype);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);results=[]
 for c in cases:
  folder=a.output/c['name'];folder.mkdir();ct=cp(client)
  if c['invalid_client']:ct[-1].update(snapshot={},snapshot_age_msec=-1)
  cs=text(ct);ss=text(c.pop('rows'));(folder/'client.txt').write_text(cs);(folder/'authority.txt').write_text(ss);result=m.analyze(cs,ss);r={**c,**dict(actual=result['transition_status'],matched=result['transition_status']==c['expected'],result=result)};results.append(r);(folder/'RESULT.json').write_text(json.dumps(r,indent=2)+'\n')
 summary=dict(scope='UNFROZEN whole-reader caller/history model assessment only',prototype_sha256=hashlib.sha256(a.prototype.read_bytes()).hexdigest(),cases=len(results),matches=sum(r['matched'] for r in results),mismatches=[{k:r[k] for k in ('name','expected','actual','source_basis','result')} for r in results if not r['matched']],cpu_affinity=[4],native_executed=False,source_approved=False)
 (a.output/'SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2));return int(bool(summary['mismatches']))
if __name__=='__main__':raise SystemExit(main())
