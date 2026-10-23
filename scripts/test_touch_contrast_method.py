#!/usr/bin/env python3
"""Pure adversarial checks for the pixel method and product scope."""
import json
from pathlib import Path
import re
import subprocess
import unittest

import numpy as np

from analyze_touch_contrast import audit_pixels, comparison_passes, matrix, scene_identity
from prepare_touch_contrast import BASELINE, TOUCH, instrument, split_args

REPO = Path(__file__).resolve().parents[1]


def synthetic(foreground=(1, 1, 1), alpha=1.0, backdrop=.05):
    u = np.full((12, 20, 3), backdrop)
    # Disconnected thin glyphs and every representable low-AA coverage level.
    cov = np.zeros((12, 20, 1))
    cov[1, 1:19, 0] = np.arange(1, 19) / 255
    cov[3:9, 2:5, 0] = .9
    cov[3:9, 12:15, 0] = 1.0
    a = cov * alpha
    convert = lambda x: np.round(np.clip(x, 0, 1) * 255).astype(np.uint8)
    return (convert(u * (1 - a) + a * foreground), convert(u),
            convert(u * (1 - a)), convert(u * (1 - a) + a))


def footprint():
    _, _, black, white = synthetic()
    return white.astype(int) - black.astype(int)


class PixelMethod(unittest.TestCase):
    def test_full_disconnected_support(self):
        p, u, b, w = synthetic()
        result = audit_pixels(p, u, b, w, 1.0, footprint=footprint())
        self.assertTrue(result["resolved"], result)
        self.assertEqual(result["support_pixels"], 54)
        self.assertGreater(result["low_coverage_pixels"], 0)
        self.assertGreater(result["contrast_lower_bound"], 4.5)

    def test_one_bad_low_coverage_background_blocks(self):
        p, u, b, w = synthetic(backdrop=.05)
        p2, u2, b2, w2 = synthetic(backdrop=.98)
        for dest, replacement in zip((p, u, b, w), (p2, u2, b2, w2)):
            dest[1, 12] = replacement[1, 12]
        result = audit_pixels(p, u, b, w, 1.0, footprint=footprint())
        self.assertLess(result["contrast_lower_bound"], 1.1)

    def test_changed_backdrop_is_rejected(self):
        p, u, b, w = synthetic()
        p[0, 0] = 180
        result = audit_pixels(p, u, b, w, 1.0, footprint=footprint())
        self.assertFalse(result["resolved"])
        self.assertEqual(result["outside_changed"], 1)

    def test_translucent_foreground_is_not_treated_opaque(self):
        result = audit_pixels(*synthetic(alpha=.24, backdrop=.8), .24, footprint=footprint())
        self.assertLess(result["contrast_lower_bound"], 3.0)

    def test_nonconstant_foreground_is_rejected(self):
        p, u, b, w = synthetic()
        p[4:6, 3] = [255, 0, 0]
        self.assertFalse(audit_pixels(p, u, b, w, 1.0, footprint=footprint())["resolved"])


    def test_supported_underlay_substitution_is_rejected(self):
        p, u, b, w = synthetic(backdrop=.8)
        u[footprint().max(axis=-1) >= 1] = 13
        result = audit_pixels(p, u, b, w, 1.0, footprint=footprint())
        self.assertFalse(result["resolved"])
        self.assertGreater(result["underlay_compositing_errors"], 0)

    def test_diagnostic_changes_outside_support_are_rejected(self):
        p, u, b, w = synthetic()
        b[0, 0] = w[0, 0] = 180
        self.assertFalse(audit_pixels(p, u, b, w, 1.0, footprint=footprint())["resolved"])

    def test_post_glyph_occlusion_is_rejected(self):
        values = [np.round(x.astype(float) * .1).astype(np.uint8) for x in synthetic()]
        result = audit_pixels(*values, 1.0, footprint=footprint())
        self.assertFalse(result["resolved"])
        self.assertGreater(result["missing_footprint_pixels"], 0)

    def test_complete_disconnected_glyph_loss_is_rejected(self):
        p, u, b, w = synthetic()
        for image in [p, b, w]: image[3:9, 2:5] = u[3:9, 2:5]
        result = audit_pixels(p, u, b, w, 1.0, footprint=footprint())
        self.assertFalse(result["resolved"])
        self.assertEqual(result["missing_footprint_pixels"], 18)

    def test_footprint_is_required(self):
        self.assertFalse(audit_pixels(*synthetic(), 1.0)["resolved"])

    def test_exact_scene_identity(self):
        self.assertEqual(len(matrix()), 32)
        invalid = {"id": "invented-00-idle"}
        self.assertTrue(scene_identity(invalid, matrix()["mobile-min-white-idle"]))


class SourceScope(unittest.TestCase):
    def test_invalid_baseline_provenance_blocks_comparison(self):
        result = {"baseline": {"pass": False, "errors": ["incorrect baseline source"]},
                  "candidate": {"pass": True, "errors": []}, "geometry_equal": True,
                  "analysis_matches_freeze": True}
        self.assertFalse(comparison_passes(result))

    def test_valid_low_contrast_baseline_remains_comparable(self):
        result = {"baseline": {"pass": False, "errors": []},
                  "candidate": {"pass": True, "errors": []}, "geometry_equal": True,
                  "analysis_matches_freeze": True}
        self.assertTrue(comparison_passes(result))

    def test_only_draw_body_changes(self):
        before = subprocess.check_output(["git", "-C", str(REPO), "show", BASELINE + ":" + TOUCH]).decode()
        after = (REPO / TOUCH).read_text()
        outside = lambda s: re.sub(r"func _draw\(\) -> void:\n.*?(?=\n# Shared geometric glyphs)", "DRAW_BODY\n", s, flags=re.S)
        self.assertEqual(outside(before), outside(after))
        self.assertNotEqual(before, after)

    def test_shared_wrapper_classifies_without_geometry_edits(self):
        source = (REPO / TOUCH).read_text()
        wrapped, receipt = instrument(source)
        self.assertGreater(len(receipt), 20)
        self.assertIn('return Color(0, 0, 0, original.a)', wrapped)
        self.assertIn('return Color(1, 1, 1, original.a)', wrapped)
        for entry in receipt:
            self.assertTrue(entry["geometry"])
        self.assertEqual(split_args('point, Color(1, 2, 3), "A,B", 1.25'),
                         ['point', 'Color(1, 2, 3)', '"A,B"', '1.25'])

    def test_original_draw_geometry_is_retained(self):
        before = subprocess.check_output(["git", "-C", str(REPO), "show", BASELINE + ":" + TOUCH]).decode()
        after = (REPO / TOUCH).read_text()
        def geometry(source):
            result = []
            for line in source.splitlines():
                match = re.search(r"\b(draw_circle|draw_arc|draw_line|draw_rect|draw_string)\((.*)\)$", line)
                if not match: continue
                kind, text = match.groups()
                args = split_args(text)
                color = {"draw_circle": 2, "draw_arc": 5, "draw_line": 2, "draw_rect": 1, "draw_string": 6}[kind]
                args.pop(color)
                args = [x.replace("knob", "origin + Vector2(movement.x, -movement.y) * 40 * hud_scale") for x in args]
                result.append((kind, args))
            return result
        candidate = iter(geometry(after))
        for original in geometry(before):
            self.assertTrue(any(original == item for item in candidate), original)


if __name__ == "__main__":
    unittest.main(verbosity=2)
