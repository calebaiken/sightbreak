"""Public CoreGraphics/AppKit adapter for an owned native Mac window.

Only the reviewed menu driver should call the event methods. The adapter checks
current permissions, focus, exact window geometry and profile absence before a
down event. OS state and later native pixels, not a void post, prove delivery.
"""
import ctypes as C
from ctypes.util import find_library
import math
import os
import time

from probe_macos_input import MacReadOnly, Point, NativePrerequisiteBlocked, require_absent_profile


def same_bounds(left, right):
    return (isinstance(left, (list, tuple)) and isinstance(right, (list, tuple)) and len(left) == len(right) == 4
            and all(isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)
                    for value in [*left, *right])
            and all(abs(a - b) <= .5 for a, b in zip(left, right)))


def settings_point(capture):
    """Authorize one exact visible SETTINGS label in native full-window pixels."""
    if capture.get('passed') is not True or capture.get('scope') != 'OS window screenshot from ScreenCaptureKit; read-only helper':
        raise RuntimeError('An accepted owned OS screenshot is required before pointer input')
    if capture.get('permissions', {}).get('CGPreflightScreenCaptureAccess') is not True:
        raise NativePrerequisiteBlocked('Capture helper permission was not established')
    bounds = capture.get('bounds_points_including_chrome', [])
    if not same_bounds(bounds, capture.get('scwindow_frame_points', [])) or min(bounds[2:]) <= 0:
        raise RuntimeError('Unknown OS screenshot bounds')
    content = capture.get('filter_content_rect_points', [])
    scale = capture.get('point_pixel_scale')
    dimensions = capture.get('image_dimensions', [])
    if (not isinstance(content, list) or len(content) != 4 or not same_bounds([0, 0, *bounds[2:]], [0, 0, *content[2:]])
            or not isinstance(scale, (int, float)) or isinstance(scale, bool) or not math.isfinite(scale)
            or not 0 < scale <= 4 or dimensions != [math.ceil(content[2] * scale), math.ceil(content[3] * scale)]):
        raise RuntimeError('Unknown OS screenshot chrome/DPI mapping')
    entries = [entry for entry in capture.get('text', []) if entry.get('confidence', 0) >= .8
               and ' '.join(entry.get('text', '').upper().split()) == 'SETTINGS']
    if len(entries) != 1:
        raise RuntimeError('Expected one high-confidence exact SETTINGS target')
    box = entries[0].get('box_normalized_bottom_left', [])
    if (len(box) != 4 or not all(isinstance(value, (int, float)) and not isinstance(value, bool)
                               and math.isfinite(value) for value in box)
            or min(box[2:]) <= 0 or box[0] < 0 or box[1] < 0 or box[2] > 1 - box[0] or box[3] > 1 - box[1]):
        raise RuntimeError('SETTINGS target lies outside original screenshot')
    return (bounds[0] + (box[0] + box[2] / 2) * bounds[2],
            bounds[1] + (1 - box[1] - box[3] / 2) * bounds[3])


class MacMenuUI(MacReadOnly):
    def __init__(self, pid, window, bounds, trace):
        super().__init__()
        self.pid, self.window, self.bounds, self.trace = pid, window, bounds, trace
        self.held = set()
        self.last_pointer_point = None
        self.event_post_attempts = 0
        self.appkit = C.CDLL('/System/Library/Frameworks/AppKit.framework/AppKit')
        self.objc = C.CDLL(find_library('objc'))
        self.bind(self.objc, 'objc_getClass', [C.c_char_p], C.c_void_p)
        self.bind(self.objc, 'sel_registerName', [C.c_char_p], C.c_void_p)
        self.pool = self.message(self.message(self.cls('NSAutoreleasePool'), 'alloc'), 'init')
        self.bind(self.cg, 'CGEventCreate', [C.c_void_p], C.c_void_p)
        self.bind(self.cg, 'CGEventGetLocation', [C.c_void_p], Point)
        self.bind(self.cg, 'CGEventCreateMouseEvent', [C.c_void_p, C.c_uint32, Point, C.c_uint32], C.c_void_p)
        self.bind(self.cg, 'CGEventCreateKeyboardEvent', [C.c_void_p, C.c_uint16, C.c_bool], C.c_void_p)
        self.bind(self.cg, 'CGEventSetFlags', [C.c_void_p, C.c_uint64], None)
        self.bind(self.cg, 'CGEventPost', [C.c_uint32, C.c_void_p], None)
        self.bind(self.cf, 'CFRunLoopGetMain', [], C.c_void_p)
        self.bind(self.cf, 'CFRunLoopGetCurrent', [], C.c_void_p)
        self.bind(self.cf, 'CFRunLoopRunInMode', [C.c_void_p, C.c_double, C.c_ubyte], C.c_int32)
        self.run_loop_default_mode = C.c_void_p.in_dll(self.cf, 'kCFRunLoopDefaultMode').value
        if not self.run_loop_default_mode:
            raise RuntimeError('Public kCFRunLoopDefaultMode is unavailable')

    def cls(self, name):
        result = self.objc.objc_getClass(name.encode())
        if not result:
            raise RuntimeError('Public AppKit class unavailable: ' + name)
        return result

    def message(self, receiver, name, *arguments, returns=C.c_void_p, types=()):
        if not receiver:
            raise RuntimeError('Public AppKit receiver unavailable: ' + name)
        function = C.CFUNCTYPE(returns, C.c_void_p, C.c_void_p, *types)(
            C.cast(self.objc.objc_msgSend, C.c_void_p).value)
        return function(receiver, self.objc.sel_registerName(name.encode()), *arguments)

    def application(self):
        return self.message(self.cls('NSRunningApplication'), 'runningApplicationWithProcessIdentifier:',
                            self.pid, types=(C.c_int32,))

    def foreground_pid(self):
        workspace = self.message(self.cls('NSWorkspace'), 'sharedWorkspace')
        app = self.message(workspace, 'frontmostApplication')
        return self.message(app, 'processIdentifier', returns=C.c_int32) if app else None

    def current_foreground_pid(self):
        # NSRunningApplication documents time-varying state as persisting until
        # the main run loop advances. Guard reads must process that loop too;
        # focus_state() deliberately retains raw before/after diagnostic reads.
        self.pump_run_loop(.001)
        return self.foreground_pid()

    def diagnostics(self):
        event = self.cg.CGEventCreate(None)
        if not event:
            raise RuntimeError('CGEventCreate returned NULL during pointer observation')
        try:
            point = self.cg.CGEventGetLocation(event)
        finally:
            self.cf.CFRelease(event)
        return {'foreground_pid': self.current_foreground_pid(), 'target_pid': self.pid,
                'lmb_down': bool(self.cg.CGEventSourceButtonState(0, 0)),
                'escape_down': bool(self.cg.CGEventSourceKeyState(0, 53)),
                'pointer_points': [point.x, point.y], 'held_by_driver': sorted(self.held),
                'state_source': 'NSWorkspace/CGEventSource combined-session state/CGEventGetLocation'}

    def require_window(self):
        """Read-only window/capture guard; does not establish foreground focus."""
        require_absent_profile()
        permissions = self.preflight()
        denied = [name for name in ('CGPreflightPostEventAccess', 'CGPreflightScreenCaptureAccess') if permissions[name] is not True]
        if denied:
            raise NativePrerequisiteBlocked('Current controller permission denied: ' + ', '.join(denied))
        current = [entry for entry in self.windows(self.pid) if entry['window_id'] == self.window and entry['onscreen']]
        if len(current) != 1 or not same_bounds(current[0]['bounds_points_including_chrome'], self.bounds):
            raise RuntimeError('Owned visible window or its geometry changed before input')

    def require_target(self):
        self.require_window()
        if self.current_foreground_pid() != self.pid:
            raise RuntimeError('Exact exported process is not foreground before input')

    def focus_state(self):
        application = self.application()
        foreground = self.foreground_pid()
        state = {'foreground_pid': foreground, 'controller_pid': os.getpid(), 'target_pid': self.pid,
                 'foreground_is_controller': foreground == os.getpid(),
                 'target_window': self.window, 'pinned_bounds_points': self.bounds,
                 'target_application_available': bool(application),
                 'state_source': 'Raw NSWorkspace/NSRunningApplication before or after an explicit run-loop turn'}
        if application:
            for label, selector in (('target_active', 'isActive'), ('target_hidden', 'isHidden'),
                                    ('target_terminated', 'isTerminated'),
                                    ('target_finished_launching', 'isFinishedLaunching')):
                state[label] = bool(self.message(application, selector, returns=C.c_bool))
            state['target_activation_policy'] = self.message(application, 'activationPolicy', returns=C.c_long)
        return state

    def pump_run_loop(self, seconds):
        current, main = self.cf.CFRunLoopGetCurrent(), self.cf.CFRunLoopGetMain()
        if not current or current != main:
            raise RuntimeError('AppKit observation requires the controller main run loop')
        started = time.monotonic()
        code = self.cf.CFRunLoopRunInMode(self.run_loop_default_mode, seconds, 0)
        return {'api': 'CFRunLoopRunInMode', 'mode': 'kCFRunLoopDefaultMode',
                'requested_seconds': seconds, 'elapsed_seconds': time.monotonic() - started,
                'return_code': code, 'controller_main_run_loop': True}

    def focus(self, seconds=5):
        started = time.monotonic()
        until = started + seconds
        self.trace('focus_before_request', focus_budget_seconds=seconds, native_state=self.focus_state())
        accepted = self.message(self.application(), 'activateWithOptions:', 3, returns=C.c_bool, types=(C.c_ulong,))
        self.trace('focus_request_returned', api='NSRunningApplication.activateWithOptions:',
                   activation_options=3, request_accepted=bool(accepted), native_state=self.focus_state())
        last = None
        while time.monotonic() < until:
            before = self.focus_state()
            available = until - time.monotonic()
            if available <= 0:
                break
            pumped = self.pump_run_loop(min(.05, available))
            last = self.focus_state()
            now = time.monotonic()
            self.trace('focus_sample', focus_seconds=now - started, before_run_loop=before,
                       run_loop=pumped, after_run_loop=last)
            if now <= until and last['foreground_pid'] == self.pid:
                self.require_target()
                state = self.diagnostics()
                if time.monotonic() <= until and state['foreground_pid'] == self.pid:
                    self.trace('focus_observed', request_accepted=accepted, native_state=state)
                    return
            # A run loop with no installed sources can return immediately. Keep
            # polling bounded without turning that result into focus proof.
            idle = min(.05 - min(.05, pumped['elapsed_seconds']), until - time.monotonic())
            if idle > 0:
                time.sleep(idle)
        self.trace('focus_timeout', focus_budget_seconds=seconds, last_sample=last,
                   elapsed_seconds=time.monotonic() - started)
        raise RuntimeError('Public NSRunningApplication activation did not produce exact foreground PID')

    def neutral(self):
        state = self.diagnostics()
        if state['foreground_pid'] != self.pid:
            raise RuntimeError('Foreground process changed during neutral-state observation')
        if state['lmb_down'] or state['escape_down'] or self.held:
            raise RuntimeError('Native controls are not neutral before input transaction')
        # Modifier keys could change menu semantics. Never release a modifier
        # this driver did not press; refuse the transaction instead.
        if any(self.cg.CGEventSourceKeyState(0, code) for code in (54, 55, 56, 57, 58, 59, 60, 61, 62, 63)):
            raise RuntimeError('Native modifier key is held; no input transaction attempted')

    def post(self, event, kind):
        if not event:
            raise RuntimeError('CoreGraphics event allocation returned NULL')
        try:
            self.cg.CGEventSetFlags(event, 0)
            self.event_post_attempts += 1
            self.trace('cg_event_post_attempt', event_kind=kind, attempt=self.event_post_attempts,
                       held_by_driver=sorted(self.held))
            self.before_event_post(kind)
            self.cg.CGEventPost(0, event)  # Public kCGHIDEventTap; ordinary global OS input.
        finally:
            self.cf.CFRelease(event)

    def before_event_post(self, kind):
        """Optional controller guard after trace IO, immediately before OS post."""
        pass

    def button(self, down, point):
        if down:
            self.require_target()
            self.neutral()
            self.last_pointer_point = point
            self.held.add('lmb')
        self.post(self.cg.CGEventCreateMouseEvent(None, 1 if down else 2, Point(*point), 0), 'lmb_down' if down else 'lmb_up')
        if not down:
            self.confirm_release('lmb')

    def escape(self, down):
        if down:
            self.require_target()
            self.neutral()
            self.held.add('escape')
        self.post(self.cg.CGEventCreateKeyboardEvent(None, 53, down), 'escape_down' if down else 'escape_up')
        if not down:
            self.confirm_release('escape')

    def confirm_release(self, name):
        until = time.monotonic() + 1
        while time.monotonic() < until:
            down = (self.cg.CGEventSourceButtonState(0, 0) if name == 'lmb'
                    else self.cg.CGEventSourceKeyState(0, 53))
            if not down:
                self.held.discard(name)
                return
            time.sleep(.02)
        raise RuntimeError('Native OS state did not acknowledge owned ' + name + ' release')

    def observed_state(self, name, down, seconds=2):
        until = time.monotonic() + seconds
        while time.monotonic() < until:
            state = self.diagnostics()
            if state[name + '_down'] is down:
                if state['foreground_pid'] != self.pid:
                    raise RuntimeError('Foreground process changed during native input')
                self.trace('native_control_observed', control=name, down=down, native_state=state)
                return
            time.sleep(.02)
        raise RuntimeError('OS control state did not acknowledge ' + name + ' down=' + str(down))

    def click_settings(self, capture):
        self.require_target()
        self.neutral()
        if capture.get('owner_pid') != self.pid or capture.get('window_id') != self.window or not same_bounds(capture.get('bounds_points_including_chrome', []), self.bounds):
            raise RuntimeError('OS screenshot is not the current exact owned window')
        point = settings_point(capture)
        self.post(self.cg.CGEventCreateMouseEvent(None, 5, Point(*point), 0), 'pointer_move')
        time.sleep(.2)
        self.require_target()
        actual = self.diagnostics()['pointer_points']
        if max(abs(a - b) for a, b in zip(point, actual)) > 2:
            raise RuntimeError('OS pointer did not reach the screenshot SETTINGS coordinates')
        self.trace('settings_pointer_observed', target_points=list(point), actual_pointer_points=actual)
        self.button(True, point)
        try:
            self.observed_state('lmb', True)
            time.sleep(.15)
        finally:
            self.button(False, point)
        self.observed_state('lmb', False)

    def tap_escape(self):
        self.require_target()
        self.neutral()
        self.escape(True)
        try:
            self.observed_state('escape', True)
            time.sleep(.15)
        finally:
            self.escape(False)
        self.observed_state('escape', False)

    def release_owned(self):
        errors = []
        for name in sorted(self.held.copy()):
            try:
                if name == 'lmb':
                    self.button(False, self.last_pointer_point)
                elif name == 'escape':
                    self.escape(False)
            except BaseException as error:
                errors.append(name + ': ' + str(error))
        result = {'held_after_release': sorted(self.held), 'errors': errors}
        try:
            result['native_state'] = self.diagnostics()
        except BaseException as error:
            result['errors'].append('native_state: ' + str(error))
        return result

    def request_close(self):
        return bool(self.message(self.application(), 'terminate', returns=C.c_bool))

    def close(self):
        if self.pool:
            self.message(self.pool, 'drain', returns=None)
            self.pool = None
