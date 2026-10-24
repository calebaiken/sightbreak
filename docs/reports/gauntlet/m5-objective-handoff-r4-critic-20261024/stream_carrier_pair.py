#!/usr/bin/env python3
"""Counter-consistent elimination pair through the complete schema reader.

This isolates the mandatory drop relation; it does not prove shot geometry,
damage attribution, or that the synthetic helper models every AI side effect.
"""
import argparse
from copy import deepcopy
import gzip
import hashlib
import importlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import types

p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
assert sorted(os.sched_getaffinity(0))==[4]
a.source=a.source.resolve();a.output.mkdir(parents=True,exist_ok=False)
sys.path.insert(0,str(a.source/'scripts'));t=importlib.import_module('test_bot_objective_observation');v=importlib.import_module('verify_bot_objective_observation')
oldcode=subprocess.check_output(['git','-C',str(a.source),'show','bc9f945d7fb0741307504381f4b95b2fa993e392:scripts/verify_bot_objective_observation.py'])
old=types.ModuleType('old_component_reader');old.__file__=str(a.source/'scripts/verify_bot_objective_observation.py');exec(compile(oldcode,'old_component_reader','exec'),old.__dict__)
results=[]
for dropped in [True,False]:
    rows=t.synthetic_records()
    obj=[r for tag,r in rows if tag=='INTERACTION' and r['label']=='forward_live_122'][-1]
    authority=[r for tag,r in rows if tag=='AUTHORITY' and r['label']=='forward_live_122'][-1]
    before=deepcopy(obj['before']);carrier=str(before['carrier']);victim=before['actors'][carrier]
    assert before['objective']=='carried' and victim['alive']
    killer=next(i for i,x in before['actors'].items() if x['alive'] and x['team']!=victim['team'])
    victim.update(alive=False,health=0,velocity=[0,0,0]);victim['deaths']+=1
    before['actors'][killer]['kills']+=1;before['actors'][killer]['credits']=min(9000,before['actors'][killer]['credits']+300)
    if dropped:before.update(objective='dropped',carrier=0,objective_position=deepcopy(victim['position']))
    after=deepcopy(before)
    # All baseline forward commands are non-interacting. Reproduce only the
    # consumer's deterministic recovery and zero-progress branch for this pair.
    assert all(not x['input']['interact'] for x in before['actors'].values())
    if after['objective']=='dropped':
        for aid,actor in after['actors'].items():
            if actor['alive'] and actor['team']==0 and math.dist(actor['position'],after['objective_position'])<2:
                after.update(objective='carried',carrier=int(aid));break
    after['interactions']={};after['interaction_progress']=0.0
    obj.update(t.interaction(obj['label'],before,after))
    post=deepcopy(after)
    if post['phase']=='live':
        attackers=sum(x['alive'] and x['team']==0 for x in post['actors'].values());defenders=sum(x['alive'] and x['team']==1 for x in post['actors'].values())
        if defenders==0:v.end_round(post,0)
        elif attackers==0 and post['objective']!='planted':v.end_round(post,1)
    if post['phase']!='match_over':post['time_left']=max(0,post['time_left']-v.DT)
    authority['after']=post
    raw=t.log(rows).encode();name='required_drop_then_consumer_recovery' if dropped else 'dead_carrier_stays_carried_complete_stream'
    (a.output/(name+'.log.gz')).write_bytes(gzip.compress(raw,mtime=0))
    def outcome(reader):
        try:reader.verify(raw.decode(),a.source)
        except (ValueError,KeyError,TypeError) as e:return False,str(e)
        return True,None
    accepted,error=outcome(v);prior,prior_error=outcome(old)
    results.append(dict(name=name,expected_accepted=dropped,r4_accepted=accepted,r4_error=error,r3_accepted=prior,r3_error=prior_error,met_expectation=accepted==dropped,raw_sha256=hashlib.sha256(raw).hexdigest(),raw_bytes=len(raw),source_basis='_eliminated must drop when its carried actor dies; the later consumer may recover a genuinely dropped device. Conditional elimination projection only; no ballistics claim.'))
report=dict(cpu_affinity=[4],frozen_source='f48c8461b3b6cb26c5ab2a79f2b51c444e94a0ec',results=results,passed=all(x['met_expectation'] for x in results))
(a.output/'results.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));raise SystemExit(not report['passed'])
