#!/usr/bin/env python3
"""Replay production HUD readers on retained native pixels, with no client running."""
import argparse
import ast
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import re
import subprocess
import sys
import time

from PIL import Image, ImageChops, ImageDraw

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'scripts'))
BASELINE = '6a0d8d5d85b4fb37943903886982f51b4ed230b0'
EXPECTED = {
    '02-offline-spawn': (15, 60), '04-move-aim': (15, 60),
    '05-after-fire': (14, 60), '06-after-reload': (15, 59),
    '06b-scoreboard': (15, 59),
    '06e-purchased-smg': (30, 120), '06f-switched-sidearm': (15, 60),
    '06g-switched-primary': (30, 120), '07d-explicit-resume': (30, 120),
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--captures', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    baseline_text = subprocess.check_output(['git', 'show', BASELINE + ':scripts/verify_offline_export.py'], cwd=ROOT).decode()
    baseline_main = next(node for node in ast.parse(baseline_text).body if isinstance(node, ast.FunctionDef) and node.name == 'main')
    baseline_reader = next(node for node in baseline_main.body if isinstance(node, ast.FunctionDef) and node.name == 'read_hud_pixels')
    baseline_code = compile(ast.Module(body=[baseline_reader], type_ignores=[]), '<original nested HUD reader>', 'exec')
    spec = importlib.util.spec_from_file_location('offline_candidate', ROOT / 'scripts/verify_offline_export.py')
    candidate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(candidate)
    commands, rows = [], []
    def ocr(image, psm, label):
        payload = io.BytesIO(); image.save(payload, format='PNG')
        command = ['tesseract', 'stdin', 'stdout', '--psm', str(psm)]
        started = time.monotonic()
        result = subprocess.run(command, input=payload.getvalue(), capture_output=True, timeout=20)
        commands.append({'command': command, 'label': label, 'elapsed_seconds': time.monotonic()-started,
                         'exit': result.returncode, 'stdout': result.stdout.decode(errors='replace'),
                         'stderr': result.stderr.decode(errors='replace')})
        if result.returncode: raise RuntimeError('OCR subprocess failed')
        return result.stdout.decode(errors='replace')
    context = {'Image': Image, 'ImageChops': ImageChops, 're': re, 'REFERENCE': candidate.REFERENCE,
               'out': args.captures, 'ocr': ocr}
    exec(baseline_code, context)
    for name, expected in EXPECTED.items():
        image_path = args.captures / (name + '.png')
        for version in ('baseline', 'candidate'):
            start = len(commands)
            try:
                got = context['read_hud_pixels'](name) if version == 'baseline' else candidate.read_hud_pixels(image_path, ocr)
                passed = (got['ammo'], got['reserve']) == expected
                row = {'reading': got, 'passed': passed}
            except RuntimeError as error:
                row = {'error': str(error), 'passed': False}
            rows.append({'version': version, 'capture': name, 'expected_ammo_reserve': expected,
                         'capture_sha256': hashlib.sha256(image_path.read_bytes()).hexdigest(),
                         'ocr_commands': [start, len(commands)], **row})
    negatives = [('actual-menu', args.captures / '01-menu.png'),
                 ('actual-eliminated', args.captures / '06c-next-round.png')]
    for label, box in [('removed-ammunition', (980, 648, 1280, 680)), ('removed-health', (0, 630, 450, 720))]:
        with Image.open(args.captures / '07d-explicit-resume.png') as image:
            image = image.copy()
            scaled = tuple(round(v*image.size[i%2]/candidate.REFERENCE[i%2]) for i,v in enumerate(box))
            ImageDraw.Draw(image).rectangle(scaled, fill=(0, 0, 0))
            path = args.output / (label + '.png'); image.save(path); negatives.append((label, path))
    for label, path in negatives:
        try:
            reading = candidate.read_hud_pixels(path, ocr)
            rows.append({'version': 'candidate', 'negative': label, 'passed': False, 'reading': reading})
        except RuntimeError as error:
            rows.append({'version': 'candidate', 'negative': label, 'passed': True, 'error': str(error)})
    result = {'baseline_source': BASELINE, 'candidate_source': subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip(),
              'candidate_reader_sha256': hashlib.sha256((ROOT/'scripts/verify_offline_export.py').read_bytes()).hexdigest(),
              'tesseract': subprocess.check_output(['tesseract','--version'],stderr=subprocess.STDOUT).decode(),
              'scope': 'unchanged Windows native screenshots replayed by local Linux Tesseract; no Windows rerun or full-flow acceptance',
              'rows': rows, 'commands': commands}
    (args.output/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    candidate_rows=[r for r in rows if r['version']=='candidate']
    print(json.dumps({'baseline_positive_passes': sum(r['passed'] for r in rows if r['version']=='baseline'),
                      'positive_count': len(EXPECTED), 'candidate_passes':sum(r['passed'] for r in candidate_rows),
                      'candidate_checks': len(candidate_rows), 'maximum_ocr_seconds':max(c['elapsed_seconds'] for c in commands)},indent=2))
    if not all(r['passed'] for r in candidate_rows): raise SystemExit(1)

if __name__ == '__main__': main()
