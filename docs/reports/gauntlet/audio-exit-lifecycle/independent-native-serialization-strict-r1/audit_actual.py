#!/usr/bin/env python3
"""Read-only actual-byte, chronology, baseline and retention audit."""
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tarfile
import tempfile
import time

ROOT = Path(__file__).resolve().parents[5]
OUT = Path(__file__).resolve().parent
BUILDER = ROOT / 'docs/reports/gauntlet/audio-exit-lifecycle/native-serialization-strict-r1'
RAW = Path('/workspace/sightbreak-audio-exit-lifecycle/.local/audio-owner-r1-20261023')
CRITIC = Path('/workspace/reviews/audio-owner-r1-native/docs/reports/gauntlet/audio-exit-lifecycle/independent-native-r1')
BASE = '26a1c59ab6d141529a3254ac7f8e68ee4ae99d8b'
HANDOFF = 'bfca91617c4062a0b37d85c179869bbc9d4eccda'
sys.path.insert(0, str(ROOT / 'scripts'))
import analyze_audio_lifecycle as analyzer
import native_log


def descriptor(raw):
    return {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def tree(root):
    return {str(p.relative_to(root)): descriptor(p.read_bytes()) for p in sorted(root.rglob('*')) if p.is_file()}


def command(name, argv):
    start = time.monotonic()
    result = subprocess.run(argv, cwd=ROOT, capture_output=True, timeout=60)
    (OUT / (name + '.stdout')).write_bytes(result.stdout)
    (OUT / (name + '.stderr')).write_bytes(result.stderr)
    return {'command': argv, 'exit': result.returncode, 'seconds': time.monotonic() - start,
            'stdout': descriptor(result.stdout), 'stderr': descriptor(result.stderr)}


def main():
    raw = (RAW / 'input-mode.log').read_bytes()
    assert descriptor(raw) == {'bytes': 2000315, 'sha256': 'a50a819152083c3d73564f21a5f15d36571c1b79c7178831667092f07537a218'}
    text = raw.decode('utf-8'); lines = text.splitlines()
    indexed = [(n, json.loads(line[len('AUDIO_LIFECYCLE '):])) for n, line in enumerate(lines, 1) if line.startswith('AUDIO_LIFECYCLE ')]
    rows = [row for _, row in indexed]
    assert len(rows) == 6884
    assert indexed[0][0] == 17 and type(rows[0]['mix_rate']) is float and rows[0]['mix_rate'] == 44100.0
    assert all(row['sequence'] == n for n, row in enumerate(rows))
    for key in ('process_frame', 'physics_frame', 'usec'):
        assert all(type(row[key]) is int and row[key] >= 0 for row in rows)
        assert all(a[key] <= b[key] for a, b in zip(rows, rows[1:]))
    counts = Counter(row['kind'] for row in rows)
    assert dict(counts) == {'header': 1, 'object': 437, 'player': 1849, 'weak': 4374, 'checkpoint': 223}
    objects = {}; pending = []; windows = []; final = {}; roles = defaultdict(set); sealed = False
    canonical = lambda value: str(int(value) % (1 << 64))
    forced = ['before_hud_leave', 'after_hud_leave'] * 6 + ['before_final_leave', 'after_final_leave', 'final_pre_quit']
    for row in rows:
        assert not sealed
        kind = row['kind']
        if kind == 'object':
            identity = canonical(row['id']); assert identity not in objects
            objects[identity] = row
        elif kind == 'player':
            identity = canonical(row['id']); assert objects[identity]['class'] == 'AudioStreamPlayer3D'
            roles[row['state']['owner']['role']].add(identity)
        elif kind == 'weak':
            identity = canonical(row['id']); assert identity in objects and type(row['alive']) is bool
            pending.append((identity, row))
        elif kind == 'checkpoint':
            identities = [identity for identity, _ in pending]
            assert len(set(identities)) == len(identities)
            assert all(item['stage'] == row['stage'] for _, item in pending)
            if row['stage'] in set(forced):
                assert set(identities) == set(objects)
                windows.append({'stage': row['stage'], 'sequence': row['sequence'], 'objects': len(objects), 'weak': len(identities)})
            if row['stage'] == 'final_pre_quit':
                final = {identity: item['alive'] for identity, item in pending}; sealed = True
            pending = []
    assert sealed and not pending and [w['stage'] for w in windows] == forced
    assert rows[-1]['sequence'] == 6883 and rows[-1]['kind'] == 'checkpoint'
    role_counts = {role: len(ids) for role, ids in sorted(roles.items())}
    assert role_counts == {'actor_hurt': 70, 'actor_shot': 70, 'match_device': 7, 'reload_voice': 280}
    assert len(set.union(*roles.values())) == 427
    classes = Counter(row['class'] for row in objects.values())
    assert dict(classes) == {'AudioStreamPlayer3D': 427, 'AudioStreamWAV': 9, 'AudioStreamPlaybackWAV': 1}
    final_classes = Counter(objects[identity]['class'] for identity, alive in final.items() if alive)
    assert dict(final_classes) == {'AudioStreamWAV': 2}
    typed = [line for line in lines if line.startswith('Leaked instance:')]
    assert typed == []
    orphans = [{'line': n, 'text': line} for n, line in enumerate(lines, 1) if line.startswith('Orphan StringName: ')]
    summaries = [{'line': n, 'text': line} for n, line in enumerate(lines, 1) if line.startswith('StringName: ')]
    assert len(orphans) == 353 and orphans[0]['line'] == 6939
    assert summaries == [{'line': 7292, 'text': 'StringName: 353 unclaimed string names at exit.'}]
    assert all(native_log.failed(item['text']) for item in orphans + summaries)
    cases = json.loads((BUILDER / 'native-cases.json').read_text())
    assert cases['orphans'] == orphans and cases['summary'] == summaries[0]
    assert cases['header'] == {'line': 17, 'text': lines[16]}
    footer = [line for line in lines if line.startswith('INPUT_MODE_TEST ')]
    assert len(footer) == 1 and 'checks=462 failures=0 graphical_pointer=false' in footer[0] and footer[0].endswith('baseline=false')
    parsed = analyzer.analyze(text)
    assert parsed['strict_raw_log_failed'] is True and parsed['sample_status'] == 'untyped_strict_failure'
    assert parsed['leaks'] == [] and parsed['unobserved_leaks'] == [] and parsed['final_alive_player_ids'] == []
    assert parsed['fixture_owner_coverage_complete'] is True
    assert parsed['server_drain'] == 'unknown; no public acknowledgment' and parsed['cause'].startswith('unproven;')
    baseline_scanner = {}; exec(compile(subprocess.check_output(['git', 'show', BASE + ':scripts/native_log.py'], cwd=ROOT), 'baseline/native_log.py', 'exec'), baseline_scanner)
    assert baseline_scanner['failed'](text) is False
    commands = []
    with tempfile.TemporaryDirectory(prefix='audio-critic-baseline-') as directory:
        directory = Path(directory)
        for name in ('analyze_audio_lifecycle.py', 'native_log.py'):
            (directory / name).write_bytes(subprocess.check_output(['git', 'show', BASE + ':scripts/' + name], cwd=ROOT))
        commands.append(command('independent-baseline-analyzer', ['python3', str(directory / 'analyze_audio_lifecycle.py'), str(RAW / 'input-mode.log')]))
        assert commands[-1]['exit'] == 2
    assert (OUT / 'independent-baseline-analyzer.stderr').read_text() == 'Audio lifecycle evidence rejected: Probe header is invalid\n'
    commands.append(command('independent-corrected-analyzer', ['python3', 'scripts/analyze_audio_lifecycle.py', str(RAW / 'input-mode.log')]))
    assert commands[-1]['exit'] == 0
    cli = json.loads((OUT / 'independent-corrected-analyzer.stdout').read_text())
    assert cli['raw_log_bytes'] == len(raw) and cli['raw_log_sha256'] == descriptor(raw)['sha256']
    assert {k:v for k,v in cli.items() if not k.startswith('raw_log_')} == parsed
    commands.append(command('builder-replay-crosscheck', ['python3', str(BUILDER / 'replay_preserved.py'), str(RAW / 'input-mode.log'), '--raw-root', str(RAW), '--critic-root', str(CRITIC)]))
    assert commands[-1]['exit'] == 0
    (OUT / 'actual-command-receipts.json').write_text(json.dumps(commands, indent=2) + '\n')
    retention = json.loads((CRITIC / 'artifact-retention.json').read_text())
    archive = CRITIC / retention['archive']
    assert descriptor(archive.read_bytes()) == {k: retention[k] for k in ('bytes', 'sha256')}
    archive_members = {}
    with tarfile.open(archive, 'r:gz') as tar:
        for member in tar.getmembers():
            assert member.isfile() and member.name not in archive_members
            archive_members[member.name] = descriptor(tar.extractfile(member).read())
    assert archive_members == retention['members'] and len(archive_members) == 375
    before = json.loads((OUT / 'preservation-before.json').read_text())
    after = {'raw': tree(RAW), 'critic': tree(CRITIC),
             'original_head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=RAW.parent.parent, text=True).strip(),
             'original_status': subprocess.check_output(['git', 'status', '--porcelain=v1'], cwd=RAW.parent.parent, text=True)}
    assert before == after and after['original_head'] == BASE and after['original_status'] == ''
    assert archive_members | retention['omitted_cache_manifest'] == after['raw']
    assert len(retention['omitted_cache_manifest']) == 62
    historical = json.loads((RAW / 'overall.json').read_text())
    assert all(historical[k] is False for k in ('acquisition_integrity', 'passed', 'sample_strict_clean'))
    # Every builder evidence byte, including red and numeric-only failures, remains Git-bound.
    bound = {}
    for path in sorted(p for p in BUILDER.rglob('*') if p.is_file() and '__pycache__' not in p.parts):
        relative = str(path.relative_to(ROOT)); expected = subprocess.check_output(['git', 'show', HANDOFF + ':' + relative], cwd=ROOT)
        assert path.read_bytes() == expected
        bound[relative] = descriptor(expected)
    history = ['4cbc1f3', '1a3e7a8', 'e356343', 'aae1f0a', 'bfca916']
    for a,b in zip(history, history[1:]):
        assert subprocess.run(['git', 'merge-base', '--is-ancestor', a, b], cwd=ROOT).returncode == 0
    result = {'implementation': 'aae1f0a5e963a01dceb4aed1d9c3b0c40520c76f',
              'review_preregistration': '52cc8df', 'raw_log': descriptor(raw), 'line_count': len(lines),
              'record_counts': counts, 'object_classes': classes, 'role_counts': role_counts,
              'forced_windows': windows, 'final_alive_classes': final_classes,
              'actual_orphans': len(orphans), 'actual_summary': summaries[0], 'typed_leak_rows': typed,
              'baseline_analyzer_exit': 2, 'baseline_strict_scanner': False,
              'corrected_parse_exit': 0, 'corrected_strict_sample': 'FAIL', 'original_acquisition': 'REJECT',
              'complete_raw_files_unchanged': len(after['raw']), 'original_critic_files_unchanged': len(after['critic']),
              'archive': descriptor(archive.read_bytes()), 'archive_members_verified': len(archive_members),
              'omitted_cache_files_bound': len(retention['omitted_cache_manifest']),
              'builder_evidence_files_unchanged': len(bound), 'builder_evidence': bound,
              'history_order_verified': history, 'original_receipt': {k: historical[k] for k in ('acquisition_integrity', 'passed', 'sample_strict_clean')}}
    (OUT / 'preservation-after.json').write_text(json.dumps(after, indent=2) + '\n')
    (OUT / 'actual-audit.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('builder_evidence','forced_windows')}, indent=2))


if __name__ == '__main__':
    main()
