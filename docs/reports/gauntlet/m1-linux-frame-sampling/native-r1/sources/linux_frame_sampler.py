"""Bounded read-only Linux CPU sampling for an already-owned offline client."""
from itertools import islice
import json
import math
import os
from pathlib import Path, PurePosixPath
import threading
import time


ENV_KEYS = ('DISPLAY', 'LIBGL_ALWAYS_SOFTWARE', 'LP_NUM_THREADS')
CPU_STAT_KEYS = ('usage_usec', 'user_usec', 'system_usec', 'nr_periods', 'nr_throttled', 'throttled_usec')
MAX_THREADS = 128


class CounterUnavailable(ValueError):
    def __init__(self, reason):
        self.reason = reason
        super().__init__(reason)


def unavailable(error):
    return {'available': False, 'reason': error.reason if isinstance(error, CounterUnavailable)
            else type(error).__name__, 'errno': getattr(error, 'errno', None)}


def read_bytes(path, limit=65536):
    with path.open('rb') as stream:
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise CounterUnavailable('read_bound_exceeded')
    return data


def attempt(read):
    try:
        return {'available': True, 'value': read()}
    except (OSError, ValueError) as error:
        return unavailable(error)


def process_stat(data):
    try:
        fields = data.rsplit(b')', 1)[1].split()
        return {'user_ticks': int(fields[11]), 'system_ticks': int(fields[12]),
                'start_time_ticks': int(fields[19])}
    except (ValueError, IndexError) as error:
        raise CounterUnavailable('invalid_proc_stat') from error


def cpu_max(data):
    try:
        quota, period = data.decode().split()
        if int(period) <= 0 or quota != 'max' and int(quota) <= 0:
            raise ValueError
        return {'quota_usec': None if quota == 'max' else int(quota),
                'unlimited': quota == 'max', 'period_usec': int(period)}
    except (ValueError, UnicodeError) as error:
        raise CounterUnavailable('invalid_cpu_max') from error


def cpu_stat(data):
    try:
        values = {key: int(value) for key, value in (line.split() for line in data.decode().splitlines())
                  if key in CPU_STAT_KEYS}
        return {'counters': values, 'unavailable_fields': [key for key in CPU_STAT_KEYS if key not in values]}
    except (ValueError, UnicodeError) as error:
        raise CounterUnavailable('invalid_cpu_stat') from error


class LinuxFrameSampler:
    """One owned worker; never discovers, signals or changes a process."""
    def __init__(self, process, output, observation, duration_seconds, *, proc=Path('/proc'), cgroup_root=Path('/sys/fs/cgroup')):
        if not math.isfinite(duration_seconds) or not 0 < duration_seconds <= 180:
            raise ValueError('Sampling duration must be within 180 seconds')
        self.process, self.output = process, Path(output)
        self.observation = Path(observation)
        self.proc, self.cgroup_root = proc, cgroup_root.resolve()
        self.pid = process.pid
        if process.poll() is not None:
            raise ValueError('Owned client already exited')
        self.identity = self._identity()
        self.duration = duration_seconds
        self.stop_event = threading.Event()
        self.samples, self.reason, self.error = 0, None, None
        self.stream = self.output.open('x', encoding='utf-8')
        self.thread = threading.Thread(target=self._run, name='offline-cpu-sampler', daemon=True)
        try:
            self.thread.start()
        except Exception:
            self.stream.close()
            raise

    def _stat(self, path):
        return process_stat(read_bytes(path))

    def _identity(self):
        return self._stat(self.proc / str(self.pid) / 'stat')['start_time_ticks']

    def _environment(self):
        values = {}
        for field in read_bytes(self.proc / str(self.pid) / 'environ', 1048576).split(b'\0'):
            key, separator, value = field.partition(b'=')
            if separator and key.decode(errors='replace') in ENV_KEYS:
                values[key.decode()] = value.decode(errors='replace')
        return {key: {'available': True, 'value': values[key]} if key in values
                else {'available': False, 'reason': 'not_set'} for key in ENV_KEYS}

    def _observation(self):
        state = json.loads(read_bytes(self.observation))
        if (not isinstance(state, dict) or type(state.get('schema')) is not int or state['schema'] != 1
                or state.get('scope') != 'debug_offline_read_only_observation'
                or state.get('scenario') != 'plant' or state.get('phase') not in ('buy', 'live', 'post', 'match_over')):
            raise CounterUnavailable('not_offline_plant_observation')
        fields = state.get('frame_diagnostics')
        if not isinstance(fields, dict):
            raise CounterUnavailable('frame_readbacks_unavailable')
        result = {'phase': state['phase'], 'frame_diagnostics': {}}
        for key in ('wall_msec', 'elapsed', 'simulation_tick', 'round_number', 'drawn_frames', 'time_scale'):
            value = state.get(key)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                raise CounterUnavailable('invalid_offline_clock_field')
            if key not in ('elapsed', 'time_scale') and type(value) is not int:
                raise CounterUnavailable('invalid_offline_clock_field')
            result[key] = value
        for key in ('read_begin_usec', 'read_end_usec', 'max_physics_steps_per_frame', 'physics_ticks_per_second',
                    'physics_jitter_fix', 'max_fps', 'process_frames', 'physics_frames', 'drawn_frames',
                    'process_max_seconds_last_engine_window', 'physics_step_max_seconds_last_engine_window',
                    'draw_calls_last_rendered_frame', 'primitives_last_rendered_frame', 'viewport_3d_scale'):
            value = fields.get(key)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
                raise CounterUnavailable('invalid_frame_readback_field')
            result['frame_diagnostics'][key] = value
        for key in ('viewport_visible_size', 'viewport_texture_size_pixels'):
            value = fields.get(key)
            if (not isinstance(value, list) or len(value) != 2
                    or any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or v < 0 for v in value)):
                raise CounterUnavailable('invalid_viewport_size')
            result['frame_diagnostics'][key] = value
        result['frame_diagnostics']['internal_3d_target_size'] = {'available': False, 'reason': 'not_exposed_by_inspected_api'}
        return result

    def _threads(self):
        directory = self.proc / str(self.pid) / 'task'
        entries = list(islice((path for path in directory.iterdir() if path.name.isdecimal()), MAX_THREADS + 1))
        result = []
        for path in sorted(entries[:MAX_THREADS], key=lambda value: int(value.name)):
            def read_thread():
                data = read_bytes(path / 'stat')
                stat = process_stat(data)
                name = data.partition(b'(')[2].rpartition(b')')[0]
                role = 'client_main' if int(path.name) == self.pid else 'mesa_llvmpipe' if name.startswith(b'llvmpipe') else 'other'
                return {'tid': int(path.name), 'role': role, **stat}
            result.append(attempt(read_thread))
        return {'threads': result, 'limit': MAX_THREADS, 'enumeration_truncated': len(entries) > MAX_THREADS}

    def _cgroup(self):
        lines = read_bytes(self.proc / str(self.pid) / 'cgroup').decode().splitlines()
        paths = [line[3:] for line in lines if line.startswith('0::')]
        if len(paths) != 1:
            raise CounterUnavailable('unified_cgroup_v2_unavailable')
        relative = PurePosixPath(paths[0])
        if not relative.is_absolute() or '..' in relative.parts or len(relative.parts) > 32:
            raise CounterUnavailable('unsafe_or_excessive_cgroup_path')
        directory = (self.cgroup_root / str(relative).lstrip('/')).resolve()
        if not directory.is_relative_to(self.cgroup_root):
            raise CounterUnavailable('cgroup_path_escapes_mount')
        groups = []
        while True:
            group_path = directory.relative_to(self.cgroup_root)
            groups.append({'path': '/' if group_path == Path('.') else '/' + group_path.as_posix(),
                           'scope': 'target' if not groups else 'ancestor',
                           'cpu_max': attempt(lambda: cpu_max(read_bytes(directory / 'cpu.max', 4096))),
                           'cpu_stat': attempt(lambda: cpu_stat(read_bytes(directory / 'cpu.stat', 4096)))})
            if directory == self.cgroup_root:
                break
            directory = directory.parent
        return groups

    def _write(self, row):
        self.stream.write(json.dumps(row) + '\n')
        self.stream.flush()

    def _owned(self):
        if self.process.poll() is not None:
            self.reason = 'owned_client_exited'
            return False
        try:
            if self._identity() == self.identity:
                return True
            self.reason = 'target_identity_changed'
        except (OSError, ValueError):
            self.reason = 'target_identity_unavailable'
        return False

    def _run(self):
        started = time.monotonic()
        try:
            environment = attempt(self._environment) if self._owned() else None
            if not self._owned():
                return
            self._write({'event': 'begin', 'pid': self.pid, 'controller_pid': os.getpid(),
                         'monotonic_ns': time.monotonic_ns(), 'wall_unix_ns': time.time_ns(),
                         'start_time_ticks': self.identity, 'cpu_ticks_per_second': os.sysconf('SC_CLK_TCK'),
                         'interval_seconds': 1, 'maximum_seconds': self.duration, 'environment': environment,
                         'cgroup_scope': 'Readable v2 target and ancestors in controller mount namespace; ancestor counters may include other processes.'})
            while time.monotonic() - started < self.duration and not self.stop_event.is_set():
                if not self._owned():
                    break
                row = {'event': 'sample', 'monotonic_begin_ns': time.monotonic_ns(), 'wall_unix_ns': time.time_ns(),
                       'process_cpu': attempt(lambda: self._stat(self.proc / str(self.pid) / 'stat')),
                       'allowed_cpus': attempt(lambda: sorted(os.sched_getaffinity(self.pid))),
                       'thread_cpu': attempt(self._threads), 'cgroup_cpu': attempt(self._cgroup),
                       'offline_frame': attempt(self._observation)}
                row['monotonic_end_ns'] = time.monotonic_ns()
                if not self._owned():
                    break
                self._write(row)
                self.samples += 1
                self.stop_event.wait(min(1.0, max(0.0, self.duration - (time.monotonic() - started))))
            if self.reason is None:
                self.reason = 'controller_stop' if self.stop_event.is_set() else 'duration_reached'
        except Exception as error:
            self.error, self.reason = unavailable(error), 'sampling_error'
        finally:
            try:
                self._write({'event': 'end', 'reason': self.reason, 'samples_written': self.samples,
                             'error': self.error, 'monotonic_ns': time.monotonic_ns()})
                self.stream.close()
            except Exception as error:
                self.error, self.reason = unavailable(error), 'output_error'
                try:
                    self.stream.close()
                except OSError:
                    pass

    def stop(self):
        self.stop_event.set()
        self.thread.join(timeout=2)
        return {'output': str(self.output), 'samples_written': self.samples, 'reason': self.reason,
                'error': self.error, 'thread_alive': self.thread.is_alive(), 'maximum_seconds': self.duration,
                'sampling_completed': not self.thread.is_alive() and self.error is None and self.samples > 0}
