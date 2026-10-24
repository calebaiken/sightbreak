#!/usr/bin/env python3
"""Read exact Git/source and old raw bytes; no engine, controller, or CI call."""
import datetime
import hashlib
import json
import pathlib
import subprocess

SOURCE = pathlib.Path('/workspace/sightbreak-windows-reopened-shutdown')
OUT = pathlib.Path(__file__).resolve().parent
VIEW = OUT.parents[3]
BASE = 'c32415148db1f110bbc7eadfca3793d4693429ff'
CANDIDATE = '7101350e5d0a2f6e4afb9a913b5b1bcf2107857a'
HANDOFF = 'a936ae967993a40b042f736fa0b64dca33c0aeb8'
ACCEPTANCE = '3d07b3eccf710ffe4ec3937c5a39021a70c7d043'
OLD = pathlib.Path('/workspace/reviews/windows-collector-actual-20261024/.local/windows40080238905/full/offline-input')

def git(*args):
    return subprocess.check_output(['git', *args], cwd=SOURCE)

def entries(ref):
    found = {}
    for row in git('ls-tree', '-rz', ref).split(b'\0'):
        if not row:
            continue
        meta, name = row.split(b'\t', 1)
        if name.startswith(b'docs/'):
            continue
        mode, kind, oid = meta.decode().split()
        assert kind == 'blob', (name, kind)
        found[name.decode()] = {'git_mode': mode, 'git_blob': oid}
    return found

assert set(__import__('os').sched_getaffinity(0)) == {4}
base, new = entries(BASE), entries(CANDIDATE)
assert len(base) == 507 and len(new) == 508
assert new == entries(HANDOFF) == entries(ACCEPTANCE)
paths = {}
for name, identity in sorted(new.items()):
    content = git('show', CANDIDATE + ':' + name)
    path = VIEW / name
    assert path.is_file() and not path.is_symlink(), name
    assert path.read_bytes() == content, name
    assert bool(path.stat().st_mode & 0o111) == (identity['git_mode'] == '100755'), name
    paths[name] = {**identity, 'bytes': len(content), 'sha256': hashlib.sha256(content).hexdigest()}
changed = [name for name in sorted(base.keys() | new.keys()) if base.get(name) != new.get(name)]
assert changed == ['.github/workflows/desktop-alpha.yml', 'scripts/test_reopened_shutdown_diagnostic.py', 'scripts/validate.sh', 'scripts/verify_offline_export.py']
game_tree = git('rev-parse', CANDIDATE + ':game').decode().strip()
assert game_tree == git('rev-parse', BASE + ':game').decode().strip()
content_digest = hashlib.sha256()
for name in sorted(paths):
    parts = pathlib.PurePosixPath(name).parts
    if parts[0] == 'game' and 'tests' not in parts and '.godot' not in parts:
        content_digest.update(name.removeprefix('game/').encode() + b'\0' + git('show', CANDIDATE + ':' + name) + b'\0')
validation_digest = hashlib.sha256()
for directory in ('scripts', '.github', 'game/tests'):
    for name in sorted(paths):
        if name.startswith(directory + '/'):
            validation_digest.update(name.encode() + b'\0' + git('show', CANDIDATE + ':' + name) + b'\0')
binding = {
    'created_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'scope': 'Git object and materialized builder-source binding only; no native output',
    'cpu_affinity': [4], 'base': BASE, 'candidate': CANDIDATE, 'handoff': HANDOFF,
    'source_acceptance': ACCEPTANCE, 'source_acceptance_preregistration': '1285a98464059104dbd551fb5055b81ae194ba7b',
    'builder_head': git('rev-parse','HEAD').decode().strip(),
    'builder_status': git('status','--porcelain','--untracked-files=all').decode(),
    'source_game_tree': game_tree, 'source_content_sha256': content_digest.hexdigest(),
    'source_validation_sha256': validation_digest.hexdigest(),
    'base_source_paths': len(base), 'candidate_source_paths': len(paths),
    'handoff_and_acceptance_source_equal': True, 'all_candidate_materialized_bytes_and_modes_equal': True, 'materialized_binding_view': str(VIEW), 'builder_sparse_missing_paths': [name for name in paths if not (SOURCE/name).is_file()],
    'changed_source_paths': changed, 'paths': paths,
    'source_workflows': {name: value for name,value in paths.items() if name.startswith('.github/workflows/')},
    'engine_expected': '4.7.2.stable.official.ed1daf0bf',
    'no_engine_was_run': True,
}
(OUT/'SOURCE_BINDINGS.json').write_text(json.dumps(binding,indent=2)+'\n')
old_files = {}
for path in sorted(OLD.rglob('*')):
    if path.is_file():
        old_files[path.relative_to(OLD).as_posix()] = {'bytes': path.stat().st_size, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
old_result = json.loads((OLD/'results.json').read_text())
old_commands = json.loads((OLD/'commands.json').read_text())
assert old_result['passed'] is False
assert old_result['error'] == 'Reopened export failed clean shutdown'
assert old_result['initial_exit'] == 0 and old_result['reopened_exit'] == 0
assert old_result['cleanup_errors'] == []
assert len(old_commands) == 2 and [x['name'] for x in old_commands] == ['client','reopened']
assert all('--verbose' not in x['command'] for x in old_commands)
old = {
    'scope': 'Old counterpart anchors only; parent critic owns full original actual review',
    'run_id': 40080238905, 'job_id': 120832097220, 'attempt': 1, 'source_commit': BASE,
    'official_raw_directory': str(OLD), 'files': old_files, 'commands': old_commands,
    'result_anchors': {k:old_result[k] for k in ('passed','error','initial_exit','reopened_exit','cleanup_errors','elapsed_seconds','source','engine','controller_command')},
    'warning_lines': {name: [dict(line_number=index, raw_text=line) for index,line in enumerate((OLD/name).read_text().splitlines(),1) if any(term in line for term in ('WARNING','ObjectDB','Leaked instance','ResourceCache','Orphan StringName'))] for name in ('client.log','reopened.log')},
    'identities_and_owners_remain_unknown': True,
}
(OUT/'ORIGINAL_COUNTERPART.json').write_text(json.dumps(old,indent=2)+'\n')
print(json.dumps({'source_paths':len(paths),'old_raw_files':len(old_files),'game_tree':game_tree,'source_content_sha256':content_digest.hexdigest(),'source_validation_sha256':validation_digest.hexdigest(),'source_and_old_raw_bytes_verified':True}))
