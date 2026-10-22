#!/usr/bin/env python3
"""Drive an actual Linux/Windows export through native input and a real authority.

Requires Pillow and a graphical desktop. Linux uses an isolated X11/XTest/Xvfb
session. Windows uses its desktop window, native SendInput and client-area captures.
The exported template cannot execute external --script drivers. Only the source
Godot process executes the fixture. This checks real exported menu/admission,
mouse firing, reload and clean engine teardown. Keyboard mode requires the
server to observe an R-key reload command; authority mode triggers reload in the
source fixture and leaves keyboard input unverified. No phone performance claim.
"""
import argparse
import ctypes as C
from ctypes.util import find_library
import hashlib
import json
import os
import platform
import signal
from pathlib import Path
import re
import shutil
import subprocess
import threading
import time
from urllib.parse import quote

from PIL import Image, ImageGrab
from build_manifest import BUILDS, OUTPUTS, source, validate_record
import toolchain
from native_log import failed as native_log_failed

ROOT = Path(__file__).resolve().parents[1]


class X11ProtocolError(RuntimeError):
    def __init__(self, operation, errors):
        self.errors = errors
        super().__init__('X11 ' + operation + ' failed: ' + json.dumps(errors))


class NativeWindowUnavailable(X11ProtocolError):
    """A specific target disappeared during a checked native request."""


class _XErrorEvent(C.Structure):
    _fields_ = [('type', C.c_int), ('display', C.c_void_p), ('resourceid', C.c_ulong),
                ('serial', C.c_ulong), ('error_code', C.c_ubyte),
                ('request_code', C.c_ubyte), ('minor_code', C.c_ubyte)]


_X_ERROR_HANDLER = C.CFUNCTYPE(C.c_int, C.c_void_p, C.POINTER(_XErrorEvent))
_X_ERROR_LOCK = threading.RLock()  # XSetErrorHandler is process-wide.


class NativeUI:
    def __init__(self, display):
        self.display = display
        self.x = C.CDLL(find_library('X11'))
        self.t = C.CDLL(find_library('Xtst'))
        self.x.XOpenDisplay.argtypes = [C.c_char_p]
        self.x.XOpenDisplay.restype = C.c_void_p
        self.x.XDefaultRootWindow.argtypes = [C.c_void_p]
        self.x.XDefaultRootWindow.restype = C.c_ulong
        self.x.XQueryTree.argtypes = [C.c_void_p, C.c_ulong, C.POINTER(C.c_ulong), C.POINTER(C.c_ulong), C.POINTER(C.POINTER(C.c_ulong)), C.POINTER(C.c_uint)]
        self.x.XFetchName.argtypes = [C.c_void_p, C.c_ulong, C.POINTER(C.c_char_p)]
        self.x.XGetGeometry.argtypes = [C.c_void_p, C.c_ulong, C.POINTER(C.c_ulong), C.POINTER(C.c_int), C.POINTER(C.c_int), C.POINTER(C.c_uint), C.POINTER(C.c_uint), C.POINTER(C.c_uint), C.POINTER(C.c_uint)]
        self.x.XSetInputFocus.argtypes = [C.c_void_p, C.c_ulong, C.c_int, C.c_ulong]
        self.x.XGetInputFocus.argtypes = [C.c_void_p, C.POINTER(C.c_ulong), C.POINTER(C.c_int)]
        self.x.XSetErrorHandler.argtypes = [C.c_void_p]
        self.x.XSetErrorHandler.restype = C.c_void_p
        self.x.XFlush.argtypes = [C.c_void_p]
        self.x.XKeysymToKeycode.argtypes = [C.c_void_p, C.c_ulong]
        self.x.XKeysymToKeycode.restype = C.c_uint
        self.x.XStringToKeysym.argtypes = [C.c_char_p]
        self.x.XStringToKeysym.restype = C.c_ulong
        self.x.XFree.argtypes = [C.c_void_p]
        self.x.XCloseDisplay.argtypes = [C.c_void_p]
        self.t.XTestFakeMotionEvent.argtypes = [C.c_void_p, C.c_int, C.c_int, C.c_int, C.c_ulong]
        self.t.XTestFakeButtonEvent.argtypes = [C.c_void_p, C.c_uint, C.c_int, C.c_ulong]
        self.t.XTestFakeKeyEvent.argtypes = [C.c_void_p, C.c_uint, C.c_int, C.c_ulong]
        self.d = self.x.XOpenDisplay(display.encode())
        self.window = None
        if not self.d:
            raise RuntimeError('Cannot open native display ' + display)
        # A desktop WM normally creates these atoms. Bare Xvfb does not, while
        # Godot 4.7.2 looks up WM_DELETE_WINDOW with only_if_exists=True at startup.
        # Construct this controller before launching the client so its cached
        # close protocol is the actual standard atom, rather than None.
        self.x.XInternAtom.argtypes = [C.c_void_p, C.c_char_p, C.c_int]
        self.x.XInternAtom.restype = C.c_ulong
        self.x.XSync.argtypes = [C.c_void_p, C.c_int]
        self.wm_delete = self._x_call(self.x.XInternAtom, b'WM_DELETE_WINDOW', 0)
        self.wm_protocols = self._x_call(self.x.XInternAtom, b'WM_PROTOCOLS', 0)

    def _x_call(self, function, *arguments, window=None, missing_requests=()):
        """Drain and check errors while the callback is alive; never raise in C."""
        if self.d is None:
            raise RuntimeError('Native display is closed')
        errors = []
        @_X_ERROR_HANDLER
        def capture(display, pointer):
            event = pointer.contents
            errors.append({'display': display, 'resourceid': event.resourceid,
                           'serial': event.serial, 'error_code': event.error_code,
                           'request_code': event.request_code, 'minor_code': event.minor_code})
            return 0
        with _X_ERROR_LOCK:
            previous = self.x.XSetErrorHandler(C.cast(capture, C.c_void_p))
            try:
                # A pending unrelated error must not inherit this call's missing-window exception.
                self.x.XSync(self.d, 0)
                if errors:
                    raise X11ProtocolError('pending requests', errors)
                result = function(self.d, *arguments)
                self.x.XSync(self.d, 0)
            finally:
                self.x.XSetErrorHandler(previous)
        if errors:
            # BadDrawable is the missing-resource reply for GetGeometry; all
            # other recoverable requests below specifically require BadWindow.
            missing = window is not None and all(
                error['display'] == self.d and error['resourceid'] == window
                and (error['error_code'], error['request_code']) in missing_requests
                for error in errors)
            error_type = NativeWindowUnavailable if missing else X11ProtocolError
            raise error_type('window request' if missing else getattr(function, '__name__', 'request'), errors)
        return result

    def window_geometry(self, window=None):
        target = self.window if window is None else window
        if target is None:
            raise RuntimeError('No native window selected for geometry')
        root, x, y = C.c_ulong(), C.c_int(), C.c_int()
        width, height, border, depth = C.c_uint(), C.c_uint(), C.c_uint(), C.c_uint()
        if not self._x_call(self.x.XGetGeometry, target, C.byref(root), C.byref(x), C.byref(y),
                            C.byref(width), C.byref(height), C.byref(border), C.byref(depth),
                            window=target, missing_requests=((9, 14),)):
            raise RuntimeError('Cannot inspect native window geometry')
        return x.value, y.value, width.value, height.value

    def focus_game(self):
        self.window = None
        root, parent, count = C.c_ulong(), C.c_ulong(), C.c_uint()
        children = C.POINTER(C.c_ulong)()
        if not self._x_call(self.x.XQueryTree, self.x.XDefaultRootWindow(self.d),
                            C.byref(root), C.byref(parent), C.byref(children), C.byref(count)):
            raise RuntimeError('Cannot enumerate native windows')
        largest, selected = 0, None
        try:
            for index in range(count.value):
                name = C.c_char_p()
                try:
                    self._x_call(self.x.XFetchName, children[index], C.byref(name),
                                 window=children[index], missing_requests=((3, 20),))
                    if not name.value or b'SIGHTBREAK' not in name.value:
                        continue
                    _, _, width, height = self.window_geometry(children[index])
                    if width * height > largest:
                        largest, selected = width * height, children[index]
                except NativeWindowUnavailable:
                    continue
                finally:
                    if name:
                        self.x.XFree(name)
        finally:
            if children:
                self.x.XFree(children)
        if selected is None:
            return False
        try:
            self._x_call(self.x.XSetInputFocus, selected, 1, 0,
                         window=selected, missing_requests=((3, 42),))
        except NativeWindowUnavailable:
            return False
        focused, revert = C.c_ulong(), C.c_int()
        self._x_call(self.x.XGetInputFocus, C.byref(focused), C.byref(revert))
        if focused.value != selected:
            return False
        self.window = selected
        return True

    def button(self, down):
        self.t.XTestFakeButtonEvent(self.d, 1, int(down), 0)
        self.x.XFlush(self.d)

    def key(self, name, down):
        code = self.x.XKeysymToKeycode(self.d, self.x.XStringToKeysym(name.encode()))
        if not code:
            raise RuntimeError('No native keycode for ' + name)
        self.t.XTestFakeKeyEvent(self.d, code, int(down), 0)
        self.x.XFlush(self.d)

    def click(self, x, y):
        self.t.XTestFakeMotionEvent(self.d, 0, x, y, 0)
        # Let the native window consume the pointer move before the click.
        # Same-batch motion/button events can hit the prior hover target.
        self.x.XFlush(self.d)
        time.sleep(.25)
        self.button(True)
        time.sleep(.2)
        self.button(False)

    def capture(self, path):
        image = ImageGrab.grab(xdisplay=self.display)
        if image.size != (1280, 720):
            raise RuntimeError('Expected isolated 1280x720 display, got ' + str(image.size))
        image.save(path)

    def menu_visible(self):
        # The connect page also has a crimson button at y=299. Sample the
        # deploy button's lower edge, outside the connect button's rectangle.
        pixel = ImageGrab.grab(xdisplay=self.display).getpixel((450, 340))
        return pixel[0] > 80 and pixel[0] > pixel[1] * 1.5

    def relative_motion(self, dx, dy):
        self.t.XTestFakeRelativeMotionEvent.argtypes = [C.c_void_p, C.c_int, C.c_int, C.c_ulong]
        self.t.XTestFakeRelativeMotionEvent(self.d, dx, dy, 0)
        self.x.XFlush(self.d)

    def diagnostics(self):
        """Observe native focus/button/key state without changing focus or input."""
        focused, revert = C.c_ulong(), C.c_int()
        self._x_call(self.x.XGetInputFocus, C.byref(focused), C.byref(revert))
        self.x.XQueryKeymap.argtypes = [C.c_void_p, C.c_void_p]
        keys = (C.c_ubyte * 32)()
        self._x_call(self.x.XQueryKeymap, keys)
        states = {}
        for name in ('r', 'd', 'w'):
            code = self.x.XKeysymToKeycode(self.d, self.x.XStringToKeysym(name.encode()))
            states[name] = bool(code and keys[code // 8] & (1 << (code % 8)))
        self.x.XQueryPointer.argtypes = [C.c_void_p, C.c_ulong, C.POINTER(C.c_ulong), C.POINTER(C.c_ulong), C.POINTER(C.c_int), C.POINTER(C.c_int), C.POINTER(C.c_int), C.POINTER(C.c_int), C.POINTER(C.c_uint)]
        root, child, rx, ry, wx, wy, mask = C.c_ulong(), C.c_ulong(), C.c_int(), C.c_int(), C.c_int(), C.c_int(), C.c_uint()
        pointer = self._x_call(self.x.XQueryPointer, self.x.XDefaultRootWindow(self.d), C.byref(root), C.byref(child), C.byref(rx), C.byref(ry), C.byref(wx), C.byref(wy), C.byref(mask))
        window = getattr(self, 'window', None)
        if window is not None:
            try:
                self.window_geometry(window)
            except NativeWindowUnavailable:
                self.window = window = None
        return {'target_window': window, 'foreground_window': focused.value,
                'target_focused': window is not None and focused.value == window,
                'lmb_down': bool(mask.value & (1 << 8)) if pointer else None,
                'keys_down': states, 'state_source': 'XGetInputFocus/XQueryPointer/XQueryKeymap'}

    def request_close(self):
        if self.window is None:
            raise RuntimeError('No native window selected for close')
        class MessageData(C.Union):
            _fields_ = [('b', C.c_char * 20), ('s', C.c_short * 10), ('l', C.c_long * 5)]
        class ClientMessage(C.Structure):
            _fields_ = [('type', C.c_int), ('serial', C.c_ulong), ('send_event', C.c_int),
                        ('display', C.c_void_p), ('window', C.c_ulong), ('message_type', C.c_ulong),
                        ('format', C.c_int), ('data', MessageData)]
        class Event(C.Union):
            _fields_ = [('message', ClientMessage), ('padding', C.c_long * 24)]
        self.x.XGetWMProtocols.argtypes = [C.c_void_p, C.c_ulong, C.POINTER(C.POINTER(C.c_ulong)), C.POINTER(C.c_int)]
        protocols, count = C.POINTER(C.c_ulong)(), C.c_int()
        advertised = self._x_call(self.x.XGetWMProtocols, self.window, C.byref(protocols), C.byref(count),
                                  window=self.window, missing_requests=((3, 20),))
        try:
            supports_close = advertised and self.wm_delete in [protocols[index] for index in range(count.value)]
        finally:
            if protocols:
                self.x.XFree(protocols)
        if not supports_close:
            raise RuntimeError('WM_DELETE_WINDOW is not advertised; create NativeUI before launching Godot on bare Xvfb')
        self.x.XSendEvent.argtypes = [C.c_void_p, C.c_ulong, C.c_int, C.c_long, C.POINTER(Event)]
        event = Event()
        event.message.type = 33  # ClientMessage
        event.message.display = self.d
        event.message.window = self.window
        event.message.message_type = self.wm_protocols
        event.message.format = 32
        event.message.data.l[0] = self.wm_delete
        event.message.data.l[1] = 0  # CurrentTime
        if not self._x_call(self.x.XSendEvent, self.window, 0, 0, C.byref(event),
                            window=self.window, missing_requests=((3, 25),)):
            raise RuntimeError('XSendEvent rejected the desktop close request')

    def close(self):
        if self.d is not None:
            try:
                self._x_call(self.x.XSync, 0)
            finally:
                self.x.XCloseDisplay(self.d)
                self.d = self.window = None


class WinUI:
    """Reference coordinates are 1280x720; captures retain actual client pixels."""
    def __init__(self, pid=None):
        if os.name != 'nt':
            raise RuntimeError('WinUI requires native Windows')
        self.pid = pid
        self.window = None
        self.user = C.WinDLL('user32', use_last_error=True)
        self.user.SetProcessDPIAware()
        self.user.GetWindowTextLengthW.argtypes = [C.c_void_p]
        self.user.GetWindowTextW.argtypes = [C.c_void_p, C.c_wchar_p, C.c_int]
        self.user.IsWindowVisible.argtypes = [C.c_void_p]
        self.user.GetWindowThreadProcessId.argtypes = [C.c_void_p, C.POINTER(C.c_uint32)]
        self.user.GetClientRect.argtypes = [C.c_void_p, C.c_void_p]
        self.user.ClientToScreen.argtypes = [C.c_void_p, C.c_void_p]
        self.user.SetForegroundWindow.argtypes = [C.c_void_p]
        self.user.GetForegroundWindow.restype = C.c_void_p
        self.user.ShowWindow.argtypes = [C.c_void_p, C.c_int]
        self.user.SetWindowPos.argtypes = [C.c_void_p, C.c_void_p, C.c_int, C.c_int, C.c_int, C.c_int, C.c_uint]
        self.user.PostMessageW.argtypes = [C.c_void_p, C.c_uint, C.c_size_t, C.c_ssize_t]
        self.user.SendInput.argtypes = [C.c_uint, C.c_void_p, C.c_int]
        self.user.MapVirtualKeyW.argtypes = [C.c_uint, C.c_uint]
        self.user.GetAsyncKeyState.argtypes = [C.c_int]
        self.user.GetAsyncKeyState.restype = C.c_short
        self.width = min(1280, self.user.GetSystemMetrics(0) - 40,
                         (self.user.GetSystemMetrics(1) - 100) * 16 // 9)
        self.width = self.width // 16 * 16
        self.height = self.width * 9 // 16
        if self.width < 640:
            raise RuntimeError('Windows desktop is too small for the native input test')

    def focus_game(self):
        callback_type = C.WINFUNCTYPE(C.c_int, C.c_void_p, C.c_ssize_t)
        candidates = []
        @callback_type
        def visit(window, _context):
            pid = C.c_uint32()
            self.user.GetWindowThreadProcessId(window, C.byref(pid))
            if pid.value != self.pid or not self.user.IsWindowVisible(window):
                return 1
            title = C.create_unicode_buffer(self.user.GetWindowTextLengthW(window) + 1)
            self.user.GetWindowTextW(window, title, len(title))
            if 'SIGHTBREAK' in title.value:
                rect = (C.c_int32 * 4)()
                if self.user.GetClientRect(window, C.byref(rect)):
                    candidates.append(((rect[2]-rect[0]) * (rect[3]-rect[1]), window))
            return 1
        self.user.EnumWindows.argtypes = [callback_type, C.c_ssize_t]
        self.user.EnumWindows(visit, 0)
        if not candidates:
            return False
        window = max(candidates)[1]
        if window != self.window:
            self.user.ShowWindow(window, 9)  # SW_RESTORE
            self.user.SetWindowPos(window, None, 0, 0, 0, 0, 0x1 | 0x4 | 0x10)
        self.window = window
        self.user.SetForegroundWindow(window)
        return self.user.GetForegroundWindow() == window

    def bounds(self):
        rect = (C.c_int32 * 4)()
        origin = (C.c_int32 * 2)()
        if not self.window or not self.user.GetClientRect(self.window, C.byref(rect)) or not self.user.ClientToScreen(self.window, C.byref(origin)):
            raise RuntimeError('Cannot locate native Windows client area')
        width, height = rect[2] - rect[0], rect[3] - rect[1]
        if width <= 0 or height <= 0 or abs(width / height - 16 / 9) > .02:
            raise RuntimeError('Expected a visible 16:9 Windows client area')
        bounds = (origin[0], origin[1], origin[0] + width, origin[1] + height)
        if bounds[0] < 0 or bounds[1] < 0 or bounds[2] > self.user.GetSystemMetrics(0) or bounds[3] > self.user.GetSystemMetrics(1):
            raise RuntimeError('Windows client is clipped by desktop bounds')
        return bounds

    def lower_owned_render_priority(self, process):
        """Opt-in hosted offline QA resource isolation; never a game setting."""
        pid = C.c_uint32()
        if (not isinstance(process, subprocess.Popen) or process.poll() is not None
                or self.pid != process.pid or not self.window
                or not self.user.GetWindowThreadProcessId(self.window, C.byref(pid))
                or pid.value != process.pid):
            raise RuntimeError('Hosted render priority requires the live owned child window/PID')
        kernel = C.WinDLL('kernel32', use_last_error=True)
        kernel.OpenProcess.argtypes = [C.c_uint32, C.c_int, C.c_uint32]
        kernel.OpenProcess.restype = C.c_void_p
        kernel.GetPriorityClass.argtypes = [C.c_void_p]
        kernel.GetPriorityClass.restype = C.c_uint32
        kernel.SetPriorityClass.argtypes = [C.c_void_p, C.c_uint32]
        kernel.SetPriorityClass.restype = C.c_int
        kernel.CloseHandle.argtypes = [C.c_void_p]
        kernel.CloseHandle.restype = C.c_int
        handle = kernel.OpenProcess(0x1000 | 0x200, False, process.pid)
        if not handle:
            raise C.WinError(C.get_last_error())
        try:
            before = kernel.GetPriorityClass(handle)
            if not before or not kernel.SetPriorityClass(handle, 0x4000):
                raise C.WinError(C.get_last_error())
            current = kernel.GetPriorityClass(handle)
            if current != 0x4000:
                raise RuntimeError('Owned hosted render priority was not applied')
            return {'pid': process.pid, 'window_pid': pid.value, 'before_priority_class': before,
                    'current_priority_class': current,
                    'scope': 'Opt-in Windows hosted offline QA only; owned child below-normal, no affinity/rules/time-scale changes'}
        finally:
            kernel.CloseHandle(handle)

    def image(self):
        return ImageGrab.grab(bbox=self.bounds(), all_screens=True)

    def diagnostics(self):
        """Read actual OS state; SendInput success alone does not prove delivery."""
        foreground = self.user.GetForegroundWindow()
        return {'target_window': self.window, 'foreground_window': foreground,
                'target_focused': self.window is not None and foreground == self.window,
                'lmb_down': bool(self.user.GetAsyncKeyState(0x01) & 0x8000),
                'keys_down': {name: bool(self.user.GetAsyncKeyState(ord(name.upper())) & 0x8000)
                              for name in ('r', 'd', 'w')},
                'state_source': 'GetForegroundWindow/GetAsyncKeyState; zero is not delivery proof'}

    def _input(self, kind, dx=0, dy=0, flags=0, scan=0):
        class Mouse(C.Structure):
            _fields_ = [('dx', C.c_int32), ('dy', C.c_int32), ('data', C.c_uint32),
                        ('flags', C.c_uint32), ('time', C.c_uint32), ('extra', C.c_size_t)]
        class Keyboard(C.Structure):
            _fields_ = [('vk', C.c_uint16), ('scan', C.c_uint16), ('flags', C.c_uint32),
                        ('time', C.c_uint32), ('extra', C.c_size_t)]
        class InputData(C.Union):
            _fields_ = [('mouse', Mouse), ('key', Keyboard)]
        class Input(C.Structure):
            _fields_ = [('type', C.c_uint32), ('data', InputData)]
        event = Input()
        event.type = kind
        if kind == 0:
            event.data.mouse = Mouse(dx, dy, 0, flags, 0, 0)
        else:
            event.data.key = Keyboard(0, scan, flags, 0, 0)
        if self.user.SendInput(1, C.byref(event), C.sizeof(event)) != 1:
            raise C.WinError(C.get_last_error())

    def key(self, name, down):
        vk = {'Escape': 0x1b, 'Tab': 0x09, 'Return': 0x0d, 'space': 0x20}.get(name)
        if vk is None and len(name) == 1 and name.isascii():
            vk = ord(name.upper())
        if vk is None:
            raise RuntimeError('Unknown native Windows key: ' + name)
        scan = self.user.MapVirtualKeyW(vk, 0)
        if not scan:
            raise RuntimeError('Cannot map native Windows key: ' + name)
        self._input(1, flags=0x8 | (0 if down else 0x2), scan=scan)

    def button(self, down):
        self._input(0, flags=0x2 if down else 0x4)

    def relative_motion(self, dx, dy):
        self._input(0, dx=dx, dy=dy, flags=0x1)

    def click(self, x, y):
        left, top, right, bottom = self.bounds()
        self.user.SetCursorPos(left + int(x * (right-left) / 1280), top + int(y * (bottom-top) / 720))
        time.sleep(.25)
        self.button(True)
        time.sleep(.2)
        self.button(False)

    def capture(self, path):
        self.image().save(path)

    def menu_visible(self):
        image = self.image()
        pixel = image.getpixel((int(450 * image.width / 1280), int(340 * image.height / 720)))
        return pixel[0] > 80 and pixel[0] > pixel[1] * 1.5

    def request_close(self):
        if not self.user.PostMessageW(self.window, 0x10, 0, 0):  # WM_CLOSE
            raise C.WinError(C.get_last_error())

    def close(self):
        pass


def windows_job():
    """Own descendants before launching; retain the handle until this process exits."""
    kernel = C.WinDLL('kernel32', use_last_error=True)
    kernel.CreateJobObjectW.restype = C.c_void_p
    kernel.GetCurrentProcess.restype = C.c_void_p
    kernel.SetInformationJobObject.argtypes = [C.c_void_p, C.c_int, C.c_void_p, C.c_uint]
    kernel.AssignProcessToJobObject.argtypes = [C.c_void_p, C.c_void_p]
    kernel.QueryInformationJobObject.argtypes = [C.c_void_p, C.c_int, C.c_void_p, C.c_uint, C.c_void_p]
    job = kernel.CreateJobObjectW(None, None)
    limits = C.create_string_buffer(144)  # x64 JOBOBJECT_EXTENDED_LIMIT_INFORMATION
    C.c_uint32.from_buffer(limits, 16).value = 0x2000  # KILL_ON_JOB_CLOSE
    if not job or not kernel.SetInformationJobObject(job, 9, limits, len(limits)) or not kernel.AssignProcessToJobObject(job, kernel.GetCurrentProcess()):
        raise C.WinError(C.get_last_error())
    return kernel, job


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=BUILDS / 'verification/integration')
    parser.add_argument('--target', choices=('linux', 'windows'), default='windows' if os.name == 'nt' else 'linux')
    parser.add_argument('--display', default=':101', help='A free isolated X11 display (Linux only)')
    parser.add_argument('--xvfb', default=os.environ.get('XVFB_BIN') or shutil.which('Xvfb'))
    parser.add_argument('--quit-after', type=int, default=0, help='Optional premature-exit control; normal flow closes the window after completion')
    parser.add_argument('--timeout', type=float, default=180, help='Whole-flow wall-clock budget, with separate bounded failure cleanup')
    parser.add_argument('--visit-armory', action='store_true', help='Capture exported inventory navigation; screenshots require visual inspection')
    parser.add_argument('--reload-mode', choices=('authority', 'keyboard'), default='keyboard')
    parser.add_argument('--input-schedule', choices=('legacy', 'release-first'), default='legacy',
                        help='Diagnostic comparison only: retain legacy capture while LMB is held, or capture after release; qualification gates are unchanged')
    parser.add_argument('--fire-capture-delay', type=float, default=0,
                        help='Explicit synthetic capture pressure in seconds (0..10); delays only the fire screenshot and is recorded separately from spontaneous failures')
    args = parser.parse_args()
    if args.target != ('windows' if os.name == 'nt' else 'linux') or platform.system() not in ('Linux', 'Windows'):
        parser.error('Execute the selected export on its matching native Linux/Windows host; macOS input is UNVERIFIED')
    if args.quit_after < 0 or args.timeout <= 0 or not 0 <= args.fire_capture_delay <= 10:
        parser.error('Frame budget must be nonnegative, timeout positive, and synthetic fire-capture delay between 0 and 10')
    display_socket = None
    if args.target == 'linux':
        if not args.xvfb:
            parser.error('Set --xvfb or XVFB_BIN to the Xvfb executable')
        if not re.fullmatch(r':[0-9]+', args.display):
            parser.error('Use a local numbered display such as :101')
        display_socket = Path('/tmp/.X11-unix/X' + args.display[1:])
        if display_socket.exists():
            parser.error('Display is already in use: ' + args.display)
    output = args.output.resolve()
    if output.exists() and any(output.iterdir()):
        parser.error('Use a new or empty evidence directory; earlier attempts are preserved')
    output.mkdir(parents=True, exist_ok=True)
    executable = BUILDS / OUTPUTS[args.target]
    processes, logs, commands, ui = [], [], [], None
    manifest = source_before = None
    result = {'passed': False, 'target': args.target, 'host': platform.platform(),
              'input_schedule': args.input_schedule, 'synthetic_fire_capture_delay_seconds': args.fire_capture_delay,
              'qualification_note': 'Any nonzero synthetic capture pressure is a diagnostic experiment, not physical performance or a spontaneous Windows failure'}
    (output / 'results.json').write_text(json.dumps(result, indent=2) + '\n')
    started = time.monotonic()
    deadline = started + args.timeout
    job = None
    held_keys = set()
    fire_down = False
    capture_dimensions = []
    events = []

    def interrupted(signum, _frame):
        raise SystemExit('Native validation interrupted by signal ' + str(signum))

    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)

    def trace(event, **details):
        entry = {'event': event, 'seconds': time.monotonic()-started,
                 'wall_unix_msec': time.time_ns() // 1_000_000,
                 'driver_held_keys': sorted(held_keys), 'driver_fire_down': fire_down, **details}
        if ui is not None:
            try:
                entry['native_state'] = ui.diagnostics()
            except Exception as error:
                entry['native_state_error'] = str(error)
        events.append(entry)
        if len(events) > 512:
            del events[0]
        (output / 'actions.json').write_text(json.dumps(events, indent=2) + '\n')

    def authority_observation():
        try:
            data = json.loads((output / 'authority-telemetry.json').read_text(encoding='utf-8'))
            return data['samples'][-1] if data['samples'] else None
        except (OSError, ValueError, KeyError):
            # The authority may be publishing this diagnostic file concurrently.
            return None

    def remaining():
        value = deadline - time.monotonic()
        if value <= 0:
            raise TimeoutError('Whole native-input flow deadline exceeded')
        return value

    def pause(seconds):
        if seconds >= remaining():
            raise TimeoutError('Whole native-input flow deadline exceeded')
        time.sleep(seconds)

    def launch(name, command, env=None, cwd=output):
        remaining()
        log = (output / (name + '.log')).open('w', encoding='utf-8')
        logs.append(log)
        process = subprocess.Popen(command, cwd=cwd, env=env, stdout=log, stderr=subprocess.STDOUT,
                                   start_new_session=os.name != 'nt')
        processes.append((name, process))
        commands.append({'name': name, 'command': command, 'pid': process.pid, 'started_seconds': time.monotonic()-started})
        (output / 'commands.json').write_text(json.dumps(commands, indent=2) + '\n')
        return process

    def wait_for(condition, seconds, label, process=None):
        trace('wait_begin', label=label, budget_seconds=seconds)
        until = min(deadline, time.monotonic() + seconds)
        while time.monotonic() < until:
            if process is not None and process.poll() is not None:
                raise RuntimeError(label + ': process exited early')
            if condition():
                trace('wait_completed', label=label, authority=authority_observation())
                return
            time.sleep(.1)
        trace('wait_timeout', label=label, authority=authority_observation())
        raise TimeoutError(label)

    def key(name, down):
        trace('key_before', key=name, down=down)
        ui.key(name, down)
        (held_keys.add if down else held_keys.discard)(name)
        trace('key_after', key=name, down=down)

    def button(down):
        nonlocal fire_down
        trace('button_before', down=down)
        ui.button(down)
        fire_down = down
        trace('button_after', down=down)

    def motion(dx, dy):
        trace('motion_before', dx=dx, dy=dy)
        ui.relative_motion(dx, dy)
        trace('motion_after', dx=dx, dy=dy)

    def capture(name):
        remaining()
        trace('capture_begin', capture=name)
        capture_started = time.monotonic()
        if name == '04-fire-input' and args.fire_capture_delay:
            trace('synthetic_capture_delay_begin', delay_seconds=args.fire_capture_delay)
            pause(args.fire_capture_delay)
            trace('synthetic_capture_delay_end')
        ui.capture(output / (name + '.png'))
        with Image.open(output / (name + '.png')) as image:
            capture_dimensions[:] = list(image.size)
        trace('capture_end', capture=name, duration_seconds=time.monotonic()-capture_started,
              authority=authority_observation())

    def open_menu_entry(x, y, label):
        ui.focus_game()
        trace('menu_click_before', x=x, y=y, label=label)
        ui.click(x, y)
        trace('menu_click_after', x=x, y=y, label=label)
        # A stale rendered menu is a readiness signal, never permission to
        # repeat an absolute pointer move after the game captures the mouse.
        # PR22 allowed three click+3s attempts (~10.35s total). Preserve that
        # aggregate cold-page budget with one click; replaying pointer motion
        # is unsafe once a page starts capturing input.
        wait_for(lambda: not ui.menu_visible(), 9.9, label, client)

    def server_has(message):
        return message in (output / 'server.log').read_text(encoding='utf-8', errors='replace')

    try:
        source_before = source()
        manifest = validate_record(args.target, source_before)
        engine = toolchain.verify_engine()
        executable_hash = hashlib.file_digest(executable.open('rb'), 'sha256').hexdigest()
        result.update({'artifact_source': manifest, 'authority_source': source_before, 'engine': engine,
                       'executable_sha256': executable_hash})
        if os.name == 'nt':
            job = windows_job()
            ui = WinUI()
        env = toolchain.environment()
        for variable, part in (('XDG_DATA_HOME', 'data'), ('XDG_CONFIG_HOME', 'config'), ('XDG_CACHE_HOME', 'cache')):
            path = output / 'state' / part
            path.mkdir(parents=True, exist_ok=True)
            env[variable] = str(path)
        if args.target == 'linux':
            xvfb = launch('xvfb', [args.xvfb, args.display, '-screen', '0', '1280x720x24', '-nolisten', 'tcp'])
            wait_for(display_socket.exists, 5, 'Xvfb readiness', xvfb)
            env.update(DISPLAY=args.display, LIBGL_ALWAYS_SOFTWARE='1', LP_NUM_THREADS='2')
            # This isolated Xvfb gameplay test has no desktop portal/session bus.
            # An explicit unavailable UNIX address prevents libdbus autolaunch
            # from escaping into init-owned DBus/AT-SPI helpers. Product startup
            # remains unchanged; portal and screen-reader coverage is unverified.
            env['DBUS_SESSION_BUS_ADDRESS'] = 'unix:path=' + quote(str(output / 'no-session-bus.sock'), safe='/._-')
            ui = NativeUI(args.display)
        else:
            # Godot uses native roaming/local AppData on Windows. Isolate test
            # state without modifying HOME or the player's actual profile.
            for variable, part in (('APPDATA', 'roaming'), ('LOCALAPPDATA', 'local')):
                path = output / 'state' / part
                path.mkdir(parents=True, exist_ok=True)
                env[variable] = str(path)
        accessibility_flags = ['--accessibility', 'disabled', '--accessibility-driver', 'dummy'] if args.target == 'linux' else []
        server_command = toolchain.command('--headless', *accessibility_flags, '--script', str(ROOT / 'scripts/fixtures/export_integration.gd'), '--', '--output=' + str(output))
        if args.reload_mode == 'authority':
            server_command.append('--automatic-reload')
        server = launch('server', server_command, env, ROOT)
        wait_for(lambda: server_has('SIGHTBREAK_SERVER_READY'), 15, 'Authority readiness', server)
        client_command = [str(executable), '--audio-driver', 'Dummy', '--position', '0,0', *accessibility_flags]
        if args.target == 'windows':
            client_command += ['--resolution', f'{ui.width}x{ui.height}']
        if args.quit_after:
            client_command += ['--quit-after', str(args.quit_after)]
        client = launch('client', client_command, env)
        if args.target == 'windows':
            ui.pid = client.pid
        wait_for(ui.focus_game, 30, 'Export window readiness', client)
        wait_for(ui.menu_visible, 60, 'Actual native menu readiness', client)
        capture('01-exported-menu')
        if args.visit_armory:
            open_menu_entry(140, 445, 'Exported inventory page opened')
            pause(1)
            capture('01b-exported-inventory')
            ui.click(1208, 46)
            wait_for(ui.menu_visible, 15, 'Return from exported armory', client)
            capture('01c-exported-menu-return')
        open_menu_entry(248, 385, 'Exported local-network page opened')
        pause(1)
        capture('02-exported-connect')
        ui.click(640, 305)
        wait_for(lambda: server_has('EXPORT_UI_ACK_READY'), 80, 'Owner snapshot acknowledged', client)
        pause(1)
        capture('03-exported-network-rifle')
        key('d', True)
        pause(.5)
        key('d', False)
        motion(12, -4)
        pause(.5)
        capture('03b-native-move-aim-input')
        trace('before_firing', authority=authority_observation())
        button(True)
        pause(.7)
        if args.input_schedule == 'legacy':
            capture('04-fire-input')
            button(False)
        else:
            button(False)
            capture('04-fire-input')
        pause(.5)
        capture('05-after-fire-input')
        key_down = None
        if args.reload_mode == 'keyboard':
            ui.focus_game()
            key('r', True)
            key_down = time.monotonic()
        wait_for(lambda: server_has('EXPORT_UI_RELOAD_STARTED'), 10, 'Authority confirms reload start', client)
        pause(.5)
        capture('06-after-authority-reload-start')
        if key_down is not None:
            pause(max(0, 2.5 - (time.monotonic() - key_down)))
            key('r', False)
        wait_for(lambda: server_has('EXPORT_UI_RELOAD_COMPLETED'), 5, 'Authority reload completion', client)
        pause(.5)
        capture('07-after-authority-reload-completion')
        pause(3)
        capture('08-settled')
        if client.poll() is not None:
            raise RuntimeError('Export exited before completion-driven desktop close')
        ui.request_close()
        client.wait(timeout=min(30, remaining()))
        (output / 'finish').write_text('finish\n')
        server.wait(timeout=min(10, remaining()))
        authority = json.loads((output / 'authority.json').read_text(encoding='utf-8'))
        if not authority['passed'] or client.returncode != 0 or server.returncode != 0:
            raise RuntimeError('Native authority or clean-exit check failed')
        if authority.get('protocol') != 6 or authority.get('prediction_default') is not False:
            raise RuntimeError('Protocol/default-off prediction contract changed')
        for name in ('client', 'server'):
            if native_log_failed((output / (name + '.log')).read_text(encoding='utf-8', errors='replace')):
                raise RuntimeError(name + ': error or resource leak; inspect log')
        validate_record(args.target, source_before)
        if source() != source_before:
            raise RuntimeError('Source changed during native verification')
        if os.name == 'nt':
            accounting = C.create_string_buffer(48)  # JOBOBJECT_BASIC_ACCOUNTING_INFORMATION
            if not job[0].QueryInformationJobObject(job[1], 1, accounting, len(accounting), None):
                raise C.WinError(C.get_last_error())
            if C.c_uint32.from_buffer(accounting, 40).value != 1:
                raise RuntimeError('Native root exited but job still owns a descendant')
        else:
            for name, process in processes:
                if name == 'xvfb':
                    continue
                try:
                    os.killpg(process.pid, 0)
                except ProcessLookupError:
                    continue
                raise RuntimeError(name + ': native root exited with descendants still alive')
        remaining()
        result.update({'passed': True, 'authority': authority, 'client_exit': client.returncode,
                       'server_exit': server.returncode, 'capture_method': 'raw X11 desktop' if args.target == 'linux' else 'raw Windows client-area desktop capture',
                       'rendered_capture_stages': 'Require visual inspection; authority timing is not rendered timing',
                       'capture_dimensions': capture_dimensions,
                       'reload_trigger': authority['reload_trigger'], 'inventory_navigation_captured': args.visit_armory,
                       'desktop_R_key_input': 'VERIFIED via server-observed reload command' if args.reload_mode == 'keyboard' else 'UNVERIFIED',
                       'movement_aim_input': 'Native input delivered; authoritative displacement not measured by this fixture',
                       'exit_method': 'completion-driven WM_DELETE_WINDOW' if args.target == 'linux' else 'completion-driven WM_CLOSE',
                       'automation_accessibility': 'Disabled with dummy driver and unavailable test-session bus; screen-reader/desktop portals UNVERIFIED' if args.target == 'linux' else 'No automation override; screen-reader/desktop portals UNVERIFIED',
                       'scope': 'Actual exported native desktop client; source Godot authority on loopback; no physical hardware or internet-security acceptance'})
    except (Exception, SystemExit) as error:
        trace('failure', error=str(error), authority=authority_observation())
        if ui is not None:
            try:
                ui.capture(output / 'failure-ui.png')
                trace('failure_capture', capture='failure-ui.png')
            except Exception as capture_error:
                trace('failure_capture_error', error=str(capture_error))
        (output / 'diagnostic-request').write_text('read-only failure snapshot\n')
        # Failure diagnostics have a separate bounded 150 ms cleanup allowance;
        # they do not extend or turn a failed qualification wait into a pass.
        time.sleep(.15)
        result.update({'passed': False, 'error': str(error), 'artifact_source': manifest, 'authority_source': source_before})
        result['failure_authority_observation'] = authority_observation()
    finally:
        cleanup_errors = []
        if ui:
            for name in list(held_keys):
                try:
                    ui.key(name, False)
                except Exception as error:
                    cleanup_errors.append('release '+name+': '+str(error))
            try:
                ui.button(False)
                ui.close()
            except Exception as error:
                cleanup_errors.append('native input teardown: '+str(error))
        # Linux groups and the Windows job establish ownership before launch.
        # Root exits are retained separately from forced cleanup.
        for name, process in reversed(processes):
            try:
                if os.name != 'nt':
                    os.killpg(process.pid, signal.SIGTERM)
                elif process.poll() is None:
                    process.terminate()
            except ProcessLookupError:
                pass
            except Exception as error:
                cleanup_errors.append(name+' termination: '+str(error))
        for name, process in reversed(processes):
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                try:
                    if os.name != 'nt':
                        os.killpg(process.pid, signal.SIGKILL)
                    else:
                        process.kill()
                    process.wait(timeout=5)
                except Exception as error:
                    cleanup_errors.append(name+' forced cleanup: '+str(error))
            if os.name != 'nt':
                # An already-exited root can leave a descendant that ignored
                # SIGTERM; do not skip group cleanup merely because wait() won.
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                except Exception as error:
                    cleanup_errors.append(name+' descendant cleanup: '+str(error))
        for entry, (name, process) in zip(commands, processes):
            entry['exit_code'] = process.returncode
        for log in logs:
            log.close()
        result['cleanup_errors'] = cleanup_errors
        if cleanup_errors:
            result.update(passed=False, error=result.get('error', 'Native process cleanup failed'))
        result['commands'] = commands
        result['elapsed_seconds'] = time.monotonic() - started
        # Include decisive measurements in CI text as well as the raw artifact.
        # This stays bounded even when downloading a CI artifact is unavailable.
        result['input_timing'] = {
            'before_firing': next((event for event in events if event['event'] == 'before_firing'), None),
            'fire_button_edges': [event for event in events if event['event'] in ('button_before', 'button_after')][-8:],
            'reload_key_edges': [event for event in events if event['event'] in ('key_before', 'key_after') and event.get('key') == 'r'][-8:],
            'capture_durations': [{key: event[key] for key in ('capture', 'seconds', 'duration_seconds')}
                                  for event in events if event['event'] == 'capture_end'][-20:],
            'last_authority_sample': authority_observation(),
        }
        (output / 'commands.json').write_text(json.dumps(commands, indent=2) + '\n')
        (output / 'results.json').write_text(json.dumps(result, indent=2) + '\n')
    if not result['passed']:
        print(json.dumps({'native_input_failure': result, 'recent_actions': events[-12:]}, indent=2))
        for name in ('server', 'client'):
            path = output / (name + '.log')
            if path.is_file():
                print(name + ' log tail (bounded):\n' + path.read_text(encoding='utf-8', errors='replace')[-12000:])
        raise RuntimeError(result.get('error', 'Native input validation failed'))
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
