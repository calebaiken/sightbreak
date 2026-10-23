#!/usr/bin/env python3
"""One staged import, then at most one frozen baseline, with retained receipts."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import time
from datetime import datetime, timezone

SOURCE = Path('/workspace/sightbreak-exhausted-primary-benchmark')
OUT = Path(__file__).resolve().parent
STAGE = OUT / 'staged-project'
STATE = OUT / 'private-state'
ENGINE = Path('/workspace/tools/godot-4.7.2/Godot_v4.7.2-stable_linux.x86_64')
FREEZE = 'b87afb717bf09a78c6d36b164d48906902734bdb'
ENGINE_HASH = '8d106cbe6144c2dc7e881d61d2429c1a8a76e6b22ef48bd5e48dcf934953f71e'
FIXTURE_HASH = '540d24dda8e58f4685030e81b55ac3778ccbf31a89f76f9873ac598c32770731'


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(name, data):
    (OUT / name).write_text(json.dumps(data, indent=2, sort_keys=True) + '\n')


def git(*args):
    return subprocess.check_output(['git', *args], cwd=SOURCE)


def original_files():
    result = []
    for line in git('ls-files', '--stage', '-z').split(b'\0'):
        if not line:
            continue
        meta, raw_path = line.split(b'\t', 1)
        mode, blob, stage = meta.decode().split()
        rel = raw_path.decode()
        path = SOURCE / rel
        entry = {'path': rel, 'mode': mode, 'git_blob': blob, 'index_stage': stage,
                 'present': path.is_file()}
        if path.is_file():
            entry.update(sha256=sha(path), bytes=path.stat().st_size)
        result.append(entry)
    return result


def stage_files():
    return [{'path': p.relative_to(STAGE).as_posix(), 'sha256': sha(p), 'bytes': p.stat().st_size}
            for p in sorted(STAGE.rglob('*')) if p.is_file()]


def proc_snapshot():
    result = {}
    for proc in Path('/proc').iterdir():
        if not proc.name.isdigit():
            continue
        try:
            stat = (proc / 'stat').read_text()
            end = stat.rfind(')')
            fields = stat[end + 2:].split()
            pid = int(proc.name)
            try:
                exe = os.readlink(proc / 'exe')
            except OSError:
                exe = ''
            result[pid] = {'pid': pid, 'comm': stat[stat.index('(') + 1:end],
                           'state': fields[0], 'ppid': int(fields[1]),
                           'pgid': int(fields[2]), 'sid': int(fields[3]),
                           'start_ticks': int(fields[19]), 'exe': exe}
        except (OSError, ValueError, IndexError):
            pass
    return result


def recognized(scan):
    return [v for v in scan.values() if 'godot' in v['comm'].lower() or
            'godot' in Path(v['exe']).name.lower()]


def live_identity(record, scan):
    return record['pid'] in scan and scan[record['pid']]['start_ticks'] == record['start_ticks']


def run_phase(name, command, outer_deadline, env):
    started = time.monotonic()
    receipt = {'name': name, 'command': command, 'cwd': str(STAGE),
               'start_utc': now(), 'phase_wall_cap_seconds': 120,
               'private_environment': {k: env[k] for k in ('SIGHTBREAK_STATE_DIR', 'XDG_DATA_HOME',
                   'XDG_CONFIG_HOME', 'XDG_CACHE_HOME', 'ANDROID_USER_HOME')},
               'stdout': name + '.stdout.log', 'stderr': name + '.stderr.log',
               'identity_observations': [], 'signals': [], 'timed_out': False}
    with (OUT / receipt['stdout']).open('wb') as stdout, (OUT / receipt['stderr']).open('wb') as stderr:
        process = subprocess.Popen(command, cwd=STAGE, env=env, stdout=stdout,
                                   stderr=stderr, start_new_session=True)
        receipt['pid'] = process.pid
        session_id = process.pid
        observed = {}
        own_record = None
        deadline = min(started + 120, outer_deadline)

        def observe():
            nonlocal own_record
            scan = proc_snapshot()
            seeds = {record['pid'] for record in observed.values() if live_identity(record, scan)}
            if process.pid in scan:
                current = scan[process.pid]
                if own_record is None:
                    own_record = current
                if live_identity(own_record, scan):
                    seeds.add(process.pid)
            seeds.update(p for p, v in scan.items() if v['sid'] == session_id)
            changed = True
            while changed:
                added = {p for p, v in scan.items() if v['ppid'] in seeds and p not in seeds}
                changed = bool(added)
                seeds.update(added)
            for pid in seeds:
                if pid in scan:
                    record = scan[pid]
                    key = (pid, record['start_ticks'])
                    if key not in observed:
                        observed[key] = record
            return scan

        # Track known identities plus currently discoverable children/session members.
        # An unobserved descendant that escapes/reparents between polls can evade this scope.
        while True:
            scan = observe()
            code = process.poll()
            if code is not None:
                break
            if time.monotonic() >= deadline:
                receipt['timed_out'] = True
                break
            time.sleep(.05)

        if receipt['timed_out']:
            # The root is still the session/group leader here; validate its identity first.
            scan = observe()
            if own_record is not None and live_identity(own_record, scan):
                try:
                    os.killpg(session_id, signal.SIGTERM)
                    receipt['signals'].append({'scope': 'original process group', 'pgid': session_id,
                                               'signal': 'SIGTERM', 'at_utc': now()})
                except ProcessLookupError:
                    pass

        cleanup_start = time.monotonic()
        cleanup_deadline = cleanup_start + 5
        while True:
            scan = observe()
            # Use identity and current session, never a broad name-based kill.
            remaining = [r for r in scan.values() if r['sid'] == session_id]
            remaining += [scan[r['pid']] for r in observed.values() if live_identity(r, scan) and
                          scan[r['pid']]['sid'] != session_id]
            if process.poll() is not None and not remaining:
                break
            elapsed = time.monotonic() - cleanup_start
            if elapsed >= 1:
                for record in remaining:
                    if record['state'] == 'Z':
                        continue
                    try:
                        os.kill(record['pid'], signal.SIGKILL)
                        receipt['signals'].append({'scope': 'observed exact identity',
                            'pid': record['pid'], 'start_ticks': record['start_ticks'],
                            'signal': 'SIGKILL', 'at_utc': now()})
                    except ProcessLookupError:
                        pass
            if time.monotonic() >= cleanup_deadline:
                break
            time.sleep(.05)
        receipt['cleanup_wall_seconds'] = time.monotonic() - cleanup_start
        receipt['exit_code'] = process.poll()
        receipt['identity_observations'] = sorted(observed.values(), key=lambda x: (x['pid'], x['start_ticks']))
        receipt['root_identity'] = own_record
        terminal_scan = observe()
        receipt['terminal_same_session'] = [v for v in terminal_scan.values() if v['sid'] == session_id]
        receipt['terminal_observed_live'] = [v for v in observed.values() if live_identity(v, terminal_scan)]
        receipt['terminal_recognized_godot'] = recognized(terminal_scan)
    receipt['end_utc'] = now()
    receipt['wall_seconds'] = time.monotonic() - started
    for stream in ('stdout', 'stderr'):
        p = OUT / receipt[stream]
        receipt[stream + '_sha256'] = sha(p)
        receipt[stream + '_bytes'] = p.stat().st_size
    text = (OUT / receipt['stdout']).read_text(errors='replace') + (OUT / receipt['stderr']).read_text(errors='replace')
    receipt['error_lines'] = [line for line in text.splitlines() if re.search(r'SCRIPT ERROR|Parse Error|(^|\s)ERROR:', line)]
    write(name + '.receipt.json', receipt)
    print(json.dumps({'phase': name, 'exit_code': receipt['exit_code'], 'timed_out': receipt['timed_out'],
                      'wall_seconds': receipt['wall_seconds'], 'stdout_bytes': receipt['stdout_bytes'],
                      'stderr_bytes': receipt['stderr_bytes'], 'error_lines': receipt['error_lines'][:5]}), flush=True)
    return receipt


def main():
    if STAGE.exists() or (OUT / 'overall.receipt.json').exists():
        raise RuntimeError('Fresh-attempt guard: staged project or receipt already exists; do not rerun')
    start = time.monotonic()
    overall = {'start_utc': now(), 'source_root': str(SOURCE), 'source_freeze': FREEZE,
               'critic_source_acceptance': '5fbf3ac6d81a224635f51af0c2eabad06cfdb12f',
               'engine': str(ENGINE), 'engine_sha256': sha(ENGINE), 'staged_project': str(STAGE),
               'private_state': str(STATE), 'whole_wrapper_cap_seconds': 240,
               'cleanup_cap_seconds_per_phase': 5,
               'cleanup_scope_limit': 'Observed stable PID identities, original process group and SID. '
                   'Polling can miss an unobserved descendant escaping/reparenting between scans; '
                   'no generic descendant/failure-path guarantee is claimed.'}
    assert overall['engine_sha256'] == ENGINE_HASH, 'pinned binary mismatch'
    overall['source_head_before'] = git('rev-parse', 'HEAD').decode().strip()
    overall['source_status_before'] = git('status', '--porcelain=v1').decode()
    assert overall['source_head_before'] == FREEZE and not overall['source_status_before'], 'source not frozen/clean'
    assert sha(SOURCE / 'game/tests/bot_exhausted_primary_probe.gd') == FIXTURE_HASH, 'fixture mismatch'
    overall['recognized_godot_before'] = recognized(proc_snapshot())
    assert not overall['recognized_godot_before'], 'another recognized native engine is running'
    original = original_files()
    write('original-tracked-before.json', original)
    STAGE.mkdir()
    copied = []
    for entry in original:
        if not entry['path'].startswith('game/'):
            continue
        assert entry['present'], 'tracked project source missing from sparse checkout'
        src, dst = SOURCE / entry['path'], STAGE / entry['path']
        assert git('hash-object', '--', entry['path']).decode().strip() == entry['git_blob'], 'original differs from Git object'
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        assert sha(dst) == entry['sha256'], 'mechanical copy differs'
        copied.append(dict(entry, original=str(src), staged=str(dst)))
    write('project-source-copy-map.json', copied)
    stage_before = stage_files()
    write('staged-before-import.json', stage_before)
    env = dict(os.environ)
    env['SIGHTBREAK_STATE_DIR'] = str(STATE)
    for key, part in (('XDG_DATA_HOME', 'data'), ('XDG_CONFIG_HOME', 'config'),
                      ('XDG_CACHE_HOME', 'cache'), ('ANDROID_USER_HOME', 'android')):
        env[key] = str(STATE / part)
        (STATE / part).mkdir(parents=True, exist_ok=True)
    outer_deadline = start + 240
    overall['preparation'] = run_phase('preparation-import', [str(ENGINE), '--headless', '--editor',
        '--path', str(STAGE / 'game'), '--import'], outer_deadline, env)
    after_import = stage_files()
    write('staged-after-import.json', after_import)
    import_map = {r['path']: r for r in after_import}
    overall['tracked_project_changes_after_import'] = [r['path'] for r in stage_before if import_map.get(r['path']) != r]
    initial_paths = {r['path'] for r in stage_before}
    added = [r for r in after_import if r['path'] not in initial_paths]
    write('preparation-added-files.json', added)
    uid_dir = OUT / 'preparation-generated-uids'
    for entry in added:
        if entry['path'].endswith('.uid'):
            dst = uid_dir / entry['path']
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(STAGE / entry['path'], dst)
    prep = overall['preparation']
    import_ok = (prep['exit_code'] == 0 and not prep['timed_out'] and not prep['error_lines'] and
                 not prep['terminal_same_session'] and not prep['terminal_observed_live'] and
                 not prep['terminal_recognized_godot'] and not overall['tracked_project_changes_after_import'])
    overall['import_qualified_to_attempt_baseline'] = import_ok
    if import_ok and time.monotonic() < outer_deadline:
        overall['baseline'] = run_phase('baseline-probe', [str(ENGINE), '--headless',
            '--path', str(STAGE / 'game'), '--script', 'res://tests/bot_exhausted_primary_probe.gd'],
            outer_deadline, env)
    else:
        overall['baseline'] = None
        overall['baseline_skipped_reason'] = 'Preparation failed qualification or whole-wrapper deadline expired'
    after = stage_files()
    write('staged-after-attempt.json', after)
    final_map = {r['path']: r for r in after}
    overall['tracked_project_changes_after_attempt'] = [r['path'] for r in stage_before if final_map.get(r['path']) != r]
    original_after = original_files()
    write('original-tracked-after.json', original_after)
    overall['original_tracked_manifest_unchanged'] = original == original_after
    overall['source_head_after'] = git('rev-parse', 'HEAD').decode().strip()
    overall['source_status_after'] = git('status', '--porcelain=v1').decode()
    overall['engine_sha256_after'] = sha(ENGINE)
    overall['recognized_godot_after'] = recognized(proc_snapshot())
    overall['end_utc'] = now()
    overall['whole_wrapper_wall_seconds'] = time.monotonic() - start
    overall['controller_sha256'] = sha(Path(__file__))
    write('overall.receipt.json', overall)
    print(json.dumps({'overall_receipt': str(OUT / 'overall.receipt.json'),
                      'original_tracked_manifest_unchanged': overall['original_tracked_manifest_unchanged'],
                      'tracked_project_changes_after_attempt': overall['tracked_project_changes_after_attempt'],
                      'whole_wrapper_wall_seconds': overall['whole_wrapper_wall_seconds']}), flush=True)


if __name__ == '__main__':
    main()
