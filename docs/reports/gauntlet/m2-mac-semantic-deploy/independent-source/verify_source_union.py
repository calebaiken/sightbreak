#!/usr/bin/env python3
"""Independent full Git mode/blob union and exact accepted-import comparison."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

repo, candidate, target = sys.argv[1:]
def git(*args):
    return subprocess.check_output(['git', '-C', repo, *args])
def tree(ref):
    rows = {}
    for raw in git('ls-tree', '-r', '-z', ref).split(b'\0'):
        if raw:
            prefix, name = raw.split(b'\t', 1)
            path = name.decode()
            if not path.startswith('docs/'):
                rows[path] = prefix.decode()
    return rows
def sha(ref, path):
    return hashlib.sha256(git('show', ref + ':' + path)).hexdigest()
union = json.loads(git('show', candidate + ':docs/reports/gauntlet/m2-mac-semantic-deploy/source-union.json'))
base, upstream = union['base'], union['read_only_source']
a, b = tree(base), tree(candidate)
changed = {p: {'base': a.get(p), 'candidate': b.get(p)} for p in sorted(a.keys() | b.keys()) if a.get(p) != b.get(p)}
allowed = (set(union['exact_imports']) | set(union['adapted_tests']) | set(union['combined_new_or_changed_runtime'])
           | {'scripts/test_macos_semantic_deploy.py'} | set(union['self_contained_source_fixtures']))
imports = {p: {'candidate': sha(candidate, p), 'upstream': sha(upstream, p), 'expected': expected}
           for p, expected in union['exact_imports'].items()}
declared = {}
for section in ('exact_imports', 'adapted_tests', 'combined_new_or_changed_runtime', 'self_contained_source_fixtures'):
    declared.update(union[section])
result = {'base': base, 'candidate': candidate, 'base_non_docs': len(a), 'candidate_non_docs': len(b),
          'unchanged': sum(a.get(p) == b.get(p) for p in a.keys() | b.keys()), 'delta': changed,
          'undeclared_delta': sorted(set(changed) - allowed), 'exact_imports': imports,
          'exact_imports_match': all(x['candidate'] == x['upstream'] == x['expected'] for x in imports.values()),
          'all_declared_sha256_match': all(sha(candidate, p) == expected for p, expected in declared.items()),
          'base_game_tree': git('rev-parse', base + ':game').decode().strip(),
          'candidate_game_tree': git('rev-parse', candidate + ':game').decode().strip(),
          'reported_game_tree': union['unaltered_game_tree'],
          'workflow_equal': git('show', base + ':.github/workflows/desktop-alpha.yml') == git('show', candidate + ':.github/workflows/desktop-alpha.yml')}
result['passed'] = (not result['undeclared_delta'] and result['exact_imports_match']
                    and result['all_declared_sha256_match'] and result['workflow_equal']
                    and result['base_game_tree'] == result['candidate_game_tree'] == result['reported_game_tree'])
Path(target).write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({k: v for k, v in result.items() if k not in ('delta', 'exact_imports')}, indent=2))
raise SystemExit(0 if result['passed'] else 1)
