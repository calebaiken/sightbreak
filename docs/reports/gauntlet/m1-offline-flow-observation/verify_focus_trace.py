#!/usr/bin/env python3
"""Check the production release predicate against real-engine ordering receipts."""
import argparse
import copy
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'scripts'))
from verify_offline_export import focus_controls_released

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('log', type=Path)
args = parser.parse_args()
lines = args.log.read_text().splitlines()
assert not any(line.startswith(('ERROR:', 'SCRIPT ERROR:')) for line in lines)
receipts = [json.loads(line.removeprefix('FOCUS_RELEASE_ORDERING ')) for line in lines if line.startswith('FOCUS_RELEASE_ORDERING ')]
assert len(receipts) == 1
receipt = receipts[0]
assert receipt['before_controller_tick']['local_input']['move'] == [0, 0]
assert receipt['before_controller_tick']['local_input']['fire'] is False
assert not focus_controls_released(receipt['before_controller_tick'])
assert not focus_controls_released(receipt['premature_press'])
assert focus_controls_released(receipt['acknowledged_release'])
assert receipt['fresh_input'] == [0, 1]
missing = copy.deepcopy(receipt['acknowledged_release'])
del missing['ui']['waiting_for_input_release']
assert not focus_controls_released(missing)
nonneutral = copy.deepcopy(receipt['acknowledged_release'])
nonneutral['local_input']['move'] = [0, 1]
assert not focus_controls_released(nonneutral)
nonneutral['local_input'].update(move=[0, 0], fire=True)
assert not focus_controls_released(nonneutral)
print(json.dumps({'checks': 9, 'failures': 0, 'scope': 'actual Godot source controller ordering plus production observer predicate, not native hardware',
                  'old_neutral_predicate_accepts_before_controller_tick': True,
                  'candidate_accepts_only_acknowledged_release': True}, indent=2))
