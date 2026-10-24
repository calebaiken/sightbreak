"""Hard wall-clock supervision for native exported-client controllers."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import time
import uuid

from godot_process import prepare_output
from matrix_process import run_process
from native_log import failed as native_log_failed

WORKER_FLAG = '--_export-flow-worker'
TOKEN_ENV = 'SIGHTBREAK_EXPORT_FLOW_TOKEN'
PROCESS_RECEIPT = 'watchdog.process.json'


def prepare_flow_output(path, supervised=False):
    if not supervised:
        return prepare_output(path)
    path = path.resolve()
    marker = json.loads((path / 'watchdog.json').read_text(encoding='utf-8'))
    if (not isinstance(marker, dict) or not os.environ.get(TOKEN_ENV)
            or marker.get('token') != os.environ[TOKEN_ENV]):
        raise RuntimeError('Export controller requires its owning watchdog token')
    if marker.get('status') != 'incomplete' or marker.get('passed') is not False:
        raise FileExistsError('Worker output belongs to a completed watchdog')
    if marker.get('process_receipt') != PROCESS_RECEIPT:
        raise RuntimeError('Export controller has an invalid process receipt owner')
    if {item.name for item in path.iterdir()} - {'watchdog.json', 'watchdog.log', 'results.json', PROCESS_RECEIPT}:
        raise FileExistsError('Worker output contains earlier evidence')
    return path


def supervise(script, arguments, output, timeout):
    """Keep initial failed receipts, then own the entire worker process tree.

    The wall-clock pass deadline includes startup and cleanup. On failure the
    shared runner has bounded additional waits to finish containment cleanup;
    a late clean exit is never a passing export flow.
    """
    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError('Watchdog timeout must be finite and positive')
    started = time.monotonic()
    deadline = started + timeout
    output = prepare_output(Path(output))
    token = uuid.uuid4().hex
    command = [sys.executable, '-B', str(script), WORKER_FLAG, *arguments]
    hash_error = None
    try:
        controller_hash = hashlib.sha256(Path(script).read_bytes()).hexdigest()
    except OSError as error:
        controller_hash, hash_error = None, error
    state = {'passed': False, 'status': 'incomplete', 'token': token,
             'command': command, 'timeout_seconds': timeout,
             'process_receipt': PROCESS_RECEIPT, 'controller_sha256': controller_hash}
    with (output / 'watchdog.json').open('x', encoding='utf-8') as receipt:
        receipt.write(json.dumps(state, indent=2) + '\n')
    with (output / 'results.json').open('x', encoding='utf-8') as receipt:
        receipt.write(json.dumps({'passed': False, 'stage': 'watchdog-start',
                                 'status': 'incomplete'}, indent=2) + '\n')
    code, failure = None, None
    with (output / 'watchdog.log').open('x', encoding='utf-8') as log:
        try:
            if hash_error is not None:
                raise hash_error
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError('Export controller exceeded the hard wall-clock watchdog before launch')
            code = run_process(command, cwd=None, env={**os.environ, TOKEN_ENV: token}, log=log,
                               result_path=output / PROCESS_RECEIPT, timeout=remaining)
            if type(code) is not int:
                raise RuntimeError('Process supervisor returned an invalid worker exit')
            if code != 0:
                failure = 'Export controller exited ' + str(code)
        except (Exception, KeyboardInterrupt) as error:
            failure = type(error).__name__ + ': ' + str(error)
            log.write('\nHARNESS_ERROR ' + failure + '\n')
        if time.monotonic() >= deadline:
            failure = (failure or '') + '; Export controller exceeded the hard wall-clock watchdog (including cleanup)'
            log.write('\nHARNESS_ERROR hard wall-clock watchdog exceeded (including cleanup)\n')
    try:
        text = (output / 'watchdog.log').read_text(encoding='utf-8', errors='replace')
    except OSError as error:
        text = ''
        failure = (failure or '') + '; missing/unreadable watchdog log: ' + str(error)
    if 'HARNESS_ERROR' in text:
        failure = (failure or '') + '; process containment reported HARNESS_ERROR (see watchdog.log)'
    if native_log_failed(text):
        failure = (failure or '') + '; controller emitted a native error or resource leak'
    try:
        result = json.loads((output / 'results.json').read_text(encoding='utf-8'))
        if not isinstance(result, dict):
            raise ValueError('result is not an object')
    except (OSError, ValueError) as error:
        result = {}
        failure = (failure or '') + '; missing/invalid worker result: ' + str(error)
    if result.get('passed') is not True:
        failure = failure or 'Export controller did not produce a passing result'
    if time.monotonic() >= deadline and not failure:
        failure = 'Export controller exceeded the hard wall-clock watchdog during final audit'
        with (output / 'watchdog.log').open('a', encoding='utf-8') as log:
            log.write('\nHARNESS_ERROR ' + failure + '\n')
    if failure:
        result.update({'passed': False, 'watchdog_error': failure})
    state.update({'passed': not failure, 'status': 'failed' if failure else 'passed',
                  'worker_exit': code, 'seconds': round(time.monotonic() - started, 3), 'error': failure})
    result['watchdog'] = {key: value for key, value in state.items() if key != 'token'}
    (output / 'watchdog.json').write_text(json.dumps(state, indent=2) + '\n', encoding='utf-8')
    (output / 'results.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2), flush=True)
    return 1 if failure else 0


def entry(main, script, default_output=None, default_timeout=300):
    if WORKER_FLAG in sys.argv[1:]:
        sys.argv.remove(WORKER_FLAG)
        main(supervised=True)
        return 0
    if '-h' in sys.argv[1:] or '--help' in sys.argv[1:]:
        main()
        return 0
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--output', type=Path, default=default_output, required=default_output is None)
    parser.add_argument('--timeout', type=float, default=default_timeout)
    args, _ = parser.parse_known_args()
    if not math.isfinite(args.timeout) or args.timeout <= 0:
        parser.error('timeout must be finite and positive')
    return supervise(Path(script), sys.argv[1:], args.output, args.timeout)
