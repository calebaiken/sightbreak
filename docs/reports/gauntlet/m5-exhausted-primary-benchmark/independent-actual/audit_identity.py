#!/usr/bin/env python3
"""Read-only independent verification of frozen source and single-attempt receipts."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

FREEZE = 'b87afb717bf09a78c6d36b164d48906902734bdb'
FIXTURE = '540d24dda8e58f4685030e81b55ac3778ccbf31a89f76f9873ac598c32770731'
ENGINE = '8d106cbe6144c2dc7e881d61d2429c1a8a76e6b22ef48bd5e48dcf934953f71e'


def audit(raw, repo):
    checks = 0
    def check(value, message):
        nonlocal checks
        checks += 1
        if not value:
            raise AssertionError(message)
    def sha(data):
        return hashlib.sha256(data).hexdigest()
    def read(name):
        return json.loads((raw / name).read_text())
    def git(*args):
        return subprocess.check_output(['git', *args], cwd=repo)
    overall = read('overall.receipt.json')
    before, after = read('original-tracked-before.json'), read('original-tracked-after.json')
    check(before == after, 'entire original before/after manifest differs')
    tree = {}
    for entry in git('ls-tree', '-r', '-z', FREEZE).split(b'\0'):
        if entry:
            meta, path = entry.split(b'\t', 1)
            mode, typ, blob = meta.decode().split()
            tree[path.decode()] = (mode, typ, blob)
    check(len(before) == len(tree) == 8933, 'full tree count')
    check(len({x['path'] for x in before}) == len(before), 'duplicate original entry')
    present = 0
    for entry in before:
        rel = entry['path']
        mode, typ, blob = tree[rel]
        check((entry['mode'], entry['git_blob'], entry['index_stage']) == (mode, blob, '0'), rel + ' tree metadata')
        if entry['present']:
            present += 1
            data = git('cat-file', 'blob', blob)
            check((sha(data), len(data)) == (entry['sha256'], entry['bytes']), rel + ' original/Git hash')
            check((repo / rel).read_bytes() == data, rel + ' original current bytes')
    copied = read('project-source-copy-map.json')
    stage = Path(overall['staged_project'])
    check(len(copied) == 324, 'game copy count')
    check({x['path'] for x in copied} == {x for x in tree if x.startswith('game/')}, 'all tracked game copies')
    stage_before, stage_import, stage_after = [read(n) for n in ('staged-before-import.json', 'staged-after-import.json', 'staged-after-attempt.json')]
    check(stage_import == stage_after, 'stage changed after baseline')
    stage_maps = [{x['path']: x for x in m} for m in (stage_before, stage_import, stage_after)]
    for entry in copied:
        rel = entry['path']
        data = git('cat-file', 'blob', tree[rel][2])
        expected = {'path': rel, 'bytes': len(data), 'sha256': sha(data)}
        for smap in stage_maps:
            check(smap[rel] == expected, rel + ' stage manifest')
        check((stage / rel).read_bytes() == data, rel + ' staged current bytes')
        check((Path(entry['original']), Path(entry['staged'])) == (repo / rel, stage / rel), rel + ' copy paths')
        check(entry['sha256'] == sha(data) and entry['bytes'] == len(data) and entry['git_blob'] == tree[rel][2], rel + ' copy receipt')
    added = read('preparation-added-files.json')
    check(len(added) == 63, 'import added count')
    check({x['path'] for x in added} == stage_maps[1].keys() - stage_maps[0].keys(), 'exact import additions')
    uid_path = 'game/tests/bot_exhausted_primary_probe.gd.uid'
    check(all(x['path'].startswith('game/.godot/') or x['path'] == uid_path for x in added), 'unexpected import additions')
    check(len([x for x in added if x['path'] == uid_path]) == 1, 'generated diagnostic UID')
    for entry in stage_after:
        data = (stage / entry['path']).read_bytes()
        check((sha(data), len(data)) == (entry['sha256'], entry['bytes']), entry['path'] + ' current stage digest')
    uid = (raw / 'preparation-generated-uids' / uid_path).read_bytes()
    check(uid == (stage / uid_path).read_bytes(), 'retained generated UID differs')
    check(sha((stage / 'game/tests/bot_exhausted_primary_probe.gd').read_bytes()) == FIXTURE, 'fixture SHA')
    check(sha(Path(overall['engine']).read_bytes()) == ENGINE == overall['engine_sha256'] == overall['engine_sha256_after'], 'engine SHA')
    check(sha((raw / 'run_once.py').read_bytes()) == overall['controller_sha256'], 'controller SHA')
    check(overall['source_freeze'] == overall['source_head_before'] == overall['source_head_after'] == FREEZE, 'freeze receipt')
    check(overall['source_status_before'] == overall['source_status_after'] == '', 'dirty recorded source')
    check(overall['recognized_godot_before'] == overall['recognized_godot_after'] == [], 'recognized engine overlap')
    check(overall['tracked_project_changes_after_import'] == overall['tracked_project_changes_after_attempt'] == [], 'recorded game changes')
    phases = []
    for key, pid, start in [('preparation',34219,971492), ('baseline',34468,972148)]:
        phase = overall[key]
        check(phase == read(phase['name'] + '.receipt.json'), key + ' receipt mismatch')
        check(phase['pid'] == pid and phase['root_identity']['start_ticks'] == start, key + ' identity')
        check(phase['root_identity']['pgid'] == phase['root_identity']['sid'] == pid, key + ' session')
        check(phase['root_identity']['exe'] == overall['engine'], key + ' executable')
        check(phase['exit_code'] == 0 and phase['timed_out'] is False and phase['wall_seconds'] < 120, key + ' completion')
        check(all(phase[x] == [] for x in ('terminal_same_session','terminal_observed_live','terminal_recognized_godot','signals','error_lines')), key + ' scoped cleanup/errors')
        check(phase['cleanup_wall_seconds'] < 5, key + ' cleanup bound')
        check(phase['cwd'] == str(stage), key + ' cwd')
        suffix = ['--editor', '--path', str(stage / 'game'), '--import'] if key == 'preparation' else ['--path', str(stage / 'game'), '--script', 'res://tests/bot_exhausted_primary_probe.gd']
        check(phase['command'] == [overall['engine'], '--headless'] + suffix, key + ' exact command')
        state = Path(overall['private_state'])
        env = phase['private_environment']
        expected_env = {'SIGHTBREAK_STATE_DIR': str(state), 'XDG_DATA_HOME': str(state / 'data'), 'XDG_CONFIG_HOME': str(state / 'config'), 'XDG_CACHE_HOME': str(state / 'cache'), 'ANDROID_USER_HOME': str(state / 'android')}
        check(env == expected_env and state.is_relative_to(raw), key + ' private paths')
        for stream in ('stdout','stderr'):
            data = (raw / phase[stream]).read_bytes()
            check((sha(data),len(data)) == (phase[stream + '_sha256'], phase[stream + '_bytes']), key + ' ' + stream + ' digest')
        phases.append({k:phase[k] for k in ('name','pid','start_utc','end_utc','wall_seconds','command','root_identity','exit_code','signals','terminal_observed_live')})
    check(overall['whole_wrapper_wall_seconds'] < 240, 'wrapper cap')
    warning = (raw / 'baseline-probe.stderr.log').read_text()
    check(warning == 'WARNING: 2 ObjectDB instances were leaked at exit (run with `--verbose` for details).\n   at: cleanup (core/object/object.cpp:2536)\n', 'warning original bytes')
    return {'identity_checks': checks, 'source_freeze': FREEZE, 'full_tracked_entries': len(tree), 'present_original_files_verified_against_git': present, 'copied_game_files':len(copied), 'import_additions':len(added), 'generated_uid_bytes':uid.decode(), 'phases':phases, 'wrapper_wall_seconds':overall['whole_wrapper_wall_seconds'], 'strict_native_verdict':'REJECT', 'original_stderr':warning, 'cleanup_limit':overall['cleanup_scope_limit']}


if __name__ == '__main__':
    print(json.dumps(audit(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()), indent=2, sort_keys=True))
