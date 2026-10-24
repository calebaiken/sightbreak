#!/usr/bin/env python3
"""Light read-only source admission. Native execution is never invoked."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time

SOURCE = Path('/workspace/sightbreak-linux-profile-fixture-native-types')
OLD_SOURCE = Path('/workspace/sightbreak-linux-profile-acquisition')
SHA = '216d39ada8f9d11e2d8544d01fde42da49607b14'
OLD = 'f242a2f20adb3ba1d9c49feb1c6caca1bdbf52b9'
ORIGINAL_REVIEW = Path('/workspace/reviews/linux-profile-acquisition-native/docs/reports/gauntlet/m1-linux-profile-acquisition/native-independent')
REPORT = 'docs/reports/gauntlet/m1-linux-profile-acquisition/native-type-correction-r1'
started = time.monotonic()
checks = []


def check(name, passed, evidence=None):
    checks.append({'name': name, 'passed': bool(passed), 'evidence': evidence})
    if not passed:
        raise AssertionError(name)


def identity(raw):
    return {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def git(root, *args):
    return subprocess.run(['git', '-C', str(root), *args], check=True, capture_output=True, timeout=10).stdout


def verify_sources(root, commit, expected=None):
    raw = git(root, 'ls-tree', '-rz', commit, '--', 'game', 'scripts')
    rows = []
    for line in raw.split(b'\0'):
        if line:
            meta, name = line.split(b'\t', 1)
            mode, kind, blob = meta.split()
            check('regular tracked source ' + name.decode(), kind == b'blob' and mode in (b'100644', b'100755'))
            name = name.decode()
            content = (root / name).read_bytes()
            observed_blob = hashlib.sha1(b'blob ' + str(len(content)).encode() + b'\0' + content).hexdigest()
            check('frozen Git byte identity ' + str(root / name), observed_blob == blob.decode())
            rows.append({'path': name, **identity(content), 'git_blob': blob.decode(), 'mode': mode.decode()})
    if expected is not None:
        check('original 430-source ledger preserved', rows == expected, {'count': len(rows)})
    return rows


def run():
    check('light work pinned to CPU 4', sorted(os.sched_getaffinity(0)) == [4])
    for root, commit in ((SOURCE, SHA), (OLD_SOURCE, OLD)):
        check('exact HEAD ' + str(root), git(root, 'rev-parse', 'HEAD').decode().strip() == commit)
        check('clean source ' + str(root), not git(root, 'status', '--porcelain', '--untracked-files=all'))
    check('unchanged game tree', git(SOURCE, 'rev-parse', SHA + ':game').decode().strip() == '55691684d31d44f1680141954bbe530443de9d1f')
    candidate_sources = verify_sources(SOURCE, SHA)
    original_before = json.loads((OLD_SOURCE / 'builds/linux-profile-acquisition-r1/original-before.json').read_bytes())
    original_sources = verify_sources(OLD_SOURCE, OLD, original_before)
    ledger = json.loads((SOURCE / REPORT / 'source.json').read_bytes())
    for name, wanted in ledger['files'].items():
        raw = (SOURCE / name).read_bytes()
        check('candidate source-manifest identity ' + name, identity(raw) == wanted)
        check('candidate source-manifest frozen bytes ' + name, raw == git(SOURCE, 'show', SHA + ':' + name))
    changed = git(SOURCE, 'diff', '--name-only', OLD, SHA).decode().splitlines()
    remaining = [name for name in changed if not name.startswith(REPORT + '/')]
    check('only declared source delta', remaining == ['scripts/diagnostics/linux_profile_overhead.gd', 'scripts/linux_profile_acquire.py'], remaining)
    fixture = 'scripts/diagnostics/linux_profile_overhead.gd'
    wrapper = 'scripts/linux_profile_acquire.py'
    old_fixture = git(SOURCE, 'show', OLD + ':' + fixture)
    wanted_fixture = old_fixture.replace(b'var keys := value.keys()', b'var keys: Array = value.keys()')
    check('one exact fixture declaration change', wanted_fixture != old_fixture and (SOURCE / fixture).read_bytes() == wanted_fixture)
    old_wrapper = git(SOURCE, 'show', OLD + ':' + wrapper)
    wanted_wrapper = old_wrapper.replace(b'builds/linux-profile-acquisition-r1', b'builds/linux-profile-acquisition-r2').replace(
        b'1e3f4094f2439a7ae054455c5f7e2ca4a993a15067affebce57e760569ee1dae',
        b'bac96e5c3aa9e63dfe0aa41522076cb6352293a3d5d9e70657a19cdfa4d52b92')
    check('two exact supervisor pin changes', wanted_wrapper != old_wrapper and (SOURCE / wrapper).read_bytes() == wanted_wrapper)
    output = SOURCE / 'builds/linux-profile-acquisition-r2'
    check('fresh R2 output and claim absent including symlinks', not output.exists() and not output.is_symlink())
    check('output parent is not symlinked', not output.parent.is_symlink())
    check('fresh R2 outer streams/receipt absent', not list((SOURCE / '.local').glob('linux-profile-acquisition-r2-*')))
    registry_path = ORIGINAL_REVIEW / 'raw-registry.json'
    registry_raw = registry_path.read_bytes()
    registry = json.loads(registry_raw)
    originals = {}
    for name, wanted in registry['files'].items():
        if '/' not in name:
            raw = (OLD_SOURCE / 'builds/linux-profile-acquisition-r1' / name).read_bytes()
            check('original top-level retained bytes ' + name, identity(raw) == wanted)
            originals[name] = identity(raw)
    outer_paths = {'wrapper.stdout': '.local/linux-profile-acquisition-r1-wrapper.stdout',
                   'wrapper.stderr': '.local/linux-profile-acquisition-r1-wrapper.stderr',
                   'outer-tool-receipt.json': '.local/linux-profile-acquisition-r1-outer-tool-receipt.json'}
    for name, path in outer_paths.items():
        raw = (OLD_SOURCE / path).read_bytes()
        check('original outer bytes ' + name, identity(raw) == registry['outer'][name])
        originals[path] = identity(raw)
    return {'passed': True, 'status': 'SOURCE ADMISSION ONLY; ROOT ONE RELEASE STILL REQUIRED',
        'candidate': SHA, 'source_path': str(SOURCE), 'candidate_sources': candidate_sources,
        'original_sources': original_sources, 'manifest_artifact_count': len(ledger['files']),
        'original_raw_registry_identity': identity(registry_raw), 'original_light_preservation': originals,
        'original_preservation_scope': 'All 430 tracked game/script files, top-level original raw files and three original outer records. Full 224-file/cache/template/archive readback is deferred until root clearance.',
        'native_launches': 0, 'root_release_observed': False, 'checks': checks}


if __name__ == '__main__':
    def deadline(_signal, _frame):
        raise TimeoutError('Light source-admission 45-second bound')
    signal.signal(signal.SIGALRM, deadline)
    signal.setitimer(signal.ITIMER_REAL, 45)
    try:
        result = run()
    except Exception as error:
        result = {'passed': False, 'error': type(error).__name__ + ': ' + str(error), 'checks': checks}
    result.update(started_monotonic=started, ended_monotonic=time.monotonic(),
                  utc=datetime.now(timezone.utc).isoformat(), observer_affinity=sorted(os.sched_getaffinity(0)))
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result['passed'] else 1)
