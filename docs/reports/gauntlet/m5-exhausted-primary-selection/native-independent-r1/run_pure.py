#!/usr/bin/env python3
"""Record only read-only independent audits; no native operation is available."""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
HERE=Path(__file__).resolve().parent
RAW=Path('/workspace/sightbreak-exhausted-primary-selection/.local/exhausted-selection-candidate-r1')
commands=[('actual-audit','review_actual.py',[str(RAW/'bot_exhausted_primary.stdout.log')]),('provenance','audit_provenance.py',[]),('archive','audit_archive.py',[])]
receipts=[]
for label,script,args in commands:
    argv=[sys.executable,'-B',str(HERE/script),*args]
    started=time.monotonic();utc=datetime.now(timezone.utc).isoformat()
    result=subprocess.run(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=60)
    seconds=time.monotonic()-started
    for name,data in [('stdout.json',result.stdout),('stderr.log',result.stderr)]:
        (HERE/(label+'.'+name)).write_bytes(data)
    receipts.append(dict(argv=argv,start_utc=utc,wall_seconds=seconds,exit_code=result.returncode,source_sha256=hashlib.sha256((HERE/script).read_bytes()).hexdigest(),stdout_sha256=hashlib.sha256(result.stdout).hexdigest(),stderr_sha256=hashlib.sha256(result.stderr).hexdigest()))
(HERE/'pure-receipts.json').write_text(json.dumps(dict(commands=receipts,engine_invocations=0),indent=2)+'\n')
assert all(r['exit_code']==0 for r in receipts),receipts
print(json.dumps(receipts,indent=2))
