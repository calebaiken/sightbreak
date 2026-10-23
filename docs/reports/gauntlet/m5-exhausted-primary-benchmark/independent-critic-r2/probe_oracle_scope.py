#!/usr/bin/env python3
"""Synthetic adversarial scope checks; not executed-game evidence."""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from test_witness_oracle import HEADER, controls
from witness_oracle import audit


def run():
    results = []
    rows = controls()
    for row in rows:
        for phase in ('before', 'after_decision', 'after_action'):
            row[phase]['position'] = [-10., 0., -10.]
        for phase in ('enemy_before', 'enemy_after_decision', 'enemy_after_action'):
            row[phase]['position'] = [10., 0., -10.]
    audit(HEADER, rows)
    results.append({'probe': 'continuous 20m in-bounds actors replacing declared 2m control lane', 'oracle': 'ACCEPTED',
                    'limit': 'Oracle verifies bounds, not exact preregistered poses, lane/snapshot agreement, endpoints or distance'})
    rows = controls()
    for row in rows:
        if row['scenario']['control'] == 'kill_rifle':
            for phase in ('before', 'after_decision', 'after_action'):
                row[phase]['ammo'] = 1
    audit(HEADER, rows)
    results.append({'probe': 'shot event and real target/reward timeline without shooter ammo consumption', 'oracle': 'ACCEPTED',
                    'limit': 'Oracle does not independently recompute full ammo conservation; fixture checks it and raw states permit later independent audit'})
    print(json.dumps({'scope': 'Synthetic supplementary boundary probes; no executed game evidence', 'results': results}, indent=2))


if __name__ == '__main__':
    run()
