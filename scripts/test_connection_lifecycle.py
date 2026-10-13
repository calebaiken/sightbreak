#!/usr/bin/env python3
"""Real adversarial ENet clients: post-auth silence, joined idle, ignored rejection."""
from pathlib import Path
import argparse
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    processes, logs = [], []
    try:
        for index, scenario in enumerate(('silent', 'idle', 'reject')):
            port = 29900 + index
            command = [str(ROOT / 'scripts/godot.sh'), '--headless', '--max-fps', '60', '--script', 'res://tests/connection_lifecycle_probe.gd', '--', '--scenario=' + scenario, '--port=' + str(port)]
            for role in ('server', 'client'):
                path = args.out / f'{scenario}-{role}.log'
                log = path.open('w'); logs.append(log)
                process = subprocess.Popen(command + ['--role=' + role], stdout=log, stderr=subprocess.STDOUT, cwd=ROOT)
                processes.append((path, process))
                if role == 'server':
                    for _ in range(100):
                        if 'SIGHTBREAK_SERVER_READY' in path.read_text(): break
                        if process.poll() is not None: raise RuntimeError('server startup failed')
                        time.sleep(.05)
                    else: raise RuntimeError('server readiness timed out')
        failures = []
        for path, process in processes:
            code = process.wait(timeout=45)
            text = path.read_text()
            if code or 'ERROR:' in text or 'SCRIPT ERROR' in text or '"ok":true' not in text:
                failures.append(path.name)
            print(path.name, text.strip().splitlines()[-1])
        if failures: raise RuntimeError('Failed: ' + ', '.join(failures))
        print('CONNECTION_LIFECYCLE_TEST three native scenarios and server cleanup passed')
    finally:
        for _, process in processes:
            if process.poll() is None: process.terminate()
        for _, process in processes:
            try: process.wait(timeout=5)
            except subprocess.TimeoutExpired: process.kill(); process.wait()
        for log in logs: log.close()

if __name__ == '__main__': main()
