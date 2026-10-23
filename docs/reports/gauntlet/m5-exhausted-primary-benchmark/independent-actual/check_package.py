#!/usr/bin/env python3
"""Bind immutable published evidence to the original uncompressed attempt."""
import gzip
import hashlib
import json
import subprocess
import sys
from pathlib import Path

COMMIT='700abf8c9d43279518c5257edfdbaee513569cea'
PREFIX='docs/reports/gauntlet/m5-exhausted-primary-benchmark/actual-r2/'

def audit(repo,raw):
    def blob(name):return subprocess.check_output(['git','show',COMMIT+':'+PREFIX+name],cwd=repo)
    def sha(data):return hashlib.sha256(data).hexdigest()
    inventory=json.loads(blob('artifacts.sha256.json'))['files']
    checks=0
    for entry in inventory:
        data=blob(entry['path'])
        assert len(data)==entry['bytes'] and sha(data)==entry['sha256'],entry['path']
        checks+=1
        original=raw/entry['path']
        if original.is_file():
            assert original.read_bytes()==data,entry['path']+' original mismatch'
            checks+=1
    archives=json.loads(blob('archive-map.json'))
    for entry in archives:
        data=blob(entry['archived']);original=gzip.decompress(data)
        assert sha(data)==entry['archived_sha256'],entry['archived']
        assert (len(original),sha(original))==(entry['original_bytes'],entry['original_sha256']),entry['original_name']
        assert original==(raw/entry['original_name']).read_bytes(),entry['original_name']+' original mismatch'
        checks+=3
    status=[]
    for pid,start in [(34219,971492),(34468,972148)]:
        path=Path('/proc')/str(pid)/'stat'
        text=path.read_text() if path.exists() else None
        current_start=int(text[text.rfind(')')+2:].split()[19]) if text else None
        assert current_start!=start,'original process still live'
        status.append(dict(pid=pid,original_start_ticks=start,current_start_ticks=current_start))
    return dict(package_commit=COMMIT,inventory_entries=len(inventory),compressed_originals=len(archives),package_checks=checks,original_process_reinspection=status)

if __name__=='__main__':print(json.dumps(audit(Path(sys.argv[1]),Path(sys.argv[2])),indent=2,sort_keys=True))
