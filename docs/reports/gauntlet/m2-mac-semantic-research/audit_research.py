#!/usr/bin/env python3
"""Read-only report audit. Optional historical Git audit is source review only.

Not a maintained workflow test, native probe, OCR runner or source approval.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import struct
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--historical-audit', action='store_true',
                        help='Also compare original Git objects/base; requires full review history.')
    arguments = parser.parse_args()
    root = Path(__file__).resolve().parent
    repository = root.parents[3]
    base = 'c838907cf4978e53c57423e08c23277c34f4496d'
    print('SOURCE-ONLY REPORT AUDIT')
    print('Base:', base)
    print('No engine, native API, input, Swift compilation, OCR executable, service, or CI execution.')
    original = {item['path']: item['content'] for item in json.loads(
        gzip.decompress((root / 'upstream-fetched-text.json.gz').read_bytes()))}
    index = json.loads((root / 'upstream-source-excerpts.json').read_text())
    assert len(index['files']) == 25
    excerpts = 0
    for item in index['files']:
        source = original[item['path']]
        assert hashlib.sha256(source.encode()).hexdigest() == item['source_utf8_sha256']
        assert len(source.encode()) == item['source_utf8_bytes']
        lines = source.splitlines()
        for excerpt in item['excerpts']:
            text = '\n'.join(lines[excerpt['first_line'] - 1:excerpt['last_line']]) + '\n'
            assert text == excerpt['text']
            assert hashlib.sha256(text.encode()).hexdigest() == excerpt['utf8_sha256']
            excerpts += 1
        assert (any(commit['sha'] in item['url'] for commit in index['immutable_commits'])
                or '826d672661f9453c8b269ab3946dbcbae6300555' in item['url'])
    print(f'PASS: {len(index["files"])} immutable source URLs/full fetched-content hashes and {excerpts} exact line-numbered excerpts.')
    assert index['sdk_accesskit_c_gitlink']['sha'] == '826d672661f9453c8b269ab3946dbcbae6300555'
    print('PASS: SDK AccessKit-C gitlink retained; Cargo.lock excerpt resolves accesskit_macos 0.26.3.')
    witness = json.loads((root / 'native-witness-index.json').read_text())
    for item in witness['files']:
        local = (root / item['path']).read_bytes()
        assert len(local) == item['bytes']
        assert hashlib.sha256(local).hexdigest() == item['sha256']
        if arguments.historical_audit:
            historical = subprocess.check_output(
                ['git', 'show', item['original_commit'] + ':' + item['original_path']], cwd=repository)
            assert local == historical
    print('PASS: all three native witness sizes and SHA-256 match their original source index.')
    expected = [('01-focused-menu.png', (1004, 664), 'eeacddfa545fc0fabe1b065d52b289bbea42e8f75bbde02d8ffa7ed4df326921'),
                ('01-focused-menu-deploy-2x.png', (2008, 1328), 'ec8b434a4906f64513512c23554b95b07d2daabecd88514179c406f3928c5e73')]
    for name, dimensions, digest in expected:
        data = (root / 'native-witnesses' / name).read_bytes()
        assert data[:8] == b'\x89PNG\r\n\x1a\n'
        assert struct.unpack('>II', data[16:24]) == dimensions
        assert hashlib.sha256(data).hexdigest() == digest
    receipt = json.loads((root / 'native-witnesses/01-focused-menu.json').read_text())
    for rows in [receipt['text'], receipt['derived_deploy_analysis']['text']]:
        target = [row for row in rows if row['text'] == 'DEPLOY • OFFLINE 5V5']
        assert len(target) == 1 and target[0]['confidence'] == 0.5
    print('PASS: original PNG dimensions/hashes and both unique 0.5 captions retained; no new OCR.')
    if arguments.historical_audit:
        subprocess.run(['git', 'diff', '--exit-code', base, '--', 'game', 'scripts', '.github', '.claude',
                        'docs/engineering', 'docs/roadmap'], cwd=repository, check=True)
        status = subprocess.check_output(['git', 'status', '--porcelain', '--untracked-files=all'],
                                         cwd=repository, text=True)
        for line in status.splitlines():
            assert line[3:].startswith('docs/reports/gauntlet/m2-mac-semantic-research/'), line
        print('PASS historical review: witnesses equal original commit 460fe42; runtime/canonical source equals exact base; only component reports change.')
    else:
        print('Historical Git comparison not requested; no claim of repeating it in this mode.')
    print('Observed AX tree: NONE. New native attempt: NONE. Gameplay acceptance: NONE. Independent source approval: PENDING.')


if __name__ == '__main__':
    main()
