#!/usr/bin/env python3
"""Independent read-only decoding of the completed single native preflight."""
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = Path('/workspace/sightbreak-collector-preflight-c324')
RAW = ROOT / 'builds/collector-native-preflight-c324-20261024'
SOURCE = 'c32415148db1f110bbc7eadfca3793d4693429ff'
ENGINE = Path('/workspace/tools/godot-4.7.2/Godot_v4.7.2-stable_linux.x86_64')
RELEASE = '236413df815c9404b5a70726b210669f66edb3fa'
predicates = []


def check(condition, name):
    predicates.append(name)
    if not condition:
        raise AssertionError(name)


def sha(path, algorithm='sha256'):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, algorithm).hexdigest()


def read(name):
    return json.loads((RAW / name).read_text())


def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args], timeout=20)


check(os.sched_getaffinity(0) == {4}, 'audit CPU4')
check(git('rev-parse', 'HEAD').decode().strip() == SOURCE, 'exact runtime HEAD')
check(not git('status', '--porcelain=v1').strip(), 'clean runtime checkout/index')
before, after = read('source-before.json'), read('source-after.json')
check(before == after, 'identical source/UID before and after manifests')
check(before == json.loads((HERE / 'source-admission.json').read_text()), 'matches prerelease source admission')
tree = {}
for entry in git('ls-tree', '-rz', SOURCE).split(b'\0'):
    if not entry:
        continue
    metadata, raw_name = entry.split(b'\t')
    name = os.fsdecode(raw_name)
    if name.startswith('docs/'):
        continue
    mode, kind, blob = metadata.decode().split()
    path = ROOT / name
    info = path.lstat()
    check(kind == 'blob', 'blob kind ' + name)
    if mode == '120000':
        check(stat.S_ISLNK(info.st_mode), 'symlink mode ' + name)
        data = os.fsencode(os.readlink(path))
    else:
        check(stat.S_ISREG(info.st_mode) and bool(info.st_mode & 0o111) == (mode == '100755'), 'regular mode ' + name)
        data = path.read_bytes()
    check(hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest() == blob, 'git blob ' + name)
    recorded = before['entries'][name]
    check(recorded == {'blob': blob, 'mode': mode, 'bytes': len(data),
                       'sha256': hashlib.sha256(data).hexdigest(),
                       'sha512': hashlib.sha512(data).hexdigest()}, 'actual hashes ' + name)
    tree[name] = recorded
check(len(tree) == 507 and tree == before['entries'], 'complete507-path source union')
uids = {str(p.relative_to(ROOT)): sha(p) for p in sorted((ROOT / 'game').rglob('*.uid'))}
check(len(uids) == 138 and uids == before['uid'], 'all138 UID bytes unchanged')
check(not (ROOT / 'game/.godot').exists(), 'source cache remains absent')
engine = read('engine.json')
check(sha(ENGINE) == engine['sha256'] == '8d106cbe6144c2dc7e881d61d2429c1a8a76e6b22ef48bd5e48dcf934953f71e', 'engine SHA256')
check(sha(ENGINE, 'sha512') == engine['sha512'] == 'ac9f3af3d8b62237694bc03e7422b8f7b1a39095cf4eeaa8361b7465f13bc9dbaad47f60ac0ac217c9f0b2b3712be207039cd83953f4c72087214bd0357cabbc', 'engine SHA512')
check(sha(ENGINE.parent / 'godot.zip', 'sha512') == engine['zip_sha512'] == '9aa00f7a605200940bce3027a567b782f49bd8e940dd06ae9e987bd65aee1b1467edd56ed84fcdcbdd44354bf613bdbb4e5d2913e925850368e150c59ed54c65', 'source-pinned ZIP SHA512')
release = read('root-release.json')
check(release['source'] == SOURCE and release['root_release_commit'] == RELEASE and release['authorized_single_invocation'] is True, 'exact pushed root release')
check(release['wrapper_sha256'] == sha(HERE / 'run_once.py') == '1e3a8123a5c3adf4d3d379c3c6ff5703f514c9f7425a76e40cb2f5f52922b057', 'released wrapper bytes')

ansi = re.compile(r'\x1b\[[0-?]*[ -/]*[@-~]')
errors = re.compile(r'^(?:SCRIPT ERROR|ERROR:)|Parse Error|ObjectDB.*leaked|Leaked instance|^Orphan StringName: [^\r\n]+ \(static: [0-9]+, total: [0-9]+\)\r?$|^StringName: [1-9][0-9]* unclaimed string names at exit\.\r?$', re.M)
logs, warnings = {}, {}
for path in sorted(RAW.rglob('*.log')):
    original = path.read_text(errors='strict')
    text = ansi.sub('', original)
    name = str(path.relative_to(RAW))
    check(errors.search(original) is None and errors.search(text) is None, 'strict full log ' + name)
    logs[name] = {'bytes': path.stat().st_size, 'sha256': sha(path)}
    warnings[name] = [line for line in text.splitlines() if 'WARNING' in line.upper()]
expected_logs = {'native/' + name + '.log' for name in ('producer-01-bootstrap', 'private-import', 'producer-02-before-movement_prediction', 'movement_prediction', 'producer-03-after-movement_prediction')}
check(expected_logs <= logs.keys(), 'all five workload logs retained')
summary = re.findall(r'^MOVEMENT_PREDICTION_TEST checks=(\d+) failures=(\d+) maximum_error_m=([0-9.]+)$', (RAW / 'native/movement_prediction.log').read_text(), re.M)
check(len(summary) == 1 and summary[0][:2] == ('742', '0'), 'unique742/0 terminal summary')
check(not (RAW / 'runner.stderr').read_bytes(), 'empty runner stderr')
stdout = json.loads((RAW / 'runner.stdout').read_text())
check(stdout == {'passed': True, 'suites': ['movement_prediction'], 'source_resources_unchanged': True, 'temporary_project_removed': True}, 'runner terminal result')
isolation = read('native/isolation.json')
results = read('native/results.json')
check(len(results) == 1 and results[0]['suite'] == 'movement_prediction' and results[0]['exit'] == 0, 'one successful maintained suite')
suite = results[0]
game_inventory = {name[5:]: value['sha256'] for name, value in tree.items() if name.startswith('game/')}
check(isolation['source_resources_sha256'] == game_inventory, 'runner native source inventory independently matches game files')
check(isolation['engine'] == '4.7.2.stable.official.ed1daf0bf', 'native accepted engine version')
check(isolation['suite_timeout_seconds'] == 120 and isolation['probe_timeout_seconds'] == 30, 'original120/30 phase caps')
check(isolation['failure'] is None and isolation['finalization_failures'] == [], 'no runner finalization failure')
namespace = isolation['namespace']
check(re.fullmatch(r'SIGHTBREAK-native-tests-[0-9a-f]{32}', namespace) is not None, 'unique namespace shape')
namespace_path = RAW / 'state/data' / namespace
producers = []
for path in sorted((RAW / 'native').glob('producer-*.json')):
    item = json.loads(path.read_text())
    selected = 'bootstrap' if 'bootstrap' in path.name else 'movement_prediction'
    check(item['os'] == 'Linux' and item['uses_custom_user_dir'] is True, 'native custom directory enabled ' + path.name)
    check(item['custom_user_dir'] == namespace + '/' + selected, 'native custom name ' + path.name)
    check(Path(item['data_dir']) == RAW / 'state/data' and Path(item['user_data_dir']) == namespace_path / selected, 'native user/data paths ' + path.name)
    check(not item['profile_exists'] and not item['diagnostics_exist'], 'no prior profile/diagnostics ' + path.name)
    check(Path(item['project_path']) == Path(suite['command'][2]) and Path(item['project_path']).is_relative_to(RAW / 'temporary'), 'native private project path ' + path.name)
    producers.append(item)
check(len(producers) == 3, 'exactly three engine producer receipts')
for label in ('before', 'after'):
    item = suite[label]
    disk = json.loads(Path(item['producer_receipt']).read_text())
    check({k: item[k] for k in disk} == disk, label + ' result binds original native receipt')
    check(item['run']['exit'] == 0 and item['run']['wall_seconds'] < 30, label + ' producer under30s')
check(isolation['import']['exit'] == 0 and isolation['import']['wall_seconds'] < 120 and suite['wall_seconds'] < 120, 'import and suite under120s')
check(suite['command'] == [str(ENGINE), '--path', str(Path(producers[0]['project_path'])), '--headless', '--script', 'res://tests/movement_prediction_test.gd'], 'unchanged movement native arguments')
copied = {str(p.relative_to(RAW / 'native/movement_prediction-userdata')): sha(p)
          for p in sorted((RAW / 'native/movement_prediction-userdata').rglob('*')) if p.is_file()}
check(copied == suite['produced_files_sha256'], 'retained produced user files match hashes')
check(not namespace_path.exists() and not Path(producers[0]['project_path']).parent.exists(), 'native user namespace/private project actually absent')
check(isolation['cleanup'] == [{'user_namespace': str(namespace_path), 'removed': True}], 'only unique owned namespace cleanup')
check(all(isolation[key] is True for key in ('source_resources_unchanged', 'copied_resources_unchanged', 'temporary_project_removed')), 'all runner isolation invariants')

wrapper = read('wrapper.json')
samples = [json.loads(line) for line in (RAW / 'process-samples.jsonl').read_text().splitlines()]
elapsed = [row['elapsed_seconds'] for row in samples]
check(elapsed == sorted(elapsed) and len(samples) == 141, 'ordered141 finite samples')
check(wrapper['runner_exit'] == 0 and wrapper['runner_exit_observed_seconds'] < 420 and wrapper['launch_count'] == 1, 'one runner completed before420')
check(wrapper['runner_exit_observed_seconds'] == wrapper['execution_stop_observed_seconds'], 'completion and stop observation agree')
check(wrapper['runner_exit_observed_seconds'] >= elapsed[-2], 'exit observation follows final running sample')
check(datetime.fromisoformat(wrapper['runner_exit_observed_utc']) < datetime.fromisoformat(wrapper['finished_utc']), 'cleanup/finalization follows exit observation')
check(samples[-1]['stage'] == 'cleanup-start' and samples[-1]['processes'] == [], 'observed group/identities absent at cleanup-start')
check(elapsed[-1] - wrapper['runner_exit_observed_seconds'] < 5 and wrapper['cleanup']['actions'] == [], 'cleanup under5s without signals')
check(0 <= wrapper['wall_seconds_including_cleanup'] - wrapper['runner_exit_observed_seconds'] < 5, 'cleanup plus finalization under5s')
check(not wrapper['timed_out'] and wrapper['failure'] is None, 'no wrapper timeout or exception')
check(wrapper['supervisor']['threads'] == {str(wrapper['supervisor']['pid']): [4]}, 'supervisor CPU4 receipt')
identities = {}
for sample in samples:
    for item in sample['processes']:
        identity = (item['pid'], item['start_ticks'])
        identities.setdefault(identity, item)
        check(item['pgid'] == wrapper['runner_pid'] and item['sid'] == wrapper['runner_pid'], 'owned native group/session ' + str(identity))
        check(bool(item['threads']) and all(cpus == [0, 1] for cpus in item['threads'].values()), 'all sampled native thread affinities ' + str(identity))
check(len(identities) == 7, 'seven observed identities including runner')
expected_identities = {(item['pid'], item['start_ticks']) for item in wrapper['observed_identities']}
check(set(identities) == expected_identities, 'samples reconstruct complete reported identity set')
observed_commands = [row['argv'] for row in identities.values()]
check(sum(argv and argv[0] == str(ENGINE) for argv in observed_commands) == 6, 'six observed Godot invocations')
check(sum('--version' in argv for argv in observed_commands) == 1, 'observed original version invocation')
check(all(not argv or '--native-input-observation' not in argv for argv in observed_commands), 'enabled emitter flag never launched')
check(not wrapper['display_present'], 'no display launch')
postrun = []
for pid, ticks in sorted(identities):
    path = Path('/proc') / str(pid) / 'stat'
    try:
        text = path.read_text()
        current = int(text[text.rindex(')') + 2:].split()[19])
    except FileNotFoundError:
        current = None
    check(current != ticks, 'scoped post-run identity absent ' + str((pid, ticks)))
    postrun.append({'pid': pid, 'start_ticks': ticks, 'current_start_ticks': current})
outer_path = Path('/workspace/collector-native-preflight-outer-tool-receipt-20261024.json')
outer_bytes = outer_path.read_bytes()
outer = json.loads(outer_bytes)
check(outer['source'] == SOURCE and outer['release'] == release, 'actual outer receipt source/release')
history = outer['tool_history']
check(len(history) == 2 and history[0]['phase'] == 'initial' and history[1]['phase'] == 'poll', 'one launch and one terminal poll')
check(history[0]['result']['session_id'] == 83052 and history[0]['result']['chunk_id'] == '4a98bd', 'exact initial tool identity')
check(history[1]['result']['exit_code'] == 0 and history[1]['result']['chunk_id'] == '53626a', 'actual outer terminal zero')
check(json.loads(history[1]['result']['output']) == wrapper, 'outer full output agrees with raw wrapper receipt')
check(sha(RAW / 'root-release.json') == wrapper['release_sha256'], 'release-byte hash binding')
(HERE / 'outer-tool-receipt.json').write_bytes(outer_bytes)
raw_inventory = {str(p.relative_to(RAW)): {'bytes': p.stat().st_size, 'sha256': sha(p)}
                 for p in sorted(RAW.rglob('*')) if p.is_file()}
result = {'passed': True, 'source': SOURCE, 'root_release': RELEASE, 'predicates': len(predicates),
          'checks': int(summary[0][0]), 'failures': int(summary[0][1]), 'maximum_error_m': float(summary[0][2]),
          'source_paths': len(tree), 'uids': len(uids), 'logs': logs, 'warnings': warnings,
          'native_producers': producers, 'user_files': copied,
          'runner_exit_observed_seconds': wrapper['runner_exit_observed_seconds'],
          'wall_seconds_including_cleanup': wrapper['wall_seconds_including_cleanup'],
          'finite_samples': len(samples), 'maximum_sample_gap_seconds': max(b - a for a, b in zip(elapsed, elapsed[1:])),
          'cleanup_elapsed_to_sample_seconds': elapsed[-1] - wrapper['runner_exit_observed_seconds'],
          'observed_processes': list(identities.values()), 'postrun_identity_readback': postrun,
          'outer_receipt_sha256': hashlib.sha256(outer_bytes).hexdigest(), 'raw_inventory': raw_inventory,
          'limitations': ['Enabled emitter/overhead unexecuted', 'Finite sampling can miss short or escaped processes',
                          'Version subprocess raw stdout/stderr not retained by existing runner',
                          'Removed private project bytes rely on source inventories and unchanged runner isolation contract']}
(HERE / 'actual-audit.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
print(json.dumps({k: result[k] for k in ('passed', 'predicates', 'checks', 'failures', 'source_paths', 'uids', 'finite_samples', 'maximum_sample_gap_seconds')}))
