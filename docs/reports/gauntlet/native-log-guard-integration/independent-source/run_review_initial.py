#!/usr/bin/env python3
"""Reproduce source-bound pure review; never launches the engine."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[4]
SOURCE = '64a7afbad452d9559a39844bde7f25026029c97b'
SHALLOW = Path('/workspace/reviews/strict-native-log-integration-depth1')
MINIMAL = Path('/workspace/reviews/strict-native-log-integration-minimal')
BASELINE = Path('/workspace/reviews/strict-native-log-integration-baseline')
RAW = Path('/workspace/sightbreak-audio-exit-lifecycle/.local/audio-owner-r1-20261023')
receipts = []


def sha(data):
    return hashlib.sha256(data).hexdigest()


def snapshot():
    return {p.relative_to(RAW).as_posix(): {'bytes': p.stat().st_size, 'sha256': sha(p.read_bytes())}
            for p in sorted(RAW.rglob('*')) if p.is_file()}


def run(label, command, cwd=ROOT, expected=0, env=None):
    started = datetime.now(timezone.utc).isoformat()
    clock = time.monotonic()
    result = subprocess.run(list(map(str, command)), cwd=cwd, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, timeout=60, env=env)
    for stream in ('stdout', 'stderr'):
        (OUT / (label + '.' + stream)).write_bytes(getattr(result, stream))
    receipt = {'label': label, 'command': list(map(str, command)), 'cwd': str(cwd),
               'started_utc': started, 'ended_utc': datetime.now(timezone.utc).isoformat(),
               'wall_seconds': time.monotonic() - clock, 'exit': result.returncode, 'expected_exit': expected,
               'stdout_sha256': sha(result.stdout), 'stderr_sha256': sha(result.stderr)}
    receipts.append(receipt)
    (OUT / 'command-receipts.json').write_text(json.dumps(receipts, indent=2) + '\n')
    print(label, 'exit', result.returncode, flush=True)
    if result.returncode != expected:
        print(result.stderr.decode(errors='replace'), flush=True)
        raise RuntimeError(label + ' unexpected result')
    return result.stdout


before = snapshot()
(OUT / 'original-preservation-before.json').write_text(json.dumps(before, indent=2) + '\n')
run('source-audit', [sys.executable, OUT / 'audit_source.py'])
assert not SHALLOW.exists(), 'Use a new empty independent shallow path'
run('shallow-init', ['git', 'init', SHALLOW])
run('shallow-origin', ['git', 'remote', 'add', 'origin', 'file:///workspace/sightbreak-strict-native-log-integration'], SHALLOW)
run('shallow-promisor', ['git', 'config', 'remote.origin.promisor', 'true'], SHALLOW)
run('shallow-filter', ['git', 'config', 'remote.origin.partialclonefilter', 'blob:none'], SHALLOW)
run('shallow-fetch', ['git', 'fetch', '--depth=1', '--filter=blob:none',
    '--upload-pack=git -c uploadpack.allowFilter=true upload-pack', 'origin', SOURCE], SHALLOW)
run('shallow-sparse-init', ['git', 'sparse-checkout', 'init', '--no-cone'], SHALLOW)
run('shallow-sparse-paths', ['git', 'sparse-checkout', 'set', '/scripts/', '/.github/',
    '/game/project.godot', '/game/export_presets.cfg'], SHALLOW)
run('shallow-autocrlf', ['git', 'config', 'core.autocrlf', 'true'], SHALLOW)
run('shallow-checkout', ['git', 'checkout', '--detach', 'FETCH_HEAD'], SHALLOW)
run('shallow-remove-origin', ['git', 'remote', 'remove', 'origin'], SHALLOW)
assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=SHALLOW).decode().strip() == SOURCE
assert subprocess.check_output(['git', 'rev-list', '--count', 'HEAD'], cwd=SHALLOW).strip() == b'1'
assert subprocess.check_output(['git', 'rev-parse', '--is-shallow-repository'], cwd=SHALLOW).strip() == b'true'
assert subprocess.check_output(['git', 'remote'], cwd=SHALLOW) == b''
assert subprocess.check_output(['git', 'status', '--porcelain'], cwd=SHALLOW) == b''
assert not (SHALLOW / 'docs').exists()
assert not list((SHALLOW / 'scripts').glob('*audio*lifecycle*'))
fixture = SHALLOW / 'scripts/fixtures/native_log/input-mode.log'
assert sha(fixture.read_bytes()) == 'a50a819152083c3d73564f21a5f15d36571c1b79c7178831667092f07537a218'
commands = [('shallow-native-log', [sys.executable, 'scripts/test_native_log.py', '-v']),
            ('shallow-build-manifest', [sys.executable, 'scripts/test_build_manifest.py', '-v']),
            ('shallow-package-qa-receipts', [sys.executable, 'scripts/test_package_qa_receipts.py', '-v']),
            ('shallow-validate-syntax', ['bash', '-n', 'scripts/validate.sh']),
            ('independent-falsifiers', [sys.executable, OUT / 'critic_controls.py', SHALLOW])]
with ThreadPoolExecutor(max_workers=len(commands)) as pool:
    futures = [pool.submit(run, label, command, SHALLOW) for label, command in commands]
    for future in futures:
        future.result()
for destination in (MINIMAL, BASELINE):
    assert not destination.exists(), 'Use a new empty independent minimal path'
    (destination / 'scripts').mkdir(parents=True)
    for filename in ('native_log.py', 'test_native_log.py'):
        shutil.copyfile(SHALLOW / 'scripts' / filename, destination / 'scripts' / filename)
    shutil.copytree(SHALLOW / 'scripts/fixtures/native_log', destination / 'scripts/fixtures/native_log')
(BASELINE / 'scripts/native_log.py').write_bytes(subprocess.check_output(
    ['git', 'show', '358b240ebadb8f32b581922ab99baec11ff9ed81:scripts/native_log.py'], cwd=ROOT))
restricted = dict(os.environ, PATH='/nonexistent-native-log-review', PYTHONNOUSERSITE='1', PYTHONDONTWRITEBYTECODE='1')
run('minimal-standalone', [sys.executable, 'scripts/test_native_log.py', '-v'], MINIMAL, env=restricted)
run('baseline-original-full-corpus-red', [sys.executable, 'scripts/test_native_log.py',
    'NativeLogTests.test_original_full_corpus_is_bound_and_rejected', '-v'], BASELINE, expected=1, env=restricted)
assert b'AssertionError: False is not true' in (OUT / 'baseline-original-full-corpus-red.stderr').read_bytes()
assert subprocess.check_output(['git', 'status', '--porcelain'], cwd=SHALLOW) == b''
minimal_files = sorted(p.relative_to(MINIMAL).as_posix() for p in MINIMAL.rglob('*') if p.is_file())
assert minimal_files == ['scripts/fixtures/native_log/.gitattributes', 'scripts/fixtures/native_log/input-mode.log',
                         'scripts/fixtures/native_log/provenance.json', 'scripts/native_log.py', 'scripts/test_native_log.py']
after = snapshot()
(OUT / 'original-preservation-after.json').write_text(json.dumps(after, indent=2) + '\n')
assert before == after
summary = {'source': SOURCE, 'head': SOURCE, 'depth': 1, 'shallow': True, 'remotes': [],
           'core_autocrlf': True, 'status_before_after': 'clean', 'reports_present': False,
           'audio_modules_present': [], 'fixture_bytes': fixture.stat().st_size, 'fixture_sha256': sha(fixture.read_bytes()),
           'maintained_methods': 37, 'independent_methods': 6, 'minimal_files': minimal_files,
           'minimal_PATH': restricted['PATH'], 'baseline_expected_red_exit': 1,
           'original_files_unchanged': len(before), 'commands': len(receipts)}
(OUT / 'verification.json').write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps(summary, indent=2))
