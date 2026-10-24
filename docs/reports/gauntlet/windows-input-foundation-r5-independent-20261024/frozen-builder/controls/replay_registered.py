#!/usr/bin/env python3
"""Replay exact registered inputs; do not repair source evidence."""
import argparse,hashlib,importlib.util,json,os,sys
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--reader-sha256',required=True);a=p.parse_args();assert sorted(os.sched_getaffinity(0))==[4];root=a.source.resolve();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False);reader=root/'scripts/analyze_input_consumption.py';assert hashlib.sha256(reader.read_bytes()).hexdigest()==a.reader_sha256;sys.path.insert(0,str(root/'scripts'));import analyze_input_consumption as m
home=Path(__file__).resolve().parents[1];frozen=home/'r4-critic-frozen';results=[]
for group in ['priority-r1','previous-histories']:
 for f in sorted((frozen/group).glob('*/RESULT.json')):
  original=json.loads(f.read_text());folder=out/group/f.parent.name;folder.mkdir(parents=True);ct=(f.parent/'client.txt').read_bytes();at=(f.parent/'authority.txt').read_bytes();(folder/'client.txt').write_bytes(ct);(folder/'authority.txt').write_bytes(at);actual=m.analyze(ct.decode(),at.decode());r=dict(group=group,name=f.parent.name,expected=original['expected'],actual=actual['transition_status'],matched=original['expected']==actual['transition_status'],result=actual,original_result=original,client_sha256=hashlib.sha256(ct).hexdigest(),authority_sha256=hashlib.sha256(at).hexdigest());(folder/'RESULT.json').write_text(json.dumps(r,indent=2)+'\n');results.append({k:r[k] for k in ['group','name','expected','actual','matched']})
for f in sorted((frozen/'source-prefixes').glob('*.json')):
 if f.name=='SUMMARY.json':continue
 original=json.loads(f.read_text());rows=original['rows'];expected=original['expected'];error=None
 try:m.authority_lifecycle_foundation(rows);actual='POSSIBLE'
 except m.UnknownTransition as e:actual='UNKNOWN';error=str(e)
 except ValueError as e:actual='INVALID';error=str(e)
 folder=out/'source-prefixes';folder.mkdir(exist_ok=True);r=dict(group='source-prefixes',name=original['name'],expected=expected,actual=actual,matched=actual==expected,rows=rows,error=error);(folder/f.name).write_text(json.dumps(r,indent=2)+'\n');results.append({k:r[k] for k in ['group','name','expected','actual','matched']})
summary=dict(source=str(root),reader_sha256=a.reader_sha256,cases=len(results),matches=sum(r['matched'] for r in results),mismatches=[r for r in results if not r['matched']],results=results,cpu_affinity=[4],native_executed=False,scope='Registered exact R4 corpus+bounded source histories, no acceptance');(out/'SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps({k:v for k,v in summary.items() if k!='results'},indent=2));raise SystemExit(bool(summary['mismatches']))
