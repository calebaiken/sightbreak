#!/usr/bin/env python3
"""Verify preserved critic evidence and its referenced existing Windows QA ZIP."""
import argparse
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import tarfile
import zipfile

HERE = Path(__file__).resolve().parent


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository-root', type=Path, default=HERE.parents[3])
    parser.add_argument('--extract', type=Path)
    args = parser.parse_args()
    manifest = json.loads((HERE/'MANIFEST.json').read_text())
    archive = HERE/manifest['archive']['path']
    assert archive.stat().st_size == manifest['archive']['bytes']
    assert digest(archive.read_bytes()) == manifest['archive']['sha256']
    expected = {r['path']:r for r in manifest['files']}
    assert len(expected) == manifest['archive']['regular_files']
    contents = {}
    with tarfile.open(archive, 'r:gz') as tar:
        members = tar.getmembers()
        assert len(members) == len(expected)
        for member in members:
            path = PurePosixPath(member.name)
            assert member.isfile() and not member.issym() and not member.islnk()
            assert not path.is_absolute() and '..' not in path.parts and '\\' not in member.name
            assert path.parts[0] in {'original','followup'}
            assert not any(p in {'.git','.godot','__pycache__','node_modules'} for p in path.parts)
            assert path.suffix.lower() not in {'.pyc','.exe','.dll','.so','.dylib','.pck','.png','.zip','.x86_64'}
            assert member.name not in contents
            record = expected[member.name]
            data = tar.extractfile(member).read()
            assert len(data) == member.size == record['bytes']
            assert digest(data) == record['sha256']
            contents[member.name] = data
    assert set(contents) == set(expected)
    omitted = {r['path']:r for r in manifest['omitted_local_derivatives_and_caches']}
    inventory_counts = {}
    for prefix in ('original','followup'):
        count = 0
        for line in contents[prefix+'/SHA256SUMS'].decode().splitlines():
            sha256, relative = line.split('  ',1)
            name = prefix+'/'+relative
            if name in contents:
                assert digest(contents[name]) == sha256
            else:
                assert omitted[name]['sha256'] == sha256
            count += 1
        inventory_counts[prefix] = count
    for archived, visible in [('original/REPORT.md','ORIGINAL_REVIEW.md'),
                              ('followup/REPORT.md','FOLLOWUP_REVIEW.md'),
                              ('original/qa-receipts/REPORT.md','PACKAGING_REVIEW.md')]:
        assert contents[archived] == (HERE/visible).read_bytes()

    before = json.loads(contents['original/cleanup-failure-observed.json'])
    after = json.loads(contents['followup/ORIGINAL_COUNTEREXAMPLE_RECHECK.json'])
    assert before['isolation_passed'] and before['isolation_failure'] is None and before['owned_namespace_remained']
    assert not after['followup_passed'] and after['followup_failure']['type'] == 'PermissionError'
    assert after['original_false_success_assertion_now_fails'] and after['review_teardown_removed_namespace']
    readback = json.loads(contents['followup/INDEPENDENT_READBACK.json'])
    assert len(readback['all-nine']['suites']) == 9
    assert readback['original_critic_files_immutable_verified'] == 340
    assert readback['preexisting_profiles_unchanged'] == 50

    reference = manifest['referenced_original_windows_qa']
    old_archive = args.repository_root/reference['repository_archive']
    assert digest(old_archive.read_bytes()) == reference['repository_archive_sha256']
    with tarfile.open(old_archive, 'r:gz') as tar:
        member = tar.getmember(reference['member'])
        assert member.isfile() and member.size == reference['member_bytes']
        windows_zip = tar.extractfile(member).read()
    assert digest(windows_zip) == reference['member_sha256']
    index = json.loads(contents['original/qa-receipts/RECONSTRUCTED_INDEX.json'])
    with zipfile.ZipFile(io.BytesIO(windows_zip)) as zip_source:
        for record in index['files']:
            data = zip_source.read(record['path'])
            assert len(data) == record['bytes'] and digest(data) == record['sha256']
        assert len(index['files']) == 91
    if args.extract:
        assert not args.extract.exists(), 'Choose a fresh extraction directory'
        args.extract.mkdir(parents=True)
        for name,data in contents.items():
            destination = args.extract/name
            destination.parent.mkdir(parents=True,exist_ok=True)
            destination.write_bytes(data)
    print(json.dumps({'archive_files_verified':len(contents),'inventory_files_verified':inventory_counts,
                      'original_rejection_preserved':True,'cleanup_followup_scoped_acceptance_preserved':True,
                      'referenced_windows_zip_sha256':reference['member_sha256'],
                      'selected_actual_windows_receipts_recomputed':len(index['files']),
                      'native_or_CI_rerun':False},indent=2))


if __name__ == '__main__':
    main()
