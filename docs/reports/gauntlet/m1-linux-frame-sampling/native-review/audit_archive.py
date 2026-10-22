"""Validate frozen retained bytes against their index and original runtime files."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--builder', type=Path, required=True)
    args = parser.parse_args()
    archive, builder = args.archive, args.builder
    runtime = builder / '.local/linux-frame-sampling/runtime-r1'
    index = json.loads((archive / 'payload-index.json').read_text())
    rows = []
    for item in index['files']:
        path = archive / item['path']
        if item['path'].startswith('export/'):
            original = builder / 'builds/linux' / item['path'].removeprefix('export/')
        elif item['path'].startswith('sources/'):
            name = Path(item['path']).name
            original = builder / ('game/scripts' if name.endswith('.gd') else 'scripts') / name
        else:
            original = runtime / item['path']
        rows.append(dict(path=item['path'], safe=path.resolve().is_relative_to(archive.resolve()) and not path.is_symlink(),
                         size_equal=path.stat().st_size == item['bytes'], hash_equal=digest(path) == item['sha256'],
                         original_bytes_equal=path.read_bytes() == original.read_bytes()))
    receipts = {name: json.loads((archive / (name + '-receipt.json')).read_text())
                for name in ('export-controller', 'source-fixture', 'native-controller')}
    stage_order = (receipts['export-controller']['finished_wall_unix_ns'] < receipts['source-fixture']['started_wall_unix_ns']
                   < receipts['source-fixture']['finished_wall_unix_ns'] < receipts['native-controller']['started_wall_unix_ns'])
    originals = {'offline_diagnostics.gd': 'game/scripts/offline_diagnostics.gd',
                 'verify_offline_match.py': 'scripts/verify_offline_match.py',
                 'linux_frame_sampler.py': 'scripts/linux_frame_sampler.py'}
    frozen_source_equal = all((archive / 'sources' / name).read_bytes() == subprocess.check_output(
        ['git', 'show', f'8afe0cc6b4c9051d3649a82bbcb4c8de8f947f9c:{path}'], cwd=builder) for name, path in originals.items())
    checks = dict(index_hash=digest(archive / 'payload-index.json') == '002a01a91b1da23733574c1f514adaa954bd2a75ff326eeab1ac657abe216463',
                  all_files_match=all(all(row[key] for key in ('safe', 'size_equal', 'hash_equal', 'original_bytes_equal')) for row in rows),
                  no_unindexed_files={path.relative_to(archive).as_posix() for path in archive.rglob('*') if path.is_file()} == {item['path'] for item in index['files']} | {'payload-index.json'},
                  actual_stage_order=stage_order, exact_frozen_source_copies=frozen_source_equal,
                  export_and_fixture_exit_zero=receipts['export-controller']['exit_code'] == receipts['source-fixture']['exit_code'] == 0,
                  original_native_failure_exit=receipts['native-controller']['exit_code'] == 1)
    output = dict(archive=str(archive), index_sha256=digest(archive / 'payload-index.json'), files=len(rows),
                  payload_bytes=sum(item['bytes'] for item in index['files']), rows=rows,
                  receipts=receipts, checks=checks, passed=all(checks.values()))
    print(json.dumps(output, indent=2))
    assert output['passed']


if __name__ == '__main__':
    main()
