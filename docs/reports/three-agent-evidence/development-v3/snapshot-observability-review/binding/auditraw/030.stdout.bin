#!/usr/bin/env python3
"""Serial, source-bound native ACK-timeline comparison (no shared harness edits).

Archives game/ from exact revisions into fresh staging directories, imports using
the supplied engine, then applies the same hash-bound external probe to both.
Source labels and paths are kept out of blind/; mapping.json is for the integrator.
"""
import argparse
import hashlib
import json
import platform
import random
import re
import shutil
import subprocess
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / 'game/tests/prediction_timeline_probe.gd'
TESTS = ['movement_prediction_test', 'input_stream_test', 'state_privacy_test',
         'snapshot_buffer_test', 'peer_lifecycle_test', 'hit_history_test']
ERRORS = re.compile(r'SCRIPT ERROR|ERROR:|ObjectDB instances leaked|Leaked instance:')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()


def write(path, data):
    path.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')


def shipping(game):
    return {p.relative_to(game).as_posix(): sha(p) for p in sorted(game.rglob('*'))
            if p.is_file() and p.relative_to(game).parts[0] not in ('.godot', 'tests')}


def execute(command, cwd, log, timeout=180):
    try:
        result = subprocess.run(command, cwd=cwd, capture_output=True, text=True,
                                encoding='utf-8', errors='replace', timeout=timeout)
        text = result.stdout + result.stderr
        code = result.returncode
    except subprocess.TimeoutExpired as error:
        text = (error.stdout or b'').decode('utf-8', errors='replace')
        text += (error.stderr or b'').decode('utf-8', errors='replace')
        code = 'timeout'
    log.write_text(text, encoding='utf-8')
    return {'command': command, 'exit': code, 'logged_error': bool(ERRORS.search(text)),
            'log_sha256': sha(log)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', default='701ce2c4d7f8b2872cf1fefa64cb6edd0cd1a3fd')
    parser.add_argument('--candidate', required=True)
    parser.add_argument('--godot', type=Path, required=True)
    parser.add_argument('--stage', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    args.godot = args.godot.resolve()
    args.stage = args.stage.resolve()
    args.out = args.out.resolve()
    # Fresh locations keep previous unsuccessful evidence and imported projects intact.
    args.stage.mkdir(parents=True, exist_ok=False)
    args.out.mkdir(parents=True, exist_ok=False)
    blind = args.out / 'blind'
    blind.mkdir()
    version = subprocess.check_output([str(args.godot), '--version'], text=True).strip()
    labels = ['sample-J', 'sample-Q']
    random.SystemRandom().shuffle(labels)
    mapping = dict(zip(labels, [('baseline', git('rev-parse', args.baseline)),
                               ('candidate', git('rev-parse', args.candidate))]))
    manifest = {'host': platform.platform(), 'python': platform.python_version(),
                'godot': str(args.godot), 'godot_version': version,
                'godot_sha256': sha(args.godot), 'harness_commit': git('rev-parse', 'HEAD'),
                'harness_status': git('status', '--porcelain'),
                'driver_sha256': sha(Path(__file__)), 'probe_sha256': sha(PROBE),
                'source_mapping': mapping, 'runs': {}}
    write(args.out / 'mapping.json', mapping)
    failed = False
    for label, (role, revision) in mapping.items():
        stage = args.stage / label
        stage.mkdir()
        evidence = args.out / label
        evidence.mkdir()
        archive = stage / 'game.tar'
        with archive.open('wb') as stream:
            subprocess.run(['git', 'archive', '--format=tar', revision, 'game'],
                           cwd=ROOT, stdout=stream, check=True)
        with tarfile.open(archive) as stream:
            stream.extractall(stage, filter='data')
        game = stage / 'game'
        original = shipping(game)
        imports = {p: p.read_bytes() for p in game.rglob('*.import')}
        shutil.copyfile(PROBE, game / 'tests' / PROBE.name)
        base = [str(args.godot), '--headless', '--path', str(game)]
        imported = execute([*base, '--editor', '--import', '--single-threaded-scene'],
                           stage, evidence / 'import.log', 240)
        # Windows Godot may rewrite line endings in source-controlled declarations.
        # Restore the archived declarations, keeping only generated .godot/ caches.
        for path, data in imports.items():
            path.write_bytes(data)
        record = {'role': role, 'source_commit': revision,
                  'source_game_tree': git('rev-parse', revision + ':game'),
                  'archive_sha256': sha(archive), 'shipping_sha256_by_path': original,
                  'import': imported, 'tests': {}}
        manifest['runs'][label] = record
        write(args.out / 'manifest.json', manifest)
        if imported['exit'] != 0 or imported['logged_error']:
            failed = True
            continue
        result_path = evidence / 'timeline.json'
        record['probe'] = execute([*base, '--script', 'res://tests/' + PROBE.name, '--',
                                   '--output=' + str(result_path)], stage, evidence / 'probe.log')
        if record['probe']['exit'] != 0 or record['probe']['logged_error'] or not result_path.exists():
            failed = True
        else:
            data = json.loads(result_path.read_text(encoding='utf-8'))
            failed |= bool(data['failures'])
            record['timeline_sha256'] = sha(result_path)
            write(blind / (label + '.json'), data)
            record['metrics'] = [{k: v for k, v in row.items() if k not in ('rows', 'snapshots')}
                                 for row in data['conditions']]
        for test in TESTS:
            result = execute([*base, '--script', 'res://tests/' + test + '.gd'],
                             stage, evidence / (test + '.log'))
            record['tests'][test] = result
            failed |= result['exit'] != 0 or result['logged_error']
        record['shipping_after_sha256_by_path'] = shipping(game)
        record['shipping_unchanged'] = original == record['shipping_after_sha256_by_path']
        failed |= not record['shipping_unchanged']
        write(args.out / 'manifest.json', manifest)
        print(label, revision, 'finished; failures observed:', failed, flush=True)
    manifest['failed'] = failed
    runs = list(manifest['runs'].values())
    manifest['shipping_sources_identical'] = (len(runs) == 2 and
        runs[0]['shipping_sha256_by_path'] == runs[1]['shipping_sha256_by_path'])
    write(args.out / 'manifest.json', manifest)
    (blind / 'README.md').write_text(
        '# Blinded ACK-timeline outcomes\n\n'
        'Compare sample-J.json and sample-Q.json before inspecting mapping.json, the PR or report.\n'
        'The inputs are the same native probe and conditions, run serially on one host.\n'
        'Neither sample name implies treatment or expected superiority.\n\n'
        'Critique whether either outcome establishes a bounded accuracy improvement, whether the ACK metric\n'
        'covers held-input intervals, and whether these data can justify enabling prediction.\n'
        'Same-time position difference includes intentional prediction lead and is not pure replay error.\n'
        'This is deterministic in-process scheduling on a flat static floor, not real ENet or a shipping map.\n'
        'Request source checks after recording the outcome-only assessment.\n', encoding='utf-8')
    raise SystemExit(1 if failed else 0)


if __name__ == '__main__':
    main()
