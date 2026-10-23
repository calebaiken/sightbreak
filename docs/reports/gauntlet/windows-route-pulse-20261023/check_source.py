"""Compare source scope with failed e28; no native calls or fixture execution."""
import ast
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess


BASE = 'e28c8e90b9ef2d0c766bd9152c194e3197ceba9a'


def original(path):
    return ast.parse(subprocess.check_output(['git', 'show', BASE + ':' + path], text=True))


def remove_keyword(node, name):
    node.keywords = [item for item in node.keywords if item.arg != name]


def remove_argument(function, name):
    index = next(index for index, arg in enumerate(function.args.kwonlyargs) if arg.arg == name)
    function.args.kwonlyargs.pop(index)
    function.args.kw_defaults.pop(index)


if __name__ == '__main__':
    results = {}
    path = 'scripts/verify_integration_export.py'
    tree = ast.parse(Path(path).read_text())
    ui = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == 'WinUI')
    ui.body = [node for node in ui.body if not (isinstance(node, ast.FunctionDef) and node.name == 'key_pulse')]
    results['integration_input_module_unchanged_except_new_pulse_method'] = ast.dump(tree) == ast.dump(original(path))

    path = 'scripts/native_approach.py'
    tree = ast.parse(Path(path).read_text())
    function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'approach_floor')
    remove_argument(function, 'pulse')
    replaced = False
    for parent in ast.walk(tree):
        body = getattr(parent, 'body', None)
        if not isinstance(body, list): continue
        for index, node in enumerate(body):
            if isinstance(node, ast.If) and ast.unparse(node.test) == 'fine and pulse is not None':
                body[index:index + 1] = deepcopy(node.orelse)
                replaced = True
                break
    results['default_approach_ast_unchanged_after_removing_optional_pulse_branch'] = replaced and ast.dump(tree) == ast.dump(original(path))

    path = 'scripts/native_settings_route.py'
    tree = ast.parse(Path(path).read_text())
    function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'relocate_settings_actor')
    remove_argument(function, 'pulse')
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and getattr(node.func, 'id', '') == 'approach_floor': remove_keyword(node, 'pulse')
    results['route_guards_and_target_unchanged_except_optional_hook_forwarding'] = ast.dump(tree) == ast.dump(original(path))

    path = 'scripts/verify_offline_export.py'
    tree = ast.parse(Path(path).read_text())
    for parent in ast.walk(tree):
        body = getattr(parent, 'body', None)
        if isinstance(body, list):
            body[:] = [node for node in body if not (isinstance(node, ast.FunctionDef) and node.name == 'settings_route_pulse')]
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and getattr(node.func, 'id', '') == 'relocate_settings_actor':
            hook = next(item.value for item in node.keywords if item.arg == 'pulse')
            assert ast.unparse(hook) == "settings_route_pulse if args.target == 'windows' else None"
            remove_keyword(node, 'pulse')
    results['offline_controller_unchanged_except_windows_route_pulse_callback'] = ast.dump(tree) == ast.dump(original(path))
    protected = ['game', '.github', 'scripts/native_focus_fence.py', 'scripts/toolchain.py']
    results['protected_paths_unchanged'] = subprocess.run(['git', 'diff', '--quiet', BASE, '--', *protected]).returncode == 0
    assert all(results.values()), results
    paths = ['scripts/verify_integration_export.py', 'scripts/verify_offline_export.py',
             'scripts/native_approach.py', 'scripts/native_settings_route.py', 'scripts/test_native_route_pulse.py']
    print(json.dumps({'source_freeze': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
                      'base': BASE, 'checks': results, 'source_sha256': {
                          path: hashlib.sha256(Path(path).read_bytes()).hexdigest() for path in paths}}, indent=2))
