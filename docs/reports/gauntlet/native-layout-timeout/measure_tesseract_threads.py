#!/usr/bin/env python3
"""Serial saved-pixel A/B; run only after the shared CPU lane is released."""
import argparse
import csv
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import resource
import shutil
import subprocess
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'scripts'))
from PIL import Image
from capture_desktop_layouts import hud_footer_region, ocr_input, ocr_lines, rendered_hud_matches


def digest(data):
    return hashlib.sha256(data).hexdigest()


def trial(command, data, env, output, label):
    peak = {'threads': 0, 'rss_kib': 0}
    finished = threading.Event()
    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    started = time.monotonic()
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, env=env)

    def sample():
        while not finished.is_set():
            try:
                rows = dict(line.split(':', 1) for line in Path(f'/proc/{process.pid}/status').read_text().splitlines() if ':' in line)
                peak['threads'] = max(peak['threads'], int(rows.get('Threads', '0')))
                peak['rss_kib'] = max(peak['rss_kib'], int(rows.get('VmRSS', '0').split()[0]))
            except (OSError, ValueError):
                pass
            finished.wait(.01)

    sampler = threading.Thread(target=sample)
    sampler.start()
    error = None
    try:
        stdout, stderr = process.communicate(data, timeout=7)
    except subprocess.TimeoutExpired as exception:
        error = str(exception)
        process.kill()
        stdout, stderr = process.communicate()
    finally:
        finished.set()
        sampler.join()
    seconds = time.monotonic() - started
    after = resource.getrusage(resource.RUSAGE_CHILDREN)
    (output / (label + '.tsv.gz')).write_bytes(gzip.compress(stdout, mtime=0))
    (output / (label + '.stderr.gz')).write_bytes(gzip.compress(stderr, mtime=0))
    text = stdout.decode('utf-8', errors='replace')
    words = [row['text'] for row in csv.DictReader(io.StringIO(text), delimiter='\t') if row.get('text', '').strip()]
    return {'label': label, 'wall_seconds': seconds,
            'user_cpu_seconds': after.ru_utime - before.ru_utime,
            'system_cpu_seconds': after.ru_stime - before.ru_stime,
            'maximum_observed_threads': peak['threads'], 'peak_observed_rss_kib': peak['rss_kib'],
            'analysis_sha256': digest(data), 'tsv_sha256': digest(stdout), 'words': words,
            'exit_code': process.returncode, 'error': error}, text


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--rounds', type=int, default=2)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    fixtures = ROOT / 'docs/reports/gauntlet/native-layout-ocr'
    manifest = json.loads((fixtures / 'fixtures.json').read_text())
    command = [os.environ.get('TESSERACT_BIN') or shutil.which('tesseract'), 'stdin', 'stdout', '--psm', '11', 'tsv']
    report = {'scope': 'Serial saved native PNG OCR only; no native render, CI failure reproduction, image quality or hardware-performance acceptance',
              'source_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
              'capture_script_sha256': digest((ROOT / 'scripts/capture_desktop_layouts.py').read_bytes()),
              'host': platform.platform(), 'cpu_max': Path('/sys/fs/cgroup/cpu.max').read_text().strip(),
              'tesseract': subprocess.check_output([command[0], '--version'], text=True).splitlines()[0],
              'command': command, 'per_trial_timeout_seconds': 7,
              'inherited_thread_settings': {key: os.environ.get(key) for key in ['OMP_THREAD_LIMIT', 'OMP_NUM_THREADS', 'OMP_DYNAMIC']},
              'trials': [], 'comparisons': []}
    failures = []
    for repetition in range(args.rounds):
        for index, fixture in enumerate(manifest['raw_native_fixtures']):
            path = fixtures / fixture['path']
            original = path.read_bytes()
            assert digest(original) == fixture['sha256']
            groups, receipts = {}, {}
            order = ['inherited', 'one-thread'] if (index + repetition) % 2 == 0 else ['one-thread', 'inherited']
            for variant in order:
                env = os.environ.copy()
                if variant == 'one-thread':
                    env['OMP_THREAD_LIMIT'] = '1'
                groups[variant], receipts[variant] = [], []
                for footer in (False, True):
                    factor = 4 if footer else (3 if fixture['size'][0] < 1100 else 2)
                    region = hud_footer_region(fixture['size']) if footer else None
                    with Image.open(io.BytesIO(original)) as raw:
                        data = ocr_input(raw, factor, region=region, threshold=None if footer else 145)
                    label = f'r{repetition}-{path.stem}-{variant}-' + ('footer' if footer else 'full')
                    receipt, text = trial(command, data, env, args.output, label)
                    receipt.update(variant=variant, fixture=fixture['path'], original_sha256=fixture['sha256'], factor=factor, region=region)
                    report['trials'].append(receipt)
                    receipts[variant].append(receipt)
                    groups[variant].append(ocr_lines(text, factor, origin=region[:2] if region else (0, 0)))
                    if receipt['error'] or receipt['exit_code']:
                        failures.append(label + ': OCR did not complete successfully')
                full, footer_groups = groups[variant]
                if (rendered_hud_matches(full, False, footer_groups) != (fixture['expected'] == 'desktop')
                        or rendered_hud_matches(full, True) != (fixture['expected'] == 'touch')):
                    failures.append(label + ': classification changed')
            for part in (0, 1):
                a, b = receipts['inherited'][part], receipts['one-thread'][part]
                comparison = {'fixture': fixture['path'], 'round': repetition, 'part': 'footer' if part else 'full',
                              'same_analysis_bytes': a['analysis_sha256'] == b['analysis_sha256'],
                              'same_tsv_bytes': a['tsv_sha256'] == b['tsv_sha256'], 'same_words': a['words'] == b['words'],
                              'inherited_wall_seconds': a['wall_seconds'], 'one_thread_wall_seconds': b['wall_seconds']}
                report['comparisons'].append(comparison)
                if not comparison['same_analysis_bytes'] or not comparison['same_words']:
                    failures.append(str(comparison))
            assert path.read_bytes() == original
            (args.output / 'results.json').write_text(json.dumps({**report, 'failures': failures}, indent=2) + '\n')
            print(f'round {repetition} {path.stem}: compared unchanged full/footer pixels', flush=True)
    report['failures'] = failures
    (args.output / 'results.json').write_text(json.dumps(report, indent=2) + '\n')
    return bool(failures)


if __name__ == '__main__':
    raise SystemExit(main())
