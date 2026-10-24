#!/usr/bin/env python3
"""Bind unchanged historic fixtures/assertions and actual original log bytes."""
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
BASE = '342c3641ab2fccd1fc875c84188a8395a9b93a96'
CRITIC = 'f8049be40286fff4ce8fe09159dbcf2db6874caf'
CRITIC_REPORT = 'docs/reports/gauntlet/windows-input-consumption-r3-fresh-source-20261024/'
p = argparse.ArgumentParser()
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
assert not a.output.exists()


def git_blob(commit, path):
    return subprocess.check_output(['git', '-C', str(ROOT), 'show', commit+':'+path])


def receipt(path, raw):
    return dict(path=path, bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


frozen = HERE/'r3-critic-frozen'
bound = []
for target in sorted(frozen.rglob('*')):
    if target.is_file():
        relative = target.relative_to(frozen).as_posix()
        raw = target.read_bytes()
        assert raw == git_blob(CRITIC, CRITIC_REPORT+relative), relative
        bound.append(receipt(relative, raw))
for item in json.loads((frozen/'fixture-manifest.json').read_text()):
    raw = (frozen/item['path']).read_bytes()
    assert len(raw) == item['bytes'] and hashlib.sha256(raw).hexdigest() == item['sha256']

historical = []
assertions = []
for target in sorted((HERE/'historical-source').glob('*.py')):
    raw = target.read_bytes()
    assert raw == git_blob(BASE, 'scripts/'+target.name), target.name
    historical.append(receipt(target.name, raw))
    if target.name.startswith('test_'):
        def tests(data):
            result = {}
            for node in ast.walk(ast.parse(data)):
                if isinstance(node, ast.FunctionDef) and node.name.startswith('test_'):
                    result[node.name] = [ast.dump(value, include_attributes=False)
                        for value in ast.walk(node) if isinstance(value, ast.Call)
                        and isinstance(value.func, ast.Attribute)
                        and isinstance(value.func.value, ast.Name)
                        and value.func.value.id == 'self' and value.func.attr.startswith('assert')]
            return result
        before, after = tests(raw), tests((ROOT/'scripts'/target.name).read_bytes())
        assert before == after, target.name
        assertions.append(dict(path=target.name, methods=len(before), assertion_calls=sum(map(len,before.values())), all_original_assertion_asts_unchanged=True))

originals = []
expected = {'client.log': 'ec5fe22c681a9bd5ea0577773e9421d7f0eca6d2711b77c8c124f4cdefff4ba4',
            'server.log': '61937ac0d1c75f29f790ffc339a4dabaa0a29eac65e9c5da5b4c526835ed0757'}
for name, digest in expected.items():
    path = ROOT/'docs/reports/gauntlet/windows-input-consumption-r2-20261023/original-native-log-bytes'/name
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == digest
    derived = frozen/'original-fixtures/independent-25/original_failed_windows_untraced'/('authority.log' if name == 'server.log' else name)
    assert derived.read_bytes() == raw.decode().replace('\r\n','\n').replace('\r','\n').encode()
    originals.append({**receipt(str(path.relative_to(ROOT)),raw), 'unchanged_critic_derivation': str(derived.relative_to(HERE)), 'normalization': 'Historical rig read_text/write_text newline normalization; raw original bytes retained separately'})

full = json.loads((HERE/'final-full-controls/results.json').read_text())
depth = json.loads((HERE/'final-depth-controls/results.json').read_text())
assert full['cases'] == depth['cases']
report = dict(scope='Historic/source fixture identity only; no native acceptance',
              base=BASE, critic_commit=CRITIC, cpu_affinity=[4],
              frozen_critic_files=bound, historical_source=historical,
              original_assertions=assertions, original_native_log_bytes=originals,
              full_depth_control_verdicts_identical=True, passed=True)
a.output.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({key:value for key,value in report.items() if key not in ('frozen_critic_files','historical_source')},indent=2))
