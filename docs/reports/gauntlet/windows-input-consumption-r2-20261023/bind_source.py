#!/usr/bin/env python3
"""Bind frozen reader bytes, protected source and the initialized shallow copy."""
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[4]
REPORT = Path(__file__).resolve().parent
DEPTH = ROOT / '.local/depth-one-source'
SOURCE = '86fe3cbe3f191b328c1e08bf8d5adc0a937e39b1'
BASE = '161d72c5f4018e5a8fb24669e1d5054bb6b12edb'
CHANGED = ['scripts/analyze_input_consumption.py',
           'scripts/test_input_consumption_identity.py']
if sorted(os.sched_getaffinity(0)) != [4]:
    raise RuntimeError('CPU 4 only')


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args], text=True).strip()


def tree(commit):
    entries = subprocess.check_output(['git', '-C', str(ROOT), 'ls-tree', '-rz', commit])
    return {path.decode(): info.split()[2].decode()
            for info, path in (row.split(b'\t', 1) for row in entries.split(b'\0') if row)}


before, final = tree(BASE), tree(SOURCE)
delta = sorted(path for path in before.keys() | final.keys()
               if not path.startswith('docs/') and before.get(path) != final.get(path))
assert delta == CHANGED, delta
subprocess.run(['git', '-C', str(ROOT), 'merge-base', '--is-ancestor', SOURCE, 'HEAD'], check=True)
assert git(DEPTH, 'rev-parse', 'HEAD') == SOURCE
assert not git(ROOT, 'diff', SOURCE, '--', '.', ':!docs')
assert not git(DEPTH, 'status', '--porcelain')
assert git(DEPTH, 'rev-parse', '--is-shallow-repository') == 'true'
assert git(DEPTH, 'rev-list', '--count', 'HEAD') == '1'
prior = ROOT / 'docs/reports/gauntlet/windows-input-consumption-diagnostic-20261023/depth-one-source-bindings.json'
paths = sorted({row['path'] for row in json.loads(prior.read_text())['files']} | set(CHANGED))
files = []
for path in paths:
    raw = (ROOT / path).read_bytes()
    assert (DEPTH / path).read_bytes() == raw, path
    blob = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
    assert blob == final[path], path
    files.append({'path': path, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(),
                  'git_blob': blob})
original = Path('/workspace/reviews/windows-pulse-native-fresh-20261023/.local/native49/full/native-input')
expected = {'client.log': 'ec5fe22c681a9bd5ea0577773e9421d7f0eca6d2711b77c8c124f4cdefff4ba4',
            'server.log': '61937ac0d1c75f29f790ffc339a4dabaa0a29eac65e9c5da5b4c526835ed0757'}
originals = []
raw_copy = REPORT / 'original-native-log-bytes'
raw_copy.mkdir(exist_ok=True)
for name, digest in expected.items():
    raw = (original / name).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == digest, name
    replay = REPORT / 'packaged-final-controls/independent-25/original_failed_windows_untraced'
    derived = (replay / ('authority.log' if name == 'server.log' else name)).read_bytes()
    # The frozen critic rig uses read_text/write_text and normalizes CRLF.
    # Preserve that unchanged derivation and the separate original raw bytes.
    assert derived == raw.decode().replace('\r\n', '\n').replace('\r', '\n').encode()
    retained = raw_copy / name
    if retained.exists():
        assert retained.read_bytes() == raw
    else:
        retained.write_bytes(raw)
    originals.append({'path': str(original / name), 'bytes': len(raw), 'sha256': digest,
                      'retained_raw_copy': str(retained.relative_to(REPORT)),
                      'critic_text_derivation_bytes': len(derived),
                      'critic_text_derivation_sha256': hashlib.sha256(derived).hexdigest(),
                      'critic_derivation': 'Unchanged rig normalizes newlines through read_text/write_text'})
result = {'scope': 'Source and offline evidence identity only; no native qualification',
          'source': SOURCE, 'checkout_head': git(ROOT, 'rev-parse', 'HEAD'),
          'base': BASE, 'cpu_affinity': [4], 'non_doc_delta': delta,
          'all_other_non_doc_git_blobs_unchanged': True,
          'depth_source': SOURCE, 'depth_shallow': True, 'depth_commit_count': 1,
          'depth_tracked_index_paths': len(git(DEPTH, 'ls-files').splitlines()),
          'depth_status': '', 'available_prior_coverage_plus_new_test': len(files),
          'source_and_depth_match_frozen_git_blobs': True, 'files': files,
          'original_read_only_log_bindings': originals, 'passed': True}
(REPORT / 'source-bindings.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({key: value for key, value in result.items() if key != 'files'}, indent=2))
