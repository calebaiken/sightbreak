#!/usr/bin/env python3
"""Independent read-only source/stage/recipe audit; no engine calls."""
import ast
import hashlib
import json
from pathlib import Path
import re
import subprocess
import time

ROOT = Path(__file__).resolve().parents[4]
REPORT = Path(__file__).resolve().parent
PACKET = ROOT / 'docs/reports/gauntlet/m6-touch-contrast-recovered'
SOURCE = '108d1cdc6cf471daa7390298c234bb1c087ae865'
OLD_SOURCE = 'b001fc5087960729535f63c896b40d6dc25bd272'
BASELINE = 'a52022169241df9ff662039547a375e1c46ac1c5'
HANDOFF = 'b9bd7e62c70d3f5a061c4177ede6c73c21dc9d35'
TOUCH = 'game/scripts/ui/touch_controls.gd'
OLD_LINE = '\t\tvar compact := key != "fire" and r < 32.0'
NEW_LINE = '\t\tvar compact: bool = key != "fire" and r < 32.0'
RECEIPT = {'scope': 'SOURCE/PURE ONLY', 'source': SOURCE, 'handoff': HANDOFF,
           'engine_invocations': 0, 'native_captures': 0, 'checks': []}


def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args])


def sha(data):
    return hashlib.sha256(data).hexdigest()


def record(name, **detail):
    RECEIPT['checks'].append({'name': name, 'pass': True, **detail})


def program(text):
    tree = ast.parse(text)
    fn = next(x for x in tree.body if isinstance(x, ast.FunctionDef) and x.name == 'paint_program')
    fn.decorator_list = []
    ns = {'re': re}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[fn], type_ignores=[])), 'critic-paint-parser', 'exec'), ns)
    return ns['paint_program']


def entries(manifest):
    return manifest['files'] + manifest['fixture'] + [
        {'path': 'game/tests/touch_contrast_instrumented.gd', 'sha256': manifest['instrumented_sha256']},
        {'path': 'game/tests/touch_contrast_instrumented.gd.uid', 'sha256': manifest['instrumented_uid_sha256']}]


def main():
    start = time.monotonic()
    old = git('show', OLD_SOURCE + ':' + TOUCH)
    new = git('show', SOURCE + ':' + TOUCH)
    assert old.count(OLD_LINE.encode()) == 1
    assert new == old.replace(OLD_LINE.encode(), NEW_LINE.encode(), 1)
    assert git('diff', '--name-only', OLD_SOURCE, SOURCE, '--', 'game').decode().splitlines() == [TOUCH]
    assert git('diff', '--name-only', OLD_SOURCE, SOURCE, '--', 'scripts').decode().splitlines() == [
        'scripts/test_touch_declaration_r4b_r3.py', 'scripts/touch_geometry_r4b.py']
    assert git('merge-base', '--is-ancestor', '439bd259', '08548776') == b''
    assert git('merge-base', '--is-ancestor', '08548776', SOURCE) == b''
    record('product-exact-one-annotation', before_sha256=sha(old), after_sha256=sha(new),
           all_other_tracked_game_bytes_identical=True, preregistrations_precede_code=True)

    helper_path = 'scripts/touch_geometry_r4b.py'
    before = git('show', OLD_SOURCE + ':' + helper_path).decode()
    after = git('show', SOURCE + ':' + helper_path).decode()
    trees = [ast.parse(text) for text in (before, after)]
    for tree in trees:
        tree.body = [x for x in tree.body if not (isinstance(x, ast.FunctionDef) and x.name == 'paint_program')]
    assert ast.dump(trees[0], include_attributes=False) == ast.dump(trees[1], include_attributes=False)
    original, corrected = program(before), program(after)
    expected = original(old.decode())
    assert len(expected) == 8
    for text in (old.decode(), new.decode()):
        actual = corrected(text)
        assert [x[0] for x in actual] == [x[0] for x in expected]
        for (_, observed), (_, previous) in zip(actual, expected):
            assert (observed.co_code, observed.co_consts, observed.co_names, observed.co_varnames) == (
                previous.co_code, previous.co_consts, previous.co_names, previous.co_varnames)
    try:
        original(new.decode())
    except AttributeError:
        pass
    else:
        raise AssertionError('original parser unexpectedly accepts bool declaration')
    rejected = []
    replacements = [NEW_LINE.replace(': bool =', ': ' + t + ' =') for t in
                    ('int', 'float', 'Variant', 'String', 'boolish', 'BOOL', 'Array[bool]')]
    replacements += [NEW_LINE.replace('compact:', 'compact :'), NEW_LINE.replace(': bool =', ': bool :='),
                     NEW_LINE.replace(': bool =', ':='), NEW_LINE + ' # comment',
                     NEW_LINE.replace(' = ', '  = '), NEW_LINE.replace('var compact', 'const compact'),
                     '', NEW_LINE + '\n' + NEW_LINE, NEW_LINE + '\n' + OLD_LINE]
    expression = 'key != "fire" and r < 32.0'
    expressions = ['key == "fire" and r < 32.0', 'key != "fire" and r <= 32.0',
                   'key != "fire" and r < 32', 'key != "fire" and r < 32.00',
                   'key != "fire" or r < 32.0', 'r < 32.0 and key != "fire"',
                   '(' + expression + ')', 'bool(' + expression + ')', 'True',
                   expression + ' and True', expression + ' ', expression.replace('key', 'action')]
    replacements += [form.replace(expression, changed) for form in (OLD_LINE, NEW_LINE) for changed in expressions]
    for declaration in replacements:
        try:
            corrected(new.decode().replace(NEW_LINE, declaration, 1))
        except (ValueError, AttributeError):
            rejected.append(declaration)
        else:
            raise AssertionError('unsupported declaration accepted: ' + repr(declaration))
    record('lexical-accommodation-exact-programs-and-falsifiers', helper_sha256=sha(after.encode()),
           outside_function_ast_identical=True, accepted_forms=2, expression_programs_each=8,
           legacy_typed_rejection='AttributeError', rejected_declaration_cases=len(rejected),
           rejected_declarations=rejected)

    freeze_path = PACKET / 'SOURCE_FREEZE-r4b-r3.json'
    assert sha(freeze_path.read_bytes()) == '4282c67c984b1840ca43158b16c0ecb03f4254d01e5cb300478682cc8adbe921'
    assert freeze_path.read_bytes() == git('show', HANDOFF + ':' + str(freeze_path.relative_to(ROOT)))
    freeze = json.loads(freeze_path.read_text())
    assert len(freeze['frozen_files']) == len({x['path'] for x in freeze['frozen_files']}) == 24
    for row in freeze['frozen_files']:
        data = (ROOT / row['path']).read_bytes()
        assert data == git('show', SOURCE + ':' + row['path'])
        assert len(data) == row['bytes'] and sha(data) == row['sha256']
    analyzer = (ROOT / 'scripts/analyze_touch_contrast_r4b.py').read_bytes()
    assert analyzer == git('show', OLD_SOURCE + ':scripts/analyze_touch_contrast_r4b.py')
    assert sha(analyzer) == 'c47bb2fd7a3b8eab83765fd75ee76885815fc5ae467ffac6b99859e72be05141'
    record('complete-freeze-and-native-method-exact', frozen_files=24, freeze_sha256=sha(freeze_path.read_bytes()),
           native_analyzer_sha256=sha(analyzer), original_thresholds_and_predicates_unchanged=True)

    stage = Path('/workspace/sightbreak-touch-contrast-fixture-recovered-r4b-r3')
    oldstage = Path('/workspace/sightbreak-touch-contrast-fixture-recovered-r4b-r2')
    for variant, source in [('baseline', BASELINE), ('candidate', SOURCE)]:
        current_root, previous_root = stage / variant, oldstage / variant
        current = json.loads((current_root / 'SOURCE.json').read_text())
        previous = json.loads((previous_root / 'SOURCE.json').read_text())
        expected = next(x for x in freeze['fixtures'] if x['name'] == variant)
        assert sha((current_root / 'SOURCE.json').read_bytes()) == expected['manifest_sha256']
        assert (current_root / 'SOURCE.json').read_bytes() == (PACKET / (variant + '-SOURCE-r4b-r3.json')).read_bytes()
        assert (previous_root / 'SOURCE.json').read_bytes() == (PACKET / (variant + '-SOURCE-r4b-r2.json')).read_bytes()
        assert current['source'] == source
        tracked = git('ls-tree', '-r', '--name-only', source, 'game').decode().splitlines()
        assert tracked == [x['path'] for x in current['files']] and len(tracked) == 323
        rows = entries(current)
        assert len(rows) == len({x['path'] for x in rows}) == 327
        assert {str(p.relative_to(current_root)) for p in current_root.rglob('*') if p.is_file()} == {x['path'] for x in rows} | {'SOURCE.json'}
        assert not list(current_root.rglob('.godot'))
        for row in rows:
            data = (current_root / row['path']).read_bytes()
            assert sha(data) == row['sha256']
            if 'bytes' in row:
                assert len(data) == row['bytes']
        for row in current['files']:
            assert (current_root / row['path']).read_bytes() == git('show', source + ':' + row['path'])
        assert len(entries(previous)) == 327
        for row in entries(previous):
            data = (previous_root / row['path']).read_bytes()
            assert sha(data) == row['sha256']
            if 'bytes' in row:
                assert len(data) == row['bytes']
            expected_data = data.replace(OLD_LINE.encode(), NEW_LINE.encode(), 1) if variant == 'candidate' and row['path'] in (TOUCH, 'game/tests/touch_contrast_instrumented.gd') else data
            assert (current_root / row['path']).read_bytes() == expected_data, row['path']
        assert current['instrumentation'] == previous['instrumentation']
        uids = [(current_root / x['path']).read_bytes() for x in rows if x['path'].endswith('.uid')]
        assert len(uids) == len(set(uids)) == 138
        record('staging-' + variant, original_git_paths=323, verified_paths=327, distinct_copied_uids=138,
               source=source, manifest_sha256=expected['manifest_sha256'],
               old_stage_327_paths_and_manifest_unchanged=True, exact_wrapper_delta=True, no_godot_cache=True)

    oldraw = Path('/workspace/sightbreak-touch-contrast-native-recovered-r4b-r2')
    payload_path = PACKET / 'native-r4b-r2/payload-manifest.json'
    assert payload_path.read_bytes() == git('show', '384d17d0:docs/reports/gauntlet/m6-touch-contrast-recovered/native-r4b-r2/payload-manifest.json')
    payload = json.loads(payload_path.read_text())
    assert len(payload['files']) == 628 and payload['png_count'] == 0 and payload['acquisition_complete'] is False
    assert {str(p.relative_to(oldraw)) for p in oldraw.rglob('*') if p.is_file()} == {x['path'] for x in payload['files']}
    for row in payload['files']:
        data = (oldraw / row['path']).read_bytes()
        assert len(data) == row['bytes'] and sha(data) == row['sha256']
    assert not Path('/workspace/sightbreak-touch-contrast-native-recovered-r4b-r3').exists()
    record('failed-r2-raw-preserved-and-new-raw-absent', original_payload_files=628,
           raw_bytes=sum(x['bytes'] for x in payload['files']), png_count=0,
           acquisition_complete=False, native_import='FAIL unchanged', future_raw_root_absent=True)

    recipe = PACKET / 'acquisition-r4b-r3'
    oldrecipe = PACKET / 'acquisition-r4b-r2'
    controller = (recipe / 'controller.py').read_text()
    previous_controller = (oldrecipe / 'controller.py').read_text()
    assert controller.count('SOURCE_FREEZE-r4b-r3.json') == 3
    assert controller.replace('SOURCE_FREEZE-r4b-r3.json', 'SOURCE_FREEZE-r4b-r2.json') == previous_controller
    assert (oldraw / 'controller.py').read_text() == previous_controller
    package = (recipe / 'package_evidence.py').read_text()
    previous_package = (oldrecipe / 'package_evidence.py').read_text()
    assert package.replace('native-r4b-r3', 'native-r4b-r2').replace(SOURCE, OLD_SOURCE) == previous_package
    assert (oldraw / 'package_evidence.py').read_text() == previous_package
    plan = (recipe / 'PLAN.md').read_text()
    snippets = re.findall(r"python3 - <<'PY'\n(.*?)\nPY", plan, re.S)
    assert len(snippets) == 3
    for i, snippet in enumerate(snippets):
        compile(snippet, 'review-plan-inline-' + str(i), 'exec')
    verification = json.loads((recipe / 'verification.json').read_text())
    for name, expected in verification['packet_files'].items():
        data = (recipe / name).read_bytes()
        assert sha(data) == expected['sha256'] and len(data) == expected['bytes']
    template = json.loads((recipe / 'lane-start.template.json').read_text())
    assert template['attempt_limit'] == 1 and template['display'] == ':131'
    assert template['taskset'] == [0,1,2,3] and template['LP_NUM_THREADS'] == template['OMP_NUM_THREADS'] == '2'
    assert template['freeze_sha256'] == sha(freeze_path.read_bytes())
    record('recipe-identity-only', controller_sha256=sha(controller.encode()),
           controller_exactly_three_freeze_literals=True, archive_exactly_source_report_literals=True,
           packet_files_checked=len(verification['packet_files']), inline_python_syntax_checked=3,
           original_caps_order_cpu_threads_display_private_state_fences_cleanup=True,
           whole_operation_timeout=False, actual_runtime_identity_and_cleanup_unobserved=True)
    RECEIPT.update(pass_all=True, wall_seconds=round(time.monotonic()-start, 6))
    (REPORT / 'checks.json').write_text(json.dumps(RECEIPT, indent=2) + '\n')
    print(json.dumps({'pass_all': True, 'check_groups': len(RECEIPT['checks']), 'wall_seconds': RECEIPT['wall_seconds']}))


if __name__ == '__main__':
    main()
