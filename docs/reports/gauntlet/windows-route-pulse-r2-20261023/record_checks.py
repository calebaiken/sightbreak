"""Short pure/source replay only; no native dispatch or historical fixture test dependency."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[3]
CANDIDATE = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT
PREFIX = sys.argv[2] if len(sys.argv) > 2 else 'pure'
GROUPS = ['test_native_route_pulse', 'test_native_settings_route', 'test_native_approach',
          'test_native_focus_fence', 'test_focus_resume_timing', 'test_offline_capture_fences',
          'test_macos_menu', 'test_native_observation', 'test_offline_export_ocr']
rows = []
for name in GROUPS:
    command = [sys.executable, 'scripts/' + name + '.py', '-v']
    result = subprocess.run(command, cwd=CANDIDATE, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    payload = result.stdout.encode()
    target = OUT / (PREFIX + '-' + name + '.log')
    target.write_bytes(payload)
    ran = re.search(r'Ran (\d+) tests?', result.stdout)
    skipped = re.search(r'skipped=(\d+)', result.stdout)
    rows.append({'command': command, 'cwd': str(CANDIDATE), 'exit': result.returncode,
                 'methods': int(ran[1]) if ran else None, 'skips': int(skipped[1]) if skipped else 0,
                 'log': target.name, 'sha256': hashlib.sha256(payload).hexdigest()})
receipt = {'source_freeze': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=CANDIDATE, text=True).strip(),
           'is_shallow': subprocess.check_output(['git', 'rev-parse', '--is-shallow-repository'], cwd=CANDIDATE, text=True).strip(),
           'history_commits': int(subprocess.check_output(['git', 'rev-list', '--count', 'HEAD'], cwd=CANDIDATE)),
           'reports_materialized': (CANDIDATE / 'docs/reports').exists(), 'pure_only': True,
           'methods': sum(row['methods'] or 0 for row in rows), 'skips': sum(row['skips'] for row in rows), 'checks': rows}
(OUT / (PREFIX + '-checks.json')).write_text(json.dumps(receipt, indent=2) + '\n')
assert all(row['exit'] == 0 and row['methods'] is not None for row in rows), rows
print(json.dumps({'methods': receipt['methods'], 'skips': receipt['skips'], 'all_groups_pass': True}))
