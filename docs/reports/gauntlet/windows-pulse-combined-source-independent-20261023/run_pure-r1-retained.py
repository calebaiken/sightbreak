"""Run pure groups only; record raw merged logs and exact-source identity."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

OUT = Path(__file__).resolve().parent
ROOT = Path(sys.argv[1]).resolve()
LABEL = sys.argv[2]
GROUPS = ['test_build_manifest', 'test_native_log', 'test_native_observation',
          'test_offline_role_guidance', 'test_offline_export_ocr', 'test_offline_capture_fences',
          'test_native_focus_fence', 'test_focus_resume_timing', 'test_native_settings_route',
          'test_native_route_pulse', 'test_native_approach', 'test_macos_menu']
assert sorted(os.sched_getaffinity(0)) == [4]
results = []
for group in GROUPS:
    command = [sys.executable, f'scripts/{group}.py', '-v']
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    raw = result.stdout + result.stderr
    log = OUT / f'{LABEL}-{group}.log'
    log.write_text(raw)
    count = re.search(r'Ran (\d+) tests?', raw)
    skipped = re.search(r'OK \(skipped=(\d+)\)', raw)
    results.append({'command': command, 'cwd': str(ROOT), 'exit': result.returncode,
                    'methods': int(count[1]) if count else None, 'skips': int(skipped[1]) if skipped else 0,
                    'log': log.name, 'sha256': hashlib.sha256(log.read_bytes()).hexdigest()})
    print(group, result.returncode, results[-1]['methods'], 'skips', results[-1]['skips'], flush=True)
shell = subprocess.run(['bash', '-n', 'scripts/validate.sh'], cwd=ROOT, capture_output=True, text=True)
(OUT / f'{LABEL}-shell-syntax.log').write_text(shell.stdout + shell.stderr)
results.append({'command': ['bash', '-n', 'scripts/validate.sh'], 'exit': shell.returncode, 'methods': 0, 'skips': 0})
report = {'source': '49ae54b0e4f5d880bdf06e4eb783a616b2dff684', 'label': LABEL,
          'cpu_affinity': sorted(os.sched_getaffinity(0)), 'results': results,
          'method_count': sum(r['methods'] or 0 for r in results), 'skips': sum(r['skips'] for r in results)}
(OUT / f'{LABEL}-pure-results.json').write_text(json.dumps(report, indent=2) + '\n')
sys.exit(any(r['exit'] or r['methods'] is None for r in results))
