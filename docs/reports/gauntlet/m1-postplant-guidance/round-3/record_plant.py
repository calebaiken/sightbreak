#!/usr/bin/env python3
"""One bounded external recording of the validator's own fresh Xvfb display."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / '.local/postplant-priority/round-3'
OUT.mkdir(parents=True, exist_ok=False)
DISPLAY = ':118'
SOCKET = Path('/tmp/.X11-unix/X118')
SOURCE = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
if SOCKET.exists():
    raise SystemExit('Refusing to record an existing display')
native_command = ['python3', 'scripts/verify_offline_match.py', '--target', 'linux',
                  '--scenario', 'plant', '--display', DISPLAY, '--timeout', '180',
                  '--xvfb', '/workspace/tools/xvfb/usr/bin/Xvfb',
                  '--output', str(OUT / 'native-plant')]
video = OUT / 'native-plant-silent.mp4'
record_command = ['ffmpeg', '-hide_banner', '-loglevel', 'info', '-y',
                  '-f', 'x11grab', '-framerate', '10', '-video_size', '1280x720',
                  '-draw_mouse', '1', '-i', DISPLAY + '.0', '-an',
                  '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '28',
                  '-threads', '1', '-pix_fmt', 'yuv420p', '-t', '200',
                  '-movflags', '+faststart', str(video)]
receipt = {'source_commit': SOURCE, 'validator_command': native_command,
           'recorder_command': record_command, 'display_was_absent': True,
           'scope': 'Silent qualitative X11 pixels; capture adds load. No FPS, latency or audio claim.',
           'started_wall_unix_msec': time.time_ns() // 1_000_000,
           'budgets': {'whole_validator_seconds': 180, 'role_guidance_seconds': 15,
                       'plant_simulation_seconds': 3, 'device_simulation_seconds': 35}}
native = recorder = None
logs = []
started = time.monotonic()
def save():
    (OUT / 'recording-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
try:
    native_log = (OUT / 'native-plant-run.log').open('wb'); logs.append(native_log)
    native = subprocess.Popen(native_command, cwd=ROOT, stdout=native_log, stderr=subprocess.STDOUT)
    receipt['validator_pid'] = native.pid
    while True:
        if native.poll() is not None:
            raise RuntimeError('Validator exited before its owned display was ready')
        # This environment exposes PPid/cmdline but not task/<pid>/children.
        child_query = subprocess.run(['ps', '-o', 'pid=', '--ppid', str(native.pid)], capture_output=True, text=True, timeout=2)
        if child_query.returncode not in (0, 1):
            raise RuntimeError('Could not query validator-owned child processes')
        children = child_query.stdout.split()
        owned = []
        for pid in children:
            try:
                args = (Path('/proc') / pid / 'cmdline').read_bytes().decode().rstrip('\0').split('\0')
            except FileNotFoundError:
                continue
            if Path(args[0]).name == 'Xvfb' and args[1:] == [DISPLAY, '-screen', '0', '1280x720x24', '-nolisten', 'tcp']:
                status = (Path('/proc') / pid / 'status').read_text()
                parent = int(next(line for line in status.splitlines() if line.startswith('PPid:')).split()[1])
                if parent == native.pid:
                    owned.append({'pid': int(pid), 'parent_pid': parent, 'command': args})
        if len(owned) == 1 and SOCKET.exists():
            receipt['owned_xvfb'] = owned[0]
            break
        if time.monotonic() - started > 10:
            raise TimeoutError('No fresh display owned by this validator became ready')
        time.sleep(.025)
    recorder_log = (OUT / 'recording-ffmpeg.log').open('wb'); logs.append(recorder_log)
    receipt['recorder_start_wall_unix_msec'] = time.time_ns() // 1_000_000
    receipt['recorder_start_monotonic'] = time.monotonic()
    recorder = subprocess.Popen(record_command, cwd=ROOT, stdin=subprocess.PIPE,
                                stdout=recorder_log, stderr=subprocess.STDOUT)
    receipt['recorder_pid'] = recorder.pid
    save()
    receipt['validator_exit'] = native.wait(timeout=220)
    receipt['validator_end_wall_unix_msec'] = time.time_ns() // 1_000_000
except BaseException as error:
    receipt['orchestration_error'] = repr(error)
    if native is not None and native.poll() is None:
        native.terminate()
        try: native.wait(timeout=20)
        except subprocess.TimeoutExpired:
            native.kill(); native.wait(timeout=5)
finally:
    if recorder is not None:
        try:
            recorder.communicate(input=b'q\n', timeout=15)
        except (BrokenPipeError, subprocess.TimeoutExpired):
            recorder.terminate()
            try: recorder.wait(timeout=5)
            except subprocess.TimeoutExpired: recorder.kill(); recorder.wait(timeout=5)
        receipt['recorder_exit'] = recorder.returncode
        receipt['recorder_end_wall_unix_msec'] = time.time_ns() // 1_000_000
        receipt['recorder_end_monotonic'] = time.monotonic()
    for log in logs: log.close()
    receipt['seconds'] = time.monotonic() - started
    receipt['source_after'] = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    receipt['display_removed'] = not SOCKET.exists()
    if video.exists():
        receipt['video_bytes'] = video.stat().st_size
        receipt['video_sha256'] = hashlib.sha256(video.read_bytes()).hexdigest()
        probe = subprocess.run(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(video)], capture_output=True, timeout=15)
        (OUT / 'recording-ffprobe.json').write_bytes(probe.stdout)
        receipt['ffprobe_exit'] = probe.returncode
        receipt['ffprobe_stderr'] = probe.stderr.decode(errors='replace')
    save()
print(json.dumps(receipt, indent=2))
raise SystemExit(0 if receipt.get('validator_exit') == 0 and receipt.get('recorder_exit') == 0 and receipt.get('ffprobe_exit') == 0 else 1)
