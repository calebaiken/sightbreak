"""Linux-only source controls of frozen 946446f; all native interactions mocked."""
import contextlib
import ctypes
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(ROOT / 'scripts'))
COMMIT = '946446f11c3bf4bf46439b7a8ec97dea76d032a1'


def frozen(path):
    return subprocess.check_output(['git', 'show', COMMIT + ':' + path], cwd=ROOT, text=True)


source = frozen('scripts/probe_macos_input.py')
probe = types.ModuleType('probe_macos_input')
probe.__file__ = 'git:' + COMMIT + ':scripts/probe_macos_input.py'
exec(compile(source, probe.__file__, 'exec'), probe.__dict__)
sys.modules['probe_macos_input'] = probe
print('Subject:', COMMIT, flush=True)
print('Frozen script SHA256:', hashlib.sha256(source.encode()).hexdigest(), flush=True)
print('Linux controls only; no native APIs, exports, engine workload, or CI.', flush=True)
tests = types.ModuleType('frozen_controls')
exec(compile(frozen('scripts/test_probe_macos_input.py'), 'frozen_tests', 'exec'), tests.__dict__)
result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
assert result.wasSuccessful()
print('ctypes sizes:', {kind.__name__: ctypes.sizeof(kind) for kind in (probe.Point, probe.Size, probe.Rect)})


class API:
    def preflight(self):
        return dict.fromkeys(('CGPreflightPostEventAccess', 'CGPreflightScreenCaptureAccess',
                              'CGPreflightListenEventAccess', 'AXIsProcessTrusted'), True)

    def displays(self): return []
    def controls(self): return {'event_delivery_verified': False, 'keyboard_focus_verified': False}
    def windows(self, pid): return [{'owner_pid': pid, 'onscreen': True}]


class Child:
    pid = 987654321
    returncode = None

    def poll(self):
        old = self.returncode
        self.returncode = 0
        return old


def control(name, expected_code, expected_status, *, existing=None, second_guard=False,
            profile_created=False, cache_created=False, engine_error=False,
            cleanup_gone=True, source_changed=False, timeout=60):
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        output, native = root / 'evidence', root / 'native-user'
        if existing:
            native.mkdir()
            entry = native / 'offline_training.json'
            if existing == 'file': entry.write_bytes(b'private profile bytes')
            elif existing == 'directory': entry.mkdir()
            elif existing == 'dangling': entry.symlink_to(native / 'missing')
            else: raise AssertionError(existing)
        actual_inventory = probe.user_directory_inventory

        def inventory():
            result = actual_inventory()
            if second_guard:
                native.mkdir(exist_ok=True)
                (native / 'offline_training.json.tmp').write_bytes(b'private temporary profile')
            return result

        def launch(command, stdout, **kwargs):
            assert kwargs['start_new_session'] is True
            assert command[command.index('--log-file') + 1] == str(output / 'engine.log')
            stdout.write('SIGHTBREAK_MAIN_READY screen=menu\n')
            stdout.flush()
            (output / 'engine.log').write_text('ERROR: injected native error\n' if engine_error else 'clean synthetic engine log\n')
            (output / 'exported-smoke.png').write_bytes(b'synthetic-control')
            if profile_created or cache_created:
                native.mkdir(exist_ok=True)
            if profile_created:
                (native / 'offline_training.json').write_bytes(b'synthetic new profile')
            if cache_created:
                (native / 'shader_cache').mkdir()
                (native / 'shader_cache/cache.bin').write_bytes(b'synthetic cache')
            return Child()

        sources = iter([{'revision': 'fixed'}, {'revision': 'changed' if source_changed else 'fixed'}])
        original_digest = probe.digest

        def digest(path):
            if Path(path).name in ('offline_training.json', 'offline_training.json.tmp'):
                raise AssertionError('A player profile was opened for hashing')
            if Path(path).is_file(): return original_digest(path)
            return 'control'

        with contextlib.ExitStack() as stack:
            stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
            launch_mock = None
            for target, attribute, kwargs in (
                (probe, 'MacReadOnly', {'new': API}),
                (probe, 'source', {'side_effect': lambda: next(sources)}),
                (probe, 'clean', {}),
                (probe, 'validate_record', {'return_value': {'artifact': {'sha256': 'control'}}}),
                (probe, 'digest', {'side_effect': digest}),
                (probe.toolchain, 'verify_engine', {'return_value': 'mocked-version-control'}),
                (probe, 'user_directory', {'return_value': native}),
                (probe, 'user_directory_inventory', {'side_effect': inventory}),
                (probe.platform, 'platform', {'return_value': 'Linux fully mocked observer control'}),
                (probe.subprocess, 'Popen', {'side_effect': launch}),
                (probe, 'reap', {'return_value': {'owned_group_gone': cleanup_gone}}),
                (probe.time, 'sleep', {}),
            ):
                mocked = stack.enter_context(patch.object(target, attribute, **kwargs))
                if attribute == 'Popen': launch_mock = mocked
            code = probe.run(output, timeout=timeout)
        receipt = json.loads((output / 'results.json').read_text())
        assert (code, receipt['status']) == (expected_code, expected_status), (name, code, receipt)
        assert receipt['native_input_verified'] is False
        assert receipt['input_events_posted'] == receipt['permission_requests_made'] == 0
        if existing or second_guard:
            launch_mock.assert_not_called()
            assert not (output / 'exported-smoke.png').exists()
        if existing == 'file':
            assert (native / 'offline_training.json').read_bytes() == b'private profile bytes'
        if cache_created:
            assert receipt['native_user_directory_side_effects']['created_files'] == ['shader_cache/cache.bin']
            assert receipt['native_user_directory_side_effects']['created_directories'] == ['shader_cache']
            assert (native / 'shader_cache/cache.bin').read_bytes() == b'synthetic cache'
        print(name + ': PASS (fully mocked native state machine)')


control('Existing private profile blocks without spawn or hashing', 2, 'BLOCKED_EXTERNALLY', existing='file')
control('Existing profile directory blocks without spawn', 2, 'BLOCKED_EXTERNALLY', existing='directory')
control('Dangling profile link blocks without spawn', 2, 'BLOCKED_EXTERNALLY', existing='dangling')
control('Second prerequisite guard blocks newly appearing temporary profile', 1, 'FAILED', second_guard=True)
control('Created cache is observed and preserved; log override supplied', 0, 'READY_FOR_INPUT_ATTEMPT', cache_created=True)
control('New profile after launch overrides readiness', 1, 'FAILED', profile_created=True)
control('Engine log error overrides readiness', 1, 'FAILED', engine_error=True)
control('Remaining owned group overrides readiness', 1, 'FAILED', cleanup_gone=False)
control('Source drift overrides readiness', 1, 'FAILED', source_changed=True)
control('Expired native-run budget fails closed', 1, 'FAILED', timeout=-1)
print('Frozen source Python compilation:', bool(compile(source, probe.__file__, 'exec')))
