"""Preregistered historical baseline ONLY; never candidate qualification."""
import ast
from copy import deepcopy
import hashlib
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'scripts'))
CAPTURED = ROOT / 'docs/reports/gauntlet/windows-input-reader-foundation-20261024/legacy-source/scripts'
EXPECTED = {
    'analyze_input_consumption.py': 'd2cab3af7e441615a37caedb259b1311eb0b5b1cde46719c1000181223facba1',
    'test_input_consumption_observation.py': '9f81e903c5932ab1762f347ae400f45ae7b928c29abf3d9f719eb6e7141ead8c',
}
sources = {}
for name, sha in EXPECTED.items():
    raw = (CAPTURED / name).read_bytes()
    if hashlib.sha256(raw).hexdigest() != sha:
        raise RuntimeError('captured baseline hash mismatch: ' + name)
    sources[name] = raw
reader = types.ModuleType('frozen_preedit_reader')
reader.__file__ = str(CAPTURED / 'analyze_input_consumption.py')
exec(compile(sources['analyze_input_consumption.py'], reader.__file__, 'exec'), reader.__dict__)
parsed = ast.parse(sources['test_input_consumption_observation.py'])
constructors = [node for node in parsed.body
                if isinstance(node, ast.FunctionDef) and node.name in {'control', 'declared_rows'}]
if len(constructors) != 2:
    raise RuntimeError('captured baseline constructors ambiguous')
namespace = {'deepcopy': deepcopy}
exec(compile(ast.Module(body=constructors, type_ignores=[]), '<frozen constructors>', 'exec'), namespace)
import test_input_consumption_foundation_model as tests

with patch.multiple(tests, analyze=reader.analyze, declared_rows=namespace['declared_rows']):
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
raise SystemExit(0 if result.wasSuccessful() else 1)
