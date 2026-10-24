"""Restore the exact prior engine from a checksum-verified official archive."""
import hashlib
import json
from pathlib import Path, PurePosixPath
import urllib.request
import zipfile

ROOT = Path(__file__).parent / 'attempt'
ROOT.mkdir()
BASE = 'https://github.com/godotengine/godot/releases/download/4.7.2-stable/'
NAME = 'Godot_v4.7.2-stable_win64.exe.zip'
EXPECTED_ENGINE = 'ab1824f85bfd8e0e4128182c000c4003a3e042245b2967848d089b2a04b22424'
result = {'passed': False, 'source': BASE, 'version': '4.7.2-stable',
          'expected_prior_engine_sha256': EXPECTED_ENGINE, 'downloads': []}

def download(name):
    request = urllib.request.Request(BASE + name, headers={'User-Agent': 'Sightbreak-source-validation'})
    with urllib.request.urlopen(request, timeout=120) as response, (ROOT / name).open('xb') as output:
        if response.status != 200:
            raise RuntimeError(f'Unexpected HTTP status {response.status}')
        while block := response.read(1024 * 1024):
            output.write(block)
        result['downloads'].append({'url': BASE + name, 'resolved_url': response.url,
                                    'status': response.status, 'file': name})
    return ROOT / name

try:
    sums = download('SHA512-SUMS.txt')
    entries = [line.split() for line in sums.read_text().splitlines() if line.strip()]
    expected = [parts[0] for parts in entries if len(parts) == 2 and parts[1].lstrip('*') == NAME]
    if len(expected) != 1:
        raise RuntimeError('Official checksum file does not uniquely identify the Windows archive')
    archive = download(NAME)
    with archive.open('rb') as stream:
        actual = hashlib.file_digest(stream, 'sha512').hexdigest()
    result['archive_sha512'] = actual
    result['published_archive_sha512'] = expected[0]
    if actual != expected[0]:
        raise RuntimeError('Official archive checksum mismatch; no extraction permitted')
    binaries = []
    with zipfile.ZipFile(archive) as bundle:
        for member in bundle.infolist():
            name = member.filename
            if (member.orig_filename != name or '\\' in name or ':' in name
                    or PurePosixPath(name).is_absolute() or len(PurePosixPath(name).parts) != 1):
                raise RuntimeError(f'Noncanonical archive path: {name!r}')
            if name not in ('Godot_v4.7.2-stable_win64.exe', 'Godot_v4.7.2-stable_win64_console.exe'):
                raise RuntimeError(f'Unexpected official archive member: {name!r}')
            path = ROOT / name
            with bundle.open(member) as source, path.open('xb') as target:
                while block := source.read(1024 * 1024):
                    target.write(block)
            with path.open('rb') as stream:
                digest = hashlib.file_digest(stream, 'sha256').hexdigest()
            binaries.append({'path': str(path), 'bytes': path.stat().st_size, 'sha256': digest})
    engine = [item for item in binaries if Path(item['path']).name == 'Godot_v4.7.2-stable_win64.exe']
    if len(engine) != 1 or engine[0]['sha256'] != EXPECTED_ENGINE:
        raise RuntimeError('Downloaded engine differs from the prior frozen official executable')
    result.update(passed=True, binaries=binaries, engine=engine[0]['path'])
except BaseException as error:
    result['error'] = repr(error)
    raise
finally:
    (ROOT / 'results.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2))
