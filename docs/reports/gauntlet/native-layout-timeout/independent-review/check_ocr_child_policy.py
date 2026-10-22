#!/usr/bin/env python3
"""Exercise the frozen helper with observable real child processes."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

CANDIDATE = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(CANDIDATE / 'scripts'))
from capture_desktop_layouts import run_layout_ocr


def main():
    original_limit = os.environ.get('OMP_THREAD_LIMIT')
    original_marker = os.environ.get('SIGHTBREAK_CRITIC_ENV_MARKER')
    report = {'scope': 'Actual child environment/error handling; no Godot or image recognition claim.',
              'source_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=CANDIDATE, text=True).strip(),
              'capture_script_sha256': hashlib.sha256((CANDIDATE / 'scripts/capture_desktop_layouts.py').read_bytes()).hexdigest()}
    try:
        os.environ['OMP_THREAD_LIMIT'] = '8'
        os.environ['SIGHTBREAK_CRITIC_ENV_MARKER'] = 'retained'
        receipt = {}
        command = [sys.executable, '-c', 'import json,os,sys; print(json.dumps({"limit":os.environ.get("OMP_THREAD_LIMIT"), "marker":os.environ.get("SIGHTBREAK_CRITIC_ENV_MARKER")})); sys.stderr.write("retained error stream\\n")']
        result = run_layout_ocr(command, b'', stderr=subprocess.PIPE, timeout=2, receipt=receipt)
        assert json.loads(result.stdout) == {'limit': '1', 'marker': 'retained'}
        assert result.stderr == b'retained error stream\n'
        assert result.returncode == receipt['exit_code'] == 0
        assert receipt['thread_environment'] == {'OMP_THREAD_LIMIT': '1'}
        assert receipt['timeout_seconds'] == 2
        assert os.environ['OMP_THREAD_LIMIT'] == '8'
        report['success_receipt'] = receipt
        report['child_limit_one_parent_limit_eight_other_environment_preserved'] = True

        receipt = {}
        result = run_layout_ocr([sys.executable, '-c', 'import sys; sys.stdout.write("partial output"); sys.stderr.write("actual failure"); sys.exit(7)'],
                                b'', stderr=subprocess.PIPE, timeout=2, receipt=receipt)
        assert result.returncode == receipt['exit_code'] == 7
        assert result.stdout == b'partial output' and result.stderr == b'actual failure'
        assert 'error_type' not in receipt
        report['nonzero_receipt'] = receipt
        report['nonzero_exit_and_streams_preserved'] = True

        receipt = {}
        try:
            run_layout_ocr([sys.executable, '-c', 'import time; time.sleep(1)'], b'',
                           stderr=subprocess.PIPE, timeout=.01, receipt=receipt)
        except subprocess.TimeoutExpired as error:
            assert error.timeout == .01
        else:
            raise AssertionError('Actual child exceeded original timeout without exception')
        assert receipt['error_type'] == 'TimeoutExpired'
        assert receipt['timeout_seconds'] == .01
        assert 'exit_code' not in receipt and receipt['elapsed_seconds'] > 0
        assert os.environ['OMP_THREAD_LIMIT'] == '8'
        report['timeout_receipt'] = receipt
        report['exact_timeout_exception_parent_environment_preserved'] = True

        receipt = {}
        try:
            run_layout_ocr(['/nonexistent-sightbreak-critic-child'], b'', stderr=subprocess.PIPE, timeout=2, receipt=receipt)
        except FileNotFoundError:
            pass
        else:
            raise AssertionError('Missing executable accepted')
        assert receipt['error_type'] == 'FileNotFoundError'
        assert 'exit_code' not in receipt and receipt['elapsed_seconds'] > 0
        report['missing_executable_receipt'] = receipt
    finally:
        for key, value in [('OMP_THREAD_LIMIT', original_limit), ('SIGHTBREAK_CRITIC_ENV_MARKER', original_marker)]:
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
    assert os.environ.get('OMP_THREAD_LIMIT') == original_limit
    assert os.environ.get('SIGHTBREAK_CRITIC_ENV_MARKER') == original_marker
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
