"""Read actual diagnostic selection receipts; never run the diagnostic or fixtures."""
import argparse
import hashlib
import json
from pathlib import Path


def audit(root, expected):
    path = root / 'input-mode-verbose/diagnostic.json'
    report = json.loads(path.read_text())
    original = root / 'regressions'
    bindings = {}
    for name, recorded in report['original_evidence_sha256'].items():
        candidate = original / name
        actual = hashlib.sha256(candidate.read_bytes()).hexdigest() if candidate.is_file() else None
        bindings[name] = {'recorded_sha256': recorded, 'actual_sha256': actual, 'match': recorded == actual}
    identity = lambda value: all(value.get(key) == expected[key] for key in
                                ('source_commit', 'source_game_tree', 'source_content_sha256', 'source_validation_sha256'))
    results = json.loads((original / 'results.json').read_text())
    isolation = json.loads((original / 'isolation.json').read_text())
    repeat = root / 'input-mode-verbose/repeat'
    repeat_files = sorted(p.relative_to(repeat).as_posix() for p in repeat.rglob('*') if p.is_file()) if repeat.exists() else []
    return {'actual_native_diagnostic_path': str(path), 'actual_source_matches': identity(report['source']) and identity(report['source_after']),
            'status': report['status'], 'passed': report['passed'], 'strict_gate_repaired': report['strict_gate_repaired'],
            'skip_reason': report.get('skip_reason'), 'seconds': report['seconds'], 'whole_deadline_seconds': report['whole_deadline_seconds'],
            'source_unchanged': report['source_unchanged'], 'original_evidence_unchanged': report['original_evidence_unchanged'],
            'original_file_hash_bindings': bindings,
            'original_reached_suites': [item['suite'] for item in results], 'original_failure': isolation['failure'],
            'diagnostic_owned_process_receipts': report.get('owned_processes'), 'diagnostic_isolation': report.get('isolation'),
            'repeat_artifact_files': repeat_files,
            'native_verbose_input_mode_log_present': (repeat / 'input_mode.log').is_file(),
            'scope_limit': 'A skipped selector is not a clean repeat; mocked invented-source control stdout is not native evidence.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('full_qa', type=Path)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.full_qa, json.loads(args.source.read_text()))
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({key: result[key] for key in ('actual_source_matches', 'status', 'passed', 'skip_reason',
                                                  'original_reached_suites', 'native_verbose_input_mode_log_present')}))
