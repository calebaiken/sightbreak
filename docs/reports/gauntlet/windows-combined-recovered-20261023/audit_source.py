#!/usr/bin/env python3
"""Independent Git-object audit only. Does not import project runtime modules."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import re
import subprocess

BASE = '05277154c6b8c92b80fd7c25e8365de9efdc4fae'
CANDIDATE = 'b2e0293a546961230afbd73e5cd2a1a307d69e94'
OUT = Path(__file__).resolve().parent
CHECKS = {}


def git(*args):
    return subprocess.check_output(['git', *args])


def blob(commit, path):
    return git('show', commit + ':' + path)


def check(name, value):
    CHECKS[name] = bool(value)


def dump(tree):
    return ast.dump(tree, include_attributes=False)


def parse(commit, path):
    return ast.parse(blob(commit, path))


def assigned(tree, name):
    return next(node for node in tree.body if isinstance(node, ast.Assign)
                and any(isinstance(target, ast.Name) and target.id == name for target in node.targets))


def inventory(commit, directory):
    return git('ls-tree', '-r', '--name-only', commit, directory).decode().splitlines()


def identical(commit, paths):
    return {path: blob(commit, path) == blob(CANDIDATE, path) for path in paths}


def identity(commit):
    shipping = hashlib.sha256()
    resources = inventory(commit, 'game')
    for path in resources:
        relative = Path(path).relative_to('game')
        if '.godot' in relative.parts or 'tests' in relative.parts:
            continue
        shipping.update(relative.as_posix().encode() + b'\0' + blob(commit, path) + b'\0')
    validation = hashlib.sha256()
    for directory in ('scripts', '.github', 'game/tests'):
        for path in inventory(commit, directory):
            if any(part in ('__pycache__', '.godot') for part in Path(path).parts) or path.endswith('.pyc'):
                continue
            validation.update(path.encode() + b'\0' + blob(commit, path) + b'\0')
    return {'source_commit': commit, 'source_game_tree': git('rev-parse', commit + ':game').decode().strip(),
            'source_content_sha256_LF': shipping.hexdigest(),
            'source_validation_sha256_LF': validation.hexdigest(), 'game_resource_count': len(resources)}


# Derive the count from the accepted actual Windows summaries, then the exact
# separately accepted native dry-weapon result. Neither is new execution.
prior = json.loads(blob(CANDIDATE, 'docs/reports/gauntlet/windows-0527715-39741504894/raw-recomputed.json'))
summaries = prior['regressions']['native_test_summaries']
counts = {}
for name, lines in summaries.items():
    explicit = re.search(r'"?checks"?\s*[:=]\s*(\d+)', lines[0])
    counts[name] = int(explicit.group(1) if explicit else re.search(r'\d+', lines[0]).group())
dry_review = blob(CANDIDATE, 'docs/reports/gauntlet/m5-dry-weapon-recovered-independent/FINAL_REVIEW.md').decode()
check('accepted_dry_fixture_590_checks', '84 / 48 / 590 | 84 / 48 / 590' in dry_review)
old_runner = parse(BASE, 'scripts/run_native_regressions.py')
new_runner = parse(CANDIDATE, 'scripts/run_native_regressions.py')
old_suites = ast.literal_eval(assigned(old_runner, 'SUITES').value)
new_suites = ast.literal_eval(assigned(new_runner, 'SUITES').value)
counts['bot_dry_weapon'] = 590
check('prior_actual_total_8844', sum(value for name, value in counts.items() if name != 'bot_dry_weapon') == 8844)
check('fifteen_exact_suites_9434', len(new_suites) == 15 and set(new_suites) == set(counts) and sum(counts.values()) == 9434)
check('prior_order_preserved', tuple(suite for suite in new_suites if suite != 'bot_dry_weapon') == old_suites)
new_args = ast.literal_eval(assigned(new_runner, 'SUITE_ARGUMENTS').value)
check('only_two_dummy_exceptions', new_args == {
    'gunplay_rules': ['--headless', '--audio-driver', 'Dummy', '--script', 'res://tests/gunplay_rules_probe.gd'],
    'bot_dry_weapon': ['--headless', '--audio-driver', 'Dummy', '--script', 'res://tests/bot_dry_weapon_test.gd']})
normalized_runner = copy.deepcopy(new_runner)
assigned(normalized_runner, 'SUITES').value.elts = [node for node in assigned(normalized_runner, 'SUITES').value.elts
                                                if ast.literal_eval(node) != 'bot_dry_weapon']
arguments = assigned(normalized_runner, 'SUITE_ARGUMENTS').value
index = next(index for index, key in enumerate(arguments.keys) if ast.literal_eval(key) == 'bot_dry_weapon')
del arguments.keys[index]
del arguments.values[index]
check('runner_other_ast_exact_baseline', dump(normalized_runner) == dump(old_runner))

# Match the exact original workflow after removing only two Mac-only new steps
# and the ID added to the preexisting Mac-only menu step.
workflow_path = '.github/workflows/desktop-alpha.yml'
workflow = blob(CANDIDATE, workflow_path).decode()
start = workflow.index('      - name: ARM Mac ordinary exported gameplay source controls\n')
end = workflow.index('      - name: Real exported keyboard and pointer input (Windows/Linux)\n', start)
mac_block = workflow[start:end]
check('two_new_steps_strictly_arm_mac', mac_block.count('      - name: ') == 2
      and mac_block.count("matrix.os == 'macos-15'") == 2)
normalized_workflow = (workflow[:start] + workflow[end:]).replace('        id: macos_menu_input\n', '')
check('entire_other_workflow_exact_baseline', normalized_workflow.encode() == blob(BASE, workflow_path))
check('windows_lane_single_windows_latest', "inputs.lane == 'windows' && '[{\"os\":\"windows-latest\",\"target\":\"windows\"}]'" in workflow)
check('windows_diagnostic_flags_absent', '--linux-frame-diagnostics' not in workflow and '--linux-gpu-profile' not in workflow)

# Normalize only the additive opt-in Linux controller statements. Exact AST
# equality then protects every ordinary Windows command, predicate, deadline,
# reward formula, process/source receipt and cleanup statement at the baseline.
controller_path = 'scripts/verify_offline_match.py'
new_controller = parse(CANDIDATE, controller_path)
removed = []


class DefaultController(ast.NodeTransformer):
    def visit_ImportFrom(self, node):
        if node.module == 'linux_frame_sampler':
            removed.append('sampler_import')
            return None
        return node

    def visit_Expr(self, node):
        if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Attribute) and node.value.func.attr == 'add_argument':
            if node.value.args and isinstance(node.value.args[0], ast.Constant) and node.value.args[0].value in ('--linux-frame-diagnostics', '--linux-gpu-profile'):
                removed.append(node.value.args[0].value)
                return None
        return self.generic_visit(node)

    def visit_Assign(self, node):
        if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) and node.targets[0].id == 'frame_sampler':
            check('default_sampler_none', isinstance(node.value, ast.Constant) and node.value.value is None)
            removed.append('default_sampler_none')
            return None
        return self.generic_visit(node)

    def visit_If(self, node):
        attributes = {child.attr for child in ast.walk(node.test) if isinstance(child, ast.Attribute)
                      and isinstance(child.value, ast.Name) and child.value.id == 'args'}
        if attributes.intersection({'linux_frame_diagnostics', 'linux_gpu_profile'}):
            removed.append(ast.unparse(node.test))
            return None
        if dump(node.test) == dump(ast.parse('frame_sampler is not None', mode='eval').body):
            removed.append('sampler_cleanup_only_when_not_none')
            return None
        return self.generic_visit(node)


normalized_controller = DefaultController().visit(copy.deepcopy(new_controller))
check('default_controller_ast_exact_baseline', dump(normalized_controller) == dump(parse(BASE, controller_path)))
check('only_nine_expected_ast_removals', len(removed) == 9)
admission = blob(CANDIDATE, controller_path).decode()
check('linux_options_native_plant_180_seed_guard', all(text in admission for text in (
    "args.target != 'linux' or args.scenario != 'plant'", 'args.timeout != 180',
    'args.seed not in (None, 42)', 'or args.linux_frame_diagnostics')))

unchanged_paths = [
    'scripts/verify_offline_export.py', 'scripts/verify_integration_export.py', 'scripts/native_log.py',
    'scripts/native_observation.py', 'scripts/native_approach.py', 'scripts/build_manifest.py',
    'scripts/export.py', 'scripts/verify_builds.py', 'scripts/package_qa_receipts.py',
    'scripts/toolchain.py', '.gitattributes', 'game/project.godot', 'game/export_presets.cfg']
unchanged = identical(BASE, unchanged_paths)
check('all_named_guard_controller_binding_paths_unchanged', all(unchanged.values()))
check('backend_server_unchanged', not git('diff', '--name-only', BASE, CANDIDATE, '--', 'backend', 'server').strip())
game_changes = git('diff', '--name-only', BASE, CANDIDATE, '--', 'game').decode().splitlines()
shipping_changes = [path for path in game_changes if 'tests' not in Path(path).parts]
check('only_two_shipping_files_changed', shipping_changes == ['game/scripts/gameplay/bot_ai.gd', 'game/scripts/offline_diagnostics.gd'])

bot_path = 'game/scripts/gameplay/bot_ai.gd'
bot_delta = '\t\t\t\t\t# Missing holstered state keeps the actor\'s normal equip defaults.\n\t\t\t\t\tif actor._ammo_store.get(w_id, Vector2i(-1, -1)) == Vector2i.ZERO:\n\t\t\t\t\t\tcontinue\n'
check('bot_only_exact_accepted_three_line_guard', blob(CANDIDATE, bot_path).decode().replace(bot_delta, '').encode() == blob(BASE, bot_path))
component_equalities = {
    'dry_weapon': identical('8e8d13e', [bot_path, 'game/tests/bot_dry_weapon_test.gd', 'scripts/run_native_regressions.py']),
    'linux': identical('b1a131ab', [controller_path, 'scripts/linux_frame_sampler.py']),
    'frame_readbacks_root_integration': identical('de3c699b', ['game/scripts/offline_diagnostics.gd']),
    'mac': identical('3730273', ['scripts/macos_ordinary_input.py', 'scripts/verify_macos_ordinary.py',
                              'scripts/test_macos_ordinary.py', 'scripts/test_macos_ordinary_controller.py',
                              'scripts/test_macos_ordinary_paths.py']),
    'market_oracle': identical('985a9d71', ['scripts/postgres_receipt_oracle.py', 'scripts/test_postgres_receipt_recovery.py',
                                         'scripts/test_postgres_receipt_refresh.py'])}
for component, results in component_equalities.items():
    check('component_exact_' + component, all(results.values()))
observer_path = 'game/scripts/offline_diagnostics.gd'
observer = blob(CANDIDATE, observer_path).decode()
start = observer.index('\tvar read_begin_usec := Time.get_ticks_usec()\n')
end = observer.index('\tif local != null:\n', start)
telemetry = observer[start:end]
check('observer_other_bytes_exact_baseline', (observer[:start] + observer[end:]).encode() == blob(BASE, observer_path))
check('telemetry_exact_22_added_lines', len(telemetry.splitlines()) == 22)

result = {'candidate': CANDIDATE, 'baseline_actual_windows_source': BASE,
          'checks': CHECKS, 'all_checks_passed': all(CHECKS.values()),
          'source_identity': identity(CANDIDATE), 'expected_suite_checks': {name: counts[name] for name in new_suites},
          'expected_total': sum(counts.values()), 'unchanged_named_paths': unchanged,
          'component_equalities': component_equalities, 'shipping_changes': shipping_changes,
          'all_game_changes': game_changes, 'removed_default_controller_ast_nodes': removed,
          'source_diff_numstat': git('diff', '--numstat', BASE, CANDIDATE, '--', 'game', 'scripts', '.github').decode(),
          'scope': 'Independent Git-object/source comparison; no native execution or new Windows evidence.'}
(OUT / 'source-audit.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({'all_checks_passed': result['all_checks_passed'], 'checks': len(CHECKS),
                  'failed': [name for name, value in CHECKS.items() if not value],
                  'identity': result['source_identity'], 'expected_total': result['expected_total']}))
raise SystemExit(0 if result['all_checks_passed'] else 1)
