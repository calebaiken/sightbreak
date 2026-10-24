#!/usr/bin/env python3
"""Own a matrix command's descendants before it can spawn any processes.

Windows uses a non-inheritable Job Object, including the supervisor itself.
Linux uses a child subreaper, so setsid/double-fork children cannot disappear
when the command exits. Other POSIX hosts fail closed rather than claim that
a process group alone contains detached descendants. No third-party modules.
"""
import argparse
import ctypes
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import uuid

CLEANUP_TIMEOUT = 5


class WindowsJob:
    """A parent-held guard; the supervisor joins this job before Popen."""
    def __init__(self, name=None):
        from ctypes import wintypes as w

        class Limits(ctypes.Structure):
            _fields_ = [('per_process', ctypes.c_int64), ('per_job', ctypes.c_int64),
                        ('flags', w.DWORD), ('min_working_set', ctypes.c_size_t),
                        ('max_working_set', ctypes.c_size_t), ('active_limit', w.DWORD),
                        ('affinity', ctypes.c_size_t), ('priority', w.DWORD),
                        ('scheduling', w.DWORD)]

        class ExtendedLimits(ctypes.Structure):
            _fields_ = [('basic', Limits), ('io', ctypes.c_uint64 * 6),
                        ('process_memory', ctypes.c_size_t), ('job_memory', ctypes.c_size_t),
                        ('peak_process_memory', ctypes.c_size_t), ('peak_job_memory', ctypes.c_size_t)]

        class Accounting(ctypes.Structure):
            _fields_ = [('times', ctypes.c_int64 * 4), ('faults', w.DWORD),
                        ('total', w.DWORD), ('active', w.DWORD), ('terminated', w.DWORD)]

        self.api = ctypes.WinDLL('kernel32', use_last_error=True)
        signatures = {
            'CreateJobObjectW': ([ctypes.c_void_p, w.LPCWSTR], w.HANDLE),
            'OpenJobObjectW': ([w.DWORD, w.BOOL, w.LPCWSTR], w.HANDLE),
            'SetInformationJobObject': ([w.HANDLE, ctypes.c_int, ctypes.c_void_p, w.DWORD], w.BOOL),
            'QueryInformationJobObject': ([w.HANDLE, ctypes.c_int, ctypes.c_void_p, w.DWORD, ctypes.c_void_p], w.BOOL),
            'AssignProcessToJobObject': ([w.HANDLE, w.HANDLE], w.BOOL),
            'TerminateJobObject': ([w.HANDLE, w.UINT], w.BOOL),
            'SetHandleInformation': ([w.HANDLE, w.DWORD, w.DWORD], w.BOOL),
            'CloseHandle': ([w.HANDLE], w.BOOL),
            'GetCurrentProcess': ([], w.HANDLE),
        }
        for function, (arguments, result) in signatures.items():
            getattr(self.api, function).argtypes = arguments
            getattr(self.api, function).restype = result
        self.accounting = Accounting
        self.handle = None
        self.name = name or ('Local\\SightbreakMatrix-' + uuid.uuid4().hex)
        try:
            if name is None:
                self.handle = self.api.CreateJobObjectW(None, self.name)
                self.require(self.handle)
                if ctypes.get_last_error() == 183:
                    raise RuntimeError('matrix Job Object already exists')
                limits = ExtendedLimits()
                limits.basic.flags = 0x2000  # KILL_ON_JOB_CLOSE, no breakaway flags.
                self.require(self.api.SetInformationJobObject(
                    self.handle, 9, ctypes.byref(limits), ctypes.sizeof(limits)))
            else:
                self.handle = self.api.OpenJobObjectW(0x1 | 0x4 | 0x8, False, name)
                self.require(self.handle)
            self.require(self.api.SetHandleInformation(self.handle, 1, 0))
        except BaseException:
            self.close()
            raise

    @staticmethod
    def require(success):
        if not success:
            raise ctypes.WinError(ctypes.get_last_error())

    def join(self):
        self.require(self.api.AssignProcessToJobObject(self.handle, self.api.GetCurrentProcess()))

    def active(self):
        accounting = self.accounting()
        self.require(self.api.QueryInformationJobObject(
            self.handle, 1, ctypes.byref(accounting), ctypes.sizeof(accounting), None))
        return accounting.active

    def stop(self):
        self.require(self.api.TerminateJobObject(self.handle, 1))
        deadline = time.monotonic() + CLEANUP_TIMEOUT
        while self.active():
            if time.monotonic() >= deadline:
                raise RuntimeError('Job Object descendants did not terminate')
            time.sleep(.01)

    def close(self):
        if self.handle:
            handle, self.handle = self.handle, None
            self.require(self.api.CloseHandle(handle))


def posix_children(pid=None):
    pid = os.getpid() if pid is None else pid
    return [int(value) for value in Path(f'/proc/{pid}/task/{pid}/children').read_text().split()]


def enable_subreaper():
    if not sys.platform.startswith('linux'):
        raise RuntimeError('verified descendant ownership requires Linux /proc + child subreaper on POSIX')
    libc = ctypes.CDLL(None, use_errno=True)
    libc.prctl.argtypes = [ctypes.c_int, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong]
    libc.prctl.restype = ctypes.c_int
    if libc.prctl(36, 1, 0, 0, 0):  # PR_SET_CHILD_SUBREAPER
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error))
    posix_children()  # Fail before launching anything if ownership cannot be audited.


def posix_children_alive():
    """Reap already-exited adoptees; zero from waitpid means live children."""
    while True:
        try:
            pid, _ = os.waitpid(-1, os.WNOHANG)
        except ChildProcessError:
            return False
        if pid == 0:
            return True


def kill_posix_group(group):
    try:
        os.killpg(group, signal.SIGKILL)
    except ProcessLookupError:
        pass


def cleanup_posix_children():
    deadline = time.monotonic() + CLEANUP_TIMEOUT
    while posix_children_alive():
        for pid in posix_children():
            try:
                group = os.getpgid(pid)
                if group != os.getpgrp():
                    kill_posix_group(group)
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        if time.monotonic() >= deadline:
            raise RuntimeError('subreaper descendants did not terminate')
        time.sleep(.01)


def cleanup_posix_supervisor(process):
    """Signal owned groups even if their leader has already exited."""
    groups = {process.pid}
    pending = [process.pid]
    seen = set()
    while pending:
        pid = pending.pop()
        if pid in seen:
            continue
        seen.add(pid)
        try:
            pending.extend(posix_children(pid))
            group = os.getpgid(pid)
            if group != os.getpgrp():
                groups.add(group)
        except ProcessLookupError:
            pass
        except FileNotFoundError:
            pass
    for group in groups:
        kill_posix_group(group)
    process.wait(timeout=CLEANUP_TIMEOUT)


def harness_error(log, error):
    log.write('\nHARNESS_ERROR ' + str(error) + '\n')
    log.flush()


def run_process(command, *, cwd, env, log, result_path, timeout):
    """Return the actual command exit, only after bounded descendant cleanup.

    The parent retains a Job Object handle for cleanup even if the supervisor
    crashes. Neither handle is inheritable. Missing/invalid receipts, launch,
    timeout, and cleanup failures always leave HARNESS_ERROR in the raw log.
    """
    job = process = None
    errors = []
    code = 1
    try:
        if result_path.exists():
            raise FileExistsError('refusing to overwrite process receipt: ' + str(result_path))
        arguments = [sys.executable, '-B', str(Path(__file__).resolve()),
                     '--result', str(result_path.resolve()), '--timeout', str(timeout)]
        if os.name == 'nt':
            job = WindowsJob()
            arguments += ['--windows-job', job.name]
        arguments += ['--', *map(str, command)]
        process = subprocess.Popen(arguments, cwd=cwd, env=env, stdout=log,
                                   stderr=subprocess.STDOUT, close_fds=True,
                                   **({'start_new_session': True} if os.name != 'nt' else {}))
        process.wait(timeout=timeout + 3 * CLEANUP_TIMEOUT)
        if process.returncode != 0:
            errors.append('process supervisor exited ' + str(process.returncode))
        receipt = json.loads(result_path.read_text(encoding='utf-8'))
        if (not isinstance(receipt, dict) or receipt.get('complete') is not True
                or type(receipt.get('exit')) is not int
                or not isinstance(receipt.get('errors'), list)
                or any(not isinstance(error, str) for error in receipt['errors'])):
            raise RuntimeError('invalid process-supervisor receipt')
        code = receipt['exit']
        errors.extend(receipt['errors'])
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as error:
        errors.append(str(error))
    finally:
        if job is not None:
            try:
                if process is not None and process.poll() is not None and job.active():
                    errors.append('descendants survived the process supervisor')
                job.stop()
            except (OSError, RuntimeError) as error:
                errors.append('Job Object cleanup failed: ' + str(error))
            finally:
                try:
                    job.close()
                except (OSError, RuntimeError) as error:
                    errors.append('Job Object close failed: ' + str(error))
        if process is not None:
            try:
                if os.name == 'nt':
                    if process.poll() is None:  # Assignment may have failed before joining the job.
                        process.kill()
                    process.wait(timeout=CLEANUP_TIMEOUT)
                else:
                    if process.poll() is not None:
                        try:
                            os.killpg(process.pid, 0)
                        except ProcessLookupError:
                            pass
                        else:
                            errors.append('process group survived the process supervisor')
                    cleanup_posix_supervisor(process)
            except (OSError, RuntimeError, subprocess.SubprocessError) as error:
                errors.append('supervisor cleanup failed: ' + str(error))
        for error in errors:
            harness_error(log, error)
    return code


def supervise(command, result_path, timeout, windows_job=None):
    """Run only after joining the containment boundary; never assign after spawn."""
    code = 1
    errors = []
    job = None
    owned = False
    try:
        if os.name == 'nt':
            if not windows_job:
                raise RuntimeError('supervisor requires a parent-owned Job Object')
            job = WindowsJob(windows_job)
            job.join()
        else:
            enable_subreaper()
        owned = True
        process = subprocess.Popen(command, close_fds=True)
        code = process.wait(timeout=timeout)
        if (job.active() > 1 if job is not None else posix_children_alive()):
            errors.append('descendants survived command exit')
    except (OSError, RuntimeError, subprocess.SubprocessError) as error:
        errors.append(str(error))
    finally:
        if owned and job is None:
            try:
                cleanup_posix_children()
            except (OSError, RuntimeError) as error:
                errors.append('descendant cleanup failed: ' + str(error))
        if job is not None:
            try:
                job.close()
            except (OSError, RuntimeError) as error:
                errors.append('Job Object close failed: ' + str(error))
        for error in errors:
            print('HARNESS_ERROR ' + error, flush=True)
        with result_path.open('x', encoding='utf-8') as result:
            json.dump({'complete': True, 'exit': code, 'errors': errors}, result, indent=2)
            result.write('\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--result', type=Path, required=True)
    parser.add_argument('--timeout', type=float, required=True)
    parser.add_argument('--windows-job')
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ['--'] else args.command
    if not command or args.timeout <= 0:
        parser.error('a command and positive timeout are required')
    supervise(command, args.result, args.timeout, args.windows_job)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
