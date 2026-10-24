#!/usr/bin/env python3
"""Run the declared source-only controls; invoke under taskset -c 4."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--root', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
root = args.root.resolve()
if os.sched_getaffinity(0) != {4}:
    raise SystemExit('This source-only replay must run on CPU 4')
names = ('macos_ax_untitled', 'macos_ax_read_only', 'macos_ax_controller', 'macos_ax_paths',
         'probe_macos_input', 'macos_menu', 'macos_focus', 'macos_screen_identity',
         'macos_ordinary', 'macos_ordinary_controller', 'macos_ordinary_paths',
         'macos_ordinary_startup', 'macos_deploy_ocr')
commands = [[sys.executable, 'scripts/test_' + name + '.py', '-v'] for name in names]
commands.append([sys.executable,
    'docs/reports/gauntlet/m2-mac-ax-read-only/r3/legacy-controls/replay_native_boundaries.py', str(root), '-v'])
with args.output.open('w') as log:
    def write(value):
        log.write(value + '\n')
        log.flush()
    for git_args in (['rev-parse', 'HEAD'], ['rev-parse', '--is-shallow-repository'],
                     ['rev-list', '--count', 'HEAD'], ['status', '--short']):
        result = subprocess.run(['git', *git_args], cwd=root, capture_output=True, text=True, check=True)
        write('GIT ' + ' '.join(git_args) + ': ' + result.stdout.strip())
    write('CPU affinity: ' + str(sorted(os.sched_getaffinity(0))))
    for path in ('scripts/probe_macos_ax.py', 'scripts/test_macos_ax_untitled.py'):
        write('SOURCE SHA256 ' + path + ': ' + hashlib.sha256((root / path).read_bytes()).hexdigest())
    failures = []
    for command in commands:
        write('\nCOMMAND: ' + ' '.join(command))
        result = subprocess.run(command, cwd=root, stdout=log, stderr=subprocess.STDOUT)
        write('EXIT: ' + str(result.returncode))
        if result.returncode:
            failures.append(command)
    status = subprocess.run(['git', 'status', '--short'], cwd=root, capture_output=True, text=True, check=True)
    write('\nFINAL GIT STATUS: ' + status.stdout.strip())
    write('FAILED COMMANDS: ' + json.dumps(failures))
print(json.dumps({'commands': len(commands), 'failed': len(failures), 'output': str(args.output)}))
raise SystemExit(bool(failures))
