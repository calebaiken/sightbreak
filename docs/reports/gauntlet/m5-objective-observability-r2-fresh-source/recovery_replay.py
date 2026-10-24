#!/usr/bin/env python3
"""Replay unchanged registered falsifiers, retaining exact compressed receipts."""
import gzip
import hashlib
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import time

root = Path(sys.argv[1]).resolve()
out = Path(sys.argv[2]).resolve()
assert sorted(os.sched_getaffinity(0)) == [4], 'CPU 4 only'
out.mkdir(parents=True, exist_ok=False)
sys.path.insert(0, str(root / 'scripts'))
import verify_bot_objective_observation as reader
verify = reader.verify
inputs = []

def retain(raw, supplied_root):
    index = len(inputs)
    encoded = raw.encode()
    path = out / f'input-{index:02d}.log.gz'
    path.write_bytes(gzip.compress(encoded, mtime=0))
    entry = {'index': index, 'path': path.name, 'bytes': len(encoded),
             'sha256': hashlib.sha256(encoded).hexdigest(),
             'gzip_sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
    inputs.append(entry)
    try:
        result = verify(raw, supplied_root)
    except Exception as exc:
        entry.update(accepted=False, error=f'{type(exc).__name__}: {exc}')
        raise
    else:
        entry.update(accepted=True, result=result)
        return result

reader.verify = retain
script = Path(__file__).resolve().with_name('fresh_controls.py')
started = time.monotonic()
sys.argv = [str(script), str(root)]
exit_code = None
try:
    runpy.run_path(str(script), run_name='__main__')
except SystemExit as exc:
    exit_code = exc.code
finally:
    report = {'source': 'dce89495d04c9d3fefece0f8c7929e2e01b8e7df',
              'root': str(root), 'head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip(),
              'script_sha256': hashlib.sha256(script.read_bytes()).hexdigest(),
              'cpu_affinity': sorted(os.sched_getaffinity(0)), 'exit_code': exit_code,
              'wall_seconds': time.monotonic()-started, 'native_executed': False,
              'inputs': inputs}
    (out/'inputs.json').write_text(json.dumps(report, indent=2)+'\n')
sys.exit(exit_code)
