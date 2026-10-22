#!/usr/bin/env python3
"""Check original observer fences and retained measurement bytes without OCR."""
import ast
import csv
import gzip
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile

root = Path(sys.argv[1]).resolve()
evidence = root / 'docs/reports/gauntlet/native-layout-timeout'
digest = lambda value: hashlib.sha256(value).hexdigest()
original = ast.parse(subprocess.check_output(['git', 'show', '7d46d2e:scripts/capture_desktop_layouts.py'], cwd=root))
candidate = ast.parse((root / 'scripts/capture_desktop_layouts.py').read_bytes())
original_case = next(node for node in original.body if isinstance(node, ast.FunctionDef) and node.name == 'capture_case')
candidate_case = next(node for node in candidate.body if isinstance(node, ast.FunctionDef) and node.name == 'capture_case')
old_analyze = next(node for node in original_case.body if isinstance(node, ast.FunctionDef) and node.name == 'analyze')
new_analyze = next(node for node in candidate_case.body if isinstance(node, ast.FunctionDef) and node.name == 'analyze')
assert ast.dump(old_analyze.args) == ast.dump(new_analyze.args)
# Preprocessing, PSM command and remaining-budget calculations are identical.
old_budget_end = next(i for i, node in enumerate(old_analyze.body) if isinstance(node, ast.With) and 'ocr-stderr.log' in ast.dump(node))
new_budget_end = next(i for i, node in enumerate(new_analyze.body) if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == 'receipt' for target in node.targets))
assert [ast.dump(node) for node in old_analyze.body[:old_budget_end]] == [ast.dump(node) for node in new_analyze.body[:new_budget_end]]
# Return-code failure, raw TSV retention and coordinate parsing are identical.
old_tail = next(i for i, node in enumerate(old_analyze.body) if isinstance(node, ast.If) and 'completed' in ast.dump(node.test))
new_tail = next(i for i, node in enumerate(new_analyze.body) if isinstance(node, ast.If) and 'completed' in ast.dump(node.test))
assert [ast.dump(node) for node in old_analyze.body[old_tail:]] == [ast.dump(node) for node in new_analyze.body[new_tail:]]
original_case.body = [node for node in original_case.body if node is not old_analyze]
candidate_case.body = [node for node in candidate_case.body if node is not new_analyze]
candidate.body = [node for node in candidate.body if not isinstance(node, ast.FunctionDef) or node.name != 'run_layout_ocr']
assert ast.dump(original) == ast.dump(candidate)

index = json.loads((evidence / 'EVIDENCE_INDEX.json').read_text())
for entry in index['files']:
    value = (evidence / entry['path']).read_bytes()
    assert len(value) == entry['bytes'] and digest(value) == entry['sha256'], entry['path']
assert digest((root / 'scripts/capture_desktop_layouts.py').read_bytes()) == index['production_script_sha256']

startup = json.loads(gzip.decompress((evidence / 'startup-repetition/results.json.gz').read_bytes()))
with tarfile.open(evidence / 'startup-repetition/raw-ocr-output.tar.gz') as archive:
    members = archive.getmembers()
    assert len(members) == len({member.name for member in members})
    assert all(member.isfile() for member in members)
    retained = {member.name: archive.extractfile(member).read() for member in members}
for trial in startup['trials']:
    raw_tsv = gzip.decompress(retained[trial['label'] + '.tsv.gz'])
    assert digest(raw_tsv) == trial['tsv_sha256']
    assert trial['words'] == [row['text'] for row in csv.DictReader(io.StringIO(raw_tsv.decode()), delimiter='\t') if row.get('text', '').strip()]
    assert trial['exit_code'] == 0 and trial['error'] is None
for case in startup['cases']:
    value = (root / case['prior_native_original']).read_bytes()
    assert digest(value) == case['original_sha256']
    ci = json.loads(gzip.decompress((evidence / 'native-ci-39719407304' / (case['size'] + '-results.json.gz')).read_bytes()))
    completed = [entry for entry in ci['ocr_commands'] if entry['original_sha256'] == digest(value)]
    assert len(completed) == case['completed_matching_ci_calls']
    assert len(completed) - 1 == case['repeat_calls_after_first']
    selected = [trial for trial in startup['trials'] if trial['size'] == case['size']]
    assert len(selected) == 6 and len({trial['analysis_sha256'] for trial in selected}) == 1
    assert len({trial['tsv_sha256'] for trial in selected}) == 1
report = {'scope': 'Static fence audit and retained measurement recomputation; no OCR or native generation.',
          'frozen_candidate': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip(),
          'all_other_production_ast_identical': True,
          'analysis_preprocessing_command_and_budget_ast_identical': True,
          'return_code_tsv_and_coordinate_parsing_ast_identical': True,
          'evidence_index_entries_verified': len(index['files']), 'startup_trials_verified': len(startup['trials']),
          'startup_cases_verified': len(startup['cases']),
          'repeated_completed_ci_calls_after_first': sum(case['repeat_calls_after_first'] for case in startup['cases'])}
print(json.dumps(report, indent=2))
