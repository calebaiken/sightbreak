#!/usr/bin/env python3
"""Independent SOURCE/PURE review; never invokes or compiles GDScript.

The action-prefix controls are synthetic copies of real baseline rows. They
exercise the first introduced matrix action through the frozen builder audit,
then deliberately stop before the next row. They are not candidate evidence.
"""
import ast
import copy
import gzip
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[5]
REPORT = ROOT / 'docs/reports/gauntlet/m5-exhausted-primary-selection'
BASE_REPORT = ROOT / 'docs/reports/gauntlet/m5-exhausted-primary-benchmark'
FREEZE = '1b7ebc71290e6c4c23017f7a2d8539d7c5eec149'
BASE = 'c7c95521200490305ff035e01951215b5980e4bb'


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


def policy(before, acquired, interact, distance, difficulty):
    """Preregistered rule, independent of the candidate oracle implementation."""
    active = before['weapon']
    own = before['inventory']
    cache = before['ammo_store']
    enabled = difficulty != 'easy'
    if acquired:
        if enabled and not interact and before['ammo'] == 0 and active != 'sidearm' and 'sidearm' in own and distance < 20:
            return 'sidearm'
    denied = [not enabled, interact, active not in ('smg', 'rifle', 'marksman'),
              before['ammo'] != 0, before['reserve'] != 0, 'sidearm' not in own,
              'sidearm' not in cache, acquired and distance > 45]
    if not any(denied) and max(cache['sidearm']) > 0:
        return 'sidearm'
    if not acquired and active == 'sidearm' and len(own) > 1:
        for primary in ('rifle', 'marksman', 'smg'):
            if primary in own and cache.get(primary, [-1, -1]) != [0, 0]:
                return primary
    return ''


class PrefixComplete(Exception):
    pass


def run():
    checks = 0
    def check(value, message):
        nonlocal checks
        checks += 1
        if not value:
            raise AssertionError(message)

    candidate = module('candidate', REPORT / 'audit_candidate.py')
    original = module('original', BASE_REPORT / 'independent-actual/audit_raw.py')
    raw = gzip.decompress((BASE_REPORT / 'actual-r2/baseline-probe.stdout.log.gz').read_bytes())
    check(hashlib.sha256(raw).hexdigest() == candidate.BASELINE_STDOUT_SHA256, 'original raw baseline hash')
    records, _ = candidate.parse(BASE_REPORT / 'actual-r2/baseline-probe.stdout.log.gz')
    baseline_audit = original.audit(copy.deepcopy(records), ROOT)
    sys.path.insert(0, str(BASE_REPORT / 'independent-actual'))
    old_falsifiers = module('old_falsifiers', BASE_REPORT / 'independent-actual/falsify_raw.py').falsifiers(records, ROOT)
    freeze = json.loads((REPORT / 'SOURCE_FREEZE.json').read_text())
    for filename, expected in freeze['sha256'].items():
        check(hashlib.sha256((ROOT / filename).read_bytes()).hexdigest() == expected, 'freeze hash ' + filename)
    check(git('merge-base', FREEZE, 'HEAD').decode().strip() == FREEZE, 'exact frozen source is review ancestor')
    check(not git('diff', FREEZE, '--', 'game', 'scripts', '.claude', 'AGENTS.md', 'CLAUDE.md',
                  'docs/roadmap', 'docs/engineering'), 'frozen source/instruction/mission bytes unchanged')
    diff_names = git('diff', '--name-only', BASE, FREEZE).decode().splitlines()
    outside_report = [p for p in diff_names if not p.startswith('docs/reports/gauntlet/m5-exhausted-primary-selection/')]
    check(outside_report == ['game/scripts/gameplay/bot_ai.gd', 'game/tests/bot_exhausted_primary_probe.gd',
          'game/tests/bot_exhausted_primary_probe.gd.uid', 'game/tests/bot_exhausted_primary_test.gd',
          'scripts/run_native_regressions.py', 'scripts/validate.sh'], 'exact product/test boundary')
    product = ROOT / 'game/scripts/gameplay/bot_ai.gd'
    delta = git('diff', '--unified=0', BASE, FREEZE, '--', 'game/scripts/gameplay/bot_ai.gd').decode()
    additions = [s[1:] for s in delta.splitlines() if s.startswith('+') and not s.startswith('+++')]
    deletions = [s for s in delta.splitlines() if s.startswith('-') and not s.startswith('---')]
    check(len(additions) == 10 and not deletions, 'ten additive product lines only')
    restored = product.read_text()
    # Remove complete inserted hunks, preserving repeated old source text.
    for hunk in delta.split('@@')[2::2]:
        block = ''.join(line[1:] + '\n' for line in hunk.splitlines() if line.startswith('+'))
        if block:
            check(restored.count(block) == 1, 'unique new hunk')
            restored = restored.replace(block, '', 1)
    check(restored.encode() == git('show', BASE + ':game/scripts/gameplay/bot_ai.gd'), 'all old product bytes preserved')
    check((ROOT / 'game/tests/bot_exhausted_primary_probe.gd').read_bytes() == git('show', 'b87afb7:game/tests/bot_exhausted_primary_probe.gd'), 'common probe exact original bytes')
    check((ROOT / 'game/tests/bot_exhausted_primary_probe.gd.uid').read_bytes() == (BASE_REPORT / 'actual-r2/preparation-generated-uids/game/tests/bot_exhausted_primary_probe.gd.uid').read_bytes(), 'UID exact preparation bytes')
    for path in ('actor.gd', 'weapons.gd', 'arena.gd', 'match.gd'):
        filename = 'game/scripts/gameplay/' + path
        check((ROOT / filename).read_bytes() == git('show', BASE + ':' + filename), 'protected source ' + filename)
    for filename in ('scripts/validate.sh', 'scripts/run_native_regressions.py'):
        regdiff = git('diff', '--unified=0', BASE, FREEZE, '--', filename).decode()
        check('Dummy' in regdiff and 'bot_exhausted_primary_test.gd' in regdiff, 'derived test registered ' + filename)
    native_log = module('native_log', ROOT / 'scripts/native_log.py')
    check(native_log.failed('WARNING: 2 ObjectDB instances were leaked at exit'), 'strict ObjectDB leak classifier')
    check(native_log.failed('Leaked instance: AudioStreamPlaybackWAV'), 'strict typed leak classifier')
    old_tree = ast.parse((BASE_REPORT / 'independent-actual/audit_raw.py').read_text())
    new_tree = ast.parse((REPORT / 'audit_candidate.py').read_text())
    helpers = ['close', 'add', 'sub', 'mul', 'dot', 'norm', 'overlap', 'slab',
               'world_trace', 'ellipsoid', 'sphere_span', 'target_trace', 'scenario']
    functions = lambda tree: {x.name: ast.dump(x, include_attributes=False) for x in tree.body if isinstance(x, ast.FunctionDef)}
    a, b = functions(old_tree), functions(new_tree)
    check(all(a[name] == b[name] for name in helpers), '13 inherited math/geometry helper ASTs')
    header = records[0][2]
    changes = {'CASE': [], 'STEP': []}
    for _, kind, row in records:
        if kind != 'CASE' and not (kind == 'STEP' and row['step'] == 0):
            continue
        scenario = row['scenario']
        acquired = scenario['target']['visible'] and row['enemy_before']['alive'] and scenario['target']['distance'] <= header['profiles'][scenario['difficulty']]['vision_range']
        check(bool(row['decision_bot_state']['target']) == acquired, 'independent initial acquisition')
        expected = policy(row['before'], acquired, scenario['objective'] != 'none', scenario['target']['distance'], scenario['difficulty'])
        if expected != row['command']['weapon']:
            check(expected == 'sidearm' and row['command']['weapon'] == '', 'only allowed new sidearm delta')
            changes[kind].append(row['label'])
    plan = candidate.planned_deltas(records)
    check(changes['CASE'] == plan['changed_matrix_labels'] and len(changes['CASE']) == 51, 'all exact matrix identities independently forecast')
    check(changes['STEP'] == plan['changed_first_sequence_labels'] and len(changes['STEP']) == 15, 'all exact sequence identities independently forecast')

    vector_count = 0
    for d, active, clip, reserve, side, owned, acquired, interacting, distance in itertools.product(
            ('easy', 'normal', 'hard'), ('smg', 'rifle', 'marksman', 'sidearm', 'unknown'),
            (0, 1), (0, 30), (None, [0, 0], [15, 0], [0, 15], [15, 60]),
            (False, True), (False, True), (False, True), (0, 6, 19.9999, 20, 24, 44.9, 45, 45.0001, 45.1, 60)):
        before = {'weapon': active, 'ammo': clip, 'reserve': reserve,
                  'inventory': [active] + (['sidearm'] if owned and active != 'sidearm' else []),
                  'ammo_store': {} if side is None else {'sidearm': side}}
        expected = policy(before, acquired, interacting, distance, d)
        actual = candidate.expected_weapon(before, acquired, interacting, distance, header['profiles'][d], header['weapon_definitions'])
        check(actual == expected, 'oracle vs independent policy vector ' + str(vector_count))
        vector_count += 1

    # Request comparator alone must not be mistaken for the action auditor.
    counterfeit = copy.deepcopy(records)
    for _, kind, row in counterfeit:
        if kind == 'CASE' and row['label'] in changes['CASE']:
            row['command'].update(weapon='sidearm', reload=False)
        if kind == 'STEP' and row['step'] == 0 and row['label'] in changes['STEP']:
            row['command']['weapon'] = 'sidearm'
    comparison = candidate.compare(counterfeit, records)
    check(comparison['preserved_common_action_rows'] == 1068, 'comparator positive control')
    try:
        candidate.audit(counterfeit, ROOT)
    except AssertionError as exc:
        comparator_limit = str(exc)
    else:
        raise AssertionError('request-only counterfeit accepted by full auditor')

    # Exercise the first introduced action, beyond the global inventory gate.
    label = changes['CASE'][0]
    prefix_rows = copy.deepcopy(records)
    row = next(r for _, k, r in prefix_rows if k == 'CASE' and r['label'] == label)
    row['command'].update(weapon='sidearm', reload=False)
    after = row['after_action']
    after['ammo_store'][after['weapon']] = [after['ammo'], after['reserve']]
    after.update(weapon='sidearm', ammo=15, reserve=0, deploy=.3,
                 actual_action_spread=header['weapon_definitions']['sidearm']['spread'] + .045)
    row['resources_after']['sidearm'].update(source='active_fields', clip=15, reserve=0)
    row['resources_after'][row['before']['weapon']].update(source='holstered_store', clip=0, reserve=0)
    row.update(switched=True, empty_reload_request=False, empty_fire_request=False)
    for kind, count in [('POLICY_HEADER', 1), ('POLICY_RANGE', 9), ('POLICY_RESERVE_STEP', 20), ('POLICY_RESERVE', 1), ('POLICY_RESULT', 1)]:
        prefix_rows[-1:-1] = [(9999, kind, {}) for _ in range(count)]

    line_start = next(node.lineno for node in ast.walk(new_tree) if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'ctx' for t in node.targets))
    def prefix_audit(rows):
        entered = False
        def trace(frame, event, arg):
            nonlocal entered
            if frame.f_code is candidate.audit.__code__ and event == 'line' and frame.f_lineno == line_start:
                if entered:
                    raise PrefixComplete()
                entered = frame.f_locals['r']['label'] == label
            return trace
        try:
            sys.settrace(trace)
            candidate.audit(rows, ROOT)
        except PrefixComplete:
            return True, 'entire introduced action row audited; deliberate stop before following row'
        except AssertionError as exc:
            return False, str(exc)
        finally:
            sys.settrace(None)
        raise AssertionError('unexpected full audit completion')

    accepted, reason = prefix_audit(prefix_rows)
    check(accepted, 'synthetic stock draw positive control: ' + reason)
    falsifiers = []
    def falsify(name, mutate, needle):
        rows = copy.deepcopy(prefix_rows)
        action = next(r for _, k, r in rows if k == 'CASE' and r.get('label') == label)
        mutate(action)
        accepted, reason = prefix_audit(rows)
        check(not accepted and needle in reason, name + ': ' + reason)
        falsifiers.append({'name': name, 'rejected': True, 'reason': reason})
    falsify('selection without stock draw', lambda r: r.update(after_action=copy.deepcopy(r['before']), switched=False,
            resources_after=copy.deepcopy(r['resources_before'])), 'complete shooter action consumption')
    falsify('instant draw without deploy cost', lambda r: r['after_action'].update(deploy=0), 'complete shooter action consumption')
    def forged_extra_round(r):
        r['after_action']['ammo'] = 16
        r['resources_after']['sidearm']['clip'] = 16
        r['equip_semantics_total_after'] += 1
    def forged_active_cache(r):
        r['after_action']['ammo_store']['smg'] = [30, 90]
        r['resources_after']['smg'].update(clip=30, reserve=90)
        r['equip_semantics_total_after'] += 120
    falsify('extra sidearm round with consistent projections', forged_extra_round, 'per-weapon conservation')
    falsify('stale active cache after equip with consistent projections', forged_active_cache, 'per-weapon conservation')
    falsify('decision resource mutation', lambda r: r['after_decision'].update(ammo=1), 'planning authority fences')
    falsify('decision target mutation', lambda r: r['enemy_after_decision'].update(health=99), 'planning authority fences')
    falsify('decision objective mutation', lambda r: r['objective_after_decision'].update(carrier=6), 'planning authority fences')
    falsify('unsettled world query', lambda r: r['lane']['pose_settle'].update(after_frame=0), 'settled world query')
    falsify('false shot on draw', lambda r: r.update(shot_delta=1), 'actual shot trigger')
    falsify('unexplained target damage', lambda r: r['enemy_after_action'].update(health=90), 'complete target action snapshot')
    falsify('unexplained reward', lambda r: r['after_action'].update(credits=1100), 'complete shooter action consumption')
    falsify('reload request alongside selection', lambda r: r['command'].update(reload=True), 'reload command cause')
    falsify('wrong resource source', lambda r: r['resources_after']['sidearm'].update(source='holstered_store'), 'raw resource projections')
    falsify('wrong physical lane', lambda r: r['lane'].update(ray_to=[99, 0, 0]), 'actual ray endpoints')
    return {'scope': 'SOURCE/PURE ONLY; synthetic oracle tests are not emitted candidate actions',
            'freeze': FREEZE, 'independent_checks': checks,
            'baseline_all_row_audit': baseline_audit,
            'original_all_row_falsifiers': old_falsifiers,
            'forecast': changes, 'policy_vectors': vector_count,
            'identical_inherited_helpers': helpers,
            'request_comparator_false_acceptance': {'accepted_request_only_counterfeit': True,
                'full_auditor_rejected': comparator_limit,
                'implication': 'compare() must be paired with audit() and strict native/source/process review'},
            'introduced_action_prefix': {'label': label, 'positive_control': reason,
                'negative_controls': falsifiers, 'entire_candidate_audit_exercised': False}}


if __name__ == '__main__':
    print(json.dumps(run(), indent=2, sort_keys=True))
