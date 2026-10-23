#!/usr/bin/env python3
"""One-shot Linux acquisition. Runtime requires root's separate release.

No production/test policy changes. A passed receipt is acquisition evidence,
never independent acceptance. Complete streams and strict failures are kept.
"""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import re
import shutil
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / 'scripts'))
from native_log import failed
from run_native_regressions import PROBE

ACCEPTED = '1b7ebc71290e6c4c23017f7a2d8539d7c5eec149'
ENGINE = Path('/workspace/tools/godot-4.7.2/Godot_v4.7.2-stable_linux.x86_64')
ENGINE_SHA = '8d106cbe6144c2dc7e881d61d2429c1a8a76e6b22ef48bd5e48dcf934953f71e'
REPORT = 'docs/reports/gauntlet/m5-exhausted-primary-selection'
NEW_UID = 'game/tests/bot_exhausted_primary_test.gd.uid'
BLOCKS = {'candidate': (240, ('bot_exhausted_primary',)),
          'regressions': (480, ('bot_ai_regression', 'bot_dry_weapon', 'bot_squad_symmetry'))}
CLEANUP_SECONDS = 5
SCOPE = ('Observed stable PID identities, ancestry and anchored SID members only; '
         'polling can miss an unobserved descendant escaping/reparenting. '
         'No generic descendant/failure-path guarantee is claimed.')


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# Reuse the exact retained Linux observation helpers; never call its old runner.
_observations = load_module('retained_pid_observations', ROOT / 'docs/reports/gauntlet/m5-exhausted-primary-benchmark/actual-r2/run_once.py')
proc_snapshot = _observations.proc_snapshot
recognized = _observations.recognized
live_identity = _observations.live_identity


class BoundExceeded(RuntimeError):
    pass


class PhaseFailed(RuntimeError):
    pass


def require(value, message):
    if not value:
        raise RuntimeError(message)


def utc():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def git(source, *args):
    return subprocess.check_output(['git', *args], cwd=source, timeout=5)


def claim(source, expected_head, block, output):
    require(not output.exists(), 'Existing output is preserved; no launch')
    require(output.is_relative_to(source / '.local'), 'Output must be inside the own ignored .local')
    for path in (source / '.local', *output.parents):
        if path == source.parent:
            break
        require(not path.is_symlink(), 'Symlink output/state ancestor rejected')
    journal_dir = source / '.local/exhausted-selection-acquisition-claims'
    journal_dir.mkdir(parents=True, exist_ok=True)
    journal = journal_dir / (expected_head + '-' + block + '.json')
    with journal.open('x') as handle:
        json.dump({'claimed_utc': utc(), 'source_head': expected_head, 'block': block,
                   'output': str(output), 'one_shot': True}, handle)
    output.mkdir(parents=True)
    return journal


def original_inventory(source):
    rows = []
    for entry in git(source, 'ls-files', '--stage', '-z').split(b'\0'):
        if not entry:
            continue
        meta, name = entry.split(b'\t', 1)
        mode, blob, stage = meta.decode().split()
        rel = name.decode()
        path = source / rel
        row = dict(path=rel, mode=mode, git_blob=blob, index_stage=stage, present=path.is_file())
        if path.is_file():
            row.update(sha256=sha(path), bytes=path.stat().st_size)
        rows.append(row)
    return rows


def stage_inventory(stage, cache=True):
    return {path.relative_to(stage).as_posix(): dict(sha256=sha(path), bytes=path.stat().st_size)
            for path in sorted(stage.rglob('*')) if path.is_file()
            and (cache or '.godot' not in path.relative_to(stage).parts)}


def prepare_identity(source, expected_head):
    require(git(source, 'rev-parse', 'HEAD').decode().strip() == expected_head, 'Exact source HEAD mismatch')
    require(not git(source, 'status', '--porcelain=v1').decode(), 'Source checkout must be clean')
    require(git(source, 'diff', '--name-only', ACCEPTED, '--', 'game', 'scripts') == b'', 'Accepted game/scripts policy source changed')
    frozen = REPORT + '/SOURCE_FREEZE.json'
    original = git(source, 'show', ACCEPTED + ':' + frozen)
    require((source / frozen).read_bytes() == original, 'Accepted candidate manifest changed')
    manifest = json.loads(original)
    for name, expected in manifest['sha256'].items():
        require(sha(source / name) == expected, 'Accepted candidate source hash mismatch: ' + name)


def copy_project(source, stage, inventory):
    copied = {}
    stage.mkdir()
    for row in inventory:
        rel = row['path']
        if not rel.startswith('game/'):
            continue
        src, dst = source / rel, stage / rel
        require(row['present'] and not src.is_symlink(), 'Missing/nonregular tracked project source: ' + rel)
        data = src.read_bytes()
        blob = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
        require(blob == row['git_blob'], 'Project bytes differ from Git: ' + rel)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        require(sha(dst) == row['sha256'], 'Mechanical copy mismatch: ' + rel)
        copied[rel] = dict(row, original=str(src), staged=str(dst))
    return copied


def preparation_sources(original, current):
    for name, value in original.items():
        require(current.get(name) == value, 'Original copied source changed: ' + name)
    added = set(current) - set(original)
    require(added <= {NEW_UID}, 'Unexpected preparation source additions: ' + str(sorted(added)))
    return sorted(added)


def suite_env(output, suite):
    state = output / 'private-state' / suite
    env = dict(os.environ)
    env['SIGHTBREAK_STATE_DIR'] = str(state)
    for key, part in [('XDG_DATA_HOME', 'data'), ('XDG_CONFIG_HOME', 'config'),
                      ('XDG_CACHE_HOME', 'cache'), ('ANDROID_USER_HOME', 'android')]:
        env[key] = str(state / part)
        (state / part).mkdir(parents=True, exist_ok=True)
    return env


def producer_identity(receipt, env, project, before):
    data = Path(env['XDG_DATA_HOME']).resolve()
    expected = data / 'godot/app_userdata/SIGHTBREAK'
    require(receipt.get('os') == 'Linux' and receipt.get('uses_custom_user_dir') is False
            and receipt.get('custom_user_dir') == '', 'Unexpected native application settings')
    for field, value in [('data_dir', data), ('user_data_dir', expected), ('project_path', project)]:
        raw = receipt.get(field)
        require(isinstance(raw, str) and Path(raw).is_absolute() and Path(raw).resolve() == value.resolve(),
                'Native producer identity mismatch: ' + field)
    require(not expected.is_symlink() and all(not p.is_symlink() for p in expected.parents if p.is_relative_to(data)), 'Symlink native userdata rejected')
    if before:
        require(receipt.get('profile_exists') is False and receipt.get('diagnostics_exist') is False,
                'Existing native player state rejected')
    return str(expected)


class Budget:
    def __init__(self, seconds):
        self.seconds = seconds
        self.started = time.monotonic()
        self.deadline = self.started + seconds
        self.finalization_deadline = None

    def remaining(self):
        return self.deadline - time.monotonic()

    def arm(self):
        remaining = self.remaining()
        if remaining <= 0:
            raise BoundExceeded('Whole block wall bound exceeded')
        signal.setitimer(signal.ITIMER_REAL, remaining)

    def finish_alarm(self):
        # A single receipt-finalization allowance, never reset by nested finally.
        now = time.monotonic()
        if self.finalization_deadline is None:
            self.finalization_deadline = now + 5 if self.remaining() <= 0 else min(now+5,self.deadline)
        remaining = self.finalization_deadline-now
        if remaining <= 0:
            raise BoundExceeded('Bounded receipt finalization exhausted')
        signal.setitimer(signal.ITIMER_REAL,remaining)


@contextmanager
def registered_launch():
    previous = signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGALRM, signal.SIGINT, signal.SIGTERM})
    try:
        yield
    finally:
        signal.pthread_sigmask(signal.SIG_SETMASK, previous)


class Owned:
    def __init__(self, pid):
        self.pid = pid
        self.root = None
        self.observed = {}
        self.root_fd = os.pidfd_open(pid)

    def close(self):
        if self.root_fd is not None:
            os.close(self.root_fd)
            self.root_fd = None

    def observe(self):
        scan = proc_snapshot()
        if self.root is None and self.pid in scan:
            self.root = scan[self.pid]
        live = {row['pid'] for row in self.observed.values() if live_identity(row, scan)}
        if self.root and live_identity(self.root, scan):
            live.add(self.pid)
        # Only an already-owned live anchor can establish continued SID ownership.
        if any(scan[pid]['sid'] == self.pid for pid in live):
            live.update(pid for pid, row in scan.items() if row['sid'] == self.pid
                        and not (pid == self.pid and self.root and row['start_ticks'] != self.root['start_ticks']))
        while True:
            more = {pid for pid, row in scan.items() if row['ppid'] in live} - live
            if not more:
                break
            live.update(more)
        for pid in live:
            row = scan[pid]
            self.observed[(pid, row['start_ticks'])] = row
        return scan

    def remaining(self, scan):
        return [scan[row['pid']] for row in self.observed.values() if live_identity(row, scan)]

    def send(self, row, sig, receipt):
        fd = None
        try:
            fd = os.pidfd_open(row['pid'])
            if not live_identity(row, proc_snapshot()):
                return
            signal.pidfd_send_signal(fd, sig)
            receipt.append(dict(pid=row['pid'], start_ticks=row['start_ticks'], signal=signal.Signals(sig).name, utc=utc(), scope='verified exact identity via pidfd'))
        except ProcessLookupError:
            pass
        finally:
            if fd is not None:
                os.close(fd)

    def cleanup(self, process, receipt):
        started = time.monotonic()
        while True:
            scan = self.observe()
            process.poll()  # Reap the direct child, including a terminal zombie.
            scan = self.observe()
            remaining = self.remaining(scan)
            if process.returncode is not None and not remaining:
                break
            elapsed = time.monotonic() - started
            if elapsed >= CLEANUP_SECONDS:
                break
            sig = signal.SIGTERM if elapsed < 1 else signal.SIGKILL
            for row in remaining:
                if row['state'] != 'Z':
                    self.send(row, sig, receipt['signals'])
            time.sleep(.05)
        scan = self.observe()
        receipt.update(cleanup_seconds=time.monotonic()-started,
                       terminal_observed=self.remaining(scan),
                       terminal_same_session=[r for r in scan.values() if r['sid'] == self.pid],
                       terminal_recognized_godot=recognized(scan),
                       observed_identities=list(self.observed.values()), root_identity=self.root)

    def fallback_root(self, process, receipt, deadline):
        # If procfs registration/observation failed, the captured pidfd still
        # identifies the original Popen child. This remains a strict failure.
        if process.poll() is not None:
            return
        for sig,wait in [(signal.SIGTERM,1),(signal.SIGKILL,4)]:
            remaining = deadline-time.monotonic()
            if remaining <= 0:
                return
            if self.root_fd is not None:
                signal.pidfd_send_signal(self.root_fd,sig)
                scope = 'original child pidfd; procfs observation failed'
            else:
                process.send_signal(sig)
                scope = 'Popen-owned unreaped direct child; pidfd creation failed'
            receipt['signals'].append(dict(pid=process.pid,signal=signal.Signals(sig).name,utc=utc(),scope=scope))
            try:
                process.wait(timeout=min(wait,remaining))
                return
            except subprocess.TimeoutExpired:
                pass


class Runner:
    def __init__(self, output, budget):
        self.output, self.budget = output, budget
        self.receipts = []

    def native(self, label, command, env, cap):
        self.budget.arm()
        started = time.monotonic()
        deadline = min(started + cap, self.budget.deadline)
        receipt = dict(label=label, command=command, cwd=str(self.output), start_utc=utc(),
                       start_monotonic=started, phase_cap_seconds=cap, timeout_seconds=deadline-started,
                       timed_out=False, exit_code=None, signals=[], failure=None, cleanup_failures=[],
                       private_environment={k:env[k] for k in ['SIGHTBREAK_STATE_DIR','XDG_DATA_HOME','XDG_CONFIG_HOME','XDG_CACHE_HOME','ANDROID_USER_HOME']})
        self.receipts.append(receipt)
        process = owned = None
        original_error = None
        try:
            with (self.output/(label+'.stdout.log')).open('wb') as stdout, (self.output/(label+'.stderr.log')).open('wb') as stderr:
                # Pending termination cannot interrupt between spawn and registration.
                with registered_launch():
                    process = subprocess.Popen(command, cwd=self.output, env=env, stdout=stdout, stderr=stderr, start_new_session=True)
                    owned = Owned(process.pid)
                    receipt['pid'] = process.pid
                    owned.observe()
                require(owned.root is not None and owned.root['pgid'] == owned.root['sid'] == process.pid,
                        'Native PID/start/session registration failed')
                while True:
                    owned.observe()
                    if process.poll() is not None:
                        break
                    if time.monotonic() >= deadline:
                        receipt['timed_out'] = True
                        raise BoundExceeded(label + ' phase wall bound exceeded')
                    time.sleep(.05)
                receipt['unexpected_members_after_root_exit'] = owned.remaining(owned.observe())
        except BaseException as error:
            original_error = error
            receipt['failure'] = dict(type=type(error).__name__, message=str(error))
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
            cleanup_deadline = time.monotonic()+CLEANUP_SECONDS
            if process is not None:
                try:
                    if owned is None:
                        owned = Owned(process.pid)
                    owned.cleanup(process, receipt)
                except BaseException as error:
                    receipt['cleanup_failures'].append(dict(type=type(error).__name__, message=str(error)))
                    try:
                        if owned is not None:
                            owned.fallback_root(process,receipt,cleanup_deadline)
                        else:
                            # Construction failed before a pidfd could be retained.
                            fallback = Owned.__new__(Owned)
                            fallback.root_fd = None
                            fallback.fallback_root(process,receipt,cleanup_deadline)
                    except BaseException as fallback_error:
                        receipt['cleanup_failures'].append(dict(type=type(fallback_error).__name__,message=str(fallback_error)))
                finally:
                    if owned is not None:
                        try:
                            owned.close()
                        except BaseException as error:
                            receipt['cleanup_failures'].append(dict(type=type(error).__name__,message=str(error)))
                receipt['exit_code'] = process.poll()
            if self.budget.remaining() > 0:
                self.budget.arm()
            else:
                self.budget.finish_alarm()
            receipt['wall_seconds'] = time.monotonic()-started
            receipt['end_utc'] = utc()
            streams = []
            for stream in ['stdout','stderr']:
                path = self.output/(label+'.'+stream+'.log')
                data = path.read_bytes() if path.exists() else b''
                receipt[stream] = dict(path=str(path), bytes=len(data), sha256=hashlib.sha256(data).hexdigest(), present=path.exists())
                streams.append(data)
            complete = b'\n'.join(streams)
            (self.output/(label+'.classification.log')).write_bytes(complete)
            receipt['strict_log_failed'] = failed(complete.decode(errors='replace'))
            receipt['complete_log_scope'] = 'Original stdout + newline + original stderr, no cross-stream chronology claimed'
            receipt['passed'] = (receipt['failure'] is None and not receipt['cleanup_failures']
                and receipt['exit_code'] == 0 and not receipt['timed_out'] and not receipt['strict_log_failed']
                and not receipt['signals'] and not receipt.get('unexpected_members_after_root_exit')
                and not receipt.get('terminal_observed') and not receipt.get('terminal_same_session')
                and not receipt.get('terminal_recognized_godot') and receipt['wall_seconds'] <= cap
                and self.budget.remaining() >= 0 and owned is not None and owned.root is not None)
            if not receipt['passed'] and receipt['failure'] is None:
                receipt['failure'] = dict(type='PhaseFailed',message=label+' failed; complete streams/strict failure retained')
            write(self.output/(label+'.receipt.json'), receipt)
        if original_error:
            raise original_error
        if not receipt['passed']:
            raise PhaseFailed(label + ' failed; complete streams/strict failure retained')
        self.budget.arm()
        return receipt


def completed_suite(suite, text):
    if suite == 'bot_ai_regression':
        require(text.splitlines().count('BOT_AI_REGRESSION_TESTS_OK') == 1, 'Missing/duplicate existing AI success marker')
    elif suite == 'bot_dry_weapon':
        rows = [json.loads(line.split(' ',1)[1]) for line in text.splitlines() if line.startswith('BOT_DRY_WEAPON_RESULT ')]
        require(rows == [dict(cases=84,sequence_steps=48,checks=590,failures=0,passed=True)], 'Existing dry-weapon result incomplete/failed')
    elif suite == 'bot_squad_symmetry':
        require(text.splitlines().count('BOT_SQUAD_SYMMETRY_RESULT samples=960 checks=2722 failures=0 mode=assertion') == 1,
                'Existing squad-symmetry result incomplete/failed')


def candidate_audit(source, output):
    oracle = load_module('candidate_raw_audit',source/REPORT/'audit_candidate.py')
    stdout = output/'bot_exhausted_primary.stdout.log'
    baseline_path = source/'docs/reports/gauntlet/m5-exhausted-primary-benchmark/actual-r2/baseline-probe.stdout.log.gz'
    require(hashlib.sha256(oracle.file_data(baseline_path)).hexdigest() == oracle.BASELINE_STDOUT_SHA256,
            'Immutable actual baseline stdout hash mismatch')
    records,_ = oracle.parse(stdout)
    baseline,_ = oracle.parse(baseline_path)
    value = dict(authority=oracle.audit(records,source),comparison=oracle.compare(records,baseline),stdout_sha256=sha(stdout))
    write(output/'candidate-builder-audit.json',value)
    return dict(passed=True,scope='Builder recomputation only; fresh independent actual-output review required')


def run(args):
    seconds, suites = BLOCKS[args.block]
    budget = Budget(seconds)
    source, output = args.source.resolve(), args.output.resolve()
    require(platform.system() == 'Linux' and Path('/proc').is_dir(), 'This wrapper is local Linux only')
    require(source == ROOT and re.fullmatch('[0-9a-f]{40}', args.expected_head), 'Use this exact own checkout and full reviewed source HEAD')
    require(hasattr(os,'pidfd_open') and hasattr(signal,'pidfd_send_signal'), 'Linux pidfd signal support is required')
    old_handlers = {s:signal.getsignal(s) for s in [signal.SIGALRM,signal.SIGINT,signal.SIGTERM]}
    def interrupted(signum, _frame):
        raise BoundExceeded('Whole block deadline' if signum == signal.SIGALRM else 'Interrupted by '+signal.Signals(signum).name)
    for sig in old_handlers:
        signal.signal(sig,interrupted)
    try:
        budget.arm()
        journal = claim(source,args.expected_head,args.block,output)
    except BaseException:
        signal.setitimer(signal.ITIMER_REAL,0)
        for sig,handler in old_handlers.items():
            signal.signal(sig,handler)
        raise
    report = dict(block=args.block, expected_source_head=args.expected_head, accepted_candidate=ACCEPTED,
                  start_utc=utc(), whole_bound_seconds=seconds, passed=False, failure=None,
                  finalization_failures=[], journal=str(journal), output=str(output), cleanup_scope=SCOPE)
    original = copied = prepared = None
    stage = output/'staged'
    runner = Runner(output,budget)
    candidate_attempted = False
    try:
        budget.arm()
        prepare_identity(source,args.expected_head)
        report['engine_sha256_before'] = sha(ENGINE)
        require(report['engine_sha256_before'] == ENGINE_SHA, 'Pinned engine hash mismatch')
        report['recognized_godot_before'] = recognized(proc_snapshot())
        require(not report['recognized_godot_before'], 'Another recognized Godot process holds the native lane')
        original = original_inventory(source)
        write(output/'original-tracked-before.json',original)
        copied = copy_project(source,stage,original)
        write(output/'project-source-copy-map.json',copied)
        initial = stage_inventory(stage,cache=False)
        write(output/'staged-before-preparation.json',stage_inventory(stage))
        driver = output/'producer.gd'
        driver.write_text(PROBE)
        report['native_producer_source_sha256'] = sha(driver)
        project = stage/'game'
        def prefix():
            return [str(ENGINE),'--headless','--audio-driver','Dummy','--path',str(project)]
        def producer(suite,when,env):
            destination = output/(suite+'-'+when+'.json')
            runner.native(suite+'-producer-'+when,prefix()+['--script',str(driver),'--','--receipt='+str(destination)],env,30)
            value = json.loads(destination.read_text())
            path = producer_identity(value,env,project,when=='before')
            return dict(receipt=value,path=path)
        def stable():
            prepare_identity(source,args.expected_head)
            require(original_inventory(source) == original, 'Original tracked source inventory changed')
            current = stage_inventory(stage,cache=False)
            if prepared is not None:
                require(current == prepared, 'Prepared staged source/UID set changed')
            else:
                preparation_sources(initial,current)
        first_env = suite_env(output,suites[0])
        before = producer(suites[0],'before',first_env)
        stable()
        before_import = stage_inventory(stage)
        write(output/'staged-before-import.json',before_import)
        runner.native('preparation-import',prefix()+['--editor','--import'],first_env,120)
        current = stage_inventory(stage,cache=False)
        added = preparation_sources(initial,current)
        prepared = current
        report['preparation'] = dict(original_tracked_bytes_unchanged=True,
            staged_noncache_source_set_equal_to_original=current==initial, added_source_files=added,
            added_uid_first_observed=('after first native producer/before editor import' if NEW_UID in before_import
                                      else 'after editor import') if NEW_UID in added else None)
        if NEW_UID in added:
            uid = stage/NEW_UID
            require(re.fullmatch(r'uid://[a-z0-9]+\n?',uid.read_text()) is not None, 'Malformed generated test UID')
            require(not any(path != uid and path.read_bytes()==uid.read_bytes() for path in project.rglob('*.uid')), 'Generated test UID collides with another UID')
            retained = output/'preparation-generated-uids'/NEW_UID
            retained.parent.mkdir(parents=True)
            shutil.copy2(uid,retained)
            report['preparation']['retained_uid_sha256'] = sha(uid)
        write(output/'staged-after-import.json',stage_inventory(stage))
        stable()
        report['suites'] = []
        for index,suite in enumerate(suites):
            env = first_env if index==0 else suite_env(output,suite)
            if index:
                before = producer(suite,'before',env)
                stable()
            candidate_attempted = suite == 'bot_exhausted_primary'
            suite_result = dict(suite=suite,before=before,passed=False)
            report['suites'].append(suite_result)
            runner.native(suite,prefix()+['--script','res://tests/'+suite+'_test.gd'],env,120)
            stable()
            text = (output/(suite+'.stdout.log')).read_text()
            if suite == 'bot_exhausted_primary':
                try:
                    report['candidate_builder_audit'] = candidate_audit(source,output)
                except BaseException as error:
                    report['candidate_builder_audit'] = dict(passed=False,type=type(error).__name__,message=str(error))
                    raise
            else:
                completed_suite(suite,text)
            after = producer(suite,'after',env)
            require(after['path'] == before['path'], 'Before/after native producer paths differ')
            suite_result.update(after=after,passed=True)
            state = Path(after['path'])
            write(output/(suite+'-userdata-inventory.json'),stage_inventory(state) if state.exists() else {})
            stable()
        require(budget.remaining() >= 0, 'Whole bound exceeded after suites')
        report['passed'] = True
    except BaseException as error:
        current = dict(type=type(error).__name__,message=str(error))
        primary = runner.receipts[-1].get('failure') if runner.receipts else None
        report['failure'] = primary or current
        if primary and primary != current:
            report['finalization_failures'].append(dict(current,stage='native receipt finalization; original phase failure preserved'))
    finally:
        # No further native command is launched, including after a strict leak.
        signal.setitimer(signal.ITIMER_REAL,0)
        try:
            budget.finish_alarm()
            if args.block=='candidate' and candidate_attempted and 'candidate_builder_audit' not in report and budget.remaining()>0:
                try:
                    report['candidate_builder_audit'] = candidate_audit(source,output)
                except BaseException as error:
                    report['candidate_builder_audit'] = dict(passed=False,type=type(error).__name__,message=str(error))
                    report['passed'] = False
            elif args.block=='candidate' and 'candidate_builder_audit' not in report:
                report['candidate_builder_audit'] = dict(passed=False,reason='Candidate not attempted or whole budget exhausted')
                report['passed'] = False
            if original is not None:
                after = original_inventory(source)
                write(output/'original-tracked-after.json',after)
                require(after==original,'Original tracked source changed during acquisition')
                prepare_identity(source,args.expected_head)
                report['original_tracked_inventory_unchanged'] = True
            if stage.exists():
                current = stage_inventory(stage,cache=False)
                write(output/'staged-after-attempt.json',stage_inventory(stage))
                if prepared is not None:
                    require(current==prepared,'Prepared non-cache source/UID set changed')
                elif copied is not None:
                    preparation_sources(initial,current)
            state = output/'private-state'
            if state.exists():
                write(output/'private-state-after-attempt.json',stage_inventory(state))
            report['engine_sha256_after'] = sha(ENGINE)
            require(report['engine_sha256_after']==ENGINE_SHA,'Pinned engine changed')
            report['recognized_godot_after'] = recognized(proc_snapshot())
            require(not report['recognized_godot_after'],'Recognized Godot process remains')
        except BaseException as error:
            report['passed'] = False
            report['finalization_failures'].append(dict(type=type(error).__name__,message=str(error)))
        finally:
            signal.setitimer(signal.ITIMER_REAL,0)
            report['wall_seconds'] = time.monotonic()-budget.started
            if report['wall_seconds'] > seconds:
                report['passed'] = False
                report['finalization_failures'].append(dict(type='BoundExceeded',message='Whole normal acquisition bound exceeded; only bounded cleanup/finalization was allowed'))
            report.update(end_utc=utc(),processes=runner.receipts)
            try:
                write(output/'overall.receipt.json',report)
                write(journal,dict(source_head=args.expected_head,block=args.block,output=str(output),finished_utc=utc(),passed=report['passed']))
            finally:
                for sig,handler in old_handlers.items():
                    signal.signal(sig,handler)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--expected-head',required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--block',choices=BLOCKS,required=True)
    args = parser.parse_args()
    report = run(args)
    print(json.dumps({'passed':report['passed'],'block':args.block,'receipt':str(args.output/'overall.receipt.json'),'scope':'Acquisition only; independent actual-output review remains required'}))
    return 0 if report['passed'] else 1


if __name__=='__main__':
    raise SystemExit(main())
