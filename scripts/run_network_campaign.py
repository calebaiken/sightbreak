#!/usr/bin/env python3
"""Run the reproducible ten-process synthetic campaign; preserve every failure.

Requires the existing Godot toolchain. No physical/cellular performance claim.
Use --reconnect-delay 0.7 to reproduce the original aggressive reconnect fixture.
"""
import argparse
import json
import os
from pathlib import Path
import signal
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--seconds', type=float, default=18)
    parser.add_argument('--clients', type=int, choices=range(2, 11), default=10)
    parser.add_argument('--port', type=int, default=32200)
    parser.add_argument('--reconnect-delay', type=float, default=2)
    parser.add_argument('--only', help='One condition name; omitted runs all twelve')
    args = parser.parse_args()
    if not 12 <= args.seconds <= 600 or not 0 <= args.reconnect_delay <= 10 or not 1024 <= args.port <= 65000:
        parser.error('seconds must be12–600, reconnect-delay0–10 and base port1024–65000')
    conditions = [('rtt-' + str(rtt), ['--rtt-ms', str(rtt)]) for rtt in [0, 50, 100, 150, 200]]
    impaired = ['--rtt-ms', '100', '--jitter-ms', '20', '--loss', '0.03', '--reorder', '0.05']
    blackout = ['--blackout-at', '4', '--blackout-seconds', '2']
    conditions += [('jitter', ['--rtt-ms', '100', '--jitter-ms', '20']),
                   ('loss', ['--rtt-ms', '100', '--loss', '0.03']),
                   ('reorder', ['--rtt-ms', '100', '--reorder', '0.05']),
                   ('impaired', impaired), ('blackout', ['--rtt-ms', '100', *blackout]),
                   ('reconnect', [*impaired, *blackout, '--reconnect-at', '8']),
                   ('prediction-disabled', ['--rtt-ms', '100', '--no-prediction'])]
    if args.only and args.only not in dict(conditions):
        parser.error('unknown condition: ' + args.only)
    args.out = args.out.resolve()
    args.out.mkdir(parents=True, exist_ok=True)
    results = []
    for index, (name, extra) in enumerate(conditions):
        if args.only and name != args.only:
            continue
        command = ['python3', str(ROOT / 'scripts/simulate_network.py'), '--clients', str(args.clients),
                   '--seconds', str(args.seconds), '--port', str(args.port + index * 20),
                   '--reconnect-delay', str(args.reconnect_delay), '--out', str(args.out / name), *extra]
        with (args.out / (name + '.log')).open('w') as log:
            process = subprocess.Popen(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            try:
                code = process.wait(timeout=args.seconds + 60)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
                code = 124
        path = args.out / name / 'summary.json'
        summary = json.loads(path.read_text()) if path.exists() else None
        results.append({'name': name, 'command': command, 'exit': code, 'summary': summary})
        (args.out / 'campaign.json').write_text(json.dumps(results, indent=2) + '\n')
        print(name + ': ' + ('PASS' if code == 0 and summary else 'FAIL'), flush=True)
    return int(any(row['exit'] != 0 or not row['summary'] for row in results))


if __name__ == '__main__':
    raise SystemExit(main())
