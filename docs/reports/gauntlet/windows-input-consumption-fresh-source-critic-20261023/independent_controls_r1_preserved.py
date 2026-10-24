#!/usr/bin/env python3
"""Independent synthetic traces; never native observations or gameplay execution."""
import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

p = argparse.ArgumentParser()
p.add_argument('--source', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
assert sorted(os.sched_getaffinity(0)) == [4]
a.output.mkdir(parents=True, exist_ok=False)
root = a.source.resolve()
spec = importlib.util.spec_from_file_location('candidate_analyzer', root / 'scripts/analyze_input_consumption.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def control(seq=-1, fire=False):
    return dict(sequence=seq, fire=fire, reload=False, move=[0.0, 0.0])

def records(role, stages=None):
    stages = stages or (['ready', 'client_attempt', 'client_connected', 'welcome_received', 'client_tick', 'input_send_called', 'client_tick'] if role == 'client' else ['ready', 'peer_connected', 'peer_bound', 'input_received', 'input_accepted', 'input_consumed', 'authority_tick'])
    times = [1000, 2000, 4000, 6000, 6500, 7000, 12000] if role == 'client' else [1000, 2500, 3000, 8000, 8500, 9000, 13000]
    rows, counters, latest = [], {}, {}
    for i, (reason, now) in enumerate(zip(stages, times), 1):
        counters[reason] = counters.get(reason, 0) + 1
        client = role == 'client'
        connected = not client or i >= 3
        bound = not client and i >= 3
        snapshot = {'tick': 83, 'epoch': 7, 'own_ack': 20, 'wall_msec': 6400} if client and i >= 5 else {}
        if snapshot:
            counters['snapshot_applied'] = 1
            latest['snapshot_applied'] = deepcopy(snapshot)
        if reason in {'input_send_called', 'input_received', 'input_accepted'}:
            latest[reason] = dict(epoch=7, count=1, first=21, last=21, fire=1, reload=0, moving=0, wall_msec=now)
        if reason == 'input_consumed':
            latest[reason] = {**control(21, True), 'peer': 71, 'actor': 4, 'generation': 1, 'wall_msec': now}
        if reason == 'welcome_received':
            latest[reason] = {'tick': 82, 'epoch': 7, 'own_ack': -1, 'wall_msec': now}
        rows.append(dict(
            schema=1, scope=m.SCOPE, role=role, reason=reason, index=i,
            wall_unix_msec=100000+now, wall_msec=now, process_frames=i, physics_frames=i, drawn_frames=i,
            connection_state=('connected' if i >= 4 else 'joining' if i >= 3 else 'connecting') if client else 'hosting',
            transport_status=2 if connected else 1, transport_id=71 if client and connected else 1 if not client else 0,
            local_id=4 if client and i >= 4 else 0, local_attempt=1 if client and i >= 2 else 0,
            peer=71 if not client and i >= 2 else 0, bound_actor=4 if bound else 0, last_bound_actor=4 if bound else 0,
            peer_bound=bound, generation=1 if not client and i >= 2 else -1, joined=bound,
            input_age_msec=0 if bound else -1, deadline_remaining_msec=20000 if bound else -1,
            simulation_tick=i if not client else 0, authority_epoch=7, stream_ack=21 if bound else -1,
            queue_count=0, stream_rejected=0, stream_skipped=0, prediction_epoch=7 if client else -1,
            prediction_sequence=21 if client else 0, pending_count=1 if reason=='input_send_called' else 0,
            pending_oldest_sequence=21 if reason=='input_send_called' else -1, pending_newest_sequence=21 if reason=='input_send_called' else -1,
            snapshot=snapshot, snapshot_age_msec=now-6400 if snapshot else -1,
            local_input=control(), physical={'r':False,'lmb':False, **({'physical_mouse_fire':False,'application_focused':True,'paused':False,'waiting_for_input_release':False} if client else {})},
            counters=deepcopy(counters), latest=deepcopy(latest),
            actor={'id':4,'alive':True,'ammo':30,'reserve':90,'reload':0.0,'input':control()} if bound or client and i>=4 else {}))
    return rows

def text(rows):
    return 'INDEPENDENT SYNTHETIC PURE CONTROL; NO NATIVE RUN\n' + '\n'.join(m.PREFIX+json.dumps(r) for r in rows)+'\n'

cases=[]
def run(name, client=None, authority=None, expected=False, raw_client=None, raw_authority=None):
    c = text(records('client') if client is None else client) if raw_client is None else raw_client
    s = text(records('authority') if authority is None else authority) if raw_authority is None else raw_authority
    result=m.analyze(c,s)
    case={'name':name,'expected_complete':expected,'actual_complete':result['diagnostic_complete'],'expectation_met':result['diagnostic_complete']==expected,'result':result}
    folder=a.output/name
    folder.mkdir()
    (folder/'client.log').write_text(c)
    (folder/'authority.log').write_text(s)
    (folder/'result.json').write_text(json.dumps(case,indent=2)+'\n')
    cases.append({k:v for k,v in case.items() if k!='result'})

run('coherent_independent_pipeline',expected=True)
for name,field,value in [('stale_receive','wall_msec',1),('receive_wrong_epoch','epoch',6),('receive_impossible_sequence','last',-9)]:
    rows=records('authority'); rows[3]['latest']['input_received'][field]=value
    run(name,authority=rows)
rows=records('authority'); rows[3]['latest'].pop('input_received')
run('receive_missing_metadata',authority=rows)
rows=records('authority'); rows[3].update(peer=72,generation=2,bound_actor=0,peer_bound=False,joined=False)
run('receive_unbound_different_peer',authority=rows)
rows=records('authority'); rows[4]['latest']['input_accepted'].update(first=22,last=20)
run('accepted_reversed_sequence_interval',authority=rows)
rows=records('authority'); rows[5]['latest']['input_consumed']['sequence']=22
run('consumption_outside_accepted_batch',authority=rows)
run('consumption_before_receive_accept',authority=records('authority',['ready','peer_connected','peer_bound','input_consumed','input_received','input_accepted','authority_tick']))
for name,field,value in [('client_send_different_transport','transport_id',72),('client_send_unwelcomed_attempt','local_attempt',2)]:
    rows=records('client'); rows[5][field]=value; rows[6][field]=value
    run(name,client=rows)
rows=records('client')
for row in rows[5:]:
    row['local_id']=5; row['actor']['id']=5
run('client_send_different_actor',client=rows)
rows=records('client'); rows[5]['prediction_epoch']=8; rows[5]['latest']['input_send_called']['epoch']=8
rows[6]['prediction_epoch']=8; rows[6]['latest']['input_send_called']['epoch']=8
run('client_send_epoch_disagrees_with_authority',client=rows)
rows=records('client'); rows[5]['latest']['input_send_called'].update(first=20,last=20)
run('send_outside_pending_interval',client=rows)
rows=records('authority'); rows[5]['reason']='authority_tick'; rows[5]['counters'].pop('input_consumed',None)
for row in rows[6:]: row['counters'].pop('input_consumed',None)
run('missing_consumption',authority=rows)
rows=records('authority'); rows[5]['latest']['input_consumed']['wall_msec']=1
run('stale_consumption',authority=rows)
rows=records('authority'); rows[5]['latest']['input_consumed']['generation']=2
run('consumption_wrong_generation',authority=rows)
rows=records('client'); rows[-1]['reason']='observation_limit'
run('explicit_cap_truncation',client=rows)
rows=records('client'); rows[5]['index']=7
run('index_gap',client=rows)
rows=records('client'); rows[-1]['account_id']='FICTIONAL_SENTINEL'
run('account_field',client=rows)
rows=records('client'); rows[-1]['actor']['position']=[3,4,5]
run('hidden_spatial_field',client=rows)
rows=records('client'); rows[-1]['physical']['r']='FICTIONAL_SENTINEL'
run('private_value_in_allowed_field',client=rows)
run('malformed_truncated_json',raw_client=text(records('client'))+m.PREFIX+'{')
run('empty_logs',raw_client='',raw_authority='')
# A full trace with a terminal event cannot be replaced by its initial pipeline prefix.
run('complete_pipeline_prefix_no_terminal_evidence')
# Original unmodified failed Windows input logs must remain insufficient.
original=Path('/workspace/reviews/windows-pulse-native-fresh-20261023/.local/native49/full/native-input')
run('original_failed_windows_untraced',raw_client=(original/'client.log').read_text(),raw_authority=(original/'server.log').read_text())

report={'scope':'Independent synthetic source-review falsifiers; no native run', 'source':subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip(), 'analyzer_sha256':hashlib.sha256((root/'scripts/analyze_input_consumption.py').read_bytes()).hexdigest(),'cpu_affinity':sorted(os.sched_getaffinity(0)), 'cases':cases, 'expectations_met':sum(c['expectation_met'] for c in cases),'cases_total':len(cases)}
(a.output/'results.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
