#!/usr/bin/env python3
"""Native OCR resource diagnostic only; never a gameplay acceptance result."""
import argparse
import csv
import ctypes as C
from ctypes import wintypes
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import subprocess
import time
import zipfile

from PIL import Image
from build_manifest import BUILDS, OUTPUTS, source, validate_record
from verify_integration_export import WinUI, windows_job


ARTIFACT_ID = 12379793621
ARCHIVE_SHA256 = 'e8d1db82d3d852cd681d5ee3e7aa996c6f3d518c2c92144026688d4db76373cd'


def sha(data):
    return hashlib.sha256(data).hexdigest()


class ProcessCpu:
    """Read real Windows process CPU times while retaining a query handle."""
    def __init__(self, pid, *, set_priority=False):
        self.kernel = C.WinDLL('kernel32', use_last_error=True)
        self.kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        self.kernel.OpenProcess.restype = wintypes.HANDLE
        self.kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        self.kernel.CloseHandle.restype = wintypes.BOOL
        self.kernel.GetProcessTimes.argtypes = [wintypes.HANDLE] + [C.POINTER(wintypes.FILETIME)] * 4
        self.kernel.GetProcessTimes.restype = wintypes.BOOL
        self.kernel.GetPriorityClass.argtypes = [wintypes.HANDLE]
        self.kernel.GetPriorityClass.restype = wintypes.DWORD
        self.kernel.SetPriorityClass.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        self.kernel.SetPriorityClass.restype = wintypes.BOOL
        self.kernel.GetProcessAffinityMask.argtypes = [wintypes.HANDLE, C.POINTER(C.c_size_t), C.POINTER(C.c_size_t)]
        self.kernel.GetProcessAffinityMask.restype = wintypes.BOOL
        self.handle = self.kernel.OpenProcess(0x1000 | 0x400 | (0x200 if set_priority else 0), False, pid)
        if not self.handle:
            raise C.WinError(C.get_last_error())

    def read(self):
        created, exited, kernel, user = [wintypes.FILETIME() for _ in range(4)]
        if not self.kernel.GetProcessTimes(self.handle, C.byref(created), C.byref(exited), C.byref(kernel), C.byref(user)):
            raise C.WinError(C.get_last_error())
        return ((kernel.dwHighDateTime << 32) + kernel.dwLowDateTime
                + (user.dwHighDateTime << 32) + user.dwLowDateTime) / 10_000_000

    def close(self):
        self.kernel.CloseHandle(self.handle)

    def priority(self):
        value = self.kernel.GetPriorityClass(self.handle)
        if not value:
            raise C.WinError(C.get_last_error())
        return value

    def set_priority(self, value):
        if not self.kernel.SetPriorityClass(self.handle, value):
            raise C.WinError(C.get_last_error())

    def affinity(self):
        process, system = C.c_size_t(), C.c_size_t()
        if not self.kernel.GetProcessAffinityMask(self.handle, C.byref(process), C.byref(system)):
            raise C.WinError(C.get_last_error())
        return {'process_mask': hex(process.value), 'system_mask': hex(system.value),
                'scope': 'Read only; diagnostic never changes affinity'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--tesseract', required=True)
    parser.add_argument('--comparison', choices=('threads', 'priority'), default='threads')
    args = parser.parse_args()
    if os.name != 'nt':
        parser.error('Execute this diagnostic on native Windows')
    args.output.mkdir(parents=True, exist_ok=False)
    archive_bytes = args.archive.read_bytes()
    if sha(archive_bytes) != ARCHIVE_SHA256:
        raise RuntimeError('Retained failed attempt archive checksum changed')
    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
        if sum(entry.file_size for entry in archive.infolist()) > 32 * 1024 * 1024:
            raise RuntimeError('Evidence archive exceeded its bounded extraction budget')
        for name in ('06d-funded-requisition.png', 'ocr-current.png'):
            (args.output / name).write_bytes(archive.read('offline-input/' + name))
        retained_source = json.loads(archive.read('windows/source.json'))
    # Exactly the existing ocr_words preprocessing, including its reference
    # resolution, threshold, grayscale conversion and2560x1440 analysis copy.
    raw_input = args.output / '06d-funded-requisition.png'
    with Image.open(raw_input) as native:
        native_size = list(native.size)
        analysis = native.convert('L').point(lambda value: 0 if value > 145 else 255)
        analysis = analysis.resize((1280 * 2, 720 * 2))
    payload = io.BytesIO()
    analysis.save(payload, format='PNG')
    analysis_bytes = payload.getvalue()
    (args.output / 'analysis-input.png').write_bytes(analysis_bytes)
    version = subprocess.run([args.tesseract, '--version'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=10)
    (args.output / 'tesseract-version.log').write_bytes(version.stdout)
    if version.returncode:
        raise RuntimeError('Tesseract version command failed')
    before = source()
    manifest = validate_record('windows', before)
    report = {'scope': __doc__, 'comparison': args.comparison, 'source': before, 'artifact_source': manifest,
              'retained_failed_attempt_artifact': ARTIFACT_ID, 'archive_sha256': ARCHIVE_SHA256,
              'retained_export_source': retained_source['source_commit'],
              'raw_input_sha256': sha(raw_input.read_bytes()), 'native_size': native_size,
              'actual_failed_ocr_capture_sha256': sha((args.output / 'ocr-current.png').read_bytes()),
              'analysis_input_sha256': sha(analysis_bytes), 'analysis_size': list(analysis.size),
              'host': platform.platform(), 'logical_cpu_count': os.cpu_count(),
              'default_omp_environment': {name: os.environ.get(name) for name in ('OMP_THREAD_LIMIT', 'OMP_NUM_THREADS')},
              'trial_timeout_seconds': 20,
              'time_scale_scope': 'Ordinary menu only; no active match or time_scale setter/injection; gameplay physics unmeasured',
              'trials': []}

    def save():
        (args.output / 'results.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')

    def trial(condition, setting, repeat, menu_cpu=None):
        environment = os.environ.copy()
        if setting == 'limit1':
            environment['OMP_THREAD_LIMIT'] = '1'
        command = [args.tesseract, 'stdin', 'stdout', '--psm', '11', 'tsv']
        original_priority = menu_cpu.priority() if menu_cpu else None
        if menu_cpu and client.poll() is not None:
            raise RuntimeError('Native menu exited before contention measurement')
        if menu_cpu and args.comparison == 'priority':
            # NORMAL_PRIORITY_CLASS versus BELOW_NORMAL_PRIORITY_CLASS; owned
            # game process only. OCR/controller priority and affinity unchanged.
            menu_cpu.set_priority(0x4000 if setting == 'below-normal-game' else 0x20)
        cpu = process = None
        timed_out = False
        try:
            menu_priority = menu_cpu.priority() if menu_cpu else None
            menu_affinity = menu_cpu.affinity() if menu_cpu else None
            native_before = ui.diagnostics() if menu_cpu else None
            menu_interval_started = time.monotonic()
            menu_before = menu_cpu.read() if menu_cpu else None
            started = time.monotonic()
            process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=environment)
            cpu = ProcessCpu(process.pid)
            ocr_priority, ocr_affinity = cpu.priority(), cpu.affinity()
            try:
                output, errors = process.communicate(input=analysis_bytes, timeout=20)
            except subprocess.TimeoutExpired:
                timed_out = True
                process.kill()
                output, errors = process.communicate(timeout=5)
            elapsed = time.monotonic() - started
            cpu_seconds = cpu.read()
            menu_after = menu_cpu.read() if menu_cpu else None
            menu_interval_seconds = time.monotonic() - menu_interval_started
            native_after = ui.diagnostics() if menu_cpu else None
            if menu_cpu and client.poll() is not None:
                raise RuntimeError('Native menu exited during contention measurement')
        finally:
            if cpu:
                cpu.close()
            if process is not None and process.poll() is None:
                process.kill()
                process.wait(timeout=5)
            if menu_cpu:
                menu_cpu.set_priority(original_priority)
        name = f'{condition}-{repeat}-{setting}'
        (args.output / (name + '.tsv')).write_bytes(output)
        (args.output / (name + '.stderr.log')).write_bytes(errors)
        words = [row for row in csv.DictReader(io.StringIO(output.decode('utf-8', errors='replace')), delimiter='\t')
                 if row.get('text', '').strip()]
        matches = [{key: row[key] for key in ('text', 'left', 'top', 'width', 'height')}
                   for row in words if row['text'].strip().upper() == 'VECTORLINE']
        entry = {'condition': condition, 'setting': setting, 'repeat': repeat, 'command': command,
                 'omp_thread_limit': environment.get('OMP_THREAD_LIMIT'), 'timed_out': timed_out,
                 'exit_code': process.returncode, 'wall_seconds': elapsed, 'ocr_cpu_seconds': cpu_seconds,
                 'ocr_priority_class': ocr_priority, 'ocr_affinity': ocr_affinity,
                 'game_priority_class_during_trial': menu_priority,
                 'game_priority_class_restored': menu_cpu.priority() if menu_cpu else None,
                 'game_affinity': menu_affinity, 'native_before': native_before, 'native_after': native_after,
                 'menu_cpu_seconds_during_trial': menu_after - menu_before if menu_cpu else None,
                 'menu_cpu_interval_wall_seconds': menu_interval_seconds if menu_cpu else None,
                 'stdout_sha256': sha(output), 'stderr_sha256': sha(errors),
                 'output_bytes': len(output), 'word_count': len(words), 'vectorline_matches': matches}
        report['trials'].append(entry)
        save()
        print(json.dumps(entry), flush=True)

    save()
    # Counterbalance order to separate the environment setting from cold-cache
    # and later-trial effects. Keep the exact same bytes and20-second budget.
    if args.comparison == 'threads':
        for repeat, settings in enumerate((('default', 'limit1'), ('limit1', 'default')), 1):
            for setting in settings:
                trial('idle', setting, repeat)
    ui, job, client, menu_cpu = WinUI(), windows_job(), None, None
    with (args.output / 'native-menu.log').open('w', encoding='utf-8') as log:
        try:
            environment = os.environ.copy()
            for variable, part in (('APPDATA', 'roaming'), ('LOCALAPPDATA', 'local')):
                directory = args.output / 'menu-state' / part
                directory.mkdir(parents=True)
                environment[variable] = str(directory.resolve())
            command = [str(BUILDS / OUTPUTS['windows']), '--audio-driver', 'Dummy', '--position', '0,0',
                       '--resolution', f'{ui.width}x{ui.height}']
            client = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, env=environment)
            ui.pid = client.pid
            until = time.monotonic() + 60
            while time.monotonic() < until:
                if client.poll() is not None:
                    raise RuntimeError('Normal exported native menu exited early')
                if ui.focus_game() and ui.menu_visible():
                    break
                time.sleep(.1)
            else:
                raise TimeoutError('Normal exported native menu startup')
            ui.capture(args.output / 'native-menu.png')
            report['native_menu'] = {'command': command, 'pid': client.pid, 'native_state': ui.diagnostics(),
                                     'scope': 'Ordinary graphical exported menu contention, not live-match load or gameplay acceptance'}
            menu_cpu = ProcessCpu(client.pid, set_priority=args.comparison == 'priority')
            save()
            schedules = ((('default', 'limit1'), ('limit1', 'default')) if args.comparison == 'threads'
                         else (('normal-game', 'below-normal-game'), ('below-normal-game', 'normal-game')))
            for repeat, settings in enumerate(schedules, 1):
                for setting in settings:
                    trial('rendered-menu', setting, repeat, menu_cpu)
            ui.request_close()
            client.wait(timeout=20)
            report['native_menu']['normal_exit'] = client.returncode
            if client.returncode:
                raise RuntimeError('Normal exported menu did not exit cleanly')
        finally:
            if menu_cpu:
                menu_cpu.close()
            if client is not None and client.poll() is None:
                client.terminate()
                try:
                    client.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    client.kill()
                    client.wait(timeout=5)
                report.setdefault('native_menu', {})['forced_cleanup_exit'] = client.returncode
            ui.close()
            # windows_job owns this Python process too: retain its kill-on-close
            # handle until process exit, following the existing harness policy.
            save()
    if source() != before:
        raise RuntimeError('Source changed during OCR diagnostic')
    validate_record('windows', before)
    report['collection_complete'] = True
    save()


if __name__ == '__main__':
    main()
