#!/usr/bin/env python3
"""Recompute saved benchmark facts from every original PNG and retained raw TSV."""
import csv
import gzip
import hashlib
import io
import json
from pathlib import Path
import statistics
import subprocess
import sys
import tarfile

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / 'scripts'))
from PIL import Image
from capture_desktop_layouts import hud_footer_region, ocr_input, ocr_lines, rendered_hud_matches


def digest(value):
    return hashlib.sha256(value).hexdigest()


def main():
    saved = Path(sys.argv[1])
    report_path = saved / 'results.json'
    report = json.loads(report_path.read_bytes() if report_path.exists()
                        else gzip.decompress((saved / 'results.json.gz').read_bytes()))
    retained_raw = {}
    if (saved / 'raw-ocr-output.tar.gz').exists():
        with tarfile.open(saved / 'raw-ocr-output.tar.gz') as archive:
            members = archive.getmembers()
            assert all(member.isfile() for member in members)
            assert len(members) == len({member.name for member in members})
            retained_raw = {member.name: archive.extractfile(member).read() for member in members}
    fixtures = ROOT / 'docs/reports/gauntlet/native-layout-ocr'
    manifest = json.loads((fixtures / 'fixtures.json').read_text())
    originals = {entry['path']: entry for entry in manifest['raw_native_fixtures']}
    expected_analysis = {}
    for path, entry in originals.items():
        raw = (fixtures / path).read_bytes()
        assert digest(raw) == entry['sha256']
        for part in ('full', 'footer'):
            footer = part == 'footer'
            region = hud_footer_region(entry['size']) if footer else None
            factor = 4 if footer else (3 if entry['size'][0] < 1100 else 2)
            with Image.open(io.BytesIO(raw)) as image:
                data = ocr_input(image, factor, region=region, threshold=None if footer else 145)
            expected_analysis[path, part] = digest(data)
    assert report['capture_script_sha256'] == digest(subprocess.check_output(
        ['git', 'show', '7d46d2e:scripts/capture_desktop_layouts.py'], cwd=ROOT))
    assert report['per_trial_timeout_seconds'] == 7
    trials = {}
    labels = set()
    grouped = {}
    for trial in report['trials']:
        label = trial['label']
        assert label not in labels
        labels.add(label)
        round_number = int(label.split('-', 1)[0][1:])
        part = 'footer' if label.endswith('-footer') else 'full'
        key = (round_number, trial['fixture'], trial['variant'], part)
        assert key not in trials
        trials[key] = trial
        original = originals[trial['fixture']]
        assert trial['original_sha256'] == original['sha256']
        assert trial['analysis_sha256'] == expected_analysis[trial['fixture'], part]
        raw_name = label + '.tsv.gz'
        value = gzip.decompress(retained_raw[raw_name] if retained_raw else (saved / raw_name).read_bytes())
        assert digest(value) == trial['tsv_sha256']
        text = value.decode('utf-8')
        words = [row['text'] for row in csv.DictReader(io.StringIO(text), delimiter='\t') if row.get('text', '').strip()]
        assert words == trial['words']
        assert trial['exit_code'] == 0 and trial['error'] is None
        assert 0 < trial['wall_seconds'] < 7
        assert trial['user_cpu_seconds'] >= 0 and trial['system_cpu_seconds'] >= 0
        assert 0 <= trial['preprocessing_seconds'] < 7
        assert trial['maximum_observed_threads'] > 0
        if trial['variant'] == 'one-thread':
            assert trial['maximum_observed_threads'] == 1
        grouped[key] = ocr_lines(text, trial['factor'], origin=trial['region'][:2] if trial['region'] else (0, 0))
    expected = {(round_number, path, variant, part) for round_number in range(2)
                for path in originals for variant in ('inherited', 'one-thread') for part in ('full', 'footer')}
    assert set(trials) == expected
    unchanged_tsv = 0
    for round_number in range(2):
        for path, original in originals.items():
            for variant in ('inherited', 'one-thread'):
                full = grouped[round_number, path, variant, 'full']
                footer = grouped[round_number, path, variant, 'footer']
                assert rendered_hud_matches(full, False, footer) == (original['expected'] == 'desktop')
                assert rendered_hud_matches(full, True) == (original['expected'] == 'touch')
            for part in ('full', 'footer'):
                a = trials[round_number, path, 'inherited', part]
                b = trials[round_number, path, 'one-thread', part]
                assert a['tsv_sha256'] == b['tsv_sha256']
                unchanged_tsv += 1
    result = {'scope': 'Independent recomputation of retained saved-pixel benchmark; no new OCR or native generation.',
              'benchmark_source': report['source_commit'], 'original_fixtures': len(originals),
              'trials_recomputed': len(trials), 'byte_identical_tsv_pairs': unchanged_tsv,
              'classifications_recomputed': 2 * 2 * len(originals), 'variants': {}}
    for variant in ('inherited', 'one-thread'):
        selected = [trial for key, trial in trials.items() if key[2] == variant]
        result['variants'][variant] = {
            'calls': len(selected), 'wall_seconds': sum(trial['wall_seconds'] for trial in selected),
            'cpu_seconds': sum(trial['user_cpu_seconds'] + trial['system_cpu_seconds'] for trial in selected),
            'median_wall_seconds': statistics.median(trial['wall_seconds'] for trial in selected),
            'maximum_wall_seconds': max(trial['wall_seconds'] for trial in selected),
            'maximum_observed_threads': max(trial['maximum_observed_threads'] for trial in selected),
            'preprocessing_seconds': sum(trial['preprocessing_seconds'] for trial in selected)}
    inherited, one = result['variants']['inherited'], result['variants']['one-thread']
    result['aggregate_cpu_reduction_percent'] = 100 * (1 - one['cpu_seconds'] / inherited['cpu_seconds'])
    result['aggregate_wall_reduction_percent'] = 100 * (1 - one['wall_seconds'] / inherited['wall_seconds'])
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
