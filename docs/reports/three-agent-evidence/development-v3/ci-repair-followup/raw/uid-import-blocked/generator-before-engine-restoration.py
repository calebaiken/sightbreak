"""Generate one new script's Godot UID in an isolated, native editor import."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(r'C:\Users\blith\AppData\Local\Temp\opencode\sightbreak-v3')
sys.path.insert(0, str(ROOT / 'scripts'))
from matrix_process import run_process
from native_log import failed
from godot_process import godot_environment

OUT = Path(__file__).parent / 'attempt'
OUT.mkdir()
PROJECT = OUT / 'project'
SCRIPT = 'game/scripts/network/ack_snapshot_diagnostics.gd'
SOURCE = '0fbce120d8c17db58596d280f7d8401ab2aa0937'
ENGINE = Path(r'C:\Users\blith\AppData\Local\Temp\opencode\godot\Godot_v4.7.2-stable_win64.exe')
source_bytes = subprocess.check_output(['git', 'show', f'{SOURCE}:{SCRIPT}'], cwd=ROOT)
script = PROJECT / 'scripts/network/ack_snapshot_diagnostics.gd'
script.parent.mkdir(parents=True)
script.write_bytes(source_bytes)
(PROJECT / 'project.godot').write_text(
    'config_version=5\n\n[application]\nconfig/name="Snapshot UID import"\n'
    '\n[rendering]\nrenderer/rendering_method="gl_compatibility"\n', encoding='utf-8')
with ENGINE.open('rb') as stream:
    engine_hash = hashlib.file_digest(stream, 'sha256').hexdigest()
command = [str(ENGINE), '--headless', '--path', str(PROJECT), '--log-file',
           str(OUT / 'editor.engine.log'), '--editor', '--import', '--quit']
before = {'source_commit': SOURCE, 'source_path': SCRIPT,
          'source_sha256': hashlib.sha256(source_bytes).hexdigest(),
          'engine_sha256': engine_hash, 'command': command,
          'scope': 'One-script isolated editor import; not a full-game validation.'}
(OUT / 'source-before.json').write_text(json.dumps(before, indent=2) + '\n', encoding='utf-8')
with (OUT / 'editor.process.log').open('x', encoding='utf-8') as log:
    code = run_process(command, cwd=PROJECT, env=godot_environment(root=PROJECT), log=log,
                       result_path=OUT / 'editor.process.json', timeout=45)
engine_log = (OUT / 'editor.engine.log').read_text(encoding='utf-8', errors='replace')
process_log = (OUT / 'editor.process.log').read_text(encoding='utf-8', errors='replace')
uid = script.with_suffix('.gd.uid').read_text(encoding='utf-8').strip()
passed = (code == 0 and not failed(engine_log) and not failed(process_log)
          and 'HARNESS_ERROR' not in process_log and re.fullmatch(r'uid://[a-z0-9]+', uid) is not None
          and script.read_bytes() == source_bytes)
result = {**before, 'passed': bool(passed), 'exit': code, 'uid': uid,
          'uid_sha256': hashlib.sha256(script.with_suffix('.gd.uid').read_bytes()).hexdigest(),
          'source_unchanged': script.read_bytes() == source_bytes}
(OUT / 'results.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(json.dumps(result, indent=2))
raise SystemExit(0 if passed else 1)
