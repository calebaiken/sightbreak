#!/usr/bin/env python3
"""Matched observability trial using an existing imported game cache, one child at a time."""
import argparse
import json
import math
import platform
import random
import shutil
import subprocess
import tarfile
from pathlib import Path

from measure_prediction_timeline import ROOT, TESTS, execute, git, sha, shipping, write

FIXTURES = ['prediction_timeline_probe.gd', 'ack_snapshot_diagnostics_probe.gd']
RUNTIME_DELTA = {'scripts/network/movement_prediction.gd', 'scripts/network/ack_snapshot_diagnostics.gd'}


def close(left, right):
    return abs(left - right) < 0.00002


def evaluate(data):
    """Compute coverage and drift independently from the delivered native positions."""
    conditions = []
    valid = True
    for case in data['conditions']:
        first = previous = None
        last_ack = None
        observations = repeats = held = legacy_held = covered_held = diagnostic_held = 0
        repeated_drift_samples = 0
        for row in case['snapshots']:
            repeated = row['ack'] == last_ack
            if not repeated:
                first = row['authority']
            sample = row['snapshot_observation']
            if sample is not None:
                observations += 1
                repeats += repeated
                valid &= (sample['observation'] == observations and sample['ack'] == row['ack']
                          and sample['epoch'] == 1 and sample['repeated_ack'] == repeated
                          and sample['prediction_enabled'] == case['prediction_enabled']
                          and sample['anchor_kind'] == 'first_observed_snapshot_not_consumption'
                          and sample['position'] == row['authority']
                          and sample['first_snapshot_position'] == first
                          and close(sample['first_snapshot_drift_m'], math.dist(first, row['authority'])))
                if repeated:
                    valid &= close(sample['previous_snapshot_delta_m'], math.dist(previous, row['authority']))
                    repeated_drift_samples += sample['previous_snapshot_delta_m'] > 0.01
                else:
                    valid &= sample['previous_snapshot_delta_m'] is None
            if row['same_ack_drift_m'] > 0.01:
                held += 1
                legacy_held += row['ack_error_m'] is not None
                diagnostic_held += sample is not None
                covered_held += row['ack_error_m'] is not None or sample is not None
            last_ack, previous = row['ack'], row['authority']
        valid &= observations == case['snapshot_diagnostic_observations']
        valid &= repeats == case['snapshot_diagnostic_repeats']
        valid &= case['snapshot_diagnostic_retained'] <= 120
        valid &= observations - case['snapshot_diagnostic_evicted'] == case['snapshot_diagnostic_retained']
        conditions.append({'condition': case['name'], 'snapshots': len(case['snapshots']),
                           'diagnostic_samples': observations, 'held_snapshots': held,
                           'legacy_held_covered': legacy_held, 'held_covered': covered_held,
                           'diagnostic_held_covered': diagnostic_held,
                           'repeated_ack_positive_drift_samples': repeated_drift_samples})
    expected_epoch, observation_count, last_ack = -1, 0, None
    first = previous = expected_sample = None
    lifecycle_present = 0
    for row in data['lifecycle_timeline']:
        if row['event'] in ('connection_reset', 'predict_epoch'):
            expected_epoch = -1 if row['event'] == 'connection_reset' else row['epoch']
            observation_count, last_ack = 0, None
            first = previous = expected_sample = None
        elif row['accepted']:
            if row['epoch'] != expected_epoch:
                expected_epoch, observation_count, last_ack = row['epoch'], 0, None
            repeated = row['ack'] == last_ack
            position = row['received_snapshot_position']
            if not repeated:
                first = position
            observation_count += 1
            expected_sample = {'ack': row['ack'], 'position': position, 'first_snapshot_position': first,
                               'repeated_ack': repeated, 'observation': observation_count, 'epoch': expected_epoch,
                               'prediction_enabled': True, 'anchor_kind': 'first_observed_snapshot_not_consumption',
                               'previous_snapshot_delta_m': math.dist(previous, position) if repeated else None,
                               'first_snapshot_drift_m': math.dist(first, position)}
            last_ack, previous = row['ack'], position
        diagnostic = row['snapshot_diagnostics']
        if diagnostic is not None:
            lifecycle_present += 1
            valid &= diagnostic['epoch'] == expected_epoch and diagnostic['observations'] == observation_count
            actual = diagnostic['sample']
            if expected_sample is None:
                valid &= actual is None
            else:
                valid &= actual is not None and actual.keys() == expected_sample.keys()
                if actual is not None:
                    for key, value in expected_sample.items():
                        valid &= close(actual[key], value) if isinstance(value, float) else actual[key] == value
    complete = (valid and lifecycle_present == len(data['lifecycle_timeline']) and
                all(c['diagnostic_samples'] == c['snapshots'] and
                             c['held_covered'] == c['held_snapshots'] for c in conditions)
                and data['diagnostic_lifecycle']['available'])
    return {'position_and_coverage_consistent': bool(valid), 'complete_observability_gate': bool(complete),
            'lifecycle_events': len(data['lifecycle_timeline']), 'lifecycle_events_with_diagnostics': lifecycle_present,
            'conditions': conditions}


def legacy_projection(data):
    projected = json.loads(json.dumps(data['conditions']))
    for case in projected:
        for key in list(case):
            if key.startswith('snapshot_diagnostic_'):
                del case[key]
        for row in case['snapshots']:
            del row['snapshot_observation']
    lifecycle = [{k: v for k, v in row.items() if k != 'snapshot_diagnostics'}
                 for row in data['lifecycle_timeline']]
    return {'conditions': projected, 'lifecycle_timeline': lifecycle}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', default='701ce2c4d7f8b2872cf1fefa64cb6edd0cd1a3fd')
    parser.add_argument('--candidate', required=True)
    parser.add_argument('--godot', type=Path, required=True)
    parser.add_argument('--cache-game', type=Path, required=True)
    parser.add_argument('--stage', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    for name in ['godot', 'cache_game', 'stage', 'out']:
        setattr(args, name, getattr(args, name).resolve())
    if git('status', '--porcelain'):
        parser.error('freeze a clean source/workload commit before measurement')
    args.stage.mkdir(parents=True, exist_ok=False)
    args.out.mkdir(parents=True, exist_ok=False)
    (args.out / 'blind').mkdir()
    cache = args.cache_game / '.godot'
    if not (cache / 'global_script_class_cache.cfg').is_file():
        parser.error('use a previously imported game; this trial never launches an editor')
    labels = ['sample-C', 'sample-R']
    random.SystemRandom().shuffle(labels)
    mapping = dict(zip(labels, [('baseline', git('rev-parse', args.baseline)),
                               ('candidate', git('rev-parse', args.candidate))]))
    receipts = {'harness_commit': git('rev-parse', 'HEAD'), 'harness_status': '',
                'driver_sha256': sha(Path(__file__)), 'support_driver_sha256': sha(ROOT / 'scripts/measure_prediction_timeline.py'),
                'fixtures': {name: sha(ROOT / 'game/tests' / name) for name in FIXTURES},
                'host': platform.platform(), 'python': platform.python_version(), 'godot_sha256': sha(args.godot),
                'godot_version': subprocess.check_output([str(args.godot), '--version'], text=True).strip(),
                'cache_path': str(cache), 'cache_sha256_by_path': {p.relative_to(cache).as_posix(): sha(p)
                    for p in sorted(cache.rglob('*')) if p.is_file()}, 'source_mapping': mapping, 'runs': {}}
    write(args.out / 'mapping.json', mapping)
    data_by_role = {}
    failed = False
    for label, (role, revision) in mapping.items():
        stage, evidence = args.stage / label, args.out / label
        stage.mkdir()
        evidence.mkdir()
        archive = stage / 'game.tar'
        with archive.open('wb') as output:
            subprocess.run(['git', 'archive', '--format=tar', revision, 'game'], cwd=ROOT, stdout=output, check=True)
        with tarfile.open(archive) as source:
            source.extractall(stage, filter='data')
        game = stage / 'game'
        original = shipping(game)
        if role == 'baseline' and shipping(args.cache_game) != original:
            raise RuntimeError('cached game shipping bytes must match the frozen baseline')
        shutil.copytree(cache, game / '.godot')
        for fixture in FIXTURES:
            shutil.copyfile(ROOT / 'game/tests' / fixture, game / 'tests' / fixture)
        record = {'role': role, 'source_commit': revision, 'source_game_tree': git('rev-parse', revision + ':game'),
                  'archive_sha256': sha(archive), 'shipping_sha256_by_path': original, 'tests': {}}
        receipts['runs'][label] = record
        write(args.out / 'manifest.json', receipts)
        base = [str(args.godot), '--headless', '--path', str(game)]
        result_path = evidence / 'observability.json'
        record['probe'] = execute([*base, '--script', 'res://tests/ack_snapshot_diagnostics_probe.gd', '--',
                                   '--output=' + str(result_path)], stage, evidence / 'probe.log')
        if record['probe']['exit'] != 0 or record['probe']['logged_error'] or not result_path.exists():
            failed = True
        else:
            data = json.loads(result_path.read_text(encoding='utf-8'))
            data_by_role[role] = data
            record['coverage'] = evaluate(data)
            failed |= bool(data['failures']) or not record['coverage']['position_and_coverage_consistent']
            record['result_sha256'] = sha(result_path)
            shutil.copyfile(result_path, args.out / 'blind' / (label + '.json'))
        for test in TESTS:
            result = execute([*base, '--script', 'res://tests/' + test + '.gd'], stage, evidence / (test + '.log'))
            record['tests'][test] = result
            failed |= result['exit'] != 0 or result['logged_error']
        record['shipping_after_sha256_by_path'] = shipping(game)
        failed |= original != record['shipping_after_sha256_by_path']
        write(args.out / 'manifest.json', receipts)
        print(label, 'completed; process/metric failure:', failed, flush=True)
    if len(data_by_role) == 2:
        equivalent = legacy_projection(data_by_role['baseline']) == legacy_projection(data_by_role['candidate'])
        receipts['legacy_outputs_identical'] = equivalent
        gates = {role: evaluate(data)['complete_observability_gate'] for role, data in data_by_role.items()}
        receipts['observability_gate'] = gates
        old, new = [r['shipping_sha256_by_path'] for r in receipts['runs'].values()]
        delta = {p for p in old.keys() | new.keys() if old.get(p) != new.get(p)}
        receipts['shipping_changed_paths'] = sorted(delta)
        failed |= not equivalent or gates != {'baseline': False, 'candidate': True} or delta != RUNTIME_DELTA
    else:
        failed = True
    receipts['failed'] = bool(failed)
    write(args.out / 'manifest.json', receipts)
    (args.out / 'blind/README.md').write_text(
        '# Neutral ACK-observation outcomes\n\n'
        'Assess sample-C.json and sample-R.json before opening any source map or author report.\n'
        'The declared bar is complete observations for reconciled snapshots, including five formerly\n'
        'unscored repeated-ACK held-state snapshots per burst condition, with correct snapshot-relative\n'
        'drift and bounded lifecycle state. Compare every pre-existing movement/ACK/correction output.\n'
        'A first observed snapshot is NOT a consumption-time pose; its earlier hold duration is unknown.\n'
        'Duplicate/out-of-order outer ticks, round/reconnect resets and cache saturation are included.\n'
        'This is deterministic in-process scheduling, not ENet, and can demonstrate observability only.\n'
        'No gameplay accuracy, performance or prediction activation win is claimed by this bar.\n', encoding='utf-8')
    raise SystemExit(1 if failed else 0)


if __name__ == '__main__':
    main()
