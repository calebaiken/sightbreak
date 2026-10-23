#!/usr/bin/env python3
"""One preregistered acquisition; execute only after exact-source lane release.

No retry/fallback. Diagnostic text packaging does not qualify stock performance.
The accepted fixture/controller is invoked unchanged as a separate process.
"""
import argparse
from contextlib import contextmanager
from copy import deepcopy
import fcntl
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import signal
import subprocess
import sys
import time
import zipfile

import linux_profile_overhead as accepted
import linux_profile_payload as payload
import toolchain

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / 'docs/reports/gauntlet/m1-linux-profile-acquisition'
OUTPUT = ROOT / 'builds/linux-profile-acquisition-r1'
PINS = REPORT / 'pins.json'
INSTALL = Path('/workspace/tools/godot-4.7.2')
LANE_LOCK = Path('/tmp/sightbreak-linux-profile-overhead.lock')
ACQUISITION_LOCK = Path('/tmp/sightbreak-linux-profile-acquisition.lock')
ACCEPTED = {'scripts/linux_profile_overhead.py': '3d495f74c7799e58616288a8812c29829c45b426ae737fcc73a5712c63782561',
            'scripts/diagnostics/linux_profile_overhead.gd': '1e3f4094f2439a7ae054455c5f7e2ca4a993a15067affebce57e760569ee1dae',
            'scripts/diagnostics/linux_profile_overhead.tscn': 'acc3cd62c2a72005c112014ed24320093d6f772d5c0f459cda5f24e3cf05fe61'}
CAPS = {'preflight': 60, 'stage': 45, 'version': 15, 'import': 120, 'import-inventory': 30,
        'export': 120, 'artifact': 60, 'seal': 30, 'block': 750, 'finalize': 60}
WHOLE, CLEANUP, FAILURE_PUBLICATION = 1320, 5, 10
require, digest, read_json, write = accepted.require, accepted.digest, accepted.read_json, accepted.write


def strict_log(text):
    return [line for line in text.splitlines() if re.search(
        r'\b(?:SCRIPT ERROR|Parse Error|ERROR|WARNING)\s*:|\bwarning\b|ObjectDB.*leaked|Leaked instance|resources? still in use|orphan(?:ed)? (?:node|object)',
        line, re.I)]


class Evidence:
    """First validated bytes win. A later observation can only confirm them."""
    def __init__(self, receipt):
        self.rows, self.logs, self.receipt = {}, set(), receipt

    def identity(self, path):
        path = Path(path)
        require(path.is_relative_to(OUTPUT) and path.is_file()
                and not any(part.is_symlink() for part in (path, *path.parents) if part.is_relative_to(OUTPUT)),
                'Missing/unsafe retained evidence: ' + str(path))
        before = path.stat().st_size
        value = {'bytes': before, 'sha256': digest(path)}
        require(path.stat().st_size == before, 'Evidence changed during hash: ' + str(path))
        return value

    def bind(self, path, raw=None, wanted=None, log=False):
        path = Path(path)
        observed = self.identity(path)
        expected = {'bytes': len(raw), 'sha256': payload.sha(raw)} if raw is not None else wanted
        if expected is not None:
            require(all(observed.get(key) == value for key, value in expected.items()),
                    'Retained evidence differs from accepted bytes: ' + str(path))
        name = path.relative_to(OUTPUT).as_posix()
        require(name not in self.rows or self.rows[name] == observed,
                'Retained evidence identity drift: ' + name)
        self.rows.setdefault(name, observed)
        if log:
            require(not strict_log(path.read_text(errors='replace')), 'Retained strict log drift: ' + name)
            self.logs.add(name)
        return observed

    def json(self, path):
        raw = Path(path).read_bytes()
        value = accepted.strict_json(raw.decode())
        self.bind(path, raw=raw)
        return value

    def publication(self, path, value):
        self.bind(path, raw=(json.dumps(value, indent=2, allow_nan=False) + '\n').encode())

    def validate(self, closed=False):
        # No rebinding and no fresh baseline: compare with every original gate.
        for name, wanted in self.rows.items():
            path = OUTPUT / name
            require(self.identity(path) == wanted, 'Retained evidence identity drift: ' + name)
            if name in self.logs:
                require(not strict_log(path.read_text(errors='replace')), 'Retained strict log drift: ' + name)
        if closed:
            paths = list(OUTPUT.rglob('*'))
            require(not any(path.is_symlink() for path in paths), 'Unexpected output symlink')
            require({path.relative_to(OUTPUT).as_posix() for path in paths if path.is_file()} == set(self.rows),
                    'Retained output set changed during publication')

    def close_outputs(self):
        self.validate()
        require(not (OUTPUT / 'outputs.json').exists() and not (OUTPUT / 'overall.json').exists(),
                'Preserve existing final publications')
        for path in sorted(OUTPUT.rglob('*')):
            require(not path.is_symlink(), 'Unexpected output symlink')
            if path.is_file():
                self.bind(path)
        self.validate(closed=True)
        return deepcopy(self.rows)


class Budget:
    """One original whole deadline; phase timers always use its remaining time."""
    def __init__(self, receipt):
        self.receipt, self.started = receipt, time.monotonic()
        self.evidence = Evidence(receipt)
        self.until = self.started + WHOLE
        self.phase_until = self.until
        receipt.update(start_monotonic=self.started, whole_deadline_monotonic=self.until,
                       whole_cap_seconds=WHOLE, phases=[])

    def check(self, stage):
        now = time.monotonic()
        self.receipt.update(last_observation=stage, end_monotonic=now, elapsed_seconds=now - self.started)
        if now >= min(self.until, self.phase_until):
            raise TimeoutError('Acquisition deadline: ' + stage)

    @contextmanager
    def armed(self, until, label):
        require(signal.getitimer(signal.ITIMER_REAL) == (0.0, 0.0), 'Existing real-time alarm')
        old = signal.getsignal(signal.SIGALRM)
        def expired(_signal, _frame):
            raise TimeoutError('Acquisition alarm: ' + label)
        signal.signal(signal.SIGALRM, expired)
        try:
            remaining = until - time.monotonic()
            if remaining <= 0:
                raise TimeoutError('Acquisition deadline before ' + label)
            signal.setitimer(signal.ITIMER_REAL, remaining)
            yield
            if time.monotonic() >= until:
                raise TimeoutError('Acquisition deadline after ' + label)
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, old)

    def phase(self, name, operation):
        started = self.started if name == 'preflight' else time.monotonic()
        self.phase_until = min(started + CAPS[name], self.until)
        row = {'name': name, 'cap_seconds': CAPS[name], 'started_monotonic': started,
               'deadline_monotonic': self.phase_until, 'passed': False}
        self.receipt['phases'].append(row)
        try:
            with self.armed(self.phase_until, name):
                self.check(name + ':entry')
                value = operation()
                self.check(name + ':operations complete')
                row['value'] = value
                # Receipt publication and reread are also inside this phase.
                before = deepcopy(row)
                write(OUTPUT / (name + '.phase.json'), before)
                self.check(name + ':published')
                require(read_json(OUTPUT / (name + '.phase.json')) == before, 'Phase publication differs')
                self.evidence.publication(OUTPUT / (name + '.phase.json'), before)
                self.check(name + ':reread')
                row['publication_sha256'] = digest(OUTPUT / (name + '.phase.json'))
                self.check(name + ':receipt hashed')
            self.check(name + ':alarm restored')
            row['passed'] = True
            return value
        except (Exception, KeyboardInterrupt) as error:
            row.update(error=str(error), error_type=type(error).__name__)
            raise
        finally:
            ended = time.monotonic()
            row.update(ended_monotonic=ended, elapsed_seconds=ended - started)
            self.phase_until = self.until
            if row['passed'] and ended >= row['deadline_monotonic']:
                row.update(passed=False, error='Acquisition deadline at phase return', error_type='TimeoutError')
                raise TimeoutError(row['error'])


def process_scan():
    result = {}
    for item in Path('/proc').iterdir():
        if not item.name.isdigit():
            continue
        try:
            raw = (item / 'stat').read_text()
            fields = raw[raw.rfind(')') + 2:].split()
            pid = int(item.name)
            result[pid] = {'pid': pid, 'start_ticks': int(fields[19]), 'state': fields[0],
                           'ppid': int(fields[1]), 'pgid': int(fields[2]), 'sid': int(fields[3]),
                           'comm': raw[raw.find('(') + 1:raw.rfind(')')]}
        except (OSError, ValueError, IndexError):
            continue
    return result


def same_identity(row, scan):
    return row['pid'] in scan and scan[row['pid']]['start_ticks'] == row['start_ticks']


def recognized_native():
    found = []
    for pid, row in process_scan().items():
        try:
            executable = os.readlink(f'/proc/{pid}/exe')
        except OSError:
            executable = ''
        if re.search('godot|xvfb|sightbreak', row['comm'] + ' ' + Path(executable).name, re.I):
            found.append({**row, 'exe': executable})
    return found


def signal_identity(row, signum):
    """PID FD binds signal delivery to the revalidated identity, not a reused PID."""
    current = process_scan()
    if not same_identity(row, current):
        return False
    descriptor = os.pidfd_open(row['pid'])
    try:
        if not same_identity(row, process_scan()):
            return False
        signal.pidfd_send_signal(descriptor, signum)
        return True
    except ProcessLookupError:
        return False
    finally:
        os.close(descriptor)


class Ownership:
    def __init__(self, process, receipt):
        self.process, self.receipt, self.known = process, receipt, {}
        scan = process_scan()
        require(process.pid in scan, 'Cannot establish child identity')
        self.root = scan[process.pid]
        require(self.root['pgid'] == self.root['sid'] == process.pid, 'Child lacks its own group/session')
        receipt.update(root_identity=self.root, signals=[], identity_observations=[])
        self.observe(scan)

    def observe(self, scan=None):
        scan = process_scan() if scan is None else scan
        seeds = {row['pid'] for row in self.known.values() if same_identity(row, scan)}
        if same_identity(self.root, scan):
            seeds.add(self.root['pid'])
        # The original session remains in scope; every signal still rechecks an
        # exact observed start identity. No process-name match grants ownership.
        session_anchored = any(same_identity(row, scan) and scan[row['pid']]['sid'] == self.root['sid']
                               for row in (self.root, *self.known.values()))
        if session_anchored:
            seeds.update(pid for pid, row in scan.items() if row['sid'] == self.root['sid'])
        while True:
            added = {pid for pid, row in scan.items() if row['ppid'] in seeds and pid not in seeds}
            if not added:
                break
            seeds.update(added)
        for pid in seeds:
            if pid in scan:
                row = scan[pid]
                self.known.setdefault((pid, row['start_ticks']), row)
        self.receipt['identity_observations'] = sorted(self.known.values(), key=lambda row: (row['pid'], row['start_ticks']))
        return scan

    def cleanup(self):
        started, forced = time.monotonic(), False
        while True:
            self.process.poll()  # Reap the root before the terminal /proc scan.
            scan = self.observe()
            remaining = [scan[row['pid']] for row in self.known.values() if same_identity(row, scan)]
            if not remaining:
                break
            forced = True
            elapsed = time.monotonic() - started
            if elapsed >= CLEANUP:
                break
            signum = signal.SIGKILL if elapsed >= 1 else signal.SIGTERM
            for row in remaining:
                if row['state'] != 'Z' and signal_identity(row, signum):
                    self.receipt['signals'].append({'pid': row['pid'], 'start_ticks': row['start_ticks'],
                                                    'signal': int(signum), 'monotonic': time.monotonic()})
            time.sleep(0.05)
        self.process.poll()
        terminal = self.observe()
        result = {'forced': forced, 'root_reaped': self.process.returncode is not None,
                  'terminal_original_group': [row for row in terminal.values() if row['pgid'] == self.root['pgid']],
                  'terminal_original_session': [row for row in terminal.values() if row['sid'] == self.root['sid']],
                  'terminal_observed_identities': [row for row in self.known.values() if same_identity(row, terminal)],
                  'seconds': time.monotonic() - started}
        result['complete'] = result['root_reaped'] and not any(result[key] for key in (
            'terminal_original_group', 'terminal_original_session', 'terminal_observed_identities'))
        self.receipt['cleanup'] = result
        return result


class Acquisition:
    def __init__(self, commit):
        self.commit = commit
        self.receipt = {'schema': 1, 'passed': False, 'source_commit': commit,
                        'purpose': 'One fixed text-script profiling-cadence acquisition, not shipping/gameplay acceptance',
                        'commands': [], 'cleanup_scope': 'Observed exact PID/start identities, original group/session; unobserved escaped/reparented descendants are outside scope'}
        self.budget, self.counter = Budget(self.receipt), 0
        self.evidence = self.budget.evidence
        self.environment = dict(os.environ)
        self.original = self.stage_record = self.seal = None

    def command(self, label, argv, cwd, environment=None):
        """Called within one active phase; cleanup temporarily owns its own alarm."""
        self.counter += 1
        name = f'{self.counter:02d}-{label}'
        row = {'label': label, 'argv': list(map(str, argv)), 'cwd': str(cwd), 'exit_code': None,
               'started_monotonic': time.monotonic(), 'timeout': False,
               'phase_deadline_monotonic': self.budget.phase_until, 'whole_deadline_monotonic': self.budget.until}
        self.receipt['commands'].append(row)
        process = owner = None
        failure = None
        stdout, stderr = OUTPUT / (name + '.stdout.log'), OUTPUT / (name + '.stderr.log')
        row.update(stdout={'path': str(stdout)}, stderr={'path': str(stderr)})
        try:
            with stdout.open('wb') as out, stderr.open('wb') as err:
                process = subprocess.Popen(row['argv'], cwd=cwd, env=environment or self.environment,
                                           stdout=out, stderr=err, start_new_session=True)
                row['pid'] = process.pid
                owner = Ownership(process, row)
                while True:
                    self.budget.check(name + ':observe')
                    owner.observe()
                    if label in ('import', 'export') and 'actual_tool_libraries' not in row:
                        try:
                            executable = Path(os.readlink(f'/proc/{process.pid}/exe')).resolve()
                        except OSError:
                            executable = None
                        if executable == self.engine:
                            maps = Path(f'/proc/{process.pid}/maps').read_text().splitlines()
                            libraries = {line.split(maxsplit=5)[5] for line in maps
                                         if len(line.split(maxsplit=5)) == 6 and line.split(maxsplit=5)[5].startswith('/')}
                            row['actual_tool_libraries'] = {path: digest(path) for path in sorted(libraries)}
                            self.budget.check(name + ':tool libraries observed')
                    if process.poll() is not None:
                        break
                    time.sleep(0.05)
                self.budget.check(name + ':completed child')
                row['exit_code'] = process.returncode
        except (Exception, KeyboardInterrupt) as error:
            failure = error
            row.update(error=str(error), timeout=isinstance(error, (TimeoutError, subprocess.TimeoutExpired)))
        finally:
            # The phase clock keeps advancing. A dedicated teardown alarm is
            # bounded separately, and the original phase/whole gate is rearmed
            # only with its remaining time afterward; it never restarts a cap.
            signal.setitimer(signal.ITIMER_REAL, 0)
            if owner:
                try:
                    with self.budget.armed(time.monotonic() + CLEANUP, name + ':cleanup'):
                        owner.cleanup()
                except (Exception, KeyboardInterrupt) as error:
                    row['cleanup_error'] = str(error)
                    failure = failure or error
            elif process:
                # An unreaped Popen root is ours even if /proc observation failed.
                # Kill only its newly created group while that unreaped root lives.
                try:
                    if process.poll() is None:
                        os.killpg(process.pid, signal.SIGKILL)
                    process.wait(timeout=CLEANUP)
                except (Exception, KeyboardInterrupt) as error:
                    row['cleanup_error'] = str(error)
                row['cleanup'] = {'complete': False, 'forced': True,
                                  'root_reaped': process.returncode is not None,
                                  'reason': 'Initial PID/start/group/session proof unavailable'}
                failure = failure or accepted.Invalid('Missing child ownership proof')
            remaining = min(self.budget.until, self.budget.phase_until) - time.monotonic()
            if remaining > 0:
                signal.setitimer(signal.ITIMER_REAL, remaining)
            else:
                failure = failure or TimeoutError('Acquisition deadline after cleanup')
            if process:
                row['exit_code'] = process.returncode
            row['ended_monotonic'] = time.monotonic()
            row['elapsed_seconds'] = row['ended_monotonic'] - row['started_monotonic']
        if failure:
            raise failure
        self.budget.check(name + ':before logs')
        out_raw, err_raw = stdout.read_bytes(), stderr.read_bytes()
        out, err = out_raw.decode(errors='replace'), err_raw.decode(errors='replace')
        self.budget.check(name + ':logs read')
        row.update(stdout={'path': str(stdout), 'bytes': stdout.stat().st_size, 'sha256': digest(stdout)},
                   stderr={'path': str(stderr), 'bytes': stderr.stat().st_size, 'sha256': digest(stderr)},
                   log_failures=strict_log(out + '\n' + err), ended_monotonic=time.monotonic())
        self.budget.check(name + ':logs hashed')
        require(row['exit_code'] == 0 and not row['timeout'], 'Command exit/timeout: ' + name)
        require(owner and row['cleanup']['complete'] and not row['cleanup']['forced'], 'Command cleanup: ' + name)
        require(not row['log_failures'], 'Strict native log gate: ' + name)
        if label in ('import', 'export'):
            require(row.get('actual_tool_libraries'), 'Missing actual preparation library evidence')
        self.evidence.bind(stdout, raw=out_raw, log=True)
        self.evidence.bind(stderr, raw=err_raw, log=True)
        return out

    def git(self, *args):
        return self.command('git', [self.git_path, *args], ROOT).strip()

    def sources(self):
        require(self.git('rev-parse', 'HEAD') == self.commit and not self.git('status', '--porcelain', '--untracked-files=all'),
                'Source is not exact and clean')
        rows = []
        for item in self.git('ls-files', '--stage', '-z', '--', 'game', 'scripts').split('\0'):
            if not item:
                continue
            metadata, name = item.split('\t', 1)
            mode, blob, stage = metadata.split()
            path = ROOT / name
            require(stage == '0' and mode in ('100644', '100755') and path.is_file() and not path.is_symlink(),
                    'Missing or unusual tracked source: ' + name)
            raw = path.read_bytes()
            require(hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest() == blob,
                    'Source differs from Git blob: ' + name)
            rows.append({'path': name, 'bytes': len(raw), 'sha256': payload.sha(raw), 'git_blob': blob, 'mode': mode})
        for name, expected in ACCEPTED.items():
            require(digest(ROOT / name) == expected, 'Accepted source changed: ' + name)
        self.budget.check('source inventory')
        return rows

    def host(self):
        result = {'uname': list(os.uname()), 'os_release_sha256': digest('/etc/os-release'),
                  'affinity': sorted(os.sched_getaffinity(0)), 'nice': os.getpriority(os.PRIO_PROCESS, 0),
                  'scheduler': os.sched_getscheduler(0), 'quota': accepted.cgroup_snapshot(os.getpid()),
                  'python': str(Path(sys.executable).resolve()), 'pid': os.getpid(), 'start_ticks': accepted.pid_start(os.getpid())}
        libraries = {line.split(maxsplit=5)[5] for line in Path('/proc/self/maps').read_text().splitlines()
                     if len(line.split(maxsplit=5)) == 6 and line.split(maxsplit=5)[5].startswith('/')}
        result['supervisor_libraries'] = {name: digest(name) for name in sorted(libraries)}
        return result

    def verify_tools(self):
        for row in self.pins['tools']:
            path = Path(row['path'])
            require(path.is_file() and path.stat().st_size == row['bytes'] and digest(path) == row['sha256'], 'Pinned tool changed: ' + str(path))
        install = INSTALL
        members = []
        for archive, expected, selection in (
            (install / 'godot.zip', toolchain.EDITORS['linux'][2], {'Godot_v4.7.2-stable_linux.x86_64': self.engine}),
            (install / 'templates.tpz', toolchain.TEMPLATES_SHA512,
             {'templates/' + name: self.templates / name for name in ('version.txt', 'linux_debug.x86_64', 'linux_release.x86_64')})):
            with archive.open('rb') as stream:
                require(hashlib.file_digest(stream, 'sha512').hexdigest() == expected, 'Official archive SHA-512 differs')
            with zipfile.ZipFile(archive) as bundle:
                require(len(bundle.namelist()) == len(set(bundle.namelist())), 'Duplicate archive member')
                for name, path in selection.items():
                    info = bundle.getinfo(name)
                    require(not info.is_dir() and (info.external_attr >> 16) & 0o170000 != 0o120000, 'Unsafe selected archive member')
                    with bundle.open(name) as stream:
                        actual = hashlib.file_digest(stream, 'sha256').hexdigest()
                    require(actual == digest(path) and info.file_size == path.stat().st_size, 'Installed member differs from official archive')
                    members.append({'archive': str(archive), 'official_sha512': expected, 'member': name,
                                    'bytes': info.file_size, 'sha256': actual})
        self.budget.check('tool archives verified')
        return members

    def preflight(self):
        self.pins = read_json(PINS)
        require(sys.platform == 'linux' and platform.machine() == 'x86_64', 'Native Linux x86_64 required')
        require(re.fullmatch('[0-9a-f]{40}', self.commit), 'Full frozen commit required')
        require(hasattr(os, 'pidfd_open') and hasattr(signal, 'pidfd_send_signal'), 'Exact PID-FD signal support required')
        self.engine = Path('/workspace/tools/godot-4.7.2/Godot_v4.7.2-stable_linux.x86_64')
        self.templates = Path('/workspace/sightbreak/.local/data/godot/export_templates/4.7.2.stable')
        self.python_path, self.git_path = str(Path(sys.executable).resolve()), str(Path(shutil.which('git')).resolve())
        self.xvfb, self.cpus, self.display = '/workspace/tools/xvfb/usr/bin/Xvfb', self.pins['cpus'], self.pins['display']
        require(self.cpus == [0, 1] and set(self.cpus) <= os.sched_getaffinity(0), 'Original selected CPUs unavailable')
        require(self.display == ':99127' and not Path('/tmp/.X11-unix/X99127').exists()
                and not Path('/tmp/.X11-unix/X99127').is_symlink() and not Path('/tmp/.X99127-lock').exists()
                and not Path('/tmp/.X99127-lock').is_symlink(), 'Original selected display unavailable')
        self.receipt['official_members'] = self.verify_tools()
        require(self.python_path in {row['path'] for row in self.pins['tools']}
                and self.git_path in {row['path'] for row in self.pins['tools']}, 'Unpinned Python/git selection')
        self.original = self.sources()
        write(OUTPUT / 'original-before.json', self.original)
        self.evidence.publication(OUTPUT / 'original-before.json', self.original)
        self.receipt['host_before'] = self.host()
        self.receipt['recognized_native_before'] = recognized_native()
        require(not self.receipt['recognized_native_before'], 'Another recognized native engine/display is running')
        require(self.receipt['host_before']['nice'] == 0 and self.receipt['host_before']['scheduler'] == 0, 'Unexpected inherited priority/scheduler')
        private = OUTPUT / 'private-export-state'
        self.environment = {key: os.environ[key] for key in ('HOME', 'USER', 'LOGNAME') if key in os.environ}
        self.environment.update(PATH=os.pathsep.join(dict.fromkeys((str(Path(self.git_path).parent), str(Path(self.python_path).parent), '/usr/bin', '/bin'))),
                                LANG='C.UTF-8', LC_ALL='C.UTF-8', SIGHTBREAK_STATE_DIR=str(private),
                                SIGHTBREAK_BUILDS_DIR=str(OUTPUT / 'export'), LP_NUM_THREADS='2',
                                LIBGL_ALWAYS_SOFTWARE='1', GODOT_SILENCE_ROOT_WARNING='1',
                                ANDROID_USER_HOME=str(private / 'android'), TMPDIR=str(OUTPUT / 'tmp'),
                                MESA_SHADER_CACHE_DIR=str(private / 'mesa'))
        for key, name in (('XDG_DATA_HOME', 'data'), ('XDG_CONFIG_HOME', 'config'), ('XDG_CACHE_HOME', 'cache')):
            self.environment[key] = str(private / name)
        require(str(Path(shutil.which('taskset', path=self.environment['PATH'])).resolve()) == '/usr/bin/taskset', 'Unpinned taskset resolution')
        for name in ('android', 'data', 'config', 'cache', 'mesa'):
            (private / name).mkdir(parents=True, exist_ok=False)
        (OUTPUT / 'tmp').mkdir()
        destination = private / 'data/godot/export_templates/4.7.2.stable'
        destination.mkdir(parents=True)
        for name in ('version.txt', 'linux_debug.x86_64', 'linux_release.x86_64'):
            shutil.copy2(self.templates / name, destination / name)
        require({path.name for path in destination.iterdir()} == {'version.txt', 'linux_debug.x86_64', 'linux_release.x86_64'}
                and all(digest(destination / name) == digest(self.templates / name) for name in ('version.txt', 'linux_debug.x86_64', 'linux_release.x86_64')),
                'Private verified template copy differs')
        self.receipt['selected_environment'] = {key: value for key, value in self.environment.items() if key not in ('HOME', 'USER', 'LOGNAME')}
        return {'tools': self.pins['tools'], 'source_files': len(self.original), 'host': self.receipt['host_before']}

    def stage(self):
        self.project = OUTPUT / 'project'
        self.command('stage', [self.python_path, str(ROOT / 'scripts/linux_profile_overhead.py'), 'stage', '--output', str(self.project)], ROOT)
        original = self.evidence.json(OUTPUT / 'project-stage.json')
        require(original['files'] == accepted.inventory(self.project), 'Initial stage does not match its record')
        project, presets = self.project / 'project.godot', self.project / 'export_presets.cfg'
        before = {'project.godot': project.read_text(), 'export_presets.cfg': presets.read_text()}
        require('[editor]' not in before['project.godot'], 'Unexpected base editor settings')
        project.write_text(before['project.godot'] + '\n[editor]\nexport/convert_text_resources_to_binary=false\n')
        require(before['export_presets.cfg'].count('script_export_mode=2') == 5, 'Unexpected base export modes')
        presets.write_text(before['export_presets.cfg'].replace('script_export_mode=2', 'script_export_mode=0', 1))
        amendment = {'before': before, 'after': {
            'project.godot': project.read_text(), 'export_presets.cfg': presets.read_text()},
            'original_stage_record_sha256': digest(OUTPUT / 'project-stage.json')}
        write(OUTPUT / 'diagnostic-packaging-amendment.json', amendment)
        self.evidence.publication(OUTPUT / 'diagnostic-packaging-amendment.json', amendment)
        self.stage_record = {**original, 'files': accepted.inventory(self.project),
                             'diagnostic_packaging': {'script_export_mode': 0, 'convert_text_resources_to_binary': False}}
        write(OUTPUT / 'diagnostic-stage.json', self.stage_record)
        self.evidence.publication(OUTPUT / 'diagnostic-stage.json', self.stage_record)
        return self.stage_record

    def retain_stage(self, label):
        require(not any(path.is_symlink() for path in self.project.rglob('*')), 'Unexpected staged symlink')
        complete = {path.relative_to(self.project).as_posix(): {'bytes': path.stat().st_size, 'sha256': digest(path)}
                    for path in sorted(self.project.rglob('*')) if path.is_file()}
        write(OUTPUT / (label + '-complete-stage.json'), complete)
        self.evidence.publication(OUTPUT / (label + '-complete-stage.json'), complete)
        generated = OUTPUT / (label + '-generated-uids')
        for name in complete:
            if name.endswith('.uid') and (not self.stage_record or name not in self.stage_record['files']):
                destination = generated / name
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(self.project / name, destination)
                self.evidence.bind(destination, wanted=complete[name])
        return complete

    def inventory_stage(self, label):
        complete = self.retain_stage(label)
        source = {name: value for name, value in complete.items() if not name.startswith('.godot/')
                  and name != 'diagnostics/linux_profile_overhead.gd.uid'}
        require(source == self.stage_record['files'], 'Staged source/UID changed after ' + label)
        for name, wanted in source.items():
            self.evidence.bind(self.project / name, wanted=wanted)
        require(not any(path.is_symlink() for path in self.project.rglob('*')), 'Unexpected staged symlink')
        require(self.sources() == self.original, 'Original tracked source changed')
        return complete

    def inspect_artifact(self):
        self.executable = OUTPUT / 'export/linux-profile-diagnostic.x86_64'
        result, pack = payload.inspect(self.executable, self.templates / 'linux_debug.x86_64', self.project, self.stage_record)
        pack_path = OUTPUT / 'embedded-diagnostic.pck'
        pack_path.write_bytes(pack)
        write(OUTPUT / 'independent-payload.json', result)
        require(read_json(OUTPUT / 'independent-payload.json') == result and digest(pack_path) == result['PCK_sha256'], 'Artifact receipt differs')
        self.receipt['independent_payload'] = result
        self.receipt['independent_payload_receipt_sha256'] = digest(OUTPUT / 'independent-payload.json')
        self.evidence.bind(self.executable, wanted={'bytes': result['ELF_bytes'], 'sha256': result['ELF_sha256']})
        self.evidence.bind(pack_path, raw=pack)
        self.evidence.publication(OUTPUT / 'independent-payload.json', result)
        for row in result['imported_resources']:
            self.evidence.bind(self.project / row['target'], wanted={'sha256': row['cache_sha256']})
        for name, wanted in result['stage_auxiliary'].items():
            self.evidence.bind(self.project / name, wanted=wanted)
        return result

    def seal_payload(self):
        self.command('seal', [self.python_path, str(ROOT / 'scripts/linux_profile_overhead.py'), 'seal',
                    '--stage-record', str(OUTPUT / 'diagnostic-stage.json'), '--executable', str(self.executable),
                    '--output', str(OUTPUT / 'seal.json')], ROOT)
        self.seal = self.evidence.json(OUTPUT / 'seal.json')
        require(self.seal['payload_sha256'] == self.receipt['independent_payload']['ELF_sha256']
                and self.seal['source_ledger_sha256'] == self.receipt['independent_payload']['ledger_sha256'], 'Seal differs from independent payload gate')
        self.receipt['seal_sha256'] = digest(OUTPUT / 'seal.json')
        self.validate_stage_record()
        return self.seal

    def validate_stage_record(self):
        path = OUTPUT / 'diagnostic-stage.json'
        require(self.seal['stage_record'] == str(path.resolve()), 'Seal stage record path differs')
        self.evidence.bind(path, wanted={'sha256': self.seal['stage_sha256']})
        require(self.evidence.json(path) == self.stage_record, 'Seal-bound stage record changed')

    def native_argv(self, *args):
        return ['/usr/bin/taskset', '-c', '0,1', *args]

    def run_block(self):
        if hasattr(self, 'lane_lock'):
            fcntl.flock(self.lane_lock, fcntl.LOCK_UN)
        try:
            self.command('accepted-block', self.native_argv(self.python_path, str(ROOT / 'scripts/linux_profile_overhead.py'), 'run',
                        '--seal', str(OUTPUT / 'seal.json'), '--output', str(OUTPUT / 'native-block'), '--xvfb', self.xvfb,
                        '--display', self.display, '--cpus', '0,1'), ROOT)
        finally:
            if hasattr(self, 'lane_lock'):
                fcntl.flock(self.lane_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        block = self.evidence.json(OUTPUT / 'native-block/block.json')
        require(block['passed'] is True and block['expected']['cpus'] == [0, 1] and block['expected']['display'] == self.display,
                'Accepted controller did not complete the registered block')
        require(block['expected']['source'] == self.seal['source'] and block['expected']['payload_sha256'] == digest(self.executable),
                'Block payload/source differs')
        require(block['expected']['executable'] == str(self.executable) and block['expected']['seal_sha256'] == self.receipt['seal_sha256'],
                'Block executable/seal receipt differs')
        accepted.evaluate(block['records'], block['expected'])
        require([row['profile'] for row in block['records']] == [False, True, True, False], 'Wrong block order')
        for row in block['records']:
            expected_output = OUTPUT / 'native-block' / f'{row["index"] + 1:02d}-' / ('on' if row['profile'] else 'off')
            require(row['output'] == str(expected_output) and not expected_output.is_symlink(), 'Block condition output escaped this attempt')
            condition = Path(row['output']) / 'condition.json'
            require(digest(condition) == row['publication_sha256'], 'Changed condition publication')
            self.evidence.bind(condition, wanted={'sha256': row['publication_sha256']})
            accepted.validate_condition(self.evidence.json(condition), block['expected'])
            log_raw = (expected_output / 'client.log').read_bytes()
            actual_log = log_raw.decode(errors='replace')
            require(actual_log == row['stdout'] and not strict_log(actual_log), 'Changed/failed strict condition log')
            self.evidence.bind(expected_output / 'client.log', raw=log_raw, log=True)
            require(self.evidence.json(expected_output / 'metrics.json') == row['fixture'], 'Metrics differ from accepted condition')
            require(digest(expected_output / 'proof.png') == row['fixture']['png_sha256'], 'Proof image differs from accepted condition')
            self.evidence.bind(expected_output / 'proof.png', wanted={'sha256': row['fixture']['png_sha256']})
            self.budget.check('outer raw condition rechecked')
        require(not strict_log((OUTPUT / 'native-block/xvfb.log').read_text(errors='replace')), 'Strict Xvfb log gate')
        self.evidence.bind(OUTPUT / 'native-block/xvfb.log', log=True)
        require(block['xvfb_cleanup']['pid_absent'] and block['xvfb_cleanup']['group_absent'], 'Xvfb cleanup failed')
        self.receipt['block_sha256'] = digest(OUTPUT / 'native-block/block.json')
        self.receipt['block'] = block
        return {'passed': True, 'sha256': self.receipt['block_sha256']}

    def finalize(self):
        self.evidence.validate()
        self.validate_stage_record()
        require(self.sources() == self.original, 'Final original tracked source changed')
        self.inventory_stage('final')
        self.verify_tools()
        private_templates = OUTPUT / 'private-export-state/data/godot/export_templates/4.7.2.stable'
        require({path.name for path in private_templates.iterdir()} == {'version.txt', 'linux_debug.x86_64', 'linux_release.x86_64'}
                and all(digest(private_templates / name) == digest(self.templates / name)
                        for name in ('version.txt', 'linux_debug.x86_64', 'linux_release.x86_64')), 'Private templates changed')
        require(digest(self.executable) == self.seal['payload_sha256'], 'Final payload changed')
        require(read_json(OUTPUT / 'seal.json') == self.seal and digest(OUTPUT / 'seal.json') == self.receipt['seal_sha256'], 'Final seal changed')
        require(digest(OUTPUT / 'embedded-diagnostic.pck') == self.receipt['independent_payload']['PCK_sha256']
                and digest(OUTPUT / 'independent-payload.json') == self.receipt['independent_payload_receipt_sha256'], 'Independent artifact evidence changed')
        host = self.host()
        before = self.receipt['host_before']
        require(all(host[key] == before[key] for key in ('uname', 'os_release_sha256', 'affinity', 'nice', 'scheduler', 'python', 'supervisor_libraries')),
                'Host/kernel/library/priority identity changed')
        require(host['quota'] == before['quota'], 'Quota or throttling changed during acquisition')
        self.receipt['host_after'] = host
        self.receipt['recognized_native_after'] = recognized_native()
        require(not self.receipt['recognized_native_after'], 'Recognized native process remains')
        require(not Path('/tmp/.X11-unix/X99127').exists() and not Path('/tmp/.X99127-lock').exists(), 'Display publication remains')
        self.budget.check('final acceptance prepared')
        self.evidence.validate()
        return {'source_unchanged': True, 'stage_unchanged': True, 'payload_unchanged': True, 'host_unchanged': True}

    def execute(self):
        self.budget.phase('preflight', self.preflight)
        self.budget.phase('stage', self.stage)
        self.budget.phase('version', lambda: require(self.command('version', self.native_argv(str(self.engine), '--headless', '--version'), self.project).strip()
                                                   == toolchain.ENGINE, 'Wrong actual engine version'))
        self.budget.phase('import', lambda: self.command('import', self.native_argv(str(self.engine), '--headless', '--editor', '--path', str(self.project), '--import', '--quit'), self.project))
        self.budget.phase('import-inventory', lambda: self.inventory_stage('import'))
        def export():
            (OUTPUT / 'export').mkdir()
            return self.command('export', self.native_argv(str(self.engine), '--headless', '--path', str(self.project),
                                '--export-debug', 'Linux', str(OUTPUT / 'export/linux-profile-diagnostic.x86_64')), self.project)
        self.budget.phase('export', export)
        self.budget.phase('artifact', lambda: {'stage': self.inventory_stage('export'), 'payload': self.inspect_artifact()})
        self.budget.phase('seal', self.seal_payload)
        self.budget.phase('block', self.run_block)
        self.budget.phase('finalize', self.finalize)
        self.final_accept_until = self.receipt['phases'][-1]['deadline_monotonic']
        self.budget.check('all phases accepted')
        self.receipt['passed'] = True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute-frozen-source', required=True, help='Full SHA separately accepted and released by root')
    args = parser.parse_args()
    def interrupted(_signal, _frame):
        raise KeyboardInterrupt('Acquisition interrupted')
    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    acquisition = Acquisition(args.execute_frozen_source)
    claimed, exclusive, lane = False, None, None
    try:
        with acquisition.budget.armed(acquisition.budget.started + CAPS['preflight'], 'admission'):
            require(OUTPUT.is_relative_to(ROOT) and not OUTPUT.parent.is_symlink(), 'Unexpected attempt parent')
            require(not OUTPUT.exists() and not OUTPUT.is_symlink(), 'One-shot attempt already claimed; preserve it')
            OUTPUT.mkdir(parents=True, exist_ok=False)
            claimed = True
            with (OUTPUT / 'attempt.claim').open('x') as claim:
                claim.write(args.execute_frozen_source + '\n')
            exclusive = ACQUISITION_LOCK.open('a')
            lane = LANE_LOCK.open('a')
            fcntl.flock(exclusive, fcntl.LOCK_EX | fcntl.LOCK_NB)
            fcntl.flock(lane, fcntl.LOCK_EX | fcntl.LOCK_NB)
            acquisition.lane_lock = lane
        acquisition.execute()
    except (Exception, KeyboardInterrupt) as error:
        if not claimed:
            try:
                with acquisition.budget.armed(time.monotonic() + FAILURE_PUBLICATION, 'admission failure stderr'):
                    print(str(error), file=sys.stderr)
            except (Exception, KeyboardInterrupt):
                pass
            return 1
        acquisition.receipt.update(passed=False, error=str(error), error_type=type(error).__name__)
    finally:
        for stream in (lane, exclusive):
            if stream:
                stream.close()
    # Normal success publication must fit the original whole cap. Failure-only
    # publication has a separate bound and never changes a rejected verdict.
    failure_until = None if acquisition.receipt['passed'] else time.monotonic() + FAILURE_PUBLICATION
    try:
        until = min(acquisition.budget.until, acquisition.final_accept_until) if acquisition.receipt['passed'] else time.monotonic() + FAILURE_PUBLICATION
        if failure_until is not None:
            until = failure_until
        if acquisition.receipt['passed']:
            acquisition.budget.phase_until = until
        with acquisition.budget.armed(until, 'overall publication'):
            if not acquisition.receipt['passed']:
                acquisition.receipt['validated_evidence'] = deepcopy(acquisition.evidence.rows)
                if hasattr(acquisition, 'project') and acquisition.project.exists():
                    try:
                        acquisition.retain_stage('failed-preparation')
                    except accepted.Invalid as retention_error:
                        acquisition.receipt['failed_inventory_error'] = str(retention_error)
                for row in acquisition.receipt['commands']:
                    for stream in ('stdout', 'stderr'):
                        path = Path(row[stream]['path'])
                        if path.is_file():
                            # Preserve the original gate identity on rejection.
                            row[stream]['failure_observation'] = {'bytes': path.stat().st_size, 'sha256': digest(path)}
            if acquisition.receipt['passed']:
                outputs = acquisition.evidence.close_outputs()
                write(OUTPUT / 'outputs.json', outputs)
                require(read_json(OUTPUT / 'outputs.json') == outputs, 'Output manifest publication differs')
                acquisition.evidence.publication(OUTPUT / 'outputs.json', outputs)
                acquisition.evidence.validate(closed=True)
                acquisition.receipt['output_manifest_sha256'] = digest(OUTPUT / 'outputs.json')
                # Overall cannot contain its own byte identity. This snapshot
                # includes the manifest; the private registry also binds overall.
                acquisition.receipt['validated_evidence'] = deepcopy(acquisition.evidence.rows)
                acquisition.budget.check('overall before publication')
            write(OUTPUT / 'overall.json', accepted.safe_failure_report(acquisition.receipt))
            reread = read_json(OUTPUT / 'overall.json')
            require(reread == accepted.safe_failure_report(acquisition.receipt), 'Overall publication differs')
            if acquisition.receipt['passed']:
                acquisition.evidence.publication(OUTPUT / 'overall.json', accepted.safe_failure_report(acquisition.receipt))
                acquisition.evidence.validate(closed=True)
                acquisition.budget.check('overall final read')
            print(json.dumps({'passed': acquisition.receipt['passed'], 'output': str(OUTPUT), 'error': acquisition.receipt.get('error')}), flush=True)
            if acquisition.receipt['passed']:
                acquisition.evidence.validate(closed=True)
                acquisition.budget.check('overall final stdout')
        if acquisition.receipt['passed']:
            acquisition.evidence.validate(closed=True)
            acquisition.budget.check('overall alarm restored')
    except (Exception, KeyboardInterrupt) as error:
        acquisition.receipt.update(passed=False, publication_error=str(error))
        acquisition.receipt['validated_evidence'] = deepcopy(acquisition.evidence.rows)
        failure_until = failure_until or time.monotonic() + FAILURE_PUBLICATION
        try:
            with acquisition.budget.armed(failure_until, 'failure publication'):
                if (OUTPUT / 'overall.json').exists():
                    shutil.copy2(OUTPUT / 'overall.json', OUTPUT / 'rejected-overall-publication.json')
                write(OUTPUT / 'failure.json', accepted.safe_failure_report(acquisition.receipt))
                write(OUTPUT / 'overall.json', accepted.safe_failure_report(acquisition.receipt))
        except (Exception, KeyboardInterrupt):
            # Keep the claim, raw logs and any pending publication. A failure
            # publication timeout grants no new budget or success exit.
            pass
    return 0 if acquisition.receipt['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
