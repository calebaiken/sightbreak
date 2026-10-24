#!/usr/bin/env python3
"""Independently seal exact observed originals; never deletes or runs native work."""
import argparse
import datetime
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import re
import tarfile

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('independent_output_rules',HERE/'audit_actual_outputs.py')
rules=importlib.util.module_from_spec(spec);spec.loader.exec_module(rules)

def sha(data):return hashlib.sha256(data).hexdigest()

def select(run,frozen):
    original={}
    for path in sorted(run.rglob('*')):
        if path.is_file():original['supervisor/'+path.relative_to(run).as_posix()]=(path,'all original supervisor/outer receipts')
    for name in ('aggregate-combined-r1-wrapper.stdout','aggregate-combined-r1-wrapper.stderr'):
        path=frozen/'.local'/name
        if not path.is_file():raise RuntimeError('Missing original redirected wrapper stream: '+str(path))
        original['outer-streams/'+name]=(path,'original redirected outer stream')
    for directory,kind in ((frozen/'.local/validation','all validation, per-suite userdata and lifecycle logs'),(frozen/'.local/aggregate-state-r1','all shared private userdata logs')):
        for path in sorted(directory.rglob('*.log')):
            original['private-logs/'+path.relative_to(frozen/'.local').as_posix()]=(path,kind)
    raw=(run/'aggregate.log').read_text()
    dirs=re.findall(r'^NETWORK_LOG_DIR=(.+)$',raw,re.M)
    if len(dirs)!=1:raise RuntimeError('Exact one original ENet directory required')
    for path in sorted(Path(dirs[0]).glob('*.log')):original['network-smoke/'+path.name]=(path,'all original ENet server/client/cleanup logs')
    return original

def main(args):
    run,frozen,out=args.run.resolve(),args.frozen.resolve(),args.output.resolve()
    if out.is_relative_to(run) or out.is_relative_to(frozen):raise RuntimeError('Archive must be outside original runtime checkout')
    out.mkdir(parents=True,exist_ok=False)
    selected=select(run,frozen);failures=[]
    terminal=json.loads((run/'log-audit.json').read_text())
    for row in terminal['files']:
        data=Path(row['path']).read_bytes()
        if len(data)!=row['bytes'] or sha(data)!=row['sha256']:failures.append('terminal-log-byte-drift: '+row['path'])
    manifest=[]
    with tarfile.open(out/'raw-logs.tar.gz','w:gz') as bundle:
        for name,(path,role) in sorted(selected.items()):
            if path.is_symlink():raise RuntimeError('Unexpected symlink original: '+str(path))
            data=path.read_bytes();info=tarfile.TarInfo(name);info.size=len(data);info.mode=path.stat().st_mode&0o777
            bundle.addfile(info,io.BytesIO(data))
            manifest.append(dict(path=name,original_path=str(path),bytes=len(data),sha256=sha(data),origin=role))
    wanted={row['path']:row for row in manifest};scans=[]
    with tarfile.open(out/'raw-logs.tar.gz','r:gz') as bundle:
        members=bundle.getmembers()
        if len(members)!=len(wanted) or {m.name for m in members}!=set(wanted):failures.append('archive member inventory mismatch')
        for member in members:
            data=bundle.extractfile(member).read();row=wanted[member.name]
            if len(data)!=row['bytes'] or sha(data)!=row['sha256'] or data!=Path(row['original_path']).read_bytes():failures.append('archive/current-origin mismatch: '+member.name)
            if member.name.endswith(('.log','.stdout','.stderr')):
                text=data.decode('utf-8');matches=[m.group(0) for m in rules.ERRORS.finditer(text)]
                scans.append(dict(path=member.name,bytes=len(data),sha256=sha(data),strict_clean=not matches,failures=matches,warnings=rules.WARNINGS.findall(text)))
                if matches:failures.append('strict original-output failure: '+member.name)
    if {name:str(value[0]) for name,value in selected.items()}!={name:str(value[0]) for name,value in select(run,frozen).items()}:failures.append('original selected file set changed during seal')
    (out/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (out/'archive-log-scan.json').write_text(json.dumps(scans,indent=2)+'\n')
    checksum=sha((out/'raw-logs.tar.gz').read_bytes());(out/'archive-sha256.txt').write_text(checksum+'  raw-logs.tar.gz\n')
    result=dict(verified=not failures,failures=failures,original_files=len(manifest),original_bytes=sum(row['bytes'] for row in manifest),archive_sha256=checksum,scanned_outputs=len(scans),strict_clean=all(row['strict_clean'] for row in scans),observed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),originals_deleted=False,scope='All supervisor/outer receipts and external redirected wrapper streams; all validation/shared and per-suite private userdata/lifecycle logs; all original ENet logs. Exact current origin comparison at this finite seal. Ordinary non-log state/cache and arbitrary future mutation are outside this claim.')
    (out/'archive-verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))
    return int(bool(failures))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',type=Path,required=True);parser.add_argument('--frozen',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    raise SystemExit(main(parser.parse_args()))
