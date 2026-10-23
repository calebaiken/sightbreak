#!/usr/bin/env python3
"""Pure review of the concrete verbose controller; never imports or runs it."""
import ast
import hashlib
import json
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[5]
OLD='700abf8c9d43279518c5257edfdbaee513569cea'
NEW='817516a'
PREFIX='docs/reports/gauntlet/m5-exhausted-primary-verbose-diagnostic/'
SOURCE=Path('/workspace/sightbreak-exhausted-primary-verbose-r2')

def git(*args,cwd=ROOT):return subprocess.check_output(['git',*args],cwd=cwd)
def sha(data):return hashlib.sha256(data).hexdigest()

def audit():
    old=git('show',OLD+':docs/reports/gauntlet/m5-exhausted-primary-benchmark/actual-r2/run_once.py').decode()
    new=git('show',NEW+':'+PREFIX+'run_verbose_once.py').decode()
    expected=old
    edits=[
        ('One staged import, then at most one frozen baseline, with retained receipts.','One fresh verbose leak diagnostic; it never replaces baseline acceptance.'),
        ("SOURCE = Path('/workspace/sightbreak-exhausted-primary-benchmark')","SOURCE = Path('/workspace/sightbreak-exhausted-primary-verbose-r2')"),
        ("               'engine': str(ENGINE),", "               'diagnostic_purpose': 'Identify only this unchanged verbose run leaked object types; no acceptance replacement',\n               'original_failed_baseline_evidence': '700abf8c9d43279518c5257edfdbaee513569cea',\n               'engine': str(ENGINE),"),
        ("overall['import_qualified_to_attempt_baseline']", "overall['import_qualified_to_attempt_diagnostic']"),
        ("overall['baseline'] = run_phase('baseline-probe', [str(ENGINE), '--headless',", "overall['verbose_diagnostic'] = run_phase('verbose-diagnostic-probe', [str(ENGINE), '--headless', '--verbose',"),
        ("overall['baseline'] = None", "overall['verbose_diagnostic'] = None"),
        ("overall['baseline_skipped_reason']", "overall['diagnostic_skipped_reason']")]
    for before,after in edits:
        assert expected.count(before)==1,before
        expected=expected.replace(before,after)
    assert new==expected,'unexpected controller byte change'
    old_ast,new_ast=ast.parse(old),ast.parse(new)
    functions={node.name:ast.dump(node,include_attributes=False) for node in old_ast.body if isinstance(node,ast.FunctionDef) and node.name!='main'}
    fresh={node.name:ast.dump(node,include_attributes=False) for node in new_ast.body if isinstance(node,ast.FunctionDef) and node.name!='main'}
    assert functions==fresh,'helper AST changed'
    assert sha(new.encode())=='43dfdeae51aaa95dbb43aeb33125c772688f50e604cc471c8b4ba0309734c7fe'
    assert git('rev-parse','HEAD',cwd=SOURCE).decode().strip()=='b87afb717bf09a78c6d36b164d48906902734bdb'
    assert git('status','--porcelain',cwd=SOURCE)==b''
    paths=git('ls-tree','-r','--name-only','HEAD','game',cwd=SOURCE).decode().splitlines()
    for path in paths:
        assert (SOURCE/path).read_bytes()==git('show','HEAD:'+path,cwd=SOURCE),path
    assert len(paths)==324
    assert sha((SOURCE/'game/tests/bot_exhausted_primary_probe.gd').read_bytes())=='540d24dda8e58f4685030e81b55ac3778ccbf31a89f76f9873ac598c32770731'
    return dict(verdict='ACCEPT source/method support for root to release exactly one verbose diagnostic',controller_commit=git('rev-parse',NEW).decode().strip(),controller_sha256=sha(new.encode()),exact_allowed_replacements=len(edits),unchanged_helper_asts=sorted(functions),fresh_source_game_files_verified=324,phase_cap_seconds=120,whole_wrapper_cap_seconds=240,original_strict_verdict='REJECT',native_execution_by_critic=False,scope='Only --verbose is added to the probe engine argv; source path, diagnostic labels/provenance change; import and all guards/cleanup unchanged. No acceptance replacement or retrospective leaked-type attribution.')

if __name__=='__main__':print(json.dumps(audit(),indent=2,sort_keys=True))
