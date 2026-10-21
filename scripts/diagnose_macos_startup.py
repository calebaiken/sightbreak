#!/usr/bin/env python3
"""Native macOS graphics controls; diagnostic evidence never replaces the launch gate.

Creates an isolated minimal project outside game/, exports it with the pinned
official editor, and compares native first-frame startup with frozen/current game
bundles. Every graphical trial has the same 120-second wall-clock budget. No
renderer setting, app signature, frozen archive or game source is modified.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import signal
import struct
import subprocess
import time
import zipfile

from build_manifest import BUILDS, OUTPUTS, clean, source, validate_record
from native_log import failed as native_log_failed
import toolchain

BASELINE_COMMIT = "0fb74800cffb96077069144028d113e308ef1744"
BASELINE_ARTIFACT_SHA256 = "45e7bd2cc36514333651c484a6950260e31afa81b7efc2bcb4fe7771b1a036eb"
GRAPHICAL_SECONDS = 120


def interrupted(signum, _frame):
    # Unwind owned-process cleanup instead of abandoning children on cancellation.
    raise SystemExit(128 + signum)


MINIMAL_SCRIPT = '''extends Node3D
var frames := 0
var capture := ""
func _init() -> void:
\tprint("MINIMAL_DIAG_INIT msec=", Time.get_ticks_msec())
func _ready() -> void:
\tprint("MINIMAL_DIAG_READY msec=", Time.get_ticks_msec())
\tfor arg in OS.get_cmdline_user_args():
\t\tif arg.begins_with("--capture="): capture = arg.trim_prefix("--capture=")
\tif "--probe-3d" in OS.get_cmdline_user_args():
\t\tvar camera := Camera3D.new()
\t\tcamera.position = Vector3(0, 0, 4)
\t\tadd_child(camera)
\t\tcamera.current = true
\t\tvar mesh := MeshInstance3D.new()
\t\tmesh.mesh = BoxMesh.new()
\t\tmesh.rotation_degrees = Vector3(20, 25, 0)
\t\tadd_child(mesh)
\t\tvar light := DirectionalLight3D.new()
\t\tlight.rotation_degrees = Vector3(-30, -30, 0)
\t\tadd_child(light)
\tvar label := Label.new()
\tlabel.text = "Official Godot 4.7.2 native graphics control"
\tlabel.position = Vector2(40, 40)
\tadd_child(label)
func _process(_delta: float) -> void:
\tframes += 1
\tif frames == 1: print("MINIMAL_DIAG_FIRST_PROCESS msec=", Time.get_ticks_msec())
\tif frames == 15:
\t\tprint("MINIMAL_DIAG_BEFORE_DRAW msec=", Time.get_ticks_msec())
\t\tawait RenderingServer.frame_post_draw
\t\tprint("MINIMAL_DIAG_AFTER_DRAW msec=", Time.get_ticks_msec())
\t\tvar error := get_viewport().get_texture().get_image().save_png(capture)
\t\tprint("MINIMAL_DIAG_EXIT capture_error=", error, " msec=", Time.get_ticks_msec())
\t\tget_tree().quit(0 if error == OK else 1)
'''
MINIMAL_PROJECT = '''config_version=5
[application]
config/name="SIGHTBREAK Native Graphics Control"
run/main_scene="res://main.tscn"
config/features=PackedStringArray("4.7", "GL Compatibility")
[display]
window/size/viewport_width=1280
window/size/viewport_height=720
window/size/window_width_override=1280
window/size/window_height_override=720
[rendering]
renderer/rendering_method="gl_compatibility"
renderer/rendering_method.mobile="gl_compatibility"
anti_aliasing/quality/msaa_3d=1
environment/defaults/default_clear_color=Color(0.026, 0.031, 0.043, 1)
'''
MINIMAL_PRESET = '''[preset.0]
name="macOS"
platform="macOS"
runnable=false
advanced_options=true
export_filter="all_resources"
script_export_mode=2
[preset.0.options]
binary_format/architecture="universal"
application/bundle_identifier="com.sightbreak.graphics-control"
application/short_version="0.0.1"
application/version="1"
application/min_macos_version_x86_64="11.00"
application/min_macos_version_arm64="13.00"
display/high_res=true
codesign/codesign=1
notarization/notarization=0
'''


def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def group_state(group):
    result = subprocess.run(["ps", "-axo", "pid=,ppid=,pgid=,stat=,etime=,pcpu=,comm="],
                            capture_output=True, text=True, timeout=5)
    # Only the owned group is retained; unrelated process arguments are not logged.
    return [line for line in result.stdout.splitlines()
            if len(line.split()) >= 3 and line.split()[2] == str(group)]


def terminate_group(process):
    for sig in (signal.SIGTERM, signal.SIGKILL):
        try:
            os.killpg(process.pid, sig)
        except ProcessLookupError:
            pass
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            continue
        try:
            if not group_state(process.pid):
                break
        except (OSError, subprocess.SubprocessError):
            # A failed diagnostic ps must not prevent the owned group's SIGKILL.
            continue


def bounded_command(command, seconds=30):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               text=True, start_new_session=True)
    timed_out = False
    try:
        output, _ = process.communicate(timeout=seconds)
    except subprocess.TimeoutExpired:
        timed_out = True
        terminate_group(process)
        output, _ = process.communicate(timeout=3)
    except (SystemExit, KeyboardInterrupt):
        terminate_group(process)
        process.communicate(timeout=3)
        raise
    descendants = group_state(process.pid)
    if descendants:
        terminate_group(process)
    return {"command": command, "exit_code": process.returncode,
            "timed_out": timed_out, "output": output,
            "descendants_after_root_exit": descendants, "surviving_owned_group": group_state(process.pid)}


def capture_description(path):
    if not path.is_file():
        return None
    header = path.read_bytes()[:24]
    if len(header) != 24 or header[:8] != b"\x89PNG\r\n\x1a\n":
        return {"valid_png": False, "sha256": digest(path)}
    width, height = struct.unpack(">II", header[16:24])
    return {"valid_png": width > 0 and height > 0, "width": width,
            "height": height, "sha256": digest(path)}


def native_trial(directory, label, command, capture, marker):
    log_path = directory / (label + ".log")
    started = time.monotonic()
    states, samples = [], []
    result = {"label": label, "command": command, "budget_seconds": GRAPHICAL_SECONDS,
              "native_exit_code": None, "timed_out": False, "surviving_owned_group": []}
    process = None
    interruption = None
    try:
        with log_path.open("w", encoding="utf-8") as log:
            process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT,
                                       start_new_session=True)
            result["pid"] = process.pid
            next_sample = 15
            while process.poll() is None and time.monotonic() - started < GRAPHICAL_SECONDS:
                elapsed = time.monotonic() - started
                if elapsed >= next_sample:
                    states.append({"seconds": elapsed, "owned_group": group_state(process.pid)})
                    sample_path = directory / f"{label}-{next_sample}s.sample.txt"
                    sample = bounded_command(["sample", str(process.pid), "2", "1", "-file", str(sample_path)], 6)
                    sample["sample_path"] = sample_path.name
                    samples.append(sample)
                    next_sample = 90 if next_sample == 15 else GRAPHICAL_SECONDS + 1
                time.sleep(.1)
            native_exit = process.poll()
            result.update({"native_exit_code": native_exit, "timed_out": native_exit is None,
                           "elapsed_before_cleanup": time.monotonic() - started})
            if native_exit is None:
                states.append({"seconds": time.monotonic() - started, "owned_group": group_state(process.pid)})
                terminate_group(process)
    except SystemExit as error:
        interruption = error.code
        result.update(interrupted=error.code, error="External cancellation")
    except Exception as error:
        result["error"] = str(error)
    finally:
        if process is not None:
            result["owned_group_after_native_exit"] = group_state(process.pid)
            if process.poll() is None:
                terminate_group(process)
            result["surviving_owned_group"] = group_state(process.pid)
            if result["surviving_owned_group"]:
                terminate_group(process)
                result["surviving_owned_group"] = group_state(process.pid)
            result["exit_code_after_cleanup"] = process.returncode
        result["elapsed_total"] = time.monotonic() - started
    output = log_path.read_text(errors="replace")
    image = capture_description(capture)
    result.update({"process_states": states, "samples": samples, "capture": image,
                   "marker_observed": marker in output, "clean_log": not native_log_failed(output),
                   "renderer_lines": [line for line in output.splitlines()
                                      if any(word in line for word in ("OpenGL", "Vulkan", "Metal", "ANGLE", "Renderer"))],
                   "phase_lines": [line for line in output.splitlines() if "MINIMAL_DIAG_" in line or "SIGHTBREAK_MAIN_READY" in line or "SIGHTBREAK_STARTUP" in line]})
    result["passed"] = (result["native_exit_code"] == 0 and result["marker_observed"]
                        and bool(image and image["valid_png"]) and result["clean_log"]
                        and not result["owned_group_after_native_exit"]
                        and not result["surviving_owned_group"] and "error" not in result)
    write_json(directory / (label + ".json"), result)
    print(json.dumps({key: result[key] for key in ("label", "native_exit_code", "timed_out", "passed", "renderer_lines", "phase_lines")}), flush=True)
    if interruption is not None:
        raise SystemExit(interruption)
    return result


def baseline_from_archive(archive, output):
    if digest(archive) != BASELINE_ARTIFACT_SHA256:
        raise RuntimeError("Frozen baseline Actions ZIP SHA256 mismatch")
    with zipfile.ZipFile(archive) as bundle:
        receipts = [name for name in bundle.namelist() if name == "macos/source.json" or name.endswith("/macos/source.json")]
        if len(receipts) != 1:
            raise RuntimeError("Expected exactly one frozen macOS source receipt")
        prefix = receipts[0][:-len("macos/source.json")]
        record = json.loads(bundle.read(receipts[0]))
        if (record.get("source_commit") != BASELINE_COMMIT or record.get("target") != "macos"
                or record.get("source_dirty") or not record.get("export_completed")):
            raise RuntimeError("Frozen baseline source receipt mismatch")
        delivery = output / "frozen-baseline"
        restored = []
        for entry in record["payload"]:
            relative = Path(entry["path"])
            if relative.is_absolute() or ".." in relative.parts or relative.parts[0] != "macos":
                raise RuntimeError("Unsafe frozen payload path")
            data = bundle.read(prefix + relative.as_posix())
            if len(data) != entry["bytes"] or hashlib.sha256(data).hexdigest() != entry["sha256"]:
                raise RuntimeError("Frozen baseline payload bytes mismatch: " + str(relative))
            destination = delivery / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
            destination.chmod(entry["archive_mode"] & 0o777)
            restored.append({"path": entry["path"], "sha256": entry["sha256"], "delivery_mode": entry["archive_mode"] & 0o777})
        write_json(delivery / "extraction.json", {"original_source_receipt": record, "outer_sha256": BASELINE_ARTIFACT_SHA256,
                   "restored_delivery_modes": restored, "scope": "Copied original payload bytes; Actions outer ZIP modes are not an app signature or a re-attestation"})
    return delivery / OUTPUTS["macos"]


def host_description():
    commands = [bounded_command(["sw_vers"]), bounded_command(["uname", "-a"]),
                bounded_command(["sysctl", "-n", "hw.model", "hw.machine", "hw.memsize", "hw.ncpu"])]
    displays = bounded_command(["system_profiler", "SPDisplaysDataType", "-json"], 30)
    try:
        data = json.loads(displays.pop("output"))
        # Omit monitor serials/UUIDs, user data and unrelated hardware identifiers.
        keys = ("_name", "sppci_model", "spdisplays_vendor", "spdisplays_device-id", "spdisplays_metal",
                "spdisplays_vram", "spdisplays_vram_shared", "spdisplays_revision-id")
        displays["gpu_capabilities"] = [{key: gpu[key] for key in keys if key in gpu}
                                       for gpu in data.get("SPDisplaysDataType", [])]
    except (ValueError, KeyError):
        displays["gpu_capabilities"] = "UNVERIFIED: profiler did not produce JSON"
    return {"platform": platform.platform(), "machine": platform.machine(), "commands": commands, "displays": displays,
            "runner_labels": {key: os.environ.get(key) for key in ("RUNNER_OS", "RUNNER_ARCH", "ImageOS", "ImageVersion")}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="Fresh ignored evidence directory outside game/")
    parser.add_argument("--baseline-archive", type=Path, help="Unmodified retained Intel Actions artifact 12247215871 ZIP")
    args = parser.parse_args()
    if platform.system() != "Darwin":
        parser.error("Run on a native macOS host; Linux execution is not macOS acceptance")
    for signum in (signal.SIGTERM, signal.SIGINT):
        signal.signal(signum, interrupted)
    output = args.output.resolve()
    if output.is_relative_to(toolchain.ROOT / "game") or output.is_relative_to(BUILDS / "macos"):
        parser.error("Diagnostic fixture/evidence must stay outside game/ and the shipped macOS payload")
    if output.exists() and any(output.iterdir()):
        parser.error("Preserve the earlier attempt; choose a fresh output directory")
    before = source()
    clean(before)
    record = validate_record("macos", before)
    output.mkdir(parents=True, exist_ok=True)
    report = {"source": before, "scope": "Native graphical startup comparison only; no gameplay, physical GPU, signing/notarization or quality acceptance",
              "default_gate_unchanged": True, "baseline_comparison": "UNVERIFIED", "trials": [], "preparation": [],
              "cache_scope": "No existing caches are deleted; ordered warm/cold differences are not performance acceptance"}
    active_trial = None
    try:
        report.update({"engine": toolchain.verify_engine(), "editor_sha256": digest(toolchain.binary()),
                       "host": host_description(), "candidate_receipt": record})
        fixture = output / "minimal-project"
        fixture.mkdir()
        for name, content in (("project.godot", MINIMAL_PROJECT), ("main.gd", MINIMAL_SCRIPT),
                              ("main.tscn", '[gd_scene load_steps=2 format=3]\n[ext_resource type="Script" path="res://main.gd" id="1"]\n[node name="GraphicsControl" type="Node3D"]\nscript=ExtResource("1")\n'),
                              ("export_presets.cfg", MINIMAL_PRESET)):
            (fixture / name).write_text(content)
        report["fixture_sha256"] = {path.name: digest(path) for path in fixture.iterdir() if path.is_file()}
        minimal_app = output / "MinimalGraphics.app"
        for arguments in (("--editor", "--import", "--quit"), ("--export-debug", "macOS", str(minimal_app))):
            command = [toolchain.binary(), "--headless", "--path", str(fixture), *arguments]
            result = bounded_command(command, 120)
            report["preparation"].append(result)
            write_json(output / "results.json", report)
            if result["exit_code"] != 0 or result["timed_out"] or native_log_failed(result["output"]):
                raise RuntimeError("Minimal official-engine import/export failed; inspect preparation receipt")
        report["fixture_sha256_after_preparation"] = {path.name: digest(path) for path in fixture.iterdir() if path.is_file()}
        minimal = minimal_app / "Contents/MacOS/MinimalGraphics"
        if not minimal.is_file():
            executables = list((minimal_app / "Contents/MacOS").iterdir())
            if len(executables) != 1:
                raise RuntimeError("Ambiguous minimal app executable")
            minimal = executables[0]
        candidate = BUILDS / OUTPUTS["macos"]
        apps = [("minimal", minimal), ("candidate", candidate)]
        baseline = None
        if args.baseline_archive:
            try:
                baseline = baseline_from_archive(args.baseline_archive, output)
            except (OSError, ValueError, RuntimeError, zipfile.BadZipFile, KeyError) as error:
                # A missing/changed historical artifact must not prevent the
                # independent minimal/current controls, or be executed as trusted.
                report["baseline_comparison"] = "UNVERIFIED: " + str(error)
        if baseline:
            apps.append(("baseline", baseline))
            report["baseline_comparison"] = "Original retained artifact bytes verified"
        report["binaries"] = [{"label": label, "path": str(executable), "sha256": digest(executable),
                               "architectures": bounded_command(["lipo", "-archs", str(executable)]),
                               "signature_check": bounded_command(["codesign", "--verify", "--deep", "--strict", str(executable.parents[2])])}
                              for label, executable in apps]
        report["universal2_checks_passed"] = all(binary["architectures"]["exit_code"] == 0
            and set(binary["architectures"]["output"].split()) == {"arm64", "x86_64"} for binary in report["binaries"])
        cases = [("editor-minimal-2d-default", [toolchain.binary(), "--path", str(fixture)], False, False),
                 ("editor-minimal-3d-default", [toolchain.binary(), "--path", str(fixture)], True, False),
                 ("export-minimal-3d-default", [str(minimal)], True, False)]
        if baseline:
            cases.append(("frozen-game-default", [str(baseline)], False, True))
        cases.append(("candidate-game-default", [str(candidate)], False, True))
        for label, command, use_3d, game in cases:
            active_trial = label
            capture = output / (label + ".png")
            user = (["--smoke"] if game else ["--probe-3d"] if use_3d else []) + ["--capture=" + str(capture)]
            result = native_trial(output, label, command + ["--verbose", "--audio-driver", "Dummy", "--log-file", str(output / (label + ".godot.log")), "--", *user], capture,
                                  "SIGHTBREAK_MAIN_READY screen=menu" if game else "MINIMAL_DIAG_EXIT capture_error=0")
            report["trials"].append(result)
            active_trial = None
            write_json(output / "results.json", report)
        if not report["trials"][-1]["passed"]:
            for label, executable, game in (("minimal-3d-opengl-diagnostic", minimal, False), ("candidate-opengl-diagnostic", candidate, True)):
                active_trial = label
                capture = output / (label + ".png")
                command = [str(executable), "--verbose", "--rendering-driver", "opengl3", "--audio-driver", "Dummy",
                           "--log-file", str(output / (label + ".godot.log")), "--",
                           "--smoke" if game else "--probe-3d", "--capture=" + str(capture)]
                report["trials"].append(native_trial(output, label, command, capture,
                    "SIGHTBREAK_MAIN_READY screen=menu" if game else "MINIMAL_DIAG_EXIT capture_error=0"))
                active_trial = None
                write_json(output / "results.json", report)
        validate_record("macos", before)
        report["exact_source_unchanged"] = source() == before
        report["all_default_graphical_passed"] = all(trial["passed"] for trial in report["trials"] if trial["label"].endswith("-default"))
        report["status"] = ("PASS startup controls only" if report["all_default_graphical_passed"] and baseline
                            and report["exact_source_unchanged"] and report["universal2_checks_passed"]
                            else "FAIL or INCOMPLETE; retain original default gate")
    except SystemExit as error:
        if active_trial and (output / (active_trial + ".json")).is_file():
            report["trials"].append(json.loads((output / (active_trial + ".json")).read_text()))
        report.update(status="INTERRUPTED; owned-process cleanup attempted", interrupted=error.code)
        raise
    except Exception as error:
        report.update({"status": "FAIL diagnostic preparation/execution", "error": str(error)})
    finally:
        write_json(output / "results.json", report)
    print(json.dumps({key: report.get(key) for key in ("status", "source", "baseline_comparison", "all_default_graphical_passed", "error")}), flush=True)
    return 0 if report["status"] == "PASS startup controls only" else 1


if __name__ == "__main__":
    raise SystemExit(main())
