#!/usr/bin/env python3
"""Independent Linux SDK-selection controls; fixture bytes are not native output."""
import hashlib
import json
import os
from pathlib import Path
import struct
import sys
import tempfile

ROOT = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(ROOT / 'scripts'))
import qualify_ios_compile as ios


def fixture_macho(*, signed=False, platform=2):
    commands = struct.pack('<6I', 0x32, 24, platform, 0, 0, 0)
    if signed:
        commands += struct.pack('<4I', 0x1D, 16, 0, 0)
    return struct.pack('<8I', 0xFEEDFACF, 0x0100000C, 0, 2, 1 + signed,
                       len(commands), 0, 0) + commands


def reject(operation, contains=None):
    try:
        operation()
    except (RuntimeError, FileExistsError) as error:
        if contains:
            assert contains in str(error), str(error)
        return str(error)
    raise AssertionError('Unexpected acceptance')


results = []
with tempfile.TemporaryDirectory() as temporary:
    base = Path(temporary)
    apps = base / 'Applications'
    developer = apps / 'Xcode_26.3.app/Contents/Developer'
    sdk = developer / 'Platforms/iPhoneOS.platform/Developer/SDKs/iPhoneOS26.2.sdk'
    sdk.mkdir(parents=True)
    (apps / 'Xcode.app').symlink_to(developer.parents[1])
    assert ios.installed_developers(apps) == [developer.resolve()]
    results.append('PASS inventory resolves and deduplicates Xcode alias')
    original = dict(os.environ)
    for case, data in [('absent', None), ('signed', fixture_macho(signed=True)),
                       ('simulator', fixture_macho(platform=7)),
                       ('truncated', b'\xcf\xfa\xed\xfe')]:
        report, calls, environment = {}, [], {'DEVELOPER_DIR': '/original', 'KEEP': 'unchanged'}
        def attempt(label, command, env):
            calls.append((label, list(command), dict(env)))
            if command[-1] == '--show-sdk-path':
                return 0, str(sdk)
            if data is not None:
                Path(command[-1]).write_bytes(data)
            return 0, ''
        reject(lambda: ios.select_xcode(report, environment, base / case, attempt, apps),
               'No installed Xcode can link')
        assert environment == {'DEVELOPER_DIR': '/original', 'KEEP': 'unchanged'}
        assert dict(os.environ) == original
        assert len(calls) == 2 and not report['sdk_selection']['candidates'][0]['compatible']
        results.append('PASS zero-exit ' + case + ' probe fails closed; environment unchanged')
    outside = base / 'unowned-sdk'
    outside.mkdir()
    calls = []
    def outside_attempt(label, command, env):
        calls.append(command)
        return 0, str(outside)
    report = {}
    reject(lambda: ios.select_xcode(report, {}, base / 'outside', outside_attempt, apps))
    assert len(calls) == 1
    assert 'does not belong' in report['sdk_selection']['candidates'][0]['failure']
    results.append('PASS SDK outside candidate Developer directory rejected before compiler')
    stale = base / 'stale/sdk-probe'
    stale.mkdir(parents=True)
    (stale / 'candidate-0').write_bytes(fixture_macho())
    calls = []
    reject(lambda: ios.select_xcode({}, {}, stale.parent,
           lambda *args: calls.append(args), apps))
    assert calls == []
    results.append('PASS stale probe directory and valid prior binary rejected before commands')
    empty = base / 'empty-applications'
    empty.mkdir()
    reject(lambda: ios.select_xcode({}, {}, base / 'no-inventory', lambda *args: None, empty),
           'No bounded installed Xcode inventory')
    results.append('PASS empty installed Xcode inventory rejected')
    for n in range(17):
        (empty / f'Xcode_{n}.app/Contents/Developer').mkdir(parents=True)
    reject(lambda: ios.select_xcode({}, {}, base / 'over-inventory', lambda *args: None, empty),
           'No bounded installed Xcode inventory')
    results.append('PASS more than 16 distinct installed Xcodes rejected')

retained = ROOT / 'docs/reports/gauntlet/m2-ios-compile/sdk-iteration/failure-0ca125d'
log = (retained / 'xcodebuild-device.txt').read_text()
reject(lambda: ios.inspect_build_actions(log))
actions = '\n'.join(line for line in log.splitlines() if line.startswith(('CompileC ', 'Ld ')))
assert " normal (in target 'sightbreak'" in actions
# This appended marker is synthetic. It exercises only the action parser.
assert ios.inspect_build_actions(actions + '\n** BUILD SUCCEEDED **\n')['linker_action']
reject(lambda: ios.inspect_build_actions(actions.replace("target 'sightbreak'", "target 'other'") + '\n** BUILD SUCCEEDED **\n'))
reject(lambda: ios.inspect_build_actions(actions + '\n** BUILD SUCCEEDED **\n** BUILD FAILED **\n'))
results.append('PASS actual failed native log rejected; observed Ld normal format accepted only in synthetic parser fixture')
results.append('PASS foreign linker target and mixed success/failure markers rejected')
raw = Path('/workspace/reviews/mac-ci-39719407304/arm-receipts/evidence/ios-compile')
hashes = {}
if raw.is_dir():
    for target, source in [('compile.json', 'compile.json'), ('exported-source.json', 'exported-source.json'),
                           ('xcodebuild-device.txt', 'xcodebuild-device.log')]:
        data = (retained / target).read_bytes()
        assert data == (raw / source).read_bytes()
        hashes[target] = hashlib.sha256(data).hexdigest()
    results.append('PASS all three retained failure files match downloaded ARM receipts byte-for-byte')
print('\n'.join(results))
print(json.dumps({'control_count': len(results), 'receipt_sha256': hashes,
                  'native_compile': 'UNVERIFIED; Linux fixture controls only'}, indent=2))
