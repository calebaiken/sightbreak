#!/usr/bin/env python3
import argparse,copy,hashlib,importlib.util,json,os,sys,types
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert sorted(os.sched_getaffinity(0))==[4];a.output.mkdir(parents=True,exist_ok=False);sys.path.insert(0,str(a.source/'scripts'));import analyze_input_consumption as candidate
from test_input_consumption_observation import declared_rows,text
raw=(a.source/'docs/reports/gauntlet/windows-input-reader-foundation-20261024/legacy-source/scripts/analyze_input_consumption.py').read_bytes();assert hashlib.sha256(raw).hexdigest()=='d2cab3af7e441615a37caedb259b1311eb0b5b1cde46719c1000181223facba1';old=types.ModuleType('frozen_prior_reader');old.__file__='<hash-bound-d2cab>';exec(compile(raw,old.__file__,'exec'),old.__dict__)
c=declared_rows('client');s=declared_rows('authority');s[-2]['counters']['authority_tick']=1;r=s[-1];r['counters']['authority_tick']=2
for stage in ['input_received','input_accepted']:
 r['counters'][stage]+=1;r['latest'][stage]=dict(epoch=1,count=1,first=2,last=2,fire=1,reload=0,moving=0,wall_msec=10500)
r.update(input_age_msec=500,deadline_remaining_msec=11000,queue_count=1)
cases=[('source-hidden-accept-ownership',copy.deepcopy(s),'UNKNOWN',None)]
for name,field,value in [('regressed-process','process_frames',1),('regressed-physics','physics_frames',1),('regressed-drawn','drawn_frames',1),('repeated-index','index',6)]:
 rows=copy.deepcopy(s);rows[-1][field]=value;cases.append((name,rows,'INVALID',field))
rows=copy.deepcopy(s);rows[-1]['counters']['authority_tick']=1;cases.append(('reason-counter-not-advanced',rows,'INVALID','counters.authority_tick'))
rows=copy.deepcopy(s);rows[-1]['counters']['peer_connected']=2;cases.append(('missing-lifecycle-event-counter',rows,'INVALID','counters.peer_connected'))
rows=copy.deepcopy(s);rows[-1]['latest']['input_consumed']['fire']=False;cases.append(('unchanged-counter-changed-latest',rows,'INVALID','latest.input_consumed.fire'))
rows=copy.deepcopy(s);rows[-1]['latest']['input_accepted']['wall_msec']=9999;cases.append(('new-metadata-before-prior-observation',rows,'INVALID','latest.input_accepted.wall_msec'))
results=[]
for name,rows,expected,field in cases:
 for row in rows:candidate.record_valid(row)
 folder=a.output/name;folder.mkdir();ct=text(c);at=text(rows);(folder/'client.txt').write_text(ct);(folder/'authority.txt').write_text(at);current=candidate.analyze(ct,at);prior=old.analyze(ct,at);r=dict(name=name,expected=expected,candidate_status=current['transition_status'],matched=current['transition_status']==expected,prior_status=prior['transition_status'],field_changed=field,candidate=current,prior=prior,disclosed_lead=name=='regressed-process',witness='C2000,A3000,L9000; tick9999/pop10000; hidden receive/accept/active10500; tick11000, same source epoch/peer/generation');(folder/'RESULT.json').write_text(json.dumps(r,indent=2)+'\n');results.append(r)
summary=dict(source=str(a.source),reader_sha256=hashlib.sha256((a.source/'scripts/analyze_input_consumption.py').read_bytes()).hexdigest(),cases=len(results),matches=sum(r['matched'] for r in results),mismatches=[{k:r[k] for k in ['name','expected','candidate_status','prior_status']} for r in results if not r['matched']],native_executed=False,new207_replay_executed=False,cpu_affinity=[4]);(a.output/'SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2));raise SystemExit(bool(summary['mismatches']))
