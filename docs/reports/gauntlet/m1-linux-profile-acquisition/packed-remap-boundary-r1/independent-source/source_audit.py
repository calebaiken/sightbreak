#!/usr/bin/env python3
"""Independent complete Git union and immutable failure-packet comparisons."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[6]
REPORT = Path(__file__).resolve().parent
OLD = '216d39ada8f9d11e2d8544d01fde42da49607b14'
NEW = 'ec6b34ce9af4db1199cd5266b2f7cfcc9831f5ef'
CODE = '7965320db8fbac4598eeb86fc191e589d08b61de'
COMPONENT = 'docs/reports/gauntlet/m1-linux-profile-acquisition/packed-remap-boundary-r1/'


def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args])


def tree(revision):
    result = {}
    for row in git('ls-tree', '-rz', revision).split(b'\0'):
        if row:
            mode, kind, rest = row.split(b' ', 2)
            blob, name = rest.split(b'\t', 1)
            result[name.decode()] = {'mode': mode.decode(), 'kind': kind.decode(), 'blob': blob.decode()}
    return result


def raw(revision, path):
    return git('show', revision + ':' + path)


def identity(value):
    return {'bytes': len(value), 'sha256': hashlib.sha256(value).hexdigest()}


old, new, code = tree(OLD), tree(NEW), tree(CODE)
union = sorted(set(old) | set(new))
changed = [name for name in union if old.get(name) != new.get(name)]
non_doc = [name for name in union if not name.startswith('docs/')]
delta = [name for name in non_doc if old.get(name) != new.get(name)]
assert delta == ['scripts/linux_profile_acquire.py', 'scripts/linux_profile_payload.py',
                 'scripts/test_linux_profile_acquire.py', 'scripts/test_linux_profile_acquire_remaps.py']
assert all(name in delta or name.startswith(COMPONENT) for name in changed)
assert all(new[name] == code[name] for name in new if not name.startswith('docs/'))
for revision in ('2e486554', CODE):
    subprocess.run(['git', '-C', str(ROOT), 'merge-base', '--is-ancestor', revision, NEW], check=True)

acquire = raw(NEW, delta[0])
assert acquire.count(b"builds/linux-profile-acquisition-r3") == 1
assert acquire.replace(b'builds/linux-profile-acquisition-r3', b'builds/linux-profile-acquisition-r2') == raw(OLD, delta[0])
fixture = raw(NEW, delta[2])
assert fixture.count(b'false\\n}\\n\\0\',') == 1
assert fixture.replace(b'false\\n}\\n\\0\',', b'false\\n}\\n\',') == raw(OLD, delta[2])

old_payload = raw(OLD, delta[1]).decode()
new_payload = raw(NEW, delta[1]).decode()
def nodes(text):
    return {node.name: ast.dump(node, include_attributes=False)
            for node in ast.parse(text).body if isinstance(node, (ast.FunctionDef, ast.ClassDef))}
before, after = nodes(old_payload), nodes(new_payload)
assert [name for name in before if before[name] != after[name]] == ['sections', 'inspect']
assert set(after) - set(before) == {'packed_import_sections'}
assert old_payload[old_payload.index('def inspect('):].replace(
    'sections(path.read_text())', "sections(original_bytes.decode('utf-8'))").replace(
    'sections(resources[name].decode())', 'packed_import_sections(resources[name])') == new_payload[new_payload.index('def inspect('):]

packet = 'docs/reports/gauntlet/m1-linux-profile-acquisition/native-r2-independent/'
fixture_dir = COMPONENT + 'fixtures/'
provenance = []
for name in ('packed-assets-icon.svg.import', 'staged-assets-icon.svg.import'):
    independent = raw('eec4c7e1', packet + 'failure-input/' + name)
    candidate = raw(NEW, fixture_dir + name)
    assert independent == candidate
    provenance.append({'path': name, 'independent_packet': 'eec4c7e1', **identity(independent)})
original_reader = raw(OLD, 'scripts/linux_profile_payload.py')
assert original_reader == raw(NEW, fixture_dir + 'reader-216d39a.py')
provenance.append({'path': 'reader-216d39a.py', 'original_source': OLD, **identity(original_reader)})
readback_raw = raw('eec4c7e1', packet + 'payload-failure-readback.json')
assert readback_raw == raw(NEW, fixture_dir + 'payload-failure-readback.json')
readback = json.loads(readback_raw)
packed_raw = raw(NEW, fixture_dir + 'packed-assets-icon.svg.import')
entry = next(row for row in readback['resources'] if row['path'] == 'assets/icon.svg.import')
assert all(entry[key] == value for key, value in identity(packed_raw).items())
assert hashlib.md5(packed_raw).hexdigest() == entry['md5']
provenance.append({'path': 'payload-failure-readback.json', 'packet_source': 'eec4c7e1', **identity(readback_raw)})

depth = ROOT / '.local/depth-one'
fixture_commit = subprocess.check_output(['git', '-C', str(depth), 'rev-parse', 'HEAD']).decode().strip()
assert fixture_commit == NEW
assert subprocess.check_output(['git', '-C', str(depth), 'rev-list', '--count', 'HEAD']).strip() == b'1'
assert subprocess.check_output(['git', '-C', str(depth), 'rev-parse', '--is-shallow-repository']).strip() == b'true'
assert subprocess.check_output(['git', '-C', str(depth), 'status', '--porcelain']) == b''
absent = {}
for revision in (OLD, CODE, '2e486554'):
    probe = subprocess.run(['git', '-C', str(depth), 'cat-file', '-e', revision + '^{commit}'],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert probe.returncode != 0
    absent[revision] = {'commit_object_absent': True, 'expected_negative_returncode': probe.returncode}
# The complete Git tree matches exactly, including paths omitted by sparsity.
assert subprocess.check_output(['git', '-C', str(depth), 'ls-tree', '-rz', 'HEAD']) == git('ls-tree', '-rz', NEW)
for name in ('scripts/linux_profile_acquire.py', 'scripts/linux_profile_payload.py',
             'scripts/test_linux_profile_acquire.py', 'scripts/test_linux_profile_acquire_remaps.py'):
    assert (depth / name).read_bytes() == raw(NEW, name)

inventory = [{'path': name, 'original': old.get(name), 'candidate': new.get(name),
              'changed': old.get(name) != new.get(name)} for name in non_doc]
(REPORT / 'complete-source-union.json').write_text(json.dumps(inventory, indent=2) + '\n')
result = {'passed': True, 'original': OLD, 'candidate': NEW, 'implementation': CODE,
          'preregistration': '2e486554', 'union_all_tracked_paths': len(union),
          'union_non_doc_paths': len(non_doc), 'unchanged_non_doc_paths': len(non_doc)-len(delta),
          'changed_non_doc_paths': delta, 'all_changes_outside_delta_inside_component_report': True,
          'candidate_source_equals_implementation': True,
          'supervisor_exact_after_only_r3_to_r2_reversal': True,
          'synthetic_fixture_exact_after_only_terminal_NUL_reversal': True,
          'payload_AST_changed_functions': ['sections', 'inspect'],
          'payload_AST_added_functions': ['packed_import_sections'],
          'inspect_exact_after_only_two_read_boundary_replacements': True,
          'immutable_failure_packet_provenance': provenance,
          'original_artifact_not_reinspected_or_continued': True,
          'depth_one': {'root': str(depth), 'HEAD': fixture_commit, 'reachable_commits': 1,
                        'shallow': True, 'clean': True, 'complete_tree_equals_candidate': True,
                        'historical_object_negative_probes': absent}}
(REPORT / 'source-audit.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
