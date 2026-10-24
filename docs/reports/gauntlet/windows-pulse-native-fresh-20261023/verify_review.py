"""Check this exact actual verdict against retained original-byte audit results."""
import hashlib
import json
from pathlib import Path


root = Path(__file__).resolve().parent
read = lambda name: json.loads((root / name).read_text())
run, jobs = read('run-final-decoded.json'), read('jobs-final-decoded.json')['jobs']
raw = read('audit-r2/raw-recomputed.json')
native = read('audit-r2/native-commands-recomputed.json')
source = read('audit-r2/source-Windows-recomputed.json')
route = read('audit-r2/settings-route-recomputed.json')
strict = read('audit-r2/runtime-completeness.json')
transfers = read('supported-transfers.json')
images = read('visual-review.json')
checks = {
    'exact_first_attempt_and_final_failed_job': run['head_sha'] == '49ae54b0e4f5d880bdf06e4eb783a616b2dff684'
        and run['head_branch'] == 'codex/v1-qualify-win-49ae54b0' and run['run_attempt'] == 1
        and run['conclusion'] == 'failure' and len(jobs) == 1 and jobs[0]['id'] == 120369601915
        and jobs[0]['conclusion'] == 'failure',
    'admission_and_preregistration_precede_dispatch': all(read('dispatch-chronology.json')['checks'].values()),
    'both_official_original_archive_digests_sizes_match': len(transfers['transferred']) == 2
        and all((root / a['archive']).stat().st_size == a['official_bytes']
                and hashlib.sha256((root / a['archive']).read_bytes()).hexdigest() == a['official_sha256']
                for a in transfers['transferred']),
    'all_selected_originals_and_PNGs_verified': read('audit-r2/full-QA-crosscheck.json')['all_match_full_QA'] is True
        and read('audit-r2/full-QA-crosscheck.json')['all_original_PNGs_pass_integrity_check'] is True
        and read('audit-r2/full-QA-crosscheck.json')['bounded_files'] == 224
        and len(read('audit-r2/full-QA-crosscheck.json')['PNGs']) == 69,
    'source_and_resource_bytes_reconcile': all(source['checks'][k] for k in
        ('source_clean_and_identity_matches_native_bytes', 'all_native_game_resource_hashes_match', 'only_declared_fixture_resource_needs_CRLF'))
        and source['native_game_resources'] == 327 and read('windows-filter-reconstruction.json')['matches'] is True
        and len(source['CRLF_validation_paths']) == 13,
    'missing_success_only_controller_digest_not_promoted': source['checks']['actual_controller_digest_matches_frozen_python'] is False,
    'sixteen_current_suites_and_actual_native_checks': native['all_checks_passed'] is True
        and len(native['actual_suite_records']) == 16 and native['native_assertion_total'] == 29550
        and len(native['checks']) == 199,
    'all_observable_oracles_reconstructed': read('audit-r2/exhausted-observable-recomputed.json')['all_exhausted_checks_passed'] is True
        and read('audit-r2/exhausted-observable-recomputed.json')['independent_predicates'] == 75890
        and read('audit-r2/dry-observable-recomputed.json')['observable_comparison_passed'] is True
        and read('audit-r2/gunplay-recomputed.json')['failures'] == [],
    'ordinary_failure_and_two_delayed_passes_preserved': [(x['scenario'], x['all_checks_passed']) for x in raw['native_input']]
        == [('native-input', False), ('reload-release-first', True), ('reload-legacy-delayed', True)]
        and read('audit-r2/ordinary-failure-recomputed.json')['all_failure_fact_checks_passed'] is True,
    'original_three_schedule_completeness_remains_failed': read('audit-r2/input-schedules-recomputed.json')['all_three_original_schedules_passed'] is False,
    'living_route_failure_and_unreached_fine_pulse_preserved': route['all_route_checks_passed'] is False
        and route['original_status'] == 'SETTINGS_ROUTE_PRECONDITION_LOST'
        and route['details']['failure_reconstruction']['reason_matches'] is True
        and read('audit-r2/route-pulses-recomputed.json')['rows'] == [],
    'later_settings_and_focus_remain_unreached': raw['journey']['receipt_passed'] is False
        and raw['settings_transaction']['transaction_receipt_available'] is False
        and read('audit-r2/focus-actual-recomputed.json')['all_focus_checks_passed'] is False,
    'both_original_objective_and_restart_gates_pass': len(raw['objectives']) == 2
        and all(o['all_checks_passed'] is True for o in raw['objectives'])
        and read('audit-r2/objective-stages-recomputed.json')['all_stage_checks_passed'] is True,
    'stock_actual_earnings_and_restart_reconstructed': raw['full_match']['all_checks_passed'] is True
        and raw['full_match']['rounds'] == 11 and raw['full_match']['score'] == [4, 7]
        and raw['full_match']['xp_gain'] == 120 and raw['full_match']['credits_gain'] == 325,
    'complete_strict_native_logs_clean': len(strict['all_transferred_logs']) == 137
        and strict['checks']['every_transferred_native_log_strict_clean'] is True
        and read('audit-r2/raw-sources-logs-recomputed.json')['retained_regression_log_count'] == 97,
    'all_export_runtime_receipts_join': read('audit-r2/export-identity-recomputed.json')['all_checks_passed'] is True
        and len(read('audit-r2/export-identity-recomputed.json')['runtime_executable_joins']) == 7,
    'direct_original_pixel_inspection_recorded': images['directly_inspected_original_count'] == 31
        and len(images['originals']) == 31 and images['ordinary_fire_afterfire_failure_same_bytes'] is True,
    'large_binary_reparse_limit_preserved': len(transfers['untransferred']) == 1
        and transfers['untransferred'][0]['bytes'] == 141138061
        and read('audit-r2/export-identity-recomputed.json')['PCK_bytes_or_directory_independently_reparsed'] is False,
    'overall_qualification_is_not_promoted': strict['all_pure_receipt_checks_passed'] is False,
}
verdict = {'qualification_verdict': 'FAIL', 'run_id': 39940242244, 'job_id': 120369601915,
           'source_commit': run['head_sha'], 'checks_of_report_evidence': checks,
           'all_report_evidence_checks_passed': all(checks.values()),
           'largest_remaining_gap': 'Actual coarse approach and release to a stopped living cover endpoint within the original corridor/deadline; new fine pulse remains unexecuted.',
           'comparison_pick': 'e28c8e9 for achieved ordinary-input/fine-correction coverage; new run separately passes legacy diagnostic; both overall fail.',
           'scope': 'Original-byte actual receipt review. No native run, retry, physical/causal or whole-release acceptance.'}
(root / 'VERDICT.json').write_text(json.dumps(verdict, indent=2) + '\n')
print(json.dumps({'all_report_evidence_checks_passed': verdict['all_report_evidence_checks_passed'],
                  'checks': len(checks), 'qualification_verdict': 'FAIL',
                  'failed': [k for k, v in checks.items() if not v]}))
raise SystemExit(0 if verdict['all_report_evidence_checks_passed'] else 1)
