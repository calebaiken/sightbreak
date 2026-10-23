#!/usr/bin/env python3
"""Read-only pure replay of the exact failed native log and optional originals."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT / 'scripts'))
import analyze_audio_lifecycle as analyzer
import native_log


def descriptor(path):
    raw = path.read_bytes()
    return {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('log', type=Path)
    parser.add_argument('--raw-root', type=Path)
    parser.add_argument('--critic-root', type=Path)
    args = parser.parse_args()
    preserved = json.loads((HERE / 'preserved-evidence.json').read_text())
    expected = preserved['raw_files']['input-mode.log']
    assert descriptor(args.log) == expected, 'Input is not the exact original native log'
    raw = args.log.read_bytes()
    text = raw.decode('utf-8')
    lines = text.splitlines()
    cases = json.loads((HERE / 'native-cases.json').read_text())
    for case in [cases['header'], *cases['orphans'], cases['summary']]:
        assert lines[case['line'] - 1] == case['text'], 'Retained excerpt disagrees with original raw bytes'
    assert len(cases['orphans']) == 353
    assert native_log.failed(text)
    assert all(native_log.failed(case['text']) for case in [*cases['orphans'], cases['summary']])
    report = analyzer.analyze(text)
    assert report['records'] == 6884 and report['objects'] == 437
    assert report['fixture_owner_coverage_complete']
    assert len(report['forced_weak_snapshots']) == 15 and report['final_checkpoint_sequence'] == 6883
    assert report['final_alive_player_ids'] == []
    assert report['strict_raw_log_failed'] and report['sample_status'] == 'untyped_strict_failure'
    assert report['leaks'] == [] and report['unobserved_leaks'] == []
    assert report['server_drain'] == 'unknown; no public acknowledgment'
    assert report['cause'].startswith('unproven;')
    result = {'source': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
              'raw_log': expected, 'actual_orphans': len(cases['orphans']),
              'pure_interpretation': report,
              'qualification': 'Pure parsing succeeds; strict sample FAIL and original acquisition REJECT remain.'}
    if args.raw_root:
        current = {str(p.relative_to(args.raw_root)): descriptor(p)
                   for p in sorted(args.raw_root.rglob('*')) if p.is_file()}
        assert current == preserved['raw_files'], 'Original raw file set or bytes changed'
        receipt = json.loads((args.raw_root / 'overall.json').read_text())
        assert all(receipt[key] is False for key in ('acquisition_integrity', 'passed', 'sample_strict_clean'))
        result['preserved_raw_files'] = len(current)
        result['original_receipt'] = {key: receipt[key] for key in ('acquisition_integrity', 'passed', 'sample_strict_clean')}
    if args.critic_root:
        expected_critic = {Path(path).name: value for path, value in preserved['critic_files'].items()}
        current = {p.name: descriptor(p) for p in args.critic_root.iterdir() if p.is_file()}
        assert current == expected_critic, 'Critic evidence file set or bytes changed'
        result['preserved_critic_files'] = len(current)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
