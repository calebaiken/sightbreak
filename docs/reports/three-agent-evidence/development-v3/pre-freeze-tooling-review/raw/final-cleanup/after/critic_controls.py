"""Read-only, serial controls of the reviewed process helper contracts.

No engine, editor, campaign, export, database or service is launched. The sole
real tree contains two approved-CPython processes and naturally ends in 2 s.
Linux process operations are entirely mocked on this Windows review host.
"""
import ctypes
from ctypes import wintypes
import io
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
from unittest.mock import Mock, patch


APPROVED = Path(r'C:\Users\blith\AppData\Local\Temp\opencode\sightbreak-tools\python\cpython-3.13.15-windows-x86_64-none\python.exe')
ROOT = Path(r'C:\Users\blith\AppData\Local\Temp\opencode\sightbreak-v3')
OUT = Path(__file__).resolve().parent
assert Path(sys.executable).resolve() == APPROVED.resolve(), sys.executable
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / 'scripts'))

import godot_process
import matrix_process


def save(name, record):
    with (OUT / (name + '.json')).open('x', encoding='utf-8') as stream:
        json.dump(record, stream, indent=2)
        stream.write('\n')
    print(json.dumps({'control': name, **record}), flush=True)


def windows_dead_root():
    assert os.name == 'nt'
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    kernel.WaitForSingleObject.restype = wintypes.DWORD
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle.restype = wintypes.BOOL
    pid_path = OUT / 'windows-owned-grandchild.json'
    started_path = OUT / 'windows-owned-grandchild-started'
    finished_path = OUT / 'windows-owned-grandchild-finished'
    leaf = ('from pathlib import Path; import os,time; '
            f'Path({str(started_path)!r}).write_text(str(os.getpid())); '
            'time.sleep(2); '
            f'Path({str(finished_path)!r}).write_text("naturally finished")')
    body = ('from pathlib import Path; import json,subprocess,sys,time; '
            f'p=subprocess.Popen([sys.executable,"-B","-c",{leaf!r}], '
            'stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); '
            f'Path({str(pid_path)!r}).write_text(json.dumps({{"pid":p.pid}})); '
            f'marker=Path({str(started_path)!r}); '
            '\nwhile not marker.exists(): time.sleep(.005)\n')
    argv = [str(APPROVED), '-B', '-c', body]
    with (OUT / 'windows-root.log').open('x', encoding='utf-8') as log:
        root = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=log,
                                stderr=subprocess.STDOUT, **godot_process.process_group_options())
        root.wait(timeout=10)
        pid = json.loads(pid_path.read_text())['pid']
        handle = kernel.OpenProcess(0x00100000, False, pid)  # SYNCHRONIZE only; no kill rights.
        if not handle:
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            before = kernel.WaitForSingleObject(handle, 0)
            with patch.object(godot_process.subprocess, 'run', side_effect=AssertionError('unexpected taskkill')) as taskkill:
                errors = godot_process.cleanup_processes([('owned-root', root)])
            after = kernel.WaitForSingleObject(handle, 0)
            final_wait = kernel.WaitForSingleObject(handle, 5000)
        finally:
            if not kernel.CloseHandle(handle):
                raise ctypes.WinError(ctypes.get_last_error())
    record = {'platform': sys.platform, 'root_pid': root.pid, 'root_exit': root.returncode,
              'grandchild_pid': pid, 'alive_before_cleanup': before == 258,
              'alive_after_successful_cleanup': after == 258, 'cleanup_errors': errors,
              'taskkill_call_count': taskkill.call_count,
              'grandchild_naturally_finished_and_handle_signalled': final_wait == 0 and finished_path.is_file(),
              'root_command': argv, 'grandchild_command': [str(APPROVED), '-B', '-c', leaf]}
    save('control-windows-exited-root', record)
    assert record['alive_before_cleanup'] and record['alive_after_successful_cleanup']
    assert errors == [] and record['grandchild_naturally_finished_and_handle_signalled']


def linux_dead_supervisor():
    # Kernel model after a supervisor has died: its /proc entry and PGID no
    # longer exist, while an owned setsid child was reparented to an outer
    # subreaper/init. This is not a live Linux test or a native runtime claim.
    dead_pid, detached_pid = 41000, 41001
    attempted_groups, inspected_pids = [], []
    state = {'detached_child_alive': True}
    process = Mock(pid=dead_pid, returncode=-9)
    process.wait.return_value = -9
    process.poll.return_value = -9
    def children(pid):
        inspected_pids.append(pid)
        if pid == dead_pid:
            raise FileNotFoundError('/proc/' + str(pid) + '/task/' + str(pid) + '/children')
        return []
    def killpg(group, sig):
        attempted_groups.append([group, sig])
        if group == dead_pid:
            raise ProcessLookupError('dead supervisor group has no members')
        if group == detached_pid and sig:
            state['detached_child_alive'] = False
    fake_os = SimpleNamespace(name='posix', killpg=killpg, getpgrp=lambda: 49999,
                              getpgid=lambda pid: detached_pid)
    receipt = OUT / 'linux-dead-supervisor.process.json'
    assert not receipt.exists()
    raw = io.StringIO()
    with patch.object(matrix_process, 'os', fake_os), \
            patch.object(matrix_process, 'signal', SimpleNamespace(SIGKILL=9)), \
            patch.object(matrix_process, 'posix_children', side_effect=children), \
            patch.object(matrix_process.subprocess, 'Popen', return_value=process) as popen:
        code = matrix_process.run_process(['not-executed'], cwd=ROOT, env={}, log=raw,
                                          result_path=receipt, timeout=1)
    with (OUT / 'linux-dead-supervisor.log').open('x', encoding='utf-8') as log:
        log.write(raw.getvalue())
    record = {'kind': 'pure mock of Linux kernel state; no actual POSIX process or signal',
              'returned_exit': code, 'raw_log_has_harness_error': 'HARNESS_ERROR' in raw.getvalue(),
              'inspected_pids': inspected_pids, 'attempted_group_signals': attempted_groups,
              'detached_pid': detached_pid, **state,
              'popen_was_mocked': True, 'mock_popen_call_count': popen.call_count,
              'boundary': 'fails evidence gate but leaves no owner able to discover detached process after supervisor death'}
    save('control-linux-dead-supervisor', record)
    assert code != 0 and state['detached_child_alive'] and 'HARNESS_ERROR' in raw.getvalue()
    assert all(group != detached_pid for group, sig in attempted_groups)


def windows_taskkill_race():
    # If taskkill fails and the root exits during the attempt, cleanup treats
    # the race as success without asserting anything about its descendants.
    process = Mock(pid=42000)
    process.poll.side_effect = [None, 0]
    process.wait.return_value = 0
    with patch.object(godot_process, 'is_windows', return_value=True), \
            patch.object(godot_process.subprocess, 'run', return_value=Mock(returncode=128)) as taskkill:
        errors = godot_process.cleanup_processes([('fixture-root', process)])
    record = {'kind': 'pure mock; no taskkill launched', 'taskkill_returncode': 128,
              'root_poll_results': [None, 0], 'cleanup_errors': errors,
              'root_kill_call_count': process.kill.call_count,
              'taskkill_call_count': taskkill.call_count}
    save('control-windows-taskkill-race', record)
    assert errors == []


if __name__ == '__main__':
    windows_dead_root()
    linux_dead_supervisor()
    windows_taskkill_race()
