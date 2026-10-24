"""Extract retained official QA ZIPs without links, duplicates or traversal."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import stat
import zipfile

parser = argparse.ArgumentParser()
parser.add_argument('archive', type=Path)
parser.add_argument('destination', type=Path)
parser.add_argument('--sha256', required=True)
arguments = parser.parse_args()
actual = hashlib.sha256(arguments.archive.read_bytes()).hexdigest()
if actual != arguments.sha256:
    raise RuntimeError('Official artifact digest mismatch')
if arguments.destination.exists():
    raise RuntimeError('Use a fresh extraction directory')
with zipfile.ZipFile(arguments.archive) as archive:
    names = set()
    total = 0
    for entry in archive.infolist():
        path = PurePosixPath(entry.filename)
        mode = entry.external_attr >> 16
        canonical=path.as_posix()
        if (canonical in names or path.is_absolute() or '..' in path.parts
                or '\\' in entry.filename or not path.parts
                or stat.S_ISLNK(mode) or (mode and stat.S_IFMT(mode) not in (0, stat.S_IFREG, stat.S_IFDIR))):
            raise RuntimeError('Unsafe or duplicate archive member: ' + entry.filename)
        names.add(canonical)
        total += entry.file_size
        if total > 250 * 1024 * 1024:
            raise RuntimeError('QA extraction exceeded the declared 250 MiB expansion guard')
    arguments.destination.mkdir(parents=True)
    archive.extractall(arguments.destination)
print(json.dumps({'archive': str(arguments.archive), 'sha256': actual, 'entries': len(names),
                  'expanded_bytes': total, 'destination': str(arguments.destination)}))
