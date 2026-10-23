#!/usr/bin/env python3
"""Run the reproducible ten-process synthetic campaign; preserve every failure.

Requires the existing Godot toolchain. No physical/cellular performance claim.
Use --reconnect-delay 0.7 to reproduce the original aggressive reconnect fixture.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

import native_log
from godot_process import prepare_output, source_failures, source_snapshot
from matrix_process import run_process

ROOT = Path(__file__).resolve().parents[1]


def trial_failures(code, summary, before, after, frozen):
    """A summary file is evidence, not proof of a successful child run."""
    failures = []
    if code != 0:
        failures.append('simulation exit ' + str(code))
    if not isinstance(summary, dict) or not summary:
        failures.append('missing or invalid simulation summary')
    else:
        if not isinstance(summary.get('failures'), list) or summary['failures']:
            failures.append('simulation summary contains failures or has no failure gate')
        if summary.get('passed') is not True:
            failures.append('simulation summary did not pass')
        if summary.get('source_unchanged') is not True:
            failures.append('simulation source was not frozen')
        if summary.get('source_before') != frozen or summary.get('source_after') != frozen:
            failures.append('simulation source does not match frozen campaign source')
    failures.extend(source_failures(before, after))
    if before != frozen or after != frozen:
        failures.append('trial source does not match frozen campaign source')
    return failures


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
    try:
        args.out = prepare_output(args.out)
    except FileExistsError as error:
        parser.error(str(error))
    frozen = source_snapshot(root=ROOT)
    if frozen['dirty']:
        parser.error('source must be clean and frozen before campaign')
    results = []
    # Open exclusively once; only this run may update its progress record.
    with (args.out / 'campaign.json').open('x', encoding='utf-8') as progress:
        for index, (name, extra) in enumerate(conditions):
            if args.only and name != args.only:
                continue
            before = source_snapshot(root=ROOT)
            command = [sys.executable, str(ROOT / 'scripts/simulate_network.py'), '--clients', str(args.clients),
                       '--seconds', str(args.seconds), '--port', str(args.port + index * 20),
                       '--reconnect-delay', str(args.reconnect_delay), '--out', str(args.out / name), *extra]
            failures = []
            code, summary = 125, None
            if before != frozen or before['dirty']:
                failures.append('source changed before trial; child not launched')
            else:
                with (args.out / (name + '.log')).open('x', encoding='utf-8') as log:
                    try:
                        code = run_process(command, cwd=ROOT, env=dict(os.environ), log=log,
                                           result_path=args.out / (name + '.process.json'),
                                           timeout=args.seconds + 60)
                    except subprocess.TimeoutExpired:
                        code = 124
                        failures.append('simulation timed out')
                    except KeyboardInterrupt:
                        code = 130
                        failures.append('campaign interrupted')
                    except OSError as error:
                        code = 127
                        failures.append('simulation launch failed: ' + str(error))
            path = args.out / name / 'summary.json'
            if path.exists():
                try:
                    summary = json.loads(path.read_text(encoding='utf-8'))
                except (OSError, ValueError) as error:
                    failures.append('invalid simulation summary: ' + str(error))
            # Independently audit every native log, not just the child's verdict.
            logs = [args.out / (name + '.log'), *sorted((args.out / name).rglob('*.log'))]
            for path in logs:
                if path.is_file():
                    text = path.read_text(encoding='utf-8', errors='replace')
                    if native_log.failed(text) or 'HARNESS_ERROR' in text:
                        failures.append(str(path.relative_to(args.out)) + ': logged error, resource leak or HARNESS_ERROR')
            after = source_snapshot(root=ROOT)
            failures.extend(trial_failures(code, summary, before, after, frozen))
            results.append({'name': name, 'command': command, 'exit': code, 'summary': summary,
                            'source_before': before, 'source_after': after,
                            'passed': not failures, 'failures': failures})
            progress.seek(0)
            progress.write(json.dumps(results, indent=2) + '\n')
            progress.truncate()
            progress.flush()
            print(name + ': ' + ('FAIL' if failures else 'PASS'), flush=True)
            if before != frozen or after != frozen or code == 130:
                break
        after = source_snapshot(root=ROOT)
        failures = source_failures(frozen, after)
        if failures:
            # A final-window mutation invalidates the campaign even when every
            # individual child finished before that mutation was observed.
            for row in results:
                row['passed'] = False
                row['failures'].extend('campaign: ' + failure for failure in failures)
            progress.seek(0)
            progress.write(json.dumps(results, indent=2) + '\n')
            progress.truncate()
            progress.flush()
            print('campaign: FAIL frozen source verification', flush=True)
    passed = bool(results) and not failures and all(row['passed'] for row in results)
    with (args.out / 'source.json').open('x', encoding='utf-8') as output:
        output.write(json.dumps({'source_before': frozen, 'source_after': after,
                                 'source_unchanged': frozen == after, 'passed': passed,
                                 'failures': failures}, indent=2) + '\n')
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
