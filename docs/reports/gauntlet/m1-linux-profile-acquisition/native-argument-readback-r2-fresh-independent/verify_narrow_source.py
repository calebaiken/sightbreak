"""Finite source and original-byte checks; only Git and Python, CPU4."""
import ast
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
BASE = '93f32edf563c74e250a95505630d4b7870722c78'
CANDIDATE = '8da2add4279f3087320d4708c047f500baffd0ee'
ORIGINAL = 'a8cf0d06386a49a4aba05fc30a0a4e83ed9aab4a'
ACTUAL = 'c9c5c64d96d2010e0905953423b01b83e04384c1'
REPORT = 'docs/reports/gauntlet/m1-linux-profile-acquisition/'
checks = 0


def check(value, message):
    global checks
    checks += 1
    if not value:
        raise AssertionError(message)


def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args])


def tree(ref):
    rows = {}
    for record in git('ls-tree', '-rz', ref).split(b'\0'):
        if record:
            meta, name = record.split(b'\t', 1)
            rows[name.decode()] = meta.decode()
    return rows


def blob(ref, path):
    return git('show', ref + ':' + path)


def descriptor(raw):
    return {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def functions(raw):
    return {node.name: ast.dump(node, include_attributes=False)
            for node in ast.walk(ast.parse(raw))
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}


check(os.sched_getaffinity(0) == {4}, 'CPU4 required')
before, after = tree(BASE), tree(CANDIDATE)
changed = sorted(path for path in set(before) | set(after)
                 if not path.startswith('docs/') and before.get(path) != after.get(path))
allowed = ['scripts/linux_profile_acquire.py', 'scripts/linux_profile_overhead.py',
           'scripts/test_linux_profile_thread_readback.py']
check(changed == allowed, 'Only three existing non-document paths may differ')
for path in before:
    if path not in changed:
        check(before[path] == after.get(path), path + ' preserved mode/type/blob')
for path in changed:
    check(before[path].split()[:2] == after[path].split()[:2] == ['100644', 'blob'], path + ' mode/type')
    check((ROOT / path).read_bytes() == blob(CANDIDATE, path), path + ' checked-out source')

guard = b'''        for key in ('caller_is_main_thread', 'caller_is_render_thread'):
            require(type(content.get('settings')) is dict
                    and content['settings'].get(key) is True
                    and content['settings'][key] is report['settings'][key],
                    'Invalid fingerprint thread readback: ' + key)
'''
path = 'scripts/linux_profile_overhead.py'
old, new = blob(BASE, path), blob(CANDIDATE, path)
check(new.count(guard) == 1 and new.replace(guard, b'') == old, 'Exact five-line validator correction')
old_hash, new_hash = descriptor(old)['sha256'], descriptor(new)['sha256']
path = 'scripts/linux_profile_acquire.py'
check(blob(CANDIDATE, path).replace(new_hash.encode(), old_hash.encode()) == blob(BASE, path),
      'Supervisor changes only the controller source pin')
for path, expected in [('scripts/linux_profile_acquire.py', []),
                       ('scripts/linux_profile_overhead.py', ['validate_condition']),
                       ('scripts/test_linux_profile_thread_readback.py', ['test_effective_readbacks_require_both_true_booleans'])]:
    old_functions, new_functions = functions(blob(BASE, path)), functions(blob(CANDIDATE, path))
    delta = sorted(key for key in set(old_functions) | set(new_functions)
                   if old_functions.get(key) != new_functions.get(key))
    check(delta == expected, path + ' function delta')
check(subprocess.run(['git', '-C', str(ROOT), 'merge-base', '--is-ancestor', '602980d7', CANDIDATE]).returncode == 0,
      'Builder preregistration precedes correction')

original_tree = tree(ORIGINAL)
original_prefix = REPORT + 'native-argument-readback-independent/'
retained_prefix = REPORT + 'native-argument-readback-r2/retained-rejection/'
original_paths = [path for path in original_tree if path.startswith(original_prefix)]
for path in original_paths:
    retained = retained_prefix + path[len(original_prefix):]
    check(original_tree[path] == after.get(retained), retained + ' original report preservation')
rig = original_prefix + 'test_independent_controls.py'
check((ROOT / rig).read_bytes() == blob(ORIGINAL, rig), 'Unchanged ten-method rig at correct relative depth')

registry_raw = blob(ACTUAL, REPORT + 'native-r3-independent/raw-registry.json')
registry = json.loads(registry_raw)
source = Path(registry['source'])
actual_names = {str(path.relative_to(source)) for path in source.rglob('*') if path.is_file()}
check(actual_names == set(registry['files']), 'Original R3 file set')
for name, expected in registry['files'].items():
    path = source / name
    check(not path.is_symlink() and descriptor(path.read_bytes()) == expected, name + ' raw identity')
check(len(actual_names) == registry['file_count'] == 370, 'Original R3 raw count')
check(sum(row['bytes'] for row in registry['files'].values()) == registry['bytes'] == 276747038, 'Original raw byte total')
aliases = {'wrapper.stdout': 'linux-profile-acquisition-r3-wrapper.stdout',
           'wrapper.stderr': 'linux-profile-acquisition-r3-wrapper.stderr',
           'outer-tool-receipt.json': 'linux-profile-acquisition-r3-outer-tool-receipt.json'}
for name, expected in registry['outer'].items():
    path = source.parents[1] / '.local' / aliases[name]
    check(not path.is_symlink() and descriptor(path.read_bytes()) == expected, name + ' original outer identity')

archive_path = REPORT + 'native-r3-independent/retained-actual.tar.gz'
archive_raw = blob(ACTUAL, archive_path)
check(descriptor(archive_raw) == {'bytes': 58661240,
      'sha256': 'b3868bc6659e22cdf03ef2111c60e9e5d2c290552bc51ecddda57dcda19d0025'}, 'Original R3 archive bytes')
archive_manifest = json.loads(blob(ACTUAL, REPORT + 'native-r3-independent/archive-members.json'))
with tarfile.open(fileobj=io.BytesIO(archive_raw), mode='r:gz') as archive:
    members = archive.getmembers()
    check(len(members) == 377, 'Original R3 archive member count')
    archive_files = {}
    for member in members:
        if member.isfile():
            archive_files[member.name] = descriptor(archive.extractfile(member).read())
    # Retained manifest binds every file, not filesystem ownership or tar timestamps.
    manifest_files = archive_manifest['members']
    check(archive_files == manifest_files, 'Original R3 archive file identities')
for path in (ROOT / 'builds/linux-profile-acquisition-r4',
             Path('/workspace/sightbreak-linux-native-argument-readback/builds/linux-profile-acquisition-r4')):
    check(not path.exists() and not path.is_symlink(), 'R4 remains absent')
result = {'passed': True, 'utc': datetime.now(timezone.utc).isoformat(), 'checks': checks,
          'base': BASE, 'candidate': CANDIDATE, 'affinity': sorted(os.sched_getaffinity(0)),
          'changed_nondoc_paths': changed, 'preserved_existing_nondoc_paths':
          sum(not path.startswith('docs/') for path in before) - len(changed),
          'preserved_existing_docs': sum(path.startswith('docs/') for path in before),
          'original_critic_paths': len(original_paths), 'original_rig': descriptor(blob(ORIGINAL, rig)),
          'r3_original_files': 370, 'r3_original_bytes': registry['bytes'], 'outer_records': len(aliases),
          'archive': descriptor(archive_raw), 'archive_members': len(members), 'r4_absent': True,
          'scope': 'Git union, changed checked-out source, and original-byte audit; no native execution.'}
(HERE / 'narrow-source-and-originals.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
