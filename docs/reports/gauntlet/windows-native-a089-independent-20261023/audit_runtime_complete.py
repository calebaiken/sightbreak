"""Fail-closed completeness gate over independent original-receipt audit results."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('receipts', type=Path)
parser.add_argument('full', type=Path)
parser.add_argument('audits', type=Path)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
read = lambda path: json.loads(path.read_text())
checks = {}
checks['current_raw_index_intact'] = all(read(args.audits / 'raw-recomputed.json')['raw_artifact_index'][name]
                                         for name in ('all_sizes_and_hashes_match', 'complete_selected_file_set'))
raw = read(args.audits / 'raw-recomputed.json')
for name in ('regressions', 'journey', 'settings_transaction', 'full_match'):
    checks[name + '_all_independent_checks'] = raw[name].get('all_checks_passed') is True
checks['two_objectives_complete'] = (len(raw['objectives']) == 2
    and {row['scenario'] for row in raw['objectives']} == {'plant', 'defuse'}
    and all(row.get('all_checks_passed') is True for row in raw['objectives']))
checks['three_input_schedules_complete'] = (len(raw['native_input']) == 3
    and {row['scenario'] for row in raw['native_input']} == {'native-input', 'reload-release-first', 'reload-legacy-delayed'}
    and all(row.get('all_checks_passed') is True for row in raw['native_input']))
checks['windows_layouts_explicitly_not_applicable'] = raw['layouts'] == {'not_applicable': True}
for name in ('native-commands-recomputed', 'source-Windows-recomputed', 'journey-OCR-recomputed', 'export-identity-recomputed'):
    checks[name] = read(args.audits / (name + '.json')).get('all_checks_passed') is True
native = read(args.audits / 'native-commands-recomputed.json')
checks['fifteen_suites_actual_9434'] = len(native['actual_suite_records']) == 15 and native.get('native_assertion_total') == 9434
checks['gunplay_mathematical_recomputation'] = read(args.audits / 'gunplay-recomputed.json')['failures'] == []
checks['dry_weapon_observable_recomputation'] = read(args.audits / 'dry-observable-recomputed.json').get('observable_comparison_passed') is True
checks['both_original_phase_brackets'] = read(args.audits / 'phase-captures-recomputed.json').get('all_native_bracket_checks_passed') is True
checks['objective_stages_original_limits'] = read(args.audits / 'objective-stages-recomputed.json').get('all_stage_checks_passed') is True
source = read(args.audits / 'raw-sources-logs-recomputed.json')
checks['all_source_identities_clean_current'] = source.get('all_current_source_records_match') is True
checks['all_regression_logs_strict_clean'] = source.get('all_retained_regression_logs_clean') is True
full = read(args.audits / 'full-QA-crosscheck.json')
checks['bounded_and_full_QA_bytes_equal'] = full.get('all_match_full_QA') is True
checks['original_PNGs_integrity'] = full.get('all_original_PNGs_pass_integrity_check') is True and bool(full['PNGs'])

# Read the newly added observer fields from the actual current native snapshot
# events, rather than borrowing Linux/ARM observations. Values remain diagnostic;
# this check asserts shape/finite counters and never derives physical performance.
frames = []
integer_fields = ('read_begin_usec', 'read_end_usec', 'max_physics_steps_per_frame', 'physics_ticks_per_second',
                  'max_fps', 'process_frames', 'physics_frames', 'drawn_frames')
numeric_fields = ('physics_jitter_fix', 'process_max_seconds_last_engine_window',
                  'physics_step_max_seconds_last_engine_window', 'draw_calls_last_rendered_frame',
                  'primitives_last_rendered_frame', 'viewport_3d_scale')
for relative in ('offline-input/initial-offline-trace/events.jsonl', 'offline-input/restart-profile-trace/events.jsonl',
                 'offline-plant/trace/events.jsonl', 'offline-defuse/trace/events.jsonl',
                 'offline-full-match/trace/events.jsonl', 'offline-full-match/trace-reopened/events.jsonl'):
    trace_path = args.receipts / 'evidence' / relative
    rows = [json.loads(line) for line in trace_path.read_text().splitlines() if line] if trace_path.is_file() else []
    snapshots = [row for row in rows if row.get('scope') == 'debug_offline_read_only_observation']
    valid = bool(snapshots)
    for row in snapshots:
        data = row.get('frame_diagnostics', {})
        valid = valid and all(type(data.get(key)) is int and data[key] >= 0 for key in integer_fields)
        valid = valid and all(type(data.get(key)) in (int, float) and math.isfinite(data[key]) and data[key] >= 0 for key in numeric_fields)
        valid = valid and all(isinstance(data.get(key), list) and len(data[key]) == 2
                             and all(type(v) in (int, float) and math.isfinite(v) and v > 0 for v in data[key])
                             for key in ('viewport_visible_size', 'viewport_texture_size_pixels'))
        valid = valid and data.get('read_end_usec', -1) >= data.get('read_begin_usec', 0)
        valid = valid and data.get('internal_3d_target_size', {}).get('available') is False
    checks['current_windows_frame_readbacks:' + relative] = bool(valid)
    frames.append({'path': relative, 'snapshots': len(snapshots), 'all_readbacks_valid': bool(valid),
                   'first_readbacks': snapshots[0].get('frame_diagnostics') if snapshots else None})

logs = []
for path in sorted(args.full.rglob('*.log')):
    text = path.read_text(errors='replace')
    failures = [{'line': index, 'text': line} for index, line in enumerate(text.splitlines(), 1)
                if re.search(r'^(?:SCRIPT ERROR|ERROR:)|Parse Error|ObjectDB.*leaked|Leaked instance', line)]
    logs.append({'path': path.relative_to(args.full).as_posix(), 'bytes': path.stat().st_size,
                 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'strict_failure_lines': failures})
checks['every_transferred_native_log_strict_clean'] = bool(logs) and all(not row['strict_failure_lines'] for row in logs)
result = {'checks': checks, 'all_pure_receipt_checks_passed': all(checks.values()), 'frame_readbacks': frames,
          'all_transferred_logs': logs, 'direct_original_pixel_review_required': True,
          'scope': 'Pure completeness, current native diagnostic shape and strict-log audit. No engine, OCR or performance claim.'}
args.output.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({'all_pure_receipt_checks_passed': result['all_pure_receipt_checks_passed'],
                  'checks': len(checks), 'native_log_count': len(logs), 'failed': [k for k, v in checks.items() if not v]}))
raise SystemExit(0 if result['all_pure_receipt_checks_passed'] else 1)
