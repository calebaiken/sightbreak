#!/usr/bin/env python3
"""Real adversarial ENet clients: post-auth silence, joined idle, ignored rejection."""
from pathlib import Path
import argparse
import subprocess
import time

from godot_process import (cleanup_processes, godot_command, godot_environment, prepare_output,
                           process_group_options, source_failures, source_snapshot)
from native_log import failed as native_log_failed

ROOT = Path(__file__).resolve().parents[1]

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    try:
        args.out = prepare_output(args.out)
    except FileExistsError as error:
        parser.error(str(error))
    source_before = source_snapshot(root=ROOT)
    if source_before['dirty']:
        parser.error('source must be clean and frozen before lifecycle test')
    processes, logs = [], []
    try:
        for index, scenario in enumerate(('silent', 'idle', 'reject')):
            port = 29900 + index
            command = ['--headless', '--max-fps', '60', '--script', 'res://tests/connection_lifecycle_probe.gd', '--', '--scenario=' + scenario, '--port=' + str(port)]
            for role in ('server', 'client'):
                path = args.out / f'{scenario}-{role}.log'
                log = path.open('x', encoding='utf-8'); logs.append(log)
                env = godot_environment(root=ROOT)
                process = subprocess.Popen(godot_command(command + ['--role=' + role], root=ROOT, env=env),
                                           stdout=log, stderr=subprocess.STDOUT, cwd=ROOT, env=env,
                                           **process_group_options())
                processes.append((path, process))
                if role == 'server':
                    for _ in range(100):
                        if 'SIGHTBREAK_SERVER_READY' in path.read_text(encoding='utf-8', errors='replace'): break
                        if process.poll() is not None: raise RuntimeError('server startup failed')
                        time.sleep(.05)
                    else: raise RuntimeError('server readiness timed out')
        failures = []
        for path, process in processes:
            code = process.wait(timeout=45)
            text = path.read_text(encoding='utf-8', errors='replace')
            if code or 'ERROR:' in text or 'SCRIPT ERROR' in text or native_log_failed(text) or '"ok":true' not in text:
                failures.append(path.name)
            print(path.name, text.strip().splitlines()[-1] if text.strip() else '(empty log)')
        if source_failures(source_before, source_snapshot(root=ROOT)):
            failures.append('source changed during lifecycle test')
        if failures: raise RuntimeError('Failed: ' + ', '.join(failures))
        print('CONNECTION_LIFECYCLE_TEST three native scenarios and server cleanup passed')
    finally:
        try:
            failures = cleanup_processes(processes)
            if failures:
                raise RuntimeError('; '.join(failures))
        finally:
            for log in logs: log.close()

if __name__ == '__main__': main()
