#!/usr/bin/env python3
"""Exact old fixtures plus conditional source handoff boundary controls."""
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
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
assert sorted(os.sched_getaffinity(0))==[4]
a.source=a.source.resolve();a.output.mkdir(parents=True,exist_ok=False);home=Path(__file__).resolve().parent;fixtures=home/'replay-fixtures'
sys.path.insert(0,str(a.source/'scripts'));v=importlib.import_module('verify_bot_objective_observation')
cases=[]
def run(item,raw):
    if item['method']=='action':
        data=json.loads(raw);v.state(data['current']);v.state(data['observed'])
    try:
        if item['method']=='action':v.action_handoff(data['current'],data['observed'])
        else:v.verify(raw.decode(),a.source)
    except (ValueError,KeyError,TypeError) as e:accepted=False;error=str(e)
    else:accepted=True;error=None
    receipt=dict(item,actual_accepted=accepted,error=error,met_expectation=accepted==item['expected_accepted'])
    if item['name'] in ['carrier_death_suppresses_required_drop','dead_carrier_stays_carried_complete_stream','root-missing-drop-14458']:
        receipt['intended_guard_error']=error=='action phase omitted required carrier drop'
    cases.append(receipt)
for item in json.loads((fixtures/'index.json').read_text())['fixtures']:
    blob=(fixtures/item['path']).read_bytes();raw=gzip.decompress(blob)
    assert hashlib.sha256(blob).hexdigest()==item['gzip_sha256'] and hashlib.sha256(raw).hexdigest()==item['raw_sha256']
    run(item,raw)
def load(name):return json.loads(gzip.decompress((fixtures/'projection'/(name+'.json.gz')).read_bytes()))
drop=load('carrier_drop_uses_post_movement_position');carrier=str(drop['current']['carrier']);team=drop['current']['actors'][carrier]['team']
other=next(i for i,x in drop['current']['actors'].items() if i!=carrier and x['team']==team)
extra=[]
x=deepcopy(drop);x['observed'].update(objective='carried',carrier=int(other));extra.append(('forged_preconsumer_recovery',x,False,'A dead carrier requires pre-consumer dropped state; actual recovery belongs to the later consumer.'))
x=deepcopy(drop);x['observed']['carrier']=int(carrier);extra.append(('dropped_device_keeps_dead_carrier_id',x,False,'Required drop clears carrier identity to0.'))
x=deepcopy(drop);x['observed']['objective']='planted';extra.append(('claimed_plant_bypasses_death_drop',x,False,'A claimed objective transition cannot bypass protected carrier death.'))
x=load('uncredited_world_elimination');x['observed'].update(objective='dropped',carrier=0,objective_position=deepcopy(x['observed']['actors'][carrier]['position']));extra.append(('noncarrier_death_cannot_drop',x,False,'Only the carried actor elimination can trigger action-phase drop.'))
x=deepcopy(drop)
for key in ['current','observed']:x[key].update(objective='planted',objective_position=[-15,0,10],objective_timer=35.0,carrier=int(carrier))
extra.append(('planted_planter_death_keeps_device_planted',x,True,'After planting the carrier field can retain its prior ID, but _eliminated drops only carried objectives.'))
x=deepcopy(drop)
for key in ['current','observed']:x[key].update(objective='dropped',objective_position=[-15,0,10],carrier=0)
extra.append(('already_dropped_noncarrier_death',x,True,'Death after the device is already dropped preserves device identity/position.'))
x=deepcopy(drop);enemy=next(i for i,z in x['current']['actors'].items() if z['team']!=team and z['alive']);victim=next(i for i,z in x['current']['actors'].items() if z['team']!=team and z['alive'] and i!=enemy)
x['observed']['actors'][victim].update(alive=False,health=0,velocity=[0,0,0]);x['observed']['actors'][victim]['deaths']+=1;x['observed']['actors'][other]['kills']+=1;x['observed']['actors'][other]['credits']=min(9000,x['observed']['actors'][other]['credits']+300)
extra.append(('carrier_drop_with_independent_opposing_death',x,True,'Necessary counter fields allow independent queued eliminations while preserving mandatory carrier drop; no attribution/physics claim.'))
x=load('moving_carrier_keeps_stored_objective_position');x['observed']['objective_position']=deepcopy(x['observed']['actors'][carrier]['position']);extra.append(('living_carrier_cannot_rewrite_stored_device_position',x,False,'Living carried movement does not update stored objective_position in the action interval.'))
folder=a.output/'new-boundaries';folder.mkdir()
for name,data,expected,basis in extra:
    raw=json.dumps(data,separators=(',',':')).encode();blob=gzip.compress(raw,mtime=0);(folder/(name+'.json.gz')).write_bytes(blob)
    run(dict(name=name,group='new-boundaries',method='action',expected_accepted=expected,source_basis=basis,raw_sha256=hashlib.sha256(raw).hexdigest(),gzip_sha256=hashlib.sha256(blob).hexdigest()),raw)
report=dict(candidate='102d79f22082b9c077e2feaccefc84f8985c5875',checkout_head=subprocess.check_output(['git','-C',str(a.source),'rev-parse','HEAD'],text=True).strip(),reader_sha256=hashlib.sha256((a.source/'scripts/verify_bot_objective_observation.py').read_bytes()).hexdigest(),cpu_affinity=[4],source_audit=v.source_audit(a.source),cases=cases,cases_total=len(cases),expectations_met=sum(c['met_expectation'] for c in cases),intended_drop_errors=all(c.get('intended_guard_error',True) for c in cases),false_accepts=[c['name'] for c in cases if not c['expected_accepted'] and c['actual_accepted']],false_rejects=[c['name'] for c in cases if c['expected_accepted'] and not c['actual_accepted']],scope='Corrected handoff component only; conditional necessary projections, no complete combat/AI/native/source/API readiness claim')
(a.output/'results.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:z for k,z in report.items() if k!='cases'},indent=2));raise SystemExit(report['expectations_met']!=len(cases) or not report['intended_drop_errors'])
