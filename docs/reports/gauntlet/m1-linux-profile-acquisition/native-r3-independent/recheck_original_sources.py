#!/usr/bin/env python3
"""Post-R3 finite R1/R2 source/mode preservation; no engine/native invocation."""
from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import time

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('independent_source_admission', HERE/'check_source_admission.py')
admission = importlib.util.module_from_spec(spec)
spec.loader.exec_module(admission)


def main():
    started = time.monotonic()
    admission.check('post-R3 original source audit CPU4', sorted(os.sched_getaffinity(0)) == [4])
    inventories = {}
    for label, root, sha in (('r1',admission.R1,admission.R1_SHA),('r2',admission.R2,admission.R2_SHA)):
        admission.check(label+' exact clean HEAD after R3', admission.git(root,'rev-parse','HEAD').decode().strip()==sha and not admission.git(root,'status','--porcelain','--untracked-files=all'))
        inventories[label] = admission.sources(root,sha)
        before=json.loads((root/('builds/linux-profile-acquisition-'+label)/'original-before.json').read_bytes())
        admission.check(label+' original source ledger after R3', inventories[label]==before)
    print(json.dumps({'passed':True,'scope':'Finite current original source/UID/Git-mode observation only; original failures and historical cache/process limits remain.','native_launches':0,'inventories':inventories,'checks':admission.checks,'started_monotonic':started,'ended_monotonic':time.monotonic(),'utc':datetime.now(timezone.utc).isoformat()},indent=2))


if __name__ == '__main__': main()
