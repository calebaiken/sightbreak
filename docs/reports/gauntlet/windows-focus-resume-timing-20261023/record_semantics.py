"""Retain declared semantic event sequences; these are not native timings."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys


root = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(root / 'scripts'))
from test_focus_resume_timing import ResumeTrial, state


dead = state(1, paused=False)
dead['local_actor'].update(alive=False, health=0)
cases = [
    ('immediate_fresh_ack', [state(1, paused=False)], 300),
    ('delayed_unpaused_ack', [state(1, paused=True), state(2, paused=False)], 300),
    ('stale_unpaused_then_fresh_ack', [state(0, paused=False), state(1, paused=False)], 300),
    ('ack_timeout', [state(1, paused=True)], 300),
    ('whole_budget_caps_ack', [state(1, paused=True)], .75),
    ('deadline_blocks_hold_then_existing_cleanup', [], .2),
    ('dead_at_ack', [dead], 300)]
rows = []
for name, states, deadline in cases:
    trial = ResumeTrial(states, deadline=deadline)
    error = None
    try:
        trial.run()
    except Exception as caught:
        error = {'type': type(caught).__name__, 'message': str(caught)}
    if name == 'deadline_blocks_hold_then_existing_cleanup':
        exec(trial.cleanup_code, trial.namespace)
    rows.append({'name': name, 'declared_states': states, 'whole_deadline': deadline,
                 'elapsed_declared_seconds': trial.elapsed, 'events': trial.events,
                 'exception': error, 'context_receipt': trial.context,
                 'guarded': trial.namespace.get('guarded')})
receipt = {'source_freeze': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
           'scope': 'Declared state/clock callbacks and actual controller AST; no native latency evidence',
           'controller_sha256': hashlib.sha256((root / 'scripts/verify_offline_export.py').read_bytes()).hexdigest(),
           'cases': rows}
Path(__file__).with_name('semantic-controls.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps({'source_freeze': receipt['source_freeze'], 'declared_cases_retained': len(rows)}))
