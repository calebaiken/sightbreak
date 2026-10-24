#!/usr/bin/env python3
"""Replay exact history and explicit source-corrected fixtures; no native work."""
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
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
assert sorted(os.sched_getaffinity(0)) == [4]
home = Path(__file__).resolve().parent
frozen = home / 'r3-critic-frozen'
spec = importlib.util.spec_from_file_location('reader', a.source/'scripts/analyze_input_consumption.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
a.output.mkdir(parents=True, exist_ok=False)
cases = []
obsolete = {(x['group'], x['name']) for x in json.loads((frozen/'fixture-adjudication.json').read_text())['old_positive_cases'] if x['source_contradictions']}


def serialize(rows):
    return 'SOURCE-CORRECTED SYNTHETIC FIXTURE; NO NATIVE OBSERVATIONS\n' + '\n'.join(m.PREFIX+json.dumps(row) for row in rows)+'\n'


def run(group, name, client, authority, expected, changes=(), historical=False):
    result = m.analyze(client, authority)
    directory = a.output/group/name
    directory.mkdir(parents=True)
    (directory/'client.log').write_text(client)
    (directory/'authority.log').write_text(authority)
    receipt = dict(group=group, name=name, expected_complete=expected,
                   actual_complete=result['diagnostic_complete'],
                   expectation_met=expected == result['diagnostic_complete'],
                   obsolete_historical_positive=historical and (group, name) in obsolete,
                   fixture_changes=list(changes), result=result)
    if historical and (group, name) in obsolete:
        receipt['required_verdict_met'] = not result['diagnostic_complete']
    else:
        receipt['required_verdict_met'] = receipt['expectation_met']
    (directory/'result.json').write_text(json.dumps(receipt, indent=2)+'\n')
    cases.append({k: v for k, v in receipt.items() if k != 'result'})


originals = json.loads((frozen/'original-fixtures/expectations.json').read_text())
for case in originals:
    directory = frozen/'original-fixtures'/case['group']/case['name']
    client, authority = (directory/'client.log').read_text(), (directory/'authority.log').read_text()
    run(case['group'], case['name'], client, authority, case['expected_complete'], historical=True)

    # Version the intended original tests against real immediate stream state.
    # Keep every existing falsifier; do not repair malformed schema or JSON.
    changes = []
    try:
        rows = m.parse_log(authority)
    except (ValueError, TypeError, json.JSONDecodeError):
        rows = None
    if rows:
        last_consumed = None
        for row in rows:
            reason = row.get('reason')
            if reason in ('peer_bound', 'input_received', 'input_accepted'):
                row['stream_ack'] = -1
            if reason == 'input_accepted' and row['queue_count'] == 0:
                row['queue_count'] = 1
            if reason == 'input_consumed' and 'input_consumed' in row['latest']:
                value = row['latest']['input_consumed']
                row['stream_ack'] = value['sequence']
                last_consumed = {key: deepcopy(value[key]) for key in m.CONTROL_KEYS}
            if last_consumed and row.get('actor'):
                row['actor']['input'] = deepcopy(last_consumed)
        changes.append('Match1068-1078/InputStream35-47: first accepted queue nonempty, pre-pop ACK absent; Match279-281/InputStream83: popped ACK and actor controls, retained on later rows. Existing identity/header/privacy/truncation mutations remain.')

        if case['name'] in ('receive_wrong_epoch', 'receive_impossible_sequence'):
            received = next(row for row in rows if row['reason'] == 'input_received')
            malformed = deepcopy(received['latest']['input_received'])
            if case['name'] == 'receive_impossible_sequence':
                malformed.update(first=-9, last=-9)
                received['latest']['input_received'] = deepcopy(malformed)
                changes.append('Match1249-1264: count1 malformed sequence projects equal negative endpoints; old unequal projection remains historical.')
            accepted = next(row for row in rows if row['reason'] == 'input_accepted')
            valid = deepcopy(accepted['latest']['input_accepted'])
            valid['wall_msec'] -= 1
            rejected = deepcopy(malformed)
            rejected['wall_msec'] += 1
            for row in rows:
                if row['index'] >= accepted['index']:
                    row['counters'].update(input_received=2, input_stream_rejected=1)
                    row['latest']['input_received'] = deepcopy(valid)
                    row['latest']['input_stream_rejected'] = deepcopy(rejected)
            changes.append('Match1066-1078/1295-1300: malformed receive rejects without printing, then same-action valid receive coalesces before valid acceptance; counters/latest explicitly include both calls.')

        if case['name'] == 'consumption_outside_accepted_batch':
            consumed = next(row for row in rows if row['reason'] == 'input_consumed')
            sequence = consumed['latest']['input_consumed']['sequence']
            packet = deepcopy(consumed['latest']['input_accepted'])
            packet.update(first=sequence, last=sequence, wall_msec=consumed['wall_msec']-1)
            for row in rows:
                if row['index'] >= consumed['index']:
                    row['counters'].update(input_received=2, input_accepted=2)
                    row['latest']['input_received'] = deepcopy(packet)
                    row['latest']['input_accepted'] = deepcopy(packet)
                    row['latest']['input_consumed'] = deepcopy(consumed['latest']['input_consumed'])
            changes.append('Match1295-1300: later same-action receive/accept may coalesce; counters/latest expose its new command while the earlier direct accepted event remains unchanged. No packet correlation inferred.')
        authority = serialize(rows)
    run('source-corrected-'+case['group'], case['name'], client, authority,
        case['expected_complete'], changes)

final = frozen/'full-r3-controls-r3/new-controls'
for directory in sorted(final.iterdir()):
    receipt = json.loads((directory/'result.json').read_text())
    run('new-controls', directory.name, (directory/'client.log').read_text(),
        (directory/'authority.log').read_text(), receipt['expected_complete'],
        [receipt['source_basis']])

report = dict(scope='Offline source consistency only; historical contradictions explicitly retained',
              checkout_head=subprocess.check_output(['git','-C',str(a.source),'rev-parse','HEAD'], text=True).strip(),
              reader_sha256=hashlib.sha256((a.source/'scripts/analyze_input_consumption.py').read_bytes()).hexdigest(),
              cpu_affinity=[4], cases=cases, cases_total=len(cases),
              required_verdicts_met=sum(x['required_verdict_met'] for x in cases),
              obsolete_historical_positives=sum(x['obsolete_historical_positive'] for x in cases),
              passed=all(x['required_verdict_met'] for x in cases))
(a.output/'results.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps({key: value for key, value in report.items() if key != 'cases'}, indent=2))
raise SystemExit(not report['passed'])
