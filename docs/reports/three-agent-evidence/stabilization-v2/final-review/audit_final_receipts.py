#!/usr/bin/env python3
"""Read-only evidence/source audit; no Godot, network or subprocess test execution."""
import ast
import datetime
import hashlib
import json
from pathlib import Path
import re
import subprocess

EVIDENCE = Path('/workspace/reviews/stabilization-v2-20261016')
OUT = EVIDENCE / 'final-review'
FROZEN = Path('/workspace/sightbreak-stabilization-v2-frozen-r2')
BUILD = Path('/workspace/sightbreak-stabilization-v2-builds-r2')
PRIMARY = Path('/workspace/sightbreak-three-agent')
COMMIT = '701ce2c4d7f8b2872cf1fefa64cb6edd0cd1a3fd'
GAME_TREE = '2d2b174c2145e9755ddfc78a1369e74443fcc400'
CONTENT = '12d50718f295f04d21de691f31fbde8f03612b145680aaa592ef9e6e08cd5eec'

def read_json(path):
    return json.loads(path.read_text())

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def git(root, *args):
    return subprocess.check_output(['git', *args], cwd=root, text=True).strip()

def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')

def source(root):
    digest = hashlib.sha256()
    for path in sorted((root / 'game').rglob('*')):
        relative = path.relative_to(root / 'game')
        if path.is_file() and '.godot' not in relative.parts and 'tests' not in relative.parts:
            digest.update(relative.as_posix().encode() + b'\0' + path.read_bytes() + b'\0')
    return dict(source_commit=git(root, 'rev-parse', 'HEAD'), source_game_tree=git(root, 'rev-parse', 'HEAD:game'), source_content_sha256=digest.hexdigest(), source_game_dirty=bool(git(root, 'status', '--porcelain', '--', 'game')))

expected_source = dict(source_commit=COMMIT, source_game_tree=GAME_TREE, source_content_sha256=CONTENT, source_game_dirty=False)
matrix = EVIDENCE / 'matrix-r2'
summary = read_json(matrix / 'summary.json')
rows = summary['checks']
assert len(rows) == 74 and len({r['name'] for r in rows}) == 74
assert summary['commit'] == COMMIT and summary['dirty'] is False and summary['source'] == expected_source
assert all(r['passed'] is True and r['source_commit'] == COMMIT for r in rows)
# Derive inventory from frozen runner and maintained shell-suite declarations.
expected_names = set()
for line in (FROZEN / 'scripts/validate.sh').read_text().splitlines():
    match = re.search(r'^(\s*)run_godot (\S+) (.+)$', line)
    if match:
        expected_names.add(match[2])
    elif line.startswith('SIGHTBREAK_STATE_DIR=') and 'run_godot profile ' in line:
        expected_names.add('profile')
for node in ast.walk(ast.parse((FROZEN / 'scripts/validate_matrix.py').read_text())):
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'run' and node.args and isinstance(node.args[0], ast.Constant):
        expected_names.add(node.args[0].value)
expected_names.update(['account-protocol', 'account-capacity', 'outbox-crash', 'native-economy', 'nested-resource-cleanup', 'frozen-source-identity'])
assert expected_names == {r['name'] for r in rows}, (expected_names - {r['name'] for r in rows}, {r['name'] for r in rows} - expected_names)
errors = re.compile(r'^(?:SCRIPT ERROR|ERROR:)|Parse Error|ObjectDB.*leaked|Leaked instance', re.M)
row_audit = []
for row in rows:
    path = matrix / row['log']
    assert path.is_file()
    record = dict(name=row['name'], log=row['log'], sha256=sha(path), bytes=path.stat().st_size, passed=row['passed'])
    if 'command' in row:
        text = path.read_text(errors='replace')
        assert row['exit'] == 0 and row['logged_errors'] is False
        assert not errors.search(text) and 'HARNESS_ERROR' not in text
        record.update(exit=row['exit'], seconds=row['seconds'], independently_scanned_log_clean=True)
    row_audit.append(record)
assert len([r for r in rows if 'command' in r]) == 72
assert [r['name'] for r in rows[-2:]] == ['nested-resource-cleanup', 'frozen-source-identity']
identity = read_json(matrix / 'source-identity.json')
assert identity == dict(before=expected_source, after=expected_source, initial_dirty=False, final_dirty=False)
assert read_json(matrix / 'nested-resource-cleanup.json') == dict(source_commit=COMMIT, leaked_logs=[])

leaks = []
nested_errors = []
logs = sorted(matrix.rglob('*.log'))
for path in logs:
    text = path.read_text(errors='replace')
    relative = str(path.relative_to(matrix))
    if re.search(r'ObjectDB.*leaked|Leaked instance', text):
        leaks.append(relative)
    lines = [dict(line=i, text=line) for i, line in enumerate(text.splitlines(), 1) if re.search(r'^(?:SCRIPT ERROR|ERROR:)|Parse Error|HARNESS_ERROR', line)]
    if lines:
        classification = 'unclassified'
        if relative.startswith('protocol/release-e67f2c8/docs/reports/'):
            classification = 'historical log copied from staged release source; not a fresh runtime result'
        elif 'client-current.server-release' in relative or 'client-release.server-current' in relative:
            classification = 'deliberate legacy/current protocol incompatibility; state logs duplicate process logs'
        assert classification != 'unclassified', relative
        nested_errors.append(dict(path=relative, sha256=sha(path), classification=classification, lines=lines))
assert not leaks
source_records = {}
for root in (FROZEN, BUILD):
    record = source(root)
    assert record == expected_source and git(root, 'status', '--porcelain') == ''
    source_records[str(root)] = dict(**record, tracked_clean=True)
primary_source = source(PRIMARY)
assert primary_source['source_game_tree'] == GAME_TREE and primary_source['source_content_sha256'] == CONTENT and not primary_source['source_game_dirty']

final_run = read_json(EVIDENCE / 'actions-v2-final-run.json')
assert final_run['id'] == 38858072161 and final_run['status'] == 'completed' and final_run['conclusion'] == 'success' and final_run['head_sha'] == COMMIT
ci = read_json(OUT / 'ci-receipt-audit.json')
ci.update(final_run=final_run, final_run_receipt_sha256=sha(EVIDENCE / 'actions-v2-final-run.json'), final_run_completed_success=True, earlier_in_progress_snapshot_superseded=True)
write_json(OUT / 'ci-receipt-audit.json', ci)

verbatim = []
for old in read_json(OUT / 'verbatim-audit.json'):
    rel = old['path']
    external = (EVIDENCE / rel).read_bytes()
    primary_rel = Path('docs/reports/three-agent-evidence/stabilization-v2') / rel
    work = (PRIMARY / primary_rel).read_bytes()
    committed = subprocess.check_output(['git', 'show', 'HEAD:' + primary_rel.as_posix()], cwd=PRIMARY)
    assert external == work == committed
    verbatim.append(dict(path=rel, sha256=hashlib.sha256(external).hexdigest(), external_equals_working_equals_committed=True))

heads = read_json(EVIDENCE / 'final-source-heads.json')
pr14 = next(p for p in heads['pull_requests'] if p['number'] == 14)
compare = read_json(EVIDENCE / 'gemini-after-freeze-compare.json')
assert pr14['head'] == '48eb0586e273f96dc20b346ed444d00ab0f3ac30' and compare['ahead_by'] == 2
assert compare['commits'][-1]['sha'] == pr14['head']
report = PRIMARY / 'docs/reports/STABILIZATION_V2_REPORT.md'
text = report.read_text()
assert all(needle in text for needle in ['74/74 PASS', '64/70', '48eb058', 'not integrated or independently validated', 'wrapper', 'unexplained', '0.3.0-dev', '0.3.1-dev', '5.5–6/10', '14/60 → 15/59', '08-settled.png'])

record = dict(audited_at=datetime.datetime.now(datetime.timezone.utc).isoformat(), read_only=True, no_engine_runs=True, source=expected_source, frozen_worktrees=source_records, primary_source=primary_source, completed_groups=len(rows), command_groups=72, final_audit_groups=2, failed=[], expected_inventory_matches_frozen_runner=True, rows=row_audit, summary_sha256=sha(matrix / 'summary.json'), source_identity_sha256=sha(matrix / 'source-identity.json'), nested_log_count=len(logs), objectdb_or_leaked_instance_logs=leaks, nested_ordinary_error_classification=nested_errors, final_ci_run=final_run, verbatim_reports=verbatim, final_source_heads=dict(receipt_sha256=sha(EVIDENCE / 'final-source-heads.json'), gemini_pr14=pr14, compare_sha256=sha(EVIDENCE / 'gemini-after-freeze-compare.json'), after_freeze_changes_integrated_or_validated=False), primary_report=dict(sha256=sha(report), reviewed_lines=len(text.splitlines()), acceptance_qualifications_present=True), qualifications=['New 74/74 campaign does not rewrite historical 64/70 or unsuccessful attempts.', 'Unexplained broad-wrapper audio-cancel baseline failure remains retained; later passes do not recover discarded raw cause.', 'Legacy/current protocol negative diagnostics and copied historical logs contain ERROR lines; no universal error-free claim.', 'Tactical and visual 8.5 gates remain failed; physical devices, public Internet, listening quality, production readiness are not established.', 'Static menu 0.3.0-dev banner remains stale relative to 0.3.1-dev/build4 metadata.', 'CI receipts and supported download audited; no additional CI aggregate byte download/rehash performed by this reviewer.'])
write_json(OUT / 'matrix-final-audit.json', record)
print(json.dumps({k:record[k] for k in ['completed_groups','command_groups','final_audit_groups','failed','nested_log_count','objectdb_or_leaked_instance_logs','summary_sha256']},indent=2))
