#!/usr/bin/env python3
"""Stage and evaluate a separate Linux profiling-cadence diagnostic.

No shipping source is edited. Runtime requires a separately reviewed fresh export.
The OFF/ON/ON/OFF block screens median post-draw cadence at declared pacing;
it does not measure complete profiler overhead, GPU completion or gameplay cost.
"""
import argparse
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import signal
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
    record = json.loads(Path(stage_record).read_text())
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
    require(report['cold_before']['clock_usec'] < anchor['clock_usec'], 'Cold anchor was not separately timed')
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
            and readback['clock_usec'] > previous['clock_usec'], 'Readback lacks a separate later draw')
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
        content = json.loads(item['serialized'])
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


class NativeRunner:
    def __init__(self, xvfb, display, output):
        self.xvfb, self.display, self.output = xvfb, display, Path(output)
        self.server = None
        self.log = None

    def start(self):
        require(re.fullmatch(r':[0-9]+', self.display), 'Use a numbered display')
        socket = Path('/tmp/.X11-unix/X' + self.display[1:])
        require(not socket.exists(), 'Display already in use')
        self.log = (self.output / 'xvfb.log').open('wb')
        self.server = subprocess.Popen([self.xvfb, self.display, '-screen', '0', '1280x720x24', '-nolisten', 'tcp'],
                                       stdout=self.log, stderr=subprocess.STDOUT, start_new_session=True)
        self.server.sightbreak_start_ticks = pid_start(self.server.pid)
        write(self.output / 'xvfb-launch.json', {'command': self.server.args, 'pid': self.server.pid,
              'start_ticks': self.server.sightbreak_start_ticks, 'started_unix_ns': time.time_ns()})
        until = time.monotonic() + 5
        while not socket.exists():
            require(self.server.poll() is None and time.monotonic() < until, 'Xvfb readiness failure')
            time.sleep(0.05)

    def stop(self):
        result = cleanup(self.server) if self.server else None
        if result is not None:
            result.update(pid=self.server.pid, start_ticks=getattr(self.server, 'sightbreak_start_ticks', None))
        if self.log:
            self.log.close()
        return result

    def condition(self, record, environment):
        output = Path(record['output'])
        until = time.monotonic() + BOUND
        process = None
        with (output / 'client.log').open('wb') as log:
            try:
                import resource
                cpu_before = resource.getrusage(resource.RUSAGE_CHILDREN)
                process = subprocess.Popen(record['process_argv'], env=environment, cwd=output,
                                           stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
                record['pid'] = process.pid
                process.sightbreak_start_ticks = pid_start(process.pid)
                record['pid_start_ticks'] = process.sightbreak_start_ticks
                write(output / 'launch.json', record)
                for filename in ('ready.json', 'metrics.json'):
                    path = output / filename
                    while not path.exists():
                        require(process.poll() is None, 'Fixture exited before ' + filename)
                        if time.monotonic() >= until:
                            raise TimeoutError(filename)
                        time.sleep(0.05)
                    require(json.loads(path.read_text())['token'] == record['token'], 'Wrong fixture token')
                    if filename == 'ready.json':
                        record['actual_cmdline'], record['actual_environment'] = owned_launch_state(process.pid, record['selected_environment'])
                        require(record['actual_cmdline'] == record['engine_argv'], 'Actual engine command differs')
                        require(record['actual_environment'] == record['selected_environment'], 'Actual selected environment differs')
                        record['host_begin'] = host_snapshot(process.pid)
                        acknowledge(output / 'begin.ack', record['token'])
                    else:
                        record['host_end'] = host_snapshot(process.pid)
                        record['fixture'] = json.loads(path.read_text())
                        record['payload_after'] = digest(record['engine_argv'][0])
                        acknowledge(output / 'finish.ack', record['token'])
                process.wait(timeout=max(0.001, until - time.monotonic()))
                cpu_after = resource.getrusage(resource.RUSAGE_CHILDREN)
                record['rusage'] = {'user_seconds': cpu_after.ru_utime - cpu_before.ru_utime,
                                    'system_seconds': cpu_after.ru_stime - cpu_before.ru_stime,
                                    'scope': 'Completed owned child process including startup; no other child is waited in this interval'}
                record['exit_code'] = process.returncode
                final = cgroup_snapshot(os.getpid())
                require(final['cgroup_path'] == record['host_end']['cgroup_path'], 'Controller/client cgroup differs')
                record['host_end']['throttling'] = final['throttling']
                require(digest(output / 'proof.png') == record['fixture']['png_sha256'], 'Actual PNG differs')
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
        record['stdout'] = (output / 'client.log').read_text(errors='replace')
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
            record = runner.condition(record, environment)
            records.append(record)
            if source_check:
                source_check()
            if index == 0 and 'host_begin' in record:
                for key in ('quota', 'cgroup_path', 'driver_libraries'):
                    expected[key] = record['host_begin'][key]
            validate_condition(record, expected)
            write(directory / 'condition.json', record)
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
        seal = json.loads(args.seal.read_text())
        require(seal['source'] == source_identity(), 'Runtime source changed since staging')
        require(digest(seal['stage_record']) == seal['stage_sha256'], 'Stage record changed since sealing')
        cpus = sorted(int(value) for value in args.cpus.split(','))
        require(set(cpus) <= os.sched_getaffinity(0), 'CPUs outside allowed affinity')
        require(inventory(Path(json.loads(Path(seal['stage_record']).read_text())['stage'])) ==
                json.loads(Path(seal['stage_record']).read_text())['files'], 'Stage changed after export')
        seal['seal_sha256'] = digest(args.seal)
        with Path('/tmp/sightbreak-linux-profile-overhead.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            runner = NativeRunner(args.xvfb, args.display, args.output)
            def check_source():
                require(source_identity() == seal['source'], 'Repository source changed during block')
                require(digest(seal['stage_record']) == seal['stage_sha256'], 'Stage record changed during block')
                require(inventory(Path(json.loads(Path(seal['stage_record']).read_text())['stage'])) ==
                        json.loads(Path(seal['stage_record']).read_text())['files'], 'Staged source changed during block')
            summary = run_block(seal, args.output, cpus, runner, check_source)
        print(json.dumps({'passed': summary['passed'], 'error': summary.get('error')}, indent=2))
        raise SystemExit(0 if summary['passed'] else 1)


if __name__ == '__main__':
    main()
