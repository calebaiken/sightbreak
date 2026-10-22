#!/usr/bin/env python3
"""Measure prior native startup bytes whose hashes recur in the failed CI run."""
import gzip
import json
import os
from pathlib import Path
import shutil
import sys
from PIL import Image
from measure_tesseract_threads import ROOT, digest, trial, ocr_input

out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=False)
previous = ROOT / 'docs/reports/gauntlet/native-layout-ocr/native-four-size-r1'
failed = ROOT / 'docs/reports/gauntlet/native-layout-timeout/native-ci-39719407304'
command = [os.environ.get('TESSERACT_BIN') or shutil.which('tesseract'), 'stdin', 'stdout', '--psm', '11', 'tsv']
report = {'scope': 'Saved prior native startup pixels have exact raw SHA matches to repeated completed calls in failed CI. New CI final menu/settings PNGs remain unavailable; this does not reproduce native timing.', 'trials': [], 'cases': []}
for size in ('960x540', '1280x720', '1920x1080', '1280x800'):
    source = previous / size / 'menu-ready-1-ocr-original.png'
    original = source.read_bytes()
    rows = json.loads(gzip.decompress((failed / (size + '-results.json.gz')).read_bytes()))['ocr_commands']
    startup = [r for r in rows if r['original_sha256'] == digest(original)]
    assert len(startup) > 1
    record = {'size': size, 'original_sha256': digest(original), 'prior_native_original': str(source.relative_to(ROOT)),
              'completed_matching_ci_calls': len(startup), 'repeat_calls_after_first': len(startup) - 1}
    for repetition in range(3):
        variants = ('inherited', 'one-thread') if repetition % 2 == 0 else ('one-thread', 'inherited')
        for variant in variants:
            env = os.environ.copy()
            if variant == 'one-thread': env['OMP_THREAD_LIMIT'] = '1'
            with Image.open(source) as raw:
                data = ocr_input(raw, 3 if raw.width < 1100 else 2)
            receipt, text = trial(command, data, env, out, f'{size}-r{repetition}-{variant}')
            assert not receipt['error'] and receipt['exit_code'] == 0
            receipt.update(size=size, variant=variant, original_sha256=digest(original))
            report['trials'].append(receipt)
    assert source.read_bytes() == original
    report['cases'].append(record)
report['same_tsv_per_size'] = all(len({r['tsv_sha256'] for r in report['trials'] if r['size'] == size}) == 1 for size in ('960x540', '1280x720', '1920x1080', '1280x800'))
assert report['same_tsv_per_size']
(out / 'results.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report['cases'], indent=2))
