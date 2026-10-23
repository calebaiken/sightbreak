#!/usr/bin/env python3
"""Read-only recipe/staging checks and tiny explicitly synthetic archive controls."""
import ast
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tarfile
import tempfile

REPO = Path('/workspace/sightbreak-touch-contrast-recovered')
OUT = Path(__file__).resolve().parent
PACKET = REPO / 'docs/reports/gauntlet/m6-touch-contrast-recovered/acquisition-r4b-r2'
BASE = PACKET.parent
COMMIT = '2ecc3083c149cfcbb035d113fbc1a4b40a10f27b'
sha = lambda data: hashlib.sha256(data).hexdigest()
git = lambda *args: subprocess.check_output(['git', '-C', str(REPO), *args])
result = {'scope': 'source-only plus synthetic archive controls; no native/engine/import/OCR', 'recipe': COMMIT}
assert git('rev-parse', 'HEAD').decode().strip() == COMMIT
assert not git('status', '--porcelain')
freeze_path = BASE / 'SOURCE_FREEZE-r4b-r2.json'
freeze = json.loads(freeze_path.read_text())
assert sha(freeze_path.read_bytes()) == 'f9d292d7cb04fc129eee7df84fdc1c0591ae14600497bcf63aac0243cd7f2563'
result['freeze_sha256'] = sha(freeze_path.read_bytes())
result['frozen_files'] = []
for item in freeze['frozen_files']:
    data = (REPO / item['path']).read_bytes()
    assert sha(data) == item['sha256'] and len(data) == item['bytes']
    assert data == git('show', 'b001fc5087960729535f63c896b40d6dc25bd272:' + item['path'])
    result['frozen_files'].append({'path': item['path'], 'sha256': sha(data), 'bytes': len(data)})
assert len(result['frozen_files']) == 22
result['staged'] = []
for item in freeze['fixtures']:
    root = Path(item['path'])
    raw = (root / 'SOURCE.json').read_bytes()
    manifest = json.loads(raw)
    assert sha(raw) == item['manifest_sha256'] and manifest['source'] == item['source_full']
    rows = manifest['files'] + manifest['fixture'] + [
        {'path': 'game/tests/touch_contrast_instrumented.gd', 'sha256': manifest['instrumented_sha256']},
        {'path': 'game/tests/touch_contrast_instrumented.gd.uid', 'sha256': manifest['instrumented_uid_sha256']}]
    assert len(manifest['files']) == 323 and len(rows) == len({x['path'] for x in rows}) == 327
    for entry in rows:
        assert sha((root / entry['path']).read_bytes()) == entry['sha256']
    for entry in manifest['files']:
        assert (root / entry['path']).read_bytes() == git('show', item['source_full'] + ':' + entry['path'])
    uids = [(root / x['path']).read_text().strip() for x in rows if x['path'].endswith('.uid')]
    assert len(uids) == len(set(uids)) == 138
    assert not (root / 'game/.godot').exists()
    result['staged'].append({'name': item['name'], 'source': item['source_full'], 'manifest_sha256': sha(raw),
                             'checked_paths': len(rows), 'git_original_paths': len(manifest['files']),
                             'unique_uids': len(uids), 'preimport_cache_absent': True})
controller = (PACKET / 'controller.py').read_text()
original = git('show', COMMIT + ':docs/reports/gauntlet/m6-touch-contrast-recovered/native-r3/controller.py').decode()
assert controller.count('SOURCE_FREEZE-r4b-r2.json') == 3
assert controller.count('scripts/analyze_touch_contrast_r4b.py') == 2
restored = controller.replace('SOURCE_FREEZE-r4b-r2.json', 'SOURCE_FREEZE-r3.json').replace('scripts/analyze_touch_contrast_r4b.py', 'scripts/analyze_touch_contrast.py')
assert restored == original
assert ast.dump(ast.parse(restored), include_attributes=False) == ast.dump(ast.parse(original), include_attributes=False)
result['controller'] = {'sha256': sha(controller.encode()), 'original_sha256': sha(original.encode()),
                        'exact_bytes_after_five_literal_restorations': True, 'engine_calls_at_most': 10,
                        'engine_wait_caps_sum_seconds': 3330, 'whole_operation_cap': None}
verified = json.loads((PACKET / 'verification.json').read_text())
result['packet_files'] = []
for name, item in verified['packet_files'].items():
    data = (PACKET / name).read_bytes()
    assert sha(data) == item['sha256'] and len(data) == item['bytes']
    result['packet_files'].append({'path': name, 'sha256': sha(data), 'bytes': len(data)})
plan = (PACKET / 'PLAN.md').read_text()
snippets = plan.split('```sh')[1:]
checked = 0
for block in snippets:
    block = block.split('```')[0]
    for part in block.split("python3 - <<'PY'\n")[1:]:
        ast.parse(part.split('\nPY')[0]); checked += 1
assert checked == 3
result['inline_python_syntax_checks'] = checked
config = json.loads((PACKET / 'lane-start.template.json').read_text())
assert not Path(config['raw_root']).exists()
assert not Path(config['raw_root']).with_suffix('.tar.xz').exists()
assert not (BASE / 'native-r4b-r2').exists()
assert not Path('/tmp/.X11-unix/X131').exists() and not Path('/tmp/.X131-lock').exists()
result['runtime_not_started'] = True
spec = importlib.util.spec_from_file_location('review_archive', PACKET / 'package_evidence.py')
module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
result['synthetic_archive_controls'] = []
for complete, clean in ((False, True), (True, True), (False, False)):
    with tempfile.TemporaryDirectory(prefix='touch-r4b-review-archive-') as temporary:
        root = Path(temporary)
        module.RAW = root / 'synthetic-raw'; module.RAW.mkdir()
        module.REPORT = root / 'synthetic-report'; module.ARCHIVE = root / 'synthetic.tar.xz'
        end = {'acquisition_complete': complete, 'error': None if complete else 'SYNTHETIC producer failure',
               'display_socket_absent': clean, 'display_lock_absent': clean,
               'owned_cleanup': [{'proc_path_absent': clean}]}
        (module.RAW / 'lane-end.json').write_text(json.dumps(end))
        (module.RAW / 'partial.log').write_text('SYNTHETIC partial output retained\n')
        accepted = True
        try:
            with contextlib.redirect_stdout(io.StringIO()): module.main()
        except AssertionError:
            accepted = False
        assert accepted == clean
        control = {'synthetic': True, 'acquisition_complete': complete, 'clean': clean, 'archive_accepted': accepted}
        if accepted:
            manifest = json.loads((module.REPORT / 'payload-manifest.json').read_text())
            archive = json.loads((module.REPORT / 'ARCHIVE.json').read_text())
            assert manifest['acquisition_complete'] is complete and manifest['acquisition_error'] == end['error']
            reassembled = b''.join((module.REPORT / p['path']).read_bytes() for p in archive['parts'])
            assert sha(reassembled) == archive['archive_sha256'] == sha(module.ARCHIVE.read_bytes())
            assert all(sha((module.REPORT / p['path']).read_bytes()) == p['sha256'] and p['bytes'] <= 24*1024*1024 for p in archive['parts'])
            with tarfile.open(module.ARCHIVE, 'r:xz') as bundle:
                embedded = json.load(bundle.extractfile('payload-manifest.json'))
                assert embedded == manifest
                assert set(bundle.getnames()) == {'payload-manifest.json', 'raw/lane-end.json', 'raw/partial.log'}
                for item in manifest['files']:
                    data = bundle.extractfile('raw/' + item['path']).read()
                    assert sha(data) == item['sha256'] and len(data) == item['bytes']
            control.update({'all_partial_originals_preserved': True, 'embedded_status_exact': True,
                            'parts_and_full_reassembly_hash_valid': True})
        result['synthetic_archive_controls'].append(control)
result['pass'] = True
(OUT / 'source-checks.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({'pass': True, 'frozen_files': len(result['frozen_files']), 'staged': result['staged'],
                  'controller': result['controller'], 'runtime_not_started': result['runtime_not_started']}))
