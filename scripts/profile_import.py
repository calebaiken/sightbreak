#!/usr/bin/env python3
"""Measure a fresh archived Godot import with writable state and error-log checks.

This is headless resource import, not mobile loading or shader compilation.
Existing global toolchain/OS caches are not flushed. No checkout files change.
"""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import re
import resource
import subprocess
import tarfile
import time

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--ref', default='HEAD')
    args = parser.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    if any(out.iterdir()):
        parser.error('Use an empty output directory to preserve a fresh import cache')
    commit = subprocess.check_output(['git', 'rev-parse', '--verify', args.ref + '^{commit}'], cwd=ROOT, text=True).strip()
    data = subprocess.check_output(['git', 'archive', commit + ':game'], cwd=ROOT)
    project = out / 'game'
    project.mkdir()
    with tarfile.open(fileobj=io.BytesIO(data)) as archive:
        archive.extractall(project, filter='data')
    env = os.environ.copy()
    for variable, suffix in [('XDG_DATA_HOME', 'data'), ('XDG_CONFIG_HOME', 'config'), ('XDG_CACHE_HOME', 'cache')]:
        path = out / 'state' / suffix
        path.mkdir(parents=True)
        env[variable] = str(path)
    godot = os.environ.get('GODOT_BIN', str(ROOT.parent / 'tools/godot-4.7.2/Godot_v4.7.2-stable_linux.x86_64'))
    command = [godot, '--path', str(project), '--headless', '--editor', '--import', '--quit']
    start = time.monotonic()
    with (out / 'import.log').open('w') as log:
        result = subprocess.run(command, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=180)
    seconds = time.monotonic() - start
    logged_errors = bool(re.search(r'^(?:SCRIPT ERROR|ERROR:)|Parse Error', (out / 'import.log').read_text(), re.M))
    report = {'source_commit': commit, 'archive_sha256': hashlib.sha256(data).hexdigest(),
              'command': command, 'seconds': seconds, 'max_child_rss_kib': resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,
              'exit': result.returncode, 'logged_errors': logged_errors,
              'passed': result.returncode == 0 and not logged_errors,
              'imported_files': sum(p.is_file() for p in (project / '.godot/imported').rglob('*')),
              'scope': 'Fresh archived game/import and XDG caches; global toolchain/OS caches retained. Headless resource import, not native shader compilation or mobile loading.'}
    (out / 'metrics.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
