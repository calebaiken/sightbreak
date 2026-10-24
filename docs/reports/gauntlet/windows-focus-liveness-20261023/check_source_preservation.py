"""Compare the frozen controller's budgets/captures/safety with original source."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess


BASE = 'b2e0293a546961230afbd73e5cd2a1a307d69e94'


def captures(source):
    return [node.args[0].value for node in ast.walk(ast.parse(source))
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
            and node.func.id == 'capture' and node.args and isinstance(node.args[0], ast.Constant)]


def waits(source):
    rows = []
    for node in ast.walk(ast.parse(source)):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and node.func.id in ('wait_for', 'observed', 'focus_observed') and len(node.args) > 2
                and isinstance(node.args[1], ast.Constant) and type(node.args[1].value) in (int, float)):
            rows.append({'seconds': node.args[1].value, 'label_ast': ast.dump(node.args[2])})
    return sorted(rows, key=lambda row: json.dumps(row, sort_keys=True))


def function(source, name):
    return ast.dump(next(node for node in ast.walk(ast.parse(source))
                         if isinstance(node, ast.FunctionDef) and node.name == name))


def git(*args):
    return subprocess.check_output(['git', *args], text=True).strip()


if __name__ == '__main__':
    baseline = git('show', BASE + ':scripts/verify_offline_export.py')
    current = Path('scripts/verify_offline_export.py').read_text()
    helper = Path('scripts/native_focus_fence.py').read_text()
    names = ('remaining', 'transition_budget', 'pause', 'wait_for', 'key', 'button', 'tap', 'capture',
             'check_guard', 'require_living_capture_phase', 'capture_living_phase', 'read_hud')
    paths = [Path('scripts') / path for path in (
        'verify_offline_export.py', 'native_focus_fence.py', 'test_native_focus_fence.py',
        'fixtures/offline_focus_observations.json', 'validate.sh')]
    receipt = {
        'base': BASE, 'source_freeze': git('rev-parse', 'HEAD'),
        'capture_calls_equal': captures(baseline) == captures(current),
        'original_capture_calls': captures(baseline), 'current_capture_calls': captures(current),
        'literal_stage_budgets_equal': waits(baseline) == waits(current + '\n' + helper),
        'original_literal_stage_budgets': waits(baseline), 'current_literal_stage_budgets': waits(current + '\n' + helper),
        'original_deadline_capture_and_held_safety_functions_unchanged': {
            name: function(baseline, name) == function(current, name) for name in names},
        'game_tree': git('rev-parse', 'HEAD:game'), 'base_game_tree': git('rev-parse', BASE + ':game'),
        'game_and_ci_worktree_diff_empty': subprocess.run(['git', 'diff', '--quiet', BASE, '--', 'game', '.github']).returncode == 0,
        'source_files': {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}}
    print(json.dumps(receipt, indent=2))
    assert receipt['capture_calls_equal'] and receipt['literal_stage_budgets_equal']
    assert all(receipt['original_deadline_capture_and_held_safety_functions_unchanged'].values())
    assert receipt['game_tree'] == receipt['base_game_tree'] and receipt['game_and_ci_worktree_diff_empty']
