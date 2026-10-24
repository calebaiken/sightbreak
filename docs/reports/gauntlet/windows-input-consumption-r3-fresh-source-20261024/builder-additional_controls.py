#!/usr/bin/env python3
"""Further source-bound synthetic lifecycle/ordering/header controls; no native run."""
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
assert sorted(os.sched_getaffinity(0)) == [4]
source=Path(sys.argv[1]).resolve(); output=Path(sys.argv[2]).resolve(); output.mkdir(parents=True,exist_ok=False)
old=Path('/workspace/reviews/windows-input-consumption-fresh-source-critic/docs/reports/gauntlet/windows-input-consumption-fresh-source-critic-20261023/independent-controls-r3/coherent_independent_pipeline')
spec=importlib.util.spec_from_file_location('reader',source/'scripts/analyze_input_consumption.py'); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
client=m.parse_log((old/'client.log').read_text()); authority=m.parse_log((old/'authority.log').read_text())

def serialize(rows): return 'INDEPENDENT SYNTHETIC R2 CONTROL ONLY; NO NATIVE OBSERVATIONS\n'+'\n'.join(m.PREFIX+json.dumps(x) for x in rows)+'\n'

def rebuild(rows):
    counters={}; latest={}
    for i,row in enumerate(rows,1):
        reason=row['reason']; counters[reason]=counters.get(reason,0)+1
        if reason in row['latest']:
            value=deepcopy(row['latest'][reason]); value['wall_msec']=row['wall_msec']; latest[reason]=value
        row['index']=row['process_frames']=row['physics_frames']=row['drawn_frames']=i
        row['wall_unix_msec']=100000+row['wall_msec']
        row['counters']=deepcopy(counters); row['latest']=deepcopy(latest)
    return rows

cases=[]
def run(name,c=None,s=None,expected=False,basis=''):
    c=deepcopy(client) if c is None else c; s=deepcopy(authority) if s is None else s
    folder=output/name; folder.mkdir(); ct=serialize(c); st=serialize(s)
    (folder/'client.log').write_text(ct); (folder/'authority.log').write_text(st)
    result=m.analyze(ct,st)
    receipt=dict(name=name,expected_complete=expected,actual_complete=result['diagnostic_complete'],expectation_met=result['diagnostic_complete']==expected,source_basis=basis,result=result)
    (folder/'result.json').write_text(json.dumps(receipt,indent=2)+'\n')
    cases.append({k:v for k,v in receipt.items() if k!='result'})

run('coherent_control',expected=True,basis='Frozen independently authored schema baseline; no native execution claim.')
rows=deepcopy(authority)
for row in rows[2:]:
    row['generation']=2
    if 'input_consumed' in row['latest']: row['latest']['input_consumed']['generation']=2
run('bound_generation_never_connected',s=rows,basis='peer_lifecycle.connected allocates generation; admitted and peer_bound use the same pending attempt. Connected generation1 cannot bind generation2 without another connected event.')
rows=deepcopy(authority)
for row in rows[2:]:
    row['peer']=72
    if 'input_consumed' in row['latest']: row['latest']['input_consumed']['peer']=72
cc=deepcopy(client)
for row in cc[2:]: row['transport_id']=72
run('bound_peer_never_connected',c=cc,s=rows,basis='Only peer71 has connected; peer72 binding cannot be admitted from its nonexistent lifecycle entry.')
rows=deepcopy(authority); rows[1],rows[2]=rows[2],rows[1]; rows[1]['wall_msec']=2500; rows[2]['wall_msec']=3000
run('binding_before_connection',s=rebuild(rows),basis='begin_join/current/admitted require the lifecycle entry created by connected before any binding.')
rows=deepcopy(authority); rebound=deepcopy(rows[2]); rebound.update(wall_msec=3500,bound_actor=5,last_bound_actor=5); rebound['actor']['id']=5; rows.insert(3,rebound)
for row in rows[4:]:
    row.update(bound_actor=5,last_bound_actor=5); row['actor']['id']=5
    if 'input_consumed' in row['latest']: row['latest']['input_consumed']['actor']=5
run('same_generation_rebound_to_other_actor',s=rebuild(rows),basis='Match._join_rpc returns when _peer_actors.has(peer_id); the same live peer/generation cannot bind another actor.')
rows=deepcopy(authority); rows[3],rows[4]=rows[4],rows[3]; rows[3]['wall_msec']=8000; rows[4]['wall_msec']=8500
run('first_accept_before_first_receive',s=rebuild(rows),basis='First input_received always precedes first input_accepted within the synchronous _input_rpc body; its first transition emits before any acceptance.')
rows=deepcopy(authority); rows[4]['latest']['input_accepted'].update(count=1,first=20,last=22)
run('one_command_two_sequence_endpoints',s=rows,basis='_native_input_packet first and last derive from the same sole command when count1. A positive increasing interval alone is insufficient.')
rows=deepcopy(client)
for row in rows[3:]: row['local_attempt']=2
run('welcome_claims_unobserved_attempt',c=rows,basis='diagnostic.attempt increments only in client_attempt, which always emits. A single observed/counted attempt cannot yield local_attempt2 at welcome.')
rows=deepcopy(authority)
for row in rows:
    row['stream_ack'] = 1 if row['reason'] in {'input_consumed','authority_tick'} else -1
    row['queue_count'] = 2 if row['reason']=='input_accepted' else 1 if row['reason'] in {'input_consumed','authority_tick'} else 0
    for stage in ['input_received','input_accepted']:
        if stage in row['latest']: row['latest'][stage].update(count=2,first=2,last=1,fire=2)
    if 'input_consumed' in row['latest']: row['latest']['input_consumed']['sequence']=1
    if row['reason'] in {'input_consumed','authority_tick'}: row['actor']['input']=dict(sequence=1,fire=True,reload=False,move=[0.0,0.0])
run('accepted_unordered_two_command_batch',s=rows,expected=True,basis='SBInputStream.accept validates commands and stages a dictionary without an array-order requirement. With no prior ACK, valid commands2 and1 can both be accepted, then pop consumes1. Header first/last are array endpoints, not extrema. This tests valid authority projection semantics; sparse client/authority observations do not establish packet identity or delivery, and this is no native proof.')
report=dict(candidate='86fe3cbe3f191b328c1e08bf8d5adc0a937e39b1',checkout_head=subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip(),cpu_affinity=[4],analyzer_sha256=hashlib.sha256((source/'scripts/analyze_input_consumption.py').read_bytes()).hexdigest(),cases=cases,cases_total=len(cases),expectations_met=sum(x['expectation_met'] for x in cases))
(output/'results.json').write_text(json.dumps(report,indent=2)+'\n'); print(json.dumps(report,indent=2))
