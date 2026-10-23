"""Read-only source/export/profile/graphics/iOS cross-check of original artifacts."""
import argparse
import hashlib
import json
from pathlib import Path
import re
from PIL import Image

read = lambda path: json.loads(path.read_text())
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()


def audit(base, expected):
    full, receipts = base / 'full-qa', base / 'receipts/evidence'
    keys = ('source_commit', 'source_game_tree', 'source_content_sha256', 'source_validation_sha256')
    identity = lambda d: all(d.get(k) == expected[k] for k in keys) and d.get('source_dirty') is False and d.get('source_game_dirty') is False
    files = {p.relative_to(full).as_posix(): p for p in full.rglob('*') if p.is_file()}
    selected = {p.relative_to(receipts).as_posix(): p for p in receipts.rglob('*') if p.is_file()}
    shared = files.keys() & selected.keys()
    result = {'full_QA_files': len(files), 'selected_receipt_files': len(selected),
              'common_files': len(shared),
              'shared_file_mismatches': [name for name in shared if files[name].read_bytes() != selected[name].read_bytes()],
              'full_only_files': sorted(files.keys() - selected.keys()),
              'receipts_only_files': sorted(selected.keys() - files.keys()), 'native_inventories': {}, 'PNGs': []}
    for name in ('macos-input-preflight', 'macos-menu-input'):
        data = read(full / name / 'results.json')
        before, after = data['native_user_directory_before'], data['native_user_directory_after']
        result['native_inventories'][name] = {
            'source_matches': identity(data['source']), 'artifact_source_matches': identity(data['artifact_source']),
            'before_files': len(before['files']), 'after_files': len(after['files']),
            'before_directories': len(before['directories']), 'after_directories': len(after['directories']),
            'exact_inventory_unchanged': before == after, 'profiles_after': data['profile_entries_after'],
            'profiles_unchanged': data['profile_entries_unchanged'], 'source_unchanged': data['source_unchanged'],
            'executable_sha256': data['executable_sha256'], 'source_bound_executable_sha256': data['artifact_source']['artifact']['sha256']}
    for path in full.rglob('*.png'):
        image = Image.open(path)
        image.verify()
        result['PNGs'].append({'path': path.relative_to(full).as_posix(), 'bytes': path.stat().st_size,
                               'sha256': sha(path), 'dimensions': Image.open(path).size})
    diagnostic = read(full / 'macos-diagnostics/results.json')
    result['diagnostic_source_matches'] = identity(diagnostic['source'])
    result['diagnostic_trials'] = [
        {'label': item['label'], 'passed': item['passed'], 'exit': item['native_exit_code'],
         'timed_out': item['timed_out'], 'owned_groups_gone': item['surviving_owned_group'] == [] and item['owned_group_after_native_exit'] == [],
         'PNG_hash_matches': sha(full / 'macos-diagnostics' / (item['label'] + '.png')) == item['capture']['sha256']}
        for item in diagnostic['trials']]
    compile_root = full / 'ios-compile'
    compiled, exported = read(compile_root / 'compile.json'), read(compile_root / 'exported-source.json')
    before, after = read(compile_root / 'source-before.log'), read(compile_root / 'source-after.log')
    xcode = (compile_root / 'xcodebuild-device.log').read_text()
    pck = next(item for item in exported['payload'] if item['path'].endswith('/sightbreak.pck'))
    result['iOS'] = {
        'status': compiled['status'], 'scope': compiled['scope'], 'compile_completed': compiled['compile_completed'],
        'all_source_snapshots_match': all(identity(d) for d in (compiled['source'], exported, before, after)),
        'before_after_snapshots_identical': before == after,
        'xcode_version': compiled['xcode_version'], 'iphoneos_sdk_version': compiled['iphoneos_sdk_version'],
        'generic_device_command': next(item for item in compiled['commands'] if item['label'] == 'xcodebuild-device'),
        'raw_build_actions': {name: len(re.findall('^' + name + r'\b', xcode, re.M)) for name in ('CompileC', 'SwiftCompile', 'Ld', 'CodeSign')},
        'BUILD_SUCCEEDED_in_raw_log': '** BUILD SUCCEEDED **' in xcode,
        'command_count': len(compiled['commands']),
        'all_cleanup_complete': all(item['cleanup_complete'] and item['cleanup_errors'] == [] and item['surviving_owned_processes'] == [] for item in compiled['commands']),
        'unexpected_command_exits': [item for item in compiled['commands'] if item['exit_code'] != (1 if item['label'] == 'unsigned-app' else 0)],
        'codesign_raw_log': (compile_root / 'unsigned-app.log').read_text(),
        'app_descriptor': compiled['app'], 'exported_pck_descriptor': pck,
        'app_PCK_matches_export_descriptor': compiled['app']['pck_sha256'] == pck['sha256'],
        'warnings': [line for line in xcode.splitlines() if 'warning:' in line],
        'binary_limit': 'No executable or PCK binary bytes transferred; descriptors are native receipts.'}
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('evidence', type=Path)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.evidence, read(args.source))
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'full_files': result['full_QA_files'], 'receipt_files': result['selected_receipt_files'],
                      'shared_mismatches': result['shared_file_mismatches'], 'PNG_count': len(result['PNGs']),
                      'iOS_status': result['iOS']['status'], 'iOS_source_matches': result['iOS']['all_source_snapshots_match']}))
