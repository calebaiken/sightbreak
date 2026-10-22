"""Independent Linux-only checks of frozen ecb3070; never loads native Mac APIs."""
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
COMMIT = 'ecb30708e9b6d3765bcbe342c5887dd25f4a4cf0'


def frozen(path):
    return subprocess.check_output(['git', 'show', COMMIT + ':' + path], cwd=ROOT, text=True)


source = frozen('scripts/probe_macos_input.py')
probe = types.ModuleType('probe_macos_input')
probe.__file__ = 'git:' + COMMIT + ':scripts/probe_macos_input.py'
exec(compile(source, probe.__file__, 'exec'), probe.__dict__)
sys.modules['probe_macos_input'] = probe
print('Subject:', COMMIT, flush=True)
print('Frozen script SHA256:', hashlib.sha256(source.encode()).hexdigest(), flush=True)
print('Linux controls only; no native APIs, exports, or engine workload.', flush=True)
tests = types.ModuleType('frozen_controls')
exec(compile(frozen('scripts/test_probe_macos_input.py'), 'frozen_tests', 'exec'), tests.__dict__)
result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
assert result.wasSuccessful()
print('ctypes sizes:', {kind.__name__: ctypes.sizeof(kind) for kind in (probe.Point, probe.Size, probe.Rect)})

permissions = dict.fromkeys(('CGPreflightPostEventAccess', 'CGPreflightScreenCaptureAccess',
                             'CGPreflightListenEventAccess', 'AXIsProcessTrusted'), True)


class API:
    def preflight(self): return dict(permissions)
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


def control(name, expected_code, expected_status, *, blocked=False, profile_changed=False,
            cleanup_gone=True, source_changed=False, final_manifest_failure=False):
    permissions['CGPreflightPostEventAccess'] = not blocked
    with tempfile.TemporaryDirectory() as temporary:
        output = Path(temporary) / 'evidence'

        def launch(command, stdout, **kwargs):
            stdout.write('SIGHTBREAK_MAIN_READY screen=menu\n')
            stdout.flush()
            (output / 'exported-smoke.png').write_bytes(b'synthetic-control')
            return Child()

        manifest_calls = []

        def manifest(*args):
            manifest_calls.append(1)
            if final_manifest_failure and len(manifest_calls) > 1:
                raise RuntimeError('changed artifact control')
            return {'artifact': {'sha256': 'control'}}

        profiles = iter([{'offline_training.json': None},
                         {'offline_training.json': 'changed' if profile_changed else None}])
        sources = iter([{'revision': 'fixed'}, {'revision': 'changed' if source_changed else 'fixed'}])
        with contextlib.ExitStack() as stack:
            stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
            for target, attribute, kwargs in (
                (probe, 'MacReadOnly', {'new': API}),
                (probe, 'source', {'side_effect': lambda: next(sources)}),
                (probe, 'clean', {}),
                (probe, 'validate_record', {'side_effect': manifest}),
                (probe, 'digest', {'return_value': 'control'}),
                (probe.toolchain, 'verify_engine', {'return_value': 'mocked-version-control'}),
                (probe, 'profile_inventory', {'side_effect': lambda: next(profiles)}),
                (probe.platform, 'platform', {'return_value': 'Linux fully mocked observer control'}),
                (probe.subprocess, 'Popen', {'side_effect': launch}),
                (probe, 'reap', {'return_value': {'owned_group_gone': cleanup_gone}}),
                (probe.time, 'sleep', {}),
            ):
                stack.enter_context(patch.object(target, attribute, **kwargs))
            code = probe.run(output)
        receipt = json.loads((output / 'results.json').read_text())
        assert (code, receipt['status']) == (expected_code, expected_status), (name, code, receipt)
        assert receipt['native_input_verified'] is False
        assert receipt['input_events_posted'] == receipt['permission_requests_made'] == 0
        print(name + ': PASS (fully mocked state machine; no Mac API/export)')


control('Denied posting remains external blocker', 2, 'BLOCKED_EXTERNALLY', blocked=True)
control('Profile drift overrides readiness', 1, 'FAILED', profile_changed=True)
control('Remaining owned group overrides readiness', 1, 'FAILED', cleanup_gone=False)
control('Source drift overrides readiness', 1, 'FAILED', source_changed=True)
control('Export mutation overrides readiness', 1, 'FAILED', final_manifest_failure=True)
print('Frozen source Python compilation:', bool(compile(source, probe.__file__, 'exec')))
