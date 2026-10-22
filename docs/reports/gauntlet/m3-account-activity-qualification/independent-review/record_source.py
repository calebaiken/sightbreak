#!/usr/bin/env python3
"""Record immutable source and cached pinned engine without launching Godot."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zipfile

root, output = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
reference = '471fbd8fe17611c0c93728bc571ea6158838b458'
prepared = '3b97a0043fc415c2408ed774f38710ac022cfd72'


def git(*args):
    return subprocess.check_output(['git', *args], cwd=root)


def digest(raw, algorithm='sha256'):
    return hashlib.new(algorithm, raw).hexdigest()


def function(raw, name):
    lines = raw.decode().splitlines(keepends=True)
    start = next(i for i, line in enumerate(lines) if line.startswith('func ' + name + '('))
    stop = next((i for i in range(start + 1, len(lines)) if lines[i].startswith('func ') or lines[i].startswith('@rpc')), len(lines))
    return ''.join(lines[start:stop]).rstrip().encode()


head = git('rev-parse', 'HEAD').decode().strip()
paths = ('scripts/test_account_match.py', 'scripts/test_account_match_output.py',
         'game/tests/account_match_probe.gd', 'game/scripts/gameplay/match.gd',
         'game/scripts/network/input_stream.gd', 'backend/app.py',
         'backend/config/economy.json', 'server/result_outbox.py', 'scripts/toolchain.py')
files = {}
for path in paths:
    raw = git('show', head + ':' + path)
    assert (root / path).read_bytes() == raw, path + ' differs from HEAD'
    files[path] = dict(sha256=digest(raw), git_blob=git('rev-parse', head + ':' + path).decode().strip())
trees = {p: {revision: git('rev-parse', revision + ':' + p).decode().strip()
             for revision in (reference, prepared, head)} for p in ('game', 'backend', 'server')}
assert trees['backend'][reference] == trees['backend'][head]
assert trees['server'][reference] == trees['server'][head]
for path in ('scripts/test_account_match.py', 'scripts/test_account_match_output.py', 'game/tests/account_match_probe.gd'):
    assert git('show', prepared + ':' + path) == git('show', head + ':' + path), 'qualification harness changed after prep'
functions = {}
for name in ('_start_ranked_match', '_ranked_payload', '_submit_ranked_result'):
    before = function(git('show', reference + ':game/scripts/gameplay/match.gd'), name)
    after = function(git('show', head + ':game/scripts/gameplay/match.gd'), name)
    assert before == after, name + ' contract changed'
    functions[name] = dict(reference_sha256=digest(before), current_sha256=digest(after), equal=True)
engine = Path('/workspace/tools/godot-4.7.2/Godot_v4.7.2-stable_linux.x86_64')
archive = engine.parent / 'godot.zip'
archive_digest = digest(archive.read_bytes(), 'sha512')
assert archive_digest == '9aa00f7a605200940bce3027a567b782f49bd8e940dd06ae9e987bd65aee1b1467edd56ed84fcdcbdd44354bf613bdbb4e5d2913e925850368e150c59ed54c65'
with zipfile.ZipFile(archive) as bundle:
    member = bundle.read(engine.name)
assert member == engine.read_bytes()
status = git('status', '--porcelain').decode()
assert not status, 'Builder worktree is dirty'
result = dict(source_commit=head, reference_commit=reference, prepared_commit=prepared,
              worktree=str(root), source_status=status, files=files, trees=trees,
              unchanged_result_contracts=functions,
              changed_game_scripts_since_reference=git('diff', '--name-only', reference, head, '--', 'game/scripts').decode().splitlines(),
              engine=dict(path=str(engine), sha256=digest(member), archive=str(archive), archive_sha512=archive_digest,
                          archive_matches_extracted_binary=True, method='Cached bytes only; no engine process launched'))
output.write_text(json.dumps(result, indent=2) + '\n')
print('Source/engine provenance:', head, 'game', trees['game'][head], flush=True)
