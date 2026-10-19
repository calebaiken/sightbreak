"""Portable native-probe launches, cleanup and frozen-source evidence gates."""
import hashlib
import ntpath
import os
from pathlib import Path
import signal
import subprocess
import sys

import native_log

ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATHS = ('game', 'scripts', 'backend', 'server', '.github', '.gitignore', 'README.md')


def is_windows():
    return os.name == 'nt'


def godot_command(arguments, *, root=ROOT, env=None):
    """Keep the POSIX wrapper; Windows must execute the native binary, not .sh.

    GODOT_BIN is one executable path, never shell text. In particular, paths and
    probe arguments containing spaces must remain individual argv elements.
    """
    env = os.environ if env is None else env
    if not is_windows():
        return [str(root / 'scripts/godot.sh'), *map(str, arguments)]
    tools = Path(env.get('SIGHTBREAK_TOOLS_DIR') or root.parent / 'tools')
    binary = env.get('GODOT_BIN') or str(tools / 'godot-4.7.2/Godot_v4.7.2-stable_win64.exe')
    candidate = Path(binary)
    if not candidate.is_absolute() and not ntpath.isabs(binary):
        candidate = root / candidate
    if candidate.suffix.lower() != '.exe' or not candidate.is_file():
        raise FileNotFoundError('Set GODOT_BIN to an existing native Godot Windows .exe: ' + binary)
    return [str(candidate), '--path', str(root / 'game'), *map(str, arguments)]


def godot_environment(*, root=ROOT, env=None):
    """Mirror godot.sh state directories, including native Windows user data."""
    child = dict(os.environ if env is None else env)
    state = Path(child.get('SIGHTBREAK_STATE_DIR') or root / '.local')
    if not state.is_absolute():
        state = root / state
    for variable, directory in (('XDG_DATA_HOME', 'data'), ('XDG_CONFIG_HOME', 'config'),
                                ('XDG_CACHE_HOME', 'cache'), ('ANDROID_USER_HOME', 'android')):
        path = state / directory
        path.mkdir(parents=True, exist_ok=True)
        child[variable] = str(path)
    if is_windows():
        # Godot's Windows user:// implementation uses APPDATA rather than XDG.
        child['APPDATA'] = child['XDG_DATA_HOME']
        child['LOCALAPPDATA'] = child['XDG_CACHE_HOME']
    return child


def process_group_options():
    """Every managed child owns a group so aborts cannot kill this harness."""
    if is_windows():
        return {'creationflags': getattr(subprocess, 'CREATE_NEW_PROCESS_GROUP', 0x200)}
    return {'start_new_session': True}


def _posix_process_groups(pid):
    """Include descendants that opened their own sessions (nested harnesses)."""
    groups = {pid}
    try:
        listing = subprocess.check_output(['ps', '-A', '-o', 'pid=,ppid='], text=True, timeout=5)
        parents = dict(tuple(map(int, line.split())) for line in listing.splitlines() if line.strip())
        descendants = {pid}
        while True:
            found = {child for child, parent in parents.items() if parent in descendants}
            if found <= descendants:
                break
            descendants.update(found)
        own_group = os.getpgrp()
        for child in descendants:
            try:
                group = os.getpgid(child)
                if group != own_group:
                    groups.add(group)
            except ProcessLookupError:
                pass
    except (OSError, subprocess.SubprocessError, ValueError):
        # Minimal POSIX systems without ps still get owned-process-group cleanup.
        pass
    return groups


def terminate_process_tree(process, timeout=5):
    """Reap a managed child and kill its tree, not just the wrapper process.

    Windows taskkill /T must run while the root is alive. POSIX also signals an
    exited leader's group, and snapshots nested groups before terminating it.
    """
    if is_windows():
        if process.poll() is None:
            try:
                result = subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'],
                                        stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
                                        check=False, timeout=timeout)
            except (OSError, subprocess.TimeoutExpired) as error:
                process.kill()
                process.wait(timeout=timeout)
                raise RuntimeError('taskkill unavailable; complete process-tree cleanup could not be verified') from error
            if result.returncode and process.poll() is None:
                process.kill()
                process.wait(timeout=timeout)
                raise RuntimeError('taskkill could not terminate the complete process tree: ' + str(process.pid))
        process.wait(timeout=timeout)
        return
    try:
        os.killpg(process.pid, 0)
    except ProcessLookupError:
        process.wait(timeout=timeout)
        return
    groups = _posix_process_groups(process.pid)
    try:
        for group in groups:
            try:
                os.killpg(group, signal.SIGTERM)
            except ProcessLookupError:
                pass
        try:
            process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            pass
    finally:
        # A parent exiting on TERM is not evidence that its children exited.
        for group in groups:
            try:
                os.killpg(group, signal.SIGKILL)
            except ProcessLookupError:
                pass
        process.wait(timeout=timeout)


def cleanup_processes(processes):
    failures = []
    for name, process in reversed(processes):
        try:
            terminate_process_tree(process)
        except (OSError, RuntimeError, subprocess.SubprocessError) as error:
            failures.append(str(name) + ': cleanup failed: ' + str(error))
    return failures


def prepare_output(path):
    """A run may use a new or empty directory, never earlier evidence."""
    path = path.resolve()
    path.mkdir(parents=True, exist_ok=True)
    if any(path.iterdir()):
        raise FileExistsError('refusing to overwrite evidence; output directory must be empty: ' + str(path))
    return path


def source_snapshot(*, root=ROOT):
    """Hash exact source bytes, including probes/harnesses and untracked source.

    Runtime/import caches and evidence ignored by Git do not become source.
    Deleted tracked files are represented too; a dirty boolean alone cannot
    distinguish two different edits made during the same run.
    """
    def git(*arguments):
        return subprocess.check_output(['git', *arguments], cwd=root, text=True,
                                       encoding='utf-8', errors='surrogateescape').rstrip('\n')

    # An exact frozen checkout also excludes staged/untracked documentation or
    # other non-runtime edits. Hash the declared source inventory below, but do
    # not let a narrower path filter turn a dirty checkout into clean evidence.
    status = git('status', '--porcelain=v1', '--untracked-files=all')
    files = sorted(set(git('ls-files', '-z', '--cached', '--others', '--exclude-standard',
                          '--', *SOURCE_PATHS).split('\0')) - {''})
    digest = hashlib.sha256()
    for relative in files:
        path = root / relative
        if path.is_symlink():
            content = b'symlink\0' + os.fsencode(os.readlink(path))
        elif path.is_file():
            content = b'file\0' + hashlib.sha256(path.read_bytes()).digest()
        else:
            content = b'missing'
        digest.update(relative.encode('utf-8', 'surrogateescape') + b'\0' + content + b'\0')
    return {'commit': git('rev-parse', 'HEAD'), 'game_tree': git('rev-parse', 'HEAD:game'),
            'dirty': bool(status), 'status': status, 'content_sha256': digest.hexdigest(),
            'source_paths': list(SOURCE_PATHS), 'source_files': len(files)}


def source_failures(before, after):
    failures = []
    if before.get('dirty'):
        failures.append('source was not clean before run')
    if after.get('dirty'):
        failures.append('source was not clean after run')
    if before != after:
        failures.append('source changed during run')
    return failures


def native_process_failures(processes, directory):
    failures = []
    for name, process in processes:
        if process.poll() != 0:
            failures.append(name + ': exit ' + str(process.poll()))
        path = directory / (name + '.log')
        if not path.is_file():
            failures.append(name + ': missing native log')
        else:
            text = path.read_text(encoding='utf-8', errors='replace')
            if native_log.failed(text) or 'ERROR:' in text or 'SCRIPT ERROR' in text:
                failures.append(name + ': logged error or resource leak')
    return failures


def resource_measurement():
    if sys.platform.startswith('linux') and Path('/proc').is_dir():
        return {'available': True, 'method': 'Linux /proc RSS KiB and process CPU seconds'}
    return {'available': False, 'method': None,
            'reason': 'Process RSS/CPU sampling is only implemented for Linux /proc; values are null, not zero.'}


def sample_process_resources(pid):
    if not resource_measurement()['available']:
        return None
    try:
        status = Path(f'/proc/{pid}/status').read_text()
        rss = next(int(line.split()[1]) for line in status.splitlines() if line.startswith('VmRSS:'))
        stat = Path(f'/proc/{pid}/stat').read_text().rsplit(')', 1)[1].split()
        cpu = (int(stat[11]) + int(stat[12])) / os.sysconf('SC_CLK_TCK')
        return {'rss_current_kib': rss, 'cpu_seconds': cpu}
    except (OSError, StopIteration, ValueError, IndexError):
        return None
