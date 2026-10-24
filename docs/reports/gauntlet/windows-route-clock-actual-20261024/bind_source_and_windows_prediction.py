#!/usr/bin/env python3
"""Preregistered pure Git source/materialization and Windows-byte forward binding."""
import ast
import hashlib
import json
import os
from pathlib import Path, PureWindowsPath
import subprocess

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[3]
BASE='7101350e5d0a2f6e4afb9a913b5b1bcf2107857a'
OLD='c32415148db1f110bbc7eadfca3793d4693429ff'
CANDIDATE='4cf6ac8e744603ed6af122a362036d276754cc76'
HANDOFF='f093d8cb09441c5b9648f7a03446ccaa77db1205'


def git(*args):
    return subprocess.check_output(['git',*args],cwd=ROOT)


def tree(ref):
    found={}
    for row in git('ls-tree','-rz',ref).split(b'\0'):
        if row:
            meta,name=row.split(b'\t',1)
            if not name.startswith(b'docs/'):
                mode,kind,oid=meta.decode().split()
                assert kind=='blob'
                found[name.decode()]={'mode':mode,'kind':kind,'git_blob':oid}
    return found

assert os.sched_getaffinity(0)=={4}
old,base,new,handoff=tree(OLD),tree(BASE),tree(CANDIDATE),tree(HANDOFF)
assert len(old)==507 and len(base)==len(new)==508 and new==handoff
changed=[n for n in sorted(base.keys()|new.keys()) if base.get(n)!=new.get(n)]
assert changed==['scripts/test_native_route_pulse.py','scripts/verify_integration_export.py']
ledger={}
for name,identity in sorted(new.items()):
    blob=git('show',CANDIDATE+':'+name);path=ROOT/name
    assert path.is_file() and not path.is_symlink() and path.read_bytes()==blob,name
    assert bool(path.stat().st_mode&0o111)==(identity['mode']=='100755'),name
    ledger[name]={**identity,'bytes':len(blob),'sha256':hashlib.sha256(blob).hexdigest()}
game=git('rev-parse',CANDIDATE+':game').decode().strip()
assert game==git('rev-parse',OLD+':game').decode().strip()==git('rev-parse',BASE+':game').decode().strip()
producer=git('show',CANDIDATE+':scripts/build_manifest.py')
assert producer==git('show',BASE+':scripts/build_manifest.py')
function=next(n for n in ast.parse(producer).body if isinstance(n,ast.FunctionDef) and n.name=='source')
directories=('scripts','.github','game/tests')
assert any(isinstance(n,ast.Tuple) and [e.value for e in n.elts if isinstance(e,ast.Constant)]==list(directories) for n in ast.walk(function))
content=hashlib.sha256()
for name in sorted((n for n in ledger if n.startswith('game/') and 'tests' not in Path(n).parts),key=PureWindowsPath):
    content.update(name.removeprefix('game/').encode()+b'\0'+git('show',CANDIDATE+':'+name)+b'\0')
assert content.hexdigest()=='43a71ef7ea38febc735b67e24337c8f975bf69d57e3e4b06f94d175170d56eb8'
records=[]
for ref in (OLD,BASE,CANDIDATE):
    entries=tree(ref)
    selected=[n for n in entries if any(n.startswith(d+'/') for d in directories) and not any(q in ('__pycache__','.godot') for q in Path(n).parts) and Path(n).suffix!='.pyc']
    ordered=[n for d in directories for n in sorted((n for n in selected if n.startswith(d+'/')),key=PureWindowsPath)]
    digest=hashlib.sha256();LF=hashlib.sha256();files=[]
    for name in ordered:
        blob=git('show',ref+':'+name)
        data=git('--attr-source='+ref,'-c','core.autocrlf=true','-c','core.eol=crlf','-c','core.attributesFile=/dev/null','cat-file','--filters','--path='+name,ref+':'+name)
        digest.update(name.encode()+b'\0'+data+b'\0')
        LF.update(name.encode()+b'\0'+blob+b'\0')
        files.append({'path':name,'git_blob':entries[name]['git_blob'],'blob_bytes':len(blob),'Windows_bytes':len(data),'Windows_sha256':hashlib.sha256(data).hexdigest(),'converted':blob!=data})
    records.append({'source':ref,'path_count':len(ordered),'directory_order':list(directories),'counts':{d:sum(n.startswith(d+'/') for n in ordered) for d in directories},'path_sort':'PureWindowsPath: casefolded path components as producer Windows Path objects','path_order_sha256':hashlib.sha256(b''.join(n.encode()+b'\0' for n in ordered)).hexdigest(),'LF_validation_sha256':LF.hexdigest(),'Windows_validation_sha256':digest.hexdigest(),'files':files})
assert records[0]['Windows_validation_sha256']=='01ebd70c265e922f20d5ec794948fc7c456697d16f1e0472be846815131d556d'
assert records[1]['Windows_validation_sha256']=='225f4d95de52057b56c15b026a420f26b05d279636e60279819d32450c96d87e'
assert records[2]['Windows_validation_sha256']=='e0e223328351507a02d6b63b845531324c2e432e29e86eebed07740c45a2c496'
assert records[2]['path_order_sha256']=='7de141a49335a3e1c78d830e2c92bb8197cb8456195b13d6d43b13c67237e79f'
attributes=[n for n in ledger if Path(n).name=='.gitattributes']
report={'candidate':CANDIDATE,'builder_handoff':HANDOFF,'base':BASE,'old':OLD,'source_paths':len(ledger),'source_changed_paths_from710':changed,'unchanged_from710':506,'handoff_source_equal':True,'all_materialized_bytes_and_modes_equal':True,'game_tree':game,'production_content_sha256':content.hexdigest(),'paths':ledger,'workflows':{n:v for n,v in ledger.items() if n.startswith('.github/workflows/')},'attributes':{n:ledger[n] for n in attributes},'producer_source_sha256':hashlib.sha256(producer).hexdigest(),'producer_source':ast.get_source_segment(producer.decode(),function),'Windows_prediction_command':['git','--attr-source=<exact-ref>','-c','core.autocrlf=true','-c','core.eol=crlf','-c','core.attributesFile=/dev/null','cat-file','--filters','--path=<path>','<ref>:<path>'],'Git_version':git('--version').decode().strip(),'predictions':records,'no_future_output_inspected':True,'no_native_API_export_CI_or_cleanup':True}
(OUT/'SOURCE_AND_WINDOWS_PREDICTION.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'source_paths':len(ledger),'protected_paths':506,'candidate_Windows_validation':records[2]['Windows_validation_sha256'],'candidate_LF_validation':records[2]['LF_validation_sha256'],'path_order':records[2]['path_order_sha256'],'converted_paths':sum(x['converted'] for x in records[2]['files'])}))
