"""Validate retained review joins without running an engine or external service."""
import hashlib
import json
from pathlib import Path
import re
import subprocess

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[3]
SOURCES = {
    'fence': ('fa718efcbe6aa36e53ca12474454a5dccfc5e9b9', '/workspace/reviews/windows-focus-liveness-r2-source'),
    'timing': ('691076fbe866ae798666e731c423ad4cc20fd876', '/workspace/reviews/windows-focus-timing-source')}


def main():
    audit = json.loads((OUT / 'source-audit.json').read_text())
    assert audit['assertion_count'] == 57 and audit['exact_single_invocation_timing_delta']
    tests, groups = [], [('test_native_focus_fence',16,0), ('test_offline_capture_fences',15,0),
        ('test_macos_menu',11,0), ('test_native_observation',7,3), ('test_offline_export_ocr',5,0)]
    replays, additional = {}, {}
    for label, (freeze, checkout) in SOURCES.items():
        replay = json.loads((OUT / (label + '-original-replay.json')).read_text())
        more = json.loads((OUT / (label + '-additional-controls.json')).read_text())
        replays[label], additional[label] = replay, more
        assert replay['source_freeze'] == more['source_freeze'] == freeze
        assert replay['corrected_case_count'] == 77 and replay['independent_assertion_count'] == 335
        assert replay['all_corrected_outcomes_pass'] and not replay['historical_assertions_claimed_passing']
        assert replay['original_defect_reproduction_assertion_now_fails'] == 'dead_bad_counter_wall_msec_MISSING reproduces false acceptance'
        assert more['case_count'] == 31 and more['assertion_count'] == 136 and more['all_passed']
        for path, digest in replay['source_hashes'].items():
            data = subprocess.check_output(['git', 'show', freeze + ':' + path], cwd=ROOT)
            assert hashlib.sha256(data).hexdigest() == digest
        assert subprocess.check_output(['git', 'status', '--porcelain'], cwd=checkout) == b''
        selected = groups + ([('test_focus_resume_timing',8,0)] if label == 'timing' else [])
        for name, methods, skips in selected:
            path = OUT / (label + '-' + name + '.log')
            text = path.read_text()
            assert re.search(r'Ran ' + str(methods) + r' tests? in ', text)
            assert ('OK (skipped=' + str(skips) + ')' if skips else 'OK') in text.splitlines()
            tests.append({'source_freeze': freeze, 'label': label,
                'command': ['python3', 'scripts/' + name + '.py', '-v'], 'cwd': checkout, 'exit': 0,
                'methods': methods, 'skips': skips, 'log': path.name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    assert replays['fence']['case_summaries'] == replays['timing']['case_summaries']
    assert replays['fence']['cases'] == replays['timing']['cases']
    assert additional['fence']['cases'][:24] == additional['timing']['cases'][:24]
    receipt = {'scope': 'source-only independent acceptance; no runtime/retry/living-input acceptance or approval',
        'verdicts': {label: {'source_freeze': freeze, 'verdict': 'ACCEPT_DECLARED_SOURCE_SCOPE'}
                     for label, (freeze, _) in SOURCES.items()},
        'original_case_count_per_source': 77, 'original_replay_assertions_per_source': 335,
        'additional_case_count_per_source': 31, 'additional_assertions_per_source': 136,
        'source_audit_assertions': 57, 'replay_outcomes_equal_between_freezes': True,
        'pure_checks': tests, 'method_totals': {label: sum(row['methods'] for row in tests if row['label'] == label) for label in SOURCES},
        'retained_files': {path.name: {'bytes': path.stat().st_size,
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest()} for path in sorted(OUT.iterdir())
            if path.is_file() and path.name != 'review-checks.json'}}
    (OUT / 'review-checks.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({k:v for k,v in receipt.items() if k not in ('retained_files', 'pure_checks')}))


if __name__ == '__main__':
    main()
