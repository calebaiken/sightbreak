#!/usr/bin/env python3
import argparse,gzip,hashlib,importlib.util,itertools,json,os
from pathlib import Path
from projected_oracle import Lifecycle

def observation(C,t,D,joined,reason):return dict(wall_msec=t,input_age_msec=t-C,deadline_remaining_msec=D-t,joined=joined,reason=reason,bound_actor=int(joined),peer_bound=joined,counters={})
def witnesses(C,joined,rows):
 candidates=sorted({r['wall_msec']+r['deadline_remaining_msec']-500 for r in rows});result=[]
 for reject in [None]+candidates:
  for cut in ([None] if reject is None else range(len(rows))):
   s=Lifecycle(C)
   if joined:s.admitted(C)
   prev=C;ok=True
   for index,r in enumerate(rows):
    if cut==index:
     if not prev<=reject<=r['wall_msec']:ok=False;break
     s.reject(reject)
    if r['reason']=='input_received' and (not s.joined or s.rejected):ok=False;break
    if s.observe(r['wall_msec'])!={k:r[k] for k in ['wall_msec','input_age_msec','deadline_remaining_msec','joined']}:ok=False;break
    prev=r['wall_msec']
   if ok:result.append(dict(reject=reject,cut=cut,events=s.events,eligible=s.expired(rows[-1]['wall_msec'])))
 return result

def corpus():
 result=[]
 for C,joined,first in itertools.product([0,1000],[False,True],[19499,19500,20000]):
  for hook in (['authority_tick','input_received'] if joined else ['authority_tick']):
   for second in sorted({first,20000,30000}):
    if second<first:continue
    for end in [20000,29999,30000,30001]:
     if end<second:continue
     for D1,D2,D3 in itertools.product([19999,20000,20001],repeat=3):
      rows=[observation(C,C+first,C+D1,joined,hook),observation(C,C+second,C+D2,joined,'authority_tick'),observation(C,C+end,C+D3,joined,'peer_expired')];w=witnesses(C,joined,rows);eligible=[v['eligible'] for v in w];expected='INVALID' if not any(eligible) else 'CONSISTENT' if all(eligible) else 'UNKNOWN';result.append(dict(C=C,joined=joined,rows=rows,witnesses=w,expected=expected))
 return result

def main():
 p=argparse.ArgumentParser();p.add_argument('--prototype',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert sorted(os.sched_getaffinity(0))==[4];a.output.mkdir(parents=True,exist_ok=False);cases=corpus();spec=importlib.util.spec_from_file_location('held_timer_cut_candidate',a.prototype);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);counts={};bad=[];digest=hashlib.sha256()
 with gzip.GzipFile(filename=str(a.output/'CASES.jsonl.gz'),mode='wb',mtime=0) as stream:
  for i,c in enumerate(cases,1):
   C,joined=c['C'],c['joined'];start=observation(C,C,C+20000,False,'peer_connected');h=m.LifecycleHypotheses(start)
   if joined:h.observe(observation(C,C,C+20000,True,'peer_bound'),1)
   for row in c['rows'][:-1]:h.observe(row,int(joined))
   actual=h.expiry(c['rows'][-1],int(joined));r=dict(id=i,**c,actual=actual,matched=actual==c['expected'],model_detail=h.detail,model_errors=h.errors);counts[c['expected']]=counts.get(c['expected'],0)+1;raw=(json.dumps(r,separators=(',',':'))+'\n').encode();digest.update(raw);stream.write(raw)
   if not r['matched']:bad.append({k:r[k] for k in ['id','expected','actual','model_detail','model_errors']})
 summary=dict(scope='Independent isolated source timer ordered-cut closure; not Match service scheduling',prototype_sha256=hashlib.sha256(a.prototype.read_bytes()).hexdigest(),cases=len(cases),matches=len(cases)-len(bad),expected=counts,mismatches=bad,raw_jsonl_sha256=digest.hexdigest(),gzip_sha256=hashlib.sha256((a.output/'CASES.jsonl.gz').read_bytes()).hexdigest(),cpu_affinity=[4],native_executed=False);(a.output/'SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2));return int(bool(bad))
if __name__=='__main__':raise SystemExit(main())
