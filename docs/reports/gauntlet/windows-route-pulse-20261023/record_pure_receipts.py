"""Record declared mocked OS/API brackets; never claim physical timing."""
import json
from pathlib import Path
import subprocess
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'scripts'))
from test_native_route_pulse import MockPulse


rows = []
for name in ('ordinary', 'partial_down_error', 'sleep_error', 'late_up', 'late_os_read', 'external_a'):
    trial = MockPulse()
    names, duration, deadline = ('d',), .125, 35
    if name == 'partial_down_error': names, trial.error_down = ('w', 'd'), {'d'}
    if name == 'sleep_error': trial.sleep_error = OSError('declared sleep failure')
    if name == 'late_up': trial.up_delay, duration, deadline = .2, .1, .15
    if name == 'late_os_read': trial.state_delays[3], duration, deadline = .2, .1, .15
    if name == 'external_a': trial.down.add('a')
    error = None
    try:
        trial.run(names, duration, deadline)
    except BaseException as caught:
        error = {'type': type(caught).__name__, 'message': str(caught)}
    rows.append({'case': name, 'events': trial.events, 'receipt': trial.receipt,
                 'exception': error, 'mock_os_keys_after': sorted(trial.down)})
receipt = {'source_freeze': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
           'scope': 'Declared fake clock/OS/API callbacks only; not real native or physical timing evidence', 'cases': rows}
Path(__file__).with_name('pure-pulse-receipts.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps({'declared_cases': len(rows), 'source_freeze': receipt['source_freeze']}))
