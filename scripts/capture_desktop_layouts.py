#!/usr/bin/env python3
"""Capture real exported Linux layouts; screenshots still need independent review.

Each requested size owns a fresh Xvfb display and user-data directory. The menu
and a separate --demo session use raw native-window captures. The latter supplies
ordinary offline HUD/roster/settings layouts, never full-gameplay or menu-navigation
acceptance. Observation files are read-only; no save or match state is edited.
OCR preprocesses copies only, leaving original PNGs untouched.
"""
import argparse
import csv
import hashlib
import io
import json
import math
import os
from pathlib import Path
import platform
import re
import shutil
import signal
import subprocess
import sys
import time
from urllib.parse import quote

from PIL import Image, ImageGrab, ImageOps
from build_manifest import BUILDS, OUTPUTS, source, validate_record
from native_log import failed as native_log_failed
from verify_integration_export import NativeUI
import toolchain

DEFAULT_SIZES = ("960x540", "1280x720", "1920x1080", "1280x800")


def run_layout_ocr(command, data, *, stderr, timeout, receipt):
    """Limit only the OCR child; retain its original budget and failed attempts."""
    env = dict(os.environ, OMP_THREAD_LIMIT="1")
    receipt.update(timeout_seconds=timeout, thread_environment={"OMP_THREAD_LIMIT": "1"})
    started = time.monotonic()
    try:
        completed = subprocess.run(command, input=data, stdout=subprocess.PIPE,
                                   stderr=stderr, timeout=timeout, env=env)
        receipt["exit_code"] = completed.returncode
        return completed
    except Exception as error:
        receipt.update(error_type=type(error).__name__, error=str(error))
        raise
    finally:
        receipt["elapsed_seconds"] = time.monotonic() - started


def ocr_input(raw, factor, *, region=None, threshold=145):
    """Prepare an analysis copy; muted footer strokes need grayscale values."""
    image = raw.crop(region) if region is not None else raw
    gray = image.convert("L")
    analysis = (gray.point(lambda value: 0 if value > threshold else 255)
                if threshold is not None else ImageOps.invert(gray))
    dimensions = (image.width * factor, image.height * factor)
    analysis = (analysis.resize(dimensions, Image.Resampling.LANCZOS)
                if threshold is None else analysis.resize(dimensions))
    data = io.BytesIO()
    analysis.save(data, format="PNG")
    return data.getvalue()


def ocr_lines(text, factor, *, origin=(0, 0)):
    groups = {}
    for row in csv.DictReader(io.StringIO(text), delimiter="\t"):
        if not row.get("text", "").strip():
            continue
        identity = tuple(row[key] for key in ("block_num", "par_num", "line_num"))
        row = {**row, **{key: int(row[key]) / factor for key in ("left", "top", "width", "height")}}
        row["left"] += origin[0]
        row["top"] += origin[1]
        groups.setdefault(identity, []).append(row)
    return list(groups.values())


def hud_footer_region(size):
    """Map the rendered hint strip through the game's fixed 1280x720 content."""
    width, height = size
    scale = min(width / 1280, height / 720)
    left, top = (width - 1280 * scale) / 2, (height - 720 * scale) / 2
    # Keep the actual footer and its padding. Including the world/gun below it
    # merges MENU with a background edge in the retained 1280x800 native frame.
    return (math.floor(left + 320 * scale), math.floor(top + 658 * scale),
            math.ceil(left + 960 * scale), math.ceil(top + 690 * scale))


def rendered_hud_matches(groups, touch_enabled, footer_groups=()):
    normalized = lambda word: re.sub("[^A-Z]", "", word.upper())
    text_lines = ["".join(normalized(row["text"]) for row in line) for line in groups]
    words = [normalized(row["text"]) for line in groups for row in line]
    if (any("FIELDSETTINGS" in line or "FIELDMENU" in line for line in text_lines)
            or words.count("BOT") >= 4):
        return False
    if touch_enabled:
        return {"FIRE", "RELOAD", "USE"}.issubset(words)
    footer = {normalized(row["text"]) for line in footer_groups for row in line}
    return ({"TAB", "ROSTER", "ESC", "MENU"}.issubset(footer)
            and bool({"HEALTH", "ELIMINATED"} & set(words)) and "FIRE" not in words)



class LayoutProgressWatchdog:
    """Reject a stalled authority while preserving real software-renderer time."""
    def __init__(self, now, stall_seconds=5):
        self.last_advanced = now
        self.previous = None
        self.stall_seconds = stall_seconds
        self.evidence = {"stall_watchdog_seconds": stall_seconds, "samples": [],
            "scope": "Software-rendered functional capture timing; not physical-device performance acceptance",
            "basis": "Retained1920x1080 S7 advanced10.7667 simulation seconds in45 wall seconds; a0.2s simulation observation may take0.84 wall seconds. Five wall seconds allows approximately six such sample periods but rejects a frozen authority."}

    def observe(self, state, now):
        if state:
            tick, elapsed = state.get("simulation_tick"), state.get("elapsed")
            if (state.get("schema") != 1 or state.get("time_scale") != 1
                    or not isinstance(tick, int) or isinstance(tick, bool) or tick < 0
                    or not isinstance(elapsed, (int, float)) or isinstance(elapsed, bool)
                    or not math.isfinite(elapsed) or elapsed < 0):
                raise RuntimeError("Layout authority clock/schema or normal simulation speed changed")
            prior = self.previous
            if prior and (tick < prior["simulation_tick"] or elapsed < prior["elapsed"]):
                raise RuntimeError("Layout authority clock moved backward")
            if prior is None or (tick > prior["simulation_tick"] and elapsed > prior["elapsed"]):
                self.last_advanced = now
                sample = {"wall_seconds": now, "simulation_tick": tick, "elapsed": elapsed,
                          "phase": state.get("phase"), "time_left": state.get("time_left"),
                          "health": state.get("local_actor", {}).get("health")}
                if len(self.evidence["samples"]) >= 1200:
                    raise RuntimeError("Layout progress evidence exceeded its bounded sample budget")
                self.evidence["samples"].append(sample)
                self.previous = sample
        if now - self.last_advanced >= self.stall_seconds:
            raise RuntimeError("Layout authority stopped advancing within the progress watchdog")
        samples = self.evidence["samples"]
        if len(samples) > 1:
            seconds = samples[-1]["wall_seconds"] - samples[0]["wall_seconds"]
            if seconds > 0:
                self.evidence["observed_simulation_seconds_per_wall_second"] = (samples[-1]["elapsed"] - samples[0]["elapsed"]) / seconds


def sha256(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def interrupted(signum, _frame):
    # Raising, rather than exiting immediately, runs owned-process finally blocks.
    raise SystemExit(128 + signum)


class LayoutUI(NativeUI):
    """Use actual screen pixels; the inherited fixed1280 capture is not applicable."""
    def __init__(self, display, size):
        super().__init__(display)
        self.size = size

    def image(self):
        image = ImageGrab.grab(xdisplay=self.display)
        if image.size != self.size:
            raise RuntimeError(f"Native display size mismatch: {image.size} != {self.size}")
        return image

    def capture(self, path):
        self.image().save(path)

    def window_size(self):
        x, y, width, height = self.window_geometry()
        if x != 0 or y != 0:
            raise RuntimeError("Native export is offset/clipped within its exact-sized display")
        return width, height


def size_value(text):
    if not re.fullmatch(r"[0-9]+x[0-9]+", text):
        raise argparse.ArgumentTypeError("Use WIDTHxHEIGHT")
    width, height = map(int, text.split("x"))
    if not (640 <= width <= 2560 and 360 <= height <= 1600):
        raise argparse.ArgumentTypeError("Use a bounded640–2560 by360–1600 native size")
    return width, height


def capture_case(args, size, display, out, executable, expected, before, whole_deadline):
    out.mkdir()
    started = time.monotonic()
    deadline = min(whole_deadline, started + args.case_timeout)
    result = {"size": list(size), "display": display, "capture_generation_passed": False,
              "visual_acceptance": "UNVERIFIED; inspect original captures independently",
              "scope": "Actual exported Linux graphical layouts; --demo HUD is not menu navigation, objective, full-match, physical hardware or performance acceptance",
              "captures": [], "commands": [], "ocr_commands": [], "actions": [],
              "touch_toggle": "NOT_REQUESTED", "cleanup_errors": []}
    logs, processes, held = [], [], set()
    ui = live = None
    ocr_sequence = 0
    ocr_deadline = None
    trace_directory = out / "offline-trace"

    def remaining():
        value = deadline - time.monotonic()
        if value <= 0:
            raise TimeoutError("Rendered layout case/whole-flow deadline exceeded")
        return value

    def pause(seconds):
        if seconds >= remaining():
            raise TimeoutError("Rendered layout case/whole-flow deadline exceeded")
        time.sleep(seconds)

    def action(event, **details):
        entry = {"event": event, "seconds": time.monotonic() - started, **details}
        if ui is not None:
            entry["native_input"] = ui.diagnostics()
        result["actions"].append(entry)

    def launch(label, command, env=None):
        remaining()
        log = (out / (label + ".log")).open("w", encoding="utf-8")
        logs.append(log)
        process = subprocess.Popen(command, cwd=out, env=env, stdout=log,
                                   stderr=subprocess.STDOUT, start_new_session=True)
        processes.append((label, process))
        result["commands"].append({"label": label, "command": command, "pid": process.pid,
                                   "started_seconds": time.monotonic() - started})
        return process

    def wait_for(condition, seconds, label, process=None):
        until = min(deadline, time.monotonic() + seconds)
        while time.monotonic() < until:
            if process is not None and process.poll() is not None:
                raise RuntimeError(label + ": native process exited early")
            if condition():
                if time.monotonic() > until:
                    raise TimeoutError(label + ": confirmation exceeded its wall budget")
                action("observed", label=label)
                return
            time.sleep(.1)
        raise TimeoutError(label)

    def read_status():
        try:
            state = json.loads((trace_directory / "status.json").read_text())
        except (OSError, ValueError):
            return {}
        if state.get("scope") != "debug_offline_read_only_observation" or state.get("scenario") != "standard":
            raise RuntimeError("Expected ordinary read-only offline observation, without objective fixtures")
        return state

    def is_live():
        state = read_status()
        live_progress.observe(state, time.monotonic() - started)
        actor, controls = state.get("local_actor", {}), state.get("ui", {})
        return (state.get("phase") == "live" and actor.get("alive") is True and actor.get("health", 0) > 0
                and controls.get("screen") == "game" and controls.get("paused") is False)

    def save_capture(label):
        remaining()
        state_before = read_status() if live else None
        path = out / (label + ".png")
        if ui.window_size() != size:
            raise RuntimeError("Export window does not match the actual requested native size")
        ui.capture(path)
        with Image.open(path) as image:
            if image.size != size:
                raise RuntimeError("Rendered capture dimensions mismatch: " + str(image.size))
        state_after = read_status() if live else None
        result["captures"].append({"name": path.name, "sha256": sha256(path), "dimensions": list(size),
            "method": "Raw native X11 display PNG",
            "state_before": state_before, "state_after": state_after})
        action("capture", name=path.name)
        print(f"{size[0]}x{size[1]} {label}", flush=True)

    def key(name, down):
        remaining()
        ui.key(name, down)
        (held.add if down else held.discard)(name)
        action("key", key=name, down=down)

    def tap(name):
        key(name, True)
        pause(.25)
        key(name, False)
        pause(.5)

    def analyze(raw_path, label, *, region=None, factor=None, threshold=145):
        factor = factor or (3 if size[0] < 1100 else 2)
        with Image.open(raw_path) as raw:
            data = ocr_input(raw, factor, region=region, threshold=threshold)
        command = [args.tesseract, "stdin", "stdout", "--psm", "11", "tsv"]
        ocr_budget = min(12, remaining())
        if ocr_deadline is not None:
            ocr_budget = min(ocr_budget, ocr_deadline - time.monotonic())
            if ocr_budget <= 0:
                raise TimeoutError("Rendered UI OCR confirmation exceeded its wall budget")
        receipt = {"command": command, "label": label, "analysis_scale": factor,
                   "analysis_region": region, "analysis_threshold": threshold}
        try:
            with (out / "ocr-stderr.log").open("ab") as stderr:
                completed = run_layout_ocr(command, data, stderr=stderr, timeout=ocr_budget, receipt=receipt)
        finally:
            receipt["original_sha256"] = sha256(raw_path)
            result["ocr_commands"].append(receipt)
        if completed.returncode:
            raise RuntimeError("Native UI OCR failed")
        text = completed.stdout.decode("utf-8", errors="replace")
        (out / (label + ".tsv")).write_text(text)
        return ocr_lines(text, factor, origin=region[:2] if region else (0, 0))

    def lines(label, *, footer=False):
        nonlocal ocr_sequence
        remaining()
        ocr_sequence += 1
        label = label + "-" + str(ocr_sequence)
        raw_path = out / (label + "-ocr-original.png")
        ui.capture(raw_path)
        groups = analyze(raw_path, label)
        if footer:
            # Reuse the identical captured frame. A second capture could mix a
            # new HUD/footer with the earlier health/overlay evidence.
            footer_groups = analyze(raw_path, label + "-footer", region=hud_footer_region(size),
                                    factor=4, threshold=None)
            return groups, footer_groups
        return groups

    def click_text(word, label):
        for attempt in range(2):
            for line in lines(label + str(attempt)):
                target = next((row for row in line if row["text"].upper() == word), None)
                if target:
                    ui.click(round(target["left"] + target["width"] / 2), round(target["top"] + target["height"] / 2))
                    action("click", text=word)
                    pause(.6)
                    return
            pause(.4)
        raise RuntimeError("Rendered native UI control not found: " + word)

    def toggle_touch(expected_value):
        matched = None
        for line in lines("touch-toggle-" + str(expected_value)):
            words = " ".join(row["text"].upper() for row in line)
            if "SHOW" in words and "TOUCH" in words and "DESKTOP" in words:
                matched = line
                break
        if matched is None:
            raise RuntimeError("Desktop touch opt-in toggle was not rendered")
        first = matched[0]
        ui.click(round(first["left"] + first["width"] / 2), round(first["top"] + first["height"] / 2))
        action("touch_toggle_native_click", expected=expected_value)
        def saved_matches():
            try:
                profile = json.loads(saved_path.read_text())
            except (OSError, ValueError):
                return False
            if profile.get("scope") != "offline_training" or profile.get("matches") != 0:
                raise RuntimeError("Layout-only run unexpectedly changed training scope/matches")
            return profile.get("settings", {}).get("touch_visible") is expected_value
        wait_for(saved_matches, 4, "Real UI touch setting persisted", live)

    def expect_paused():
        return read_status().get("ui", {}).get("paused") is True

    def rendered_roster():
        rows = lines("tab-roster-check")
        return sum(row["text"].upper() == "BOT" for line in rows for row in line) >= 4

    def rendered_menu():
        words = {re.sub("[^A-Z]", "", row["text"].upper()) for line in lines("menu-ready") for row in line}
        return {"SIGHTBREAK", "DEPLOY"}.issubset(words)

    def rendered_field_settings():
        return any("".join(re.sub("[^A-Z]", "", row["text"].upper()) for row in line) == "FIELDSETTINGS"
                   for line in lines("field-settings-check"))

    def rendered_field_menu():
        return any("".join(re.sub("[^A-Z]", "", row["text"].upper()) for row in line) == "FIELDMENU"
                   for line in lines("field-menu-check"))

    def rendered_hud(touch_enabled):
        if touch_enabled:
            return rendered_hud_matches(lines("touch-hud-check"), True)
        groups, footer = lines("keyboard-hud-check", footer=True)
        return rendered_hud_matches(groups, False, footer)

    def wait_rendered_ui(paused, label, rendered, seconds=5, touch_enabled=None, scoreboard_visible=None):
        nonlocal ocr_deadline
        # Read-only UI flags precede drawing the new screen. Require two actual
        # drawn frames after observing them, then inspect the native pixels too.
        first_frames = None
        final = {}
        def ready():
            nonlocal first_frames, final
            state = read_status()
            controls = state.get("ui", {})
            if (controls.get("screen") != "game" or controls.get("paused") is not paused
                    or touch_enabled is not None and controls.get("touch_controls") is not touch_enabled
                    or scoreboard_visible is not None and controls.get("scoreboard_visible") is not scoreboard_visible):
                first_frames = None
                return False
            frames = state.get("drawn_frames")
            if not isinstance(frames, int) or isinstance(frames, bool) or frames < 0:
                raise RuntimeError("Rendered layout fence requires an actual drawn-frame observation")
            if first_frames is None:
                first_frames = frames
            if frames < first_frames:
                raise RuntimeError("Rendered layout frame clock moved backward")
            if frames < first_frames + 2 or not rendered():
                return False
            final = state
            return True
        previous_deadline = ocr_deadline
        ocr_deadline = min(deadline, time.monotonic() + seconds)
        try:
            wait_for(ready, seconds, label, live)
        finally:
            ocr_deadline = previous_deadline
        action("rendered_ui_fence", label=label, first_drawn_frames=first_frames,
               final_drawn_frames=final["drawn_frames"], state=final)

    try:
        validate_record("linux", before)
        if sha256(executable) != expected:
            raise RuntimeError("Extracted/exported executable changed or mismatches source receipt")
        env = dict(os.environ, DISPLAY=display, LIBGL_ALWAYS_SOFTWARE="1", LP_NUM_THREADS="2",
                   DBUS_SESSION_BUS_ADDRESS="unix:path=" + quote(str(out / "unavailable-session-bus"), safe="/._-"))
        for variable, part in (("XDG_DATA_HOME", "data"), ("XDG_CONFIG_HOME", "config"), ("XDG_CACHE_HOME", "cache")):
            path = out / "state" / part
            path.mkdir(parents=True, exist_ok=True)
            env[variable] = str(path)
        saved_path = Path(env["XDG_DATA_HOME"]) / "godot/app_userdata/SIGHTBREAK/offline_training.json"
        socket = Path("/tmp/.X11-unix/X" + display[1:])
        if socket.exists():
            raise RuntimeError("Selected isolated display already exists")
        xvfb = launch("xvfb", [args.xvfb, display, "-screen", "0", f"{size[0]}x{size[1]}x24", "-nolisten", "tcp"])
        wait_for(socket.exists, 5, "Fresh Xvfb display", xvfb)
        # Seed standard close atoms before either Godot client caches them.
        ui = LayoutUI(display, size)
        flags = ["--audio-driver", "Dummy", "--accessibility", "disabled", "--accessibility-driver", "dummy",
                 "--position", "0,0", "--resolution", f"{size[0]}x{size[1]}"]
        # The viewport texture can retain1280x720 content in a1280x800 native
        # window. Qualify actual OS bounds/pixels, including any letterboxing.
        menu = launch("menu", [str(executable), *flags], env)
        wait_for(ui.focus_game, 20, "Actual exported menu window", menu)
        if ui.window_size() != size:
            raise RuntimeError("Native menu window geometry differs from requested size")
        wait_for(rendered_menu, 15, "Actual rendered main menu", menu)
        save_capture("01-menu")
        ui.request_close()
        menu.wait(timeout=min(12, remaining()))
        menu_log = (out / "menu.log").read_text(errors="replace")
        result["native_menu_exit"] = menu.returncode
        if menu.returncode != 0 or native_log_failed(menu_log):
            raise RuntimeError("Actual rendered exported menu did not complete cleanly")
        live = launch("live-layout", [str(executable), *flags, "--", "--demo", "--offline-validation",
                      "--offline-trace-dir=" + str(trace_directory)], env)
        wait_for(ui.focus_game, 20, "Actual exported HUD window", live)
        if ui.window_size() != size:
            raise RuntimeError("Native export window geometry differs from requested size")
        wait_for(lambda: read_status().get("ui", {}).get("screen") == "game", 10, "Read-only standard offline readiness", live)
        if expect_paused():
            tap("Escape")
            action("explicit_resume_after_initial_focus")
        # Fifteen simulation seconds of ordinary buy time took more than45
        # wall seconds on the retained1920x1080 llvmpipe runner. Keep normal
        # clocks and a finite case deadline; reject true stalls separately.
        live_progress = LayoutProgressWatchdog(time.monotonic() - started)
        result["live_phase_wait"] = live_progress.evidence
        wait_for(is_live, remaining(), "Ordinary living-player live phase", live)
        result["live_phase_wait"]["live_observed"] = True
        save_capture("02-live-hud")
        key("Tab", True)
        pause(.7)
        wait_rendered_ui(False, "Actual rendered Tab roster", rendered_roster, seconds=8, scoreboard_visible=True)
        save_capture("03-tab-roster")
        key("Tab", False)
        tap("Escape")
        wait_rendered_ui(True, "Actual rendered paused field menu", rendered_field_menu)
        save_capture("04-field-menu")
        click_text("SETTINGS", "field-settings-control")
        wait_rendered_ui(True, "Actual rendered field settings", rendered_field_settings, seconds=8)
        save_capture("05-field-settings")
        if args.touch_toggle and size == (1280, 720):
            toggle_touch(True)
            tap("Escape")  # Explicit native dismissal/resume, not a state call.
            wait_rendered_ui(False, "Explicit rendered touch-HUD resume", lambda: rendered_hud(True), touch_enabled=True)
            save_capture("06-touch-hud-opt-in")
            tap("Escape")
            wait_rendered_ui(True, "Actual rendered touch-mode field menu", rendered_field_menu)
            click_text("SETTINGS", "touch-field-settings-control")
            wait_rendered_ui(True, "Actual rendered touch-mode field settings", rendered_field_settings, seconds=8)
            toggle_touch(False)
            tap("Escape")
            wait_rendered_ui(False, "Explicit rendered keyboard/mouse resume", lambda: rendered_hud(False), touch_enabled=False)
            save_capture("07-keyboard-mouse-restored")
            result["touch_toggle"] = "Real settings click persisted on/off; explicit resumes and rendered touch HUD captured"
        if live.poll() is not None:
            raise RuntimeError("Export exited before normal desktop close")
        ui.request_close()
        live.wait(timeout=min(12, remaining()))
        if live.returncode != 0 or native_log_failed((out / "live-layout.log").read_text(errors="replace")):
            raise RuntimeError("Actual layout session did not exit cleanly")
        result["native_menu_exit"] = menu.returncode
        result["native_live_exit"] = live.returncode
        result["exit_method"] = "Menu and live session completion-driven WM_DELETE_WINDOW"
        validate_record("linux", before)
        if source() != before or sha256(executable) != expected:
            raise RuntimeError("Source/executable changed during rendered layout capture")
        result["capture_generation_passed"] = True
    except SystemExit as error:
        result.update(capture_generation_passed=False, interrupted=True, error=str(error))
        raise
    except Exception as error:
        result["error"] = str(error)
    finally:
        if ui is not None:
            for name in list(held):
                try:
                    ui.key(name, False)
                except Exception as error:
                    result["cleanup_errors"].append("Release key: " + str(error))
            try:
                ui.button(False)
                ui.close()
            except Exception as error:
                result["cleanup_errors"].append("Native UI cleanup: " + str(error))
        for label, process in reversed(processes):
            try:
                os.killpg(process.pid, 0)
                if label != "xvfb":
                    result["cleanup_errors"].append(label + ": forced cleanup or descendant after root exit")
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait(timeout=3)
                result["cleanup_errors"].append(label + ": required SIGKILL")
            try:
                os.killpg(process.pid, 0)
                result["cleanup_errors"].append(label + ": owned group survives cleanup")
            except ProcessLookupError:
                pass
        for handle in logs:
            handle.close()
        for entry, (_, process) in zip(result["commands"], processes):
            entry["exit_code"] = process.returncode
        if result["cleanup_errors"]:
            result["capture_generation_passed"] = False
        result["elapsed_seconds"] = time.monotonic() - started
        write_json(out / "results.json", result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--executable", type=Path, help="Optional extracted Linux ELF; bytes must match the original export receipt")
    parser.add_argument("--sizes", type=size_value, nargs="+", default=[size_value(size) for size in DEFAULT_SIZES])
    parser.add_argument("--display-base", type=int, default=130)
    parser.add_argument("--case-timeout", type=float, default=120)
    parser.add_argument("--timeout", type=float, default=520)
    parser.add_argument("--xvfb", default=os.environ.get("XVFB_BIN") or shutil.which("Xvfb"))
    parser.add_argument("--tesseract", default=os.environ.get("TESSERACT_BIN") or shutil.which("tesseract"))
    parser.add_argument("--touch-toggle", action="store_true", help="At1280x720, opt in/out through real field settings and capture touch HUD")
    args = parser.parse_args()
    if platform.system() != "Linux" or not args.xvfb or not args.tesseract:
        parser.error("Requires native Linux, Xvfb/XTest, Pillow and Tesseract; other platform layouts remain UNVERIFIED")
    if not 0 < args.case_timeout <= 120 or not 0 < args.timeout <= 600 or not 1 <= args.display_base <= 1000:
        parser.error("Use case deadline1–120seconds, whole deadline1–600seconds and display base1–1000")
    if len(set(args.sizes)) != len(args.sizes):
        parser.error("Select unique sizes")
    for signum in (signal.SIGTERM, signal.SIGINT):
        signal.signal(signum, interrupted)
    out = args.output.resolve()
    if out.is_relative_to(toolchain.ROOT / "game") or out.is_relative_to(BUILDS / "linux"):
        parser.error("Layout evidence must stay outside game/ and the shipped Linux payload")
    if out.exists() and any(out.iterdir()):
        parser.error("Preserve earlier evidence; use a fresh output directory")
    before = source()
    manifest = validate_record("linux", before)
    executable = (args.executable or BUILDS / OUTPUTS["linux"]).resolve()
    expected = manifest["artifact"]["sha256"]
    if sha256(executable) != expected:
        parser.error("Extracted/exported executable does not match exact-source receipt")
    started = time.monotonic()
    out.mkdir(parents=True, exist_ok=True)
    report = {"source": before, "artifact_source": manifest, "engine": toolchain.verify_engine(),
              "host": platform.platform(), "controller_command": [sys.executable, *sys.argv],
              "executable": str(executable), "executable_sha256": expected,
              "requested_sizes": [list(size) for size in args.sizes], "cases": [],
              "visual_acceptance": "UNVERIFIED; independent original-image review required",
              "automation_accessibility": "Disabled driver and unavailable isolated session bus; accessibility/portals UNVERIFIED"}
    try:
        for index, size in enumerate(args.sizes):
            case_path = out / f"{size[0]}x{size[1]}"
            try:
                result = capture_case(args, size, ":" + str(args.display_base + index),
                                      case_path, executable, expected, before, started + args.timeout)
            except SystemExit as error:
                report["interrupted"] = str(error)
                if (case_path / "results.json").is_file():
                    report["cases"].append(json.loads((case_path / "results.json").read_text()))
                raise
            report["cases"].append(result)
            write_json(out / "results.json", report)
    finally:
        report["exact_source_unchanged"] = source() == before
        report["capture_generation_passed"] = ("interrupted" not in report and report["exact_source_unchanged"]
            and len(report["cases"]) == len(args.sizes) and all(case["capture_generation_passed"] for case in report["cases"]))
        report["elapsed_seconds"] = time.monotonic() - started
        write_json(out / "results.json", report)
    print(json.dumps({key: report[key] for key in ("requested_sizes", "capture_generation_passed", "visual_acceptance", "exact_source_unchanged")}), flush=True)
    return 0 if report["capture_generation_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
