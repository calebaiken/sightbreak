"""Full-stream falsifier for the independently identified mandatory drop."""
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

assert sorted(os.sched_getaffinity(0)) == [4]
out = Path(sys.argv[1])
out.mkdir(exist_ok=False)
rows = copy.deepcopy(fixtures.synthetic_records())
row = [r for k, r in rows if k == 'INTERACTION' and r['label'] == 'forward_live_122'][-1]
authority = [r for k, r in rows if k == 'AUTHORITY' and r['label'] == 'forward_live_122'][-1]
victim = str(row['before']['carrier'])
for state in (row['before'], row['after'], authority['after']):
    assert state['objective'] == 'carried' and state['actors'][victim]['alive']
    actor = state['actors'][victim]
    actor.update(alive=False, health=0)
    actor['deaths'] += 1
row.update(fixtures.interaction(row['label'], row['before'], row['after']))
raw = fixtures.log(rows).encode()
packed = gzip.compress(raw, mtime=0)
(out / 'missing-drop.log.gz').write_bytes(packed)
try:
    result = reader.verify(raw.decode(), ROOT)
except (ValueError, KeyError, TypeError) as error:
    accepted, detail = False, str(error)
else:
    accepted, detail = True, result
report = {'head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
          'reader_sha256': hashlib.sha256((ROOT / 'scripts/verify_bot_objective_observation.py').read_bytes()).hexdigest(),
          'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(),
          'gzip_sha256': hashlib.sha256(packed).hexdigest(), 'accepted': accepted,
          'detail': detail, 'expected_acceptance': False, 'passed': not accepted,
          'cpu_affinity': sorted(os.sched_getaffinity(0)), 'native_executed': False}
(out / 'results.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report))
sys.exit(0 if report['passed'] else 1)
