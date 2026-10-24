#!/usr/bin/env python3
"""Pure preparation controls; no engine, real /proc sampling or native signals."""
import ast
import importlib.util
import json
from pathlib import Path
import tempfile
from unittest import mock

HERE = Path(__file__).resolve().parent
path = HERE / 'run_once.py'
spec = importlib.util.spec_from_file_location('preflight_controls', path)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
tree = ast.parse(path.read_text())
launches = [node for node in ast.walk(tree) if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name)
            and node.func.value.id == 'subprocess' and node.func.attr == 'Popen']
assert len(launches) == 1
assert m.WHOLE_SECONDS == 420 and m.CLEANUP_SECONDS == 5
controls = ['one fixed runner launch site', '420/5 budgets unchanged']
# This is the same decision used by the real monitor after child.poll().
# A successful return code does not excuse its first observation at the deadline.
for observed in (420.0, 420.001, 421.0):
    stop, timed_out = m.deadline_state(0, observed, 420.0)
    assert stop and timed_out
controls.append('successful exit first observed at/after420 rejected')
stop, timed_out = m.deadline_state(0, 419.999, 420.0)
assert stop and not timed_out
controls.append('successful exit observed justbefore420 admitted to remaining gates')
assert m.deadline_state(None, 420.0, 420.0) == (True, True)
assert m.deadline_state(None, 419.999, 420.0) == (False, False)
controls.append('running child stops at420 and continues before420')
with tempfile.TemporaryDirectory(prefix='collector-preparation-control-') as directory:
    target = Path(directory) / 'fresh'
    target.mkdir(parents=True, exist_ok=False)
    try:
        target.mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        controls.append('existing output rejects reuse')
    else:
        raise AssertionError('Output reuse accepted')
with mock.patch.object(m, 'git', return_value=b'wrong-head\n'):
    try:
        m.source_manifest()
    except AssertionError:
        controls.append('wrong runtime HEAD rejected')
    else:
        raise AssertionError('Wrong HEAD accepted')

clock = [0.0]
signals = []
row = {'pid': 123, 'pgid': 123, 'sid': 123}


def sleep(seconds):
    clock[0] += seconds


def cleanup(sample):
    with mock.patch.object(m.time, 'monotonic', lambda: clock[0]), \
            mock.patch.object(m.time, 'sleep', sleep), \
            mock.patch.object(m.os, 'killpg', lambda pid, sig: signals.append((pid, sig.name))):
        return m.clean_group(123, set(), sample)


receipt = cleanup(lambda stage: [row] if clock[0] < 3 else [])
assert receipt['all_observed_identities_gone'] and clock[0] <= 5
assert signals == [(123, 'SIGTERM'), (123, 'SIGKILL')]
controls.append('TERM then KILL within5s')
clock[0] = 0
signals.clear()
stuck = cleanup(lambda stage: [row])
assert not stuck['all_observed_identities_gone'] and clock[0] <= 5
controls.append('surviving identity remains failure')
clock[0] = 0
signals.clear()
absent = cleanup(lambda stage: [])
assert absent['all_observed_identities_gone'] and signals == [] and clock[0] == 0
controls.append('absent group receives no signal')
result = {'passed': True, 'controls': controls, 'native_invocations': 0,
          'observer_invocations': 0, 'scope': 'Static source, temporary mkdir, mocked samples and virtual time'}
(HERE / 'preparation-controls.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result))
