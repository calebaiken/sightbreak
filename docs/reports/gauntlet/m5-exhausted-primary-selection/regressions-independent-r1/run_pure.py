#!/usr/bin/env python3
"""Read-only independent actual regressions verification, with recoverable receipts."""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
HERE=Path(__file__).resolve().parent
commands=[('rows','audit_rows.py',[]),('controls','test_controls.py',[]),('provenance','audit_provenance.py',[]),('archive','audit_archive.py',['01c4bafa46444dc113f8dc1dbef5843286f9557f','docs/reports/gauntlet/m5-exhausted-primary-selection/native-root-r1/regressions'])]
receipts=[]
for label,script,args in commands:
    argv=[sys.executable,'-B',str(HERE/script),*args]
    start=time.monotonic();utc=datetime.now(timezone.utc).isoformat()
    result=subprocess.run(argv,capture_output=True,timeout=60)
    duration=time.monotonic()-start
    (HERE/(label+'.stdout.json')).write_bytes(result.stdout)
    (HERE/(label+'.stderr.log')).write_bytes(result.stderr)
    receipts.append(dict(argv=argv,start_utc=utc,wall_seconds=duration,exit_code=result.returncode,source_sha256=hashlib.sha256((HERE/script).read_bytes()).hexdigest(),stdout_sha256=hashlib.sha256(result.stdout).hexdigest(),stderr_sha256=hashlib.sha256(result.stderr).hexdigest()))
(HERE/'pure-receipts.json').write_text(json.dumps(dict(commands=receipts,engine_invocations=0),indent=2)+'\n')
assert all(r['exit_code']==0 for r in receipts),receipts
print(json.dumps(receipts,indent=2))
