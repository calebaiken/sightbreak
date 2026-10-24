"""Read-only source-freeze comparison; historical Git objects are review inputs."""
import ast
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'scripts'))
from test_focus_resume_timing import resume_block


BASE = 'fa718efcbe6aa36e53ca12474454a5dccfc5e9b9'
path = Path('scripts/verify_offline_export.py')
baseline = ast.parse(subprocess.check_output(['git', 'show', BASE + ':' + str(path)], text=True))
changed = ast.parse(path.read_text())
before_body, before_start, before_end = resume_block(baseline)
body, start, end = resume_block(changed)
replacement = [ast.unparse(node) for node in body[start:end]]
assert replacement == ["key('Escape', True)", 'pause(0.3)', "key('Escape', False)"]
body[start:end] = deepcopy(before_body[before_start:before_end])
assert ast.dump(changed) == ast.dump(baseline)
print(json.dumps({'fence_only_freeze': BASE,
                  'combined_source': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
                  'controller_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                  'only_controller_ast_change': 'Replace focus-resume tap(Escape) with down, same 0.3 hold, up',
                  'replacement_statements': replacement,
                  'all_other_controller_ast_unchanged': True}, indent=2))
