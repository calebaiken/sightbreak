#!/usr/bin/env python3
"""Full non-doc source union plus exact erasure of the two scoped changes."""
import ast
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[5]
OUT = Path(__file__).resolve().parents[1]
BASE = '7101350e5d0a2f6e4afb9a913b5b1bcf2107857a'
SOURCE = '4cf6ac8e744603ed6af122a362036d276754cc76'
ALLOWED = ['scripts/test_native_route_pulse.py', 'scripts/verify_integration_export.py']
assert sorted(os.sched_getaffinity(0)) == [4]


def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args])


def tree(ref):
    result = {}
    for row in git('ls-tree', '-rz', ref).split(b'\0'):
        if row:
            meta, path = row.split(b'\t');path = path.decode()
            if not path.startswith('docs/'):
                mode, kind, oid = meta.decode().split()
                result[path] = dict(mode=mode, kind=kind, oid=oid)
    return result


def method_bounds(text):
    return text.index('    def key_pulse('), text.index('\n    def button(', text.index('    def key_pulse('))


base, candidate = tree(BASE), tree(SOURCE)
assert base.keys() == candidate.keys() and len(base) == 508
changed, rows, omitted = [], [], []
for name in sorted(base):
    old, current = base[name], candidate[name]
    assert (old['mode'], old['kind']) == (current['mode'], current['kind']), name
    original = git('cat-file', 'blob', old['oid'])
    raw = git('cat-file', 'blob', current['oid'])
    if old != current:
        changed.append(name)
        assert name in ALLOWED
        s, b = raw.decode(), original.decode()
        if name.endswith('verify_integration_export.py'):
            lo, hi = method_bounds(s);blo, bhi = method_bounds(b)
            assert s[:lo] + b[blo:bhi] + s[hi:] == b
            fixture = (OUT / 'controls/baseline_key_pulse.py').read_text()
            assert fixture == 'import ctypes as C\nimport time\n\n' + b[blo:bhi][4:].replace('\n    ', '\n')
        else:
            assert s.count('import math\n') == 1
            s = s.replace('import math\n', '')
            lo = s.index('class IndependentClockPulse') - 2
            hi = s.index("if __name__ == '__main__':", lo)
            assert s[:lo] + s[hi:] == b
        erased = original
    else:
        assert raw == original
        erased = raw
    path = ROOT / name
    if path.exists():
        assert path.read_bytes() == raw, name
    else:
        omitted.append(name)
    rows.append(dict(path=name, baseline=old, candidate=current,
                     original_sha256=hashlib.sha256(original).hexdigest(),
                     candidate_sha256=hashlib.sha256(raw).hexdigest(),
                     erased_sha256=hashlib.sha256(erased).hexdigest()))
assert changed == ALLOWED
assert not git('diff', '--name-only', SOURCE, '--', ':!docs/')
report = dict(passed=True, base=BASE, source=SOURCE, cpu_affinity=[4],
              path_count=len(rows), changed_original_paths=changed,
              unchanged_path_count=len(rows)-len(changed),
              all_modes_equal=True, scoped_erasure_equal=True,
              sparse_omitted_paths=omitted, identities=rows)
(OUT / 'source-union.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({k:v for k,v in report.items() if k not in ('identities','sparse_omitted_paths')},indent=2))
