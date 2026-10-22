#!/usr/bin/env python3
"""Read-only native ARM Mac input readiness; never post events or request access.

The export's smoke PNG is internal rendered output, not an OS screenshot.
READY means the observed preflights permit a later input attempt; it does not
qualify delivery, focus, gameplay, physical devices, or human play.
"""
import argparse
import ctypes as C
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import plistlib
import signal
import subprocess
import time

from build_manifest import BUILDS, OUTPUTS, clean, source, validate_record
from native_log import failed
import toolchain


class Point(C.Structure):
    _fields_ = [('x', C.c_double), ('y', C.c_double)]


class Size(C.Structure):
    _fields_ = [('width', C.c_double), ('height', C.c_double)]


class Rect(C.Structure):
    _fields_ = [('origin', Point), ('size', Size)]


class MacReadOnly:
    def __init__(self):
        if platform.system() != 'Darwin' or platform.machine() != 'arm64':
            raise RuntimeError('Requires native ARM macOS; no native-input claim from another host')
        self.cg = C.CDLL('/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics')
        self.cf = C.CDLL('/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation')
        self.ax = C.CDLL('/System/Library/Frameworks/ApplicationServices.framework/ApplicationServices')
        for name in ('CGPreflightPostEventAccess', 'CGPreflightScreenCaptureAccess',
                     'CGPreflightListenEventAccess'):
            self.bind(self.cg, name, [], C.c_bool)
        self.bind(self.ax, 'AXIsProcessTrusted', [], C.c_bool)
        self.bind(self.cg, 'CGGetActiveDisplayList', [C.c_uint32, C.POINTER(C.c_uint32), C.POINTER(C.c_uint32)], C.c_int32)
        self.bind(self.cg, 'CGDisplayBounds', [C.c_uint32], Rect)
        self.bind(self.cg, 'CGWindowListCopyWindowInfo', [C.c_uint32, C.c_uint32], C.c_void_p)
        self.bind(self.cg, 'CGEventSourceKeyState', [C.c_int32, C.c_uint16], C.c_bool)
        self.bind(self.cg, 'CGEventSourceButtonState', [C.c_int32, C.c_uint32], C.c_bool)
        self.bind(self.cf, 'CFPropertyListCreateData', [C.c_void_p, C.c_void_p, C.c_long, C.c_ulong, C.POINTER(C.c_void_p)], C.c_void_p)
        self.bind(self.cf, 'CFDataGetLength', [C.c_void_p], C.c_long)
        self.bind(self.cf, 'CFDataGetBytePtr', [C.c_void_p], C.c_void_p)
        self.bind(self.cf, 'CFRelease', [C.c_void_p], None)

    @staticmethod
    def bind(library, name, arguments, returns):
        function = getattr(library, name)
        function.argtypes, function.restype = arguments, returns

    def preflight(self):
        return {name: bool(getattr(library, name)()) for library, name in (
            (self.cg, 'CGPreflightPostEventAccess'), (self.cg, 'CGPreflightScreenCaptureAccess'),
            (self.cg, 'CGPreflightListenEventAccess'), (self.ax, 'AXIsProcessTrusted'))}

    def displays(self):
        displays, count = (C.c_uint32 * 16)(), C.c_uint32()
        error = self.cg.CGGetActiveDisplayList(16, displays, C.byref(count))
        if error or not 0 < count.value < 16:
            raise RuntimeError('CGGetActiveDisplayList error=' + str(error) + ' count=' + str(count.value))
        result = []
        for display in displays[:count.value]:
            rect = self.cg.CGDisplayBounds(display)
            bounds = [rect.origin.x, rect.origin.y, rect.size.width, rect.size.height]
            if not all(math.isfinite(value) for value in bounds) or min(bounds[2:]) <= 0:
                raise RuntimeError('CGDisplayBounds returned invalid bounds')
            result.append({'display_id': display, 'bounds_points': bounds})
        return result

    def windows(self, pid):
        # On-screen only, excluding desktop elements. Never retain another PID's
        # window name or metadata. CF's property-list serialization preserves
        # native numbers and bounds without an Objective-C bridge dependency.
        windows = self.cg.CGWindowListCopyWindowInfo(1 | 16, 0)
        if not windows:
            raise RuntimeError('CGWindowListCopyWindowInfo returned NULL')
        data, error = None, C.c_void_p()
        try:
            data = self.cf.CFPropertyListCreateData(None, windows, 100, 0, C.byref(error))
            if not data:
                raise RuntimeError('CFPropertyListCreateData returned NULL')
            length = self.cf.CFDataGetLength(data)
            if not 0 < length <= 4 * 1024 * 1024:
                raise RuntimeError('Window metadata exceeds its bounded byte budget')
            values = plistlib.loads(C.string_at(self.cf.CFDataGetBytePtr(data), length))
            return owned_windows(values, pid)
        finally:
            if data:
                self.cf.CFRelease(data)
            if error:
                self.cf.CFRelease(error)
            self.cf.CFRelease(windows)

    def controls(self):
        return {'state_source': 'CGEventSourceKeyState/CGEventSourceButtonState combined-session state',
                'escape_down': bool(self.cg.CGEventSourceKeyState(0, 53)),
                'tab_down': bool(self.cg.CGEventSourceKeyState(0, 48)),
                'lmb_down': bool(self.cg.CGEventSourceButtonState(0, 0)),
                'event_delivery_verified': False, 'keyboard_focus_verified': False}


def owned_windows(values, pid):
    result = []
    for entry in values:
        if entry.get('kCGWindowOwnerPID') != pid or entry.get('kCGWindowLayer') != 0:
            continue
        bounds = entry.get('kCGWindowBounds', {})
        rectangle = [bounds.get(name) for name in ('X', 'Y', 'Width', 'Height')]
        if (not all(isinstance(value, (int, float)) and not isinstance(value, bool)
                    and math.isfinite(value) for value in rectangle) or min(rectangle[2:]) <= 0):
            raise RuntimeError('Owned CoreGraphics window has malformed bounds')
        result.append({'window_id': entry['kCGWindowNumber'], 'owner_pid': pid,
                       'bounds_points_including_chrome': rectangle,
                       'onscreen': bool(entry.get('kCGWindowIsOnscreen'))})
    return result


def denied_permissions(preflight):
    return [name for name in ('CGPreflightPostEventAccess', 'CGPreflightScreenCaptureAccess')
            if preflight.get(name) is not True]


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def profile_inventory():
    directory = Path.home() / 'Library/Application Support/Godot/app_userdata/SIGHTBREAK'
    return {name: digest(directory / name) if (directory / name).is_file() else None
            for name in ('offline_training.json', 'offline_training.json.tmp')}


def group_exists(pid):
    try:
        os.killpg(pid, 0)
        return True
    except ProcessLookupError:
        return False


def reap(process):
    forced = []
    for signum in (signal.SIGTERM, signal.SIGKILL):
        if not group_exists(process.pid):
            break
        try:
            os.killpg(process.pid, signum)
        except ProcessLookupError:
            break
        forced.append(signal.Signals(signum).name)
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            pass
    process.poll()
    return {'pid': process.pid, 'exit_code': process.returncode, 'signals_sent': forced,
            'owned_group_gone': not group_exists(process.pid)}


def run(output, timeout=60):
    output = Path(output).resolve()
    if output.exists() and any(output.iterdir()):
        raise RuntimeError('Preserve earlier attempts; use a fresh evidence directory')
    if output.is_relative_to(toolchain.ROOT / 'game') or output.is_relative_to(BUILDS / 'macos'):
        raise RuntimeError('Keep diagnostic evidence outside source and the native export')
    output.mkdir(parents=True, exist_ok=True)
    started, process, before, saved = time.monotonic(), None, None, None
    report = {'scope': 'Read-only ARM Mac preflight; no native input or OS screenshot acceptance',
              'status': 'FAILED', 'native_input_verified': False, 'input_events_posted': 0,
              'permission_requests_made': 0, 'host': platform.platform(), 'architecture': platform.machine()}
    try:
        api = MacReadOnly()
        before = source()
        clean(before)
        manifest = validate_record('macos', before)
        executable = BUILDS / OUTPUTS['macos']
        report.update(source=before, artifact_source=manifest, executable_sha256=digest(executable),
                      engine=toolchain.verify_engine(), permissions=api.preflight(),
                      displays=api.displays(), initial_controls=api.controls())
        report['blocked_apis'] = denied_permissions(report['permissions'])
        if report['executable_sha256'] != manifest['artifact']['sha256']:
            raise RuntimeError('Export executable differs from its source-bound receipt')
        saved = profile_inventory()
        report['profile_sha256_before'] = saved
        capture = output / 'exported-smoke.png'
        report['capture_scope'] = 'Original export viewport PNG; not an OS screenshot'
        command = [str(executable), '--audio-driver', 'Dummy', '--windowed', '--resolution', '960x540',
                   '--position', '40,60', '--', '--smoke', '--capture=' + str(capture)]
        report['command'] = command
        observations = []
        report['window_observations'] = observations
        with (output / 'client.log').open('w', encoding='utf-8') as log:
            process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            report['client_pid'] = process.pid
            while process.poll() is None:
                if time.monotonic() - started >= timeout:
                    raise TimeoutError('Read-only Mac preflight exceeded ' + str(timeout) + ' seconds')
                windows = api.windows(process.pid)
                if windows and (not observations or observations[-1]['windows'] != windows):
                    observations.append({'seconds': time.monotonic() - started, 'windows': windows})
                time.sleep(.05)
        report['normal_exit_code'] = process.returncode
        report['final_controls'] = api.controls()
        text = (output / 'client.log').read_text(encoding='utf-8', errors='replace')
        if process.returncode or failed(text) or 'SIGHTBREAK_MAIN_READY screen=menu' not in text or not capture.is_file():
            raise RuntimeError('Exported Mac smoke failed; retain raw log and startup capture')
        if not any(window['onscreen'] for entry in observations for window in entry['windows']):
            raise RuntimeError('No visible layer-zero window observed for the exact exported PID')
        report['capture_sha256'] = digest(capture)
        report['status'] = 'BLOCKED_EXTERNALLY' if report['blocked_apis'] else 'READY_FOR_INPUT_ATTEMPT'
    except BaseException as error:
        report['failure'] = {'type': type(error).__name__, 'message': str(error)}
        report['status'] = 'FAILED'
    finally:
        try:
            report['cleanup'] = reap(process) if process is not None else {'owned_group_gone': True, 'process_started': False}
            if not report['cleanup']['owned_group_gone']:
                raise RuntimeError('Owned native process group remains alive after cleanup')
            if saved is not None:
                report['profile_sha256_after'] = profile_inventory()
                report['profile_unchanged'] = report['profile_sha256_after'] == saved
                if not report['profile_unchanged']:
                    raise RuntimeError('Native player profile changed during read-only launch')
            if before is not None:
                report['source_unchanged'] = source() == before
                validate_record('macos', before)
                if not report['source_unchanged']:
                    raise RuntimeError('Source changed during Mac preflight')
        except BaseException as error:
            report['finalization_failure'] = {'type': type(error).__name__, 'message': str(error)}
            report['status'] = 'FAILED'
        report['seconds'] = time.monotonic() - started
        (output / 'results.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))
    return 0 if report['status'] == 'READY_FOR_INPUT_ATTEMPT' else 2 if report['status'] == 'BLOCKED_EXTERNALLY' else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    arguments = parser.parse_args()
    def interrupted(signum, _frame):
        raise SystemExit('Mac preflight interrupted by signal ' + str(signum))
    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    return run(arguments.output)


if __name__ == '__main__':
    raise SystemExit(main())
