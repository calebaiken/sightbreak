"""Audit original source identities and regression logs without native execution."""
import argparse
import json
from pathlib import Path
import re


def audit(root, identity):
    base = root / 'evidence'
    records = []
    manifest = json.loads((base / 'manifest.json').read_text())
    records.append({'path': 'manifest.json',
                    'matches': all(manifest.get(key) == expected for key, expected in identity.items())
                    and manifest.get('source_dirty') is False and manifest.get('source_game_dirty') is False,
                    'source': {key: manifest[key] for key in (*identity.keys(), 'source_dirty', 'source_game_dirty')}})
    for path in sorted(base.rglob('results.json')):
        value = json.loads(path.read_text())
        if not isinstance(value, dict):
            continue
        source = value.get('source', value.get('authority_source'))
        if isinstance(source, dict) and source.get('source_commit'):
            records.append({'path': path.relative_to(base).as_posix(),
                            'matches': all(source.get(key) == expected for key, expected in identity.items())
                            and source.get('source_dirty') is False and source.get('source_game_dirty') is False,
                            'source': source})
    leaks, errors = [], []
    logs = sorted((base / 'regressions').rglob('*.log'))
    for path in logs:
        for index, line in enumerate(path.read_text(errors='replace').splitlines(), 1):
            item = {'path': path.relative_to(base).as_posix(), 'line': index, 'text': line}
            if re.search(r'ObjectDB.*leaked|Leaked instance|Orphan StringName:|StringName: [1-9][0-9]* unclaimed string names at exit\.', line):
                leaks.append(item)
            if re.search(r'^(?:SCRIPT ERROR|ERROR:)|Parse Error', line):
                errors.append(item)
    hud = (base / 'regressions/hud_objective_hint.log').read_text()
    samples = [json.loads(line.split('HUD_PRIORITY_SAMPLE ', 1)[1])
               for line in hud.splitlines() if line.startswith('HUD_PRIORITY_SAMPLE ')]
    benchmarks = [json.loads(line.split('HUD_PRIORITY_BENCHMARK ', 1)[1])
                  for line in hud.splitlines() if line.startswith('HUD_PRIORITY_BENCHMARK ')]
    return {'current_source_records': records,
            'all_current_source_records_match': bool(records) and all(item['matches'] for item in records),
            'retained_regression_log_count': len(logs),
            'regression_ObjectDB_or_instance_leak_lines': leaks,
            'regression_engine_error_lines': errors,
            'all_retained_regression_logs_clean': not leaks and not errors,
            'native_priority_sample_count': len(samples),
            'native_priority_all_correct_frozen_tick_zero': bool(samples) and all(item['correct'] is True and item['game_tick'] == 0 for item in samples),
            'native_priority_benchmarks': benchmarks,
            'scope': 'Actual native raw log and source receipts. Frozen priority samples are source UI assertions, not physical continuous gameplay or input acceptance.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    parser.add_argument('--source-audit', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    identity = json.loads(args.source_audit.read_text())['native_identity']
    result = audit(args.root, identity)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({key: value for key, value in result.items() if key != 'current_source_records'}))
    print(json.dumps({'source_records': len(result['current_source_records'])}))
