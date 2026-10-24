#!/usr/bin/env python3
"""Preserve old method failure against declared fine-sleep/coarse-clock input."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[5]
OUT = Path(__file__).resolve().parents[1]
assert sorted(os.sched_getaffinity(0)) == [4]
sys.path.insert(0, str(ROOT / 'scripts'))
from test_native_route_pulse import IndependentClockPulse
fixture = OUT / 'controls/baseline_key_pulse.py'
namespace = {'__name__': 'preserved_baseline'}
exec(compile(fixture.read_text(), str(fixture), 'exec'), namespace)
trial = IndependentClockPulse(tick=.015625)
try:
    namespace['key_pulse'](trial.ui, ('d',), .12567175974707734,
                           deadline=trial.epoch + 1, receipt=trial.receipt,
                           clock=trial.monotonic, sleep=trial.sleep)
except RuntimeError as error:
    failure = str(error)
else:
    raise AssertionError('Original method unexpectedly passed')
assert failure == 'Native route pulse sleep returned before its requested boundary'
assert trial.receipt['hold_until_monotonic'] == 768.093671759747
assert trial.receipt['edges'][0]['before_monotonic'] == 767.968
assert trial.receipt['edges'][1]['before_monotonic'] == 768.093
assert trial.receipt['release_complete'] is True and not trial.down
report = dict(scope='Declared pure counterexample; not physical reconstruction',
              fixture_sha256=hashlib.sha256(fixture.read_bytes()).hexdigest(),
              expected_failure=failure, pulse_receipt=trial.receipt,
              modeled_sleep_requests=trial.sleep_requests, passed=True)
(OUT / 'baseline-model-result.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
