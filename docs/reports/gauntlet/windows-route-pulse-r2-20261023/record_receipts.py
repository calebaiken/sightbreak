"""Retain fake User32 receipts through the actual WinUI.key/_input path."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[3]
sys.path.insert(0, str(ROOT / 'scripts'))
from test_native_route_pulse import RealKeyPulse

rows = []
for name in ('two_key_positive', 'focus_after_w', 'owner_after_w', 'hidden_after_w',
             'thread_unknown_after_w', 'rebound_after_w', 'external_a_after_w',
             'unknown_before_d', 'cancel_before_d', 'late_before_d_hold',
             'late_before_d_cap', 'partial_down_and_up_error', 'late_release_read', 'list_alias'):
    rig = RealKeyPulse()
    names, seconds, deadline = ('w', 'd'), .125, 35
    expected = None
    if name in ('focus_after_w', 'owner_after_w', 'hidden_after_w', 'thread_unknown_after_w'):
        field, value = {'focus_after_w': ('foreground', 99), 'owner_after_w': ('owner', 99),
                        'hidden_after_w': ('visible', False), 'thread_unknown_after_w': ('thread', 0)}[name]
        rig.after_down_hook = lambda: setattr(rig, field, value)
        expected = 'RuntimeError'
    elif name == 'rebound_after_w':
        rig.after_down_hook = lambda: setattr(rig.ui, 'window', 99)
        expected = 'RuntimeError'
    elif name == 'external_a_after_w':
        rig.after_down_hook = lambda: rig.down.add('a')
        expected = 'RuntimeError'
    elif name in ('unknown_before_d', 'cancel_before_d'):
        error = OSError('declared unknown per-down read') if name == 'unknown_before_d' else KeyboardInterrupt()
        def read(stage):
            if stage == 'before_key_down:d': raise error
        rig.read_hook = read
        expected = type(error).__name__
    elif name in ('late_before_d_hold', 'late_before_d_cap'):
        if name == 'late_before_d_cap': deadline = .1
        def read(stage):
            if stage == 'before_key_down:d': rig.now += .2
        rig.read_hook = read
        expected = 'TimeoutError'
    elif name == 'partial_down_and_up_error':
        rig.error_down, rig.error_up = {'d'}, {'w'}
        expected = 'OSError'
    elif name == 'late_release_read':
        def read(stage):
            if stage == 'after_release': rig.now += .2
        rig.read_hook = read
        seconds, deadline, expected = .1, .15, 'TimeoutError'
    elif name == 'list_alias':
        names = ['w', 'd']
    initial = {'keys': sorted(rig.down), 'owner': rig.owner, 'foreground': rig.foreground,
               'window': rig.ui.window, 'pid': rig.ui.pid, 'time': rig.now}
    caught = None
    try:
        rig.run(names, seconds, deadline)
    except BaseException as error:
        caught = {'type': type(error).__name__, 'message': str(error)}
    assert (caught['type'] if caught else None) == expected, (name, caught, expected)
    if name == 'list_alias':
        names[:] = ['s']
        assert rig.receipt['keys'] == ['w', 'd']
    rows.append({'case': name, 'raw_before': initial, 'calls': deepcopy(rig.calls),
                 'receipt': deepcopy(rig.receipt), 'exception': caught, 'read_stages': list(rig.read_stages),
                 'raw_after': {'keys': sorted(rig.down), 'owner': rig.owner, 'foreground': rig.foreground,
                               'window': rig.ui.window, 'pid': rig.ui.pid, 'time': rig.now}})
value = {'source_freeze': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
         'scope': 'Declared mock OS/API/time only; actual key/_input source path, no native execution or physical timing proof',
         'cases': rows}
(OUT / 'pure-real-key-receipts.json').write_text(json.dumps(value, indent=2) + '\n')
print(json.dumps({'cases': len(rows), 'source_freeze': value['source_freeze']}))
