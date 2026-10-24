#!/usr/bin/env python3
"""Bind retained R4 bytes, unchanged assertions and exact source-view results."""
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import subprocess

assert sorted(os.sched_getaffinity(0)) == [4]
ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
BASE = '642dd0e0543698cae5d90b9046d5875beabed111'
BUILDER = 'd139124e8c663c3951eb6c7aaff99d49f2ce9712'
CRITIC = 'ad12f7ae08ca9cf1eaf05807ea41c44104544fdc'
p = argparse.ArgumentParser()
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
assert not a.output.exists()


def blob(commit, path):
    return subprocess.check_output(['git','-C',str(ROOT),'show',commit+':'+path])


def entry(path, raw):
    return dict(path=path, bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


retained = []
for name, commit, old_path in (
        ('r4-builder-frozen', BUILDER, 'docs/reports/gauntlet/windows-input-consumption-r4-20261024/'),
        ('r4-critic-frozen', CRITIC, 'docs/reports/gauntlet/windows-input-reader-r4-independent-source-20261024/')):
    for path in sorted((HERE/name).rglob('*')):
        if path.is_file():
            relative = path.relative_to(HERE/name).as_posix()
            raw = path.read_bytes()
            assert raw == blob(commit, old_path+relative), relative
            retained.append(dict(commit=commit, **entry(name+'/'+relative, raw)))

historical = []
for path in sorted((HERE/'historical-source').glob('*.py')):
    raw = path.read_bytes()
    assert raw == blob(BASE, 'scripts/'+path.name)
    historical.append(entry(path.name, raw))


def assertions(raw):
    result = {}
    for node in ast.walk(ast.parse(raw)):
        if isinstance(node, ast.FunctionDef) and node.name.startswith('test_'):
            result[node.name] = [ast.dump(call,include_attributes=False)
                for call in ast.walk(node) if isinstance(call,ast.Call)
                and isinstance(call.func,ast.Attribute)
                and isinstance(call.func.value,ast.Name)
                and call.func.value.id == 'self' and call.func.attr.startswith('assert')]
    return result


preserved = []
for group in ('observation','identity','lifecycle','state'):
    name = 'scripts/test_input_consumption_'+group+'.py'
    before, after = assertions(blob(BASE,name)), assertions((ROOT/name).read_bytes())
    assert before == after, name
    preserved.append(dict(path=name, methods=len(before), assertion_calls=sum(map(len,before.values())),
                          original_assertion_asts_unchanged=True))

full = json.loads((HERE/'final-full-controls/results.json').read_text())
depth = json.loads((HERE/'final-depth-controls/results.json').read_text())
assert full['cases'] == depth['cases']
for case in full['cases']:
    relative = Path(case['group'])/case['name']/'result.json'
    assert (HERE/'final-full-controls'/relative).read_bytes() == (HERE/'final-depth-controls'/relative).read_bytes()
raw_logs = []
for name, digest in (
        ('client.log','ec5fe22c681a9bd5ea0577773e9421d7f0eca6d2711b77c8c124f4cdefff4ba4'),
        ('server.log','61937ac0d1c75f29f790ffc339a4dabaa0a29eac65e9c5da5b4c526835ed0757')):
    path = ROOT/'docs/reports/gauntlet/windows-input-consumption-r2-20261023/original-native-log-bytes'/name
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == digest
    raw_logs.append(entry(str(path.relative_to(ROOT)),raw))
original = next(case for case in full['cases'] if case['group']=='historical-independent-25'
                and case['name']=='original_failed_windows_untraced')
assert original['actual_complete'] is False

report = dict(scope='Exact fixture/assertion provenance only; no native acceptance',
              base=BASE, builder_handoff=BUILDER, critic=CRITIC, cpu_affinity=[4],
              retained_files=retained, historical_source=historical,
              original_methods_and_assertions=preserved,
              original_native_log_bytes=raw_logs, original_untraced_logs_still_incomplete=True,
              full_depth_control_verdicts_and_result_bodies_identical=True, passed=True)
a.output.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({key:value for key,value in report.items() if key not in ('retained_files','historical_source')},indent=2))
