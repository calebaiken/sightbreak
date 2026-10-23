#!/usr/bin/env python3
"""Source/continuous geometry controls; no engine and no rendered acceptance."""
import hashlib
import json
from pathlib import Path
import subprocess
import unittest

import numpy as np

from touch_geometry_r4b import Vector2, geometry, interval_certificate, check_case, function_source

REPO = Path(__file__).resolve().parents[1]
SOURCE = REPO / "game/scripts/ui/touch_controls.gd"
SIZES = ((960,540),(960,720),(1280,720),(1280,800),(1920,720),(1920,1080),(860,480),(720,1280))
INSETS = ((0,0,0,0),(32,0,32,0),(80,24,80,56),(100,40,20,30))


def reference():
    data = json.loads((REPO / "scripts/fixtures/touch_contrast_r4/r3_glyph_support.json").read_text())
    return {e["action"]: e for e in data["controls"] if e["layout"] == "desktop-min"}


class ProductGeometry(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SOURCE.read_text()
        cls.old = subprocess.check_output(["git", "-C", str(REPO), "show", "16335ab:game/scripts/ui/touch_controls.gd"]).decode()

    def test_event_layout_persistence_and_input_consumption_functions_unchanged(self):
        for name in ("_ready", "_notification", "refresh_safe_area", "restore_layout", "reset_layout", "exported_layout", "reset_input", "joystick_vector", "_input", "consume_look", "_draw_action_icon"):
            self.assertEqual(function_source(self.source, name)[0], function_source(self.old, name)[0], name)
        self.assertEqual(self.source.split("var positions:")[0], self.old.split("var positions:")[0])

    def test_real_source_tie_winner_independent_of_neighbor_order(self):
        args = (self.source, (1280,720), (0,0,0,0), 1.)
        a = geometry(*args, positions={"grenade": (.5,.5), "smoke": (.5,.5)})
        b = geometry(*args, positions={"grenade": (.5,.5), "smoke": (.5,.5)}, reverse=True)
        p = a["points"]["grenade"]
        self.assertEqual(a["env"]["action_at"](p), "grenade")
        self.assertEqual(b["env"]["action_at"](p), "grenade")

    def test_dictionary_order_does_not_change_default_ownership(self):
        for size in SIZES:
            a = geometry(self.source,size,(32,0,32,0),1.5)
            b = geometry(self.source,size,(32,0,32,0),1.5,reverse=True)
            for action in a["points"]:
                if action == "move": continue
                for offset in ((0,0),(10,0),(0,10),(-10,-10)):
                    p = a["points"][action] + Vector2(*offset)
                    self.assertEqual(a["env"]["action_at"](p),b["env"]["action_at"](p))

    def test_original_wrong_owner_witness_is_no_longer_frag_affordance(self):
        result = check_case(self.source,(960,720),(32,0,32,0),1.5,reference(),sample=True)
        self.assertFalse(result["errors"], result["errors"])
        model = geometry(self.source,(960,720),(32,0,32,0),1.5)
        self.assertGreater(model["points"]["grenade"].distance_to(Vector2(610.5,575.5)), model["radii"]["grenade"] + 2.625)

    def test_inherited_menu_target_spill_is_corrected(self):
        m = geometry(self.source,(960,720),(32,0,32,0),1.5)
        p,h = m["points"]["pause"],m["hits"]["pause"]
        self.assertLessEqual(p.x+h,928)
        self.assertGreaterEqual(p.y-h,0)

    def test_saved_coordinates_are_values_not_modified_by_projection(self):
        m = geometry(self.source,(960,720),(32,0,32,0),1.5)
        self.assertEqual(m["env"]["positions"]["grenade"].x,.6)
        self.assertEqual(m["env"]["resolved_position"]("grenade").x,.58)
        custom=geometry(self.source,(960,720),(32,0,32,0),1.5,positions={"grenade":(.2,.5)})
        self.assertEqual(custom["env"]["resolved_position"]("grenade").x,.2)

    def test_deliberately_bad_custom_layout_is_rejected(self):
        result=check_case(self.source,(960,720),(32,0,32,0),1.,reference(),positions={"grenade":(.6,.8),"smoke":(.6,.8)})
        self.assertTrue(any(x["kind"]=="wrong_owner" for x in result["errors"]))

    def test_endpoint_and_midpoint_sample_sweep(self):
        for size in SIZES:
            for insets in INSETS:
                for scale in (.7,1.,1.5):
                    row=check_case(self.source,size,insets,scale,reference(),sample=True)
                    self.assertFalse(row["errors"], (size,insets,scale,row["errors"][:2]))


def emit_certificate(path):
    source=SOURCE.read_text()
    rows=[interval_certificate(source,size,insets,reference()) for size in SIZES for insets in INSETS]
    data={"scope":"SOURCE_DERIVED_CONTINUOUS_GEOMETRY_ONLY_NOT_NATIVE_OR_PHYSICAL_REACH", "source_sha256":hashlib.sha256(source.encode()).hexdigest(),
        "scale_interval":[.7,1.5],"raster_envelope_margin":.75,"cases":rows,"pass":all(r["pass"] for r in rows),
        "intervals":sum(len(r["intervals"]) for r in rows),"engine_invocations":0,
        "custom_layout_limit":"Colliding/coincident user-created layouts are rejected by this proof, not automatically repaired or qualified by the product."}
    path.write_text(json.dumps(data,indent=2)+"\n")
    print(json.dumps({"pass":data["pass"],"cases":len(rows),"intervals":data["intervals"]}))
    return 0 if data["pass"] else 1


if __name__=="__main__":
    import sys
    if len(sys.argv)==3 and sys.argv[1]=="--certificate": raise SystemExit(emit_certificate(Path(sys.argv[2])))
    unittest.main(verbosity=2)
