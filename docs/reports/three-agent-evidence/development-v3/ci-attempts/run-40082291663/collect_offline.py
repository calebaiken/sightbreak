"""Offline evidence inspection only; never imports or executes audited source/payloads."""
import hashlib
import json
import pathlib
import shutil
import subprocess
import zipfile
from collections import Counter

BASE = pathlib.Path(__file__).resolve().parent
COLLECTION = BASE.parent / 'sightbreak-v3-evidence' / 'ci-40082291663'
REPO = BASE.parent / 'sightbreak-v3'
COMMIT = '4099facb21a9242d41df79fd9e75bbbea031f2e0'
SOURCE_PATHS = ('game', 'scripts', 'backend', 'server', '.github', '.gitignore', 'README.md')
TEXT = {'.json', '.log', '.txt', '.csv', '.md', '.py', '.gd', '.sh', '.yml', '.yaml', '.tscn', '.tres', '.cfg', '.godot', '.pbxproj', '.plist', '.xcprivacy'}
errors = []
members = []
archives = []


def dump(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=True) + '\n', encoding='utf-8')


def safe(name):
    p = pathlib.PurePosixPath(name)
    if p.is_absolute() or '..' in p.parts or '\\' in name or ':' in name:
        raise ValueError('unsafe archive member ' + name)
    return p


def filehash(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def inspect(path, identity, depth=0):
    digest = filehash(path)
    info = {'identity': identity, 'path': str(path), 'bytes': path.stat().st_size, 'sha256': digest, 'depth': depth}
    print('Inspecting', identity, flush=True)
    with zipfile.ZipFile(path) as bundle:
        infos = bundle.infolist()
        duplicates = [n for n, count in Counter(i.filename for i in infos).items() if count > 1]
        if duplicates:
            errors.append({'archive': identity, 'duplicate_names': duplicates})
        info.update(members=len(infos), uncompressed_bytes=sum(i.file_size for i in infos), duplicates=duplicates)
        archives.append(info)
        for i, entry in enumerate(infos):
            safe(entry.filename)
            if entry.is_dir():
                members.append({'archive': identity, 'member': entry.filename, 'directory': True, 'bytes': 0, 'mode': oct(entry.external_attr >> 16)})
                continue
            p = pathlib.PurePosixPath(entry.filename)
            nest = p.suffix.lower() in {'.zip', '.apk'} and depth < 3
            retain = depth == 0 and (p.suffix.lower() in TEXT or p.suffix.lower() == '.wav' or
                                     (p.suffix.lower() == '.png' and entry.filename.startswith(('v3-export-network/', 'v3-export-offline/'))))
            output = None
            if retain:
                output = BASE / 'raw' / pathlib.PurePosixPath(identity) / p
            elif nest:
                output = BASE / 'spool' / (hashlib.sha256((identity + '!' + entry.filename).encode()).hexdigest() + p.suffix)
            if output:
                output.parent.mkdir(parents=True, exist_ok=True)
            h = hashlib.sha256()
            count = 0
            head = b''
            with bundle.open(entry) as stream:
                target = output.open('xb') if output else None
                try:
                    while chunk := stream.read(1024 * 1024):
                        if not head:
                            head = chunk[:64]
                        h.update(chunk)
                        count += len(chunk)
                        if target:
                            target.write(chunk)
                finally:
                    if target:
                        target.close()
            if count != entry.file_size:
                errors.append({'archive': identity, 'member': entry.filename, 'size_mismatch': count})
            row = {'archive': identity, 'member': entry.filename, 'bytes': count, 'compressed_bytes': entry.compress_size,
                   'sha256': h.hexdigest(), 'crc32': f'{entry.CRC:08x}', 'mode': oct(entry.external_attr >> 16),
                   'create_system': entry.create_system, 'compression': entry.compress_type, 'header_hex': head.hex()}
            if retain:
                row['raw_external'] = str(output.relative_to(BASE)).replace('\\', '/')
            members.append(row)
            if nest:
                inspect(output, identity + '!' + entry.filename, depth + 1)


def frozen_source():
    tree = subprocess.check_output(['git', 'ls-tree', '-rz', COMMIT, '--', *SOURCE_PATHS], cwd=REPO)
    entries = []
    for item in tree.split(b'\0'):
        if not item:
            continue
        prefix, name = item.split(b'\t', 1)
        mode, kind, oid = prefix.decode().split()
        entries.append((name.decode(), mode, kind, oid))
    entries.sort()
    manifest = []
    shipping = hashlib.sha256()
    validation = hashlib.sha256()
    process = subprocess.Popen(['git', 'cat-file', '--batch'], cwd=REPO, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    for name, mode, kind, oid in entries:
        process.stdin.write((oid + '\n').encode())
        process.stdin.flush()
        returned, typ, size = process.stdout.readline().decode().split()
        data = process.stdout.read(int(size))
        assert process.stdout.read(1) == b'\n'
        assert returned == oid and typ == kind == 'blob'
        sha = hashlib.sha256(data).hexdigest()
        encoded = b'symlink\0' + data if mode == '120000' else b'file\0' + bytes.fromhex(sha)
        validation.update(name.encode() + b'\0' + encoded + b'\0')
        rel = pathlib.PurePosixPath(name)
        if rel.parts[0] == 'game' and not {'tests', '.godot'}.intersection(rel.parts[1:]):
            shipping.update(rel.relative_to('game').as_posix().encode() + b'\0' + data + b'\0')
        manifest.append({'path': name, 'git_blob': oid, 'git_mode': mode, 'bytes': len(data), 'sha256': sha})
        if rel.suffix.lower() in TEXT or rel.name in {'.gitignore', 'README.md'}:
            dest = BASE / 'frozen-source' / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
    process.stdin.close()
    assert process.wait() == 0
    result = {'commit': COMMIT, 'game_tree': subprocess.check_output(['git', 'rev-parse', COMMIT + ':game'], cwd=REPO).decode().strip(),
              'source_paths': SOURCE_PATHS, 'source_files': len(entries), 'shipping_sha256': shipping.hexdigest(),
              'validation_sha256': validation.hexdigest(), 'files': manifest,
              'method': 'Read exact Git objects, no checkout/current staged files; independent implementation of frozen source hash algorithms.'}
    dump(BASE / 'source-manifest.json', result)
    print('Frozen source', {k: v for k, v in result.items() if k != 'files'}, flush=True)


if __name__ == '__main__':
    (BASE / 'metadata').mkdir(exist_ok=True)
    for path in COLLECTION.iterdir():
        if path.is_file() and path.suffix != '.zip':
            shutil.copyfile(path, BASE / 'metadata' / path.name)
    frozen_source()
    for path in sorted(COLLECTION.glob('*.zip')):
        inspect(path, path.name)
    dump(BASE / 'archive-index.json', archives)
    dump(BASE / 'member-index.json', members)
    dump(BASE / 'collection-inspection.json', {'errors': errors, 'archives': len(archives), 'members': len(members),
                                             'raw_files': sum('raw_external' in m for m in members)})
    print('Completed', len(archives), 'archives;', len(members), 'member observations; errors', errors, flush=True)
