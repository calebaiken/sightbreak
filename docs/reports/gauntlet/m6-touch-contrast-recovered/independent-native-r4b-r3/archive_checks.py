#!/usr/bin/env python3
"""Verify every original member and part without extracting or changing raw."""
import datetime
import hashlib
import json
from pathlib import Path
import tarfile
import time

OUT = Path(__file__).resolve().parent
RAW = Path('/workspace/sightbreak-touch-contrast-native-recovered-r4b-r3')
REPORT = Path('/workspace/sightbreak-touch-contrast-recovered/docs/reports/gauntlet/m6-touch-contrast-recovered/native-r4b-r3')
started = time.monotonic()


def digest(path):
    value = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(chunk)
    return value.hexdigest()


manifest_data = (REPORT / 'payload-manifest.json').read_bytes()
manifest = json.loads(manifest_data)
archive_receipt = json.loads((REPORT / 'ARCHIVE.json').read_text())
assert hashlib.sha256(manifest_data).hexdigest() == archive_receipt['payload_manifest_sha256']
entries = {row['path']: row for row in manifest['files']}
assert len(entries) == len(manifest['files']) == manifest['file_count']
actual_paths = {str(path.relative_to(RAW)) for path in RAW.rglob('*') if path.is_file()}
assert actual_paths == set(entries)
for name, row in entries.items():
    assert (RAW / name).stat().st_size == row['bytes'] and digest(RAW / name) == row['sha256'], name
assert sum(row['bytes'] for row in entries.values()) == manifest['raw_bytes']
assert sum(name.endswith('.png') for name in entries) == manifest['png_count'] == 5648
end = json.loads((RAW / 'lane-end.json').read_text())
assert manifest['acquisition_complete'] is end['acquisition_complete'] is True
assert manifest['acquisition_error'] is end['error'] is None
assert manifest['source_freeze'] == '108d1cdc6cf471daa7390298c234bb1c087ae865'
archive = Path(archive_receipt['archive_local_path'])
assert archive == RAW.with_suffix('.tar.xz')
assert archive.stat().st_size == archive_receipt['archive_bytes']
assert digest(archive) == archive_receipt['archive_sha256']
reassembled = hashlib.sha256()
part_bytes = 0
for index, part in enumerate(archive_receipt['parts']):
    assert part['path'] == 'evidence.tar.xz.part-%03d' % index
    path = REPORT / part['path']
    data = path.read_bytes()
    assert len(data) == part['bytes'] <= 24 * 1024 * 1024
    assert hashlib.sha256(data).hexdigest() == part['sha256']
    reassembled.update(data)
    part_bytes += len(data)
assert part_bytes == archive_receipt['archive_bytes']
assert reassembled.hexdigest() == archive_receipt['archive_sha256']
seen = set()
with tarfile.open(archive, 'r:xz') as bundle:
    for member in bundle:
        assert member.isfile() and member.name not in seen
        seen.add(member.name)
        stream = bundle.extractfile(member)
        value = hashlib.sha256()
        count = 0
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            count += len(chunk)
            value.update(chunk)
        if member.name == 'payload-manifest.json':
            assert count == member.size == len(manifest_data)
            assert value.hexdigest() == hashlib.sha256(manifest_data).hexdigest()
        else:
            assert member.name.startswith('raw/')
            row = entries[member.name[4:]]
            assert count == member.size == row['bytes'] and value.hexdigest() == row['sha256'], member.name
assert seen == {'payload-manifest.json'} | {'raw/' + name for name in entries}
assert len(seen) == archive_receipt['members'] == len(entries) + 1
result = {'kind': 'INDEPENDENT_IMMUTABLE_ARCHIVE_AUDIT', 'time_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'raw_files': len(entries), 'raw_bytes': manifest['raw_bytes'], 'pngs': manifest['png_count'], 'archive_members': len(seen), 'archive_bytes': archive_receipt['archive_bytes'], 'archive_sha256': archive_receipt['archive_sha256'], 'parts': len(archive_receipt['parts']), 'every_original_raw_path_size_hash': True, 'every_unique_archive_member_size_hash': True, 'embedded_manifest_exact': True, 'every_part_hash_size_and_ordered_reassembly': True, 'acquisition_complete_recorded': True, 'acquisition_error_recorded': None, 'source_freeze': manifest['source_freeze'], 'original_quality_failures_preserved': True, 'full_descendant_cleanup_not_established_by_archive': True, 'raw_mutations': [], 'wall_seconds': time.monotonic() - started}
(OUT / 'archive-checks.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result))
