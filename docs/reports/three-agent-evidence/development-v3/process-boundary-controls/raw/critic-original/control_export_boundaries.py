"""Synthetic boundary controls, NOT native/export evidence. Never launch an engine.

Uses the captured review source. X11/process/image boundaries are replaced with
explicit fixtures; the OCR-hang control launches only the isolated CPython.
"""
from contextlib import ExitStack
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import patch
import hashlib
import json
import os
import signal
import subprocess
import sys
import time

OUT = Path(__file__).resolve().parent
ROOT = Path(r"C:\Users\blith\AppData\Local\Temp\opencode\sightbreak-v3")
sys.path[:0] = [str(OUT / "source/scripts"), str(ROOT / "scripts")]
import build_manifest as manifest
import verify_integration_export as integration

IDENTITY = dict(source_commit="SYNTHETIC-NOT-A-GIT-COMMIT", source_game_tree="SYNTHETIC-TREE",
                source_content_sha256="SYNTHETIC-GAME-HASH", source_validation_sha256="SYNTHETIC-TOOLING-HASH",
                source_game_dirty=False, source_dirty=False)
REAL_POPEN = subprocess.Popen
REAL_CHECK_OUTPUT = subprocess.check_output
REAL_SLEEP = time.sleep


def save(path, obj):
    path.write_text(json.dumps(obj, indent=2) + "\n")


def create_export(case):
    root = case / "synthetic-project"
    builds = root / "builds"
    with patch.object(manifest, "ROOT", root), patch.object(manifest, "BUILDS", builds), \
            patch.object(manifest, "source", lambda: dict(IDENTITY)):
        manifest.begin("linux")
        executable = builds / "linux/sightbreak.x86_64"
        executable.write_bytes(b"SYNTHETIC CONTROL A - NOT A NATIVE EXECUTABLE\n")
        manifest.finish("linux")
    return root, executable


class FixtureProcess:
    def __init__(self):
        self.returncode = None

    def poll(self):
        return self.returncode

    def wait(self, timeout=None):
        self.returncode = 0
        return 0

    def terminate(self):
        self.returncode = 0

    def kill(self):
        self.returncode = -1


class FixtureUI:
    def __init__(self, display):
        self.menu = True
        self.d = 1
        self.t = SimpleNamespace(XTestFakeMotionEvent=lambda *args: None)
        self.x = SimpleNamespace(XFlush=lambda *args: None)

    def focus_game(self):
        return True

    def menu_visible(self):
        return self.menu

    def click(self, x, y):
        self.menu = (x, y) == (640, 318)

    def capture(self, path):
        path.write_bytes(b"SYNTHETIC CONTROL PLACEHOLDER - NOT A SCREENSHOT\n")

    def button(self, down):
        pass

    def key(self, key, down):
        pass

    def request_close(self):
        pass

    def close(self):
        pass


def fixture_boundaries(stack, module, case, root, executable, mutate=False):
    display_ready = {"ready": False}
    actual_exists = Path.exists
    def exists(path):
        if str(path).replace("\\", "/").startswith("/tmp/.X11-unix/X"):
            return display_ready["ready"]
        return actual_exists(path)

    def popen(command, *args, **kwargs):
        if str(command[0]) == sys.executable:
            return REAL_POPEN(command, *args, **kwargs)
        output = kwargs["stdout"]
        name = Path(output.name).stem
        if name == "xvfb":
            display_ready["ready"] = True
        elif name == "server":
            output.write("SIGHTBREAK_SERVER_READY\nEXPORT_UI_ACK_READY\n"
                         "EXPORT_UI_RELOAD_STARTED\nEXPORT_UI_RELOAD_COMPLETED\n")
            output.flush()
            save(Path(kwargs["cwd"]) / "unused.json", {"synthetic_control": True})
            evidence = next(arg.removeprefix("--output=") for arg in command if arg.startswith("--output="))
            save(Path(evidence) / "authority.json", {"passed": True, "reload_trigger": "SYNTHETIC-CONTROL",
                                                    "synthetic_control_not_native_evidence": True})
        elif name == "client":
            if mutate:
                executable.write_bytes(b"SYNTHETIC CONTROL B - REPLACED AFTER PREFLIGHT\n")
                save(case / "mutation.json", {"stage": "client Popen boundary, after actual frozen_export",
                                             "replacement_sha256": hashlib.sha256(executable.read_bytes()).hexdigest()})
            output.write("MATCH: Round live. Secure Relay Yard.\n")
            output.flush()
        else:
            raise AssertionError("Unexpected external launch: " + repr(command))
        return FixtureProcess()

    stack.enter_context(patch.object(module, "ROOT", root))
    stack.enter_context(patch.object(module, "source", lambda: dict(IDENTITY)))
    stack.enter_context(patch.object(integration, "source", lambda: dict(IDENTITY)))
    stack.enter_context(patch.object(module, "NativeUI", FixtureUI))
    stack.enter_context(patch.object(subprocess, "Popen", popen))
    stack.enter_context(patch.object(Path, "exists", exists))
    stack.enter_context(patch.object(time, "sleep", lambda seconds: None))


def mutate_control():
    case = OUT / "export-mutation-control"
    case.mkdir()
    root, executable = create_export(case)
    evidence = case / "synthetic-controller-output"
    with ExitStack() as stack:
        fixture_boundaries(stack, integration, case, root, executable, mutate=True)
        stack.enter_context(patch.object(sys, "argv", ["verify_integration_export.py", "--output", str(evidence),
                                                     "--xvfb", "SYNTHETIC-XVFB-NOT-EXECUTED", "--display", ":61971",
                                                     "--reload-mode", "keyboard", "--timeout", "10"]))
        integration.main()
    result = json.loads((evidence / "results.json").read_text())
    actual_hash = hashlib.sha256(executable.read_bytes()).hexdigest()
    finding = {"synthetic_boundary_control_not_native_evidence": True,
               "controller_passed": result["passed"], "claimed_executable_sha256": result["executable_sha256"],
               "on_disk_executable_sha256": actual_hash,
               "bug_reproduced": result["passed"] and result["executable_sha256"] != actual_hash}
    save(case / "reproduction.json", finding)
    print(json.dumps(finding, indent=2), flush=True)


class FixtureCrop:
    width = 10
    height = 10

    def crop(self, box):
        return self

    def resize(self, size):
        return self

    def save(self, stream, format):
        stream.write(b"SYNTHETIC OCR INPUT - NOT AN IMAGE")


def watchdog_child(case):
    fake_pil = ModuleType("PIL")
    fake_pil.Image = SimpleNamespace(open=lambda path: FixtureCrop())
    with patch.dict(sys.modules, {"PIL": fake_pil}):
        import verify_offline_export as offline
    root, executable = create_export(case)
    evidence = case / "synthetic-controller-output"
    def blocked_ocr(command, **kwargs):
        save(case / "ocr-call.json", {"synthetic_boundary_control_not_native_evidence": True,
                                     "requested_timeout_seconds": 0.25, "timeout_keyword_present": "timeout" in kwargs,
                                     "ocr_command": command, "elapsed_basis": "real monotonic clock"})
        child = ("from pathlib import Path; import json, os, time; "
                 f"Path({str(case / 'ocr-child.json')!r}).write_text(json.dumps({{'pid':os.getpid()}})); "
                 "time.sleep(20); print('100 HEALTH')")
        return REAL_CHECK_OUTPUT([sys.executable, "-B", "-c", child], **kwargs)
    with ExitStack() as stack:
        fixture_boundaries(stack, offline, case, root, executable)
        stack.enter_context(patch.object(subprocess, "check_output", blocked_ocr))
        stack.enter_context(patch.object(sys, "argv", ["verify_offline_export.py", "--output", str(evidence),
                                                     "--xvfb", "SYNTHETIC-XVFB-NOT-EXECUTED", "--display", ":61972",
                                                     "--tesseract", "SYNTHETIC-OCR-MAPPED-TO-CPYTHON", "--timeout", "0.25"]))
        offline.main()


def watchdog_control():
    case = OUT / "offline-watchdog-control"
    case.mkdir()
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    with (case / "controller.stdout.txt").open("wb") as stdout, (case / "controller.stderr.txt").open("wb") as stderr:
        controller = REAL_POPEN([sys.executable, "-B", str(Path(__file__).resolve()), "watchdog-child", str(case)],
                                env=env, stdout=stdout, stderr=stderr)
        deadline = time.monotonic() + 15
        marker = case / "ocr-child.json"
        while not marker.exists() and controller.poll() is None and time.monotonic() < deadline:
            REAL_SLEEP(.01)
        if not marker.exists():
            controller.kill()
            controller.wait()
            raise RuntimeError("Control did not reach OCR; inspect retained stdout/stderr")
        pid = json.loads(marker.read_text())["pid"]
        began = time.monotonic()
        REAL_SLEEP(1.25)
        elapsed = time.monotonic() - began
        finding = {"synthetic_boundary_control_not_native_evidence": True,
                   "requested_timeout_seconds": 0.25, "observed_blocked_ocr_seconds": elapsed,
                   "controller_still_running": controller.poll() is None,
                   "failure_receipt_exists_before_external_intervention": (case / "synthetic-controller-output/results.json").exists(),
                   "bug_reproduced": controller.poll() is None and elapsed > 5 * .25}
        save(case / "at-watchdog-overrun.json", finding)
        os.kill(pid, signal.SIGTERM)
        try:
            controller.wait(timeout=10)
        except subprocess.TimeoutExpired:
            controller.kill()
            controller.wait()
        finding["controller_exit_after_external_ocr_termination"] = controller.returncode
        save(case / "reproduction.json", finding)
    print(json.dumps(finding, indent=2), flush=True)


if __name__ == "__main__":
    if sys.argv[1] == "mutation":
        mutate_control()
    elif sys.argv[1] == "watchdog":
        watchdog_control()
    elif sys.argv[1] == "watchdog-child":
        watchdog_child(Path(sys.argv[2]))
    else:
        raise SystemExit("Unknown control")
