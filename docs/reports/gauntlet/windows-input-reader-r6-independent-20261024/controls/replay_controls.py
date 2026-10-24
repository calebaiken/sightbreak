#!/usr/bin/env python3
"""Exact retained corpora plus a separately adjudicated source-state version."""
import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess

assert sorted(os.sched_getaffinity(0)) == [4]
p=argparse.ArgumentParser()
p.add_argument('--source',type=Path,required=True)
p.add_argument('--reader',type=Path)
p.add_argument('--output',type=Path,required=True)
a=p.parse_args()
home=Path(__file__).resolve().parent
reader=a.reader or a.source/'scripts/analyze_input_consumption.py'
spec=importlib.util.spec_from_file_location('actual_reader',reader)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
a.output.mkdir(parents=True,exist_ok=False)
cases=[]
obsolete=('historical-source-corrected-independent-25','consumption_outside_accepted_batch')

def run(group,name,client,authority,expected,basis,prior=None):
    result=m.analyze(client,authority)
    status=result.get('transition_status', 'CONSISTENT' if result['diagnostic_complete'] else 'INVALID')
    folder=a.output/group/name
    folder.mkdir(parents=True)
    (folder/'client.log').write_text(client)
    (folder/'authority.log').write_text(authority)
    receipt=dict(group=group,name=name,expected_complete=expected,
        actual_complete=result['diagnostic_complete'], expected_status='CONSISTENT' if expected else 'INVALID',
        actual_status=status, legacy_status_inferred='transition_status' not in result,
        expectation_met=result['diagnostic_complete']==expected and status==('CONSISTENT' if expected else 'INVALID'),
        source_basis=basis,prior_expectation=prior,result=result)
    (folder/'result.json').write_text(json.dumps(receipt,indent=2)+'\n')
    cases.append({key:value for key,value in receipt.items() if key!='result'})

old=home/'r5-builder-frozen/final-full-controls'
for case in json.loads((old/'results.json').read_text())['cases']:
    group,name=case['group'],case['name']
    folder=old/group/name
    client,authority=(folder/'client.log').read_text(),(folder/'authority.log').read_text()
    newly_obsolete=(group,name)==obsolete
    run('prior-'+group,name,client,authority,False if newly_obsolete else case['expected_complete'],
        'Exact prior108 bytes/outcomes retained. '+('Independent adjudication: queued21/22 cannot pop22 first with C1/skipped0, and ACK regresses next row; obsolete positive.' if newly_obsolete else 'Prior registered source requirement unchanged.'),
        dict(r5_expected_complete=case['expected_complete'],r5_actual_complete=case['actual_complete'],r6_newly_obsolete=newly_obsolete))
    if newly_obsolete:
        rows=m.parse_log(authority)
        consumed=next(row for row in rows if row['reason']=='input_consumed')
        value=deepcopy(consumed['latest']['input_consumed'])
        value['sequence']=21
        for row in rows:
            if row['index']>=consumed['index']:
                row.update(stream_ack=21,queue_count=1)
                row['latest']['input_consumed']=deepcopy(value)
                row['actor']['input']={key:deepcopy(value[key]) for key in m.CONTROL_KEYS}
        corrected='VERSIONED SOURCE-FAITHFUL QUEUE STATE; NO NATIVE OBSERVATIONS\n'+'\n'.join(m.PREFIX+json.dumps(row) for row in rows)+'\n'
        run('versioned','consumption_older_than_latest_accepted',client,corrected,True,
            'Independent fixture adjudication: retain latest accepted22/A2/R2 but pop oldest21, ACK/actor21 and queue1 retaining22 through terminal tick. Exact old impossible case stays separate.')

fresh=home/'r5-critic-frozen/own-fresh-controls'
for folder in sorted(fresh.iterdir()):
    if folder.is_dir():
        case=json.loads((folder/'RESULT.json').read_text())
        run('fresh-r5-critic',folder.name,(folder/'client.txt').read_text(),
            (folder/'authority.txt').read_text(),case['expected'],case['source_basis'])

report=dict(scope='Offline transition constraints; exact old corpora and adjudication retained',
    source=subprocess.check_output(['git','-C',str(a.source),'rev-parse','HEAD'],text=True).strip(),
    reader_path=str(reader.resolve()),reader_sha256=hashlib.sha256(reader.read_bytes()).hexdigest(),
    cpu_affinity=[4],cases=cases,total=len(cases),met=sum(c['expectation_met'] for c in cases),
    newly_obsolete_positive_count=1,passed=all(c['expectation_met'] for c in cases))
(a.output/'results.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({key:value for key,value in report.items() if key!='cases'},indent=2))
raise SystemExit(not report['passed'])
