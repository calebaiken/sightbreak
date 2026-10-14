#!/usr/bin/env python3
"""Two to ten actual clients repeatedly reconnect to one server; bounded short soak."""
import argparse
import json
from pathlib import Path
import subprocess
import time
ROOT = Path(__file__).resolve().parents[1]

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True); parser.add_argument('--port', type=int, default=29830)
    parser.add_argument('--clients', type=int, choices=range(2, 11), default=2)
    args = parser.parse_args(); args.out = args.out.resolve(); args.out.mkdir(parents=True, exist_ok=True)
    if any(args.out.glob('*.json')):
        parser.error('refusing to overwrite earlier soak evidence')
    def source():
        return {'commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                'dirty': bool(subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, text=True).strip())}
    source_before = source()
    processes = []; logs = []
    try:
        for name in ['server', *['client-' + str(i) for i in range(args.clients)]]:
            if name != 'server' and len(processes) == 1:
                for _ in range(200):
                    if 'SIGHTBREAK_SERVER_READY' in (args.out / 'server.log').read_text(): break
                    if processes[0][1].poll() is not None: raise RuntimeError('server failed')
                    time.sleep(.05)
                else: raise RuntimeError('server readiness timed out')
            log = (args.out / (name + '.log')).open('w'); logs.append(log)
            command = [str(ROOT / 'scripts/godot.sh'), '--headless', '--max-fps', '60', '--script', str(ROOT / 'scripts/fixtures/network_soak.gd'), '--', '--port=' + str(args.port), '--clients=' + str(args.clients), '--output=' + str(args.out / (name + '.json'))]
            if name == 'server': command.append('--server')
            processes.append((name, subprocess.Popen(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)))
        results = []
        for name, process in processes:
            code = process.wait(timeout=85)
            text = (args.out / (name + '.log')).read_text()
            report = json.loads((args.out / (name + '.json')).read_text())
            assert code == 0 and 'ERROR:' not in text and report['passed'], name + ' failed'
            results.append(report)
        assert source() == source_before, 'source changed during soak'
        summary = {'source': source_before, 'processes': results}
        (args.out / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
        print(json.dumps(summary, indent=2))
    finally:
        for _, process in processes:
            if process.poll() is None: process.terminate()
        for _, process in processes:
            try: process.wait(timeout=5)
            except subprocess.TimeoutExpired: process.kill(); process.wait()
        for log in logs: log.close()

if __name__ == '__main__': main()
