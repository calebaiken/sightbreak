"""Hard wall-clock supervision for native exported-client controllers."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid

from godot_process import prepare_output, process_group_options, terminate_process_tree
from native_log import failed as native_log_failed

WORKER_FLAG = '--_export-flow-worker'
TOKEN_ENV = 'SIGHTBREAK_EXPORT_FLOW_TOKEN'


def prepare_flow_output(path, supervised=False):
    if not supervised:
        return prepare_output(path)
    path = path.resolve()
    marker = json.loads((path / 'watchdog.json').read_text(encoding='utf-8'))
    if not os.environ.get(TOKEN_ENV) or marker.get('token') != os.environ[TOKEN_ENV]:
        raise RuntimeError('Export controller requires its owning watchdog token')
    if {item.name for item in path.iterdir()} - {'watchdog.json', 'watchdog.log', 'results.json'}:
        raise FileExistsError('Worker output contains earlier evidence')
    return path


def supervise(script, arguments, output, timeout):
    """Keep raw output and an incomplete receipt before starting the worker."""
    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError('Watchdog timeout must be finite and positive')
    output = prepare_output(Path(output))
    token = uuid.uuid4().hex
    command = [sys.executable, str(script), WORKER_FLAG, *arguments]
    state = {'passed': False, 'status': 'incomplete', 'token': token,
             'command': command, 'timeout_seconds': timeout,
             'controller_sha256': hashlib.sha256(Path(script).read_bytes()).hexdigest()}
    (output / 'watchdog.json').write_text(json.dumps(state, indent=2) + '\n', encoding='utf-8')
    (output / 'results.json').write_text(json.dumps({'passed': False, 'stage': 'watchdog-start',
                                                  'status': 'incomplete'}, indent=2) + '\n', encoding='utf-8')
    process, code, failure = None, None, None
    started = time.monotonic()
    with (output / 'watchdog.log').open('xb') as log:
        try:
            process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT,
                                       env={**os.environ, TOKEN_ENV: token}, **process_group_options())
            code = process.wait(timeout=timeout)
            if code != 0:
                failure = 'Export controller exited ' + str(code)
        except subprocess.TimeoutExpired:
            failure = 'Export controller exceeded the hard wall-clock watchdog'
        except (Exception, KeyboardInterrupt) as error:
            failure = type(error).__name__ + ': ' + str(error)
        finally:
            if process is not None:
                try:
                    terminate_process_tree(process)
                except (Exception, KeyboardInterrupt) as error:
                    failure = (failure or '') + '; watchdog cleanup failed: ' + str(error)
    if native_log_failed((output / 'watchdog.log').read_text(encoding='utf-8', errors='replace')):
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
