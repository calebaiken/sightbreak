#!/usr/bin/env python3
"""Independent source-only fixtures; never acquired native observations."""
import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess

p = argparse.ArgumentParser()
p.add_argument('--source', type=Path, required=True)
p.add_argument('--reader', type=Path)
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
assert sorted(os.sched_getaffinity(0)) == [4]
home = Path(__file__).resolve().parent
reader = a.reader or a.source/'scripts/analyze_input_consumption.py'
spec = importlib.util.spec_from_file_location('independent_reader', reader)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
a.output.mkdir(parents=True, exist_ok=False)
cases = []

def write_case(group, name, client, authority, expected, basis):
    result = m.analyze(client, authority)
    folder = a.output/group/name
    folder.mkdir(parents=True)
    (folder/'client.log').write_text(client)
    (folder/'authority.log').write_text(authority)
    receipt = dict(group=group, name=name, expected_complete=expected,
                   actual_complete=result['diagnostic_complete'],
                   expectation_met=expected == result['diagnostic_complete'],
                   source_basis=basis, result=result)
    (folder/'result.json').write_text(json.dumps(receipt, indent=2)+'\n')
    cases.append({k:v for k,v in receipt.items() if k != 'result'})

fixtures = home/'original-fixtures'
for case in json.loads((fixtures/'expectations.json').read_text()):
    folder = fixtures/case['group']/case['name']
    write_case(case['group'], case['name'], (folder/'client.log').read_text(),
               (folder/'authority.log').read_text(), case['expected_complete'],
               'Exact preserved fixture/expectation; see fixture-manifest.json.')

baseline = fixtures/'independent-25/coherent_independent_pipeline'
client = m.parse_log((baseline/'client.log').read_text())
authority = m.parse_log((baseline/'authority.log').read_text())
# Normalize the original schema fixture's simplified stream state for all new
# controls. The unchanged original38 above retain their exact original bytes.
for row in authority:
    if row['reason'] in ['peer_bound','input_received','input_accepted']:
        row['stream_ack'] = -1
    if row['reason'] == 'input_accepted': row['queue_count'] = 1
    if row['reason'] in ['input_consumed','authority_tick']:
        row['actor']['input'].update(sequence=21,fire=True)

def serialize(rows):
    return 'INDEPENDENT SOURCE-ONLY SYNTHETIC CONTROL; NO NATIVE RUN\n' + '\n'.join(m.PREFIX+json.dumps(row) for row in rows)+'\n'

def run(name, rows, expected, basis):
    write_case('new-controls', name, serialize(client), serialize(rows), expected, basis)

def append_event(rows, reason, **updates):
    row = deepcopy(rows[-1])
    now = row['wall_msec'] + 1000
    row.update(reason=reason, index=len(rows)+1, wall_msec=now,
               wall_unix_msec=100000+now,
               process_frames=len(rows)+1, physics_frames=len(rows)+1,
               drawn_frames=len(rows)+1)
    row['counters'][reason] = row['counters'].get(reason, 0)+1
    row.update(updates)
    if reason in row['latest']:
        row['latest'][reason]['wall_msec'] = now
    rows.append(row)
    return row

run('normalized_stream_control', deepcopy(authority), True,
    'Original schema baseline with pre-pop ACK-1, nonempty accepted queue, and actor input equal to the popped command; still synthetic, never native qualification.')

rows = deepcopy(authority)
row = append_event(rows, 'peer_connected', generation=2, joined=False)
row = append_event(rows, 'peer_bound', generation=2, joined=True,
                   bound_actor=5, last_bound_actor=5)
row['actor']['id'] = 5
run('same_peer_second_live_generation', rows, False,
    'peer_lifecycle.connected returns false while peers.has(peer); no disconnect/forget can be hidden because peer_disconnected always emits. A second live generation for peer71 cannot exist.')

rows = deepcopy(authority)
for row in rows[2:]: row['counters']['peer_bound'] = 2
run('binding_counter_claims_hidden_lifecycle_event', rows, False,
    'Every peer_bound increments its counter and always emits. Exactly one observed binding cannot have cumulative count2; no missing index or observation_limit exists.')

rows = deepcopy(authority)
append_event(rows, 'authority_tick')['counters']['authority_tick'] = 1
run('emitted_reason_counter_does_not_increment', rows, False,
    '_native_input_observe increments diagnostic.counters[reason] before every emitted row. The second directly observed authority_tick cannot retain count1.')

rows = deepcopy(authority)
rows[-1]['latest'].pop('input_accepted')
run('latest_accepted_deleted_without_reset', rows, False,
    'diagnostic.latest is initialized once and only updated by reason; an existing input_accepted key cannot disappear at authority_tick.')

rows = deepcopy(authority)
rows[4]['queue_count'] = 0
run('direct_accepted_has_empty_queue', rows, False,
    'input_stream.accept returns true only with nonempty staged commands, writes them to queues, then _input_rpc calls input_accepted synchronously before any pop.')

rows = deepcopy(authority)
rows[5]['stream_ack'] = 20
run('consumed_ack_disagrees_with_command', rows, False,
    'input_stream.pop sets acknowledged[peer] to returned command.sequence; authority immediately observes that consumed command before any next pop.')

rows = deepcopy(authority)
rows[5]['actor']['input']['sequence'] = 22
run('consumed_actor_projection_disagrees', rows, False,
    'authority_tick assigns actors[id].input_state = command, then observes input_consumed. The actor input sequence and consumed command sequence must agree.')

rows = deepcopy(authority)
row = append_event(rows, 'input_accepted')
row['latest']['input_accepted'].update(fire=0, first=22, last=22)
row['queue_count'] = 1
run('second_accept_without_receive_counter_increment', rows, False,
    'Each accept attempt calls input_received first and increments its counter even if coalesced. Two accepted calls cannot coexist with a cumulative receive count1. Fire1 to0 would also force a direct receive edge.')

rows = deepcopy(authority)
rows[4]['latest']['input_accepted']['fire'] = 0
run('accepted_latest_differs_from_synchronous_receive', rows, False,
    '_input_rpc passes the same data to input_received and input_accepted synchronously. A current accepted fire0 cannot retain received fire1 metadata from that invocation.')

rows = deepcopy(authority)
rows[3]['latest']['input_received']['last'] = -9
run('received_one_command_two_endpoints', rows, False,
    '_native_input_packet count1 visits one command: first/last both derive from its sequence, including invalid negative sequences; a nondict produces -1/-1. Prevalidation does not permit an impossible projection.')

rows = deepcopy(authority)
malformed = deepcopy(rows[3]['latest']['input_received'])
malformed.update(epoch=-1,first=-9,last=-9)
rows[3]['latest']['input_received'] = deepcopy(malformed)
for row in rows[4:]:
    row['counters']['input_received'] = 2
    row['counters']['input_stream_rejected'] = 1
    rejected = deepcopy(malformed)
    rejected['wall_msec'] = 8100
    row['latest']['input_stream_rejected'] = rejected
    row['latest']['input_received']['wall_msec'] = 8400
run('malformed_receive_then_coalesced_valid_receive', rows, True,
    'Invalid epoch/negative sequence is observable before validation; count1 still projects equal endpoints. Stream rejection increments without emitting; later valid receive can coalesce because epoch/sequence are excluded from its action edge. Counters/latest account for both receives and rejection before acceptance.')

for hidden_accept in [False, True]:
    rows = deepcopy(authority)
    for row in rows:
        for stage in ['input_received','input_accepted']:
            if stage in row['latest']:
                row['latest'][stage].update(first=1,last=1,moving=1)
        if 'input_consumed' in row['latest']:
            row['latest']['input_consumed'].update(sequence=1,move=[1.0,0.0])
        if row['reason'] in ['input_consumed','authority_tick']:
            row['stream_ack'] = 1
            row['actor']['input'].update(sequence=1,fire=True,move=[1.0,0.0])
    append_event(rows, 'peer_connected', peer=72,generation=2,bound_actor=0,
                 peer_bound=False,joined=False,stream_ack=-1,queue_count=0)
    row = append_event(rows, 'peer_bound', bound_actor=5,last_bound_actor=5,
                       peer_bound=True,joined=True)
    row['actor']['id'] = 5
    row['actor']['input'].update(sequence=-1,fire=False,move=[0.0,0.0])
    row = append_event(rows, 'input_consumed', stream_ack=1)
    row['latest']['input_consumed'].update(peer=72,generation=2,actor=5,
                                          sequence=1,fire=True,move=[-1.0,0.0])
    row['actor']['input'].update(sequence=1,fire=True,move=[-1.0,0.0])
    if hidden_accept:
        for stage in ['input_received','input_accepted']:
            row['counters'][stage] = 2
            row['latest'][stage]['wall_msec'] = row['wall_msec']-500
    run('second_peer_coalesced_acceptance' if hidden_accept else 'second_peer_pop_without_any_acceptance',
        rows, hidden_accept,
        'Per-reason receive/accepted edges omit peer identity and use moving count, while consumed edge includes full move. A +X then B -X can hide B receive/accept but emit B consumption. Both counters/latest must advance; when they remain1 after B binding there was no B acceptance to populate its empty queue.')

# Positive projection controls keep the R2 false-rejection class visible.
for first,last in [(2,1),(1,1)]:
    rows = deepcopy(authority)
    for row in rows:
        for stage in ['input_received','input_accepted']:
            if stage in row['latest']:
                row['latest'][stage].update(count=2,first=first,last=last,fire=2)
        if row['reason'] == 'input_accepted': row['queue_count'] = 2 if first != last else 1
        if row['reason'] in ['input_consumed','authority_tick']:
            row['stream_ack'] = 1
            row['queue_count'] = int(first != last)
            row['latest']['input_consumed']['sequence'] = 1
            row['actor']['input'].update(sequence=1,fire=True)
    run('valid_batch_endpoints_%s_%s'%(first,last), rows, True,
        'accept validates commands individually and stages a dictionary; valid incoming array endpoints may be reversed or duplicated. Pop returns sorted fresh sequence1.')

result = dict(scope='Independent pure source critique; no native or complete-acquisition claim',
              checkout_head=subprocess.check_output(['git','-C',str(a.source),'rev-parse','HEAD'],text=True).strip(),
              frozen_source='342c3641ab2fccd1fc875c84188a8395a9b93a96',
              reader_path=str(reader.resolve()), reader_sha256=hashlib.sha256(reader.read_bytes()).hexdigest(),
              cpu_affinity=sorted(os.sched_getaffinity(0)), cases=cases,
              cases_total=len(cases), expectations_met=sum(x['expectation_met'] for x in cases),
              false_accepts=[x['name'] for x in cases if not x['expected_complete'] and x['actual_complete']],
              false_rejects=[x['name'] for x in cases if x['expected_complete'] and not x['actual_complete']])
(a.output/'results.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='cases'},indent=2))
raise SystemExit(result['expectations_met'] != len(cases))
