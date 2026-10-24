#!/usr/bin/env python3
"""Inspect actual native artifacts; does not substitute for mobile device testing."""
import argparse
import json
import os
import pathlib
import plistlib
import re
import struct
import subprocess
import zipfile

from native_log import failed as native_log_failed
from build_manifest import BUILDS, ROOT, OUTPUTS, VERSION, BUILD_NUMBER, IOS_VERSION, descriptor, payload, source, write_json, require_clean, same_source
from godot_process import godot_environment, prepare_output
from matrix_process import run_process


def require(condition, message):
    # These are delivery gates, not assertions removable with python -O.
    if not condition:
        raise RuntimeError(message)


class VerificationAttempt:
    """One fresh attempt, with fail-closed results even when preflight fails."""

    def __init__(self, output, scope):
        self.output = prepare_output(pathlib.Path(output))
        self.report = {"passed": False, "status": "incomplete", "completed": False,
                       "scope": scope, "failures": [], "processes": [],
                       "source_before": None, "source_after": None, "source_unchanged": False,
                       "physical_device_installation": "NOT TESTED", "device_performance": "NOT TESTED",
                       "xcode_build": "NOT TESTED"}
        self.final_checks = []
        self.environment = None
        self.save()

    def save(self):
        write_json(self.output / "results.json", self.report)

    def run(self, label, command, *, cwd=None, timeout=120):
        """Own descendants before spawn; audit the complete receipt and raw log."""
        path = self.output / (label + ".log")
        receipt_path = self.output / (label + ".process.json")
        row = {"label": label, "command": list(map(str, command)), "log": path.name,
               "process_receipt": receipt_path.name, "receipt": None,
               "exit": None, "timed_out": False, "passed": False, "failures": []}
        self.report["processes"].append(row)
        self.save()
        try:
            require(not receipt_path.exists(), "refusing to overwrite process receipt: " + str(receipt_path))
            # Native children write raw bytes through this file descriptor;
            # the shared runner also needs a text stream for HARNESS_ERROR.
            with path.open("x", encoding="utf-8", newline="\n") as stream:
                try:
                    row["exit"] = run_process(row["command"], cwd=cwd, env=self.environment,
                                              log=stream, result_path=receipt_path, timeout=timeout)
                except (Exception, SystemExit, KeyboardInterrupt) as error:
                    row["timed_out"] = isinstance(error, (subprocess.TimeoutExpired, TimeoutError))
                    row["failures"].append(f"{label}: {type(error).__name__}: {error}")
                    stream.write(f"\nHARNESS_ERROR {label}: {type(error).__name__}: {error}\n")
                finally:
                    stream.flush()
        except (Exception, SystemExit, KeyboardInterrupt) as error:
            row["failures"].append(f"{label}: log capture failed: {error}")
        if type(row["exit"]) is not int or row["exit"] != 0:
            row["failures"].append(f"{label}: expected actual exit 0, got exit={row['exit']}")
        try:
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            require(isinstance(receipt, dict) and receipt.get("complete") is True
                    and type(receipt.get("exit")) is int and receipt["exit"] == row["exit"]
                    and isinstance(receipt.get("errors"), list)
                    and all(isinstance(error, str) for error in receipt["errors"]),
                    "invalid or incomplete process-supervisor receipt")
            row["receipt"] = receipt
            row["failures"].extend(f"{label}: process containment failed: {error}" for error in receipt["errors"])
        except (Exception, SystemExit, KeyboardInterrupt) as error:
            row["failures"].append(f"{label}: process receipt failed: {error}")
        text = path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""
        if "HARNESS_ERROR" in text:
            row["failures"].append(f"{label}: process containment reported HARNESS_ERROR")
        if "HARNESS_ERROR" in text and "timed out" in text.lower():
            row["timed_out"] = True
        if native_log_failed(text):
            row["failures"].append(f"{label}: emitted error or resource leak")
        row["passed"] = not row["failures"]
        self.save()
        require(row["passed"], "; ".join(row["failures"]) + f"; see {path}")
        return text

    def execute(self, verifier):
        try:
            before = source()
            self.report.update(before)
            self.report["source_before"] = before
            self.save()
            require_clean(before)
            self.environment = godot_environment(root=ROOT, env={**os.environ,
                                                "SIGHTBREAK_STATE_DIR": str(self.output / "state")})
            verifier(self)
        except (Exception, SystemExit, KeyboardInterrupt) as error:
            self.report["failures"].append(f"{type(error).__name__}: {error}")
        finally:
            for label, check in self.final_checks:
                try:
                    check()
                except (Exception, SystemExit, KeyboardInterrupt) as error:
                    self.report["failures"].append(f"{label}: {type(error).__name__}: {error}")
            try:
                after = source()
                self.report["source_after"] = after
                require_clean(after)
                require(self.report["source_before"] == after, "Frozen source changed during verification")
                self.report["source_unchanged"] = True
            except (Exception, SystemExit, KeyboardInterrupt) as error:
                self.report["failures"].append(f"Final source check: {type(error).__name__}: {error}")
            self.report["passed"] = not self.report["failures"]
            self.report["completed"] = True
            self.report["status"] = "passed" if self.report["passed"] else "failed"
            self.save()
        print(json.dumps(self.report, indent=2))
        return 0 if self.report["passed"] else 1


def check_export(target, record, current):
    require_clean(record)
    require(record.get("target") == target and record.get("export_completed") is True,
            f"{target}: incomplete export receipt")
    require(same_source(record, current), f"{target}: different frozen source identity")
    require(record.get("artifact") == descriptor(BUILDS / OUTPUTS[target]),
            f"{target}: primary artifact changed after export")
    require(record.get("payload") == payload(target), f"{target}: payload changed after export")


def load_exports(current):
    records = {}
    for target in OUTPUTS:
        record = json.loads((BUILDS / target / "source.json").read_text(encoding="utf-8"))
        check_export(target, record, current)
        records[target] = record
    return records


def recheck_exports(records, current):
    for target, record in records.items():
        require(json.loads((BUILDS / target / "source.json").read_text(encoding="utf-8")) == record,
                f"{target}: export receipt changed during verification")
        check_export(target, record, current)


def linux_elf(path):
    with path.open("rb") as stream:
        header = stream.read(20)
    require(len(header) == 20 and header[:6] == b"\x7fELF\x02\x01"
            and struct.unpack("<HH", header[16:20])[0] in (2, 3)
            and struct.unpack("<HH", header[16:20])[1] == 62,
            "Expected a Linux x86_64 ELF executable: " + str(path))


def packed_paths(path, embedded=False):
    with path.open("rb") as stream:
        start = 0
        if embedded:
            stream.seek(-12, 2)
            size, magic = struct.unpack("<QI", stream.read(12))
            require(magic == 0x43504447, "Missing embedded Godot pack trailer")
            stream.seek(-12-size, 2)
            start = stream.tell()
        magic, version, major, minor, patch, flags, base = struct.unpack("<6IQ", stream.read(32))
        require(magic == 0x43504447 and version in (3, 4), "Unexpected pack header")
        require(not flags & 1, "Encrypted pack directory is not inspected by this check")
        directory, = struct.unpack("<Q", stream.read(8))
        stream.seek(start + directory)
        count, = struct.unpack("<I", stream.read(4))
        paths = []
        for _ in range(count):
            size, = struct.unpack("<I", stream.read(4))
            paths.append(stream.read(size).rstrip(b"\0").decode())
            stream.seek(36, 1)
        return paths


def no_test_harnesses(paths):
    require(paths, "Artifact contains no resources")
    require(not any("tests/" in path or "_test.gdc" in path for path in paths), "Test harness shipped in artifact")


def integrated_resources(paths):
    """Check imported payloads, not just GLB references or source filenames."""
    for basename in ("relay_ar.glb-", "relay_ar_arms.glb-", "relay_ar_hands.glb-"):
        require(any(basename in path and path.endswith('.scn') for path in paths), f"Missing imported scene: {basename}")
    for basename in ("relay_ar_albedo.png-", "relay_ar_normal.png-", "relay_ar_orm.png-",
                     "relay_ar_arms_albedo.png-", "relay_ar_arms_normal.png-", "relay_ar_arms_orm.png-"):
        require(any(basename in path and path.endswith('.ctex') for path in paths), f"Missing imported texture: {basename}")
    for basename in ("state_privacy", "snapshot_buffer", "movement_prediction", "movement_step", "peer_lifecycle", "reconnect_policy", "result_outbox", "viewmodel_shading", "bot_ai", "reload_audio", "reload_phases", "confirm_sheet"):
        require(any(path.endswith('/' + basename + '.gdc') for path in paths), f"Missing compiled module: {basename}")


def verify_exports(attempt):
    build_source = attempt.report["source_before"]
    records = load_exports(build_source)
    attempt.report["export_receipts"] = records
    attempt.final_checks.append(("Final export payload/receipt check", lambda: recheck_exports(records, build_source)))
    run = attempt.run
    executable = str(BUILDS / "linux/sightbreak.x86_64")
    linux_elf(pathlib.Path(executable))
    menu = run("linux-menu", [executable, "--headless", "--", "--smoke"])
    require("SIGHTBREAK_MAIN_READY screen=menu" in menu, "Linux menu readiness marker missing")
    run("linux-demo", [executable, "--headless", "--quit-after", "120", "--", "--demo"])
    linux_paths = packed_paths(pathlib.Path(executable), embedded=True)
    no_test_harnesses(linux_paths)
    integrated_resources(linux_paths)
    tools = pathlib.Path(os.environ.get("SIGHTBREAK_TOOLS_DIR", ROOT.parent / "tools"))
    sdk = pathlib.Path(os.environ.get("ANDROID_SDK_ROOT", tools / "android-sdk"))
    android_tools = sdk / "build-tools/36.0.0"
    apk = str(BUILDS / "android/sightbreak-debug.apk")
    signature = run("android-signature", [str(android_tools / "apksigner"), "verify", "--verbose", "--print-certs", apk])
    require("Verified using v2 scheme (APK Signature Scheme v2): true" in signature, "APK v2 signature not verified")
    require("Verified using v3 scheme (APK Signature Scheme v3): true" in signature, "APK v3 signature not verified")
    badging = run("android-manifest", [str(android_tools / "aapt"), "dump", "badging", apk])
    for expected in ["package: name='com.sightbreak.game'", f"versionCode='{BUILD_NUMBER}'", f"versionName='{VERSION}'", "sdkVersion:'24'", "targetSdkVersion:'36'", "'arm64-v8a'", "'x86_64'"]:
        require(expected in badging, f"Missing APK metadata: {expected}")
    android_manifest = run("android-layout", [str(android_tools / "aapt"), "dump", "xmltree", apk, "AndroidManifest.xml"])
    require(re.search(r"android:screenOrientation[^\n]*\(type 0x10\)0x0\b", android_manifest), "Android landscape orientation missing")
    launcher_alias = android_manifest.split("E: activity-alias", 1)[1].split("E: meta-data", 1)[0]
    require('"com.godot.game.GodotAppLauncher"' in launcher_alias, "Android launcher alias missing")
    require('"com.godot.game.GodotApp"' in launcher_alias, "Android launcher target missing")
    require(re.search(r"android:exported[^\n]*0xffffffff", launcher_alias), "Launcher alias must be exported")
    require('"android.intent.action.MAIN"' in launcher_alias and '"android.intent.category.LAUNCHER"' in launcher_alias,
            "Android main launcher intent missing")
    with zipfile.ZipFile(apk) as archive:
        android_paths = [name for name in archive.namelist() if name.startswith("assets/")]
    no_test_harnesses(android_paths)
    integrated_resources(android_paths)
    ios = BUILDS / "ios"
    ios_paths = packed_paths(ios / "sightbreak.pck")
    no_test_harnesses(ios_paths)
    integrated_resources(ios_paths)
    with (ios / "sightbreak/sightbreak-Info.plist").open("rb") as stream:
        plist = plistlib.load(stream)
    require(plist["CFBundleIdentifier"] == "$(PRODUCT_BUNDLE_IDENTIFIER)", "iOS plist bundle identifier mismatch")
    require(plist["NSLocalNetworkUsageDescription"], "iOS local network usage description missing")
    require(plist["UISupportedInterfaceOrientations"], "iOS orientations missing")
    require(all("Landscape" in value for value in plist["UISupportedInterfaceOrientations"]), "iOS must be landscape only")
    project = (ios / "sightbreak.xcodeproj/project.pbxproj").read_text()
    require("UNSIGNED00" not in project and 'DEVELOPMENT_TEAM = "";' in project, "iOS project must have an empty unsigned team")
    require("PRODUCT_BUNDLE_IDENTIFIER = com.sightbreak.game;" in project, "iOS project bundle identifier mismatch")
    require(f"MARKETING_VERSION = {IOS_VERSION};" in project, "Wrong iOS marketing version")
    require(f"CURRENT_PROJECT_VERSION = {BUILD_NUMBER};" in project, "Wrong iOS build number")
    attempt.report.update({"linux_menu_smoke": True, "linux_demo_120_frames": True,
              "linux_pck_resources": len(linux_paths), "android_assets": len(android_paths), "ios_pck_resources": len(ios_paths),
              "test_harnesses_excluded": True, "android_signature_schemes": ["v2", "v3"],
              "integrated_imported_rifle_arms_textures_network_modules": True,
              "android_version": f"{VERSION} ({BUILD_NUMBER})", "android_min_sdk": 24, "android_target_sdk": 36,
              "android_abis": ["arm64-v8a", "x86_64"], "android_landscape_manifest": True,
              "android_launcher_alias": "com.sightbreak.game/com.godot.game.GodotAppLauncher", "ios_project_plist_and_unsigned_team": True,
              "physical_device_installation": "NOT TESTED", "device_performance": "NOT TESTED", "xcode_build": "NOT TESTED"})


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=pathlib.Path, default=BUILDS / "verification",
                        help="New or empty attempt directory; earlier evidence is never overwritten")
    args = parser.parse_args(argv)
    try:
        attempt = VerificationAttempt(args.output, "Actual native exports; Linux menu/demo, APK metadata/signature, unsigned iOS structure")
    except (OSError, ValueError) as error:
        parser.error(str(error))
    return attempt.execute(verify_exports)


if __name__ == "__main__":
    raise SystemExit(main())
