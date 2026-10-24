#!/usr/bin/env python3
"""Independent runner for unchanged maintained pure/stub suites; no engine."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import time

parser = argparse.ArgumentParser()
parser.add_argument('--source', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
source = args.source.resolve()
output = args.output.resolve()
output.mkdir(parents=True, exist_ok=False)
scripts = ['transaction_restart_oracle', 'account_network_output', 'account_match_output',
           'build_manifest', 'native_log', 'native_observation', 'offline_role_guidance',
           'offline_export_ocr', 'offline_capture_fences', 'native_focus_fence',
           'focus_resume_timing', 'native_settings_route', 'native_route_pulse',
           'native_approach', 'macos_menu', 'reopened_shutdown_diagnostic']
commands = [('server', [sys.executable, '-m', 'unittest', 'discover', '-s', 'server/tests', '-v'])]
commands += [(name, [sys.executable, f'scripts/test_{name}.py', '-v']) for name in scripts]
commands += [('shell', ['bash', '-n', 'scripts/validate.sh'])]
rows = []
for name, command in commands:
    started = time.monotonic()
    result = subprocess.run(command, cwd=source, capture_output=True, timeout=60)
    (output / (name + '.stdout')).write_bytes(result.stdout)
    (output / (name + '.stderr')).write_bytes(result.stderr)
    text = (result.stdout + result.stderr).decode(errors='replace')
    counts = re.findall(r'Ran (\d+) tests? in', text)
    skipped = re.findall(r'skipped=(\d+)', text)
    rows.append(dict(name=name, command=command, exit=result.returncode,
                     methods=sum(map(int, counts)), skipped=sum(map(int, skipped)),
                     seconds=time.monotonic()-started,
                     stdout_sha256=hashlib.sha256(result.stdout).hexdigest(),
                     stderr_sha256=hashlib.sha256(result.stderr).hexdigest()))
summary = dict(source=str(source), interpreter=sys.executable, rows=rows,
               methods=sum(row['methods'] for row in rows),
               skipped=sum(row['skipped'] for row in rows),
               all_exit_zero=all(row['exit'] == 0 for row in rows))
(output / 'SUMMARY.json').write_text(json.dumps(summary, indent=2)+'\n')
print(json.dumps({key:value for key,value in summary.items() if key != 'rows'}))
sys.exit(not summary['all_exit_zero'])
