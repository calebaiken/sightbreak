#!/usr/bin/env python3
"""Read official extracted originals without launching product/native/OCR code."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('receipts', type=Path)
    parser.add_argument('full', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    here = Path(__file__).resolve().parent
    args.output.mkdir(parents=True, exist_ok=False)
    specs = [('schedules', 'audit_input_schedules.py', [args.receipts]),
             ('route', 'audit_settings_route.py', [args.receipts]),
             ('pulse-api', 'audit_route_pulses.py', [args.receipts]),
             ('phase-captures', 'audit_phase_captures.py', [args.receipts, '--full', args.full]),
             ('focus', 'audit_focus_actual.py', [args.receipts, args.full]),
             ('journey-ocr', 'audit_journey_ocr.py', [args.receipts]),
             ('failure-diagnostics', 'audit_failure_diagnostics.py', [args.receipts]),
             ('full-qa-crosscheck', 'audit_full_qa.py', [args.receipts, args.full])]
    records = []
    for name, script, values in specs:
        command = [sys.executable, str(here / script), *map(str, values), '--output', str(args.output / (name + '.json'))]
        started = time.monotonic()
        outcome = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=180)
        for suffix, data in [('stdout', outcome.stdout), ('stderr', outcome.stderr)]:
            (args.output / (name + '.' + suffix)).write_bytes(data)
        records.append(dict(name=name, command=command, exit=outcome.returncode,
                            wall_seconds=time.monotonic() - started,
                            stdout_sha256=hashlib.sha256(outcome.stdout).hexdigest(),
                            stderr_sha256=hashlib.sha256(outcome.stderr).hexdigest()))
    report = dict(source='c32415148db1f110bbc7eadfca3793d4693429ff', run_id=40080238905,
                  records=records, scope='Pure original receipt review; script exit0 alone is not a native verdict')
    (args.output / 'commands.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'records': len(records), 'audit_process_failures': [row['name'] for row in records if row['exit']]}))


if __name__ == '__main__':
    main()
