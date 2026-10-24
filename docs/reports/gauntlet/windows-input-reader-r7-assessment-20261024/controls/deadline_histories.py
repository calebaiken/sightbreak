#!/usr/bin/env python3
"""Independent grouped visible-prefix oracle for one absorbing rejection."""
import argparse,copy,hashlib,importlib.util,json,os,sys
from pathlib import Path
cp=copy.deepcopy

def histories(Emitter,command,template):
 result=[];C_expected=None
 for offset in [None,100,500,600,750,1000,1001,1010,1500,5000,19500]:
  w=Emitter(template);w.connect(9,1);w.accept([command(1)]);w.pop();w.tick(True);peer=10;w.generation+=1;C=w.t+1
  if C_expected is None:C_expected=C
  assert C==C_expected
  w.states[peer]=dict(generation=w.generation,actor=0,bound=False,ack=-1,queue={},last_input=C,deadline=C+20000);w.emit('peer_connected',peer);w.events.append(dict(event='unbound_connected',peer=peer,at=C))
  sample=C+1001
  def reject():
   assert offset is not None and C+offset>=w.t and offset<20000;w.t=C+offset;w.states[peer]['deadline']=w.t+500;w.events.append(dict(event='reject_once',peer=peer,at=w.t))
  if offset is not None and offset<1001:reject()
  if w.states[peer]['deadline']<=sample:continue # prefix service would retire it
  w.t=C+1000;w.tick();assert w.t==sample
  if offset is not None and offset>=1001:reject()
  T=C+21000;w.t=T-10;w.connect(11,3);w.t=T;w.tick();assert w.rows[-1]['peer']==11 and w.rows[-1]['reason']=='peer_bound'
  # The global pre-service tick coalesced after foreign lifecycle output.
  prefix=cp(w.rows);w.emit('peer_expired',peer);expiry_index=len(w.rows)-1;w.events.append(dict(event='expired',peer=peer,at=w.t));w.disconnect(peer)
  result.append(dict(C=C,prefix=prefix,rows=cp(w.rows),expiry_index=expiry_index,final_deadline=w.states.get(peer,{}).get('deadline',C+20000 if offset is None else C+offset+500),events=cp(w.events),reject_offset=offset))
 return result,C_expected

def main():
 p=argparse.ArgumentParser();p.add_argument('--prototype',type=Path,required=True);p.add_argument('--schema-source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert sorted(os.sched_getaffinity(0))==[4];a.output.mkdir(parents=True,exist_ok=False);home=Path(__file__).resolve().parent
 ns={'__name__':'source_oracle_only','__file__':str(home/'r6-causal-v3-oracle.py')};exec(compile((home/'r6-causal-v3-oracle.py').read_text(),str(home/'r6-causal-v3-oracle.py'),'exec'),ns);sys.path.insert(0,str(a.schema_source/'scripts'));from test_input_consumption_observation import declared_rows,text
 concrete,C=histories(ns['Emitter'],ns['cmd'],declared_rows('authority')[0]);groups={}
 for h in concrete:
  key=json.dumps(h['prefix'],separators=(',',':'),sort_keys=True);group=groups.setdefault(key,dict(prefix_sha256=hashlib.sha256(key.encode()).hexdigest(),witnesses={},canonical=h));group['witnesses'].setdefault(h['final_deadline'],h)
 deadlines=sorted({C+20000}|{C+r+500 for r in [100,500,600,750,1000,1001,1010,1500,5000,19500]})
 # Complete expected sets fixed independently before candidate import. A changed
 # deadline has a unique reject time; initial deadline also permits no reject.
 spec=importlib.util.spec_from_file_location('held_db912_deadline_history',a.prototype);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 client=declared_rows('client')
 for row in client:row['wall_unix_msec']+=9000
 ct=text(client);results=[]
 for number,(_,g) in enumerate(sorted(groups.items()),1):
  for D in deadlines:
   witness=g['witnesses'].get(D);h=witness or g['canonical'];rows=cp(h['rows']);index=h['expiry_index'];rows[index]['deadline_remaining_msec']=D-rows[index]['wall_msec'];expected='CONSISTENT' if witness else 'INVALID';name='prefix'+str(number)+'-deadline'+str(D);folder=a.output/name;folder.mkdir();at=text(rows);(folder/'client.txt').write_text(ct);(folder/'authority.txt').write_text(at);r=m.analyze(ct,at)
   result=dict(name=name,expected=expected,actual=r['transition_status'],matched=r['transition_status']==expected,C=C,claimed_deadline=D,visible_prefix_sha256=g['prefix_sha256'],all_possible_deadlines=sorted(g['witnesses']),source_witness=cp(witness['events']) if witness else None,canonical_source_events=cp(h['events']),mutated_expiry_index=index+1,result=r);(folder/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');results.append(result)
 s=dict(scope='UNFROZEN bounded absorbing rejection history assessment',prototype_sha256=hashlib.sha256(a.prototype.read_bytes()).hexdigest(),concrete_source_histories=len(concrete),visible_prefixes=len(groups),cases=len(results),expected_valid=sum(r['expected']=='CONSISTENT' for r in results),expected_invalid=sum(r['expected']=='INVALID' for r in results),matches=sum(r['matched'] for r in results),false_complete=[r['name'] for r in results if r['expected']=='INVALID' and r['actual']=='CONSISTENT'],unexpected=[{k:r[k] for k in ['name','expected','actual']} for r in results if not r['matched']],cpu_affinity=[4],native_executed=False,source_approved=False)
 (a.output/'SUMMARY.json').write_text(json.dumps(s,indent=2)+'\n');print(json.dumps(s,indent=2));return int(bool(s['unexpected']))
if __name__=='__main__':raise SystemExit(main())
