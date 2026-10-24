"""Read-only index/source audit; does not execute native validation."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(r'C:\Users\blith\AppData\Local\Temp\opencode\sightbreak-v3')
OUTPUT = Path(__file__).with_name('index-audit.json')
PREFIX = 'docs/reports/three-agent-evidence/development-v3/'
LEDGERS = [
    PREFIX + 'pre-freeze-tooling-review/SHA256SUMS.txt',
    PREFIX + 'backend-input-review/round1/PUBLISHED_SHA256SUMS.txt',
    PREFIX + 'backend-input-review/source-review/PUBLISHED_SHA256SUMS.txt',
]


def git(*arguments, data=None):
    return subprocess.run(['git', *arguments], cwd=ROOT, input=data,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          check=True).stdout


if OUTPUT.exists():
    raise SystemExit('Refusing to replace an earlier index audit')
staged = git('diff', '--cached', '--name-only', '-z').decode().split('\0')[:-1]
assert staged and all(name.startswith(('.github/', 'game/', 'scripts/', 'docs/'))
                      for name in staged), staged
entries = []
for name in LEDGERS:
    parent = Path(name).parent
    for line in (ROOT / name).read_text(encoding='utf-8').splitlines():
        digest, relative = line.split(None, 1)
        relative = relative.lstrip('*')
        assert len(digest) == 64 and not Path(relative).is_absolute()
        entries.append(((parent / relative).as_posix(), digest))
batch = git('cat-file', '--batch', data=''.join(':' + name + '\n' for name, _ in entries).encode())
position = 0
mismatches = []
for name, expected in entries:
    end = batch.index(b'\n', position)
    header = batch[position:end].decode()
    fields = header.split()
    assert len(fields) == 3 and fields[1] == 'blob', (name, header)
    size = int(fields[2])
    data = batch[end + 1:end + 1 + size]
    position = end + 1 + size + 1
    actual = hashlib.sha256(data).hexdigest()
    if actual != expected:
        mismatches.append({'path': name, 'expected': expected, 'actual': actual})
assert position == len(batch)
receipt = json.loads((ROOT.parent / 'sightbreak-v3-evidence/pre-freeze-tooling-20261019/attempt-20261019T201340147085Z/results.json').read_text())
source_drift = []
for name, expected in receipt['source_after'].items():
    actual = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
    if actual != expected:
        source_drift.append({'path': name, 'expected': expected, 'actual': actual})
whitespace = subprocess.run(['git', 'diff', '--cached', '--check', '--', '.github', 'game', 'scripts'],
                            cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
result = {'scope': 'Read-only staged archive bytes and pre-freeze Python source audit; not native validation',
          'parent_commit': git('rev-parse', 'HEAD').decode().strip(),
          'staged_files': len(staged), 'ledger_payloads': len(entries),
          'ledger_mismatches': mismatches, 'source_drift': source_drift,
          'whitespace_exit': whitespace.returncode,
          'whitespace_stdout': whitespace.stdout.decode(errors='replace'),
          'whitespace_stderr': whitespace.stderr.decode(errors='replace'),
          'staged_paths': staged,
          'passed': not mismatches and not source_drift and whitespace.returncode == 0}
with OUTPUT.open('x', encoding='utf-8') as stream:
    json.dump(result, stream, indent=2)
print(json.dumps({key: value for key, value in result.items() if key != 'staged_paths'}, indent=2))
raise SystemExit(0 if result['passed'] else 1)
