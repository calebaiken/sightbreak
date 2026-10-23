#!/usr/bin/env python3
"""Retain one bounded verbose ARM actor/input_mode leak repeat; keep strict failure."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import re
import subprocess
import time

from build_manifest import BUILDS, clean, same_source, source
from native_log import failed
from probe_macos_input import reap
from run_native_regressions import NativeSceneSuites, SUITES, inventory
import toolchain


LEAK_SUITES = ('actor', 'input_mode')


def evidence(directory):
    return {name: hashlib.sha256((directory / name).read_bytes()).hexdigest() if (directory / name).is_file() else None
            for name in ('results.json', 'isolation.json', 'actor.log', 'input_mode.log')}


def same_native_path(left, right):
    return (isinstance(left, str) and isinstance(right, str) and Path(left).is_absolute()
            and Path(right).is_absolute() and Path(left).resolve() == Path(right).resolve())


def selected_identity(row, isolation):
    """Validate original argv/native producer identities; never launch their paths."""
    suite, namespace = row['suite'], isolation.get('namespace', '')
    command = row.get('command', [])
    if (not re.fullmatch(r'SIGHTBREAK-native-tests-[0-9a-f]{32}', namespace)
            or not isinstance(command, list) or len(command) != 6
            or not all(isinstance(arg, str) for arg in command)
            or command[0] != toolchain.binary() or command[1] != '--path'
            or command[3:] != ['--headless', '--script', 'res://tests/' + suite + '_test.gd']
            or not Path(command[2]).is_absolute() or Path(command[2]).name != 'project'
            or not Path(command[2]).parent.name.startswith('sightbreak-native-tests-')
            or isolation.get('engine') != toolchain.ENGINE):
        return False
    native_root = None
    for phase in ('before', 'after'):
        receipt = row.get(phase, {})
        if not isinstance(receipt, dict):
            return False
        data_dir, user_dir = receipt.get('data_dir'), receipt.get('user_data_dir')
        if (not isinstance(data_dir, str) or not isinstance(user_dir, str)
                or receipt.get('uses_custom_user_dir') is not True
                or receipt.get('custom_user_dir') != namespace + '/' + suite
                or not same_native_path(receipt.get('project_path'), command[2])
                or not same_native_path(user_dir, str(Path(data_dir) / namespace / suite))
                or receipt.get('run', {}).get('exit') != 0
                or receipt.get('run', {}).get('clean_log') is not True):
            return False
        current_root = str(Path(user_dir).parent)
        if native_root is not None and not same_native_path(native_root, current_root):
            return False
        native_root = current_root
        if phase == 'before' and (receipt.get('profile_exists') is not False or receipt.get('diagnostics_exist') is not False):
            return False
    cleanup = isolation.get('cleanup', [])
    return (isinstance(cleanup, list) and len(cleanup) == 1 and isinstance(cleanup[0], dict)
            and cleanup[0].get('removed') is True
            and same_native_path(cleanup[0].get('user_namespace'), native_root))


def select_failure(directory, selection=None):
    """Select the first retained whitelisted leak; preserve the reason-only API."""
    missing = [name for name in ('results.json', 'isolation.json') if not (directory / name).is_file()]
    if missing:
        return 'Original failure evidence is absent: ' + ', '.join(missing)
    try:
        results = json.loads((directory / 'results.json').read_text())
        isolation = json.loads((directory / 'isolation.json').read_text())
    except json.JSONDecodeError:
        return 'Original failure evidence is not valid JSON'
    if (not isinstance(results, list) or not all(isinstance(row, dict) for row in results)
            or not isinstance(isolation, dict) or not isinstance(isolation.get('failure'), dict)):
        return 'Original failure receipt shape does not establish the required strict failure'
    names = [row.get('suite') for row in results]
    if any(name not in SUITES for name in names) or len(set(names)) != len(names):
        return 'Original suite identifiers are unknown or duplicated'
    failures = [index for index, row in enumerate(results)
                if type(row.get('exit')) is not int or row['exit'] != 0 or row.get('clean_log') is not True]
    if len(failures) != 1 or failures[0] != len(results) - 1:
        return 'Original results do not establish one first failure at the terminal result'
    row = results[failures[0]]
    suite = row['suite']
    if (suite not in LEAK_SUITES or type(row.get('exit')) is not int or row['exit'] != 0
            or row.get('clean_log') is not False or isolation.get('passed') is not False
            or isolation['failure'].get('message') != suite + ' failed; raw output retained'):
        return 'Original first strict failure is not a whitelisted exit-zero leak candidate'
    log = directory / (suite + '.log')
    if not log.is_file():
        return 'Original failed-suite log is absent: ' + log.name
    text = log.read_text(errors='replace')
    if not re.search(r'ObjectDB.*leaked', text) or not failed(text):
        return 'Original failed-suite log does not establish the ObjectDB leak'
    if (isolation.get('source_resources_unchanged') is not True
            or isolation.get('copied_resources_unchanged') is not True
            or isolation.get('temporary_project_removed') is not True
            or isolation.get('finalization_failures') != [] or not isolation.get('cleanup')
            or not all(isinstance(item, dict) and item.get('removed') is True for item in isolation['cleanup'])):
        return 'Original source or owned cleanup receipt was not clean'
    if isolation.get('source_resources_sha256') != inventory(toolchain.ROOT / 'game'):
        return 'Current source bytes differ from the original failed strict suite'
    if not selected_identity(row, isolation):
        return 'Original failed-suite argv or native producer/cleanup identity is foreign or unproven'
    if selection is not None:
        selection['suite'] = suite
    return None


class VerboseInputMode(NativeSceneSuites):
    """Legacy class name retained; optional suite defaults to input_mode."""
    def __init__(self, output, deadline, suite='input_mode'):
        if suite not in LEAK_SUITES:
            raise ValueError('Unsupported diagnostic suite')
        super().__init__(output)
        self.suite = suite
        self.deadline = deadline
        self.processes = []
        self.report.update(scope='Diagnostic-only verbose first failed leak suite; original strict gate remains failed',
                           selected_suite=suite,
                           whole_deadline_seconds=240, process_receipts='owned-processes.json')

    def execute(self, label, arguments, timeout):
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError('Whole verbose diagnostic deadline exceeded')
        arguments = list(arguments)
        if label in SUITES:
            if label != self.suite or arguments != ['--headless', '--script', 'res://tests/' + self.suite + '_test.gd']:
                raise RuntimeError('Diagnostic must repeat only the exact selected maintained suite')
            arguments.insert(1, '--verbose')
        command = [toolchain.binary(), '--path', str(self.project), *arguments]
        started = time.monotonic()
        receipt = {'label': label, 'command': command, 'timeout_seconds': min(timeout, remaining),
                   'timed_out': False, 'exit': None, 'clean_log': False}
        self.processes.append(receipt)
        process = None
        log_path = self.output / (label + '.log')
        try:
            with log_path.open('w', encoding='utf-8') as log:
                process = subprocess.Popen(command, env=toolchain.environment(), stdout=log,
                                           stderr=subprocess.STDOUT, start_new_session=True)
                receipt['pid'] = process.pid
                try:
                    process.wait(timeout=min(timeout, max(.001, self.deadline - time.monotonic())))
                except subprocess.TimeoutExpired:
                    receipt['timed_out'] = True
                    raise
        finally:
            if process is not None:
                receipt['cleanup'] = reap(process)
                receipt['exit'] = process.returncode
            receipt.update(wall_seconds=time.monotonic() - started, log=str(log_path))
            receipt['clean_log'] = log_path.exists() and not failed(log_path.read_text(errors='replace'))
            (self.output / 'owned-processes.json').write_text(json.dumps(self.processes, indent=2) + '\n')
        if receipt.get('cleanup', {}).get('owned_group_gone') is not True:
            raise RuntimeError('Owned verbose diagnostic process group remained after cleanup')
        if time.monotonic() > self.deadline:
            raise TimeoutError('Whole verbose diagnostic deadline exceeded')
        if label == 'private-import':
            self.report['import'] = receipt
            if receipt['exit'] or not receipt['clean_log']:
                raise RuntimeError(label + ' failed; raw output retained')
        return receipt


def run(failed_output, output):
    failed_output, output = Path(failed_output).resolve(), Path(output).resolve()
    if (output.is_relative_to(failed_output) or failed_output.is_relative_to(output)
            or output.is_relative_to(toolchain.ROOT / 'game') or output.is_relative_to(BUILDS / 'macos')):
        raise RuntimeError('Keep new diagnostic evidence separate from source, export and original evidence')
    if output.exists() and any(output.iterdir()):
        raise RuntimeError('Preserve earlier diagnostic evidence; choose fresh output')
    output.mkdir(parents=True, exist_ok=True)
    started, before, original, runner = time.monotonic(), None, None, None
    report = {'scope': 'Diagnostic only; original strict native regression failure is retained',
              'passed': False, 'strict_gate_repaired': False, 'status': 'FAILED',
              'original_output': str(failed_output), 'whole_deadline_seconds': 240}
    try:
        if platform.system() != 'Darwin' or platform.machine() != 'arm64':
            raise RuntimeError('Verbose native diagnostic requires actual ARM macOS')
        before = source()
        clean(before)
        report['source'] = before
        original = evidence(failed_output)
        report['original_evidence_sha256'] = original
        selection = {}
        reason = select_failure(failed_output, selection)
        if reason is not None:
            report.update(status='SKIPPED_DIFFERENT_OR_UNPROVEN_FAILURE', skip_reason=reason)
        else:
            suite = selection['suite']
            report['selected_suite'] = suite
            if evidence(failed_output) != original:
                raise RuntimeError('Original strict failure evidence changed before repeat; no launch')
            current = source()
            if not same_source(before, current) or current['source_dirty'] or current['source_game_dirty']:
                raise RuntimeError('Source changed before verbose repeat; no launch')
            if time.monotonic() - started >= 240:
                raise TimeoutError('Whole verbose diagnostic deadline exceeded before repeat; no launch')
            runner = VerboseInputMode(output / 'repeat', started + 240, suite)
            try:
                with runner:
                    runner.run(suite)
            finally:
                report['isolation'] = runner.report
                report['owned_processes'] = runner.processes
            if time.monotonic() - started > 240:
                raise TimeoutError('Whole verbose diagnostic deadline exceeded during finalization')
            report.update(status='DIAGNOSTIC_CLEAN_REPEAT', passed=runner.report['passed'])
    except (Exception, SystemExit) as error:
        report['failure'] = {'type': type(error).__name__, 'message': str(error)}
    finally:
        try:
            if before is not None:
                after = source()
                report.update(source_after=after, source_unchanged=same_source(before, after)
                              and not after['source_dirty'] and not after['source_game_dirty'])
                if not report['source_unchanged']:
                    raise RuntimeError('Source identity changed during verbose diagnostic')
            if original is not None:
                report['original_evidence_unchanged'] = evidence(failed_output) == original
                if not report['original_evidence_unchanged']:
                    raise RuntimeError('Original strict failure evidence changed')
            if time.monotonic() - started > 240:
                raise TimeoutError('Whole verbose diagnostic deadline exceeded during receipt checks')
        except (Exception, SystemExit) as error:
            report['finalization_failure'] = {'type': type(error).__name__, 'message': str(error)}
            report.update(passed=False, status='FAILED')
        report['seconds'] = time.monotonic() - started
        (output / 'diagnostic.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))
    return 0 if report['passed'] or report['status'] == 'SKIPPED_DIFFERENT_OR_UNPROVEN_FAILURE' else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--failed-output', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    return run(args.failed_output, args.output)


if __name__ == '__main__':
    raise SystemExit(main())
