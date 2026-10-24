"""Replay unchanged independent cases, retaining their now-obsolete defect assertions."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess


directory = Path(__file__).parent
probe_path = directory / 'probe_fence.py'
spec = importlib.util.spec_from_file_location('unchanged_independent_probe', probe_path)
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)
rows, original_failure = None, None
try:
    probe.main()
except AssertionError as error:
    original_failure = str(error)
    trace = error.__traceback__
    while trace:
        if trace.tb_frame.f_code.co_name == 'main' and 'rows' in trace.tb_frame.f_locals:
            rows = trace.tb_frame.f_locals['rows']
        trace = trace.tb_next
assert rows is not None and len(rows) == 77
assert probe_path.read_bytes() == (directory / 'rejected-review/probe_fence.py').read_bytes()
checks = []
positives = {'valid_living_movement', 'bad_.time_scale_3', 'predicate_returns_after_original_deadline'}
timeouts = {'stale_movement_then_timeout', 'missing_publication_then_timeout', 'whole_deadline_limits_wait'}
for row in rows:
    name = row['name']
    if name in positives:
        assert row['observation'] == 'LIVING_MOVEMENT_OBSERVED', name
    elif name in timeouts:
        assert row['observation'] == 'TimeoutError', name
        assert row['fresh_press']['status'] == 'RESPONSE_NOT_OBSERVED_BEFORE_ORIGINAL_DEADLINE', name
        assert row['keys'] == [['w', True], ['w', False]], name
    elif name == 'dispatch_failure_still_releases':
        assert row['observation'] == 'RuntimeError' and row['keys'] == [['w', True], ['w', False]], name
    else:
        assert row['observation'] == 'FocusPreconditionLost', name
        assert row['context_fence']['status'] == 'FOCUS_PRECONDITION_LOST', name
        assert 'rejected_state' in row['context_fence']['precondition_loss'], name
        assert 'moved' not in row['fresh_press'], name
    checks.append(name)
assert original_failure == 'dead_bad_counter_wall_msec_MISSING reproduces false acceptance'
receipt = {
    'source_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
    'scope': 'Pure unchanged independent case inputs and actual controller AST; corrected outcome assertions',
    'unchanged_probe_sha256': hashlib.sha256(probe_path.read_bytes()).hexdigest(),
    'original_defect_reproduction_assertion_now_fails': original_failure,
    'original_case_count': 77, 'original_assertion_count': 49,
    'corrected_case_assertions': len(checks), 'all_corrected_outcomes_passed': True,
    'cases': rows}
(directory / 'independent-replay.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps({key: value for key, value in receipt.items() if key != 'cases'}))
