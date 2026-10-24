#!/usr/bin/env python3
"""Reconstruct validation bytes with Git filters; no checkout/native mutation."""
import hashlib
import json
from pathlib import Path
import subprocess

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[3]
BASE='c32415148db1f110bbc7eadfca3793d4693429ff'
CANDIDATE='7101350e5d0a2f6e4afb9a913b5b1bcf2107857a'

def git(*args):
    return subprocess.check_output(['git',*args],cwd=ROOT)

for name in ('.gitattributes','scripts/fixtures/native_log/.gitattributes'):
    assert git('show',BASE+':'+name)==git('show',CANDIDATE+':'+name)==(ROOT/name).read_bytes()
records=[]
for ref in (BASE,CANDIDATE):
    names=[]
    for row in git('ls-tree','-rz',ref).split(b'\0'):
        if row:
            _,name=row.split(b'\t',1)
            value=name.decode()
            if any(value.startswith(d+'/') for d in ('scripts','.github','game/tests')):
                names.append(value)
    digest=hashlib.sha256();differences=[]
    for directory in ('scripts','.github','game/tests'):
        for name in sorted(x for x in names if x.startswith(directory+'/')):
            blob=git('show',ref+':'+name)
            filtered=git('-c','core.autocrlf=true','cat-file','--filters','--path='+name,ref+':'+name)
            digest.update(name.encode()+b'\0'+filtered+b'\0')
            if filtered!=blob:
                differences.append({'path':name,'blob_bytes':len(blob),'Windows_checkout_bytes':len(filtered)})
    records.append({'source':ref,'validation_paths':len(names),'Windows_filtered_digest':digest.hexdigest(),'filtered_differences':differences})
assert records[0]['Windows_filtered_digest']=='01ebd70c265e922f20d5ec794948fc7c456697d16f1e0472be846815131d556d'
assert records[1]['Windows_filtered_digest']=='225f4d95de52057b56c15b026a420f26b05d279636e60279819d32450c96d87e'
report={'scope':'Pure Git smudge reconstruction using pinned source and unchanged attributes; no native process or checkout mutation',
        'command':['git','-c','core.autocrlf=true','cat-file','--filters','--path=<path>','<source>:<path>'],'sources':records}
(OUT/'WINDOWS_CHECKOUT_VALIDATION_HASHES.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'baseline':records[0]['Windows_filtered_digest'],'candidate':records[1]['Windows_filtered_digest'],'converted_paths':len(records[1]['filtered_differences'])}))
