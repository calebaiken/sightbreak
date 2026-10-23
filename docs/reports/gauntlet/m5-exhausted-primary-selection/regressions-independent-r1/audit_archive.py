#!/usr/bin/env python3
"""Bind committed preservation package to every retained original payload."""
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile
import sys

ROOT=Path('/workspace/sightbreak-v1-recovered')
SOURCE=Path('/workspace/sightbreak-exhausted-primary-selection')
RAW=SOURCE/'.local/exhausted-selection-regressions-r1'
COMMIT=sys.argv[1]
REPORT=sys.argv[2].rstrip('/')+'/'
HEAD='6276f0b799fde78811075af1fc37434ea4d0aec8'

def sha(data):return hashlib.sha256(data).hexdigest()
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)
def run():
    checks=0
    def check(v,m):
        nonlocal checks
        checks+=1
        assert v,m
    bound={}
    retention=json.loads((ROOT/(REPORT+'artifact-retention.json')).read_text())
    archive_name=retention['archive']
    check(Path(archive_name).name==archive_name,'plain archive filename')
    for name in (archive_name,'artifact-members.json','artifact-retention.json','outer-tool-receipt.json','wrapper.stdout','wrapper.stderr'):
        data=(ROOT/(REPORT+name)).read_bytes()
        check(data==git('show',COMMIT+':'+REPORT+name),'immutable committed package '+name)
        bound[name]=dict(bytes=len(data),sha256=sha(data))
    manifest=json.loads((ROOT/(REPORT+'artifact-members.json')).read_text())
    retention=json.loads((ROOT/(REPORT+'artifact-retention.json')).read_text())
    data=(ROOT/(REPORT+archive_name)).read_bytes()
    check(len(data)==retention['bytes'] and sha(data)==retention['sha256'],'exact archive digest/size')
    check(manifest['source']==HEAD and len(manifest['members'])==retention['payload_members'] and len(manifest['omitted_cache'])==retention['omitted_cache_files'],'full package registration')
    outer={
        'outer/wrapper.stdout':RAW.with_name(RAW.name+'-wrapper.stdout'),
        'outer/wrapper.stderr':RAW.with_name(RAW.name+'-wrapper.stderr'),
        'outer/claim.json':SOURCE/('.local/exhausted-selection-acquisition-claims/'+HEAD+'-regressions.json'),
        'outer/exec-tool.json':ROOT/(REPORT+'outer-tool-receipt.json')}
    originals={'raw/'+str(p.relative_to(RAW)):p for p in RAW.rglob('*') if p.is_file()}
    originals.update(outer)
    wanted={x['path'] for x in manifest['members']}
    omitted={x['path'] for x in manifest['omitted_cache']}
    check(len(wanted)==len(manifest['members']) and len(omitted)==len(manifest['omitted_cache']) and not(wanted&omitted) and wanted|omitted==originals.keys(),'every original in payload or declared cache-only omission')
    check(all(x.startswith('raw/staged/game/.godot/') for x in omitted),'omits only staged engine cache')
    with tarfile.open(fileobj=io.BytesIO(data),mode='r:gz') as archive:
        names=archive.getnames()
        check(len(names)==len(set(names))==retention['archive_members']==len(wanted)+1 and set(names)==wanted|{'payload-manifest.json'},'unique complete archive member inventory')
        check(archive.extractfile('payload-manifest.json').read()==(ROOT/(REPORT+'artifact-members.json')).read_bytes(),'embedded manifest exact external bytes')
        for row in manifest['members']:
            name=row['path'];member=archive.getmember(name)
            check(member.isfile() and not member.issym() and not member.islnk(),'regular archive member '+name)
            b=archive.extractfile(member).read();original=originals[name].read_bytes()
            check(b==original,'archive payload vs untouched original '+name)
            check((len(b),sha(b))==(row['bytes'],row['sha256']),'archive member digest '+name)
    for row in manifest['omitted_cache']:
        b=originals[row['path']].read_bytes()
        check((len(b),sha(b))==(row['bytes'],row['sha256']),'retained omitted cache hash '+row['path'])
    terminal=json.loads(outer['outer/wrapper.stdout'].read_text())
    receipt=json.loads(outer['outer/exec-tool.json'].read_text())
    check(receipt['terminal']['exit_code']==0 and receipt['launch']['session_id']==28150,'retained actual outer zero exit/session')
    check(terminal['passed'] is True and terminal['publication_confirmed'] is True and len(terminal['publication_readbacks'])==2,'terminal success after both publication readbacks')
    check(outer['outer/wrapper.stdout'].read_bytes()==(ROOT/(REPORT+'wrapper.stdout')).read_bytes() and outer['outer/wrapper.stderr'].read_bytes()==(ROOT/(REPORT+'wrapper.stderr')).read_bytes(),'root terminal copies byte exact')
    return dict(independent_archive_predicates=checks,package_commit=COMMIT,source_head=HEAD,payload_members=len(wanted),archive_members=len(names),retained_cache_omissions=len(omitted),bound_commit_objects=bound,outer_exit_code=receipt['terminal']['exit_code'],scope='All original noncache bytes and declared omitted-cache hashes verified; no complete PTY transcript beyond retained original tool response fields.')

if __name__=='__main__':print(json.dumps(run(),indent=2,sort_keys=True))
