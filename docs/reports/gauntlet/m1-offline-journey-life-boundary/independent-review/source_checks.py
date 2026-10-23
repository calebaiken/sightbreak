#!/usr/bin/env python3
"""Supporting source checks using real Windows state; never native proof."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[5]
OUT = Path(__file__).resolve().parent
COMMIT = '171169e545a91e271ad8c73a571aeee6fe37dd90'
RAW = Path('/workspace/reviews/native-ci-39719407304/windows-receipts/evidence/offline-input')


def main():
    path = ROOT / 'scripts/verify_offline_export.py'
    source = subprocess.check_output(['git', '-C', str(ROOT), 'show', COMMIT + ':scripts/verify_offline_export.py'], text=True)
    tree = ast.parse(source)
    raw = json.loads((RAW / 'results.json').read_text())
    pause = next(row for row in raw['hud_analysis_pauses'] if row['capture'] == '06g-switched-primary')['after_analysis']
    guard = next(node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == 'require_resume_context')
    namespace = {'settings_pause': pause}
    exec(compile(ast.Module(body=[guard], type_ignores=[]), COMMIT, 'exec'), namespace)
    require = namespace['require_resume_context']
    checks = []

    def check(label, state, expected):
        try:
            require(state)
            accepted = True
        except RuntimeError:
            accepted = False
        checks.append({'label': label, 'expected_accept': expected, 'accepted': accepted, 'passed': accepted == expected})

    check('actual living paused Windows boundary', pause, True)
    check('actual final Windows dead observation', raw['last_offline_observation'], False)
    for path_keys, value in [(('ui', 'screen'), 'menu'), (('ui', 'focused'), False), (('time_scale',), 0.5),
                             (('phase',), 'buy'), (('round_number',), 3), (('local_actor', 'alive'), False),
                             (('local_actor', 'id'), 2), (('local_actor', 'weapon'), 'sidearm'),
                             (('local_actor', 'ammo'), 29), (('local_actor', 'reserve'), 119)]:
        changed = copy.deepcopy(pause)
        target = changed
        for key in path_keys[:-1]:
            target = target[key]
        target[path_keys[-1]] = value
        check('reject changed ' + '.'.join(path_keys), changed, False)
    raw_dead = copy.deepcopy(raw['last_offline_observation'])
    raw_dead['ui']['paused'] = True
    read_hud = next(node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == 'read_hud')
    class NativeReleased:
        def diagnostics(self):
            return {'lmb_down': False, 'keys_down': {}}
    called = []
    def pixels(*_):
        called.append(True)
        raise AssertionError('Dead observation reached pixel acceptance')
    namespace = {'ui': NativeReleased(), 'held_keys': set(), 'offline_observation': lambda: raw_dead,
                 'read_hud_pixels': pixels, 'out': RAW, 'ocr': None}
    exec(compile(ast.Module(body=[read_hud], type_ignores=[]), COMMIT, 'exec'), namespace)
    try:
        namespace['read_hud']('07d-explicit-resume')
        accepted = True
    except RuntimeError as error:
        accepted = False
        message = str(error)
    checks.append({'label': 'actual dead Windows observation also rejects when already paused', 'accepted': accepted,
                   'passed': not accepted and not called, 'error': message})
    checks.append({'label': 'game source unchanged', 'passed': not subprocess.check_output(['git', '-C', str(ROOT), 'diff', '4418161', COMMIT, '--', 'game'])})
    previous = ast.parse(subprocess.check_output(['git', '-C', str(ROOT), 'show', '0ca125d:scripts/verify_offline_export.py'], text=True))
    baseline_reader = next(node for node in previous.body if isinstance(node, ast.FunctionDef) and node.name == 'read_hud_pixels')
    final_reader = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'read_hud_pixels')
    checks.append({'label': 'final reader AST identical to the baseline reader exercised on Windows frames',
                   'passed': ast.dump(baseline_reader) == ast.dump(final_reader)})
    result = {'scope': 'AST-executed production guards with saved native state and deliberate mutations; no native input proof',
              'source_commit': COMMIT, 'source_sha256': hashlib.sha256(source.encode()).hexdigest(),
              'checks': checks, 'all_checks_pass': all(row['passed'] for row in checks)}
    (OUT / 'source-checks.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'checks': len(checks), 'all_checks_pass': result['all_checks_pass']}))


if __name__ == '__main__':
    main()
