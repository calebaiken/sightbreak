#!/usr/bin/env python3
"""Independent Git union, byte erasure, source binding and original-log audit."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

p=argparse.ArgumentParser(); p.add_argument('--source',type=Path,required=True); p.add_argument('--output',type=Path,required=True); a=p.parse_args()
assert sorted(os.sched_getaffinity(0))==[4]
assert not a.output.exists()
root=a.source.resolve(); base='49ae54b0e4f5d880bdf06e4eb783a616b2dff684'; candidate='c0738163965804297a1881905d5bb4646da40a16'
def git(*args): return subprocess.check_output(['git','-C',str(root),*args])
def tree(commit):
    out={}
    for record in git('ls-tree','-r','-z',commit).split(b'\0'):
        if not record: continue
        header,name=record.split(b'\t',1); mode,kind,blob=header.decode().split()
        out[name.decode()]={'mode':mode,'kind':kind,'blob':blob}
    return out
old,new=tree(base),tree(candidate)
modified={'game/scripts/gameplay/match.gd','game/tests/movement_prediction_test.gd','scripts/fixtures/export_integration.gd','scripts/validate.sh','scripts/verify_integration_export.py'}
added={'scripts/analyze_input_consumption.py','scripts/test_input_consumption_observation.py'}
changes=[]; non_doc=[]; erased=[]
for name in sorted(set(old)|set(new)):
    before,after=old.get(name),new.get(name)
    if before!=after: changes.append({'path':name,'before':before,'after':after})
    if name.startswith('docs/'): continue
    non_doc.append({'path':name,'before':before,'after':after})
    if before==after: continue
    if name in added:
        assert before is None and after['mode']=='100644'; continue
    assert name in modified and before['mode']==after['mode'] and before['kind']==after['kind']=='blob',name
    source=git('show',candidate+':'+name)
    inside=False; residual=[]; removed=[]
    for line in source.splitlines(keepends=True):
        if line.lstrip().startswith(b'# BEGIN INPUT OBSERVATION'):
            assert not inside; inside=True; removed.append(line)
        elif line.lstrip().startswith(b'# END INPUT OBSERVATION'):
            assert inside; inside=False; removed.append(line)
        elif inside or b'# INPUT_OBSERVATION_HOOK' in line:
            removed.append(line)
        else: residual.append(line)
    assert not inside
    original=git('show',base+':'+name)
    assert b''.join(residual)==original,name
    erased.append({'path':name,'original_sha256':hashlib.sha256(original).hexdigest(),'candidate_sha256':hashlib.sha256(source).hexdigest(),'removed_lines':len(removed),'byte_exact_residual':True})
assert set(e['path'] for e in erased)==modified
# Own preregistration and later evidence are documentation only.
head=tree('HEAD')
assert {p:v for p,v in head.items() if not p.startswith('docs/')}=={p:v for p,v in new.items() if not p.startswith('docs/')}
original_root=Path('/workspace/reviews/windows-pulse-native-fresh-20261023/.local/native49/full/native-input')
bindings=json.loads(git('show',candidate+':docs/reports/gauntlet/windows-input-consumption-diagnostic-20261023/original-bindings.json'))
originals=[]
for entry in bindings['files']:
    raw=(original_root/entry['path']).read_bytes(); observed=dict(path=entry['path'],bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
    assert observed==entry
    if entry['path'].endswith('.log'): observed['observation_records']=raw.count(b'SIGHTBREAK_INPUT_OBSERVATION ')
    originals.append(observed)
report=dict(base=base,candidate=candidate,checkout_head=git('rev-parse','HEAD').decode().strip(),cpu_affinity=[4],git_changed_paths=changes,non_doc_union_count=len(non_doc),unchanged_non_doc_count=sum(x['before']==x['after'] for x in non_doc),erased_existing=erased,new_non_doc_paths=sorted(added),all_non_doc_union=non_doc,original_files=originals,all_checks_passed=True)
a.output.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ('all_non_doc_union','git_changed_paths')},indent=2))
