#!/usr/bin/env python3
"""Read-only complete non-document tree binding, beyond workflow payload paths."""
import json
from pathlib import Path
import subprocess

ROOT = next(p for p in Path(__file__).resolve().parents if (p / '.git').exists())
FREEZE = 'e28c8e90b9ef2d0c766bd9152c194e3197ceba9a'
PREVIOUS = 'c838907cf4978e53c57423e08c23277c34f4496d'
ROUTE = 'af13a9979988d8b19de670fe27b78672ad2369ed'
PATHS = {'scripts/native_settings_route.py', 'scripts/test_native_settings_route.py',
         'scripts/verify_offline_export.py', 'scripts/validate.sh'}


def inventory(commit):
    rows = subprocess.check_output(['git', 'ls-tree', '-r', '-z', commit], cwd=ROOT)
    result = {}
    for row in rows.split(b'\0'):
        if not row:
            continue
        metadata, path = row.split(b'\t', 1)
        path = path.decode()
        if path.startswith('docs/'):
            continue
        mode, kind, blob = metadata.decode().split()
        assert kind == 'blob', path
        result[path] = {'mode': mode, 'git_blob': blob}
    return result


if __name__ == '__main__':
    original, route, target = map(inventory, (PREVIOUS, ROUTE, FREEZE))
    delta = {p for p in original.keys() | target.keys() if original.get(p) != target.get(p)}
    assert delta == PATHS
    expected = dict(original)
    expected.update({p: route[p] for p in PATHS})
    assert expected == target
    print(json.dumps({'passed': True, 'freeze': FREEZE, 'previous': PREVIOUS, 'route': ROUTE,
                      'non_document_files': len(target), 'delta': sorted(delta),
                      'entire_non_document_tree_exact_union': True, 'inventory': target}, indent=2))
