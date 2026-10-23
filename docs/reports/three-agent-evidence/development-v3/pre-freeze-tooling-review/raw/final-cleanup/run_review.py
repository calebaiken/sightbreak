"""Serial replay of unchanged critic controls against retained source copies."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

root = Path(__file__).resolve().parent
phase = sys.argv[1]
assert phase in {'before', 'after'}
stage = root / phase
sys.path[:0] = [str(stage / 'source/scripts'),
                r'C:\Users\blith\AppData\Local\Temp\opencode\sightbreak-v3\scripts']
import godot_process
import matrix_process

spec = importlib.util.spec_from_file_location('unchanged_critic_controls', stage / 'critic_controls.py')
controls = importlib.util.module_from_spec(spec)
spec.loader.exec_module(controls)
outcomes = []
for name in ['windows_dead_root', 'linux_dead_supervisor', 'windows_taskkill_race']:
    error = None
    try:
        getattr(controls, name)()
    except Exception as caught:
        error = type(caught).__name__ + ': ' + str(caught)
    outcomes.append({'control': name, 'exception': error})


def load(name):
    return json.loads((stage / name).read_text(encoding='utf-8-sig'))


windows = load('control-windows-exited-root.json')
linux = load('control-linux-dead-supervisor.json')
race = load('control-windows-taskkill-race.json')
raw = (stage / 'linux-dead-supervisor.log').read_text()
if phase == 'before':
    gates = {'old_assertions_pass': all(item['exception'] is None for item in outcomes),
             'windows_uncertainty_was_hidden': windows['cleanup_errors'] == [],
             'taskkill_race_was_hidden': race['cleanup_errors'] == [],
             'linux_uncertainty_was_not_explicit': 'detached-descendant cleanup unverified' not in raw}
else:
    gates = {'windows_exited_root_is_failed_closed': bool(windows['cleanup_errors'])
                 and 'cleanup unverified' in windows['cleanup_errors'][0],
             'taskkill_race_is_failed_closed': bool(race['cleanup_errors'])
                 and 'taskkill exited 128' in race['cleanup_errors'][0],
             'linux_dead_owner_is_explicitly_unverified': 'HARNESS_ERROR' in raw
                 and 'detached-descendant cleanup unverified' in raw,
             'linux_does_not_guess_reparented_process_ownership': linux['detached_child_alive']
                 and all(group != linux['detached_pid'] for group, sig in linux['attempted_group_signals']),
             'no_real_taskkill_or_pid_reuse_kill': windows['taskkill_call_count'] == 0
                 and race['root_kill_call_count'] == 0,
             'real_child_naturally_finished': windows['grandchild_naturally_finished_and_handle_signalled'],
             'only_expected_old_assertions_changed': [item['exception'] for item in outcomes]
                 == ['AssertionError: ', None, 'AssertionError: ']}
summary = {'phase': phase, 'python': sys.executable, 'argv': sys.argv,
           'gates': gates, 'control_outcomes': outcomes, 'passed': all(gates.values()),
           'unresolved_limit': 'Linux exceptional supervisor death can leave reparented detached descendants; '
                               'the fallback does not claim cleanup verified or kill unrelated PIDs.'}
with (stage / 'review.json').open('x', encoding='utf-8') as output:
    json.dump(summary, output, indent=2)
    output.write('\n')
hashes = [{'file': 'scripts/' + path.name,
           'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
          for path in sorted((stage / 'source/scripts').iterdir()) if path.is_file()]
with (stage / 'reviewed-source-hashes.json').open('x', encoding='utf-8') as output:
    json.dump(hashes, output, indent=2)
    output.write('\n')
print(json.dumps(summary, indent=2))
raise SystemExit(0 if summary['passed'] else 1)
