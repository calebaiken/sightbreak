"""Publish retained workflow rejection and source-only lint, excluding binaries."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE / 'attempt'
DEST = Path(r'C:\Users\blith\AppData\Local\Temp\opencode\sightbreak-v3\docs\reports\three-agent-evidence\development-v3\ci-attempts\workflow-rejected-7b6a71a')
DEST.mkdir(parents=True, exist_ok=False)
names = ['run.json', 'jobs.json', 'run.html', 'rejected-workflow.yml', 'corrected-workflow.yml',
         'actionlint-checksums.txt', 'results.json', 'before.stdout.txt', 'before.stderr.txt',
         'after.stdout.txt', 'after.stderr.txt']
for name in names:
    data = (SOURCE / name).read_bytes()
    (DEST / name).write_bytes(data)
for name in ['collect_and_lint.py', 'publish.py']:
    (DEST / name).write_bytes((HERE / name).read_bytes())
(DEST / '.gitattributes').write_text('* -text\n', encoding='utf-8')
(DEST / 'README.md').write_text('''# Workflow rejection, before native execution

Frozen source: `7b6a71a683ec5d1ed42d7245395c640225058e20`.
[Actions run 39879374637](https://github.com/calebaiken/sightbreak/actions/runs/39879374637)
was rejected at workflow validation: `runner.temp` is unavailable in job-level
`env` at original lines 106–108. `jobs.json` records zero jobs. No game test,
campaign, audio control, native flow or export ran; no development artifact exists
for this attempt. Raw public run API, jobs API and HTML annotation are retained.

The correction moves the three isolated audio paths into a runtime shell step,
writing `$RUNNER_TEMP`-derived values to `$GITHUB_ENV` before their first use.
No gameplay, thresholds, workload counts or acceptance gates changed.

`collect_and_lint.py` fetched the official actionlint 1.7.12 Windows archive and
verified it against that release's published SHA-256 list before execution.
`results.json` retains archive/executable hashes, actual commands and source
hashes: original workflow exit **1**, corrected workflow exit **0**. Shellcheck
and pyflakes were disabled explicitly; this proves workflow-schema/expression
validation only, not shell correctness or native execution. The corrected copy
contains the physical Windows bytes checked, not a claimed Linux execution.

The original attempt directory and downloaded executable/archive remain external
under `sightbreak-v3-evidence/ci-rejection-20261022/attempt`; binary downloads are
not redistributed here. Its failed workflow and diagnostics were not overwritten.
A new exact source commit and actual CI attempt are still required. These local
checks do not qualify a native candidate, development package or human/device gate.
''', encoding='utf-8')
files = sorted(p for p in DEST.iterdir() if p.is_file())
(DEST / 'SHA256SUMS.txt').write_text(''.join(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}\n' for p in files), encoding='utf-8')
print(json.dumps({'published_files': len(files) + 1, 'bytes': sum(p.stat().st_size for p in DEST.iterdir() if p.is_file()), 'path': str(DEST)}, indent=2))
