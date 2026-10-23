#!/usr/bin/env python3
"""R4 full-glyph gates plus a separately registered final-component edge audit.

The original R3 analyzer and failed results remain immutable. This module imports
its exact complete-footprint pixel oracle; it never reclassifies an R3 result.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image

from analyze_touch_contrast import audit_pixels

GROUPS = ["active_label", "inactive_label", "active_icon", "inactive_icon",
          "empty_count", "ready_count", "border", "held_border", "joystick_ring", "joystick_knob"]
LIMITS = {"active_label": 4.5, "empty_count": 4.5, "ready_count": 4.5,
          "active_icon": 3.0, "border": 3.0, "held_border": 3.0,
          "joystick_ring": 3.0, "joystick_knob": 3.0}
LAYOUTS = {"mobile-min": ([960, 720], .7, 32), "mobile-max": ([960, 720], 1.5, 32),
           "desktop-min": ([1280, 720], .7, 0), "desktop-max": ([1280, 720], 1.5, 0)}
BACKGROUNDS = ("white", "gray", "arena", "smoke")
ACTIONS = ("fire", "jump", "crouch", "reload", "interact", "grenade", "smoke", "buy", "pause", "switch", "score")
LABELS = dict(zip(ACTIONS, ("FIRE", "JUMP", "LOW", "RELOAD", "USE", "FRAG", "SMOKE", "BUY", "MENU", "SWAP", "TEAM")))
LEGACY = {"border", "held_border"}
LAYER_FOOTPRINTS = ("label_surround", "icon_surround", "badge_paint", "held_fill")


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def matrix():
    return {layout + "-" + background + "-" + state: (layout, background, state == "held")
            for layout in LAYOUTS for background in BACKGROUNDS for state in ("idle", "held")}


def scene_identity(info, expected):
    errors = []
    layout, background, held = expected
    size, scale, inset = LAYOUTS[layout]
    fields = {"id": layout + "-" + background + ("-held" if held else "-idle"),
              "layout": layout, "size": size, "scale": scale, "inset": inset, "held": held,
              "counts": {"grenade": 0, "smoke": 1}, "movement": [.65, .45] if held else [0, 0],
              "actions": ["fire", "reload", "interact"] if held else []}
    for field, value in fields.items():
        if info.get(field) != value:
            errors.append("incorrect " + field)
    keys = {"fire", "jump", "crouch", "reload", "interact", "grenade", "smoke", "buy", "pause", "switch", "score", "move"}
    if set(info.get("geometry", {})) != keys:
        errors.append("incomplete component identities")
    return errors


def luminance(rgb):
    rgb = np.clip(rgb, 0, 1)
    lin = np.where(rgb <= .04045, rgb / 12.92, ((rgb + .055) / 1.055) ** 2.4)
    return lin @ np.array([.2126, .7152, .0722])


def ratio(a, b):
    return (np.maximum(a, b) + .05) / (np.minimum(a, b) + .05)


def native_contrast_lower(p, u):
    """Observed native P/U contrast, conservatively allowing ±0.5 code/channel."""
    pl, ph, ul, uh = [luminance(np.clip(x / 255, 0, 1)) for x in (p - .5, p + .5, u - .5, u + .5)]
    return np.where(pl > uh, (pl + .05) / (uh + .05), np.where(ul > ph, (ul + .05) / (ph + .05), 1.0))


def line_steps(dy, dx):
    """Inclusive integer Bresenham path; all samples must belong to this F."""
    x, y, tx, ty = 0, 0, dx, dy
    ax, ay, sx, sy = abs(dx), abs(dy), 1 if dx >= 0 else -1, 1 if dy >= 0 else -1
    err, out = ax - ay, []
    while True:
        out.append((y, x))
        if (x, y) == (tx, ty): return out
        e = err * 2
        if e > -ay: err -= ay; x += sx
        if e < ax: err += ax; y += sy


def audit_boundary(normal, underlay, black, white, primitive_alpha, footprint):
    """Every 8-neighbor contour, holes included, needs its own connected witness.

    No source RGB, shared-color fit, percentile, handpicked arc, flood-fill glyph
    mask or missing-pixel exclusion is used. Glyph coverage is a separate gate.
    P/U are the actual normal and whole-component-suppressed native images.
    """
    p, u, b, w, f = [np.asarray(x, dtype=float) for x in (normal, underlay, black, white, footprint)]
    if len({x.shape for x in (p, u, b, w, f)}) != 1 or p.ndim != 3 or p.shape[-1] != 3:
        raise ValueError("component diagnostic sizes differ")
    if not 0 < primitive_alpha <= 1: raise ValueError("missing component primitive alpha")
    d, support = w - b, f.max(axis=-1) >= 1
    result = {"support_pixels": int(support.sum()),
        "outside_changed": int(((np.maximum.reduce([np.abs(x - u).max(axis=-1) for x in (p, b, w)]) > 1) & ~support).sum()),
        "unexpected_support_pixels": int(((d.max(axis=-1) >= 1) & ~support).sum()),
        "underlay_compositing_errors": int(((np.abs(b - u * (1 - d / 255)).max(axis=-1) > 2) & support).sum()),
        "missing_footprint_pixels": int(((d + 2 < f * primitive_alpha).any(axis=-1) & support).sum()),
        "negative_diagnostic_pixels": int((d.min(axis=-1) < -1).sum()),
        "nonneutral_coverage_pixels": int((d.max(axis=-1) - d.min(axis=-1) > 1).sum()),
        "nonneutral_footprint_pixels": int((f.max(axis=-1) - f.min(axis=-1) > 1).sum())}
    if not support.any(): return {**result, "resolved": False, "pass": False, "reason": "missing complete component footprint"}
    padded = np.pad(support, 1, constant_values=False)
    interior = np.logical_and.reduce([padded[1 + y:1 + y + support.shape[0], 1 + x:1 + x + support.shape[1]]
        for y in (-1, 0, 1) for x in (-1, 0, 1)])
    contour = np.argwhere(support & ~interior)
    # D is a quantized subtraction: D-2 must still represent >=0.8 opacity.
    qualified = d.min(axis=-1) >= 206
    lower = native_contrast_lower(p, u)
    best = np.zeros(len(contour))
    witness = np.full_like(contour, -1)
    height, width = support.shape
    for dy in range(-4, 5):
        for dx in range(-4, 5):
            if dx * dx + dy * dy > 16: continue
            ys, xs = contour[:, 0] + dy, contour[:, 1] + dx
            valid = (ys >= 0) & (ys < height) & (xs >= 0) & (xs < width)
            indices = np.flatnonzero(valid)
            for step_y, step_x in line_steps(dy, dx):
                indices = indices[support[contour[indices, 0] + step_y, contour[indices, 1] + step_x]]
            indices = indices[qualified[ys[indices], xs[indices]]]
            indices = indices[lower[ys[indices], xs[indices]] > best[indices]]
            best[indices] = lower[ys[indices], xs[indices]]
            witness[indices] = np.stack((ys[indices], xs[indices]), axis=1)
    def detail(index):
        wy, wx = witness[index]
        return {"contour_yx": contour[index].tolist(), "witness_yx": witness[index].tolist() if wy >= 0 else None,
            "contrast_lower_bound": float(best[index]),
            "normal_rgb": p[wy, wx].astype(int).tolist() if wy >= 0 else None,
            "underlay_rgb": u[wy, wx].astype(int).tolist() if wy >= 0 else None,
            "diagnostic_contribution_lower": float((d[wy, wx].min() - 2) / 255) if wy >= 0 else None}
    failures = np.flatnonzero(best < 3)
    result.update({"contour_pixels": len(contour), "contrast_lower_bound": float(best.min()),
        "worst": detail(int(np.argmin(best))), "unqualified_contours": int((witness[:, 0] < 0).sum()),
        "failing_contours": [detail(int(i)) for i in failures], "required": 3.0,
        "witness_radius_native_pixels": 4, "qualified_diagnostic_min_codes": 206})
    result["resolved"] = not any(result[k] for k in ("outside_changed", "unexpected_support_pixels", "underlay_compositing_errors",
        "missing_footprint_pixels", "negative_diagnostic_pixels", "nonneutral_coverage_pixels", "nonneutral_footprint_pixels", "unqualified_contours"))
    result["pass"] = bool(result["resolved"] and not len(failures))
    return result


def paint_identity(info, variant):
    errors, metadata = [], info.get("paint_geometry", {})
    if set(metadata) != set(ACTIONS): return ["incomplete paint geometry identities"]
    for action in ACTIONS:
        data, physical = metadata[action], info["geometry"][action]
        r, point = physical["radius"], physical["point"]
        compact = variant == "r4" and action != "fire" and r < 32
        body = min(1.25 * r, max(r, 26)) if compact else r
        expected = {"point": point, "nominal_radius": r, "hit_radius": 1.25 * r,
            "body_radius": body, "rim_radius": body + 1 if compact else r,
            "rim_shadow": (3.5 if compact else 5.25), "font_size": 12,
            "icon_center": [point[0], point[1] + (-13 if compact else -8)],
            "label_origin": [point[0] - data["label_width"] / 2, point[1] + (6 if compact else 17)],
            "badge_center": [point[0] + r * .72, point[1] - r * .72], "badge_radius": 9,
            "badge_shadow": 5.25 if variant == "r4" else 0, "badge_rim": 1.25 if variant == "r4" else 0}
        if data.get("label") != LABELS[action] or any(not np.allclose(data.get(k, np.nan), v, atol=.0002, rtol=0) for k, v in expected.items()):
            errors.append(action + ": paint geometry differs from frozen policy")
        if any(not isinstance(data.get(k), (int, float)) or data[k] <= 0 for k in ("label_width", "font_ascent", "font_descent")):
            errors.append(action + ": missing native font metric")
    return errors


def audit_affordance(info, footprints, components):
    """Pixel centers are (x+.5,y+.5). Account for every native glyph/support pixel."""
    rows, errors = [], []
    for action, image in components.items():
        yy, xx = np.where(image.max(axis=-1) >= 1)
        data = info["paint_geometry"][action]
        distance = np.hypot(xx + .5 - data["point"][0], yy + .5 - data["point"][1])
        rows.append({"action": action, "kind": "complete_visual_component", "support_pixels": len(xx),
            "outside_hit_pixels": int((distance > data["hit_radius"]).sum()),
            "maximum_distance": float(distance.max()) if len(xx) else None,
            "maximum_hit_spill": float(max(0, distance.max() - data["hit_radius"])) if len(xx) else None,
            "pixel_bbox_xyxy": [int(xx.min()), int(yy.min()), int(xx.max()), int(yy.max())] if len(xx) else None,
            "includes_noninteractive_badge": action in info["counts"]})
    for group in ("active_label", "inactive_label", "active_icon", "inactive_icon", "empty_count", "ready_count"):
        mask = footprints[group].max(axis=-1) >= 1
        yy, xx = np.where(mask)
        x, y, assigned = xx + .5, yy + .5, np.zeros(len(xx), dtype=int)
        for action in ACTIONS:
            depleted = info["counts"].get(action, 1) <= 0
            if group.startswith("inactive_") != depleted and group.endswith(("label", "icon")): continue
            if group == "empty_count" and action != "grenade": continue
            if group == "ready_count" and action != "smoke": continue
            data = info["paint_geometry"][action]
            if group.endswith("label"):
                ox, oy = data["label_origin"]
                region = (x >= ox - 1) & (x <= ox + data["label_width"] + 1) & (y >= oy - data["font_ascent"] - 1) & (y <= oy + data["font_descent"] + 1)
            elif group.endswith("icon"):
                ox, oy = data["icon_center"]
                region = (abs(x - ox) <= 15.5) & (abs(y - oy) <= 15.5)
            else:
                region = np.ones(len(xx), dtype=bool)
            belongs = region & (components[action][yy, xx].max(axis=-1) >= 1)
            assigned += belongs
            distance = np.hypot(x[belongs] - data["point"][0], y[belongs] - data["point"][1])
            outside = int((distance > data["hit_radius"]).sum())
            rows.append({"action": action, "kind": group, "support_pixels": int(belongs.sum()), "outside_hit_pixels": outside,
                "maximum_distance": float(distance.max()) if len(distance) else None,
                "noninteractive_count_exception": group.endswith("count")})
            if not belongs.any(): errors.append(action + ": no " + group + " support")
            if outside and not group.endswith("count"): errors.append(action + ": " + group + " foreground outside physical hit circle")
        if (assigned != 1).any(): errors.append(group + ": native glyph pixels not assigned to exactly one expected source control: " + str(int((assigned != 1).sum())))
    return {"rows": rows, "errors": errors, "pass": not errors, "pixel_coordinate_convention": "native pixel center (x+0.5,y+0.5)",
        "scope": "Every glyph pixel is assigned once using its source font/icon bounds and complete native component footprint; decoration and noninteractive count spill are reported separately."}


def intermediate_overlap(scene, group, alpha, footprint, all_footprints):
    """Report hidden/replaced prior strokes; never turn these into visible passes."""
    black, white = [read(scene / (group + "-" + p + ".png")).astype(float) for p in ("black", "white")]
    hidden = (((white - black) + 2 < footprint.astype(float) * alpha).any(axis=-1) & (footprint.max(axis=-1) >= 1))
    overlaps, covered = {}, np.zeros(hidden.shape, dtype=bool)
    for name, image in all_footprints.items():
        if name in (group, "border"): continue
        mask = image.max(axis=-1) >= 1
        overlaps[name] = int((hidden & mask).sum())
        covered |= mask
    return {"hidden_or_replaced_pixels": int(hidden.sum()), "isolated_layer_intersections": overlaps,
        "without_recorded_layer_intersection": int((hidden & ~covered).sum()),
        "scope": "Spatial footprint intersections, not exclusive causal labels; original source order and all native diagnostics remain available. Intermediate failure is retained."}


def read(path):
    return np.asarray(Image.open(path).convert("RGB"))


def audit_source(folder, expected_receipt=None, background_folder=None, expected_background_receipt=None):
    rows, errors, affordances = [], [], []
    required = matrix()
    scenes = sorted(folder.glob("*/scene.json"))
    if {p.parent.name for p in scenes} != set(required):
        errors.append("scene identities differ from exact preregistered 32-scene matrix")
    capture, background_capture = {}, {}
    if expected_receipt is None or background_folder is None:
        errors.append("missing frozen source receipt or native background folder")
    else:
        try:
            capture = json.loads((folder / "capture.json").read_text())
            bg_manifest = background_folder / "capture.json"
            background_capture = json.loads(bg_manifest.read_text())
            background_expected = expected_background_receipt or expected_receipt
            if capture.get("source_manifest_sha256") != expected_receipt["manifest_sha256"] or capture.get("source") != expected_receipt["source_full"]:
                errors.append("native capture source differs from frozen fixture receipt")
            if background_capture.get("source_manifest_sha256") != background_expected["manifest_sha256"] or background_capture.get("source") != background_expected["source_full"]:
                errors.append("native background source differs from frozen baseline fixture receipt")
            if capture.get("background_manifest_sha256") != digest(bg_manifest):
                errors.append("native background receipt mismatch")
            if capture.get("mode") != "controls" or background_capture.get("mode") != "backgrounds":
                errors.append("incorrect native capture mode")
            if capture.get("engine") != background_capture.get("engine") or capture.get("renderer") != background_capture.get("renderer"):
                errors.append("controls/background engine or renderer differs")
            for identity in (capture, background_capture):
                if [identity.get("engine", {}).get(k) for k in ("major", "minor", "patch")] != [4, 7, 2] or not identity.get("renderer"):
                    errors.append("missing pinned native renderer identity")
                if identity.get("source_verified_before_after") is not True:
                    errors.append("native source/UID before-after fence missing")
            expected_background_names = {l + "-" + b + ".png" for l in LAYOUTS for b in BACKGROUNDS}
            if {Path(x).name for x in background_capture.get("images", {})} != expected_background_names:
                errors.append("incomplete frozen native background matrix")
            for path, recorded in background_capture.get("images", {}).items():
                actual = background_folder / Path(path).name
                if digest(actual) != recorded:
                    errors.append("changed frozen native background: " + actual.name)
            if expected_receipt.get("paint_variant") not in ("r3", "r4"):
                errors.append("missing frozen paint variant")
            if len(capture.get("images", {})) != 2816:
                errors.append("expected 2816 source/normal/group/component/layer PNG identities")
        except (OSError, ValueError, KeyError) as exc:
            errors.append("native receipt: " + str(exc))
    capture_records = {x.get("id"): x for x in capture.get("records", [])}
    for metadata in scenes:
        scene = metadata.parent
        info = json.loads(metadata.read_text())
        if scene.name not in required:
            errors.append(scene.name + ": unknown scene")
            continue
        errors.extend(scene.name + ": " + x for x in scene_identity(info, required[scene.name]))
        try:
            errors.extend(scene.name + ": " + x for x in paint_identity(info, expected_receipt["paint_variant"]))
        except (KeyError, TypeError, ValueError) as exc:
            errors.append(scene.name + ": invalid paint metadata: " + str(exc))
        if capture_records.get(scene.name) != info:
            errors.append(scene.name + ": scene differs from native capture receipt")
        layout, background, held = required[scene.name]
        group_names = [x for x in GROUPS if x != "held_border" or held] + ["component_" + x for x in ACTIONS]
        expected_images = {"normal.png", "original.png"} | {g + "-" + p + ".png" for g in group_names for p in ("underlay", "black", "white", "footprint")} | {g + "-footprint.png" for g in LAYER_FOOTPRINTS}
        if set(info.get("images", {})) != expected_images:
            errors.append(scene.name + ": incomplete exact diagnostic image list")
        for name, recorded in info.get("images", {}).items():
            try:
                if digest(scene / name) != recorded or capture.get("images", {}).get(str(scene / name)) != recorded:
                    errors.append(scene.name + ": changed native image " + name)
            except OSError as exc:
                errors.append(str(exc))
        if background_folder is not None:
            bg = background_folder / (layout + "-" + background + ".png")
            try:
                if digest(bg) != info.get("background_sha256") or Path(info.get("background", "")) != bg:
                    errors.append(scene.name + ": background identity differs")
            except OSError as exc:
                errors.append(str(exc))
        normal = read(scene / "normal.png")
        if list(normal.shape[:2][::-1]) != LAYOUTS[layout][0]:
            errors.append(scene.name + ": incorrect native resolution")
        original = read(scene / "original.png")
        if not np.array_equal(normal, original):
            errors.append(info["id"] + ": wrapped normal is not pixel-identical to actual source")
        footprints, components = {}, {}
        for group in GROUPS:
            if group == "held_border" and info["id"].endswith("-idle"):
                continue
            try:
                footprints[group] = read(scene / (group + "-footprint.png"))
                row = audit_pixels(normal, *[read(scene / (group + "-" + p + ".png"))
                    for p in ("underlay", "black", "white")], info["alphas"][group],
                    footprint=footprints[group])
            except (OSError, ValueError, KeyError) as exc:
                errors.append(info["id"] + ": " + group + ": " + str(exc))
                continue
            row.update({"scene": info["id"], "group": group, "required": LIMITS.get(group),
                        "inactive_exception": group.startswith("inactive_"),
                        "gate": "retained_intermediate_stroke_diagnostic" if group in LEGACY else "complete_foreground"})
            row["pass"] = bool(row["resolved"] and (group not in LIMITS or row.get("contrast_lower_bound", 0) >= LIMITS[group]))
            rows.append(row)
        for action in ACTIONS:
            group = "component_" + action
            try:
                components[action] = read(scene / (group + "-footprint.png"))
                row = audit_boundary(normal, *[read(scene / (group + "-" + p + ".png")) for p in ("underlay", "black", "white")],
                    info["alphas"][group], components[action])
                rows.append({**row, "scene": info["id"], "group": group, "inactive_exception": False, "gate": "final_component_boundary"})
            except (OSError, ValueError, KeyError) as exc:
                errors.append(info["id"] + ": " + group + ": " + str(exc))
        try:
            layers = {g: read(scene / (g + "-footprint.png")) for g in LAYER_FOOTPRINTS}
            for row in rows:
                if row["scene"] == info["id"] and row["group"] in LEGACY:
                    row["hidden_coverage_accounting"] = intermediate_overlap(scene, row["group"], info["alphas"][row["group"]],
                        footprints[row["group"]], {**footprints, **layers})
        except (OSError, ValueError, KeyError) as exc:
            errors.append(info["id"] + ": intermediate coverage accounting: " + str(exc))
        try:
            affordances.append({"scene": info["id"], **audit_affordance(info, footprints, components)})
        except (ValueError, KeyError) as exc:
            errors.append(info["id"] + ": affordance: " + str(exc))
    gated = [x for x in rows if x["group"] not in LEGACY]
    return {"folder": str(folder), "scenes": len(scenes), "errors": errors, "rows": rows,
            "affordances": affordances, "gated_rows": len(gated), "retained_intermediate_rows": len(rows) - len(gated),
            "provenance_valid": bool(not errors and len(rows) == 656 and len(affordances) == 32),
            "pass": bool(not errors and len(rows) == 656 and len(gated) == 608 and len(affordances) == 32 and
                all(x["resolved"] and (x["inactive_exception"] or x["pass"]) for x in gated) and all(x["pass"] for x in affordances)),
            "external_surround_scope": "UNRESOLVED: independent actual-image inspection of final dark surrounds, truthful target affordance and scene occlusion is required; the registered four-pixel contour witness is a separate bounded measurement."}


def comparison_passes(result):
    # A low-contrast baseline is a valid bar. A baseline with invalid source,
    # matrix, native renderer, backgrounds or image identities is not comparable.
    return bool(result["baseline"]["provenance_valid"] and result["candidate"]["provenance_valid"] and
                result["candidate"]["pass"] and result["geometry_equal"] and
                result["font_metrics_equal"] and result["analysis_matches_freeze"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--freeze", type=Path, required=True)
    parser.add_argument("--backgrounds", type=Path, required=True)
    args = parser.parse_args()
    freeze = json.loads(args.freeze.read_text())
    receipts = {x["name"]: x for x in freeze["fixtures"]}
    result = {name: audit_source(getattr(args, name), receipts[name], args.backgrounds, receipts["baseline"])
              for name in ("baseline", "candidate")}
    frozen = {x["path"]: x["sha256"] for x in freeze["frozen_files"]}
    result["analysis_matches_freeze"] = all(digest(Path(__file__).parent / name) == frozen.get("scripts/" + name) for name in ("analyze_touch_contrast_r4.py", "analyze_touch_contrast.py"))
    baseline_geometry = {p.parent.name: json.loads(p.read_text())["geometry"] for p in args.baseline.glob("*/scene.json")}
    candidate_geometry = {p.parent.name: json.loads(p.read_text())["geometry"] for p in args.candidate.glob("*/scene.json")}
    result["geometry_equal"] = baseline_geometry == candidate_geometry and len(baseline_geometry) == 32
    fonts = {}
    for name in ("baseline", "candidate"):
        fonts[name] = {p.parent.name: {a: {k: v[k] for k in ("label", "label_width", "font_size", "font_ascent", "font_descent")}
            for a, v in json.loads(p.read_text())["paint_geometry"].items()} for p in getattr(args, name).glob("*/scene.json")}
    result["font_metrics_equal"] = fonts["baseline"] == fonts["candidate"] and len(fonts["baseline"]) == 32
    result["analysis_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    args.out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"baseline_pass": result["baseline"]["pass"], "candidate_pass": result["candidate"]["pass"], "geometry_equal": result["geometry_equal"]}))
    return 0 if comparison_passes(result) else 1


if __name__ == "__main__":
    raise SystemExit(main())
