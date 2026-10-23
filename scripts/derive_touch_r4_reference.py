#!/usr/bin/env python3
"""Read retained R3 native masks; derive a small source-only geometry reference."""
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image

REPO = Path(__file__).resolve().parents[1]
RAW = Path("/workspace/sightbreak-touch-contrast-native-recovered-r3/candidate")
OUT = REPO / "scripts/fixtures/touch_contrast_r4/r3_glyph_support.json"


def main():
    rows, inputs = [], []
    for layout in ("mobile-min", "mobile-max", "desktop-min", "desktop-max"):
        scene = RAW / (layout + "-white-idle")
        info = json.loads((scene / "scene.json").read_text())
        masks = {}
        assignments = {}
        for group in ("active_label", "inactive_label", "active_icon", "inactive_icon"):
            path = scene / (group + "-footprint.png")
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            assert digest == info["images"][path.name]
            masks[group] = np.asarray(Image.open(path).convert("RGB")).max(axis=-1) >= 1
            assignments[group] = np.zeros(masks[group].shape, dtype=np.uint8)
            inputs.append({"scene": scene.name, "file": path.name, "sha256": digest})
        for action, geometry in info["geometry"].items():
            if action == "move":
                continue
            point = geometry["point"]
            entry = {"layout": layout, "action": action, "point": point,
                     "radius": geometry["radius"], "support": {}}
            for kind in ("label", "icon"):
                group = ("inactive_" if action == "grenade" else "active_") + kind
                mask = masks[group]
                x, y = point
                left, right = int(x) - (36 if kind == "label" else 18), int(x) + (36 if kind == "label" else 18)
                top, bottom = (int(y), int(y) + 28) if kind == "label" else (int(y) - 27, int(y) + 10)
                top, bottom, left, right = max(top, 0), min(bottom, mask.shape[0]), max(left, 0), min(right, mask.shape[1])
                yy, xx = np.nonzero(mask[top:bottom, left:right])
                assert len(xx), (layout, action, kind)
                assignments[group][top:bottom, left:right] += mask[top:bottom, left:right]
                entry["support"][kind] = np.column_stack((xx + left, yy + top)).tolist()
            rows.append(entry)
        for group, mask in masks.items():
            assert np.all(assignments[group][mask] == 1), (layout, group, "incomplete/ambiguous reference assignment")
    result = {"source": "a52022169241df9ff662039547a375e1c46ac1c5",
              "scope": "Derived from unchanged R3 isolated native masks; not an R4 render or acceptance result.",
              "inputs": inputs, "controls": rows}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, separators=(",", ":")) + "\n")
    print("R3_REFERENCE controls=%d points=%d" % (len(rows), sum(len(p) for r in rows for p in r["support"].values())))


if __name__ == "__main__":
    main()
