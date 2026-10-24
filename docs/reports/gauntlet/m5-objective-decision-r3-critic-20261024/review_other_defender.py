#!/usr/bin/env python3
"""Isolate non-nearest defender role; no complete AI/path model claim."""
import argparse
from copy import deepcopy
import gzip
import hashlib
import importlib
import json
import os
from pathlib import Path
import sys

p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
assert sorted(os.sched_getaffinity(0))==[4]
a.output.mkdir(parents=True,exist_ok=False)
sys.path.insert(0,str(a.source.resolve()/'scripts'));t=importlib.import_module('test_bot_objective_observation');v=importlib.import_module('verify_bot_objective_observation')
before=t.protected(127);before.update(objective='planted',objective_position=[-15,0,10],objective_timer=35.0)
for aid,actor in before['actors'].items():
    if actor['team']==1:actor['position']=[100+int(aid),0,100]
before['actors']['6'].update(team=1,alive=True,position=[-15,0,14])
before['actors']['7'].update(team=1,alive=True,position=[-15,0,12])
row=t.decision('isolated_other_defender',before,interact=False)
row['observation']['decision']['role']='retake_cover'
# Actor6 uses planted-site0 offset[6%5]=[0,0,-4] on the clear-path
# branch. This corpus isolates role/nearest checks, not arena geometry.
for branch in ['plan','decision']:row['observation'][branch]['destination']=[-15,0,6]
row['observation']['navigation_destination']=[-15,0,6]
cases=[]
for name,role,expected in [('other_defender_retake_cover','retake_cover',True),('other_defender_forges_defuser','defuser',False)]:
    current=deepcopy(row);current['observation']['decision']['role']=role
    error=None
    try:v.decision(current)
    except (ValueError,KeyError,TypeError) as e:accepted=False;error=str(e)
    else:accepted=True
    raw=json.dumps(current,separators=(',',':')).encode();(a.output/(name+'.json.gz')).write_bytes(gzip.compress(raw,mtime=0))
    cases.append(dict(name=name,expected_accepted=expected,accepted=accepted,error=error,met_expectation=accepted==expected,input_sha256=hashlib.sha256(raw).hexdigest(),source_basis='bot_ai planted non-nearest defender receives retake_cover; nearest role comes from protected live all-bot state.'))
(a.output/'results.json').write_text(json.dumps(dict(cpu_affinity=[4],cases=cases,passed=all(x['met_expectation'] for x in cases)),indent=2)+'\n')
print(json.dumps(cases,indent=2));raise SystemExit(not all(x['met_expectation'] for x in cases))
