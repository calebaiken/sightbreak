#!/usr/bin/env python3
"""Stage and evaluate a separate Linux profiling-cadence diagnostic.

No shipping source is edited. Runtime requires a separately reviewed fresh export.
The OFF/ON/ON/OFF block screens median post-draw cadence at declared pacing;
it does not measure complete profiler overhead, GPU completion or gameplay cost.
"""
import argparse
from contextlib import contextmanager
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import signal
import stat
import struct
import subprocess
import sys
import time

from native_log import failed as native_log_failed

ROOT = Path(__file__).resolve().parents[1]
ORDER = (False, True, True, False)
WARM, SAMPLES, BOUND = 32, 64, 180
ENGINE = (4, 7, 2)
ENGINE_HASH = 'ed1daf0bf'
SETTINGS = {'viewport': [1280, 720], 'texture_size': [1280, 720], 'msaa_3d': 1,
            'render_scale': 1.0, 'scaling_3d_mode': 0, 'max_fps': 60, 'physics_hz': 60, 'physics_limit': 8,
            'jitter_fix': 0.5, 'time_scale': 1.0, 'thread_model_project': 1,
            'thread_mode_argument': 'safe', 'print_profile_setting': False}
FIXTURE = ROOT / 'scripts/diagnostics/linux_profile_overhead.gd'
SCENE = ROOT / 'scripts/diagnostics/linux_profile_overhead.tscn'


class Invalid(ValueError):
    pass


def require(value, message):
    if not value:
        raise Invalid(message)


def strict_json(text):
    def number(value):
        result = float(value)
        require(math.isfinite(result), 'Nonfinite JSON number')
        return result
    def constant(_value):
        raise Invalid('Nonfinite JSON constant')
    return json.loads(text, parse_float=number, parse_constant=constant)


def read_json(path):
    return strict_json(Path(path).read_text())


class Deadline:
    """One absolute bound; alarms interrupt blocking host reads in the main thread.

    Cleanup is separately bounded and never turns a late condition into a pass.
    An existing real-time alarm is rejected rather than silently replaced.
    """
    def __init__(self, record, bound=BOUND):
        self.record = record
        self.started = time.monotonic()
        self.until = self.started + bound
        record['timing'] = {'bound_seconds': bound, 'started_monotonic_seconds': self.started,
                            'deadline_monotonic_seconds': self.until, 'observations': []}

    def observe(self, stage):
        now = time.monotonic()
        timing = self.record['timing']
        timing.update(ended_monotonic_seconds=now, elapsed_seconds=now - self.started)
        timing['observations'].append({'stage': stage, 'monotonic_seconds': now,
                                       'elapsed_seconds': now - self.started})
        return now

    def check(self, stage):
        if self.observe(stage) >= self.until:
            raise TimeoutError('Condition deadline at ' + stage)

    @contextmanager
    def armed(self, stage):
        self.check(stage + ':entry')
        require(signal.getitimer(signal.ITIMER_REAL) == (0.0, 0.0), 'An existing real-time alarm is active')
        previous = signal.getsignal(signal.SIGALRM)
        def expired(_signum, _frame):
            raise TimeoutError('Condition deadline interrupted ' + stage)
        signal.signal(signal.SIGALRM, expired)
        try:
            remaining = self.until - time.monotonic()
            if remaining <= 0:
                raise TimeoutError('Condition deadline before arming ' + stage)
            signal.setitimer(signal.ITIMER_REAL, remaining)
            yield
            self.check(stage + ':complete')
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, previous)


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write(path, value):
    path = Path(path)
    text = json.dumps(value, indent=2, allow_nan=False) + '\n'
    temporary = path.with_name(path.name + '.pending')
    require(not temporary.exists(), 'Preserve an incomplete publication: ' + str(temporary))
    temporary.write_text(text)
    temporary.replace(path)


def acknowledge(path, token):
    temporary = path.with_name(path.name + '.pending')
    require(not temporary.exists() and not path.exists(), 'Preserve an earlier acknowledgement')
    temporary.write_text(token)
    temporary.replace(path)


def safe_failure_report(value):
    """Retain invalid-number evidence in failure summaries; never feed it back to evaluation."""
    if isinstance(value, float) and not math.isfinite(value):
        return {'invalid_nonfinite_value': repr(value)}
    if isinstance(value, dict):
        return {key: safe_failure_report(item) for key, item in value.items()}
    if isinstance(value, list):
        return [safe_failure_report(item) for item in value]
    return value


def positive(value):
    return type(value) in (int, float) and math.isfinite(value) and value > 0


def median(values):
    require(values and all(positive(value) for value in values), 'Nonfinite/nonpositive duration')
    ordered = sorted(values)
    middle = len(ordered) // 2
    return (ordered[middle - 1] + ordered[middle]) / 2 if len(ordered) % 2 == 0 else ordered[middle]


def drift(a, b):
    require(positive(a) and positive(b), 'Invalid drift inputs')
    return max(a, b) / min(a, b) - 1


def source_identity():
    def git(*args):
        return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()
    require(not git('status', '--porcelain', '--untracked-files=all'), 'Commit diagnostic source first')
    return {'commit': git('rev-parse', 'HEAD'), 'game_tree': git('rev-parse', 'HEAD:game'),
            'fixture_sha256': digest(FIXTURE), 'scene_sha256': digest(SCENE),
            'controller_sha256': digest(Path(__file__))}


def inventory(directory):
    return {path.relative_to(directory).as_posix(): {'bytes': path.stat().st_size, 'sha256': digest(path)}
            for path in sorted(Path(directory).rglob('*')) if path.is_file() and '.godot' not in path.parts
            and path.relative_to(directory).as_posix() != 'diagnostics/linux_profile_overhead.gd.uid'}


def stage(destination):
    """Only copy tracked game bytes and inject the explicit unshipped overlay."""
    identity = source_identity()
    destination = Path(destination).resolve()
    require(not destination.exists(), 'Use a fresh stage directory')
    require(not (destination.parent / (destination.name + '-stage.json')).exists(), 'Preserve the existing stage record')
    destination.mkdir(parents=True)
    names = subprocess.check_output(['git', 'ls-files', '-z', 'game'], cwd=ROOT).decode().split('\0')
    base = {}
    for name in filter(None, names):
        path = Path(name)
        relative = path.relative_to('game')
        if 'tests' in relative.parts:
            continue
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / path, target)
        base[relative.as_posix()] = digest(ROOT / path)
    project = destination / 'project.godot'
    text = project.read_text()
    require(text.count('run/main_scene="res://main.tscn"') == 1, 'Unexpected project main scene')
    require('print_gpu_profile' not in text and 'thread_model' not in text, 'Unexpected base profiling/thread setting')
    text = text.replace('run/main_scene="res://main.tscn"', 'run/main_scene="res://diagnostics/linux_profile_overhead.tscn"')
    text = text.replace('[rendering]\n', '[rendering]\ndriver/threads/thread_model=1\n')
    text += '\n[debug]\nsettings/stdout/print_gpu_profile=false\n'
    project.write_text(text)
    diagnostic = destination / 'diagnostics'
    diagnostic.mkdir()
    shutil.copy2(FIXTURE, diagnostic / FIXTURE.name)
    shutil.copy2(SCENE, diagnostic / SCENE.name)
    ledger = {'source': identity, 'content': base,
              'fixture_sha256': identity['fixture_sha256'], 'scene_sha256': identity['scene_sha256']}
    write(diagnostic / 'source_ledger.json', ledger)
    presets = destination / 'export_presets.cfg'
    presets.write_text(presets.read_text().replace('include_filter=""', 'include_filter="diagnostics/*.json"', 1))
    record = {'schema': 1, 'source': identity, 'base_files': base,
              'source_ledger_sha256': digest(diagnostic / 'source_ledger.json'),
              'files': inventory(destination), 'stage': str(destination)}
    write(destination.parent / (destination.name + '-stage.json'), record)
    return record


def seal_payload(stage_record, executable, output):
    """Bind a fresh externally exported diagnostic; this does not run an exporter."""
    record = read_json(stage_record)
    require(record['source'] == source_identity(), 'Stage source changed')
    require(record['files'] == inventory(Path(record['stage'])), 'Staged source changed')
    executable = Path(executable).resolve()
    with executable.open('rb') as stream:
        header = stream.read(20)
        require(header[:5] == b'\x7fELF\x02' and struct.unpack_from('<H', header, 18)[0] == 62, 'Not x86_64 ELF')
        stream.seek(-12, 2)
        size, magic = struct.unpack('<QI', stream.read(12))
        require(magic == 0x43504447, 'No embedded pack')
        stream.seek(-12-size, 2)
        pack = struct.unpack('<6IQ', stream.read(32))
        require(tuple(pack[2:5]) == ENGINE, 'Wrong pack engine version')
    sealed = {'schema': 1, 'source': record['source'], 'stage_sha256': digest(stage_record),
              'source_ledger_sha256': record['source_ledger_sha256'], 'stage_record': str(Path(stage_record).resolve()),
              'executable': str(executable), 'payload_sha256': digest(executable), 'payload_bytes': executable.stat().st_size}
    require(not Path(output).exists(), 'Preserve the existing seal')
    write(output, sealed)
    return sealed


def engine_argv(executable, profile, output, token):
    command = [str(executable)]
    if profile:
        command.append('--gpu-profile')
    return command + ['--render-thread', 'safe', '--audio-driver', 'Dummy', '--accessibility', 'disabled',
                      '--accessibility-driver', 'dummy', '--', '--output=' + str(output), '--token=' + token]


def caches(output):
    return {name: str(Path(output) / 'state' / name) for name in ('data', 'config', 'cache', 'mesa')}


def profile_blocks(stdout):
    blocks, current = [], None
    for line in stdout.splitlines():
        header = re.fullmatch(r'GPU PROFILE \(total (.+)ms\):\s*', line)
        row = re.fullmatch(r'\t-(.+): (.+)ms', line)
        require(not line.startswith('GPU PROFILE') or header, 'Malformed profile output')
        if header:
            value = float(header[1])
            require(math.isfinite(value) and value >= 0, 'Invalid profile header')
            current = []
            blocks.append(current)
        elif row:
            require(current is not None and positive(float(row[2])) and float(row[2]) > 0.01, 'Invalid profile row')
            current.append(row[1])
    return blocks


def interval_values(report):
    anchor = report['anchor']
    require(type(anchor['counter']) is int and type(anchor['callback']) is int and anchor['callback'] > 0,
            'Invalid cold anchor identity')
    require(positive(anchor['clock_usec']), 'Invalid cold anchor clock')
    require(type(report['cold_before']['counter']) is int and type(report['cold_before']['callback']) is int,
            'Invalid pre-anchor identity')
    cold_clock = report['cold_before']['clock_usec']
    require(type(cold_clock) in (int, float) and math.isfinite(cold_clock) and cold_clock >= 0,
            'Invalid pre-anchor clock')
    require(positive(anchor['clock_usec'] - cold_clock), 'Cold anchor was not separately timed')
    require(anchor['callback'] == report['cold_before']['callback'] + 1 and
            anchor['counter'] == report['cold_before']['counter'], 'Unexpected synchronous cold-anchor callback')
    previous = anchor
    groups = []
    for name, count in (('warm', WARM), ('measured', SAMPLES)):
        rows = report[name]
        require(len(rows) == count, 'Incomplete interval array: ' + name)
        values = []
        for row in rows:
            begin, end = row['begin'], row['end']
            require(begin == previous, 'Intervals lack consecutive post-draw anchoring')
            require(type(end['counter']) is int and end['counter'] == begin['counter'] + 1,
                    'Skipped or duplicate drawn identity')
            require(type(end['callback']) is int and end['callback'] == begin['callback'] + 1,
                    'Unexpected post-draw callback')
            duration = end['clock_usec'] - begin['clock_usec']
            require(positive(end['clock_usec']) and positive(duration), 'Nonfinite/nonpositive interval')
            require(type(row['draw_calls']) is int and row['draw_calls'] > 0 and
                    type(row['primitives']) is int and row['primitives'] > 0, 'Missing work counters')
            values.append(duration / 1000)
            previous = end
        groups.append(values)
    readback = report['readback']
    require(readback['counter'] == previous['counter'] + 1 and readback['callback'] == previous['callback'] + 1
            and positive(readback['clock_usec']) and positive(readback['clock_usec'] - previous['clock_usec']),
            'Readback lacks a separate later draw')
    require(report['readback_after']['counter'] == readback['counter'] and
            report['readback_after']['callback'] == readback['callback'] and
            positive(report['readback_after']['clock_usec']) and
            report['readback_after']['clock_usec'] >= readback['clock_usec'], 'Unexpected callback during readback/output')
    return groups


def validate_condition(record, expected):
    require(not record.get('error'), 'Incomplete condition: ' + str(record.get('error')))
    index = record['index']
    require(type(index) is int and 0 <= index < len(ORDER), 'Unknown condition')
    profile = ORDER[index]
    require(record['profile'] is profile, 'Wrong condition order')
    wanted = engine_argv(expected['executable'], profile, record['output'], record['token'])
    require(record['engine_argv'] == wanted, 'Wrong flag placement/default or engine argv')
    require(record['process_argv'] == ['taskset', '-c', ','.join(map(str, expected['cpus'])), *wanted], 'Wrong affinity launch')
    require(record['actual_cmdline'] == wanted, 'Actual owned command differs')
    require(record['actual_environment'] == record['selected_environment'], 'Actual graphics/cache environment differs')
    paths = caches(record['output'])
    require(record['selected_environment'] == {'DISPLAY': expected['display'], 'LIBGL_ALWAYS_SOFTWARE': '1', 'LP_NUM_THREADS': '2',
            'XDG_DATA_HOME': paths['data'], 'XDG_CONFIG_HOME': paths['config'], 'XDG_CACHE_HOME': paths['cache'],
            'MESA_SHADER_CACHE_DIR': paths['mesa']}, 'Changed graphics/cache environment')
    require(record['exit_code'] == 0 and record['timeout'] is False, 'Timeout or native exit failure')
    timing = record['timing']
    require(timing['bound_seconds'] == BOUND and type(timing['started_monotonic_seconds']) in (int, float)
            and math.isfinite(timing['started_monotonic_seconds']) and timing['started_monotonic_seconds'] >= 0
            and timing['deadline_monotonic_seconds'] == timing['started_monotonic_seconds'] + BOUND
            and type(timing['elapsed_seconds']) in (int, float) and math.isfinite(timing['elapsed_seconds'])
            and 0 <= timing['elapsed_seconds'] < BOUND
            and timing['ended_monotonic_seconds'] == timing['started_monotonic_seconds'] + timing['elapsed_seconds'],
            'Invalid or exceeded whole-condition deadline')
    require(record['cleanup'] == {'pid_absent': True, 'group_absent': True, 'forced': False}, 'Failed owned cleanup')
    require(record['payload_before'] == record['payload_after'] == expected['payload_sha256'], 'Payload changed')
    require(record['seal_sha256'] == expected['seal_sha256'], 'Payload/source seal differs')
    require(record['cache_initial'] == {'paths': caches(record['output']), 'empty': True}, 'Cache isolation missing')
    begin, end = record['host_begin'], record['host_end']
    for host in (begin, end):
        require(host['affinity'] == expected['cpus'] and host['quota'] == expected['quota'], 'Affinity/quota changed')
        require(host['driver_libraries'] and host['driver_libraries'] == expected['driver_libraries'], 'Driver payload changed')
        require(host['cgroup_path'] == expected['cgroup_path'], 'Cgroup identity changed')
        require(all(type(host['throttling'].get(key)) is int for key in ('nr_throttled', 'throttled_usec')),
                'Missing throttling counters')
    require(begin['throttling'] == end['throttling'], 'Throttling increased or counters reset')
    require(record['rusage'] and all(type(record['rusage'].get(key)) in (int, float)
                                  and math.isfinite(record['rusage'][key]) and record['rusage'][key] >= 0
                                  for key in ('user_seconds', 'system_seconds')), 'Missing owned whole-process CPU')
    report = record['fixture']
    require(report['schema'] == 1 and report['token'] == record['token'], 'Fixture identity mismatch')
    require(report['source_ledger_sha256'] == expected['source_ledger_sha256'], 'Fixture source ledger differs')
    for key, value in SETTINGS.items():
        require(report['settings'].get(key) == value, 'Altered setting: ' + key)
    require(type(report['settings'].get('vsync_mode')) is int, 'Missing V-Sync getter')
    info = report['engine']
    require(tuple(info.get(key) for key in ('major', 'minor', 'patch')) == ENGINE and
            info.get('status') == 'stable' and info.get('hash', '').startswith(ENGINE_HASH), 'Wrong actual engine')
    require('llvmpipe' in report['adapter']['name'].lower() and 'mesa' in report['adapter']['api'].lower(), 'Wrong actual renderer')
    require(report['workload'] == {'actors': 5, 'view': 'approach', 'static': True,
                                   'authority_ticks': 0, 'visual_ticks': 0}, 'Moving or different workload')
    for name in ('fingerprint_initial', 'fingerprint_terminal'):
        item = report[name]
        require(hashlib.sha256(item['serialized'].encode()).hexdigest() == item['sha256'], 'Invalid fingerprint hash')
        content = strict_json(item['serialized'])
        require(content['source_ledger_sha256'] == expected['source_ledger_sha256'] and content['nodes']
                and content['settings'] == report['settings'], 'Incomplete fingerprint')
    require(report['fingerprint_initial'] == report['fingerprint_terminal'], 'Scene changed during condition')
    require(re.fullmatch('[0-9a-f]{64}', report['png_sha256']) is not None, 'Missing image hash')
    blocks = profile_blocks(record['stdout'])
    require(not native_log_failed(record['stdout']), 'Engine log failed')
    require(any(blocks) if profile else not blocks, 'Missing ON profile capability or unexpected OFF output')
    warm, measured = interval_values(report)
    require(drift(median(warm[:16]), median(warm[16:])) <= 0.10 + 1e-12, 'Warm-up failed to stabilize')
    counters = {(row['draw_calls'], row['primitives']) for row in report['measured']}
    require(len(counters) == 1, 'Changing sampled work counters')
    return {'index': index, 'profile': profile, 'median_cadence_ms': median(measured),
            'cadence_total_ms': sum(measured), 'cadence_mean_ms': sum(measured) / len(measured),
            'largest_interval_ms': max(measured), 'samples_ms_in_order': measured,
            'cold_anchor_ms': (report['anchor']['clock_usec'] - report['cold_before']['clock_usec']) / 1000,
            'warm_half_drift': drift(median(warm[:16]), median(warm[16:])),
            'profile_headers': len(blocks), 'work_counters': list(next(iter(counters)))}


def evaluate(records, expected):
    require(len(records) == 4 and [row['index'] for row in records] == list(range(4)), 'Incomplete/reordered block')
    require(len({row['output'] for row in records}) == 4, 'Conditions reused an output/cache root')
    rows = [validate_condition(record, expected) for record in records]
    reference = records[0]['fixture']
    for record, row in zip(records, rows):
        report = record['fixture']
        for key in ('settings', 'adapter', 'engine', 'fingerprint_initial', 'fingerprint_terminal', 'png_sha256'):
            require(report[key] == reference[key], 'Cross-condition work/pixel/settings changed: ' + key)
        require(row['work_counters'] == rows[0]['work_counters'], 'Cross-condition work counters changed')
    require(drift(rows[0]['median_cadence_ms'], rows[3]['median_cadence_ms']) <= 0.05 + 1e-12, 'OFF drift exceeded')
    require(drift(rows[1]['median_cadence_ms'], rows[2]['median_cadence_ms']) <= 0.05 + 1e-12, 'ON drift exceeded')
    ratios = [rows[1]['median_cadence_ms'] / rows[0]['median_cadence_ms'],
              rows[2]['median_cadence_ms'] / rows[3]['median_cadence_ms']]
    if all(value >= 1.10 for value in ratios):
        outcome = 'flag_associated_median_cadence_increase_in_this_block'
    elif all(0.90 <= value < 1.10 for value in ratios):
        outcome = 'block_did_not_resolve_a_10_percent_median_cadence_increase'
    else:
        outcome = 'unresolved'
    secondary = {key: [rows[1][key] / rows[0][key], rows[2][key] / rows[3][key]]
                 for key in ('cadence_total_ms', 'cadence_mean_ms', 'largest_interval_ms')}
    return {'schema': 1, 'comparable': True, 'outcome': outcome, 'paired_median_ratios': ratios,
            'descriptive_secondary_ratios': secondary, 'conditions': rows,
            'scope': 'Median warm wall cadence between consecutive post-draw callbacks at cap 60 and declared pacing. Previous-frame profile tail, scheduling and pacing can enter the intervals; sparse stdout stalls can disappear from medians. No complete profiler overhead, physical FPS, uncapped cost, CPU-function or gameplay attribution.'}


def cgroup_snapshot(pid):
    lines = Path(f'/proc/{pid}/cgroup').read_text().splitlines()
    relative = next(line[3:] for line in lines if line.startswith('0::'))
    require('..' not in Path(relative).parts, 'Unsafe cgroup path')
    root = Path('/sys/fs/cgroup') / relative.lstrip('/')
    stat = dict(line.split() for line in (root / 'cpu.stat').read_text().splitlines())
    return {'cgroup_path': str(root), 'quota': (root / 'cpu.max').read_text().strip(),
            'throttling': {key: int(stat[key]) for key in ('nr_throttled', 'throttled_usec')}}


def host_snapshot(pid):
    libraries = {}
    for line in Path(f'/proc/{pid}/maps').read_text().splitlines():
        parts = line.split(maxsplit=5)
        if len(parts) == 6 and parts[5].startswith('/') and re.search(r'(libGL|libEGL|libOpenGL|libgallium|libLLVM|libglapi|libdrm|/dri/)', parts[5]):
            path = str(Path(parts[5]).resolve())
            libraries[path] = digest(path)
    require(libraries, 'No loaded driver-library evidence')
    return {**cgroup_snapshot(pid), 'affinity': sorted(os.sched_getaffinity(pid)),
            'driver_libraries': dict(sorted(libraries.items()))}


def absent(identity, group=False):
    try:
        os.kill(-identity if group else identity, 0)
    except ProcessLookupError:
        return True
    return False


def pid_start(pid):
    text = Path(f'/proc/{pid}/stat').read_text()
    return int(text[text.rfind(')') + 2:].split()[19])


def owned_launch_state(pid, selected):
    command = [part.decode() for part in Path(f'/proc/{pid}/cmdline').read_bytes().split(b'\0') if part]
    entries = dict(part.split(b'=', 1) for part in Path(f'/proc/{pid}/environ').read_bytes().split(b'\0') if b'=' in part)
    return command, {key: entries[key.encode()].decode() for key in selected}


def cleanup(process):
    forced = False
    if process.poll() is None or not absent(process.pid, True):
        forced = True
        if process.poll() is None and hasattr(process, 'sightbreak_start_ticks'):
            require(pid_start(process.pid) == process.sightbreak_start_ticks, 'Owned PID identity changed before cleanup')
        # When the initial proc read itself failed, poll/waitpid still identifies
        # this unreaped child created by Popen in its new session. Tear it down;
        # the missing identity remains a failed condition, never a valid record.
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=5)
        if not absent(process.pid, True):
            os.killpg(process.pid, signal.SIGKILL)
    return {'pid_absent': absent(process.pid), 'group_absent': absent(process.pid, True), 'forced': forced}


def owned_display(process, socket, lock):
    """Join the published path to a socket FD held by this exact live child."""
    require(process.poll() is None and pid_start(process.pid) == process.sightbreak_start_ticks,
            'Owned Xvfb is not live with its original identity')
    before = socket.lstat()
    require(stat.S_ISSOCK(before.st_mode), 'Display path is not a Unix socket')
    lock_before = lock.lstat()
    require(stat.S_ISREG(lock_before.st_mode) and lock.read_text().strip() == str(process.pid),
            'Display lock does not name owned Xvfb')
    inodes = {line.split()[6] for line in Path(f'/proc/{process.pid}/net/unix').read_text().splitlines()[1:]
              if len(line.split()) == 8 and line.split()[7] == str(socket)}
    descriptors = {os.readlink(path) for path in Path(f'/proc/{process.pid}/fd').iterdir()}
    held = sorted(inode for inode in inodes if 'socket:[' + inode + ']' in descriptors)
    require(held, 'Ready display socket is not held by owned Xvfb')
    after, lock_after = socket.lstat(), lock.lstat()
    require((before.st_dev, before.st_ino) == (after.st_dev, after.st_ino)
            and (lock_before.st_dev, lock_before.st_ino) == (lock_after.st_dev, lock_after.st_ino)
            and lock.read_text().strip() == str(process.pid), 'Display publication changed during ownership check')
    require(process.poll() is None and pid_start(process.pid) == process.sightbreak_start_ticks,
            'Owned Xvfb exited or changed identity during readiness')
    return {'pid': process.pid, 'start_ticks': process.sightbreak_start_ticks,
            'socket_device': before.st_dev, 'socket_inode': before.st_ino,
            'owned_kernel_socket_inodes': held, 'lock_pid': process.pid}


class NativeRunner:
    def __init__(self, xvfb, display, output):
        self.xvfb, self.display, self.output = xvfb, display, Path(output)
        self.server = None
        self.log = None

    def start(self):
        require(re.fullmatch(r':[0-9]+', self.display), 'Use a numbered display')
        socket = Path('/tmp/.X11-unix/X' + self.display[1:])
        lock = Path('/tmp/.X' + self.display[1:] + '-lock')
        require(not socket.exists() and not socket.is_symlink() and not lock.exists() and not lock.is_symlink(),
                'Display socket or lock already in use')
        self.log = (self.output / 'xvfb.log').open('wb')
        self.server = subprocess.Popen([self.xvfb, self.display, '-screen', '0', '1280x720x24', '-nolisten', 'tcp'],
                                       stdout=self.log, stderr=subprocess.STDOUT, start_new_session=True)
        self.server.sightbreak_start_ticks = pid_start(self.server.pid)
        write(self.output / 'xvfb-launch.json', {'command': self.server.args, 'pid': self.server.pid,
              'start_ticks': self.server.sightbreak_start_ticks, 'started_unix_ns': time.time_ns()})
        receipt = {}
        deadline = Deadline(receipt, 5)
        try:
            with deadline.armed('Xvfb readiness'):
                while True:
                    deadline.check('Xvfb readiness poll')
                    require(self.server.poll() is None and pid_start(self.server.pid) == self.server.sightbreak_start_ticks,
                            'Xvfb readiness failure: owned server exited or changed identity')
                    if socket.exists():
                        receipt['ownership'] = owned_display(self.server, socket, lock)
                        deadline.check('Xvfb ownership accepted')
                        break
                    time.sleep(0.05)
            write(self.output / 'xvfb-readiness.json', receipt)
        except (Exception, KeyboardInterrupt) as error:
            deadline.observe('Xvfb readiness rejected')
            receipt.update(error=str(error), owned_exit_code=self.server.poll())
            write(self.output / 'xvfb-readiness.json', receipt)
            raise

    def stop(self):
        result = cleanup(self.server) if self.server else None
        if result is not None:
            result.update(pid=self.server.pid, start_ticks=getattr(self.server, 'sightbreak_start_ticks', None))
        if self.log:
            self.log.close()
        return result

    def condition(self, record, environment, deadline):
        output = Path(record['output'])
        process = None
        try:
            with deadline.armed('native observations'), (output / 'client.log').open('wb') as log:
                import resource
                cpu_before = resource.getrusage(resource.RUSAGE_CHILDREN)
                process = subprocess.Popen(record['process_argv'], env=environment, cwd=output,
                                           stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
                deadline.check('client spawned')
                record['pid'] = process.pid
                process.sightbreak_start_ticks = pid_start(process.pid)
                record['pid_start_ticks'] = process.sightbreak_start_ticks
                write(output / 'launch.json', record)
                for filename in ('ready.json', 'metrics.json'):
                    path = output / filename
                    deadline.check('before ' + filename)
                    while not path.exists():
                        require(process.poll() is None, 'Fixture exited before ' + filename)
                        deadline.check('waiting for ' + filename)
                        time.sleep(0.05)
                    deadline.check('published ' + filename)
                    publication = read_json(path)
                    deadline.check('read ' + filename)
                    require(publication['token'] == record['token'], 'Wrong fixture token')
                    if filename == 'ready.json':
                        record['actual_cmdline'], record['actual_environment'] = owned_launch_state(process.pid, record['selected_environment'])
                        deadline.check('owned launch observed')
                        require(record['actual_cmdline'] == record['engine_argv'], 'Actual engine command differs')
                        require(record['actual_environment'] == record['selected_environment'], 'Actual selected environment differs')
                        record['host_begin'] = host_snapshot(process.pid)
                        deadline.check('initial host observed')
                        acknowledge(output / 'begin.ack', record['token'])
                        deadline.check('begin acknowledged')
                    else:
                        record['host_end'] = host_snapshot(process.pid)
                        deadline.check('final host observed')
                        record['fixture'] = publication
                        record['payload_after'] = digest(record['engine_argv'][0])
                        deadline.check('payload verified')
                        acknowledge(output / 'finish.ack', record['token'])
                        deadline.check('finish acknowledged')
                deadline.check('before child wait')
                process.wait(timeout=deadline.until - time.monotonic())
                deadline.check('child completed')
                cpu_after = resource.getrusage(resource.RUSAGE_CHILDREN)
                record['rusage'] = {'user_seconds': cpu_after.ru_utime - cpu_before.ru_utime,
                                    'system_seconds': cpu_after.ru_stime - cpu_before.ru_stime,
                                    'scope': 'Completed owned child process including startup; no other child is waited in this interval'}
                record['exit_code'] = process.returncode
                final = cgroup_snapshot(os.getpid())
                deadline.check('final cgroup observed')
                require(final['cgroup_path'] == record['host_end']['cgroup_path'], 'Controller/client cgroup differs')
                record['host_end']['throttling'] = final['throttling']
                require(digest(output / 'proof.png') == record['fixture']['png_sha256'], 'Actual PNG differs')
                deadline.check('PNG verified')
        except (Exception, KeyboardInterrupt) as error:
            record.update(error=str(error), timeout=isinstance(error, (TimeoutError, subprocess.TimeoutExpired)))
        finally:
            try:
                record['cleanup'] = cleanup(process) if process else {'pid_absent': False, 'group_absent': False, 'forced': True}
            except Exception as error:
                record['cleanup'] = {'pid_absent': False, 'group_absent': False, 'forced': True}
                record['cleanup_error'] = str(error)
            if process and 'exit_code' not in record:
                record['exit_code'] = process.returncode
            deadline.observe('owned cleanup ended')
        record['stdout'] = ''
        if not record.get('error'):
            try:
                with deadline.armed('final client log read'):
                    record['stdout'] = (output / 'client.log').read_text(errors='replace')
            except (Exception, KeyboardInterrupt) as error:
                record.update(error=str(error), timeout=isinstance(error, (TimeoutError, subprocess.TimeoutExpired)))
        else:
            record['stdout_retained_on_disk'] = str(output / 'client.log')
        return record


def run_block(seal, output, cpus, runner, source_check=None):
    """The real sequencing/stop policy is also used with synthetic process runners."""
    require(len(cpus) == 2 and all(type(cpu) is int and cpu >= 0 for cpu in cpus) and cpus == sorted(set(cpus)),
            'Select exactly two sorted allowed CPUs')
    require(digest(seal['executable']) == seal['payload_sha256'], 'Payload differs before launch')
    output = Path(output).resolve()
    require(not output.exists(), 'Preserve prior output; use a fresh block directory')
    output.mkdir(parents=True)
    records = []
    expected = {**seal, 'cpus': cpus, 'display': runner.display}
    summary = {'passed': False, 'records': records, 'scope': 'One screening block, not gameplay or total profiling cost'}
    try:
        runner.start()
        for index, profile in enumerate(ORDER):
            if source_check:
                source_check()
            directory = output / f'{index + 1:02d}-' / ('on' if profile else 'off')
            directory.mkdir(parents=True)
            paths = caches(directory)
            for name in paths.values():
                Path(name).mkdir(parents=True, exist_ok=False)
                require(not any(Path(name).iterdir()), 'Cache was not empty')
            token = f'condition-{index}-' + hashlib.sha256(str(directory).encode()).hexdigest()[:16]
            command = engine_argv(seal['executable'], profile, directory, token)
            record = {'index': index, 'profile': profile, 'output': str(directory), 'token': token,
                      'engine_argv': command, 'process_argv': ['taskset', '-c', ','.join(map(str, cpus)), *command],
                      'timeout': False, 'payload_before': digest(seal['executable']),
                      'seal_sha256': seal['seal_sha256'], 'cache_initial': {'paths': paths, 'empty': True}}
            environment = dict(os.environ, DISPLAY=runner.display, LIBGL_ALWAYS_SOFTWARE='1', LP_NUM_THREADS='2',
                               XDG_DATA_HOME=paths['data'], XDG_CONFIG_HOME=paths['config'], XDG_CACHE_HOME=paths['cache'],
                               MESA_SHADER_CACHE_DIR=paths['mesa'], DBUS_SESSION_BUS_ADDRESS='unix:path=' + str(directory / 'unavailable-bus'))
            record['selected_environment'] = {key: environment[key] for key in ('DISPLAY', 'LIBGL_ALWAYS_SOFTWARE', 'LP_NUM_THREADS',
                                               'XDG_DATA_HOME', 'XDG_CONFIG_HOME', 'XDG_CACHE_HOME', 'MESA_SHADER_CACHE_DIR')}
            deadline = Deadline(record)
            record = runner.condition(record, environment, deadline)
            records.append(record)
            try:
                require(not record.get('error'), 'Incomplete condition: ' + str(record.get('error')))
                with deadline.armed('condition acceptance'):
                    if source_check:
                        source_check()
                        deadline.check('source rechecked')
                    if index == 0 and 'host_begin' in record:
                        for key in ('quota', 'cgroup_path', 'driver_libraries'):
                            expected[key] = record['host_begin'][key]
                    validate_condition(record, expected)
                    deadline.check('condition validated')
                    # This immutable copy is the publication; later acceptance times
                    # and its hash live in block.json without rewriting the receipt.
                    publication = strict_json(json.dumps(record, allow_nan=False))
                    write(directory / 'condition.json', publication)
                    deadline.check('condition published')
                    published = read_json(directory / 'condition.json')
                    deadline.check('condition publication reread')
                    require(published == publication, 'Published condition differs')
                    validate_condition(published, expected)
                    record['publication_sha256'] = digest(directory / 'condition.json')
                    deadline.check('condition accepted after final read')
            except (Exception, KeyboardInterrupt) as error:
                record.setdefault('error', str(error))
                record['timeout'] = record.get('timeout', False) or isinstance(error, (TimeoutError, subprocess.TimeoutExpired))
                if str(error) != record['error']:
                    record['acceptance_error'] = str(error)
                deadline.observe('condition rejected')
                raise
        summary['evaluation'] = evaluate(records, expected)
        summary['passed'] = True
    except (Exception, KeyboardInterrupt) as error:
        summary['error'] = str(error)
    finally:
        try:
            summary['xvfb_cleanup'] = runner.stop()
        except Exception as error:
            summary['xvfb_cleanup'] = None
            summary['cleanup_error'] = str(error)
        if not summary['xvfb_cleanup'] or not summary['xvfb_cleanup']['pid_absent'] or not summary['xvfb_cleanup']['group_absent']:
            summary['passed'] = False
            summary['cleanup_error'] = 'Failed owned Xvfb cleanup'
            summary.setdefault('error', summary['cleanup_error'])
        summary['expected'] = expected
        write(output / 'block.json', safe_failure_report(summary))
    return summary


def main():
    def interrupted(_signum, _frame):
        raise KeyboardInterrupt('Diagnostic interrupted')
    signal.signal(signal.SIGINT, interrupted)
    signal.signal(signal.SIGTERM, interrupted)
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    staging = sub.add_parser('stage')
    staging.add_argument('--output', type=Path, required=True)
    sealing = sub.add_parser('seal')
    sealing.add_argument('--stage-record', type=Path, required=True)
    sealing.add_argument('--executable', type=Path, required=True)
    sealing.add_argument('--output', type=Path, required=True)
    running = sub.add_parser('run')
    running.add_argument('--seal', type=Path, required=True)
    running.add_argument('--output', type=Path, required=True)
    running.add_argument('--xvfb', required=True)
    running.add_argument('--display', required=True)
    running.add_argument('--cpus', required=True)
    args = parser.parse_args()
    if args.action == 'stage':
        print(json.dumps(stage(args.output), indent=2))
    elif args.action == 'seal':
        print(json.dumps(seal_payload(args.stage_record, args.executable, args.output), indent=2))
    else:
        require(sys.platform == 'linux', 'Run the fixed diagnostic on native Linux only')
        seal = read_json(args.seal)
        require(seal['source'] == source_identity(), 'Runtime source changed since staging')
        require(digest(seal['stage_record']) == seal['stage_sha256'], 'Stage record changed since sealing')
        cpus = sorted(int(value) for value in args.cpus.split(','))
        require(set(cpus) <= os.sched_getaffinity(0), 'CPUs outside allowed affinity')
        require(inventory(Path(read_json(seal['stage_record'])['stage'])) ==
                read_json(seal['stage_record'])['files'], 'Stage changed after export')
        seal['seal_sha256'] = digest(args.seal)
        with Path('/tmp/sightbreak-linux-profile-overhead.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            runner = NativeRunner(args.xvfb, args.display, args.output)
            def check_source():
                require(source_identity() == seal['source'], 'Repository source changed during block')
                require(digest(seal['stage_record']) == seal['stage_sha256'], 'Stage record changed during block')
                require(inventory(Path(read_json(seal['stage_record'])['stage'])) ==
                        read_json(seal['stage_record'])['files'], 'Staged source changed during block')
            summary = run_block(seal, args.output, cpus, runner, check_source)
        print(json.dumps({'passed': summary['passed'], 'error': summary.get('error')}, indent=2))
        raise SystemExit(0 if summary['passed'] else 1)


if __name__ == '__main__':
    main()
