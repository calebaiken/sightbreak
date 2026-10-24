"""Read-only comparison with exact failed-run controller and game source."""
import ast
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess


BASE = 'a089473481ced0f2e7b2a7468bbc5d079f92f0ff'


def call(statement, name):
    return (isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Call)
            and getattr(statement.value.func, 'id', '') == name)


def source_function(tree, name):
    return ast.dump(next(node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == name))


if __name__ == '__main__':
    original = ast.parse(subprocess.check_output(['git', 'show', BASE + ':scripts/verify_offline_export.py'], text=True))
    actual = ast.parse(Path('scripts/verify_offline_export.py').read_text())
    normalized = deepcopy(actual)
    normalized.body = [node for node in normalized.body
                       if not (isinstance(node, ast.ImportFrom) and node.module == 'native_settings_route')]
    original_wait = next(node for node in ast.walk(original) if isinstance(node, ast.Expr) and any(
        isinstance(value, ast.Constant) and value.value == 'Second active round for weapon switching' for value in ast.walk(node)))
    changed = False
    for parent in ast.walk(normalized):
        body = getattr(parent, 'body', None)
        if not isinstance(body, list):
            continue
        for index, node in enumerate(body):
            if (isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == 'second_live_until'
                                                   for target in node.targets)):
                assert ast.unparse(node.value) == 'min(deadline, time.monotonic() + 35)'
                end = next(i for i in range(index, len(body)) if call(body[i], 'transition_budget') and any(
                    isinstance(value, ast.Constant) and value.value == 'Completed fixed settings route before weapon switching'
                    for value in ast.walk(body[i])))
                route = next(value for value in body[index:end + 1] if call(value, 'relocate_settings_actor'))
                kwargs = {kw.arg: ast.unparse(kw.value) for kw in route.value.keywords}
                assert kwargs['deadline'] == 'second_live_until' and kwargs['round_number'] == '2'
                body[index:end + 1] = [deepcopy(original_wait)]
                changed = True
                break
    assert changed and ast.dump(normalized) == ast.dump(original)
    names = ('remaining', 'transition_budget', 'wait_for', 'pause', 'key', 'button', 'tap', 'capture',
             'read_hud', 'require_resume_context', 'resume_budget', 'resume_acknowledged', 'check_guard')
    unchanged = {name: source_function(original, name) == source_function(actual, name) for name in names}
    assert all(unchanged.values())
    protected = ['game', '.github', 'scripts/native_approach.py', 'scripts/native_focus_fence.py', 'scripts/toolchain.py']
    assert subprocess.run(['git', 'diff', '--quiet', BASE, '--', *protected]).returncode == 0
    paths = ['scripts/verify_offline_export.py', 'scripts/native_settings_route.py',
             'scripts/test_native_settings_route.py', 'scripts/validate.sh', 'scripts/native_approach.py']
    receipt = {'base': BASE, 'source_freeze': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
               'entire_controller_ast_equal_after_removing_only_route_import_and_shared_cap_route_block': True,
               'unchanged_functions': unchanged, 'protected_paths_unchanged': protected,
               'game_tree': subprocess.check_output(['git', 'rev-parse', 'HEAD:game'], text=True).strip(),
               'source_sha256': {path: hashlib.sha256(Path(path).read_bytes()).hexdigest() for path in paths}}
    print(json.dumps(receipt, indent=2))
