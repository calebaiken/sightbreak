#!/usr/bin/env python3
"""Isolate actual headless ENet smoke cleanup; do not create PID1 zombies."""
import argparse
import ctypes
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time


def group_members(group):
    result = []
    for path in Path('/proc').glob('[0-9]*/stat'):
        try:
            content = path.read_text()
            fields = content.rsplit(')', 1)[1].split()
            if int(fields[2]) != group:
                continue
            result.append({'pid': int(path.parent.name), 'state': fields[0], 'ppid': int(fields[1]),
                           'group': int(fields[2]), 'session': int(fields[3]),
                           'exit_status_raw': int(fields[49]), 'command': content.split('(', 1)[1].rsplit(')', 1)[0]})
        except (OSError, ValueError, IndexError):
            continue
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--script', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--terminate-after', type=float)
    parser.add_argument('--terminate-client-after', type=float)
    parser.add_argument('--stop-server', action='store_true')
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(exist_ok=False)
    # Adopt the baseline shell's abandoned children so this diagnostic can reap
    # them itself. The parent chain is recorded, not presented as production.
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.prctl(36, 1, 0, 0, 0) != 0:
        raise OSError(ctypes.get_errno(), 'PR_SET_CHILD_SUBREAPER failed')
    script = args.script.resolve()
    (out / 'tmp').mkdir()
    env = dict(os.environ, SIGHTBREAK_STATE_DIR=str(out / 'state'), TMPDIR=str(out / 'tmp'))
    record = {'command': ['bash', str(script)], 'script_sha256': hashlib.sha256(script.read_bytes()).hexdigest(),
              'scope': 'Actual source headless local ENet smoke; subreaper isolates cleanup diagnosis; no exported/graphical/internet-security acceptance',
              'subreaper_pid': os.getpid()}
    started = time.monotonic()
    process = None
    try:
        with (out / 'console.log').open('w') as log:
            process = subprocess.Popen(record['command'], env=env, stdout=log, stderr=subprocess.STDOUT,
                                       start_new_session=True)
            record['group'] = process.pid
            if args.stop_server:
                time.sleep(.5)
                for child in group_members(process.pid):
                    cmdline = (Path('/proc') / str(child['pid']) / 'cmdline').read_bytes().split(b'\0')
                    if child['ppid'] == process.pid and b'--server' in cmdline:
                        record['external_server_stall'] = {'signal': 'SIGSTOP', **child,
                            'command': [arg.decode(errors='replace') for arg in cmdline if arg],
                            'seconds': time.monotonic() - started}
                        os.kill(child['pid'], signal.SIGSTOP)
                        break
                else:
                    raise RuntimeError('No owned actual network server was observed for the stall control')
            if args.terminate_after is not None:
                time.sleep(args.terminate_after)
                record['external_interruption'] = {'signal': 'SIGTERM', 'pid': process.pid,
                                                   'seconds': time.monotonic() - started}
                os.kill(process.pid, signal.SIGTERM)
            elif args.terminate_client_after is not None:
                time.sleep(args.terminate_client_after)
                for child in group_members(process.pid):
                    cmdline = (Path('/proc') / str(child['pid']) / 'cmdline').read_bytes().split(b'\0')
                    if child['ppid'] == process.pid and any(b'network_probe.gd' in arg for arg in cmdline) and b'--server' not in cmdline:
                        record['external_client_failure'] = {'signal': 'SIGTERM', **child,
                            'command': [arg.decode(errors='replace') for arg in cmdline if arg],
                            'seconds': time.monotonic() - started}
                        os.kill(child['pid'], signal.SIGTERM)
                        break
                else:
                    raise RuntimeError('No owned actual network client was observed for the negative control')
            record['shell_exit'] = process.wait(timeout=35)
            record['shell_elapsed_seconds'] = time.monotonic() - started
            time.sleep(.25)
            record['members_after_shell_exit'] = group_members(process.pid)
    except Exception as error:
        record['error'] = str(error)
    finally:
        if process is not None:
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=5)
            until = time.monotonic() + 5
            reaped = []
            while time.monotonic() < until:
                while True:
                    try:
                        pid, status = os.waitpid(-1, os.WNOHANG)
                    except ChildProcessError:
                        pid = 0
                    if not pid:
                        break
                    reaped.append({'pid': pid, 'wait_status_raw': status})
                members = group_members(process.pid)
                if not members:
                    break
                for member in members:
                    if member['state'] != 'Z':
                        try:
                            os.kill(member['pid'], signal.SIGKILL)
                        except ProcessLookupError:
                            pass
                time.sleep(.1)
            record['adopted_children_reaped_by_diagnostic'] = reaped
            record['members_after_diagnostic_cleanup'] = group_members(process.pid)
        record['elapsed_seconds'] = time.monotonic() - started
        (out / 'results.json').write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps(record, indent=2))
    return int(bool(record.get('error') or record.get('members_after_diagnostic_cleanup')))


if __name__ == '__main__':
    raise SystemExit(main())
