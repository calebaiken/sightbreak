#!/usr/bin/env python3
"""Full tracked non-doc tree identity, including sparse omissions and modes."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

p=argparse.ArgumentParser()
p.add_argument('--source',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
a=p.parse_args()
assert sorted(os.sched_getaffinity(0))==[4]
a.output.parent.mkdir(parents=True,exist_ok=True)
assert not a.output.exists()
frozen='342c3641ab2fccd1fc875c84188a8395a9b93a96'
base='86fe3cbe3f191b328c1e08bf8d5adc0a937e39b1'
def git(*args): return subprocess.check_output(['git','-C',str(a.source),*args])
def tree(ref):
    rows={}
    for raw in git('ls-tree','-rz','-r',ref).split(b'\0'):
        if not raw: continue
        head,path=raw.split(b'\t',1)
        path=path.decode(); mode,kind,oid=head.decode().split()
        if path.startswith('docs/'): continue
        rows[path]=dict(path=path,mode=mode,kind=kind,git_object=oid)
    return rows
candidate=tree(frozen); old=tree(base); checkout=tree('HEAD')
union=sorted(set(candidate)|set(old))
entries=[]
for path in union:
    entry=dict(path=path,rejected_r2=old.get(path),frozen_r3=candidate.get(path))
    local=a.source/path
    if path in candidate and local.is_file():
        raw=local.read_bytes()
        oid=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
        mode='100755' if local.stat().st_mode&0o111 else '100644'
        entry.update(present=True,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),
                     checkout_git_object=oid,checkout_mode=mode,
                     content_and_mode_match=(oid==candidate[path]['git_object'] and mode==candidate[path]['mode']))
    else:
        entry.update(present=False,reason='Sparse omission; exact full tree Git object and mode retained above.')
    entries.append(entry)
objects=sorted({row['git_object'] for row in list(candidate.values())+list(old.values())})
proc=subprocess.run(['git','-C',str(a.source),'cat-file','--batch-check'],input=('\n'.join(objects)+'\n').encode(),capture_output=True,check=True)
missing=[line.decode() for line in proc.stdout.splitlines() if line.endswith(b' missing')]
result=dict(frozen_source=frozen,rejected_r2=base,checkout_head=git('rev-parse','HEAD').decode().strip(),
            cpu_affinity=[4],non_document_definition='Every tracked path except docs/; includes dotfiles, instructions, workflows, server, game and scripts.',
            full_non_document_union_count=len(union),frozen_count=len(candidate),r2_count=len(old),
            present_count=sum(row['present'] for row in entries),sparse_omission_count=sum(not row['present'] for row in entries),
            changed_non_document_paths=[path for path in union if old.get(path)!=candidate.get(path)],
            checkout_head_non_document_tree_matches_frozen=(checkout==candidate),
            available_unique_git_objects=len(objects),missing_git_objects=missing,
            source_checkout_matches=all(row.get('content_and_mode_match',True) for row in entries),
            source_status=git('status','--porcelain','--untracked-files=no').decode(),
            entries=entries)
a.output.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='entries'},indent=2))
raise SystemExit(bool(missing) or not result['source_checkout_matches'] or not result['checkout_head_non_document_tree_matches_frozen'])
