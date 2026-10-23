#!/usr/bin/env python3
"""Bounded independent source/freshness observation; launches only Git reads."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time

SOURCE = Path('/workspace/sightbreak-linux-packed-import-boundary')
SHA = 'ec6b34ce9af4db1199cd5266b2f7cfcc9831f5ef'
R2 = Path('/workspace/sightbreak-linux-profile-fixture-native-types')
R2_SHA = '216d39ada8f9d11e2d8544d01fde42da49607b14'
R1 = Path('/workspace/sightbreak-linux-profile-acquisition')
R1_SHA = 'f242a2f20adb3ba1d9c49feb1c6caca1bdbf52b9'
PREFIX = 'docs/reports/gauntlet/m1-linux-profile-acquisition/'
REPORT = PREFIX + 'packed-remap-boundary-r1/'
REVIEWS = {
    'r1': Path('/workspace/reviews/linux-profile-acquisition-native') / (PREFIX + 'native-independent'),
    'r2': Path('/workspace/reviews/linux-profile-acquisition-r2-native') / (PREFIX + 'native-r2-independent'),
}
started = time.monotonic()
checks = []


def check(name, passed, evidence=None):
    checks.append({'name': name, 'passed': bool(passed), 'evidence': evidence})
    if not passed:
        raise AssertionError(name)


def identity(raw):
    return {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def git(root, *args):
    return subprocess.run(['git', '-C', str(root), *args], check=True,
                          capture_output=True, timeout=10).stdout


def sources(root, commit):
    rows = []
    for line in git(root, 'ls-tree', '-rz', commit, '--', 'game', 'scripts').split(b'\0'):
        if not line:
            continue
        meta, name = line.split(b'\t', 1)
        mode, kind, blob = meta.decode().split()
        name = name.decode()
        path = root / name
        check('regular tracked source ' + str(path), kind == 'blob' and
              mode in ('100644', '100755') and path.is_file() and not path.is_symlink())
        raw = path.read_bytes()
        observed = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
        check('frozen Git bytes ' + str(path), observed == blob)
        check('materialized executable mode ' + str(path), bool(path.stat().st_mode & 0o111) == (mode == '100755'))
        rows.append({'path': name, **identity(raw), 'git_blob': blob, 'mode': mode})
    return rows


def original_light(label, root):
    review = REVIEWS[label]
    registry_raw = (review / 'raw-registry.json').read_bytes()
    registry = json.loads(registry_raw)
    found = {}
    for name, wanted in registry['files'].items():
        if '/' not in name:
            raw = (root / ('builds/linux-profile-acquisition-' + label) / name).read_bytes()
            check(label + ' original top-level bytes ' + name, identity(raw) == wanted)
            found[name] = identity(raw)
    for name, suffix in (('wrapper.stdout', 'wrapper.stdout'), ('wrapper.stderr', 'wrapper.stderr'),
                         ('outer-tool-receipt.json', 'outer-tool-receipt.json')):
        relative = '.local/linux-profile-acquisition-' + label + '-' + suffix
        raw = (root / relative).read_bytes()
        check(label + ' original outer bytes ' + name, identity(raw) == registry['outer'][name])
        found[relative] = identity(raw)
    return {'registry_identity': identity(registry_raw), 'original_file_count': registry['file_count'],
            'light_file_count': len(found), 'light_files': found}


def run():
    check('light work pinned CPU 4', sorted(os.sched_getaffinity(0)) == [4])
    inventories = {}
    for label, root, commit in (('candidate', SOURCE, SHA), ('r2', R2, R2_SHA), ('r1', R1, R1_SHA)):
        check(label + ' exact clean HEAD', git(root, 'rev-parse', 'HEAD').decode().strip() == commit
              and not git(root, 'status', '--porcelain', '--untracked-files=all'))
        check(label + ' unchanged shipping game tree', git(root, 'rev-parse', commit + ':game').decode().strip()
              == '55691684d31d44f1680141954bbe530443de9d1f')
        inventories[label] = sources(root, commit)
    for label, root in (('r2', R2), ('r1', R1)):
        original = json.loads((root / ('builds/linux-profile-acquisition-' + label) / 'original-before.json').read_bytes())
        check(label + ' historical source ledger preserved', inventories[label] == original,
              {'count': len(original)})
    ledger = json.loads((SOURCE / REPORT / 'source.json').read_bytes())
    for name, wanted in ledger['candidate_files'].items():
        raw = (SOURCE / name).read_bytes()
        check('candidate declared source hash ' + name, hashlib.sha256(raw).hexdigest() == wanted)
        check('candidate declared source frozen bytes ' + name, raw == git(SOURCE, 'show', SHA + ':' + name))
    changed = git(SOURCE, 'diff', '--name-only', R2_SHA, SHA).decode().splitlines()
    remaining = [name for name in changed if not name.startswith(REPORT)]
    check('complete only declared source delta', remaining == sorted(ledger['candidate_files']), remaining)
    wrapper = 'scripts/linux_profile_acquire.py'
    old = git(SOURCE, 'show', R2_SHA + ':' + wrapper)
    check('exact one wrapper output delta', old.replace(b'builds/linux-profile-acquisition-r2',
          b'builds/linux-profile-acquisition-r3') == (SOURCE / wrapper).read_bytes())
    frozen = {}
    for name in ('scripts/linux_profile_overhead.py', 'scripts/diagnostics/linux_profile_overhead.gd',
                 'scripts/diagnostics/linux_profile_overhead.tscn', 'scripts/toolchain.py',
                 PREFIX + 'pins.json', REPORT + 'HANDOFF.md', REPORT + 'source.json',
                 REPORT + 'fixtures/packed-assets-icon.svg.import',
                 REPORT + 'fixtures/staged-assets-icon.svg.import', REPORT + 'fixtures/reader-216d39a.py'):
        raw = (SOURCE / name).read_bytes()
        check('frozen report/controller/tool pin ' + name, raw == git(SOURCE, 'show', SHA + ':' + name))
        frozen[name] = identity(raw)
    output = SOURCE / 'builds/linux-profile-acquisition-r3'
    check('fresh R3 output and claim absent including symlinks', not output.exists() and not output.is_symlink()
          and not (output / 'attempt.claim').exists() and not (output / 'attempt.claim').is_symlink())
    check('fresh output parent not symlink', not output.parent.is_symlink())
    local = SOURCE / '.local'
    check('prescribed root mkdir completed before activation', local.is_dir() and not local.is_symlink())
    check('fresh R3 external streams and receipt absent including symlinks',
          not list(local.glob('linux-profile-acquisition-r3-*')))
    old_bytes = {label: original_light(label, root) for label, root in (('r1', R1), ('r2', R2))}
    return {'passed': True, 'status': 'PREPARATION ADMISSION ONLY; FRESH SOURCE ACCEPTANCE AND ROOT ONE RELEASE REQUIRED',
            'candidate': SHA, 'source_path': str(SOURCE), 'inventories': inventories,
            'frozen_artifacts': frozen, 'original_light_preservation': old_bytes,
            'source_acceptance_observed': False, 'root_release_observed': False, 'native_launches': 0,
            'scope': 'All materialized tracked game/script/UID bytes and modes for candidate, R1 and R2; declared candidate delta; original top-level/outer bytes. Large full raw/archive/official-member replays deferred to root clearance. Historical overwritten cache bytes and unobserved short/escaped processes cannot be recreated.',
            'checks': checks}


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
