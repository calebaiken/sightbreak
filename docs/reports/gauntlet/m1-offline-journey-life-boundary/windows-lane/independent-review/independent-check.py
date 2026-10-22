#!/usr/bin/env python3
"""Review exact Windows lane YAML. Node checks JS-compatible logical operators only."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import yaml

root = Path(sys.argv[1]).resolve()
workflow = '.github/workflows/desktop-alpha.yml'
refs = ['7d46d2e', '47b142d']
texts = [subprocess.check_output(['git', 'show', ref + ':' + workflow], cwd=root, text=True) for ref in refs]
before, after = [yaml.load(text, Loader=yaml.BaseLoader) for text in texts]
old_input = before['on']['workflow_dispatch']['inputs']['lane']
new_input = after['on']['workflow_dispatch']['inputs']['lane']
assert old_input['options'] == ['all', 'arm-macos-ios']
assert new_input == dict(old_input, options=['all', 'arm-macos-ios', 'windows'])
expressions = [item['jobs']['native']['strategy']['matrix']['include'] for item in [before, after]]
for expression in expressions:
    assert expression.startswith('${{ fromJSON(') and expression.endswith(') }}')
stripped = copy.deepcopy(after)
stripped['on']['workflow_dispatch']['inputs']['lane'] = copy.deepcopy(old_input)
stripped['jobs']['native']['strategy']['matrix']['include'] = expressions[0]
assert stripped == before, 'Unrelated workflow change'
scenarios = []
for event in ['workflow_dispatch', 'push', 'workflow_call']:
    for lane in [None, '', 'all', 'arm-macos-ios', 'windows', 'unknown']:
        scenarios.append({'event': event, 'inputs': {} if lane is None else {'lane': lane}})
# Evaluate the exact scalar's standard logical operations with a separate runtime.
# This does not invoke GitHub's expression evaluator or its remote dispatch API.
node = r'''
const fs = require('fs');
const data = JSON.parse(fs.readFileSync(0, 'utf8'));
const evaluators = data.expressions.map(expression => new Function('github', 'inputs', 'fromJSON',
    'return (' + expression.slice(3, -3).trim() + ');'));
const rows = data.scenarios.map(scenario => ({...scenario,
    results: evaluators.map(evaluate => evaluate({event_name: scenario.event}, scenario.inputs, JSON.parse))}));
process.stdout.write(JSON.stringify(rows));
'''
rows = json.loads(subprocess.check_output(['node', '-e', node], input=json.dumps({'expressions': expressions, 'scenarios': scenarios}), text=True))
all_hosts = [{'os':'ubuntu-24.04','target':'linux'}, {'os':'windows-latest','target':'windows'},
             {'os':'macos-15','target':'macos'}, {'os':'macos-15-intel','target':'macos'}]
for row in rows:
    old, new = row['results']
    event, lane = row['event'], row['inputs'].get('lane')
    if event == 'workflow_dispatch' and lane == 'windows':
        assert old == all_hosts
        assert new == [{'os':'windows-latest','target':'windows'}]
    else:
        assert old == new
        assert new == ([{'os':'macos-15','target':'macos'}] if event == 'workflow_dispatch' and lane == 'arm-macos-ios' else all_hosts)
    row['pass'] = True
steps = after['jobs']['native']['steps']
result = {'candidate_commit':subprocess.check_output(['git','rev-parse',refs[1]],cwd=root,text=True).strip(),
          'comparison_commit':subprocess.check_output(['git','rev-parse',refs[0]],cwd=root,text=True).strip(),
          'workflow_sha256':{ref:hashlib.sha256(text.encode()).hexdigest() for ref,text in zip(refs,texts)},
          'all_unrelated_yaml_fields_identical':True,
          'unchanged_step_count':len(steps), 'case_count':len(rows), 'cases':rows,
          'scope':'Static YAML and Node logical-operator replay. No GitHub engine, dispatch or native Windows run.'}
print(json.dumps(result,indent=2))
