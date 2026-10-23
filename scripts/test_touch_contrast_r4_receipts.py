#!/usr/bin/env python3
"""R4 metadata/affordance controls. Marker bytes are never rendered evidence."""
from contextlib import ExitStack
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

import analyze_touch_contrast_r4 as method


class ReceiptControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix="touch-r4-pure-receipts-")
        cls.root = Path(cls.tmp.name)
        cls.controls, cls.backgrounds = cls.root / "controls", cls.root / "backgrounds"
        cls.controls.mkdir(); cls.backgrounds.mkdir()
        cls.expected = {"manifest_sha256": "PURE FROZEN MANIFEST", "source_full": "PURE FROZEN SOURCE", "paint_variant": "r3"}
        identity = {"engine": {"major": 4, "minor": 7, "patch": 2}, "renderer": "PURE METADATA STUB", "source_verified_before_after": True}
        bg = {**identity, "mode": "backgrounds", "source": cls.expected["source_full"], "source_manifest_sha256": cls.expected["manifest_sha256"], "images": {}}
        for layout in method.LAYOUTS:
            for background in method.BACKGROUNDS:
                path = cls.backgrounds / (layout + "-" + background + ".png")
                path.write_bytes(b"PURE BACKGROUND MARKER")
                bg["images"][str(path)] = method.digest(path)
        cls.bg_path = cls.backgrounds / "capture.json"
        cls.bg_path.write_text(json.dumps(bg))
        capture = {**identity, "source": cls.expected["source_full"], "source_manifest_sha256": cls.expected["manifest_sha256"],
            "background_manifest_sha256": method.digest(cls.bg_path), "mode": "controls", "images": {}, "records": []}
        for name, (layout, background, held) in method.matrix().items():
            size, scale, inset = method.LAYOUTS[layout]
            folder = cls.controls / name; folder.mkdir()
            groups = [g for g in method.GROUPS if g != "held_border" or held] + ["component_" + a for a in method.ACTIONS]
            files = {"normal.png", "original.png"} | {g + "-" + p + ".png" for g in groups for p in ("underlay", "black", "white", "footprint")} | {g + "-footprint.png" for g in method.LAYER_FOOTPRINTS}
            images = {}
            for image in files:
                path = folder / image; path.write_bytes(b"PURE IMAGE MARKER")
                images[image] = method.digest(path); capture["images"][str(path)] = images[image]
            geometry = {a: {"point": [100 + index * 50, 300], "radius": (65 if a == "move" else 40 if a == "fire" else 28) * scale}
                for index, a in enumerate((*method.ACTIONS, "move"))}
            paint = {}
            for a in method.ACTIONS:
                point, r = geometry[a]["point"], geometry[a]["radius"]
                paint[a] = {"point": point, "nominal_radius": r, "hit_radius": r * 1.25, "body_radius": r, "rim_radius": r, "rim_shadow": 5.25,
                    "font_size": 12, "label": method.LABELS[a], "label_width": 40, "font_ascent": 12, "font_descent": 3,
                    "icon_center": [point[0], point[1] - 8], "label_origin": [point[0] - 20, point[1] + 17],
                    "badge_center": [point[0] + r * .72, point[1] - r * .72], "badge_radius": 9, "badge_shadow": 0, "badge_rim": 0}
            bg_image = cls.backgrounds / (layout + "-" + background + ".png")
            info = {"id": name, "layout": layout, "size": size, "scale": scale, "inset": inset, "held": held,
                "counts": {"grenade": 0, "smoke": 1}, "movement": [.65, .45] if held else [0, 0], "actions": ["fire", "reload", "interact"] if held else [],
                "geometry": geometry, "paint_geometry": paint, "alphas": {g: 1. for g in groups}, "images": images,
                "background": str(bg_image), "background_sha256": method.digest(bg_image)}
            (folder / "scene.json").write_text(json.dumps(info)); capture["records"].append(info)
        cls.capture_path = cls.controls / "capture.json"
        cls.capture_path.write_text(json.dumps(capture))
        cls.backups = {p: p.read_bytes() for p in cls.root.rglob("*") if p.is_file()}
        cls.arrays = {w: np.zeros((720, w, 3), np.uint8) for w in (960, 1280)}

    @classmethod
    def tearDownClass(cls): cls.tmp.cleanup()

    def tearDown(self):
        for path, original in self.backups.items(): path.write_bytes(original)

    def run_receipts(self, pixel=None, edge=None, affordance=None):
        # Decode/contrast/affordance are explicitly stubbed only to isolate
        # source/matrix/PNG/renderer receipt gates. No marker is a native PNG.
        with ExitStack() as stack:
            stack.enter_context(patch.object(method, "read", lambda p: self.arrays[960 if p.parent.name.startswith("mobile") else 1280]))
            stack.enter_context(patch.object(method, "audit_pixels", pixel or (lambda *a, **k: {"resolved": True, "contrast_lower_bound": 9.})))
            stack.enter_context(patch.object(method, "audit_boundary", edge or (lambda *a, **k: {"resolved": True, "pass": True})))
            stack.enter_context(patch.object(method, "audit_affordance", affordance or (lambda *a, **k: {"pass": True})))
            stack.enter_context(patch.object(method, "intermediate_overlap", lambda *a, **k: {"scope": "PURE METADATA STUB"}))
            return method.audit_source(self.controls, self.expected, self.backgrounds, self.expected)

    def mutate_json(self, path, **changes):
        data = json.loads(path.read_text()); data.update(changes); path.write_text(json.dumps(data))

    def test_positive_complete_metadata_fixture(self):
        result = self.run_receipts()
        self.assertTrue(result["pass"], result["errors"])
        self.assertEqual((len(result["rows"]), result["gated_rows"], result["retained_intermediate_rows"]), (656, 608, 48))

    def test_unrelated_background_source_and_manifest_reject_even_rebound_hash(self):
        self.mutate_json(self.bg_path, source="UNRELATED SOURCE", source_manifest_sha256="UNRELATED MANIFEST")
        self.mutate_json(self.capture_path, background_manifest_sha256=method.digest(self.bg_path))
        self.assertFalse(self.run_receipts()["provenance_valid"])

    def test_different_background_renderer_reject_even_rebound_hash(self):
        self.mutate_json(self.bg_path, renderer="OTHER RENDERER")
        self.mutate_json(self.capture_path, background_manifest_sha256=method.digest(self.bg_path))
        self.assertFalse(self.run_receipts()["provenance_valid"])

    def test_changed_source_or_native_fence_or_engine_reject(self):
        for changes in ({"source": "UNRELATED"}, {"source_manifest_sha256": "OTHER MANIFEST"}, {"source_verified_before_after": False},
                        {"engine": {"major": 4, "minor": 7, "patch": 1}}, {"mode": "backgrounds"}):
            self.capture_path.write_bytes(self.backups[self.capture_path]); self.mutate_json(self.capture_path, **changes)
            self.assertFalse(self.run_receipts()["provenance_valid"], changes)

    def test_missing_scene_or_incorrect_matrix_reject(self):
        path = self.controls / "mobile-min-white-idle/scene.json"
        path.unlink(); self.assertFalse(self.run_receipts()["provenance_valid"])
        path.write_bytes(self.backups[path]); self.mutate_json(path, scale=1.)
        self.assertFalse(self.run_receipts()["provenance_valid"])

    def test_changed_footprint_or_background_bytes_reject(self):
        for path in (self.controls / "mobile-min-white-idle/component_fire-footprint.png", self.backgrounds / "mobile-min-white.png"):
            path.write_bytes(b"CHANGED PURE MARKER")
            self.assertFalse(self.run_receipts()["provenance_valid"])
            path.write_bytes(self.backups[path])

    def test_missing_capture_image_identity_reject(self):
        value = json.loads(self.capture_path.read_text()); value["images"].pop(next(iter(value["images"])))
        self.capture_path.write_text(json.dumps(value)); self.assertFalse(self.run_receipts()["provenance_valid"])

    def test_paint_layout_mutation_rejects_even_with_matching_scene_receipt(self):
        path = self.controls / "mobile-min-white-idle/scene.json"
        scene = json.loads(path.read_text()); scene["paint_geometry"]["reload"]["label_origin"][1] -= 1
        path.write_text(json.dumps(scene))
        capture = json.loads(self.capture_path.read_text())
        capture["records"] = [scene if v["id"] == scene["id"] else v for v in capture["records"]]
        self.capture_path.write_text(json.dumps(capture))
        self.assertFalse(self.run_receipts()["provenance_valid"])

    def test_unresolved_inactive_glyph_rejects(self):
        calls = [0]
        def pixel(*a, **k):
            calls[0] += 1
            return {"resolved": calls[0] != 2, "contrast_lower_bound": 9.}
        self.assertFalse(self.run_receipts(pixel=pixel)["pass"])

    def test_unresolved_boundary_or_affordance_rejects(self):
        self.assertFalse(self.run_receipts(edge=lambda *a, **k: {"resolved": False, "pass": False})["pass"])
        self.assertFalse(self.run_receipts(affordance=lambda *a, **k: {"pass": False})["pass"])

    def test_legacy_stroke_failure_stays_reported_without_relabeling(self):
        calls = [0]
        def pixel(*a, **k):
            calls[0] += 1
            return {"resolved": calls[0] != 7, "contrast_lower_bound": 9.}
        value = self.run_receipts(pixel=pixel)
        self.assertTrue(value["pass"])
        failed = [x for x in value["rows"] if not x["resolved"]]
        self.assertEqual(len(failed), 1)
        self.assertEqual((failed[0]["group"], failed[0]["gate"]), ("border", "retained_intermediate_stroke_diagnostic"))


class AffordanceControls(unittest.TestCase):
    def fixture(self):
        info = {"counts": {"grenade": 0, "smoke": 1}, "paint_geometry": {}}
        footprints = {g: np.zeros((120, 800, 3), np.uint8) for g in ("active_label", "inactive_label", "active_icon", "inactive_icon", "empty_count", "ready_count")}
        components = {}
        yy, xx = np.indices((120, 800))
        for index, action in enumerate(method.ACTIONS):
            x, y = index * 65 + 50, 60
            badge = [x + 19.6 * .72, y - 19.6 * .72]
            data = {"point": [x, y], "hit_radius": 24.5, "label_origin": [x - 30, y + 6], "label_width": 60,
                "font_ascent": 12, "font_descent": 3, "icon_center": [x, y - 13]}
            info["paint_geometry"][action] = data
            support = np.hypot(xx + .5 - x, yy + .5 - y) < 27
            if action in info["counts"]: support |= np.hypot(xx + .5 - badge[0], yy + .5 - badge[1]) < 12
            components[action] = np.repeat((support * 255).astype(np.uint8)[..., None], 3, axis=-1)
            prefix = "inactive_" if action == "grenade" else "active_"
            footprints[prefix + "label"][y + 2, x] = 255
            footprints[prefix + "icon"][y - 13, x] = 255
            if action in info["counts"]: footprints["empty_count" if action == "grenade" else "ready_count"][int(badge[1]), int(badge[0])] = 255
        return info, footprints, components

    def test_all_native_glyphs_assigned_once_and_decorative_spill_reported(self):
        value = method.audit_affordance(*self.fixture())
        self.assertTrue(value["pass"], value["errors"])
        self.assertTrue(any(x["outside_hit_pixels"] for x in value["rows"] if x["kind"] == "complete_visual_component"))

    def test_missing_glyph_foreground_rejects(self):
        info, footprints, components = self.fixture()
        footprints["active_label"][62, 50] = 0
        self.assertFalse(method.audit_affordance(info, footprints, components)["pass"])

    def test_foreground_hit_spill_rejects(self):
        info, footprints, components = self.fixture()
        footprints["active_label"][60, 76] = 255
        value = method.audit_affordance(info, footprints, components)
        self.assertFalse(value["pass"])
        self.assertTrue(any("foreground outside" in e for e in value["errors"]))

    def test_unassigned_foreground_pixel_rejects(self):
        info, footprints, components = self.fixture()
        footprints["active_icon"][0, 0] = 1
        self.assertFalse(method.audit_affordance(info, footprints, components)["pass"])


if __name__ == "__main__": unittest.main(verbosity=2)
