#!/usr/bin/env python3
"""Capture just the 121-insertion ACK cache boundary, serially in existing imported stages."""
import argparse
import hashlib
import io
import json
import math
import random
import subprocess
import tarfile
import zipfile
from pathlib import Path

from measure_prediction_timeline import ROOT, execute, git, sha, shipping, write

BASELINE = '701ce2c4d7f8b2872cf1fefa64cb6edd0cd1a3fd'
RUNTIME = '0fbce120d8c17db58596d280f7d8401ab2aa0937'
PROBE = 'game/tests/ack_cache_boundary_probe.gd'


def source_shipping(revision):
    data = subprocess.check_output(['git', 'archive', '--format=tar', revision, 'game'], cwd=ROOT)
    with tarfile.open(fileobj=io.BytesIO(data)) as archive:
        return {m.name.removeprefix('game/'): hashlib.sha256(archive.extractfile(m).read()).hexdigest()
                for m in archive if m.isfile() and not m.name.startswith('game/tests/')}


def audit(directory):
    """Recompute the raw insertion window/geometry; absent interface is N/A, not a failure."""
    traces = {p.stem: json.loads(p.read_text()) for p in sorted(directory.glob('sample-*.json'))}
    assert len(traces) == 2
    summary = {}
    for label, trace in traces.items():
        rows = trace['rows']
        assert not trace['failures'] and trace['count'] == len(rows) == 121
        assert trace['anchor'] == [3, .0625, -2] and trace['step_m'] == 1 / 32
        present = trace['diagnostic_status'] == 'available'
        for n, row in enumerate(rows, 1):
            position = [3 + (n - 1) / 32, .0625, -2]
            assert row['insertion'] == n and row['received_position'] == position
            assert row['ack'] == 1 and row['epoch'] == 7
            legacy = row['legacy']
            assert legacy['position'] == position and legacy['velocity'] == [.125, 0, 0]
            assert legacy['error_samples_m'] == [.5] and legacy['pending'] == []
            assert legacy['sequence'] == 1 and legacy['epoch'] == 7
            assert legacy['corrections'] == n and legacy['hard_corrections'] == 0
            assert len(legacy['large_corrections']) == 1 and legacy['health'] == 100 and legacy['ammo'] == 15
            observation = row['diagnostic']
            if not present:
                assert observation is None
                continue
            assert observation['observed_count'] == n and observation['retained_size'] == min(n, 120)
            assert observation['eviction_count'] == max(n - 120, 0)
            assert observation['repeats'] == n - 1 and observation['ignored'] == 0
            assert observation['retained_ordinals'] == list(range(max(1, n - 119), n + 1))
            for key, ordinal in [('latest_sample', n), ('oldest_sample', max(1, n - 119))]:
                sample = observation[key]
                expected_position = rows[ordinal - 1]['received_position']
                assert sample['observation'] == ordinal and sample['ack'] == 1 and sample['epoch'] == 7
                assert sample['position'] == expected_position and sample['first_snapshot_position'] == trace['anchor']
                assert sample['first_snapshot_drift_m'] == math.dist(expected_position, trace['anchor'])
                assert sample['previous_snapshot_delta_m'] == (None if ordinal == 1 else 1 / 32)
                assert sample['repeated_ack'] == (ordinal > 1) and sample['prediction_enabled']
                assert sample['anchor_kind'] == 'first_observed_snapshot_not_consumption'
        summary[label] = {'insertions': 121, 'cache_boundary': 'pass' if present else 'not_applicable',
                          'last_diagnostic': rows[-1]['diagnostic']}
    left, right = traces.values()
    assert [{k: v for k, v in r.items() if k != 'diagnostic'} for r in left['rows']] == [
        {k: v for k, v in r.items() if k != 'diagnostic'} for r in right['rows']]
    assert sorted(t['diagnostic_status'] for t in traces.values()) == ['available', 'not_available_not_applicable']
    return {'legacy_parity_rows': 121, 'failures': 0, 'samples': summary}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--audit', type=Path)
    parser.add_argument('--baseline-game', type=Path)
    parser.add_argument('--candidate-game', type=Path)
    parser.add_argument('--godot', type=Path)
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    if args.audit:
        print(json.dumps(audit(args.audit), indent=2))
        return
    if not all([args.baseline_game, args.candidate_game, args.godot, args.out]):
        parser.error('capture requires both imported game paths, --godot and a new --out directory')
    if git('status', '--porcelain'):
        parser.error('freeze the clean external workload before capture')
    revision = git('rev-parse', 'HEAD')
    expected = {'baseline': source_shipping(BASELINE), 'candidate': source_shipping(revision)}
    assert expected['candidate'] == source_shipping(RUNTIME), 'shipping runtime must remain exactly 0fbce120'
    args.out = args.out.resolve()
    args.out.mkdir(parents=True, exist_ok=False)
    private, public = args.out / 'controller', args.out / 'evidence'
    private.mkdir()
    public.mkdir()
    fixture = subprocess.check_output(['git', 'show', revision + ':' + PROBE], cwd=ROOT)
    assert fixture == (ROOT / PROBE).read_bytes()
    labels = ['sample-M', 'sample-T']
    random.SystemRandom().shuffle(labels)
    mapping = dict(zip(labels, ['baseline', 'candidate']))
    write(private / 'mapping.json', mapping)
    manifest = {'harness_commit': revision, 'baseline_commit': BASELINE, 'runtime_commit': RUNTIME,
                'probe_sha256': hashlib.sha256(fixture).hexdigest(), 'driver_sha256': sha(Path(__file__)),
                'support_driver_sha256': sha(ROOT / 'scripts/measure_prediction_timeline.py'),
                'godot_sha256': sha(args.godot), 'godot_version': subprocess.check_output([str(args.godot), '--version'], text=True).strip(),
                'shipping_sha256_by_source': expected, 'runs': {}}
    captures = {}
    for label, role in mapping.items():
        game = (args.baseline_game if role == 'baseline' else args.candidate_game).resolve()
        assert not game.is_relative_to(ROOT) and not (game.parent / '.git').exists(), 'use own staging caches only'
        cache = game / '.godot/global_script_class_cache.cfg'
        assert cache.is_file(), 'existing imported cache required'
        before = shipping(game)
        assert before == expected[role], 'cached shipping bytes must match exact Git source'
        destination = game / 'tests' / Path(PROBE).name
        assert not destination.exists() or destination.read_bytes() == fixture, 'do not overwrite a different fixture'
        destination.write_bytes(fixture)
        command = [str(args.godot), '--headless', '--path', str(game), '--script', 'res://tests/' + destination.name,
                   '--', '--output=' + str(public / (label + '.json'))]
        run = execute(command, game.parent, public / (label + '.log'), timeout=60)
        run.update({'role': role, 'source_commit': BASELINE if role == 'baseline' else revision,
                    'cache_index_sha256': sha(cache), 'shipping_after_identical': shipping(game) == before})
        manifest['runs'][label] = run
        write(private / 'capture.json', manifest)
        assert run['exit'] == 0 and not run['logged_error'] and run['shipping_after_identical'], 'retain failed capture'
        run['trace_sha256'] = sha(public / (label + '.json'))
        captures[label] = {key: run[key] for key in ['exit', 'logged_error', 'log_sha256', 'trace_sha256', 'shipping_after_identical']}
        print(label, 'native capture complete', flush=True)
    write(private / 'capture.json', manifest)
    # Identity-bearing paths/commands and label mapping stay controller-only until the verdict.
    write(public / 'source-receipt.json', {**{k: v for k, v in manifest.items() if k != 'runs'}, 'captures': captures})
    write(public / 'audit.json', audit(public))
    with zipfile.ZipFile(public / 'blind-traces.zip', 'x', compression=zipfile.ZIP_DEFLATED) as packet:
        packet.writestr('README.md', '# Cache-boundary traces only\n\n'
            'Review both JSON traces before any identity mapping or source-linked capture receipt.\n'
            'This is the narrow follow-up to the recorded observability verdict, not a new accuracy trial.\n'
            'Each has121 direct same-ACK reconciliations: P(n)=[3+(n-1)/32, 0.0625, -2], n=1..121.\n'
            'A real pending command supplies a0.5m legacy error on the first ACK; later ACKs must not append.\n'
            'Compare every legacy row across traces. Helper absence is N/A for the cache-boundary assertion.\n'
            'Where available, verify each raw retained-ID list, observed/retained/eviction count, oldest/latest\n'
            'position, original anchor and drift. At121:120 retained,1 evicted, IDs2..121, original anchor,\n'
            '3.75m total drift and1/32m previous-snapshot delta. All offsets are exactly representable.\n'
            'No transport, physics-time, consumption-time or gameplay accuracy inference is supported.\n'
            'Freeze the outcome-only boundary verdict before requesting the separate controller key.\n')
        for label in mapping:
            packet.write(public / (label + '.json'), label + '.json')
    print('trace packet SHA256:', sha(public / 'blind-traces.zip'))


if __name__ == '__main__':
    main()
