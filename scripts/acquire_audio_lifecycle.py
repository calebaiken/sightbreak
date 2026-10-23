#!/usr/bin/env python3
"""One Linux-only isolated audio ownership diagnostic; never closes a leak gate."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import signal
import subprocess
import time
import uuid

from analyze_audio_lifecycle import analyze
from native_log import failed
import toolchain

WHOLE, CLEANUP, FINAL_RESERVE = 240, 5, 8
SUITE = ['--headless', '--verbose', '--script', 'res://tests/input_mode_test.gd', '--', '--audio-lifecycle-diagnostic']
PROBE = '''extends SceneTree
func _initialize() -> void:
    var destination := ""
    for argument in OS.get_cmdline_user_args():
        if argument.begins_with("--receipt="): destination = argument.trim_prefix("--receipt=")
    var data := {"project_path":ProjectSettings.globalize_path("res://"), "data_dir":OS.get_data_dir(),
        "user_data_dir":OS.get_user_data_dir(), "driver":AudioServer.get_driver_name(),
        "uses_custom_user_dir":ProjectSettings.get_setting("application/config/use_custom_user_dir"),
        "custom_user_dir":ProjectSettings.get_setting("application/config/custom_user_dir_name"),
        "profile_exists":FileAccess.file_exists("user://offline_training.json"),
        "diagnostics_exist":DirAccess.dir_exists_absolute(ProjectSettings.globalize_path("user://offline-diagnostics-unit"))}
    var file := FileAccess.open(destination, FileAccess.WRITE)
    if file == null:
        push_error("Cannot write owned native identity receipt")
        quit(2)
        return
    file.store_string(JSON.stringify(data))
    file.close()
    quit(0)
'''


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write(path, data):
    Path(path).write_text(json.dumps(data, indent=2, sort_keys=True) + '\n')


def remaining(deadline, reserve=0):
    value = deadline - time.monotonic() - reserve
    if value <= 0:
        raise TimeoutError('Whole acquisition deadline has no reserved time remaining')
    return value


def git(source, deadline, *arguments):
    return subprocess.check_output(['git', *arguments], cwd=source, timeout=remaining(deadline), text=True)


def tracked(source, freeze, deadline):
    if git(source, deadline, 'rev-parse', 'HEAD').strip() != freeze:
        raise RuntimeError('Source HEAD differs from the exact reviewed freeze')
    if git(source, deadline, 'status', '--porcelain=v1', '--untracked-files=all').strip():
        raise RuntimeError('Source is not clean')
    if git(source, deadline, 'rev-parse', '--show-object-format').strip() != 'sha1':
        raise RuntimeError('Unsupported Git object format')
    result = {}
    for entry in git(source, deadline, 'ls-tree', '-r', '-z', freeze, '--', 'game', 'scripts').split('\0'):
        if not entry: continue
        metadata, name = entry.split('\t', 1)
        mode, kind, blob = metadata.split()
        path = source / name
        remaining(deadline)
        if mode not in ('100644', '100755') or kind != 'blob' or path.is_symlink() or not path.is_file():
            raise RuntimeError('Missing, linked or unsupported tracked source: ' + name)
        raw = path.read_bytes()
        if hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest() != blob:
            raise RuntimeError('Source bytes differ from Git object: ' + name)
        result[name] = {'git_blob': blob, 'mode': mode, 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}
    if 'game/tests/audio_lifecycle_probe.gd' not in result or 'game/project.godot' not in result:
        raise RuntimeError('Reviewed observer/project source is absent')
    return result


def inventory(directory, deadline):
    result = {}
    for path in sorted(directory.rglob('*')):
        remaining(deadline)
        if path.is_symlink(): raise RuntimeError('Linked file in owned output tree')
        if path.is_file(): result[path.relative_to(directory).as_posix()] = sha(path)
    return result


def imported(before, after, project):
    if any(after.get(path) != digest for path, digest in before.items()):
        raise RuntimeError('Import changed copied tracked project bytes')
    additions = {path: digest for path, digest in after.items() if path not in before}
    for path in additions:
        if path.startswith('.godot/'): continue
        if (not path.endswith('.gd.uid') or path[:-4] not in before
                or not re.fullmatch(r'uid://[a-z0-9]+\n?', (project / path).read_text())):
            raise RuntimeError('Import added an undeclared non-cache resource: ' + path)
    return additions


def copy_owned_tree(source, destination, deadline):
    destination.mkdir()
    for path in sorted(source.rglob('*')):
        remaining(deadline)
        if path.is_symlink(): raise RuntimeError('Linked private state is not archived')
        target = destination / path.relative_to(source)
        if path.is_dir(): target.mkdir(exist_ok=True)
        elif path.is_file(): target.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(path, target)


def proc_table():
    result = {}
    for path in Path('/proc').iterdir():
        if not path.name.isdigit(): continue
        try:
            raw = (path / 'stat').read_text(); end = raw.rfind(')'); fields = raw[end + 2:].split()
            try: executable = os.readlink(path / 'exe')
            except OSError: executable = ''
            result[int(path.name)] = {'pid': int(path.name), 'state': fields[0], 'ppid': int(fields[1]),
                'pgid': int(fields[2]), 'sid': int(fields[3]), 'start_ticks': int(fields[19]),
                'comm': raw[raw.index('(') + 1:end], 'exe': executable}
        except (OSError, ValueError, IndexError): pass
    return result


def recognized(table):
    return [row for row in table.values() if 'godot' in row['comm'].lower() or 'godot' in Path(row['exe']).name.lower()]


def live(record, table):
    return record['pid'] in table and table[record['pid']]['start_ticks'] == record['start_ticks']


def signal_identity(record, signum):
    # Re-read immediately before signaling; a reused PID is never a target.
    if live(record, proc_table()):
        try: os.kill(record['pid'], signum); return True
        except ProcessLookupError: pass
    return False


def phase_snapshots(output, receipts, deadline, errors, completed):
    """Hash, scan and analyze one retained byte snapshot, preserving old receipts."""
    directory = output / 'final-phase-logs'; directory.mkdir()
    snapshots, analysis = [], None
    for phase in receipts:
        remaining(deadline)
        label = phase['label']
        try:
            if not re.fullmatch('[a-z][a-z-]*', label) or phase.get('log') != label + '.log':
                raise RuntimeError('Phase log identity differs from its declared label')
            raw = (output / phase['log']).read_bytes()
            saved = directory / phase['log']; saved.write_bytes(raw)
            if saved.read_bytes() != raw: raise RuntimeError('Retained raw snapshot bytes differ')
            digest = hashlib.sha256(raw).hexdigest(); clean = not failed(raw.decode('utf-8', errors='replace'))
            receipt_bytes = (output / (label + '.receipt.json')).read_bytes()
            receipt_matches = json.loads(receipt_bytes) == phase
            row = {'label': label, 'original_log': phase['log'], 'retained_log': str(saved.relative_to(output)),
                   'sha256': digest, 'bytes': len(raw), 'clean_log': clean,
                   'phase_receipt_sha256': hashlib.sha256(receipt_bytes).hexdigest(),
                   'receipt_matches': receipt_matches,
                   'matches_phase_snapshot': (phase.get('log_sha256') == digest and phase.get('log_bytes') == len(raw)
                                              and phase.get('clean_log') is clean)}
            snapshots.append(row)
            if not receipt_matches or not row['matches_phase_snapshot']:
                errors.append({'stage': 'phase_finalization', 'phase': label, 'error': 'Retained phase log or receipt drifted'})
            if label == 'input-mode':
                try:
                    analysis = analyze(raw.decode('utf-8', errors='replace'))
                    analysis.update(raw_log_sha256=digest, raw_log_bytes=len(raw))
                    write(output / 'analysis.json', analysis)
                    if analysis['strict_raw_log_failed'] is clean:
                        raise RuntimeError('Analyzer and strict scanner disagree on retained bytes')
                    if analysis['driver'] != 'Dummy' or not analysis['fixture_owner_coverage_complete']:
                        raise RuntimeError('Actual default driver or fixture owner coverage is incomplete')
                except BaseException as error:
                    if completed: errors.append({'stage': 'final_analysis', 'error': str(error)})
        except BaseException as error:
            errors.append({'stage': 'phase_finalization', 'phase': label, 'error': str(error)})
    write(output / 'final-phase-snapshots.json', snapshots)
    return snapshots, analysis


def seal_phase_snapshots(output, snapshots, analysis, deadline):
    checks, errors = [], []
    for row in snapshots:
        remaining(deadline)
        check = {'label': row['label']}
        try:
            for name in ('original_log', 'retained_log'):
                raw = (output / row[name]).read_bytes()
                current = {'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw),
                           'clean_log': not failed(raw.decode('utf-8', errors='replace'))}
                check[name] = current
                if any(current[key] != row[key] for key in current):
                    errors.append('Phase raw bytes changed during finalization: ' + row['label'] + ' ' + name)
            check['receipt_sha256'] = sha(output / (row['label'] + '.receipt.json'))
            if check['receipt_sha256'] != row['phase_receipt_sha256']:
                errors.append('Phase receipt changed during finalization: ' + row['label'])
        except BaseException as error: errors.append(row['label'] + ': ' + str(error))
        checks.append(check)
    try:
        if analysis is not None and json.loads((output / 'analysis.json').read_bytes()) != analysis:
            errors.append('Retained analysis changed during finalization')
    except BaseException as error: errors.append('Retained analysis: ' + str(error))
    write(output / 'phase-seal.json', {'checks': checks, 'errors': errors, 'sealed': not errors})
    if errors: raise RuntimeError('; '.join(errors))


class Phases:
    def __init__(self, output, engine, engine_sha256, deadline, environment):
        self.output, self.engine, self.engine_sha256 = output, engine, engine_sha256
        self.deadline, self.environment, self.receipts = deadline, environment, []

    def execute(self, label, arguments, cap):
        remaining(self.deadline, FINAL_RESERVE + CLEANUP)
        if sha(self.engine) != self.engine_sha256: raise RuntimeError('Executable hash changed before phase')
        timeout = min(cap, remaining(self.deadline, FINAL_RESERVE + CLEANUP))
        command = [str(self.engine), *arguments]
        receipt = {'label': label, 'command': command, 'timeout_seconds': timeout, 'timed_out': False,
                   'pid': None, 'exit': None, 'signals': [], 'observed': [], 'cleanup_complete': False}
        self.receipts.append(receipt)
        started, process, root, observed = time.monotonic(), None, None, {}
        log = self.output / (label + '.log')

        def observe():
            nonlocal root
            table = proc_table()
            if root is None and process.pid in table:
                candidate = table[process.pid]
                if candidate['pgid'] != process.pid or candidate['sid'] != process.pid:
                    raise RuntimeError('Spawned child lacks its own expected group/session')
                root = candidate
            seeds = {row['pid'] for row in observed.values() if live(row, table)}
            if root is not None and live(root, table): seeds.add(root['pid'])
            if any(table[pid]['sid'] == process.pid for pid in seeds):
                seeds.update(pid for pid, row in table.items() if row['sid'] == process.pid)
            while True:
                children = {pid for pid, row in table.items() if row['ppid'] in seeds} - seeds
                if not children: break
                seeds.update(children)
            for pid in seeds:
                observed[(pid, table[pid]['start_ticks'])] = table[pid]
            return table

        write(self.output / (label + '.receipt.json'), receipt)
        try:
            with log.open('wb') as stream:
                process = subprocess.Popen(command, env=self.environment, stdout=stream,
                                           stderr=subprocess.STDOUT, start_new_session=True)
                receipt['pid'] = process.pid
                while True:
                    observe()
                    if process.poll() is not None: break
                    if time.monotonic() >= started + timeout:
                        receipt['timed_out'] = True
                        break
                    time.sleep(min(.05, max(0, started + timeout - time.monotonic())))
        except BaseException as error:
            receipt['error'] = {'type':type(error).__name__, 'message':str(error)}
            raise
        finally:
            try:
                if process is not None:
                    cleanup_start = time.monotonic()
                    cleanup_deadline = min(cleanup_start + CLEANUP, self.deadline - FINAL_RESERVE)
                    termed, killed = set(), set()
                    while True:
                        table = observe(); process.poll()
                        survivors = [row for row in observed.values() if live(row, table)]
                        if process.returncode is not None and not survivors: break
                        for row in survivors:
                            identity = (row['pid'], row['start_ticks'])
                            use_kill = time.monotonic() - cleanup_start >= 1
                            sent = killed if use_kill else termed
                            if identity not in sent and row['state'] != 'Z':
                                signum = signal.SIGKILL if use_kill else signal.SIGTERM
                                if signal_identity(row, signum):
                                    receipt['signals'].append({'pid': row['pid'], 'start_ticks': row['start_ticks'],
                                                               'signal': signum.name})
                                sent.add(identity)
                        if time.monotonic() >= cleanup_deadline: break
                        time.sleep(min(.05, max(0, cleanup_deadline - time.monotonic())))
                    table = observe(); process.poll()
                    receipt.update(exit=process.returncode, root_identity=root,
                        observed=list(observed.values()), cleanup_wall_seconds=time.monotonic() - cleanup_start,
                        terminal_observed=[row for row in observed.values() if live(row, table)],
                        terminal_session=[row for row in table.values() if row['sid'] == process.pid],
                        terminal_group=[row for row in table.values() if row['pgid'] == process.pid])
                    receipt['cleanup_complete'] = (root is not None and process.returncode is not None and not receipt['terminal_observed']
                                                   and not receipt['terminal_session'] and not receipt['terminal_group'])
            except BaseException as error:
                receipt["cleanup_error"] = {"type":type(error).__name__, "message":str(error)}
            if process is None: receipt['cleanup_complete'] = True
            raw = log.read_bytes() if log.exists() else None
            receipt.update(wall_seconds=time.monotonic() - started, log=log.name,
                           log_sha256=hashlib.sha256(raw).hexdigest() if raw is not None else None,
                           log_bytes=len(raw) if raw is not None else None,
                           clean_log=raw is not None and not failed(raw.decode('utf-8', errors='replace')))
            write(self.output / (label + '.receipt.json'), receipt)
        if receipt['timed_out']: raise TimeoutError(label + ' exceeded its phase bound')
        if not receipt['cleanup_complete']: raise RuntimeError(label + ' owned cleanup is incomplete')
        remaining(self.deadline, FINAL_RESERVE)
        return receipt


def qualified(receipt):
    return receipt['exit'] == 0 and receipt['clean_log'] and receipt['cleanup_complete'] and not receipt['timed_out']


def acquire(source, freeze, engine, engine_sha256, output):
    source, engine, output = Path(source).resolve(), Path(engine).resolve(), Path(output).absolute()
    if platform.system() != 'Linux': raise RuntimeError('Only Linux /proc acquisition is supported')
    if not re.fullmatch('[0-9a-f]{40}', freeze) or not re.fullmatch('[0-9a-f]{64}', engine_sha256):
        raise ValueError('Pass exact full source commit and executable SHA-256')
    if output.resolve().is_relative_to(source / 'game') or output.is_symlink():
        raise RuntimeError('Output must not alias project source')
    output.mkdir(parents=True, exist_ok=False)  # Exclusive one-shot reservation, even on failure.
    output = output.resolve()
    started = time.monotonic(); deadline = started + WHOLE
    project, state = output / 'project', output / 'private-state'
    report = {'source_commit': freeze, 'engine': str(engine), 'engine_sha256': engine_sha256,
              'whole_cap_seconds': WHOLE, 'original_leak_blocker_resolved': False, 'passed': False, 'acquisition_integrity': False,
              'scope': 'Linux ownership/strict exit only; no audible/physical or complete-descendant qualification',
              'cleanup_scope': 'Observed PID/start identities and original group/session; polling may miss unseen escaped descendants',
              'phases': [], 'finalization_errors': [], 'phase_logs_sealed': False}
    original, before, prepared, runner = None, None, None, None
    additions = {}; final_inventories = {}; snapshots, analysis = [], None
    try:
        original = tracked(source, freeze, deadline); write(output / 'source-before.json', original)
        report['engine_sha256_before'] = sha(engine)
        if report['engine_sha256_before'] != engine_sha256: raise RuntimeError('Executable SHA-256 differs from reviewed pin')
        if recognized(proc_table()): raise RuntimeError('Another recognized engine is running; no launch')
        env = dict(os.environ)
        env['SIGHTBREAK_STATE_DIR'] = str(state)
        for key, part in [('XDG_DATA_HOME', 'data'), ('XDG_CONFIG_HOME', 'config'), ('XDG_CACHE_HOME', 'cache'), ('ANDROID_USER_HOME', 'android')]:
            env[key] = str(state / part); (state / part).mkdir(parents=True, exist_ok=True)
        report['private_environment'] = {key: env[key] for key in ['SIGHTBREAK_STATE_DIR', 'XDG_DATA_HOME', 'XDG_CONFIG_HOME', 'XDG_CACHE_HOME', 'ANDROID_USER_HOME']}
        runner = Phases(output, engine, engine_sha256, deadline, env)
        version = runner.execute('engine-version', ['--headless', '--version'], 30)
        if not qualified(version) or (output / 'engine-version.log').read_text().strip() != toolchain.ENGINE:
            raise RuntimeError('Pinned engine version is not established')
        project.mkdir(); copies = {}
        for name, descriptor in original.items():
            if not name.startswith('game/'): continue
            remaining(deadline, FINAL_RESERVE)
            relative = name.removeprefix('game/'); dst = project / relative
            dst.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(source / name, dst)
            if sha(dst) != descriptor['sha256']: raise RuntimeError('Mechanical source copy changed')
            copies[relative] = descriptor['sha256']
        write(output / 'exact-copy-map.json', copies)
        namespace = 'SIGHTBREAK-audio-lifecycle-' + uuid.uuid4().hex
        custom = namespace + '/input_mode'
        config = (project / 'project.godot').read_text()
        if config.count('[application]\n') != 1 or re.search(r'^config/(use_custom_user_dir|custom_user_dir_name)=', config, re.M):
            raise RuntimeError('Unsupported original project application settings')
        config = config.replace('[application]\n', '[application]\nconfig/use_custom_user_dir=true\nconfig/custom_user_dir_name=' + json.dumps(custom) + '\n', 1)
        (project / 'project.godot').write_text(config)
        report['declared_project_override'] = {'custom_user_dir': custom, 'project_sha256': sha(project / 'project.godot')}
        before = inventory(project, deadline); write(output / 'project-before-import.json', before)
        imported_run = runner.execute('private-import', ['--path', str(project), '--headless', '--editor', '--import', '--quit'], 120)
        after = inventory(project, deadline); write(output / 'project-after-import.json', after)
        additions = imported(before, after, project); write(output / 'import-additions.json', additions)
        for name in additions:
            if name.endswith('.uid'):
                dst = output / 'generated-uids' / name; dst.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(project / name, dst)
        if not qualified(imported_run): raise RuntimeError('Strict private import failed; suite is skipped')
        prepared = {name: digest for name, digest in after.items() if not name.startswith('.godot/')}
        driver = output / 'identity_probe.gd'; driver.write_text(PROBE)
        report['identity_probe_sha256'] = sha(driver)

        def identity(label):
            destination = output / (label + '.json')
            receipt = runner.execute(label, ['--path', str(project), '--headless', '--script', str(driver), '--', '--receipt=' + str(destination)], 30)
            if not qualified(receipt): raise RuntimeError('Strict native identity probe failed')
            data = json.loads(destination.read_text())
            if (Path(data['project_path']).resolve() != project or Path(data['data_dir']).resolve() != state / 'data'
                    or Path(data['user_data_dir']).resolve() != state / 'data' / custom
                    or data['uses_custom_user_dir'] is not True or data['custom_user_dir'] != custom or data['driver'] != 'Dummy'):
                raise RuntimeError('Actual native project/userdata/default driver identity differs')
            return data

        native_before = identity('before-input-mode'); report['native_before'] = native_before
        if native_before['profile_exists'] is not False or native_before['diagnostics_exist'] is not False:
            raise RuntimeError('Refusing preexisting native suite state')
        suite = runner.execute('input-mode', ['--path', str(project), *SUITE], 120)
        if suite['exit'] != 0: raise RuntimeError('Diagnostic suite did not exit zero')
        report['native_after'] = identity('after-input-mode')
        report['acquisition_completed'] = True
    except BaseException as error:
        report['error'] = {'type': type(error).__name__, 'message': str(error)}
    finally:
        report['phases'] = runner.receipts if runner is not None else []
        for label, operation in [
            ('source-after', lambda: tracked(source, freeze, deadline)),
            ('project-final', lambda: inventory(project, deadline) if project.exists() else {}),
            ('private-state-final', lambda: inventory(state, deadline) if state.exists() else {})]:
            try:
                data = operation(); write(output / (label + '.json'), data); final_inventories[label] = data
                if label == 'source-after' and original is not None and data != original: raise RuntimeError('Original source manifest drifted')
                if label == 'project-final' and prepared is not None and {k: v for k, v in data.items() if not k.startswith('.godot/')} != prepared:
                    raise RuntimeError('Prepared non-cache project resources drifted')
            except BaseException as error: report['finalization_errors'].append({'stage': label, 'error': str(error)})
        try:
            snapshots, analysis = phase_snapshots(output, report['phases'], deadline, report['finalization_errors'], report.get('acquisition_completed', False))
        except BaseException as error: report['finalization_errors'].append({'stage': 'phase_snapshots', 'error': str(error)})
        try:
            report['engine_sha256_after'] = sha(engine)
            if report['engine_sha256_after'] != engine_sha256: raise RuntimeError('Executable hash drifted')
            if recognized(proc_table()): raise RuntimeError('Recognized engine remains after acquisition')
            if any(not row['cleanup_complete'] for row in report['phases']): raise RuntimeError('Owned process cleanup incomplete; private trees retained')
            if any(path.is_symlink() or path.resolve().parent != output for path in (state, project)):
                raise RuntimeError('Private cleanup path no longer belongs to reserved output')
            if state.exists():
                original_state = final_inventories['private-state-final']
                if inventory(state, deadline) != original_state: raise RuntimeError('Private state changed before archive')
                copy_owned_tree(state, output / 'produced-private-state', deadline)
                archive = inventory(output / 'produced-private-state', deadline)
                state_after = inventory(state, deadline)
                write(output / 'private-state-archive.json', archive); write(output / 'private-state-after-copy.json', state_after)
                report['private_state_archive_verified'] = archive == original_state == state_after
                if not report['private_state_archive_verified']: raise RuntimeError('Private archive inventory/content differs; original preserved')
            expected_uids = {name: digest for name, digest in additions.items() if name.endswith('.uid')}
            retained_uids = inventory(output / 'generated-uids', deadline)
            write(output / 'retained-uids-final.json', retained_uids)
            if retained_uids != expected_uids: raise RuntimeError('Retained UID archive differs; original preserved')
            seal_phase_snapshots(output, snapshots, analysis, deadline)
            report['phase_logs_sealed'] = True
            if project.exists() and inventory(project, deadline) != final_inventories['project-final']:
                raise RuntimeError('Private project changed during finalization')
            sealed_source = tracked(source, freeze, deadline); write(output / 'source-sealed.json', sealed_source)
            if original is not None and sealed_source != original: raise RuntimeError('Source changed during finalization')
            report['engine_sha256_sealed'] = sha(engine)
            if report['engine_sha256_sealed'] != engine_sha256: raise RuntimeError('Executable changed during finalization')
            if report['finalization_errors']:
                raise RuntimeError('Retained evidence integrity failed; originals preserved')
            if state.exists():
                archive_sealed = inventory(output / 'produced-private-state', deadline)
                source_sealed = inventory(state, deadline)
                matches = archive_sealed == source_sealed == final_inventories['private-state-final']
                write(output / 'private-state-archive-seal.json', {'archive': archive_sealed, 'source': source_sealed, 'verified': matches})
                if not matches: raise RuntimeError('Private archive/source changed before removal; originals preserved')
            if inventory(output / 'generated-uids', deadline) != expected_uids:
                raise RuntimeError('UID archive changed before removal; originals preserved')
            if state.exists(): remaining(deadline); shutil.rmtree(state)
            if project.exists(): remaining(deadline); shutil.rmtree(project)
        except BaseException as error: report['finalization_errors'].append({'stage': 'owned_cleanup', 'error': str(error)})
        report['private_project_removed'] = not project.exists(); report['private_state_removed'] = not state.exists()
        report['originals_preserved_due_integrity_failure'] = bool(report['finalization_errors'])
        report['whole_wall_seconds'] = time.monotonic() - started
        if report['whole_wall_seconds'] > WHOLE: report['finalization_errors'].append({'stage': 'whole_deadline', 'error': '240-second bound exceeded'})
        report['acquisition_integrity'] = bool(report.get('acquisition_completed') and not report.get('error')
                                               and not report['finalization_errors'] and analysis is not None)
        report['sample_strict_clean'] = not analysis['strict_raw_log_failed'] if analysis is not None else False
        report['passed'] = report['acquisition_integrity'] and report['sample_strict_clean']
        write(output / 'overall.json', report)
    return 0 if report['passed'] else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-commit', required=True)
    parser.add_argument('--engine', required=True, type=Path)
    parser.add_argument('--engine-sha256', required=True)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    previous = signal.getsignal(signal.SIGTERM)
    def interrupted(_signum, _frame): raise InterruptedError('Acquisition controller received SIGTERM')
    signal.signal(signal.SIGTERM, interrupted)
    try: return acquire(toolchain.ROOT, args.source_commit, args.engine, args.engine_sha256, args.output)
    finally: signal.signal(signal.SIGTERM, previous)


if __name__ == '__main__':
    raise SystemExit(main())
