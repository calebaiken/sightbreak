#!/usr/bin/env python3
"""Run eight existing pure groups, retaining native Windows skips accurately."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[5]
OUT = Path(__file__).parent
NAMES = ['native_settings_route', 'native_approach', 'native_focus_fence', 'focus_resume_timing',
         'offline_capture_fences', 'macos_menu', 'native_observation', 'offline_export_ocr']
checks = []
for name in NAMES:
    command = [sys.executable, 'scripts/test_' + name + '.py', '-v']
    start = time.monotonic()
    result = subprocess.run(command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    log = OUT / ('maintained-' + name + '.log')
    log.write_bytes(result.stdout)
    text = result.stdout.decode(errors='replace')
    ran = re.search(r'Ran (\d+) tests?', text)
    skipped = re.search(r'OK \(skipped=(\d+)\)', text)
    check = {'command': command, 'exit': result.returncode, 'seconds': time.monotonic() - start,
             'methods': int(ran[1]) if ran else None, 'skipped': int(skipped[1]) if skipped else 0,
             'log': log.name, 'sha256': hashlib.sha256(result.stdout).hexdigest()}
    checks.append(check)
    print(json.dumps(check), flush=True)
summary = {'target': 'af13a9979988d8b19de670fe27b78672ad2369ed', 'pure_only': True,
           'checks': checks, 'methods': sum(c['methods'] or 0 for c in checks),
           'skipped': sum(c['skipped'] for c in checks), 'passed': all(c['exit'] == 0 for c in checks)}
(OUT / 'maintained-results.json').write_text(json.dumps(summary, indent=2) + '\n')
raise SystemExit(not summary['passed'])
