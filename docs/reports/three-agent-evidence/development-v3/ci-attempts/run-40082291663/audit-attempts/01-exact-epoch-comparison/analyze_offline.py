"""Independent static audit of retained evidence; no audited modules are imported."""
import array
import csv
import hashlib
import io
import json
import pathlib
import plistlib
import re
import shutil
import stat
import struct
import wave
import zipfile
from collections import Counter

BASE = pathlib.Path(__file__).resolve().parent
COLLECTION = BASE.parent / 'sightbreak-v3-evidence/ci-40082291663'
DEV = BASE / 'raw/artifact-12555294271.zip'
AUDIO = BASE / 'raw/artifact-12555647143.zip'
VALID = BASE / 'raw/artifact-12556088968.zip'
FROZEN = BASE / 'frozen-source'
SOURCE = json.loads((BASE / 'source-manifest.json').read_text())
MEMBERS = json.loads((BASE / 'member-index.json').read_text())
ARCHIVES = json.loads((BASE / 'archive-index.json').read_text())
INDEX = {(m['archive'], m['member']): m for m in MEMBERS}
ARCHIVE = {a['identity']: a for a in ARCHIVES}
SOURCE_FILES = {r['path']: r for r in SOURCE['files']}
CHECKS = []
DETAILS = {}


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def dump(name, value):
    (BASE / name).write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')


def check(label, good, **details):
    CHECKS.append({'id': label, 'passed': bool(good), **details})


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def same_source(value):
    if 'source_commit' in value:
        return (value['source_commit'] == SOURCE['commit'] and value['source_game_tree'] == SOURCE['game_tree']
                and value['source_content_sha256'] == SOURCE['shipping_sha256']
                and value['source_validation_sha256'] == SOURCE['validation_sha256']
                and value['source_game_dirty'] is False and value['source_dirty'] is False)
    return (value.get('commit') == SOURCE['commit'] and value.get('game_tree') == SOURCE['game_tree']
            and value.get('content_sha256') == SOURCE['validation_sha256'] and value.get('dirty') is False
            and value.get('status') == '' and value.get('source_files') == SOURCE['source_files']
            and value.get('source_paths') == SOURCE['source_paths'])


def receipt(path, code=0):
    data = load(path)
    return (data.get('complete') is True and type(data.get('exit')) is int and data['exit'] == code
            and data.get('errors') == [] and data.get('posix_cleanup_verified') is True)


# Transport checks are separate from package payload acceptance.
meta = load(BASE / 'metadata/artifacts-001.json')
transport = []
for a in meta['artifacts']:
    actual = ARCHIVE[f"artifact-{a['id']}.zip"]
    ok = actual['sha256'] == a['digest'].removeprefix('sha256:') and actual['bytes'] == a['size_in_bytes']
    check('transport/' + str(a['id']), ok)
    transport.append({**a, 'actual_sha256': actual['sha256'], 'actual_bytes': actual['bytes'], 'digest_matches': ok})
check('collection/completed', load(BASE / 'metadata/COLLECTION.json')['collection_complete'] is True)
for directory in COLLECTION.glob('*-receipts'):
    aid = directory.name.removesuffix('-receipts') + '.zip'
    for row in load(directory / 'receipt-index.json'):
        check('retained-receipt/' + aid + '/' + row['member'],
              sha(directory / row['retained']) == row['sha256'] == INDEX[aid, row['member']]['sha256'])
check('archives/stream-crc-inventory', load(BASE / 'collection-inspection.json')['errors'] == [])
run = load(BASE / 'metadata/run.json')
jobs = load(BASE / 'metadata/jobs-001.json')['jobs']
check('run/identity', run['head_sha'] == SOURCE['commit'] and run['id'] == 40082291663)
check('jobs/identity', len(jobs) == 3 and all(j['head_sha'] == SOURCE['commit'] and j['conclusion'] == 'success' for j in jobs))
DETAILS['transport'] = transport

# Matrix inventory and every command's actual supervisor receipt + log.
matrix = VALID / 'builds/v3-matrix'
summary = load(matrix / 'summary.json')
validate = (FROZEN / 'scripts/validate.sh').read_text()
native_names = []
for line in validate.splitlines():
    match = re.search(r'^\s*run_godot (\S+) ', line)
    if match:
        native_names.append(match[1])
    elif line.startswith('SIGHTBREAK_STATE_DIR=') and 'run_godot profile ' in line:
        native_names.append('profile')
extra = ['account-output-unit', 'worker-unit', 'network', 'network-soak', 'network-soak-ten',
         'connection-lifecycle', 'bridge-transport', 'build-manifest', 'matrix-harness-unit',
         'matrix-process-unit', 'source-identity-unit', 'verifier-unit', 'network-harness-unit',
         'offline-hud-unit', 'export-ui-unit', 'export-flow-unit', 'negative-audio-harness-unit',
         'reload-contact', 'protocol-matrix', 'hostile-handshake', 'catalog-fixture', 'postgresql',
         'account-protocol', 'account-capacity', 'outbox-crash', 'native-economy', 'account-full-reconnect',
         'economy-conservation', 'native-render-lifecycle', 'native-hud-overflow', 'native-paint-visibility',
         'nested-resource-cleanup', 'frozen-source-identity']
expected = native_names + extra
check('matrix/exact-inventory', [r['name'] for r in summary['checks']] == expected,
      expected_count=len(expected), actual_count=len(summary['checks']))
check('matrix/source', same_source(summary['source']) and same_source(summary['validation_source']) and not summary['dirty'])
native_rx = re.compile(r'^(?:SCRIPT ERROR|ERROR:)|Parse Error|ObjectDB.*leaked|Leaked instance|HARNESS_ERROR', re.M)
matrix_rows = []
for row in summary['checks']:
    path = matrix / row['log']
    good = row['passed'] is True and row['source_commit'] == SOURCE['commit'] and path.is_file()
    if 'exit' in row:
        text = path.read_text(errors='replace')
        good = good and row['exit'] == 0 and row['logged_errors'] is False and not native_rx.search(text)
        good = good and receipt(matrix / (row['name'] + '.process.json'))
    check('matrix/' + row['name'], good)
    matrix_rows.append({**row, 'independent_receipt_and_log_valid': good})
identity = load(matrix / 'source-identity.json')
check('matrix/before-after', identity['before'] == identity['after'] and identity['validation_before'] == identity['validation_after']
      and same_source(identity['before']) and same_source(identity['validation_before'])
      and identity['failures'] == [] and identity['initial_dirty'] is False and identity['final_dirty'] is False)
check('matrix/nested-leak-receipt', load(matrix / 'nested-resource-cleanup.json')['leaked_logs'] == [])
DETAILS['matrix'] = {'rows': matrix_rows, 'groups': len(matrix_rows), 'commands': sum('exit' in r for r in matrix_rows),
                     'expected_inventory': expected}

# Broad strict scan: expected negative stimuli and historical files remain visible.
strict = re.compile(r'^\s*(?:SCRIPT ERROR|ERROR:)|(?:Parse|Parser|Compile) Error|ObjectDB.*leaked|Leaked instance|'
                    r'\bleaked\b|HARNESS_ERROR|Segmentation fault|(?:resources?|RIDs?)[^\r\n]*still in use|'
                    r'Orphan StringName|unclaimed string names|\bFATAL:', re.M | re.I)
scan = []
for root in (DEV, AUDIO, VALID):
    for path in sorted(root.rglob('*.log')):
        relative = path.relative_to(root).as_posix()
        matches = [{'line': i, 'text': line} for i, line in enumerate(path.read_text(errors='replace').splitlines(), 1) if strict.search(line)]
        classification = 'no_strict_error_or_leak_match'
        if matches:
            if relative.startswith('raw/01') and 'mutant-A' in relative:
                classification = 'expected_completed_audio_assertions'
            elif relative == '.local/validation/outbox-fa26219b/api.log':
                classification = 'intentional_database_outage_HTTP500_then_recovery'
            elif relative == 'builds/v3-matrix/protocol/release-e67f2c8/docs/reports/native-render.log':
                classification = 'historical_e67f2c8_git_archive_not_current_execution'
            elif ('client-current.server-release' in relative or 'client-release.server-current' in relative) and relative.startswith('builds/v3-matrix/protocol/'):
                classification = 'cross_version_ENet_rejection_errors_including_mirrored_state_log'
            else:
                classification = 'UNRESOLVED'
        scan.append({'artifact': root.name, 'member': relative, 'sha256': sha(path), 'matches': matches,
                     'classification': classification})
check('logs/no-unclassified-errors', not any(r['classification'] == 'UNRESOLVED' for r in scan))
DETAILS['log_scan'] = {'files': len(scan), 'by_artifact': dict(Counter(r['artifact'] for r in scan)),
                       'matching_files': sum(bool(r['matches']) for r in scan), 'matched_lines': sum(len(r['matches']) for r in scan),
                       'classifications': dict(Counter(r['classification'] for r in scan)), 'rows': scan,
                       'all_retained_logs_error_free': not any(r['matches'] for r in scan), 'pattern': strict.pattern}

# All campaign conditions and all 132 underlying process reports/logs.
campaign_dir = VALID / 'builds/v3-network'
campaign = load(campaign_dir / 'campaign.json')
conditions = [('rtt-' + str(n), {'rtt_ms': float(n)}) for n in (0, 50, 100, 150, 200)]
conditions += [('jitter', {'rtt_ms': 100., 'jitter_ms': 20.}), ('loss', {'rtt_ms': 100., 'loss': .03}),
               ('reorder', {'rtt_ms': 100., 'reorder': .05}),
               ('impaired', {'rtt_ms': 100., 'jitter_ms': 20., 'loss': .03, 'reorder': .05}),
               ('blackout', {'rtt_ms': 100., 'blackout_at': 4., 'blackout_seconds': 2.}),
               ('reconnect', {'rtt_ms': 100., 'jitter_ms': 20., 'loss': .03, 'reorder': .05,
                              'blackout_at': 4., 'blackout_seconds': 2., 'reconnect_at': 8.}),
               ('prediction-disabled', {'rtt_ms': 100., 'no_prediction': True})]
check('campaign/exact-inventory', [r['name'] for r in campaign] == [c[0] for c in conditions])
campaign_rows = []
child_rows = []
for index, (row, (name, extra_condition)) in enumerate(zip(campaign, conditions)):
    directory = campaign_dir / name
    s = load(directory / 'summary.json')
    defaults = dict(rtt_ms=0., jitter_ms=0., loss=0., reorder=0., no_prediction=False, blackout_at=-1,
                    blackout_seconds=0, reconnect_at=-1, reconnect_delay=2., clients=10, seconds=18., seed=7301,
                    port=39000 + 20 * index, render_client=-1, account_tickets=False)
    defaults.update(extra_condition)
    good = row['exit'] == 0 and row['passed'] is True and row['failures'] == [] and row['summary'] == s
    good = good and receipt(campaign_dir / (name + '.process.json'))
    good = good and s['passed'] is True and s['failures'] == [] and s['shared_stop_reached'] is True
    good = good and all(s['conditions'].get(k) == v for k, v in defaults.items())
    snapshots = [row['source_before'], row['source_after'], s['source_before'], s['source_after']]
    good = good and all(same_source(x) and x == snapshots[0] for x in snapshots) and s['source_unchanged'] is True
    check('campaign/' + name, good)
    occupancy = load(directory / 'server.json')['occupancy']
    bindings_good = bool(occupancy) and all(len(x['enet']) <= 10 and len(x['bindings']) <= 10 and
                        len({b['actor'] for b in x['bindings']}) == len(x['bindings']) for x in occupancy)
    final = occupancy[-1]['bindings']
    bindings_good = bindings_good and len(final) == 10 and all(b['idle_msec'] < 750 and b['input_ack'] >= 10 for b in final)
    check('campaign/' + name + '/authority', bindings_good)
    for label in ['server'] + ['client-' + str(n) for n in range(10)]:
        p = directory / (label + '.json')
        data = load(p)
        log = directory / (label + '.log')
        summary_lines = re.findall(r'^NETWORK_SIMULATION (\{.*\})$', log.read_text(), re.M)
        native_summary = json.loads(summary_lines[0]) if len(summary_lines) == 1 else {}
        valid = (data['role'] == ('server' if label == 'server' else 'client') and len(summary_lines) == 1
                 and data['measurement_start_epoch'] == s['measurement_start_epoch'] and data['wall_elapsed_seconds'] >= 18.
                 and not strict.search(log.read_text()))
        if label != 'server':
            valid = valid and data['joined'] is True and data['state'] == 'connected' and data['last_snapshot_age_seconds'] < .75
            valid = valid and data['snapshots'] >= 10 and data['max_displacement'] > .1 and data['accepted_snapshots'] >= 10
            valid = valid and data['last_accepted_age_seconds'] < .75 and data['prediction_enabled'] == (name != 'prediction-disabled')
            valid = valid and (name != 'reconnect' or (data['reconnect_passed'] is True and data['initial_id'] == data['final_id']))
            valid = valid and native_summary.get('joined') == data['joined'] and native_summary.get('snapshots') == data['snapshots']
        check('campaign/' + name + '/' + label, valid)
        child_rows.append({'condition': name, 'process': label, 'report_sha256': sha(p), 'log_sha256': sha(log),
                           'role': data['role'], 'connected': data['state'], 'wall_elapsed_seconds': data['wall_elapsed_seconds'],
                           'accepted_snapshots': data['accepted_snapshots'], 'last_accepted_age_seconds': data['last_accepted_age_seconds'],
                           'reconnect_passed': data['reconnect_passed'], 'prediction_enabled': data['prediction_enabled'],
                           'independent_os_exit_receipt': False, 'report_checks_passed': valid})
    campaign_rows.append({'name': name, 'conditions': s['conditions'], 'exit': row['exit'], 'parent_receipt': load(campaign_dir / (name + '.process.json')),
                          'authority_checked': bindings_good, 'tick_usec_p95': s['tick_usec_p95'], 'tick_interval_usec_p95': s['tick_interval_usec_p95'],
                          'resource_measurement': s['resource_measurement'], 'whole_proxy_lifetime_seconds': s['traffic_window_seconds'],
                          'measurement_seconds': s['measurement_duration_seconds'], 'source_verified': good})
source_receipt = load(campaign_dir / 'source.json')
check('campaign/final-source', source_receipt['source_before'] == source_receipt['source_after'] and same_source(source_receipt['source_before'])
      and source_receipt['source_unchanged'] is True and source_receipt['passed'] is True and source_receipt['failures'] == [])
DETAILS['campaign'] = {'conditions': campaign_rows, 'children': child_rows, 'report_count': len(child_rows),
                       'native_log_count': len(child_rows), 'parent_exit_receipts': 12, 'per_child_os_exit_receipts': 0,
                       'limit': 'Individual OS exits are enforced by pinned simulate_network.py native_process_failures after cleanup, not retained as per-child numeric receipts.'}

# Audio complete counts, expected assertion identity, byte restoration, WAV structure.
audio_attempts = []
wav_rows = []
expected_counts = [(92, 0), (179, 0), (29, 0), (14, 0), (11, 0), (15, 0), (15, 0), (3, 0), (4, 0), (24, 0), (14, 6), (11, 1), (14, 1)]
for i, d in enumerate(sorted(p for p in (AUDIO / 'raw').iterdir() if p.is_dir())):
    assessment = load(d / 'assessment.json')
    attempt = load(d / 'attempt.json')
    text = (d / 'native.log').read_text()
    found = re.findall(r'^(?:RELOAD_SEQUENCE_TEST|WEAPON_ART_TEST|RELOAD_AUDIO_TEST|RELOAD_AUDIO_CAPTURE|RELOAD_VISIBILITY_TEST|RELOAD_DISCOLOUR_TEST|VIEWMODEL_LIGHT_TEST|RELOAD_CONTACT_TEST)\b[^\r\n]*', text, re.M)
    checks, failures = expected_counts[i]
    code = 0 if i < 10 else 1
    complete = len(found) == 1 and re.search(r'\bchecks=' + str(checks) + r' failures=' + str(failures) + r'\b', found[0])
    errors = re.findall(r'^ERROR: (.*)$', text, re.M)
    fail_messages = re.findall(r'^FAIL (.*)$', text, re.M)
    unsafe = re.search(r'HARNESS_ERROR|SCRIPT ERROR|(?:Parse|Parser|Compile) Error|\bleak(?:ed|s|ing)?\b|FATAL|CRASH|Segmentation fault|signal (?:6|11)\b', text, re.I)
    good = bool(complete) and not unsafe and attempt['exit'] == code and receipt(d / 'process.json', code)
    good = good and attempt['containment_and_artifact_errors'] == [] and assessment['summary']['checks'] == checks and assessment['summary']['failures'] == failures
    if i < 10:
        good = good and not errors and assessment['state'] == 'passed'
    else:
        good = good and len(errors) == failures and errors == fail_messages and assessment['state'] == 'FAILED'
    if i == 10:
        good = good and [line.split(' on voice')[0] for line in fail_messages] == ['unlatch', 'extract', 'pouch', 'land', 'enter', 'seat']
    if i == 11:
        good = good and fail_messages == ['after the cancel (and 80 ms of mixer latency) every reload voice is silent (peak 0.01783)']
    if i == 12:
        good = good and fail_messages == ['nothing is audible on any reload voice before the first event (peak 0.03063)']
    for filename, expected_hash in attempt['capture_sha256'].items():
        good = good and sha(d / 'capture' / filename) == expected_hash
    for wav in d.rglob('*.wav'):
        with wave.open(str(wav), 'rb') as pcm:
            params = pcm.getparams()
            samples = array.array('h', pcm.readframes(pcm.getnframes()))
        report_file = next(wav.parent.glob('report_*.txt'))
        report = report_file.read_text()
        voice_file = next(wav.parent.glob('voices_*.csv'))
        voices = list(csv.DictReader(voice_file.open(newline='')))
        good = good and params.nchannels == 1 and params.sampwidth == 2 and params.framerate == 44100 and params.nframes == 139264 and params.comptype == 'NONE'
        good = good and len(re.findall(r'^(?:ok  |FAIL) ', report, re.M)) == checks
        good = good and len(re.findall(r'^FAIL ', report, re.M)) == failures and len(voices) == (4 if 'cancel' in wav.name else 6)
        wav_rows.append({'member': wav.relative_to(AUDIO).as_posix(), 'sha256': sha(wav), 'bytes': wav.stat().st_size,
                         'channels': params.nchannels, 'sample_width': params.sampwidth, 'rate_hz': params.framerate,
                         'frames': params.nframes, 'seconds': params.nframes / params.framerate,
                         'peak_s16': max(map(abs, samples)), 'nonzero_samples': sum(s != 0 for s in samples),
                         'voice_events': len(voices), 'report_failures': failures})
    check('audio/' + d.name, good)
    audio_attempts.append({'name': d.name, 'checks': checks, 'failures': failures, 'os_exit': code,
                           'summary': found[0] if found else None, 'independent_checks_passed': bool(good), 'errors': errors})
before = load(AUDIO / 'raw/sources-before.json')
after = load(AUDIO / 'raw/sources-after.json')
restored = after['sources'] == before['sources'] and after['byte_restored'] is True and after['error'] is None
for path, digest in {**before['sources'], **before['tooling']}.items():
    relative = path.split('/sightbreak-v3-controls/', 1)[1]
    restored = restored and SOURCE_FILES[relative]['sha256'] == digest
for control in ['A5', 'A6', 'A7']:
    record = load(AUDIO / ('raw/control-' + control + '.json'))
    pending = {}
    for edit in record['edits']:
        relative = edit['path'].split('/sightbreak-v3-controls/', 1)[1]
        data = pending.get(relative, (FROZEN / relative).read_bytes())
        mutated = data.replace(edit['old'].encode(), edit['new'].encode(), 1)
        restored = restored and data.count(edit['old'].encode()) == 1 and hashlib.sha256(data).hexdigest() == edit['before_sha256']
        restored = restored and hashlib.sha256(mutated).hexdigest() == edit['after_sha256'] and edit['matches'] == 1
        pending[relative] = mutated
check('audio/mutations-and-restoration', restored)
check('audio/source-before-after', load(AUDIO / 'source-before.json') == load(AUDIO / 'source-after.json') and same_source(load(AUDIO / 'source-before.json')))
root_result = load(AUDIO / 'raw/result.json')
audio_job = next(j for j in jobs if j['name'] == 'adversarial-audio-controls')
root_step = next(s for s in audio_job['steps'] if s['number'] == 6)
check('audio/root-exit-consistency', root_result['exit'] == 0 and root_result['baseline_skipped'] is False
      and root_result['controls'] == [['A5', 'caught'], ['A6', 'caught'], ['A7', 'caught']] and root_step['conclusion'] == 'success')
DETAILS['audio'] = {'baseline_groups': 10, 'baseline_assertions': sum(c for c, _ in expected_counts[:10]),
                    'attempts': audio_attempts, 'wav': wav_rows, 'sources_restored': restored,
                    'root_result_exit': root_result['exit'], 'root_exit_evidence': 'Successful exact Bash -e CI step invoking xvfb-run, raw/result.json exit0 and pinned sys.exit(main()); no separate root OS containment receipt.'}

# Compare actual package ZIP bytes, full inventories/modes, and extracted bytes.
manifest = load(DEV / 'manifest.json')
check('packages/source', same_source(manifest))
check('packages/packaging-copy', manifest == load(DEV / 'packaging.json'))
package_rows = []
for record in manifest['exports']:
    target = record['target']
    name = 'sightbreak-' + target + ('-xcode-project.zip' if target == 'ios' else '-debug.zip')
    aid = DEV.name + '!' + name
    top = INDEX[DEV.name, name]
    desc = next(x for x in manifest['artifacts'] if x['path'] == name)
    expected_members = {x['path']: x for x in record['payload']}
    raw_receipt = (DEV / target / 'source.json').read_bytes()
    receipt_name = target + '/source.json'
    expected_members[receipt_name] = {'path': receipt_name, 'bytes': len(raw_receipt), 'sha256': hashlib.sha256(raw_receipt).hexdigest(), 'mode': 0o644}
    actual_members = {m['member']: m for m in MEMBERS if m['archive'] == aid}
    good = (same_source(record) and record['export_completed'] is True and load(DEV / target / 'source.json') == record
            and top['sha256'] == desc['sha256'] and top['bytes'] == desc['bytes'] and set(actual_members) == set(expected_members))
    for n, e in expected_members.items():
        m = actual_members[n]
        extracted = INDEX[DEV.name, 'v3-package-verification/extracted/' + n]
        good = good and m['sha256'] == e['sha256'] and m['bytes'] == e['bytes']
        good = good and int(m['mode'], 8) == stat.S_IFREG | e['mode'] and m['create_system'] == 3
        good = good and extracted['sha256'] == e['sha256'] and extracted['bytes'] == e['bytes']
    with zipfile.ZipFile(ARCHIVE[aid]['path']) as bundle:
        good = good and bundle.read(receipt_name) == raw_receipt
    check('packages/' + target, good)
    package_rows.append({'target': target, 'archive': name, 'bytes': top['bytes'], 'sha256': top['sha256'],
                         'members_including_receipt': len(actual_members), 'payload_members': len(record['payload']),
                         'receipt_sha256': expected_members[receipt_name]['sha256'], 'inventory_hashes_modes_extracted_identity_verified': good})
for folder in ['verification', 'v3-package-verification']:
    report = load(DEV / folder / 'results.json')
    good = (report['completed'] is True and report['passed'] is True and report['failures'] == []
            and report['source_before'] == report['source_after'] and same_source(report['source_before']) and report['source_unchanged'] is True)
    for row in report['processes']:
        good = good and row['exit'] == 0 and not row['timed_out'] and row['failures'] == [] and row['passed'] is True
        good = good and receipt(DEV / folder / row['process_receipt']) and not strict.search((DEV / folder / row['log']).read_text())
        if row['label'].startswith('linux') and row['label'] != 'linux-demo':
            good = good and 'SIGHTBREAK_MAIN_READY screen=menu' in (DEV / folder / row['log']).read_text()
    check('packages/' + folder + '/actual-process-receipts', good, processes=len(report['processes']))
checksums = dict((line.split('  ', 1)[1], line.split('  ', 1)[0]) for line in (DEV / 'checksums.txt').read_text().splitlines())
check('packages/checksum-inventory', checksums == {r['path']: r['sha256'] for r in manifest['artifacts']})
DETAILS['packages'] = package_rows

# Reinspect binary formats/resources without executing them.
def spool_member(aid, name):
    out = BASE / 'spool' / (hashlib.sha256((aid + '!' + name).encode()).hexdigest() + '.bin')
    if not out.exists():
        with zipfile.ZipFile(ARCHIVE[aid]['path']) as z, z.open(name) as s, out.open('xb') as t:
            shutil.copyfileobj(s, t, 1024 * 1024)
    return out


def packed(path, embedded=False):
    with path.open('rb') as f:
        start = 0
        if embedded:
            f.seek(-12, 2)
            size, magic = struct.unpack('<QI', f.read(12))
            assert magic == 0x43504447
            f.seek(-12-size, 2)
            start = f.tell()
        magic, version, major, minor, patch, flags, base = struct.unpack('<6IQ', f.read(32))
        assert magic == 0x43504447 and version in (3, 4) and not flags & 1
        directory, = struct.unpack('<Q', f.read(8))
        f.seek(start + directory)
        count, = struct.unpack('<I', f.read(4))
        names = []
        for _ in range(count):
            length, = struct.unpack('<I', f.read(4))
            names.append(f.read(length).rstrip(b'\0').decode())
            f.seek(36, 1)
        return names


def integrated(names):
    wanted = [('relay_ar.glb-', '.scn'), ('relay_ar_arms.glb-', '.scn'), ('relay_ar_hands.glb-', '.scn')]
    wanted += [(n + '.png-', '.ctex') for n in ['relay_ar_albedo', 'relay_ar_normal', 'relay_ar_orm', 'relay_ar_arms_albedo', 'relay_ar_arms_normal', 'relay_ar_arms_orm']]
    modules = ['state_privacy', 'snapshot_buffer', 'movement_prediction', 'movement_step', 'peer_lifecycle', 'reconnect_policy',
               'result_outbox', 'viewmodel_shading', 'bot_ai', 'reload_audio', 'reload_phases', 'confirm_sheet']
    return (not any('tests/' in n or '_test.gdc' in n for n in names)
            and all(any(a in n and n.endswith(b) for n in names) for a, b in wanted)
            and all(any(n.endswith('/' + m + '.gdc') for n in names) for m in modules))


elf = spool_member(DEV.name + '!sightbreak-linux-debug.zip', 'linux/sightbreak.x86_64')
with elf.open('rb') as f:
    header = f.read(20)
elf_good = header[:6] == b'\x7fELF\x02\x01' and struct.unpack('<HH', header[16:20])[0] in (2, 3) and struct.unpack('<H', header[18:20])[0] == 62
linux_names = packed(elf, True)
ios_aid = DEV.name + '!sightbreak-ios-xcode-project.zip'
ios_pack = spool_member(ios_aid, 'ios/sightbreak.pck')
ios_names = packed(ios_pack)
with zipfile.ZipFile(ARCHIVE[DEV.name + '!android/sightbreak-debug.apk']['path']) as apk:
    android_names = [n for n in apk.namelist() if n.startswith('assets/')]
check('platform/resource-inspection', elf_good and len(linux_names) == 132 and len(ios_names) == 132 and len(android_names) == 134
      and all(integrated(names) for names in [linux_names, ios_names, android_names]))
ios_plist = plistlib.loads((DEV / 'v3-package-verification/extracted/ios/sightbreak/sightbreak-Info.plist').read_bytes())
ios_project = (DEV / 'v3-package-verification/extracted/ios/sightbreak.xcodeproj/project.pbxproj').read_text()
check('platform/ios-unsigned-structure', ios_plist['CFBundleIdentifier'] == '$(PRODUCT_BUNDLE_IDENTIFIER)'
      and bool(ios_plist['NSLocalNetworkUsageDescription']) and all('Landscape' in v for v in ios_plist['UISupportedInterfaceOrientations'])
      and 'DEVELOPMENT_TEAM = "";' in ios_project and 'UNSIGNED00' not in ios_project
      and 'PRODUCT_BUNDLE_IDENTIFIER = com.sightbreak.game;' in ios_project and 'MARKETING_VERSION = 0.3.2;' in ios_project
      and 'CURRENT_PROJECT_VERSION = 5;' in ios_project)
signature = (DEV / 'verification/android-signature.log').read_text()
badging = (DEV / 'verification/android-manifest.log').read_text()
layout = (DEV / 'verification/android-layout.log').read_text()
check('platform/android-recorded-inspection', all(s in signature for s in ['Verified using v2 scheme (APK Signature Scheme v2): true', 'Verified using v3 scheme (APK Signature Scheme v3): true', 'CN=Android Debug'])
      and all(s in badging for s in ["package: name='com.sightbreak.game'", "versionCode='5'", "versionName='0.3.2-dev'", "sdkVersion:'24'", "targetSdkVersion:'36'", "'arm64-v8a'", "'x86_64'"])
      and bool(re.search(r'android:screenOrientation[^\n]*\(type 0x10\)0x0\b', layout))
      and all(s in layout for s in ['com.godot.game.GodotAppLauncher', 'android.intent.action.MAIN', 'android.intent.category.LAUNCHER']))
DETAILS['platform_resources'] = {'linux': linux_names, 'ios': ios_names, 'android': android_names,
                                 'android_signature_scope': 'Retained apksigner actual exit0/log for the hash-pinned APK; cryptographic verification not rerun offline.'}

# Both UI flows: pinned executable/controller, source gates, normal X11 close, bounded clean root exit.
flows = []
for folder, controller in [('v3-export-network', 'scripts/verify_integration_export.py'), ('v3-export-offline', 'scripts/verify_offline_export.py')]:
    path = DEV / folder
    r = load(path / 'results.json')
    w = load(path / 'watchdog.json')
    close = r['window_close']
    good = r['passed'] is True and r['executable_sha256'] == sha(elf)
    good = good and same_source(r.get('source', r.get('authority_source'))) and r['premature_exit_control_frames'] == 0
    good = good and w['passed'] is True and w['worker_exit'] == 0 and w['error'] is None and w['seconds'] < w['timeout_seconds']
    good = good and w['controller_sha256'] == SOURCE_FILES[controller]['sha256'] and receipt(path / 'watchdog.process.json')
    good = good and close['protocols_atom'] > 0 and close['delete_atom'] > 0 and close['delete_atom'] in close['advertised_protocols']
    good = good and close['method'] == 'WM_DELETE_WINDOW ClientMessage' and 'completion-driven native WM_DELETE_WINDOW' in r['exit_method']
    good = good and not strict.search((path / 'client.log').read_text())
    if folder.endswith('network'):
        s = (path / 'server.log').read_text()
        shot_rows = re.findall(r'^EXPORT_UI_SHOT actor=1 shots=(\d+) ammo=(\d+)$', s, re.M)
        authority = load(path / 'authority.json')
        good = good and same_source(r['artifact_source']) and r['authority'] == authority and r['client_exit'] == r['server_exit'] == 0
        good = good and shot_rows == [(str(i), str(30-i)) for i in range(1, 7)] and 'EXPORT_UI_ACK_READY actor=1 ack=14 ammo=30' in s
        good = good and 'EXPORT_UI_RELOAD_COMMAND actor=1' in s and 'EXPORT_UI_RELOAD_STARTED trigger=native_client_input' in s
        good = good and 'EXPORT_UI_RELOAD_COMPLETED ammo=30' in s and authority['largest_ack'] == 169 and not strict.search(s)
        good = good and authority['shots'] == 6 and authority['lowest_ammo'] == 24 and authority['reload_completed'] is True
    else:
        f, a = r['fired_hud'], r['reloaded_hud']
        good = good and r['exit'] == 0 and r['clean_exit'] is True and (f['health'], f['ammo'], f['reserve']) == (100, 14, 60)
        good = good and (a['health'], a['ammo'], a['reserve']) == (100, 15, 59) and f['ammo'] + f['reserve'] == a['ammo'] + a['reserve'] == 74
        for p in path.glob('*-ocr.process.json'):
            good = good and receipt(p)
        good = good and len(list(path.glob('*-ocr.process.json'))) == 6
        for stem in ['05-inspection-pause', '06-inspection-pause']:
            good = good and 'Training is paused.' in (path / (stem + '-pause-ocr.stdout.txt')).read_text()
    check('ui/' + folder, good)
    flows.append({'flow': folder, 'controller_sha256': w['controller_sha256'], 'executable_sha256': r['executable_sha256'],
                  'seconds': w['seconds'], 'timeout_seconds': w['timeout_seconds'], 'close': close, 'worker_exit': w['worker_exit'],
                  'independent_checks_passed': good,
                  'post_source_limit': 'UI result retains initial source; successful pinned controller enforces unchanged_export after runtime. No separate UI after-source snapshot.'})
DETAILS['flows'] = flows

dump('checks.json', CHECKS)
dump('findings-data.json', DETAILS)
dump('counts.json', {'checks': len(CHECKS), 'failed_checks': [r['id'] for r in CHECKS if not r['passed']],
                     'matrix_groups': len(matrix_rows), 'matrix_command_receipts': sum('exit' in r for r in matrix_rows),
                     'campaign_conditions': len(campaign_rows), 'campaign_native_reports': len(child_rows),
                     'campaign_native_logs': len(child_rows), 'audio_baseline_groups': 10,
                     'audio_baseline_assertions': sum(c for c, _ in expected_counts[:10]), 'audio_mutants': 3,
                     'audio_wav': len(wav_rows), 'package_archives': len(package_rows),
                     'artifact_members_and_nested_occurrences': len(MEMBERS), 'archives_including_nested': len(ARCHIVES)})
print(json.dumps(load(BASE / 'counts.json'), indent=2))
print('Transport', [(x['id'], x['digest_matches']) for x in transport])
print('Logs', {k: v for k, v in DETAILS['log_scan'].items() if k not in ('rows', 'pattern')})
print('Packages', package_rows)
print('PCM', wav_rows)
print('Raw byte totals', [(p.name, sum(f.stat().st_size for f in p.rglob('*') if f.is_file())) for p in (BASE / 'raw').iterdir()])
