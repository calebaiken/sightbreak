#!/usr/bin/env python3
"""Read exact Git bytes, prove collector erasure and exercise actual flag AST."""
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

BASE = '49ae54b0e4f5d880bdf06e4eb783a616b2dff684'
SOURCE = 'c0738163965804297a1881905d5bb4646da40a16'
PATHS = ['game/scripts/gameplay/match.gd', 'game/tests/movement_prediction_test.gd',
         'scripts/fixtures/export_integration.gd', 'scripts/verify_integration_export.py']


def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args])


def stripped(data):
    result, inside = [], False
    for line in data.splitlines(keepends=True):
        if b'# BEGIN INPUT OBSERVATION' in line:
            assert not inside
            inside = True
        elif b'# END INPUT OBSERVATION' in line:
            assert inside
            inside = False
        elif not inside and b'# INPUT_OBSERVATION_HOOK' not in line:
            result.append(line)
    assert not inside
    return b''.join(result)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert sorted(os.sched_getaffinity(0)) == [4]
    payloads, bindings = {}, {}
    for path in PATHS:
        before = git(args.repo, 'show', BASE + ':' + path)
        after = git(args.repo, 'show', SOURCE + ':' + path)
        recovered = stripped(after)
        assert recovered == before, path
        mode = git(args.repo, 'ls-tree', SOURCE, path).decode().split()[0]
        assert mode == git(args.repo, 'ls-tree', BASE, path).decode().split()[0] == '100644'
        assert b'analyze_input_consumption' not in after
        assert b'diagnostic_complete' not in after
        payloads[path] = after.decode()
        bindings[path] = {'candidate_blob': git(args.repo, 'rev-parse', SOURCE + ':' + path).decode().strip(),
                          'base_blob': git(args.repo, 'rev-parse', BASE + ':' + path).decode().strip(),
                          'candidate_sha256': sha(after), 'base_sha256': sha(before),
                          'recovered_sha256': sha(recovered), 'candidate_bytes': len(after),
                          'base_bytes': len(before), 'mode': mode, 'exact_erasure': True}
    module = ast.parse(payloads['scripts/verify_integration_export.py'])
    declaration = next(node for node in ast.walk(module) if isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Call)
        and any(isinstance(arg, ast.Constant) and arg.value == '--observe-input-consumption'
                for arg in node.value.args))
    branches = sorted((node for node in ast.walk(module) if isinstance(node, ast.If)
                       and isinstance(node.test, ast.Attribute)
                       and node.test.attr == 'observe_input_consumption'), key=lambda x: x.lineno)
    assert len(branches) == 3
    flag_cases = []
    for enabled in (False, True):
        actual_parser = argparse.ArgumentParser()
        exec(compile(ast.Module(body=[declaration], type_ignores=[]), 'exact-collector-flag', 'exec'), {'parser': actual_parser})
        actual_args = actual_parser.parse_args(['--observe-input-consumption'] if enabled else [])
        env = {'args': actual_args, 'result': {}, 'client_command': ['game', '--quit-after', '10'],
               'server_command': ['godot', '--', '--output=fresh']}
        exec(compile(ast.Module(body=branches, type_ignores=[]), 'exact-collector-command-branches', 'exec'), env)
        assert env['client_command'] == ['game', '--quit-after', '10'] + (['--', '--native-input-observation'] if enabled else [])
        assert env['server_command'] == ['godot', '--', '--output=fresh'] + (['--native-input-observation'] if enabled else [])
        assert bool(env['result']) == enabled
        flag_cases.append({'enabled': enabled, 'client': env['client_command'],
                           'server': env['server_command'], 'result': env['result']})
    runtime = payloads['game/scripts/gameplay/match.gd']
    methods = runtime.split('# BEGIN INPUT OBSERVATION METHODS\n')[1].split('# END INPUT OBSERVATION METHODS')[0]
    # This lexical falsifier supplements contextual manual review; it is not a
    # general side-effect proof or GDScript type/API validation.
    forbidden = [r'@rpc', r'\.rpc(?:_id)?\(',
                 r'_input_stream\.(?:accept|pop|forget|reset_epoch)\(',
                 r'_prediction\.(?:predict|packet|reconcile|reset)\(',
                 r'_peer_lifecycle\.(?:active|allow_input|admitted|forget|reject|connected)\(',
                 r'\b(?:set_local_input|start_reload|_connect_client|_apply_snapshot)\(',
                 r'Input\.(?:parse_input_event|action_press|action_release|flush_buffered_events)\(',
                 r'^\s*(?:actor\.|options\[|_local_input\s*=|_peer_actors\[|_last_input_sequence\[|connection_state\s*=)']
    for pattern in forbidden:
        assert re.search(pattern, methods, re.M) is None, pattern
    for required in ['if _native_input_observation.is_empty(): return',
                     'if int(diagnostic.count) >= 1024: return',
                     '"observation_limit" if int(diagnostic.count) == 1023',
                     'now - int(diagnostic.last_emit) < 1000',
                     'OS.is_debug_build()', 'commands.slice(0, SBInputStream.MAX_BATCH)']:
        assert required in methods, required
    # The only controller mutation is isolated observer state: fixed projection
    # metadata does not read any omitted analyzer or interpreted result file.
    imported = []
    for node in ast.walk(module):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.append(node.module)
    assert not any(name and 'analyz' in name for name in imported)
    tests = payloads['game/tests/movement_prediction_test.gd']
    assert '\tnative_input_observation_controls() # INPUT_OBSERVATION_HOOK\n' in tests
    assert 'movement_prediction' in git(args.repo, 'show', BASE + ':scripts/run_native_regressions.py').decode()
    checks = tests.split('# BEGIN INPUT OBSERVATION TESTS\n')[1].split('# END INPUT OBSERVATION TESTS')[0]
    syntactic_calls = len(re.findall(r'^\s*check\(', checks, re.M))
    # A five-element patch loop expands one syntactic call into five checks.
    assert syntactic_calls == 13, syntactic_calls
    result = {'source': SOURCE, 'base': BASE, 'scope': 'Four-path collector proposal, source-only; no implemented split or native pass',
              'cpu_affinity': [4], 'bindings': bindings, 'flag_ast_cases': flag_cases,
              'controller_imports': imported, 'reader_dependency_found': False,
              'erasure_restores_all_four_original_files': True,
              'godot_new_check_calls_syntactic': syntactic_calls, 'godot_new_checks_with_patch_loop': syntactic_calls + 4,
              'godot_controls_reachable_in_original_native_suite': True,
              'lexical_mutator_patterns_absent': forbidden, 'passed': True}
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
