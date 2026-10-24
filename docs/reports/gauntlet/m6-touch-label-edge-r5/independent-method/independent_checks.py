"""Bounded independent source, interval, and attribution controls; no engine use."""
import copy
import hashlib
import importlib.util
import itertools
import json
import math
from pathlib import Path
import subprocess
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET

import numpy as np

HERE = Path(__file__).resolve().parent
PROPOSAL = HERE.parent
REPO = HERE.parents[4]
spec = importlib.util.spec_from_file_location("reviewed_prototype", PROPOSAL / "prototype.py")
prototype = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prototype)
ACTIONS = prototype.ACTIONS


def digest(data):
    return hashlib.sha256(data).hexdigest()


def fixture():
    shape = (9, 70, 3)
    groups = {g: np.zeros(shape, np.uint8) for g in ("active_label", "inactive_label")}
    info = {"size": [70, 9], "counts": {"grenade": 0, "smoke": 1}, "geometry": {}}
    components, labels = {}, {}
    for i, action in enumerate(ACTIONS):
        x = 4 + i * 6
        info["geometry"][action] = {"point": [x, 4], "hit_radius": 2.9}
        components[action] = np.zeros(shape, np.uint8)
        labels[action] = np.zeros(shape, np.uint8)
        group = "inactive_label" if action == "grenade" else "active_label"
        for xx, code in ((x - 2, 1), (x - 1, 64), (x, 255)):
            labels[action][4, xx] = code
            components[action][4, xx] = 255
            groups[group][4, xx] = code
    return info, groups, components, labels


def attribution_controls():
    results = []

    def observe(name, args, expected):
        try:
            outcome = prototype.audit_labels(*args)
            passed = outcome.get("pass") is True
            results.append({"case": name, "expected_accept": expected,
                            "actual_accept": passed, "matched": passed == expected,
                            "errors": outcome.get("errors", [])})
        except Exception as exc:
            results.append({"case": name, "expected_accept": expected,
                            "actual_accept": False, "matched": not expected,
                            "exception": type(exc).__name__ + ": " + str(exc)})

    observe("complete distinct controls preserve 1/64/255 code coverage", fixture(), True)
    mutations = {}
    args = fixture(); args[3]["jump"][4, 8] = 0
    mutations["one-code deletion while label remains nonempty"] = args
    args = fixture(); args[3]["jump"][4, 8] = 2
    mutations["intensity change with identical binary support"] = args
    args = fixture(); args[3]["jump"][4, 8] = [1, 2, 1]
    mutations["single-channel forged footprint"] = args
    args = fixture(); args[3]["jump"][4, 7] = 1; args[2]["jump"][4, 7] = 255
    mutations["extra low-code foreground"] = args
    args = fixture(); args[2]["jump"][4, 8] = 0
    mutations["component drops only AA pixel"] = args
    args = fixture(); args[0]["geometry"]["jump"]["hit_radius"] = 1.0
    mutations["paint inside component but outside actual hit"] = args
    args = fixture(); args[0]["geometry"]["fire"]["point"] = [8.5, 4.5]
    mutations["closer overlapping foreign control"] = args
    args = fixture(); args[3]["fire"][4, 8] = 1; args[2]["fire"][4, 8] = 255
    mutations["duplicate same-group AA pixel"] = args
    args = fixture(); args[1]["inactive_label"][4, 8] = 1
    args[3]["grenade"][4, 8] = 1; args[2]["grenade"][4, 8] = 255
    mutations["same native pixel claimed across active/inactive groups"] = args
    args = fixture(); args[0]["counts"]["grenade"] = 1
    mutations["inactive label falsely classified active"] = args
    args = fixture(); args[0]["geometry"].pop("jump")
    mutations["missing original hit geometry"] = args
    args = fixture(); args[0]["geometry"]["jump"]["point"] = [math.nan, 4]
    mutations["nonfinite geometry"] = args
    args = fixture(); args[3].pop("jump")
    mutations["old evidence without one required new action image"] = args
    args = fixture(); args[3]["jump"] = args[3]["jump"].astype(np.float64)
    mutations["non-RGB8 float mask"] = args
    args = fixture(); args[3]["jump"] = np.zeros((1, 1, 3), np.uint8)
    mutations["wrong native dimensions"] = args
    args = fixture(); args[3]["jump"][:] = 0
    mutations["empty action evidence"] = args
    for name, args in mutations.items():
        observe(name, args, False)

    # Reach the lexical tie, with a source action that loses that tie.
    args = fixture(); args[0]["geometry"]["buy"]["point"] = [10, 4]
    observe("normalized-distance exact tie uses lexical owner", args, False)

    # These two results document the prototype's delegated metadata boundary.
    delegated = []
    for name, update in (
        ("nonfinite active-action count", lambda x: x[0]["counts"].update(jump=math.nan)),
        ("unknown count identity", lambda x: x[0]["counts"].update(unknown=0)),
    ):
        args = fixture(); update(args)
        result = prototype.audit_labels(*args)
        delegated.append({"case": name, "prototype_accepts": result["pass"],
                          "scope": "requires unchanged full scene_identity before this helper"})
    sys.path.insert(0, str(REPO / "scripts"))
    from analyze_touch_contrast import matrix, scene_identity
    native_info = json.loads((PROPOSAL / "retained/mobile-min-white-idle/scene.json").read_text())
    assert not scene_identity(native_info, matrix()[native_info["id"]])
    for item, (action, value) in zip(delegated, (("jump", math.nan), ("unknown", 0))):
        changed = copy.deepcopy(native_info)
        changed["counts"][action] = value
        item["unchanged_full_scene_errors"] = scene_identity(changed, matrix()[changed["id"]])
        item["unchanged_full_scene_rejects"] = bool(item["unchanged_full_scene_errors"])
    return {"controls": results, "all_matched": all(r["matched"] for r in results),
            "delegated_metadata_examples": delegated}


def interval_controls():
    records = []
    # This derives the feasible difference from independently clipped code cells.
    # It is stricter at code endpoints; the proposal may conservatively overbound.
    values = (0, 1, 2, 28, 29, 30, 127, 128, 253, 254, 255)
    channel_pairs = list(itertools.product(values, repeat=2))
    misses = []
    max_excess = 0.0
    cases = []
    for i, pair in enumerate(channel_pairs):
        cases.append([pair, channel_pairs[(i * 13 + 7) % len(channel_pairs)],
                      channel_pairs[(i * 31 + 19) % len(channel_pairs)]])
    for base in (0, 1, 2, 127, 254, 255):
        for deltas in itertools.product(range(-3, 4), repeat=3):
            if all(0 <= base + d <= 255 for d in deltas):
                cases.append([(base, base + d) for d in deltas])
    feasible_cases = 0
    for triples in cases:
        b = np.array([p[0] for p in triples], float)
        w = np.array([p[1] for p in triples], float)
        exact_lo = max(0., float((np.maximum(0, w - .5) - np.minimum(255, b + .5)).max()))
        exact_hi = min(255., float((np.minimum(255, w + .5) - np.maximum(0, b - .5)).min()))
        result = prototype.neutral_difference_interval(b, w)
        if exact_lo <= exact_hi and (not result["feasible"] or result["lower"] > exact_lo or result["upper"] < exact_hi):
            misses.append({"b": b.tolist(), "w": w.tolist(), "exact": [exact_lo, exact_hi], "actual": result})
        if exact_lo <= exact_hi:
            feasible_cases += 1
            max_excess = max(max_excess, exact_lo - result["lower"], result["upper"] - exact_hi)
    for b, w in (([0]*3, [0]*3), ([255]*3, [255]*3), ([0]*3, [255]*3),
                 ([0]*3, [28,29,30]), ([0]*3, [28,29,31]), ([255]*3, [254]*3),
                 ([255]*3, [253]*3)):
        records.append({"black": b, "white": w, "result": prototype.neutral_difference_interval(b,w)})
    rejected = []
    for b, w in (([math.nan]*3,[1]*3), ([math.inf]*3,[1]*3), ([-1]*3,[1]*3),
                 ([256]*3,[1]*3), ([0,0],[1,1]), ([0,0,0,0],[1,1,1,1])):
        try:
            prototype.neutral_difference_interval(b,w)
            rejected.append(False)
        except ValueError:
            rejected.append(True)
    fractional = prototype.neutral_difference_interval([0.25]*3,[1.25]*3)
    return {"independent_clipped_cell_cases": len(cases), "feasible_cell_cases": feasible_cases,
            "false_exclusions": misses,
            "maximum_cell_overbound_codes": max_excess, "selected_boundaries": records,
            "six_malformed_inputs_rejected": all(rejected),
            "fractional_code_acceptance": {"feasible": fractional["feasible"],
                "limitation": "helper does not itself require integer RGB8 code metadata"},
            "contrast_scope": "No ratio or 3:1/4.5:1 acceptance is calculated by this helper. W=B has feasible D=0."}


def original_witnesses():
    from PIL import Image

    def image(path):
        return np.asarray(Image.open(path).convert("RGB"))

    manifest = json.loads((PROPOSAL / "retained-inputs.json").read_text())
    label_rows = []
    for scene in manifest["label_scenes"]:
        folder = PROPOSAL / "retained" / scene
        info = json.loads((folder / "scene.json").read_text())
        grouped = image(folder / "active_label-footprint.png")
        yy, xx = np.where(grouped.max(axis=-1) > 0)
        assigned = np.zeros(len(xx), np.uint8)
        for action in ACTIONS:
            if info["counts"].get(action, 1) <= 0:
                continue
            data = info["paint_geometry"][action]
            ox, oy = data["label_origin"]
            inside = ((xx + .5 >= ox - 1) & (xx + .5 <= ox + data["label_width"] + 1) &
                      (yy + .5 >= oy - data["font_ascent"] - 1) &
                      (yy + .5 <= oy + data["font_descent"] + 1))
            component = image(folder / ("component_" + action + "-footprint.png"))
            assigned += inside & (component[yy, xx].max(axis=-1) > 0)
        failed = np.where(assigned != 1)[0]
        jump = image(folder / "component_jump-footprint.png")
        pixels = []
        for index in failed:
            x, y = int(xx[index]), int(yy[index])
            eligible = []
            for action in ACTIONS:
                point, hit = info["geometry"][action]["point"], info["geometry"][action]["hit_radius"]
                n = math.hypot(x + .5 - point[0], y + .5 - point[1]) / hit
                if n <= 1:
                    eligible.append((n, action))
            pixels.append({"xy": [x,y], "footprint_rgb": grouped[y,x].tolist(),
                           "inside_jump_component": bool(jump[y,x].max() > 0),
                           "independent_hit_owner": min(eligible)[1] if eligible else None})
        label_rows.append({"scene": scene, "nominal_rectangle_failed_pixels": pixels})
    investigation = json.loads((PROPOSAL / "quantization-investigation.json").read_text())
    pixel_rows = []
    for row in investigation["records"]:
        folder = PROPOSAL / "retained" / row["scene"]
        x, y = row["pixel_xy"]
        pixels = {name: image(folder / (row["group"] + "-" + name + ".png"))[y,x].tolist()
                  for name in ("black", "white", "underlay")}
        pixel_rows.append({"scene": row["scene"], "group": row["group"], "xy": [x,y],
                           "all_reported_pixel_inputs_match_original": all(pixels[k] == row[k] for k in pixels),
                           "difference_channel_spread": int(np.ptp(np.array(pixels["white"]) - np.array(pixels["black"]))),
                           "original_frozen_resolved": row["original_frozen_resolved"]})
    return {"mobile_label_witnesses": label_rows, "seven_gated_pixel_witnesses": pixel_rows}


def preservation():
    manifest = json.loads((PROPOSAL / "retained-inputs.json").read_text())
    bad, total = [], 0
    for item in manifest["files"]:
        old, new = Path(item["original"]).read_bytes(), (PROPOSAL / item["copy"]).read_bytes()
        total += len(old)
        if old != new or len(old) != item["bytes"] or digest(old) != item["sha256"]:
            bad.append(item["copy"])
    freeze = json.loads((PROPOSAL / "SOURCE_FREEZE.json").read_text())
    freeze_bad = []
    for item in freeze["files"]:
        data = (REPO / item["path"]).read_bytes()
        if len(data) != item["bytes"] or digest(data) != item["sha256"]:
            freeze_bad.append(item["path"])
    source_diff = subprocess.check_output(["git", "-C", str(REPO), "diff", "--name-status",
        "108d1cdc6cf471daa7390298c234bb1c087ae865", "163daa53c24b214af79725a6c59adc75183b8c5d",
        "--", "game", "scripts", "tests", ".github"]).decode()
    changed = subprocess.check_output(["git", "-C", str(REPO), "diff", "--name-only",
        "b9bd7e62c70d3f5a061c4177ede6c73c21dc9d35", "163daa53c24b214af79725a6c59adc75183b8c5d"]).decode().splitlines()
    return {"retained_files": len(manifest["files"]), "retained_bytes": total,
            "original_vs_retained_mismatches": bad, "frozen_files": len(freeze["files"]),
            "freeze_mismatches": freeze_bad, "source_tree_diff": source_diff,
            "all_changes_since_original_handoff_are_proposal_reports": all(p.startswith("docs/reports/gauntlet/m6-touch-label-edge-r5/") for p in changed),
            "changed_report_files": len(changed)}


def fetch_api():
    commit = "ed1daf0bf001b61586d9930840f2f1394092c079"
    expected = json.loads((PROPOSAL / "pinned-font-api.json").read_text())
    documents = []
    for name in ("Font", "TextServer"):
        url = f"https://raw.githubusercontent.com/godotengine/godot/{commit}/doc/classes/{name}.xml"
        with urllib.request.urlopen(url, timeout=20) as response:
            data = response.read()
        root = ET.fromstring(data)
        proposal = next(x for x in expected["sources"] if x["url"] == url)
        descriptions = {}
        for method in root.find("methods"):
            if method.attrib["name"] in proposal["methods"]:
                descriptions[method.attrib["name"]] = " ".join("".join(method.find("description").itertext()).split())
        documents.append({"url": url, "sha256": digest(data), "bytes": len(data),
                          "matches_proposal_hash": digest(data) == proposal["sha256"],
                          "descriptions": descriptions})
    return {"engine_commit": commit, "retrieved_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),
            "documents": documents, "scope": "independently retrieved official pinned API; no native glyph metrics"}


if __name__ == "__main__":
    started = time.monotonic()
    result = {"scope": "SOURCE_AND_SYNTHETIC_ONLY_NO_NEW_NATIVE_EVIDENCE",
              "attribution": attribution_controls(), "quantization": interval_controls(),
              "preservation": preservation(), "original_witnesses": original_witnesses()}
    if "--fetch-api" in sys.argv:
        result["api"] = fetch_api()
    result["wall_seconds"] = time.monotonic() - started
    (HERE / "independent-results.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"attribution_all_matched": result["attribution"]["all_matched"],
                      "quantization_false_exclusions": len(result["quantization"]["false_exclusions"]),
                      "preservation": result["preservation"], "wall_seconds": result["wall_seconds"]}, indent=2))
    assert result["attribution"]["all_matched"]
    assert not result["quantization"]["false_exclusions"]
    assert not result["preservation"]["original_vs_retained_mismatches"]
    assert not result["preservation"]["freeze_mismatches"]
    assert not result["preservation"]["source_tree_diff"]
