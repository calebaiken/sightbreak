#!/usr/bin/env python3
"""Drive the actual Linux export's native UI against a source-engine authority.

Requires Pillow, X11/XTest, a free 1280x720 Xvfb display, and the export templates.
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
from pathlib import Path
import re
import shutil
import subprocess
import time

from PIL import ImageGrab
from build_manifest import source
from native_log import failed as native_log_failed

ROOT = Path(__file__).resolve().parents[1]


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
        if not self.d:
            raise RuntimeError('Cannot open native display ' + display)

    def focus_game(self):
        root, parent, count = C.c_ulong(), C.c_ulong(), C.c_uint()
        children = C.POINTER(C.c_ulong)()
        self.x.XQueryTree(self.d, self.x.XDefaultRootWindow(self.d), C.byref(root), C.byref(parent), C.byref(children), C.byref(count))
        largest, selected = 0, None
        try:
            for index in range(count.value):
                name = C.c_char_p()
                self.x.XFetchName(self.d, children[index], C.byref(name))
                try:
                    if not name.value or b'SIGHTBREAK' not in name.value:
                        continue
                    wr, wx, wy = C.c_ulong(), C.c_int(), C.c_int()
                    ww, wh, border, depth = C.c_uint(), C.c_uint(), C.c_uint(), C.c_uint()
                    self.x.XGetGeometry(self.d, children[index], C.byref(wr), C.byref(wx), C.byref(wy), C.byref(ww), C.byref(wh), C.byref(border), C.byref(depth))
                    if ww.value * wh.value > largest:
                        largest, selected = ww.value * wh.value, children[index]
                finally:
                    if name:
                        self.x.XFree(name)
        finally:
            if children:
                self.x.XFree(children)
        if selected is None:
            return False
        self.x.XSetInputFocus(self.d, selected, 1, 0)
        self.x.XFlush(self.d)
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
        pixel = ImageGrab.grab(xdisplay=self.display).getpixel((46, 299))
        return pixel[0] > 80 and pixel[0] > pixel[1] * 1.5

    def close(self):
        self.x.XCloseDisplay(self.d)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'builds/verification/integration')
    parser.add_argument('--display', default=':101', help='A free isolated X11 display')
    parser.add_argument('--xvfb', default=os.environ.get('XVFB_BIN') or shutil.which('Xvfb'))
    parser.add_argument('--quit-after', type=int, default=300)
    parser.add_argument('--timeout', type=float, default=180)
    parser.add_argument('--visit-armory', action='store_true', help='Capture actual exported inventory navigation; screenshots require visual inspection')
    parser.add_argument('--reload-mode', choices=('authority', 'keyboard'), default='authority')
    args = parser.parse_args()
    if not args.xvfb:
        parser.error('Set --xvfb or XVFB_BIN to the Xvfb executable')
    if not re.fullmatch(r':[0-9]+', args.display):
        parser.error('Use a local numbered display such as :101')
    if args.quit_after <= 0 or args.timeout <= 0:
        parser.error('Exit iterations and timeout must be positive')
    display_socket = Path('/tmp/.X11-unix/X' + args.display[1:])
    if display_socket.exists():
        parser.error('Display is already in use: ' + args.display)
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    # Reject stale success records; retain each campaign in a separate directory.
    for name in ('finish', 'authority.json', 'results.json'):
        (output / name).unlink(missing_ok=True)
    executable = ROOT / 'builds/linux/sightbreak.x86_64'
    manifest = json.loads((executable.parent / 'source.json').read_text())
    source_before = source()
    if manifest['source_content_sha256'] != source_before['source_content_sha256']:
        raise RuntimeError('Export and source authority have different runtime content')
    executable_hash = hashlib.file_digest(executable.open('rb'), 'sha256').hexdigest()
    if executable_hash != manifest['artifact']['sha256']:
        raise RuntimeError('Export no longer matches its build manifest')
    processes, logs, ui = [], [], None

    def launch(name, command, env=None, cwd=output):
        log = (output / (name + '.log')).open('w')
        logs.append(log)
        process = subprocess.Popen(command, cwd=cwd, env=env, stdout=log, stderr=subprocess.STDOUT)
        processes.append(process)
        return process

    def wait_for(condition, seconds, label, process=None):
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            if condition():
                return
            if process is not None and process.poll() is not None:
                raise RuntimeError(label + ': process exited early')
            time.sleep(.1)
        raise TimeoutError(label)

    def server_has(message):
        return message in (output / 'server.log').read_text()

    try:
        xvfb = launch('xvfb', [args.xvfb, args.display, '-screen', '0', '1280x720x24', '-nolisten', 'tcp'])
        wait_for(display_socket.exists, 5, 'Xvfb readiness', xvfb)
        env = dict(os.environ, DISPLAY=args.display, LIBGL_ALWAYS_SOFTWARE='1', LP_NUM_THREADS='2')
        for name, directory in [('XDG_DATA_HOME', 'data'), ('XDG_CONFIG_HOME', 'config'), ('XDG_CACHE_HOME', 'cache')]:
            path = output / 'state' / directory
            path.mkdir(parents=True, exist_ok=True)
            env[name] = str(path)
        server_command = [str(ROOT / 'scripts/godot.sh'), '--headless', '--script', str(ROOT / 'scripts/fixtures/export_integration.gd'), '--', '--output=' + str(output)]
        if args.reload_mode == 'authority':
            server_command.append('--automatic-reload')
        server = launch('server', server_command,
                        {**env, 'SIGHTBREAK_STATE_DIR': str(output / 'server-state')}, ROOT)
        wait_for(lambda: server_has('SIGHTBREAK_SERVER_READY'), 15, 'Authority readiness', server)
        client = launch('client', [str(executable), '--audio-driver', 'Dummy', '--quit-after', str(args.quit_after)], env)
        ui = NativeUI(args.display)
        wait_for(ui.focus_game, 30, 'Export window readiness', client)
        wait_for(ui.menu_visible, 60, 'Actual native menu readiness', client)
        ui.focus_game()
        ui.capture(output / '01-exported-menu.png')
        if args.visit_armory:
            ui.click(140, 445)
            time.sleep(2)
            ui.capture(output / '01b-exported-inventory.png')
            ui.click(1208, 46)
            wait_for(ui.menu_visible, 15, 'Return from exported armory', client)
            ui.capture(output / '01c-exported-menu-return.png')
        ui.click(248, 385)
        time.sleep(1)
        ui.capture(output / '02-exported-connect.png')
        ui.click(640, 305)
        wait_for(lambda: server_has('EXPORT_UI_ACK_READY'), 80, 'Owner snapshot acknowledged', client)
        time.sleep(1)
        ui.capture(output / '03-exported-network-rifle.png')
        ui.button(True)
        time.sleep(.7)
        ui.capture(output / '04-fire-input.png')
        ui.button(False)
        time.sleep(.5)
        ui.capture(output / '05-after-fire-input.png')
        key_down = None
        if args.reload_mode == 'keyboard':
            ui.focus_game()
            ui.key('r', True)
            key_down = time.monotonic()
        wait_for(lambda: server_has('EXPORT_UI_RELOAD_STARTED'), 10, 'Authority confirms reload start', client)
        time.sleep(.5)
        ui.capture(output / '06-after-authority-reload-start.png')
        if key_down is not None:
            time.sleep(max(0, 2.5 - (time.monotonic() - key_down)))
            ui.key('r', False)
        wait_for(lambda: server_has('EXPORT_UI_RELOAD_COMPLETED'), 5, 'Authority reload completion', client)
        time.sleep(.5)
        ui.capture(output / '07-after-authority-reload-completion.png')
        time.sleep(3)
        ui.capture(output / '08-settled.png')
        # Rendered capture stages must be visually reviewed: software rendering
        # can lag the authority. The filenames describe capture timing only.
        client.wait(timeout=args.timeout)
        (output / 'finish').write_text('finish\n')
        server.wait(timeout=10)
        authority = json.loads((output / 'authority.json').read_text())
        if not authority['passed'] or client.returncode != 0 or server.returncode != 0:
            raise RuntimeError('Native authority or clean-exit check failed')
        for name in ('client', 'server'):
            log_text = (output / (name + '.log')).read_text()
            if native_log_failed(log_text):
                raise RuntimeError(name + ': error or resource leak; inspect log')
        if source()['source_content_sha256'] != source_before['source_content_sha256']:
            raise RuntimeError('Runtime source changed during verification')
        result = {'passed': True, 'artifact_source': manifest, 'authority_source': source_before,
                  'executable_sha256': executable_hash, 'authority': authority,
                  'client_exit': client.returncode, 'server_exit': server.returncode,
                  'capture_dimensions': [1280, 720], 'capture_method': 'raw X11 ImageGrab; no image edits',
                  'rendered_capture_stages': 'Require visual inspection; authority timing is not rendered timing',
                  'reload_trigger': authority['reload_trigger'],
                  'inventory_navigation_captured': args.visit_armory,
                  'desktop_R_key_input': 'VERIFIED via server-observed reload command' if args.reload_mode == 'keyboard' else 'UNVERIFIED',
                  'exit_method': 'supported --quit-after ' + str(args.quit_after),
                  'scope': 'Actual exported Linux client through native UI; source Godot authority on loopback; llvmpipe software rendering; no physical-device performance claim'}
        (output / 'results.json').write_text(json.dumps(result, indent=2) + '\n')
        print(json.dumps(result, indent=2))
    except Exception as error:
        (output / 'results.json').write_text(json.dumps({'passed': False, 'error': str(error), 'artifact_source': manifest, 'authority_source': source_before}, indent=2) + '\n')
        raise
    finally:
        if ui:
            ui.close()
        for process in reversed(processes):
            if process.poll() is None:
                process.terminate()
        for process in reversed(processes):
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        for log in logs:
            log.close()


if __name__ == '__main__':
    main()
