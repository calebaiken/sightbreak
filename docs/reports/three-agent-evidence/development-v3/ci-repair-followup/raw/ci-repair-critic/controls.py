"""Pure synthetic wiring controls; no X11/native executable/OCR/service launch.

The real controller main functions, manifest checks, HUD parsers and receipts run.
Only desktop/process/time/image/OCR boundaries are replaced, locally per module.
Synthetic passing results are NOT evidence of an actual exported-client pass.
"""
import contextlib
import ctypes as C
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
from unittest.mock import Mock, patch
import zipfile

from audit import OUT, ROOT, snapshot

sys.path.insert(0, str(ROOT / "scripts"))
import verify_integration_export as network
import verify_offline_export as offline
from offline_hud import parse_hud_text


class Scenario:
    def __init__(self, mode, fault):
        self.mode, self.fault = mode, fault
        self.root = OUT / "controls" / (mode + "-" + fault)
        self.output = self.root / "evidence"
        executable = self.root / "builds/linux/sightbreak.x86_64"
        executable.parent.mkdir(parents=True)
        executable.write_bytes(b"synthetic fixture only -- never executed\n")
        self.current = dict(source_commit="synthetic-commit", source_game_tree="synthetic-tree",
                            source_content_sha256="synthetic-runtime", source_validation_sha256="synthetic-tools",
                            source_game_dirty=False, source_dirty=False)
        manifest = {**self.current, "export_completed": True,
                    "artifact": {"sha256": hashlib.sha256(executable.read_bytes()).hexdigest()}}
        (executable.parent / "source.json").write_text(json.dumps(manifest), encoding="utf-8")
        self.now, self.trace, self.processes, self.frames = 0.0, [], [], {}
        self.ui, self.client, self.xvfb_started = None, None, False

    def record(self, event, **details):
        self.trace.append(dict(t=round(self.now, 3), event=event, **details))

    def sleep(self, seconds):
        self.now += seconds

    def path(self, value):
        if str(value).startswith('/tmp/.X11-unix/X'):
            return SimpleNamespace(exists=lambda: self.xvfb_started)
        return Path(value)

    def popen(self, command, *, stdout, **kwargs):
        name = 'xvfb' if command[0] == 'synthetic-xvfb' else ('client' if str(command[0]).endswith('.x86_64') else 'server')
        self.record('launch', name=name, command=list(map(str, command)))
        if name == 'xvfb':
            self.xvfb_started = True
        if name == 'server':
            stdout.write('SIGHTBREAK_SERVER_READY\nEXPORT_UI_ACK_READY\n'
                         'EXPORT_UI_RELOAD_STARTED\nEXPORT_UI_RELOAD_COMPLETED\n')
            stdout.flush()
        if name == 'client':
            stdout.write('MATCH: Round live. Secure Relay Yard.\n')
            if self.fault == 'native-log-leak':
                stdout.write('WARNING: ObjectDB instances leaked at exit\n')
            stdout.flush()
        scenario = self

        class Process:
            returncode = None

            def poll(self):
                return self.returncode

            def wait(self, timeout=None):
                scenario.record('wait', name=name, timeout=timeout)
                if name == 'client' and self.returncode is None and scenario.fault == 'native-close-hang':
                    raise subprocess.TimeoutExpired('synthetic client close', timeout)
                if self.returncode is None:
                    self.returncode = 7 if ((name == 'client' and scenario.fault == 'native-close-exit7')
                                             or (name == 'server' and scenario.fault == 'server-exit7')) else 0
                if name == 'server':
                    (scenario.output / 'authority.json').write_text(json.dumps(
                        {'passed': scenario.fault != 'authority-false', 'reload_trigger': 'native client input',
                         'synthetic_control_not_native_evidence': True}), encoding='utf-8')
                return self.returncode

            def terminate(self):
                scenario.record('terminate', name=name)
                self.returncode = 1

            def kill(self):
                scenario.record('kill', name=name)
                self.returncode = 1

        process = Process()
        self.processes.append(process)
        if name == 'client':
            self.client = process
        return process

    def native_ui(self, display):
        scenario = self
        self.record('native-init-atoms-and-sync', display=display)
        if self.fault == 'source-mutated-at-native-init':
            self.current['source_validation_sha256'] = 'changed-during-ui-init'

        class UI:
            screen, overlay, ammo, reserve = 'menu', None, 15, 60
            d, window = 123, 456
            t = SimpleNamespace(XTestFakeMotionEvent=lambda *args: None)
            x = SimpleNamespace(XFlush=lambda *args: None)

            def focus_game(self):
                scenario.record('focus')
                return True

            def menu_visible(self):
                return self.screen == 'menu'

            def click(self, x, y):
                scenario.record('click', x=x, y=y)
                if (x, y) == (140, 445):
                    self.screen = 'armory'
                elif (x, y) == (1208, 46):
                    self.screen = 'menu'
                elif (x, y) == (248, 385):
                    self.screen = 'connect'
                elif (x, y) in ((248, 319), (640, 305)):
                    self.screen = 'game'
                elif (x, y) == (640, 318) and self.overlay == 'field':
                    self.screen, self.overlay = 'menu', None

            def key(self, key, down):
                scenario.record('key', key=key, down=down, overlay=self.overlay)
                if not down:
                    return
                if key == 'b':
                    self.overlay = 'requisition'
                elif key == 'Escape':
                    if self.overlay == 'field' and scenario.fault == 'resume-not-consumed':
                        return
                    if self.overlay is None and scenario.fault == 'pause-not-consumed':
                        return
                    self.overlay = None if self.overlay is not None else 'field'
                elif key == 'r' and self.overlay is None and scenario.fault != 'reload-input-ignored':
                    scenario.record('reload-accepted-unpaused')
                    self.reserve -= 15 - self.ammo
                    self.ammo = 15
                    if scenario.fault == 'ammo-not-conserved':
                        self.reserve -= 1

            def button(self, down):
                scenario.record('button', down=down, overlay=self.overlay)
                if not down and self.screen == 'game' and self.overlay is None:
                    self.ammo -= 1

            def capture(self, path):
                scenario.record('capture', image=path.name, overlay=self.overlay)
                frame = dict(name=path.stem, overlay=self.overlay, ammo=self.ammo, reserve=self.reserve,
                             synthetic_control_not_native_evidence=True)
                scenario.frames[path.stem] = frame
                path.write_text(json.dumps(frame), encoding='utf-8')
                if scenario.fault == 'early-zero-exit-before-close' and path.stem in ('08-settled', '08-return-menu'):
                    scenario.client.returncode = 0

            def request_close(self):
                scenario.record('request-close')
                if scenario.fault == 'unadvertised-close':
                    raise RuntimeError('Exported window does not advertise the prepared WM_DELETE_WINDOW')
                if scenario.fault == 'source-mutated-before-final-audit':
                    scenario.current['source_validation_sha256'] = 'changed-before-final-audit'
                return dict(method='synthetic request -- not X11 evidence')

            def close(self):
                scenario.record('close-display')

        self.ui = UI()
        return self.ui

    def image_open(self, path):
        scenario = self

        class Image:
            width, height, box = 100, 100, None

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def crop(self, box):
                self.box = box
                return self

            def resize(self, size):
                return self

            def save(self, data, format):
                data.write(json.dumps(dict(frame=scenario.frames[path.stem], box=self.box)).encode())

        return Image()

    def ocr(self, command, data, deadline, output):
        payload = json.loads(data)
        frame, box = payload['frame'], payload['box']
        self.record('ocr', image=frame['name'], box=box, current_overlay=self.ui.overlay)
        assert self.ui.overlay == 'field' or self.fault == 'pause-not-consumed', 'OCR escaped the ordinary paused inspection'
        self.now += 5  # Simulated costly OCR while the ordinary offline menu is open.
        if self.now >= deadline:
            raise TimeoutError('synthetic OCR exceeded its wall-clock budget')
        if box[1] == 40:
            text = ('FIELD MENU\nTraining is paused.\n' if frame['overlay'] == 'field' else 'unpaused live HUD')
            if self.fault == 'network-pause-label':
                text = 'FIELD MENU\nThe match continues while this menu is open.\n'
        elif box[0] == 0:
            text = '100 HEALTH\n'
            if ((self.fault == 'eliminated-after-reload' and frame['name'].startswith('06-'))
                    or (self.fault == 'eliminated-after-fire' and frame['name'].startswith('05-'))):
                text = 'ELIMINATED - SPECTATING\n'
            if self.fault == 'zero-health-after-reload' and frame['name'].startswith('06-'):
                text = '000 HEALTH\n'
        else:
            text = f"SIDEARM {frame['ammo']}/{frame['reserve']}\n"
        output.with_suffix('.stdout.txt').write_text(text, encoding='utf-8')
        return text

    def run(self):
        module = offline if self.mode == 'offline' else network
        arguments = [module.__file__, '--output', str(self.output), '--display', ':99998',
                     '--xvfb', 'synthetic-xvfb', '--timeout', '300']
        if self.mode == 'offline':
            arguments += ['--tesseract', 'synthetic-ocr']
        else:
            arguments += ['--visit-armory', '--reload-mode', 'keyboard']
        process_api = SimpleNamespace(Popen=self.popen, STDOUT=subprocess.STDOUT, TimeoutExpired=subprocess.TimeoutExpired)
        error = None
        with (self.root / 'controller-output.log').open('x', encoding='utf-8') as raw, contextlib.ExitStack() as stack:
            stack.enter_context(contextlib.redirect_stdout(raw))
            stack.enter_context(patch.object(sys, 'argv', arguments))
            stack.enter_context(patch.object(module, 'ROOT', self.root))
            stack.enter_context(patch.object(module, 'Path', self.path))
            stack.enter_context(patch.object(module, 'NativeUI', self.native_ui))
            stack.enter_context(patch.object(module, 'subprocess', process_api))
            stack.enter_context(patch.object(module, 'time', SimpleNamespace(monotonic=lambda: self.now, sleep=self.sleep)))
            stack.enter_context(patch.object(network, 'source', lambda: dict(self.current)))
            if self.mode == 'offline':
                stack.enter_context(patch.dict(sys.modules, {'PIL': SimpleNamespace(Image=SimpleNamespace(open=self.image_open))}))
                stack.enter_context(patch.object(offline, 'ocr_text', self.ocr))
            try:
                module.main()
            except (Exception, SystemExit) as caught:
                error = dict(type=type(caught).__name__, message=str(caught))
        result = json.loads((self.output / 'results.json').read_text(encoding='utf-8'))
        expected_success = self.fault == 'none'
        passed = (result.get('passed') is expected_success and (error is None) is expected_success)
        launches = [item['name'] for item in self.trace if item['event'] == 'launch']
        if self.fault == 'source-mutated-at-native-init':
            passed = passed and 'client' not in launches
        if expected_success:
            names = [item['event'] for item in self.trace]
            client_index = next(i for i, item in enumerate(self.trace) if item['event'] == 'launch' and item['name'] == 'client')
            passed = passed and names.index('native-init-atoms-and-sync') < client_index
            passed = passed and not any(item['event'] in ('terminate', 'kill') and item['name'] == 'client' for item in self.trace)
            if self.mode == 'offline':
                passed = passed and [item['image'] for item in self.trace if item['event'] == 'ocr'] == [
                    '05-inspection-pause', '05-after-fire', '05-after-fire',
                    '06-inspection-pause', '06-after-reload', '06-after-reload']
                passed = passed and names.count('reload-accepted-unpaused') == 1
        row = dict(mode=self.mode, fault=self.fault, control_passed=passed, error=error,
                   controller_passed=result.get('passed'), synthetic_control_not_native_evidence=True)
        (self.root / 'control.json').write_text(json.dumps(dict(row=row, trace=self.trace), indent=2) + '\n', encoding='utf-8')
        return row


def protocol_controls():
    rows = []
    for outcome in ('empty', 'failed-with-allocation', 'valid'):
        ui = network.NativeUI.__new__(network.NativeUI)
        ui.d, ui.window = 123, 456
        values = (C.c_ulong * 2)(8, 9)

        def query(display, window, pointer, count):
            C.cast(pointer, C.POINTER(C.POINTER(C.c_ulong)))[0] = C.cast(values, C.POINTER(C.c_ulong))
            C.cast(count, C.POINTER(C.c_int))[0] = 0 if outcome == 'empty' else 2
            return 0 if outcome == 'failed-with-allocation' else 1

        ui.x = SimpleNamespace(XGetWMProtocols=query, XFree=Mock())
        error = None
        try:
            result = ui.window_protocols()
        except Exception as caught:
            error, result = type(caught).__name__, None
        freed_address = C.cast(ui.x.XFree.call_args.args[0], C.c_void_p).value
        passed = ui.x.XFree.call_count == 1 and freed_address == C.addressof(values)
        passed = passed and ((outcome == 'empty' and result == [] and error is None)
                             or (outcome == 'valid' and result == [8, 9] and error is None)
                             or (outcome == 'failed-with-allocation' and error == 'RuntimeError'))
        rows.append(dict(control='wm-protocols-' + outcome, passed=passed, atoms=result, error=error,
                         frees=ui.x.XFree.call_count))
    # Pure LP64 type-layout model, NOT a test of native Linux libX11 or a compiled C ABI.
    class Data(C.Union):
        _fields_ = [('b', C.c_char * 20), ('s', C.c_short * 10), ('l', C.c_int64 * 5)]
    class Client(C.Structure):
        _fields_ = [('type', C.c_int32), ('serial', C.c_uint64), ('send_event', C.c_int32),
                    ('display', C.c_void_p), ('window', C.c_uint64), ('message_type', C.c_uint64),
                    ('format', C.c_int32), ('data', Data)]
    offsets = {name: getattr(Client, name).offset for name, _ in Client._fields_}
    expected = dict(type=0, serial=8, send_event=16, display=24, window=32, message_type=40, format=48, data=56)
    rows.append(dict(control='LP64-client-message-layout-model', passed=C.sizeof(Client) == 96 and offsets == expected,
                     sizeof=C.sizeof(Client), offsets=offsets, limitation='Model only; Windows native c_long is 32-bit'))
    return rows


def original_failure_controls():
    evidence = ROOT.parent / 'sightbreak-v3-evidence/ci-39880125007'
    records = []
    for phase in ('05-after-fire', '06-after-reload'):
        files = [evidence / f'flow-screens-20261024/{phase}-{label}-ocr.stdout.txt' for label in ('status', 'ammo')]
        text = [path.read_text(encoding='utf-8') for path in files]
        try:
            parsed, error = parse_hud_text(*text), None
        except ValueError as caught:
            parsed, error = None, str(caught)
        records.append(dict(phase=phase, texts=text, parsed=parsed, error=error,
                            control_passed=(parsed is not None) is phase.startswith('05'),
                            files=[dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest()) for path in files]))
    with zipfile.ZipFile(evidence / 'artifact-12470681259.zip') as archive:
        selected = {}
        for member in ('v3-export-network/authority.json', 'v3-export-network/watchdog.log',
                       'v3-export-network/watchdog.process.json', 'v3-export-offline/watchdog.log'):
            info = archive.getinfo(member)
            assert info.file_size < 128 * 1024, 'Refuse bulk archive reads'
            data = archive.read(info)
            selected[member] = dict(bytes=len(data), sha256=hashlib.sha256(data).hexdigest(),
                                    text=data.decode('utf-8', errors='replace'))
        info = archive.getinfo('v3-export-network/08-settled.png')
        selected[info.filename] = dict(bytes=info.file_size, crc32=info.CRC, image_not_extracted=True)
    return dict(hud_controls=records, selected_archive_members=selected)


if __name__ == '__main__':
    snapshot('controls-before')
    rows = []
    for mode in ('network', 'offline'):
        faults = ['none', 'source-mutated-at-native-init', 'source-mutated-before-final-audit',
                  'unadvertised-close', 'native-close-hang', 'native-close-exit7',
                  'native-log-leak', 'early-zero-exit-before-close']
        faults += (['server-exit7', 'authority-false'] if mode == 'network' else
                   ['pause-not-consumed', 'network-pause-label', 'resume-not-consumed',
                    'reload-input-ignored', 'eliminated-after-fire', 'eliminated-after-reload',
                    'zero-health-after-reload', 'ammo-not-conserved'])
        for fault in faults:
            row = Scenario(mode, fault).run()
            rows.append(row)
            print(json.dumps(row), flush=True)
    protocols = protocol_controls()
    originals = original_failure_controls()
    result = dict(synthetic_only=True, controllers=rows, protocols=protocols, original_failure_controls=originals)
    (OUT / 'controls.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    snapshot('controls-after')
    assert all(row['control_passed'] for row in rows), 'A synthetic controller control failed -- inspect retained evidence'
    assert all(row['passed'] for row in protocols)
    assert all(row['control_passed'] for row in originals['hud_controls'])
