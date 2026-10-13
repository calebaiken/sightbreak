#!/usr/bin/env python3
"""Regression checks for export/source provenance; no engine or SDK required."""
import json
import configparser
import pathlib
import tempfile
import unittest
from unittest.mock import patch

import build_manifest as manifest


class BuildManifestTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = pathlib.Path(self.temporary.name)
        self.builds = self.root / "builds"
        self.current = {"source_commit": "abc", "source_game_tree": "def", "source_content_sha256": "123", "source_game_dirty": False}
        for name, value in [("ROOT", self.root), ("BUILDS", self.builds), ("source", lambda: dict(self.current))]:
            mock = patch.object(manifest, name, value)
            mock.start()
            self.addCleanup(mock.stop)

    def make_export(self, target):
        manifest.begin(target)
        artifact = self.builds / manifest.OUTPUTS[target]
        artifact.parent.mkdir(parents=True, exist_ok=True)
        artifact.write_bytes(b"native fixture")
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
            self.make_export(target)
            (self.builds / target / "GODOT-LICENSE.txt").write_text("license fixture")
            manifest.finish(target)
        with patch("builtins.print"):
            manifest.package()
        data = json.loads((self.builds / "manifest.json").read_text())
        self.assertEqual(data["version"], manifest.VERSION)
        self.assertEqual(len(data["exports"]), 3)
        self.assertEqual(len(data["artifacts"]), 5)
        import zipfile
        for target in manifest.OUTPUTS:
            suffix = "xcode-project" if target == "ios" else "debug"
            with zipfile.ZipFile(self.builds / f"sightbreak-{target}-{suffix}.zip") as bundle:
                self.assertIn(f"{target}/GODOT-LICENSE.txt", bundle.namelist())
                self.assertIn(f"{target}/source.json", bundle.namelist())

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
