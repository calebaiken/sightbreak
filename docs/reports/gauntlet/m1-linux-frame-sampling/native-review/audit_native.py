"""Recompute actual instrumented native receipts; reads files, never runs engine."""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path

EXPECTED_SOURCE = '8afe0cc6b4c9051d3649a82bbcb4c8de8f947f9c'
EXPECTED_CONTROLLER = 'dd4558ebd1bbdeea94f2261613aac347b7ac1c80c41df73d69eb885f7ea66688'
FRAME_KEYS = set(('read_begin_usec read_end_usec max_physics_steps_per_frame physics_ticks_per_second '
                  'physics_jitter_fix max_fps process_frames physics_frames drawn_frames '
                  'process_max_seconds_last_engine_window physics_step_max_seconds_last_engine_window '
                  'draw_calls_last_rendered_frame primitives_last_rendered_frame viewport_3d_scale '
                  'viewport_visible_size viewport_texture_size_pixels internal_3d_target_size').split())
OFFLINE_KEYS = set('phase frame_diagnostics wall_msec elapsed simulation_tick round_number drawn_frames time_scale'.split())


def load(path):
    return json.loads(path.read_text())


def lines(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def extent(values):
    return [min(values), max(values)] if values else None


def action_interval(first, last):
    a, b = first['observed'], last['observed']
    ticks, draws = b['simulation_tick'] - a['simulation_tick'], b['drawn_frames'] - a['drawn_frames']
    return dict(driver_wall_seconds=last['seconds'] - first['seconds'],
                simulation_tick_delta=ticks, simulation_seconds=b['elapsed'] - a['elapsed'],
                drawn_frame_delta=draws, ticks_per_drawn_frame=ticks / draws,
                boundary_limit='Action clock bracket; associated engine observations may precede their actions.')


def thread_map(row):
    value = row['thread_cpu']
    if not value['available']:
        return {}
    return {(item['value']['tid'], item['value']['start_time_ticks']): item['value']
            for item in value['value']['threads'] if item['available']}


def interval(rows, tick_hz):
    first, last = rows[0], rows[-1]
    a, b = [row['offline_frame']['value'] for row in (first, last)]
    fa, fb = a['frame_diagnostics'], b['frame_diagnostics']
    wall = (last['monotonic_begin_ns'] - first['monotonic_begin_ns']) / 1e9
    cpu = None
    if first['process_cpu']['available'] and last['process_cpu']['available']:
        ca, cb = [row['process_cpu']['value'] for row in (first, last)]
        cpu = sum(cb[key] - ca[key] for key in ('user_ticks', 'system_ticks')) / tick_hz
    ta, tb = thread_map(first), thread_map(last)
    roles = Counter()
    for key in ta.keys() & tb.keys():
        roles[tb[key]['role']] += sum(tb[key][field] - ta[key][field] for field in ('user_ticks', 'system_ticks')) / tick_hz
    frames = [row['offline_frame']['value']['frame_diagnostics'] for row in rows]
    ticks, processes, draws = b['simulation_tick'] - a['simulation_tick'], fb['process_frames'] - fa['process_frames'], fb['drawn_frames'] - fa['drawn_frames']
    return dict(samples=len(rows), first_phase=a['phase'], last_phase=b['phase'],
                first_round=a['round_number'], last_round=b['round_number'],
                sampler_monotonic_seconds=wall, observed_engine_msec_delta=b['wall_msec'] - a['wall_msec'],
                simulation_tick_delta=ticks, observed_simulation_seconds=b['elapsed'] - a['elapsed'],
                process_frame_delta=processes, drawn_frame_delta=draws,
                ticks_per_process_frame=ticks / processes if processes else None,
                process_minus_drawn_delta=processes - draws,
                sampled_process_monitor_max_range_seconds=extent([f['process_max_seconds_last_engine_window'] for f in frames]),
                sampled_physics_step_monitor_max_range_seconds=extent([f['physics_step_max_seconds_last_engine_window'] for f in frames]),
                snapshot_readback_usec_range=extent([f['read_end_usec'] - f['read_begin_usec'] for f in frames]),
                process_cpu_seconds=cpu, process_cpu_seconds_per_sampler_wall_second=cpu / wall if wall and cpu is not None else None,
                stable_thread_cpu_seconds_by_role=dict(roles),
                stable_threads_compared=len(ta.keys() & tb.keys()),
                boundary_limit='Frame observations can precede external reads; monitor windows overlap and cannot partition frame wall time.')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--native', type=Path, required=True)
    args = parser.parse_args()
    raw = args.native
    results, commands = load(raw / 'results.json'), load(raw / 'commands.json')
    sample_rows = lines(raw / 'linux-frame-samples.jsonl')
    header, end = sample_rows[0], sample_rows[-1]
    samples = [row for row in sample_rows if row['event'] == 'sample']
    valid = [row for row in samples if row['offline_frame']['available']]
    events, actions = lines(raw / 'trace/events.jsonl'), lines(raw / 'actions.jsonl')
    initial, terminal = events[0], load(raw / 'trace/status.json')
    client = next(command for command in commands if command['name'] == 'client')
    frame_values = [row['offline_frame']['value']['frame_diagnostics'] for row in valid]
    spacings = [(b['monotonic_begin_ns'] - a['monotonic_begin_ns']) / 1e9 for a, b in zip(samples, samples[1:])]
    environments = header['environment']['value']
    settings = initial['initial_profile']['settings']
    failure = next(row for row in actions if row['event'] == 'failure')
    initial_capture = next(row for row in actions if row['event'] == 'capture_end' and row.get('capture') == '02-offline-initial-conditions')
    resolved_capture = next(row for row in actions if row['event'] == 'capture_end' and row.get('capture') == '07-objective-round-resolved')
    initial_bracket, post_bracket = action_interval(initial_capture, failure), action_interval(resolved_capture, failure)
    sample_keys = set('event monotonic_begin_ns monotonic_end_ns wall_unix_ns process_cpu allowed_cpus thread_cpu cgroup_cpu offline_frame'.split())
    thread_values = [row['thread_cpu']['value'] for row in samples if row['thread_cpu']['available']]
    thread_entries = [item['value'] for value in thread_values for item in value['threads'] if item['available']]
    numeric_frame_keys = FRAME_KEYS - {'viewport_visible_size', 'viewport_texture_size_pixels', 'internal_3d_target_size'}
    checks = dict(
        exact_clean_source=results['source']['source_commit'] == EXPECTED_SOURCE and not results['source']['source_dirty'] and not results['source']['source_game_dirty'],
        export_source_equals_runtime=all(results['source'][key] == results['artifact_source'][key] for key in results['source']),
        executable_hash_matches=results['executable_sha256'] == results['artifact_source']['artifact']['sha256'],
        engine_version=results['engine'] == '4.7.2.stable.official.ed1daf0bf',
        controller_hash=results['controller_sha256'] == EXPECTED_CONTROLLER,
        original_whole_budget=results['timeout_seconds'] == 180,
        original_native_mode=results['scenario'] == 'plant' and results['target'] == 'linux' and '--linux-frame-diagnostics' in results['controller_command'],
        original_selectors=environments['DISPLAY']['value'] == ':122' and environments['LIBGL_ALWAYS_SOFTWARE']['value'] == '1' and environments['LP_NUM_THREADS']['value'] == '2',
        environment_whitelist=set(environments) == {'DISPLAY', 'LIBGL_ALWAYS_SOFTWARE', 'LP_NUM_THREADS'},
        original_settings=settings['graphics_quality'] == 1 and settings['render_scale'] == 1 and settings['fps_limit'] == 60,
        original_rules=initial['rules'] == dict(buy_seconds=15, round_seconds=100, device_seconds=35, plant_seconds=3, defuse_seconds=5, win_score=7),
        offline_authority_contract=initial['scope'] == 'debug_offline_read_only_observation' and initial['protocol'] == 6 and initial['prediction_enabled'] is False and len(initial['actors']) == 10,
        sampler_identity=header['pid'] == client['pid'] and all(row['process_cpu']['available'] and row['process_cpu']['value']['start_time_ticks'] == header['start_time_ticks'] for row in samples),
        sampler_limits=0 < header['maximum_seconds'] <= 180 and header['interval_seconds'] == 1 and len(samples) <= math.ceil(header['maximum_seconds']),
        sample_starts_within_bound=all(0 <= (row['monotonic_begin_ns'] - header['monotonic_ns']) / 1e9 < header['maximum_seconds'] for row in samples),
        cadence_no_bursts=bool(spacings) and min(spacings) >= 1,
        all_reads_ordered=all(row['monotonic_begin_ns'] <= row['monotonic_end_ns'] for row in samples),
        frame_whitelist=all(set(row['offline_frame']['value']) == OFFLINE_KEYS and set(row['offline_frame']['value']['frame_diagnostics']) == FRAME_KEYS for row in valid),
        sample_top_level_whitelist=all(set(row) == sample_keys for row in samples),
        frame_numeric_types=all(not isinstance(f[key], bool) and isinstance(f[key], (int, float)) and math.isfinite(f[key]) for f in frame_values for key in numeric_frame_keys),
        thread_bounds=all(value['limit'] == 128 and len(value['threads']) <= 128 for value in thread_values),
        thread_name_privacy=all(set(item) == {'tid', 'role', 'user_ticks', 'system_ticks', 'start_time_ticks'} and item['role'] in ('client_main', 'mesa_llvmpipe', 'other') for item in thread_entries),
        readbacks_preserved=all(f['max_physics_steps_per_frame'] == 8 and f['physics_ticks_per_second'] == 60 and f['physics_jitter_fix'] == .5 and f['max_fps'] == 60 and f['viewport_3d_scale'] == 1 and f['viewport_visible_size'] == [1280, 720] and f['viewport_texture_size_pixels'] == [1280, 720] and f['internal_3d_target_size']['available'] is False for f in frame_values),
        readback_order=all(f['read_begin_usec'] <= f['read_end_usec'] for f in frame_values),
        time_scale_unchanged=all(row['offline_frame']['value']['time_scale'] == 1 for row in valid),
        sampler_end=end['event'] == 'end' and end['samples_written'] == len(samples) and end['error'] is None,
        stopped_worker=results['linux_frame_diagnostics']['thread_alive'] is False and results['linux_frame_diagnostics']['sampling_completed'] is True and results['linux_frame_diagnostics']['error'] is None,
        cleanup_report=results['cleanup_errors'] == [],
        no_recorder_in_commands=all(command['name'] in ('xvfb', 'client') for command in commands) and not list(raw.rglob('*.mp4')),
        native_failed_original_next_buy=results['passed'] is False and results['error'] == 'Natural next round after objective resolution' and 12 <= post_bracket['driver_wall_seconds'] < 12.2,
        restart_unreached='reopened' not in {command['name'] for command in commands},
    )
    groups = []
    for row in valid:
        state = row['offline_frame']['value']
        key = (state['round_number'], state['phase'])
        if not groups or groups[-1][0] != key:
            groups.append((key, []))
        groups[-1][1].append(row)
    cgroups = []
    if samples[0]['cgroup_cpu']['available'] and samples[-1]['cgroup_cpu']['available']:
        ga, gb = [row['cgroup_cpu']['value'] for row in (samples[0], samples[-1])]
        by_path = {group['path']: group for group in gb}
        for first in ga:
            last = by_path.get(first['path'])
            if last and first['cpu_stat']['available'] and last['cpu_stat']['available']:
                ca, cb = first['cpu_stat']['value']['counters'], last['cpu_stat']['value']['counters']
                cgroups.append(dict(path=first['path'], scope=first['scope'], cpu_max=last['cpu_max'],
                                    delta={key: cb[key] - ca[key] for key in ca.keys() & cb.keys()},
                                    attribution='Cgroup shared counters are not client-only CPU or descheduling evidence.'))
    output = dict(raw=str(raw), checks=checks, passed=all(checks.values()), native_passed=results['passed'], native_error=results.get('error'),
                  native_partial_checks=results['partial_checks'], original_next_buy_budget_seconds=12,
                  terminal={key: terminal[key] for key in ('wall_msec', 'elapsed', 'simulation_tick', 'phase', 'time_left', 'round_number', 'objective_state')},
                  header=header, sampler_end=end, samples=len(samples), frame_samples=len(valid),
                  unavailable_frame_reasons=dict(Counter(row['offline_frame'].get('reason') for row in samples if not row['offline_frame']['available'])),
                  spacing_seconds_range=extent(spacings), sample_read_seconds_range=extent([(row['monotonic_end_ns'] - row['monotonic_begin_ns']) / 1e9 for row in samples]),
                  all_valid_frames=interval(valid, header['cpu_ticks_per_second']),
                  phase_intervals=[interval(group, header['cpu_ticks_per_second']) for _, group in groups if len(group) >= 2],
                  cgroup_deltas=cgroups, commands=commands,
                  thread_count_range=extent([len(value['threads']) for value in thread_values]),
                  any_thread_enumeration_truncated=any(value['enumeration_truncated'] for value in thread_values),
                  initial_capture_to_failure=initial_bracket, resolved_capture_to_failure=post_bracket,
                  last_actions=[{key: row[key] for key in ('event', 'seconds', 'label', 'error', 'capture') if key in row} for row in actions[-8:]],
                  input_sha256={path.relative_to(raw).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(raw.rglob('*')) if path.is_file()})
    print(json.dumps(output, indent=2))
    assert output['passed']


if __name__ == '__main__':
    main()
