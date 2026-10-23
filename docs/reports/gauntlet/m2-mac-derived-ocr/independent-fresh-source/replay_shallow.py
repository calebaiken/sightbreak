#!/usr/bin/env python3
"""Run only the Deploy pure suite in a separate exact-ref depth-one checkout."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[5]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ref', default='a282b3f55c4014072144f3184e91fbefbafc0077')
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--expected-exit', type=int, default=1)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    records = []
    with tempfile.TemporaryDirectory(prefix='sightbreak-ocr-shallow-replay-') as temporary:
        checkout = Path(temporary) / 'checkout'
        checkout.mkdir()

        def run(label, command):
            result = subprocess.run(command, cwd=checkout, stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT, timeout=60)
            path = args.output / (label + '.txt')
            path.write_bytes(result.stdout)
            records.append({'label': label, 'command': command, 'exit_code': result.returncode,
                            'log': path.name, 'sha256': hashlib.sha256(result.stdout).hexdigest()})
            return result

        for label, command in (
                ('init', ['git', 'init']),
                ('remote', ['git', 'remote', 'add', 'origin', ROOT.as_uri()]),
                ('fetch', ['git', 'fetch', '--depth=1', '--filter=blob:none',
                           '--upload-pack=git -c uploadpack.allowFilter=true upload-pack', 'origin', args.ref]),
                ('sparse', ['git', 'sparse-checkout', 'set', '--cone', 'scripts',
                            'docs/reports/gauntlet/m2-mac-derived-ocr']),
                ('checkout', ['git', 'checkout', '--detach', 'FETCH_HEAD'])):
            result = run(label, command)
            assert result.returncode == 0, result.stdout.decode()
        head = run('head', ['git', 'rev-parse', 'HEAD']).stdout.decode().strip()
        shallow = run('shallow', ['git', 'rev-parse', '--is-shallow-repository']).stdout.decode().strip()
        assert head == args.ref and shallow == 'true', (head, shallow)
        result = run('deploy-controls', [sys.executable, 'scripts/test_macos_deploy_ocr.py', '-v'])
        (args.output / 'result.json').write_text(json.dumps({
            'scope': 'Exact-ref local shallow Git checkout and pure tests only; no native/CI execution',
            'head': head, 'shallow': shallow,
            'test_source_sha256': hashlib.sha256((checkout / 'scripts/test_macos_deploy_ocr.py').read_bytes()).hexdigest(),
            'exit_code': result.returncode, 'expected_exit_code': args.expected_exit,
            'commands': records}, indent=2) + '\n')
        print(result.stdout.decode(), end='')
        return 0 if result.returncode == args.expected_exit else 1


if __name__ == '__main__':
    raise SystemExit(main())
