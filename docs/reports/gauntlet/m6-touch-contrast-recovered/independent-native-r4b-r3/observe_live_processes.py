#!/usr/bin/env python3
"""Bounded lightweight /proc observations; never controls the native pipeline."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import time

RAW = Path('/workspace/sightbreak-touch-contrast-native-recovered-r4b-r3')
REPORT = Path(__file__).resolve().parent
SELECTORS = ('DISPLAY', 'SIGHTBREAK_STATE_DIR', 'XDG_DATA_HOME', 'XDG_CONFIG_HOME', 'XDG_CACHE_HOME', 'LP_NUM_THREADS', 'OMP_NUM_THREADS')
parser = argparse.ArgumentParser()
parser.add_argument('--seconds', type=float, default=3600)
parser.add_argument('--interval', type=float, default=1)
args = parser.parse_args()
require_absent = REPORT / 'live-process-observations.jsonl'
assert not require_absent.exists()
known = {}
start = time.monotonic()


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def process(pid):
    root = Path('/proc') / str(pid)
    try:
        raw_stat = (root / 'stat').read_text()
        tail = raw_stat[raw_stat.rfind(')') + 2:].split()
        command = (root / 'cmdline').read_bytes().decode(errors='replace').rstrip('\0').split('\0')
        data = {'pid': pid, 'state': tail[0], 'ppid': int(tail[1]), 'stat_pgid': int(tail[2]), 'stat_sid': int(tail[3]), 'start_ticks': int(tail[19]), 'command': command}
        for name, fn in [('getpgid', os.getpgid), ('getsid', os.getsid), ('affinity', lambda p: sorted(os.sched_getaffinity(p)))]:
            try:
                data[name] = fn(pid)
            except OSError as exc:
                data[name + '_error'] = repr(exc)
        try:
            env = dict(part.split('=', 1) for part in (root / 'environ').read_bytes().decode(errors='replace').split('\0') if '=' in part)
            data['environment_selectors'] = {key: env.get(key) for key in SELECTORS}
        except OSError as exc:
            data['environment_error'] = repr(exc)
        return data
    except (OSError, ValueError, IndexError) as exc:
        return {'pid': pid, 'read_error': repr(exc)}


with require_absent.open('x') as stream:
    def write(row):
        stream.write(json.dumps(row) + '\n')
        stream.flush()

    write({'event': 'observer_start', 'time_utc': now(), 'observer_pid': os.getpid(), 'observer_affinity': sorted(os.sched_getaffinity(0)), 'max_observation_seconds': args.seconds, 'interval_seconds': args.interval, 'scope': 'Read-only process metadata; this bound does not bound the controller.'})
    scans = 0
    while time.monotonic() - start < args.seconds:
        receipts, receipt_errors = [], []
        for path in sorted(RAW.glob('*-command.json')):
            try:
                row = json.loads(path.read_text())
                pid = row.get('pid')
                if type(pid) is int:
                    known[pid] = path.name
                receipts.append({'path': path.name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'pid': pid})
            except (OSError, ValueError) as exc:
                receipt_errors.append({'path': path.name, 'error': repr(exc)})
        owned = [process(pid) for pid in sorted(known)]
        groups = set(known)
        groups.update(row['getpgid'] for row in owned if 'getpgid' in row)
        members, unreadable, controllers = [], [], []
        for root in Path('/proc').iterdir():
            if not root.name.isdigit():
                continue
            pid = int(root.name)
            try:
                raw_stat = (root / 'stat').read_text()
                tail = raw_stat[raw_stat.rfind(')') + 2:].split()
                pgid, sid = int(tail[2]), int(tail[3])
                command = (root / 'cmdline').read_bytes()
            except (OSError, ValueError, IndexError) as exc:
                unreadable.append({'pid': pid, 'error': repr(exc)})
                continue
            if pgid in groups or sid in groups:
                members.append({'pid': pid, 'state': tail[0], 'ppid': int(tail[1]), 'pgid': pgid, 'sid': sid, 'start_ticks': int(tail[19])})
            if str(RAW / 'controller.py').encode() in command and pid != os.getpid():
                controllers.append(process(pid))
        write({'event': 'scan', 'time_utc': now(), 'elapsed_seconds': time.monotonic() - start, 'command_receipts': receipts, 'receipt_read_errors': receipt_errors, 'owned': owned, 'owned_group_members': members, 'unreadable_proc_records': unreadable, 'controllers_or_outer_shells': controllers, 'display_socket_exists': Path('/tmp/.X11-unix/X131').exists(), 'display_lock_exists': Path('/tmp/.X131-lock').exists()})
        scans += 1
        if (RAW / 'lane-end.json').exists():
            write({'event': 'observer_stop', 'reason': 'lane_end_receipt_exists', 'time_utc': now(), 'scans': scans, 'wall_seconds': time.monotonic() - start, 'quality_outputs_read': False})
            break
        time.sleep(args.interval)
    else:
        write({'event': 'observer_stop', 'reason': 'independent_observation_bound', 'time_utc': now(), 'scans': scans, 'wall_seconds': time.monotonic() - start, 'quality_outputs_read': False})
print(json.dumps({'observer_output': str(require_absent), 'scans': scans, 'quality_outputs_read': False}))
