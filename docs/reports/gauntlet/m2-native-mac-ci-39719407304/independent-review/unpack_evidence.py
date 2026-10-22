#!/usr/bin/env python3
"""Restore retained connector ZIPs to fresh local audit directories."""
import hashlib
import json
from pathlib import Path
import zipfile


def unpack(archive, output):
    with zipfile.ZipFile(archive) as bundle:
        for entry in bundle.infolist():
            path = Path(entry.filename)
            if path.is_absolute() or '..' in path.parts or (entry.external_attr >> 16) & 0o170000 == 0o120000:
                raise RuntimeError('Unsafe archive entry: ' + entry.filename)
        bundle.extractall(output)


def main():
    base = Path(__file__).resolve().parent
    metadata = json.loads((base / 'ARTIFACTS.json').read_text())
    for record in metadata['archives']:
        archive = base / record['path']
        if archive.stat().st_size != record['bytes'] or hashlib.sha256(archive.read_bytes()).hexdigest() != record['sha256']:
            raise RuntimeError('Archive digest mismatch: ' + str(archive))
        host = archive.name.split('-')[0]
        output = base / (host + ('-receipts' if '-receipts-' in archive.name else '-qa'))
        if output.exists():
            raise RuntimeError('Keep existing evidence; choose a fresh checkout: ' + str(output))
        output.mkdir()
        unpack(archive, output)
        for nested in output.glob('*.zip'):
            unpack(nested, output)
        print(output)


if __name__ == '__main__':
    main()
