#!/usr/bin/env python3
"""Pure R4 falsifiers. Synthetic arrays/marker files are never native evidence."""
import json
from pathlib import Path
import re
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

import analyze_touch_contrast_r4 as method
from prepare_touch_contrast_r4 import BASELINE, instrument, split_args
from test_touch_contrast_method import PixelMethod  # Unchanged 11 full-glyph controls.

REPO = Path(__file__).resolve().parents[1]


def component(background=255, foreground=0, mask=None):
    if mask is None:
        mask = np.zeros((40, 40), dtype=bool)
        mask[6:34, 6:34] = True
    u = np.broadcast_to(np.asarray(background, dtype=float), (*mask.shape, 3)).copy()
    p, b, w, f = u.copy(), u.copy(), u.copy(), np.zeros_like(u)
    p[mask], b[mask], w[mask], f[mask] = foreground, 0, 255, 255
    return [x.astype(np.uint8) for x in (p, u, b, w, f)]


def boundary(values, alpha=1):
    p, u, b, w, f = values
    return method.audit_boundary(p, u, b, w, alpha, f)


class FinalBoundary(unittest.TestCase):
    def test_complete_contours_on_bright_dark_and_busy(self):
        for background in (0, 255, np.broadcast_to((np.indices((40, 40)).sum(axis=0) % 2 * 255)[..., None], (40, 40, 3))):
            foreground = 255 - np.asarray(background)
            values = component(background=background)
            values[0][values[-1].max(axis=-1) > 0] = np.broadcast_to(foreground, (40, 40, 3))[values[-1].max(axis=-1) > 0]
            self.assertTrue(boundary(values)["pass"])

    def test_one_low_contrast_arc_section_fails(self):
        values = component()
        values[0][12:28, 6:11] = 255
        row = boundary(values)
        self.assertTrue(row["resolved"])
        self.assertFalse(row["pass"])
        self.assertTrue(row["failing_contours"])

    def test_distant_contrast_cannot_rescue_edge(self):
        values = component(foreground=255)
        values[0][15:25, 15:25] = 0
        row = boundary(values)
        self.assertFalse(row["pass"])
        self.assertEqual(row["contrast_lower_bound"], 1)

    def test_disconnected_foreign_object_cannot_supply_witness(self):
        mask = np.zeros((40, 40), dtype=bool)
        mask[10:16, 10:13] = True
        mask[10:16, 14:17] = True
        values = component(mask=mask, foreground=255)
        values[0][10:16, 14:17] = 0
        row = boundary(values)
        self.assertFalse(row["pass"])
        failed = {tuple(x["contour_yx"]) for x in row["failing_contours"]}
        self.assertIn((12, 12), failed)  # Bright neighbor is only 2px away across a gap.

    def test_single_code_aa_contour_keeps_expected_support(self):
        values = component()
        for x, val in zip(values, (254, 255, 254, 255, 1)):
            x[5, 6:34] = val
        row = boundary(values)
        self.assertTrue(row["pass"], row)
        self.assertEqual(row["support_pixels"], 28 * 29)

    def test_foreign_front_paint_is_not_aa(self):
        values = component()
        # An unchanged later 90%-opaque black layer also appears in U.
        for image in values[:4]: image[12:20, 6:12] = np.rint(image[12:20, 6:12] * .1)
        row = boundary(values)
        self.assertFalse(row["resolved"])
        self.assertGreater(row["missing_footprint_pixels"], 0)

    def test_supported_underlay_and_outside_changes_reject(self):
        for kind in ("underlay", "outside"):
            values = component()
            if kind == "underlay":
                # At fully opaque D=255, P/B/W cannot identify U. Source-bound
                # suppression/provenance must establish it. This pixel control
                # checks a genuinely translucent contribution, as in R3.
                values[0][6:34, 6:34] = 36
                values[2][6:34, 6:34] = 36
                values[1][10, 6] = 20
            else: values[2][0, 0] = 20
            self.assertFalse(boundary(values)["resolved"])

    def test_full_glyph_loss_still_fails_when_component_passes(self):
        from test_touch_contrast_method import synthetic, footprint
        values = component()
        self.assertTrue(boundary(values)["pass"])
        p, u, b, w = synthetic()
        for image in (p, b, w): image[3:9, 2:5] = u[3:9, 2:5]
        self.assertFalse(method.audit_pixels(p, u, b, w, 1, footprint=footprint())["resolved"])

    def test_contribution_quantization_is_conservative(self):
        values = component()
        values[2][6:34, 6:34] = 0
        values[3][6:34, 6:34] = 205
        # Use matching actual-opacity footprint metadata; there is still no
        # qualified witness because D-2 is below 0.8*255.
        values[1][:] = 0
        values[0][6:34, 6:34] = 205
        self.assertFalse(boundary(values, alpha=.8)["resolved"])


class Instrumentation(unittest.TestCase):
    def test_hidden_prior_stroke_accounting_keeps_unattributed_loss(self):
        image = np.zeros((12, 12, 3), np.uint8)
        footprint, white = image.copy(), image.copy()
        footprint[2:10, 5] = 255
        white[2:10, 5] = 242
        white[3:5, 5] = 0
        badge = image.copy(); badge[3, 5] = 255
        with patch.object(method, "read", lambda path: image if "black" in path.name else white):
            row = method.intermediate_overlap(Path("PURE"), "border", .95, footprint, {"badge_paint": badge})
        self.assertEqual(row["hidden_or_replaced_pixels"], 2)
        self.assertEqual(row["isolated_layer_intersections"]["badge_paint"], 1)
        self.assertEqual(row["without_recorded_layer_intersection"], 1)

    def test_every_original_draw_call_classified_with_same_noncolor_arguments(self):
        for source in (subprocess.check_output(["git", "-C", str(REPO), "show", BASELINE + ":game/scripts/ui/touch_controls.gd"]).decode(),
                       (REPO / "game/scripts/ui/touch_controls.gd").read_text()):
            wrapped, receipt = instrument(source)
            actual = []
            for number, line in enumerate(source.splitlines(), 1):
                match = re.search(r"\b(draw_circle|draw_arc|draw_line|draw_rect|draw_string_outline|draw_string)\((.*)\)$", line)
                if not match: continue
                kind, text = match.groups()
                args = split_args(text)
                index = {"draw_circle": 2, "draw_arc": 5, "draw_line": 2, "draw_rect": 1, "draw_string": 6, "draw_string_outline": 7}[kind]
                actual.append({"line": number, "call": kind, "color": args[index], "geometry": args[:index] + args[index + 1:]})
            self.assertEqual(actual, [{k: v for k, v in x.items() if k != "group"} for x in receipt])
            self.assertIn('probe_action = "move"', wrapped)
            self.assertIn('var selected := group == probe_group or component == probe_group', wrapped)
            self.assertEqual(wrapped.count('probe_icon_underlay = true'), int('icon_surround' in source))
            self.assertIn('draw_string_outline', wrapped)


class Comparison(unittest.TestCase):
    def valid(self):
        return {"baseline": {"provenance_valid": True, "pass": False}, "candidate": {"provenance_valid": True, "pass": True},
            "geometry_equal": True, "font_metrics_equal": True, "analysis_matches_freeze": True}

    def test_valid_failed_baseline_remains_comparable(self):
        self.assertTrue(method.comparison_passes(self.valid()))

    def test_invalid_baseline_candidate_geometry_fonts_or_freeze_reject(self):
        for field in ("baseline", "candidate", "geometry_equal", "font_metrics_equal", "analysis_matches_freeze"):
            result = self.valid()
            if field in ("baseline", "candidate"): result[field]["provenance_valid"] = False
            else: result[field] = False
            self.assertFalse(method.comparison_passes(result), field)


if __name__ == "__main__":
    unittest.main(verbosity=2)
