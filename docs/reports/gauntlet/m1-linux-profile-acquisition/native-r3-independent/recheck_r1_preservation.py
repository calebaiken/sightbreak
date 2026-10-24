#!/usr/bin/env python3
"""Read-only complete failed-R1 identity replay; no native commands or writes."""
import ast
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import tarfile
import time
import zipfile

SOURCE = Path('/workspace/sightbreak-linux-profile-acquisition')
OLD = 'f242a2f20adb3ba1d9c49feb1c6caca1bdbf52b9'
CRITIC = '5cbbcd3c0e58a2b381c762d11cdbc0fe92936a5e'
PREFIX = 'docs/reports/gauntlet/m1-linux-profile-acquisition/native-independent'
REVIEW = Path('/workspace/reviews/linux-profile-acquisition-native') / PREFIX
RAW = SOURCE / 'builds/linux-profile-acquisition-r1'
started = time.monotonic()
checks = []


def check(name, value):
    checks.append({'name': name, 'passed': bool(value)})
    if not value:
        raise AssertionError(name)


def git(commit, name):
    return subprocess.run(['git', '-C', str(SOURCE), 'show', commit + ':' + name],
                          check=True, capture_output=True, timeout=10).stdout


def stream_identity(stream, sha512=False):
    h256, h512, size = hashlib.sha256(), hashlib.sha512(), 0
    for chunk in iter(lambda: stream.read(1024 * 1024), b''):
        size += len(chunk)
        h256.update(chunk)
        if sha512:
            h512.update(chunk)
    return {'bytes': size, 'sha256': h256.hexdigest(), **({'sha512': h512.hexdigest()} if sha512 else {})}


def identity(path, sha512=False):
    with Path(path).open('rb') as stream:
        return stream_identity(stream, sha512)


def run():
    check('CPU 4 only', sorted(os.sched_getaffinity(0)) == [4])
    for name in ('raw-registry.json', 'archive-members.json', 'audit-results.json', 'REVIEW.md'):
        check('original critic frozen bytes ' + name, (REVIEW / name).read_bytes() == git(CRITIC, PREFIX + '/' + name))
    registry = json.loads((REVIEW / 'raw-registry.json').read_bytes())
    archived = json.loads((REVIEW / 'archive-members.json').read_bytes())
    earlier = json.loads((REVIEW / 'audit-results.json').read_bytes())
    actual_names = {p.relative_to(RAW).as_posix() for p in RAW.rglob('*') if p.is_file()}
    check('no original raw symlinks', not any(p.is_symlink() for p in RAW.rglob('*')))
    check('exact complete 224-file original set', actual_names == set(registry['files']) and len(actual_names) == 224)
    for name, wanted in registry['files'].items():
        check('original raw identity ' + name, identity(RAW / name) == wanted)
    check('original total byte count', sum(v['bytes'] for v in registry['files'].values()) == registry['bytes'] == 178615722)
    outer = {'wrapper.stdout': SOURCE / '.local/linux-profile-acquisition-r1-wrapper.stdout',
             'wrapper.stderr': SOURCE / '.local/linux-profile-acquisition-r1-wrapper.stderr',
             'outer-tool-receipt.json': SOURCE / '.local/linux-profile-acquisition-r1-outer-tool-receipt.json'}
    for name, path in outer.items():
        check('original outer identity ' + name, identity(path) == registry['outer'][name])
    exclusions = registry['archive_exclusions']
    check('only three independently bound official template copies excluded', len(exclusions) == 3 and
          all(name.startswith('private-export-state/data/godot/export_templates/4.7.2.stable/') for name in exclusions))
    expected = {'attempt/' + name: value for name, value in registry['files'].items() if name not in exclusions}
    expected.update({'outer/' + name: value for name, value in registry['outer'].items()})
    for name in archived['members']:
        if name.startswith('frozen-source/'):
            raw = git(OLD, name.removeprefix('frozen-source/'))
            expected[name] = {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}
    check('exact frozen-source member count', sum(name.startswith('frozen-source/') for name in expected) == 7)
    check('complete independent archive ledger', expected == archived['members'] and len(expected) == 231)
    archive_path = REVIEW / archived['archive']
    check('original archive full identity', identity(archive_path) == archived['identity'])
    with tarfile.open(archive_path, 'r:gz') as archive:
        members = archive.getmembers()
        check('archive unique closed member set', len(members) == len(expected) and {m.name for m in members} == set(expected))
        for member in members:
            check('regular archive member ' + member.name, member.isfile() and not member.issym() and not member.islnk())
            with archive.extractfile(member) as stream:
                check('reopened archive member identity ' + member.name, stream_identity(stream) == expected[member.name])
    tree = ast.parse(git(OLD, 'scripts/toolchain.py'))
    constants = {node.targets[0].id: ast.literal_eval(node.value) for node in tree.body
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id in ('EDITORS', 'TEMPLATES_SHA512')}
    pins = {'godot.zip': constants['EDITORS']['linux'][2], 'templates.tpz': constants['TEMPLATES_SHA512']}
    overall = json.loads((RAW / 'overall.json').read_bytes())
    official = {}
    for name, pin in pins.items():
        path = Path('/workspace/tools/godot-4.7.2') / name
        observed = identity(path, sha512=True)
        check('official archive pin and prior identity ' + name,
              observed['sha512'] == pin and observed == earlier['observations']['official_archives'][name])
        official[name] = observed
        with zipfile.ZipFile(path) as archive:
            check('official archive unique names ' + name, len(archive.namelist()) == len(set(archive.namelist())))
            for row in overall['official_members']:
                if Path(row['archive']).name != name:
                    continue
                with archive.open(row['member']) as stream:
                    wanted = stream_identity(stream)
                check('official selected member ' + row['member'], wanted == {'bytes': row['bytes'], 'sha256': row['sha256']}
                      and row['official_sha512'] == pin)
                if name == 'templates.tpz':
                    member_name = Path(row['member']).name
                    excluded = 'private-export-state/data/godot/export_templates/4.7.2.stable/' + member_name
                    check('excluded official template direct equality ' + member_name,
                          exclusions[excluded] == wanted and identity(RAW / excluded) == wanted)
    for name, wanted in registry['files'].items():
        check('original remains equal after archive replay ' + name, identity(RAW / name) == wanted)
    for name, path in outer.items():
        check('outer remains equal after archive replay ' + name, identity(path) == registry['outer'][name])
    return {'passed': True, 'original_verdict': 'FAILED', 'original_source': OLD,
            'original_critic': CRITIC, 'raw_count': 224, 'raw_bytes': registry['bytes'],
            'archive_members': 231, 'archive_identity': archived['identity'],
            'official_archives': official, 'checks': checks, 'native_launches': 0,
            'scope': 'Finite original raw/outer/archive/official-member identity replay only. No R2 runtime or root release.'}


if __name__ == '__main__':
    def deadline(_signal, _frame):
        raise TimeoutError('Original preservation replay 120-second bound')
    signal.signal(signal.SIGALRM, deadline)
    signal.setitimer(signal.ITIMER_REAL, 120)
    try:
        result = run()
    except Exception as error:
        result = {'passed': False, 'error': type(error).__name__ + ': ' + str(error), 'checks': checks}
    result.update(started_monotonic=started, ended_monotonic=time.monotonic(),
                  utc=datetime.now(timezone.utc).isoformat(), observer_affinity=sorted(os.sched_getaffinity(0)))
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result['passed'] else 1)
