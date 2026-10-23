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


def luminance(rgb):
    rgb = np.clip(rgb, 0, 1)
    lin = np.where(rgb <= .04045, rgb / 12.92, ((rgb + .055) / 1.055) ** 2.4)
    return lin @ np.array([.2126, .7152, .0722])


def ratio(a, b):
    return (np.maximum(a, b) + .05) / (np.minimum(a, b) + .05)


def audit_pixels(normal, underlay, black, white, primitive_alpha):
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
    support = d.max(axis=-1) >= 1  # The quantization floor, never a brightness mask.
    outside = ~support
    result = {"support_pixels": int(support.sum()), "outside_changed": int(
        ((np.max(np.abs(p - u), axis=-1) > 1) & outside).sum()),
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
    result["resolved"] = not (invalid_interval or result["max_fit_residual_codes"] > 2 or
        result["outside_changed"] or result["negative_diagnostic_pixels"] or result["nonneutral_coverage_pixels"])
    return result


def read(path):
    return np.asarray(Image.open(path).convert("RGB"))


def audit_source(folder):
    rows, errors = [], []
    scenes = sorted(folder.glob("*/scene.json"))
    if len(scenes) != 32:
        errors.append("expected 32 scenes, got %d" % len(scenes))
    for metadata in scenes:
        scene = metadata.parent
        info = json.loads(metadata.read_text())
        normal = read(scene / "normal.png")
        original = read(scene / "original.png")
        if not np.array_equal(normal, original):
            errors.append(info["id"] + ": wrapped normal is not pixel-identical to actual source")
        for group in GROUPS:
            if group == "held_border" and info["id"].endswith("-idle"):
                continue
            try:
                row = audit_pixels(normal, *[read(scene / (group + "-" + p + ".png"))
                    for p in ("underlay", "black", "white")], info["alphas"][group])
            except (OSError, ValueError, KeyError) as exc:
                errors.append(info["id"] + ": " + group + ": " + str(exc))
                continue
            row.update({"scene": info["id"], "group": group, "required": LIMITS.get(group),
                        "inactive_exception": group.startswith("inactive_")})
            row["pass"] = bool(row["resolved"] and (group not in LIMITS or row.get("contrast_lower_bound", 0) >= LIMITS[group]))
            rows.append(row)
    return {"folder": str(folder), "scenes": len(scenes), "errors": errors, "rows": rows,
            "pass": bool(not errors and rows and all(x["pass"] for x in rows if not x["inactive_exception"]))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = {name: audit_source(getattr(args, name)) for name in ("baseline", "candidate")}
    baseline_geometry = {p.parent.name: json.loads(p.read_text())["geometry"] for p in args.baseline.glob("*/scene.json")}
    candidate_geometry = {p.parent.name: json.loads(p.read_text())["geometry"] for p in args.candidate.glob("*/scene.json")}
    result["geometry_equal"] = baseline_geometry == candidate_geometry and len(baseline_geometry) == 32
    result["analysis_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    args.out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"baseline_pass": result["baseline"]["pass"], "candidate_pass": result["candidate"]["pass"], "geometry_equal": result["geometry_equal"]}))
    return 0 if result["candidate"]["pass"] and result["geometry_equal"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
