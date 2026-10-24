"""Derive and execute every maintained pure unittest group; no engine."""
import ast
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys

OUT = Path(__file__).resolve().parent
ROOT = Path(sys.argv[1]).resolve()
LABEL = sys.argv[2]
assert sorted(os.sched_getaffinity(0)) == [4]
commands, excluded = [], []
for number, raw in enumerate((ROOT / 'scripts/validate.sh').read_text().splitlines(), 1):
    if not raw.startswith('python3 '):
        continue
    args = shlex.split(raw.split('|', 1)[0])
    if args[1:3] == ['-m', 'unittest']:
        commands.append({'line': number, 'declared': raw, 'argv': [sys.executable, *args[1:]], 'scope': 'maintained'})
    elif args[1].endswith('.py'):
        tree = ast.parse((ROOT / args[1]).read_text())
        is_unittest = any(isinstance(n, ast.Import) and any(a.name == 'unittest' for a in n.names) for n in ast.walk(tree))
        if is_unittest:
            commands.append({'line': number, 'declared': raw, 'argv': [sys.executable, *args[1:]], 'scope': 'maintained'})
        else:
            excluded.append({'line': number, 'declared': raw, 'reason': 'non-unittest helper; native fixture/lifecycle scope not executed in source-only review'})
assert len(commands) == 14, commands
for group in ('test_native_approach', 'test_macos_menu'):
    commands.append({'declared': f'python3 scripts/{group}.py -v', 'argv': [sys.executable, f'scripts/{group}.py', '-v'], 'scope': 'additional default/Mac component'})
results = []
for index, row in enumerate(commands):
    command = row['argv']
    label = 'server-discover' if command[1] == '-m' else Path(command[1]).stem
    env = dict(os.environ, GIT_NO_LAZY_FETCH='1')
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, env=env)
    raw = result.stdout + result.stderr
    log = OUT / f'{LABEL}-{label}.log'
    log.write_text(raw)
    count = re.search(r'Ran (\d+) tests?', raw)
    skipped = re.search(r'OK \(skipped=(\d+)\)', raw)
    results.append({**row, 'cwd': str(ROOT), 'exit': result.returncode,
                    'methods': int(count[1]) if count else None, 'skips': int(skipped[1]) if skipped else 0,
                    'log': log.name, 'sha256': hashlib.sha256(log.read_bytes()).hexdigest()})
    print(label, result.returncode, results[-1]['methods'], 'skips', results[-1]['skips'], flush=True)
shell = subprocess.run(['bash', '-n', 'scripts/validate.sh'], cwd=ROOT, capture_output=True, text=True, env=dict(os.environ, GIT_NO_LAZY_FETCH='1'))
(OUT / f'{LABEL}-shell-syntax.log').write_text(shell.stdout + shell.stderr)
maintained = [r for r in results if r['scope'] == 'maintained']
additional = [r for r in results if r['scope'] != 'maintained']
report = {'source': '49ae54b0e4f5d880bdf06e4eb783a616b2dff684', 'label': LABEL,
          'cpu_affinity': sorted(os.sched_getaffinity(0)), 'no_lazy_fetch': True,
          'results': results, 'excluded_non_unittest': excluded, 'shell_syntax_exit': shell.returncode,
          'maintained_group_count': len(maintained), 'maintained_method_count': sum(r['methods'] or 0 for r in maintained),
          'additional_group_count': len(additional), 'additional_method_count': sum(r['methods'] or 0 for r in additional),
          'skips': sum(r['skips'] for r in results)}
(OUT / f'{LABEL}-pure-results.json').write_text(json.dumps(report, indent=2) + '\n')
sys.exit(shell.returncode or any(r['exit'] or r['methods'] is None for r in results))
