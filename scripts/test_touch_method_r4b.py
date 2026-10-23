#!/usr/bin/env python3
"""R4B pure receipt/ownership controls. No marker or synthetic array is native."""
import ast
import inspect
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

import analyze_touch_contrast_r4b as method
import analyze_touch_contrast_r4 as retained
import prepare_touch_contrast_r4b as prepare
import test_touch_contrast_r4_receipts as receipts
from test_touch_contrast_r4_method import FinalBoundary
from test_touch_contrast_method import PixelMethod
from touch_geometry_r4b import geometry

REPO=Path(__file__).resolve().parents[1]


class Receipts(receipts.ReceiptControls):
    @classmethod
    def setUpClass(cls):
        cls.old_method=receipts.method
        receipts.method=method
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        receipts.method=cls.old_method

    def run_receipts(self,**kwargs):
        # This fixture isolates original source/background/renderer/matrix/image
        # gates. Source-geometry and native-owner calls have separate real
        # function/synthetic controls below; neither is fabricated native data.
        with patch.object(method,"geometry_identity",lambda *a:[]),patch.object(method,"audit_ownership",lambda *a:{"pass":True,"errors":[]}):
            return super().run_receipts(**kwargs)


class Ownership(unittest.TestCase):
    def fixture(self):
        info={"geometry":{},"ownership":{},"action_order":list(method.ACTIONS)}
        components={}
        for i,a in enumerate(method.ACTIONS):
            x,y=40+i*60,50
            info["geometry"][a]={"point":[x,y],"hit_radius":31}
            image=np.zeros((100,720,3),np.uint8);image[y,x]=255;components[a]=image
            info["ownership"][a]={"support_pixels":1,"wrong_owner_pixels":0,"unclaimed_pixels":0,"wrong_owner_witnesses_xy_action":[]}
        return info,components

    def test_complete_native_claim_and_independent_replay(self):
        self.assertTrue(method.audit_ownership(*self.fixture(),"r4b")["pass"])

    def test_inside_own_hit_does_not_override_actual_neighbor(self):
        info,images=self.fixture()
        info["geometry"]["smoke"]["point"]=[80,50]
        # FIRE at40 and SMOKE at80 overlap. At61, own-hit membership is true
        # for FIRE, but SMOKE wins; preserving that point must fail.
        images["fire"][:]=0;images["fire"][50,61]=255
        info["ownership"]["fire"].update(wrong_owner_pixels=1,wrong_owner_witnesses_xy_action=[[61,50,"smoke"]])
        self.assertFalse(method.audit_ownership(info,images,"r4b")["pass"])

    def test_false_zero_owner_claim_cannot_hide_wrong_native_pixel(self):
        info,images=self.fixture()
        images["fire"][:]=0;images["fire"][50,100]=255
        self.assertFalse(method.audit_ownership(info,images,"r4b")["pass"])

    def test_missing_or_malformed_ownership_record_rejects(self):
        info,images=self.fixture();info["ownership"].pop("smoke")
        self.assertFalse(method.audit_ownership(info,images,"r4b")["pass"])
        info,images=self.fixture();info["ownership"]["smoke"]["support_pixels"]=0
        self.assertTrue(method.audit_ownership(info,images,"r4b")["errors"])


class SourceMethod(unittest.TestCase):
    def test_pixel_oracle_and_final_band_predicates_unchanged(self):
        for name in ("audit_pixels","audit_boundary","native_contrast_lower","line_steps","audit_affordance","intermediate_overlap"):
            self.assertEqual(ast.dump(ast.parse(inspect.getsource(getattr(method,name)))),ast.dump(ast.parse(inspect.getsource(getattr(retained,name)))))

    def test_new_wrapper_uses_actual_hit_and_badge_geometry(self):
        source=(REPO/prepare.TOUCH).read_text();wrapped,calls=prepare.instrument(source)
        self.assertIn('"hit_radius": hit_radius(key)',wrapped)
        self.assertIn('point.x + minf(r * 0.66, (hit_radius(key) - 12.625)',wrapped)
        self.assertGreater(len(calls),30)

    def test_geometry_receipt_binds_actual_source_functions(self):
        source=(REPO/prepare.TOUCH).read_text()
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);path=root/prepare.TOUCH;path.parent.mkdir(parents=True);path.write_text(source)
            model=geometry(source,(960,720),(32,0,32,0),1.5)
            info={"layout":"mobile-max","effective_scale":model["env"]["effective_scale"](),"action_order":list(model["points"]),
                "geometry":{a:{"point":p.array().tolist(),"radius":model["radii"][a],"hit_radius":model["hits"][a],"resolved_position":model["env"]["resolved_position"](a).array().tolist()} for a,p in model["points"].items()}}
            receipt={"path":str(root),"original_touch_sha256":method.digest(path)}
            self.assertFalse(method.geometry_identity(info,receipt))
            info["geometry"]["smoke"]["point"][0]+=1
            self.assertTrue(method.geometry_identity(info,receipt))

    def test_geometry_amendment_does_not_waive_bad_baseline(self):
        valid={"baseline":{"provenance_valid":True},"candidate":{"provenance_valid":True,"pass":True},"geometry_policy_valid":True,"font_metrics_equal":True,"analysis_matches_freeze":True}
        self.assertTrue(method.comparison_passes(valid))
        valid["baseline"]["provenance_valid"]=False
        self.assertFalse(method.comparison_passes(valid))


if __name__=="__main__":unittest.main(verbosity=2)
