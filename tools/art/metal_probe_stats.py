#!/usr/bin/env python3
"""Statistics for the frames written by game/tests/viewmodel_metal_probe.gd.

For every <view>_<tick>.png with <view>_<tick>_<part>.png beside it, the part's visible pixels are those that differ between the two
(the same rule as viewmodel_light_probe.gd: summed channel difference above 0.03 of full scale, on every second pixel). Per part it prints
the median sRGB colour, luma median / p10 / p90, the (r - b) / luma balance, the local detail (mean absolute luma difference to the
four neighbours three pixels away, as the light probe computes it) and the share of pixels brighter than the median by 25 luma
(a measure of how much of the face is highlight, not of how bright the highlight is).

    metal_probe_stats.py <dir> [--parts receiver,handguard] [--json out.json]
"""
import argparse
import glob
import json
import os
import re
import sys

import numpy as np
from PIL import Image


def luma(a):
    return 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]


def load(path):
    return np.asarray(Image.open(path).convert("RGB")).astype(np.float32)


def stats(base, hidden):
    diff = np.abs(base - hidden).sum(axis=2) / 255.0
    mask = np.zeros(diff.shape, bool)
    mask[::2, ::2] = diff[::2, ::2] > 0.03
    n = int(mask.sum())
    if n < 24:
        return {"n": n * 4}
    lum = luma(base)
    pad = np.pad(lum, 3, mode="edge")
    h, w = lum.shape
    around = (pad[3:3 + h, 0:w] + pad[3:3 + h, 6:6 + w] + pad[0:h, 3:3 + w] + pad[6:6 + h, 3:3 + w]) * 0.25
    detail = np.abs(lum - around)[mask].mean()
    rgb = base[mask]
    med = np.median(rgb, axis=0)
    l = lum[mask]
    ml = float(np.median(l))
    return {
        "n": n * 4,
        "rgb": [float(x) for x in med],
        "median": ml,
        "p10": float(np.percentile(l, 10)),
        "p90": float(np.percentile(l, 90)),
        "p99": float(np.percentile(l, 99)),
        "max": float(l.max()),
        "chroma": float((med[0] - med[2]) / max(ml, 1.0)),
        "detail": float(detail),
        "hot": float((l > ml + 25.0).mean()),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dir")
    ap.add_argument("--parts", default="receiver,handguard")
    ap.add_argument("--json")
    args = ap.parse_args()
    parts = [p for p in args.parts.split(",") if p]
    result = {}
    for path in sorted(glob.glob(os.path.join(args.dir, "*.png"))):
        m = re.match(r"^(?P<view>[a-z]+)_(?P<tick>-?\d+)\.png$", os.path.basename(path))
        if not m:
            continue
        key = "%s_%s" % (m["view"], m["tick"])
        base = load(path)
        entry = {}
        for part in parts:
            hp = os.path.join(args.dir, "%s_%s_%s.png" % (m["view"], m["tick"], part))
            if os.path.exists(hp):
                entry[part] = stats(base, load(hp))
        result[key] = entry
        for part, s in entry.items():
            if s.get("n", 0) < 24:
                print("%s %-9s n=%d (not visible)" % (key, part, s.get("n", 0)))
                continue
            print("%-13s %-9s n=%6d rgb=(%3.0f,%3.0f,%3.0f) luma med=%5.1f p10=%5.1f p90=%5.1f p99=%5.1f max=%5.1f chroma=%+.3f detail=%.2f hot=%.3f" % (
                key, part, s["n"], *s["rgb"], s["median"], s["p10"], s["p90"], s["p99"], s["max"], s["chroma"], s["detail"], s["hot"]))
    if args.json:
        with open(args.json, "w") as f:
            json.dump(result, f, indent=1)


if __name__ == "__main__":
    sys.exit(main())
