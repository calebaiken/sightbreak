#!/usr/bin/env python3
"""Exercise the embedded Linux game pack, with an external, unshipped fixture.

Requires a native display; Xvfb/software is functional evidence, not phone FPS.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]


def main():
    executable = ROOT / 'builds/linux/sightbreak.x86_64'
    fixture = ROOT / 'scripts/fixtures/export_integration.gd'
    output = ROOT / 'builds/verification/integration'
    output.mkdir(parents=True, exist_ok=True)
    processes = []
    logs = []
    records = []
    try:
        for role in ('offline', 'server', 'client'):
            log = (output / (role + '.log')).open('w')
            logs.append(log)
            display = ['--headless'] if role == 'server' else ['--audio-driver', 'Dummy']
            command = [str(executable), *display, '--max-fps', '60', '--script', str(fixture), '--', '--role=' + role,
                       '--output=' + str(output / (role + '.png'))]
            process = subprocess.Popen(command, cwd=output, env=os.environ, stdout=log, stderr=subprocess.STDOUT)
            processes.append((role, process))
            if role == 'server':
                for _ in range(200):
                    if 'SIGHTBREAK_SERVER_READY' in (output / 'server.log').read_text(): break
                    if process.poll() is not None: raise RuntimeError('Exported server failed to start')
                    time.sleep(.05)
                else: raise RuntimeError('Exported server readiness timed out')
            else:
                process.wait(timeout=120)
        for role, process in processes:
            code = process.wait(timeout=30)
            text = (output / (role + '.log')).read_text()
            assert code == 0 and re.search(r'EXPORT_INTEGRATION role=' + role + r' passed=true', text), role + ': fixture failed'
            assert not re.search(r'^(?:SCRIPT ERROR|ERROR:)|Parse Error|ObjectDB instances leaked|Leaked instance', text, re.M), role + ': error/leak in log'
            records.append({'role': role, 'passed': True, 'log': role + '.log'})
        report = {'source': json.loads((ROOT / 'builds/linux/source.json').read_text()),
                  'executable_sha256': hashlib.sha256(executable.read_bytes()).hexdigest(), 'checks': records,
                  'scope': 'actual exported Linux executable/embedded PCK; native offline and ENet client; headless exported server; Xvfb/Mesa, no device performance claim'}
        (output / 'results.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(report, indent=2))
    finally:
        for _, process in processes:
            if process.poll() is None: process.terminate()
        for _, process in processes:
            try: process.wait(timeout=5)
            except subprocess.TimeoutExpired: process.kill(); process.wait()
        for log in logs: log.close()


if __name__ == '__main__': main()
