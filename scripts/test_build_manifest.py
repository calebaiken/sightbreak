#!/usr/bin/env python3
"""Regression checks for export/source provenance; no engine or SDK required."""
import json
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


if __name__ == "__main__":
    unittest.main()
