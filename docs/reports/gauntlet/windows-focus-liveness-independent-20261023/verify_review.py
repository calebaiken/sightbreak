"""Recheck source identity, retained pure controls and original raw joins."""
import ast
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
FREEZE = '19304d5d736b09326d5d2503da09dc8cf7b45129'
BASE = 'b2e0293a546961230afbd73e5cd2a1a307d69e94'

def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


def main():
    paths = ['scripts/native_focus_fence.py', 'scripts/test_native_focus_fence.py',
             'scripts/fixtures/offline_focus_observations.json', 'scripts/verify_offline_export.py', 'scripts/validate.sh']
    hashes = {}
    for path in paths:
        data = (ROOT / path).read_bytes()
        assert data == git('show', FREEZE + ':' + path), path
        hashes[path] = hashlib.sha256(data).hexdigest()
        if path.endswith('.py'):
            ast.parse(data)
    preserved = json.loads((OUT / 'source-preservation-recomputed.json').read_text())
    original = json.loads((ROOT / 'docs/reports/gauntlet/windows-focus-liveness-20261023/source-preservation.json').read_text())
    assert {k:v for k,v in preserved.items() if k != 'source_freeze'} == {k:v for k,v in original.items() if k != 'source_freeze'}
    assert git('diff', BASE, FREEZE, '--', 'game', '.github') == b''
    assert git('diff', BASE, FREEZE, '--', 'scripts/validate.sh').decode().count('+python3 scripts/test_native_focus_fence.py -v') == 1
    tests = []
    for name, count, skips in [('test_native_focus_fence', 11, 0), ('test_offline_capture_fences', 15, 0),
        ('test_macos_menu', 11, 0), ('test_native_observation', 7, 3), ('test_offline_export_ocr', 5, 0)]:
        path = OUT / (name + '.log')
        text = path.read_text()
        assert re.search(r'Ran ' + str(count) + r' tests? in ', text), name
        expected = 'OK (skipped=' + str(skips) + ')' if skips else 'OK'
        assert expected in text.splitlines(), name
        tests.append({'command': ['python3', 'scripts/' + name + '.py', '-v'], 'exit': 0,
                      'methods': count, 'skips': skips, 'log': path.name,
                      'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    timeline = json.loads((OUT / 'original-timeline-recomputed.json').read_text())
    saved = json.loads((ROOT / 'docs/reports/gauntlet/windows-focus-liveness-20261023/original-timeline.json').read_text())
    assert timeline == saved
    fixture = json.loads((ROOT / 'scripts/fixtures/offline_focus_observations.json').read_text())
    assert fixture['last_living_guard'] == timeline['last_living_guard']['state']
    assert fixture['dead_release_ack'] == timeline['released_ack']['state']
    assert fixture['focus_start'] == next(row['state'] for row in timeline['focus_actions']
        if row.get('label') == 'Fresh stock match reaches a living active player before native focus loss' and row.get('state'))
    probes = json.loads((OUT / 'counterexamples.json').read_text())
    assert probes['controller_sha256'] == hashes['scripts/verify_offline_export.py']
    assert probes['helper_sha256'] == hashes['scripts/native_focus_fence.py']
    assert probes['case_count'] == 77 and probes['assertion_count'] == 49
    assert len(probes['cases']) == 19
    receipt = {'source_freeze': FREEZE, 'report_head': '0823ceee1b4bcf860f96cfda3344ac1e199aded0',
        'verdict': 'REJECT', 'scope': 'pure source-only diagnostic; no native/retry acceptance or authorization',
        'source_hashes': hashes, 'source_bytes_equal_freeze': True, 'preservation_receipt_matches': True,
        'pure_checks': tests, 'pure_methods': sum(row['methods'] for row in tests),
        'original_timeline_equal': True, 'fixture_raw_states_equal_original': True,
        'declared_probe_cases': 77, 'probe_assertions': 49, 'full_raw_cases_retained': 19,
        'retained_files': {path.name: {'bytes': path.stat().st_size,
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest()} for path in sorted(OUT.iterdir())
            if path.is_file() and path.name != 'review-checks.json'}}
    (OUT / 'review-checks.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({k:v for k,v in receipt.items() if k not in ('retained_files', 'source_hashes', 'pure_checks')}))


if __name__ == '__main__':
    main()
