"""Read actual failed-stage receipts and bounded offline readback spans only."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import statistics

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('receipts', type=Path)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
base = args.receipts / 'evidence'
bindings = []


def read(path, lines=False):
    if not path.is_file():
        return None
    data = path.read_bytes()
    bindings.append({'path': path.relative_to(base).as_posix(), 'bytes': len(data),
                     'sha256': hashlib.sha256(data).hexdigest()})
    text = data.decode('utf-8')
    return [json.loads(line) for line in text.splitlines() if line] if lines else json.loads(text)


def state(row):
    keys = ('schema', 'scope', 'scenario', 'wall_msec', 'elapsed', 'drawn_frames', 'simulation_tick',
            'time_scale', 'phase', 'time_left', 'round_number', 'attack_score', 'defend_score',
            'objective_state', 'objective_timer', 'interaction_progress', 'local_contribution',
            'completion_calls', 'events_dropped', 'local_actor', 'local_input', 'ui', 'frame_diagnostics')
    return {key: row[key] for key in keys if key in row}


def distribution(values):
    ordered = sorted(values)
    if not ordered:
        return None
    return {'count': len(ordered), 'min': ordered[0], 'median': statistics.median(ordered),
            'p95_nearest_rank': ordered[math.ceil(.95 * len(ordered)) - 1], 'max': ordered[-1]}


stages = []
traces = []
for name in ('offline-input', 'offline-plant', 'offline-defuse', 'offline-full-match'):
    directory = base / name
    receipt = read(directory / 'results.json')
    commands = read(directory / 'commands.json')
    actions = read(directory / 'actions.json')
    if actions is None:
        actions = read(directory / 'actions.jsonl', lines=True)
    actions = actions or []
    if isinstance(actions, dict):
        raise ValueError('Unexpected action container at ' + name)
    if receipt is None:
        stages.append({'scenario': name, 'results_retained': False})
        continue
    observed = [row.get('state', row.get('observed')) for row in actions
                if isinstance(row.get('state', row.get('observed')), dict)]
    waits = [row for row in actions if row.get('event') in ('wait_completed', 'observed')]
    snapshot_rows = [row for row in observed if 'phase' in row]
    stages.append({'scenario': name, 'results_retained': True, 'passed': receipt.get('passed'),
                   'error': receipt.get('error'), 'elapsed_seconds': receipt.get('elapsed_seconds'),
                   'cleanup_errors': receipt.get('cleanup_errors'),
                   'initial_exit': receipt.get('initial_exit'), 'reopened_exit': receipt.get('reopened_exit'),
                   'source': receipt.get('source', receipt.get('authority_source')),
                   'last_offline_observation': receipt.get('last_offline_observation'),
                   'last_state': state(snapshot_rows[-1]) if snapshot_rows else None,
                   'last_six_actions': actions[-6:], 'last_six_waits': waits[-6:],
                   'capture_names': sorted({str(row['capture']) for row in actions if 'capture' in row}),
                   'partial_checks': receipt.get('partial_checks'),
                   'actual_commands': commands if commands is not None else receipt.get('commands'),
                   'receipt_fields': sorted(receipt)})
    for path in sorted(directory.rglob('events.jsonl')):
        # Trace directories come directly from the retained official artifact;
        # no process discovery or external clock joins are performed.
        rows = read(path, lines=True)
        status = read(path.with_name('status.json'))
        candidates = [(row, path.name) for row in rows if isinstance(row.get('frame_diagnostics'), dict)]
        if isinstance(status, dict) and isinstance(status.get('frame_diagnostics'), dict):
            candidates.append((status, 'status.json'))
        samples = {}
        invalid = []
        for row, origin in candidates:
            frame = row['frame_diagnostics']
            begin, end = frame.get('read_begin_usec'), frame.get('read_end_usec')
            if type(begin) is not int or type(end) is not int or end < begin:
                invalid.append({'origin': origin, 'begin': begin, 'end': end})
                continue
            key = (begin, end, row.get('wall_msec'), row.get('simulation_tick'))
            samples.setdefault(key, {'origin': origin, 'span_usec': end - begin, 'state': state(row)})
        unique = sorted(samples.values(), key=lambda item: item['state']['wall_msec'])
        counters = ('process_frames', 'physics_frames', 'drawn_frames')
        maxima = ('process_max_seconds_last_engine_window', 'physics_step_max_seconds_last_engine_window')
        monitor_distributions = {}
        for key in maxima:
            values = [item['state']['frame_diagnostics'].get(key) for item in unique]
            if all(type(value) in (int, float) and math.isfinite(value) and value >= 0 for value in values):
                monitor_distributions[key] = distribution(values)
            else:
                monitor_distributions[key] = {'invalid_values': values}
        record = {'scenario': name, 'trace': path.parent.relative_to(base).as_posix(),
                  'event_records': len(rows), 'candidate_snapshots_in_events_and_last_status': len(candidates),
                  'unique_retained_snapshots': len(unique), 'invalid_readback_spans': invalid,
                  'readback_span_microseconds': distribution([item['span_usec'] for item in unique]),
                  'engine_window_maxima_seconds': monitor_distributions,
                  'first_retained_snapshot': unique[0] if unique else None,
                  'last_retained_snapshot': unique[-1] if unique else None}
        if unique:
            first, last = unique[0]['state'], unique[-1]['state']
            record['native_observed_interval'] = {
                'wall_msec_delta': last['wall_msec'] - first['wall_msec'],
                'game_simulation_ticks_delta': last['simulation_tick'] - first['simulation_tick'],
                'game_elapsed_seconds_delta': last['elapsed'] - first['elapsed'],
                **{key + '_delta': last['frame_diagnostics'][key] - first['frame_diagnostics'][key] for key in counters}}
        traces.append(record)

result = {'run_id': 39940242244, 'source_commit': '49ae54b0e4f5d880bdf06e4eb783a616b2dff684',
          'stages': stages, 'native_frame_readbacks': traces, 'original_file_bindings': bindings,
          'measurement_limits': [
              'Spans cover only the read_begin through read_end getter/dictionary block; they exclude earlier snapshot work, later serialization/I/O and controller work.',
              'Events and the final status are sparse retained snapshots, not the complete five-Hz status stream; repeated snapshots are deduplicated within each process trace.',
              'Process and physics monitor values are maxima from the last engine statistics window; repeated rows do not establish independent windows or CPU function costs.',
              'Counter deltas describe this hosted native process interval and include engine activity while game simulation may be paused; no physical FPS or latency estimate is made.',
              'There is no matched observer-off or bot-guard-off control; these observations cannot attribute either failure or total overhead to a source delta.']}
args.output.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({'stages': [{key: stage.get(key) for key in ('scenario', 'passed', 'error', 'elapsed_seconds', 'cleanup_errors')}
                              for stage in stages],
                  'trace_count': len(traces), 'readback_span_summaries': [{key: trace[key] for key in
                    ('trace', 'unique_retained_snapshots', 'readback_span_microseconds')} for trace in traces]}))
