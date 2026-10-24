#!/usr/bin/env python3
"""Recompute the one retained profile capability attempt without engine use."""
import argparse
from collections import Counter, defaultdict
import gzip
import hashlib
import json
import math
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
RUNTIME_SOURCE = 'b1a131ab4790ac84371b54ee236441a66faf4125'


def read(path):
    data = path.read_bytes()
    return gzip.decompress(data) if path.suffix == '.gz' else data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence', type=Path, default=HERE / 'native-r1')
    args = parser.parse_args()
    evidence = args.evidence
    index = json.loads((evidence / 'payload-index.json').read_text())
    for item in index['files']:
        path = evidence / item['archive_path']
        archive = path.read_bytes()
        assert len(archive) == item['archive_bytes']
        assert hashlib.sha256(archive).hexdigest() == item['archive_sha256']
        raw = read(path)
        assert len(raw) == item['raw_bytes']
        assert hashlib.sha256(raw).hexdigest() == item['raw_sha256']
    result = json.loads((evidence / 'native-plant/results.json').read_text())
    preflight = json.loads((evidence / 'preflight.json').read_text())
    cleanup = json.loads((evidence / 'post-run-cleanup.json').read_text())
    exported = json.loads((evidence / 'export-source-verified.json').read_text())
    assert result['source'] == preflight['source'] == cleanup['source_after'] == exported['source']
    assert result['source']['source_commit'] == RUNTIME_SOURCE and not result['source']['source_dirty']
    assert hashlib.sha256((evidence / 'sources/scripts/verify_offline_match.py').read_bytes()).hexdigest() == result['controller_sha256']
    assert result['passed'] is False and result['error'] == 'Objective scenario live phase'
    assert result['cleanup_errors'] == [] and result['partial_checks'] == {}
    assert result['initial_exit'] is None and result['reopened_exit'] is None
    assert [item['name'] for item in result['commands']] == ['xvfb', 'client']
    command = result['commands'][1]['command']
    assert command[1] == '--gpu-profile' and command.index('--gpu-profile') < command.index('--')
    assert '--linux-gpu-profile' in result['controller_command']
    assert '--linux-frame-diagnostics' not in result['controller_command']
    assert result['timeout_seconds'] == 180 and '--offline-seed=42' in command
    assert cleanup['sampler_output_absent'] and cleanup['controller_absent'] and cleanup['display_socket_absent'] and cleanup['display_lock_absent']
    assert all(item['pid_absent'] and item['process_group_absent'] for item in cleanup['owned_children'])
    status = json.loads((evidence / 'native-plant/trace/status.json').read_text())
    assert status['phase'] == 'buy' and status['round_number'] == 1 and status['time_left'] > 0
    settings = result['initial']['initial_profile']['settings']
    assert settings['graphics_quality'] == 1 and settings['render_scale'] == 1 and settings['fps_limit'] == 60
    assert result['initial']['time_scale'] == 1 and len(result['initial']['actors']) == 10
    blocks = []
    for line_number, line in enumerate(read(evidence / 'native-plant/client.log.gz').decode().splitlines(), 1):
        header = re.fullmatch(r'GPU PROFILE \(total (.+)ms\):\s*', line)
        row = re.fullmatch(r'\t-(.+): (.+)ms', line)
        if header:
            total = float(header[1])
            assert math.isfinite(total) and total >= 0
            blocks.append({'stdout_line': line_number, 'header_latest_profile_total_ms': total, 'rows': []})
        elif row:
            assert blocks, 'Task row lacks a header'
            value = float(row[2])
            assert math.isfinite(value) and value > 0.01
            blocks[-1]['rows'].append({'name': row[1], 'reported_interval_average_ms': value})
    capable = [block for block in blocks if block['rows']]
    assert capable, 'No intact finite header with positive named task rows'
    values = defaultdict(list)
    largest = Counter()
    for block in capable:
        largest[max(block['rows'], key=lambda item: item['reported_interval_average_ms'])['name']] += 1
        for row in block['rows']:
            values[row['name']].append(row['reported_interval_average_ms'])
    actions = [json.loads(line) for line in (evidence / 'native-plant/actions.jsonl').read_text().splitlines()]
    failure = next(item for item in actions if item['event'] == 'failure')
    initial_capture = next(item for item in actions if item['event'] == 'capture_end' and item['capture'] == '02-offline-initial-conditions')
    print(json.dumps({'runtime_source': RUNTIME_SOURCE, 'archive_payloads_verified': len(index['files']),
                      'profile_capability_bytes_present': True, 'profile_header_count': len(blocks),
                      'row_bearing_blocks': len(capable), 'largest_printed_task_counts': dict(largest),
                      'task_reported_ranges_ms': {name: {'printed_blocks': len(items), 'min': min(items), 'max': max(items)} for name, items in sorted(values.items())},
                      'header_total_range_ms': {'min': min(block['header_latest_profile_total_ms'] for block in blocks), 'max': max(block['header_latest_profile_total_ms'] for block in blocks)},
                      'ordinary_flow_passed': False, 'ordinary_error': result['error'],
                      'controller_elapsed_seconds': result['elapsed_seconds'],
                      'initial_capture_end_to_failure_driver_seconds': failure['seconds'] - initial_capture['seconds'],
                      'terminal': {key: status[key] for key in ('phase', 'round_number', 'elapsed', 'time_left', 'simulation_tick', 'drawn_frames', 'objective_state')},
                      'plant_next_buy_and_restart_reached': False,
                      'source_unchanged_through_cleanup': True, 'owned_cleanup_passed': True,
                      'semantics': 'Historical buffered query blocks. Rows average task intervals over reporting draw calls; header uses latest retained profile. No phase/source-frame identities, CPU attribution, physical FPS, overhead, causality or improvement inference.',
                      'blocks': blocks}, indent=2))


if __name__ == '__main__':
    main()
