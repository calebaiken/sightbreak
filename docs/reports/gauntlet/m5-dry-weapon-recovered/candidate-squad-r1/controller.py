#!/usr/bin/env python3
"""Bounded single-engine runner with exact source and owned-session receipts."""
from pathlib import Path
import hashlib
import json
import os
import signal
import subprocess
import sys
import time

repo = Path(__file__).resolve().parents[1]
label, script, expected_source = sys.argv[1:4]
out = repo / 'docs/reports/gauntlet/m5-dry-weapon-recovered' / label
command = ['./scripts/godot.sh', '--headless', '--audio-driver', 'Dummy', '--script', script]
timeout_seconds = 120


def proc_table():
    table = {}
    for entry in Path('/proc').iterdir():
        if not entry.name.isdigit():
            continue
        try:
            stat = (entry / 'stat').read_text()
            fields = stat[stat.rindex(')') + 2:].split()
            argv = (entry / 'cmdline').read_bytes().split(b'\0')
            table[int(entry.name)] = {
                'pid': int(entry.name), 'ppid': int(fields[1]),
                'pgrp': int(fields[2]), 'sid': int(fields[3]),
                'start_ticks': int(fields[19]), 'state': fields[0],
                'argv': [arg.decode(errors='replace') for arg in argv if arg],
            }
        except (FileNotFoundError, ProcessLookupError, PermissionError, ValueError):
            continue
    return table


def engines(table):
    return [value for value in table.values()
            if value['argv'] and Path(value['argv'][0]).name.startswith('Godot_')]


def source():
    files = ['game/tests/bot_dry_weapon_test.gd', 'game/tests/bot_dry_weapon_test.gd.uid',
             'game/scripts/gameplay/bot_ai.gd', 'game/scripts/gameplay/actor.gd']
    return {
        'head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=repo, text=True).strip(),
        'tracked_diff': subprocess.check_output(['git', 'diff', '--binary', 'HEAD'], cwd=repo, text=True),
        'sha256': {name: hashlib.sha256((repo / name).read_bytes()).hexdigest() for name in files},
    }


before = source()
assert before['head'] == expected_source and not before['tracked_diff'], before
before_engines = engines(proc_table())
assert not before_engines, before_engines
out.mkdir(parents=True, exist_ok=False)
controller = Path(__file__).read_bytes()
(out / 'controller.py').write_bytes(controller)
(out / 'source-before.json').write_text(json.dumps(before, indent=2) + '\n')
environment = os.environ.copy()
environment['SIGHTBREAK_TOOLS_DIR'] = '/workspace/tools'
environment['SIGHTBREAK_STATE_DIR'] = str(repo / '.local' / ('dry-weapon-' + label + '-state'))
start = time.monotonic()
seen = {}
timed_out = False
cleanup_signals = []
with (out / 'runtime.log').open('wb') as log:
    child = subprocess.Popen(command, cwd=repo, env=environment, stdout=log,
                             stderr=subprocess.STDOUT, start_new_session=True)
    while child.poll() is None:
        table = proc_table()
        for item in table.values():
            if item['sid'] == child.pid:
                seen[(item['pid'], item['start_ticks'])] = item
        if time.monotonic() - start >= timeout_seconds:
            timed_out = True
            os.killpg(child.pid, signal.SIGTERM)
            cleanup_signals.append('SIGTERM to owned session process group')
            try:
                child.wait(timeout=3)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid, signal.SIGKILL)
                cleanup_signals.append('SIGKILL to owned session process group')
            break
        time.sleep(0.05)
    exit_code = child.wait(timeout=5)

after_table = proc_table()
owned_remaining = [item for item in after_table.values() if item['sid'] == child.pid]
if owned_remaining:
    os.killpg(child.pid, signal.SIGTERM)
    cleanup_signals.append('SIGTERM to remaining owned descendants')
    deadline = time.monotonic() + 3
    while time.monotonic() < deadline:
        after_table = proc_table()
        owned_remaining = [item for item in after_table.values() if item['sid'] == child.pid]
        if not owned_remaining:
            break
        time.sleep(0.05)
if owned_remaining:
    os.killpg(child.pid, signal.SIGKILL)
    cleanup_signals.append('SIGKILL to remaining owned descendants')
after_table = proc_table()
owned_remaining = [item for item in after_table.values() if item['sid'] == child.pid]
after = source()
(out / 'source-after.json').write_text(json.dumps(after, indent=2) + '\n')
raw = (out / 'runtime.log').read_bytes()
rows = raw.decode(errors='replace').splitlines()
results = [json.loads(line.removeprefix('BOT_DRY_WEAPON_RESULT '))
           for line in rows if line.startswith('BOT_DRY_WEAPON_RESULT ')]
receipt = {
    'label': label, 'command': command, 'cwd': str(repo),
    'source_head': expected_source, 'timeout_seconds': timeout_seconds,
    'private_state_dir': environment['SIGHTBREAK_STATE_DIR'],
    'controller_sha256': hashlib.sha256(controller).hexdigest(),
    'runtime_log_sha256': hashlib.sha256(raw).hexdigest(),
    'engine_processes_before': before_engines,
    'pid': child.pid, 'sid': child.pid,
    'observed_owned_processes': list(seen.values()),
    'exit_code': exit_code, 'timed_out': timed_out,
    'duration_seconds': time.monotonic() - start,
    'cleanup_signals': cleanup_signals, 'owned_processes_after': owned_remaining,
    'engine_processes_after': engines(after_table),
    'tracked_source_unchanged': before == after,
    'fixture_result': results,
    'error_lines': [line for line in rows if line.startswith(('SCRIPT ERROR', 'ERROR:')) or 'Parse Error' in line],
}
(out / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps(receipt, indent=2))
assert before == after and not owned_remaining
sys.exit(exit_code if not timed_out else 124)
