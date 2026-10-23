"""Check retained review joins and honest failed completeness without native work."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
read = lambda name: json.loads((P / name).read_text())
checks = {}
run = read('run-final.json')
checks['original_failed_exact_attempt'] = run['id'] == 39916539053 and run['run_attempt'] == 1 and run['conclusion'] == 'failure' and run['head_sha'] == 'a089473481ced0f2e7b2a7468bbc5d079f92f0ff'
raw = read('raw-recomputed.json')
checks['native_suites_accepted_with_raw_producers'] = raw['regressions']['all_checks_passed'] is True and read('native-commands-recomputed.json')['native_assertion_total'] == 9434
checks['three_input_schedules_independently_pass'] = len(raw['native_input']) == 3 and all(x['all_checks_passed'] is True for x in raw['native_input'])
checks['both_objectives_independently_pass_original_limits'] = len(raw['objectives']) == 2 and all(x['all_checks_passed'] is True for x in raw['objectives']) and read('objective-stages-recomputed.json')['all_stage_checks_passed'] is True
checks['stock_earned_reload_independently_passes'] = raw['full_match']['all_checks_passed'] is True and raw['full_match']['rounds'] == 7 and raw['full_match']['xp_gain'] == 120 and raw['full_match']['credits_gain'] == 250
checks['whole_living_journey_remains_failed'] = raw['journey']['receipt_passed'] is False and read('focus-actual-recomputed.json')['all_focus_checks_passed'] is False and read('runtime-completeness.json')['all_pure_receipt_checks_passed'] is False
settings = read('settings-failure-recomputed.json')
checks['reached_resume_then_death_facts_verified'] = settings['all_reached_fact_checks_passed'] is True and settings['whole_journey_passed'] is False and settings['typed_focus_rejection'].startswith('UNREACHED;')
checks['all_current_sources_and_native_export_joins'] = read('raw-sources-logs-recomputed.json')['all_current_source_records_match'] is True and read('export-identity-recomputed.json')['all_checks_passed'] is True
checks['missing_success_only_controller_digest_remains_missing'] = read('source-Windows-recomputed.json')['checks']['actual_controller_digest_matches_frozen_python'] is False
checks['strict_native_logs_clean'] = read('runtime-completeness.json')['checks']['every_transferred_native_log_strict_clean'] is True
checks['native_math_receipts_recomputed'] = read('gunplay-recomputed.json')['failures'] == [] and read('dry-observable-recomputed.json')['observable_comparison_passed'] is True
checks['originals_transferred_within_supported_limit'] = all((P / x['path']).stat().st_size == x['bytes'] <= 32 * 1024 * 1024 and hashlib.sha256((P / x['path']).read_bytes()).hexdigest() == x['sha256'] for x in read('supported-transfers.json')['artifacts'])
checks['all_selected_originals_equal_full_QA_and_images_intact'] = read('full-QA-crosscheck.json')['all_match_full_QA'] is True and read('full-QA-crosscheck.json')['all_original_PNGs_pass_integrity_check'] is True
visual = read('visual-review.json')
checks['direct_pixel_review_and_exact_convenience_copies'] = visual['originals_directly_inspected'] == 35 and all(hashlib.sha256((P / x['path']).read_bytes()).hexdigest() == x['sha256'] for x in visual['byte_identical_convenience_copies'])
checks['registration_timing_limitation_preserved'] = '36 seconds' in (P / 'REGISTRATION_TIMING.md').read_text() and '36 seconds' in (P / 'REPORT.md').read_text()
checks['original_reviewer_failures_retained'] = any(x['exit'] != 0 for x in read('audit-run-r1.json')) and read('settings-initial-auditor-overcomparison.json')['all_reached_fact_checks_passed'] is False
r = {'checks': checks, 'all_review_consistency_checks_passed': all(checks.values()),
     'actual_combined_runtime_passed': False,
     'scope': 'Consistency of already reviewed retained bytes and scoped verdicts. This is not another native run or independent acceptance by self-count.'}
(P / 'review-consistency.json').write_text(json.dumps(r, indent=2) + '\n')
print(json.dumps({'all_review_consistency_checks_passed': r['all_review_consistency_checks_passed'], 'failed': [k for k, v in checks.items() if not v], 'actual_combined_runtime_passed': False}))
raise SystemExit(0 if all(checks.values()) else 1)
