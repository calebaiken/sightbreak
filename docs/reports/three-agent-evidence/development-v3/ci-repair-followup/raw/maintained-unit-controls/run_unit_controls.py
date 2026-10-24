"""Retain actual isolated unit results; this is not native/export acceptance."""
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(r'C:\Users\blith\AppData\Local\Temp\opencode\sightbreak-v3')
OUT = Path(__file__).parent / ('units-' + datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
OUT.mkdir()


def hashes():
    return {path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted((ROOT / 'scripts').glob('*.py'))}


result = {'scope': 'Pure/synthetic controller and matrix unit repairs on uncommitted integration; no native client or Linux acceptance',
          'python': sys.version, 'source_before': hashes(), 'suites': []}
for name in ('test_validate_matrix.py', 'test_export_ui.py', 'test_offline_hud.py', 'test_export_flow.py'):
    command = [sys.executable, '-X', 'faulthandler', str(ROOT / 'scripts' / name), '-v']
    with (OUT / (name + '.log')).open('xb') as log:
        run = subprocess.run(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, timeout=180)
    result['suites'].append({'command': command, 'actual_exit': run.returncode, 'log': name + '.log'})
result['source_after'] = hashes()
result['passed'] = (result['source_before'] == result['source_after']
                    and all(row['actual_exit'] == 0 for row in result['suites']))
(OUT / 'results.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'output': str(OUT), 'passed': result['passed'], 'suites': result['suites']}, indent=2))
raise SystemExit(0 if result['passed'] else 1)
