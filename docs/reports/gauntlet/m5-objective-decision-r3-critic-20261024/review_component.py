#!/usr/bin/env python3
"""Independent exact-input replay and isolated source decision controls."""
import argparse
from copy import deepcopy
import gzip
import hashlib
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import types

p=argparse.ArgumentParser()
p.add_argument('--source',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
a=p.parse_args();a.source=a.source.resolve();a.output=a.output.resolve()
assert sorted(os.sched_getaffinity(0))==[4]
a.output.mkdir(parents=True,exist_ok=False)
sys.path.insert(0,str(a.source/'scripts'))
t=importlib.import_module('test_bot_objective_observation')
v=importlib.import_module('verify_bot_objective_observation')
base='dce89495d04c9d3fefece0f8c7929e2e01b8e7df'
sealed='b2370e68'
prefix='docs/reports/gauntlet/m5-objective-observability-r3-20261024/'
def git(*words):return subprocess.check_output(['git','-C',str(a.source),*words])
oldcode=git('show',base+':scripts/verify_bot_objective_observation.py')
(a.output/'historical-verifier.py.txt').write_bytes(oldcode)
old=types.ModuleType('historical_verifier');old.__file__=str(a.source/'scripts/verify_bot_objective_observation.py')
exec(compile(oldcode,'historical_verifier_from_'+base,'exec'),old.__dict__)
oldhelper=types.ModuleType('historical_fixture_helper');oldhelper.__file__=str(a.source/'scripts/test_bot_objective_observation.py')
exec(compile(git('show',base+':scripts/test_bot_objective_observation.py'),'historical_fixture_helper','exec'),oldhelper.__dict__)

manifest=json.loads(git('show',sealed+':'+prefix+'MANIFEST.json'))
manifest_checks=[]
for path,entry in manifest['files'].items():
    blob=git('show',sealed+':'+prefix+path)
    manifest_checks.append(dict(path=path,bytes_match=len(blob)==entry['bytes'],sha256_match=hashlib.sha256(blob).hexdigest()==entry['sha256']))
builder=a.output/'builder-sealed';builder.mkdir()
for path in ['HANDOFF.md','MANIFEST.json','SOURCE_COMPOSITION.json','component-inputs/results.json']+[f'component-inputs/{name}.log.gz' for name in ['positive','wrong_actor','unperceived_target','wrong_defuser_destination','invented_role']]:
    target=builder/path;target.parent.mkdir(parents=True,exist_ok=True)
    target.write_bytes(git('show',sealed+':'+prefix+path))

cases=[]
def outcome(module,rows,method='verify_records'):
    try:getattr(module,method)(rows)
    except (ValueError,KeyError,TypeError) as error:return False,str(error)
    return True,None
def record(name,rows,expected,method='decision',group='isolated-decision',basis=''):
    start=time.monotonic();accepted,error=outcome(v,rows,method);prior,prior_error=outcome(old,rows,method)
    folder=a.output/group;folder.mkdir(exist_ok=True)
    raw=json.dumps(rows,separators=(',',':')).encode()
    (folder/(name+'.json.gz')).write_bytes(gzip.compress(raw,mtime=0))
    cases.append(dict(group=group,name=name,expected_accepted=expected,r3_accepted=accepted,r3_error=error,r2_accepted=prior,r2_error=prior_error,
                      met_expectation=accepted==expected,input_sha256=hashlib.sha256(raw).hexdigest(),source_basis=basis,elapsed_seconds=time.monotonic()-start))

root_results=json.loads((builder/'component-inputs/results.json').read_text())
positive=None
for case in root_results['cases']:
    raw=gzip.decompress((builder/'component-inputs'/(case['name']+'.log.gz')).read_bytes())
    assert hashlib.sha256(raw).hexdigest()==case['sha256'] and len(raw)==case['bytes']
    rows=v.records(raw.decode())
    if case['name']=='positive':positive=rows
    record(case['name'],rows,case['name']=='positive','verify_records','sealed-component',case.get('expected_error') or 'Corrected schema-positive baseline; no complete engine model.')

original_results=[]
for path in sorted((a.source/prefix/'original-independent-inputs').glob('*.gz')):
    rows=v.records(gzip.decompress(path.read_bytes()).decode())
    accepted,error=outcome(v,rows);prior,prior_error=outcome(old,rows)
    original_results.append(dict(name=path.name,r3_accepted=accepted,r3_error=error,r2_accepted=prior,r2_error=prior_error))

fresh=t.synthetic_records();previous=oldhelper.synthetic_records()
def changes(left,right,path=()):
    if type(left) is dict and type(right) is dict:
        if left.keys()!=right.keys():yield dict(path=list(path),old_keys=list(left),new_keys=list(right));return
        for k in left:yield from changes(left[k],right[k],path+(k,))
    elif isinstance(left,(list,tuple)) and isinstance(right,(list,tuple)):
        if len(left)!=len(right):yield dict(path=list(path),old_length=len(left),new_length=len(right));return
        for i,(x,y) in enumerate(zip(left,right)):yield from changes(x,y,path+(i,))
    elif left!=right:yield dict(path=list(path),old=left,new=right)
diffs=list(changes(previous,fresh))
allowed=[]
for entry in diffs:
    path=entry['path'];index=path[0]
    allowed.append(previous[index][0]=='DECISION' and previous[index][1]['label']=='control_defuse' and
                   path[2:] in [['observation','plan','destination',0],['observation','decision','destination',0]] and entry.get('old')==15 and entry.get('new')==-15)
fixture=dict(new_helper_typed_rows_equal_sealed_positive=(fresh==positive),old_new_typed_differences=diffs,
             minimal_defuser_destination_changes_only=bool(diffs) and all(allowed),differences_count=len(diffs))

# Full-record freshness branch identity is independent of the first CALL case.
rows=deepcopy(positive)
next(row for tag,row in rows if tag=='CALL' and row['case']=='branch_change')['output']['decision']['actor_id']=7
record('branch_change_wrong_actor',rows,False,'verify_records','independent-call','Probe freshness_controls always calls actor6, including branch_change.')

def defuser(distance,dead_closer=False):
    before=t.protected(127)
    before.update(objective='planted',objective_position=[-15,0,10],objective_timer=35.0)
    for aid,actor in before['actors'].items():
        if actor['team']==1:actor['position']=[100+int(aid),0,100]
    before['actors']['6'].update(team=1,alive=True,position=[-15,0,10+distance])
    if dead_closer:before['actors']['7'].update(team=1,alive=False,position=[-15,0,10])
    return t.decision('isolated_source_defuser',before,interact=distance<=2.6)

for distance in [0.0,2.5,2.7,4.0]:
    record('nearest_distance_'+str(distance),defuser(distance),True,basis='Source nearest all-bot defender keeps the device destination; interact only at distance<=2.6. Robust inside/outside values avoid unqualified float/native boundary inference.')
record('dead_closer_defender_does_not_take_role',defuser(4.0,True),True,basis='nearest_defender skips dead actors before distance comparison.')
for role in ['anchor','retake_cover','pursue_memory']:
    row=defuser(4.0);row['observation']['decision']['role']=role
    record('nearest_legal_role_bypass_'+role,row,False,basis='Nearest defuser identity is protected-state derived; planted objectives exclude pursue_memory override.')
for distance in [0.0,4.0]:
    row=defuser(distance)
    for branch in ['plan','decision']:row['observation'][branch]['destination']=[999,0,999]
    if row['observation']['movement_mode']=='navigate':row['observation']['navigation_destination']=[999,0,999]
    record('nearest_forged_device_plan_'+str(distance),row,False,basis='Plan remains the actual device at every nearest-defender distance; no await or later destination override changes plan.')

# Check every source role literal remains allowed at the observation schema
# boundary. These isolate the allowlist; they do not assert role/context fidelity.
for role in sorted(v.DECISION_ROLES):
    obs=deepcopy(t.decision('schema',t.protected(120))['observation']);obs['decision']['role']=role
    record('role_schema_'+role,obs,True,'observation','role-schema','Source role literal/schema allowance only; role/context correctness is not qualified.')
obs=deepcopy(t.decision('schema',t.protected(120))['observation']);obs['decision']['role']='not_source_role'
record('invented_role_schema',obs,False,'observation','role-schema','Arbitrary role string is absent from fixed source literals.')

report=dict(frozen_source='bc9f945d7fb0741307504381f4b95b2fa993e392',builder_seal=sealed,checkout_head=git('rev-parse','HEAD').decode().strip(),cpu_affinity=[4],source_audit=v.source_audit(a.source),
            builder_manifest_checks=manifest_checks,builder_manifest_passed=all(x['bytes_match'] and x['sha256_match'] for x in manifest_checks),fixture_fidelity=fixture,
            original_inputs_unmodified_replay=original_results,cases=cases,cases_total=len(cases),expectations_met=sum(x['met_expectation'] for x in cases),
            false_rejects=[x['name'] for x in cases if x['expected_accepted'] and not x['r3_accepted']],false_accepts=[x['name'] for x in cases if not x['expected_accepted'] and x['r3_accepted']],
            scope='Four declared component guards only; full reader retains eight blockers, no native/runtime acceptance')
(a.output/'results.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ['cases','builder_manifest_checks','fixture_fidelity']},indent=2))
print(json.dumps({k:v for k,v in fixture.items() if k!='old_new_typed_differences'},indent=2))
raise SystemExit(report['expectations_met']!=len(cases) or not report['builder_manifest_passed'] or not fixture['minimal_defuser_destination_changes_only'] or not fixture['new_helper_typed_rows_equal_sealed_positive'])
