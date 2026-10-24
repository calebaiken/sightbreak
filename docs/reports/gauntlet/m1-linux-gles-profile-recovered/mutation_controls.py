#!/usr/bin/env python3
"""Run the maintained pure controls against isolated controller mutations."""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[4]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    source = (ROOT / 'scripts/verify_offline_match.py').read_text()
    insertion = "        if args.linux_gpu_profile:\n            command.insert(1, '--gpu-profile')\n"
    mutations = {
        'candidate': None,
        'allow-sampler': ('or args.linux_frame_diagnostics):', '):'),
        'omit-engine-option': (insertion, ''),
        'profile-default': (insertion, "        command.insert(1, '--gpu-profile')\n"),
        'append-as-user-argument': ("command.insert(1, '--gpu-profile')", "command.append('--gpu-profile')"),
    }
    records = []
    for name, change in mutations.items():
        mutated = source
        if change:
            assert source.count(change[0]) == 1, name
            mutated = source.replace(*change)
        compile(mutated, name, 'exec')
        with tempfile.TemporaryDirectory(prefix='sightbreak-profile-pure-') as temporary:
            copy = Path(temporary) / 'verify_offline_match.py'
            copy.write_text(mutated)
            environment = dict(os.environ, PYTHONPATH=os.pathsep.join((temporary, str(ROOT / 'scripts'))))
            command = [sys.executable, '-m', 'unittest', 'test_linux_gpu_profile', '-v']
            result = subprocess.run(command, cwd=temporary, env=environment,
                                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=30)
        raw = result.stdout
        archive = gzip.compress(raw, mtime=0)
        output = args.output / (name + '.txt.gz')
        output.write_bytes(archive)
        assert gzip.decompress(output.read_bytes()) == raw
        expected_pass = change is None
        records.append({'case': name, 'controller_sha256': hashlib.sha256(mutated.encode()).hexdigest(),
                        'command': command, 'exit_code': result.returncode,
                        'expected_pass': expected_pass, 'expectation_met': (result.returncode == 0) == expected_pass,
                        'raw_bytes': len(raw), 'raw_sha256': hashlib.sha256(raw).hexdigest(),
                        'gzip_path': output.name, 'gzip_sha256': hashlib.sha256(archive).hexdigest()})
    summary = {'controller_sha256': hashlib.sha256(source.encode()).hexdigest(),
               'test_sha256': hashlib.sha256((ROOT / 'scripts/test_linux_gpu_profile.py').read_bytes()).hexdigest(),
               'native_engine_export_runs': 0, 'results': records}
    (args.output / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2))
    assert all(record['expectation_met'] for record in records), 'A controller mutation escaped the maintained controls'


if __name__ == '__main__':
    main()
