"""Run corrected entry -> supervisor -> token-bound actual offline main with mocks."""
from pathlib import Path
import ctypes
from ctypes import wintypes
import json
import os
import signal
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
case = HERE / "entry-offline-ocr-control"
case.mkdir()
out = case / "evidence"
command = [sys.executable, "-B", str(HERE / "synthetic_offline_entry.py"), "--output", str(out),
           "--timeout", "1", "--xvfb", "SYNTHETIC-NOT-EXECUTED", "--display", ":61974",
           "--tesseract", "SYNTHETIC-MAPPED-TO-CPYTHON"]
env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
started = time.monotonic()
with (case / "entry.stdout.txt").open("xb") as stdout, (case / "entry.stderr.txt").open("xb") as stderr:
    process = subprocess.Popen(command, stdout=stdout, stderr=stderr, env=env)
    code = process.wait(timeout=15)
elapsed = time.monotonic() - started
result = json.loads((out / "results.json").read_text())
ocr_pid_path = case / "ocr-child-pid.json"
ocr_alive = None
if ocr_pid_path.exists():
    pid = json.loads(ocr_pid_path.read_text())["pid"]
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    handle = kernel.OpenProcess(0x1000, False, pid)
    ocr_alive = False
    if handle:
        status = wintypes.DWORD()
        if not kernel.GetExitCodeProcess(handle, ctypes.byref(status)):
            raise ctypes.WinError(ctypes.get_last_error())
        ocr_alive = status.value == 259
        kernel.CloseHandle(handle)
    if ocr_alive:
        os.kill(pid, signal.SIGTERM)
observation = {"synthetic_control_not_native_evidence": True,
               "probe_adjustment": "Actual corrected offline main under original synthetic UI fixtures; actual entry/supervisor/token handshake; OCR mapped to sleeping CPython.",
               "command": command, "entry_exit": code, "elapsed_seconds": elapsed,
               "main_reached_actual_ocr_subprocess": ocr_pid_path.exists(),
               "ocr_child_alive_after_watchdog": ocr_alive,
               "external_child_cleanup_needed": ocr_alive is True,
               "controller_passed": result.get("passed"), "watchdog_error": result.get("watchdog_error"),
               "correctly_failclosed": code != 0 and result.get("passed") is False,
               "watchdog_log": (out / "watchdog.log").read_text()}
(case / "after-observation.json").write_text(json.dumps(observation, indent=2) + "\n")
print(json.dumps(observation, indent=2), flush=True)
