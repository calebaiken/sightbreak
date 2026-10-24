#!/usr/bin/env python3
"""Pinned pure grammar parser only; never Godot compilation/type/API validation."""
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys

parser_args = argparse.ArgumentParser()
parser_args.add_argument('--source', type=Path, required=True)
parser_args.add_argument('--tool-root', type=Path, required=True)
parser_args.add_argument('--output', type=Path, required=True)
args = parser_args.parse_args()
if sorted(os.sched_getaffinity(0)) != [4] or args.output.exists():
    raise RuntimeError('CPU 4 and a fresh grammar output are required')
sys.path.insert(0, str(args.tool_root.resolve()))
from gdtoolkit.parser import parser
if importlib.metadata.version('gdtoolkit') != '4.3.4':
    raise RuntimeError('The inspected pure grammar version must remain pinned')
parser.disable_grammar_caching()
report = {'scope': 'Pure GDScript grammar only; no Godot compilation, type/API or runtime validation',
          'source': subprocess.check_output(['git', '-C', str(args.source), 'rev-parse', 'HEAD'], text=True).strip(),
          'cpu_affinity': sorted(os.sched_getaffinity(0)), 'gdtoolkit': importlib.metadata.version('gdtoolkit'),
          'lark': importlib.metadata.version('lark'), 'files': []}
for name in ['game/scripts/gameplay/match.gd', 'game/tests/movement_prediction_test.gd', 'scripts/fixtures/export_integration.gd']:
    raw = (args.source / name).read_bytes()
    tree = parser.parse(raw.decode(), gather_metadata=True)
    report['files'].append({'path': name, 'sha256': hashlib.sha256(raw).hexdigest(), 'parsed': True, 'root': str(tree.data)})
args.output.write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
