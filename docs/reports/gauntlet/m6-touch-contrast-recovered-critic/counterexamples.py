#!/usr/bin/env python3
"""Independent pure falsifiers. No engine, native process, OCR or service.

Usage: python counterexamples.py --scripts /path/to/frozen/scripts --out result.json
Exit 1 means the supplied oracle accepted at least one invalid witness.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import tempfile

import numpy as np
from PIL import Image


def load(path):
    spec = importlib.util.spec_from_file_location("reviewed_touch_analysis", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def pixels(alpha=1.0, backdrop=.05):
    u = np.full((12, 20, 3), backdrop)
    cov = np.zeros((12, 20, 1))
    cov[1, 1:19, 0] = np.arange(1, 19) / 255
    cov[3:9, 2:5, 0] = .9
    cov[3:9, 12:15, 0] = 1.0
    a = cov * alpha
    q = lambda x: np.round(np.clip(x, 0, 1) * 255).astype(np.uint8)
    return [q(u * (1 - a) + a), q(u), q(u * (1 - a)), q(u * (1 - a) + a)]


def run(module):
    results = {}
    p, u, b, w = pixels(backdrop=.8)
    true = module.audit_pixels(p, u, b, w, 1.0)
    changed_u = u.copy()
    support = (w.astype(int) - b.astype(int)).max(axis=-1) >= 1
    changed_u[support] = 13
    false = module.audit_pixels(p, changed_u, b, w, 1.0)
    results["supported_underlay_mismatch"] = {
        "true_contrast": true.get("contrast_lower_bound"), "changed": false,
        "false_accept": bool(false["resolved"] and false.get("contrast_lower_bound", 0) >= 4.5),
        "required": "Reject changed suppressed underlay on glyph support."}

    p, u, b, w = pixels()
    b[0, 0] = w[0, 0] = 180
    false = module.audit_pixels(p, u, b, w, 1.0)
    results["outside_diagnostics_mismatch"] = {
        "changed": false, "false_accept": bool(false["resolved"]),
        "required": "Reject black/white diagnostic changes outside their support."}

    # A later .9-opacity black layer attenuates a white glyph by .1. It is
    # composited after all diagnostics, rather than being antialiasing.
    p, u, b, w = pixels()
    attenuate = lambda x: np.round(x.astype(float) * .1).astype(np.uint8)
    p, u, b, w = map(attenuate, (p, u, b, w))
    false = module.audit_pixels(p, u, b, w, 1.0)
    actual_ratio = float(module.ratio(module.luminance(np.array([[.1, .1, .1]])),
                                      module.luminance(np.array([[.005, .005, .005]])))[0])
    results["later_layer_occlusion"] = {
        "actual_full_glyph_contrast": actual_ratio, "changed": false,
        "false_accept": bool(false["resolved"] and false.get("contrast_lower_bound", 0) >= 4.5),
        "required": "Separate AA from later-layer occlusion or fail unresolved."}

    # The old entry point requires neither source receipts nor real dimensions,
    # scene identities, actual engine metadata or matching background pixels.
    with tempfile.TemporaryDirectory(prefix="touch-critic-pure-") as name:
        root = Path(name)
        for number in range(32):
            scene = root / ("invented-%02d-idle" % number)
            scene.mkdir()
            p, u, b, w = pixels()
            Image.fromarray(p).save(scene / "normal.png")
            Image.fromarray(p).save(scene / "original.png")
            for group in module.GROUPS:
                for pass_name, arr in (("underlay", u), ("black", b), ("white", w)):
                    if group.startswith("inactive_"):
                        arr = u  # No foreground support: must be unresolved.
                    Image.fromarray(arr).save(scene / (group + "-" + pass_name + ".png"))
            (scene / "scene.json").write_text(json.dumps({
                "id": scene.name, "geometry": {},
                "alphas": {x: 1.0 for x in module.GROUPS},
                "background": "/nonexistent/never-captured.png"}))
        false = module.audit_source(root)
        inactive = [x for x in false["rows"] if x["inactive_exception"]]
        results["invented_matrix_missing_binding_and_unresolved_inactive"] = {
            "scenes": false["scenes"], "errors": false["errors"],
            "pass": false["pass"], "inactive_rows": len(inactive),
            "unresolved_inactive_rows": sum(not x["resolved"] for x in inactive),
            "false_accept": bool(false["pass"]),
            "required": "Require exact matrix, source/native/background binding, and resolved inactive rows."}
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scripts", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    results = run(load(args.scripts / "analyze_touch_contrast.py"))
    args.out.write_text(json.dumps(results, indent=2) + "\n")
    print(json.dumps({name: item["false_accept"] for name, item in results.items()}))
    return int(any(x["false_accept"] for x in results.values()))


if __name__ == "__main__":
    raise SystemExit(main())
