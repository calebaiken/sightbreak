"""Declared single AppKit focus/ordinary close; no event creation or AX action."""
import ctypes as C
from ctypes.util import find_library
import os
import time

from macos_ax_contract import require_capture, require_owned
from macos_ordinary_input import OwnedWindowChanged
from probe_macos_input import MacReadOnly


SELECTORS = ('alloc', 'init', 'drain', 'runningApplicationWithProcessIdentifier:',
             'sharedWorkspace', 'frontmostApplication', 'processIdentifier',
             'activateWithOptions:', 'terminate')
CLASSES = ('NSAutoreleasePool', 'NSRunningApplication', 'NSWorkspace')


class AXWindow(MacReadOnly):
    def __init__(self, pid, window, bounds, trace, private_guard):
        super().__init__()
        self.pid, self.window, self.bounds = pid, window, list(bounds) if bounds is not None else None
        self.trace, self.private_guard = trace, private_guard
        self.event_post_attempts, self.focus_requests, self.pinned = 0, 0, False
        self.appkit = C.CDLL('/System/Library/Frameworks/AppKit.framework/AppKit')
        self.objc = C.CDLL(find_library('objc'))
        self.bind(self.objc, 'objc_getClass', [C.c_char_p], C.c_void_p)
        self.bind(self.objc, 'sel_registerName', [C.c_char_p], C.c_void_p)
        self.bind(self.cf, 'CFRunLoopGetMain', [], C.c_void_p)
        self.bind(self.cf, 'CFRunLoopGetCurrent', [], C.c_void_p)
        self.bind(self.cf, 'CFRunLoopRunInMode', [C.c_void_p, C.c_double, C.c_ubyte], C.c_int32)
        self.run_loop_default_mode = C.c_void_p.in_dll(self.cf, 'kCFRunLoopDefaultMode').value
        if not self.run_loop_default_mode:
            raise RuntimeError('Public main-run-loop mode unavailable')
        self.pool = self.message(self.message(self.cls('NSAutoreleasePool'), 'alloc'), 'init')

    def cls(self, name):
        if name not in CLASSES:
            raise RuntimeError('AppKit class outside diagnostic allowlist')
        result = self.objc.objc_getClass(name.encode())
        if not result:
            raise RuntimeError('Required public AppKit class unavailable')
        return result

    def message(self, receiver, selector, *arguments, returns=C.c_void_p, types=()):
        if not receiver or selector not in SELECTORS:
            raise RuntimeError('Unavailable receiver or selector outside diagnostic allowlist')
        function = C.CFUNCTYPE(returns, C.c_void_p, C.c_void_p, *types)(
            C.cast(self.objc.objc_msgSend, C.c_void_p).value)
        return function(receiver, self.objc.sel_registerName(selector.encode()), *arguments)

    def application(self):
        return self.message(self.cls('NSRunningApplication'), 'runningApplicationWithProcessIdentifier:',
                            self.pid, types=(C.c_int32,))

    def foreground_pid(self):
        workspace = self.message(self.cls('NSWorkspace'), 'sharedWorkspace')
        application = self.message(workspace, 'frontmostApplication')
        return self.message(application, 'processIdentifier', returns=C.c_int32) if application else None

    def pump(self, seconds):
        current = self.cf.CFRunLoopGetCurrent()
        if not current or current != self.cf.CFRunLoopGetMain():
            raise RuntimeError('AppKit requires the controller main run loop')
        return self.cf.CFRunLoopRunInMode(self.run_loop_default_mode, seconds, 0)

    def state(self):
        return {'foreground_pid': self.foreground_pid(), 'target_pid': self.pid,
                'controller_pid': os.getpid(), 'event_post_attempts': self.event_post_attempts,
                'focus_requests': self.focus_requests, 'geometry_pinned': self.pinned,
                'controls': self.controls()}

    def require_window(self):
        if self.window is None or self.bounds is None:
            raise RuntimeError('Close-only adapter cannot observe or pin a window')
        self.private_guard()
        rows = self.windows(self.pid)
        self.trace('owned_window_guard', observed_owned_layer_zero_windows=rows,
                   expected_window=self.window, expected_bounds_points=self.bounds,
                   geometry_pinned=self.pinned, event_post_attempts=0)
        try:
            require_owned(rows, self.pid, self.window, self.bounds)
        except RuntimeError as error:
            raise OwnedWindowChanged(str(error)) from error
        if self.event_post_attempts:
            raise RuntimeError('Read-only diagnostic forbids all event attempts')
        return rows

    def require_target(self):
        rows = self.require_window()
        self.pump(.001)
        if self.foreground_pid() != self.pid:
            raise RuntimeError('Pinned exported client is no longer foreground')
        return rows

    def focus(self, seconds):
        if self.focus_requests or self.pinned or not 0 < seconds <= 5:
            raise RuntimeError('Exactly one bounded pre-pin focus request is allowed')
        self.require_window()
        until = time.monotonic() + seconds
        self.focus_requests += 1
        self.trace('focus_before_request', native_state=self.state(), budget_seconds=seconds)
        accepted = self.message(self.application(), 'activateWithOptions:', 3,
                                returns=C.c_bool, types=(C.c_ulong,))
        self.trace('focus_request_returned', request_accepted=bool(accepted), native_state=self.state())
        while time.monotonic() < until:
            self.require_window()
            self.pump(min(.05, max(0, until - time.monotonic())))
            if self.foreground_pid() == self.pid and time.monotonic() < until:
                self.require_target()
                if time.monotonic() < until:
                    self.trace('focus_observed', native_state=self.state())
                    return
            available = until - time.monotonic()
            if available > 0:
                time.sleep(min(.02, available))
        raise TimeoutError('Original single focus budget exceeded')

    def pin(self, capture):
        if self.pinned or self.event_post_attempts or self.focus_requests != 1:
            raise RuntimeError('Fresh geometry can be pinned once after the sole focus request')
        require_capture(capture, self.pid, self.window, self.bounds)
        self.require_target()
        self.pinned = True
        self.trace('read_only_geometry_pinned', window_id=self.window,
                   bounds_points_including_chrome=self.bounds, native_state=self.state())

    def request_close(self):
        return bool(self.message(self.application(), 'terminate', returns=C.c_bool))

    def close(self):
        if self.pool:
            self.message(self.pool, 'drain', returns=None)
            self.pool = None
