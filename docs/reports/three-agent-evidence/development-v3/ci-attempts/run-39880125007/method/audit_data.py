"""Independent offline verification and text/media-only evidence selection."""
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import wave
import zipfile

from inspect import EVIDENCE, FROZEN, OUT, REPO, ENV, git, sha, write, dump

def log_failed(text):
    return bool(re.search(r'^(?:SCRIPT ERROR|ERROR:)|Parse Error|ObjectDB.*leaked|Leaked instance', text, re.M))

def blob_map():
    entries = []
    for line in git('ls-tree', '-rz', '--full-tree', FROZEN).split(b'\0'):
        if not line:
            continue
        metadata, name = line.split(b'\t', 1)
        mode, kind, oid = metadata.decode().split()
        path = name.decode()
        if path.split('/')[0] in ('game', 'scripts', 'backend', 'server', '.github', '.gitignore', 'README.md'):
            entries.append((path, mode, oid))
    entries.sort()
    result = subprocess.check_output(['git', 'cat-file', '--batch'], input=b''.join((e[2]+'\n').encode() for e in entries), cwd=REPO, env=ENV)
    offset, blobs, rows = 0, {}, []
    content_hash = hashlib.sha256()
    runtime_hash = hashlib.sha256()
    for path, mode, oid in entries:
        end = result.index(b'\n', offset)
        got_oid, kind, size = result[offset:end].split()
        data = result[end+1:end+1+int(size)]
        assert got_oid.decode() == oid and kind == b'blob'
        assert sha(data) and len(data) == int(size)
        offset = end+2+int(size)
        blobs[path] = data
        content = b'symlink\0'+data if mode == '120000' else b'file\0'+hashlib.sha256(data).digest()
        content_hash.update(path.encode()+b'\0'+content+b'\0')
        is_runtime = path.startswith('game/') and not any(part in ('tests', '.godot') for part in PurePosixPath(path).parts[1:])
        if is_runtime:
            runtime_hash.update(path[5:].encode()+b'\0'+data+b'\0')
        rows.append({'path': path, 'mode': mode, 'git_blob': oid, 'bytes': len(data), 'sha256': sha(data), 'runtime_hash_input': is_runtime})
    assert offset == len(result)
    identity = {'commit': FROZEN, 'game_tree': git('rev-parse', FROZEN+':game').decode().strip(),
                'content_sha256': content_hash.hexdigest(), 'source_files': len(entries),
                'runtime_content_sha256': runtime_hash.hexdigest(),
                'method': 'Independent reimplementation of frozen godot_process.py:166-195 and build_manifest.py:24-36 using Git object bytes, without checking out or importing project code.'}
    dump('source-object-audit.json', {'identity': identity, 'files': rows})
    for name in ('game/tests/reload_audio_capture.gd', 'game/tests/network_simulation_probe.gd',
                 'game/scripts/gameplay/reload_audio.gd', 'game/scripts/gameplay/actor.gd',
                 'game/scripts/gameplay/reload_phases.gd'):
        write('frozen/'+name, blobs[name])
    return blobs, identity

def archive_audit():
    collection = json.loads((EVIDENCE/'COLLECTION.json').read_bytes())
    expected = {str(a['id']): a for a in collection['artifacts']}
    archives, receipts = {}, []
    for path in sorted(EVIDENCE.glob('*.zip')):
        with path.open('rb') as stream:
            digest = hashlib.file_digest(stream, 'sha256').hexdigest()
        aid = path.stem.removeprefix('artifact-')
        rows = []
        with zipfile.ZipFile(path) as z:
            names = z.namelist()
            assert len(names) == len(set(names))
            for item in z.infolist():
                h = hashlib.sha256()
                with z.open(item) as stream:
                    while chunk := stream.read(1024*1024):
                        h.update(chunk)
                rows.append({'member': item.filename, 'bytes': item.file_size, 'sha256': h.hexdigest(),
                             'mode': oct(item.external_attr >> 16), 'crc32': f'{item.CRC:08x}'})
            if aid in expected:
                exp = expected[aid]
                assert digest == exp['sha256'] == exp['published_digest'].removeprefix('sha256:')
                assert path.stat().st_size == exp['bytes'] and len(rows) == exp['members']
                index = json.loads((EVIDENCE/(path.stem+'-receipts')/'receipt-index.json').read_bytes())
                for rec in index:
                    data = z.read(rec['member'])
                    retained = (EVIDENCE/(path.stem+'-receipts')/rec['retained']).read_bytes()
                    assert data == retained and sha(data) == rec['sha256']
                    receipts.append({'artifact': path.name, **rec, 'byte_identical': True})
        archives[path.name] = {'path': str(path), 'bytes': path.stat().st_size, 'sha256': digest,
                               'transport_digest_match': aid in expected,
                               'all_members_read_crc_valid': True, 'members': rows}
        print('HASHED', path.name, digest, len(rows), flush=True)
    dump('archive-byte-audit.json', archives)
    dump('selected-receipt-audit.json', receipts)
    return archives

def retain_text_media():
    selected = []
    for aid in ('12470739875', '12470965068', '12470681259', 'run-logs'):
        basename = f'artifact-{aid}' if aid != 'run-logs' else aid
        with zipfile.ZipFile(EVIDENCE/(basename+'.zip')) as z:
            for item in z.infolist():
                n = item.filename
                take = aid == '12470965068' or aid == 'run-logs'
                if aid == '12470739875':
                    # Keep commands, gate receipts and all small native logs, not fixture source trees or trajectories.
                    take = (n.startswith('builds/v3-matrix/') and n.count('/') == 2) or n == 'builds/v3-network/campaign.json'
                    take |= n.startswith('builds/v3-network/') and (n.endswith(('.log', '.process.json', '/summary.json', '/source.json')))
                    take |= n.startswith('builds/v3-matrix/') and n.endswith('.log') and '/release-' not in n and '/state/' not in n
                    take |= n == 'builds/v3-matrix/protocol/matrix.md'
                if aid == '12470681259':
                    take = '/state/' not in n and '/server-state/' not in n and '/extracted/' not in n and n.endswith(('.json', '.txt', '.log'))
                    take |= n.startswith('v3-export-offline/') and n.endswith('.input.png')
                    take |= n in ('v3-export-network/03-exported-network-rifle.png',
                                  'v3-export-network/06-after-authority-reload-start.png',
                                  'v3-export-network/07-after-authority-reload-completion.png',
                                  'v3-export-network/08-settled.png',
                                  'v3-export-offline/02-offline-spawn.png',
                                  'v3-export-offline/04-move-aim.png',
                                  'v3-export-offline/05-after-fire.png',
                                  'v3-export-offline/06-after-reload.png')
                if take:
                    assert not n.endswith(('.zip', '.apk', '.exe', '.x86_64', '.a', '.sqlite', '.so'))
                    data = z.read(item)
                    write('selected/'+basename+'/'+n, data)
                    selected.append({'archive': basename+'.zip', 'member': n, 'relative': basename+'/'+n, 'bytes': len(data), 'sha256': sha(data)})
    dump('selection-manifest.json', selected)
    print('SELECTED', len(selected), sum(r['bytes'] for r in selected), 'bytes')

if __name__ == '__main__':
    blobs, identity = blob_map()
    print('FROZEN IDENTITY', json.dumps(identity), flush=True)
    archive_audit()
    retain_text_media()
