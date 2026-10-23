#!/usr/bin/env python3
"""Pure in-memory analyzer mutation controls; never native receipts."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

if sorted(os.sched_getaffinity(0)) != [4]:
    raise RuntimeError('Pure mutations require CPU 4')
output = Path(sys.argv[1])
output.mkdir(parents=True, exist_ok=False)
source = Path('scripts/analyze_input_consumption.py')
before = source.read_bytes()
cases = [
    ('privacy_projection_removed', None, 'test_unexpected_private_payload_or_other_actor_fields_are_rejected'),
    ('retired_binding_guard_removed', 'input stage has no current observed peer-generation binding', 'test_retired_generation_cannot_consume_even_when_actor_id_is_reused'),
    ('stage_freshness_removed', 'input stage refers to stale metadata', 'test_stale_epoch_or_stale_latest_metadata_never_qualifies_an_input_stage'),
    ('direct_event_requirement_removed', 'missing direct pipeline event records', 'test_missing_direct_event_cannot_be_replaced_by_counter_claim'),
    ('truncation_guard_removed', 'observer reached its hard cap; evidence truncated', 'test_truncation_and_mixed_roles_are_rejected'),
]
report = {'scope': 'Synthetic pure analyzer mutations; expected failed tests are retained', 'source': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(), 'cpu_affinity': [4], 'analyzer_sha256': hashlib.sha256(before).hexdigest(), 'cases': []}
for name, message, method in cases:
    code = '''import sys,unittest
sys.path.insert(0,"scripts")
import analyze_input_consumption as oracle
from test_input_consumption_observation import InputConsumptionControls
message=__MESSAGE__
if message is None:
    oracle.record_valid=lambda row: None
else:
    original=oracle.need
    oracle.need=lambda ok,actual: None if actual==message else original(ok,actual)
print("SYNTHETIC_MUTATION_CONTROL "+__NAME__,flush=True)
result=unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite([InputConsumptionControls(__METHOD__)]))
raise SystemExit(not result.wasSuccessful())
'''.replace('__MESSAGE__', repr(message)).replace('__NAME__', repr(name)).replace('__METHOD__', repr(method))
    result = subprocess.run([sys.executable, '-c', code], capture_output=True, timeout=30)
    raw = result.stdout + result.stderr
    (output / (name + '.log')).write_bytes(raw)
    report['cases'].append({'mutation': name, 'test': method, 'exit_code': result.returncode, 'rejected': result.returncode == 1, 'log_sha256': hashlib.sha256(raw).hexdigest()})
if source.read_bytes() != before:
    raise RuntimeError('Mutation changed source bytes')
report['all_rejected'] = all(case['rejected'] for case in report['cases'])
report['source_unchanged'] = True
(output / 'results.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
raise SystemExit(not report['all_rejected'])
