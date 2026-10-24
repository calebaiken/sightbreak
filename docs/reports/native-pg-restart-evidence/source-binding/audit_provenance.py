"""Static provenance audit. Reads Git/files only; never imports or runs application/harness code."""
import collections
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import zipfile

OUT = Path(__file__).resolve().parent
PACKET = OUT.parent
CONTROLLER = Path(r'C:/Users/blith/AppData/Local/Temp/opencode/receipt-review-37c55530e7a77a8a/CONTROLLER')
REPO = Path(r'C:/Users/blith/OneDrive/Documents/Default Project/sightbreak')
GIT = ['git', '-c', 'core.packedGitWindowSize=16m', '-c', 'core.packedGitLimit=64m', '-C', str(REPO)]
MAPPING_PIN = '70a6936e0ebca5b38559fe013d18b0174cf1689bd6fb85788b059b613c70b2bd'
FROZEN_VERDICT_PIN = '750bfb02e65f3f348567b8bf453b4387f931c70549d7c50469d377fc63bec2ee'
HARNESS_COMMIT = '31438cbcea6ef08a131ae312c65b94f7e3e882c3'
STAGES = ['01-before.json', '02-committed-before-kill.json', '03-after-kill.json',
          '04-after-recovery.json', '05-after-second-restart.json']
errors = []
checks = 0


def check(condition, message):
    global checks
    checks += 1
    if not condition:
        errors.append(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def git(*args):
    return subprocess.check_output(GIT + list(args))


def show(revision, path):
    return git('show', revision + ':' + path)


def tree(revision, *prefixes):
    result = {}
    for entry in git('ls-tree', '-rz', revision, '--', *prefixes).split(b'\0'):
        if entry:
            meta, path = entry.split(b'\t', 1)
            mode, kind, oid = meta.decode().split()
            if kind == 'blob':
                result[path.decode()] = oid
    return result


def blobs(oids):
    oids = list(dict.fromkeys(oids))
    process = subprocess.run(GIT + ['cat-file', '--batch'],
                             input=''.join(x + '\n' for x in oids).encode(), capture_output=True, check=True)
    offset = 0
    result = {}
    for expected in oids:
        end = process.stdout.index(b'\n', offset)
        oid, kind, length = process.stdout[offset:end].decode().split()
        length = int(length)
        data = process.stdout[end + 1:end + 1 + length]
        check(oid == expected and kind == 'blob', 'git batch identity ' + expected)
        check(hashlib.sha1(b'blob ' + str(length).encode() + b'\0' + data).hexdigest() == oid,
              'independent Git blob hash ' + oid)
        result[oid] = data
        offset = end + length + 2
    check(offset == len(process.stdout), 'git batch byte framing')
    return result


mapping_bytes = (CONTROLLER / 'mapping.json').read_bytes()
check(sha(mapping_bytes) == MAPPING_PIN, 'mapping pin')
check(sha((PACKET / '_FROZEN_VERDICT.md').read_bytes()) == FROZEN_VERDICT_PIN, 'blind verdict unchanged')
mapping = json.loads(mapping_bytes)
EVIDENCE = mapping['evidence_commit']
check(mapping['frozen_measured_harness_commit'] == HARNESS_COMMIT, 'frozen harness commit')
evidence_tree = tree(EVIDENCE, 'docs/reports/native-pg-restart-evidence/r9/baseline',
                     'docs/reports/native-pg-restart-evidence/r10/candidate-7b6f379',
                     'scripts/validate_native_transaction_restart.py', 'scripts/native_transaction_restart_probe.gd')
data_by_oid = blobs(evidence_tree.values())
raw = {name: data_by_oid[oid] for name, oid in evidence_tree.items()}
verified_bindings = set()


def binding(record):
    name = record['path']
    data = raw[name]
    check(record['commit'] == EVIDENCE and record['git_blob'] == evidence_tree[name], 'bound commit/path/blob ' + name)
    check(len(data) == record['bytes'] and sha(data) == record['sha256'], 'bound original length/SHA256 ' + name)
    verified_bindings.add(name)
    return data


report = {'mapping_sha256': sha(mapping_bytes), 'blind_verdict_sha256': FROZEN_VERDICT_PIN,
          'evidence_commit': EVIDENCE, 'observations': [], 'groups': {}, 'scope': 'Static/source-and-artifact binding, not execution attestation.'}
original_rows = [x for x in mapping['files'] if 'original' in x]
check(len(original_rows) == 114, 'exactly 114 observation mappings')
check(len({x['packet_path'] for x in original_rows}) == 114, '114 unique mapped packet paths')
operation_counts = collections.Counter()
for row in original_rows:
    original = binding(row['original'])
    raw_path = REPO / row['original']['path']
    check(raw_path.is_file(), 'working raw artifact exists ' + str(raw_path))
    raw_identical = raw_path.is_file() and raw_path.read_bytes() == original
    check(raw_identical, 'working raw artifact byte-identical to Git ' + row['original']['path'])
    current = original
    group_name, case_name, name = row['packet_path'].split('/')
    aliases = mapping['labels'][group_name]['cases'][case_name]['aliases']
    permitted = {}
    for category, source, target in aliases:
        for spelling in {source, source.replace('\\', '/'), source.replace('/', '\\')}:
            permitted[(spelling, target, category, 'literal')] = True
            permitted[(json.dumps(spelling)[1:-1], target, category, 'JSON-escaped')] = True
    for transformation in row['transformations']:
        old = transformation['original_text'].encode()
        new = transformation['replacement_text'].encode()
        check((transformation['original_text'], transformation['replacement_text'], transformation['category'],
               transformation['representation']) in permitted, 'transform restricted to declared absolute-path alias ' + row['packet_path'])
        check(current.count(old) == transformation['occurrences'], 'exact transformation count ' + row['packet_path'])
        current = current.replace(old, new)
        operation_counts[transformation['category']] += transformation['occurrences']
    packet = (PACKET / row['packet_path']).read_bytes()
    check(current == packet, 'full transformation replay ' + row['packet_path'])
    check(len(packet) == row['packet_bytes'] and sha(packet) == row['packet_sha256'], 'transformed hash/size ' + row['packet_path'])
    check(row['byte_identical'] == (original == packet), 'truthful byte-identical flag ' + row['packet_path'])
    if name in STAGES:
        check(original == packet and not row['transformations'], 'unmodified SQL bytes ' + row['packet_path'])
    report['observations'].append({'packet_path': row['packet_path'], 'original_path': row['original']['path'],
                                   'git_blob': row['original']['git_blob'], 'raw_git_identical': raw_identical,
                                   'byte_identical': original == packet, 'transformations': len(row['transformations'])})
for row in mapping['files']:
    if row.get('generated'):
        check(sha((PACKET / row['packet_path']).read_bytes()) == row['packet_sha256'], 'derived file hash ' + row['packet_path'])
        for record in row['original_inputs']:
            binding(record)
for row in mapping['ancillary']:
    check((CONTROLLER / row['controller_relative_path']).read_bytes() == binding(row['original']),
          'ancillary controller copy ' + row['controller_relative_path'])
for record in mapping['withheld_sources']:
    data = binding(record)
    check((CONTROLLER / 'frozen-source' / Path(record['path']).name).read_bytes() == data,
          'controller frozen-source copy ' + record['path'])
    check(show(HARNESS_COMMIT, record['path']) == data, 'frozen 31438cb source equals controller/evidence ' + record['path'])

for label, record in mapping['labels'].items():
    summary = json.loads(binding(record['original_summary']))
    prefix = record['original_summary']['path'].rsplit('/', 1)[0] + '/'
    revision = record['measured_source_commit']
    source_tree = tree(revision, 'game', 'backend')
    source_blobs = blobs(source_tree.values())
    source_data = {name: source_blobs[oid] for name, oid in source_tree.items()}
    source_manifest = json.loads(raw[prefix + 'source-manifest.json'])
    cache_manifest = json.loads(raw[prefix + 'cache-manifest.json'])
    evidence_manifest = json.loads(raw[prefix + 'evidence-manifest.json'])
    check(set(source_manifest) == set(source_data), label + ' source manifest exact measured Git tree file set')
    archive_path = OUT / label / 'reproduced-source-archive.zip'
    git('archive', '--format=zip', '--output=' + str(archive_path), revision, 'game', 'backend')
    with archive_path.open('rb') as stream:
        archive_digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    check(archive_digest == summary['archive_sha256'], label + ' deterministic source archive SHA256')
    with zipfile.ZipFile(archive_path) as archive:
        archived_data = {i.filename: archive.read(i) for i in archive.infolist() if not i.is_dir()}
    archived = {name: sha(data) for name, data in archived_data.items()}
    check(archived == source_manifest, label + ' archive file bytes equal complete source manifest')
    crlf_paths = []
    for name, data in source_data.items():
        if data != archived_data[name]:
            crlf_paths.append(name)
            check(data.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n') == archived_data[name],
                  label + ' Git archive difference is only LF-to-CRLF ' + name)
    if label == 'Set-8F5F7604':
        candidate_archived_ancillary = archived_data['game/tests/native_economy_test.gd']
    for name, digest in evidence_manifest.items():
        check(sha(raw[prefix + name]) == digest, label + ' retained evidence manifest ' + name)
    expected_evidence = {name[len(prefix):] for name in raw if name.startswith(prefix)} - {'evidence-manifest.json'}
    check(set(evidence_manifest) == expected_evidence, label + ' evidence manifest complete')
    for section in ['source', 'source_after']:
        check(summary[section] == record['source_identity'], label + ' mapped source identity ' + section)
        check(summary[section]['status'] == '' and summary[section]['measured_commit'] == revision, label + ' clean measured source identity')
        for folder in ['game', 'backend']:
            check(summary[section][folder + '_tree'] == git('rev-parse', revision + ':' + folder).decode().strip(),
                  label + ' source tree identity ' + folder)
    check(summary['harness_checkout'] == summary['harness_after'], label + ' before/after harness identity consistency')
    check(summary['harness_checkout']['checkout_head'] == HARNESS_COMMIT
          and summary['harness_checkout']['measured_commit'] == HARNESS_COMMIT
          and summary['harness_checkout']['status'] == '', label + ' frozen harness identity')
    for folder in ['game', 'backend']:
        check(summary['harness_checkout'][folder + '_tree'] == git('rev-parse', HARNESS_COMMIT + ':' + folder).decode().strip(),
              label + ' harness tree identity ' + folder)
        check(summary['cache_source'][folder + '_tree'] == git('rev-parse', summary['cache_source']['measured_commit'] + ':' + folder).decode().strip(),
              label + ' cache source Git identity ' + folder)
    check(summary['cache_source']['game_tree'] == summary['source']['game_tree'] and summary['cache_source']['status'] == '',
          label + ' cache identity bound to same clean game tree')
    for stem, key in [('validate_native_transaction_restart.py', 'harness_sha256'),
                      ('native_transaction_restart_probe.gd', 'probe_sha256')]:
        data = raw[prefix + stem]
        check(data == show(HARNESS_COMMIT, 'scripts/' + stem), label + ' retained executed script equals frozen source ' + stem)
        check(sha(data) == summary[key] == record[key], label + ' summary/mapping/source digest ' + key)
    check(summary['godot_sha256'] == record['executable_sha256'], label + ' executable pin agrees')
    check(len(cache_manifest) == 62 and all(re.fullmatch('[0-9a-f]{64}', x) for x in cache_manifest.values()), label + ' 62 valid recorded cache digests')
    cache_scripts = [p for p in cache_manifest if p.endswith(('.gd', '.gdc', '.pck', '.remap'))]
    check(not cache_scripts, label + ' no recorded executable script/remap payload in copied cache')
    check('[autoload]' not in source_data['game/project.godot'].decode(), label + ' no project autoload replacement')
    source_fixture_reads = []
    for name, data in source_data.items():
        if name.endswith(('.gd', '.py')) and '/tests/' not in name:
            if b'SIGHTBREAK_RECEIPT_FIXTURE' in data:
                source_fixture_reads.append(name)
    check(not source_fixture_reads, label + ' production source does not read restart fixture environment')
    expected_service = [('GET', '/health', 200)]
    case_bindings = []
    for index, (case_name, case_record) in enumerate(record['cases'].items()):
        cp = case_record['original_prefix']
        expected_paths = {p for p in raw if p.startswith(cp)}
        mapped_paths = {row['original']['path'] for row in original_rows if row['packet_path'].startswith(label + '/' + case_name + '/')}
        check(mapped_paths == expected_paths, label + '/' + case_name + ' all raw case files mapped without omission')
        fixture = json.loads(raw[cp + 'fixture.redacted.json'])
        timeline = [json.loads(line) for line in raw[cp + 'timeline.jsonl'].splitlines()]
        initial_command = next(x['command'] for x in timeline if x['event'] == 'native_started')
        aliases = {x[0]: x[1] for x in case_record['aliases']}
        check(initial_command[0] == aliases['executable_path']
              and initial_command[initial_command.index('--path') + 1] == aliases['project_path']
              and initial_command[initial_command.index('--script') + 1] == aliases['external_probe_path']
              and fixture['journal'] == aliases['private_journal_path'], label + '/' + case_name + ' aliases derive from original observed command/fixture')
        project_root = aliases['project_path'].replace('\\', '/').rsplit('/', 1)[0]
        cmd = summary['service']['command']
        check(cmd[cmd.index('--app-dir') + 1].replace('\\', '/') == project_root + '/backend', label + '/' + case_name + ' API and native use same archived source root')
        check(summary['setup']['command'][3].replace('\\', '/') == project_root, label + '/' + case_name + ' setup uses same archived source root')
        check(summary['setup']['command'][4] == summary['database'], label + '/' + case_name + ' setup database binding')
        for stage in STAGES:
            state = json.loads(raw[cp + stage])
            check(state['postgresql']['current_database'] == summary['database'] and state['postgresql']['inet_server_port'] == 55439,
                  label + '/' + case_name + ' recorded PostgreSQL database/port ' + stage)
        result = json.loads(raw[cp + 'result.json'])
        check(summary['runs'][index] == result, label + '/' + case_name + ' summary embeds actual retained result')
        expected_service.append(('POST', '/market/list', 201))
        requests = [x for x in timeline if x['event'] == 'proxy_request']
        responses = [x for x in timeline if x['event'] == 'proxy_upstream_response']
        check(len(requests) == len(responses), label + '/' + case_name + ' complete upstream pairs')
        for request, response in zip(requests, responses):
            check(request['path'] == response['path'] and request['phase'] == response['phase'], label + '/' + case_name + ' ordered upstream request/response pairing')
            expected_service.append((request['method'], request['path'], response['status']))
        case_bindings.append({'case': case_name, 'raw_files': len(expected_paths), 'database': summary['database'],
                              'native_project': aliases['project_path'], 'journal_path': fixture['journal'],
                              'proxy_url': fixture['url'], 'upstream_requests': len(requests)})
    service = raw[prefix + 'service.stdout.txt'].decode()
    service_requests = [(m.group(1), m.group(2), int(m.group(3))) for m in re.finditer(r'"(GET|POST|PUT|DELETE) ([^ ]+) HTTP/1\.1" (\d+)', service)]
    check(service_requests[:len(expected_service)] == expected_service, label + ' full paired-run upstream service request sequence')
    port = summary['service']['command'][summary['service']['command'].index('--port') + 1]
    check('http://127.0.0.1:' + port in service, label + ' recorded service listens at configured proxy upstream')
    report['groups'][label] = {
        'source_commit': revision, 'game_tree': summary['source']['game_tree'], 'backend_tree': summary['source']['backend_tree'],
        'archive_sha256': archive_digest, 'source_manifest_entries_verified': len(source_manifest),
        'git_blob_to_archive_crlf_only_files': len(crlf_paths),
        'cache_manifest_entries': len(cache_manifest), 'cache_payloads_present_in_retained_evidence': False,
        'evidence_manifest_entries_verified': len(evidence_manifest), 'service_paired_request_sequence_count': len(expected_service),
        'harness_sha256': summary['harness_sha256'], 'probe_sha256': summary['probe_sha256'],
        'source_digests': {name: sha(source_data[name]) for name in [
            'game/scripts/ui/economy_ui.gd', 'game/scripts/ui/economy_api.gd', 'game/scripts/ui/transaction_journal.gd',
            'backend/app.py', 'backend/models.py', 'game/project.godot'] if name in source_data},
        'archived_source_digests': {name: archived[name] for name in [
            'game/scripts/ui/economy_ui.gd', 'game/scripts/ui/economy_api.gd', 'game/scripts/ui/transaction_journal.gd',
            'backend/app.py', 'backend/models.py', 'game/project.godot'] if name in source_data},
        'case_bindings': case_bindings,
        'service_launcher_pid': summary['service']['pid'],
        'service_logged_pid': int(re.search(r'Started server process \[(\d+)\]', service).group(1)),
    }

candidate = report['groups']['Set-8F5F7604']
baseline = report['groups']['Set-673EECBC']
check(candidate['backend_tree'] == baseline['backend_tree'], 'same complete backend tree for both arms')
check(candidate['source_digests']['game/scripts/ui/economy_api.gd'] == baseline['source_digests']['game/scripts/ui/economy_api.gd'],
      'same actual EconomyAPI implementation for both arms')
ancillary = 'docs/reports/native-pg-restart-evidence/r10/candidate-7b6f379/'
original_probe = raw[ancillary + 'native-economy-original/executed-probe.gd']
calibrated_probe = raw[ancillary + 'native-economy-dns-calibrated/executed-probe.gd']
check(original_probe == candidate_archived_ancillary, 'ancillary original source equals actual candidate archive bytes')
check(original_probe.replace(b'\r\n', b'\n') == show(candidate['source_commit'], 'game/tests/native_economy_test.gd').replace(b'\r\n', b'\n'),
      'ancillary original source equals candidate Git after verified newline normalization')
old, new = b'"http://127.0.0.1:9"', b'"http://native-receipt-oracle.invalid"'
check(original_probe.count(old) == 1 and original_probe.replace(old, new) == calibrated_probe, 'ancillary exact one-literal calibration')
report['counts'] = {'observations': len(original_rows),
                    'unchanged_observations': sum(x['byte_identical'] for x in original_rows),
                    'transformed_observations': sum(not x['byte_identical'] for x in original_rows),
                    'sql_stage_files_byte_identical': sum(x['packet_path'].split('/')[-1] in STAGES for x in original_rows),
                    'generated_aids': sum(x.get('generated', False) for x in mapping['files']),
                    'ancillary_bound_files': len(mapping['ancillary']), 'unique_original_bindings': len(verified_bindings),
                    'transformed_path_occurrences': dict(operation_counts)}
report['current_probe_matches_frozen'] = (REPO / 'scripts/native_transaction_restart_probe.gd').read_bytes() == show(HARNESS_COMMIT, 'scripts/native_transaction_restart_probe.gd')
report['current_probe_matches_frozen_after_newline_normalization'] = (REPO / 'scripts/native_transaction_restart_probe.gd').read_bytes().replace(b'\r\n', b'\n') == show(HARNESS_COMMIT, 'scripts/native_transaction_restart_probe.gd').replace(b'\r\n', b'\n')
exe_path = Path(mapping['labels']['Set-8F5F7604']['cases']['case-01']['aliases'][0][1])
if exe_path.is_file():
    digest = hashlib.sha256()
    with exe_path.open('rb') as source:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
    report['current_executable_bytes_sha256'] = digest.hexdigest()
    check(digest.hexdigest() == mapping['labels']['Set-8F5F7604']['executable_sha256'], 'current executable bytes match recorded executable pin (not historical execution attestation)')
report['checks_evaluated'] = checks
report['mismatches'] = errors
(OUT / 'provenance-audit.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps({k: v for k, v in report.items() if k != 'observations'}, indent=2))
