#!/usr/bin/env python3
"""Replay retained native JSON only; never invoke OCR, native APIs or an engine."""
import copy
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT/'scripts'))
from macos_ordinary_input import label_point

original = json.loads((Path(__file__).parent/'original-native-39912086121/macos-ordinary-input/01-focused-menu.json').read_text())
rows = []
for case in ('original', 'middle_dot_only', 'confidence_only'):
    image = copy.deepcopy(original)
    row = next(row for row in image['text'] if row['text'].startswith('DEPLOY'))
    if case == 'middle_dot_only': row['text'] = row['text'].replace('•', '·')
    if case == 'confidence_only': row['confidence'] = .8
    try:
        point = label_point(image, 'DEPLOY · OFFLINE 5V5')
    except RuntimeError as error:
        rows.append({'case': case, 'deploy_observation': row, 'error': str(error)})
    else:
        raise AssertionError('Original/native-only observation incorrectly accepted: '+repr(point))
print(json.dumps({'scope': 'Pure retained JSON replay; no new OCR observation', 'cases': rows}, indent=2))
