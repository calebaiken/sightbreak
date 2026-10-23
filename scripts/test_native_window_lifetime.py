#!/usr/bin/env python3
"""Exercise native controller lifetime races using real Xvfb windows.

Each case owns a separate Python child so a fatal baseline Xlib error is retained
as a failed child, not mistaken for a Python exception or a successful test.
"""
import argparse
import ctypes as C
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time


CASES = ('discovery-race', 'focus-race', 'stale-diagnostics', 'geometry-race',
         'unrelated-error', 'pending-error', 'different-resource-error',
         'handler-restoration', 'positive-and-repeat')


def child_case(name, module_path, display):
    spec = importlib.util.spec_from_file_location('native_window_subject', module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if name == 'geometry-race':
        sys.modules['verify_integration_export'] = module
        from capture_desktop_layouts import LayoutUI
        ui = LayoutUI(display, (320, 240))
    else:
        ui = module.NativeUI(display)
    x = C.CDLL(module.find_library('X11'))
    x.XOpenDisplay.argtypes = [C.c_char_p]
    x.XOpenDisplay.restype = C.c_void_p
    x.XDefaultRootWindow.argtypes = [C.c_void_p]
    x.XDefaultRootWindow.restype = C.c_ulong
    x.XCreateSimpleWindow.argtypes = [C.c_void_p, C.c_ulong, C.c_int, C.c_int,
                                     C.c_uint, C.c_uint, C.c_uint, C.c_ulong, C.c_ulong]
    x.XCreateSimpleWindow.restype = C.c_ulong
    x.XStoreName.argtypes = [C.c_void_p, C.c_ulong, C.c_char_p]
    x.XMapWindow.argtypes = [C.c_void_p, C.c_ulong]
    x.XDestroyWindow.argtypes = [C.c_void_p, C.c_ulong]
    x.XSync.argtypes = [C.c_void_p, C.c_int]
    x.XCloseDisplay.argtypes = [C.c_void_p]
    x.XQueryTree.argtypes = ui.x.XQueryTree.argtypes
    x.XFree.argtypes = [C.c_void_p]
    x.XSetInputFocus.argtypes = ui.x.XSetInputFocus.argtypes
    x.XSetErrorHandler.argtypes = [C.c_void_p]
    x.XSetErrorHandler.restype = C.c_void_p
    creator = x.XOpenDisplay(display.encode())
    assert creator, 'Fixture display connection failed'
    windows = set()
    result = {'case': name, 'native_calls': True}

    def create(title, width=80, height=60):
        window = x.XCreateSimpleWindow(creator, x.XDefaultRootWindow(creator),
                                      0, 0, width, height, 0, 0, 0)
        assert window
        windows.add(window)
        x.XStoreName(creator, window, title.encode())
        x.XMapWindow(creator, window)
        x.XSync(creator, 0)
        return window

    def destroy(window):
        x.XDestroyWindow(creator, window)
        x.XSync(creator, 0)
        windows.remove(window)

    try:
        if name == 'discovery-race':
            victim = create('SIGHTBREAK vanishing', 100, 80)
            survivor = create('SIGHTBREAK live')
            native = ui.x.XFetchName
            def disappear(connection, window, output):
                if window == victim and victim in windows:
                    destroy(victim)
                return native(connection, window, output)
            ui.x.XFetchName = disappear
            assert ui.focus_game() is True
            assert ui.window == survivor
            assert ui.diagnostics()['target_focused'] is True
            result['destroyed_between_enumeration_and_name'] = victim
        elif name == 'focus-race':
            victim = create('SIGHTBREAK vanishing')
            native = ui.x.XSetInputFocus
            def disappear(connection, window, revert, timestamp):
                destroy(victim)
                return native(connection, window, revert, timestamp)
            ui.x.XSetInputFocus = disappear
            assert ui.focus_game() is False
            assert ui.diagnostics()['target_window'] is None
            assert ui.diagnostics()['target_focused'] is False
        elif name == 'stale-diagnostics':
            victim = create('SIGHTBREAK old')
            assert ui.focus_game() is True
            destroy(victim)
            observed = ui.diagnostics()
            assert observed['target_window'] is None
            assert observed['target_focused'] is False
        elif name == 'geometry-race':
            victim = create('SIGHTBREAK old')
            assert ui.focus_game() is True
            assert ui.window_size() == (80, 60)
            destroy(victim)
            try:
                ui.window_size()
            except RuntimeError as error:
                assert 'window' in str(error).lower()
                result['controlled_geometry_error'] = str(error)
            else:
                raise AssertionError('Destroyed geometry was falsely accepted')
            try:
                ui.request_close()
            except RuntimeError as error:
                result['controlled_close_error'] = str(error)
            else:
                raise AssertionError('Destroyed target was falsely accepted for close')
        elif name == 'unrelated-error':
            victim = create('SIGHTBREAK live')
            native = ui.x.XFetchName
            def invalid_value(connection, window, output):
                # Actual BadValue from a valid window, not a missing-window race.
                x.XSetInputFocus(connection, victim, 999, 0)
                return native(connection, window, output)
            ui.x.XFetchName = invalid_value
            try:
                ui.focus_game()
            except RuntimeError as error:
                assert any(item['error_code'] == 2 and item['request_code'] == 42
                           for item in error.errors), str(error)
                result['propagated_errors'] = error.errors
            else:
                raise AssertionError('Unrelated X error was suppressed')
        elif name == 'pending-error':
            victim = create('SIGHTBREAK live')
            # Queue a real unrelated error before the checked operation starts.
            x.XSetInputFocus(ui.d, victim, 999, 0)
            try:
                ui.focus_game()
            except RuntimeError as error:
                assert 'pending requests' in str(error), str(error)
                assert any(item['error_code'] == 2 for item in error.errors)
            else:
                raise AssertionError('Pending unrelated X error was suppressed')
        elif name == 'different-resource-error':
            victim = create('SIGHTBREAK live')
            other = create('unrelated removed window')
            destroy(other)
            native = ui.x.XFetchName
            def wrong_resource(connection, _window, output):
                return native(connection, other, output)
            ui.x.XFetchName = wrong_resource
            try:
                ui.focus_game()
            except RuntimeError as error:
                assert not isinstance(error, module.NativeWindowUnavailable)
                assert any(item['resourceid'] == other and item['error_code'] == 3
                           for item in error.errors)
            else:
                raise AssertionError('An unrelated missing resource was suppressed')
        elif name == 'handler-restoration':
            victim = create('SIGHTBREAK live')
            received = []
            callback_type = C.CFUNCTYPE(C.c_int, C.c_void_p, C.c_void_p)
            @callback_type
            def previous_handler(_display, _error):
                received.append(True)
                return 0
            previous = x.XSetErrorHandler(C.cast(previous_handler, C.c_void_p))
            try:
                assert ui.focus_game() is True
                native = ui.x.XFetchName
                def invalid_value(connection, window, output):
                    x.XSetInputFocus(connection, victim, 999, 0)
                    return native(connection, window, output)
                ui.x.XFetchName = invalid_value
                try:
                    ui.focus_game()
                except RuntimeError as error:
                    assert any(item['error_code'] == 2 for item in error.errors)
                else:
                    raise AssertionError('Native error did not reach Python')
                finally:
                    ui.x.XFetchName = native
                assert received == [], 'Checked errors escaped to the previous handler'
                assert ui.focus_game() is True
                destroy(victim)
                assert ui.diagnostics()['target_window'] is None
                # The prior handler must receive a later, unrelated operation.
                x.XSetInputFocus(creator, victim, 1, 0)
                x.XSync(creator, 0)
                assert received == [True], received
            finally:
                x.XSetErrorHandler(previous)
        elif name == 'positive-and-repeat':
            create('unrelated large window', 200, 180)
            create('SIGHTBREAK small')
            selected = create('SIGHTBREAK large', 120, 90)
            started = time.monotonic()
            for _ in range(50):
                assert ui.focus_game() is True
                assert ui.window == selected
                observed = ui.diagnostics()
                assert observed['target_focused'] is True
                assert observed['lmb_down'] is False
                assert not any(observed['keys_down'].values())
            result['iterations'] = 50
            result['query_wall_seconds'] = time.monotonic() - started
            assert result['query_wall_seconds'] < 5, result
            try:
                ui.request_close()
            except RuntimeError as error:
                assert 'not advertised' in str(error)
            else:
                raise AssertionError('Unadvertised close protocol was accepted')
            x.XSetWMProtocols.argtypes = [C.c_void_p, C.c_ulong, C.POINTER(C.c_ulong), C.c_int]
            protocols = (C.c_ulong * 1)(ui.wm_delete)
            x.XSetWMProtocols(creator, selected, protocols, 1)
            x.XSync(creator, 0)
            ui.request_close()
            class MessageData(C.Union):
                _fields_ = [('l', C.c_long * 5), ('b', C.c_char * 20)]
            class ClientMessage(C.Structure):
                _fields_ = [('type', C.c_int), ('serial', C.c_ulong), ('send_event', C.c_int),
                            ('display', C.c_void_p), ('window', C.c_ulong),
                            ('message_type', C.c_ulong), ('format', C.c_int), ('data', MessageData)]
            class Event(C.Union):
                _fields_ = [('message', ClientMessage), ('padding', C.c_long * 24)]
            x.XPending.argtypes = [C.c_void_p]
            x.XNextEvent.argtypes = [C.c_void_p, C.POINTER(Event)]
            assert x.XPending(creator) > 0
            event = Event()
            x.XNextEvent(creator, C.byref(event))
            assert event.message.type == 33 and event.message.window == selected
            assert event.message.message_type == ui.wm_protocols
            assert event.message.data.l[0] == ui.wm_delete
            result['advertised_close_delivered'] = True
        else:
            raise AssertionError(name)
    finally:
        for window in list(windows):
            destroy(window)
        root, parent, count = C.c_ulong(), C.c_ulong(), C.c_uint()
        children = C.POINTER(C.c_ulong)()
        x.XQueryTree(creator, x.XDefaultRootWindow(creator), C.byref(root),
                     C.byref(parent), C.byref(children), C.byref(count))
        try:
            assert count.value == 0, 'Fixture windows survived cleanup'
        finally:
            if children:
                x.XFree(children)
            x.XCloseDisplay(creator)
            ui.close()
    result['windows_and_connections_closed'] = True
    print(json.dumps(result), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--module', type=Path, default=Path(__file__).with_name('verify_integration_export.py'))
    parser.add_argument('--display', default=':231')
    parser.add_argument('--xvfb', default=os.environ.get('XVFB_BIN') or shutil.which('Xvfb'))
    parser.add_argument('--case', choices=CASES, action='append')
    parser.add_argument('--child', choices=CASES, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.child:
        child_case(args.child, args.module.resolve(), args.display)
        return 0
    if sys.platform != 'linux' or not args.xvfb or not args.display.startswith(':') or not args.display[1:].isdigit() or int(args.display[1:]) < 200:
        parser.error('Requires Linux, Xvfb and an isolated numbered display at least 200')
    socket = Path('/tmp/.X11-unix/X' + args.display[1:])
    if socket.exists():
        parser.error('Selected display is already in use')
    outcomes = []
    with tempfile.TemporaryDirectory(prefix='sightbreak-x11-lifetime-') as temporary:
        with (Path(temporary) / 'xvfb.txt').open('w+') as log:
            server = subprocess.Popen([args.xvfb, args.display, '-screen', '0', '320x240x24', '-nolisten', 'tcp'],
                                      stdout=log, stderr=subprocess.STDOUT)
            try:
                deadline = time.monotonic() + 5
                while not socket.exists() and server.poll() is None and time.monotonic() < deadline:
                    time.sleep(.02)
                if not socket.exists() or server.poll() is not None:
                    log.seek(0)
                    raise RuntimeError('Owned Xvfb failed: ' + log.read())
                for name in args.case or CASES:
                    started = time.monotonic()
                    completed = subprocess.run([sys.executable, str(Path(__file__).resolve()), '--child', name,
                                                '--module', str(args.module.resolve()), '--display', args.display],
                                               capture_output=True, text=True, timeout=10)
                    outcome = {'case': name, 'exit_code': completed.returncode,
                               'wall_seconds': time.monotonic() - started,
                               'stdout': completed.stdout, 'stderr': completed.stderr}
                    outcomes.append(outcome)
                    print(json.dumps(outcome), flush=True)
            finally:
                if server.poll() is None:
                    server.terminate()
                try:
                    server.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    server.kill()
                    server.wait(timeout=3)
                    raise RuntimeError('Owned Xvfb required forced cleanup')
                assert server.returncode == 0, 'Owned Xvfb did not exit cleanly'
    passed = all(item['exit_code'] == 0 for item in outcomes)
    print(json.dumps({'passed': passed, 'cases': len(outcomes), 'xvfb_reaped': True}), flush=True)
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
