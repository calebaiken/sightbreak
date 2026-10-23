#!/usr/bin/env python3
"""Reproduce this source/pure review; never compile or call native services."""
import ast
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import tempfile
import time
import zipfile

ROOT = Path(__file__).resolve().parents[5]
OUT = Path(__file__).resolve().parent
FREEZE = 'cbd01547a5f0b2a435fa2c24a827468a963535aa'
BASE = 'c08889b8c1118c89e83c151079df4dc224076760'
HANDOFF = 'a282b3f55c4014072144f3184e91fbefbafc0077'
SOURCE_PATHS = ['.github/workflows/desktop-alpha.yml', 'scripts/macos_deploy_ocr.py',
                'scripts/macos_ordinary_input.py', 'scripts/macos_window_capture.swift',
                'scripts/test_macos_deploy_ocr.py', 'scripts/test_macos_ordinary_controller.py',
                'scripts/verify_macos_ordinary.py']
SUITES = ['test_macos_ordinary', 'test_macos_ordinary_controller', 'test_macos_ordinary_paths',
          'test_macos_ordinary_startup', 'test_macos_deploy_ocr', 'test_macos_menu',
          'test_macos_focus', 'test_macos_screen_identity', 'test_probe_macos_input']
commands = []


def sha(data): return hashlib.sha256(data).hexdigest()


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


def execute(label, arguments, expected=0, env=None):
    started = time.monotonic()
    run = subprocess.run(arguments, cwd=ROOT, env=env, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, timeout=60)
    path = OUT / 'pure' / (label + '.txt')
    path.parent.mkdir(exist_ok=True)
    path.write_bytes(run.stdout)
    tests = re.search(rb'Ran (\d+) tests? in ', run.stdout)
    row = {'label': label, 'command': arguments, 'exit_code': run.returncode,
           'expected_exit_code': expected, 'seconds': time.monotonic() - started,
           'tests': int(tests[1]) if tests else None, 'log': str(path.relative_to(OUT)),
           'bytes': len(run.stdout), 'sha256': sha(run.stdout)}
    commands.append(row)
    assert run.returncode == expected, row
    if expected == 1:
        assert b'FAIL:' in run.stdout and b'AssertionError' in run.stdout, row
        row['assertion_failure_observed'] = True
    return row


def functions(source):
    tree = ast.parse(source)
    return {node.name: ast.dump(node, include_attributes=False)
            for node in tree.body if isinstance(node, (ast.FunctionDef, ast.ClassDef))}


def assignments(source, names):
    return {node.targets[0].id: ast.literal_eval(node.value) for node in ast.parse(source).body
            if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id in names}


def source_audit():
    paths = git('diff', '--name-only', BASE, FREEZE, '--', 'scripts', '.github', 'game').decode().splitlines()
    assert sorted(paths) == sorted(SOURCE_PATHS), paths
    hashes = {}
    for path in SOURCE_PATHS:
        current = (ROOT / path).read_bytes()
        assert current == git('show', FREEZE + ':' + path)
        assert current == git('show', HANDOFF + ':' + path)
        hashes[path] = sha(current)
    path = 'scripts/macos_window_capture.swift'
    old = git('show', BASE + ':' + path).decode()
    current = (ROOT / path).read_text()
    begin, end = '            let permissions = ', '            report["passed"] = true'
    old_body = old[old.index(begin):old.index(end)]
    new_body = current[current.index(begin):current.index('            if let url = analysisURL {')]
    assert old_body == new_body
    default_body_sha256 = sha(old_body.encode())
    path = 'scripts/verify_macos_ordinary.py'
    old = git('show', BASE + ':' + path)
    current = (ROOT / path).read_bytes()
    boundary = b"            ui.click_label(menu, 'DEPLOY"
    assert old[old.index(boundary):] == current[current.index(boundary):]
    assert assignments(old, ('BUDGETS', 'ENVIRONMENT_KEYS')) == assignments(current, ('BUDGETS', 'ENVIRONMENT_KEYS'))
    path = 'scripts/macos_ordinary_input.py'
    old = git('show', BASE + ':' + path)
    current = (ROOT / path).read_bytes()
    old_functions, new_functions = functions(old), functions(current)
    changed = [name for name in old_functions if old_functions[name] != new_functions[name]]
    assert changed == ['label_point', 'MacOrdinaryUI'], changed
    old_ui = next(node for node in ast.parse(old).body if isinstance(node, ast.ClassDef) and node.name == 'MacOrdinaryUI')
    new_ui = next(node for node in ast.parse(current).body if isinstance(node, ast.ClassDef) and node.name == 'MacOrdinaryUI')
    old_methods = {node.name: ast.dump(node) for node in old_ui.body if isinstance(node, ast.FunctionDef)}
    new_methods = {node.name: ast.dump(node) for node in new_ui.body if isinstance(node, ast.FunctionDef)}
    assert [name for name in old_methods if old_methods[name] != new_methods[name]] == ['click_label']
    unchanged = ['scripts/verify_macos_menu.py', 'scripts/probe_macos_input.py',
                 'scripts/macos_native_input.py', 'scripts/test_macos_ordinary.py',
                 'scripts/test_macos_ordinary_paths.py', 'scripts/test_macos_ordinary_startup.py',
                 'scripts/test_macos_menu.py', 'scripts/test_macos_focus.py',
                 'scripts/test_macos_screen_identity.py', 'scripts/test_probe_macos_input.py']
    assert git('diff', '--name-only', BASE, FREEZE, '--', *unchanged, 'game') == b''
    return {'changed_source_paths': paths, 'source_sha256': hashes,
            'default_capture_ocr_body_sha256': default_body_sha256,
            'default_capture_ocr_body_byte_identical': True,
            'deploy_through_teardown_byte_identical': True,
            'budgets_and_environment_whitelist_ast_identical': True,
            'ordinary_changed_functions': changed, 'ordinary_changed_ui_methods': ['click_label'],
            'unchanged_paths': unchanged, 'game_tree_unchanged': True}


def artifact_audit():
    component = OUT.parent
    evidence = json.loads((component / 'evidence-index.json').read_text())
    for row in evidence['files']:
        data = (component / row['path']).read_bytes()
        assert len(data) == row['bytes'] and sha(data) == row['sha256'], row
    index = json.loads((component / 'original-native-index.json').read_text())
    original = component / 'original-native-39912086121'
    assert index['source'] == BASE and index['run_id'] == 39912086121
    for row in index['files']:
        data = (original / row['path']).read_bytes()
        assert len(data) == row['bytes'] and sha(data) == row['sha256'], row
    qa_count = receipt_count = 0
    receipt_images_absent = []
    with zipfile.ZipFile(original / 'arm-39912086121-qa.zip') as qa:
        with zipfile.ZipFile(original / 'arm-39912086121-receipts.zip') as outer:
            with zipfile.ZipFile(io.BytesIO(outer.read('qa-receipts.zip'))) as receipt:
                for path in sorted((original / 'macos-ordinary-input').iterdir()):
                    rel = str(path.relative_to(original))
                    assert qa.read(rel) == path.read_bytes(), rel
                    qa_count += 1
                    if 'evidence/' + rel in receipt.namelist():
                        assert receipt.read('evidence/' + rel) == path.read_bytes(), rel
                        receipt_count += 1
                    else:
                        assert path.suffix == '.png', rel
                        receipt_images_absent.append(rel)
    assert qa_count == 29 and receipt_count == 21 and len(receipt_images_absent) == 8
    captions = []
    for name in ('00-startup-menu-7', '01-focused-menu'):
        data = json.loads((original / 'macos-ordinary-input' / (name + '.json')).read_text())
        rows = [row for row in data['text'] if row['text'].startswith('DEPLOY')]
        assert len(rows) == 1 and rows[0]['text'] == 'DEPLOY • OFFLINE 5V5' and rows[0]['confidence'] == .5
        assert 'derived_deploy_analysis' not in data
        captions.append({'capture': name, 'row': rows[0]})
    result = json.loads((original / 'macos-ordinary-input/results.json').read_text())
    assert result['status'] == 'FAILED' and result['cg_event_post_attempts'] == 0
    assert result['failure_ordinary_close'] == {'needed': True, 'request_accepted': True, 'exit_code': 0}
    assert len(result['cleanup']) == 10 and all(row['owned_group_gone'] and not row['signals_sent'] for row in result['cleanup'])
    return {'builder_evidence_index_files_hash_verified': len(evidence['files']),
            'index_files_hash_verified': len(index['files']), 'qa_zip_local_bytes_matched': qa_count,
            'nested_receipts_zip_local_bytes_matched': receipt_count,
            'nested_receipts_png_members_absent_by_design': receipt_images_absent, 'original_png_json_pairs': 8,
            'native_deploy_captions': captions, 'actual_run_status': result['status'],
            'actual_failure': result['failure'], 'cg_event_post_attempts': 0,
            'ordinary_close_exit_code': 0, 'cleanup_groups_gone': 10}


def main():
    source = source_audit()
    artifacts = artifact_audit()
    normal = [execute('normal-' + suite, [sys.executable, 'scripts/' + suite + '.py', '-v']) for suite in SUITES]
    execute('independent-controls', [sys.executable, str(OUT / 'independent_controls.py')])
    execute('original-selector-replay', [sys.executable, str(OUT.parent / 'replay_original_selector.py')])
    alias_context = []
    with tempfile.TemporaryDirectory(prefix='sightbreak-fresh-ocr-review-') as temporary:
        root = Path(temporary).resolve(strict=True)
        physical = root / 'physical'
        physical.mkdir()
        alias = root / 'alias'
        alias.symlink_to(physical, target_is_directory=True)
        env = dict(os.environ, TMPDIR=str(alias), TMP=str(alias), TEMP=str(alias))
        alias_context = {'alias': str(alias), 'canonical_target': str(physical),
                         'environment': {name: env.get(name) for name in ('TMPDIR', 'TMP', 'TEMP', 'LANG', 'LC_ALL', 'PYTHONPATH', 'PYTHONDONTWRITEBYTECODE')}}
        for suite in SUITES[:5]:
            execute('alias-' + suite, [sys.executable, 'scripts/' + suite + '.py', '-v'], env=env)
        mutations = json.loads((OUT.parent / 'pure-candidate/mutation-spec.json').read_text())['mutations']
        for label, mutation in mutations.items():
            directory = root / label
            directory.mkdir()
            text = (ROOT / 'scripts/macos_deploy_ocr.py').read_text()
            assert text.count(mutation['needle']) == 1
            (directory / 'macos_deploy_ocr.py').write_text(text.replace(mutation['needle'], mutation['replacement']))
            code = ('import sys,unittest;sys.path[:0]=' + repr([str(directory), str(ROOT / 'scripts')])
                    + ';import test_macos_deploy_ocr as module;unittest.main(module=module,verbosity=2)')
            execute('mutation-' + label, [sys.executable, '-c', code], expected=1)
    summary = {'scope': 'Source and pure synthetic checks only; no Swift compile/OCR/native API/engine/export/CI/input/service',
               'source_freeze': FREEZE, 'handoff': HANDOFF, 'review_base': git('rev-parse', 'HEAD').decode().strip(),
               'python': sys.version, 'platform': platform.platform(), 'source_audit': source,
               'artifact_audit': artifacts, 'maintained_top_level_tests': sum(row['tests'] for row in normal),
               'independent_top_level_tests': 8, 'alias_context': alias_context, 'commands': commands,
               'passed': True}
    (OUT / 'checks.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps({'passed': True, 'maintained_tests': summary['maintained_top_level_tests'],
                      'independent_tests': 8, 'commands': len(commands), 'artifact_files': artifacts['index_files_hash_verified']}, indent=2))


if __name__ == '__main__':
    main()
