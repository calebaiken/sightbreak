#!/usr/bin/env python3
"""Pure, read-only independent audit of one already-complete actual capture."""
import collections
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

SOURCE = '26a1c59ab6d141529a3254ac7f8e68ee4ae99d8b'
ENGINE_SHA = '8d106cbe6144c2dc7e881d61d2429c1a8a76e6b22ef48bd5e48dcf934953f71e'
source, raw, destination = map(Path, sys.argv[1:4])
sys.path.insert(0, str(source / 'scripts'))
from analyze_audio_lifecycle import analyze
from native_log import failed

checks = []
def check(name, value, detail=None):
    checks.append({'check': name, 'passed': bool(value), 'detail': detail})
def load(name):
    return json.loads((raw / name).read_bytes())
def sha(data):
    return hashlib.sha256(data).hexdigest()
def inventory(directory):
    return {str(p.relative_to(directory)): sha(p.read_bytes())
            for p in sorted(directory.rglob('*')) if p.is_file()}
def git(*args):
    return subprocess.check_output(['git', *args], cwd=source)

overall = load('overall.json')
check('source_commit', overall['source_commit'] == SOURCE)
check('actual_current_head', git('rev-parse', 'HEAD').decode().strip() == SOURCE)
check('actual_source_clean', not git('status', '--porcelain=v1', '--untracked-files=all').strip())
for key in ('engine_sha256', 'engine_sha256_before', 'engine_sha256_after', 'engine_sha256_sealed'):
    check(key, overall[key] == ENGINE_SHA)
check('actual_current_executable', sha(Path(overall['engine']).read_bytes()) == ENGINE_SHA)

manifest = {}
for row in git('ls-tree', '-rz', SOURCE, '--', 'game', 'scripts').decode().split('\0'):
    if not row:
        continue
    meta, name = row.split('\t')
    mode, kind, blob = meta.split()
    data = git('cat-file', 'blob', blob)
    manifest[name] = {'git_blob': blob, 'mode': mode, 'sha256': sha(data), 'bytes': len(data)}
    check('local_source:' + name, (source / name).read_bytes() == data)
for name in ('source-before.json', 'source-after.json', 'source-sealed.json'):
    check(name, load(name) == manifest)
copies = {name[5:]: item['sha256'] for name, item in manifest.items() if name.startswith('game/')}
check('exact-copy-map', load('exact-copy-map.json') == copies)
custom = overall['declared_project_override']['custom_user_dir']
check('unique_custom_namespace', re.fullmatch(r'SIGHTBREAK-audio-lifecycle-[0-9a-f]{32}/input_mode', custom))
config = git('show', SOURCE + ':game/project.godot').decode()
config = config.replace('[application]\n', '[application]\nconfig/use_custom_user_dir=true\nconfig/custom_user_dir_name=' + json.dumps(custom) + '\n', 1)
copies['project.godot'] = sha(config.encode())
check('only_declared_project_override', load('project-before-import.json') == copies)
check('declared_override_hash', overall['declared_project_override']['project_sha256'] == copies['project.godot'])
prepared, final = load('project-after-import.json'), load('project-final.json')
check('copied_bytes_unchanged_by_import', all(prepared.get(name) == digest for name, digest in copies.items()))
additions = {name: digest for name, digest in prepared.items() if name not in copies}
check('import_additions_inventory', load('import-additions.json') == additions)
uids = {name: digest for name, digest in additions.items() if name.endswith('.uid')}
check('only_cache_or_declared_script_uid_additions', all(name.startswith('.godot/') or (name.endswith('.gd.uid') and name[:-4] in copies) for name in additions))
check('retained_uid_manifest', load('retained-uids-final.json') == uids)
check('actual_uid_bytes_inventory', inventory(raw / 'generated-uids') == uids)
check('actual_uid_syntax', all(re.fullmatch(rb'uid://[a-z0-9]+\n?', (raw / 'generated-uids' / name).read_bytes()) for name in uids))
check('prepared_noncached_project_stable', {k:v for k,v in prepared.items() if not k.startswith('.godot/')} == {k:v for k,v in final.items() if not k.startswith('.godot/')})

expected_env = {'SIGHTBREAK_STATE_DIR': str(raw / 'private-state'),
                **{key:str(raw / 'private-state' / part) for key,part in
                   [('XDG_DATA_HOME','data'),('XDG_CONFIG_HOME','config'),('XDG_CACHE_HOME','cache'),('ANDROID_USER_HOME','android')]}}
check('private_environment', overall['private_environment'] == expected_env)
for label, key in [('before-input-mode', 'native_before'), ('after-input-mode', 'native_after')]:
    identity = load(label + '.json')
    check(label + ':sidecar_exactly_matches_embedded', identity == overall[key])
    check(label + ':project', Path(identity['project_path']).resolve() == raw / 'project')
    check(label + ':data', Path(identity['data_dir']).resolve() == raw / 'private-state/data')
    check(label + ':userdata', Path(identity['user_data_dir']).resolve() == raw / 'private-state/data' / custom)
    check(label + ':default_dummy', identity['driver'] == 'Dummy')
    check(label + ':custom', identity['uses_custom_user_dir'] is True and identity['custom_user_dir'] == custom)
check('native_initial_state_absent', overall['native_before']['profile_exists'] is False and overall['native_before']['diagnostics_exist'] is False)
check('identity_probe_retained_bytes', sha((raw / 'identity_probe.gd').read_bytes()) == overall['identity_probe_sha256'])

expected_commands = {
    'engine-version': ['--headless','--version'],
    'private-import': ['--path',str(raw/'project'),'--headless','--editor','--import','--quit'],
    'before-input-mode': ['--path',str(raw/'project'),'--headless','--script',str(raw/'identity_probe.gd'),'--','--receipt='+str(raw/'before-input-mode.json')],
    'input-mode': ['--path',str(raw/'project'),'--headless','--verbose','--script','res://tests/input_mode_test.gd','--','--audio-lifecycle-diagnostic'],
    'after-input-mode': ['--path',str(raw/'project'),'--headless','--script',str(raw/'identity_probe.gd'),'--','--receipt='+str(raw/'after-input-mode.json')],
}
caps = {'engine-version':30,'private-import':120,'before-input-mode':30,'input-mode':120,'after-input-mode':30}
check('five_ordered_phases', [p['label'] for p in overall['phases']] == list(expected_commands))
snapshots = {p['label']:p for p in load('final-phase-snapshots.json')}
seal = load('phase-seal.json')
sealchecks = {p['label']:p for p in seal['checks']}
check('phase_seal_complete', seal['sealed'] is True and not seal['errors'] and set(sealchecks) == set(expected_commands))
phases = []
for phase in overall['phases']:
    label = phase['label']
    check(label + ':command', phase['command'] == [overall['engine'], *expected_commands[label]])
    check(label + ':persisted_receipt', phase == load(label+'.receipt.json'))
    data = (raw / phase['log']).read_bytes()
    text = data.decode('utf-8',errors='replace')
    metadata = {'sha256':sha(data),'bytes':len(data),'clean_log':not failed(text)}
    snapshot = snapshots[label]
    check(label + ':raw_receipt', phase['log_sha256'] == metadata['sha256'] and phase['log_bytes'] == metadata['bytes'] and phase['clean_log'] == metadata['clean_log'])
    check(label + ':snapshot_metadata', all(snapshot[k] == v for k,v in metadata.items()) and snapshot['receipt_matches'] and snapshot['matches_phase_snapshot'])
    check(label + ':retained_log_bytes', (raw / snapshot['retained_log']).read_bytes() == data)
    check(label + ':receipt_hash', snapshot['phase_receipt_sha256'] == sha((raw/(label+'.receipt.json')).read_bytes()))
    check(label + ':sealed_metadata', sealchecks[label]['original_log'] == metadata and sealchecks[label]['retained_log'] == metadata and sealchecks[label]['receipt_sha256'] == snapshot['phase_receipt_sha256'])
    check(label + ':exit_and_caps', phase['exit'] == 0 and not phase['timed_out'] and 0 < phase['timeout_seconds'] <= caps[label] and phase['wall_seconds'] <= phase['timeout_seconds'] + 5)
    root = phase['root_identity']
    check(label + ':root_identity', root['pid'] == phase['pid'] == root['pgid'] == root['sid'] and root['start_ticks'] > 0)
    check(label + ':root_observed', any(p['pid'] == root['pid'] and p['start_ticks'] == root['start_ticks'] for p in phase['observed']))
    check(label + ':cleanup', phase['cleanup_complete'] is True and not phase['terminal_observed'] and not phase['terminal_session'] and not phase['terminal_group'] and phase['cleanup_wall_seconds'] <= 5)
    check(label + ':signals_bound_to_observed_identities', all(any(s['pid']==p['pid'] and s['start_ticks']==p['start_ticks'] for p in phase['observed']) for s in phase['signals']))
    phases.append({'label':label, **metadata, 'wall_seconds':phase['wall_seconds'], 'timeout_seconds':phase['timeout_seconds'], 'observed_count':len(phase['observed']), 'signals':phase['signals'], 'root':root,
                   'strict_lines':[line for line in text.splitlines() if re.search(r'^(?:SCRIPT ERROR|ERROR:)|Parse Error|ObjectDB.*leaked|Leaked instance|Orphan StringName',line)]})
check('version_output', (raw/'engine-version.log').read_text().strip() == '4.7.2.stable.official.ed1daf0bf')
check('whole_cap', overall['whole_cap_seconds'] == 240 and overall['whole_wall_seconds'] <= 240)

archive = inventory(raw/'produced-private-state')
for name in ('private-state-final.json','private-state-archive.json','private-state-after-copy.json'):
    check(name, load(name) == archive)
if (raw/'private-state-archive-seal.json').exists():
    archive_seal = load('private-state-archive-seal.json')
    check('private_archive_seal', archive_seal == {'archive':archive, 'source':archive, 'verified':True})
else:
    check('private_archive_seal_not_reached_after_integrity_failure', overall['acquisition_integrity'] is False and bool(overall['finalization_errors']))
check('actual_original_preservation', overall['private_project_removed'] is False and overall['private_state_removed'] is False and overall['originals_preserved_due_integrity_failure'] is True and (raw/'project').is_dir() and (raw/'private-state').is_dir())
check('actual_preserved_project_inventory', inventory(raw/'project') == final)
check('actual_preserved_state_inventory', inventory(raw/'private-state') == archive)
check('acquisition_acceptance_gate', overall['acquisition_completed'] is True and overall['acquisition_integrity'] is True and not overall['finalization_errors'] and not overall.get('error'), overall['finalization_errors'])
check('phase_seal_and_archive_flags', overall['phase_logs_sealed'] is True and overall['private_state_archive_verified'] is True)
check('historical_blocker_unresolved', overall['original_leak_blocker_resolved'] is False)

data = (raw/'input-mode.log').read_bytes()
text = data.decode('utf-8', errors='replace')
analysis = None
analyzer_error = None
try:
    analysis = analyze(text)
    analysis.update(raw_log_sha256=sha(data), raw_log_bytes=len(data))
except Exception as error:
    analyzer_error = {'type':type(error).__name__, 'message':str(error)}
check('analyzer_actual_bytes_accepted', analysis is not None, analyzer_error)
if analysis is not None:
    check('analyzer_actual_bytes_exact_output', analysis == load('analysis.json'))
else:
    check('no_analysis_file_after_rejection', not (raw/'analysis.json').exists())
    check('recorded_rejection_matches_replay', any(p['stage']=='final_analysis' and p['error']==analyzer_error['message'] for p in overall['finalization_errors']))
check('failed_overall_status_retained', overall['sample_strict_clean'] is False and overall['passed'] is False)
rows = [json.loads(line[len('AUDIO_LIFECYCLE '):]) for line in text.splitlines() if line.startswith('AUDIO_LIFECYCLE ')]
check('exact_headless_footer', re.findall(r'^INPUT_MODE_TEST checks=(\d+) failures=(\d+) graphical_pointer=(\w+) .* baseline=(\w+)$',text,re.M) == [('462','0','false','false')])
check('probe_schema_and_chronology', all(r['schema']==1 and all(type(r[k]) is int and r[k]>=0 for k in ('sequence','process_frame','physics_frame','usec')) for r in rows) and all(all(b[k]>=a[k] for k in ('process_frame','physics_frame','usec')) for a,b in zip(rows,rows[1:])))
check('actual_native_header_compatible_with_frozen_analyzer', type(rows[0]['mix_rate']) is int, rows[0])
check('strict_sample_no_orphan_stringnames', not re.search(r'^Orphan StringName:|^StringName: [1-9][0-9]* unclaimed string names at exit\.',text,re.M))
objects, snapshots_independent, pending, final_weak, player_rows = {}, [], [], {}, []
for index,row in enumerate(rows):
    check('sequence:'+str(index), row['sequence'] == index)
    if row['kind'] == 'object':
        identity = str(int(row['id']) % (1<<64))
        check('unique_registration:'+identity, identity not in objects)
        objects[identity] = row
    elif row['kind'] == 'player':
        player_rows.append(row)
    elif row['kind'] == 'weak':
        pending.append(row)
    elif row['kind'] == 'checkpoint':
        identities = [str(int(p['id']) % (1<<64)) for p in pending]
        check('weak_window:'+str(index), len(identities)==len(set(identities)) and all(p['stage']==row['stage'] for p in pending))
        if row['stage'] != 'existing_process_frame':
            check('forced_complete:'+str(index), set(identities)==set(objects))
            snapshots_independent.append({'stage':row['stage'],'sequence':index,'registered':len(objects),'alive':sum(p['alive'] for p in pending)})
        if row['stage']=='final_pre_quit':
            final_weak = {str(int(p['id']) % (1<<64)):p for p in pending}
        pending=[]
check('independent_15_forced_stages', [p['stage'] for p in snapshots_independent] == ['before_hud_leave','after_hud_leave']*6+['before_final_leave','after_final_leave','final_pre_quit'])
roles = collections.defaultdict(set)
for row in player_rows:
    roles[row['state']['owner']['role']].add(str(int(row['id'])%(1<<64)))
check('independent_exact_roles', {k:len(v) for k,v in roles.items()} == {'actor_shot':70,'actor_hurt':70,'reload_voice':280,'match_device':7})
leaks=[]
for cls,identity,refs in re.findall(r'^Leaked instance: (\w+):(\d+) - Reference count: (\d+)$', text,re.M):
    identity=str(int(identity)%(1<<64))
    registration=objects.get(identity)
    associations=[row for row in player_rows if identity in (row['state']['stream_id'],row['state']['latest_playback_id'])]
    check('independent_leak_join:'+identity, registration is None or registration['class']==cls)
    leaks.append({'class':cls,'id':identity,'references':int(refs),'registered':registration,
                  'player_observation_count':len(associations),'observed_roles':dict(collections.Counter(r['state']['owner']['role'] for r in associations)),
                  'last_player_observation':associations[-1] if associations else None,'final_weak':final_weak.get(identity)})
if analysis is not None:
    check('independent_leak_count', len(leaks)==len(analysis['leaks']))
final_census=collections.defaultdict(lambda:collections.Counter())
for identity,row in final_weak.items():
    final_census[objects[identity]['class']]['alive' if row['alive'] else 'dead']+=1
result={'source':SOURCE,'raw_directory':str(raw),'checks':checks,
        'check_count':len(checks),'failures':[p for p in checks if not p['passed']],
        'phases':phases,'whole_wall_seconds':overall['whole_wall_seconds'],
        'source_paths':len(manifest),'project_paths':len(copies),'uid_count':len(uids),
        'archive_file_count':len(archive),'archive':archive,'current_driver':rows[0]['driver'],
        'records':len(rows),'objects':len(objects),'record_kinds':dict(collections.Counter(p['kind'] for p in rows)),
        'registered_classes':dict(collections.Counter(p['class'] for p in objects.values())),
        'final_weak_census':{k:dict(v) for k,v in final_census.items()},
        'forced_snapshots':snapshots_independent,'roles':{k:len(v) for k,v in roles.items()},
        'frozen_scanner_failed':failed(text),'analyzer_error':analyzer_error,'header':rows[0],
        'orphan_stringname_lines':[line for line in text.splitlines() if line.startswith('Orphan StringName:')],
        'unclaimed_stringname_summaries':[line for line in text.splitlines() if re.fullmatch(r'StringName: \d+ unclaimed string names at exit\.',line)],
        'leaks':leaks,
        'raw_inventory':{str(p.relative_to(raw)):{'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size} for p in sorted(raw.rglob('*')) if p.is_file()}}
destination.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ('checks','raw_inventory','archive','phases','orphan_stringname_lines')},indent=2,sort_keys=True))
sys.exit(bool(result['failures']))
