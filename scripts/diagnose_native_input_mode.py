#!/usr/bin/env python3
"""Retain one bounded verbose ARM input_mode repeat; never repair its strict gate."""
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
from run_native_regressions import NativeSceneSuites, inventory
import toolchain


def evidence(directory):
    return {name: hashlib.sha256((directory / name).read_bytes()).hexdigest() if (directory / name).is_file() else None
            for name in ('results.json', 'isolation.json', 'input_mode.log')}


def select_failure(directory):
    """Select only the retained exit-zero input_mode leak, without changing it."""
    missing = [name for name in ('results.json', 'isolation.json', 'input_mode.log') if not (directory / name).is_file()]
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
    matches = [row for row in results if row.get('suite') == 'input_mode']
    if (len(matches) != 1 or results[-1] != matches[0] or matches[0].get('exit') != 0
            or matches[0].get('clean_log') is not False or isolation.get('passed') is not False
            or isolation.get('failure', {}).get('message') != 'input_mode failed; raw output retained'):
        return 'Original strict failure is not the exit-zero input_mode log failure'
    text = (directory / 'input_mode.log').read_text(errors='replace')
    if not re.search(r'ObjectDB.*leaked', text) or not failed(text):
        return 'Original input_mode log does not establish the ObjectDB leak'
    if (isolation.get('source_resources_unchanged') is not True
            or isolation.get('copied_resources_unchanged') is not True
            or isolation.get('temporary_project_removed') is not True
            or isolation.get('finalization_failures') != [] or not isolation.get('cleanup')
            or not all(isinstance(item, dict) and item.get('removed') is True for item in isolation['cleanup'])):
        return 'Original source or owned cleanup receipt was not clean'
    if isolation.get('source_resources_sha256') != inventory(toolchain.ROOT / 'game'):
        return 'Current source bytes differ from the original failed strict suite'
    return None


class VerboseInputMode(NativeSceneSuites):
    def __init__(self, output, deadline):
        super().__init__(output)
        self.deadline = deadline
        self.processes = []
        self.report.update(scope='Diagnostic-only verbose input_mode repeat; original strict gate remains failed',
                           whole_deadline_seconds=240, process_receipts='owned-processes.json')

    def execute(self, label, arguments, timeout):
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError('Whole verbose diagnostic deadline exceeded')
        arguments = list(arguments)
        if label == 'input_mode':
            if arguments != ['--headless', '--script', 'res://tests/input_mode_test.gd']:
                raise RuntimeError('Diagnostic must repeat the exact maintained input_mode suite')
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
        reason = select_failure(failed_output)
        if reason is not None:
            report.update(status='SKIPPED_DIFFERENT_OR_UNPROVEN_FAILURE', skip_reason=reason)
        else:
            runner = VerboseInputMode(output / 'repeat', started + 240)
            try:
                with runner:
                    runner.run('input_mode')
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
