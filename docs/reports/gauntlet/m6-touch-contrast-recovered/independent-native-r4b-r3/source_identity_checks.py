#!/usr/bin/env python3
"""Read-only pre-native identity audit. Writes only its own review receipt."""
import ast
import datetime
import hashlib
import json
from pathlib import Path
import re
import subprocess
import time

REPO = Path(__file__).resolve().parents[5]
BUILDER = Path('/workspace/sightbreak-touch-contrast-recovered')
REPORT = Path(__file__).resolve().parent
COMPONENT = Path('docs/reports/gauntlet/m6-touch-contrast-recovered')
SOURCE = '108d1cdc6cf471daa7390298c234bb1c087ae865'
HANDOFF = 'b9bd7e62c70d3f5a061c4177ede6c73c21dc9d35'
OLD = 'b001fc5087960729535f63c896b40d6dc25bd272'
RAW = Path('/workspace/sightbreak-touch-contrast-native-recovered-r4b-r3')
STAGES = Path('/workspace/sightbreak-touch-contrast-fixture-recovered-r4b-r3')
OLD_STAGES = Path('/workspace/sightbreak-touch-contrast-fixture-recovered-r4b-r2')
start = time.monotonic()
checks = []


def digest(data):
    return hashlib.sha256(data).hexdigest()


def git(source, path):
    return subprocess.check_output(['git', 'show', source + ':' + str(path)], cwd=REPO)


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def audit(name, fn):
    try:
        checks.append({'name': name, 'pass': True, 'observation': fn()})
    except Exception as exc:
        checks.append({'name': name, 'pass': False, 'error': repr(exc)})


freeze_path = COMPONENT / 'SOURCE_FREEZE-r4b-r3.json'
freeze = json.loads((BUILDER / freeze_path).read_text())
packet = BUILDER / COMPONENT / 'acquisition-r4b-r3'


def frozen():
    data = (BUILDER / freeze_path).read_bytes()
    require(digest(data) == '4282c67c984b1840ca43158b16c0ecb03f4254d01e5cb300478682cc8adbe921', 'freeze hash')
    require(data == git(HANDOFF, freeze_path), 'freeze handoff identity')
    require(len(freeze['frozen_files']) == 24, 'freeze count')
    for row in freeze['frozen_files']:
        data = (BUILDER / row['path']).read_bytes()
        require(digest(data) == row['sha256'] and len(data) == row['bytes'], row['path'])
        require(data == git(SOURCE, row['path']), 'exact source Git: ' + row['path'])
        require(data == (REPO / row['path']).read_bytes(), 'own review source: ' + row['path'])
    return {'files': 24, 'freeze_sha256': digest((BUILDER / freeze_path).read_bytes())}


def product():
    path = 'game/scripts/ui/touch_controls.gd'
    before, after = git(OLD, path), git(SOURCE, path)
    old = b'var compact := key != "fire" and r < 32.0'
    new = b'var compact: bool = key != "fire" and r < 32.0'
    require(before.count(old) == after.count(new) == 1, 'single compact declaration')
    require(before.replace(old, new) == after, 'one-line product delta')
    names = subprocess.check_output(['git', 'diff', '--name-only', OLD, SOURCE, '--', 'game'], cwd=REPO).decode().splitlines()
    require(names == [path], 'other game delta')
    before_ast, after_ast = [ast.parse(git(source, 'scripts/touch_geometry_r4b.py')) for source in (OLD, SOURCE)]
    for tree in (before_ast, after_ast):
        tree.body = [node for node in tree.body if not isinstance(node, ast.FunctionDef) or node.name != 'paint_program']
    require(ast.dump(before_ast) == ast.dump(after_ast), 'helper beyond paint_program')
    analyzer = (BUILDER / 'scripts/analyze_touch_contrast_r4b.py').read_bytes()
    require(analyzer == git(OLD, 'scripts/analyze_touch_contrast_r4b.py'), 'analyzer changed')
    require(digest(analyzer) == 'c47bb2fd7a3b8eab83765fd75ee76885815fc5ae467ffac6b99859e72be05141', 'analyzer hash')
    return {'product_sha256': digest(after), 'game_changed_paths': names, 'helper_outside_paint_program_equal': True, 'analyzer_unchanged': True}


def manifest_rows(manifest):
    return manifest['files'] + manifest['fixture'] + [
        {'path': 'game/tests/touch_contrast_instrumented.gd', 'sha256': manifest['instrumented_sha256']},
        {'path': 'game/tests/touch_contrast_instrumented.gd.uid', 'sha256': manifest['instrumented_uid_sha256']}]


def stages():
    observed = []
    for expected in freeze['fixtures']:
        root = STAGES / expected['name']
        data = (root / 'SOURCE.json').read_bytes()
        require(digest(data) == expected['manifest_sha256'], 'new manifest hash')
        manifest = json.loads(data)
        require(manifest['source'] == expected['source_full'], 'new source')
        rows = manifest_rows(manifest)
        require(len(manifest['files']) == 323 and len(rows) == len({r['path'] for r in rows}) == 327, 'stage counts')
        for row in rows:
            data = (root / row['path']).read_bytes()
            require(digest(data) == row['sha256'], 'new stage: ' + row['path'])
            require('bytes' not in row or len(data) == row['bytes'], 'new stage size')
        for row in manifest['files']:
            require((root / row['path']).read_bytes() == git(manifest['source'], row['path']), 'original Git game path')
        uids = [(root / row['path']).read_text().strip() for row in rows if row['path'].endswith('.uid')]
        require(len(uids) == len(set(uids)) == 138, 'new UID uniqueness')
        require(not (root / 'game/.godot').exists(), 'new imported cache')
        old_root = OLD_STAGES / expected['name']
        old_manifest = json.loads((old_root / 'SOURCE.json').read_text())
        old_receipt = BUILDER / COMPONENT / (expected['name'] + '-SOURCE-r4b-r2.json')
        require((old_root / 'SOURCE.json').read_bytes() == old_receipt.read_bytes(), 'old manifest changed')
        old_rows = manifest_rows(old_manifest)
        require(len(old_rows) == 327, 'old stage count')
        for row in old_rows:
            data = (old_root / row['path']).read_bytes()
            require(digest(data) == row['sha256'], 'old stage changed: ' + row['path'])
            new_data = (root / row['path']).read_bytes()
            if expected['name'] == 'candidate' and row['path'] in ('game/scripts/ui/touch_controls.gd', 'game/tests/touch_contrast_instrumented.gd'):
                data = data.replace(b'var compact := key != "fire" and r < 32.0', b'var compact: bool = key != "fire" and r < 32.0')
            require(data == new_data, 'unexpected new stage delta: ' + row['path'])
        observed.append({'name': expected['name'], 'source': manifest['source'], 'manifest_sha256': digest((root / 'SOURCE.json').read_bytes()), 'paths': 327, 'original_git_paths': 323, 'unique_uids': 138, 'preimport_cache_absent': True, 'old_r2_paths_unchanged': 327})
    return observed


def recipe():
    verification = json.loads((packet / 'verification.json').read_text())
    for name, row in verification['packet_files'].items():
        data = (packet / name).read_bytes()
        require(digest(data) == row['sha256'] and len(data) == row['bytes'], 'packet: ' + name)
        require(data == git(HANDOFF, COMPONENT / 'acquisition-r4b-r3' / name), 'packet handoff: ' + name)
    controller = (packet / 'controller.py').read_text()
    old_controller = (BUILDER / COMPONENT / 'acquisition-r4b-r2/controller.py').read_text()
    require(controller.count('SOURCE_FREEZE-r4b-r3.json') == 3, 'freeze literal count')
    require(controller.replace('SOURCE_FREEZE-r4b-r3.json', 'SOURCE_FREEZE-r4b-r2.json') == old_controller, 'controller beyond three freeze literals')
    package = (packet / 'package_evidence.py').read_text()
    package = package.replace('native-r4b-r3', 'native-r4b-r2').replace(SOURCE, OLD)
    require(package == (BUILDER / COMPONENT / 'acquisition-r4b-r2/package_evidence.py').read_text(), 'archive beyond identities')
    snippets = re.findall(r"python3 - <<'PY'\n(.*?)\nPY", (packet / 'PLAN.md').read_text(), re.S)
    require(len(snippets) == 3, 'inline snippet count')
    for i, snippet in enumerate(snippets):
        compile(snippet, 'unexecuted-inline-' + str(i), 'exec')
    return {'packet_files': len(verification['packet_files']), 'controller_only_three_freeze_literals': True, 'archive_only_report_source_identities': True, 'inline_snippets_syntax_checked_only': 3, 'whole_operation_hard_bound': False}


def old_raw():
    manifest = json.loads((BUILDER / COMPONENT / 'native-r4b-r2/payload-manifest.json').read_text())
    root = Path(manifest['raw_root'])
    rows = manifest['files']
    require(len(rows) == 628, 'old raw count')
    require({str(p.relative_to(root)) for p in root.rglob('*') if p.is_file()} == {r['path'] for r in rows}, 'old raw path set')
    for row in rows:
        data = (root / row['path']).read_bytes()
        require(len(data) == row['bytes'] and digest(data) == row['sha256'], 'old raw changed: ' + row['path'])
    require(manifest['png_count'] == 0 and manifest['acquisition_complete'] is False, 'old failure changed')
    return {'verified_files': 628, 'verified_bytes': sum(row['bytes'] for row in rows), 'pngs': 0, 'acquisition_complete': False, 'archive_not_reaudited': True}


def no_runtime():
    require(not RAW.exists() and not RAW.with_suffix('.tar.xz').exists(), 'new raw or archive exists')
    require(not (BUILDER / COMPONENT / 'native-r4b-r3').exists(), 'new native report exists')
    return {'future_raw_absent': True, 'future_archive_absent': True, 'future_native_report_absent': True, 'engine_invocations': 0}


for name, fn in [('before_runtime_absence', no_runtime), ('freeze', frozen), ('product_helper_analyzer', product), ('new_and_old_stages', stages), ('recipe', recipe), ('old_r2_raw_preservation', old_raw), ('after_runtime_absence', no_runtime)]:
    audit(name, fn)
result = {'kind': 'READ_ONLY_SOURCE_IDENTITY_ONLY', 'time_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'handoff': HANDOFF, 'source': SOURCE, 'preregistration_commit': '86c2c9b3', 'checks': checks, 'pass': all(row['pass'] for row in checks), 'wall_seconds': time.monotonic() - start}
(REPORT / 'source-identity-checks.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result))
raise SystemExit(not result['pass'])
