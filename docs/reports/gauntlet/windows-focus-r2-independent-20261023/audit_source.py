"""Independently bind exact source freezes, budgets, scope and isolated timing AST."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[3]
BASE = 'b2e0293a546961230afbd73e5cd2a1a307d69e94'
FENCE = 'fa718efcbe6aa36e53ca12474454a5dccfc5e9b9'
TIMING = '691076fbe866ae798666e731c423ad4cc20fd876'
PREREG = '71de706'
CONTROLLER = 'scripts/verify_offline_export.py'
LABEL = 'Explicit resume with W and LMB still physically held'


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


def blob(commit, path):
    return git('show', commit + ':' + path)


def functions(tree, name):
    return ast.dump(next(node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == name))


def captures(tree):
    return [node.args[0].value for node in ast.walk(tree) if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name) and node.func.id == 'capture' and node.args
            and isinstance(node.args[0], ast.Constant)]


def waits(tree):
    return sorted((node.args[1].value, ast.dump(node.args[2])) for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        and node.func.id in ('wait_for', 'observed', 'focus_observed') and len(node.args) > 2
        and isinstance(node.args[1], ast.Constant) and type(node.args[1].value) in (int, float))


def main():
    rows, assertions = [], []
    def check(name, condition):
        assert condition, name
        assertions.append(name)
    baseline = ast.parse(blob(BASE, CONTROLLER))
    fence = ast.parse(blob(FENCE, CONTROLLER))
    timing = ast.parse(blob(TIMING, CONTROLLER))
    preserved_names = ('remaining', 'transition_budget', 'pause', 'wait_for', 'key', 'button', 'tap', 'capture',
                       'check_guard', 'require_living_capture_phase', 'capture_living_phase', 'read_hud')
    original_validation = blob(BASE, 'scripts/validate.sh').decode()
    expected_fence = original_validation.replace("printf 'Validation completed.",
        "python3 scripts/test_native_focus_fence.py -v\nprintf 'Validation completed.")
    expected_timing = expected_fence.replace("printf 'Validation completed.",
        "python3 scripts/test_focus_resume_timing.py -v\nprintf 'Validation completed.")
    for freeze, tree, label, validation in ((FENCE, fence, 'fence', expected_fence), (TIMING, timing, 'timing', expected_timing)):
        helper_bytes = blob(freeze, 'scripts/native_focus_fence.py')
        combined_tree = ast.parse(blob(freeze, CONTROLLER) + b'\n' + helper_bytes)
        check(label + ': literal capture calls preserved', captures(tree) == captures(baseline))
        check(label + ': original literal stage budgets preserved', waits(combined_tree) == waits(baseline))
        for name in preserved_names:
            check(label + ': original ' + name + ' unchanged', functions(tree, name) == functions(baseline, name))
        check(label + ': original game and CI unchanged', git('diff', BASE, freeze, '--', 'game', '.github') == b'')
        check(label + ': exact aggregate registration only', blob(freeze, 'scripts/validate.sh').decode() == validation)
        checkout = Path('/workspace/reviews/windows-focus-liveness-r2-source' if label == 'fence' else '/workspace/reviews/windows-focus-timing-source')
        check(label + ': checkout exact HEAD', git('-C', str(checkout), 'rev-parse', 'HEAD').decode().strip() == freeze)
        check(label + ': checkout clean after pure checks', git('-C', str(checkout), 'status', '--porcelain') == b'')
        paths = [CONTROLLER, 'scripts/native_focus_fence.py', 'scripts/test_native_focus_fence.py', 'scripts/validate.sh',
                 'scripts/fixtures/offline_focus_observations.json']
        if label == 'timing':
            paths.append('scripts/test_focus_resume_timing.py')
        hashes = {path: hashlib.sha256(blob(freeze, path)).hexdigest() for path in paths}
        for path in paths:
            check(label + ': exact checkout bytes ' + path, blob(freeze, path) == (checkout / path).read_bytes())
        rows.append({'source_freeze': freeze, 'label': label, 'source_hashes': hashes,
                     'game_tree': git('rev-parse', freeze + ':game').decode().strip(),
                     'capture_calls': captures(tree), 'literal_stage_budgets': waits(combined_tree)})
    # Reverse exactly one down/.3/up invocation replacement in a fresh copy.
    count = 0
    for node in ast.walk(timing):
        if isinstance(node, ast.Try):
            for index, statement in enumerate(node.body):
                if isinstance(statement, ast.Assign) and any(isinstance(item, ast.Constant) and item.value == LABEL for item in ast.walk(statement)):
                    check('combined exact Escape prefix', [ast.unparse(item) for item in node.body[index - 3:index]] ==
                        ["key('Escape', True)", 'pause(0.3)', "key('Escape', False)"])
                    node.body[index - 3:index] = ast.parse("tap('Escape')").body
                    count += 1
                    break
    check('exactly one timing invocation changed', count == 1)
    check('entire controller AST equals fence after reversing one invocation', ast.dump(timing) == ast.dump(fence))
    check('same corrected fence helper bytes in both freezes', blob(FENCE, 'scripts/native_focus_fence.py') == blob(TIMING, 'scripts/native_focus_fence.py'))
    check('same corrected focus test bytes in both freezes', blob(FENCE, 'scripts/test_native_focus_fence.py') == blob(TIMING, 'scripts/test_native_focus_fence.py'))
    check('only intended three script paths differ between freezes', set(git('diff', '--name-only', FENCE, TIMING, '--', 'scripts').decode().splitlines()) ==
        {CONTROLLER, 'scripts/validate.sh', 'scripts/test_focus_resume_timing.py'})
    for prior, later in ((FENCE, PREREG), (PREREG, '34b70a0'), ('34b70a0', TIMING)):
        check('ancestry ' + prior + ' before ' + later,
              subprocess.run(['git', 'merge-base', '--is-ancestor', prior, later], cwd=ROOT).returncode == 0)
    prereg_path = 'docs/reports/gauntlet/windows-focus-resume-timing-20261023/PREREGISTRATION.md'
    check('timing preregistration existed before implementation', bool(blob(PREREG, prereg_path)))
    receipt = {'scope': 'independent source-only comparison; no native or retry approval',
               'base': BASE, 'assertion_count': len(assertions), 'assertions': assertions, 'sources': rows,
               'timing_preregistration': git('rev-parse', PREREG).decode().strip(),
               'exact_single_invocation_timing_delta': True}
    (OUT / 'source-audit.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({key:value for key,value in receipt.items() if key not in ('assertions', 'sources')}))


if __name__ == '__main__':
    main()
