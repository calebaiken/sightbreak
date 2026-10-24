#!/usr/bin/env python3
"""Preserve every finalized raw file and exact root outer receipt; never delete raw."""
import hashlib
import json
from pathlib import Path
import tarfile

HERE = Path(__file__).resolve().parent
RAW = Path('/workspace/sightbreak-collector-preflight-c324/builds/collector-native-preflight-c324-20261024')
audit = json.loads((HERE / 'actual-audit.json').read_text())


def sha(data):
    return hashlib.sha256(data).hexdigest()


expected = audit['raw_inventory']
files = {str(path.relative_to(RAW)): path for path in sorted(RAW.rglob('*')) if path.is_file()}
assert files.keys() == expected.keys()
for name, path in files.items():
    assert {'bytes': path.stat().st_size, 'sha256': sha(path.read_bytes())} == expected[name]
archive = HERE / 'actual-raw-and-outer.tar.gz'
with archive.open('xb') as stream, tarfile.open(fileobj=stream, mode='w:gz') as bundle:
    for name, path in files.items():
        bundle.add(path, arcname='raw/' + name, recursive=False)
    bundle.add(HERE / 'outer-tool-receipt.json', arcname='outer-tool-receipt.json', recursive=False)
members = {}
with tarfile.open(archive, 'r:gz') as bundle:
    for member in bundle.getmembers():
        assert member.isfile() and member.name not in members
        data = bundle.extractfile(member).read()
        members[member.name] = {'bytes': len(data), 'sha256': sha(data)}
archive_expected = {'raw/' + name: identity for name, identity in expected.items()}
outer = (HERE / 'outer-tool-receipt.json').read_bytes()
archive_expected['outer-tool-receipt.json'] = {'bytes': len(outer), 'sha256': sha(outer)}
assert members == archive_expected
for name, path in files.items():
    assert {'bytes': path.stat().st_size, 'sha256': sha(path.read_bytes())} == expected[name]
receipt = {'passed': True, 'archive': archive.name, 'bytes': archive.stat().st_size,
           'sha256': sha(archive.read_bytes()), 'raw_files': len(expected),
           'raw_bytes': sum(value['bytes'] for value in expected.values()),
           'archive_members': len(members), 'members': members,
           'original_raw_unchanged': True, 'original_raw_path': str(RAW)}
(HERE / 'archive-manifest.json').write_text(json.dumps(receipt, indent=2, sort_keys=True) + '\n')
print(json.dumps({key: receipt[key] for key in ('passed', 'archive', 'bytes', 'sha256', 'raw_files', 'archive_members', 'original_raw_unchanged')}))
