#!/usr/bin/env python3
"""Reproduce sealed, unchanged critic cases; retain their static original labels."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

p=argparse.ArgumentParser()
p.add_argument('--source',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
a=p.parse_args()
if sorted(os.sched_getaffinity(0)) != [4]: raise RuntimeError('CPU 4 only')
a.output.mkdir(parents=True,exist_ok=False)
base=Path(__file__).resolve().parent/'unchanged-critic-controls'
expected={'independent_controls.py':'0a9d9117abb25bb995e385b689d3d860df346ae07145241508c94bf80c255e80','supplemental_controls.py':'250fea854a64e932c50f4468f46834b20c62c0f587521a1b267ceeacd3bfffd5'}
report={'scope':'Unchanged independent synthetic falsifiers; no native run or source approval','source':subprocess.check_output(['git','-C',str(a.source),'rev-parse','HEAD'],text=True).strip(),'analyzer_sha256':hashlib.sha256((a.source/'scripts/analyze_input_consumption.py').read_bytes()).hexdigest(),'cpu_affinity':[4],'groups':[],'note':'The rigs retain original hardcoded candidate c0738163 labels. Actual source and analyzer bytes are independently bound by this wrapper and each rig checkout_head.'}
for name,count in [('independent_controls.py',25),('supplemental_controls.py',4)]:
 rig=base/name
 if hashlib.sha256(rig.read_bytes()).hexdigest()!=expected[name]: raise RuntimeError('Changed critic rig: '+name)
 target=a.output/('independent-25' if count==25 else 'supplemental-4')
 command=[sys.executable,str(rig),'--source',str(a.source.resolve()),'--output',str(target.resolve())] if count==25 else [sys.executable,str(rig),str(a.source.resolve()),str(target.resolve())]
 result=subprocess.run(command,capture_output=True,timeout=60)
 (a.output/(name+'.stdout')).write_bytes(result.stdout)
 (a.output/(name+'.stderr')).write_bytes(result.stderr)
 observed=json.loads((target/'results.json').read_text()) if (target/'results.json').exists() else {}
 passed=result.returncode==0 and observed.get('cases_total')==count and observed.get('expectations_met')==count and observed.get('checkout_head')==report['source'] and observed.get('analyzer_sha256')==report['analyzer_sha256']
 report['groups'].append({'rig':name,'rig_sha256':expected[name],'command':command,'exit_code':result.returncode,'cases':observed.get('cases_total'),'expectations_met':observed.get('expectations_met'),'passed':passed})
report['passed']=all(row['passed'] for row in report['groups'])
(a.output/'binding-results.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
raise SystemExit(not report['passed'])
