#!/usr/bin/env python3
"""Pure independent R2 pixel and receipt-gate checks; no engine or native PNGs."""
import argparse
from contextlib import redirect_stdout
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

import numpy as np


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def checks(module, original):
    results = {}
    footprint = original.pixels()[3].astype(int) - original.pixels()[2].astype(int)
    audit = module.audit_pixels
    # The original runner now receives a real footprint, rather than rejecting
    # solely because R2 made that input mandatory.
    with patch.object(module, "audit_pixels", lambda *a, **k: audit(*a, footprint=footprint, **k)):
        results["original_witnesses_with_valid_footprint"] = original.run(module)
    results["valid_white_disconnected_glyph"] = audit(*original.pixels(), 1.0, footprint=footprint)
    p, u, b, w = original.pixels()
    for arr in (p, b, w):
        arr[3:9, 2:5] = u[3:9, 2:5]
    results["lost_disconnected_stroke"] = audit(p, u, b, w, 1.0, footprint=footprint)
    results["legitimate_translucent_glyph"] = audit(*original.pixels(alpha=.24), .24, footprint=footprint)

    # This fixture deliberately stubs the pixel layer to isolate metadata gates.
    # Its files are marker bytes, not native images. Never use it as visual data.
    with tempfile.TemporaryDirectory(prefix="touch-r2-receipts-") as tmp:
        root = Path(tmp)
        folder, backgrounds = root / "controls", root / "backgrounds"
        folder.mkdir(); backgrounds.mkdir()
        engine = {"major": 4, "minor": 7, "patch": 2}
        identity = {"engine": engine, "renderer": "PURE METADATA STUB", "source_verified_before_after": True}
        bg_capture = {**identity, "mode": "backgrounds", "images": {},
                      "source": "FROZEN SOURCE COMMIT", "source_manifest_sha256": "FROZEN SOURCE MANIFEST"}
        for layout in module.LAYOUTS:
            for background in module.BACKGROUNDS:
                path = backgrounds / (layout + "-" + background + ".png")
                path.write_bytes(b"PURE BACKGROUND MARKER")
                bg_capture["images"][str(path)] = module.digest(path)
        (backgrounds / "capture.json").write_text(json.dumps(bg_capture))
        expected = {"manifest_sha256": "FROZEN SOURCE MANIFEST", "source_full": "FROZEN SOURCE COMMIT"}
        capture = {**identity, "mode": "controls", "source_manifest_sha256": expected["manifest_sha256"],
                   "source": expected["source_full"], "background_manifest_sha256": module.digest(backgrounds / "capture.json"),
                   "images": {}, "records": []}
        keys = ["fire", "jump", "crouch", "reload", "interact", "grenade", "smoke", "buy", "pause", "switch", "score", "move"]
        for name, (layout, background, held) in module.matrix().items():
            size, scale, inset = module.LAYOUTS[layout]
            scene = folder / name; scene.mkdir()
            groups = [g for g in module.GROUPS if g != "held_border" or held]
            files = {"normal.png", "original.png"} | {g + "-" + p + ".png" for g in groups for p in ["underlay", "black", "white", "footprint"]}
            images = {}
            for image in files:
                path = scene / image; path.write_bytes(b"PURE IMAGE MARKER")
                images[image] = module.digest(path)
                capture["images"][str(path)] = images[image]
            bg = backgrounds / (layout + "-" + background + ".png")
            info = {"id": name, "layout": layout, "size": size, "scale": scale, "inset": inset, "held": held,
                    "counts": {"grenade": 0, "smoke": 1}, "movement": [.65, .45] if held else [0, 0],
                    "actions": ["fire", "reload", "interact"] if held else [], "geometry": {k: {} for k in keys},
                    "alphas": {g: 1.0 for g in groups}, "images": images, "background": str(bg), "background_sha256": module.digest(bg)}
            capture["records"].append(info)
            (scene / "scene.json").write_text(json.dumps(info))
        (folder / "capture.json").write_text(json.dumps(capture))
        arrays = {w: np.zeros((720, w, 3), dtype=np.uint8) for w in (960, 1280)}
        def fake_read(path):
            return arrays[960 if path.parent.name.startswith("mobile") else 1280]
        def pixel_ok(*args, **kwargs):
            return {"resolved": True, "contrast_lower_bound": 9.0}
        def run_metadata():
            value = module.audit_source(folder, expected, backgrounds)
            return {"pass": value["pass"], "errors": value["errors"], "rows": len(value["rows"])}
        with patch.object(module, "read", fake_read), patch.object(module, "audit_pixels", pixel_ok):
            cases = {"valid_metadata": run_metadata()}
            path = folder / "capture.json"
            saved = path.read_bytes()
            changed = json.loads(saved); changed["source"] = "OTHER SOURCE"
            path.write_text(json.dumps(changed)); cases["changed_source"] = run_metadata(); path.write_bytes(saved)
            changed = json.loads(saved); changed["renderer"] = ""
            path.write_text(json.dumps(changed)); cases["missing_renderer"] = run_metadata(); path.write_bytes(saved)
            scene = folder / next(iter(module.matrix()))
            metadata = scene / "scene.json"; old = metadata.read_bytes()
            changed = json.loads(old); changed["scale"] = 1.0
            metadata.write_text(json.dumps(changed)); cases["changed_scale"] = run_metadata(); metadata.write_bytes(old)
            metadata.rename(scene / "removed.json"); cases["missing_scene"] = run_metadata(); (scene / "removed.json").rename(metadata)
            image = scene / "active_label-footprint.png"; old = image.read_bytes()
            image.write_bytes(b"CHANGED"); cases["changed_footprint_image"] = run_metadata(); image.write_bytes(old)
            bg = backgrounds / "mobile-min-white.png"; old = bg.read_bytes()
            bg.write_bytes(b"CHANGED"); cases["changed_frozen_background"] = run_metadata(); bg.write_bytes(old)
            calls = [0]
            def inactive_unresolved(*args, **kwargs):
                calls[0] += 1
                return {"resolved": calls[0] != 2, "contrast_lower_bound": 9.0}
            with patch.object(module, "audit_pixels", inactive_unresolved):
                cases["unresolved_inactive"] = run_metadata()
            for label, changes in [("unbound_background_source", {"source": "UNRELATED SOURCE", "source_manifest_sha256": "UNRELATED MANIFEST"}),
                                   ("different_background_renderer", {"renderer": "OTHER RENDERER"})]:
                old_bg, old_capture = (backgrounds / "capture.json").read_bytes(), (folder / "capture.json").read_bytes()
                changed_bg = json.loads(old_bg); changed_bg.update(changes)
                (backgrounds / "capture.json").write_text(json.dumps(changed_bg))
                changed_capture = json.loads(old_capture)
                changed_capture["background_manifest_sha256"] = module.digest(backgrounds / "capture.json")
                (folder / "capture.json").write_text(json.dumps(changed_capture))
                cases[label] = run_metadata()
                (backgrounds / "capture.json").write_bytes(old_bg); (folder / "capture.json").write_bytes(old_capture)
            results["metadata_gate_cases"] = cases
        # Candidate-only success cannot validate a comparative baseline that
        # failed its source receipt. Geometry and analyzer freeze still match.
        freeze = root / "freeze.json"
        freeze.write_text(json.dumps({"fixtures": [{"name": "baseline"}, {"name": "candidate"}],
            "frozen_files": [{"path": "scripts/analyze_touch_contrast.py", "sha256": module.digest(module.__file__)}]}))
        call_count = [0]
        def invalid_baseline(*args):
            call_count[0] += 1
            return {"pass": call_count[0] != 1, "errors": ["native capture source differs from frozen fixture receipt"] if call_count[0] == 1 else []}
        argv = ["analyze", "--baseline", str(folder), "--candidate", str(folder), "--out", str(root / "analysis.json"),
                "--freeze", str(freeze), "--backgrounds", str(backgrounds)]
        with patch.object(module, "audit_source", invalid_baseline), patch.object(sys, "argv", argv), redirect_stdout(io.StringIO()):
            code = module.main()
        results["cli_accepts_invalid_baseline"] = {"exit_code": code, "false_accept": code == 0}
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scripts", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    module = load(args.scripts / "analyze_touch_contrast.py", "r2analysis")
    original = load(Path(__file__).with_name("counterexamples.py"), "r1witnesses")
    result = checks(module, original)
    checks_pass = (not any(x["false_accept"] for x in result["original_witnesses_with_valid_footprint"].values())
                   and result["valid_white_disconnected_glyph"]["resolved"]
                   and result["legitimate_translucent_glyph"]["resolved"]
                   and not result["lost_disconnected_stroke"]["resolved"]
                   and result["metadata_gate_cases"]["valid_metadata"]["pass"]
                   and all(not x["pass"] for k, x in result["metadata_gate_cases"].items() if k != "valid_metadata")
                   and not result["cli_accepts_invalid_baseline"]["false_accept"])
    result["independent_checks_pass"] = bool(checks_pass)
    args.out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"independent_checks_pass": bool(checks_pass)}))
    return int(not checks_pass)


if __name__ == "__main__":
    raise SystemExit(main())
