"""Independent exact union, source boundary and falsifier audit; no engine."""
import ast
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
BASE = '28a3e294'
FINAL = '49ae54b0e4f5d880bdf06e4eb783a616b2dff684'
COMPONENT = 'a4899dd5534553ae832a433dd704f3539914a421'
SHALLOW = Path('/workspace/reviews/windows-pulse-combined-depth-one-isolated')
CHECKS = []


def git(*args, root=ROOT):
    return subprocess.check_output(['git', *args], cwd=root)


def check(name, result, detail=None):
    CHECKS.append({'check': name, 'pass': bool(result), 'detail': detail})
    if not result:
        raise AssertionError(name)


def source(ref, path):
    return git('show', f'{ref}:{path}').decode()


def tree(ref):
    result = {}
    for entry in git('ls-tree', '-rz', ref).split(b'\0'):
        if entry:
            meta, path = entry.split(b'\t', 1)
            result[path.decode()] = meta.decode()
    return result


def dump(node):
    return ast.dump(node, include_attributes=False)


def normalized(path):
    value = ast.parse(source(FINAL, path))
    if path.endswith('verify_integration_export.py'):
        cls = next(n for n in value.body if isinstance(n, ast.ClassDef) and n.name == 'WinUI')
        cls.body = [n for n in cls.body if not isinstance(n, ast.FunctionDef) or n.name != 'key_pulse']
    else:
        class RemoveDeclaredExtension(ast.NodeTransformer):
            def visit_FunctionDef(self, node):
                if node.name == 'settings_route_pulse':
                    return None
                if node.name in ('approach_floor', 'relocate_settings_actor'):
                    idx = next(i for i, arg in enumerate(node.args.kwonlyargs) if arg.arg == 'pulse')
                    node.args.kwonlyargs.pop(idx)
                    node.args.kw_defaults.pop(idx)
                return self.generic_visit(node)

            def visit_If(self, node):
                if dump(node.test) == dump(ast.parse('fine and pulse is not None', mode='eval').body):
                    return [self.visit(n) for n in node.orelse]
                return self.generic_visit(node)

            def visit_Call(self, node):
                if isinstance(node.func, ast.Name) and node.func.id in ('approach_floor', 'relocate_settings_actor'):
                    node.keywords = [kw for kw in node.keywords if kw.arg != 'pulse']
                return self.generic_visit(node)
        value = RemoveDeclaredExtension().visit(value)
    return value


assert sorted(os.sched_getaffinity(0)) == [4]
before, after, component = tree(BASE), tree(FINAL), tree(COMPONENT)
paths = ['scripts/' + name for name in ('native_approach.py', 'native_settings_route.py',
         'test_native_route_pulse.py', 'validate.sh', 'verify_integration_export.py', 'verify_offline_export.py')]
changed = sorted(p for p in before.keys() | after.keys() if not p.startswith('docs/') and before.get(p) != after.get(p))
check('exact_six_non_doc_delta', changed == sorted(paths), changed)
non_doc = [p for p in before if not p.startswith('docs/')]
check('all_other_non_doc_modes_and_objects_preserved', all(before[p] == after.get(p) for p in non_doc if p not in paths), len(non_doc))
check('five_incoming_files_exact_component_modes_and_blobs', all(after[p] == component[p] for p in paths if p != 'scripts/validate.sh'))
base_validate = source(BASE, 'scripts/validate.sh')
marker = 'python3 scripts/test_native_settings_route.py -v\n'
addition = 'python3 scripts/test_native_route_pulse.py -v\n'
expected = base_validate.replace(marker, marker + addition)
actual = source(FINAL, 'scripts/validate.sh')
check('independent_validate_union_exact', base_validate.count(marker) == 1 and actual == expected)
registrations = ['run_godot bot-exhausted-primary --headless --audio-driver Dummy --script res://tests/bot_exhausted_primary_test.gd',
                 'python3 scripts/test_native_log.py -v', addition.rstrip('\n')]
check('each_existing_and_new_registration_exactly_once', all(actual.count(row) == 1 for row in registrations), registrations)
check('preserved_registration_order', actual.index(registrations[0]) < actual.index(registrations[1]) < actual.index(registrations[2]))
check('validate_executable_mode_preserved', before['scripts/validate.sh'] == after['scripts/validate.sh'] or (before['scripts/validate.sh'].split()[0] == after['scripts/validate.sh'].split()[0] == '100755'))
game = [p for p in before if p.startswith('game/')]
uids = [p for p in game if p.endswith('.uid')]
check('game_tree_exact', all(before[p] == after.get(p) for p in game) and set(game) == {p for p in after if p.startswith('game/')}, len(game))
check('all_138_uid_paths_and_modes_exact', len(uids) == 138 and all(before[p] == after.get(p) for p in uids), len(uids))
for path in ('scripts/verify_integration_export.py', 'scripts/native_approach.py', 'scripts/native_settings_route.py', 'scripts/verify_offline_export.py'):
    check('unchanged_ast_outside_declared_extension:' + path, dump(normalized(path)) == dump(ast.parse(source(BASE, path))))
check('root_own_source_exact_freeze', not git('diff', '--name-only', FINAL, 'HEAD', '--', '.', ':!docs/**').strip())
check('own_materialized_scripts_exact_freeze', all((ROOT / p).read_bytes() == git('show', f'{FINAL}:{p}') for p in after if p.startswith('scripts/')))
check('shallow_exact_head', git('rev-parse', 'HEAD', root=SHALLOW).decode().strip() == FINAL)
check('shallow_single_commit', git('rev-list', '--count', 'HEAD', root=SHALLOW).strip() == b'1')
check('shallow_boundary_real', git('rev-parse', '--is-shallow-repository', root=SHALLOW).strip() == b'true')
check('shallow_no_docs_materialized', not (SHALLOW / 'docs').exists())
check('shallow_no_remote_for_lazy_history_fetch', not git('remote', root=SHALLOW).strip())
check('shallow_required_current_fixture_exact', (SHALLOW / 'game/export_presets.cfg').read_bytes() == git('show', f'{FINAL}:game/export_presets.cfg'))
parent = git('rev-parse', f'{FINAL}^').decode().strip()
check('shallow_parent_object_absent', subprocess.run(['git', 'cat-file', '-e', parent], cwd=SHALLOW, capture_output=True, env=dict(os.environ, GIT_NO_LAZY_FETCH='1')).returncode != 0)
check('shallow_all_scripts_modes_blobs_exact', all((SHALLOW / p).read_bytes() == git('show', f'{FINAL}:{p}') for p in after if p.startswith('scripts/')))
check('shallow_no_alternates', not (SHALLOW / '.git/objects/info/alternates').exists())
check('original_prereg_identity', hashlib.sha256((OUT / 'PREREGISTRATION.md').read_bytes()).hexdigest() == '24fa284b1c594566860d596643ce1b41eee9133040e6778c932efed3139ffd07')
for name in ('original_controls.py', 'semantic_controls.py', 'boundary_controls.py', 'audit_source_and_originals.py'):
    expected_control = git('show', f'791998d3:docs/reports/gauntlet/windows-route-pulse-r2-independent-20261023/{name}')
    check('original_control_bytes_exact:' + name, (OUT / name).read_bytes() == expected_control)
for row in registrations:
    check('weakening_rejected_registration:' + row.split()[1], actual.replace(row + '\n', '') != expected)
weak_map = deepcopy(after)
weak_map['game/project.godot'] = '100644 blob counterfeited'
check('weakening_rejected_product_change', sorted(p for p in before.keys() | weak_map.keys() if not p.startswith('docs/') and before.get(p) != weak_map.get(p)) != sorted(paths))
check('weakening_rejected_scope_ast', dump(ast.parse(source(BASE, 'scripts/native_settings_route.py').replace('<= 100', '<= 101'))) != dump(normalized('scripts/native_settings_route.py')))
benchmark = json.loads((OUT / 'aggregate-input-inventory-benchmark.json').read_text())
inputs = benchmark['inventory']
check('all_808_benchmark_inputs_rebound_to_exact_base', len(inputs) == 808 and all(before[row['path']] == row['mode'] + ' blob ' + row['git_blob'] for row in inputs))
check('all_808_existing_input_modes_preserved', all(after[row['path']].split()[0] == row['mode'] for row in inputs))
check('all_803_unchanged_input_objects_exact', sum(row['path'] not in paths for row in inputs) == 803 and all(before[row['path']] == after[row['path']] for row in inputs if row['path'] not in paths))
protected_prefixes = ('game/', 'scripts/', 'backend/', 'server/', '.github/', 'docs/reports/gauntlet/native-layout-ocr/', 'docs/reports/media/art-v9/hands/logs/')
current_inputs = {p for p in after if p.startswith(protected_prefixes)}
check('new_exact_input_union_has_809_paths', current_inputs == {row['path'] for row in inputs} | {'scripts/test_native_route_pulse.py'}, len(current_inputs))
command_ledger = json.loads((OUT / 'command-count-ledger.json').read_text())
check('all_14_154_actual_maintained_groups_zero_exit_both_checkouts', command_ledger['group_count'] == 14 and command_ledger['discovered_methods'] == 154 and all(row['own_exit'] == row['shallow_exit'] == 0 for row in command_ledger['current_validate_derived_and_actually_executed']))
check('original_windows_skips_only_and_additional_default_Mac_20_passes', command_ledger['original_windows_skips'] == 3 and sum(row['methods'] for row in command_ledger['additional_component_groups']) == 20 and all(row['own_exit'] == row['shallow_exit'] == 0 for row in command_ledger['additional_component_groups']))
result = {'source': FINAL, 'base': git('rev-parse', BASE).decode().strip(), 'component': COMPONENT,
          'cpu_affinity': sorted(os.sched_getaffinity(0)), 'checks': CHECKS,
          'six_files': {p: {'mode_blob': after[p], 'sha256': hashlib.sha256(git('show', f'{FINAL}:{p}')).hexdigest()} for p in paths}}
(OUT / 'source-union-results.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({'checks': len(CHECKS), 'pass': all(r['pass'] for r in CHECKS), 'source': FINAL, 'non_doc_paths': len(non_doc), 'game_paths': len(game), 'uids': len(uids), 'cpu_affinity': result['cpu_affinity']}, indent=2))
