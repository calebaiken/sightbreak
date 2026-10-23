#!/usr/bin/env python3
"""Independent duplicate/role falsifiers derived from retained synthetic baseline."""
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
assert sorted(os.sched_getaffinity(0))==[4]
base=Path(__file__).resolve().parent
source=Path(sys.argv[1]).resolve(); output=Path(sys.argv[2]).resolve(); output.mkdir(parents=True,exist_ok=False)
spec=importlib.util.spec_from_file_location('candidate',source/'scripts/analyze_input_consumption.py'); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
folder=base/'independent-controls-r3/coherent_independent_pipeline'
c=(folder/'client.log').read_text(); s=(folder/'authority.log').read_text()
rows=m.parse_log(c); server=m.parse_log(s)
def text(rows): return 'INDEPENDENT SYNTHETIC SUPPLEMENT ONLY\n'+'\n'.join(m.PREFIX+json.dumps(x) for x in rows)+'\n'
cases=[]
def run(name,ct,st):
    result=m.analyze(ct,st); path=output/name; path.mkdir(); (path/'client.log').write_text(ct); (path/'authority.log').write_text(st); (path/'result.json').write_text(json.dumps(result,indent=2)+'\n'); cases.append(dict(name=name,expected_complete=False,actual_complete=result['diagnostic_complete'],expectation_met=not result['diagnostic_complete']))
run('duplicate_index_record',c+m.PREFIX+json.dumps(rows[-1])+'\n',s)
run('duplicate_json_key',c.replace('"schema": 1','"schema": 1, "schema": 1',1),s)
ss=deepcopy(server); repeated=deepcopy(ss[5]); repeated.update(index=7,wall_msec=9500,wall_unix_msec=109500,process_frames=7,physics_frames=7,drawn_frames=7); repeated['counters']['input_consumed']=2; repeated['latest']['input_consumed']['wall_msec']=9500; ss.insert(6,repeated); ss[-1].update(index=8,process_frames=8,physics_frames=8,drawn_frames=8); ss[-1]['counters']['input_consumed']=2
run('duplicate_consumption_sequence',c,text(ss))
rr=deepcopy(rows); impossible=deepcopy(rr[-1]); impossible.update(reason='peer_expired',index=8,wall_msec=14000,wall_unix_msec=114000,process_frames=8,physics_frames=8,drawn_frames=8,snapshot_age_msec=7600); impossible['counters']['peer_expired']=1; rr.append(impossible)
run('authority_expiry_stage_in_client_role',text(rr),s)
report=dict(candidate='c0738163965804297a1881905d5bb4646da40a16',checkout_head=subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip(),cpu_affinity=[4],analyzer_sha256=hashlib.sha256((source/'scripts/analyze_input_consumption.py').read_bytes()).hexdigest(),cases=cases,cases_total=len(cases),expectations_met=sum(x['expectation_met'] for x in cases))
(output/'results.json').write_text(json.dumps(report,indent=2)+'\n'); print(json.dumps(report,indent=2))
