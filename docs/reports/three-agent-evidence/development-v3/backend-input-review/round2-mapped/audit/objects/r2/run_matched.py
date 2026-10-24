from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys
import time

root = Path(__file__).resolve().parent
repo = Path('C:/Users/blith/AppData/Local/Temp/opencode/sightbreak-backend-trade-read-v3')
baseline = Path('C:/Users/blith/AppData/Local/Temp/opencode/sightbreak-v2-baseline')
env = os.environ.copy()
env['SIGHTBREAK_TEST_ADMIN_URL'] = 'postgresql://sightbreak:sightbreak_local_only@127.0.0.1:55439/postgres'
env['PYTHONDONTWRITEBYTECODE'] = '1'
records = []
for label, source, runtime in [('baseline', baseline, '701ce2c'), ('candidate', repo, '4a8e9ea')]:
    command = [sys.executable, '-B', str(repo / 'scripts/benchmark_trade_reads.py'),
               '--source', str(source), '--runtime-reference', runtime,
               '--out', str(root / label), '--samples', '10']
    start = time.monotonic()
    with (root / (label + '-console.log')).open('w', encoding='utf-8') as log:
        result = subprocess.run(command, cwd=repo, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=600)
    records.append({'label': label, 'command': command, 'exit': result.returncode,
                    'seconds': time.monotonic() - start})
    (root / 'runs.json').write_text(json.dumps(records, indent=2) + '\n')
    print((root / (label + '-console.log')).read_text(), flush=True)
    result.check_returncode()
    verify = [sys.executable, '-B', str(repo / 'scripts/verify_trade_read_artifacts.py'), str(root / label)]
    with (root / (label + '-verification.json')).open('w', encoding='utf-8') as log:
        checked = subprocess.run(verify, cwd=repo, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=60)
    print((root / (label + '-verification.json')).read_text(), flush=True)
    checked.check_returncode()
