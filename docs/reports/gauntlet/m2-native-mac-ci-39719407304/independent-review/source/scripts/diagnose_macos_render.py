#!/usr/bin/env python3
"""Isolate first-draw feature costs in a diagnostic macOS export of the real menu.

No shipping source, payload, graphics defaults or 120-second gate is changed.
A completed diagnostic case is not acceptance of the game or that graphics preset.
"""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import re
import signal
import subprocess

from build_manifest import BUILDS, clean, source, validate_record
from diagnose_macos_startup import (GRAPHICAL_SECONDS, MINIMAL_PRESET, bounded_command,
    digest, host_description, interrupted, native_trial, write_json)
from native_log import failed as native_log_failed
import toolchain

CASES = ("full", "shadows-off", "surface-detail-off", "sky-off", "materials-untextured")
PROBE = toolchain.ROOT / "scripts/diagnostics/render_feature_probe.gd"


def prepare_fixture(output):
    """Copy tracked game bytes only; never copy imports, saves or local caches."""
    fixture = output / "render-project"
    fixture.mkdir(parents=True)
    paths = subprocess.check_output(["git", "ls-files", "-z", "--", "game"],
                                    cwd=toolchain.ROOT).decode().split("\0")
    copied = []
    for name in paths:
        if not name:
            continue
        relative = Path(name).relative_to("game")
        if ".godot" in relative.parts or "tests" in relative.parts:
            continue
        original = toolchain.ROOT / name
        if original.is_symlink() or not original.is_file():
            raise RuntimeError("Expected regular tracked game file: " + name)
        destination = fixture / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(original.read_bytes())
        copied.append({"path": name, "sha256": digest(original)})
    project = fixture / "project.godot"
    settings = project.read_text()
    old = 'run/main_scene="res://main.tscn"'
    if settings.count(old) != 1:
        raise RuntimeError("Expected exactly one shipping main scene setting")
    # Separate user:// keeps pre-existing player saves out of the control.
    if settings.count('config/name="SIGHTBREAK"') != 1 or "config/use_custom_user_dir" in settings or "config/custom_user_dir_name" in settings:
        raise RuntimeError("Unexpected application data-directory settings; preserve save isolation")
    settings = settings.replace(old, 'run/main_scene="res://render_probe.tscn"')
    settings = settings.replace('config/name="SIGHTBREAK"',
        'config/name="SIGHTBREAK Render Diagnostic"\nconfig/use_custom_user_dir=true\n'
        'config/custom_user_dir_name="SIGHTBREAK-render-diagnostic-' + hashlib.sha256(str(output.resolve()).encode()).hexdigest()[:12] + '"')
    project.write_text(settings)
    (fixture / "render_probe.gd").write_bytes(PROBE.read_bytes())
    (fixture / "render_probe.tscn").write_text('[gd_scene load_steps=2 format=3]\n'
        '[ext_resource type="Script" path="res://render_probe.gd" id="1"]\n'
        '[node name="RenderFeatureDiagnostic" type="Node"]\nscript=ExtResource("1")\n')
    (fixture / "export_presets.cfg").write_text(MINIMAL_PRESET.replace(
        "com.sightbreak.graphics-control", "com.sightbreak.render-diagnostic"))
    write_json(output / "fixture-source.json", {"copied_shipping_files": copied,
        "diagnostic_overrides": {name: digest(fixture / name) for name in
            ("project.godot", "export_presets.cfg", "render_probe.gd", "render_probe.tscn")},
        "scope": "Isolated diagnostic wrapper and export preset; not a shipping artifact"})
    return fixture


def draw_trace(log, case):
    pattern = re.compile(r"^RENDER_DIAG phase=drawn frame=(\d+) case=(\S+) msec=(\d+) draws=(\d+(?:\.\d+)?) primitives=(\d+(?:\.\d+)?)$", re.MULTILINE)
    frames = [{"frame": int(number), "case": name, "msec": int(msec),
               "draws": float(draws), "primitives": float(primitives)}
              for number, name, msec, draws, primitives in pattern.findall(log)]
    complete = ([frame["frame"] for frame in frames] == list(range(1, 16))
        and all(frame["case"] == case for frame in frames)
        and all(after["msec"] >= before["msec"] for before, after in zip(frames, frames[1:])))
    return frames, complete


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--cases", nargs="+", choices=CASES, default=list(CASES))
    args = parser.parse_args()
    if platform.system() != "Darwin":
        parser.error("Run on native macOS; Linux controls cannot verify the Intel failure")
    output = args.output.resolve()
    if output.is_relative_to(toolchain.ROOT / "game") or output.is_relative_to(BUILDS / "macos"):
        parser.error("Keep diagnostic fixtures outside game/ and the shipping macOS payload")
    if output.exists() and any(output.iterdir()):
        parser.error("Choose a fresh evidence directory; keep previous attempts")
    for signum in (signal.SIGTERM, signal.SIGINT):
        signal.signal(signum, interrupted)
    before = source()
    clean(before)
    receipt = validate_record("macos", before)
    output.mkdir(parents=True, exist_ok=True)
    report = {"source": before, "shipping_receipt": receipt, "trials": [], "preparation": [],
        "scope": "Feature attribution only; no game, gameplay, GPU or visual-quality acceptance",
        "budget_seconds": GRAPHICAL_SECONDS, "shipping_gate_unchanged": True,
        "cache_scope": "No pre-existing cache is deleted; case order is not performance acceptance"}
    active_case = None
    try:
        report.update(engine=toolchain.verify_engine(), editor_sha256=digest(toolchain.binary()), host=host_description())
        fixture = prepare_fixture(output)
        application = output / "RenderDiagnostic.app"
        for label, flags in (("render-import", ("--editor", "--import", "--quit")),
            ("render-export", ("--export-debug", "macOS", str(application)))):
            result = bounded_command([toolchain.binary(), "--headless", "--path", str(fixture), *flags], 120)
            (output / (label + ".log")).write_text(result.pop("output"))
            report["preparation"].append(result)
            write_json(output / "results.json", report)
            if result["exit_code"] != 0 or result["timed_out"] or native_log_failed((output / (label + ".log")).read_text()):
                raise RuntimeError("Diagnostic import/export failed; inspect " + label + ".log")
        executables = list((application / "Contents/MacOS").iterdir())
        if len(executables) != 1:
            raise RuntimeError("Expected one diagnostic executable")
        executable = executables[0]
        report["diagnostic_binary"] = {"sha256": digest(executable),
            "architectures": bounded_command(["lipo", "-archs", str(executable)])}
        if (report["diagnostic_binary"]["architectures"]["exit_code"] != 0 or
            set(report["diagnostic_binary"]["architectures"]["output"].split()) != {"arm64", "x86_64"}):
            raise RuntimeError("Expected Universal 2 diagnostic executable")
        # Always retain the full feature reference, even with a requested subset.
        report["diagnostic_payload"] = [{"path": path.relative_to(application).as_posix(), "sha256": digest(path)}
            for path in sorted(application.rglob("*")) if path.is_file()]
        for case in dict.fromkeys(("full", *args.cases)):
            active_case = case
            capture = output / (case + ".png")
            command = [str(executable), "--verbose", "--audio-driver", "Dummy", "--log-file",
                str(output / (case + ".godot.log")), "--", "--render-case=" + case,
                "--capture=" + str(capture)]
            result = native_trial(output, case, command, capture, "RENDER_DIAG_EXIT capture_error=0")
            log = (output / (case + ".log")).read_text()
            result["draw_phase_lines"] = [line for line in log.splitlines() if "RENDER_DIAG" in line]
            result["draw_trace"], result["trace_complete"] = draw_trace(log, case)
            result["passed"] = result["passed"] and result["trace_complete"]
            write_json(output / (case + ".json"), result)
            report["trials"].append(result)
            active_case = None
            write_json(output / "results.json", report)
        validate_record("macos", before)
        report["exact_source_unchanged"] = source() == before
        report["status"] = ("COMPLETE diagnostic cases only" if report["exact_source_unchanged"]
            else "FAIL source changed")
    except (OSError, RuntimeError, subprocess.SubprocessError, SystemExit) as error:
        if active_case and (output / (active_case + ".json")).is_file():
            report["trials"].append(json.loads((output / (active_case + ".json")).read_text()))
        report.update(status="FAIL or INTERRUPTED diagnostic preparation/execution", error=str(error))
        raise
    finally:
        write_json(output / "results.json", report)
        print(json.dumps({"status": report.get("status"), "results": str(output / "results.json")}), flush=True)
    return 0 if report["status"] == "COMPLETE diagnostic cases only" else 1


if __name__ == "__main__":
    raise SystemExit(main())
