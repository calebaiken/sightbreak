#!/usr/bin/env python3
"""Own the one released native lane. Never mutate staged source or method."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time

RAW = Path(__file__).resolve().parent
CONFIG = json.loads((RAW / "lane-start.json").read_text())
STAGE = Path(CONFIG["fixture_root"])
ENGINE = CONFIG["engine"]
REPO = Path("/workspace/sightbreak-touch-contrast-recovered")
PREFIX = ["taskset", "-c", "0,1,2,3", ENGINE]
events = []
owned = []


def stamp():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, obj):
    Path(path).write_text(json.dumps(obj, indent=2) + "\n")


def fence(name, label):
    root = STAGE / name
    receipt = json.loads((root / "SOURCE.json").read_text())
    rows = []
    for entry in receipt["files"] + receipt["fixture"]:
        actual = sha(root / entry["path"])
        rows.append([entry["path"], actual])
        if actual != entry["sha256"]:
            raise RuntimeError("source/UID changed: " + entry["path"])
    for filename, key in [("touch_contrast_instrumented.gd", "instrumented_sha256"),
                          ("touch_contrast_instrumented.gd.uid", "instrumented_uid_sha256")]:
        actual = sha(root / "game/tests" / filename)
        rows.append(["game/tests/" + filename, actual])
        if actual != receipt[key]:
            raise RuntimeError("instrumented source/UID changed: " + filename)
    freeze = json.loads((RAW / "SOURCE_FREEZE-r4b-r2.json").read_text())
    expected = next(x for x in freeze["fixtures"] if x["name"] == name)
    if sha(root / "SOURCE.json") != expected["manifest_sha256"]:
        raise RuntimeError("staged manifest differs from source freeze")
    result = {"time": stamp(), "source": receipt["source"], "name": name,
              "checked_paths": len(rows), "manifest_sha256": sha(root / "SOURCE.json"),
              "actual_path_hashes": rows, "unchanged": True}
    write(RAW / (label + "-" + name + "-source.json"), result)
    return result


def environment(label):
    env = dict(os.environ)
    state = RAW / "private-state" / label
    for key, part in [("XDG_DATA_HOME", "data"), ("XDG_CONFIG_HOME", "config"), ("XDG_CACHE_HOME", "cache")]:
        path = state / part
        path.mkdir(parents=True, exist_ok=True)
        env[key] = str(path)
    env.update({"SIGHTBREAK_STATE_DIR": str(state), "GODOT_SILENCE_ROOT_WARNING": "1",
                "DISPLAY": CONFIG["display"], "LP_NUM_THREADS": "2", "OMP_NUM_THREADS": "2"})
    return env


def run(label, args, source=None, timeout=300):
    if source:
        fence(source, label + "-before")
    command = PREFIX + args
    log = RAW / (label + ".log")
    record = {"label": label, "command": command, "source": source, "start_utc": stamp(),
              "environment_selectors": {k: environment(label)[k] for k in ("DISPLAY", "SIGHTBREAK_STATE_DIR", "XDG_DATA_HOME", "XDG_CONFIG_HOME", "XDG_CACHE_HOME", "LP_NUM_THREADS", "OMP_NUM_THREADS")}}
    write(RAW / (label + "-command.json"), record)
    print("START", label, flush=True)
    start = time.monotonic()
    with log.open("wb") as stream:
        process = subprocess.Popen(command, stdout=stream, stderr=subprocess.STDOUT,
                                   env=environment(label), start_new_session=True)
        owned.append(process)
        record["pid"] = process.pid
        write(RAW / (label + "-command.json"), record)
        try:
            code = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            code = 124
    output = log.read_text(errors="replace")
    record.update({"exit_code": code, "end_utc": stamp(), "wall_seconds": time.monotonic() - start,
                   "log_sha256": sha(log), "engine_errors": re.findall(r"^.*(?:SCRIPT ERROR|Parse Error|ERROR:).*$", output, re.M)})
    write(RAW / (label + "-result.json"), record)
    events.append(record)
    if source:
        fence(source, label + "-after")
    print("END", label, "exit", code, "errors", len(record["engine_errors"]), flush=True)
    if code or record["engine_errors"]:
        raise RuntimeError(label + " failed; immutable raw log retained")
    return output


def main():
    success, error, display = False, None, None
    try:
        for name in ("baseline", "candidate"):
            fence(name, "initial")
        version = run("engine-version", ["--headless", "--version"], timeout=30)
        if version.strip() != "4.7.2.stable.official.ed1daf0bf":
            raise RuntimeError("engine version mismatch: " + repr(version.strip()))
        for name in ("baseline", "candidate"):
            run("import-" + name, ["--path", str(STAGE / name / "game"), "--headless", "--editor", "--import", "--quit"], name)
        socket = Path("/tmp/.X11-unix/X131")
        if socket.exists() or Path("/tmp/.X131-lock").exists():
            raise RuntimeError("explicit display :131 is already in use")
        xvfb_cmd = ["/workspace/tools/xvfb/usr/bin/Xvfb", CONFIG["display"], "-screen", "0", "1280x720x24", "+extension", "GLX", "+render", "-noreset", "-nolisten", "tcp"]
        with (RAW / "xvfb.log").open("wb") as stream:
            display = subprocess.Popen(xvfb_cmd, stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
        owned.append(display)
        write(RAW / "xvfb-command.json", {"command": xvfb_cmd, "pid": display.pid, "start_utc": stamp()})
        for _ in range(100):
            if socket.exists(): break
            if display.poll() is not None: raise RuntimeError("Xvfb startup failed")
            time.sleep(.05)
        if not socket.exists(): raise RuntimeError("Xvfb socket did not appear")
        render = ["--audio-driver", "Dummy", "--display-driver", "x11", "--rendering-method", "gl_compatibility", "--resolution", "1280x720", "--max-fps", "60", "--script", "res://tests/touch_contrast_capture.gd", "--"]
        background = RAW / "backgrounds"
        background.mkdir()
        run("backgrounds", ["--path", str(STAGE / "baseline/game"), *render, "--mode=backgrounds", "--out=" + str(background)], "baseline")
        image_hashes = {str(p.relative_to(background)): sha(p) for p in sorted(background.rglob("*")) if p.is_file()}
        write(RAW / "background-freeze.json", {"files": image_hashes, "time": stamp()})
        for name in ("baseline", "candidate"):
            out = RAW / name
            out.mkdir()
            if any(sha(background / p) != h for p, h in image_hashes.items()):
                raise RuntimeError("shared backgrounds changed before " + name)
            run("controls-" + name, ["--path", str(STAGE / name / "game"), *render, "--mode=controls", "--out=" + str(out), "--background-dir=" + str(background)], name, timeout=600)
            if any(sha(background / p) != h for p, h in image_hashes.items()):
                raise RuntimeError("shared backgrounds changed after " + name)
        for name in ("baseline", "candidate"):
            for test in ("touch", "input_mode"):
                run("regression-" + name + "-" + test, ["--path", str(STAGE / name / "game"), "--headless", "--audio-driver", "Dummy", "--script", "res://tests/" + test + "_test.gd"], name)
        freeze = json.loads((RAW / "SOURCE_FREEZE-r4b-r2.json").read_text())
        analyzer = REPO / "scripts/analyze_touch_contrast_r4b.py"
        if sha(analyzer) != next(x["sha256"] for x in freeze["frozen_files"] if x["path"] == "scripts/analyze_touch_contrast_r4b.py"):
            raise RuntimeError("analyzer changed from approved freeze")
        cmd = [sys.executable, str(analyzer), "--baseline", str(RAW / "baseline"), "--candidate", str(RAW / "candidate"), "--backgrounds", str(background), "--freeze", str(RAW / "SOURCE_FREEZE-r4b-r2.json"), "--out", str(RAW / "recomputed.json")]
        with (RAW / "analyzer.log").open("wb") as stream:
            analyzed = subprocess.run(cmd, stdout=stream, stderr=subprocess.STDOUT)
        write(RAW / "analyzer-result.json", {"command": cmd, "exit_code": analyzed.returncode, "time": stamp(), "analyzer_sha256": sha(analyzer)})
        print("ANALYZER exit", analyzed.returncode, flush=True)
        # Analyzer failure is retained evidence, not a controller acquisition failure.
        success = True
    except Exception as exc:
        error = str(exc)
        print("STOP", error, flush=True)
    finally:
        cleanup = []
        for process in reversed(owned):
            before = process.poll()
            if before is None:
                os.killpg(process.pid, signal.SIGTERM)
                try: process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
            cleanup.append({"pid": process.pid, "exit_code": process.poll(), "was_running": before is None,
                            "proc_path_absent": not Path("/proc/" + str(process.pid)).exists()})
        final = {"acquisition_complete": success, "error": error, "end_utc": stamp(), "events": events,
                 "owned_cleanup": cleanup, "display_socket_absent": not Path("/tmp/.X11-unix/X131").exists(),
                 "display_lock_absent": not Path("/tmp/.X131-lock").exists()}
        write(RAW / "lane-end.json", final)
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
