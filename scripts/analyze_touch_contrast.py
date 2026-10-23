#!/usr/bin/env python3
"""Audit complete diagnostic support; fail closed on residuals or missing scenes."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image

GROUPS = ["active_label", "inactive_label", "active_icon", "inactive_icon",
          "empty_count", "ready_count", "border", "held_border", "joystick_ring", "joystick_knob"]
LIMITS = {"active_label": 4.5, "empty_count": 4.5, "ready_count": 4.5,
          "active_icon": 3.0, "border": 3.0, "held_border": 3.0,
          "joystick_ring": 3.0, "joystick_knob": 3.0}
LAYOUTS = {"mobile-min": ([960, 720], .7, 32), "mobile-max": ([960, 720], 1.5, 32),
           "desktop-min": ([1280, 720], .7, 0), "desktop-max": ([1280, 720], 1.5, 0)}
BACKGROUNDS = ("white", "gray", "arena", "smoke")


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


def audit_pixels(normal, underlay, black, white, primitive_alpha, footprint=None):
    """Native color comes from P=B+C(W-B); alpha only comes from call metadata.

    Every support pixel contributes to checks and the contrast minimum. A shared
    foreground color is fitted across the group, then bounded with all native
    pixel inequalities. This avoids dividing a single 1-code-value AA pixel.
    Black/white retain original alpha; repeated same-color glyph strokes remain
    affine. A nonconstant foreground, nonlinear blend or changed backdrop fails.
    """
    p, u, b, w = [np.asarray(x, dtype=np.float64) for x in (normal, underlay, black, white)]
    if len({x.shape for x in (p, u, b, w)}) != 1 or p.shape[-1] != 3:
        raise ValueError("diagnostic image sizes differ")
    d = w - b
    observed_support = d.max(axis=-1) >= 1
    footprint_present = footprint is not None
    f = np.asarray(footprint, dtype=np.float64) if footprint_present else np.maximum(d, 0)
    if f.shape != p.shape:
        raise ValueError("footprint size differs")
    support = f.max(axis=-1) >= 1  # Complete isolated native footprint, including occluded strokes.
    outside = ~support
    result = {"footprint_present": footprint_present, "support_pixels": int(support.sum()), "outside_changed": int(
        ((np.maximum.reduce([np.max(np.abs(x - u), axis=-1) for x in (p, b, w)]) > 1) & outside).sum()),
        "unexpected_support_pixels": int((observed_support & outside).sum()),
        "underlay_compositing_errors": int(((np.abs(b - u * (1 - d / 255)).max(axis=-1) > 2) & support).sum()),
        "missing_footprint_pixels": int(((d + 2 < f * float(primitive_alpha)).any(axis=-1) & support).sum()),
        "negative_diagnostic_pixels": int((d.min(axis=-1) < -1).sum()),
        "nonneutral_coverage_pixels": int(((d.max(axis=-1) - d.min(axis=-1)) > 1).sum())}
    if not support.any():
        return {**result, "resolved": False, "reason": "no rendered foreground support"}
    ds, ps, bs, us = d[support], p[support], b[support], u[support]
    # Least squares uses every supported pixel, with inherent D² conditioning.
    color = np.sum(ds * (ps - bs), axis=0) / np.maximum(np.sum(ds * ds, axis=0), 1)
    residual = np.abs(ps - (bs + ds * color))
    result["max_fit_residual_codes"] = float(residual.max())
    # ±2 code values conservatively bound the subtraction of quantized captures.
    lo = np.maximum(0, (ps - bs - 2) / np.maximum(ds + 2, 1)).max(axis=0)
    hi = np.minimum(1, (ps - bs + 2) / np.maximum(ds - 2, 1)).min(axis=0)
    result["inferred_rgb"] = color.tolist()
    result["inferred_rgb_interval"] = [lo.tolist(), hi.tolist()]
    invalid_interval = bool(np.any(lo > hi) or np.any(color < -.01) or np.any(color > 1.01))
    alpha = float(primitive_alpha)
    if not 0 < alpha <= 1:
        raise ValueError("primitive alpha missing or out of range")
    # Source alpha is permitted metadata, never source RGB. The minimum primitive
    # opacity is conservative for overlapping same-color strokes. Compare native
    # reconstructed color at that opacity with every exact background pixel.
    low_u, high_u = np.clip((us - .5) / 255, 0, 1), np.clip((us + .5) / 255, 0, 1)
    low_f = alpha * lo + (1 - alpha) * low_u
    high_f = alpha * hi + (1 - alpha) * high_u
    ul, uh, fl, fh = [luminance(x) for x in (low_u, high_u, low_f, high_f)]
    lower_ratio = np.where(fl > uh, (fl + .05) / (uh + .05),
                           np.where(ul > fh, (ul + .05) / (fh + .05), 1.0))
    index = int(np.argmin(lower_ratio))
    coords = np.argwhere(support)[index]
    result.update({"primitive_alpha": alpha,
                   "contrast_lower_bound": float(lower_ratio.min()),
                   "worst_pixel_yx": coords.tolist(),
                   "worst_underlay_rgb": us[index].astype(int).tolist(),
                   "low_coverage_pixels": int((ds.max(axis=-1) < alpha * 255 * .5).sum())})
    # Report observed strong-coverage contrast separately; never discard low-AA
    # support from reconstructed full-coverage background protection.
    strong = ds.min(axis=-1) >= alpha * 255 * .95
    result["strong_coverage_pixels"] = int(strong.sum())
    result["observed_strong_min"] = float(ratio(luminance(ps[strong] / 255), luminance(us[strong] / 255)).min()) if strong.any() else None
    result["resolved"] = not (not footprint_present or invalid_interval or result["max_fit_residual_codes"] > 2 or
        result["outside_changed"] or result["negative_diagnostic_pixels"] or result["nonneutral_coverage_pixels"] or
        result["underlay_compositing_errors"] or result["missing_footprint_pixels"] or result["unexpected_support_pixels"])
    return result


def read(path):
    return np.asarray(Image.open(path).convert("RGB"))


def audit_source(folder, expected_receipt=None, background_folder=None):
    rows, errors = [], []
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
            if capture.get("source_manifest_sha256") != expected_receipt["manifest_sha256"] or capture.get("source") != expected_receipt["source_full"]:
                errors.append("native capture source differs from frozen fixture receipt")
            if capture.get("background_manifest_sha256") != digest(bg_manifest):
                errors.append("native background receipt mismatch")
            if capture.get("mode") != "controls" or background_capture.get("mode") != "backgrounds":
                errors.append("incorrect native capture mode")
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
            if len(capture.get("images", {})) != 1280:
                errors.append("expected 1280 source/normal/diagnostic PNG identities")
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
        if capture_records.get(scene.name) != info:
            errors.append(scene.name + ": scene differs from native capture receipt")
        layout, background, held = required[scene.name]
        group_names = [x for x in GROUPS if x != "held_border" or held]
        expected_images = {"normal.png", "original.png"} | {g + "-" + p + ".png" for g in group_names for p in ("underlay", "black", "white", "footprint")}
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
        for group in GROUPS:
            if group == "held_border" and info["id"].endswith("-idle"):
                continue
            try:
                row = audit_pixels(normal, *[read(scene / (group + "-" + p + ".png"))
                    for p in ("underlay", "black", "white")], info["alphas"][group],
                    footprint=read(scene / (group + "-footprint.png")))
            except (OSError, ValueError, KeyError) as exc:
                errors.append(info["id"] + ": " + group + ": " + str(exc))
                continue
            row.update({"scene": info["id"], "group": group, "required": LIMITS.get(group),
                        "inactive_exception": group.startswith("inactive_")})
            row["pass"] = bool(row["resolved"] and (group not in LIMITS or row.get("contrast_lower_bound", 0) >= LIMITS[group]))
            rows.append(row)
    return {"folder": str(folder), "scenes": len(scenes), "errors": errors, "rows": rows,
            "pass": bool(not errors and len(rows) == 304 and all(x["resolved"] and (x["inactive_exception"] or x["pass"]) for x in rows)),
            "external_surround_scope": "UNRESOLVED: independent inspection of the complete dark surround against external backgrounds is still required."}


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
    result = {name: audit_source(getattr(args, name), receipts[name], args.backgrounds) for name in ("baseline", "candidate")}
    result["analysis_matches_freeze"] = digest(__file__) == next(x["sha256"] for x in freeze["frozen_files"] if x["path"] == "scripts/analyze_touch_contrast.py")
    baseline_geometry = {p.parent.name: json.loads(p.read_text())["geometry"] for p in args.baseline.glob("*/scene.json")}
    candidate_geometry = {p.parent.name: json.loads(p.read_text())["geometry"] for p in args.candidate.glob("*/scene.json")}
    result["geometry_equal"] = baseline_geometry == candidate_geometry and len(baseline_geometry) == 32
    result["analysis_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    args.out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"baseline_pass": result["baseline"]["pass"], "candidate_pass": result["candidate"]["pass"], "geometry_equal": result["geometry_equal"]}))
    return 0 if result["candidate"]["pass"] and result["geometry_equal"] and result["analysis_matches_freeze"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
