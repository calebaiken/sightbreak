#!/usr/bin/env python3
"""Verify exact critic text and referenced builder evidence without extraction."""
import hashlib
import json
from pathlib import Path
import tarfile

HERE = Path(__file__).resolve().parent
data = json.loads((HERE / 'preservation.json').read_text())
for record in data['copied_exact_files']:
    payload = (HERE / record['path']).read_bytes()
    assert len(payload) == record['bytes'], record['path']
    assert hashlib.sha256(payload).hexdigest() == record['sha256'], record['path']
assert hashlib.sha256((HERE / 'review-manifest.json').read_bytes()).hexdigest() == data['original_review_manifest_sha256']
file_count = 0
for record in data['builder_archives']:
    archive = HERE / record['path']
    payload = archive.read_bytes()
    assert len(payload) == record['bytes'], record['path']
    assert hashlib.sha256(payload).hexdigest() == record['sha256'], record['path']
    manifest = json.loads((HERE / record['manifest']).read_text())
    assert manifest['archive_sha256'] == record['sha256']
    with tarfile.open(archive) as packet:
        for member in manifest['files']:
            content = packet.extractfile(member['path']).read()
            assert len(content) == member['bytes'], member['path']
            assert hashlib.sha256(content).hexdigest() == member['sha256'], member['path']
            file_count += 1
for record in data['referenced_negative_control_images']:
    with tarfile.open(HERE / record['archive']) as packet:
        payload = packet.extractfile(record['archive_member']).read()
    assert len(payload) == record['bytes'], record['archive_member']
    assert hashlib.sha256(payload).hexdigest() == record['sha256'], record['archive_member']
print(json.dumps({'passed': True, 'exact_critic_files': len(data['copied_exact_files']),
                  'builder_archives': len(data['builder_archives']), 'builder_files': file_count,
                  'referenced_negative_images': len(data['referenced_negative_control_images']),
                  'scope': 'Docs evidence preservation only; no new gameplay or native execution result'}, indent=2))
