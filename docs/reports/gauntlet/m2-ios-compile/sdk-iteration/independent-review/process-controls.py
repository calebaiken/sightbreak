#!/usr/bin/env python3
"""Independent process controls; mocked Darwin receipts do not prove a Mac build."""
import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from unittest.mock import patch

ROOT = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(ROOT / 'scripts'))
import qualify_ios_compile as ios

with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    log = root / 'partial.log'
    result = ios.bounded_command([sys.executable, '-c',
        "import time; print('partial-before-timeout', flush=True); time.sleep(10)"], log, .08)
    assert result['timed_out'] and result['cleanup_complete'] and result['exit_code'] != 0
    assert 'partial-before-timeout' in log.read_text()
    print('PASS real Linux 80 ms timeout retains partial log and reaps owned process')
    print(json.dumps(result, sort_keys=True))
    marker = root / 'escaped-marker'
    descendant = "import pathlib,time; time.sleep(.3); pathlib.Path(" + repr(str(marker)) + ").write_text('bad')"
    leader = "import subprocess,sys; subprocess.Popen([sys.executable, '-c', " + repr(descendant) + "])"
    result = ios.bounded_command([sys.executable, '-c', leader], root / 'leader.log', 1)
    assert result['exit_code'] == 0 and result['unexpected_descendants'] and result['cleanup_complete']
    time.sleep(.35)
    assert not marker.exists()
    print('PASS real Linux zero-exit leader with residual descendant is flagged and child killed')
    print(json.dumps(result, sort_keys=True))
    expired = root / 'must-not-open.log'
    try:
        ios.bounded_command([sys.executable, '-c', 'raise SystemExit(0)'], expired, 0)
    except RuntimeError as error:
        assert 'deadline exhausted' in str(error)
    else:
        raise AssertionError('Expired command launched')
    assert not expired.exists()
    print('PASS exhausted budget rejects launch before opening log')

    apps = root / 'Applications'
    developer = apps / 'Xcode_26.3.app/Contents/Developer'
    sdk = developer / 'SDKs/iPhoneOS.sdk'
    sdk.mkdir(parents=True)
    selection = ios.select_xcode
    original_environment = dict(os.environ)
    for mode in ['link-rejection', 'timeout', 'cleanup-failure']:
        commands = []
        def fake_bounded(command, log, seconds, *, env=None):
            commands.append((list(command), seconds, dict(env)))
            if '--source-snapshot' in command:
                output = '{}'
            elif command == ['xcode-select', '-p']:
                output = '/default'
            elif command[-1] == '--show-sdk-path':
                output = str(sdk)
            elif 'clang' in command:
                output = 'Undefined symbols: _MTLTensorDomain'
            else:
                raise AssertionError('Unexpected post-preflight command: ' + repr(command))
            Path(log).write_text(output)
            probe = 'clang' in command
            return {'command': list(command), 'timeout_seconds': seconds,
                    'timed_out': probe and mode == 'timeout',
                    'exit_code': 1 if probe else 0,
                    'cleanup_complete': not (probe and mode == 'cleanup-failure'),
                    'unexpected_descendants': False, 'cleanup_errors': []}
        output = root / mode / 'output'
        with patch.object(ios.platform, 'system', return_value='Darwin'), \
             patch.object(ios.platform, 'machine', return_value='arm64'), \
             patch.object(ios, 'bounded_command', side_effect=fake_bounded), \
             patch.object(ios, 'select_xcode', side_effect=lambda *args: selection(*args, applications=apps)), \
             contextlib.redirect_stdout(io.StringIO()):
            code = ios.qualify(output, root / mode / 'export', root / mode / 'derived', 1)
        report = json.loads((output / 'compile.json').read_text())
        assert code == 1 and report['status'] == 'FAILED' and not report['compile_completed']
        assert len(commands) == 4 and not (root / mode / 'export').exists()
        budgets = [item[1] for item in commands]
        assert 0 < budgets[-1] < budgets[0] <= 1 and all(a >= b for a,b in zip(budgets, budgets[1:]))
        assert dict(os.environ) == original_environment
        print('PASS qualify fixture ' + mode + ': FAILED receipt, no export, decreasing shared budget, no global environment mutation')
        print(json.dumps({'failure': report['failure'], 'budgets': budgets,
                          'commands': [c[0] for c in commands]}, sort_keys=True))
print('NATIVE COMPILE UNVERIFIED. Process tests run on Linux; qualify host/command receipts above are fixtures.')
