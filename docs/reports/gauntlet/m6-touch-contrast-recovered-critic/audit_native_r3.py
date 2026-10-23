#!/usr/bin/env python3
"""Read-only independent native receipt and selected-pixel recomputation."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
from PIL import Image


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return np.asarray(Image.open(path).convert("RGB"), dtype=np.float64)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--analyzer", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    spec = importlib.util.spec_from_file_location("frozen_r3", args.analyzer)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    root = args.raw
    original = json.loads((root / "recomputed.json").read_text())
    freeze = json.loads((root / "SOURCE_FREEZE-r3.json").read_text())
    output = {"analyzer_sha256": digest(args.analyzer), "raw_result_sha256": digest(root / "recomputed.json"),
              "raw_freeze_sha256": digest(root / "SOURCE_FREEZE-r3.json"), "receipts": {}, "selected": []}
    geometries = {}
    for name in ("backgrounds", "baseline", "candidate"):
        folder = root / name
        capture = json.loads((folder / "capture.json").read_text())
        bad = [p for p, sha in capture["images"].items() if digest(Path(p)) != sha]
        result = {"images": len(capture["images"]), "image_hash_mismatches": bad,
                  "source": capture["source"], "source_manifest_sha256": capture["source_manifest_sha256"],
                  "source_verified_before_after": capture["source_verified_before_after"],
                  "engine": capture["engine"], "renderer": capture["renderer"]}
        if name != "backgrounds":
            receipt = next(x for x in freeze["fixtures"] if x["name"] == name)
            result["source_matches_freeze"] = capture["source"] == receipt["source_full"] and capture["source_manifest_sha256"] == receipt["manifest_sha256"]
            result["background_receipt_matches"] = capture["background_manifest_sha256"] == digest(root / "backgrounds/capture.json")
            bad_scenes, geometry = [], {}
            records = {x["id"]: x for x in capture["records"]}
            for scene, expected in m.matrix().items():
                info = json.loads((folder / scene / "scene.json").read_text())
                if info != records[scene] or m.scene_identity(info, expected): bad_scenes.append(scene)
                if list(Image.open(folder / scene / "normal.png").size) != info["size"]: bad_scenes.append(scene + " resolution")
                geometry[scene] = info["geometry"]
            result["scene_mismatches"] = bad_scenes
            geometries[name] = geometry
        output["receipts"][name] = result
    output["geometry_equal"] = geometries["baseline"] == geometries["candidate"]
    selections = [
        ("candidate", "mobile-min-white-idle", "active_icon"),
        ("candidate", "mobile-min-white-idle", "border"),
        ("candidate", "desktop-min-white-idle", "inactive_icon"),
        ("candidate", "desktop-max-white-held", "border"),
        ("candidate", "desktop-max-white-held", "held_border"),
        ("candidate", "mobile-min-white-held", "held_border"),
        ("candidate", "mobile-min-white-held", "active_label"),
        ("baseline", "desktop-max-white-idle", "active_label"),
        ("baseline", "desktop-max-white-idle", "empty_count"),
        ("baseline", "desktop-max-white-idle", "joystick_ring")]
    for source, scene, group in selections:
        folder = root / source / scene
        info = json.loads((folder / "scene.json").read_text())
        p, u, b, w, f = [read(folder / name) for name in ["normal.png"] + [group + "-" + x + ".png" for x in ("underlay", "black", "white", "footprint")]]
        alpha = info["alphas"][group]
        result = m.audit_pixels(p, u, b, w, alpha, footprint=f)
        saved = next(x for x in original[source]["rows"] if x["scene"] == scene and x["group"] == group)
        same = all(result[k] == saved[k] for k in result)
        d, support = w - b, f.max(axis=-1) >= 1
        errors = support & ((np.abs(b - u * (1 - d / 255)).max(axis=-1) > 2) | (d + 2 < f * alpha).any(axis=-1))
        points = [tuple(result["worst_pixel_yx"])] + [tuple(x) for x in np.argwhere(errors)[:3]]
        pixels = []
        for y, x in dict.fromkeys(points):
            badges = {}
            for key in ("grenade", "smoke"):
                item = info["geometry"][key]
                center = np.array(item["point"]) + np.array([.72, -.72]) * item["radius"]
                badges[key] = float(np.linalg.norm(np.array([x, y]) - center))
            pixels.append({"yx": [int(y), int(x)], "P": p[y,x].tolist(), "U": u[y,x].tolist(),
                           "B": b[y,x].tolist(), "W": w[y,x].tolist(), "footprint": f[y,x].tolist(),
                           "D": d[y,x].tolist(), "source_alpha": alpha,
                           "compositing_error_codes": float(np.abs(b[y,x] - u[y,x] * (1-d[y,x]/255)).max()),
                           "observed_P_vs_U_contrast": float(m.ratio(m.luminance(p[y,x]/255),m.luminance(u[y,x]/255))),
                           "distance_to_badge_centers": badges})
        output["selected"].append({"source": source, "scene": scene, "group": group,
                                   "matches_original_recomputation": same, "audit": result, "pixels": pixels})
    args.out.write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps({"geometry_equal": output["geometry_equal"], "image_hash_mismatches": sum(len(x["image_hash_mismatches"]) for x in output["receipts"].values()),
                      "selected_exact_recomputations": sum(x["matches_original_recomputation"] for x in output["selected"])}))


if __name__ == "__main__":
    main()
