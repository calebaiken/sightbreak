#!/usr/bin/env python3
"""Read-only recomputation of the archived ACK-timeline positions and receipts."""
import argparse
import hashlib
import json
import math
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def p95(values):
    return sorted(values)[int((len(values) - 1) * 0.95)]


def close(left, right):
    # JSON holds single-precision native vectors; recomputation uses doubles.
    return abs(left - right) < 0.00002


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('evidence', type=Path)
    args = parser.parse_args()
    root = args.evidence
    manifest = json.loads((root / 'manifest.json').read_text(encoding='utf-8'))
    checks = 0

    def check(ok, label):
        nonlocal checks
        checks += 1
        if not ok:
            raise AssertionError(label)

    summaries = {}
    for label, source in manifest['runs'].items():
        location = root / label
        check(sha(location / 'timeline.json') == source['timeline_sha256'], label + ': raw hash')
        check(source['shipping_sha256_by_path'] == source['shipping_after_sha256_by_path'], label + ': shipping stable')
        for name, receipt in {**source['tests'], 'probe': source['probe'], 'import': source['import']}.items():
            check(receipt['exit'] == 0 and not receipt['logged_error'], name + ': native exit/errors')
            check(sha(location / (name + '.log')) == receipt['log_sha256'], name + ': log hash')
        data = json.loads((location / 'timeline.json').read_text(encoding='utf-8'))
        check(not data['failures'], label + ': native assertions')
        summary = []
        for case in data['conditions']:
            positions = []
            for row in case['rows']:
                separation = math.dist(row['authority'], row['prediction'])
                check(close(separation, row['error_m']), case['name'] + ': geometry')
                if row['tick'] > 60:
                    positions.append(separation)
            check(close(p95(positions), case['same_time_error_p95_m']), case['name'] + ': paired-time percentile')
            ack_errors = []
            held = unscored = 0
            for row in case['snapshots']:
                drift = math.dist(row['authority'], row['pose_at_consumption'])
                check(close(drift, row['same_ack_drift_m']), case['name'] + ': same-ACK geometry')
                if row['saved_ack_pose'] is not None:
                    ack_error = math.dist(row['authority'], row['saved_ack_pose'])
                    check(close(ack_error, row['ack_error_m']), case['name'] + ': ACK geometry')
                    ack_errors.append(ack_error)
                else:
                    check(row['ack_error_m'] is None, case['name'] + ': missing sample is not zero')
                if drift > 0.01:
                    held += 1
                    unscored += row['ack_error_m'] is None
            check(len(ack_errors) == case['ack_error_sample_count'], case['name'] + ': ACK coverage')
            check((held, unscored) == (case['held_snapshots'], case['unscored_held_snapshots']), case['name'] + ': held coverage')
            if case['prediction_enabled']:
                check(close(p95(ack_errors), case['ack_error_p95_m']), case['name'] + ': ACK percentile')
            else:
                check(case['ack_error_p95_m'] is None, case['name'] + ': disabled score excluded')
            summary.append({'condition': case['name'], 'snapshot_count': len(case['snapshots']),
                            'ack_samples': len(ack_errors), 'held_snapshots': held,
                            'unscored_held_snapshots': unscored})
        summaries[label] = summary
    payloads = [root / label / 'timeline.json' for label in manifest['runs']]
    check(payloads[0].read_bytes() == payloads[1].read_bytes(), 'matched native raw outcomes identical')
    print(json.dumps({'checks': checks, 'failures': 0, 'summaries': summaries,
                      'scope': 'geometric metric and receipt recomputation, not an independent human/agent review'}, indent=2))


if __name__ == '__main__':
    main()
