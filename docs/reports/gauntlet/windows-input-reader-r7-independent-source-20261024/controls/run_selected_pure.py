#!/usr/bin/env python3
"""Run pure modules in process; omit server process and Mac groups by scope."""
import argparse
import contextlib
import hashlib
import importlib
import io
import json
import os
from pathlib import Path
import sys
import unittest

p = argparse.ArgumentParser()
p.add_argument('--source', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
root, output = a.source.resolve(), a.output.resolve()
assert sorted(os.sched_getaffinity(0)) == [4]
output.mkdir(parents=True, exist_ok=False)
os.chdir(root)
sys.path.insert(0, str(root / 'scripts'))
names = ['transaction_restart_oracle', 'account_network_output', 'account_match_output',
         'build_manifest', 'native_log', 'native_observation', 'offline_role_guidance',
         'offline_export_ocr', 'offline_capture_fences', 'native_focus_fence',
         'focus_resume_timing', 'native_settings_route', 'native_route_pulse',
         'input_consumption_observation', 'native_approach', 'input_consumption_identity',
         'input_consumption_lifecycle', 'input_consumption_state', 'input_consumption_stream',
         'input_consumption_transitions', 'input_consumption_receipts',
         'input_consumption_expiry', 'input_consumption_absorbing']
rows = []
for name in names:
    stdout, stderr = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        module = importlib.import_module('test_' + name)
        suite = unittest.defaultTestLoader.loadTestsFromModule(module)
        result = unittest.TextTestRunner(stream=stderr, verbosity=2).run(suite)
    for stream, value in [('stdout', stdout.getvalue()), ('stderr', stderr.getvalue())]:
        (output / (name + '.' + stream)).write_text(value)
    rows.append(dict(name=name, methods=result.testsRun, failures=len(result.failures),
                     errors=len(result.errors), skips=len(result.skipped),
                     stdout_sha256=hashlib.sha256(stdout.getvalue().encode()).hexdigest(),
                     stderr_sha256=hashlib.sha256(stderr.getvalue().encode()).hexdigest()))
report = dict(source=str(root), cpu_affinity=sorted(os.sched_getaffinity(0)), rows=rows,
              methods=sum(x['methods'] for x in rows), skips=sum(x['skips'] for x in rows),
              failures=sum(x['failures'] for x in rows), errors=sum(x['errors'] for x in rows),
              excluded_builder_groups={'server':11, 'macos_menu':11},
              scope='Selected inherited modules plus transition/receipt suites; excludes server process fixture and all Mac groups; no full maintained-union claim')
(output / 'SUMMARY.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k != 'rows'}, sort_keys=True))
sys.exit(bool(report['failures'] or report['errors']))
