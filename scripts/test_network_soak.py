#!/usr/bin/env python3
"""Two to ten actual clients repeatedly reconnect to one server; bounded short soak."""
import argparse
import json
from pathlib import Path
import subprocess
import time

from godot_process import (cleanup_processes, godot_command, godot_environment, prepare_output,
                           process_group_options, source_failures, source_snapshot)
from native_log import failed as native_log_failed

ROOT = Path(__file__).resolve().parents[1]

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True); parser.add_argument('--port', type=int, default=29830)
    parser.add_argument('--clients', type=int, choices=range(2, 11), default=2)
    args = parser.parse_args()
    try:
        args.out = prepare_output(args.out)
    except FileExistsError as error:
        parser.error(str(error))
    source_before = source_snapshot(root=ROOT)
    if source_before['dirty']:
        parser.error('source must be clean and frozen before soak')
    processes = []; logs = []
    try:
        for name in ['server', *['client-' + str(i) for i in range(args.clients)]]:
            if name != 'server' and len(processes) == 1:
                for _ in range(200):
                    if 'SIGHTBREAK_SERVER_READY' in (args.out / 'server.log').read_text(encoding='utf-8', errors='replace'): break
                    if processes[0][1].poll() is not None: raise RuntimeError('server failed')
                    time.sleep(.05)
                else: raise RuntimeError('server readiness timed out')
            log = (args.out / (name + '.log')).open('x', encoding='utf-8'); logs.append(log)
            command = ['--headless', '--max-fps', '60', '--script', str(ROOT / 'scripts/fixtures/network_soak.gd'), '--', '--port=' + str(args.port), '--clients=' + str(args.clients), '--output=' + str(args.out / (name + '.json'))]
            if name == 'server': command.append('--server')
            env = godot_environment(root=ROOT)
            processes.append((name, subprocess.Popen(godot_command(command, root=ROOT, env=env), cwd=ROOT,
                                                     env=env, stdout=log, stderr=subprocess.STDOUT,
                                                     **process_group_options())))
        results = []
        for name, process in processes:
            code = process.wait(timeout=85)
            text = (args.out / (name + '.log')).read_text(encoding='utf-8', errors='replace')
            report = json.loads((args.out / (name + '.json')).read_text(encoding='utf-8'))
            assert code == 0 and 'ERROR:' not in text and not native_log_failed(text) and report['passed'], name + ' failed'
            results.append(report)
        source_after = source_snapshot(root=ROOT)
        assert not source_failures(source_before, source_after), 'source changed during soak'
        summary = {'source': source_before, 'source_before': source_before, 'source_after': source_after,
                   'source_unchanged': source_before == source_after, 'processes': results}
        with (args.out / 'summary.json').open('x', encoding='utf-8') as output:
            output.write(json.dumps(summary, indent=2) + '\n')
        print(json.dumps(summary, indent=2))
    finally:
        try:
            failures = cleanup_processes(processes)
            if failures:
                raise RuntimeError('; '.join(failures))
        finally:
            for log in logs: log.close()

if __name__ == '__main__': main()
