#!/usr/bin/env python3
"""Independent R4B source/pure review. Reads stages; writes this report only."""
import ast
import hashlib
import inspect
import json
from pathlib import Path
import re
import subprocess
import sys

import numpy as np

REPO = Path(__file__).resolve().parents[5]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO / "scripts"))
import analyze_touch_contrast_r4b as method
import analyze_touch_contrast_r4 as retained
from prepare_touch_contrast_r4b import instrument, TOUCH
from touch_geometry_r4b import geometry, check_case, critical_scales, ownership_minimum, component_envelopes
from test_touch_geometry_r4b import reference, SIZES, INSETS
from test_touch_method_r4b import Ownership

FREEZE = "2ea23f947aec6085449bced53c9b061618a67029"
report = {"source_freeze": FREEZE, "scope": "SOURCE_PURE_ONLY", "engine_invocations": 0, "native_captures": 0, "checks": {}}


def sha(data): return hashlib.sha256(data).hexdigest()
def git(*args): return subprocess.check_output(["git", "-C", str(REPO), *args])
def check(name, condition, **evidence):
    report["checks"][name] = {"pass": bool(condition), **evidence}
    assert condition, name


freeze_path = REPO / "docs/reports/gauntlet/m6-touch-contrast-recovered/SOURCE_FREEZE-r4b.json"
freeze_bytes = freeze_path.read_bytes()
freeze = json.loads(freeze_bytes)
for entry in freeze["frozen_files"]:
    data = (REPO / entry["path"]).read_bytes()
    assert data == git("show", FREEZE + ":" + entry["path"])
    assert sha(data) == entry["sha256"] and len(data) == entry["bytes"]
check("twenty_frozen_files_match_exact_source", len(freeze["frozen_files"]) == 20,
      freeze_sha256=sha(freeze_bytes), count=len(freeze["frozen_files"]))

stages = []
for receipt in freeze["fixtures"]:
    root = Path(receipt["path"])
    manifest_bytes = (root / "SOURCE.json").read_bytes()
    manifest = json.loads(manifest_bytes)
    assert sha(manifest_bytes) == receipt["manifest_sha256"]
    assert manifest["source"] == receipt["source_full"]
    paths = git("ls-tree", "-r", "--name-only", receipt["source_full"], "game").decode().splitlines()
    assert paths == [e["path"] for e in manifest["files"]]
    expected = set()
    for entry in manifest["files"]:
        data = (root / entry["path"]).read_bytes()
        assert data == git("show", receipt["source_full"] + ":" + entry["path"])
        assert sha(data) == entry["sha256"] and len(data) == entry["bytes"]
        expected.add(entry["path"])
    for entry in manifest["fixture"]:
        data = (root / entry["path"]).read_bytes()
        assert data == (REPO / "scripts/fixtures/touch_contrast_r4b" / Path(entry["path"]).name).read_bytes()
        assert sha(data) == entry["sha256"]
        expected.add(entry["path"])
    wrapped, calls = instrument((root / TOUCH).read_text())
    assert calls == manifest["instrumentation"]
    wrapped = wrapped.replace("class_name TacticalTouch\n", "", 1)
    for name, key in (("touch_contrast_instrumented.gd", "instrumented_sha256"), ("touch_contrast_instrumented.gd.uid", "instrumented_uid_sha256")):
        path = "game/tests/" + name
        data = (root / path).read_bytes()
        assert sha(data) == manifest[key]
        if name.endswith(".gd"): assert data == wrapped.encode()
        expected.add(path)
    assert {str(p.relative_to(root)) for p in root.rglob("*") if p.is_file()} == expected | {"SOURCE.json"}
    uid_values = [p.read_bytes() for p in root.rglob("*.uid")]
    assert len(uid_values) == len(set(uid_values)) and not any(root.rglob(".godot"))
    stages.append({"name": receipt["name"], "original_paths": len(paths), "checked_paths": len(expected), "uid_paths": len(uid_values), "manifest_sha256": sha(manifest_bytes), "cache_present": False})
check("independent_read_only_staging_exact", all(s["original_paths"] == 323 and s["checked_paths"] == 327 for s in stages), stages=stages)

glyph = json.loads((REPO / "scripts/fixtures/touch_contrast_r4/r3_glyph_support.json").read_text())
raw = Path("/workspace/sightbreak-touch-contrast-native-recovered-r3/candidate")
for entry in glyph["inputs"]:
    path = raw / entry["scene"] / entry["file"]
    scene = json.loads((path.parent / "scene.json").read_text())
    assert sha(path.read_bytes()) == entry["sha256"] == scene["images"][entry["file"]]
check("historical_native_glyph_inputs_remain_bound", glyph["source"] == freeze["baseline_commit"], inputs=len(glyph["inputs"]), assignments=len(glyph["controls"]))

source = (REPO / TOUCH).read_text()
check("handoff_changes_no_frozen_code", git("diff", "--name-only", FREEZE, "a4f942af1213f2d4a18a790adea624bcbcd3b7b5", "--", "game", "scripts") == b"")
for name in ("audit_pixels", "audit_boundary", "native_contrast_lower", "line_steps", "audit_affordance", "intermediate_overlap"):
    assert ast.dump(ast.parse(inspect.getsource(getattr(method, name)))) == ast.dump(ast.parse(inspect.getsource(getattr(retained, name))))
check("old_pixel_and_final_band_predicates_unchanged", method.LIMITS == retained.LIMITS and method.LEGACY == retained.LEGACY, thresholds=method.LIMITS, retained_diagnostic_groups=sorted(method.LEGACY))

original_certificate = json.loads((freeze_path.parent / "r4b-continuous-certificate.json").read_text())
rep_bytes = (OUT / "reproduced-certificate.json").read_bytes()
rep = json.loads(rep_bytes)
check("reproduced_continuous_certificate_exact", rep == original_certificate and sha(rep_bytes) == freeze["geometry_certificate_sha256"], sha256=sha(rep_bytes), cases=len(rep["cases"]), intervals=rep["intervals"])

# Independently enumerate branch interiors, including quarter points and near
# branch endpoints. This is a source cross-check, not a replacement proof.
sampled = 0
actual_min = {"ownership": float("inf"), "paint_clearance": float("inf"), "inside_own_hit": float("inf")}
max_skipped_requested_scale = 0.
for row in rep["cases"]:
    critical = critical_scales(source, row["size"], row["insets"])
    assert critical == row["critical_scales"]
    scales = set(critical)
    for lo, hi in zip(critical, critical[1:]):
        scales.update(lo + (hi - lo) * f for f in (.001, .25, .499, .751, .999))
    for interval in row["intervals"]:
        assert all(interval[k] > 0 for k in ("ownership_squared_margin_lower", "inside_hit_margin_lower", "paint_clearance_lower"))
    sorted_intervals = sorted(row["intervals"], key=lambda x: x["lo"])
    for a, b in zip(sorted_intervals, sorted_intervals[1:]):
        max_skipped_requested_scale = max(max_skipped_requested_scale, b["lo"] - a["hi"])
    for scale in sorted(scales):
        case = check_case(source, row["size"], row["insets"], scale, reference(), sample=True)
        assert not case["errors"], (row["size"], row["insets"], scale, case["errors"][:1])
        sampled += 1
        actual_min["ownership"] = min(actual_min["ownership"], case["minimum_normalized_squared_ownership_margin"])
        actual_min["paint_clearance"] = min(actual_min["paint_clearance"], case["minimum_paint_clearance"])
        model = geometry(source, row["size"], row["insets"], scale)
        for action, point in model["points"].items():
            if action == "move": continue
            for circle in component_envelopes(source, model, action, reference()):
                margin = model["hits"][action] - np.linalg.norm(circle["center"] - point.array()) - circle["radius"]
                actual_min["inside_own_hit"] = min(actual_min["inside_own_hit"], float(margin))
check("critical_branch_interiors_hold", sampled > 1000, cases_sampled=sampled, actual_minima=actual_min, largest_nextafter_gap=max_skipped_requested_scale,
      qualification="Source arithmetic plus audited branch formulas; Python doubles and native Vector2/raster rounding are not identical.")

# Independent numeric minimization samples the whole disk, not only its rim.
# It must never find a value below the closed-form lower bound.
rng = np.random.default_rng(90423)
maximum_bound_excess = -float("inf")
for _ in range(200):
    center, own, neighbor = rng.uniform(-100, 100, (3, 2))
    radius, oh, nh = rng.uniform(1, 80, 3)
    bound, _ = ownership_minimum(center, radius, own, neighbor, oh, nh)
    angles = np.linspace(0, 2 * np.pi, 257)
    distances = np.linspace(0, radius, 25)
    xy = center + (distances[:, None, None] * np.stack((np.cos(angles), np.sin(angles)), axis=-1)).reshape(-1, 2)
    values = np.sum((xy - neighbor) ** 2, axis=-1) / nh ** 2 - np.sum((xy - own) ** 2, axis=-1) / oh ** 2
    maximum_bound_excess = max(maximum_bound_excess, float(bound - values.min()))
check("disk_minimum_does_not_overstate_random_lower_bounds", maximum_bound_excess < 1e-9, random_disks=200, maximum_bound_excess=maximum_bound_excess)

custom = check_case(source, (960,720), (32,0,32,0), 1., reference(), positions={"grenade": (.6,.8), "smoke": (.6,.8)})
tiny = check_case(source, (200,200), (0,0,0,0), 1.5, reference())
check("custom_collisions_and_tiny_dimensions_remain_unqualified", bool(custom["errors"] and tiny["errors"]), custom_error_kinds=sorted({e["kind"] for e in custom["errors"]}), tiny_error_kinds=sorted({e["kind"] for e in tiny["errors"]}))

# Preserve the three strongest retained limitations against this exact analyzer.
def square():
    u = np.zeros((30,30,3), dtype=np.uint8)
    p,b,w,f = (u.copy() for _ in range(4))
    p[4:26,4:26] = w[4:26,4:26] = f[4:26,4:26] = 255
    return p,u,b,w,f
def audit(v, alpha=1):
    p,u,b,w,f = v
    return method.audit_boundary(p,u,b,w,alpha,f)
v=square();v[1][4:26,4:26]=32
wrong_u=audit(v)
v=square();v[0][4:26,4:26]=0;v[0][6:24,6:24]=255
outer=audit(v)
v=square();v[0][12:18,12:18]=v[3][12:18,12:18]=102
interior=audit(v,.35)
check("strongest_final_band_falsifiers_remain", all(x["pass"] for x in (wrong_u,outer,interior)),
      opaque_unrelated_underlay_passes=wrong_u["pass"], invisible_outer_contour_passes=outer["pass"], interior_sixty_percent_replacement_passes=interior["pass"])

# BLOCKER: a baseline receipt contradicts independent replay but receives no
# provenance error. The final comparison allows failing baselines by design.
info, images = Ownership().fixture()
images["fire"][:] = 0
images["fire"][50,100] = 255
ownership = method.audit_ownership(info, images, "r3")
comparison = {"baseline": {"provenance_valid": not ownership["errors"], "pass": ownership["pass"]}, "candidate": {"provenance_valid": True, "pass": True}, "geometry_policy_valid": True, "font_metrics_equal": True, "analysis_matches_freeze": True}
false_accept = method.comparison_passes(comparison)
check("invalid_baseline_ownership_receipt_counterexample_reproduces", false_accept and not ownership["errors"] and not ownership["pass"],
      synthetic_only=True, ownership_errors=ownership["errors"], fire_row=ownership["rows"][0], comparison_accepts_invalid_baseline=bool(false_accept),
      requirement="Invalid baseline ownership receipt blocks comparison; legitimate baseline geometry failure remains comparable.")

# Correct count and support do not validate the recorded wrong winning identity.
info, images = Ownership().fixture()
images["fire"][:] = 0
images["fire"][50,100] = 255
info["ownership"]["fire"].update(wrong_owner_pixels=1,wrong_owner_witnesses_xy_action=[[100,50,"pause"]])
forged = method.audit_ownership(info, images, "r3")
check("invalid_baseline_recorded_winner_not_reconciled", not forged["errors"] and forged["rows"][0]["native_record_well_formed"],
      synthetic_only=True, supplied_wrong_winner="pause", independently_selected_winner="jump", fire_row=forged["rows"][0])

report["verdict"] = "REJECT_SOURCE_METHOD_READINESS_INVALID_BASELINE_OWNERSHIP_RECEIPT_FENCE"
report["native_lane_released"] = False
report["all_expected_review_findings_reproduced"] = all(x["pass"] for x in report["checks"].values())
(OUT / "checks.json").write_text(json.dumps(report,indent=2)+"\n")
print(json.dumps({"checks":len(report["checks"]),"expected_findings_reproduced":report["all_expected_review_findings_reproduced"],"verdict":report["verdict"]}))
