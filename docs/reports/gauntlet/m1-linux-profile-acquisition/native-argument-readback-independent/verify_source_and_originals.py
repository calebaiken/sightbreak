"""Independent finite source/original-byte audit; invokes only git and Python."""
import ast
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
BASE = 'ec6b34ce9af4db1199cd5266b2f7cfcc9831f5ef'
CANDIDATE = '93f32edf563c74e250a95505630d4b7870722c78'
ACTUAL_CRITIC = 'c9c5c64d96d2010e0905953423b01b83e04384c1'
BUILDER = ROOT / 'docs/reports/gauntlet/m1-linux-profile-acquisition/native-argument-readback-r1'
checks = 0


def check(value, message):
    global checks
    checks += 1
    if not value:
        raise AssertionError(message)


def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args])


def tree(commit):
    result = {}
    for record in git('ls-tree', '-rz', commit).split(b'\0'):
        if record:
            meta, name = record.split(b'\t', 1)
            mode, kind, oid = meta.decode().split()
            result[name.decode()] = {'mode': mode, 'kind': kind, 'git_oid': oid}
    return result


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def functions(raw):
    return {node.name: ast.dump(node, include_attributes=False)
            for node in ast.parse(raw).body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))}


check(os.sched_getaffinity(0) == {4}, 'Audit must use CPU4')
before, after = tree(BASE), tree(CANDIDATE)
nondoc_before = {k: v for k, v in before.items() if not k.startswith('docs/')}
nondoc_after = {k: v for k, v in after.items() if not k.startswith('docs/')}
changed = sorted(k for k in set(nondoc_before) | set(nondoc_after)
                 if nondoc_before.get(k) != nondoc_after.get(k))
allowed = sorted(['scripts/diagnostics/linux_profile_overhead.gd',
    'scripts/linux_profile_acquire.py', 'scripts/linux_profile_overhead.py',
    'scripts/test_linux_profile_acquire.py', 'scripts/test_linux_profile_overhead.py',
    'scripts/test_linux_profile_thread_readback.py'])
check(changed == allowed, 'Unexpected non-document changes')
existing_docs = {k: v for k, v in before.items() if k.startswith('docs/')}
for name, meta in existing_docs.items():
    check(meta == after.get(name), name + ' preserved earlier document/report/pin')
inventory = json.loads((BUILDER / 'base-nondoc-inventory.json').read_text())
check(inventory['commit'] == BASE, 'Wrong inventory baseline')
check(set(inventory['files']) == set(nondoc_before), 'Incomplete baseline inventory')
for name, meta in nondoc_before.items():
    raw = git('cat-file', 'blob', meta['git_oid'])
    wanted = inventory['files'][name]
    check(sha(raw) == wanted['sha256'] and len(raw) == wanted['bytes'], name + ' base inventory')
    check(meta['mode'] == wanted['mode'] and meta['git_oid'] == wanted['blob'], name + ' baseline mode/blob')
    if name not in changed:
        check(meta == nondoc_after[name], name + ' protected Git metadata')
        path = ROOT / name
        check(not path.is_symlink() and path.read_bytes() == raw, name + ' current physical bytes')
for name in changed:
    meta = nondoc_after[name]
    check(meta['mode'] == '100644', name + ' changed mode')
    check((ROOT / name).read_bytes() == git('cat-file', 'blob', meta['git_oid']), name + ' current candidate bytes')
for name in ('scripts/linux_profile_acquire.py', 'scripts/linux_profile_overhead.py'):
    old, new = git('show', BASE + ':' + name), git('show', CANDIDATE + ':' + name)
    funcs_old, funcs_new = functions(old), functions(new)
    delta = sorted(k for k in set(funcs_old) | set(funcs_new) if funcs_old.get(k) != funcs_new.get(k))
    check(delta == ([] if 'acquire' in name else ['validate_condition']), name + ' function delta')
for prefix in ('game/', 'backend/', 'server/', '.github/', '.claude/', 'tools/'):
    old = {k: v for k, v in before.items() if k.startswith(prefix)}
    new = {k: v for k, v in after.items() if k.startswith(prefix)}
    check(old == new, prefix + ' protected subtree')

registry_path = 'docs/reports/gauntlet/m1-linux-profile-acquisition/native-r3-independent/raw-registry.json'
registry_raw = git('show', ACTUAL_CRITIC + ':' + registry_path)
registry = json.loads(registry_raw)
builder_registry = json.loads((BUILDER / 'initial-raw-registry.json').read_text())
check(registry['files'] == builder_registry['files'], 'Builder raw inventory must match actual critic')
source = Path(registry['source'])
observed_paths = {str(p.relative_to(source)) for p in source.rglob('*') if p.is_file()}
check(observed_paths == set(registry['files']), 'Original raw file-set delta')
total = 0
for name, wanted in registry['files'].items():
    path = source / name
    check(not path.is_symlink(), name + ' original symlink')
    raw = path.read_bytes()
    total += len(raw)
    check({'bytes': len(raw), 'sha256': sha(raw)} == wanted, name + ' original bytes')
check(total == registry['bytes'] == builder_registry['bytes'], 'Raw byte total')
check(len(observed_paths) == registry['file_count'] == 370, 'Raw count')
outer = registry['outer']
for name, wanted in outer.items():
    aliases = {'wrapper.stdout': 'linux-profile-acquisition-r3-wrapper.stdout',
               'wrapper.stderr': 'linux-profile-acquisition-r3-wrapper.stderr',
               'outer-tool-receipt.json': 'linux-profile-acquisition-r3-outer-tool-receipt.json'}
    path = source.parents[1] / '.local' / aliases[name]
    check(path.is_absolute() and not path.is_symlink(), 'Outer identity path')
    raw = path.read_bytes()
    check({'bytes': len(raw), 'sha256': sha(raw)} == wanted, name + ' outer bytes')
check(git('-C', str(source.parents[1]), 'rev-parse', 'HEAD').decode().strip() == BASE, 'Original frozen source HEAD')
check(git('-C', str(source.parents[1]), 'status', '--porcelain').decode() == '', 'Original frozen source clean status')
for path in (ROOT / 'builds/linux-profile-acquisition-r4',
             Path('/workspace/sightbreak-linux-native-argument-readback/builds/linux-profile-acquisition-r4')):
    check(not path.exists() and not path.is_symlink(), 'Unreleased r4 output exists')
result = {'passed': True, 'utc': datetime.now(timezone.utc).isoformat(),
    'source_base': BASE, 'candidate': CANDIDATE, 'actual_critic': ACTUAL_CRITIC,
    'checks': checks, 'base_nondoc_count': len(nondoc_before),
    'candidate_nondoc_count': len(nondoc_after), 'changed_nondoc_paths': changed,
    'preserved_existing_document_paths': len(existing_docs),
    'unchanged_existing_nondoc_count': len(nondoc_before) - 5,
    'raw_file_count': len(observed_paths), 'raw_bytes': total,
    'raw_registry_sha256': sha(registry_raw), 'outer_records': len(outer),
    'source_clean': True, 'r4_absent': True, 'affinity': sorted(os.sched_getaffinity(0)),
    'scope': 'Finite Git/physical-source/original-byte checks only; zero native invocations.'}
(HERE / 'independent-source-and-originals.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
