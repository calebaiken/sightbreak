#!/usr/bin/env python3
"""Read-only exact Git and fixture bindings for the reviewed source."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

parser=argparse.ArgumentParser()
parser.add_argument('--root',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args()
root=args.root.resolve()
assert os.sched_getaffinity(0)=={4}
base='4854aed946d25d27482af66c332f84aa51cea8fb'
candidate='d5277180a7705befd64d2f40a362ad566e83d91b'
actual='617b348b'
def git(*command):
    return subprocess.check_output(['git',*command],cwd=root)
def digest(data):
    return hashlib.sha256(data).hexdigest()
helper='scripts/macos_window_capture.swift'
original=git('show',base+':'+helper)
current=git('show',candidate+':'+helper)
assert current==(root/helper).read_bytes()
assert original==(root/'scripts/fixtures/macos_capture_diagnostics/original_helper.swift.txt').read_bytes()
raw=git('show',actual+':docs/reports/gauntlet/m2-mac-ax-read-only/r3/independent-actual/native-39943145541/qa/ax-read-only/00-startup-menu-1.json')
assert raw==(root/'scripts/fixtures/macos_capture_diagnostics/original-failure-39943145541.json').read_bytes()
changed=git('diff','--name-only',base,candidate,'--','scripts','.github','game').decode().splitlines()
assert changed==[
    'scripts/fixtures/macos_capture_diagnostics/original-failure-39943145541.json',
    'scripts/fixtures/macos_capture_diagnostics/original_helper.swift.txt',
    'scripts/macos_window_capture.swift',
    'scripts/test_macos_ax_read_only.py',
    'scripts/test_macos_capture_diagnostics.py',
    'scripts/test_macos_deploy_ocr.py']
for path in ['game','.github',
             'scripts/fixtures/macos_ax_read_only/preserved-source.json',
             'scripts/fixtures/macos_ordinary_source/reference.json']:
    assert git('rev-parse',base+':'+path)==git('rev-parse',candidate+':'+path)
report=Path(__file__).resolve().parent
logs={}
for name in ['maintained-pure.log','depth-one-maintained-pure.log']:
    text=(report/'receipts'/name).read_text()
    counts=[int(value) for value in re.findall(r'^Ran (\d+) tests? in ',text,re.M)]
    assert len(counts)==15 and sum(counts)==139
    assert 'FAILED COMMANDS: []' in text
    logs[name]={'commands':15,'methods':sum(counts),'method_counts':counts,'sha256':digest(text.encode())}
original_negative=(report/'receipts/original-depth-one-new-diagnostics-negative.log').read_text()
assert 'FAILED (failures=3)' in original_negative
assert original_negative.endswith('EXIT 1\n')
clones={}
for name,path in [('candidate','/workspace/reviews/m2-mac-capture-guard-fresh-source-depth-one'),
                  ('original','/workspace/reviews/m2-mac-capture-guard-original-depth-one')]:
    def read(*command):
        return subprocess.check_output(['git',*command],cwd=path,text=True).strip()
    clones[name]={'path':path,'head':read('rev-parse','HEAD'),
                  'shallow':read('rev-parse','--is-shallow-repository'),
                  'reachable_commits':int(read('rev-list','--count','HEAD')),
                  'status':read('status','--short'),
                  'objects':'borrowed via git clone --shared; isolated initialized index/worktree'}
    assert clones[name]['head']==(candidate if name=='candidate' else base)
    assert clones[name]['shallow']=='true' and clones[name]['reachable_commits']==1
    assert clones[name]['status']==''
result={'scope':'source and pure synthetic controls only','candidate':candidate,'base':base,
        'cpu_affinity':sorted(os.sched_getaffinity(0)),
        'helper_sha256':digest(current),'original_helper_sha256':digest(original),
        'original_failure':{'actual_report_commit':actual,'bytes':len(raw),'sha256':digest(raw),
                            'passed':json.loads(raw)['passed'],'post_capture_geometry':'not observed'},
        'changed_source_paths':changed,
        'unchanged_game_tree':git('rev-parse',candidate+':game').decode().strip(),
        'unchanged_workflow_tree':git('rev-parse',candidate+':.github').decode().strip(),
        'maintained':logs,'initialized_depth_one_checkouts':clones,
        'independent_methods':8,'original_source_negative_failures':3,
        'native_compilation_runtime_or_cause_accepted':False}
args.output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps({'bound':True,'maintained_methods':139,'independent_methods':8,'original_negative_failures':3}))
