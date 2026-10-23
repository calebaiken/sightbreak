#!/usr/bin/env python3
"""Pure full-map receipt reconciliation and full comparison-path controls."""
from contextlib import redirect_stdout
from copy import deepcopy
import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

import analyze_touch_contrast_r4b as method
import test_touch_contrast_r4_receipts as metadata
import test_touch_method_r4b as original_controls


def genuine_failure():
    info,images=original_controls.Ownership().fixture()
    images["fire"][:]=0
    for x,y in ((10,10),(40,50),(100,50),(160,50)):images["fire"][y,x]=255
    info["ownership"]["fire"]={"support_pixels":4,"wrong_owner_pixels":3,"unclaimed_pixels":1,
        "wrong_owner_witnesses_xy_action":[[10,10,""],[100,50,"jump"],[160,50,"crouch"]]}
    return info,images


def mutated(name):
    info,images=genuine_failure()
    record=info["ownership"]["fire"]
    samples=record["wrong_owner_witnesses_xy_action"]
    if name=="false_zero":record.update(wrong_owner_pixels=0,unclaimed_pixels=0,wrong_owner_witnesses_xy_action=[])
    elif name=="missing":samples.pop();record["wrong_owner_pixels"]-=1
    elif name=="extra":samples.append([40,50,"pause"]);record["wrong_owner_pixels"]+=1
    elif name=="duplicate":samples.append([100,50,"jump"]);record["wrong_owner_pixels"]+=1
    elif name=="wrong_winner":samples[1][2]="pause"
    elif name=="swapped_winners":samples[1][2],samples[2][2]=samples[2][2],samples[1][2]
    elif name=="false_unclaimed":samples[1][2]="";record["unclaimed_pixels"]+=1
    elif name=="hidden_unclaimed":samples[0][2]="pause";record["unclaimed_pixels"]=0
    elif name=="wrong_unclaimed_count":record["unclaimed_pixels"]=0
    elif name=="unsupported":samples[1][0]=101
    elif name=="out_of_bounds":samples[1][0]=-1
    elif name=="malformed":samples[1].pop()
    elif name=="noninteger":samples[1][0]=100.0
    elif name=="unknown_winner":samples[1][2]="invented"
    elif name=="support_count":record["support_pixels"]+=1
    elif name=="wrong_count":record["wrong_owner_pixels"]=2
    elif name=="float_count":record["wrong_owner_pixels"]=3.0
    elif name=="boolean_count":record["unclaimed_pixels"]=True
    else:raise ValueError(name)
    return info,images


NEGATIVES=("false_zero","missing","extra","duplicate","wrong_winner","swapped_winners","false_unclaimed","hidden_unclaimed",
    "wrong_unclaimed_count","unsupported","out_of_bounds","malformed","noninteger","unknown_winner","support_count","wrong_count","float_count","boolean_count")


def comparison(baseline,candidate=None):
    candidate=candidate or {"provenance_valid":True,"pass":True}
    return method.comparison_passes({"baseline":baseline,"candidate":candidate,"geometry_policy_valid":True,"font_metrics_equal":True,"analysis_matches_freeze":True})


class CompleteMap(unittest.TestCase):
    def test_genuine_bad_product_has_valid_ownership_receipt_for_both_sources(self):
        for variant in ("r3","r4b"):
            result=method.audit_ownership(*genuine_failure(),variant)
            self.assertFalse(result["pass"])
            self.assertFalse(result["errors"],result["errors"])
            self.assertTrue(all(r["native_receipt_matches_replay"] for r in result["rows"]))
            self.assertTrue(comparison({"provenance_valid":not result["errors"],"pass":False}))

    def test_all_receipt_mutations_invalidate_both_sources(self):
        for variant in ("r3","r4b"):
            for name in NEGATIVES:
                with self.subTest(variant=variant,mutation=name):
                    result=method.audit_ownership(*mutated(name),variant)
                    self.assertTrue(result["errors"],result)
                    self.assertFalse(result["pass"])
                    suspect={"provenance_valid":not result["errors"],"pass":result["pass"]}
                    self.assertFalse(comparison(suspect))
                    self.assertFalse(comparison({"provenance_valid":True,"pass":False},suspect))

    def test_witness_order_does_not_change_complete_map(self):
        info,images=genuine_failure();info["ownership"]["fire"]["wrong_owner_witnesses_xy_action"].reverse()
        self.assertFalse(method.audit_ownership(info,images,"r3")["errors"])

    def test_same_totals_and_coordinates_do_not_hide_wrong_identities(self):
        result=method.audit_ownership(*mutated("swapped_winners"),"r3")
        row=result["rows"][0]
        self.assertTrue(row["native_record_well_formed"])
        self.assertEqual(row["actual_native_wrong_owner_pixels"],row["independent_normalized_hit_replay_wrong_pixels"])
        self.assertFalse(row["native_receipt_matches_replay"])
        self.assertEqual(len(row["wrong_native_winners_xy_native_replay"]),2)

    def test_missing_extra_and_duplicate_component_identity_reject(self):
        info,images=genuine_failure();images.pop("smoke")
        self.assertTrue(method.audit_ownership(info,images,"r3")["errors"])
        info,images=genuine_failure();info["ownership"]["extra"]=deepcopy(info["ownership"]["fire"])
        self.assertTrue(method.audit_ownership(info,images,"r3")["errors"])
        info,images=genuine_failure();info["action_order"][0]="jump"
        self.assertTrue(method.audit_ownership(info,images,"r3")["errors"])


class FullProvenanceComparison(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old_method=metadata.method
        metadata.method=method
        metadata.ReceiptControls.setUpClass.__func__(cls)

    @classmethod
    def tearDownClass(cls):
        metadata.ReceiptControls.tearDownClass.__func__(cls)
        metadata.method=cls.old_method

    def tearDown(self):metadata.ReceiptControls.tearDown(self)

    def audited_source(self,ownership):
        # Real 32-scene audit_source receipt/provenance propagation. Marker PNG
        # decoding, source geometry and contrast are isolated stubs; ownership
        # reconciliation itself ran on the explicit synthetic full samples.
        with patch.object(method,"geometry_identity",lambda *a:[]),patch.object(method,"audit_ownership",return_value=ownership):
            return metadata.ReceiptControls.run_receipts(self)

    def cli(self,baseline,candidate):
        freeze=self.root/"comparison-freeze.json"
        names=("analyze_touch_contrast_r4b.py","analyze_touch_contrast.py","touch_geometry_r4b.py")
        scripts=Path(method.__file__).parent
        freeze.write_text(json.dumps({"fixtures":[{"name":"baseline"},{"name":"candidate"}],
            "frozen_files":[{"path":"scripts/"+n,"sha256":method.digest(scripts/n)} for n in names]}))
        argv=["analyze","--baseline",str(self.controls),"--candidate",str(self.controls),"--out",str(self.root/"comparison.json"),"--freeze",str(freeze),"--backgrounds",str(self.backgrounds)]
        with patch.object(method,"audit_source",side_effect=[baseline,candidate]),patch.object(sys,"argv",argv),redirect_stdout(io.StringIO()):
            return method.main()

    def test_all_contradictory_baselines_fail_full_provenance_comparison_and_cli(self):
        good=self.audited_source(method.audit_ownership(*original_controls.Ownership().fixture(),"r3"))
        self.assertTrue(good["provenance_valid"] and good["pass"])
        for name in NEGATIVES:
            with self.subTest(mutation=name):
                bad=self.audited_source(method.audit_ownership(*mutated(name),"r3"))
                self.assertFalse(bad["provenance_valid"])
                self.assertTrue(bad["errors"])
                self.assertFalse(comparison(bad,good))
                self.assertEqual(self.cli(bad,good),1)

    def test_genuine_bad_baseline_stays_valid_and_cli_comparable(self):
        bad=self.audited_source(method.audit_ownership(*genuine_failure(),"r3"))
        good=self.audited_source(method.audit_ownership(*original_controls.Ownership().fixture(),"r4b"))
        self.assertTrue(bad["provenance_valid"])
        self.assertFalse(bad["pass"])
        self.assertFalse(bad["errors"])
        self.assertTrue(comparison(bad,good))
        self.assertEqual(self.cli(bad,good),0)


if __name__=="__main__":unittest.main(verbosity=2)
