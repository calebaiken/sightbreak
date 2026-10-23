#!/usr/bin/env python3
"""Evidence trace must prove every completed native draw for the requested case."""
import unittest
import tempfile
from pathlib import Path

from diagnose_macos_render import draw_trace, prepare_fixture
from build_manifest import source


def trace():
    return "\n".join(f"RENDER_DIAG phase=drawn frame={frame} case=full msec={frame * 100} draws=134.0 primitives=43186.0"
                     for frame in range(1, 16))


class TraceTest(unittest.TestCase):
    def test_fixture_preserves_source_and_separates_user_data(self):
        before = source()
        with tempfile.TemporaryDirectory() as directory:
            fixture = prepare_fixture(Path(directory))
            self.assertFalse((fixture / "tests").exists())
            self.assertFalse((fixture / ".godot").exists())
            settings = (fixture / "project.godot").read_text()
            self.assertIn('config/use_custom_user_dir=true', settings)
            self.assertIn('config/custom_user_dir_name="SIGHTBREAK-render-diagnostic-', settings)
            self.assertIn('renderer/rendering_method="gl_compatibility"', settings)
            self.assertEqual((fixture / "scripts/main.gd").read_bytes(),
                             (Path(__file__).resolve().parents[1] / "game/scripts/main.gd").read_bytes())
        self.assertEqual(source(), before)

    def test_complete_native_trace(self):
        frames, complete = draw_trace(trace(), "full")
        self.assertTrue(complete)
        self.assertEqual(frames[0]["msec"], 100)
        self.assertEqual(frames[-1]["primitives"], 43186)

    def test_missing_duplicate_wrong_case_and_regressing_clock_fail(self):
        original = trace()
        for corrupt in ("\n".join(original.splitlines()[1:]),
                        original + "\n" + original.splitlines()[-1],
                        original.replace("case=full", "case=shadows-off", 1),
                        original.replace("msec=1500", "msec=1")):
            with self.subTest(trace=corrupt):
                self.assertFalse(draw_trace(corrupt, "full")[1])

    def test_exit_marker_without_draws_is_not_a_trace(self):
        self.assertFalse(draw_trace("RENDER_DIAG_EXIT capture_error=0 case=full msec=1200", "full")[1])


if __name__ == "__main__":
    unittest.main()
