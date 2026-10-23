#!/usr/bin/env python3
"""Bounded read-only ownership observer; never launches or signals a subject."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import time

SOURCE = Path('/workspace/sightbreak-linux-packed-import-boundary')
SHA = 'ec6b34ce9af4db1199cd5266b2f7cfcc9831f5ef'
REPORT = Path(__file__).resolve().parent
OUTPUT = SOURCE / 'builds/linux-profile-acquisition-r3'


def parse_stat(pid, raw):
    fields = raw[raw.rfind(')') + 2:].split()
    return {'pid': pid, 'start_ticks': int(fields[19]), 'state': fields[0],
            'ppid': int(fields[1]), 'pgid': int(fields[2]), 'sid': int(fields[3]),
            'comm': raw[raw.find('(') + 1:raw.rfind(')')]}


def scan():
    result = {}
    for item in Path('/proc').iterdir():
        if item.name.isdigit():
            try:
                row = parse_stat(int(item.name), (item / 'stat').read_text())
                result[row['pid']] = row
            except (OSError, ValueError, IndexError):
                pass
    return result


def key(row):
    return row['pid'], row['start_ticks']


def detail(row):
    pid = row['pid']
    base = Path('/proc') / str(pid)
    result = dict(row)
    try:
        result['argv'] = (base / 'cmdline').read_bytes().decode(errors='replace').strip('\0').split('\0')
        result['cwd'] = os.readlink(base / 'cwd')
        result['exe'] = os.readlink(base / 'exe')
        result['affinity'] = sorted(os.sched_getaffinity(pid))
        result['nice'] = os.getpriority(os.PRIO_PROCESS, pid)
        result['scheduler'] = os.sched_getscheduler(pid)
        wanted = {'DISPLAY', 'LIBGL_ALWAYS_SOFTWARE', 'LP_NUM_THREADS', 'XDG_DATA_HOME',
                  'XDG_CONFIG_HOME', 'XDG_CACHE_HOME', 'MESA_SHADER_CACHE_DIR',
                  'GODOT_SILENCE_ROOT_WARNING'}
        env = (base / 'environ').read_bytes().split(b'\0')
        result['selected_environment'] = {k.decode(): v.decode(errors='replace')
            for part in env if b'=' in part for k, v in [part.split(b'=', 1)] if k.decode(errors='replace') in wanted}
        result['threads'] = {p.name: sorted(os.sched_getaffinity(int(p.name)))
                             for p in (base / 'task').iterdir() if p.name.isdigit()}
        sockets = []
        for fd in (base / 'fd').iterdir():
            try:
                target = os.readlink(fd)
                if target.startswith('socket:['):
                    sockets.append({'fd': int(fd.name), 'inode': target[8:-1]})
            except OSError:
                pass
        result['sockets'] = sorted(sockets, key=lambda item: item['fd'])
        result['identity_revalidated'] = key(parse_stat(pid, (base / 'stat').read_text())) == key(row)
    except (OSError, ValueError, IndexError) as error:
        result['read_error'] = type(error).__name__ + ': ' + str(error)
    return result


def listeners(inodes=()):
    result = {}
    for name in ('tcp', 'tcp6', 'udp', 'udp6'):
        try:
            lines = Path('/proc/net', name).read_text().splitlines()[1:]
            result[name] = [line.strip() for line in lines if len(line.split()) > 9
                and (line.split()[9] in inodes or line.split()[3] == '0A'
                     or name.startswith('udp') and line.split()[3] == '07')]
        except OSError as error:
            result[name] = {'read_error': str(error)}
    try:
        result['unix_display_or_owned'] = [line.strip() for line in Path('/proc/net/unix').read_text().splitlines()[1:]
            if 'X99127' in line or len(line.split()) > 6 and line.split()[6] in inodes]
    except OSError as error:
        result['unix_display_or_owned'] = {'read_error': str(error)}
    for name in ('/tmp/.X11-unix/X99127', '/tmp/.X99127-lock'):
        path = Path(name)
        try:
            item = path.lstat()
            result[name] = {'exists': True, 'inode': item.st_ino, 'mode': item.st_mode,
                            'symlink': path.is_symlink()}
        except FileNotFoundError:
            result[name] = {'exists': False}
    return result


def descendants(current, seeds):
    result = set(seeds)
    while True:
        added = {pid for pid, row in current.items() if row['ppid'] in result} - result
        if not added:
            return result
        result |= added


def is_supervisor(row):
    observed = detail(row)
    argv = observed.get('argv', [])
    paths = {str(SOURCE / 'scripts/linux_profile_acquire.py'), 'scripts/linux_profile_acquire.py'}
    return (observed.get('cwd') == str(SOURCE) and any(value in paths for value in argv)
            and '--execute-frozen-source' in argv and SHA in argv
            and observed.get('identity_revalidated') is True)


def self_check():
    fields = ['S', '11', '12', '13', *(['0'] * 15), '456', '0']
    row = parse_stat(10, '10 (unusual ) name) ' + ' '.join(fields))
    assert (row['comm'], row['ppid'], row['pgid'], row['sid'], row['start_ticks']) == ('unusual ) name', 11, 12, 13, 456)
    current = {1: {'ppid': 0}, 2: {'ppid': 1}, 3: {'ppid': 2}, 4: {'ppid': 0}}
    assert descendants(current, {1}) == {1, 2, 3}
    assert key({'pid': 1, 'start_ticks': 10}) != key({'pid': 1, 'start_ticks': 11})
    print('PASS: tricky stat name, multi-generation ownership and PID reuse controls')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--self-check', action='store_true')
    parser.add_argument('--root-release-ref')
    args = parser.parse_args()
    if args.self_check:
        self_check()
        return
    if not args.root_release_ref:
        parser.error('Record the actual explicit ROOT ONE release reference; no release is inferred')
    if sorted(os.sched_getaffinity(0)) != [4]:
        parser.error('Run this observer on CPU 4 only')
    if OUTPUT.exists() or OUTPUT.is_symlink():
        parser.error('Start the independent observer before the fresh acquisition output exists')
    local = SOURCE / '.local'
    if not local.is_dir() or local.is_symlink():
        parser.error('Root must first complete prescribed non-symlink .local mkdir')
    if OUTPUT.parent.is_symlink() or list(local.glob('linux-profile-acquisition-r3-*')):
        parser.error('Fresh output parent or external streams/receipt are not admissible')
    target = REPORT / 'live-observer.jsonl'
    started = time.monotonic()
    known, sessions, groups = {}, set(), set()
    root_key, root_ended, root_original = None, None, None
    previous, sample_number = None, 0
    with target.open('x') as stream:
        def emit(event, **data):
            stream.write(json.dumps({'event': event, 'utc': datetime.now(timezone.utc).isoformat(),
                'monotonic': time.monotonic(), **data}, sort_keys=True) + '\n')
            stream.flush()
        emit('start', source=SHA, source_path=str(SOURCE), release_reference=args.root_release_ref,
             observer=detail(scan()[os.getpid()]), interval_seconds=0.1,
             cap_seconds=1440, discovery_cap_seconds=60, terminal_grace_seconds=10,
             preexisting_listeners=listeners(), semantics='Read-only observations; no signals or children; no CPU utilization sampling')
        while time.monotonic() - started < 1440:
            current = scan()
            if root_key is None:
                matches = [row for row in current.values() if 'python' in row['comm'].lower() and is_supervisor(row)]
                if len(matches) > 1:
                    emit('failure', reason='Multiple exact supervisors', matches=matches)
                    break
                if matches:
                    root_key = key(matches[0])
                    root_original = {name: matches[0][name] for name in ('pgid', 'sid')}
                    known[root_key] = matches[0]
                    emit('supervisor_discovered', identity=detail(matches[0]))
                elif time.monotonic() - started >= 60:
                    emit('failure', reason='No exact supervisor observed within discovery cap')
                    break
            live_seeds = {pid for pid, row in current.items() if key(row) in known}
            anchored_sessions = {row['sid'] for row in current.values() if key(row) in known and row['sid'] in sessions}
            anchored_groups = {row['pgid'] for row in current.values() if key(row) in known and row['pgid'] in groups}
            seeds = live_seeds | {pid for pid, row in current.items()
                if row['sid'] in anchored_sessions or row['pgid'] in anchored_groups}
            selected = descendants(current, seeds)
            new_details = []
            for pid in selected:
                row = current[pid]
                if key(row) not in known:
                    known[key(row)] = row
                    new_details.append(detail(row))
                if row['sid'] == row['pgid'] == pid:
                    sessions.add(row['sid'])
                    groups.add(row['pgid'])
            alive = [row for row in current.values() if key(row) in known]
            observed = [detail(row) for row in alive]
            inodes = {item['inode'] for row in observed for item in row.get('sockets', [])}
            view = {'observed': observed, 'listeners': listeners(inodes),
                    'original_groups': [row for row in current.values() if row['pgid'] in groups],
                    'original_sessions': [row for row in current.values() if row['sid'] in sessions],
                    'supervisor_original_ids': root_original,
                    'supervisor_original_group_members': [row for row in current.values()
                        if root_original and row['pgid'] == root_original['pgid']],
                    'supervisor_original_session_members': [row for row in current.values()
                        if root_original and row['sid'] == root_original['sid']]}
            serialized = json.dumps(view, sort_keys=True)
            if serialized != previous or sample_number % 10 == 0:
                emit('observation', sample=sample_number, newly_observed=new_details, **view)
                previous = serialized
            sample_number += 1
            if root_key and root_key not in {key(row) for row in current.values()}:
                if root_ended is None:
                    root_ended = time.monotonic()
                    emit('supervisor_absent', observed_survivors=alive)
                if time.monotonic() - root_ended >= 10:
                    emit('terminal', supervisor=root_key, observed_identity_count=len(known),
                         all_observed_absent=not alive, **view)
                    break
            time.sleep(0.1)
        else:
            emit('failure', reason='Observer absolute cap reached; no acquisition verdict implied')
        emit('observer_return', elapsed_seconds=time.monotonic() - started, samples=sample_number)


if __name__ == '__main__':
    main()
