#!/usr/bin/env python3
"""Package raw QA receipts below the connector's single-artifact download limit.

The original full QA artifact retains screenshots. This archive contains every
selected receipt without truncation and makes no gameplay-acceptance claim.
"""
import argparse
import hashlib
import json
from pathlib import Path
import tempfile
import zipfile


MAX_ARCHIVE_BYTES = 30 * 1024 * 1024
SUFFIXES = {'.json', '.jsonl', '.log'}
EXCLUDED = {'.git', '.godot', '__pycache__', 'node_modules', 'cache', '.cache'}


def selected(source):
    paths = []
    for path in sorted(source.rglob('*'), key=lambda item: item.relative_to(source).as_posix()):
        relative = path.relative_to(source)
        if any(part in EXCLUDED or part.endswith(('.app', '.framework', '.xcodeproj')) for part in relative.parts):
            continue
        if path.is_symlink():
            raise RuntimeError('Symlinked QA receipt rejected: ' + relative.as_posix())
        eligible = path.suffix.lower() in SUFFIXES or (relative.parts[0] == 'macos-diagnostics' and path.suffix.lower() == '.txt')
        if not eligible:
            continue
        if path.is_file():
            paths.append(path)
    return paths


def zip_info(name):
    info = zipfile.ZipInfo(name, (2026, 1, 1, 0, 0, 0))
    info.create_system = 3
    info.external_attr = 0o100644 << 16
    info.compress_type = zipfile.ZIP_STORED
    return info


def package(source, output, max_bytes=MAX_ARCHIVE_BYTES):
    source, output = Path(source).resolve(), Path(output).resolve()
    if not source.is_dir():
        raise RuntimeError('QA source directory does not exist')
    if output.is_relative_to(source):
        raise RuntimeError('Keep packaged QA output outside the evidence source')
    if output.exists():
        raise RuntimeError('Preserve existing packaged QA receipts; choose a fresh output')
    paths = selected(source)
    if not paths:
        raise RuntimeError('No QA receipts found; no evidence artifact was created')
    output.parent.mkdir(parents=True, exist_ok=True)
    index = {'schema': 1, 'scope': 'Raw QA receipts; screenshots remain in the full QA artifact. Packaging does not establish test acceptance.',
             'source_directory': str(source), 'max_archive_bytes': max_bytes,
             'excluded': ['screenshots', 'native payloads', 'archives', 'developer/import caches'], 'files': []}
    with tempfile.TemporaryDirectory(prefix='sightbreak-qa-receipts-', dir=output.parent) as temporary:
        archive = Path(temporary) / 'receipts.zip'
        with zipfile.ZipFile(archive, 'w') as bundle:
            raw_bytes = 0
            for path in paths:
                relative = path.relative_to(source).as_posix()
                entry = 'evidence/' + relative
                before = path.stat()
                digest = hashlib.sha256()
                size = 0
                with path.open('rb') as stream, bundle.open(zip_info(entry), 'w', force_zip64=True) as member:
                    while block := stream.read(1024 * 1024):
                        raw_bytes += len(block)
                        if raw_bytes > max_bytes:
                            raise RuntimeError('QA receipts exceed the download bound; full QA artifact remains required')
                        member.write(block)
                        digest.update(block)
                        size += len(block)
                after = path.stat()
                if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns) or size != after.st_size:
                    raise RuntimeError('QA receipt changed while packaging: ' + relative)
                index['files'].append({'path': relative, 'archive_path': entry, 'bytes': size, 'sha256': digest.hexdigest()})
            bundle.writestr(zip_info('qa-receipts-index.json'), json.dumps(index, indent=2, sort_keys=True).encode('utf-8') + b'\n')
        size = archive.stat().st_size
        if size > max_bytes:
            raise RuntimeError('QA receipts exceed the download bound; no partial artifact was published')
        digest = hashlib.sha256(archive.read_bytes()).hexdigest()
        archive.replace(output)
    return {'archive': str(output), 'bytes': size, 'sha256': digest, 'files': len(paths),
            'bound_bytes': max_bytes, 'scope': index['scope']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    arguments = parser.parse_args()
    print(json.dumps(package(arguments.source, arguments.output), indent=2))


if __name__ == '__main__':
    main()
