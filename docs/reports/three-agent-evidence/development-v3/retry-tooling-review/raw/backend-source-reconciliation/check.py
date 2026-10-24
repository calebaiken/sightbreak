"""Read-only reconciliation after an interrupted source-transfer task."""
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(r'C:\Users\blith\AppData\Local\Temp\opencode\sightbreak-v3')
DEST = Path(__file__).with_name('results.json')
EXPECTED = {
    'backend/tests/test_trade_reads.py': '8dc8e3715dcaeb99fe6e3544243ee591d68c337b',
    'scripts/benchmark_trade_reads.py': '8dc8e3715dcaeb99fe6e3544243ee591d68c337b',
    'scripts/check_trade_read_assurance.py': '3e7ce7409322766d07afe504d97f47c5b3614875',
    'scripts/verify_trade_read_artifacts.py': '8070436f53dd98e9529e8c21ea7b0f7e3ecb6daf',
}
rows = []
for name, commit in EXPECTED.items():
    frozen = subprocess.check_output(['git', 'show', f'{commit}:{name}'], cwd=ROOT)
    path = ROOT / name
    row = {'path': name, 'expected_commit': commit,
           'expected_git_sha256': hashlib.sha256(frozen).hexdigest(), 'exists': path.is_file()}
    if path.is_file():
        actual = path.read_bytes()
        normalized = actual.replace(b'\r\n', b'\n')
        row.update(physical_sha256=hashlib.sha256(actual).hexdigest(),
                   git_normalized_sha256=hashlib.sha256(normalized).hexdigest(),
                   exact_git_bytes=actual == frozen, normalized_git_match=normalized == frozen,
                   crlf_lines=actual.count(b'\r\n'), bare_lf=actual.count(b'\n') - actual.count(b'\r\n'))
        ast.parse(actual.decode('utf-8-sig'), filename=name)
        row['ast_parsed'] = True
    rows.append(row)
report = {'utc': datetime.now(timezone.utc).isoformat(), 'python': sys.version,
          'scope': 'AST and exact Git-normalized source transfer only; no DB, pytest or benchmark execution',
          'passed': all(row.get('normalized_git_match') and row.get('ast_parsed') for row in rows),
          'rows': rows}
with DEST.open('x', encoding='utf-8') as stream:
    json.dump(report, stream, indent=2)
    stream.write('\n')
print(json.dumps(report, indent=2))
raise SystemExit(0 if report['passed'] else 1)
