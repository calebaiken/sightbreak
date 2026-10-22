#!/usr/bin/env python3
"""Replay retained Windows native pixels/authority through production guards."""
import argparse
import ast
import copy
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
from types import SimpleNamespace

from PIL import Image, ImageChops, ImageDraw


def function(text, name, context):
    node = next(n for n in ast.walk(ast.parse(text)) if isinstance(n, ast.FunctionDef) and n.name == name)
    exec(compile(ast.Module(body=[node], type_ignores=[]), '<actual production ' + name + '>', 'exec'), context)
    return context[name], hashlib.sha256(ast.dump(node).encode()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--candidate', type=Path, required=True)
    p.add_argument('--baseline', type=Path, required=True)
    p.add_argument('--receipts', type=Path, required=True)
    p.add_argument('--captures', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    baseline, candidate = args.baseline.read_text(), args.candidate.read_text()
    receipts = json.loads((args.receipts / 'results.json').read_text())
    good = receipts['hud_analysis_pauses'][-1]['after_analysis']
    dead = receipts['last_offline_observation']
    rows, commands = [], []
    readers = {}
    for label, text in [('baseline', baseline), ('candidate', candidate)]:
        context = {'Image': Image, 'ImageChops': ImageChops, 'Path': Path, 're': re, 'REFERENCE': (1280, 720)}
        readers[label], digest = function(text, 'read_hud_pixels', context)
        rows.append({'check': 'actual pixel reader AST', 'version': label, 'sha256': digest})
    expected = {'02-offline-spawn': (15, 60), '04-move-aim': (15, 60), '05-after-fire': (14, 60),
                '06-after-reload': (15, 59), '06b-scoreboard': (15, 59), '06e-purchased-smg': (30, 120),
                '06f-switched-sidearm': (15, 60), '06g-switched-primary': (30, 120)}
    def ocr(image, psm, label):
        payload = io.BytesIO(); image.save(payload, format='PNG')
        command = ['tesseract', 'stdin', 'stdout', '--psm', str(psm)]
        completed = subprocess.run(command, input=payload.getvalue(), capture_output=True, timeout=20)
        commands.append({'command': command, 'label': label, 'exit': completed.returncode,
                         'stdout': completed.stdout.decode(errors='replace'), 'stderr': completed.stderr.decode(errors='replace')})
        completed.check_returncode()
        return completed.stdout.decode(errors='replace')
    paths = [(name, args.captures / (name + '.png'), value) for name, value in expected.items()]
    paths.extend([(name, args.captures / (name + '.png'), None) for name in ('01-menu', '06c-next-round', '07d-explicit-resume')])
    for name, box in [('removed-ammunition', (980, 648, 1280, 680)), ('removed-health', (0, 630, 450, 720))]:
        with Image.open(args.captures / '06g-switched-primary.png') as original:
            image = original.copy()
            scaled = tuple(round(value * image.size[i % 2] / (1280, 720)[i % 2]) for i, value in enumerate(box))
            ImageDraw.Draw(image).rectangle(scaled, fill=(0, 0, 0))
            path = args.output / (name + '.png'); image.save(path)
        paths.append((name, path, None))
    for name, path, expected_pair in paths:
        for label, reader in readers.items():
            row = {'check': name, 'version': label, 'native_original': path.parent == args.captures,
                   'capture_sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'expected_pair': expected_pair}
            try:
                value = reader(path, ocr)
                row.update(reading=value, passed=expected_pair is not None and (value['ammo'], value['reserve']) == expected_pair)
            except RuntimeError as error:
                row.update(error=str(error), passed=expected_pair is None)
            rows.append(row)
    # These compile the actual production closures without running a native game.
    # Retained real authority samples provide the positive and dead counterexample;
    # copies alter one boundary at a time and remain labeled synthetic controls.
    physical = {'lmb_down': False, 'keys_down': {'r': False, 'd': False, 'w': False}}
    for state_name, state in [('actual-dead', dead), ('dead-paused-copy', {**dead, 'ui': {**dead['ui'], 'paused': True}})]:
        context = {'ui': SimpleNamespace(diagnostics=lambda: physical), 'held_keys': set(),
                   'offline_observation': lambda: state}
        reader, _ = function(candidate, 'read_hud', context)
        try:
            reader('unused')
            rows.append({'check': 'HUD guard ' + state_name, 'passed': False})
        except RuntimeError as error:
            rows.append({'check': 'HUD guard ' + state_name, 'passed': 'actual living, focused offline player' in str(error), 'error': str(error)})
    context = {'settings_pause': good}
    require, _ = function(candidate, 'require_resume_context', context)
    controls = [('actual-living-paused', good, True), ('actual-dead', dead, False)]
    for field, value in [('alive', False), ('id', 99), ('weapon', 'sidearm'), ('ammo', 0), ('reserve', 0)]:
        state = copy.deepcopy(good); state['local_actor'][field] = value
        controls.append(('altered actor ' + field, state, False))
    for field, value in [('phase', 'post'), ('round_number', good['round_number'] + 1), ('time_scale', 0.5)]:
        state = copy.deepcopy(good); state[field] = value
        controls.append(('altered state ' + field, state, False))
    for field, value in [('focused', False), ('screen', 'menu')]:
        state = copy.deepcopy(good); state['ui'][field] = value
        controls.append(('altered UI ' + field, state, False))
    for label, state, accepted in controls:
        try:
            require(state)
            rows.append({'check': 'resume context ' + label, 'passed': accepted})
        except RuntimeError as error:
            rows.append({'check': 'resume context ' + label, 'passed': not accepted, 'error': str(error)})
    # The already-paused path must also reject a context change while external
    # OCR is running, rather than checking only before it starts.
    changed = copy.deepcopy(good); changed['round_number'] += 1
    context = {'ui': SimpleNamespace(diagnostics=lambda: physical), 'held_keys': set(),
               'offline_observation': lambda: good, 'read_hud_pixels': lambda *args: {'ammo': 30, 'reserve': 120},
               'out': args.output, 'ocr': None, 'observed': lambda *args: changed}
    reader, _ = function(candidate, 'read_hud', context)
    try:
        reader('synthetic-paused-transition', require_context=require)
        rows.append({'check': 'already-paused OCR rejects changed original context', 'passed': False})
    except RuntimeError as error:
        rows.append({'check': 'already-paused OCR rejects changed original context', 'passed': True, 'error': str(error)})
    report = {'scope': 'Actual Windows receipts/pixels replayed on Linux; altered controls and AST execution are not native gameplay',
              'candidate_sha256': hashlib.sha256(args.candidate.read_bytes()).hexdigest(),
              'baseline_sha256': hashlib.sha256(args.baseline.read_bytes()).hexdigest(),
              'actual_results_sha256': hashlib.sha256((args.receipts / 'results.json').read_bytes()).hexdigest(),
              'rows': rows, 'ocr_commands': commands}
    (args.output / 'results.json').write_text(json.dumps(report, indent=2) + '\n')
    checks = [r for r in rows if 'passed' in r]
    print(json.dumps({'checks': len(checks), 'passed': sum(r['passed'] for r in checks), 'failed': [r['check'] for r in checks if not r['passed']]}, indent=2))
    if not all(r['passed'] for r in checks):
        raise SystemExit(1)

if __name__ == '__main__':
    main()
