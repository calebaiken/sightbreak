#!/usr/bin/env python3
"""Run only pure Mac source/controllers, with CPU 4 affinity; no native execution."""
import argparse
import os
from pathlib import Path
import subprocess
import sys
import time
import json

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source-root', type=Path, default=Path(__file__).resolve().parents[4])
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
root, output = args.source_root.resolve(), args.output.resolve()
if output.exists():
    raise SystemExit('Preserve pure output; select a fresh path')
os.sched_setaffinity(0, {4})
commands = [
    [sys.executable, '-m', 'unittest', 'discover', '-s', 'scripts', '-p', 'test_macos*.py', '-v'],
    [sys.executable, 'scripts/test_probe_macos_input.py', '-v'],
    [sys.executable, 'scripts/test_native_log.py', '-v'],
]
output.mkdir(parents=True)
rows = []
for index, command in enumerate(commands):
    started = time.monotonic()
    with (output/(str(index)+'.log')).open('w') as log:
        process = subprocess.run(command, cwd=root, stdout=log, stderr=subprocess.STDOUT, timeout=180)
    rows.append({'command': command, 'exit': process.returncode, 'seconds': time.monotonic()-started})
result = {'scope': 'Pure source/synthetic controls only; no native host, compilation, capture, OCR or gameplay',
          'cpu_affinity': sorted(os.sched_getaffinity(0)), 'commands': rows,
          'passed': all(row['exit'] == 0 for row in rows)}
(output/'results.json').write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps(result, indent=2))
raise SystemExit(0 if result['passed'] else 1)
