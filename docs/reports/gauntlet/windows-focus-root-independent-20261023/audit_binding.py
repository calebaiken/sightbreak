"""Bind exact combined root to the accepted Windows and Mac source union."""
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys

OUT = Path(__file__).resolve().parent
OWN = OUT.parents[3]
CHECKOUT = Path('/workspace/reviews/windows-focus-root-a089-source')
FREEZE = 'a089473481ced0f2e7b2a7468bbc5d079f92f0ff'
WINDOWS = '691076fbe866ae798666e731c423ad4cc20fd876'
MAC = 'c08889b8c1118c89e83c151079df4dc224076760'
BASE = 'b2e0293a546961230afbd73e5cd2a1a307d69e94'
WORKFLOW = '.github/workflows/desktop-alpha.yml'
MAC_PATHS = {WORKFLOW, 'scripts/macos_ordinary_input.py', 'scripts/test_macos_ordinary_controller.py',
             'scripts/test_macos_ordinary_startup.py', 'scripts/verify_macos_ordinary.py'}
WINDOWS_PATHS = {'scripts/fixtures/offline_focus_observations.json', 'scripts/native_focus_fence.py',
    'scripts/test_focus_resume_timing.py', 'scripts/test_native_focus_fence.py',
    'scripts/validate.sh', 'scripts/verify_offline_export.py'}


def git(*args):
    return subprocess.check_output(['git', *args], cwd=OWN)


def inventory(commit):
    result = {}
    for row in git('ls-tree', '-r', '-z', commit, '--', 'scripts', '.github', 'game').split(b'\0'):
        if not row:
            continue
        metadata, path = row.split(b'\t', 1)
        mode, kind, digest = metadata.decode().split()
        assert kind == 'blob'
        result[path.decode()] = {'mode': mode, 'git_blob': digest}
    return result


def main():
    assertions = []
    def check(name, condition):
        assert condition, name
        assertions.append(name)
    inventories = {label: inventory(commit) for label, commit in (('base',BASE), ('windows',WINDOWS), ('mac',MAC), ('combined',FREEZE))}
    before, windows, mac, combined = (inventories[key] for key in ('base','windows','mac','combined'))
    windows_delta = {path for path in set(before) | set(windows) if before.get(path) != windows.get(path)}
    mac_delta = {path for path in set(before) | set(mac) if before.get(path) != mac.get(path)}
    check('exact six accepted Windows source delta paths', windows_delta == WINDOWS_PATHS)
    check('exact five accepted Mac code/workflow delta paths', mac_delta == MAC_PATHS)
    check('accepted component deltas are disjoint', not windows_delta & mac_delta)
    expected = dict(before)
    for path in windows_delta:
        expected[path] = windows[path]
    for path in mac_delta:
        expected[path] = mac[path]
    check('entire combined code/workflow/game inventory is exact accepted union', combined == expected)
    check('exact detached source HEAD', git('-C', str(CHECKOUT), 'rev-parse', 'HEAD').decode().strip() == FREEZE)
    check('exact detached source clean', git('-C', str(CHECKOUT), 'status', '--porcelain') == b'')
    sha256 = {}
    for path, entry in sorted(combined.items()):
        data = (CHECKOUT / path).read_bytes()
        blob_hash = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
        check('exact checkout Git blob ' + path, blob_hash == entry['git_blob'])
        sha256[path] = hashlib.sha256(data).hexdigest()
    game_trees = {label: git('rev-parse', commit + ':game').decode().strip()
                  for label, commit in (('base',BASE), ('windows',WINDOWS), ('mac',MAC), ('combined',FREEZE))}
    check('all game trees unchanged', len(set(game_trees.values())) == 1)
    text = (CHECKOUT / WORKFLOW).read_text()
    base_workflow = git('show', BASE + ':' + WORKFLOW).decode()
    added_after = '          python scripts/test_macos_ordinary_paths.py -v\n'
    check('workflow only adds accepted Mac startup pure command', text == base_workflow.replace(
        added_after, added_after + '          python scripts/test_macos_ordinary_startup.py -v\n'))
    blocks = re.split(r'(?=^      - )', text, flags=re.M)
    mac_block = next(block for block in blocks if 'python scripts/test_macos_ordinary_startup.py -v' in block)
    check('added workflow command remains Mac-only', "matrix.os == 'macos-15'" in mac_block)
    check('existing single Windows matrix selection preserved',
          "inputs.lane == 'windows' && '[{\"os\":\"windows-latest\",\"target\":\"windows\"}]'" in text)
    check('existing full workflow 60 minute limit preserved', '    timeout-minutes: 60\n' in text)
    required_stages = ['Packaging integrity controls', 'Atomic observation reader filesystem semantics',
        'Verify strict native menu captions', 'QA receipt packaging controls', 'Export exact clean source',
        'Native authority and compatibility regressions', 'Real exported keyboard and pointer input (Windows/Linux)',
        'Controlled delayed-capture reload comparison (Windows)', 'Retain original delayed-capture schedule (Windows diagnostic)',
        'Living-player offline input and settings restart (Windows/Linux)',
        'Real player plant and natural device resolution (Windows/Linux)',
        'Real player defuse after ordinary bot plant (Windows/Linux)',
        'Complete stock-rules offline match and earned training restart (Windows/Linux)',
        'Package bounded raw QA receipts', 'Preserve separately downloadable raw QA receipts']
    for name in required_stages:
        actual = next(block for block in blocks if block.startswith('      - name: ' + name + '\n'))
        original = next(block for block in re.split(r'(?=^      - )', base_workflow, flags=re.M)
                        if block.startswith('      - name: ' + name + '\n'))
        check('unchanged Windows workflow block ' + name, actual == original)
    # Check imports without importing any native frontend or starting processes.
    local = {path.stem: path for path in (CHECKOUT / 'scripts').glob('*.py')}
    entrypoints = ['verify_integration_export','verify_offline_export','verify_offline_match',
                   'run_native_regressions','export','verify_builds','build_manifest','package_qa_receipts']
    visited, pending = set(), list(entrypoints)
    while pending:
        name = pending.pop()
        if name in visited:
            continue
        visited.add(name)
        tree = ast.parse(local[name].read_bytes())
        for node in ast.walk(tree):
            candidates = []
            if isinstance(node, ast.Import):
                candidates = [alias.name.split('.')[0] for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                candidates = [node.module.split('.')[0]]
            pending.extend(item for item in candidates if item in local and item not in visited)
    check('Windows workflow entrypoint static imports exclude changed Mac ordinary modules',
          not {'macos_ordinary_input','verify_macos_ordinary'} & visited)
    # Build-manifest provenance function is read-only and does not export.
    sys.path.insert(0, str(CHECKOUT / 'scripts'))
    spec = importlib.util.spec_from_file_location('bound_build_manifest', CHECKOUT / 'scripts/build_manifest.py')
    manifest = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(manifest)
    identity = manifest.source()
    check('manifest binds exact clean source', identity['source_commit'] == FREEZE
          and not identity['source_dirty'] and not identity['source_game_dirty'])
    content = hashlib.sha256()
    for path in sorted(path for path in combined if path.startswith('game/')):
        relative = Path(path).relative_to('game')
        if 'tests' in relative.parts or '.godot' in relative.parts:
            continue
        content.update(relative.as_posix().encode() + b'\0' + (CHECKOUT / path).read_bytes() + b'\0')
    validation = hashlib.sha256()
    for directory in ('scripts','.github','game/tests'):
        for path in sorted(path for path in combined if path.startswith(directory + '/')):
            validation.update(path.encode() + b'\0' + (CHECKOUT / path).read_bytes() + b'\0')
    check('independent tracked-content provenance matches function', identity['source_content_sha256'] == content.hexdigest())
    check('independent tracked-validation provenance matches function', identity['source_validation_sha256'] == validation.hexdigest())
    check('unchanged original shipping content hash', identity['source_content_sha256'] == 'bcb872f6998ed8504c852dee354ab0acf5b6f19e58e40717267a1927e6d68a50')
    evidence_trees = []
    for accepted, path in (
        ('0d4f7e0', 'docs/reports/gauntlet/windows-focus-liveness-independent-20261023'),
        ('2203393', 'docs/reports/gauntlet/windows-focus-r2-independent-20261023'),
        (MAC, 'docs/reports/gauntlet/windows-combined-recovered-20261023')):
        original_tree = git('rev-parse', accepted + ':' + path).decode().strip()
        combined_tree = git('rev-parse', FREEZE + ':' + path).decode().strip()
        check('preserved exact evidence tree ' + path, original_tree == combined_tree)
        evidence_trees.append({'path': path, 'accepted_commit': accepted,
                               'original_tree': original_tree, 'combined_tree': combined_tree})
    receipt = {'source_freeze': FREEZE, 'accepted_windows_source': WINDOWS, 'accepted_mac_source': MAC,
        'scope': 'source binding and readiness for one full Windows workflow attempt; no dispatch or runtime acceptance',
        'assertion_count': len(assertions), 'assertions': assertions,
        'source_identity': identity, 'game_trees': game_trees,
        'windows_delta_paths': sorted(windows_delta), 'mac_delta_paths': sorted(mac_delta),
        'exact_source_union': True, 'tracked_code_files_bound': len(combined),
        'changed_source_sha256': {path: sha256[path] for path in sorted(windows_delta | mac_delta)},
        'workflow_sha256': sha256[WORKFLOW], 'unchanged_windows_workflow_blocks': required_stages,
        'preserved_evidence_trees': evidence_trees,
        'static_windows_local_import_closure': sorted(visited),
        'proposed_existing_workflow': WORKFLOW, 'proposed_input': {'lane':'windows'},
        'attempt_limit': 1, 'immutable_ref_must_resolve_to': FREEZE, 'dispatch_performed': False,
        'inventory': combined}
    (OUT / 'source-binding.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({key:value for key,value in receipt.items() if key not in ('assertions','inventory','static_windows_local_import_closure')}))


if __name__ == '__main__':
    main()
