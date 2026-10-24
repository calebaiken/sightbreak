#!/usr/bin/env python3
"""Retain prior verdict history and replay versioned source-faithful controls."""
import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess

assert sorted(os.sched_getaffinity(0)) == [4]
p = argparse.ArgumentParser()
p.add_argument('--source', type=Path, required=True)
p.add_argument('--reader', type=Path)
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
home = a.source.resolve() / 'docs/reports/gauntlet/windows-input-consumption-r5-20261024'
reader = a.reader or a.source/'scripts/analyze_input_consumption.py'
spec = importlib.util.spec_from_file_location('actual_reader', reader)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
a.output.mkdir(parents=True, exist_ok=False)
cases = []
newly_obsolete = {('source-corrected-independent-25', 'receive_wrong_epoch'),
                  ('source-corrected-independent-25', 'receive_impossible_sequence'),
                  ('new-controls', 'malformed_receive_then_coalesced_valid_receive')}


def run(group, name, client, authority, expected, basis, prior=None):
    result = m.analyze(client, authority)
    directory = a.output/group/name
    directory.mkdir(parents=True)
    (directory/'client.log').write_text(client)
    (directory/'authority.log').write_text(authority)
    receipt = dict(group=group, name=name, expected_complete=expected,
                   actual_complete=result['diagnostic_complete'],
                   expectation_met=expected == result['diagnostic_complete'],
                   source_basis=basis, prior_expectation=prior, result=result)
    (directory/'result.json').write_text(json.dumps(receipt,indent=2)+'\n')
    cases.append({key:value for key,value in receipt.items() if key != 'result'})


old = home/'r4-builder-frozen/final-full-controls'
for case in json.loads((old/'results.json').read_text())['cases']:
    group, name = case['group'], case['name']
    directory = old/group/name
    client, authority = (directory/'client.log').read_text(), (directory/'authority.log').read_text()
    previous_required = False if case['obsolete_historical_positive'] else case['expected_complete']
    expected = False if (group,name) in newly_obsolete else previous_required
    basis = 'Exact prior R4 fixture preserved, with original receipt/outcome retained separately.'
    if (group,name) in newly_obsolete:
        basis += ' Final R4 critic adjudicates hidden rejection counter1 with stream state0 in the same live epoch as impossible; reject this newly obsolete positive.'
    run('historical-'+group, name, client, authority, expected, basis,
        dict(original_expected_complete=case['expected_complete'],
             r4_required_complete=previous_required, r4_actual_complete=case['actual_complete'],
             r5_newly_obsolete=(group,name) in newly_obsolete))
    if (group,name) in newly_obsolete:
        rows = m.parse_log(authority)
        for row in rows:
            if row['counters'].get('input_stream_rejected',0):
                row['stream_rejected'] = 1
        corrected = 'VERSIONED REJECTION STATE FIXTURE; NO NATIVE OBSERVATIONS\n'+'\n'.join(m.PREFIX+json.dumps(row) for row in rows)+'\n'
        run('state-corrected-'+group, name, client, corrected, True,
            'Only stream_rejected becomes1 once the hidden rejection counter is1; source increments stream state before Match1068-1070 observes rejection. Same live epoch excludes replacement. Exact prior bytes remain above.')

fresh = home/'r4-critic-frozen/own-fresh-controls-r2'
for directory in sorted(fresh.iterdir()):
    if not directory.is_dir():
        continue
    case = json.loads((directory/'RESULT.json').read_text())
    run('fresh-r4-critic', directory.name, (directory/'client.txt').read_text(),
        (directory/'authority.txt').read_text(), case['expected'], case['source_basis'])

report = dict(scope='Offline consistency only; old92 requirements explicitly adjudicated',
              source=subprocess.check_output(['git','-C',str(a.source),'rev-parse','HEAD'],text=True).strip(),
              reader_path=str(reader.resolve()), reader_sha256=hashlib.sha256(reader.read_bytes()).hexdigest(),
              cpu_affinity=[4], cases=cases, total=len(cases),
              met=sum(case['expectation_met'] for case in cases),
              newly_obsolete_prior_positive_count=len(newly_obsolete),
              passed=all(case['expectation_met'] for case in cases))
(a.output/'results.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({key:value for key,value in report.items() if key != 'cases'},indent=2))
raise SystemExit(not report['passed'])
