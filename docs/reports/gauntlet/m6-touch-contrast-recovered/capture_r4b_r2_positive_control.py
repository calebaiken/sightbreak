#!/usr/bin/env python3
"""Retain the agreeing bad-baseline full CLI control, synthetic metadata only."""
import json
from pathlib import Path
import sys

REPORT=Path(__file__).resolve().parent
sys.path.insert(0,str(REPORT.parents[3]/"scripts"))
import analyze_touch_contrast_r4b as method
from test_touch_receipts_r4b_r2 import FullProvenanceComparison,genuine_failure
from test_touch_method_r4b import Ownership

FullProvenanceComparison.setUpClass()
try:
    case=FullProvenanceComparison("test_genuine_bad_baseline_stays_valid_and_cli_comparable")
    owner=method.audit_ownership(*genuine_failure(),"r3")
    baseline=case.audited_source(owner)
    candidate=case.audited_source(method.audit_ownership(*Ownership().fixture(),"r4b"))
    code=case.cli(baseline,candidate)
    cli=json.loads((case.root/"comparison.json").read_text())
    result={"scope":"SYNTHETIC OWNERSHIP AND 32-SCENE METADATA MARKERS; NO NATIVE EVIDENCE", "engine_invocations":0,
        "baseline":{"ownership":owner,"provenance_valid":baseline["provenance_valid"],"product_pass":baseline["pass"],"errors":baseline["errors"]},
        "candidate":{"provenance_valid":candidate["provenance_valid"],"product_pass":candidate["pass"]},"cli_exit":code,
        "geometry_policy_valid":cli["geometry_policy_valid"],"font_metrics_equal":cli["font_metrics_equal"],"analysis_matches_freeze":cli["analysis_matches_freeze"]}
    result["positive_control_pass"]=bool(baseline["provenance_valid"] and not baseline["pass"] and not baseline["errors"] and candidate["pass"] and code==0)
    (REPORT/"r4b-r2-genuine-bad-baseline-control.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({"positive_control_pass":result["positive_control_pass"],"cli_exit":code}))
    assert result["positive_control_pass"]
finally:
    FullProvenanceComparison.tearDownClass()
