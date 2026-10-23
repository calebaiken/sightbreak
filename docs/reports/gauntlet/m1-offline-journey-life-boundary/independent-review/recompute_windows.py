#!/usr/bin/env python3
"""Recompute actual Windows evidence without starting a native renderer."""
import ast
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess

from PIL import Image, ImageChops

REPO = Path('/workspace/sightbreak-offline-journey')
RAW = Path('/workspace/reviews/native-ci-39719407304')
OUT = Path(__file__).resolve().parent


def source_at(commit):
    return subprocess.check_output(['git', '-C', str(REPO), 'show', commit + ':scripts/verify_offline_export.py'], text=True)


def reader_at(commit):
    source = source_at(commit)
    tree = ast.parse(source)
    node = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'read_hud_pixels')
    namespace = {'Image': Image, 'ImageChops': ImageChops, 'Path': Path, 're': re, 'REFERENCE': (1280, 720)}
    exec(compile(ast.Module(body=[node], type_ignores=[]), commit, 'exec'), namespace)
    return namespace['read_hud_pixels'], hashlib.sha256(ast.dump(node).encode()).hexdigest()


def main():
    receipt = json.loads((RAW / 'windows-receipts/evidence/offline-input/results.json').read_text())
    actions = json.loads((RAW / 'windows-receipts/evidence/offline-input/actions.json').read_text())
    events = [json.loads(line) for line in (RAW / 'windows-receipts/evidence/offline-input/initial-offline-trace/events.jsonl').read_text().splitlines()]
    summary = {'scope': 'Saved real Windows pixels, local Tesseract; not a native Windows rerun',
               'tesseract_version': subprocess.check_output(['tesseract', '--version'], text=True).splitlines()[0],
               'frozen_windows_source': receipt['source'],
               'baseline_failure': receipt['error'], 'baseline_elapsed_seconds': receipt['elapsed_seconds'],
               'baseline_cleanup_errors': receipt['cleanup_errors'], 'readers': {}, 'pixel_results': []}
    primary = next(item for item in receipt['hud_analysis_pauses'] if item['capture'] == '06g-switched-primary')
    summary['primary_pause'] = {name: {**{key: value.get(key) for key in ('simulation_tick', 'wall_msec', 'elapsed', 'drawn_frames', 'phase', 'round_number')},
                                      'local_actor': {key: value.get('local_actor', {}).get(key) for key in ('id', 'alive', 'health', 'deaths', 'weapon', 'ammo', 'reserve')}}
                                for name, value in primary.items() if isinstance(value, dict)}
    summary['decisive_actions'] = [event for event in actions if event.get('seconds', 0) >= 89 and
                                  (event.get('key') == 'Escape' or event.get('capture') in ('07c-settings-changed', '07d-explicit-resume'))]
    summary['death_events'] = [{key: event.get(key) for key in ('event', 'event_index', 'simulation_tick', 'elapsed', 'wall_msec', 'drawn_frames', 'phase', 'round_number', 'local_actor')}
                               for event in events if 3200 < event.get('simulation_tick', 0) < 3300 and event.get('local_actor', {}).get('alive') is False]
    for commit in ('0ca125dfba637868e6e8e9772ff9c40400413e32', '5c11a5b9894ccb28f505d3a60990b0ff46b6eaa0'):
        reader, digest = reader_at(commit)
        summary['readers'][commit] = digest
        for name, expected in [('05-after-fire', True), ('06-after-reload', True), ('06g-switched-primary', True), ('01-menu', False), ('07d-explicit-resume', False)]:
            path = RAW / 'windows-full/offline-input' / (name + '.png')
            result = {'commit': commit, 'capture': name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                      'expected_living_hud': expected, 'ocr_calls': []}

            def ocr(image, psm, label):
                data = io.BytesIO()
                image.save(data, format='PNG')
                process = subprocess.run(['tesseract', 'stdin', 'stdout', '--psm', str(psm)], input=data.getvalue(),
                                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20, check=True)
                text = process.stdout.decode('utf-8', errors='replace')
                result['ocr_calls'].append({'psm': psm, 'label': label, 'stdout': text, 'stderr': process.stderr.decode('utf-8', errors='replace')})
                return text
            try:
                result['reading'] = reader(path, ocr)
                result['accepted_living_hud'] = True
            except RuntimeError as error:
                result.update(accepted_living_hud=False, error=str(error))
            result['matches_expected'] = result['accepted_living_hud'] == expected
            summary['pixel_results'].append(result)
    summary['all_pixel_checks_pass'] = all(result['matches_expected'] for result in summary['pixel_results'])
    (OUT / 'windows-recomputed.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps({'all_pixel_checks_pass': summary['all_pixel_checks_pass'], 'readers_identical': len(set(summary['readers'].values())) == 1,
                      'checks': len(summary['pixel_results']), 'baseline_error': summary['baseline_failure'],
                      'death_events': [{key: value for key, value in row.items() if key != 'local_actor'} for row in summary['death_events']]}, indent=2))


if __name__ == '__main__':
    main()
