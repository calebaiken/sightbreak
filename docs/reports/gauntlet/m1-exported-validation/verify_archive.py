#!/usr/bin/env python3
"""Check preserved bytes and references only; never execute game/test controllers."""
from pathlib import Path, PurePosixPath
import gzip
import hashlib
import json
import tarfile

ROOT = Path(__file__).resolve().parent


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    manifest = json.loads((ROOT / 'manifest.json').read_text())
    archive = ROOT / manifest['archive']
    assert archive.stat().st_size == manifest['compressed_bytes'] < manifest['max_compressed_bytes'] < 100_000_000
    assert digest(archive.read_bytes()) == manifest['archive_sha256']
    expected = {row['path']: row for row in manifest['files']}
    files = {}
    with tarfile.open(archive) as bundle:
        members = bundle.getmembers()
        assert len(members) == len(expected) == manifest['file_count']
        assert [row.name for row in members] == sorted(expected)
        for member in members:
            path = PurePosixPath(member.name)
            assert not path.is_absolute() and '..' not in path.parts and member.isfile()
            assert not any(part in path.parts for part in ('cache', 'shader_cache', '__pycache__', '.godot', '.venv'))
            assert path.suffix.lower() not in ('.x86_64', '.tpz', '.zip', '.pem', '.key', '.p12', '.pfx', '.keystore', '.pyc')
            data = bundle.extractfile(member).read()
            assert not data.startswith((b'\x7fELF', b'MZ'))
            assert b'-----BEGIN PRIVATE KEY-----' not in data and b'-----BEGIN RSA PRIVATE KEY-----' not in data
            assert len(data) == expected[member.name]['bytes'] and digest(data) == expected[member.name]['sha256']
            files[member.name] = data
    assert sum(map(len, files.values())) == manifest['payload_bytes'] < manifest['max_payload_bytes']
    references = json.loads((ROOT / 'baseline-references.json').read_text())
    baseline = (ROOT / references['references'][0]['repository_archive']).resolve()
    assert digest(baseline.read_bytes()) == references['existing_baseline_archive_sha256']
    external = {}
    with tarfile.open(baseline) as bundle:
        for row in references['references']:
            data = bundle.extractfile(row['archive_member']).read()
            assert len(data) == row['bytes'] and digest(data) == row['sha256']
            external[row['original_path']] = data
    original = json.loads(files['root/builds/mission-m1/critic-native/MANIFEST.json'])
    for row in original['files']:
        data = files.get('root/' + row['path'], external.get(row['path']))
        assert data is not None and len(data) == row['bytes'] and digest(data) == row['sha256']
    assert len(original['files']) == 346 and len(external) == 10
    counts = {}
    for name, expected_count in [('plant-candidate-r1', 61), ('plant-candidate-r2', 188), ('defuse-candidate-r1', 169)]:
        content = gzip.decompress(files['root/builds/mission-m1/' + name + '-status.jsonl.gz'])
        rows = [json.loads(line) for line in content.splitlines()]
        assert len(rows) == expected_count
        for row in rows:
            raw = row['raw'].encode('utf-8')
            assert digest(raw) == row['sha256']
            json.loads(raw)
        counts[name] = len(rows)
    for outside, inside in [('independent-review.md', 'native-independent-review.md'), ('native-critic-brief.txt', 'native-critic-brief.txt'), ('helper-source-review.md', 'critic-helper-source/source-review.md'), ('source.json', 'candidate-build/linux/source.json'), ('catalog-fixture-check.txt', 'catalog-fixture-check.txt')]:
        assert (ROOT / outside).read_bytes() == files['root/builds/mission-m1/' + inside]
    exclusions = json.loads((ROOT / 'exclusions.json').read_text())
    for row in exclusions['synthetic_profiles_retained']:
        profile = json.loads(files['root/' + row['path']])
        assert profile['scope'] == 'offline_training' and profile['matches'] == profile['credits'] == profile['xp'] == 0 and profile['history'] == []
    receipt = json.loads((ROOT / 'source.json').read_text())
    assert receipt['source_commit'] == manifest['source_under_review']
    assert receipt['source_dirty'] is False and receipt['source_game_dirty'] is False
    assert next(row for row in exclusions['excluded_artifacts'] if row['path'].endswith('sightbreak.x86_64'))['sha256'] == receipt['artifact']['sha256']
    return {'purpose': 'Preservation integrity only; no gameplay execution or new acceptance', 'archive_sha256': manifest['archive_sha256'], 'members_verified': len(files), 'original_critic_manifest_entries_verified': len(original['files']), 'external_baseline_members_verified': len(external), 'raw_snapshot_hashes_verified': counts, 'raw_snapshot_total': sum(counts.values()), 'png_files': sum(name.endswith('.png') for name in files), 'tsv_files': sum(name.endswith('.tsv') for name in files), 'mp4_files': sum(name.endswith('.mp4') for name in files), 'synthetic_profiles_checked': len(exclusions['synthetic_profiles_retained']), 'verbatim_report_copies_match': True, 'outer_checksums': 'Run sha256sum -c sha256.txt separately; the saved verification report is included in those hashes.'}


if __name__ == '__main__':
    print(json.dumps(main(), indent=2) + '\n', end='')
