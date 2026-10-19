import ast
import json
from pathlib import Path
import subprocess

out = Path('C:/Users/blith/AppData/Local/Temp/opencode/sightbreak-backend-trade-evidence')
def git(*args):
    return subprocess.check_output(['git', *args], text=True).strip()
baseline = '701ce2c4d7f8b2872cf1fefa64cb6edd0cd1a3fd'
candidate = git('rev-parse', 'HEAD')
def declarations(ref):
    node = ast.parse(git('show', ref + ':backend/app.py'))
    return {n.name: ast.dump(n, include_attributes=False) for n in node.body
            if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
a, b = declarations(baseline), declarations(candidate)
changed = [name for name in sorted(a.keys() | b.keys()) if a.get(name) != b.get(name)]
paths = ['game', 'server', 'backend/models.py', 'backend/migrations', 'backend/config',
         'backend/uv.lock', 'backend/tests/test_economy.py']
record = {'baseline': baseline, 'candidate': candidate, 'changed_app_declarations': changed,
          'unchanged_objects': {p: {'baseline': git('rev-parse', baseline + ':' + p),
                                    'candidate': git('rev-parse', candidate + ':' + p)} for p in paths},
          'pr15_ancestor': subprocess.run(['git', 'merge-base', '--is-ancestor', '228c382', candidate]).returncode == 0,
          'baseline_backend': git('rev-parse', baseline + ':backend'),
          'pr16_backend': git('rev-parse', 'd2439ac:backend'),
          'pr15_backend': git('rev-parse', '228c382:backend')}
assert changed == ['trade_json', 'trades']
assert all(v['baseline'] == v['candidate'] for v in record['unchanged_objects'].values())
(out / 'source-preservation.json').write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps(record, indent=2))
