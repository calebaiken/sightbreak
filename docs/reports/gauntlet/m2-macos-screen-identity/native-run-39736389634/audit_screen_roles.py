"""Inspect exact screen roles in new original Vision receipts; no OCR execution."""
import argparse
import json
import math
from pathlib import Path

HOME = ('SIGHTBREAK', 'OPERATOR RECORD', 'SETTINGS')
SETTINGS = 'FIELD SETTINGS'


def observation(entry):
    text = ' '.join(entry.get('text', '').upper().split())
    value = entry.get('confidence')
    confident = isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value >= .8
    box = entry.get('box_normalized_bottom_left')
    numeric = isinstance(box, list) and len(box) == 4 and all(
        isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) for v in box)
    bounded = numeric and min(box[:2]) >= 0 and min(box[2:]) > 0 and box[2] <= 1 - box[0] and box[3] <= 1 - box[1]
    return {'normalized_text': text, 'confidence': value, 'qualifying_confidence': confident,
            'positive_finite_in_bounds_box': bounded, 'box': box}


def audit(root):
    result = []
    for name, expected in [('00-background-window', None), ('01-menu-0', 'home'),
                           ('02-field-settings', 'settings'), ('03-returned-menu', 'home')]:
        path = root / 'macos-menu-input' / (name + '.json')
        if not path.exists():
            result.append({'name': name, 'expected_role': expected, 'receipt_exists': False})
            continue
        receipt = json.loads(path.read_text())
        rows = [observation(entry) for entry in receipt.get('text', [])]
        roles = {label: [r for r in rows if r['normalized_text'] == label and r['qualifying_confidence']]
                 for label in (*HOME, SETTINGS)}
        unique = {label: len(matches) == 1 and matches[0]['positive_finite_in_bounds_box']
                  for label, matches in roles.items()}
        home = all(unique[label] for label in HOME) and not roles[SETTINGS]
        settings = unique[SETTINGS] and not any(roles[label] for label in HOME)
        result.append({'name': name, 'expected_role': expected, 'receipt_exists': True,
                       'owner_pid': receipt.get('owner_pid'), 'window_id': receipt.get('window_id'),
                       'capture_passed': receipt.get('passed'), 'roles': roles, 'unique_valid_roles': unique,
                       'home_identity': bool(home), 'settings_identity': bool(settings),
                       'expected_role_observed': None if expected is None else bool(home if expected == 'home' else settings),
                       'shared_title_bar_rows': [r for r in rows if r['normalized_text'].startswith('SIGHTBREAK (')],
                       'masthead_rows': [r for r in rows if 'TACTICAL OPERATIONS' in r['normalized_text']]})
    return {'confidence_minimum': .8, 'source': 'Original new-run Vision receipts; no stored fixture replay', 'captures': result}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('full_qa', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.full_qa)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({item['name']: item.get('expected_role_observed') for item in result['captures']}))
