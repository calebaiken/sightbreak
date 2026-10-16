#!/usr/bin/env python3
"""Stability numbers from a metal_probe_stats.py --json file, on the definitions reload_discolour_probe.gd asserts: the highest over the
lowest per-part median luma over the probed reload ticks, and the largest shift of the receiver's (r - b) / luma from its first tick.

    metal_probe_stability.py stats.json [view]
"""
import json
import sys

data = json.load(open(sys.argv[1]))
view = sys.argv[2] if len(sys.argv) > 2 else "sunlit"
keys = sorted((k for k in data if k.startswith(view + "_")), key=lambda k: int(k.split("_")[1]))
for part in ("receiver", "handguard"):
    vals = [data[k][part]["median"] for k in keys if part in data[k] and "median" in data[k][part]]
    print("%s %-9s median luma min %.1f max %.1f ratio %.3f over %d ticks" % (view, part, min(vals), max(vals), max(vals) / min(vals), len(vals)))
ch = [data[k]["receiver"]["chroma"] for k in keys]
print("%s receiver chroma first %.3f largest shift %.3f" % (view, ch[0], max(abs(c - ch[0]) for c in ch)))
