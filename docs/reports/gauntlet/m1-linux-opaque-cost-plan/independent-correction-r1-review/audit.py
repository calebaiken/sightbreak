#!/usr/bin/env python3
"""Independent source/pure re-review. Fake children; real Python POSIX timer only."""
from contextlib import ExitStack, redirect_stdout
from copy import deepcopy
import hashlib
import io
import json
import os
from pathlib import Path
import runpy
import signal
import subprocess
import sys
import time
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[5]
OUT = Path(__file__).resolve().parent
PLAN = 'docs/reports/gauntlet/m1-linux-opaque-cost-plan/'
CORRECTION = ROOT / PLAN / 'implementation-correction-r1'
FROZEN = '3fd9718bc066bedf879f241760c106ee96923060'
OLD = '12901729f7be29d0f64d87a0d92219a84500f1a6'
CRITIC = '51add37cd801731016a2f52049e66b17fa90b393'
sys.path.insert(0, str(ROOT / 'scripts'))
import linux_profile_overhead as d
import test_linux_profile_overhead as supplied

def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)

def blob(commit, path):
    return git('show', commit + ':' + path)

ledger = json.loads(blob(FROZEN, PLAN + 'implementation-correction-r1/source.json'))
for row in ledger['files']:
    data = (ROOT / row['path']).read_bytes()
    assert data == blob(FROZEN, row['path'])
    assert len(data) == row['bytes'] and hashlib.sha256(data).hexdigest() == row['sha256']
for name in ('REVIEW.md', 'audit.py', 'pure-controls.txt', 'recomputed.json'):
    assert (CORRECTION / 'retained-rejection' / name).read_bytes() == blob(
        CRITIC, PLAN + 'independent-fixture-review/' + name)
assert not git('diff', OLD, FROZEN, '--', 'game', 'scripts/verify_offline_match.py',
               'scripts/diagnostics/linux_profile_overhead.gd', 'scripts/diagnostics/linux_profile_overhead.tscn',
               PLAN + 'PREREGISTRATION.md', 'docs/engineering', 'docs/roadmap')
assert git('rev-parse', FROZEN + ':game').decode().strip() == ledger['shipping_game_tree']

pure = subprocess.run([sys.executable, 'scripts/test_linux_profile_overhead.py', '-v'],
                      cwd=ROOT, capture_output=True, text=True)
(OUT / 'pure-controls.txt').write_text(pure.stdout + pure.stderr)
assert pure.returncode == 0

# Execute the retained original AST replay without rewriting the builder receipt.
original_write = d.write
def redirected_write(path, value):
    if Path(path) == CORRECTION / 'replay.json':
        path = OUT / 'original-counterexample-replay.json'
    return original_write(path, value)
with patch.object(d, 'write', side_effect=redirected_write), redirect_stdout(io.StringIO()):
    replay_namespace = runpy.run_path(str(CORRECTION / 'replay.py'))
replay = replay_namespace['result']
assert replay == d.read_json(CORRECTION / 'replay.json')

def real_timer_controls():
    previous = signal.getsignal(signal.SIGALRM)
    assert signal.getitimer(signal.ITIMER_REAL) == (0.0, 0.0)
    read_fd, write_fd = os.pipe()
    started = time.monotonic()
    record = {}
    try:
        try:
            with d.Deadline(record, 0.04).armed('independent blocked Python pipe read'):
                os.read(read_fd, 1)
        except TimeoutError as error:
            interruption = str(error)
        else:
            raise AssertionError('The real alarm failed to interrupt os.read')
    finally:
        os.close(read_fd)
        os.close(write_fd)
    elapsed = time.monotonic() - started
    assert 'interrupted independent blocked Python pipe read' in interruption
    assert signal.getsignal(signal.SIGALRM) == previous
    assert signal.getitimer(signal.ITIMER_REAL) == (0.0, 0.0)
    sentinel = lambda *_args: None
    signal.signal(signal.SIGALRM, sentinel)
    signal.setitimer(signal.ITIMER_REAL, 5)
    try:
        try:
            with d.Deadline({}).armed('preexisting real alarm'):
                raise AssertionError('An active alarm was accepted')
        except d.Invalid as error:
            active_rejection = str(error)
        assert signal.getsignal(signal.SIGALRM) is sentinel
        remaining = signal.getitimer(signal.ITIMER_REAL)[0]
        assert 0 < remaining <= 5
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)
    try:
        with d.Deadline({}).armed('body failure'):
            raise ValueError('independent body failure')
    except ValueError:
        pass
    assert signal.getsignal(signal.SIGALRM) == previous
    assert signal.getitimer(signal.ITIMER_REAL) == (0.0, 0.0)
    return {'real_pipe_read_interrupted': True, 'elapsed_seconds': elapsed,
            'interruption': interruption, 'previous_handler_restored': True,
            'active_alarm_rejected_without_replacing_handler_or_timer': active_rejection,
            'body_exception_restores_handler_and_disarms': True,
            'native_processes_started': 0}

def additional_deadline_controls():
    check = d.Deadline.check
    observe = d.Deadline.observe
    cases = {}
    stages = ('client spawned', 'published ready.json', 'read ready.json', 'owned launch observed',
              'initial host observed', 'begin acknowledged', 'published metrics.json', 'read metrics.json',
              'final host observed', 'payload verified', 'finish acknowledged', 'before child wait',
              'child completed', 'final cgroup observed', 'PNG verified', 'final client log read:complete',
              'condition acceptance:entry', 'condition validated', 'condition published',
              'condition publication reread', 'condition accepted after final read', 'condition acceptance:complete')
    for target in stages:
        hit = []
        def injected(self, stage):
            if stage == target and not hit:
                hit.append(stage)
                d.time.monotonic.side_effect = lambda: self.until + 0.001
            return check(self, stage)
        with patch.object(d.Deadline, 'check', injected):
            summary, registry = supplied.DeadlineReplayTests().execute('valid_before_boundary')
        assert hit == [target] and not summary['passed'] and len(registry) == 1
        assert summary['records'][0]['timeout'] is True
        cases[target] = {'passed': False, 'clients_launched': len(registry), 'error': summary.get('error')}
    def late_cleanup(self, stage):
        if stage == 'owned cleanup ended':
            d.time.monotonic.side_effect = lambda: self.until + 0.001
        return observe(self, stage)
    with patch.object(d.Deadline, 'observe', late_cleanup):
        summary, registry = supplied.DeadlineReplayTests().execute('valid_before_boundary')
    assert not summary['passed'] and len(registry) == 1 and summary['records'][0]['timeout']
    cases['owned cleanup ended'] = {'passed': False, 'clients_launched': len(registry), 'error': summary.get('error')}
    run_block = d.run_block
    current = {}
    initialize = d.Deadline.__init__
    def remember(self, *args, **kwargs):
        initialize(self, *args, **kwargs)
        current['deadline'] = self
    def source_checked(*args, **kwargs):
        def source_check():
            if 'deadline' in current:
                deadline = current['deadline']
                d.time.monotonic.side_effect = lambda: deadline.until + 0.001
        return run_block(*args, **kwargs, source_check=source_check)
    with patch.object(d.Deadline, '__init__', remember), patch.object(d, 'run_block', source_checked):
        summary, registry = supplied.DeadlineReplayTests().execute('valid_before_boundary')
    assert not summary['passed'] and len(registry) == 1 and summary['records'][0]['timeout']
    cases['source rechecked'] = {'passed': False, 'clients_launched': len(registry), 'error': summary.get('error')}
    publications = {}
    def capture(path, value):
        original_write(path, value)
        if Path(path).name == 'condition.json':
            assert str(path) not in publications
            publications[str(path)] = Path(path).read_bytes()
    with patch.object(d, 'write', side_effect=capture):
        summary, registry = supplied.DeadlineReplayTests().execute('valid_before_boundary')
    assert summary['passed'] and len(registry) == 4 and len(publications) == 4
    for row in summary['records']:
        data = publications[str(Path(row['output']) / 'condition.json')]
        assert hashlib.sha256(data).hexdigest() == row['publication_sha256']
        assert row['timing']['elapsed_seconds'] < 180
        receipt = d.strict_json(data.decode())
        assert receipt['timing']['ended_monotonic_seconds'] <= row['timing']['ended_monotonic_seconds']
    return {'late_stage_rejections': cases, 'positive_boundary': {
        'block_passed': summary['passed'], 'clients_launched': len(registry),
        'elapsed_seconds_each': [row['timing']['elapsed_seconds'] for row in summary['records']],
        'four_immutable_publications_hashed_and_bound': True}}

def ownership_controls():
    socket, lock = Path('/tmp/.X11-unix/X99119'), Path('/tmp/.X99119-lock')
    def run(mode):
        calls = {'poll': 0, 'start': 0, 'socket': 0, 'lock': 0, 'lock_read': 0}
        def poll():
            calls['poll'] += 1
            return 1 if mode == 'dies_during_observation' and calls['poll'] > 1 else None
        process = SimpleNamespace(pid=43210, sightbreak_start_ticks=12345, poll=poll)
        def start(_pid):
            calls['start'] += 1
            return 12346 if mode == 'start_changes_at_final_guard' and calls['start'] > 1 else 12345
        def info(path):
            key = 'socket' if path == socket else 'lock'
            calls[key] += 1
            inode = 2 if key == 'socket' else 3
            if mode == key + '_inode_changes' and calls[key] > 1:
                inode += 10
            kind = 0o140777 if key == 'socket' else 0o100600
            if mode == key + '_wrong_type':
                kind = 0o120777
            return SimpleNamespace(st_mode=kind, st_dev=1, st_ino=inode)
        def text(path, **_kwargs):
            if path == lock:
                calls['lock_read'] += 1
                return '99999' if mode == 'lock_pid_changes' and calls['lock_read'] > 1 else '43210'
            assert str(path) == '/proc/43210/net/unix'
            path_text = str(socket) + ('-alien' if mode == 'kernel_path_differs' else '')
            return 'Num RefCount Protocol Flags Type St Inode Path\n0: 2 0 00010000 0001 01 777 ' + path_text + '\n'
        with patch.object(d, 'pid_start', side_effect=start), patch.object(Path, 'lstat', info), \
                patch.object(Path, 'read_text', text), \
                patch.object(Path, 'iterdir', lambda _path: iter([Path('/proc/43210/fd/3')])), \
                patch.object(d.os, 'readlink', return_value='socket:[888]' if mode == 'held_inode_differs' else 'socket:[777]'):
            try:
                receipt = d.owned_display(process, socket, lock)
            except d.Invalid as error:
                return {'accepted': False, 'error': str(error)}
            return {'accepted': True, 'receipt': receipt}
    modes = ('valid', 'dies_during_observation', 'start_changes_at_final_guard', 'socket_inode_changes',
             'lock_inode_changes', 'lock_pid_changes', 'socket_wrong_type', 'lock_wrong_type',
             'kernel_path_differs', 'held_inode_differs')
    results = {mode: run(mode) for mode in modes}
    assert results['valid']['accepted']
    assert all(not row['accepted'] for name, row in results.items() if name != 'valid')
    for target in (socket, lock):
        with tempfile_directory() as temporary, patch.object(Path, 'exists', lambda _path: False), \
                patch.object(Path, 'is_symlink', lambda path: path == target), \
                patch.object(d.subprocess, 'Popen', side_effect=AssertionError('No launch permitted')):
            try:
                d.NativeRunner('/fake-xvfb', ':99119', temporary).start()
            except d.Invalid as error:
                results['dangling_' + ('socket' if target == socket else 'lock')] = {'accepted': False, 'error': str(error)}
            else:
                raise AssertionError('A dangling display path was accepted')
    return results

def tempfile_directory():
    import tempfile
    return tempfile.TemporaryDirectory()

result = {'frozen_commit': FROZEN, 'controller_sha256': d.digest(ROOT / 'scripts/linux_profile_overhead.py'),
          'ledger_files_verified': len(ledger['files']), 'retained_original_critic_files_verified': 4,
          'shipping_game_tree': ledger['shipping_game_tree'], 'fixture_scene_registration_shipping_canonical_unchanged': True,
          'supplied_pure_methods': 22, 'supplied_pure_exit_code': pure.returncode,
          'original_counterexample_replay_matches_retained_receipt': True,
          'original_counterexamples_reject_after_correction': replay['corrected_source']['events'],
          'real_posix_timer': real_timer_controls(), 'additional_deadlines': additional_deadline_controls(),
          'ownership_mutations': ownership_controls(),
          'engine_import_compile_uid_export_native_ocr_ci_service_runs': 0}
original_write(OUT / 'recomputed.json', result)
print(json.dumps(result, indent=2, allow_nan=False))
