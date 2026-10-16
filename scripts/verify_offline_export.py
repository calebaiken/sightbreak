#!/usr/bin/env python3
"""Drive the actual Linux export through offline play and return to its menu.

Native screenshots require independent visual inspection. This does not read
private game state or establish physical-device performance. Normal termination
uses the engine's frame budget; interrupted attempts remain failures.
"""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time

from build_manifest import ROOT, source
from PIL import Image

from native_log import failed
from verify_integration_export import NativeUI


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--display', default=':104')
    parser.add_argument('--xvfb', default=os.environ.get('XVFB_BIN') or shutil.which('Xvfb'))
    parser.add_argument('--quit-after', type=int, default=300)
    parser.add_argument('--timeout', type=float, default=300)
    parser.add_argument('--tesseract', default=shutil.which('tesseract'))
    args = parser.parse_args()
    if not args.tesseract:
        parser.error('Tesseract is required to verify rendered ammunition and living-player state')
    if not args.xvfb or not re.fullmatch(r':[0-9]+', args.display):
        parser.error('Supply Xvfb and an isolated numbered display')
    if args.quit_after <= 0 or args.timeout <= 0:
        parser.error('Frame and timeout budgets must be positive')
    socket = Path('/tmp/.X11-unix/X' + args.display[1:])
    if socket.exists():
        parser.error('Display already in use')
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    if (out / 'results.json').exists():
        parser.error('Use a new output directory for each attempt')
    executable = ROOT / 'builds/linux/sightbreak.x86_64'
    manifest = json.loads((executable.parent / 'source.json').read_text())
    before = source()
    digest = hashlib.file_digest(executable.open('rb'), 'sha256').hexdigest()
    if before['source_content_sha256'] != manifest['source_content_sha256'] or digest != manifest['artifact']['sha256']:
        raise RuntimeError('Export does not match source and manifest')
    logs, processes, events = [], [], []
    ui = client = None
    started = time.monotonic()

    def launch(name, command, env=None):
        log = (out / (name + '.log')).open('w')
        logs.append(log)
        process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, env=env, cwd=out)
        processes.append(process)
        return process

    def wait_for(condition, seconds, label):
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            if condition():
                return
            if client is not None and client.poll() is not None:
                raise RuntimeError(label + ': export exited early')
            time.sleep(.1)
        raise TimeoutError(label)

    def capture(name):
        ui.capture(out / (name + '.png'))
        events.append(name)
        (out / 'actions.json').write_text(json.dumps(events, indent=2) + '\n')
        print(name, flush=True)

    def read_hud(name):
        image = Image.open(out / (name + '.png'))
        def text(box):
            crop = image.crop(box)
            crop = crop.resize((crop.width * 3, crop.height * 3))
            data = io.BytesIO()
            crop.save(data, format='PNG')
            return subprocess.check_output([args.tesseract, 'stdin', 'stdout', '--psm', '6'], input=data.getvalue(), stderr=subprocess.DEVNULL).decode()
        status = text((0, 630, 450, 720))
        ammo_text = text((980, 625, 1280, 710))
        match = re.search(r'(\d+)\s*/\s*(\d+)', ammo_text)
        if 'ELIMINATED' in status.upper() or 'SPECTATING' in status.upper() or match is None:
            raise RuntimeError('Rendered living-player/ammunition check failed: ' + repr((status, ammo_text)))
        return {'ammo': int(match[1]), 'reserve': int(match[2]), 'status_ocr': status, 'ammo_ocr': ammo_text}

    def tap(key):
        ui.key(key, True)
        time.sleep(.3)
        ui.key(key, False)
        time.sleep(1)

    try:
        launch('xvfb', [args.xvfb, args.display, '-screen', '0', '1280x720x24', '-nolisten', 'tcp'])
        wait_for(socket.exists, 5, 'Xvfb readiness')
        env = dict(os.environ, DISPLAY=args.display, LIBGL_ALWAYS_SOFTWARE='1', LP_NUM_THREADS='2')
        for key, directory in [('XDG_DATA_HOME', 'data'), ('XDG_CONFIG_HOME', 'config'), ('XDG_CACHE_HOME', 'cache')]:
            path = out / 'state' / directory
            path.mkdir(parents=True, exist_ok=True)
            env[key] = str(path)
        client = launch('client', [str(executable), '--audio-driver', 'Dummy', '--quit-after', str(args.quit_after)], env)
        ui = NativeUI(args.display)
        wait_for(lambda: ui.focus_game() and ui.menu_visible(), 60, 'Native menu')
        capture('01-menu')
        for _ in range(3):
            ui.click(248, 319)
            time.sleep(1)
            if not ui.menu_visible():
                break
        if ui.menu_visible():
            raise RuntimeError('Offline deployment did not leave menu')
        time.sleep(3)
        capture('02-offline-spawn')
        tap('b')
        capture('03-requisition')
        tap('Escape')
        ui.key('d', True)
        time.sleep(.3)
        ui.key('d', False)
        ui.t.XTestFakeMotionEvent(ui.d, 0, 690, 350, 0)
        ui.x.XFlush(ui.d)
        capture('04-move-aim')
        # React to the real phase announcement; waiting a fixed wall duration
        # can leave a human eliminated before the input checks even begin.
        wait_for(lambda: 'MATCH: Round live. Secure Relay Yard.' in (out / 'client.log').read_text(), 60, 'Actual offline live phase')
        ui.focus_game()
        time.sleep(.25)
        for _ in range(2):
            ui.button(True)
            time.sleep(1.0)
            ui.button(False)
            time.sleep(.35)
        capture('05-after-fire')
        fired_hud = read_hud('05-after-fire')
        if not 0 < fired_hud['ammo'] < 15 or fired_hud['reserve'] != 60:
            raise RuntimeError('Native fire did not deplete the initial sidearm magazine')
        ui.key('r', True)
        time.sleep(1.0)
        ui.key('r', False)
        time.sleep(2.5)
        capture('06-after-reload')
        reloaded_hud = read_hud('06-after-reload')
        if reloaded_hud['ammo'] != 15 or reloaded_hud['reserve'] >= fired_hud['reserve'] or sum(reloaded_hud[k] for k in ('ammo', 'reserve')) != sum(fired_hud[k] for k in ('ammo', 'reserve')):
            raise RuntimeError('Native offline reload did not conserve rendered ammunition')
        tap('Escape')
        capture('07-field-menu')
        ui.click(640, 318)
        wait_for(ui.menu_visible, 30, 'Return from offline match')
        capture('08-return-menu')
        client.wait(timeout=max(1, args.timeout - (time.monotonic() - started)))
        if client.returncode != 0 or failed((out / 'client.log').read_text()):
            raise RuntimeError('Export failed clean termination or native log gate')
        if before != source():
            raise RuntimeError('Source changed during offline validation')
        result = {'source': before, 'executable_sha256': digest, 'events': events,
                  'exit': client.returncode, 'clean_exit': True, 'passed': True,
                  'fired_hud': fired_hud, 'reloaded_hud': reloaded_hud,
                  'controller_sha256': hashlib.file_digest(Path(__file__).open('rb'), 'sha256').hexdigest(),
                  'limits': 'Screenshots require visual review; no private authority instrumentation or mobile performance claim.'}
        (out / 'results.json').write_text(json.dumps(result, indent=2) + '\n')
        print(json.dumps(result), flush=True)
    finally:
        if ui:
            ui.close()
        for process in reversed(processes):
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
        for log in logs:
            log.close()


if __name__ == '__main__':
    main()
