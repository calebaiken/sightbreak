#!/usr/bin/env python3
"""Independent source invariants fixed before R4 inspection; synthetic only."""
import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

p = argparse.ArgumentParser()
p.add_argument('--source', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
root = a.source.resolve()
sys.path.insert(0, str(root / 'scripts'))
from test_input_consumption_observation import declared_rows
spec = importlib.util.spec_from_file_location('independent_actual_reader', root / 'scripts/analyze_input_consumption.py')
reader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reader)
a.output.mkdir(parents=True, exist_ok=False)
cases = []


def serialize(rows):
    return 'INDEPENDENT SYNTHETIC SOURCE CONTROL; NO NATIVE OBSERVATIONS\n' + ''.join(reader.PREFIX + json.dumps(row, sort_keys=True) + '\n' for row in rows)


def append(rows, reason):
    row = deepcopy(rows[-1])
    index, now = len(rows) + 1, rows[-1]['wall_msec'] + 1000
    row.update(reason=reason, index=index, wall_msec=now, wall_unix_msec=100000 + now,
               process_frames=index, drawn_frames=index, physics_frames=index * 2)
    row['counters'][reason] = row['counters'].get(reason, 0) + 1
    if row['snapshot']:
        row['snapshot_age_msec'] = now - row['snapshot']['wall_msec']
    rows.append(row)
    return row


def second_accept(sequence):
    rows = declared_rows('authority')
    for reason in ('input_received', 'input_accepted'):
        row = append(rows, reason)
        row['latest'][reason].update(first=sequence, last=sequence, wall_msec=row['wall_msec'])
        if reason == 'input_accepted':
            row['queue_count'] = 1
    return rows


def malformed_then_valid(count=0, first=-1, last=-1):
    rows = declared_rows('authority')
    malformed = dict(epoch=1, count=count, first=first, last=last, fire=0, reload=0, moving=0,
                     wall_msec=rows[3]['wall_msec'])
    rows[3]['latest']['input_received'] = deepcopy(malformed)
    incoming = deepcopy(rows[3])
    incoming.update(wall_msec=8500, wall_unix_msec=108500)
    incoming['counters'].update(input_received=2, input_stream_rejected=1)
    incoming['stream_rejected'] = 1
    valid = deepcopy(rows[4]['latest']['input_accepted'])
    valid['wall_msec'] = 8500
    rejection = deepcopy(malformed)
    rejection['wall_msec'] += 1
    incoming['latest']['input_received'] = valid
    incoming['latest']['input_stream_rejected'] = rejection
    for row in rows[4:]:
        row['counters'].update(input_received=2, input_stream_rejected=1)
        row['stream_rejected'] = 1
        row['latest']['input_received'] = deepcopy(valid)
        row['latest']['input_stream_rejected'] = deepcopy(rejection)
    rows.insert(4, incoming)
    for index, row in enumerate(rows, 1):
        row.update(index=index, process_frames=index, drawn_frames=index, physics_frames=index * 2)
    return rows


def hidden_accept(old_timestamp=False):
    rows = declared_rows('authority')
    previous = rows[-1]['wall_msec']
    row = append(rows, 'authority_tick')
    for reason in ('input_received', 'input_accepted'):
        row['counters'][reason] += 1
        row['latest'][reason].update(first=2, last=2, wall_msec=1 if old_timestamp else previous + 1)
    row['queue_count'] = 1
    return rows


def run(name, authority, expected, basis, client=None, paired_control=None):
    client = declared_rows('client') if client is None else client
    client_text, authority_text = serialize(client), serialize(authority)
    # Independently validate the freshness equality before interpreting any result.
    for row in client + authority:
        if row['snapshot']:
            assert row['snapshot_age_msec'] == row['wall_msec'] - row['snapshot']['wall_msec'] >= 0
        else:
            assert row['snapshot_age_msec'] == -1
    result = reader.analyze(client_text, authority_text)
    directory = a.output / name
    directory.mkdir()
    (directory / 'client.txt').write_text(client_text)
    (directory / 'authority.txt').write_text(authority_text)
    receipt = dict(name=name, expected=expected, actual=result['diagnostic_complete'],
                   expectation_met=result['diagnostic_complete'] == expected,
                   source_basis=basis, paired_control=paired_control, result=result,
                   snapshot_freshness_independently_valid=True)
    (directory / 'RESULT.json').write_text(json.dumps(receipt, indent=2)+'\n')
    cases.append({k:v for k,v in receipt.items() if k != 'result'})


baseline = declared_rows('authority')
run('declared_source_corrected_control', baseline, True, 'The maintained corrected shared fixture is an explicit synthetic control, not native capture.')
run('fresh_single_command_above_ack', second_accept(2), True, 'InputStream14-47 permits sequence2 after ACK1; existing actor controls remain sequence1 until next pop.')
run('acknowledged_single_command_falsely_accepted', second_accept(1), False,
    'InputStream24-38: packet count1 sequence1 with ACK1 has no staged command and MUST reject.', paired_control='fresh_single_command_above_ack')
queue = deepcopy(baseline)
queue[4]['queue_count'] = 121
run('queue_exceeds_max_ahead', queue, False,
    'InputStream5,24-47: queue keys remain unique in (ACK,ACK+120]; pop deletes, forget/reset clears. Queue121 is impossible.', paired_control='declared_source_corrected_control')
rejected = deepcopy(baseline)
rejected[-1]['stream_rejected'] = 1
run('stream_rejected_without_rejection_call', rejected, False,
    'InputStream14-47 increments rejected once for each failed accept, followed synchronously by Match1068 rejection observation. No rejection counter or call exists here.', paired_control='declared_source_corrected_control')
run('empty_malformed_receive_then_valid', malformed_then_valid(), True,
    'Match1249-1264 projects an empty commands array as count0,endpoints-1/-1,actions0. RPC rejection does not print; changed valid receive does print before acceptance.')
missing_rejected = malformed_then_valid()
for row in missing_rejected:
    if row['counters'].get('input_stream_rejected', 0):
        row['stream_rejected'] = 0
run('rejection_counter_without_stream_rejected_state', missing_rejected, False,
    'InputStream rejection increments rejected before synchronous Match input_stream_rejected hook; a rejection counter1 cannot have stream_rejected0.', paired_control='empty_malformed_receive_then_valid')
run('nondictionary_malformed_receive_then_valid', malformed_then_valid(2), True,
    'Match1256 skips nondictionaries while count retains raw array size. Two nondictionary values project endpoints-1/-1 and zero actions.')
run('empty_packet_projects_nonempty_endpoint', malformed_then_valid(0, 21, 21), False,
    'Match1249-1264 initializes first/last=-1 and only changes them while visiting dictionary commands. Empty count0 cannot project sequence21.', paired_control='empty_malformed_receive_then_valid')
run('hidden_accept_timestamp_after_prior_row', hidden_accept(), True,
    'Match1295 coalesces same action aggregates while global counters and latest advance. Hidden receive/accept occur after preceding emitted row.')
run('hidden_accept_latest_timestamp_regresses', hidden_accept(True), False,
    'Time.get_ticks_msec sampled by Match1269 is monotonic; stage calls after prior emitted row cannot acquire timestamp1 after prior wall11000.', paired_control='hidden_accept_timestamp_after_prior_row')
current = declared_rows('client')
append(current, 'client_tick')
run('inserted_client_tick_freshness_control', baseline, True,
    'New client_tick advances all current timing, snapshot_age and its stage counter.', client=current)
current[-1]['counters']['client_tick'] -= 1
run('inserted_client_tick_counter_only_falsifier', baseline, False,
    'Only client_tick counter is changed relative to the paired current fresh event. No stale snapshot confound.', client=current,
    paired_control='inserted_client_tick_freshness_control')
report = dict(source=str(root), reader_sha256=hashlib.sha256((root/'scripts/analyze_input_consumption.py').read_bytes()).hexdigest(),
              cases=cases, total=len(cases), met=sum(x['expectation_met'] for x in cases),
              false_accepts=[x['name'] for x in cases if not x['expected'] and x['actual']],
              false_rejects=[x['name'] for x in cases if x['expected'] and not x['actual']])
(a.output/'SUMMARY.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k != 'cases'}, indent=2))
sys.exit(report['met'] != report['total'])
