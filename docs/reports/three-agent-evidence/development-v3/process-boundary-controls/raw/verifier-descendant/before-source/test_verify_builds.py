#!/usr/bin/env python3
"""Adversarial artifact-verifier unit controls; never execute an engine or SDK.

Tiny synthetic ELF/PCK/ZIP fixtures exercise the real byte/receipt checks. Native
launches and cleanup are mocked, and all source identities are synthetic.
"""
from contextlib import ExitStack
import hashlib
import json
import os
import pathlib
import plistlib
import shutil
import struct
import subprocess
import tempfile
import unittest
import warnings
import zipfile
from unittest.mock import Mock, patch

import build_manifest as manifest
import verify_builds as verifier
import verify_packaged_builds as packaged


READY = b"Godot Engine v4.7.2\nSIGHTBREAK_MAIN_READY screen=menu\n"
SIGNATURE = (b"Verified using v2 scheme (APK Signature Scheme v2): true\n"
             b"Verified using v3 scheme (APK Signature Scheme v3): true\n")
BADGING = (f"package: name='com.sightbreak.game' versionCode='{manifest.BUILD_NUMBER}' "
           f"versionName='{manifest.VERSION}'\nsdkVersion:'24'\ntargetSdkVersion:'36'\n"
           "native-code: 'arm64-v8a' 'x86_64'\n").encode()
LAYOUT = (b"A: android:screenOrientation(0x1)=(type 0x10)0x0\nE: activity-alias\n"
          b'"com.godot.game.GodotAppLauncher"\n"com.godot.game.GodotApp"\n'
          b'android:exported(0x1)=(type 0x12)0xffffffff\n'
          b'"android.intent.action.MAIN"\n"android.intent.category.LAUNCHER"\nE: meta-data\n')


def resources():
    paths = ["res://.godot/imported/" + name + "fixture.scn" for name in
             ("relay_ar.glb-", "relay_ar_arms.glb-", "relay_ar_hands.glb-")]
    paths.extend("res://.godot/imported/" + name + "fixture.ctex" for name in
                 ("relay_ar_albedo.png-", "relay_ar_normal.png-", "relay_ar_orm.png-",
                  "relay_ar_arms_albedo.png-", "relay_ar_arms_normal.png-", "relay_ar_arms_orm.png-"))
    paths.extend("res://scripts/" + name + ".gdc" for name in
                 ("state_privacy", "snapshot_buffer", "movement_prediction", "movement_step", "peer_lifecycle",
                  "reconnect_policy", "result_outbox", "viewmodel_shading", "bot_ai", "reload_audio",
                  "reload_phases", "confirm_sheet"))
    return paths


def pack_bytes(paths):
    result = struct.pack("<6IQ", 0x43504447, 3, 4, 7, 2, 0, 0) + struct.pack("<QI", 40, len(paths))
    for path in paths:
        encoded = path.encode() + b"\0"
        result += struct.pack("<I", len(encoded)) + encoded + bytes(36)
    return result


def elf_bytes(paths):
    header = bytearray(64)
    header[:6] = b"\x7fELF\x02\x01"
    header[16:20] = struct.pack("<HH", 2, 62)
    pack = pack_bytes(paths)
    return header + pack + struct.pack("<QI", len(pack), 0x43504447)


class FixtureTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="sightbreak-verifier-unit-")
        self.addCleanup(temporary.cleanup)
        self.root = pathlib.Path(temporary.name) / "checkout with spaces & unicode-\u0152"
        self.root.mkdir()
        self.builds = self.root / "builds"
        self.current = {"source_commit": "frozen-commit", "source_game_tree": "frozen-tree",
                        "source_content_sha256": "runtime-bytes", "source_validation_sha256": "validation-bytes",
                        "source_game_dirty": False, "source_dirty": False}
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        for module in (manifest, verifier):
            self.stack.enter_context(patch.object(module, "ROOT", self.root))
            self.stack.enter_context(patch.object(module, "BUILDS", self.builds))
            self.stack.enter_context(patch.object(module, "source", side_effect=lambda: dict(self.current)))
        self.stack.enter_context(patch.object(packaged, "BUILDS", self.builds))
        # Windows has no POSIX executable stat bits. Give synthetic fixtures
        # explicit receipt modes, while extraction checks real modes on POSIX.
        self.stack.enter_context(patch.object(manifest, "archive_mode", side_effect=lambda path:
            0o755 if path.name == "sightbreak.x86_64" or path.suffix == ".sh" else 0o644))
        self.launches = []
        self.children = []
        self.cleanup = self.stack.enter_context(patch.object(verifier, "terminate_process_tree"))
        self.popen = self.stack.enter_context(patch.object(verifier.subprocess, "Popen", side_effect=self.launch))
        self.stack.enter_context(patch.object(packaged, "linux_host", return_value=True))
        self.stack.enter_context(patch("builtins.print"))
        self.output_overrides = {}
        self.exit_code = 0
        self.poll_code = 0
        self.wait_error = None
        self.launch_hook = None
        self.attempt_number = 0
        self.make_exports()

    def make_exports(self, wrappers=("sightbreak.sh", "console launch.sh")):
        for target in manifest.OUTPUTS:
            manifest.begin(target)
            path = self.builds / manifest.OUTPUTS[target]
            path.parent.mkdir(parents=True, exist_ok=True)
            if target == "linux":
                path.write_bytes(elf_bytes(resources()))
                path.chmod(0o755)
                for name in wrappers:
                    wrapper = self.builds / target / name
                    wrapper.write_text('#!/bin/sh\nexec "$(dirname "$0")/sightbreak.x86_64" "$@"\n', encoding="utf-8")
                    wrapper.chmod(0o755)
            elif target == "android":
                with zipfile.ZipFile(path, "w") as bundle:
                    for resource in resources():
                        bundle.writestr("assets/" + resource.removeprefix("res://"), b"resource fixture")
            else:
                path.write_text(f'DEVELOPMENT_TEAM = "";\nPRODUCT_BUNDLE_IDENTIFIER = com.sightbreak.game;\n'
                                f'MARKETING_VERSION = {manifest.IOS_VERSION};\n'
                                f'CURRENT_PROJECT_VERSION = {manifest.BUILD_NUMBER};\n', encoding="utf-8")
                (self.builds / target / "sightbreak.pck").write_bytes(pack_bytes(resources()))
                plist_path = self.builds / target / "sightbreak/sightbreak-Info.plist"
                plist_path.parent.mkdir()
                plist_path.write_bytes(plistlib.dumps({"CFBundleIdentifier": "$(PRODUCT_BUNDLE_IDENTIFIER)",
                    "NSLocalNetworkUsageDescription": "Fixture network", "UISupportedInterfaceOrientations":
                    ["UIInterfaceOrientationLandscapeLeft", "UIInterfaceOrientationLandscapeRight"]}))
            (self.builds / target / "GODOT-LICENSE.txt").write_text("license fixture\n", encoding="utf-8")
            manifest.finish(target)

    def launch(self, command, **kwargs):
        self.launches.append((command, kwargs))
        if pathlib.Path(command[0]).name == "apksigner":
            label, content = "android-signature", SIGNATURE
        elif "badging" in command:
            label, content = "android-manifest", BADGING
        elif "xmltree" in command:
            label, content = "android-layout", LAYOUT
        else:
            label = "linux-demo" if "--demo" in command else "linux-menu"
            content = READY
        content = self.output_overrides.get(label, content)
        kwargs["stdout"].write(content)
        kwargs["stdout"].flush()
        process = Mock(pid=1000 + len(self.launches))
        process.wait.return_value = self.exit_code
        process.poll.return_value = self.poll_code
        process.log = kwargs["stdout"]
        if self.wait_error is not None:
            process.wait.side_effect = self.wait_error
        self.children.append(process)
        if self.launch_hook:
            self.launch_hook(command, kwargs)
        return process

    def run_verifier(self, module=verifier):
        self.attempt_number += 1
        output = self.root / f"evidence {self.attempt_number}"
        code = module.main(["--output", str(output)])
        report = json.loads((output / "results.json").read_text(encoding="utf-8"))
        evidence = os.environ.get("SIGHTBREAK_VERIFY_UNIT_EVIDENCE")
        if code and evidence:
            name = hashlib.sha256(self.id().encode()).hexdigest()[:12] + f"-{self.attempt_number}"
            retained = pathlib.Path(evidence) / name
            shutil.copytree(output, retained)
            (retained / "UNIT-MOCK-ONLY.txt").write_text(
                "Synthetic unit control; no engine or SDK process was executed.\nTest: " + self.id() + "\n", encoding="utf-8")
        return code, report, output

    def refresh_fixture_receipt(self, target):
        """Only synthetic fixtures may deliberately describe an invalid export."""
        path = self.builds / target / "source.json"
        record = json.loads(path.read_text())
        record.update(artifact=manifest.descriptor(self.builds / manifest.OUTPUTS[target]), payload=manifest.payload(target))
        manifest.write_json(path, record)

    def package(self):
        manifest.package()

    def rewrite_archive(self, target, transform):
        name = f"sightbreak-{target}-{'xcode-project' if target == 'ios' else 'debug'}.zip"
        path = self.builds / name
        with zipfile.ZipFile(path) as bundle:
            entries = [(entry, bundle.read(entry)) for entry in bundle.infolist()]
        entries = transform(entries)
        with warnings.catch_warnings(), zipfile.ZipFile(path, "w") as bundle:
            warnings.simplefilter("ignore", UserWarning)  # intentional duplicate-member controls
            for entry, content in entries:
                bundle.writestr(entry, content)
        # Recompute only the outer ZIP hash. Inner export receipts remain
        # frozen, so these controls actually exercise archived-member gates.
        data = json.loads((self.builds / "manifest.json").read_text())
        data["artifacts"] = [manifest.descriptor(path) if item["path"] == name else item for item in data["artifacts"]]
        manifest.write_json(self.builds / "manifest.json", data)
        (self.builds / "checksums.txt").write_text("".join(f"{item['sha256']}  {item['path']}\n" for item in data["artifacts"]))

    def assert_failed(self, code, report, text):
        self.assertEqual(code, 1)
        self.assertFalse(report["passed"])
        self.assertEqual(report["status"], "failed")
        self.assertTrue(any(text in failure for failure in report["failures"]), report["failures"])


class AttemptTests(FixtureTests):
    def test_native_export_success_preserves_all_existing_gates(self):
        code, report, output = self.run_verifier()
        self.assertEqual(code, 0)
        self.assertTrue(report["passed"] and report["completed"] and report["source_unchanged"])
        self.assertEqual(report["source_before"], self.current)
        self.assertEqual(report["source_after"], self.current)
        self.assertEqual(len(self.launches), 5)
        self.assertEqual(report["android_signature_schemes"], ["v2", "v3"])
        self.assertEqual(report["android_abis"], ["arm64-v8a", "x86_64"])
        self.assertTrue(report["linux_demo_120_frames"] and report["android_landscape_manifest"]
                        and report["ios_project_plist_and_unsigned_team"])
        self.assertIn([str(self.builds / manifest.OUTPUTS["linux"]), "--headless", "--quit-after", "120", "--", "--demo"],
                      [command for command, _ in self.launches])
        for command, options in self.launches:
            self.assertNotIn("shell", options)
            self.assertTrue("creationflags" in options or options.get("start_new_session") is True)
            self.assertEqual(options["stderr"], subprocess.STDOUT)
            self.assertEqual(options["env"]["XDG_DATA_HOME"], str(output / "state/data"))
        self.assertEqual(self.cleanup.call_count, 5)
        for gate in ("physical_device_installation", "device_performance", "xcode_build"):
            self.assertEqual(report[gate], "NOT TESTED")

    def test_default_output_is_fresh_verification_directory(self):
        self.assertEqual(verifier.main([]), 0)
        self.assertTrue((self.builds / "verification/results.json").is_file())

    def test_previous_success_and_log_are_refused_untouched(self):
        output = self.root / "earlier passed attempt"
        output.mkdir()
        files = {"results.json": b'{"passed":true}\n', "linux-menu.log": b"earlier successful log\n"}
        for name, content in files.items():
            (output / name).write_bytes(content)
        with patch("sys.stderr"), self.assertRaises(SystemExit) as failure:
            verifier.main(["--output", str(output)])
        self.assertEqual(failure.exception.code, 2)
        self.popen.assert_not_called()
        self.assertEqual({path.name: path.read_bytes() for path in output.iterdir()}, files)

    def test_previous_failed_log_alone_is_also_refused_untouched(self):
        output = self.root / "failed evidence"
        output.mkdir()
        (output / "linux-menu.log").write_bytes(b"timeout partial log")
        with patch("sys.stderr"), self.assertRaises(SystemExit):
            verifier.main(["--output", str(output)])
        self.assertEqual((output / "linux-menu.log").read_bytes(), b"timeout partial log")
        self.assertFalse((output / "results.json").exists())

    def test_incomplete_false_result_exists_before_any_native_launch(self):
        def check_initial(command, options):
            path = pathlib.Path(options["stdout"].name).parent / "results.json"
            data = json.loads(path.read_text())
            self.assertFalse(data["passed"] or data["completed"])
            self.assertEqual(data["status"], "incomplete")
        self.launch_hook = check_initial
        self.assertEqual(self.run_verifier()[0], 0)

    def test_dirty_preflight_writes_failed_result_without_launching(self):
        self.current["source_dirty"] = True
        code, report, _ = self.run_verifier()
        self.assert_failed(code, report, "validation tooling")
        self.popen.assert_not_called()

    def test_missing_export_receipt_is_a_failed_current_attempt(self):
        (self.builds / "linux/source.json").unlink()
        code, report, _ = self.run_verifier()
        self.assert_failed(code, report, "FileNotFoundError")
        self.popen.assert_not_called()

    def test_invalid_json_export_receipt_is_a_failed_current_attempt(self):
        (self.builds / "linux/source.json").write_text("{broken")
        code, report, _ = self.run_verifier()
        self.assert_failed(code, report, "JSONDecodeError")
        self.popen.assert_not_called()

    def test_incomplete_or_dirty_export_receipt_prevents_launch(self):
        path = self.builds / "linux/source.json"
        original = path.read_bytes()
        for key, value in (("export_completed", False), ("source_game_dirty", True), ("source_dirty", True)):
            with self.subTest(key=key):
                record = json.loads(original)
                record[key] = value
                manifest.write_json(path, record)
                code, report, _ = self.run_verifier()
                self.assertEqual(code, 1)
                self.assertFalse(report["passed"])
        self.popen.assert_not_called()

    def test_payload_changed_before_verification_prevents_launch(self):
        (self.builds / "linux/GODOT-LICENSE.txt").write_bytes(b"stale license")
        code, report, _ = self.run_verifier()
        self.assert_failed(code, report, "payload changed after export")
        self.popen.assert_not_called()

    def test_source_lookup_failure_is_retained_even_before_preflight(self):
        with patch.object(verifier, "source", side_effect=FileNotFoundError("git unavailable")):
            code, report, _ = self.run_verifier()
        self.assert_failed(code, report, "git unavailable")
        self.assertIsNone(report["source_before"])
        self.popen.assert_not_called()

    def test_timeout_retains_raw_partial_bytes_and_cleans_process_tree(self):
        partial = b"\xffraw partial stdout before timeout\nSIGHTBREAK_MAIN_READY screen=menu\n"
        self.output_overrides["linux-menu"] = partial
        self.wait_error = subprocess.TimeoutExpired("native fixture", 120)
        self.poll_code = -9
        code, report, output = self.run_verifier()
        self.assert_failed(code, report, "timed out")
        self.assertEqual((output / "linux-menu.log").read_bytes(), partial)
        self.assertTrue(report["processes"][0]["timed_out"])
        self.assertEqual(report["processes"][0]["exit"], -9)
        self.cleanup.assert_called_once_with(self.children[0])
        self.popen.assert_called_once()

    def test_nonzero_native_exit_rejected_even_with_readiness_marker(self):
        self.exit_code = self.poll_code = 7
        code, report, _ = self.run_verifier()
        self.assert_failed(code, report, "expected actual exit 0")
        self.assertEqual(report["processes"][0]["exit"], 7)
        self.cleanup.assert_called_once()

    def test_running_child_cannot_pass_with_fabricated_wait_zero(self):
        self.poll_code = None
        code, report, _ = self.run_verifier()
        self.assert_failed(code, report, "exit=None")
        self.cleanup.assert_called_once()

    def test_resource_leak_or_engine_error_cannot_pass_with_exit_zero(self):
        for text in (b"WARNING: 4 ObjectDB instances were leaked at exit\n", b"Leaked instance: AudioStreamWAV\n",
                     b"ERROR: failed\n", b"SCRIPT ERROR: bad\n", b"Parse Error: bad\n"):
            with self.subTest(text=text):
                self.output_overrides["linux-menu"] = READY + text
                code, report, _ = self.run_verifier()
                self.assert_failed(code, report, "error or resource leak")

    def test_leak_emitted_during_cleanup_is_not_lost(self):
        def cleanup(process):
            process.log.write(b"WARNING: ObjectDB instances leaked at exit\n")
            process.log.flush()
        self.cleanup.side_effect = cleanup
        code, report, output = self.run_verifier()
        self.assert_failed(code, report, "resource leak")
        self.assertIn(b"instances leaked", (output / "linux-menu.log").read_bytes())

    def test_cleanup_error_cannot_leave_passed_result(self):
        self.cleanup.side_effect = RuntimeError("tree cleanup unavailable")
        code, report, _ = self.run_verifier()
        self.assert_failed(code, report, "process-tree cleanup failed")

    def test_launch_error_retains_failed_result_and_raw_empty_log(self):
        self.popen.side_effect = OSError("exec format error")
        code, report, output = self.run_verifier()
        self.assert_failed(code, report, "exec format error")
        self.assertEqual((output / "linux-menu.log").read_bytes(), b"")
        self.cleanup.assert_not_called()

    def test_interrupt_still_cleans_and_records_failure(self):
        self.wait_error = KeyboardInterrupt()
        code, report, _ = self.run_verifier()
        self.assert_failed(code, report, "KeyboardInterrupt")
        self.cleanup.assert_called_once()

    def test_exact_final_source_identity_changes_rejected(self):
        before = dict(self.current)
        for key in ("source_commit", "source_game_tree", "source_content_sha256", "source_validation_sha256"):
            with self.subTest(key=key), patch.object(verifier, "source", side_effect=[before, {**before, key: "changed"}]):
                code, report, _ = self.run_verifier()
                self.assert_failed(code, report, "Frozen source changed")
                self.assertFalse(report["source_unchanged"])

    def test_failed_final_source_lookup_cannot_leave_success(self):
        with patch.object(verifier, "source", side_effect=[dict(self.current), OSError("git failed at end")]):
            code, report, _ = self.run_verifier()
        self.assert_failed(code, report, "Final source check")
        self.assertIsNone(report["source_after"])

    def test_final_secondary_payload_mutation_rejected(self):
        def mutate(command, options):
            (self.builds / "linux/GODOT-LICENSE.txt").write_bytes(b"changed during native verification")
        self.launch_hook = mutate
        code, report, _ = self.run_verifier()
        self.assert_failed(code, report, "payload changed after export")

    def test_final_primary_payload_mutation_rejected(self):
        def mutate(command, options):
            if "--demo" in command:
                with (self.builds / manifest.OUTPUTS["linux"]).open("ab") as stream:
                    stream.write(b"new bytes after engine exit")
        self.launch_hook = mutate
        code, report, _ = self.run_verifier()
        self.assert_failed(code, report, "artifact changed after export")

    def test_final_export_receipt_mutation_rejected(self):
        def mutate(command, options):
            path = self.builds / "linux/source.json"
            data = json.loads(path.read_text())
            data["built_at_utc"] = "changed receipt"
            manifest.write_json(path, data)
        self.launch_hook = mutate
        code, report, _ = self.run_verifier()
        self.assert_failed(code, report, "export receipt changed")

    def test_stale_validation_commit_or_runtime_receipt_prevents_launch(self):
        path = self.builds / "linux/source.json"
        original = path.read_bytes()
        for key in ("source_commit", "source_game_tree", "source_content_sha256", "source_validation_sha256"):
            with self.subTest(key=key):
                data = json.loads(original)
                data[key] = "stale identity"
                manifest.write_json(path, data)
                code, report, _ = self.run_verifier()
                self.assert_failed(code, report, "different frozen source identity")
        self.popen.assert_not_called()

    def test_missing_readiness_marker_fails(self):
        self.output_overrides["linux-menu"] = b"Godot started without a menu\n"
        code, report, _ = self.run_verifier()
        self.assert_failed(code, report, "readiness marker missing")

    def test_linux_must_be_a_real_x86_64_elf(self):
        with self.assertRaisesRegex(RuntimeError, "ELF"):
            verifier.linux_elf(self.builds / "linux/sightbreak.sh")

    def test_each_required_integrated_resource_remains_required(self):
        for resource in resources():
            with self.subTest(resource=resource), self.assertRaisesRegex(RuntimeError, "Missing"):
                verifier.integrated_resources([path for path in resources() if path != resource])

    def test_shipped_test_harnesses_and_empty_packs_remain_rejected(self):
        for paths in ([], ["res://tests/probe.gdc"], ["res://scripts/network_test.gdc"]):
            with self.subTest(paths=paths), self.assertRaises(RuntimeError):
                verifier.no_test_harnesses(paths)

    def test_both_android_signature_schemes_remain_required(self):
        for scheme in (b"v2", b"v3"):
            with self.subTest(scheme=scheme):
                self.output_overrides["android-signature"] = b"\n".join(line for line in SIGNATURE.splitlines() if scheme not in line)
                code, report, _ = self.run_verifier()
                self.assert_failed(code, report, "signature not verified")

    def test_all_android_metadata_and_abis_remain_required(self):
        for token in (b"com.sightbreak.game", str(manifest.BUILD_NUMBER).encode(), manifest.VERSION.encode(),
                      b"sdkVersion:'24'", b"targetSdkVersion:'36'", b"arm64-v8a", b"x86_64"):
            with self.subTest(token=token):
                self.output_overrides["android-manifest"] = BADGING.replace(token, b"removed")
                code, report, _ = self.run_verifier()
                self.assert_failed(code, report, "Missing APK metadata")

    def test_android_landscape_and_exported_launcher_gates_remain_required(self):
        for token in (b"0x0\n", b"com.godot.game.GodotAppLauncher", b"com.godot.game.GodotApp\"",
                      b"0xffffffff", b"android.intent.action.MAIN", b"android.intent.category.LAUNCHER"):
            with self.subTest(token=token):
                self.output_overrides["android-layout"] = LAYOUT.replace(token, b"removed")
                code, report, _ = self.run_verifier()
                self.assertEqual(code, 1)
                self.assertFalse(report["passed"])

    def test_ios_unsigned_version_and_bundle_gates_remain_required(self):
        path = self.builds / "ios/sightbreak.xcodeproj/project.pbxproj"
        for token in ('DEVELOPMENT_TEAM = "";', "PRODUCT_BUNDLE_IDENTIFIER = com.sightbreak.game;",
                      f"MARKETING_VERSION = {manifest.IOS_VERSION};", f"CURRENT_PROJECT_VERSION = {manifest.BUILD_NUMBER};"):
            with self.subTest(token=token):
                original = path.read_bytes()
                path.write_text(original.decode().replace(token, "removed"))
                record_path = self.builds / "ios/source.json"
                record = json.loads(record_path.read_text())
                record.update(artifact=manifest.descriptor(path), payload=manifest.payload("ios"))
                manifest.write_json(record_path, record)
                code, report, _ = self.run_verifier()
                self.assertEqual(code, 1)
                self.assertFalse(report["passed"])
                path.write_bytes(original)

    def test_ios_plist_identity_network_and_landscape_gates_remain_required(self):
        path = self.builds / "ios/sightbreak/sightbreak-Info.plist"
        original = plistlib.loads(path.read_bytes())
        for key, value in (("CFBundleIdentifier", "wrong.bundle"), ("NSLocalNetworkUsageDescription", ""),
                           ("UISupportedInterfaceOrientations", []),
                           ("UISupportedInterfaceOrientations", ["UIInterfaceOrientationPortrait"])):
            with self.subTest(key=key, value=value):
                path.write_bytes(plistlib.dumps({**original, key: value}))
                self.refresh_fixture_receipt("ios")
                code, report, _ = self.run_verifier()
                self.assertEqual(code, 1)
                self.assertFalse(report["passed"])

    def test_ios_unsigned_placeholder_team_cannot_ship(self):
        with (self.builds / manifest.OUTPUTS["ios"]).open("a") as stream:
            stream.write("UNSIGNED00\n")
        self.refresh_fixture_receipt("ios")
        code, report, _ = self.run_verifier()
        self.assert_failed(code, report, "unsigned team")

    def test_test_harness_cannot_ship_in_android_export(self):
        with zipfile.ZipFile(self.builds / manifest.OUTPUTS["android"], "a") as bundle:
            bundle.writestr("assets/tests/probe.gdc", b"must not ship")
        self.refresh_fixture_receipt("android")
        code, report, _ = self.run_verifier()
        self.assert_failed(code, report, "Test harness shipped")

    def test_missing_compiled_module_in_ios_pack_is_rejected(self):
        (self.builds / "ios/sightbreak.pck").write_bytes(pack_bytes([path for path in resources() if "bot_ai" not in path]))
        self.refresh_fixture_receipt("ios")
        code, report, _ = self.run_verifier()
        self.assert_failed(code, report, "Missing compiled module: bot_ai")


class PackagedTests(FixtureTests):
    def setUp(self):
        super().setUp()
        self.package()

    def test_success_extracts_every_member_and_runs_elf_and_every_wrapper_directly(self):
        code, report, output = self.run_verifier(packaged)
        self.assertEqual(code, 0)
        self.assertTrue(report["passed"] and report["packaged_linux_elf_smoke"])
        self.assertEqual(report["packaged_linux_console_wrappers_smoke"], ["linux/console launch.sh", "linux/sightbreak.sh"])
        self.assertEqual(len(self.launches), 3)
        self.assertEqual(self.cleanup.call_count, 3)
        for command, options in self.launches:
            executable = pathlib.Path(command[0])
            self.assertTrue(executable.is_relative_to(output / "extracted/linux"))
            self.assertEqual(command[1:], ["--headless", "--", "--smoke"])
            self.assertEqual(options["cwd"], executable.parent)
            self.assertNotIn("shell", options)
        for target, record in report["archives_verified"].items():
            self.assertTrue(record["byte_hashes_verified"] and record["archive_modes_verified"])
            for item in record["members"]:
                path = output / "extracted" / item["path"]
                self.assertEqual(path.stat().st_size, item["bytes"])
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), item["sha256"])
            self.assertTrue((output / "extracted" / target / "source.json").exists())
        for gate in ("physical_device_installation", "device_performance", "xcode_build"):
            self.assertEqual(report[gate], "NOT TESTED")

    def test_packaged_default_output_directory(self):
        self.assertEqual(packaged.main([]), 0)
        self.assertTrue((self.builds / "packaged-verification/results.json").is_file())

    def test_packaged_stale_success_refused_without_altering_any_evidence(self):
        output = self.root / "prior package verification"
        output.mkdir()
        (output / "results.json").write_bytes(b'{"passed":true}\n')
        with patch("sys.stderr"), self.assertRaises(SystemExit):
            packaged.main(["--output", str(output)])
        self.assertEqual((output / "results.json").read_bytes(), b'{"passed":true}\n')
        self.popen.assert_not_called()

    def test_missing_package_manifest_retains_preflight_failure(self):
        (self.builds / "manifest.json").unlink()
        code, report, _ = self.run_verifier(packaged)
        self.assert_failed(code, report, "FileNotFoundError")
        self.popen.assert_not_called()

    def test_dirty_packaged_preflight_never_launches(self):
        self.current["source_dirty"] = True
        code, report, _ = self.run_verifier(packaged)
        self.assert_failed(code, report, "validation tooling")
        self.popen.assert_not_called()

    def test_packaged_manifest_must_bind_exact_current_source(self):
        path = self.builds / "manifest.json"
        original = path.read_bytes()
        for key in ("source_commit", "source_game_tree", "source_content_sha256", "source_validation_sha256"):
            with self.subTest(key=key):
                data = json.loads(original)
                data[key] = "different source"
                manifest.write_json(path, data)
                code, report, _ = self.run_verifier(packaged)
                self.assert_failed(code, report, "different frozen source identity")
        self.popen.assert_not_called()

    def test_outer_archive_hash_mismatch_prevents_execution(self):
        with (self.builds / "sightbreak-linux-debug.zip").open("ab") as stream:
            stream.write(b"changed package")
        code, report, _ = self.run_verifier(packaged)
        self.assert_failed(code, report, "Packaged artifact changed")
        self.popen.assert_not_called()

    def test_checksums_are_complete_unique_and_match_manifest(self):
        path = self.builds / "checksums.txt"
        original = path.read_text()
        for content in ("", original.splitlines()[0] + "\n", original + original.splitlines()[0] + "\n",
                        original.replace(original[:64], "0" * 64, 1), "not a checksum\n"):
            with self.subTest(content=content):
                path.write_text(content)
                code, report, _ = self.run_verifier(packaged)
                self.assertEqual(code, 1)
                self.assertFalse(report["passed"])
        self.popen.assert_not_called()

    def test_traversal_absolute_backslash_drive_and_noncanonical_paths_rejected(self):
        for name in ("linux/../../escaped.txt", "/escaped.txt", "linux\\..\\escaped.txt", "C:/escaped.txt",
                     "linux//escaped.txt", "linux/./escaped.txt", ".", "", "linux/file\x00suffix"):
            with self.subTest(name=name), self.assertRaisesRegex(RuntimeError, "Unsafe"):
                packaged.safe_member(name, "linux")

    def test_traversal_member_is_rejected_before_extraction_or_execution(self):
        def mutate(entries):
            entry = zipfile.ZipInfo("linux/../../escaped.txt")
            entry.create_system = 3
            entry.external_attr = 0o100644 << 16
            return [*entries, (entry, b"must not be extracted")]
        self.rewrite_archive("linux", mutate)
        code, report, output = self.run_verifier(packaged)
        self.assert_failed(code, report, "Unsafe archive path")
        self.assertFalse((output / "escaped.txt").exists())
        self.assertFalse((output / "extracted").exists())
        self.popen.assert_not_called()

    def test_duplicate_member_rejected_even_when_outer_archive_hash_is_valid(self):
        self.rewrite_archive("linux", lambda entries: [*entries, entries[0]])
        code, report, _ = self.run_verifier(packaged)
        self.assert_failed(code, report, "inventory differs")
        self.popen.assert_not_called()

    def test_missing_member_rejected_even_when_outer_archive_hash_is_valid(self):
        self.rewrite_archive("linux", lambda entries: entries[1:])
        code, report, _ = self.run_verifier(packaged)
        self.assert_failed(code, report, "inventory differs")
        self.popen.assert_not_called()

    def test_archived_member_bytes_must_match_receipt_not_just_zip_hash(self):
        def mutate(entries):
            return [(entry, b"X" * len(content) if entry.filename.endswith("GODOT-LICENSE.txt") else content)
                    for entry, content in entries]
        self.rewrite_archive("linux", mutate)
        code, report, _ = self.run_verifier(packaged)
        self.assert_failed(code, report, "Extracted bytes differ from receipt")
        self.popen.assert_not_called()

    def test_archived_receipt_bytes_must_equal_original_export_receipt(self):
        def mutate(entries):
            return [(entry, content.replace(b"  ", b"\t ") if entry.filename.endswith("/source.json") else content)
                    for entry, content in entries]
        self.rewrite_archive("linux", mutate)
        code, report, _ = self.run_verifier(packaged)
        self.assert_failed(code, report, "Extracted bytes differ from receipt")
        self.popen.assert_not_called()

    def test_archived_wrapper_executable_mode_must_match_receipt(self):
        def mutate(entries):
            for entry, _ in entries:
                if entry.filename.endswith(".sh"):
                    entry.external_attr = 0o100644 << 16
            return entries
        self.rewrite_archive("linux", mutate)
        code, report, _ = self.run_verifier(packaged)
        self.assert_failed(code, report, "executable mode differs")
        self.popen.assert_not_called()

    def test_archived_symlink_or_special_permission_bits_rejected(self):
        path = self.builds / "sightbreak-linux-debug.zip"
        original = path.read_bytes()
        for mode in (0o120755, 0o104755):
            with self.subTest(mode=mode):
                path.write_bytes(original)
                def mutate(entries):
                    for entry, _ in entries:
                        if entry.filename.endswith(".sh"):
                            entry.external_attr = mode << 16
                    return entries
                self.rewrite_archive("linux", mutate)
                code, report, _ = self.run_verifier(packaged)
                self.assertEqual(code, 1)
                self.assertFalse(report["passed"])
        self.popen.assert_not_called()

    def test_no_console_wrappers_is_a_failure_even_with_valid_archive_receipts(self):
        # Build fresh synthetic receipts/package inventory without wrappers.
        for path in (self.builds / "linux").glob("*.sh"):
            path.unlink()
        receipt = self.builds / "linux/source.json"
        record = json.loads(receipt.read_text())
        record["payload"] = manifest.payload("linux")
        manifest.write_json(receipt, record)
        data = json.loads((self.builds / "manifest.json").read_text())
        data["exports"] = [record if item["target"] == "linux" else item for item in data["exports"]]
        manifest.write_json(self.builds / "manifest.json", data)
        self.rewrite_archive("linux", lambda entries: [(entry, receipt.read_bytes() if entry.filename.endswith("/source.json") else content)
                                                     for entry, content in entries if not entry.filename.endswith(".sh")])
        code, report, _ = self.run_verifier(packaged)
        self.assert_failed(code, report, "console wrapper(s) missing")
        self.popen.assert_not_called()

    def test_nonlinux_host_fails_without_any_runtime_pass_claim(self):
        with patch.object(packaged, "linux_host", return_value=False):
            code, report, _ = self.run_verifier(packaged)
        self.assert_failed(code, report, "requires Linux")
        self.assertNotIn("packaged_linux_elf_smoke", report)
        self.popen.assert_not_called()

    def test_packaged_nonzero_engine_exit_rejected_even_with_menu_marker(self):
        self.exit_code = self.poll_code = 9
        code, report, _ = self.run_verifier(packaged)
        self.assert_failed(code, report, "expected actual exit 0")
        self.cleanup.assert_called_once()

    def test_packaged_wrapper_nonzero_exit_is_not_hidden_by_successful_elf(self):
        def change_exit(command, options):
            if command[0].endswith(".sh"):
                self.children[-1].wait.return_value = self.children[-1].poll.return_value = 8
        self.launch_hook = change_exit
        code, report, _ = self.run_verifier(packaged)
        self.assert_failed(code, report, "linux-wrapper-0: expected actual exit 0")
        self.assertEqual(len(self.launches), 2)

    def test_packaged_wrapper_timeout_retains_raw_log_and_cleans_tree(self):
        def timeout_wrapper(command, options):
            if command[0].endswith(".sh"):
                options["stdout"].write(b"wrapper partial text before timeout\n")
                options["stdout"].flush()
                self.children[-1].wait.side_effect = subprocess.TimeoutExpired(command, 120)
                self.children[-1].poll.return_value = -9
        self.launch_hook = timeout_wrapper
        code, report, output = self.run_verifier(packaged)
        self.assert_failed(code, report, "timed out")
        self.assertIn(b"wrapper partial text before timeout", (output / "linux-wrapper-0.log").read_bytes())
        self.assertEqual(self.cleanup.call_count, 2)

    def test_packaged_wrapper_must_reach_the_actual_menu(self):
        def no_menu(command, options):
            if command[0].endswith(".sh"):
                options["stdout"].seek(0)
                options["stdout"].truncate()
                options["stdout"].write(b"wrapper finished without starting the menu\n")
                options["stdout"].flush()
        self.launch_hook = no_menu
        code, report, _ = self.run_verifier(packaged)
        self.assert_failed(code, report, "Packaged Linux menu readiness marker missing")

    def test_packaged_wrapper_resource_leak_cannot_hide_behind_clean_elf(self):
        def leak(command, options):
            if command[0].endswith(".sh"):
                options["stdout"].write(b"WARNING: ObjectDB instances leaked at exit\n")
                options["stdout"].flush()
        self.launch_hook = leak
        code, report, _ = self.run_verifier(packaged)
        self.assert_failed(code, report, "linux-wrapper-0: emitted error or resource leak")

    def test_packaged_resource_leak_rejected(self):
        self.output_overrides["linux-menu"] = READY + b"WARNING: 4 ObjectDB instances were leaked at exit\n"
        code, report, _ = self.run_verifier(packaged)
        self.assert_failed(code, report, "resource leak")

    def test_final_archive_mutation_is_rejected(self):
        def mutate(command, options):
            with (self.builds / "sightbreak-linux-debug.zip").open("ab") as stream:
                stream.write(b"concurrent archive mutation")
        self.launch_hook = mutate
        code, report, _ = self.run_verifier(packaged)
        self.assert_failed(code, report, "Packaged artifact changed during verification")

    def test_final_manifest_or_checksums_mutation_is_rejected(self):
        for filename in ("manifest.json", "checksums.txt"):
            original = (self.builds / filename).read_bytes()
            def mutate(command, options):
                with (self.builds / filename).open("ab") as stream:
                    stream.write(b"\n")
            with self.subTest(filename=filename):
                self.launch_hook = mutate
                code, report, _ = self.run_verifier(packaged)
                self.assert_failed(code, report, "changed during verification")
                (self.builds / filename).write_bytes(original)

    def test_final_extracted_bytes_mutation_is_rejected(self):
        def mutate(command, options):
            (pathlib.Path(command[0]).parent / "GODOT-LICENSE.txt").write_bytes(b"changed extracted license")
        self.launch_hook = mutate
        code, report, _ = self.run_verifier(packaged)
        self.assert_failed(code, report, "Extracted payload changed during verification")

    def test_final_extracted_extra_file_is_rejected(self):
        def mutate(command, options):
            (pathlib.Path(command[0]).parent / "unreceipted-file.txt").write_bytes(b"unexpected")
        self.launch_hook = mutate
        code, report, _ = self.run_verifier(packaged)
        self.assert_failed(code, report, "Extracted payload inventory changed")

    def test_final_unpacked_export_mutation_is_also_rejected(self):
        def mutate(command, options):
            (self.builds / "android/GODOT-LICENSE.txt").write_bytes(b"concurrent raw payload mutation")
        self.launch_hook = mutate
        code, report, _ = self.run_verifier(packaged)
        self.assert_failed(code, report, "android: payload changed after export")

    def test_final_exact_packaged_source_change_is_rejected(self):
        before = dict(self.current)
        with patch.object(verifier, "source", side_effect=[before, {**before, "source_validation_sha256": "changed"}]):
            code, report, _ = self.run_verifier(packaged)
        self.assert_failed(code, report, "Frozen source changed")
        self.assertFalse(report["source_unchanged"])


if __name__ == "__main__":
    unittest.main()
