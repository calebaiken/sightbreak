#!/usr/bin/env python3
"""Fixed single-run supervisor. Requires a root-authored release JSON; no retries."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import stat
import subprocess
import sys
import time

SOURCE = 'c32415148db1f110bbc7eadfca3793d4693429ff'
PREREGISTRATION = '15cdc599'
ROOT = Path('/workspace/sightbreak-collector-preflight-c324')
OUTPUT = ROOT / 'builds/collector-native-preflight-c324-20261024'
ENGINE = Path('/workspace/tools/godot-4.7.2/Godot_v4.7.2-stable_linux.x86_64')
ENGINE_SHA256 = '8d106cbe6144c2dc7e881d61d2429c1a8a76e6b22ef48bd5e48dcf934953f71e'
ENGINE_SHA512 = 'ac9f3af3d8b62237694bc03e7422b8f7b1a39095cf4eeaa8361b7465f13bc9dbaad47f60ac0ac217c9f0b2b3712be207039cd83953f4c72087214bd0357cabbc'
ZIP_SHA512 = '9aa00f7a605200940bce3027a567b782f49bd8e940dd06ae9e987bd65aee1b1467edd56ed84fcdcbdd44354bf613bdbb4e5d2913e925850368e150c59ed54c65'
WHOLE_SECONDS = 420
CLEANUP_SECONDS = 5
CADENCE_SECONDS = 0.10


def utc():
    return datetime.now(timezone.utc).isoformat()


def save(name, value):
    (OUTPUT / name).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def digest(path, algorithm):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, algorithm).hexdigest()


def git(*arguments):
    return subprocess.check_output(['git', '-C', str(ROOT), *arguments], timeout=20)


def source_manifest():
    assert git('rev-parse', 'HEAD').decode().strip() == SOURCE, 'Wrong runtime HEAD'
    assert not git('status', '--porcelain=v1').strip(), 'Runtime checkout is not clean'
    entries = {}
    for entry in git('ls-tree', '-rz', SOURCE).split(b'\0'):
        if not entry:
            continue
        header, raw_name = entry.split(b'\t', 1)
        name = os.fsdecode(raw_name)
        if name.startswith('docs/'):
            continue
        mode, kind, blob = header.decode().split()
        path = ROOT / name
        observed = path.lstat()
        assert kind == 'blob', ('Unexpected tree kind', name, kind)
        if mode == '120000':
            assert stat.S_ISLNK(observed.st_mode), ('File kind changed', name)
            data = os.fsencode(os.readlink(path))
        else:
            assert stat.S_ISREG(observed.st_mode), ('File kind changed', name)
            assert bool(observed.st_mode & 0o111) == (mode == '100755'), ('Mode changed', name)
            data = path.read_bytes()
        actual_blob = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
        assert actual_blob == blob, ('Source bytes changed', name)
        entries[name] = {'mode': mode, 'blob': blob, 'bytes': len(data),
                         'sha256': hashlib.sha256(data).hexdigest(),
                         'sha512': hashlib.sha512(data).hexdigest()}
    assert len(entries) == 507, 'Unexpected source inventory size'
    assert not (ROOT / 'game/.godot').exists(), 'Source cache must stay absent'
    uid = {str(path.relative_to(ROOT)): digest(path, 'sha256')
           for path in sorted((ROOT / 'game').rglob('*.uid'))}
    return {'source': SOURCE, 'entries': entries, 'uid': uid,
            'git_status': git('status', '--porcelain=v1').decode()}


def process(pid):
    try:
        directory = Path('/proc') / str(pid)
        text = (directory / 'stat').read_text()
        tail = text[text.rindex(')') + 2:].split()
        threads = {}
        for task in (directory / 'task').iterdir():
            try:
                threads[task.name] = sorted(os.sched_getaffinity(int(task.name)))
            except (OSError, ProcessLookupError):
                pass
        return {'pid': int(pid), 'start_ticks': int(tail[19]), 'ppid': int(tail[1]),
                'pgid': int(tail[2]), 'sid': int(tail[3]), 'state': tail[0],
                'argv': os.fsdecode((directory / 'cmdline').read_bytes()).split('\0')[:-1],
                'threads': threads}
    except (OSError, ValueError, ProcessLookupError):
        return None


def scan_owned(leader, leader_start, seen):
    """Read /proc only. Store descendants and owned session/group, no unrelated argv."""
    rows = {}
    for directory in Path('/proc').iterdir():
        if not directory.name.isdecimal():
            continue
        try:
            text = (directory / 'stat').read_text()
            tail = text[text.rindex(')') + 2:].split()
            rows[int(directory.name)] = (int(tail[1]), int(tail[2]), int(tail[3]), int(tail[19]))
        except (OSError, ValueError):
            pass
    # A reused leader PID cannot confer ownership on a new group/session.
    same_session = leader_start is None or leader not in rows or rows[leader][3] == leader_start
    owned = {pid for pid, row in rows.items()
             if (same_session and (row[1] == leader or row[2] == leader))
             or (pid, row[3]) in seen}
    while True:
        children = {pid for pid, row in rows.items() if row[0] in owned}
        if children <= owned:
            break
        owned |= children
    observations = []
    for pid in sorted(owned):
        row = process(pid)
        if row is not None and row['start_ticks'] == rows[pid][3]:
            seen.add((pid, row['start_ticks']))
            observations.append(row)
    return observations


def clean_group(leader, seen, sample):
    deadline = time.monotonic() + CLEANUP_SECONDS
    actions = []
    rows = sample('cleanup-start')
    group = [row for row in rows if row['pgid'] == leader and row['sid'] == leader]
    if group:
        try:
            os.killpg(leader, signal.SIGTERM)
            actions.append({'signal': 'TERM', 'utc': utc()})
        except ProcessLookupError:
            pass
    killed = False
    while rows and time.monotonic() < deadline:
        if not killed and time.monotonic() >= deadline - 2.5:
            group = [row for row in rows if row['pgid'] == leader and row['sid'] == leader]
            if group:
                try:
                    os.killpg(leader, signal.SIGKILL)
                    actions.append({'signal': 'KILL', 'utc': utc()})
                except ProcessLookupError:
                    pass
            killed = True
        time.sleep(min(CADENCE_SECONDS, max(0, deadline - time.monotonic())))
        rows = sample('cleanup')
    return {'actions': actions, 'remaining': rows, 'all_observed_identities_gone': not rows,
            'scope': 'Owned group/session and observed descendants only; finite sampling can miss short or escaped descendants'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--release', type=Path, required=True)
    args = parser.parse_args()
    release_bytes = args.release.read_bytes()
    release = json.loads(release_bytes)
    assert release['source'] == SOURCE and release['authorized_single_invocation'] is True
    assert release['preregistration'].startswith(PREREGISTRATION)
    assert release['wrapper_sha256'] == digest(Path(__file__), 'sha256')
    assert isinstance(release['root_release_commit'], str) and len(release['root_release_commit']) == 40
    assert os.sched_getaffinity(0) == {4}, 'Supervisor and observer require CPU4'
    OUTPUT.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    deadline = started + WHOLE_SECONDS
    report = {'source': SOURCE, 'started_utc': utc(), 'whole_seconds': WHOLE_SECONDS,
              'cleanup_seconds': CLEANUP_SECONDS, 'cadence_target_seconds': CADENCE_SECONDS,
              'supervisor': process(os.getpid()), 'release_sha256': hashlib.sha256(release_bytes).hexdigest(),
              'passed': False, 'launch_count': 0, 'failure': None}
    (OUTPUT / 'root-release.json').write_bytes(release_bytes)
    child = None
    seen, sample_times = set(), []
    try:
        before = source_manifest()
        save('source-before.json', before)
        engine = {'path': str(ENGINE), 'sha256': digest(ENGINE, 'sha256'),
                  'sha512': digest(ENGINE, 'sha512'),
                  'zip_sha512': digest(ENGINE.parent / 'godot.zip', 'sha512')}
        save('engine.json', engine)
        assert engine['sha256'] == ENGINE_SHA256 and engine['sha512'] == ENGINE_SHA512
        assert engine['zip_sha512'] == ZIP_SHA512
        (OUTPUT / 'state').mkdir()
        (OUTPUT / 'temporary').mkdir()
        command = [sys.executable, 'scripts/run_native_regressions.py', '--suites',
                   'movement_prediction', '--output', str(OUTPUT / 'native')]
        env = dict(os.environ)
        env.pop('DISPLAY', None)
        env.update(GODOT_BIN=str(ENGINE), SIGHTBREAK_TOOLS_DIR='/workspace/tools',
                   SIGHTBREAK_STATE_DIR=str(OUTPUT / 'state'), TMPDIR=str(OUTPUT / 'temporary'))
        report['command'] = command
        report['environment_overrides'] = {key: env[key] for key in
            ('GODOT_BIN', 'SIGHTBREAK_TOOLS_DIR', 'SIGHTBREAK_STATE_DIR', 'TMPDIR')}
        report['display_present'] = 'DISPLAY' in env
        with (OUTPUT / 'process-samples.jsonl').open('x') as samples, \
                (OUTPUT / 'runner.stdout').open('xb') as stdout, \
                (OUTPUT / 'runner.stderr').open('xb') as stderr:
            def native_affinity():
                os.sched_setaffinity(0, {0, 1})

            if time.monotonic() >= deadline:
                raise TimeoutError('Whole deadline exhausted during preparation; no runner launched')
            child = subprocess.Popen(command, cwd=ROOT, env=env, stdout=stdout, stderr=stderr,
                                     start_new_session=True, preexec_fn=native_affinity)
            report['launch_count'] = 1
            report['runner_pid'] = child.pid
            leader_start = None

            def sample(stage):
                now = time.monotonic()
                sample_times.append(now)
                rows = scan_owned(child.pid, leader_start, seen)
                samples.write(json.dumps({'utc': utc(), 'elapsed_seconds': now - started,
                                          'stage': stage, 'processes': rows}) + '\n')
                samples.flush()
                return rows

            timed_out = False
            try:
                initial = process(child.pid)
                if initial is None:
                    # The unreaped child still owns this session ID during cleanup.
                    raise RuntimeError('Could not bind runner start-time identity')
                leader_start = initial['start_ticks']
                seen.add((child.pid, leader_start))
                report['runner_start_ticks'] = leader_start
                while True:
                    sample('running')
                    result = child.poll()
                    if result is not None:
                        report['runner_exit'] = result
                        break
                    if time.monotonic() >= deadline:
                        timed_out = True
                        break
                    time.sleep(min(CADENCE_SECONDS, max(0, deadline - time.monotonic())))
            finally:
                report['timed_out'] = timed_out
                report['cleanup'] = clean_group(child.pid, seen, sample)
                # Reap a terminated runner without extending the five-second cleanup window.
                report['runner_exit'] = child.poll()
        report['whole_execution_seconds'] = sample_times[-1] - started
        report['sample_count'] = len(sample_times)
        report['maximum_sample_gap_seconds'] = max((b - a for a, b in zip(sample_times, sample_times[1:])), default=0)
        report['observed_identities'] = [{'pid': pid, 'start_ticks': ticks} for pid, ticks in sorted(seen)]
        after = source_manifest()
        save('source-after.json', after)
        report['source_and_uids_unchanged'] = after == before
        # Actual acceptance is independently reconstructed after root execution.
        report['passed'] = (not report['timed_out'] and report['runner_exit'] == 0
                            and report['source_and_uids_unchanged']
                            and report['cleanup']['all_observed_identities_gone'])
    except BaseException as error:
        report['failure'] = {'type': type(error).__name__, 'message': str(error)}
        report['passed'] = False
    finally:
        report['finished_utc'] = utc()
        report['wall_seconds_including_cleanup'] = time.monotonic() - started
        save('wrapper.json', report)
    print(json.dumps(report, sort_keys=True), flush=True)
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
