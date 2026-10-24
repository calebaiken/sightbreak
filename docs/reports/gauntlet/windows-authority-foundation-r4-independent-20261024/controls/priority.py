#!/usr/bin/env python3
import argparse,copy,hashlib,json,os,sys,types
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert sorted(os.sched_getaffinity(0))==[4];a.output.mkdir(parents=True,exist_ok=False);sys.path.insert(0,str(a.source.resolve()/'scripts'));import analyze_input_consumption as m
home=Path(__file__).resolve().parents[1];assert hashlib.sha256((a.source/'scripts/analyze_input_consumption.py').read_bytes()).hexdigest()=='a2ae9daaf52adc3f4a17de476ca5436c77aca88885a076a5aed2fdae957f67d4'
raw=(a.source/'docs/reports/gauntlet/windows-input-reader-foundation-20261024/legacy-source/scripts/analyze_input_consumption.py').read_bytes();assert hashlib.sha256(raw).hexdigest()=='d2cab3af7e441615a37caedb259b1311eb0b5b1cde46719c1000181223facba1';old=types.ModuleType('old');old.__file__='<hash-bound-d2cab>';exec(compile(raw,old.__file__,'exec'),old.__dict__)
cases=[]
for f in sorted((home/'r3-frozen-priority').glob('*/RESULT.json')):
 r=json.loads(f.read_text());cases.append((f.parent.name,(f.parent/'client.txt').read_text(),(f.parent/'authority.txt').read_text(),r['expected'],'exact frozen R3 bytes'))
base=home/'r3-frozen-priority/source-hidden-accept-ownership';ct=(base/'client.txt').read_text();rows=m.parse_log((base/'authority.txt').read_text())
variants=[]
for name in ['unix-regression','rx-count-unbalanced','accept-count-unbalanced','rejection-state-without-call','rejection-state-exceeds-call','rejection-state-missing-increment','sole-rx-accept-payload-mismatch']:
 x=copy.deepcopy(rows);r=x[-1]
 if name=='unix-regression':r['wall_unix_msec']=1
 if name=='rx-count-unbalanced':r['counters']['input_received']=3
 if name=='accept-count-unbalanced':r['counters']['input_accepted']=3
 if name=='rejection-state-without-call':r['stream_rejected']=1
 if name in {'rejection-state-exceeds-call','rejection-state-missing-increment'}:
  r['counters'].update(input_received=3,input_stream_rejected=1);r['latest']['input_stream_rejected']=copy.deepcopy(r['latest']['input_received']);r['stream_rejected']=2 if name=='rejection-state-exceeds-call' else 0
 if name=='sole-rx-accept-payload-mismatch':r['latest']['input_received']['fire']=0
 at='\n'.join(m.PREFIX+json.dumps(y,separators=(',',':')) for y in x)+'\n';cases.append((name,ct,at,'INVALID','independent registered coupled final-row mutation'))
results=[]
for name,ct,at,expected,provenance in cases:
 folder=a.output/name;folder.mkdir();(folder/'client.txt').write_text(ct);(folder/'authority.txt').write_text(at);schema_error=None
 try:
  for row in m.parse_log(at):m.record_valid(row)
 except Exception as e:schema_error=str(e)
 current=m.analyze(ct,at);prior=old.analyze(ct,at);r=dict(name=name,expected=expected,actual=current['transition_status'],matched=current['transition_status']==expected,schema_error=schema_error,candidate=current,prior=prior,provenance=provenance);(folder/'RESULT.json').write_text(json.dumps(r,indent=2)+'\n');results.append(r)
summary=dict(source='52d2fe5e08d5fb2833040a07fb37f7a99bfd90da',cases=len(results),matches=sum(r['matched'] for r in results),schema_failures=[r['name'] for r in results if r['schema_error']],mismatches=[{k:r[k] for k in ['name','expected','actual','schema_error']} for r in results if not r['matched']],native_executed=False,cpu_affinity=[4]);(a.output/'SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2));raise SystemExit(bool(summary['mismatches']))
