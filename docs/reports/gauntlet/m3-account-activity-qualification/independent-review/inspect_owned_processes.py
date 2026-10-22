#!/usr/bin/env python3
"""Inspect only children of the explicitly supplied fake-run driver PID."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

driver, run, output = int(sys.argv[1]), Path(sys.argv[2]).resolve(), Path(sys.argv[3]).resolve()
report = json.loads((run / 'report.json').read_text())
driver_proc = Path('/proc') / str(driver)
driver_cmd = [part.decode() for part in (driver_proc / 'cmdline').read_bytes().split(b'\0') if part]
assert any('test_account_match.py' in part for part in driver_cmd)
driver_cwd = (driver_proc / 'cwd').resolve()
out_arg = driver_cmd[driver_cmd.index('--out') + 1]
assert (driver_cwd / out_arg).resolve() == run
child_path = driver_proc / 'task' / str(driver) / 'children'
if child_path.exists():
    pids = [int(p) for p in child_path.read_text().split()]
    child_method = 'Exact driver proc children file'
else:
    # This execution environment omits the optional proc children file.
    pids = [int(p) for p in subprocess.check_output(['ps', '-o', 'pid=', '--ppid', str(driver)], text=True).split()]
    child_method = 'ps filtered to exact owned driver PPID; proc children file unavailable'
children = []
for pid in pids:
    proc = Path('/proc') / str(pid)
    try:
        args = [a.decode() for a in (proc / 'cmdline').read_bytes().split(b'\0') if a]
        exe = (proc / 'exe').resolve()
        cwd = (proc / 'cwd').resolve()
    except FileNotFoundError:
        continue
    assert cwd in (run.parents[1], run.parents[1] / 'game'), (pid, str(cwd), str(run.parents[1]))
    item = dict(pid=pid, ppid=driver, args=args, exe=str(exe), cwd=str(cwd))
    if 'account_match_probe.gd' in ' '.join(args):
        assert exe == Path('/workspace/tools/godot-4.7.2/Godot_v4.7.2-stable_linux.x86_64')
        item['exe_sha256'] = hashlib.sha256(exe.read_bytes()).hexdigest()
        assert item['exe_sha256'] == report['engine']['sha256']
        item['role'] = 'server' if '--role=server' in args else 'client'
    children.append(item)
native = [item for item in children if 'role' in item]
assert len(native) == 11 and sum(p['role'] == 'server' for p in native) == 1
server = next(item for item in native if item['role'] == 'server')
proc = Path('/proc') / str(server['pid'])
socket_inodes = set()
for fd in (proc / 'fd').iterdir():
    try:
        link = str(fd.readlink())
    except FileNotFoundError:
        continue
    if link.startswith('socket:['):
        socket_inodes.add(link[8:-1])
bindings = []
for protocol in ('udp', 'udp6'):
    for line in (proc / 'net' / protocol).read_text().splitlines()[1:]:
        columns = line.split()
        if columns[9] in socket_inodes and int(columns[1].split(':')[1], 16) == report['game_port']:
            bindings.append(dict(protocol=protocol, local_hex=columns[1], remote_hex=columns[2], inode=columns[9]))
assert bindings, 'No owned native server UDP socket found'
result = dict(at_utc=datetime.now(timezone.utc).isoformat(), source_commit=report['source_commit'],
              driver_pid=driver, children=children, native_count=len(native),
              game_port=report['game_port'], owned_game_bindings=bindings,
              method=child_method + '; no environment or credential access; socket inode filter')
output.write_text(json.dumps(result, indent=2) + '\n')
print('Independent live native inspection:', len(native), 'processes;', bindings, flush=True)
