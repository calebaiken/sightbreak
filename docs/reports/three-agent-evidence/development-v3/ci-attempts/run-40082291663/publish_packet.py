"""Publish only a new, bounded, byte-preserving evidence packet; never stage Git."""
import datetime
import hashlib
import json
import pathlib
import shutil

BASE = pathlib.Path(__file__).resolve().parent
REPO = BASE.parent / 'sightbreak-v3'
COLLECTION = BASE.parent / 'sightbreak-v3-evidence/ci-40082291663'
DEST = REPO / 'docs/reports/three-agent-evidence/development-v3/ci-attempts/run-40082291663'
DRAFT = BASE / 'packet-draft-02'
CAP = 12 * 1024 * 1024


def load(path):
    return json.loads(path.read_text())


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write_json(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(value, indent=2) + '\n')


if DEST.exists() or DRAFT.exists():
    raise SystemExit('Refuse to overwrite any existing destination/draft; preserve earlier attempts.')
primary = load(BASE / 'checks.json')
supplement = load(BASE / 'supplement.json')
all_checks = primary + supplement['checks']
assert all(row['passed'] for row in all_checks)
DRAFT.mkdir()
selected = {}


def select(path, relative=None):
    relative = relative or path.relative_to(BASE).as_posix()
    if relative in selected:
        assert selected[relative] == path
        return
    selected[relative] = path


for name in ['AUDIT.md', 'VISUAL_REVIEW.md', 'AUDIT_ATTEMPTS.md', 'source-manifest.json',
             'archive-index.json', 'collection-inspection.json', 'counts.json', 'checks.json',
             'findings-data.json', 'supplement.json', 'collect_offline.py', 'analyze_offline.py',
             'supplement_offline.py', 'publish_packet.py', 'publication-budget-failure.json']:
    select(BASE / name)
for p in (BASE / 'metadata').iterdir():
    if p.is_file():
        select(p)
for p in (BASE / 'audit-attempts').rglob('*'):
    if p.is_file():
        select(p)

contracts = ['scripts/build_manifest.py', 'scripts/godot_process.py', 'scripts/matrix_process.py',
             'scripts/native_log.py', 'scripts/validate_matrix.py', 'scripts/validate.sh',
             'scripts/run_network_campaign.py', 'scripts/simulate_network.py',
             'scripts/reload_negative_controls.py', 'scripts/verify_builds.py',
             'scripts/verify_packaged_builds.py', 'scripts/verify_integration_export.py',
             'scripts/verify_offline_export.py', 'scripts/export_flow.py', 'scripts/ocr_process.py',
             'scripts/offline_hud.py', 'scripts/fixtures/export_integration.gd',
             'scripts/test_protocol_compat.sh', 'scripts/test_result_outbox.py',
             '.github/workflows/v3-development.yml', 'game/tests/reload_audio_capture.gd',
             'game/tests/network_simulation_probe.gd', 'game/scripts/main.gd']
for name in contracts:
    select(BASE / 'frozen-source' / name)

# Complete audio raw evidence, including every failed mutant attempt and all WAVs.
for p in (BASE / 'raw/artifact-12555647143.zip').rglob('*'):
    if p.is_file():
        select(p)

# Preserve native/matrix logs, including negative paths and historical leaks.
# Twelve redundant campaign-root JSON console dumps remain externally retained;
# all 132 corresponding native child logs remain in the compact packet.
for artifact in ['artifact-12555294271.zip', 'artifact-12556088968.zip']:
    for p in (BASE / 'raw' / artifact).rglob('*.log'):
        if artifact == 'artifact-12556088968.zip' and p.parent == BASE / 'raw' / artifact / 'builds/v3-network':
            continue
        select(p)

dev = BASE / 'raw/artifact-12555294271.zip'
for p in dev.rglob('*'):
    if not p.is_file() or p.suffix == '.png':
        continue
    relative = p.relative_to(dev)
    if not ({'state', 'server-state', 'extracted'} & set(relative.parts)):
        select(p)
select(dev / 'v3-package-verification/extracted/linux/sightbreak.sh')
screens = {
    'v3-export-network': ['01-exported-menu.png', '01b-exported-inventory.png',
                          '03-exported-network-rifle.png', '07-after-authority-reload-completion.png', '08-settled.png'],
    'v3-export-offline': ['05-after-fire.png', '05-inspection-pause.png', '06-after-reload.png',
                          '06-inspection-pause.png', '08-return-menu.png'],
}
for folder, names in screens.items():
    for name in names:
        select(dev / folder / name)
for p in (dev / 'v3-export-offline').glob('*-ocr.input.png'):
    if p.name == '06-after-reload-status-ocr.input.png':
        assert digest(p) == digest(p.with_name('05-after-fire-status-ocr.input.png'))
        continue
    select(p)

val = BASE / 'raw/artifact-12556088968.zip/builds'
for p in (val / 'v3-matrix').glob('*.json'):
    select(p)
for p in (val / 'v3-matrix').rglob('*.json'):
    if p.name in {'summary.json', 'results.json'} and 'protocol' not in p.parts:
        select(p)
for p in (val / 'v3-network').glob('*.json'):
    select(p)
for p in (BASE / 'raw/run-logs.zip').rglob('*.txt'):
    if p.name.startswith(('2_Run actions_checkout', '6_Require the broad baseline', '7_Audit source restoration',
                          '5_Inspect and package actual exports', '6_Drive actual exported network client',
                          '7_Drive actual exported living-player offline client')):
        select(p)

for relative, source in sorted(selected.items()):
    target = DRAFT / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    assert digest(source) == digest(target)

(DRAFT / '.gitattributes').write_text('# Scoped byte preservation for this immutable evidence packet.\n** -text -filter -ident -working-tree-encoding\n', encoding='utf-8', newline='\n')
(DRAFT / '.gitignore').write_text('# Scoped re-inclusion of evidence, including ancestor-ignored raw logs/builds.\n!**/\n!**/*\n!**/*.log\n', encoding='utf-8', newline='\n')

members = load(BASE / 'member-index.json')
retained = []
for row in members:
    raw = row.get('raw_external')
    if raw in selected:
        assert row['sha256'] == digest(DRAFT / raw)
        row['packet_path'] = raw
        row['retention'] = 'packet-and-original-external-archive'
        retained.append({'archive': row['archive'], 'member': row['member'], 'packet_path': raw,
                         'bytes': row['bytes'], 'sha256': row['sha256']})
    else:
        row['retention'] = 'original-external-archive-only'
write_json(DRAFT / 'member-index.json', members)
write_json(DRAFT / 'retention-index.json', {
    'method': 'Every archive member is indexed in member-index.json; exact archive/member addresses and archive-index paths resolve external-only members, including nested archives.',
    'member_observations': len(members), 'copied_raw_members': len(retained),
    'external_only_member_observations': len(members) - len(retained), 'retained': retained,
    'no_original_evidence_deleted': True,
})

artifacts = load(BASE / 'metadata/artifacts-001.json')['artifacts']
write_json(DRAFT / 'external-references.json', {
    'collection_directory': str(COLLECTION), 'external_audit_directory': str(BASE),
    'run_url': 'https://github.com/calebaiken/sightbreak/actions/runs/40082291663',
    'source_commit': '4099facb21a9242d41df79fd9e75bbbea031f2e0',
    'archive_occurrences': load(BASE / 'archive-index.json'), 'artifacts': artifacts,
    'expiration_scope': 'Retained metadata only; no online expiration refresh was attempted.',
    'large_omissions': ['Actual package ZIPs and payload executables/APK/static libraries',
                       'Most large per-child trajectory JSON reports; every one remains in the full original archive and hash index',
                       'Some original screenshots; all remain in the original development artifact and external extraction',
                       '12 redundant campaign-root JSON console logs; campaign.json contains the same summary records and all132 native logs are retained',
                       'One duplicate status OCR input PNG; the retained05-after-fire-status crop has the identical SHA256'],
    'preserved_budget_attempt': {'directory': str(BASE / 'packet-draft'), 'bytes': 13107431,
                                 'receipt': str(BASE / 'publication-budget-failure.json'),
                                 'published': False},
})

findings = [
    {'id': 'OS-CHILD-RECEIPTS', 'kind': 'unresolved_observability_limit', 'severity': 'scope-limiting',
     'observed': '132 campaign native reports/logs, 12 parent OS receipts, zero per-child numeric OS exit receipts.',
     'effect': 'No claim of 132 independently retained numeric exits; pinned harness enforces child zero exits before root success.'},
    {'id': 'OS-AUDIO-ROOT', 'kind': 'unresolved_observability_limit', 'severity': 'scope-limiting',
     'observed': 'Direct Bash-e CI step success and root/result exit0; no standalone root process receipt.'},
    {'id': 'UI-POST-SOURCE', 'kind': 'receipt_granularity_limit', 'severity': 'scope-limiting',
     'observed': 'Post-run unchanged source/executable checks enforced by exact pinned controllers; no separate after-source UI snapshot.'},
    {'id': 'VISIBLE-VERSION', 'kind': 'confirmed_product_inconsistency', 'severity': 'minor-open',
     'observed': 'Original menu displays 0.3.0-dev; actual package manifest/APK metadata says 0.3.2-dev. Frozen main.gd:266 contains old label.',
     'effect': 'No hash/source mismatch, but version-label correctness is not accepted or fixed by this audit.'},
    {'id': 'RENDER-AUTHORITY-LAG', 'kind': 'confirmed_evidence_limit', 'severity': 'scope-limiting',
     'observed': 'Authority-completion-named original network screenshot is still RELOADING 0.5s; settled frame later shows30/84.'},
    {'id': 'STRICT-LOG-EXCEPTIONS', 'kind': 'classified_nonclean_logs', 'severity': 'disclosed',
     'observed': '402 logs, nine matching files /27 lines: audio expected assertions, injected DB outage, incompatible protocol errors/mirrors, historical archived texture leaks.',
     'effect': 'No unclassified marker; no blanket error-free-archive claim.'},
]
write_json(DRAFT / 'FINDINGS.json', {
    'recommendation': 'Retain as source-pinned automated development-candidate evidence only; all listed scope limits/open findings remain.',
    'unconditional_acceptance': False, 'release_approved': False,
    'blocking_audited_runtime_contract_contradictions': [],
    'primary_static_predicates': len(primary), 'supplemental_static_predicates': len(supplement['checks']),
    'total_static_predicates': len(all_checks), 'failed_final_predicates': [c['id'] for c in all_checks if not c['passed']],
    'findings': findings,
    'unverified_gates': ['Human uninterrupted full match', 'Subjective gunplay/aim/listening', 'Touch/gyro usability',
                         'Physical Android install/play/performance', 'macOS/Xcode iOS build/signing/physical install',
                         'Sustained device FPS/latency/thermal/battery', 'Production deployment/reliability',
                         'Security review', 'Every applicable8.5-per-category art/quality gate'],
})

files = sorted(p for p in DRAFT.rglob('*') if p.is_file())
ledger = ''.join(digest(p) + '  ' + p.relative_to(DRAFT).as_posix() + '\n' for p in files)
(DRAFT / 'SHA256SUMS.txt').write_text(ledger, encoding='utf-8', newline='\n')
total = sum(p.stat().st_size for p in DRAFT.rglob('*') if p.is_file())
if total > CAP:
    write_json(BASE / 'publication-budget-failure.json', {'bytes': total, 'cap_bytes': CAP, 'preserved_draft': str(DRAFT)})
    raise SystemExit('Draft exceeds12MiB; preserved without publishing: ' + str(total))

DEST.mkdir(parents=True, exist_ok=False)
for source in DRAFT.rglob('*'):
    if not source.is_file():
        continue
    target = DEST / source.relative_to(DRAFT)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    assert digest(source) == digest(target)
lines = (DEST / 'SHA256SUMS.txt').read_text().splitlines()
for line in lines:
    expected, relative = line.split('  ', 1)
    assert digest(DEST / relative) == expected
actual = {p.relative_to(DEST).as_posix() for p in DEST.rglob('*') if p.is_file()}
assert actual == {line.split('  ', 1)[1] for line in lines} | {'SHA256SUMS.txt'}
assert sum(p.stat().st_size for p in DEST.rglob('*') if p.is_file()) == total
receipt = {'published_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
           'destination': str(DEST), 'external_audit': str(BASE), 'files': len(actual), 'bytes': total,
           'cap_bytes': CAP, 'ledger_entries': len(lines), 'all_packet_bytes_reverified': True,
           'sha256_ledger_sha256': digest(DEST / 'SHA256SUMS.txt'), 'audit_md_sha256': digest(DEST / 'AUDIT.md'),
           'retained_raw_member_count': len(retained), 'external_only_member_observations': len(members)-len(retained),
           'static_predicates': len(all_checks), 'failed_final_predicates': []}
write_json(BASE / 'publication-receipt.json', receipt)
print(json.dumps(receipt, indent=2))
