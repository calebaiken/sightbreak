"""Retain real verifier outcomes for the independently specified decision cases."""
import copy
import gzip
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'scripts'))
import test_bot_objective_observation as fixtures
import verify_bot_objective_observation as reader

out = Path(sys.argv[1])
out.mkdir(exist_ok=False)
assert sorted(os.sched_getaffinity(0)) == [4]
base = fixtures.synthetic_records()
cases = [('positive', copy.deepcopy(base), None)]

rows = copy.deepcopy(base)
next(r for k, r in rows if k == 'CALL' and r['case'] == 'live_complete')['output']['decision']['actor_id'] = 7
cases.append(('wrong_actor', rows, 'freshness call describes another actor'))
rows = copy.deepcopy(base)
next(r for k, r in rows if k == 'CALL' and r['case'] == 'direct_perception')['output']['target_id'] = 10
cases.append(('unperceived_target', rows, 'direct perception selected an unperceived target'))
rows = copy.deepcopy(base)
row = next(r for k, r in rows if k == 'DECISION' and r['label'] == 'control_defuse')
row['observation']['plan']['destination'] = [999, 0, 999]
row['observation']['decision']['destination'] = [999, 0, 999]
cases.append(('wrong_defuser_destination', rows, 'defuser destination contradicts device'))
rows = copy.deepcopy(base)
next(r for k, r in rows if k == 'DECISION' and r['label'] == 'pose_122')['observation']['decision']['role'] = 'invented_role_not_in_source'
cases.append(('invented_role', rows, 'typed decision roles'))

results = []
for name, rows, expected_error in cases:
    raw = fixtures.log(rows).encode()
    path = out / (name + '.log.gz')
    path.write_bytes(gzip.compress(raw, mtime=0))
    try:
        reader.verify(raw.decode(), ROOT)
    except (ValueError, KeyError, TypeError) as error:
        accepted, detail = False, str(error)
    else:
        accepted, detail = True, None
    results.append({'name': name, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(),
                    'gzip_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                    'accepted': accepted, 'error': detail,
                    'expected_error': expected_error,
                    'passed': accepted if expected_error is None else not accepted and expected_error == detail})
report = {'source': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
          'cpu_affinity': sorted(os.sched_getaffinity(0)), 'source_audit': reader.source_audit(ROOT),
          'cases': results, 'passed': all(row['passed'] for row in results),
          'remaining_eight_trace_defects_block_readiness': True, 'native_executed': False}
(out / 'results.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report))
sys.exit(0 if report['passed'] else 1)
