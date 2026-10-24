"""Finite source and original-byte audit; Git/Python only, no engine launch."""
import ast
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
BASE = '93f32edf563c74e250a95505630d4b7870722c78'
SOURCE = '8da2add4279f3087320d4708c047f500baffd0ee'
ACTUAL = 'c9c5c64d96d2010e0905953423b01b83e04384c1'


def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args])


def tree(ref):
    result = {}
    for row in git('ls-tree', '-rz', ref).split(b'\0'):
        if row:
            meta, name = row.split(b'\t', 1)
            result[name.decode()] = meta.decode().split()
    return result


assert os.sched_getaffinity(0) == {4}
before, after = tree(BASE), tree(SOURCE)
changed = sorted(name for name in before.keys() | after.keys()
                 if not name.startswith('docs/') and before.get(name) != after.get(name))
assert changed == sorted(['scripts/linux_profile_overhead.py',
                         'scripts/linux_profile_acquire.py',
                         'scripts/test_linux_profile_thread_readback.py'])
for name, meta in before.items():
    if name.startswith('docs/'):
        assert after.get(name) == meta, name
for name, meta in after.items():
    if not name.startswith('docs/'):
        path = ROOT / name
        assert not path.is_symlink() and path.read_bytes() == git('cat-file', 'blob', meta[2]), name

old = git('show', BASE + ':scripts/linux_profile_overhead.py')
new = (ROOT / 'scripts/linux_profile_overhead.py').read_bytes()
guard = b'''        for key in ('caller_is_main_thread', 'caller_is_render_thread'):
            require(type(content.get('settings')) is dict
                    and content['settings'].get(key) is True
                    and content['settings'][key] is report['settings'][key],
                    'Invalid fingerprint thread readback: ' + key)
'''
assert new.count(guard) == 1 and new.replace(guard, b'') == old
old_pin, new_pin = hashlib.sha256(old).hexdigest(), hashlib.sha256(new).hexdigest()
supervisor = (ROOT / 'scripts/linux_profile_acquire.py').read_bytes()
assert supervisor.replace(new_pin.encode(), old_pin.encode()) == git('show', BASE + ':scripts/linux_profile_acquire.py')

def functions(raw):
    return {node.name: ast.dump(node, include_attributes=False)
            for node in ast.parse(raw).body if isinstance(node, (ast.FunctionDef, ast.ClassDef))}

a, b = functions(old), functions(new)
assert sorted(key for key in a.keys() | b.keys() if a.get(key) != b.get(key)) == ['validate_condition']
registry = json.loads(git('show', ACTUAL + ':docs/reports/gauntlet/m1-linux-profile-acquisition/native-r3-independent/raw-registry.json'))
raw_root = Path(registry['source'])
assert {str(path.relative_to(raw_root)) for path in raw_root.rglob('*') if path.is_file()} == set(registry['files'])
for name, wanted in registry['files'].items():
    path = raw_root / name
    assert not path.is_symlink(), name
    raw = path.read_bytes()
    assert len(raw) == wanted['bytes'] and hashlib.sha256(raw).hexdigest() == wanted['sha256'], name
outer = {}
for label, wanted in registry['outer'].items():
    # Registry keys are logical labels; the originals are outside the raw tree.
    path = raw_root.parent.parent / '.local' / ('linux-profile-acquisition-r3-' + label)
    raw = path.read_bytes()
    assert len(raw) == wanted['bytes'] and hashlib.sha256(raw).hexdigest() == wanted['sha256'], label
    outer[label] = str(path)
assert not (ROOT / 'builds/linux-profile-acquisition-r4').exists()
result = {'source': SOURCE, 'cpu_affinity': sorted(os.sched_getaffinity(0)),
          'changed_non_doc': changed, 'non_doc_count': sum(not name.startswith('docs/') for name in after),
          'all_materialized_non_doc_exact': True, 'prior_docs_unchanged': True,
          'controller_reverse_guard_exact': True, 'supervisor_only_pin_changed': True,
          'raw_file_count': len(registry['files']), 'raw_bytes': registry['bytes'],
          'outer_records': outer, 'r4_absent': True}
(HERE / 'resumed-source-and-preservation.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
