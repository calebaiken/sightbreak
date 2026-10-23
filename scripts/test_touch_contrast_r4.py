#!/usr/bin/env python3
"""Pure source, physical-target and retained-native-mask checks for R4."""
import json
import math
from pathlib import Path
import re
import subprocess
import unittest

import numpy as np

REPO = Path(__file__).resolve().parents[1]
SOURCE = REPO / "game/scripts/ui/touch_controls.gd"
BASELINE = "a52022169241df9ff662039547a375e1c46ac1c5"


def paint(action, radius):
    compact = action != "fire" and radius < 32
    body = min(radius * 1.25, max(radius, 26)) if compact else radius
    return {"radius": body, "rim_radius": body + 1 if compact else body,
            "rim_shadow": 3.5 if compact else 5.25,
            "icon_y": -13 if compact else -8, "label_y": 6 if compact else 17}


class R4Source(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old = subprocess.check_output(["git", "-C", str(REPO), "show", BASELINE + ":game/scripts/ui/touch_controls.gd"]).decode()
        cls.new = SOURCE.read_text()

    def test_all_non_drawing_source_is_identical(self):
        self.assertEqual(self.old[:self.old.index("func _draw()")], self.new[:self.new.index("func _draw()")])

    def test_foreground_glyph_paths_and_widths_remain_identical(self):
        old = self.old[self.old.index("func _draw_action_icon("):]
        new = self.new[self.new.index("func _draw_action_icon("):]
        new = new.replace(", stroke_extra: float = 0.0", "")
        new = new.replace(" + stroke_extra * 0.5", "").replace(" + stroke_extra", "")
        self.assertEqual(old, new)
        self.assertIn("icon_surround, 2.0)", self.new)

    def test_font_words_and_no_shrinking(self):
        self.assertIn('var label_text: String = LABELS[key]', self.new)
        self.assertIn('label_text, HORIZONTAL_ALIGNMENT_LEFT, -1, 12, Color', self.new)
        self.assertIn('label_text, HORIZONTAL_ALIGNMENT_LEFT, -1, 12, 3, Color', self.new)
        self.assertNotRegex(self.new, r'font_size\s*[:=]')

    def test_badge_fill_and_surround_precede_foregrounds(self):
        fill = self.new.index('draw_circle(badge, 9,')
        halo = self.new.index('_draw_action_icon(key, point + Vector2(0, icon_y), icon_surround, 2.0)')
        outline = self.new.index('draw_string_outline(font, point + Vector2(-width / 2, label_y)')
        icon = self.new.index('_draw_action_icon(key, point + Vector2(0, icon_y), ink)')
        label = self.new.index('draw_string(font, point + Vector2(-width / 2, label_y)')
        digits = self.new.index('draw_string(font, badge + Vector2(-digit_width / 2, 4.5)')
        self.assertLess(fill, halo)
        self.assertLess(halo, outline)
        self.assertLess(outline, icon)
        self.assertLess(icon, label)
        self.assertLess(label, digits)

    def test_body_and_shadow_fit_existing_hit_and_safe_inset(self):
        for scale in np.linspace(.7, 1.5, 1001):
            for action, base in (("reload", 28), ("fire", 40)):
                radius = float(scale) * base
                actual = paint(action, radius)
                self.assertLessEqual(actual["radius"], radius * 1.25 + 1e-10)
                self.assertLessEqual(actual["rim_radius"] + actual["rim_shadow"] / 2, radius + 8 + 1e-10)
                self.assertLessEqual(radius * .72 + 11.625, radius + 8 + 1e-10)

    def test_minimum_extra_plate_fill_and_maximum_unchanged(self):
        r = 28 * .7
        extra = 10 * math.pi * (paint("reload", r)["radius"] ** 2 - r ** 2)
        self.assertLess(extra, 960 * 720 * .01)
        self.assertEqual(paint("reload", 42)["radius"], 42)
        self.assertEqual(paint("reload", 42)["icon_y"], -8)
        self.assertEqual(paint("reload", 42)["label_y"], 17)

    def test_retained_native_glyph_translation_bounds(self):
        data = json.loads((REPO / "scripts/fixtures/touch_contrast_r4/r3_glyph_support.json").read_text())
        self.assertEqual(len(data["controls"]), 44)
        for entry in data["controls"]:
            point = np.array(entry["point"])
            r = entry["radius"]
            geometry = paint(entry["action"], r)
            glyphs = {}
            for kind, old_y in (("label", 17), ("icon", -8)):
                values = np.array(entry["support"][kind], dtype=float)
                values[:, 1] += geometry[kind + "_y"] - old_y
                distances = np.linalg.norm(values - point, axis=1)
                self.assertTrue(np.all(distances <= 1.25 * r), (entry["layout"], entry["action"], kind, distances.max()))
                glyphs[kind] = {tuple(x) for x in values}
                if kind == "label":
                    # Include the held rim's wider inner edge and 48-segment
                    # chord inset, rather than checking only the idle arc.
                    inner = geometry["rim_radius"] * math.cos(math.pi / 48) - 1
                    self.assertTrue(np.all(distances < inner), (entry["layout"], entry["action"], distances.max(), inner))
            self.assertFalse(glyphs["label"] & glyphs["icon"], (entry["layout"], entry["action"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
