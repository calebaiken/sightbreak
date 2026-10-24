"""Copy exact bounded failed inputs; never write the original raw root."""
import hashlib
import json
from pathlib import Path
import shutil

HERE = Path(__file__).resolve().parent
RAW = Path("/workspace/sightbreak-touch-contrast-native-recovered-r4b-r3")
candidate = RAW / "candidate"
result = json.loads((RAW / "recomputed.json").read_text())["candidate"]
gated = [row for row in result["rows"] if not row["pass"] and
         row["gate"] != "retained_intermediate_stroke_diagnostic"]
labels = sorted(row["scene"] for row in result["affordances"] if not row["pass"])
assert len(gated) == 7 and len(labels) == 16
paths = {RAW / "recomputed.json", RAW / "SOURCE_FREEZE-r4b-r3.json"}
actions = ("fire", "jump", "crouch", "reload", "interact", "grenade", "smoke", "buy", "pause", "switch", "score")
for row in gated:
    scene = candidate / row["scene"]
    info = json.loads((scene / "scene.json").read_text())
    row["primitive_alpha"] = info["alphas"][row["group"]]
    paths.add(scene / "scene.json")
    paths.add(scene / "normal.png")
    for part in ("underlay", "black", "white", "footprint"):
        paths.add(scene / (row["group"] + "-" + part + ".png"))
for name in labels:
    scene = candidate / name
    paths.add(scene / "scene.json")
    for group in ("active_label", "inactive_label", "active_icon", "inactive_icon", "empty_count", "ready_count"):
        paths.add(scene / (group + "-footprint.png"))
    for action in actions:
        paths.add(scene / ("component_" + action + "-footprint.png"))
files = []
for original in sorted(paths):
    relative = original.relative_to(candidate) if original.is_relative_to(candidate) else Path("raw-metadata") / original.name
    copy = HERE / "retained" / relative
    if copy.exists(): raise SystemExit("refusing to overwrite retained input: " + str(copy))
    copy.parent.mkdir(parents=True, exist_ok=True)
    data = original.read_bytes()
    shutil.copyfile(original, copy)
    assert data == copy.read_bytes()
    files.append({"original": str(original), "copy": str(copy.relative_to(HERE)),
                  "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
manifest = {"scope": "EXACT_OLD_FAILURE_INPUTS_NO_NEW_NATIVE_EVIDENCE", "raw_root": str(RAW),
            "product_source": "108d1cdc6cf471daa7390298c234bb1c087ae865",
            "handoff": "b9bd7e62c70d3f5a061c4177ede6c73c21dc9d35",
            "source_acceptance": "95703781009fe402b1ec9998c3be9c2fc3eeb512",
            "files": files, "gated_rows": gated, "label_scenes": labels}
(HERE / "retained-inputs.json").write_text(json.dumps(manifest, indent=2) + "\n")
print(json.dumps({"files": len(files), "bytes": sum(row["bytes"] for row in files),
                  "gated_rows": len(gated), "label_scenes": len(labels)}))
