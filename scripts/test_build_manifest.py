#!/usr/bin/env python3
"""Regression checks for export/source provenance; no engine or SDK required."""
import json
import configparser
import pathlib
import tempfile
import unittest
from unittest.mock import patch

import build_manifest as manifest
import native_log


class NativeLogTests(unittest.TestCase):
    def test_actual_engine_warning_and_errors_rejected(self):
        for message in ('WARNING: 4 ObjectDB instances were leaked at exit (run with `--verbose` for details).',
                        'WARNING: ObjectDB instances leaked at exit', 'Leaked instance: AudioStreamWAV',
                        'ERROR: failed', 'SCRIPT ERROR: broken', 'Parse Error: invalid'):
            with self.subTest(message=message): self.assertTrue(native_log.failed(message))

    def test_normal_log_and_vsync_warning_allowed(self):
        self.assertFalse(native_log.failed('Godot Engine v4.7.2\nWARNING: Could not set V-Sync mode'))


class BuildManifestTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = pathlib.Path(self.temporary.name)
        self.builds = self.root / "builds"
        self.current = {"source_commit": "abc", "source_game_tree": "def", "source_content_sha256": "123", "source_game_dirty": False, "source_dirty": False, "source_validation_sha256": "456"}
        for name, value in [("ROOT", self.root), ("BUILDS", self.builds), ("source", lambda: dict(self.current))]:
            mock = patch.object(manifest, name, value)
            mock.start()
            self.addCleanup(mock.stop)

    def make_export(self, target, license=False):
        manifest.begin(target)
        artifact = self.builds / manifest.OUTPUTS[target]
        artifact.parent.mkdir(parents=True, exist_ok=True)
        artifact.write_bytes(b"native fixture")
        if target == "linux": artifact.chmod(0o755)
        if license:
            (self.builds / target / "GODOT-LICENSE.txt").write_text("license fixture")
        manifest.finish(target)

    def test_source_change_during_export_rejected(self):
        manifest.begin("linux")
        self.current["source_content_sha256"] = "changed"
        with self.assertRaisesRegex(SystemExit, "changed during export"):
            manifest.finish("linux")

    def test_missing_artifact_rejected(self):
        manifest.begin("android")
        with self.assertRaisesRegex(SystemExit, "Missing export"):
            manifest.finish("android")

    def test_modified_artifact_rejected(self):
        self.make_export("linux")
        (self.builds / manifest.OUTPUTS["linux"]).write_bytes(b"different")
        with self.assertRaisesRegex(SystemExit, "Changed linux artifact"):
            manifest.package()

    def test_uncommitted_game_rejected(self):
        self.current["source_game_dirty"] = True
        self.current["source_dirty"] = True
        with self.assertRaisesRegex(SystemExit, "Commit game source"):
            manifest.package()

    def test_changed_secondary_payload_rejected(self):
        manifest.begin("linux")
        (self.builds / manifest.OUTPUTS["linux"]).write_bytes(b"native fixture")
        license_file = self.builds / "linux/GODOT-LICENSE.txt"
        license_file.write_text("license fixture")
        manifest.finish("linux")
        license_file.write_text("modified license")
        with self.assertRaisesRegex(SystemExit, "Changed linux artifact"):
            manifest.package()

    def test_stale_source_rejected(self):
        self.make_export("linux")
        self.current["source_content_sha256"] = "changed"
        with self.assertRaisesRegex(SystemExit, "Stale or incomplete"):
            manifest.package()

    def test_completed_export_has_exact_digest(self):
        self.make_export("android")
        data = json.loads((self.builds / "android/source.json").read_text())
        self.assertTrue(data["export_completed"])
        self.assertEqual(data["artifact"], manifest.descriptor(self.builds / manifest.OUTPUTS["android"]))

    def test_all_targets_package_with_current_version_and_license(self):
        for target in manifest.OUTPUTS:
            self.make_export(target, license=True)
        with patch("builtins.print"):
            manifest.package(list(manifest.OUTPUTS))
        data = json.loads((self.builds / "manifest.json").read_text())
        self.assertEqual(data["version"], manifest.VERSION)
        self.assertEqual(len(data["exports"]), 5)
        self.assertEqual(len(data["artifacts"]), 9)
        import zipfile
        for target in manifest.OUTPUTS:
            suffix = "xcode-project" if target == "ios" else "debug"
            with zipfile.ZipFile(self.builds / f"sightbreak-{target}-{suffix}.zip") as bundle:
                self.assertIn(f"{target}/GODOT-LICENSE.txt", bundle.namelist())
                self.assertIn(f"{target}/source.json", bundle.namelist())

    def test_single_target_needs_no_other_sdks(self):
        self.make_export("windows", license=True)
        with patch("builtins.print"):
            manifest.package(["windows"])
        data = json.loads((self.builds / "manifest.json").read_text())
        self.assertEqual(data["targets"], ["windows"])
        self.assertEqual(len(data["exports"]), 1)

    def test_identical_runtime_different_commit_rejected(self):
        self.make_export("linux")
        self.current["source_commit"] = "other-commit"
        with self.assertRaisesRegex(SystemExit, "Stale or incomplete"):
            manifest.package(["linux"])

    def test_validation_source_change_rejected(self):
        self.make_export("linux")
        self.current["source_validation_sha256"] = "other-tooling"
        with self.assertRaisesRegex(SystemExit, "Stale or incomplete"):
            manifest.package(["linux"])

    def test_existing_export_and_reattestation_rejected(self):
        self.make_export("linux")
        with self.assertRaisesRegex(SystemExit, "Existing linux output"):
            manifest.begin("linux")
        with self.assertRaisesRegex(SystemExit, "already attested"):
            manifest.finish("linux")

    def test_executable_permission_change_rejected(self):
        import os
        if os.name == "nt": self.skipTest("POSIX mode check")
        self.make_export("linux")
        (self.builds / manifest.OUTPUTS["linux"]).chmod(0o600)
        with self.assertRaisesRegex(SystemExit, "Changed linux artifact"):
            manifest.package(["linux"])

    def test_developer_file_cannot_be_attested(self):
        manifest.begin("linux")
        (self.builds / manifest.OUTPUTS["linux"]).write_bytes(b"native fixture")
        (self.builds / "linux/credentials.json").write_text("fictional fixture")
        with self.assertRaisesRegex(SystemExit, "Developer/credential file"):
            manifest.finish("linux")

    def test_all_source_dirt_rejected(self):
        self.current["source_dirty"] = True
        with self.assertRaisesRegex(SystemExit, "Commit game source"):
            manifest.begin("linux")

    def test_apple_developer_files_rejected(self):
        for target, relative in (("macos", "SIGHTBREAK.app/Contents/Resources/credentials.json"), ("ios", "dev_probe.py")):
            with self.subTest(target=target):
                manifest.begin(target)
                artifact = self.builds / manifest.OUTPUTS[target]
                artifact.parent.mkdir(parents=True, exist_ok=True)
                artifact.write_bytes(b"native fixture")
                extra = self.builds / target / relative
                extra.parent.mkdir(parents=True, exist_ok=True)
                extra.write_text("fictional fixture")
                with self.assertRaisesRegex(SystemExit, "Developer/credential file"):
                    manifest.finish(target)

    def test_receipt_version_tampering_rejected(self):
        self.make_export("linux")
        path = self.builds / "linux/source.json"
        receipt = json.loads(path.read_text())
        receipt["version"] = "99.99.99"
        path.write_text(json.dumps(receipt))
        with self.assertRaisesRegex(SystemExit, "Stale or incomplete"):
            manifest.package(["linux"])

    def test_packaged_executable_mode_matches_receipt(self):
        self.make_export("linux")
        with patch("builtins.print"):
            manifest.package(["linux"])
        receipt = json.loads((self.builds / "linux/source.json").read_text())
        import zipfile
        with zipfile.ZipFile(self.builds / "sightbreak-linux-debug.zip") as archive:
            self.assertEqual((archive.getinfo("linux/sightbreak.x86_64").external_attr >> 16) & 0o777, receipt["artifact"]["archive_mode"])

    def test_export_versions_match_manifest(self):
        presets = configparser.ConfigParser(interpolation=None)
        presets.read(pathlib.Path(__file__).resolve().parents[1] / "game/export_presets.cfg")
        self.assertEqual(presets["preset.1.options"]["version/name"], f'"{manifest.VERSION}"')
        self.assertEqual(int(presets["preset.1.options"]["version/code"]), manifest.BUILD_NUMBER)
        self.assertEqual(presets["preset.2.options"]["application/short_version"], f'"{manifest.IOS_VERSION}"')
        self.assertEqual(presets["preset.2.options"]["application/version"], f'"{manifest.BUILD_NUMBER}"')

    def test_prebuilt_android_template_does_not_override_gradle_sdk(self):
        presets = configparser.ConfigParser(interpolation=None)
        presets.read(pathlib.Path(__file__).resolve().parents[1] / "game/export_presets.cfg")
        android = presets["preset.1.options"]
        if android["gradle_build/use_gradle_build"] == "false":
            self.assertEqual(android["gradle_build/min_sdk"], '\"\"')
            self.assertEqual(android["gradle_build/target_sdk"], '\"\"')


if __name__ == "__main__":
    unittest.main()
