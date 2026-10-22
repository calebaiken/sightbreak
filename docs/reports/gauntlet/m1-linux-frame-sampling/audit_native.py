#!/usr/bin/env python3
"""Recompute the frozen diagnostic receipt; no engine, process reads or mutations."""
import hashlib
import json
from pathlib import Path
import statistics


ROOT = Path(__file__).resolve().parent
RAW = ROOT / 'native-r1'
PLANT = RAW / 'native-plant'


def read(path):
    return json.loads(path.read_text())


def rows(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def spread(values):
    return {'count': len(values), 'minimum': min(values), 'median': statistics.median(values), 'maximum': max(values)}


def action(actions, event, key=None, value=None):
    matches = [row for row in actions if row['event'] == event and (key is None or row.get(key) == value)]
    assert len(matches) == 1
    return matches[0]


def bracket(start, end):
    a, b = start['observed'], end['observed']
    ticks, frames = b['simulation_tick'] - a['simulation_tick'], b['drawn_frames'] - a['drawn_frames']
    assert abs(b['elapsed'] - a['elapsed'] - ticks / 60) < 1e-9
    return {'driver_wall_seconds': end['seconds'] - start['seconds'], 'observed_tick_delta': ticks,
            'observed_simulation_seconds': ticks / 60, 'observed_drawn_frame_delta': frames,
            'observed_ticks_per_drawn_frame': ticks / frames,
            'start_tick': a['simulation_tick'], 'end_tick': b['simulation_tick'],
            'clock_limit': 'Engine observations can precede driver actions; clock domains are not equated.'}


index = read(RAW / 'payload-index.json')
for entry in index['files']:
    data = (RAW / entry['path']).read_bytes()
    assert len(data) == entry['bytes'] and hashlib.sha256(data).hexdigest() == entry['sha256']
result, status = read(PLANT / 'results.json'), read(PLANT / 'trace/status.json')
actions, events = rows(PLANT / 'actions.jsonl'), rows(PLANT / 'trace/events.jsonl')
samples = rows(PLANT / 'linux-frame-samples.jsonl')
begin, end = samples[0], samples[-1]
assert begin['event'] == 'begin' and end['event'] == 'end'
samples = [row for row in samples if row['event'] == 'sample']
assert len(samples) == end['samples_written'] == result['linux_frame_diagnostics']['samples_written'] == 132
assert not result['passed'] and result['error'] == 'Natural next round after objective resolution'
assert result['linux_frame_diagnostics']['sampling_completed'] and not result['linux_frame_diagnostics']['thread_alive']
assert result['linux_frame_diagnostics']['error'] is None and not result['cleanup_errors']
assert status['phase'] == 'post' and status['round_number'] == 1 and abs(status['time_left'] - 0.383333333333346) < 1e-10
identity = begin['start_time_ticks']
assert all(row['process_cpu']['available'] and row['process_cpu']['value']['start_time_ticks'] == identity for row in samples)
assert all(row['monotonic_end_ns'] >= row['monotonic_begin_ns'] for row in samples)
intervals = [(b['monotonic_begin_ns'] - a['monotonic_begin_ns']) / 1e9 for a, b in zip(samples, samples[1:])]
assert min(intervals) >= 1
available = [row for row in samples if row['offline_frame']['available']]
assert len(available) == 123
frames = [row['offline_frame']['value']['frame_diagnostics'] for row in available]
assert all(row['max_physics_steps_per_frame'] == 8 and row['physics_ticks_per_second'] == 60
           and row['max_fps'] == 60 and row['physics_jitter_fix'] == 0.5 and row['viewport_3d_scale'] == 1
           and row['viewport_texture_size_pixels'] == [1280, 720] and row['viewport_visible_size'] == [1280, 720]
           and row['process_frames'] == row['drawn_frames'] for row in frames)
assert all(row['offline_frame']['value']['time_scale'] == 1 for row in available)
assert set(begin['environment']['value']) == {'DISPLAY', 'LIBGL_ALWAYS_SOFTWARE', 'LP_NUM_THREADS'}
assert begin['environment']['value']['LP_NUM_THREADS']['value'] == '2'
assert begin['environment']['value']['LIBGL_ALWAYS_SOFTWARE']['value'] == '1'

cpu_clock = begin['cpu_ticks_per_second']
def cpu_interval(selected):
    first, last = selected[0], selected[-1]
    a, b = first['process_cpu']['value'], last['process_cpu']['value']
    wall = (last['monotonic_begin_ns'] - first['monotonic_begin_ns']) / 1e9
    return {'sample_clock_wall_seconds': wall,
            'process_cpu_seconds': ((b['user_ticks'] + b['system_ticks']) - (a['user_ticks'] + a['system_ticks'])) / cpu_clock}


def role_cpu(selected):
    by_thread = {}
    for row in selected:
        assert row['thread_cpu']['available'] and not row['thread_cpu']['value']['enumeration_truncated']
        for thread in row['thread_cpu']['value']['threads']:
            assert thread['available']
            value = thread['value']
            key = value['tid'], value['start_time_ticks'], value['role']
            by_thread.setdefault(key, []).append(value['user_ticks'] + value['system_ticks'])
    result = {}
    for (_, _, role), values in by_thread.items():
        result[role] = result.get(role, 0) + (values[-1] - values[0]) / cpu_clock
    return {'cpu_seconds_by_thread_role': result,
            'scope': 'Per-thread first-to-last observed CPU deltas; late-started or vanished threads do not cover the whole process interval.'}


phase_stats = {}
for phase in ('buy', 'live', 'post'):
    selected = [row for row in available if row['offline_frame']['value']['phase'] == phase]
    values = [row['offline_frame']['value']['frame_diagnostics'] for row in selected]
    phase_stats[phase] = {
        'sample_count': len(selected), 'cpu': cpu_interval(selected), 'threads': role_cpu(selected),
        'process_window_max_seconds': spread([row['process_max_seconds_last_engine_window'] for row in values]),
        'physics_step_window_max_seconds': spread([row['physics_step_max_seconds_last_engine_window'] for row in values]),
        'readback_collection_microseconds': spread([row['read_end_usec'] - row['read_begin_usec'] for row in values]),
    }

groups = {}
for row in samples:
    assert row['cgroup_cpu']['available']
    for group in row['cgroup_cpu']['value']:
        assert group['cpu_max']['available'] and group['cpu_stat']['available']
        assert not group['cpu_stat']['value']['unavailable_fields']
        groups.setdefault(group['path'], []).append(group)
group_stats = {}
for path, values in groups.items():
    a, b = values[0]['cpu_stat']['value']['counters'], values[-1]['cpu_stat']['value']['counters']
    group_stats[path] = {'quota_readback': values[0]['cpu_max']['value'],
                         'counter_deltas': {key: b[key] - a[key] for key in a},
                         'scope': 'Readable cgroup counter; may include other processes and does not expose hidden ancestors.'}

failure = action(actions, 'failure')
hold = result['objective_hold']
cleanup = read(RAW / 'post-run-cleanup.json')
assert not cleanup['source_after']['source_dirty'] and cleanup['manifest_still_valid']
assert not cleanup['display_socket_exists'] and not any(row['proc_exists'] for row in cleanup['owned_pid_presence'])
report = {
    'scope': 'Builder recomputation; diagnostic receipt only, original gameplay failure preserved.',
    'payload_index_sha256': hashlib.sha256((RAW / 'payload-index.json').read_bytes()).hexdigest(),
    'payload_files_verified': len(index['files']), 'source': result['source'],
    'native_result': {'passed': result['passed'], 'error': result['error'], 'elapsed_seconds': result['elapsed_seconds'],
                      'partial_checks': result['partial_checks'], 'objective_resolution': result['objective_resolution'],
                      'objective_hold': hold, 'final_time_left': status['time_left']},
    'initial_capture_to_failure': bracket(action(actions, 'capture_end', 'capture', '02-offline-initial-conditions'), failure),
    'resolution_capture_to_failure': bracket(action(actions, 'capture_end', 'capture', '07-objective-round-resolved'), failure),
    'sampler': {'summary': result['linux_frame_diagnostics'], 'begin': begin, 'end': end,
                'sample_count': len(samples), 'available_frame_rows': len(available),
                'unavailable_frame_reasons': [row['offline_frame'] for row in samples if not row['offline_frame']['available']],
                'cadence_seconds': spread(intervals),
                'external_collection_milliseconds': spread([(row['monotonic_end_ns'] - row['monotonic_begin_ns']) / 1e6 for row in samples]),
                'whole_interval_cpu': cpu_interval(samples), 'whole_interval_threads': role_cpu(samples)},
    'phases': phase_stats, 'cgroups': group_stats, 'cleanup': cleanup,
    'monitor_limits': ['Engine publishes prior-window maxima at roughly one-second refresh; repeated or phase-lagged values are expected.',
                       'Process monitor includes callbacks, renderer sync and draw; physics monitor is the largest individual step.',
                       'Readback collection duration excludes serialization, existing file writes and external sampler cost.',
                       'No internal 3D target size or physical GPU timing is available.'],
}
print(json.dumps(report, indent=2) + '\n', end='')
