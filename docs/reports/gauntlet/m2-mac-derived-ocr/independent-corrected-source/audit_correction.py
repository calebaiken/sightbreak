#!/usr/bin/env python3
"""Independent immutable-source/reference audit; only Git and Python reads."""
import ast
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[5]
OUT = Path(__file__).resolve().parent
COMPONENT = OUT.parent
BASE = 'c08889b8c1118c89e83c151079df4dc224076760'
REJECTED = 'a282b3f55c4014072144f3184e91fbefbafc0077'
SOURCE = '3973447175370d64ef2d790a3551102a89bb3a8e'
HANDOFF = '39cb67402c8dbeef3e85c15bfd0e761846ff4f0c'
REVIEW = 'bde551cb2a80a38b901d6c7b0ad5f8301947dcfb'


def git(*args): return subprocess.check_output(['git', *args], cwd=ROOT)
def sha(data): return hashlib.sha256(data).hexdigest()
def original(commit, path): return git('show', commit + ':' + path)


def test_methods(data):
    suite = next(node for node in ast.parse(data).body
                 if isinstance(node, ast.ClassDef) and node.name == 'DeployAnalysisControls')
    return {node.name: ast.dump(node, include_attributes=False) for node in suite.body
            if isinstance(node, ast.FunctionDef) and node.name.startswith('test_')}


def main():
    changed = git('diff', '--name-only', REJECTED, SOURCE).decode().splitlines()
    source_paths = [path for path in changed if not path.startswith('docs/reports/')]
    expected = ['scripts/fixtures/macos_ordinary_source/default_capture_body.swift.txt',
                'scripts/fixtures/macos_ordinary_source/reference.json', 'scripts/test_macos_deploy_ocr.py']
    assert source_paths == expected, source_paths
    assert not [path for path in git('diff', '--name-only', SOURCE, HANDOFF).decode().splitlines()
                if not path.startswith('docs/reports/')]
    for path in expected:
        assert (ROOT / path).read_bytes() == original(SOURCE, path) == original(HANDOFF, path)
    protected = ['scripts/macos_window_capture.swift', 'scripts/macos_deploy_ocr.py',
                 'scripts/macos_ordinary_input.py', 'scripts/verify_macos_ordinary.py',
                 'scripts/test_macos_ordinary_controller.py', '.github/workflows/desktop-alpha.yml']
    for path in protected:
        assert (ROOT / path).read_bytes() == original(REJECTED, path) == original(SOURCE, path)
    directory = ROOT / 'scripts/fixtures/macos_ordinary_source'
    manifest = (directory / 'reference.json').read_bytes()
    assert sha(manifest) == '47d2484fe191af3a374dbb586474af53d36448d48acf3c8e00ed7a9f6b45d92a'
    reference = json.loads(manifest)
    assert reference['source_commit'] == BASE
    helper = original(BASE, reference['helper_source_path'])
    driver = original(BASE, reference['driver_source_path'])
    assert sha(helper) == reference['helper_source_sha256']
    assert sha(driver) == reference['driver_source_sha256']
    start, end = reference['helper_default_start'].encode(), reference['helper_default_end'].encode()
    body = helper[helper.index(start):helper.index(end)]
    golden = (directory / reference['helper_default_fixture']).read_bytes()
    assert len(body) == 3601 and body == golden and sha(body) == reference['helper_default_sha256']
    current = (ROOT / reference['helper_source_path']).read_bytes()
    assert current[current.index(start):current.index(b'            if let url = analysisURL {')] == body
    boundary = reference['driver_gameplay_boundary'].encode()
    tail = driver[driver.index(boundary):]
    current = (ROOT / reference['driver_source_path']).read_bytes()
    assert len(tail) == 11726 and current[current.index(boundary):] == tail
    assert sha(tail) == reference['driver_gameplay_tail_sha256']
    path = 'scripts/test_macos_deploy_ocr.py'
    old_methods = test_methods(original(REJECTED, path))
    new_methods = test_methods((ROOT / path).read_bytes())
    assert old_methods.keys() == new_methods.keys() and len(new_methods) == 13
    assert [name for name in old_methods if old_methods[name] != new_methods[name]] == [
        'test_default_native_helper_ocr_and_gameplay_tail_are_byte_preserved']
    assert 'subprocess' not in (ROOT / path).read_text()
    # All original critic files, including both failing shallow reproductions.
    prior_prefix = 'docs/reports/gauntlet/m2-mac-derived-ocr/independent-fresh-source/'
    prior_paths = git('ls-tree', '-r', '--name-only', REVIEW, '--', prior_prefix).decode().splitlines()
    assert len(prior_paths) == 55
    for path in prior_paths:
        assert original(REVIEW, path) == (COMPONENT / 'shallow-checkout-correction/rejected-review' / path[len(prior_prefix):]).read_bytes()
    for name in ('independent_controls.py', 'replay_shallow.py'):
        assert original(REVIEW, prior_prefix + name) == (COMPONENT / 'shallow-checkout-correction' / name).read_bytes()
    original_index = json.loads((COMPONENT / 'original-native-index.json').read_text())
    for row in original_index['files']:
        data = (COMPONENT / 'original-native-39912086121' / row['path']).read_bytes()
        assert len(data) == row['bytes'] and sha(data) == row['sha256']
    shallow = json.loads((OUT / 'exact-shallow-controls/result.json').read_text())
    assert shallow['head'] == SOURCE and shallow['shallow'] == 'true'
    assert shallow['reachable_commit_count'] == 1 and shallow['baseline_c08889b_absent']
    counts = {}
    for row in shallow['commands']:
        data = (OUT / 'exact-shallow-controls' / row['log']).read_bytes()
        assert len(data) == row['bytes'] and sha(data) == row['sha256']
        assert row['exit_code'] == row['expected_exit_code']
        match = re.search(rb'Ran (\d+) tests? in ', data)
        if match: counts[row['label']] = int(match[1])
    assert sum(count for label, count in counts.items() if label.startswith('normal-')) == 83
    assert counts['independent-controls'] == 8
    assert len([label for label in counts if label.startswith('alias-')]) == 5
    assert len([row for row in shallow['commands'] if row['expected_exit_code'] == 1]) == 7
    assert (OUT / 'exact-shallow-controls/status.txt').read_bytes() == b''
    for path, digest in shallow['tested_file_sha256'].items():
        assert sha((ROOT / path).read_bytes()) == digest
    replay = json.loads((OUT / 'original-critic-replay/result.json').read_text())
    assert replay['head'] == SOURCE and replay['shallow'] == 'true' and replay['exit_code'] == 0
    summary = {'scope': 'Source/reference and pure evidence audit only; no native/Swift/OCR/engine/CI',
               'source_freeze': SOURCE, 'handoff': HANDOFF, 'changed_source_paths': source_paths,
               'source_sha256': {path: sha((ROOT / path).read_bytes()) for path in expected + protected},
               'baseline_source': BASE, 'reference_manifest_sha256': sha(manifest),
               'default_helper_body': {'bytes': len(body), 'sha256': sha(body), 'baseline_fixture_current_equal': True},
               'gameplay_tail': {'bytes': len(tail), 'sha256': sha(tail), 'baseline_current_equal': True},
               'test_methods': len(new_methods), 'unchanged_test_methods': 12,
               'prior_critic_files_byte_verified': len(prior_paths), 'original_native_files_hash_verified': len(original_index['files']),
               'unchanged_critic_scripts': ['independent_controls.py', 'replay_shallow.py'],
               'runtime_helper_controller_workflow_unchanged': True, 'game_tree_unchanged': True,
               'exact_depth_one_pure_counts': counts, 'exact_depth_one_clean': True,
               'original_falsifier_now_passes_without_baseline_object': True, 'passed': True}
    (OUT / 'audit.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps({'passed': True, 'changed_source_paths': source_paths,
                      'old_critic_files_verified': len(prior_paths), 'baseline_fixture_body_bytes': len(body),
                      'baseline_gameplay_tail_bytes': len(tail)}, indent=2))


if __name__ == '__main__':
    main()
