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
        self.current = {"source_commit": "abc", "source_game_tree": "def", "source_content_sha256": "123", "source_validation_sha256": "456", "source_game_dirty": False, "source_dirty": False}
        for name, value in [("ROOT", self.root), ("BUILDS", self.builds), ("source", lambda: dict(self.current))]:
            mock = patch.object(manifest, name, value)
            mock.start()
            self.addCleanup(mock.stop)

    def make_export(self, target, license_file=False):
        manifest.begin(target)
        artifact = self.builds / manifest.OUTPUTS[target]
        artifact.parent.mkdir(parents=True, exist_ok=True)
        artifact.write_bytes(b"native fixture")
        if license_file:
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
        with self.assertRaisesRegex(SystemExit, "Commit game source"):
            manifest.package()

    def test_dirty_tooling_rejected_before_export(self):
        self.current["source_dirty"] = True
        with self.assertRaisesRegex(SystemExit, "validation tooling"):
            manifest.begin("linux")
        self.assertFalse((self.builds / "linux/source.json").exists())

    def test_dirty_source_during_export_rejected(self):
        manifest.begin("linux")
        self.current["source_dirty"] = True
        with self.assertRaisesRegex(SystemExit, "validation tooling"):
            manifest.finish("linux")

    def test_commit_or_tree_change_during_export_rejected(self):
        for key, target in zip(("source_commit", "source_game_tree", "source_validation_sha256"), manifest.OUTPUTS):
            with self.subTest(key=key):
                original = self.current[key]
                manifest.begin(target)
                self.current[key] = "changed-with-same-runtime-bytes"
                with self.assertRaisesRegex(SystemExit, "changed during export"):
                    manifest.finish(target)
                self.current[key] = original

    def test_identical_runtime_from_another_commit_rejected(self):
        self.make_export("linux")
        self.current["source_commit"] = "different-commit"
        with self.assertRaisesRegex(SystemExit, "Stale or incomplete"):
            manifest.package()

    def test_dirty_tooling_at_packaging_rejected(self):
        self.make_export("linux")
        self.current["source_dirty"] = True
        with self.assertRaisesRegex(SystemExit, "validation tooling"):
            manifest.package()

    def test_tainted_export_receipt_rejected(self):
        self.make_export("linux")
        path = self.builds / "linux/source.json"
        record = json.loads(path.read_text())
        record["source_dirty"] = True
        path.write_text(json.dumps(record))
        with self.assertRaisesRegex(SystemExit, "Stale or incomplete"):
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
            self.make_export(target, license_file=True)
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
        project = pathlib.Path(__file__).resolve().parents[1] / "game/project.godot"
        self.assertIn(f'config/version="{manifest.VERSION}"', project.read_text().splitlines())

    def test_existing_artifact_cannot_be_re_attested(self):
        self.make_export("linux")
        path = self.builds / "linux/source.json"
        original = path.read_bytes()
        self.current["source_commit"] = "different-commit"
        with self.assertRaisesRegex(SystemExit, "fresh empty"):
            manifest.begin("linux")
        self.assertEqual(path.read_bytes(), original)

    def test_completed_receipt_cannot_be_finished_again(self):
        self.make_export("linux")
        with self.assertRaisesRegex(SystemExit, "already completed"):
            manifest.finish("linux")

    def test_wrapper_execute_permission_survives_packaging(self):
        import zipfile
        for target in manifest.OUTPUTS:
            manifest.begin(target)
            artifact = self.builds / manifest.OUTPUTS[target]
            artifact.parent.mkdir(parents=True, exist_ok=True)
            artifact.write_bytes(b"native fixture")
            if target == "linux":
                wrapper = self.builds / "linux/sightbreak.sh"
                wrapper.write_text("#!/bin/sh\n")
                wrapper.chmod(0o755)
            # Windows chmod does not model POSIX execute bits; exercise that
            # metadata explicitly there, while POSIX uses the actual file mode.
            original = pathlib.Path.stat
            def executable_stat(path, *args, **kwargs):
                result = original(path, *args, **kwargs)
                if path.name == "sightbreak.sh":
                    import os
                    values = list(result)
                    values[0] = 0o100755
                    return os.stat_result(values)
                return result
            with patch.object(pathlib.Path, "stat", executable_stat):
                manifest.finish(target)
        with patch.object(pathlib.Path, "stat", executable_stat), patch("builtins.print"):
            manifest.package()
        with zipfile.ZipFile(self.builds / "sightbreak-linux-debug.zip") as bundle:
            self.assertEqual((bundle.getinfo("linux/sightbreak.sh").external_attr >> 16) & 0o777, 0o755)

    def test_payload_mutation_between_check_and_archive_rejected(self):
        for target in manifest.OUTPUTS:
            self.make_export(target, license_file=True)
        original = pathlib.Path.read_bytes
        def mutated(path):
            if path.name == "GODOT-LICENSE.txt":
                return b"concurrent changed payload"
            return original(path)
        with patch.object(pathlib.Path, "read_bytes", mutated):
            with self.assertRaisesRegex(SystemExit, "Changed linux payload"):
                manifest.package()
        self.assertFalse((self.builds / "manifest.json").exists())

    def test_earlier_packaging_success_is_not_overwritten(self):
        self.builds.mkdir()
        path = self.builds / "manifest.json"
        path.write_bytes(b'{"earlier": true}\n')
        with self.assertRaisesRegex(SystemExit, "fresh packaging attempt"):
            manifest.package()
        self.assertEqual(path.read_bytes(), b'{"earlier": true}\n')

    def test_prebuilt_android_template_does_not_override_gradle_sdk(self):
        presets = configparser.ConfigParser(interpolation=None)
        presets.read(pathlib.Path(__file__).resolve().parents[1] / "game/export_presets.cfg")
        android = presets["preset.1.options"]
        if android["gradle_build/use_gradle_build"] == "false":
            self.assertEqual(android["gradle_build/min_sdk"], '\"\"')
            self.assertEqual(android["gradle_build/target_sdk"], '\"\"')


if __name__ == "__main__":
    unittest.main()
