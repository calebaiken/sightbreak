#!/usr/bin/env python3
"""Run unchanged pure groups on CPU 4; never start an engine or native helper."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

parser = argparse.ArgumentParser()
parser.add_argument('--source', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
source, output = args.source.resolve(), args.output.resolve()
output.mkdir(parents=True, exist_ok=False)
if sorted(os.sched_getaffinity(0)) != [4]:
    raise RuntimeError('Pure checks require CPU 4 only')

def git(*words):
    return subprocess.check_output(['git', '-C', str(source), *words], text=True).strip()

report = {'source': git('rev-parse', 'HEAD'), 'cpu_affinity': sorted(os.sched_getaffinity(0)),
          'shallow': git('rev-parse', '--is-shallow-repository'),
          'commit_count': int(git('rev-list', '--count', 'HEAD')), 'groups': []}
commands = [('server', ['-m', 'unittest', 'discover', '-s', 'server/tests', '-v'])]
maintained = ['transaction_restart_oracle', 'account_network_output', 'account_match_output',
              'build_manifest', 'native_log', 'native_observation', 'offline_role_guidance',
              'offline_export_ocr', 'offline_capture_fences', 'native_focus_fence',
              'focus_resume_timing', 'native_settings_route', 'native_route_pulse', 'input_consumption_observation']
commands += [(name, ['scripts/test_' + name + '.py', '-v']) for name in maintained]
commands += [(name, ['scripts/test_' + name + '.py', '-v'])
             for name in ['native_approach', 'macos_menu', 'input_consumption_identity', 'input_consumption_lifecycle']]
for name, command in commands:
    start = time.monotonic()
    result = subprocess.run([sys.executable, *command], cwd=source, capture_output=True, timeout=60)
    raw = result.stdout + result.stderr
    path = output / (name + '.log')
    path.write_bytes(raw)
    found = re.search(rb'Ran (\d+) tests? in', raw)
    skips = re.search(rb'OK \(skipped=(\d+)\)', raw)
    report['groups'].append({'name': name, 'command': [sys.executable, *command],
                             'exit_code': result.returncode, 'elapsed_seconds': time.monotonic() - start,
                             'methods': int(found[1]) if found else None,
                             'skips': int(skips[1]) if skips else 0,
                             'log': path.name, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()})
syntax = subprocess.run(['bash', '-n', 'scripts/validate.sh'], cwd=source, capture_output=True)
report.update(shell_syntax_exit=syntax.returncode, total_methods=sum(r['methods'] or 0 for r in report['groups']),
              maintained_methods=sum(r['methods'] or 0 for r in report['groups'][:len(maintained) + 1]),
              skips=sum(r['skips'] for r in report['groups']),
              passed=syntax.returncode == 0 and all(r['exit_code'] == 0 and r['methods'] is not None for r in report['groups']))
(output / 'results.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
raise SystemExit(not report['passed'])
