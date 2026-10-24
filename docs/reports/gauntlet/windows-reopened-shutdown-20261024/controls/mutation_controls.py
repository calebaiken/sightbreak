#!/usr/bin/env python3
"""Pure in-memory mutation checks; no runtime controller or native helper executes."""
import ast
import io
import json
import os
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[5]
OUT = Path(__file__).resolve().parents[1]
TEST = ROOT / 'scripts/test_reopened_shutdown_diagnostic.py'
SOURCE = (ROOT / 'scripts/verify_offline_export.py').read_text()
WORKFLOW = (ROOT / '.github/workflows/desktop-alpha.yml').read_text()
assert sorted(os.sched_getaffinity(0)) == [4]


def replace_once(raw, old, new):
    assert raw.count(old) == 1, (old, raw.count(old))
    return raw.replace(old, new)


def run(name, source=SOURCE, workflow=WORKFLOW):
    namespace = {'__file__': str(TEST), '__name__': 'declared_mutation_control'}
    exec(compile(TEST.read_text(), str(TEST), 'exec'), namespace)
    namespace['SOURCE'], namespace['WORKFLOW'] = source, workflow
    namespace['TREE'] = ast.parse(source)
    namespace['MAIN'] = next(n for n in namespace['TREE'].body if isinstance(n, ast.FunctionDef) and n.name == 'main')
    output = io.StringIO()
    result = unittest.TextTestRunner(stream=output, verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(namespace['ReopenedDiagnosticTests']))
    (OUT / ('mutation-' + name + '.log')).write_text(output.getvalue())
    return dict(name=name, methods=result.testsRun, rejected=not result.wasSuccessful(),
                failures=len(result.failures), errors=len(result.errors))


rows = [run('unchanged')]
rows.append(run('default-enabled', replace_once(SOURCE, "action='store_true',", "action='store_true', default=True,")))
rows.append(run('initial-also-verbose', replace_once(SOURCE, "client_command = [str(executable), '--audio-driver', 'Dummy', *flags]", "client_command = [str(executable), '--audio-driver', 'Dummy', *flags, '--verbose']")))
rows.append(run('verbose-after-separator', replace_once(SOURCE, "*(['--verbose'] if args.reopened_verbose else []), '--',", "'--', *(['--verbose'] if args.reopened_verbose else []),")))
rows.append(run('always-verbose', replace_once(SOURCE, "*(['--verbose'] if args.reopened_verbose else []),", "*(['--verbose']),")))
rows.append(run('never-verbose', replace_once(SOURCE, "*(['--verbose'] if args.reopened_verbose else []),", "*([]),")))
rows.append(run('misspelled-engine-flag', replace_once(SOURCE, "*(['--verbose'] if args.reopened_verbose else []),", "*(['--verbos'] if args.reopened_verbose else []),")))
rows.append(run('expanded-whole-budget', replace_once(SOURCE, "default=300, help='Whole-flow", "default=600, help='Whole-flow")))
rows.append(run('adapter-all-hosts', workflow=replace_once(WORKFLOW, "runner.os == 'Windows' && inputs.verbose_reopened_shutdown", "inputs.verbose_reopened_shutdown")))
rows.append(run('adapter-default-enabled', workflow=replace_once(WORKFLOW, "verbose_reopened_shutdown:\n        description: Diagnose only reopened Windows client shutdown with engine verbose output\n        type: boolean\n        required: false\n        default: false", "verbose_reopened_shutdown:\n        description: Diagnose only reopened Windows client shutdown with engine verbose output\n        type: boolean\n        required: false\n        default: true")))
report = dict(cpu_affinity=sorted(os.sched_getaffinity(0)), cases=rows,
              passed=not rows[0]['rejected'] and all(r['rejected'] and r['errors'] == 0 for r in rows[1:]))
(OUT / 'mutation-controls.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
raise SystemExit(not report['passed'])
