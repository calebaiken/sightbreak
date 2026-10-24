"""Independent source/default-path comparison and original trace audit. No native work."""
import ast
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess

BASE = 'e28c8e90b9ef2d0c766bd9152c194e3197ceba9a'
SOURCE = 'a4899dd5534553ae832a433dd704f3539914a421'
HANDOFF = 'd3b0fc1676b8904b96f69cf738edb0c312f1981a'
OUT = Path(__file__).parent

def git(*args):
    return subprocess.check_output(['git', *args])

def file_at(ref, path):
    return git('show', ref + ':' + path)

def tree_at(ref, path):
    return git('rev-parse', ref + ':' + path).decode().strip()

def dump(tree):
    return ast.dump(tree, include_attributes=False)

def parse(ref, path):
    return ast.parse(file_at(ref, path))

def strip_arg(node, name):
    index = [a.arg for a in node.args.kwonlyargs].index(name)
    node.args.kwonlyargs.pop(index)
    node.args.kw_defaults.pop(index)

checks = {}
path = 'scripts/verify_integration_export.py'
new = parse(SOURCE, path)
winui = next(n for n in new.body if isinstance(n, ast.ClassDef) and n.name == 'WinUI')
winui.body = [n for n in winui.body if getattr(n, 'name', None) != 'key_pulse']
checks['all_existing_WinUI_and_other_module_AST_unchanged'] = dump(new) == dump(parse(BASE, path))

path = 'scripts/native_approach.py'
new = parse(SOURCE, path)
function = next(n for n in new.body if isinstance(n, ast.FunctionDef) and n.name == 'approach_floor')
strip_arg(function, 'pulse')
for parent in ast.walk(new):
    body = getattr(parent, 'body', None)
    if not isinstance(body, list): continue
    for index, node in enumerate(body):
        if isinstance(node, ast.If) and ast.unparse(node.test) == 'fine and pulse is not None':
            body[index:index+1] = deepcopy(node.orelse)
            break
checks['default_approach_and_coarse_path_AST_unchanged'] = dump(new) == dump(parse(BASE, path))

path = 'scripts/native_settings_route.py'
new = parse(SOURCE, path)
strip_arg(next(n for n in new.body if isinstance(n, ast.FunctionDef) and n.name == 'relocate_settings_actor'), 'pulse')
for node in ast.walk(new):
    if isinstance(node, ast.Call) and getattr(node.func, 'id', None) == 'approach_floor':
        node.keywords = [kw for kw in node.keywords if kw.arg != 'pulse']
checks['all_route_bounds_health_identity_weapon_settle_guards_AST_unchanged'] = dump(new) == dump(parse(BASE, path))

path = 'scripts/verify_offline_export.py'
new = parse(SOURCE, path)
for parent in ast.walk(new):
    body = getattr(parent, 'body', None)
    if isinstance(body, list):
        body[:] = [n for n in body if not (isinstance(n, ast.FunctionDef) and n.name == 'settings_route_pulse')]
for node in ast.walk(new):
    if isinstance(node, ast.Call) and getattr(node.func, 'id', None) == 'relocate_settings_actor':
        value = next(kw.value for kw in node.keywords if kw.arg == 'pulse')
        checks['Windows_only_route_hook'] = ast.unparse(value) == "settings_route_pulse if args.target == 'windows' else None"
        node.keywords = [kw for kw in node.keywords if kw.arg != 'pulse']
checks['other_controller_caps_schedules_OCR_and_gameplay_assertions_AST_unchanged'] = dump(new) == dump(parse(BASE, path))

protected = ['game', '.github', 'scripts/toolchain.py', 'scripts/native_focus_fence.py']
protected_trees = {p: {'base': tree_at(BASE, p), 'candidate': tree_at(SOURCE, p)} for p in protected}
checks['protected_game_CI_toolchain_focus_exact'] = all(v['base'] == v['candidate'] for v in protected_trees.values())
checks['handoff_changes_no_script_source'] = not git('diff', '--name-only', SOURCE, HANDOFF, '--', 'scripts').strip()
oldvalidate, newvalidate = file_at(BASE, 'scripts/validate.sh'), file_at(SOURCE, 'scripts/validate.sh')
checks['validate_only_adds_pure_pulse_group'] = newvalidate.replace(b'python3 scripts/test_native_route_pulse.py -v\n', b'') == oldvalidate

original_root = Path('/workspace/reviews/windows-native-e28c8e9/.local/e28-actual/receipts/evidence')
declared = json.loads((OUT.parent/'windows-route-pulse-20261023/original-failed-trace.json').read_bytes())
raw = {}
for binding in declared['bindings']:
    payload = (original_root/binding['path']).read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    checks['raw_digest_' + binding['path']] = digest == binding['sha256'] and len(payload) == binding['bytes']
    raw[binding['path']] = json.loads(payload)

result, actions, legacy = (raw[p] for p in ['offline-input/results.json', 'offline-input/actions.json', 'reload-legacy-delayed/results.json'])
route = result['settings_cover_route']
checks['original_base_and_failure_preserved'] = result['source']['source_commit'] == BASE and result['passed'] is False
checks['retained_full_route_equal_original'] = declared['original_failed_route'] == route
checks['retained_original_route_error_equal'] = declared['original_route_error'] == result['error']
checks['legacy_original_still_failed'] = legacy['passed'] is False and declared['original_legacy_failure'] == {
    'passed': False, 'error': legacy.get('error'), 'elapsed_seconds': legacy.get('elapsed_seconds')}
pulses = []
for start, row in enumerate(actions):
    if row.get('event') != 'settings_route_movement_control' or row.get('mode') != 'pulse': continue
    end = next(i for i in range(start+1, len(actions)) if actions[i].get('event') == 'settings_route_movement_pulse_released')
    edges = [r for r in actions[start+1:end+1] if r.get('event') in ('key_before', 'key_after')]
    down = next(r for r in edges if r.get('event') == 'key_after' and r.get('down') is True)
    up = next(r for r in edges if r.get('event') == 'key_after' and r.get('key') == down['key'] and r.get('down') is False and r['seconds'] > down['seconds'])
    pulses.append({'request': row, 'all_driver_edges': edges, 'selected_down_after': down, 'selected_up_after': up,
                   'after_call_driver_bracket_seconds': up['seconds']-down['seconds']})
checks['retained_pulses_equal_all_original_edges'] = pulses == declared['pulses']
for path, digest in declared['inspected_original_source_sha256'].items():
    checks['original_source_digest_' + path] = hashlib.sha256(file_at(BASE, path)).hexdigest() == digest
paths = ['scripts/verify_integration_export.py', 'scripts/verify_offline_export.py', 'scripts/native_approach.py',
         'scripts/native_settings_route.py', 'scripts/test_native_route_pulse.py', 'scripts/validate.sh']
binding = {p: hashlib.sha256(file_at(SOURCE, p)).hexdigest() for p in paths}
previous, rejected = (route['precondition_loss'][n] for n in ('previous_valid_state', 'rejected_state'))
report = {'source': SOURCE, 'handoff': HANDOFF, 'base': BASE, 'checks': checks, 'protected_git_objects': protected_trees,
          'source_sha256': binding, 'changed_paths': git('diff','--name-only',BASE,SOURCE).decode().splitlines(),
          'original_bindings': declared['bindings'], 'last_valid_actor': previous['local_actor'],
          'rejected_actor': rejected['local_actor'], 'rejected_tick': rejected['simulation_tick'],
          'pulse_requests': [p['request']['pulse_wall_seconds'] for p in pulses],
          'driver_after_call_brackets': [p['after_call_driver_bracket_seconds'] for p in pulses],
          'legacy_error': legacy.get('error'),
          'limits': 'All controls are source and mock only. Driver brackets do not prove physical hold or cause.'}
(OUT/'source-and-originals.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps({'checks':len(checks), 'failed':[k for k,v in checks.items() if not v], 'source_sha256':binding},indent=2))
assert all(checks.values())
