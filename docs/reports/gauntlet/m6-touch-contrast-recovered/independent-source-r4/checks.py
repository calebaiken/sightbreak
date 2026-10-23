#!/usr/bin/env python3
"""Independent source/pure review. No engine, import, image acquisition or edits."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

import numpy as np

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO / "scripts"))
from analyze_touch_contrast_r4 import audit_boundary
from prepare_touch_contrast_r4 import instrument

OUT = Path(__file__).with_name("checks.json")
FREEZE = "16335abfaf2068b2b2ea54c7e100a1505f62b5c1"
report = {"source_freeze": FREEZE, "scope": "SOURCE_AND_SYNTHETIC_ONLY", "engine_invocations": 0, "checks": {}}


def check(name, condition, **evidence):
    report["checks"][name] = {"pass": bool(condition), **evidence}
    assert condition, name


def square():
    u = np.zeros((30, 30, 3), dtype=np.uint8)
    p, b, w, f = (u.copy() for _ in range(4))
    p[4:26, 4:26] = w[4:26, 4:26] = f[4:26, 4:26] = 255
    return p, u, b, w, f


def audit(values, alpha=1):
    p, u, b, w, f = values
    return audit_boundary(p, u, b, w, alpha, f)


def summary(row):
    return {k: row[k] for k in ("pass", "resolved", "support_pixels", "missing_footprint_pixels", "underlay_compositing_errors", "contrast_lower_bound", "unqualified_contours")}


freeze_path = REPO / "docs/reports/gauntlet/m6-touch-contrast-recovered/SOURCE_FREEZE-r4.json"
# SOURCE_FREEZE-r4.json is in the handoff commit, so use its exact committed bytes.
freeze_bytes = subprocess.check_output(["git", "-C", str(REPO), "show", "bb1fc88850a3e41376b1717b163bc479aab378a6:" + str(freeze_path.relative_to(REPO))])
freeze = json.loads(freeze_bytes)
frozen_errors = []
for entry in freeze["frozen_files"]:
    actual = (REPO / entry["path"]).read_bytes()
    if hashlib.sha256(actual).hexdigest() != entry["sha256"] or len(actual) != entry["bytes"]:
        frozen_errors.append(entry["path"])
check("fifteen_frozen_files_exact", not frozen_errors, errors=frozen_errors, count=len(freeze["frozen_files"]), freeze_sha256=hashlib.sha256(freeze_bytes).hexdigest())

staging = []
for receipt in freeze["fixtures"]:
    root = Path(receipt["path"])
    manifest_bytes = (root / "SOURCE.json").read_bytes()
    manifest = json.loads(manifest_bytes)
    assert hashlib.sha256(manifest_bytes).hexdigest() == receipt["manifest_sha256"]
    assert manifest["source"] == receipt["source_full"]
    expected = set()
    for entry in manifest["files"]:
        data = (root / entry["path"]).read_bytes()
        assert hashlib.sha256(data).hexdigest() == entry["sha256"]
        committed = subprocess.check_output(["git", "-C", str(REPO), "show", receipt["source_full"] + ":" + entry["path"]])
        assert committed == data
        expected.add(entry["path"])
    for entry in manifest["fixture"]:
        data = (root / entry["path"]).read_bytes()
        assert hashlib.sha256(data).hexdigest() == entry["sha256"]
        assert data == (REPO / "scripts/fixtures/touch_contrast_r4" / Path(entry["path"]).name).read_bytes()
        expected.add(entry["path"])
    wrapped, calls = instrument((root / "game/scripts/ui/touch_controls.gd").read_text())
    assert calls == manifest["instrumentation"]
    wrapped = wrapped.replace("class_name TacticalTouch\n", "", 1)
    for name, key in (("touch_contrast_instrumented.gd", "instrumented_sha256"), ("touch_contrast_instrumented.gd.uid", "instrumented_uid_sha256")):
        rel = "game/tests/" + name
        data = (root / rel).read_bytes()
        assert hashlib.sha256(data).hexdigest() == manifest[key]
        if name.endswith(".gd"): assert data == wrapped.encode()
        expected.add(rel)
    actual = {str(p.relative_to(root)) for p in root.rglob("*") if p.is_file()}
    assert actual == expected | {"SOURCE.json"}
    uid_values = [p.read_bytes() for p in root.rglob("*.uid")]
    assert len(uid_values) == len(set(uid_values))
    assert not any(root.rglob(".godot"))
    staging.append({"name": receipt["name"], "checked_paths": len(expected), "original_paths": len(manifest["files"]), "unique_uid_paths": len(uid_values), "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(), "godot_cache_present": False})
check("independent_read_only_staging_exact", all(x["checked_paths"] == 327 and x["original_paths"] == 323 for x in staging), fixtures=staging)

reference = json.loads((REPO / "scripts/fixtures/touch_contrast_r4/r3_glyph_support.json").read_text())
reference_errors = []
raw = Path("/workspace/sightbreak-touch-contrast-native-recovered-r3/candidate")
for entry in reference["inputs"]:
    path = raw / entry["scene"] / entry["file"]
    scene = json.loads((path.parent / "scene.json").read_text())
    if hashlib.sha256(path.read_bytes()).hexdigest() != entry["sha256"] or scene["images"][entry["file"]] != entry["sha256"]:
        reference_errors.append(str(path))
check("retained_glyph_mask_inputs_bound_to_r3", not reference_errors and reference["source"] == freeze["baseline_commit"], errors=reference_errors, input_images=len(reference["inputs"]), control_assignments=len(reference["controls"]))

source = (REPO / "game/scripts/ui/touch_controls.gd").read_text()
baseline = subprocess.check_output(["git", "-C", str(REPO), "show", freeze["baseline_commit"] + ":game/scripts/ui/touch_controls.gd"]).decode()
check("input_and_physical_geometry_unchanged", source.split("func _draw()", 1)[0] == baseline.split("func _draw()", 1)[0])
check("later_smoke_body_is_source_bound", source.index('"grenade": Vector2(0.60, 0.80)') < source.index('"smoke": Vector2(0.69, 0.80)') and 'draw_circle(point, paint_r, Color(0.045, 0.058, 0.072, 0.86))' in source)

# Exact fixture policy at mobile-max. This is analytic native-pixel-center
# geometry, not a prediction of Godot raster pixel values.
r, alpha = 28 * 1.5, .35
frag = np.array([32 + .60 * 896, .80 * 720])
smoke = np.array([32 + .69 * 896, .80 * 720])
yy, xx = np.indices((110, 200))
xy = np.stack((xx + 500.5, yy + 520.5), axis=-1)
fd, sd = (np.linalg.norm(xy - center, axis=-1) for center in (frag, smoke))
core_lens = (fd <= r - 1) & (sd <= r - 1)
coords = np.argwhere(core_lens)
native_yx = (coords + np.array([520, 500])).tolist()
gap = float(np.linalg.norm(smoke - frag))
check("known_overlap_contains_full_pixel_centers", bool(len(coords)), centers={"grenade": frag.tolist(), "smoke": smoke.tolist()}, radius=r, center_distance=gap, body_overlap=2*r-gap, halo_overlap=2*(r+5.25/2)-gap, pixel_centers_one_px_inside_both=len(coords), witnesses_yx=native_yx[:12], later_body_alpha=.86, maximum_selected_d_after_body_codes=255*(1-.86), missing_threshold_codes=255*alpha-2)

defaults = source.split("const DEFAULT_POSITIONS :=", 1)[1].split("var positions:", 1)[0]
points, radii = {}, {}
for action, sx, sy in re.findall(r'"(\w+)": Vector2\(([\d.]+), ([\d.]+)\)', defaults):
    radii[action] = (65 if action == "move" else 40 if action == "fire" else 28)*1.5
    inset = radii[action] + 8
    points[action] = np.clip(np.array([32+float(sx)*896, float(sy)*720]), [32+inset,inset], [928-inset,720-inset])
paint_point = np.array([610.5,575.5])
normalized = {a: float(np.linalg.norm(paint_point-p)/radii[a]) for a,p in points.items() if a != "move"}
winner = min((a for a in normalized if normalized[a] <= 1.25), key=normalized.get)
check("visible_frag_body_point_selects_smoke", np.linalg.norm(paint_point-frag) < r and winner == "smoke", point_xy=paint_point.tolist(), actual_action_at_winner=winner, normalized_distances={a: normalized[a] for a in ("grenade","smoke")}, hit_circle_overlap=2*1.25*r-gap, interpretation="Inside-own-hit-circle is insufficient to establish ownership when normalized nearest-action selection wins for a neighbor")
pause = points["pause"]
check("legacy_max_pause_hit_region_exceeds_safe_area", pause[0]+radii["pause"]*1.25 > 928, pause_center=pause.tolist(), hit_radius=radii["pause"]*1.25, safe_right=928, right_spill=float(pause[0]+radii["pause"]*1.25-928), top_spill=float(max(0,radii["pause"]*1.25-pause[1])), interpretation="Existing unchanged geometry; radius+8 inset is smaller than radius*1.25 at maximum scale. No physical safe-area acceptance follows from source identity.")

# Conservative body-only model: own full component can contribute no more than
# 255 codes before the later .86 smoke fill. Its footprint is isolated/opaque.
# Source halos would add later opacity, so they cannot rescue these lost pixels.
mask, later = fd < r, sd < r
u = np.full((*mask.shape, 3), 255., dtype=float)
p, b, w, f = (u.copy() for _ in range(4))
f[:] = 0
f[mask] = 255
body_rgb = np.array([.045, .058, .072])*255
p[mask] = .86*body_rgb + .14*u[mask]
b[mask] = .14*u[mask]
w[mask] = .86*255 + .14*u[mask]
plain = [np.rint(a).astype(np.uint8) for a in (p,u,b,w,f)]
before = audit(plain, alpha)
check("unoccluded_source_body_model_passes", before["pass"], result=summary(before))
for image in (p,u,b,w):
    image[later] = .86*body_rgb + .14*image[later]
after = audit([np.rint(a).astype(np.uint8) for a in (p,u,b,w,f)], alpha)
check("source_overlap_model_fails_frozen_gate", not after["pass"] and after["missing_footprint_pixels"] >= len(coords), result=summary(after), expected_failure="Cross-control full-footprint loss is retained even for depleted component alpha .35")

# Opaque diagnostics contain no U information. An unrelated supported U can
# remain resolved and pass. Source-bound suppression is an external dependency.
v = square()
check("opaque_positive", audit(v)["pass"])
v[1][4:26,4:26] = 32
wrong_u = audit(v)
check("opaque_unrelated_underlay_can_pass_pixels", wrong_u["resolved"] and wrong_u["pass"], result=summary(wrong_u), interpretation="Identifiability limitation, not native evidence; exact suppression source and receipts remain necessary")

# The registered inward witness can approve an outer contour identical to U.
# Its claim must remain 'contrast within four pixels', not perimeter contrast.
v = square()
v[0][4:26,4:26] = 0
v[0][6:24,6:24] = 255
edge = audit(v)
check("invisible_outer_contour_can_pass_registered_band", edge["pass"], result=summary(edge), outer_contour_normal_equals_underlay=True, inward_offset=2)

# A component-wide minimum primitive alpha cannot certify expected opacity at
# every interior pixel. Complete foreground gates must remain separate.
v = square()
v[0][12:18,12:18] = v[3][12:18,12:18] = 102
interior = audit(v, alpha=.35)
check("interior_sixty_percent_replacement_can_pass_component", interior["pass"], result=summary(interior), interpretation="Minimum-alpha and contour scope permit this; it must not be called complete action nonocclusion")

report["minimum_correction"] = {"drawing_only": "Separate the complete FRAG/SMOKE decorative footprints before native; preserve all glyphs and unchanged hit geometry.", "max_mobile_equal_rim_radius_without_margin": gap/2 - 5.25/2, "current_rim_radius": r, "required_radius_reduction_before_raster_margin": r - (gap/2 - 5.25/2), "alternative_extra_center_spacing_before_raster_margin": 2*(r+5.25/2)-gap, "warning": "These are analytic limits, not a validated patch; include raster margin and inspect all layouts/neighbor badges in the next freeze."}
report["all_review_checks_pass"] = all(x["pass"] for x in report["checks"].values())
report["native_acquisition_authorized_by_review"] = False
report["verdict"] = "NO_GO_PRODUCT_GEOMETRY_CHANGE_BEFORE_NATIVE"
OUT.write_text(json.dumps(report, indent=2)+"\n")
print(json.dumps({"checks": len(report["checks"]), "all_pass": report["all_review_checks_pass"], "verdict": report["verdict"], "overlap_row": summary(after)}))
