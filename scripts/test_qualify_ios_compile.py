#!/usr/bin/env python3
"""Portable fixture controls; these do not claim an actual Apple compiler run."""
import hashlib
import json
import os
from pathlib import Path
import plistlib
import struct
import subprocess
import sys
import tempfile
import time
import unittest

import qualify_ios_compile as ios


def macho(*, cpu=0x0100000C, kind=2, platform=2, signed=False):
    commands = struct.pack("<6I", 0x32, 24, platform, 0, 0, 0)
    if signed:
        commands += struct.pack("<4I", 0x1D, 16, 0, 0)
    return struct.pack("<8I", 0xFEEDFACF, cpu, 0, kind, 1 + signed, len(commands), 0, 0) + commands


def pack():
    paths = ["res://imported/" + name + "-fixture.scn" for name in ("relay_ar.glb", "relay_ar_arms.glb", "relay_ar_hands.glb")]
    paths += ["res://imported/" + name + "-fixture.ctex" for name in
              ("relay_ar_albedo.png", "relay_ar_normal.png", "relay_ar_orm.png", "relay_ar_arms_albedo.png", "relay_ar_arms_normal.png", "relay_ar_arms_orm.png")]
    paths += ["res://scripts/" + name + ".gdc" for name in
              ("state_privacy", "snapshot_buffer", "movement_prediction", "movement_step", "peer_lifecycle", "reconnect_policy", "result_outbox", "viewmodel_shading", "bot_ai", "reload_audio", "reload_phases", "confirm_sheet")]
    return struct.pack("<6IQQI", 0x43504447, 3, 4, 7, 2, 0, 0, 40, len(paths)) + b"".join(
        struct.pack("<I", len(path.encode())) + path.encode() + bytes(36) for path in paths)


class IosCompileControls(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def test_accepts_only_unsigned_arm64_device_executable(self):
        binary = self.root / "executable"
        binary.write_bytes(macho())
        self.assertEqual(ios.inspect_macho(binary)["platform"], "iOS device")
        failures = {"x86_64": macho(cpu=0x01000007), "dylib": macho(kind=6),
                    "simulator_arm64": macho(platform=7), "macos_arm64": macho(platform=1),
                    "signature_even_empty": macho(signed=True), "truncated_header": macho()[:31],
                    "truncated_commands": macho()[:-1], "fat_container": b"\xca\xfe\xba\xbe" + bytes(60),
                    "zero_command_size": macho()[:36] + struct.pack("<I", 0) + macho()[40:],
                    "excess_commands": macho()[:16] + struct.pack("<I", 2) + macho()[20:],
                    "unconsumed_commands": macho()[:16] + struct.pack("<I", 0) + macho()[20:]}
        for name, data in failures.items():
            with self.subTest(name=name):
                binary.write_bytes(data)
                with self.assertRaises(RuntimeError):
                    ios.inspect_macho(binary)

    def app_fixture(self):
        export = self.root / "export"
        (export / "ios").mkdir(parents=True)
        exported_pack = export / "ios/sightbreak.pck"
        exported_pack.write_bytes(pack())
        app = self.root / "sightbreak.app"
        app.mkdir()
        (app / "sightbreak").write_bytes(macho())
        (app / "sightbreak.pck").write_bytes(exported_pack.read_bytes())
        with (app / "Info.plist").open("wb") as stream:
            plistlib.dump({"CFBundleIdentifier": "com.sightbreak.game", "CFBundleShortVersionString": ios.manifest.IOS_VERSION,
                          "CFBundleVersion": str(ios.manifest.BUILD_NUMBER), "CFBundleExecutable": "sightbreak",
                          "DTPlatformName": "iphoneos", "CFBundleSupportedPlatforms": ["iPhoneOS"]}, stream)
        record = {"payload": [{"path": "ios/sightbreak.pck", "bytes": exported_pack.stat().st_size,
                               "sha256": hashlib.sha256(exported_pack.read_bytes()).hexdigest()}]}
        return app, export, record

    def test_app_checks_actual_pack_against_manifest_and_inspects_resources(self):
        app, export, record = self.app_fixture()
        result = ios.inspect_app(app, export, record)
        self.assertEqual(result["pck_resources"], 21)
        self.assertEqual(result["pck_sha256"], hashlib.sha256(pack()).hexdigest())
        (app / "sightbreak.pck").write_bytes(pack()[:-1] + b"x")
        with self.assertRaisesRegex(RuntimeError, "differs"):
            ios.inspect_app(app, export, record)

    def test_export_pack_tamper_missing_provenance_and_signatures_fail(self):
        app, export, record = self.app_fixture()
        for field, value in (("sha256", "0" * 64), ("bytes", 1), ("path", "ios/other.pck")):
            with self.subTest(field=field):
                changed = json.loads(json.dumps(record))
                changed["payload"][0][field] = value
                with self.assertRaises(RuntimeError):
                    ios.inspect_app(app, export, changed)
        (app / "_CodeSignature").mkdir()
        with self.assertRaisesRegex(RuntimeError, "Signature"):
            ios.inspect_app(app, export, record)
        (app / "_CodeSignature").rmdir()
        (export / "ios/sightbreak.pck").write_bytes(b"changed")
        with self.assertRaisesRegex(RuntimeError, "changed"):
            ios.inspect_app(app, export, record)

    def test_missing_duplicate_and_symlinked_pack_fail(self):
        app, export, record = self.app_fixture()
        packed = app / "sightbreak.pck"
        packed.unlink()
        with self.assertRaises(RuntimeError):
            ios.inspect_app(app, export, record)
        packed.symlink_to(export / "ios/sightbreak.pck")
        with self.assertRaises(RuntimeError):
            ios.inspect_app(app, export, record)
        packed.unlink()
        packed.write_bytes(pack())
        (app / "extra.pck").write_bytes(pack())
        with self.assertRaises(RuntimeError):
            ios.inspect_app(app, export, record)

    def test_timeout_retains_partial_log_and_kills_owned_group(self):
        log = self.root / "timeout.log"
        result = ios.bounded_command([sys.executable, "-c", "import time; print('before-timeout', flush=True); time.sleep(10)"], log, 0.15)
        self.assertTrue(result["timed_out"])
        self.assertTrue(result["cleanup_complete"], result)
        self.assertLess(result["seconds"], 6)
        self.assertIn("before-timeout", log.read_text())
        self.assertNotEqual(result["exit_code"], 0)

    def test_descendant_is_killed_even_when_command_leader_exits_zero(self):
        marker = self.root / "must-not-be-created"
        child = "import pathlib, signal, time; signal.signal(signal.SIGTERM, signal.SIG_IGN); time.sleep(1); pathlib.Path(" + repr(str(marker)) + ").write_text('escaped')"
        parent = "import subprocess, sys, time; subprocess.Popen([sys.executable, '-c', " + repr(child) + "]); time.sleep(0.1)"
        result = ios.bounded_command([sys.executable, "-c", parent], self.root / "descendant.log", 2)
        self.assertEqual(result["exit_code"], 0)
        self.assertTrue(result["unexpected_descendants"], result)
        self.assertTrue(result["cleanup_complete"], result)
        time.sleep(1.1)
        self.assertFalse(marker.exists())

    def test_cleanup_diagnostic_failure_never_reports_complete(self):
        from unittest.mock import patch
        with patch.object(ios, "group_state", side_effect=subprocess.CalledProcessError(1, "ps")):
            result = ios.bounded_command([sys.executable, "-c", "import time; time.sleep(10)"], self.root / "cleanup-failure.log", 0.1)
        self.assertTrue(result["timed_out"])
        self.assertFalse(result["cleanup_complete"])
        self.assertTrue(result["cleanup_errors"])
        self.assertNotEqual(result["exit_code"], 0)

    def test_nonzero_command_exit_is_retained_without_becoming_a_timeout(self):
        result = ios.bounded_command([sys.executable, "-c", "print('compiler-failed'); raise SystemExit(65)"], self.root / "compiler-failure.log", 2)
        self.assertEqual(result["exit_code"], 65)
        self.assertFalse(result["timed_out"])
        self.assertTrue(result["cleanup_complete"])
        self.assertIn("compiler-failed", (self.root / "compiler-failure.log").read_text())

    def test_native_requirement_fails_with_receipt_instead_of_skipping(self):
        from unittest.mock import patch
        with patch.object(ios.manifest, "source", return_value={"source_dirty": False, "source_game_dirty": False}), patch.object(ios.platform, "system", return_value="Linux"):
            result = ios.qualify(self.root / "receipts", self.root / "export", self.root / "derived", 1)
        self.assertEqual(result, 1)
        report = json.loads((self.root / "receipts/compile.json").read_text())
        self.assertFalse(report["compile_completed"])
        self.assertEqual(report["status"], "FAILED")
        self.assertIn("no test skip", report["failure"])

    def test_command_is_generic_device_debug_with_only_signing_disabled(self):
        command = ios.compile_command(self.root / "export", self.root / "derived")
        self.assertIn("generic/platform=iOS", command)
        self.assertIn("Debug", command)
        self.assertIn("CODE_SIGNING_ALLOWED=NO", command)
        self.assertEqual(command[-1], "build")
        self.assertFalse(any("archive" == word or "allowProvisioning" in word for word in command))

    def xcode_fixture(self, outcomes):
        applications = self.root / "Applications"
        for version in outcomes:
            developer = applications / ("Xcode_" + version + ".app/Contents/Developer")
            (developer / "Platforms/iPhoneOS.platform/Developer/SDKs/iPhoneOS.sdk").mkdir(parents=True)
        calls = []
        def attempt(label, command, environment):
            developer = Path(environment["DEVELOPER_DIR"])
            version = developer.parents[1].name.removeprefix("Xcode_").removesuffix(".app")
            calls.append((label, command, dict(environment)))
            if command[-1] == "--show-sdk-path":
                return 0, str(developer / "Platforms/iPhoneOS.platform/Developer/SDKs/iPhoneOS.sdk")
            result = outcomes[version]
            if result == 0:
                Path(command[-1]).write_bytes(macho())
            return result, "Undefined symbols" if result else ""
        return applications, calls, attempt

    def test_sdk_selection_falls_back_after_real_probe_failure_and_isolates_environment(self):
        applications, calls, attempt = self.xcode_fixture({"26.3": 1, "26.2": 0, "16.4": 1})
        before = dict(os.environ)
        environment = {"HOME": "/unchanged-home", "SIGHTBREAK_BUILDS_DIR": str(self.root / "export")}
        report = {}
        developer, sdk = ios.select_xcode(report, environment, self.root / "derived", attempt, applications)
        self.assertIn("Xcode_26.2.app", str(developer))
        self.assertTrue(sdk.is_relative_to(developer))
        self.assertEqual(environment["HOME"], "/unchanged-home")
        self.assertEqual(environment["DEVELOPER_DIR"], str(developer))
        self.assertEqual(dict(os.environ), before)
        self.assertEqual([item["probe_exit_code"] for item in report["sdk_selection"]["candidates"]], [1, 0])
        self.assertEqual(len(calls), 4)
        for _, command, candidate_env in calls:
            self.assertEqual(candidate_env["HOME"], "/unchanged-home")
            self.assertNotIn("xcode-select", command)
            if "clang" in command:
                self.assertIn("-no_adhoc_codesign", command)
                self.assertIn("arm64-apple-ios15.0", command)
                self.assertEqual(command.count("-u"), len(ios.REQUIRED_SDK_SYMBOLS))
                for symbol in ios.REQUIRED_SDK_SYMBOLS:
                    self.assertIn(symbol, command)

    def test_no_compatible_installed_sdk_fails_preflight_and_keeps_failure_evidence(self):
        applications, calls, attempt = self.xcode_fixture({"16.4": 1})
        environment = {"DEVELOPER_DIR": "/original/selection"}
        report = {}
        with self.assertRaisesRegex(RuntimeError, "No installed Xcode can link"):
            ios.select_xcode(report, environment, self.root / "derived", attempt, applications)
        self.assertEqual(environment["DEVELOPER_DIR"], "/original/selection")
        self.assertFalse(report["sdk_selection"]["candidates"][0]["compatible"])
        self.assertEqual(report["sdk_selection"]["candidates"][0]["probe_exit_code"], 1)
        self.assertEqual(len(calls), 2)

    def test_successful_probe_exit_requires_a_fresh_unsigned_device_binary(self):
        applications, _, attempt = self.xcode_fixture({"26.3": 0})
        def wrong_platform(label, command, environment):
            result = attempt(label, command, environment)
            if "clang" in command:
                Path(command[-1]).write_bytes(macho(platform=7))
            return result
        report = {}
        with self.assertRaisesRegex(RuntimeError, "No installed Xcode can link"):
            ios.select_xcode(report, {}, self.root / "derived", wrong_platform, applications)
        self.assertIn("device-iOS", report["sdk_selection"]["candidates"][0]["failure"])

    def test_actual_native_failed_log_never_qualifies_and_observed_linker_format_is_supported(self):
        log = (ios.manifest.ROOT / "docs/reports/gauntlet/m2-ios-compile/sdk-iteration/failure-0ca125d/xcodebuild-device.txt").read_text()
        with self.assertRaises(RuntimeError):
            ios.inspect_build_actions(log)
        actions = "\n".join(line for line in log.splitlines() if line.startswith(("CompileC ", "Ld ")))
        self.assertIn(" normal (in target 'sightbreak'", actions)
        # The success marker below is a fixture. The retained native run failed.
        self.assertTrue(ios.inspect_build_actions(actions + "\n** BUILD SUCCEEDED **\n")["linker_action"])
        self.assertTrue(ios.inspect_build_actions(actions.replace(" normal (", " normal arm64 (") + "\n** BUILD SUCCEEDED **\n")["linker_action"])
        for missing in ("CompileC", "Ld"):
            with self.subTest(missing=missing):
                with self.assertRaises(RuntimeError):
                    ios.inspect_build_actions("\n".join(line for line in actions.splitlines() if not line.startswith(missing)) + "\n** BUILD SUCCEEDED **\n")


if __name__ == "__main__":
    unittest.main()
