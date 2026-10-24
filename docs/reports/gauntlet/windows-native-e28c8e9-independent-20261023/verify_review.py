"""Verify the retained failure verdict and independently supported bounded passes."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
READ = lambda n: json.loads((P/n).read_text())
run, jobs = READ('run-final-decoded.json'), READ('jobs-final-decoded.json')['jobs']
raw, source = READ('audit-r2/raw-recomputed.json'), READ('audit-r2/source-Windows-recomputed.json')
route = READ('audit-r2/settings-route-recomputed.json')
legacy = READ('audit-r2/legacy-failure-recomputed.json')
strict = READ('audit-r2/runtime-completeness.json')
native = READ('audit-r2/native-commands-recomputed.json')
checks = {
    'exact_original_failed_attempt': run['id']==39926044462 and run['run_attempt']==1
        and run['conclusion']=='failure' and run['event']=='workflow_dispatch'
        and run['head_sha']=='e28c8e90b9ef2d0c766bd9152c194e3197ceba9a'
        and run['head_branch']=='codex/v1-qualify-win-e28c8e9',
    'one_original_windows_job':len(jobs)==1 and jobs[0]['id']==120322557935
        and jobs[0]['labels']==['windows-latest'] and jobs[0]['conclusion']=='failure',
    'preregistered_commits_before_dispatch':READ('dispatch-chronology.json')['all_commits_precede_dispatch'] is True,
    'official_archive_digests_match':all(r['matches'] is True and hashlib.sha256((P/r['archive']).read_bytes()).hexdigest()==r['official_sha256']
        for r in READ('supported-transfers.json')['transferred']),
    'selected_raw_index_complete':all(raw['raw_artifact_index'][k] is True
        for k in ('all_sizes_and_hashes_match','complete_selected_file_set')),
    'full_QA_matches_all_selected_originals':READ('audit-r2/full-QA-crosscheck.json')['all_match_full_QA'] is True,
    'all_70_PNGs_intact':len(READ('audit-r2/full-QA-crosscheck.json')['PNGs'])==70
        and READ('audit-r2/full-QA-crosscheck.json')['all_original_PNGs_pass_integrity_check'] is True,
    '24_originals_directly_reviewed':READ('visual-review.json')['direct_original_count']==24,
    'exact_native_source_reconciled':all(source['checks'][k] is True for k in
        ('source_clean_and_identity_matches_native_bytes','all_native_game_resource_hashes_match','only_declared_fixture_resource_needs_CRLF')),
    'missing_controller_digest_remains_false':source['checks']['actual_controller_digest_matches_frozen_python'] is False,
    'all_current_source_records_match':READ('audit-r2/raw-sources-logs-recomputed.json')['all_current_source_records_match'] is True,
    'maintained_native_9434_and_186_audits':native['native_assertion_total']==9434
        and len(native['checks'])==186 and all(native['checks'].values()),
    'gunplay_4399_predicates':READ('audit-r2/gunplay-recomputed.json')['checks']==4399
        and READ('audit-r2/gunplay-recomputed.json')['failures']==[],
    'dry_primary_1974_observable_predicates':READ('audit-r2/dry-observable-recomputed.json')['predicates']==1974
        and READ('audit-r2/dry-observable-recomputed.json')['observable_comparison_passed'] is True,
    'two_input_passes_and_failed_legacy':[(r['scenario'],r['all_checks_passed']) for r in raw['native_input']]
        ==[('native-input',True),('reload-release-first',True),('reload-legacy-delayed',False)],
    'original_legacy_failure_recomputed':legacy['qualification_verdict']=='FAIL'
        and legacy['all_failure_fact_checks_passed'] is True,
    'route_failure_not_promoted':route['all_route_checks_passed'] is False
        and route['original_status']=='SETTINGS_ROUTE_PRECONDITION_LOST'
        and route['details']['failure_reconstruction']['reason_matches'] is True
        and route['details']['failure_reconstruction']['same_living_actor_at_rejection'] is True,
    'focus_and_settings_unreached':raw['journey']['receipt_passed'] is False
        and raw['settings_transaction']['transaction_receipt_available'] is False
        and READ('audit-r2/focus-actual-recomputed.json')['original_focus_receipt']=={},
    'only_first_phase_bracket_passes':[r['accepted'] for r in READ('audit-r2/phase-captures-recomputed.json')['cases']]==[True,False],
    'both_objective_passes':len(raw['objectives'])==2 and all(r['all_checks_passed'] is True for r in raw['objectives'])
        and READ('audit-r2/objective-stages-recomputed.json')['all_stage_checks_passed'] is True,
    'stock_12_round_earned_exact_disk_reload':raw['full_match']['all_checks_passed'] is True
        and raw['full_match']['rounds']==12 and raw['full_match']['score']==[7,5]
        and raw['full_match']['xp_gain']==120 and raw['full_match']['credits_gain']==250,
    'all_133_logs_independently_strict_clean':len(strict['all_transferred_logs'])==133
        and all(r['strict_failure_lines']==[] for r in strict['all_transferred_logs']),
    'overall_completeness_remains_failed':strict['all_pure_receipt_checks_passed'] is False,
    'R1_setup_failures_retained':(P/'audit-r1/phase-captures-recomputed.log').is_file()
        and 'StopIteration' in (P/'audit-r1/phase-captures-recomputed.log').read_text()
        and 'TypeError' in (P/'audit-r1/runtime-completeness.log').read_text(),
}
verdict = {'run_id':39926044462,'source_commit':run['head_sha'],'verdict':'FAIL',
           'review_integrity_checks':checks,'review_consistent':all(checks.values()),
           'largest_gap':'Actual ordinary-control route endpoint and continuous living settings/LEAVE/reopen/focus/normal-close qualification.',
           'comparison':'Identified a089 output has greater achieved living-journey and legacy-diagnostic coverage; neither overall passes. No causal runtime improvement claim.',
           'native_binary_reparsed':False,'retry_approved':False}
(P/'VERDICT.json').write_text(json.dumps(verdict,indent=2)+'\n')
print(json.dumps({'qualification_verdict':'FAIL','review_consistent':verdict['review_consistent'],
                  'review_integrity_checks':len(checks),'failed_review_checks':[k for k,v in checks.items() if not v]}))
raise SystemExit(0 if verdict['review_consistent'] else 1)
