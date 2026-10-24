"""Complete the saved source audit after interruption, without redoing Git/application work."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONTROLLER = Path(r'C:/Users/blith/AppData/Local/Temp/opencode/receipt-review-37c55530e7a77a8a/CONTROLLER')
prior_bytes = (ROOT / 'provenance-audit.json').read_bytes()
prior = json.loads(prior_bytes)
mapping = json.loads((CONTROLLER / 'mapping.json').read_bytes())
frozen = ROOT.parent / '_FROZEN_VERDICT.md'
assert hashlib.sha256(frozen.read_bytes()).hexdigest() == prior['blind_verdict_sha256']
expected_resolved = {
    'Set-673EECBC entire source manifest equals measured Git tree',
    'Set-8F5F7604 entire source manifest equals measured Git tree',
    'ancillary original source equals candidate Git',
}
assert set(prior['mismatches']) == expected_resolved
resolved = []
for label, expected_count in [('Set-673EECBC', 278), ('Set-8F5F7604', 286)]:
    rows = json.loads((ROOT / label / 'git-archive-transforms.json').read_bytes())
    assert len(rows) == expected_count and all(row['LF_to_CRLF'] for row in rows)
    manifest = json.loads((ROOT / label / 'source-manifest.json').read_bytes())
    resolved.append({
        'label': label,
        'source_manifest_entries_verified_in_saved_audit': prior['groups'][label]['source_manifest_entries_verified'],
        'only_LF_to_CRLF_differences_from_git_blobs': expected_count,
        'reproduced_archive_sha256_previously_verified': prior['groups'][label]['archive_sha256'],
        'relevant_archived_byte_digests': {key: value for key, value in manifest.items() if key in [
            'game/scripts/ui/economy_ui.gd', 'game/scripts/ui/economy_api.gd',
            'game/scripts/ui/transaction_journal.gd', 'backend/app.py']},
        'resolution': 'The earlier direct-Git-byte equality assumption was too strong. The complete measured Git archive matched both the recorded archive SHA256 and every source-manifest entry. All blob/archive differences were independently checked to be only LF-to-CRLF conversion.',
    })

executable = Path(mapping['labels']['Set-8F5F7604']['cases']['case-01']['aliases'][0][1])
executable_result = {'path': str(executable), 'exists_now': executable.is_file(), 'executed_by_this_audit': False}
if executable.is_file():
    with executable.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    executable_result['current_bytes_sha256'] = digest
    executable_result['matches_recorded_pin'] = digest == mapping['labels']['Set-8F5F7604']['executable_sha256']
    assert executable_result['matches_recorded_pin']

completion = {
    'verdict': 'PASS for bounded source/artifact binding; blind WIN retained separately',
    'prior_audit_sha256': hashlib.sha256(prior_bytes).hexdigest(),
    'blind_verdict_sha256': prior['blind_verdict_sha256'],
    'mapping_sha256': prior['mapping_sha256'],
    'completed_observation_audit_counts': prior['counts'],
    'source_archive_resolution': resolved,
    'ancillary_resolution': 'Before interruption, the original executed probe matched the reproduced candidate archive exactly; the calibrated version differed by exactly one unreachable-address literal. The original raw-Git mismatch was the same newline conversion.',
    'current_probe_resolution_at_source_inspection': '2475 working-tree bytes versus 2424 frozen bytes; independently verified identical after CRLF-to-LF normalization. The frozen probe, retained executed copies, summary digests, and controller copy matched byte-for-byte.',
    'executable': executable_result,
    'unexplained_source_or_transform_mismatches': [],
    'fixture_assisted_dataflow_concern': 'Closed at inspected-source level: driver retry supplies no path/payload; UI loads, claims, and sends the journal transaction. Fixture expected_price is unconditionally read only for normalization, and is not used as recovery input.',
    'minimal_recovery_config_control_required_for_bounded_acceptance': False,
    'remaining_limits': [
        'No minimal-config dynamic control was run; its omission is an empirical corroboration gap, not a remaining source dataflow ambiguity.',
        'The unmodified driver still requires config.payload.expected_price at line 19 even in retry mode; omission can fail before reaching production recovery.',
        'Historical cache payloads are not retained; their 62-entry manifests and same-game-tree identity assertions are bound, not independently reconstructed runtime caches.',
        'Recorded source-before/source-after cleanliness and source-unchanged flags are producer observations, not independent execution attestation.',
        'Service launcher versus logged worker PID lineage is not captured: 20396/13692 for baseline, 2824/15020 for candidate.',
        'Stable postcommit process-kill scope only; no new application, native, database, power-loss, or manual-UI test was executed.',
    ],
}
(ROOT / 'source-binding-completion.json').write_text(json.dumps(completion, indent=2), encoding='utf-8')
print(json.dumps(completion, indent=2))
