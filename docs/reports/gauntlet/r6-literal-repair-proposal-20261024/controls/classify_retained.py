#!/usr/bin/env python3
"""Static retained-record/source classification. Never imports/executes reader."""
import ast,gzip,hashlib,json,subprocess
from collections import Counter
from pathlib import Path
C='b5a3ea334e5a2b02fe6600683823c4f21e56b23e';R='docs/reports/gauntlet/windows-input-foundation-r6-root-20261024/literal158-r1/';P=Path(__file__).resolve().parents[1]
def blob(p):return subprocess.check_output(['git','show',C+':'+p])
failraw=blob(R+'FAILURES.json');failures=json.loads(failraw);rawgzip=blob(R+'CALLS.jsonl.gz');records=[json.loads(x) for x in gzip.decompress(rawgzip).splitlines()];byid={x['id']:x for x in records};source={}
def method_data(test):
 module,cls,method=test.split(' (',1)[0].split('.')
 path='scripts/'+module+'.py';raw=source.setdefault(path,blob(path));t=ast.parse(raw);cl=next(n for n in t.body if isinstance(n,ast.ClassDef) and n.name==cls);fn=next(n for n in cl.body if isinstance(n,ast.FunctionDef) and n.name==method);segment=b''.join(raw.splitlines(keepends=True)[fn.lineno-1:fn.end_lineno]);return dict(path=path,line=fn.lineno,method_sha256=hashlib.sha256(segment).hexdigest(),module_sha256=hashlib.sha256(raw).hexdigest())
def authority_rows(rec):
 if not rec:return []
 if rec['entry']=='analyze':return [json.loads(x[len('SIGHTBREAK_INPUT_OBSERVATION '):]) for x in rec['authority_text'].splitlines() if x.startswith('SIGHTBREAK_INPUT_OBSERVATION ')]
 return rec.get('rows',[])
def contradiction(rows):
 peers={};prior=None
 for row in rows:
  peer,gen,now=row['peer'],row['generation'],row['wall_msec'];identity=(peer,gen)
  if row['reason']=='peer_connected' and peer not in {x[0] for x in peers} and len(peers)<10:
   age,rem=row['input_age_msec'],row['deadline_remaining_msec']
   if age>=0 and age+rem!=20000:return dict(kind='successful-connect-sum',row=row['index'],now=now,age=age,remaining=rem,sum=age+rem,required=20000,source='PeerLifecycle.connected11–16')
   if age>=0:peers[identity]=dict(C=now-age,L=now-age)
  if identity in peers and row['input_age_msec']>=0:
   state=peers[identity];last=now-row['input_age_msec'];deadline=now+row['deadline_remaining_msec']
   if deadline!=state['C']+20000 and deadline-500>now:
    return dict(kind='impossible-deadline',row=row['index'],now=now,C=state['C'],observed_D=deadline,unrejected_D=state['C']+20000,required_reject_at=deadline-500,source='PeerLifecycle.connected11–16/reject34–37; proposed rejection is in future')
   if last<state['C']:return dict(kind='last-before-connection',row=row['index'],now=now,L=last,C=state['C'],source='PeerLifecycle.connected/admitted/active')
   if last<state['L']:return dict(kind='last-regressed',row=row['index'],now=now,L=last,prior_L=state['L'],source='PeerLifecycle.admitted27–32/active49–51/reject34–37')
   state['L']=last
  if row['reason']=='peer_disconnected':peers.pop(identity,None)
  prior=row
 return None
out=[];historical_index=0
for ordinal,event in enumerate(failures):
 test=event['test'];base=test.split(' (',1)[0];calls=[byid[i] for i in event['calls'] if i in byid];analyses=[x for x in calls if x['entry']=='analyze'];rec=analyses[-1] if analyses else next((x for x in reversed(calls) if x['entry']=='analyze_role' and x.get('role')=='authority'),None)
 if 'test_known_schema_valid_source_negatives_are_frozen' in test:
  matches=[x for x in records if x['entry']=='analyze' and x.get('test')==base];assert len(matches)==8;rec=matches[historical_index];historical_index+=1
 info=method_data(test);result=rec.get('result') if rec else None;rows=authority_rows(rec);cert=contradiction(rows) if rows else None
 x=dict(ordinal=ordinal,kind=event['kind'],test=test,source=info,original_failure_sha256=hashlib.sha256(json.dumps(event,sort_keys=True).encode()).hexdigest(),original_failure_reference=C+':'+R+'FAILURES.json#'+str(ordinal),traceback=event['traceback'],retained_call_ids=event['calls'],selected_call_id=rec['id'] if rec else None,selected_result=result,selected_authority_input_sha256=hashlib.sha256(rec['authority_text'].encode()).hexdigest() if rec and rec['entry']=='analyze' else None)
 if 'test_input_consumption_foundation_model.' in test:
  x.update(classification='historical-preedit-target',purpose='Explicit frozen old-reader/helper benchmark, not current-reader positive; existing exact18 adapter is the retained target.',first_repair_group=False,proposal='Use existing historical18 target unchanged; never count its old false completes as current success.')
 elif 'test_new_positive_lifecycle_projection_and_old_helper_unchanged' in test:
  x.update(classification='legacy-reference-current-reader-target-conflict',purpose='Method compares a frozen pre-amendment helper against new source-projected rows; the new rows must still execute the CURRENT reader.',first_repair_group=True,proposal='Bind only this method test-module declared_rows to immutable old9f constructor; keep analyze on CURRENT R6. Preserve all original assertions. Different adjudication required.')
 elif 'test_missing_legacy_connected_foundation_stays_unknown_then_later_invalid' in test:
  x.update(classification='historical-expiry-target-conflict',purpose='Method explicitly asserts expiry-only missing-foundation UNKNOWN followed by a definitive later INVALID, predating foundation enforcement.',first_repair_group=True,proposal='Bind only this named method to immutable old d2 reader/old9f constructor, no current candidate credit; preserve current foundation INVALID controls separately. Different adjudication required.')
 elif 'test_definite_prefix_faults_are_not_hidden' in test:
  x.update(classification='source-impossible-control-permitted-proposal-unapplied',purpose='An alleged UNKNOWN parent precedes structural mutations, but count1 seq1 is fully acknowledged at prior ACK1; no new accepted intent.',source_certificate=dict(kind='fully-acknowledged-accept',count=1,first=1,last=1,prior_ack=1,source='InputStream.accept25–39; exact23-leaf alternative already43a adjudicated'),first_repair_group=False,proposal='Only already supported exact23-leaf version may replace construction; original assertions/source/results remain unchanged until separately implemented.')
 elif 'old_generation_or_actor_alias_cannot_qualify' in test:
  x.update(classification='negative-message-priority-conflict',purpose='Input remains correctly INVALID; expected consumed-identity substring loses to persistent metadata mutation without a counter increment.',source_certificate=dict(kind='persistent-metadata-counter-contradiction',source='analyze_input_consumption.observation_prefix_invariants; original actual error retained'),first_repair_group=False,proposal='Future named constructor must isolate consumed-identity purpose without adding an unrelated earlier contradiction; no assertion/message weakening is approved.')
 else:
  x.update(classification='source-impossible-derived-construction' if cert else 'unresolved-needs-specific-witness',purpose='Original stream/queue/lifecycle claim is not adjudicated by this failure because its seed already contradicts the source lifecycle projection.',source_certificate=cert,first_repair_group=False,proposal='New named source-operation constructor and full paired intended counterfactuals required; timer repair alone does not prove coalescing/physics/ownership/packet semantics.')
 if rec and rec['entry']=='analyze_role':x['selected_authority_rows_sha256']=hashlib.sha256(json.dumps(rows,sort_keys=True).encode()).hexdigest()
 out.append(x)
summary=dict(source=C,reader_code='6ef4d145ab70ed943c54ec26865e0c884b64b1a9',events=len(out),failure_events=sum(x['kind']=='failure' for x in out),errors=sum(x['kind']=='error' for x in out),categories=dict(Counter(x['classification'] for x in out)),raw_failure_blob_sha256=hashlib.sha256(failraw).hexdigest(),raw_calls_gzip_sha256=hashlib.sha256(rawgzip).hexdigest(),copied_original_call_corpus=False,new_reader_or_model_execution=False,events_detail=out)
assert len(out)==46 and historical_index==8
purposes=json.loads((P/'PURPOSES.json').read_text())
for event in out:
 method=event['test'].split(' (',1)[0].split('.')[-1]
 if method in purposes:event['purpose']=purposes[method]
(P/'CLASSIFICATION.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps({k:v for k,v in summary.items() if k!='events_detail'},indent=2))
for x in out:
 if x['classification'].startswith('source-impossible-derived') or x['classification'].startswith('unresolved'):
  print(x['ordinal'],x['test'].split('.')[-1],x.get('source_certificate'))
