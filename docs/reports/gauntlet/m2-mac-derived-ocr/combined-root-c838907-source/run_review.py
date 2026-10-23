#!/usr/bin/env python3
"""Bind the combined source and run pure checks in its exact shallow checkout."""
import ast
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[5]
OUT = Path(__file__).resolve().parent
FREEZE = 'c838907cf4978e53c57423e08c23277c34f4496d'
PREVIOUS = 'f5bf19481d608945c87ce9f35838eaa87a2bd475'
MAC = '3973447175370d64ef2d790a3551102a89bb3a8e'
WINDOWS = 'a089473481ced0f2e7b2a7468bbc5d079f92f0ff'
LINUX = '3fd9718bc066bedf879f241760c106ee96923060'
WORKFLOW = '.github/workflows/desktop-alpha.yml'
MAC_PATHS = {WORKFLOW, 'scripts/macos_deploy_ocr.py', 'scripts/macos_ordinary_input.py',
             'scripts/macos_window_capture.swift', 'scripts/test_macos_deploy_ocr.py',
             'scripts/test_macos_ordinary_controller.py', 'scripts/verify_macos_ordinary.py',
             'scripts/fixtures/macos_ordinary_source/reference.json',
             'scripts/fixtures/macos_ordinary_source/default_capture_body.swift.txt'}
WINDOWS_PATHS = {'scripts/fixtures/offline_focus_observations.json', 'scripts/native_focus_fence.py',
                 'scripts/test_focus_resume_timing.py', 'scripts/test_native_focus_fence.py',
                 'scripts/validate.sh', 'scripts/verify_offline_export.py'}
LINUX_PATHS = {'scripts/linux_profile_overhead.py', 'scripts/test_linux_profile_overhead.py',
               'scripts/diagnostics/linux_profile_overhead.gd', 'scripts/diagnostics/linux_profile_overhead.tscn'}
MAC_SUITES = ['test_macos_ordinary', 'test_macos_ordinary_controller', 'test_macos_ordinary_paths',
              'test_macos_ordinary_startup', 'test_macos_deploy_ocr', 'test_macos_menu',
              'test_macos_focus', 'test_macos_screen_identity', 'test_probe_macos_input']
OTHER_SUITES = ['test_build_manifest', 'test_native_observation', 'test_offline_export_ocr',
                'test_package_qa_receipts', 'test_diagnose_native_input_mode', 'test_native_first_leak',
                'test_qualify_ios_compile', 'test_native_focus_fence', 'test_focus_resume_timing',
                'test_offline_capture_fences', 'test_linux_profile_overhead']
WHITELIST = ('HOME', 'PATH', 'TMPDIR', 'TMP', 'TEMP', 'DISPLAY', 'LANG', 'LC_ALL',
             'PYTHONPATH', 'PYTHONDONTWRITEBYTECODE', 'SIGHTBREAK_TOOLS_DIR',
             'SIGHTBREAK_STATE_DIR', 'SIGHTBREAK_BUILDS_DIR')


def sha(data): return hashlib.sha256(data).hexdigest()
def git(*args): return subprocess.check_output(['git', *args], cwd=ROOT)


def inventory(commit):
    result = {}
    for row in git('ls-tree', '-r', '-z', commit, '--', 'scripts', '.github', 'game').split(b'\0'):
        if row:
            metadata, path = row.split(b'\t', 1)
            mode, kind, blob = metadata.decode().split()
            assert kind == 'blob'
            result[path.decode()] = {'mode': mode, 'git_blob': blob}
    return result


def source_binding():
    versions = {name: inventory(commit) for name, commit in
                (('previous', PREVIOUS), ('mac', MAC), ('windows', WINDOWS), ('linux', LINUX), ('combined', FREEZE))}
    previous, combined = versions['previous'], versions['combined']
    delta = {path for path in set(previous) | set(combined) if previous.get(path) != combined.get(path)}
    assert delta == MAC_PATHS, delta
    expected = dict(previous)
    for path in MAC_PATHS:
        expected[path] = versions['mac'][path]
    assert expected == combined
    assert not MAC_PATHS & WINDOWS_PATHS and not MAC_PATHS & LINUX_PATHS and not WINDOWS_PATHS & LINUX_PATHS
    for label, paths in (('windows', WINDOWS_PATHS), ('linux', LINUX_PATHS)):
        for path in paths:
            assert combined[path] == versions[label][path] == previous[path], (label, path)
    trees = {name: git('rev-parse', commit + ':game').decode().strip() for name, commit in
             (('previous', PREVIOUS), ('mac', MAC), ('windows', WINDOWS), ('linux', LINUX), ('combined', FREEZE))}
    assert len(set(trees.values())) == 1
    assert git('diff', '--name-only', PREVIOUS, FREEZE, '--', '.claude', 'AGENTS.md', 'CLAUDE.md',
               'docs/engineering', 'docs/roadmap') == b''
    workflow = git('show', FREEZE + ':' + WORKFLOW).decode()
    old_workflow = git('show', PREVIOUS + ':' + WORKFLOW).decode()
    needle = '          python scripts/test_macos_ordinary_startup.py -v\n'
    assert workflow == old_workflow.replace(needle, needle + '          python scripts/test_macos_deploy_ocr.py -v\n')
    assert workflow.encode() == git('show', MAC + ':' + WORKFLOW)
    blocks = re.split(r'(?=^      - )', workflow, flags=re.M)
    controls = next(block for block in blocks if 'python scripts/test_macos_deploy_ocr.py -v' in block)
    assert "matrix.os == 'macos-15'" in controls
    assert "inputs.lane == 'arm-macos-ios' && '[{\"os\":\"macos-15\",\"target\":\"macos\"}]'" in workflow
    assert '    timeout-minutes: 60\n' in workflow
    # Every workflow step other than the additional ARM pure command is intact.
    old_blocks = re.split(r'(?=^      - )', old_workflow, flags=re.M)
    assert len(blocks) == len(old_blocks)
    unchanged_blocks = []
    for old, current in zip(old_blocks, blocks):
        if old != current:
            assert current == old.replace(needle, needle + '          python scripts/test_macos_deploy_ocr.py -v\n')
        else:
            name = re.search(r'^      - name: (.+)$', current, flags=re.M)
            if name: unchanged_blocks.append(name[1])
    preserved = []
    for path in ('docs/reports/gauntlet/windows-focus-root-independent-20261023',
                 'docs/reports/gauntlet/m1-linux-opaque-cost-plan',
                 'docs/reports/gauntlet/m2-mac-journey-recovered/native-actual-c088-independent'):
        before = git('rev-parse', PREVIOUS + ':' + path).decode().strip()
        after = git('rev-parse', FREEZE + ':' + path).decode().strip()
        assert before == after
        preserved.append({'path': path, 'previous_tree': before, 'combined_tree': after})
    return {'source_freeze': FREEZE, 'previous_root': PREVIOUS, 'accepted_mac': MAC,
            'accepted_windows': WINDOWS, 'accepted_linux_diagnostic': LINUX,
            'exact_nine_path_mac_union': True, 'mac_delta_paths': sorted(delta),
            'windows_paths_byte_identical': sorted(WINDOWS_PATHS),
            'linux_paths_byte_identical': sorted(LINUX_PATHS), 'component_paths_disjoint': True,
            'game_trees': trees, 'canonical_docs_unchanged': True,
            'workflow_sha256': sha(workflow.encode()), 'unchanged_workflow_steps': unchanged_blocks,
            'preserved_evidence_trees': preserved, 'tracked_code_files_bound': len(combined),
            'inventory': combined}


def main():
    global OUT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=OUT)
    args = parser.parse_args()
    OUT = args.output.resolve()
    OUT.mkdir(parents=True, exist_ok=True)
    assert not (OUT / 'pure').exists(), 'Retain prior output; select a fresh review directory'
    (OUT / 'pure').mkdir()
    binding = source_binding()
    commands = []
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
    with tempfile.TemporaryDirectory(prefix='sightbreak-mac-root-c838907-') as temporary:
        checkout = Path(temporary).resolve(strict=True) / 'checkout'
        checkout.mkdir()

        def run(label, command, expected=0, child_env=None):
            actual_env = env if child_env is None else child_env
            started = time.monotonic()
            result = subprocess.run(command, cwd=checkout, env=actual_env, stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT, timeout=60)
            path = OUT / 'pure' / (label + '.txt')
            path.write_bytes(result.stdout)
            match = re.search(rb'Ran (\d+) tests? in ', result.stdout)
            skipped = re.search(rb'OK \(skipped=(\d+)\)', result.stdout)
            commands.append({'label': label, 'command': command, 'exit_code': result.returncode,
                             'expected_exit_code': expected, 'seconds': time.monotonic() - started,
                             'test_methods': int(match[1]) if match else None,
                             'skipped': int(skipped[1]) if skipped else 0,
                             'environment_allowlist': {key: actual_env.get(key) for key in WHITELIST},
                             'log': str(path.relative_to(OUT)), 'bytes': len(result.stdout), 'sha256': sha(result.stdout)})
            print(label + ': ' + str(result.returncode), flush=True)
            assert result.returncode == expected, result.stdout.decode()
            return result.stdout

        for label, command in (
                ('init', ['git', 'init']), ('remote', ['git', 'remote', 'add', 'origin', ROOT.as_uri()]),
                ('fetch', ['git', 'fetch', '--depth=1', '--filter=blob:none',
                           '--upload-pack=git -c uploadpack.allowFilter=true upload-pack', 'origin', FREEZE]),
                ('sparse', ['git', 'sparse-checkout', 'set', '--cone', 'scripts', '.github', 'game',
                            'docs/reports/gauntlet/m2-mac-derived-ocr',
                            'docs/reports/gauntlet/m2-macos-screen-identity/fixtures',
                            'docs/reports/gauntlet/m2-macos-first-leak/fixtures',
                            'docs/reports/gauntlet/m2-ios-compile/sdk-iteration/failure-0ca125d']),
                ('checkout', ['git', 'checkout', '--detach', 'FETCH_HEAD'])):
            run(label, command)
        assert run('head', ['git', 'rev-parse', 'HEAD']).decode().strip() == FREEZE
        assert run('shallow', ['git', 'rev-parse', '--is-shallow-repository']).strip() == b'true'
        assert run('commit-count', ['git', 'rev-list', '--count', 'HEAD']).strip() == b'1'
        run('baseline-absent', ['git', 'show', 'c08889b:scripts/macos_window_capture.swift'], expected=128)
        hashes = {}
        for path, entry in sorted(binding['inventory'].items()):
            data = (checkout / path).read_bytes()
            assert hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest() == entry['git_blob'], path
            assert ('100755' if (checkout / path).stat().st_mode & 0o111 else '100644') == entry['mode'], path
            hashes[path] = sha(data)
        # Static source analysis only; import neither OS input adapter nor runner.
        local = {path.stem: path for path in (checkout / 'scripts').glob('*.py')}
        pending = ['export', 'verify_builds', 'run_native_regressions', 'diagnose_native_input_mode',
                   'probe_macos_input', 'verify_macos_menu', 'verify_macos_ordinary',
                   'qualify_ios_compile', 'build_manifest', 'package_qa_receipts']
        visited = set()
        while pending:
            name = pending.pop()
            if name in visited: continue
            visited.add(name)
            for node in ast.walk(ast.parse(local[name].read_bytes())):
                imports = []
                if isinstance(node, ast.Import): imports = [item.name.split('.')[0] for item in node.names]
                if isinstance(node, ast.ImportFrom) and node.module: imports = [node.module.split('.')[0]]
                pending.extend(item for item in imports if item in local and item not in visited)
        assert not {'native_focus_fence', 'linux_profile_overhead', 'verify_offline_export'} & visited
        binding['arm_entrypoint_static_local_import_closure'] = sorted(visited)
        for suite in MAC_SUITES + OTHER_SUITES:
            run(suite, [sys.executable, 'scripts/' + suite + '.py', '-v'])
        independent = 'docs/reports/gauntlet/m2-mac-derived-ocr/shallow-checkout-correction/independent_controls.py'
        run('independent-mac-controls', [sys.executable, independent, '-v'])
        physical, alias = checkout.parent / 'physical-temp', checkout.parent / 'alias-temp'
        physical.mkdir(); alias.symlink_to(physical, target_is_directory=True)
        alias_env = dict(env, TMPDIR=str(alias), TMP=str(alias), TEMP=str(alias))
        for suite in MAC_SUITES[:5]:
            run('alias-' + suite, [sys.executable, 'scripts/' + suite + '.py', '-v'], child_env=alias_env)
        assert run('final-status', ['git', 'status', '--porcelain']) == b''
        for path, digest in hashes.items(): assert sha((checkout / path).read_bytes()) == digest, path
        # Read-only source identity; no begin/finish/export operation.
        sys.path.insert(0, str(checkout / 'scripts'))
        spec = importlib.util.spec_from_file_location('combined_manifest', checkout / 'scripts/build_manifest.py')
        manifest = importlib.util.module_from_spec(spec); spec.loader.exec_module(manifest)
        identity = manifest.source()
        assert identity['source_commit'] == FREEZE and not identity['source_dirty'] and not identity['source_game_dirty']
        content, validation = hashlib.sha256(), hashlib.sha256()
        for path in sorted(hashes):
            relative = Path(path)
            if path.startswith('game/') and 'tests' not in relative.parts and '.godot' not in relative.parts:
                content.update(relative.relative_to('game').as_posix().encode() + b'\0' + (checkout / path).read_bytes() + b'\0')
        for directory in ('scripts', '.github', 'game/tests'):
            for path in sorted(name for name in hashes if name.startswith(directory + '/')):
                validation.update(path.encode() + b'\0' + (checkout / path).read_bytes() + b'\0')
        assert identity['source_content_sha256'] == content.hexdigest() == 'bcb872f6998ed8504c852dee354ab0acf5b6f19e58e40717267a1927e6d68a50'
        assert identity['source_validation_sha256'] == validation.hexdigest()
        binding['source_identity'] = identity
        binding['source_sha256'] = hashes
        binding['exact_shallow_checkout'] = {'head': FREEZE, 'reachable_commits': 1, 'baseline_c088_absent': True,
                                           'clean_after_pure_checks': True, 'code_bytes_unchanged': True}
    methods = sum(row['test_methods'] or 0 for row in commands if row['label'] in MAC_SUITES + OTHER_SUITES)
    skipped = sum(row['skipped'] for row in commands if row['label'] in MAC_SUITES + OTHER_SUITES)
    assert sum(row['test_methods'] or 0 for row in commands if row['label'] in MAC_SUITES) == 83
    assert skipped == 3
    binding.update({'scope': 'Source binding and pure readiness for one existing full ARM workflow; no dispatch/runtime acceptance',
                    'pure_suite_groups': len(MAC_SUITES + OTHER_SUITES), 'pure_test_methods': methods, 'skipped': skipped,
                    'independent_mac_methods': 8, 'alias_suite_groups': 5,
                    'proposed_existing_workflow': WORKFLOW, 'proposed_input': {'lane': 'arm-macos-ios'},
                    'attempt_limit': 1, 'immutable_ref_must_resolve_to': FREEZE, 'dispatch_performed': False,
                    'commands': commands, 'passed': True})
    (OUT / 'binding.json').write_text(json.dumps(binding, indent=2) + '\n')
    print(json.dumps({'passed': True, 'code_files': len(binding['inventory']), 'pure_groups': binding['pure_suite_groups'],
                      'methods': methods, 'skipped': skipped, 'independent_mac_methods': 8, 'alias_groups': 5}, indent=2))


if __name__ == '__main__':
    main()
