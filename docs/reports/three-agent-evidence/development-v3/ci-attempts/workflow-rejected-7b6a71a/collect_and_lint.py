"""Retain the rejected workflow and check its narrow correction, not gameplay."""
import hashlib
import json
from pathlib import Path
import subprocess
import urllib.request
import zipfile
from datetime import datetime, timezone

ROOT = Path(r'C:\Users\blith\AppData\Local\Temp\opencode\sightbreak-v3')
HERE = Path(__file__).resolve().parent
OUT = HERE / 'attempt'
OUT.mkdir(exist_ok=False)
OLD = '7b6a71a683ec5d1ed42d7245395c640225058e20'
RUN = '39879374637'
VERSION = '1.7.12'


def fetch(url, name):
    with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'sightbreak-source-evidence'}), timeout=90) as response:
        data = response.read()
        (OUT / name).write_bytes(data)
        return data


fetch(f'https://api.github.com/repos/calebaiken/sightbreak/actions/runs/{RUN}', 'run.json')
fetch(f'https://api.github.com/repos/calebaiken/sightbreak/actions/runs/{RUN}/jobs', 'jobs.json')
fetch(f'https://github.com/calebaiken/sightbreak/actions/runs/{RUN}', 'run.html')
old_bytes = subprocess.check_output(['git', 'show', f'{OLD}:.github/workflows/v3-development.yml'], cwd=ROOT)
(OUT / 'rejected-workflow.yml').write_bytes(old_bytes)
fixed = ROOT / '.github/workflows/v3-development.yml'
fixed_bytes = fixed.read_bytes()
(OUT / 'corrected-workflow.yml').write_bytes(fixed_bytes)
archive_name = f'actionlint_{VERSION}_windows_amd64.zip'
base = f'https://github.com/rhysd/actionlint/releases/download/v{VERSION}/'
checksums = fetch(base + f'actionlint_{VERSION}_checksums.txt', 'actionlint-checksums.txt')
archive_bytes = fetch(base + archive_name, archive_name)
expected = next(line.split()[0] for line in checksums.decode().splitlines() if line.split()[-1].lstrip('*') == archive_name)
actual = hashlib.sha256(archive_bytes).hexdigest()
if expected != actual:
    raise RuntimeError('Official actionlint archive checksum mismatch')
with zipfile.ZipFile(OUT / archive_name) as archive:
    executable = archive.read('actionlint.exe')
(OUT / 'actionlint.exe').write_bytes(executable)
rows = []
for label, path in [('before', OUT / 'rejected-workflow.yml'), ('after', fixed)]:
    command = [str(OUT / 'actionlint.exe'), '-no-color', '-shellcheck=', '-pyflakes=', str(path)]
    result = subprocess.run(command, cwd=ROOT, capture_output=True, timeout=30)
    (OUT / f'{label}.stdout.txt').write_bytes(result.stdout)
    (OUT / f'{label}.stderr.txt').write_bytes(result.stderr)
    rows.append({'label': label, 'command': command, 'exit': result.returncode})
report = {
    'utc': datetime.now(timezone.utc).isoformat(), 'scope': 'Workflow source validation only; no native job executed',
    'rejected_source': OLD, 'run_id': RUN, 'actionlint_version': VERSION,
    'actionlint_archive_sha256': actual, 'actionlint_exe_sha256': hashlib.sha256(executable).hexdigest(),
    'before_sha256': hashlib.sha256(old_bytes).hexdigest(), 'after_sha256': hashlib.sha256(fixed_bytes).hexdigest(),
    'checks': rows, 'workflow_unchanged_during_check': fixed.read_bytes() == fixed_bytes,
}
(OUT / 'results.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps(report, indent=2))
if rows[0]['exit'] == 0 or rows[1]['exit'] != 0 or not report['workflow_unchanged_during_check']:
    raise SystemExit(1)
