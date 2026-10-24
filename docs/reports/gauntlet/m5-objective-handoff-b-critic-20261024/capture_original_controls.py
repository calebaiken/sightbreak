#!/usr/bin/env python3
"""Run unchanged critic rig, retaining each actual new input once."""
import argparse
import contextlib
import gzip
import hashlib
import importlib
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import time

p=argparse.ArgumentParser()
p.add_argument('--source',type=Path,required=True)
p.add_argument('--rig',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
a=p.parse_args()
assert sorted(os.sched_getaffinity(0))==[4]
a.source=a.source.resolve();a.rig=a.rig.resolve();a.output=a.output.resolve()
a.output.mkdir(parents=True,exist_ok=False);(a.output/'inputs').mkdir()
sys.path.insert(0,str(a.source/'scripts'))
t=importlib.import_module('test_bot_objective_observation')
original_log=t.log
inputs={}
def retained_log(rows):
    raw=original_log(rows);blob=raw.encode();sha=hashlib.sha256(blob).hexdigest()
    if sha not in inputs:
        path=a.output/'inputs'/(sha+'.log.gz')
        path.write_bytes(gzip.compress(blob,compresslevel=6,mtime=0))
        inputs[sha]=dict(path=str(path.relative_to(a.output)),raw_bytes=len(blob),compressed_bytes=path.stat().st_size,compressed_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    return raw
t.log=retained_log
sys.argv=[str(a.rig),str(a.source)]
start=time.monotonic();code=0
with (a.output/'rig.stdout').open('w') as out,(a.output/'rig.stderr').open('w') as err,contextlib.redirect_stdout(out),contextlib.redirect_stderr(err):
    try:runpy.run_path(str(a.rig),run_name='__main__')
    except SystemExit as e:code=e.code
raw=(a.output/'rig.stdout').read_text();decoder=json.JSONDecoder();objects=[]
while raw.strip():
    obj,end=decoder.raw_decode(raw.lstrip());objects.append(obj);raw=raw.lstrip()[end:]
report=dict(scope='Unchanged independent13 mutation rig against corrected helper; synthetic source-only inputs',
            frozen_source='102d79f22082b9c077e2feaccefc84f8985c5875',
            checkout_head=subprocess.check_output(['git','-C',str(a.source),'rev-parse','HEAD'],text=True).strip(),
            verifier_sha256=hashlib.sha256((a.source/'scripts/verify_bot_objective_observation.py').read_bytes()).hexdigest(),
            helper_sha256=hashlib.sha256((a.source/'scripts/test_bot_objective_observation.py').read_bytes()).hexdigest(),
            rig_sha256=hashlib.sha256(a.rig.read_bytes()).hexdigest(),cpu_affinity=[4],elapsed_seconds=time.monotonic()-start,exit_code=code,
            static_footer_source_label_is_legacy=True,results=objects[-1],inputs=inputs)
(a.output/'results.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ['inputs','results']},indent=2))
print(json.dumps({'positive_accepted':objects[-1]['positive_accepted'],'mutations_rejected':objects[-1]['mutations_rejected'],'false_passes':objects[-1]['false_passes']},indent=2))
raise SystemExit(code)
