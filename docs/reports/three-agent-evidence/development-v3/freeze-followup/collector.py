"""Archive completed critic/control bytes only; do not execute their programs."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess

ROOT = Path(r'C:\Users\blith\AppData\Local\Temp\opencode\sightbreak-v3')
HERE = Path(__file__).parent
CRITIC = ROOT.parent / 'sol-freeze-final-critic-20261023T002632558647Z'
DEST = ROOT / 'docs/reports/three-agent-evidence/development-v3/freeze-followup'
if DEST.exists():
    raise SystemExit('Refusing to replace a published follow-up attempt')
DEST.mkdir(parents=True)
sources = [(CRITIC, 'critic'), (HERE / 'pathlib-after', 'corrected-control')]
records = []
for source, prefix in sources:
    for path in sorted(source.rglob('*')):
        if path.is_symlink():
            raise SystemExit('Symlink evidence refused')
        if not path.is_file() or '__pycache__' in path.parts:
            continue
        target = DEST / 'raw' / prefix / path.relative_to(source)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
        data = target.read_bytes()
        records.append({'origin': str(path), 'path': target.relative_to(DEST).as_posix(), 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
for name in ['pathlib_after.py', 'index-audit.json', 'audit_index.py']:
    target = DEST / 'raw' / name
    shutil.copyfile(HERE / name, target)
    data = target.read_bytes()
    records.append({'origin': str(HERE / name), 'path': target.relative_to(DEST).as_posix(), 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
if sum(item['bytes'] for item in records) > 1024 * 1024:
    raise SystemExit('Follow-up exceeds the 1 MiB publication bound')
shutil.copyfile(__file__, DEST / 'collector.py')
diff = subprocess.run(['git', 'diff', '--', 'scripts/test_matrix_process.py'], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
(DEST / 'TEST_ONLY_CHANGE.diff').write_bytes(diff.stdout)
(DEST / '.gitattributes').write_text('* -text\nraw/** -text\n', encoding='utf-8', newline='\n')
(DEST / '.gitignore').write_text('!raw/**\n', encoding='utf-8', newline='\n')
(DEST / 'COLLECTION.json').write_text(json.dumps({'scope': 'Completed source/synthetic critic and test-only correction; not Linux/native acceptance', 'files': records, 'omissions': ['Generated __pycache__ files only'], 'execution': 'This collector copied completed evidence; it did not execute controls.'}, indent=2), encoding='utf-8')
(DEST / 'README.md').write_text('''# Last bounded freeze follow-up

The independent critic found one P2 Linux-facing test-mock defect: mutating the
shared `os.name` made POSIX-initialized pathlib select unsupported WindowsPath.
Its original failed reproduction, corrected comparison, source hashes and raw
ordinary controls remain unchanged under `raw/critic/`.

The production implementation was not changed. `TEST_ONLY_CHANGE.diff` isolates
the Windows mock to the module reference. The actual existing unit then passed
with POSIX-initialized CPython 3.13.15 stdlib pathlib on Windows, and all 17
matrix-process tests exited zero. This is synthetic platform evidence, **not an
actual Linux/Python 3.12 run**. Earlier 272 normal + 74 optimized executions are
not relabelled as having run after this later test-only change.

The first index audit also caught four archive-metadata newline transformations;
its failed JSON is retained. The unpublished archive was given byte-preserving
attributes, with only its attributes checksum updated. Original raw payloads and
the external copies were not changed. Final index verification is a separate
read-only operation, not a retrospective change to that failure.

Exceptional Linux supervisor-death cleanup remains explicitly unverified and
fails closed. No game, native audio, campaign, export, database or device work was
performed by this follow-up. No human/device/production/8.5 gate is waived.
''', encoding='utf-8')
files = sorted(path for path in DEST.rglob('*') if path.is_file())
(DEST / 'SHA256SUMS.txt').write_text(''.join(hashlib.sha256(path.read_bytes()).hexdigest() + '  ' + path.relative_to(DEST).as_posix() + '\n' for path in files), encoding='utf-8', newline='\n')
print(json.dumps({'copied_files': len(records), 'copied_bytes': sum(item['bytes'] for item in records), 'published_payloads': len(files), 'directory': str(DEST)}, indent=2))
